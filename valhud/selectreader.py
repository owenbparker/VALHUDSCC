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
import time

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
#
# Where the cards sit can be a few pixels off the screenshots this was built
# from (another resolution or aspect, the game's own layout tweaks), and a
# portrait matched even 10px off reads as nothing. So the reader keeps a
# Layout (scale and offset of the card column) and, when a card plainly has
# a portrait on it but nothing matches, searches round it for where the
# portraits really are and keeps that for every card.

CONTENT_STD = 20          # a card's portrait area this busy has a portrait (empty cards ~11-16, a hover fading in 18+)
SEARCH = 2                # each card is matched within this many px of where the layout puts it
WIDE, WIDE_K = 96, 4      # the search for the layout: this far round a card, at 1/4 scale
WIDE_SCALES = (0.84, 0.88, 0.92, 0.96, 1.0, 1.04, 1.08, 1.12, 1.16, 1.2)
WIDE_MIN = 0.5            # a 1/4-scale match good enough to look at closely
CALIBRATE_EVERY = 5.0     # seconds between searches while cards stay unread
RECHECK = 2.0             # seconds between second looks at a name already read


class Layout:
    """The card column's scale and offset from where the 1080p screenshots
    had it: a point (x, y) is at (960 + (x - 960) * s + dx, 540 + (y - 540) *
    s + dy), dx mirrored for the attackers."""

    def __init__(self):
        self.s, self.dx, self.dy = 1.0, 0.0, 0.0
        self.searched_at = 0.0
        self.wait = CALIBRATE_EVERY   # longer after each search that finds nothing better (e.g. an agent with no icon here)

    def point(self, side, x, y):
        sign = 1 if side == "defenders" else -1
        return 960 + (x - 960) * self.s + self.dx * sign, 540 + (y - 540) * self.s + self.dy

    def icon(self, side, row):
        """The portrait's box (x0, y0, size) on screen, in 1080p coordinates."""
        size = ICON * self.s
        if side == "defenders":
            x0, y0 = self.point(side, ICON_X[side], ICON_Y0 + ROW_STEP * row)
        else:   # mirrored: the box's right edge is where the defenders' left is
            x1, y0 = self.point(side, ICON_X[side] + ICON, ICON_Y0 + ROW_STEP * row)
            x0 = x1 - size
        return x0, y0, size

    def found(self, side, row, x0, y0, size):
        """A card's portrait was found at this box: the layout that puts it there."""
        s = size / ICON
        sign = 1 if side == "defenders" else -1
        x = ICON_X[side] if side == "defenders" else ICON_X[side] + ICON
        xs = x0 if side == "defenders" else x0 + size
        self.s = s
        self.dx = (xs - (960 + (x - 960) * s)) * sign
        self.dy = y0 - (540 + (ICON_Y0 + ROW_STEP * row - 540) * s)


_banks = {}


def _bank(side, k=1):
    """Every agent's bust, as drawn on this side (the attackers' mirrored),
    at 1/k scale: (names, masks, masked refs, per-agent sums) laid out so a
    whole batch of card crops is scored against all agents at once."""
    key = (side, k)
    if key not in _banks:
        np = _np()
        from PIL import Image, ImageOps
        size = round(ICON / k)
        top, bottom = round(SHOWN[0] / k), round(SHOWN[1] / k)
        names, masks, refs = [], [], []
        folder = os.path.join(REFS, "agents")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".png"):
                continue
            img = Image.open(os.path.join(folder, name)).convert("RGBA")
            if img.size != (ICON, ICON):
                img = img.resize((ICON, ICON), Image.LANCZOS)
            if side == "attackers":
                img = ImageOps.mirror(img)
            full_mask = np.asarray(img, dtype=np.float32)[SHOWN[0]:SHOWN[1], :, 3] > 230
            if full_mask.sum() < 500:
                continue
            if k != 1:
                img = img.resize((size, size), Image.BILINEAR)
            a = np.asarray(img, dtype=np.float32)[top:bottom]
            mask = (a[..., 3] > 230).astype(np.float32)
            m3 = np.repeat(mask[..., None], 3, axis=2)
            names.append(name[:-4])
            masks.append(m3.ravel())
            refs.append((a[..., :3] * m3).ravel())
        W, R = np.array(masks), np.array(refs)
        n = W.sum(axis=1)
        sr = R.sum(axis=1)
        vr = (R * R).sum(axis=1) - sr * sr / n
        _banks[key] = (names, W, R, n, sr, vr, (bottom - top, size))
    return _banks[key]


