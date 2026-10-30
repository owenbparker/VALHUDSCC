"""Settings for the VALORANT HUD, saved to config.json next to the project (or
next to ValorantHUD.exe in the desktop build).

Everything here can be changed from the control panel while the app runs.
"""

import copy
import json
import os
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = getattr(sys, "frozen", False)
# Read-only files shipped with the app (overlay, fonts, images). In the .exe
# build these are unpacked by PyInstaller.
RESOURCE_DIR = getattr(sys, "_MEIPASS", ROOT) if FROZEN else ROOT
# Things the app writes: settings, uploaded logos, output files.
DATA_DIR = os.path.dirname(os.path.abspath(sys.executable)) if FROZEN else ROOT
WEB_DIR = os.path.join(RESOURCE_DIR, "web")
LOGO_DIR = os.path.join(DATA_DIR, "logos")
SPONSOR_DIR = os.path.join(DATA_DIR, "sponsors")   # uploaded sponsor logos (served as sponsors/...)
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

DEFAULTS = {
    # A different port from the League HUD (8777), so both can run at once.
    "http_host": "127.0.0.1",
    "http_port": 8778,
    # Let other PCs on your network read the overlay and data (changes can
    # still only be made on this PC).
    "allow_network": False,
    "output_dir": "output",
    # Read the match off the VALORANT spectator screen on this PC.
    "screen_reader": False,
    # How long live data (from /api/ingest) counts as current, in seconds.
    "live_timeout": 10,

    "left": {"name": "Team Left", "tricode": "SCC", "logo": "assets/logos/scc.png", "wins": 0, "color": "#2fc7a6"},
    "right": {"name": "Team Right", "tricode": "OPP", "logo": "assets/logo_right.png", "wins": 0, "color": "#e3475a"},
    "best_of": 3,
    # Players a team: 5, or 2 for skirmish streams (two player tabs a side,
    # each with that player's 16:9 webcam under it).
    "team_size": 5,
    # The HUD's two side colours (the templates' teal and red); they still
    # swap at half time. See valhud/recolor.py.
    "defense_color": "#00ffcc",
    "attack_color": "#ff4e5d",
    # Which team attacks in the first half: "left" or "right".
    "attack_first": "left",
    # The maps of the series, in order; "winner" is "left", "right" or "".
    "maps": [{"name": "Ascent", "winner": ""}, {"name": "Bind", "winner": ""}, {"name": "Haven", "winner": ""}],
    "current_map": 0,
    "timeouts": {"left": 2, "right": 2},
    # A timeout card on screen: "", "left" or "right".
    "timeout_call": "",
    "tech_pause": False,
    # Player names to show, per team, in slot order (overrides the feed).
    "player_names": {"left": ["", "", "", "", ""], "right": ["", "", "", "", ""]},
    # Timeout diamonds under the score; keep the scoreboard overlay on screen.
    "show": {"timeouts": True, "scoreboard": False},
    # Player webcams (SCC Player Cam): the spectated player's cam pops up
    # above the bottom of the screen.
    "cams": {"enabled": True,
             # The name and K / D / A under the cam: a font installed on this
             # PC ("" = the HUD's own) and its size in pixels.
             "name_font": "", "name_size": 18, "kda_font": "", "kda_size": 18,
             # Cam links (VDO.Ninja view links etc.), each beside the player's
             # Riot ID, which finds them in the match: [{"riot_id", "link"}].
             "links": [],
             # Riot IDs whose cam (link or Player Cam) is hidden, e.g. not working.
             "hidden": []},
    # The agent select overlay (/agent-select): "pro" (the PRO Selector
    # template) or "champions" (in the Champions 2025 HUD's style).
    "agent_select": {"look": "pro"},
    # Map bans (see valhud/mapbans.py): the map pool (None: the current VCT
    # pool, as of this release), Team A (bans first) and each veto's steps.
    "map_bans": {"pool": None, "team_a": "left",
                 "bo1": {"steps": []}, "bo3": {"steps": []}},

    # Which screen the "HUD on the game" window covers (0 = main screen).
    "overlay_screen": 0,
    # Sponsor logos rotating in the top right of the HUD, in order (paths
    # like "sponsors/x.png"); empty: the template's own two. Seconds each.
    "sponsors": [],
    "sponsor_seconds": 4,
    # Observer client: the GFX PC whose HUD to show.
    "observer_url": "",
    # The SCC GFX Engine this HUD sends its game and series to (see valhud/enginelink.py).
    "gfx_engine": {"url": "", "name": "", "connected": False},
}

_lock = threading.Lock()


def _merge(base, extra):
    out = copy.deepcopy(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


class Config:
    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self.data = copy.deepcopy(DEFAULTS)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.data = _merge(DEFAULTS, json.load(f))

    def get(self):
        with _lock:
            return copy.deepcopy(self.data)

    def update(self, changes):
        with _lock:
            self.data = _merge(self.data, changes)
            snapshot = copy.deepcopy(self.data)
        self.save(snapshot)
        return snapshot

    def save(self, snapshot=None):
        snapshot = snapshot if snapshot is not None else self.get()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
        os.replace(tmp, self.path)

    def output_dir(self):
        out = self.get()["output_dir"]
        return out if os.path.isabs(out) else os.path.join(DATA_DIR, out)


def web_file(rel):
    """Path on disk for a URL path like "assets/logos/x.png", or None.

    Uploaded logos live in LOGO_DIR (served as assets/logos/...); everything
    else comes from WEB_DIR. Paths that try to climb out are refused.
    """
    rel = rel.replace("\\", "/").lstrip("/")
    candidates = []
    if rel.startswith("assets/logos/"):
        candidates.append((LOGO_DIR, rel[len("assets/logos/"):]))
    if rel.startswith("sponsors/"):
        candidates.append((SPONSOR_DIR, rel[len("sponsors/"):]))
    candidates.append((WEB_DIR, rel))
    # The scoreboard shares the HUD's agent, weapon and shield images.
    if rel.startswith("scoreboard/Resources/"):
        candidates.append((WEB_DIR, "hud/Resources/" + rel[len("scoreboard/Resources/"):]))
    # So does the agent select template, for maps and weapons.
    if rel.lower().startswith(("select/resources/maps/", "select/resources/armas/")):
        candidates.append((WEB_DIR, "hud/Resources/" + rel[len("select/Resources/"):]))
    for base, sub in candidates:
        path = os.path.normpath(os.path.join(base, sub))
        if not path.startswith(os.path.normpath(base) + os.sep):
            continue
        if os.path.isfile(path):
            return path
        # The HUD templates spell folders both "Resources" and "resources"
        # (fine on Windows); match case-insensitively everywhere.
        found = _find_nocase(base, sub)
        if found:
            return found
    return None


def _find_nocase(base, sub):
    path = os.path.normpath(base)
    for part in sub.split("/"):
        if not part or part in (".", ".."):
            return None
        try:
            names = os.listdir(path)
        except OSError:
            return None
        match = next((n for n in names if n.lower() == part.lower()), None)
        if match is None:
            return None
        path = os.path.join(path, match)
    return path if os.path.isfile(path) else None
