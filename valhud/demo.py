"""A simulated VALORANT match, so the HUD can be set up and tested without a
game: buy phases, fights, the spike, the economy, ultimates and half time.

Not a faithful model of the game, just believable numbers that move.
"""

import random
import time

from .game import SIDES, ULT_MAX, WEAPONS, empty_state, merge

BUY_TIME, ROUND_TIME, SPIKE_TIME, END_TIME = 30, 100, 45, 7
DEMO_AGENTS = [["Jett", "Sova", "Omen", "Killjoy", "Fade"], ["Raze", "Viper", "Skye", "Cypher", "Breach"]]
DEMO_NAMES = [["Ace", "Bolt", "Cipher", "Dash", "Echo"], ["Flux", "Grit", "Halo", "Ion", "Jinx"]]
RIFLES = ["Vandal", "Phantom"]


class DemoGame:
    def __init__(self, speed=4.0, seed=None, attack_first="left", map_name="Ascent", team_size=5):
        self.speed = speed
        self.team_size = 2 if team_size == 2 else 5
        self.rng = random.Random(seed)
        self.attack_first = attack_first
        self.state = empty_state()
        self.state["connected"] = True
        self.state["match"]["map"] = map_name
        players = []
        for t, side in enumerate(SIDES):
            for i in range(self.team_size):
                agent = DEMO_AGENTS[t][i]
                players.append({"team": side, "slot": i + 1, "name": DEMO_NAMES[t][i], "agent": agent,
                                "ult_max": ULT_MAX[agent], "credits": 800})
        self.state = merge(self.state, {"players": players})
        self.loss_streak = {"left": 0, "right": 0}
        self.clock = 0.0
        self._last = None
        self._new_round()

    # --- the source interface (as used by the app) ------------------------

    last_error = None

    def fetch(self):
        now = time.monotonic()
        dt = 0 if self._last is None else (now - self._last) * self.speed
        self._last = now
        self.advance(dt)
        return self.state

    def advance(self, seconds):
        """Run the match forward (in game seconds), a second at a time."""
        while seconds > 0:
            step = min(1.0, seconds)
            self._tick(step)
            seconds -= step

    # --- the match --------------------------------------------------------

    def _players(self, side=None, alive=None):
        return [p for p in self.state["players"] if p["slot"] <= self.team_size
                and (side is None or p["team"] == side) and (alive is None or p["alive"] == alive)]

    def _attackers(self, round_no):
        first, other = self.attack_first, ("right" if self.attack_first == "left" else "left")
        if round_no <= 12:
            return first
        if round_no <= 24:
            return other
        return first if round_no % 2 else other  # overtime swaps every round

    def _new_round(self):
        m = self.state["match"]
        m["round"] += 1
        if m["round"] in (1, 13) or (m["round"] > 24 and m["round"] % 2):
            for p in self._players():
                p["credits"] = 800 if m["round"] in (1, 13) else 5000
                p["weapon"], p["shield"] = "Classic", 0
                p["abilities"] = {"C": [0, 2], "Q": [0, 1], "E": [1, 1]}
        m["attackers"] = self._attackers(m["round"])
        m["phase"], m["timer"] = "buy", BUY_TIME
        m["round_winner"], m["win_type"] = "", ""
        m["spike"] = {"state": "carried", "timer": 0, "carrier": None}
        for p in self._players():
            p["alive"], p["health"], p["spike"] = True, 100, False
            if p["shield"] and self.rng.random() < 0.5:
                p["shield"] = 0  # used up last round
        carrier = self.rng.choice(self._players(m["attackers"]))
        carrier["spike"] = True
        m["spike"]["carrier"] = [carrier["team"], carrier["slot"]]
        self._bought = False

    def _buy(self):
        for p in self._players():
            money = p["credits"]
            if money >= 3900 and p["weapon"] not in RIFLES + ["Operator"]:
                gun = "Operator" if p["agent"] in ("Jett", "Chamber") and money >= 5700 else self.rng.choice(RIFLES)
            elif money >= 3900 or p["weapon"] in RIFLES + ["Operator"]:
                gun = p["weapon"]
            elif money >= 2400:
                gun = self.rng.choice(["Spectre", "Bulldog", "Guardian", "Marshal"])
            elif money >= 800:
                gun = self.rng.choice(["Sheriff", "Ghost", "Classic"])
            else:
                gun = p["weapon"]
            if gun != p["weapon"]:
                p["credits"] -= WEAPONS[gun]
                p["weapon"] = gun
            if p["credits"] >= 1000 and p["shield"] < 50:
                p["credits"], p["shield"] = p["credits"] - 1000, 50
            elif p["credits"] >= 400 and p["shield"] < 25:
                p["credits"], p["shield"] = p["credits"] - 400, 25
            for key in ("C", "Q"):
                have, most = p["abilities"][key]
                while have < most and p["credits"] >= 250:
                    p["credits"] -= 250
                    have += 1
                p["abilities"][key] = [have, most]
        self._bought = True

    def _tick(self, dt):
        m = self.state["match"]
        m["timer"] = max(0, m["timer"] - dt)
        if m["phase"] == "buy":
            if not self._bought and m["timer"] < BUY_TIME - 5:
                self._buy()
            if m["timer"] <= 0:
                m["phase"], m["timer"] = "combat", ROUND_TIME
        elif m["phase"] == "combat":
            self._fight(dt)
        elif m["phase"] == "end":
            if m["timer"] <= 0:
                score = m["score"]
                if max(score.values()) >= 13 and abs(score["left"] - score["right"]) >= 2:
                    self.__init__(self.speed, attack_first=self.attack_first, map_name=m["map"], team_size=self.team_size)
                else:
                    self._new_round()
        self._spectate()

    def _fight(self, dt):
        m = self.state["match"]
        atk = m["attackers"]
        dfn = "right" if atk == "left" else "left"
        spike = m["spike"]
        # Abilities get used early in the round.
        for p in self._players(alive=True):
            for key in ("C", "Q", "E"):
                have, most = p["abilities"][key]
                if have and self.rng.random() < 0.02 * dt:
                    p["abilities"][key] = [have - 1, most]
            if p["ult_points"] >= p["ult_max"] and self.rng.random() < 0.01 * dt:
                p["ult_points"] = 0
        # Chip damage and the odd duel.
        for p in self._players(alive=True):
            if self.rng.random() < 0.05 * dt:
                p["health"] = max(1, p["health"] - self.rng.randint(10, 40))
        if self.rng.random() < 0.09 * dt:
            killer_side = self.rng.choice((atk, dfn))
            victims = self._players("right" if killer_side == "left" else "left", alive=True)
            killers = self._players(killer_side, alive=True)
            if victims and killers:
                v, k = self.rng.choice(victims), self.rng.choice(killers)
                self._kill(k, v)
        # The spike.
        if spike["state"] == "carried" and m["timer"] < ROUND_TIME - 25 and self.rng.random() < 0.04 * dt:
            carrier = next((p for p in self._players(atk, alive=True) if p["spike"]), None)
            if carrier:
                carrier["spike"], carrier["credits"] = False, carrier["credits"] + 300
                spike.update(state="planted", timer=SPIKE_TIME, carrier=None)
                m["timer"] = SPIKE_TIME
        elif spike["state"] == "planted":
            spike["timer"] = m["timer"]
            if self._players(dfn, alive=True) and self.rng.random() < 0.015 * dt:
                spike["state"] = "defused"
                return self._end_round(dfn, "Deactivation")
        # How the round ends.
        if not self._players(dfn, alive=True):
            return self._end_round(atk, "Detonation" if spike["state"] == "planted" else "Elimination")
        if not self._players(atk, alive=True) and spike["state"] != "planted":
            return self._end_round(dfn, "Elimination")
        if m["timer"] <= 0:
            if spike["state"] == "planted":
                spike["state"] = "detonated"
                return self._end_round(atk, "Detonation")
            return self._end_round(dfn, "Time")

    def _kill(self, killer, victim):
        victim["alive"], victim["health"], victim["shield"] = False, 0, 0
        victim["deaths"] += 1
        victim["ult_points"] = min(victim["ult_max"], victim["ult_points"] + 1)
        if victim["spike"]:
            victim["spike"] = False
            alive = self._players(victim["team"], alive=True)
            if alive:  # someone picks it up
                carrier = self.rng.choice(alive)
                carrier["spike"] = True
                self.state["match"]["spike"]["carrier"] = [carrier["team"], carrier["slot"]]
        killer["kills"] += 1
        # The observer follows whoever gets the kill.
        self.state["match"]["observed"] = {"team": killer["team"], "slot": killer["slot"]}
        killer["credits"] = min(9000, killer["credits"] + 200)
        killer["ult_points"] = min(killer["ult_max"], killer["ult_points"] + 1)
        mates = [p for p in self._players(killer["team"], alive=True) if p is not killer]
        if mates and self.rng.random() < 0.4:
            self.rng.choice(mates)["assists"] += 1

    def _spectate(self):
        """Someone's always spectated: a living player (a new one once the
        one watched dies, or at the start of each round)."""
        m = self.state["match"]
        o = m.get("observed")
        p = next((p for p in self._players() if o and (p["team"], p["slot"]) == (o["team"], o["slot"])), None)
        if p is None or (not p["alive"] and m["phase"] == "combat" and self.rng.random() < 0.3):
            alive = self._players(alive=True)
            if alive:
                p = self.rng.choice(alive)
                m["observed"] = {"team": p["team"], "slot": p["slot"]}

    def _end_round(self, winner, how):
        m = self.state["match"]
        loser = "right" if winner == "left" else "left"
        m["phase"], m["timer"] = "end", END_TIME
        m["round_winner"], m["win_type"] = winner, how
        m["score"][winner] += 1
        m["rounds"].append({"winner": winner, "win_type": how})
        self.loss_streak[winner] = 0
        self.loss_streak[loser] = min(2, self.loss_streak[loser] + 1)
        for p in self._players():
            if p["team"] == winner:
                p["credits"] += 3000
            else:
                p["credits"] += 1900 + 500 * (self.loss_streak[loser] - 1)
            p["credits"] = min(9000, p["credits"])
            if p["alive"] is False:
                p["weapon"] = "Classic"
            p["ult_points"] = min(p["ult_max"], p["ult_points"] + 1 if self.rng.random() < 0.3 else p["ult_points"])