def _scores(bank, crops):
    """NCC of each of N crops (N x P) against each agent: (A x N)."""
    np = _np()
    names, W, R, n, sr, vr, _ = bank
    C = crops.T
    sc = W @ C
    vc = W @ (C * C) - sc * sc / n[:, None]
    cov = R @ C - sc * sr[:, None] / n[:, None]
    d = np.sqrt(np.maximum(vc, 1e-6) * vr[:, None])
    return cov / d


def _windows(region, h, w, step=1):
    """Every h x w window of an image array (rows of N x P) and their offsets."""
    np = _np()
    v = np.lib.stride_tricks.sliding_window_view(region, (h, w, 3))[::step, ::step, 0]
    ny, nx = v.shape[:2]
    return v.reshape(ny * nx, -1), nx


def _best(scores):
    """(best score, agent index, window index, runner-up score)."""
    np = _np()
    i = int(np.argmax(scores.max(axis=0)))
    col = scores[:, i]
    order = np.argsort(col)[::-1]
    return float(col[order[0]]), int(order[0]), i, float(col[order[1]]) if len(order) > 1 else 0.0


def _match(frame, side, row, layout, search=SEARCH):
    """(agent or "", score) for a card, looked for within a few px of where
    the layout puts it."""
    np = _np()
    bank = _bank(side)
    h, w = bank[6]
    x0, y0, size = layout.icon(side, row)
    k = size / ICON                      # screen px (1080p) per template px
    m = search
    box = (x0 - m * k, y0 + (SHOWN[0] - m) * k, x0 + (ICON + m) * k, y0 + (SHOWN[1] + m) * k)
    region = np.asarray(frame.crop(*box, size=(w + 2 * m, h + 2 * m)), dtype=np.float32)
    crops, _ = _windows(region, h, w)
    best, a, _, runner_up = _best(_scores(bank, crops))
    agent = bank[0][a] if best >= AGENT_MIN and best - runner_up >= AGENT_MARGIN else ""
    return agent, best


def has_portrait(frame, side, row, layout):
    np = _np()
    x0, y0, size = layout.icon(side, row)
    k = size / ICON
    crop = frame.crop(x0, y0 + SHOWN[0] * k, x0 + size, y0 + SHOWN[1] * k, size=(ICON, SHOWN[1] - SHOWN[0]))
    return float(np.asarray(crop.convert("L"), dtype=np.float32).std()) >= CONTENT_STD


