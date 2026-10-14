"""The running app: keeps the latest game state (from the live feed or the
demo game), serves the overlay and control panel over HTTP."""

import base64
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from . import game, outputs
from .config import DATA_DIR, LOGO_DIR, WEB_DIR, web_file
from .demo import DemoGame
from .log import log, since
from .source import LiveFeed
from .updater import Updater, clean_up_old_update

mimetypes.add_type("font/otf", ".otf")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/mp4", ".m4v")
mimetypes.add_type("video/webm", ".webm")

# Bundled logos (shipped with the app) plus ones you've uploaded.
BUNDLED_LOGO_DIR = os.path.join(WEB_DIR, "assets", "logos")


class HudApp:
    def __init__(self, config, source=None, mode="live"):
        self.config = config
        self.mode = mode
        self.demo_speed = getattr(source, "speed", 4.0)
        self.feed = LiveFeed(config)          # live data posted to /api/ingest
        self.source = source or self.feed
        self.writer = outputs.FileWriter(config.output_dir())
        self.state = game.empty_state()
        self.fields = game.fields(self.state, config.get())
        self.updated_at = 0.0
        self.server = None
        self.updater = Updater()
        self.overlay_window = None  # the desktop app's HUD-over-the-game window
        # "gfx" runs the HUD; "observer" only shows another PC's HUD over the
        # game here. None until one is picked.
        self.role = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._was_connected = None
        self._last_round = None

    def set_mode(self, mode, speed=None):
        """Switch between the live feed ("live") and a simulated match ("demo")."""
        if speed:
            self.demo_speed = float(speed)
        cfg = self.config.get()
        if mode == "demo":
            maps = cfg.get("maps") or [{}]
            current = maps[min(int(cfg.get("current_map") or 0), len(maps) - 1)].get("name") or "Ascent"
            self.source = DemoGame(speed=self.demo_speed, attack_first=cfg.get("attack_first", "left"), map_name=current)
            log(f"Demo match started ({self.demo_speed:g}x speed)")
        elif mode == "live":
            self.source = self.feed
            log("Using the live feed")
        else:
            raise ValueError(f"Unknown mode {mode!r}")
        self.mode = mode
        self._was_connected = None
        self.refresh()

    def ingest(self, update):
        """Live data from a feed (screen reader, Overwolf app, another tool)."""
        self.feed.apply(update)
        if self.mode == "live":
            self.refresh()

    def refresh(self, fetch=True):
        cfg = self.config.get()
        raw = self.source.fetch() if fetch else self.source.state
        state = game.with_overrides(raw, cfg)
        fields = game.fields(state, cfg)
        with self._lock:
            self.state, self.fields = state, fields
            self.updated_at = time.time()
        self.writer.write(fields)
        if fetch:
            self._log_changes(state)
        return state

    def _log_changes(self, state):
        connected = state["connected"]
        if connected != self._was_connected:
            if connected:
                log("Match data coming in" + (f" ({state['match']['map']})" if state["match"]["map"] else ""))
            elif self._was_connected is not None:
                log("No match data - waiting for the feed")
            self._was_connected = connected
        m = state["match"]
        if m["round_winner"] and self._last_round != m["round"]:
            self._last_round = m["round"]
            cfg = self.config.get()
            log(f"Round {m['round']}: {cfg[m['round_winner']]['tricode']} ({m['win_type'] or 'win'}) - "
                f"{m['score']['left']}-{m['score']['right']}")

    def set_role(self, role):
        if role not in ("gfx", "observer", None):
            raise ValueError(f"Unknown client: {role}")
        if role != self.role and self.overlay_window and self.overlay_window.window:
            self.overlay_window.close()
        if self.overlay_window:
            self.overlay_window.url = None
        self.role = role
        if role:
            log({"gfx": "GFX Controller", "observer": "Observer Client"}[role] + " started")

    def run_poller(self):
        while not self._stop.is_set():
            if self.role == "observer":  # the GFX PC has the match data, not this one
                self._stop.wait(1)
                continue
            try:
                self.refresh()
            except Exception as e:  # keep the HUD alive whatever the game sends
                log(f"Update failed: {e!r}", "error")
            self._stop.wait(0.25)

    def stop(self):
        self._stop.set()
        if self.server:
            self.server.stop()

    def app_info(self):
        cfg = self.config.get()
        port = self.server.port if self.server else cfg["http_port"]
        network = bool(cfg.get("allow_network"))
        lan = lan_ip() if network else None
        return {"mode": self.mode, "role": self.role, "demo_speed": self.demo_speed, "network": network, "port": port,
                "feed": self.feed.info(), "update": self.updater.info(),
                "overlay_window": self.overlay_window.info() if self.overlay_window else {"available": False},
                "lan_url": f"http://{lan}:{port}" if lan else None, "data_dir": DATA_DIR}

    def snapshot(self):
        with self._lock:
            return {"game": self.state, "fields": self.fields, "updated_at": self.updated_at,
                    "config": self.config.get(), "output_dir": self.config.output_dir(), "app": self.app_info()}

    def save_logo(self, side, filename, data_b64):
        name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(filename or "logo.png"))
        if os.path.splitext(name)[1].lower() not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
            raise ValueError("Logo must be a PNG, JPG, WEBP or SVG")
        os.makedirs(LOGO_DIR, exist_ok=True)
        with open(os.path.join(LOGO_DIR, name), "wb") as f:
            f.write(base64.b64decode(data_b64))
        self.config.update({side: {"logo": f"assets/logos/{name}"}})
        log(f"Logo uploaded for the {side} team: {name}")
        return f"assets/logos/{name}"

    def list_logos(self):
        names = set()
        for folder in (BUNDLED_LOGO_DIR, LOGO_DIR):
            if os.path.isdir(folder):
                names.update(f for f in os.listdir(folder) if not f.startswith("."))
        return [f"assets/logos/{n}" for n in sorted(names)]

    def set_network(self, enabled):
        self.config.update({"allow_network": bool(enabled)})
        if self.server:
            self.server.restart(self.host())
        log("Other PCs on your network can now read the HUD" if enabled else "HUD is now only reachable from this PC")

    def host(self):
        cfg = self.config.get()
        return "0.0.0.0" if cfg.get("allow_network") else cfg["http_host"]

    def open_folder(self, which):
        folders = {"output": self.config.output_dir(), "logos": LOGO_DIR, "app": DATA_DIR}
        path = folders[which]
        os.makedirs(path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)  # noqa: only exists on Windows
        else:
            subprocess.Popen(["xdg-open" if sys.platform != "darwin" else "open", path])


