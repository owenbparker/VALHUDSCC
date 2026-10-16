"""Reads agent select off the observer's VALORANT screen.

The observer's agent select screen (a custom game) shows, on a 1920x1080
frame:

  - DEFENDERS (teal, left) and ATTACKERS (red, right) across the top, the
    phase timer between them;
  - the map's loading art in the middle, with its name;
  - five cards a side: the agent's bust portrait (once a player hovers or
    locks one) above a bar with the player's name. The name is white while
    the player is hovering and turns the team's colour once locked in.

Agents are told by comparing each card with the agents' bust icons, placed
exactly as the game draws them (web/reader_refs/select/agents); the map by
comparing the middle with each map's loading art as the game crops it
(web/reader_refs/select/maps). The timer and names are read with Windows'
text recognition, like the rest of the screen reader.

A reading is {"active", "map", "timer", "players": [{"team", "slot",
"agent", "locked", "name"}]} with team "defenders" / "attackers" (the app
works out which of its teams that is).
"""

import os

from .config import WEB_DIR
from .reader import Frame, _label, _line, _np, number

REFS = os.path.join(WEB_DIR, "reader_refs", "select")
SIDES = ("defenders", "attackers")

# A card's bust portrait: the agent's icon at 220px, its top-left at
# (50, 154) for the first defender, every 160px down; mirrored for the
# attackers, at x 1650. Only rows 204-322 show (the rest is under the
# header or the name bar).
ICON = 220
ICON_X = {"defenders": 50, "attackers": 1650}
ICON_Y0, ROW_STEP = 154, 160
SHOWN = (204 - ICON_Y0, 322 - ICON_Y0)
NAME_Y = 339                      # middle of the first name bar
NAME_X = {"defenders": (84, 392), "attackers": (1526, 1838)}   # after / before the role icon
MAP_BOX = (490, 224, 1430, 944)   # the map art
MAP_TEXT = (230, 200, 710, 470)   # its name, within MAP_BOX (left out when comparing)
MAP_K = 4                         # map art compared at 1/4 scale
TIMER_BOX = (880, 40, 1040, 116)

AGENT_MIN, AGENT_MARGIN = 0.52, 0.1   # a portrait must match this well, and clearly better than the next
# (a hovered portrait fades in: ~0.6 at its faintest; empty cards stay under 0.47)
MAP_MIN, MAP_MARGIN = 0.6, 0.2


def _mean(frame, box):
    np = _np()
    return np.asarray(frame.crop(*box), dtype=np.float32).reshape(-1, 3).mean(axis=0)


def on_screen(frame):
    """Is this the agent select screen? (DEFENDERS teal and ATTACKERS red
    across the top, the timer's light grey box between.)"""
    r1, g1, _ = _mean(frame, (320, 20, 520, 60))
    r2, g2, _ = _mean(frame, (1420, 20, 1620, 60))
    mid = _mean(frame, (890, 45, 1030, 105))
    return g1 > 75 and g1 - r1 > 20 and r2 > 75 and r2 - g2 > 25 and mid.min() > 140 and mid.max() - mid.min() < 25


# --- agents -------------------------------------------------------------------

_agent_refs = {}


def _agents(side):
    """{agent: (rgb, mask)} of the visible part of each bust, as drawn on
    this side (the attackers' are mirrored)."""
    if side not in _agent_refs:
        np = _np()
        from PIL import Image, ImageOps
        refs = {}
        folder = os.path.join(REFS, "agents")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".png"):
                continue
            img = Image.open(os.path.join(folder, name)).convert("RGBA")
            if img.size != (ICON, ICON):
                img = img.resize((ICON, ICON), Image.LANCZOS)
            if side == "attackers":
                img = ImageOps.mirror(img)
            a = np.asarray(img, dtype=np.float32)[SHOWN[0]:SHOWN[1]]
            mask = a[..., 3] > 230
            if mask.sum() >= 500:
                refs[name[:-4]] = (a[..., :3][mask], mask)
        _agent_refs[side] = refs
    return _agent_refs[side]


def _ncc(a, b):
    np = _np()
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def card_agent(frame, side, row):
    """The agent on a card, or "" (an empty card). Matched by shape and
    shading, so a portrait faded in while hovering still counts."""
    np = _np()
    x, y = ICON_X[side], ICON_Y0 + ROW_STEP * row
    card = np.asarray(frame.crop(x, y + SHOWN[0], x + ICON, y + SHOWN[1]), dtype=np.float32)
    scores = sorted(((_ncc(card[mask].ravel(), rgb.ravel()), agent)
                     for agent, (rgb, mask) in _agents(side).items()), reverse=True)
    if not scores:
        return ""
    (best, agent), runner_up = scores[0], scores[1][0] if len(scores) > 1 else 0.0
    return agent if best >= AGENT_MIN and best - runner_up >= AGENT_MARGIN else ""


