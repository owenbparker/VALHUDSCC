"""Team colours: the HUD templates are drawn in teal (the defending team) and
red (the attacking team). The control panel can pick other colours; the
templates' art and styles are then recoloured as they're served.

Only colours near the template's teal or red change, keeping their shading
(a darker teal becomes a darker shade of the new colour), so greys, the gold
highlight and the agents' portraits stay as they are. The templates still
swap the two colours at half time themselves.
"""

import colorsys
import os
import re
import threading

# The templates' own colours: (config key, reference colour, hue window).
DEFAULTS = {"defense_color": "#00ffcc", "attack_color": "#ff4e5d"}
FAMILIES = (("defense_color", 168.0), ("attack_color", 345.0))
FULL, FADE = 25.0, 40.0   # degrees from a family's hue: fully recoloured, then fading out

# What gets recoloured: the templates' pages and styles, and their art (not
# agents, weapons, logos or maps, which live in subfolders of Resources).
_TEXT = (".css", ".js", ".html")


def _hex(c):
    c = str(c or "").strip().lower()
    return c if re.fullmatch(r"#[0-9a-f]{6}", c) else None


def colours(cfg):
    """{"defense_color": "#rrggbb", "attack_color": ...} that differ from the
    templates' own, or {} when there's nothing to change."""
    out = {}
    for key, default in DEFAULTS.items():
        c = _hex(cfg.get(key))
        if c and c != default:
            out[key] = c
    return out


def applies(rel):
    """Is this web file (path relative to web/) one that gets recoloured?"""
    parts = rel.replace("\\", "/").lstrip("/").split("/")
    if not parts or parts[0] not in ("hud", "scoreboard"):
        return False
    name = parts[-1].lower()
    if name.endswith(_TEXT):
        return len(parts) == 2
    return name.endswith(".png") and len(parts) == 3 and parts[1] == "Resources"


def _hsv(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


def _plan(chosen):
    """[(family hue, hue shift, saturation factor, value factor), ...]"""
    plan = []
    for key, centre in FAMILIES:
        if key not in chosen:
            continue
        rh, rs, rv = _hsv(DEFAULTS[key])
        th, ts, tv = _hsv(chosen[key])
        plan.append((centre, (th - rh) % 360, ts / max(rs, 1e-3), tv / max(rv, 1e-3)))
    return plan


def _weight(dist):
    if dist <= FULL:
        return 1.0
    if dist >= FADE:
        return 0.0
    return (FADE - dist) / (FADE - FULL)


def recolour_rgb(r, g, b, plan):
    """One colour (0-255 channels)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.15 or v < 0.06:
        return r, g, b
    h *= 360
    for centre, shift, fs, fv in plan:
        w = _weight(abs((h - centre + 180) % 360 - 180))
        if w <= 0:
            continue
        nr, ng, nb = colorsys.hsv_to_rgb(((h + shift) % 360) / 360, min(1.0, s * fs), min(1.0, v * fv))
        return tuple(round(o + (n * 255 - o) * w) for o, n in zip((r, g, b), (nr, ng, nb)))
    return r, g, b


_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b|rgba?\(\s*([0-9.]+)[\s,]+([0-9.]+)[\s,]+([0-9.]+)")


def recolour_text(text, plan):
    def swap(m):
        t = m.group(0)
        if t.startswith("#"):
            d = t[1:]
            if len(d) == 3:
                d = "".join(ch * 2 for ch in d)
            r, g, b = (int(d[i:i + 2], 16) for i in (0, 2, 4))
            nr, ng, nb = recolour_rgb(r, g, b, plan)
            if (nr, ng, nb) == (r, g, b):
                return t
            return "#%02x%02x%02x" % (nr, ng, nb) + d[6:]
        try:
            r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        except ValueError:
            return t
        nr, ng, nb = recolour_rgb(round(r), round(g), round(b), plan)
        if (nr, ng, nb) == (round(r), round(g), round(b)):
            return t
        head = t[:t.index("(") + 1]
        sep = "," if "," in t else " "
        return f"{head}{nr}{sep}{' ' if sep == ',' else ''}{ng}{sep}{' ' if sep == ',' else ''}{nb}"
    return _COLOUR.sub(swap, text)


def recolour_image(data, plan):
    """PNG bytes -> recoloured PNG bytes (None if nothing in it changes)."""
    import io

    import numpy as np
    from PIL import Image
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    a = np.asarray(img)
    # Only the coloured pixels are worked on (most of the art is grey or empty).
    rgb8 = a[..., :3].reshape(-1, 3)
    mx8, mn8 = rgb8.max(1), rgb8.min(1)
    idx = np.nonzero((a[..., 3].reshape(-1) > 0) & (mx8 >= 16) & ((mx8 - mn8) >= 0.15 * mx8) & (mx8 > mn8))[0]
    if not len(idx):
        return None
    rgb = rgb8[idx].astype(np.float32) / 255
    mx, mn = rgb.max(1), rgb.min(1)
    d = mx - mn
    s = d / np.maximum(mx, 1e-6)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    out = rgb.copy()
    done = np.zeros(len(idx), bool)
    for centre, shift, fs, fv in plan:
        dist = np.abs((h - centre + 180) % 360 - 180)
        w = np.where(done, 0, np.clip((FADE - dist) / (FADE - FULL), 0, 1))
        sel = np.nonzero(w > 0)[0]
        if not len(sel):
            continue
        nh = (h[sel] + shift) % 360
        ns = np.clip(s[sel] * fs, 0, 1)
        nv = np.clip(mx[sel] * fv, 0, 1)
        c = nv * ns
        x = c * (1 - np.abs((nh / 60) % 2 - 1))
        m = nv - c
        k = (nh // 60).astype(int) % 6
        z = np.zeros_like(c)
        r_ = np.choose(k, [c, x, z, z, x, c]) + m
        g_ = np.choose(k, [x, c, c, x, z, z]) + m
        b_ = np.choose(k, [z, z, x, c, c, x]) + m
        new = np.stack([r_, g_, b_], 1)
        out[sel] += (new - out[sel]) * w[sel, None]
        done[sel] = True
    if not done.any():
        return None
    flat = a.reshape(-1, 4).copy()
    flat[idx, :3] = np.round(out * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(flat.reshape(a.shape), "RGBA").save(buf, "PNG", compress_level=1)
    return buf.getvalue()


_cache = {}
_lock = threading.Lock()


def served(path, rel, chosen):
    """The bytes to serve for web file `path` (`rel` relative to web/) with
    the chosen colours, or None to serve the file as it is."""
    if not chosen or not applies(rel):
        return None
    key = (path, os.path.getmtime(path), tuple(sorted(chosen.items())))
    with _lock:
        if key in _cache:
            return _cache[key]
    plan = _plan(chosen)
    with open(path, "rb") as f:
        data = f.read()
    if path.lower().endswith(".png"):
        out = recolour_image(data, plan) or data
    else:
        out = recolour_text(data.decode("utf-8", "replace"), plan).encode("utf-8")
    with _lock:
        if len(_cache) > 64:
            _cache.clear()
        _cache[key] = out
    return out
