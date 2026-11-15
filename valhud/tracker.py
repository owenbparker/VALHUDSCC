"""The new VALORANT reader's brain (shadow mode for now).

The screen reader (reader.py) reads each frame on its own: the top bar's
health bars and agents, the score digits, the Tab scoreboard, the kill feed.
Today each of those readings is steadied by its own rule ("the same twice",
"five times running") and tracked by seat. This module keeps one picture of
the match instead and lets the game's rules decide what can change:

  - Players are people, not seats: the Riot Client's roster (account id,
    Riot ID, team, agent) is the list of players; agents are unique within a
    team, so an agent recognised on the top bar says exactly who it is.
  - Teams are Red and Blue (Red attacks first). Which one the top bar shows
    on the left is worked out once a map, from the agents on each side.
  - The score only moves the way VALORANT scores move: one round at a time,
    to one team, or back to 0-0 for a new map after agent select. Anything
    else (12-11 read as 1-1, 10 as 0) has to be read many times running, or
    agree with the round history on the Tab scoreboard, before it counts.

It runs beside today's reader: it gets the same readings (observe), and what
it would have shown is recorded with the match (kind "shadow") and compared
by python -m valhud.replay. It takes over once the replays show it's better.
"""

import time

TEAMS = ("Red", "Blue")
SIDES = ("left", "right")


def _norm(text):
    return "".join(ch for ch in str(text or "").lower() if ch.isalnum())


class ScoreKeeper:
    """The score, moved only the way the game moves it."""

    STEP_READS = 2         # a round won (one side +1): read the same this many times running
    NEW_MAP_READS = 2      # back to 0-0 after agent select
    ODD_READS = 12         # anything else (about six seconds of full reads)
    GAP = 90.0             # no score read this long (reader off, a menu): the next one starts afresh

    def __init__(self):
        self.score = None          # (left, right)
        self._pending, self._count = None, 0
        self.new_map = False       # agent select seen since the last score
        self.read_at = 0.0
        self.rejected = 0          # readings the rules turned away (for the report)

    def agent_select(self):
        self.new_map = True

    def offer(self, left, right, now=None, history=None, eliminated=None):
        """A score read off the top bar. history: (left wins, right wins)
        counted on the Tab scoreboard's round history, if open. eliminated:
        the side whose players are all dead now (that side lost the round).
        Returns the score now held."""
        now = time.time() if now is None else now
        cand = (int(left), int(right))
        if self.score is not None and now - self.read_at > self.GAP and not self.new_map:
            self.score = None   # (a long gap: whatever happened meanwhile, start again)
        self.read_at = now
        if cand == self.score:
            self._pending, self._count = None, 0
            return self.score
        if cand == self._pending:
            self._count += 1
        else:
            self._pending, self._count = cand, 1
        need = self._reads_needed(cand, history, eliminated)
        if self._count >= need:
            self.score, self._pending, self._count = cand, None, 0
            if cand == (0, 0):
                self.new_map = False
        else:
            self.rejected += 1 if self._count == 1 else 0
        return self.score

    def _reads_needed(self, cand, history, eliminated):
        if history is not None and tuple(history) == cand:
            return 1   # (the round history agrees: that's the score)
        if self.score is None:
            return self.STEP_READS
        l0, r0 = self.score
        l1, r1 = cand
        if cand == (0, 0) and self.new_map:
            return self.NEW_MAP_READS
        if (l1, r1) in ((l0 + 1, r0), (l0, r0 + 1)):
            winner = "left" if l1 > l0 else "right"
            if eliminated and eliminated != winner:
                return 1   # (the other side's all dead: this side won the round)
            return self.STEP_READS
        return self.ODD_READS


class SideKeeper:
    """Which team (Red / Blue) the top bar shows on each side, from the agents."""

    def __init__(self):
        self.left = None           # "Red" / "Blue" once known
        self._votes = {"Red": 0, "Blue": 0}

    def reset(self):
        self.left, self._votes = None, {"Red": 0, "Blue": 0}

    def observe(self, top_agents, roster):
        """top_agents: {(side, slot): agent}; roster: [{"team": "Red"/"Blue", "agent"}]."""
        if not roster:
            return self.left
        team_agents = {t: sorted(p["agent"] for p in roster if p.get("team") == t and p.get("agent")) for t in TEAMS}
        left = [a for (side, _), a in top_agents.items() if side == "left"]
        if not left:
            return self.left
        overlap = {t: sum(min(left.count(a), team_agents[t].count(a)) for a in set(left)) for t in TEAMS}
        if overlap["Red"] == overlap["Blue"]:
            return self.left   # (a mirror comp, or too little seen)
        best = max(TEAMS, key=lambda t: overlap[t])
        self._votes[best] += 1
        other = "Blue" if best == "Red" else "Red"
        if self._votes[best] >= 3 and self._votes[best] > 2 * self._votes[other]:
            self.left = best
        return self.left

    def team_of(self, side):
        if not self.left:
            return None
        return self.left if side == "left" else ("Blue" if self.left == "Red" else "Red")


