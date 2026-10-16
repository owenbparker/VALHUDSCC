"""Agent select: the map and each player's agent, hovered or locked in, for
the agent select overlay (/agent-select).

It comes from the observer's agent select screen (the screen reader sends
{"agent_select": {...}} to /api/ingest), the demo, or the control panel. A
reading looks like

    {"active": bool, "map": "Ascent", "timer": seconds left,
     "players": [{"team": "left", "slot": 1, "agent": "Jett", "locked": bool}, ...]}

and is merged into what's known (a partial reading only changes what it has).
"""

import random
import re
import threading
import time

from .game import AGENTS, SIDES, agent_name

MAPS = ["Abyss", "Ascent", "Bind", "Breeze", "Corrode", "Fracture", "Haven", "Icebox", "Lotus", "Pearl",
        "Split", "Sunset"]
STALE_AFTER = 10.0   # a screen reading counts for this long (it's sent every second or so)


def map_name(text):
    """"ASCENT", "Map - Ascent", "ascent" -> "Ascent"; "" when it isn't a map."""
    words = re.findall(r"[a-z]+", str(text or "").lower())
    for m in MAPS:
        if m.lower() in words:
            return m
    return ""


def empty():
    return {"active": False, "map": "", "timer": 0, "timer_at": 0.0,
            "players": {side: [{"agent": "", "locked": False} for _ in range(5)] for side in SIDES}}


class AgentSelect:
    def __init__(self):
        self.state = empty()
        self.source = ""
        self.updated_at = 0.0
        self._lock = threading.Lock()

    def apply(self, reading, source=""):
        """Merge a reading. Returns the map read, if it's a new one."""
        if not isinstance(reading, dict):
            raise ValueError("Expected an object")
        new_map = ""
        with self._lock:
            s = self.state
            if "active" in reading:
                if reading["active"] and not s["active"]:
                    # A new agent select: start from empty slots.
                    s["players"] = empty()["players"]
                s["active"] = bool(reading["active"])
            if reading.get("map") is not None:
                m = map_name(reading["map"])
                if m and m != s["map"]:
                    new_map = m
                s["map"] = m or s["map"] if reading["map"] else ""
            if reading.get("timer") is not None:
                s["timer"] = max(0.0, float(reading["timer"]))
                s["timer_at"] = time.time()
            for p in reading.get("players") or []:
                team, slot = p.get("team"), p.get("slot")
                if team not in SIDES or not isinstance(slot, int) or not 1 <= slot <= 5:
                    continue
                target = s["players"][team][slot - 1]
                if "agent" in p:
                    a = agent_name(p["agent"]) if p["agent"] else ""
                    target["agent"] = a if a in AGENTS else ""
                if "locked" in p:
                    target["locked"] = bool(p["locked"]) and bool(target["agent"])
            self.source = source or self.source
            self.updated_at = time.time()
        return new_map

    def clear(self):
        with self._lock:
            self.state = empty()
            self.updated_at = time.time()

    def view(self, players):
        """What the overlay draws: the state with each player's name, and the
        timer counted down to now. players: the HUD's players (for names)."""
        with self._lock:
            s = {"active": self.state["active"], "map": self.state["map"],
                 "players": {side: [dict(p) for p in self.state["players"][side]] for side in SIDES}}
            timer, at = self.state["timer"], self.state["timer_at"]
            # A screen reading that has stopped coming: agent select is over.
            if self.source == "screen" and time.time() - self.updated_at > STALE_AFTER:
                s["active"] = False
        s["timer"] = max(0, int(timer - (time.time() - at) + 0.999)) if at else 0
        names = {(p["team"], p["slot"]): p.get("name") or "" for p in players}
        for side in SIDES:
            for i, p in enumerate(s["players"][side]):
                p["name"] = names.get((side, i + 1), "")
        s["source"] = self.source
        return s


class AgentSelectDemo:
    """A made-up agent select: players hover an agent or two, then lock in,
    over about a minute."""

    def __init__(self, select, map_name="Ascent", speed=1.0, seed=None):
        self.select, self.map, self.speed = select, map_name, speed
        self.rng = random.Random(seed)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()

    def running(self):
        return self._thread.is_alive()

    def _wait(self, seconds):
        return self._stop.wait(seconds / self.speed)

    def _run(self):
        rng, sel = self.rng, self.select
        total = 75
        sel.apply({"active": True, "map": self.map, "timer": total}, "demo")
        start = time.time()
        order = [(side, slot) for side in SIDES for slot in range(1, 6)]
        rng.shuffle(order)
        taken = {side: set() for side in SIDES}
        for side, slot in order:
            pool = [a for a in AGENTS if a not in taken[side]]
            for _ in range(rng.randint(1, 3)):       # a hover or two before choosing
                sel.apply({"players": [{"team": side, "slot": slot, "agent": rng.choice(pool), "locked": False}],
                           "timer": total - (time.time() - start) * self.speed}, "demo")
                if self._wait(rng.uniform(1.2, 2.5)):
                    return
            pick = rng.choice(pool)
            taken[side].add(pick)
            sel.apply({"players": [{"team": side, "slot": slot, "agent": pick, "locked": True}]}, "demo")
            if self._wait(rng.uniform(0.8, 2.0)):
                return
        # Everyone's in: the screen holds a moment, then the match loads.
        sel.apply({"timer": 8}, "demo")
        if self._wait(8):
            return
        sel.apply({"active": False}, "demo")
