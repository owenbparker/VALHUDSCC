"""The series, kept up to date from the match: the maps from Map Bans, who
won each map (and by what score), the series score, and when the HUD clears
after a map.

    - A map is won at 13 rounds with a lead of 2 (from 12-12 it's overtime,
      win by two). Its score and winner are kept on the map, and the
      winner's series score goes up.
    - A minute after a map's won the in-game HUD clears; the stats (sent to
      the GFX Engine) stay until the next map's agent select starts, which
      also makes the next map the current one.
    - Once the Map Bans picks (and decider) are in, they're the series' maps.
"""

import time

from . import game, mapbans

CLEAR_AFTER = 60.0   # seconds from a map's last round to the HUD clearing


def map_winner(score):
    """"left" / "right" once a map's won at this score, else None."""
    left, right = int(score.get("left") or 0), int(score.get("right") or 0)
    if max(left, right) >= 13 and abs(left - right) >= 2:
        return "left" if left > right else "right"
    return None


def maps_from_bans(cfg):
    """[{"name", "picked_by"}] for the series' maps, from the Map Bans page
    (Bo1: the decider; Bo3: Team A's pick, Team B's pick, the decider), or
    None until they're all chosen."""
    bo = int(cfg.get("best_of") or 3)
    if bo not in (1, 3):
        return None
    steps = mapbans.steps(cfg, f"bo{bo}")
    chosen = [s for s in steps if s["action"] in ("pick", "decider")]
    if not chosen or not all(s["map"] for s in chosen):
        return None
    return [{"name": s["map"], "picked_by": s["team"] if s["action"] == "pick" else ""} for s in chosen]


def wins_needed(cfg):
    return int(cfg.get("best_of") or 3) // 2 + 1


class Series:
    """Watches the live match (see HudApp.refresh) and moves the series on."""

    def __init__(self, config, log):
        self.config = config
        self.log = log
        self.won_at = 0.0          # when the current map was won (0: it hasn't been)
        self.cleared = False       # the in-game HUD is cleared (after a won map)
        self.stats = None          # the fields kept for the stats while cleared
        self._last_score = None
        self._bans = None
        self._round = None
        self._round_kills = {}     # (team, slot) -> kills at the start of the round

    # --- Map Bans -> maps -----------------------------------------------------

    def sync_maps(self):
        """Take the maps from Map Bans when they change there."""
        cfg = self.config.get()
        picked = maps_from_bans(cfg)
        key = repr(picked)
        if key == self._bans:
            return
        first = self._bans is None
        self._bans = key
        if not picked:
            return
        maps = [dict(m) for m in cfg.get("maps") or []]
        names = [m.get("name") for m in maps[:len(picked)]]
        pickers = [m.get("picked_by", "") for m in maps[:len(picked)]]
        if names == [p["name"] for p in picked] and pickers == [p["picked_by"] for p in picked]:
            return
        if first and all(m.get("winner") for m in maps[:1]):
            return   # (a series already under way when the app started: left alone)
        out = []
        for i, p in enumerate(picked):
            old = maps[i] if i < len(maps) else {}
            keep = old.get("name") == p["name"]
            out.append({"name": p["name"], "picked_by": p["picked_by"],
                        "winner": old.get("winner", "") if keep else "",
                        "score": old.get("score") if keep else None})
        self.config.update({"maps": out})
        self.log("Maps from Map Bans: " + ", ".join(p["name"] for p in picked))

    # --- the live match -------------------------------------------------------

    def round_kills(self, state):
        """Each player's kills this round, as "round_kills" (for the kill
        tag above the player cam)."""
        m = state["match"]
        key = (m.get("round"), m.get("phase") == "buy")
        if key != self._round:
            self._round = key
            self._round_kills = {(p["team"], p["slot"]): p["kills"] for p in state["players"]}
        for p in state["players"]:
            start = self._round_kills.get((p["team"], p["slot"]))
            if start is None or p["kills"] < start:
                self._round_kills[(p["team"], p["slot"])] = start = p["kills"]
            p["round_kills"] = max(0, p["kills"] - start) if m.get("phase") != "buy" else 0

    def watch(self, state, fields):
        """A live state: a won map is recorded. Returns the state to show
        (empty once the HUD's cleared)."""
        score = state["match"]["score"]
        now = (int(score.get("left") or 0), int(score.get("right") or 0))
        before, self._last_score = self._last_score, now
        winner = map_winner(score)
        # Only when the score got there a round at a time (one misread
        # score mustn't win a map).
        if winner and before and sum(now) == sum(before) + 1 and not map_winner(dict(zip(("left", "right"), before))):
            self._map_won(winner, now, fields)
        if not self.cleared and self.won_at and time.time() - self.won_at >= CLEAR_AFTER:
            self.cleared = True
            self.log("Map over a minute ago: the in-game HUD is cleared (stats kept until agent select)")
        if self.cleared:
            out = game.empty_state()
            out["connected"] = state["connected"]
            return out
        return state

    def _map_won(self, winner, score, fields):
        cfg = self.config.get()
        maps = [dict(m) for m in cfg.get("maps") or []]
        i = int(cfg.get("current_map") or 0)
        if not 0 <= i < len(maps) or maps[i].get("winner"):
            return
        maps[i]["winner"] = winner
        maps[i]["score"] = {"left": score[0], "right": score[1]}
        wins = min(wins_needed(cfg), int(cfg[winner].get("wins") or 0) + 1)
        self.config.update({"maps": maps, winner: {"wins": wins}})
        self.won_at = time.time()
        self.stats = dict(fields)
        self.log(f"Map {i + 1} ({maps[i].get('name') or '?'}) won by {cfg[winner]['tricode']} "
                 f"{score[0]}-{score[1]}: series {cfg['left']['tricode']} "
                 f"{wins if winner == 'left' else cfg['left'].get('wins', 0)}-"
                 f"{wins if winner == 'right' else cfg['right'].get('wins', 0)} {cfg['right']['tricode']}")

    def agent_select_started(self):
        """The next map's agent select: it's the current map now, and the
        last map's HUD and stats are done with. Returns True when the match
        data should start again from empty."""
        cfg = self.config.get()
        maps = cfg.get("maps") or []
        i = int(cfg.get("current_map") or 0)
        done = 0 <= i < len(maps) and bool(maps[i].get("winner"))
        if done and i + 1 < len(maps):
            self.config.update({"current_map": i + 1})
            self.log(f"Agent select: map {i + 2} ({maps[i + 1].get('name') or '?'}) is the current map")
        reset = done or self.cleared
        self.won_at, self.cleared, self.stats, self._last_score = 0.0, False, None, None
        return reset
