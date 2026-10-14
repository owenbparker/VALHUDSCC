"""Reads the match off the VALORANT spectator screen.

VALORANT gives other programs no live match data, so this captures the game
window a couple of times a second and reads what the spectator view shows:

  - the top bar (always on screen): each player's agent, health bar (none
    when dead), who carries the spike, the score, the round timer and the
    planted spike;
  - the Tab scoreboard, whenever it's open (e.g. the buy phase): names, ult
    points, kills / deaths / assists, weapon, shield and credits.

Agents and weapons are recognised by comparing against the HUD's own agent
and weapon images; text is read with Windows' built-in text recognition.
Everything is measured on a 1920x1080 frame and scaled with the window's
height, centred (the spectator HUD is laid out that way).

    python -m valhud.reader SCREENSHOT.png      read a saved screenshot
"""

import asyncio
import os
import re
import sys
import threading
import time

from . import game
from .config import WEB_DIR
from .log import log

REF_H = 1080
# Top bar: centre of each player's portrait / health bar, left team then right.
TOP_X = {"left": [466, 532, 598, 664, 730], "right": [1191, 1257, 1323, 1389, 1455]}
BAR_Y = (76, 82)            # the white health bar under each portrait
BAR_HALF = 20               # bar is 40px wide
PORTRAIT_Y, PORTRAIT_SIZE = 30, 40
CARRIER_Y = (90, 124)       # the spike icon under the carrier's portrait
SCORE_LINE = (790, 24, 1130, 72)   # "0   0:24   0"
SPIKE_ICON = (930, 24, 990, 70)    # replaces the timer once planted
# Tab scoreboard: row tops (34px rows), left team's block then right's.
ROW_TOP = {"left": 338, "right": 569}
ROW_H = 34
COLS = {"portrait": (573, 607), "name": (643, 812), "ult": (812, 933), "k": (934, 973), "d": (974, 1013),
        "a": (1014, 1053), "weapon": (1060, 1168), "shield": (1170, 1204), "creds": (1204, 1294)}
WINDOW_TITLE = "VALORANT"


# --- geometry ---------------------------------------------------------------

class Frame:
    """A captured frame and the mapping from 1920x1080 coordinates to it."""

    def __init__(self, image):
        self.image = image.convert("RGB")
        self.k = self.image.height / REF_H
        self.cx = self.image.width / 2

    def x(self, x):
        return round(self.cx + (x - 960) * self.k)

    def y(self, y):
        return round(y * self.k)

    def crop(self, x0, y0, x1, y1, size=None):
        """A region given in 1080p coordinates, resized back to 1080p scale
        (or to size) so the measurements below hold at any resolution."""
        from PIL import Image
        img = self.image.crop((self.x(x0), self.y(y0), self.x(x1), self.y(y1)))
        target = size or (x1 - x0, y1 - y0)
        return img if img.size == target else img.resize(target, Image.BILINEAR)


def _np():
    import numpy
    return numpy


# --- agents and weapons -----------------------------------------------------

_icons, _weapons = {}, {}


def _agent_icon(agent, size):
    np = _np()
    from PIL import Image
    key = (agent, size)
    if key not in _icons:
        path = os.path.join(WEB_DIR, "hud", "Resources", "Agentes", agent, agent + ".png")
        t = np.asarray(Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS), dtype=np.float32)
        _icons[key] = (t[..., :3], t[..., 3] > 128)
    return _icons[key]


