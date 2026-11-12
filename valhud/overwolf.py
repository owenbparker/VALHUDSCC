"""VALORANT data from Overwolf's game events (the SCC VAL HUD Link app in
overwolf-app/ posts them to /api/ingest as {"source": "overwolf",
"overwolf": {...}}).

While Overwolf is live it is where the HUD gets everything it gives: names,
agents, alive or dead, K/D/A, credits, weapons, shields, ult points, the
spike carrier, round, phase, score, sides, map, round history and agent
select. The screen reader still reads health (Overwolf only has the local
player's) and anything Overwolf leaves empty (e.g. the spike being planted,
or the whole scoreboard if Overwolf doesn't fill it in for an observer).
When Overwolf stops sending (the app, Overwolf or its game events die), or
its score disagrees with the screen's for a while, the screen reader takes
over everything again by itself.

What Overwolf sends (dev.overwolf.com, VALORANT): info updates
{"info": {"match_info": {"scoreboard_3": "<json>", ...}}, "feature": ...},
events {"events": [{"name": "spike_defused", "data": ""}]}, and the app's own
{"heartbeat": {"running": bool, "features": [...]}, "info": <getInfo res>}
every two seconds.
"""

import json
import re
import threading
import time

from . import game

GAME_ID = 21640
LIVE_FOR = 6.0         # seconds without a word from the app before Overwolf counts as gone
DISAGREE_FOR = 30.0    # seconds its score may differ from the screen's before it's set aside
SELECT_SCENE = "CharacterSelectPersistentLevel"

# Internal agent ids (me.agent, sometimes scoreboard character) -> our names.
AGENT_IDS = {"Clay": "Raze", "Pandemic": "Viper", "Wraith": "Omen", "Hunter": "Sova", "Thorne": "Sage",
             "Phoenix": "Phoenix", "Wushu": "Jett", "Gumshoe": "Cypher", "Sarge": "Brimstone", "Breach": "Breach",
             "Vampire": "Reyna", "Killjoy": "Killjoy", "Guide": "Skye", "Stealth": "Yoru", "Rift": "Astra",
             "Grenadier": "Kayo", "Deadeye": "Chamber", "Sprinter": "Neon", "BountyHunter": "Fade",
             "Mage": "Harbor", "AggroBot": "Gekko", "Cable": "Deadlock", "Sequoia": "Iso", "Smonk": "Clove",
             "Nox": "Vyse", "Cashew": "Tejo", "Terra": "Waylay"}
_AGENT_IDS = {k.lower(): v for k, v in AGENT_IDS.items()}

MAP_IDS = {"Infinity": "Abyss", "Triad": "Haven", "Duality": "Bind", "Bonsai": "Split", "Ascent": "Ascent",
           "Port": "Icebox", "Foxtrot": "Breeze", "Canyon": "Fracture", "Pitt": "Pearl", "Jam": "Lotus",
           "Juliett": "Sunset", "Rook": "Corrode", "Range": "Range", "HURM_Alley": "District",
           "HURM_Yard": "Piazza", "HURM_Bowl": "Kasbah", "HURM_Helix": "Drift", "HURM_HighTide": "Glitch"}

WEAPON_IDS = {"Pistol_Classic": "Classic", "Pistol_Slim": "Shorty", "Pistol_AutoPistol": "Frenzy",
              "Pistol_Luger": "Ghost", "Pistol_Sheriff": "Sheriff", "Shotguns_Pump": "Bucky",
              "Shotguns_Persuader": "Judge", "SMGs_Vector": "Stinger", "SMGs_Ninja": "Spectre",
              "Rifles_Burst": "Bulldog", "Rifles_DMR": "Guardian", "Rifles_Ghost": "Phantom",
              "Rifles_Volcano": "Vandal", "Sniper_Bolt": "Marshal", "Sniper_Operater": "Operator",
              "Sniper_DoubleSniper": "Outlaw", "LMG": "Ares", "HMG": "Odin", "knife": "Knife"}

PHASES = {"shopping": "buy", "combat": "combat", "end": "end", "game_end": "end"}
SHIELDS = {0: (0, False), 1: (25, False), 2: (50, False), 4: (25, True)}   # 3: an enemy's (unknown)
HALF = {"bomb": 12, "swift": 4, "quick bomb": 3}   # rounds a side, by game mode