def find_card(frame, side, row, layout):
    """Search round a card that has a portrait no agent matched, for the
    scale and place its portrait really is at: its box (x0, y0, size) on
    screen in 1080p coordinates, or None."""
    np = _np()
    small = _bank(side, WIDE_K)
    h, w = small[6]
    x0, y0, size = layout.icon(side, row)
    best = None
    for f in WIDE_SCALES:
        s = size * f / ICON              # screen px per full template px, at this scale
        k = s * WIDE_K                   # screen px per 1/4 template px
        pad = WIDE / k
        box = (x0 - WIDE, y0 + SHOWN[0] * s - WIDE, x0 + ICON * s + WIDE, y0 + SHOWN[1] * s + WIDE)
        out = (round(w + 2 * pad), round(h + 2 * pad))
        region = np.asarray(frame.crop(*box, size=out), dtype=np.float32)
        crops, nx = _windows(region, h, w)
        score, a, i, runner_up = _best(_scores(small, crops))
        if best is None or score > best[0]:
            iy, ix = divmod(i, nx)
            # The window's top-left back on screen -> the portrait's box.
            bx = box[0] + ix * (box[2] - box[0]) / out[0]
            by = box[1] + iy * (box[3] - box[1]) / out[1] - SHOWN[0] * s
            best = (score, bx, by, ICON * s)
    if not best or best[0] < WIDE_MIN:
        return None
    # Closer, at full scale: a few sizes round it, a few px either way.
    bank = _bank(side)
    hh, ww = bank[6]
    found, m = None, 4
    cx, cy = best[1] + best[3] / 2, best[2] + best[3] / 2
    for f in (0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03):
        sz = best[3] * f
        x0, y0, k = cx - sz / 2, cy - sz / 2, sz / ICON
        box = (x0 - m * k, y0 + (SHOWN[0] - m) * k, x0 + (ICON + m) * k, y0 + (SHOWN[1] + m) * k)
        region = np.asarray(frame.crop(*box, size=(ww + 2 * m, hh + 2 * m)), dtype=np.float32)
        crops, nx = _windows(region, hh, ww)
        score, a, i, runner_up = _best(_scores(bank, crops))
        if score >= AGENT_MIN and score - runner_up >= AGENT_MARGIN and (found is None or score > found[0]):
            iy, ix = divmod(i, nx)
            found = (score, x0 + (ix - m) * k, y0 + (iy - m) * k, sz)
    return found[1:] if found else None


def find_layout(frame, layout, unread):
    """The layout from cards with a portrait no agent matched (unread:
    [(side, row)]): one found sets the scale and place; a second one rows
    away on the same side pins the scale by the spacing between them.
    Returns a new Layout, or None."""
    for side, row in unread:
        box = find_card(frame, side, row, layout)
        if not box:
            continue
        trial = Layout()
        trial.found(side, row, *box)
        others = sorted((r for s_, r in unread if s_ == side and r != row), key=lambda r: -abs(r - row))
        for other in others[:1]:
            box2 = find_card(frame, side, other, trial)
            if box2 and abs(box2[2] / box[2] - 1) < 0.05:
                s = (box2[1] - box[1]) / (ROW_STEP * (other - row))
                if abs(s / trial.s - 1) < 0.1:
                    size = ICON * s
                    # (same middle as found, the spacing's size)
                    trial.found(side, row, box[0] + (box[2] - size) / 2, box[1] + (box[2] - size) / 2, size)
        return trial
    return None


def card_agent(frame, side, row, layout=None):
    """The agent on a card, or "" (an empty card). Matched by shape and
    shading, so a portrait faded in while hovering still counts."""
    return _match(frame, side, row, layout or Layout())[0]


def card_locked(frame, side, row, layout=None):
    """Locked in: the name is in the team's colour (white while hovering)."""
    np = _np()
    layout = layout or Layout()
    x0, x1 = NAME_X[side]
    y = NAME_Y + ROW_STEP * row
    (a, b0), (c, b1) = layout.point(side, x0, y - 8), layout.point(side, x1, y + 8)
    px = np.asarray(frame.crop(min(a, c), b0, max(a, c), b1, size=(x1 - x0, 16)), dtype=np.int32).reshape(-1, 3)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    # (thresholds loose enough for thin text resampled off another resolution)
    white = int((px.min(axis=1) > 170).sum())
    if side == "defenders":
        tinted = int(((g > 130) & (b > 100) & (g - r > 50)).sum())
    else:
        tinted = int(((r > 130) & (r - g > 50) & (r - b > 40)).sum())
    # (a short name, resampled off another resolution, can have only a few)
    return tinted >= 6 and tinted > white


def _ncc(a, b):
    np = _np()
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


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


def read_name(frame, side, row, ocr, layout=None):
    from .reader import player_name
    layout = layout or Layout()
    x0, x1 = NAME_X[side]
    y = NAME_Y + ROW_STEP * row
    (a, b0), (c, b1) = layout.point(side, x0 - 26, y - 12), layout.point(side, x1, y + 12)
    words = ocr.words(_light_text(frame.crop(min(a, c), b0, max(a, c), b1, size=(x1 - x0 + 26, 24))))
    return player_name(" ".join(t for t, _, _ in sorted(words, key=lambda w: w[1])))


