"""Map bans: the veto for a best of one and a best of three, in the official
VCT order, and what the map bans graphics (/map-bans?bo=1 or ?bo=3) show.

The control panel keeps it in config["map_bans"]:
    pool      the maps that can be banned or picked (any VALORANT map)
    team_a    "left" or "right": Team A, who bans first
    bo1, bo3  {"steps": [{"map", "side"} x 7]}: each step of that veto in
              order; "side" ("attack" / "defence") on the picks and the
              decider is the side the other team (or Team A, on the decider)
              starts on

Map art: a portrait made for the graphic (web/mapbans/maps), the map's splash
art (downloaded once from valorant-api.com, kept in maps/ next to the app),
or the HUD's own map picture.
"""

import json
import os
import threading
import time
import urllib.request

from .config import DATA_DIR, WEB_DIR
from .log import log

ALL_MAPS = ["Abyss", "Ascent", "Bind", "Breeze", "Corrode", "Fracture", "Haven", "Icebox", "Lotus", "Pearl",
            "Split", "Summit", "Sunset"]
# The VCT / Competitive pool since patch 13.08 (October 2026).
VCT_POOL = ["Abyss", "Bind", "Corrode", "Haven", "Lotus", "Summit", "Sunset"]

# The official VCT veto. ("ban" / "pick", whose turn); the last map left is the
# decider, and Team A picks its side. A picked map's side is picked by the
# other team.
ORDER = {
    "bo1": [("ban", "A"), ("ban", "B"), ("ban", "A"), ("ban", "B"), ("ban", "A"), ("ban", "B"), ("decider", None)],
    "bo3": [("ban", "A"), ("ban", "B"), ("pick", "A"), ("pick", "B"), ("ban", "A"), ("ban", "B"), ("decider", None)],
}

PORTRAIT_DIR = os.path.join(WEB_DIR, "mapbans", "maps")
SPLASH_DIR = os.path.join(DATA_DIR, "maps")
HUD_MAP_DIR = os.path.join(WEB_DIR, "hud", "Resources", "Maps")
API = "https://valorant-api.com/v1/maps"


def fmt(bo):
    return "bo1" if str(bo).lower().lstrip("bo") == "1" else "bo3"


def settings(cfg):
    mb = cfg.get("map_bans") or {}
    pool = [m for m in ALL_MAPS if m in (mb.get("pool") or VCT_POOL)]
    return pool, "right" if mb.get("team_a") == "right" else "left"


def steps(cfg, bo):
    """The veto's 7 steps, filled in: who, what, the map, and whose side pick.
    The decider is the one map left in the pool once the others are chosen
    (or the one set by hand)."""
    form = fmt(bo)
    pool, team_a = settings(cfg)
    team_b = "right" if team_a == "left" else "left"
    who = {"A": team_a, "B": team_b}
    saved = ((cfg.get("map_bans") or {}).get(form) or {}).get("steps") or []
    out = []
    for i, (action, turn) in enumerate(ORDER[form]):
        s = saved[i] if i < len(saved) and isinstance(saved[i], dict) else {}
        team = who[turn] if turn else None
        chooser = team_a if action == "decider" else (who["B" if turn == "A" else "A"] if action == "pick" else None)
        side = s.get("side") if s.get("side") in ("attack", "defence") else ""
        out.append({"n": i + 1, "action": action, "team": team, "map": s.get("map") if s.get("map") in ALL_MAPS else "",
                    "side_team": chooser, "side": side if chooser else ""})
    decider = out[-1]
    if not decider["map"]:
        left = [m for m in pool if m not in {s["map"] for s in out[:-1]}]
        if len(left) == 1:
            decider["map"] = left[0]
            decider["auto"] = True
    return out


def view(cfg, bo):
    """What the graphic shows."""
    form = fmt(bo)
    teams = {side: {"name": cfg[side]["name"], "tricode": cfg[side]["tricode"], "logo": cfg[side]["logo"],
                    "color": cfg[side]["color"]} for side in ("left", "right")}
    slots = steps(cfg, form)
    for s in slots:
        s["art"] = f"/map-art/{s['map']}" if s["map"] else ""
    return {"format": form, "teams": teams, "steps": slots, "team_a": settings(cfg)[1]}


# --- map art ------------------------------------------------------------------

class MapArt:
    """Finds each map's picture; fetches splash art it doesn't have, in the
    background, once."""

    def __init__(self, opener=None):
        self._opener = opener or urllib.request.build_opener()
        self._lock = threading.Lock()
        self._busy = False
        self._tried_at = 0

    def path(self, name):
        name = next((m for m in ALL_MAPS if m.lower() == str(name).lower()), None)
        if not name:
            return None
        self.fetch_missing()
        for folder, exts in ((PORTRAIT_DIR, (".png", ".jpg")), (SPLASH_DIR, (".png", ".jpg")), (HUD_MAP_DIR, (".png",))):
            for ext in exts:
                p = os.path.join(folder, name + ext)
                if os.path.isfile(p):
                    return p
        return None

    def missing(self):
        have = lambda folder, m: any(os.path.isfile(os.path.join(folder, m + e)) for e in (".png", ".jpg"))
        return [m for m in ALL_MAPS if not have(PORTRAIT_DIR, m) and not have(SPLASH_DIR, m)]

    def fetch_missing(self):
        """Downloads the splash art of the maps without a portrait (not more
        than once every 10 minutes; offline is fine, the HUD's pictures do)."""
        with self._lock:
            if self._busy or time.time() - self._tried_at < 600 or not self.missing():
                return
            self._busy, self._tried_at = True, time.time()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            with self._opener.open(API, timeout=10) as r:
                data = json.loads(r.read()).get("data") or []
            os.makedirs(SPLASH_DIR, exist_ok=True)
            got = []
            for m in self.missing():
                hit = next((d for d in data if str(d.get("displayName", "")).lower() == m.lower() and d.get("splash")), None)
                if not hit:
                    continue
                with self._opener.open(hit["splash"], timeout=20) as r:
                    blob = r.read()
                ext = ".jpg" if blob[:3] == b"\xff\xd8\xff" else ".png"
                tmp = os.path.join(SPLASH_DIR, m + ext + ".tmp")
                with open(tmp, "wb") as f:
                    f.write(blob)
                os.replace(tmp, os.path.join(SPLASH_DIR, m + ext))
                got.append(m)
            if got:
                log(f"Map bans: downloaded the art for {', '.join(got)}")
        except Exception as e:
            log(f"Map bans: couldn't download map art ({e}); using the HUD's own pictures", "warn")
        finally:
            with self._lock:
                self._busy = False