def card_locked(frame, side, row):
    """Locked in: the name is in the team's colour (white while hovering)."""
    np = _np()
    x0, x1 = NAME_X[side]
    y = NAME_Y + ROW_STEP * row
    px = np.asarray(frame.crop(x0, y - 8, x1, y + 8), dtype=np.int32).reshape(-1, 3)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    white = int((px.min(axis=1) > 200).sum())
    if side == "defenders":
        tinted = int(((g > 170) & (b > 140) & (r < 150) & (g - r > 70)).sum())
    else:
        tinted = int(((r > 170) & (g < 140) & (b < 140) & (r - g > 60)).sum())
    return tinted >= 15 and tinted > white


# --- the map ------------------------------------------------------------------

_map_refs = None


def _maps():
    global _map_refs
    if _map_refs is None:
        np = _np()
        from PIL import Image
        folder = os.path.join(REFS, "maps")
        _map_refs = {name[:-4]: np.asarray(Image.open(os.path.join(folder, name)).convert("L"), dtype=np.float32)
                     for name in sorted(os.listdir(folder)) if name.endswith(".png")}
    return _map_refs


def read_map(frame):
    """The map in the middle, or "" (compared with each map's art, the name
    across it left out)."""
    np = _np()
    from PIL import Image
    x0, y0, x1, y1 = MAP_BOX
    size = ((x1 - x0) // MAP_K, (y1 - y0) // MAP_K)
    art = np.asarray(frame.crop(x0, y0, x1, y1).convert("L").resize(size, Image.BILINEAR), dtype=np.float32)
    mask = np.ones(art.shape, bool)
    tx0, ty0, tx1, ty1 = (v // MAP_K for v in MAP_TEXT)
    mask[ty0:ty1, tx0:tx1] = False
    scores = sorted(((_ncc(art[mask], ref[mask]), name) for name, ref in _maps().items() if ref.shape == art.shape),
                    reverse=True)
    if not scores:
        return ""
    (best, name), runner_up = scores[0], scores[1][0] if len(scores) > 1 else 0.0
    return name if best >= MAP_MIN and best - runner_up >= MAP_MARGIN else ""


# --- text ---------------------------------------------------------------------

def _light_text(img, level=150):
    """Coloured or white text on a darker bar -> black on white, enlarged."""
    from PIL import Image
    np = _np()
    a = np.asarray(img.convert("RGB"), dtype=np.int32).max(axis=2)
    out = Image.fromarray(np.where(a >= level, 0, 255).astype("uint8"), "L")
    return out.resize((out.width * 3, out.height * 3), Image.LANCZOS)


def read_timer(frame, ocr):
    """The seconds left (white digits in the grey box), or None."""
    from .reader import _fit, ink
    crop = frame.crop(*TIMER_BOX)
    digits = _fit(ink(crop, 2, 235))
    line = _line([_label("time", 34), digits], 50)
    text = " ".join(t for t, _, _ in sorted(ocr.words(line), key=lambda w: w[1]))
    m = text.lower().split("time", 1)
    value = number(m[1]) if len(m) == 2 else None
    return value if value is not None and 0 <= value <= 120 else None


def read_name(frame, side, row, ocr):
    from .reader import player_name
    x0, x1 = NAME_X[side]
    y = NAME_Y + ROW_STEP * row
    words = ocr.words(_light_text(frame.crop(x0 - 26, y - 12, x1, y + 12)))
    return player_name(" ".join(t for t, _, _ in sorted(words, key=lambda w: w[1])))


# --- a whole frame ------------------------------------------------------------

def read(image, ocr=None, names=None):
    """The agent select reading for a frame, or None when it isn't agent
    select. names: {(side, row): name} already read (names don't change, so
    they're only read once)."""
    frame = image if isinstance(image, Frame) else Frame(image)
    if not on_screen(frame):
        return None
    names = names if names is not None else {}
    reading = {"active": True, "players": []}
    m = read_map(frame)
    if m:
        reading["map"] = m
    if ocr:
        t = read_timer(frame, ocr)
        if t is not None:
            reading["timer"] = t
    for side in SIDES:
        for row in range(5):
            agent = card_agent(frame, side, row)
            p = {"team": side, "slot": row + 1, "agent": agent, "locked": bool(agent) and card_locked(frame, side, row)}
            if ocr and not names.get((side, row)):
                try:
                    names[(side, row)] = read_name(frame, side, row, ocr)
                except Exception:
                    pass
            if names.get((side, row)):
                p["name"] = names[(side, row)]
            reading["players"].append(p)
    return reading