# --- a whole frame ------------------------------------------------------------

def read(image, ocr=None, names=None, layout=None):
    """The agent select reading for a frame, or None when it isn't agent
    select. names: {(side, row): name} already read (names don't change, so
    they're only read once). layout: where the cards are (kept between
    frames by the caller; found again when a portrait goes unmatched)."""
    frame = image if isinstance(image, Frame) else Frame(image)
    if not on_screen(frame):
        return None
    names = names if names is not None else {}
    keep = layout is not None
    layout = layout if keep else Layout()
    reading = {"active": True, "players": []}
    m = read_map(frame)
    if m:
        reading["map"] = m
    if ocr:
        t = read_timer(frame, ocr)
        if t is not None:
            reading["timer"] = t
    cards = {(side, row): _match(frame, side, row, layout)[0] for side in SIDES for row in range(5)}
    # Portraits no agent matches: the cards aren't where the layout has them.
    if not keep or time.time() - layout.searched_at >= layout.wait:
        unread = [key for key, agent in cards.items() if not agent and has_portrait(frame, key[0], key[1], layout)]
        if unread:
            layout.searched_at = time.time()
            layout.wait = min(layout.wait * 2, 60.0)
            trial = find_layout(frame, layout, unread)
            if trial and 0.8 <= trial.s <= 1.25 and abs(trial.dx) <= 150 and abs(trial.dy) <= 150:
                again = {key: _match(frame, key[0], key[1], trial)[0] for key in cards}
                if sum(map(bool, again.values())) > sum(map(bool, cards.values())):
                    layout.s, layout.dx, layout.dy = trial.s, trial.dx, trial.dy
                    layout.wait = CALIBRATE_EVERY
                    cards = again
                    try:
                        from .log import log
                        log(f"Agent select: cards found {trial.s:.3f}x, {trial.dx:+.0f}px across, {trial.dy:+.0f}px down "
                            "from the usual place")
                    except Exception:
                        pass
    # Cards still showing a portrait no agent matched (kept as a problem frame
    # by the reader when it lasts).
    reading["unread"] = sum(1 for (side, row), agent in cards.items()
                            if not agent and has_portrait(frame, side, row, layout))
    for side in SIDES:
        for row in range(5):
            agent = cards[(side, row)]
            p = {"team": side, "slot": row + 1, "agent": agent,
                 "locked": bool(agent) and card_locked(frame, side, row, layout)}
            have = names.get((side, row))
            if ocr and have and time.time() - names.get(("checked", side, row), 0) >= RECHECK:
                # A name confirmed mid-animation can be the start of the real
                # one ("Juw" for "Juwan"): looked at again now and then, and
                # a longer reading that starts the same, read twice, takes over.
                names[("checked", side, row)] = time.time()
                try:
                    text = read_name(frame, side, row, ocr, layout)
                    longer = names.setdefault(("longer", side, row), [])
                    if text and len(text) > len(have) and text.lower().startswith(have.lower()[:max(2, len(have) - 1)]):
                        longer.append(text)
                        if longer.count(text) >= 2:
                            names[(side, row)] = text
                except Exception:
                    pass
            if ocr and not names.get((side, row)):
                # A name counts once it's been read the same twice (a first
                # read mid-animation, or of a locked card's coloured text,
                # can come out cut short); after 6 reads, the commonest.
                try:
                    tries = names.setdefault(("tries", side, row), [])
                    text = read_name(frame, side, row, ocr, layout)
                    if text:
                        tries.append(text)
                    if text and tries.count(text) >= 2:
                        names[(side, row)] = text
                    elif len(tries) >= 6:
                        names[(side, row)] = max(set(tries), key=lambda t: (tries.count(t), len(t)))
                except Exception:
                    pass
            if names.get((side, row)):
                p["name"] = names[(side, row)]
            reading["players"].append(p)
    return reading