class Tracker:
    """Shadow tracker: takes the screen reader's raw readings and the Riot
    Client's roster, keeps the match by the game's rules, and says what the
    HUD would show (view)."""

    def __init__(self):
        self.score = ScoreKeeper()
        self.sides = SideKeeper()
        self.roster = []           # [{"puuid", "name", "team": "Red"/"Blue", "agent"}]
        self.agents = {}           # (side, slot) -> agent, from the top bar
        self._agent_votes = {}
        self.names = {}            # (side, slot) -> name read off the scoreboard (steady)
        self._name_pending = {}

    # --- inputs --------------------------------------------------------------

    def agent_select(self):
        """Agent select is on: a new map (or a remake) follows."""
        self.score.agent_select()
        self.sides.reset()
        self.agents, self._agent_votes, self.names, self._name_pending = {}, {}, {}, {}

    def riot_roster(self, players):
        """[{"puuid", "name", "team": "Red"/"Blue", "agent"}] from the Riot Client."""
        self.roster = [dict(p) for p in players or [] if p.get("team") in TEAMS]

    def observe(self, update, now=None):
        """One full reading of a frame (reader.read_frame's update, before any
        steadying)."""
        now = time.time() if now is None else now
        m = update.get("match") or {}
        for side, slot, agent in update.get("seen_agents") or []:
            key = (side, slot)
            votes = self._agent_votes.setdefault(key, {})
            votes[agent] = votes.get(agent, 0) + 1
            if votes[agent] >= 3:
                self.agents[key] = agent
                self._agent_votes[key] = {}
        self.sides.observe(self.agents, self.roster)
        for p in update.get("players") or []:
            if p.get("name"):
                key = (p["team"], p["slot"])
                if self._name_pending.get(key) == p["name"]:
                    self.names[key] = p["name"]
                self._name_pending[key] = p["name"]
        s = m.get("score")
        if s and s.get("left") is not None and s.get("right") is not None:
            history = None
            rounds = m.get("rounds")
            if rounds:
                history = (sum(1 for r in rounds if (r or {}).get("winner") == "left"),
                           sum(1 for r in rounds if (r or {}).get("winner") == "right"))
                if sum(history) != s["left"] + s["right"]:
                    history = None
            self.score.offer(s["left"], s["right"], now, history, self._eliminated(update))

    @staticmethod
    def _eliminated(update):
        for side in SIDES:
            seats = [p for p in update.get("players") or [] if p.get("team") == side]
            if seats and all(p.get("alive") is False for p in seats):
                return side
        return None

    # --- what it would show ----------------------------------------------------

    def player_for(self, side, slot):
        """The roster player on that seat (by team and agent), or None."""
        team, agent = self.sides.team_of(side), self.agents.get((side, slot))
        if not team or not agent:
            return None
        match = [p for p in self.roster if p["team"] == team and p.get("agent") == agent]
        return match[0] if len(match) == 1 else None

    def view(self):
        """An update in the HUD's usual shape: the score and each seat's
        player (Riot ID first, then the steady scoreboard name)."""
        players = []
        for side in SIDES:
            for slot in range(1, 6):
                p = {"team": side, "slot": slot}
                if (side, slot) in self.agents:
                    p["agent"] = self.agents[(side, slot)]
                who = self.player_for(side, slot)
                if who and who.get("name"):
                    p["name"], p["puuid"] = who["name"], who.get("puuid")
                elif self.names.get((side, slot)):
                    p["name"] = self.names[(side, slot)]
                players.append(p)
        match = {}
        if self.score.score is not None:
            match["score"] = {"left": self.score.score[0], "right": self.score.score[1]}
        if self.sides.left:
            match["left_team"] = self.sides.left
        return {"source": "screen", "match": match, "players": players}