def _ncc(a, b):
    np = _np()
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def identify_agent(crop, sizes, slack=3, agents=None):
    """[(score, agent), ...] best first, for a portrait crop whose top-left is
    roughly where the icon starts (within `slack` px)."""
    np = _np()
    c = np.asarray(crop, dtype=np.float32)
    H, W = c.shape[:2]
    out = []
    for agent in agents or game.AGENTS:
        best = -1.0
        for s in sizes:
            rgb, mask = _agent_icon(agent, s)
            for dy in range(-slack, slack + 1):
                for dx in range(-slack, slack + 1):
                    y0, x0 = max(0, dy), max(0, dx)
                    y1, x1 = min(H, dy + s), min(W, dx + s)
                    if y1 - y0 < 10 or x1 - x0 < 10:
                        continue
                    m = mask[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
                    if m.sum() < 120:
                        continue
                    v = _ncc(c[y0:y1, x0:x1][m].ravel(), rgb[y0 - dy:y1 - dy, x0 - dx:x1 - dx][m].ravel())
                    best = max(best, v)
        out.append((round(best, 3), agent))
    out.sort(reverse=True)
    return out


def _silhouette(mask, size=(72, 24)):
    np = _np()
    from PIL import Image
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return None
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    img = Image.fromarray((m * 255).astype("uint8"))
    w, h = img.size
    k = min(size[0] / w, size[1] / h)
    img = img.resize((max(1, round(w * k)), max(1, round(h * k))), Image.BILINEAR)
    out = Image.new("L", size, 0)
    out.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return np.asarray(out, dtype=np.float32) / 255, w / h


def identify_weapon(crop):
    """(weapon, score) from the white weapon icon in a scoreboard cell."""
    np = _np()
    from PIL import Image
    if not _weapons:
        folder = os.path.join(WEB_DIR, "hud", "Resources", "Armas")
        for name in game.WEAPONS:
            alpha = np.asarray(Image.open(os.path.join(folder, name + ".png")).convert("RGBA"))[..., 3] > 100
            _weapons[name] = _silhouette(alpha)
    seen = _silhouette(np.asarray(crop.convert("L")) > 170)
    if seen is None:
        return None, 0.0
    shape, ratio = seen
    best = (None, -1.0)
    for name, (t, r) in _weapons.items():
        score = float(np.minimum(shape, t).sum() / np.maximum(shape, t).sum()) - 0.15 * abs(float(np.log(ratio / r)))
        if score > best[1]:
            best = (name, round(score, 3))
    return best


# --- the top bar ------------------------------------------------------------

def _pixels(img):
    img = img.convert("RGB")
    return img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()


def _bright(img, level=185):
    """Fraction of pixels that are near-white."""
    data = _pixels(img)
    return sum(1 for p in data if min(p) >= level) / max(1, len(data))


def health_bar(frame, side, slot):
    """(alive, health 0-100) from the bar under a portrait."""
    x = TOP_X[side][slot - 1]
    strip = frame.crop(x - BAR_HALF, BAR_Y[0], x + BAR_HALF, BAR_Y[1])
    cols = [any(min(strip.getpixel((cx, cy))) >= 170 for cy in range(strip.height)) for cx in range(strip.width)]
    lit = sum(cols)
    if lit < 2:
        return False, 0
    if lit >= strip.width - 2:
        return True, 100   # full (the bar's ends are soft)
    return True, max(1, round(100 * lit / strip.width))


def carries_spike(frame, side, slot):
    x = TOP_X[side][slot - 1]
    return _bright(frame.crop(x - 18, CARRIER_Y[0], x + 18, CARRIER_Y[1]), 160) > 0.08


def spike_planted(frame):
    """The timer turns into a red spike icon once it's planted."""
    data = _pixels(frame.crop(*SPIKE_ICON))
    red = sum(1 for r, g, b in data if r > 150 and r > g + 70 and r > b + 70)
    return red / max(1, len(data)) > 0.12


def top_portrait(frame, side, slot):
    x = TOP_X[side][slot - 1]
    from PIL import Image
    crop = frame.crop(x - 20 - 3, PORTRAIT_Y - 3, x + 20 + 3, PORTRAIT_Y + PORTRAIT_SIZE + 3)
    return crop.transpose(Image.FLIP_LEFT_RIGHT) if side == "right" else crop


# --- the scoreboard ---------------------------------------------------------

def scoreboard_open(frame):
    """Is the Tab scoreboard on screen? (teal rows above red rows)"""
    def share(y0, test):
        data = _pixels(frame.crop(820, y0, 930, y0 + 5 * ROW_H))
        return sum(1 for p in data if test(p)) / max(1, len(data))
    teal = share(ROW_TOP["left"], lambda p: p[1] > p[0] + 25 and p[1] > 60)
    red = share(ROW_TOP["right"], lambda p: p[0] > p[1] + 25 and p[0] > 60)
    return teal > 0.6 and red > 0.6


def row_cell(frame, side, row, col, pad=0):
    x0, x1 = COLS[col]
    y0 = ROW_TOP[side] + ROW_H * row
    return frame.crop(x0, y0 + pad, x1, y0 + ROW_H - pad)


def shield_level(cell):
    """0 / 25 / 50 from the shield icon next to the weapon (none: no icon).
    Bigger, filled icon = heavy shield (calibrate with real frames)."""
    lit = _bright(cell, 170)
    if lit < 0.04:
        return 0
    return 50 if lit > 0.22 else 25


# --- text ---------------------------------------------------------------------

class WindowsOcr:
    """Windows.Media.Ocr through the winrt packages."""

    def __init__(self):
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine
        engine = OcrEngine.try_create_from_language(Language("en-US"))
        if engine is None:
            engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise RuntimeError("Windows text recognition isn't installed for any of your languages")
        self.engine = engine

    def words(self, image):
        """[(text, x_centre, y_centre), ...] in the image's pixels."""
        from winrt.windows.graphics.imaging import BitmapAlphaMode, BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter
        rgba = image.convert("RGBA")
        writer = DataWriter()
        writer.write_bytes(rgba.tobytes("raw", "BGRA"))
        buffer = writer.detach_buffer()
        try:
            bitmap = SoftwareBitmap.create_copy_from_buffer(buffer, BitmapPixelFormat.BGRA8, rgba.width, rgba.height)
        except TypeError:
            bitmap = SoftwareBitmap(BitmapPixelFormat.BGRA8, rgba.width, rgba.height, BitmapAlphaMode.PREMULTIPLIED)
            bitmap.copy_from_buffer(buffer)

        async def run():
            return await self.engine.recognize_async(bitmap)

        result = asyncio.run(run())
        out = []
        for line in result.lines:
            for word in line.words:
                r = word.bounding_rect
                out.append((word.text, r.x + r.width / 2, r.y + r.height / 2))
        return out


def ink(img, scale=2, level=150):
    """White text -> black on white, enlarged: what Windows OCR reads best."""
    from PIL import Image
    gray = img.convert("L").point(lambda v: 0 if v >= level else 255)
    return gray.resize((gray.width * scale, gray.height * scale), Image.LANCZOS)


_DIGITS = str.maketrans({"O": "0", "o": "0", "D": "0", "Q": "0", "l": "1", "I": "1", "|": "1", "i": "1",
                         "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2", "g": "9"})


def number(text):
    digits = re.sub(r"\D", "", (text or "").translate(_DIGITS))
    return int(digits) if digits else None


def read_score_line(frame, ocr):
    """{"left": int, "right": int, "timer": seconds} from the top bar."""
    x0, y0, x1, y1 = SCORE_LINE
    words = ocr.words(ink(frame.crop(x0, y0, x1, y1), 2, 170))
    mid = (960 - x0) * 2
    out = {}
    for text, cx, _ in words:
        if ":" in text or "." in text:
            m = re.search(r"(\d+)[:.](\d\d)", text.translate(_DIGITS))
            if m:
                out["timer"] = int(m.group(1)) * 60 + int(m.group(2))
            continue
        value = number(text)
        if value is None or value > 30:
            continue
        side = "left" if cx < mid - 60 else "right" if cx > mid + 60 else None
        if side and side not in out:
            out[side] = value
    return out


def read_scoreboard(frame, ocr):
    """Per row (left rows 0-4, right rows 0-4): name, ult, K/D/A, credits."""
    rows = {}
    for side in ("left", "right"):
        top = ROW_TOP[side]
        x0, x1 = COLS["name"][0], COLS["creds"][1]
        img = ink(frame.crop(x0, top, x1, top + 5 * ROW_H), 2, 150)
        words = ocr.words(img)
        for r in range(5):
            mine = [(t, x0 + cx / 2) for t, cx, cy in words if r * ROW_H <= cy / 2 < (r + 1) * ROW_H]
            cells = {c: [t for t, x in mine if COLS[c][0] <= x < COLS[c][1]] for c in ("name", "ult", "k", "d", "a", "creds")}
            ult = re.findall(r"\d+", " ".join(cells["ult"]).translate(_DIGITS))
            rows[(side, r)] = {
                "name": " ".join(cells["name"]).strip(),
                "ult": (int(ult[0]), int(ult[-1])) if len(ult) >= 2 else None,
                "k": number(" ".join(cells["k"])), "d": number(" ".join(cells["d"])), "a": number(" ".join(cells["a"])),
                "creds": number(" ".join(cells["creds"])),
            }
    return rows


# --- putting it together ----------------------------------------------------

def read_frame(image, ocr=None, known_agents=None):
    """Everything readable in one frame, as an update for game.merge()."""
    frame = Frame(image)
    players = []
    top_agents = {}
    for side in ("left", "right"):
        for slot in range(1, 6):
            alive, health = health_bar(frame, side, slot)
            p = {"team": side, "slot": slot, "alive": alive, "health": health,
                 "spike": alive and carries_spike(frame, side, slot)}
            agent = (known_agents or {}).get((side, slot))
            if not agent and alive:
                best = identify_agent(top_portrait(frame, side, slot), (40, 42))
                if best[0][0] >= 0.6 and best[0][0] - best[1][0] >= 0.05:
                    agent = best[0][1]
            if agent:
                p["agent"] = agent
                top_agents[(side, slot)] = agent
            players.append(p)
    update = {"source": "screen", "match": {}, "players": players}
    planted = spike_planted(frame)
    update["match"]["spike"] = {"state": "planted"} if planted else {}
    carrier = next(((p["team"], p["slot"]) for p in players if p["spike"]), None)
    if not planted:
        update["match"]["spike"] = {"state": "carried" if carrier else "", "carrier": list(carrier) if carrier else None}
    if ocr:
        line = read_score_line(frame, ocr)
        if "left" in line and "right" in line:
            update["match"]["score"] = {"left": line["left"], "right": line["right"]}
            update["match"]["round"] = line["left"] + line["right"] + 1
        if "timer" in line:
            update["match"]["timer"] = line["timer"]
    if scoreboard_open(frame):
        board = read_scoreboard(frame, ocr) if ocr else {}
        by_slot = {(p["team"], p["slot"]): p for p in players}
        for side in ("left", "right"):
            # Scoreboard rows aren't in top-bar order: match them by agent.
            row_agents = {}
            team = [a for (t, _), a in (known_agents or {}).items() if t == side]
            for r in range(5):
                best = identify_agent(row_cell(frame, side, r, "portrait"), (32, 34, 36),
                                      agents=team if len(set(team)) == 5 else None)
                row_agents[r] = best[0][1] if best[0][0] >= 0.6 else None
            free = [s for s in range(1, 6)]
            assign = {}
            for r, agent in row_agents.items():
                slot = next((s for s in free if top_agents.get((side, s)) == agent), None)
                if slot:
                    assign[r] = slot
                    free.remove(slot)
            for r in range(5):
                if r not in assign and free:
                    assign[r] = free.pop(0)
            for r, slot in assign.items():
                p = by_slot[(side, slot)]
                if row_agents[r]:
                    p["agent"] = row_agents[r]
                weapon, score = identify_weapon(row_cell(frame, side, r, "weapon", 4))
                if weapon and score >= 0.6:
                    p["weapon"] = weapon
                p["shield"] = shield_level(row_cell(frame, side, r, "shield", 4))
                info = board.get((side, r)) or {}
                if info.get("name"):
                    p["name"] = info["name"]
                if info.get("ult"):
                    p["ult_points"], p["ult_max"] = info["ult"]
                for key, field in (("k", "kills"), ("d", "deaths"), ("a", "assists"), ("creds", "credits")):
                    if info.get(key) is not None:
                        p[field] = info[key]
        update["match"]["scoreboard_open"] = True
    return update


# --- capturing the game window ----------------------------------------------

def capture_valorant():
    """(image, None) with the VALORANT window's client area, or (None, reason)."""
    import ctypes
    from ctypes import wintypes
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        n = user32.GetWindowTextLengthW(hwnd)
        if n and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value.strip() == WINDOW_TITLE:
                found.append(hwnd)
        return True

    user32.EnumWindows(each, 0)
    if not found:
        return None, "VALORANT window not found"
    hwnd = found[0]
    if user32.IsIconic(hwnd):
        return None, "VALORANT is minimised"
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    width, height = rect.right, rect.bottom
    if width < 200 or height < 200:
        return None, "VALORANT window is too small"
    from PIL import ImageGrab
    point = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    image = ImageGrab.grab((point.x, point.y, point.x + width, point.y + height), all_screens=True)
    return image, None


def make_dpi_aware():
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()


class ScreenReader:
    """Reads the game in the background and hands each update to `send`."""

    def __init__(self, send):
        self.send = send
        self.status = "off"
        self.enabled = False
        self.last = None
        self.read_at = 0.0
        self.agents = {}       # (side, slot) -> agent, kept for the match
        self._agent_votes = {}
        self._stop = threading.Event()
        self._thread = None
        self.ocr = None
        self.available, self.reason = self._check()

    def _check(self):
        if sys.platform != "win32":
            return False, "Reading the screen only works on Windows"
        make_dpi_aware()  # real pixels, whatever the display scaling
        try:
            import numpy  # noqa: F401
            import PIL  # noqa: F401
            self.ocr = WindowsOcr()
        except Exception as e:
            return False, f"Screen reading unavailable: {e!r}"
        return True, ""

    def info(self):
        return {"available": self.available, "enabled": self.enabled, "status": self.status if self.available else self.reason,
                "age": round(time.time() - self.read_at, 1) if self.read_at else None}

    def set_enabled(self, on):
        self.enabled = bool(on) and self.available
        if self.enabled and not (self._thread and self._thread.is_alive()):
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            log("Reading VALORANT off the screen")
        elif not self.enabled:
            self._stop.set()
            self.status = "off"

    def stop(self):
        self._stop.set()

    def _learn_agents(self, update):
        """An agent counts once it's been seen three times in the same slot."""
        for p in update["players"]:
            key, agent = (p["team"], p["slot"]), p.get("agent")
            if not agent or self.agents.get(key) == agent:
                continue
            votes = self._agent_votes.setdefault(key, {})
            votes[agent] = votes.get(agent, 0) + 1
            if votes[agent] >= 3:
                self.agents[key] = agent
                self._agent_votes[key] = {}

    def _run(self):
        last_reason = None
        while not self._stop.is_set():
            reason = None
            try:
                image, reason = capture_valorant()
                if image is not None:
                    update = read_frame(image, self.ocr, self.agents)
                    self._learn_agents(update)
                    for p in update["players"]:
                        if (p["team"], p["slot"]) in self.agents:
                            p["agent"] = self.agents[(p["team"], p["slot"])]
                    self.last, self.read_at = update, time.time()
                    self.send(update)
            except Exception as e:
                reason = f"Screen read failed: {e!r}"
            self.status = reason or "reading"
            if reason != last_reason:
                log(reason or "Reading the spectator screen", "warn" if reason else "info")
                last_reason = reason
            self._stop.wait(0.5)


TEXT_FIELDS = ("name", "credits", "ult_points", "ult_max", "kills", "deaths", "assists")


def main(argv):
    """python -m valhud.reader IMAGE [--expect EXPECTED.json]

    Prints what was read from a saved screenshot; with --expect, checks the
    given players' fields and exits 1 on a mismatch.
    """
    import argparse
    import json
    from PIL import Image
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--expect")
    parser.add_argument("--no-ocr", action="store_true")
    args = parser.parse_args(argv)
    ocr = None if args.no_ocr else WindowsOcr()
    update = read_frame(Image.open(args.image), ocr)
    print(json.dumps(update["match"]))
    for p in update["players"]:
        print(json.dumps(p))
    if not args.expect:
        return 0
    with open(args.expect, encoding="utf-8") as f:
        expected = json.load(f)
    bad = []
    for key, value in expected.get("match", {}).items():
        if ocr is None and key in ("score", "timer", "round"):
            continue
        if update["match"].get(key) != value:
            bad.append(f"match {key}: read {update['match'].get(key)!r}, expected {value!r}")
    by_slot = {(p["team"], p["slot"]): p for p in update["players"]}
    for e in expected.get("players", []):
        p = by_slot[(e["team"], e["slot"])]
        for key, value in e.items():
            if key in ("team", "slot") or (ocr is None and key in TEXT_FIELDS):
                continue
            if p.get(key) != value:
                bad.append(f"{e['team']} {e['slot']} {key}: read {p.get(key)!r}, expected {value!r}")
    print("\n".join(bad) if bad else "OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