# What Overwolf can own: a key it gave stops the screen's reading of it.
PLAYER_KEYS = ("name", "agent", "alive", "kills", "deaths", "assists", "credits", "weapon", "shield",
               "regen_shield", "ult_points", "ult_max", "spike")


def _decoded(value):
    if isinstance(value, str) and value[:1] in "{[":
        try:
            return json.loads(value)
        except ValueError:
            # (ui_team_order_* have unquoted keys)
            try:
                return json.loads(re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', value))
            except ValueError:
                return value
    return value


def agent(text):
    """Our agent name from Overwolf's (display name or internal id)."""
    t = str(text or "").strip()
    t = re.sub(r"_PC_C$", "", re.sub(r"^TX_Killfeed_", "", t))
    t = re.sub(r"\d+$", "", t)
    name = _AGENT_IDS.get(t.lower()) or game.agent_name(t)
    return name if name in game.AGENTS else ""


def weapon(code):
    t = re.sub(r"^TX_Hud_", "", str(code or "").strip())
    name = WEAPON_IDS.get(t) or game.weapon_name(t.split("_")[-1])
    return name if name in game.WEAPONS or name == "Knife" else ""


def map_name(code):
    return MAP_IDS.get(str(code or "").strip(), "")


def riot_name(text):
    """"Name #TAG" -> "Name" (the HUD and the screen show names without tags)."""
    return str(text or "").split("#")[0].strip()


def _int(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _bool(v):
    return v is True or str(v).lower() in ("true", "1")


class Overwolf:
    def __init__(self, config, log=None):
        self.config = config
        self.log = log or (lambda *a, **k: None)
        self._lock = threading.Lock()
        self.info = {}            # feature -> key -> decoded value
        self.heard_at = 0.0
        self.running = False
        self.features = []
        self.messages = 0
        self.screen_agents = {}   # (side, slot) -> agent, as the screen reader sees the top bar
        self.seats = {}           # player key -> (side, slot)
        self.rounds, self.rounds_whole = [], True
        self._score = None        # (team_0, team_1) last seen
        self._round_end = ""      # "detonated" / "defused" this round
        self._spike_event = ""    # sent once with the next update
        self._disagree_since = 0.0
        self._was_live = None
        self._select_active = False
        self.owned = ({}, set())  # ({seat: {keys}}, {match keys}) the last update gave

    # --- receiving ------------------------------------------------------------

    def receive(self, msg):
        """Take one message from the app. Returns (update for game.merge or
        None, agent select reading or None)."""
        if not isinstance(msg, dict):
            raise ValueError("Expected an object")
        with self._lock:
            self.heard_at, self.messages = time.time(), self.messages + 1
            beat = msg.get("heartbeat")
            if isinstance(beat, dict):
                self.running = _bool(beat.get("running"))
                self.features = [str(f) for f in beat.get("features") or []][:20]
            info = msg.get("info")
            if isinstance(info, dict):
                for feature, keys in info.items():
                    if isinstance(keys, dict):
                        target = self.info.setdefault(str(feature), {})
                        for k, v in keys.items():
                            target[str(k)] = _decoded(v)
            for e in msg.get("events") or []:
                if isinstance(e, dict):
                    self._event(str(e.get("name") or ""), e.get("data"))
            self._track_score()
            self._check_live()
            if not self.live():
                return None, None
            select = self._select()
            # (in agent select the scoreboard is still last game's)
            return (None if self._select_active else self._update()), select

    def _event(self, name, data):
        if name == "match_start":
            self._new_match()
        elif name in ("spike_defused", "spike_detonated"):
            self._round_end = self._spike_event = name.split("_")[1]

    def _new_match(self):
        self.seats, self.rounds, self.rounds_whole = {}, [], True
        self._score, self._round_end = None, ""

    # --- liveness ---------------------------------------------------------------

    def live(self):
        return (self.running and time.time() - self.heard_at < LIVE_FOR
                and not (self._disagree_since and time.time() - self._disagree_since > DISAGREE_FOR))

    def _check_live(self):
        now = self.live()
        if now != self._was_live and self._was_live is not None:
            self.log("Overwolf is live: the HUD's game info comes from it (health from the screen)" if now else
                     "Overwolf stopped: the screen reader reads everything again", "info" if now else "warn")
        self._was_live = now

    def status(self):
        with self._lock:
            self._check_live()
            age = round(time.time() - self.heard_at, 1) if self.heard_at else None
            players = len(self._scoreboard())
            if not self.heard_at:
                text = "Overwolf: not heard from. The screen reader reads everything"
            elif age >= LIVE_FOR:
                text = f"Overwolf: nothing for {int(age)} s. The screen reader reads everything"
            elif not self.running:
                text = "Overwolf: connected, VALORANT isn't running"
            elif not self.live():
                text = "Overwolf: its score disagrees with the screen. The screen reader reads everything"
            elif self._select_active:
                text = "Overwolf: live (agent select)"
            elif players:
                text = f"Overwolf: live, {players} players. Health from the screen"
            else:
                text = "Overwolf: live, but it has no scoreboard. The screen reader fills in"
            return {"live": self.live(), "age": age, "running": self.running, "players": players,
                    "messages": self.messages, "features": self.features, "status": text}

    # --- the screen reader ------------------------------------------------------

    def screen(self, update):
        """A screen reading, with what Overwolf owns taken out (while it's live)."""
        with self._lock:
            for p in update.get("players") or []:
                if isinstance(p, dict) and p.get("agent") and p.get("team") in game.SIDES:
                    self.screen_agents[(p["team"], p.get("slot"))] = game.agent_name(p["agent"])
            m = update.get("match") or {}
            score = m.get("score")
            mine = self._sides_score()
            if isinstance(score, dict) and mine and {"left", "right"} <= set(score):
                if (score["left"], score["right"]) != mine:
                    self._disagree_since = self._disagree_since or time.time()
                elif self._disagree_since:
                    self._disagree_since = 0.0
            self._check_live()
            if not self.live():
                return update
            seats, match_keys = self.owned
            out = dict(update)
            if isinstance(update.get("match"), dict):
                out["match"] = {k: v for k, v in update["match"].items() if k not in match_keys}
                spike = update["match"].get("spike")
                if "spike" in match_keys and isinstance(spike, dict) and spike.get("state") == "planted":
                    out["match"]["spike"] = {"state": "planted"}   # (only the screen sees a plant)
            players = []
            for p in update.get("players") or []:
                if not isinstance(p, dict):
                    continue
                keys = seats.get((p.get("team"), p.get("slot"))) or {}
                q = {k: v for k, v in p.items() if k not in keys}
                if "alive" in keys:
                    if keys["alive"] is False:
                        q["health"] = 0
                    elif "health" in q and q["health"] <= 0:
                        q.pop("health")   # Overwolf says alive: a missed bar isn't a death
                    q["alive"] = keys["alive"]
                players.append(q)
            if "players" in update:
                out["players"] = players
            return out

    def screen_select(self):
        """True while Overwolf has agent select (the screen's reading is dropped)."""
        with self._lock:
            return self.live() and self._select_active

    def observing(self):
        """Name of the player the observer is watching (custom games), or ""."""
        with self._lock:
            if not self.live():
                return ""
            return riot_name((self.info.get("match_info") or {}).get("observing"))

    # --- building the HUD's update ------------------------------------------------

    def _scoreboard(self):
        mi = self.info.get("match_info") or {}
        rows = []
        for k, v in mi.items():
            n = _int(k[len("scoreboard_"):]) if k.startswith("scoreboard_") else None
            if n is not None and isinstance(v, dict) and (v.get("name") or v.get("character")):
                rows.append((n, v))
        return [v for _, v in sorted(rows, key=lambda r: r[0])]

    def _team_sides(self, by_team):
        """{0: side, 1: side}. Team 0 starts on attack; which HUD side it is
        comes from the agents the screen reader sees on each side of the top
        bar, else from who attacks first in the control panel."""
        votes = 0
        for team, agents in by_team.items():
            for side in game.SIDES:
                seen = {a for (s, _), a in self.screen_agents.items() if s == side and a}
                n = len(seen & agents)
                votes += n if (team == 0) == (side == "left") else -n
        if votes:
            first = "left" if votes > 0 else "right"
        else:
            first = self.config.get().get("attack_first") or "left"
        return {0: first, 1: "right" if first == "left" else "left"}

    def _place(self, rows):
        """(side, slot) for each scoreboard row: by agent where the screen
        reader knows the top bar's seats, else in Overwolf's order."""
        size = 2 if self.config.get().get("team_size") == 2 else 5
        sides = self._team_sides(self._by_team(rows))
        placed, taken = {}, set()
        keyed = [((r.get("player_id") or r.get("name") or str(i)), r) for i, r in enumerate(rows)]
        for key, r in keyed:   # by agent on the top bar
            t = _int(r.get("team"))
            if t not in sides:
                continue
            side, a = sides[t], agent(r.get("character"))
            slot = next((s for (sd, s), sa in self.screen_agents.items() if sd == side and sa == a and a), None)
            if slot and 1 <= slot <= size and (side, slot) not in taken:
                placed[key] = (side, slot)
                taken.add((side, slot))
        for key, r in keyed:   # the rest: their seat from before, else the first free one
            t = _int(r.get("team"))
            if key in placed or t not in sides:
                continue
            side, before = sides[t], self.seats.get(key)
            if before and before[0] == side and before not in taken and before[1] <= size:
                seat = before
            else:
                seat = next(((side, s) for s in range(1, size + 1) if (side, s) not in taken), None)
            if seat:
                placed[key] = seat
                taken.add(seat)
        self.seats = placed
        return [(placed[key], r) for key, r in keyed if key in placed], sides

    def _team_score(self):
        s = (self.info.get("match_info") or {}).get("match_score")
        if isinstance(s, dict) and "team_0" in s and "team_1" in s:
            return _int(s["team_0"], 0), _int(s["team_1"], 0)
        return None

    def _by_team(self, rows):
        by_team = {}
        for r in rows:
            t = _int(r.get("team"))
            if t in (0, 1):
                by_team.setdefault(t, set()).add(agent(r.get("character")))
        return by_team

    def _sides_score(self):
        """Overwolf's score as (left, right), or None."""
        score, rows = self._team_score(), self._scoreboard()
        if not score or not rows:
            return None
        sides = self._team_sides(self._by_team(rows))
        by = {sides[0]: score[0], sides[1]: score[1]}
        return by["left"], by["right"]

    def _attacking_team(self, rnd):
        """0 or 1, the team attacking in round `rnd`, or None for modes we don't know."""
        mode = (self.info.get("match_info") or {}).get("game_mode")
        mode = str(mode.get("mode") if isinstance(mode, dict) else mode or "bomb").lower()
        half = HALF.get(mode)
        if not half or not rnd:
            return None
        if rnd <= 2 * half:
            return 0 if rnd <= half else 1
        return (rnd - 2 * half - 1) % 2   # overtime: sides swap every round, team 0 first

    def _track_score(self):
        """Round history: a round goes on it each time one team's score goes up one."""
        score = self._team_score()
        if score is None or score == self._score:
            return
        old, self._score = self._score, score
        if score == (0, 0):
            self.rounds, self.rounds_whole = [], True
            return
        if old is None:
            self.rounds_whole = False   # joined mid-match: the history before is unknown
            return
        up = [t for t in (0, 1) if score[t] == old[t] + 1]
        if len(up) != 1 or score[1 - up[0]] != old[1 - up[0]]:
            self.rounds_whole = False
            return
        winner = up[0]
        attackers = self._attacking_team(sum(old) + 1)
        rows = self._scoreboard()
        losers_dead = rows and all(not _bool(r.get("alive")) for r in rows if _int(r.get("team")) == 1 - winner)
        if self._round_end == "detonated":
            how = "Detonation"
        elif self._round_end == "defused":
            how = "Deactivation"
        elif losers_dead or attackers is None or winner == attackers:
            how = "Elimination"
        else:
            how = "Time"
        self.rounds.append({"team": winner, "win_type": how})
        self._round_end = ""

    def _update(self):
        mi = self.info.get("match_info") or {}
        out = {"source": "overwolf", "match": {}, "players": []}
        seats_owned = {}
        placed, sides = self._place(self._scoreboard())
        for (side, slot), r in placed:
            p = {"team": side, "slot": slot}
            name, a = riot_name(r.get("name")), agent(r.get("character"))
            if a:
                p["agent"] = a
            if name and name.lower() not in (a.lower(), "me"):   # (a hidden name shows as the agent)
                p["name"] = name
            if "alive" in r:
                p["alive"] = _bool(r["alive"])
            for src, dst in (("kills", "kills"), ("deaths", "deaths"), ("assists", "assists"), ("money", "credits"),
                             ("ult_points", "ult_points"), ("ult_max", "ult_max")):
                if _int(r.get(src)) is not None:
                    p[dst] = _int(r[src])
            w = weapon(r.get("weapon"))
            if w:
                p["weapon"] = w
            shield = _int(r.get("shield"))
            if shield in SHIELDS:
                p["shield"], p["regen_shield"] = SHIELDS[shield]
            if "spike" in r:
                p["spike"] = _bool(r["spike"])
            if p.get("alive") is False:
                p["health"] = 0
            out["players"].append(p)
            seats_owned[(side, slot)] = {k: p[k] for k in PLAYER_KEYS if k in p}
        m = out["match"]
        rnd = _int(mi.get("round_number"))
        if rnd:
            m["round"] = rnd
        phase = PHASES.get(str(mi.get("round_phase") or ""))
        if phase:
            m["phase"] = phase
        mp = map_name(mi.get("map"))
        if mp and mp != "Range":
            m["map"] = mp
        score = self._team_score()
        if score:
            m["score"] = {sides[0]: score[0], sides[1]: score[1]}
            if self.rounds_whole and len(self.rounds) == sum(score):
                m["rounds"] = [{"winner": sides[r["team"]], "win_type": r["win_type"]} for r in self.rounds]
            if phase == "end" and self.rounds and self.rounds_whole:
                m["round_winner"], m["win_type"] = sides[self.rounds[-1]["team"]], self.rounds[-1]["win_type"]
        if rnd:
            att = self._attacking_team(rnd)
            if att is not None and placed:
                m["attackers"] = sides[att]
        carrier = next(((p["team"], p["slot"]) for p in out["players"] if p.get("spike")), None)
        if carrier:
            m["spike"] = {"state": "carried", "carrier": list(carrier)}
        elif self._spike_event:
            m["spike"] = {"state": self._spike_event, "carrier": None}
        self._spike_event = ""
        if phase == "buy":
            self._round_end = ""
        self.owned = (seats_owned, {k for k in m if k not in ("round_winner", "win_type")})
        if not out["players"]:
            del out["players"]
        return out if (m or out.get("players")) else None

    def _select(self):
        """Agent select from Overwolf's roster while the game's on that screen."""
        gi = self.info.get("game_info") or {}
        scene = str(gi.get("scene") or "")
        if scene != SELECT_SCENE:
            if self._select_active and scene:
                self._select_active = False
                return {"active": False}
            return None
        if not self._select_active:
            self._new_match()
        self._select_active = True
        mi = self.info.get("match_info") or {}
        rows = []
        for k, v in mi.items():
            n = _int(k[len("roster_"):]) if k.startswith("roster_") else None
            if n is not None and isinstance(v, dict) and (v.get("name") or v.get("character") or v.get("player_id")):
                rows.append((n, v))
        rows.sort(key=lambda r: r[0])
        teams = {str(r.get("player_id") or ""): _int(r.get("team")) for r in self._scoreboard()}
        sides = self._team_sides({})
        size = 2 if self.config.get().get("team_size") == 2 else 5
        slots, players = {0: 0, 1: 0}, []
        for i, (n, r) in enumerate(rows):
            team = teams.get(str(r.get("player_id") or ""))
            if team not in (0, 1):
                team = _int(r.get("team"))
            if team not in (0, 1):
                team = 0 if i < len(rows) / 2 else 1   # (unconfirmed: the first half is team 0)
            slots[team] += 1
            if slots[team] > size:
                continue
            a, name = agent(r.get("character")), riot_name(r.get("name"))
            p = {"team": sides[team], "slot": slots[team], "agent": a, "locked": _bool(r.get("locked")) and bool(a)}
            if name and name.lower() not in (a.lower(), "me"):
                p["name"] = name
            players.append(p)
        reading = {"active": True, "players": players}
        mp = map_name(mi.get("map"))
        if mp and mp != "Range":
            reading["map"] = mp
        return reading