def parse_range(header, size):
    """'bytes=100-' -> (100, size - 1); None if absent or unusable."""
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", (header or "").strip())
    if not m or size <= 0 or (not m.group(1) and not m.group(2)):
        return None
    if m.group(1):
        start = int(m.group(1))
        end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
    else:  # last N bytes
        start, end = max(0, size - int(m.group(2))), size - 1
    return (start, end) if start <= end < size else None


def check_gfx(text):
    """Observer client: is the GFX PC's HUD reachable at this address?"""
    from .overlay_window import gfx_base_url
    try:
        base = gfx_base_url(text)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    try:
        # Straight to the GFX PC on the network, never through a web proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(base + "/api/state", timeout=3) as r:
            ok = "game" in json.loads(r.read())
    except Exception as e:
        reason = getattr(e, "reason", e)
        return {"ok": False, "error": f"Can't reach the HUD at {base} ({reason}). Check the address, that VALORANT HUD is "
                                      "running there, and that \"Let other PCs on the network read the HUD\" is ticked."}
    if not ok:
        return {"ok": False, "error": f"{base} isn't a VALORANT HUD"}
    return {"ok": True, "overlay": base + "/overlay"}


def lan_ip():
    """This PC's address on the local network (no traffic is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def _is_local(address):
    return address in ("127.0.0.1", "::1") or address.startswith("127.")


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, body, ctype="application/json", status=200):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _static(self, rel):
            path = web_file(unquote(rel))
            if not path:
                return self._send('{"error":"not found"}', status=404)
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            size = os.path.getsize(path)
            span = parse_range(self.headers.get("Range"), size)
            if span is None and size < 8 * 1024 * 1024:
                with open(path, "rb") as f:
                    return self._send(f.read(), ctype)
            # Big files (background videos) are streamed, with byte ranges so
            # the browser can seek and loop.
            start, end = span or (0, size - 1)
            self.send_response(206 if span else 200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if span:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                with open(path, "rb") as f:
                    f.seek(start)
                    left = end - start + 1
                    while left > 0:
                        chunk = f.read(min(256 * 1024, left))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        left -= len(chunk)
            except (ConnectionError, OSError):
                pass  # the browser stopped reading (normal while seeking)

        def do_GET(self):
            url = urlparse(self.path)
            path = url.path
            fields = app.snapshot()["fields"]
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/control")
                self.end_headers()
            elif path == "/api/observer/check":
                # Observer client: can this PC reach the GFX PC's HUD?
                if not _is_local(self.client_address[0]):
                    return self._send('{"error":"forbidden"}', status=403)
                self._send(json.dumps(check_gfx((parse_qs(url.query).get("url") or [""])[0])))
            elif path in ("/overlay", "/scoreboard", "/hud", "/hud/", "/scoreboard/"):
                # The overlays are the templates in web/hud and web/scoreboard
                # (their images load relative to their own folder).
                folder = "scoreboard" if path.startswith("/scoreboard") else "hud"
                self.send_response(302)
                self.send_header("Location", f"/{folder}/Console.html" + (f"?{url.query}" if url.query else ""))
                self.end_headers()
            elif path in ("/control", "/start", "/observer"):
                self._static(path[1:] + ".html")
            elif path == "/api/state":
                self._send(json.dumps(app.snapshot()))
            elif path == "/api/log":
                after = int((parse_qs(url.query).get("after") or ["0"])[0])
                self._send(json.dumps(since(after)))
            elif path == "/hud.json":
                self._send(json.dumps([fields]))
            elif path == "/hud.csv":
                self._send(outputs.to_csv(fields), "text/csv; charset=utf-8")
            elif path == "/hud.xml":
                self._send(outputs.to_xml(fields), "application/xml; charset=utf-8")
            elif path == "/api/logos":
                self._send(json.dumps(app.list_logos()))
            else:
                self._static(path.lstrip("/"))

        def do_POST(self):
            # Other PCs may read the HUD (when allowed), but only this PC can
            # change it.
            if not _is_local(self.client_address[0]):
                return self._send('{"error":"Changes can only be made on the HUD PC"}', status=403)
            url = urlparse(self.path)
            path = url.path
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                if path == "/api/config":
                    app.config.update(body)
                elif path == "/api/logo":
                    app.save_logo(body["side"], body.get("filename"), body["data"])
                elif path == "/api/mode":
                    app.set_mode(body["mode"], body.get("speed"))
                elif path == "/api/network":
                    app.set_network(body["enabled"])
                elif path == "/api/open":
                    app.open_folder(body["folder"])
                elif path == "/api/ingest":
                    # Live match data (partial updates, see valhud/game.py).
                    app.ingest(body)
                    return self._send('{"ok":true}')
                elif path == "/api/update/check":
                    app.updater.check()
                elif path == "/api/update/install":
                    app.updater.install_in_background()
                elif path == "/api/overlay-window":
                    if not app.overlay_window:
                        raise ValueError("The HUD window is only available in the desktop app")
                    if body.get("url") is not None:
                        app.config.update({"observer_url": body["url"]})
                    app.overlay_window.set(bool(body.get("open")), body.get("screen"), body.get("url"))
                elif path == "/api/role":
                    app.set_role(body.get("role"))
                else:
                    return self._send('{"error":"not found"}', status=404)
                app.refresh(fetch=False)
                self._send(json.dumps(app.snapshot()))
            except (ValueError, KeyError, OSError) as e:
                self._send(json.dumps({"error": str(e)}), status=400)

    return Handler


class Server:
    """The HTTP server in a background thread; can be restarted on a new host."""

    def __init__(self, app, host, port):
        self.app, self.port = app, port
        self.httpd = None
        self._start(host)

    def _start(self, host):
        self.httpd = ThreadingHTTPServer((host, self.port), make_handler(self.app))
        self.httpd.daemon_threads = True
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.host = host

    def restart(self, host):
        if host == self.host:
            return
        old = self.httpd
        old.shutdown()
        old.server_close()
        self._start(host)

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def start(app):
    """Start the web server and the game poller. Raises OSError if the port is taken."""
    port = app.config.get()["http_port"]
    app.server = Server(app, app.host(), port)
    clean_up_old_update()
    app.updater.check_in_background()
    threading.Thread(target=app.run_poller, daemon=True).start()
    log(f"VALORANT HUD {app.updater.current} running - control panel http://localhost:{port}/control")
    log(f"Overlay (browser source, 1920x1080): http://localhost:{port}/overlay")
    log(f"vMix data source: http://localhost:{port}/hud.csv  - file: {app.config.output_dir()}")
    return app.server
