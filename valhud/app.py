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

from . import game, mapbans, outputs, recolor
from .agentselect import AgentSelect, AgentSelectDemo
from .cams import CamHub
from .config import DATA_DIR, LOGO_DIR, SPONSOR_DIR, WEB_DIR, web_file
from .demo import DemoGame
from .enginelink import EngineLink, save_logo_bytes, save_sponsors
from .log import log, since
from .reader import ScreenReader
from .series import Series
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
        self.reader = ScreenReader(self._reader_update)
        self.overlay_window = None  # the desktop app's HUD-over-the-game window
        # "gfx" runs the HUD; "observer" only shows another PC's HUD over the
        # game here. None until one is picked.
        self.role = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        # The SCC GFX Engine: the game and series go to it; its teams can come here.
        self.engine = EngineLink("VALORANT HUD", "valorant", self._engine_snapshot, self._engine_apply_global,
                                 load=lambda: self.config.get().get("gfx_engine"),
                                 save=lambda d: self.config.update({"gfx_engine": d}), log=log)
        self._was_connected = None
        self._last_round = None
        # The observer client's reading of who it's spectating:
        # (text, time, agent, "attackers"/"defenders" or None).
        self.spectating = ("", 0.0, None, None)
        self.cams = CamHub()   # player webcams (SCC Player Cam, VALORANT mode)
        self.agent_select = AgentSelect()
        self._select_demo = None
        self.map_art = mapbans.MapArt()
        self.series = Series(config, log)   # maps from Map Bans, won maps, the series score

    # --- agent select -------------------------------------------------------

    def agent_select_update(self, reading, source=""):
        """A reading of agent select (screen, demo or control panel). A map
        read off the screen becomes the map being played."""
        was_active = self.agent_select.state["active"]
        new_map = self.agent_select.apply(reading, source)
        if source != "demo" and reading.get("active") and not was_active:
            # The next map: it's the current one, and the last one's data goes.
            if self.series.agent_select_started():
                self.feed.apply({"source": "agent select", "reset": True})
        if new_map and source != "demo":
            cfg = self.config.get()
            maps = [dict(m) for m in cfg.get("maps") or []]
            i = int(cfg.get("current_map") or 0)
            if 0 <= i < len(maps) and maps[i].get("name") != new_map:
                maps[i]["name"] = new_map
                self.config.update({"maps": maps})
                log(f"Agent select: the map is {new_map} (map {i + 1} of the series)")
            self.feed.apply({"source": source or "agent select", "match": {"map": new_map}})

    def _select_sides(self, reading):
        """The agent select screen shows DEFENDERS left and ATTACKERS right:
        which of our teams those are comes from who attacks first."""
        attackers = self.config.get().get("attack_first") or "left"
        side = {"attackers": attackers, "defenders": "right" if attackers == "left" else "left"}
        players = []
        for p in reading.get("players") or []:
            p = dict(p)
            p["team"] = side.get(p.get("team"), p.get("team"))
            players.append(p)
        return dict(reading, players=players) if "players" in reading else reading

    def agent_select_demo(self, on):
        if self._select_demo:
            self._select_demo.stop()
            self._select_demo = None
        if on:
            cfg = self.config.get()
            maps = cfg.get("maps") or [{}]
            current = maps[min(int(cfg.get("current_map") or 0), len(maps) - 1)].get("name") or "Ascent"
            self.agent_select.clear()
            self._select_demo = AgentSelectDemo(self.agent_select, current).start()
            log(f"Agent select demo started ({current})")
        else:
            self.agent_select.apply({"active": False}, "demo")

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

    def _reader_update(self, update):
        """The screen reader's reading: used here, or sent to the GFX PC when
        this is an observer client."""
        cfg = self.config.get()
        if self.role == "observer":
            if not cfg.get("observer_url"):
                return
            from .overlay_window import gfx_base_url
            req = urllib.request.Request(gfx_base_url(cfg["observer_url"]) + "/api/ingest",
                                         json.dumps(update).encode("utf-8"), {"Content-Type": "application/json"})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=3) as r:
                return json.loads(r.read() or b"{}")
        else:
            return self.ingest(update)

    def set_reader(self, enabled):
        self.config.update({"screen_reader": bool(enabled)})
        if enabled and not self.reader.available:
            raise ValueError(self.reader.reason)
        self.reader.set_enabled(enabled)
        if not enabled:
            log("Stopped reading the screen")

    def ingest(self, update):
        """Live data from a feed (screen reader, Overwolf app, another tool)."""
        if isinstance(update, dict) and isinstance(update.get("agent_select"), dict):
            update = dict(update)
            self.agent_select_update(self._select_sides(update.pop("agent_select")), "screen")
            if not update.get("match") and not update.get("players") and "spectating" not in update:
                if self.mode == "live":
                    self.refresh()   # (a map read off the screen)
                return {"ok": True}
        if isinstance(update, dict) and isinstance(update.get("spectating"), dict):
            update = dict(update)
            sp = update.pop("spectating")
            self.spectating = (str(sp.get("text") or ""), time.time(), sp.get("agent"), sp.get("side"))
            if not update.get("match") and not update.get("players"):
                self.refresh(fetch=False)
                return self.observed_name()
        self.feed.apply(update)
        if self.mode == "live":
            self.refresh()
        return self.observed_name()

    SPECTATING_FOR = 3.0   # seconds a reading counts for (the observer sends one a second at least)

    def observed_name(self):
        """{"observed": name of the player the observer is spectating, or None}."""
        with self._lock:
            o = self.state["match"].get("observed")
            p = next((p for p in self.state["players"] if o and (p["team"], p["slot"]) == (o["team"], o["slot"])), None)
        return {"ok": True, "observed": p["name"] if p else None}

    def refresh(self, fetch=True):
        cfg = self.config.get()
        raw = self.source.fetch() if fetch else self.source.state
        state = game.with_overrides(raw, cfg)
        # Names not typed or scanned: the ones read in agent select, by agent.
        picks = self.agent_select.view([])["players"]
        for p in state["players"]:
            if not p.get("name") and p.get("agent"):
                match = [q["name"] for q in picks.get(p["team"], []) if q.get("agent") == p["agent"] and q.get("name")]
                if len(match) == 1:
                    p["name"] = match[0]
        text, at, agent, side = self.spectating
        if time.time() - at < self.SPECTATING_FOR:
            state["match"]["observed"] = (game.observed_player(state, text)
                                          or game.observed_by_agent(state, agent, side))
        if self.mode == "live" and fetch:
            self.series.sync_maps()
            self.series.round_kills(state)
            fields = game.fields(state, cfg)
            shown = self.series.watch(state, fields)
            if shown is not state:   # cleared after the map
                state, fields = shown, game.fields(shown, cfg)
        else:
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

    def _engine_snapshot(self):
        """What the GFX Engine gets: the HUD's fields and the series."""
        cfg = self.config.get()
        with self._lock:
            # (Once the HUD's cleared after a map, the stats are its last.)
            fields = dict(self.series.stats or self.fields)
        series = {side: {"name": cfg[side]["name"], "short": cfg[side]["tricode"], "score": int(cfg[side].get("wins") or 0),
                         "color": cfg[side]["color"]} for side in ("left", "right")}
        series["best_of"] = int(cfg.get("best_of") or 3)
        # Its own pages, which GFX Engine adds to its graphics to take on air.
        hud = {"port": self.server.port if self.server else cfg["http_port"], "network": bool(cfg.get("allow_network")),
               "graphics": [{"id": "agent-select", "name": "Agent select", "path": "/agent-select", "kind": "board"},
                            {"id": "hud", "name": "In-game HUD", "path": "/overlay", "kind": "overlay"},
                            {"id": "scoreboard", "name": "Scoreboard", "path": "/scoreboard", "kind": "overlay"},
                            {"id": "map-bans-bo1", "name": "Map bans Bo1", "path": "/map-bans?bo=1", "kind": "board", "backdrop": True},
                            {"id": "map-bans-bo3", "name": "Map bans Bo3", "path": "/map-bans?bo=3", "kind": "board", "backdrop": True}]}
        return {"fields": fields, "series": series, "hud": hud}

    def _engine_apply_global(self, g, fetch):
        """The GFX Engine's teams (names, short names, logos) and sponsors into the HUD."""
        changes, done = {}, []
        for side in ("left", "right"):
            t = g.get(side) or {}
            team = {}
            if t.get("name"):
                team["name"] = t["name"]
            if t.get("short"):
                team["tricode"] = t["short"][:5]
            if t.get("logo_url"):
                try:
                    blob = fetch(t["logo_url"])
                    name = save_logo_bytes(LOGO_DIR, f"engine-{t.get('short') or t.get('name') or side}", blob)
                    team["logo"] = f"assets/logos/{name}"
                except Exception as e:
                    log(f"Couldn't fetch the {side} logo from the GFX Engine: {e}", "warn")
            if team:
                changes[side] = team
                done.append(f"{side}: {team.get('name') or team.get('tricode') or 'logo'}")
        # Its sponsors, in the HUD's sponsor rotation.
        sponsors, secs = save_sponsors(g, fetch, SPONSOR_DIR, "sponsors/", log)
        if sponsors:
            changes["sponsors"] = sponsors
            if secs:
                changes["sponsor_seconds"] = secs
            done.append(f"{len(sponsors)} sponsor{'s' if len(sponsors) != 1 else ''}")
        if not changes:
            raise ValueError("The engine's Global configuration has no team names, logos or sponsors yet")
        self.config.update(changes)
        self.refresh(fetch=False)
        return ", ".join(done)

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
        self.reader.stop()
        self.engine.stop()
        if self.server:
            self.server.stop()

    def app_info(self):
        cfg = self.config.get()
        port = self.server.port if self.server else cfg["http_port"]
        network = bool(cfg.get("allow_network"))
        lan = lan_ip() if network else None
        return {"mode": self.mode, "role": self.role, "demo_speed": self.demo_speed, "network": network, "port": port,
                "feed": self.feed.info(), "reader": self.reader.info(), "update": self.updater.info(),
                "scan": getattr(self, "last_scan", None),
                "overlay_window": self.overlay_window.info() if self.overlay_window else {"available": False},
                "lan_url": f"http://{lan}:{port}" if lan else None, "data_dir": DATA_DIR}

    def snapshot(self):
        with self._lock:
            players = list(self.state["players"])
            snap = {"game": self.state, "fields": self.fields, "updated_at": self.updated_at,
                    "config": self.config.get(), "output_dir": self.config.output_dir(), "app": self.app_info()}
        snap["cams"] = {"publishers": self.cams.publishers(players)}
        snap["agent_select"] = self.agent_select.view(players)
        snap["agent_select"]["demo"] = bool(self._select_demo and self._select_demo.running())
        snap["agent_select"]["agents"] = game.AGENTS
        cfg = snap["config"]
        pool, team_a = mapbans.settings(cfg)
        snap["map_bans"] = {"maps": mapbans.ALL_MAPS, "vct_pool": mapbans.VCT_POOL, "pool": pool, "team_a": team_a,
                            "bo1": mapbans.steps(cfg, "bo1"), "bo3": mapbans.steps(cfg, "bo3")}
        return snap

    def cam_post(self, path, body):
        """Webcam messages (also from other PCs on the network)."""
        if path == "/api/cam/poll":
            result = self.cams.poll(str(body.get("id") or ""), body.get("riot_id"), body.get("label"), body.get("wait", 20))
            if result["riot_id"]:
                with self._lock:
                    players = list(self.state["players"])
                result["player"] = next((p["player"] for p in self.cams.publishers(players)
                                         if p["id"] == body.get("id")), None)
                cfg = self.config.get()
                if result["player"]:
                    result["player"]["team_name"] = cfg[result["player"]["team"]]["name"]
            return result
        if path == "/api/cam/send":
            self.cams.send(str(body.get("to") or ""), str(body.get("from") or ""), body.get("data"))
            return {"ok": True}
        return None

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

    def save_sponsor(self, filename, data_b64):
        """Store an uploaded sponsor logo; it joins the rotation when the
        sponsors are saved. Returns its path."""
        name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(filename or "sponsor.png"))
        if os.path.splitext(name)[1].lower() not in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"):
            raise ValueError("Sponsor logos must be PNG, JPG, WEBP, GIF or SVG")
        os.makedirs(SPONSOR_DIR, exist_ok=True)
        base, ext = os.path.splitext(name)
        n = 1
        while os.path.exists(os.path.join(SPONSOR_DIR, name)):   # don't overwrite one in use
            n += 1
            name = f"{base}-{n}{ext}"
        with open(os.path.join(SPONSOR_DIR, name), "wb") as f:
            f.write(base64.b64decode(data_b64))
        return f"sponsors/{name}"

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
        folders = {"output": self.config.output_dir(), "logos": LOGO_DIR, "app": DATA_DIR, "sponsors": SPONSOR_DIR,
                   "frames": os.path.join(DATA_DIR, "frames")}
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


def find_gfx(port):
    """The GFX PCs on this network with the HUD running (and letting other
    PCs read it): [{"ip", "overlay", "teams"}]."""
    from .discover import find_huds

    def is_gfx(state):
        return "game" in state and (state.get("app") or {}).get("role") != "observer"
    out = []
    for hit in find_huds(port, is_gfx):
        cfg = hit["state"].get("config") or {}
        teams = " vs ".join(t for t in ((cfg.get("left") or {}).get("name"), (cfg.get("right") or {}).get("name")) if t)
        out.append({"ip": hit["ip"], "overlay": hit["url"] + "/overlay", "teams": teams})
    log(f"Looked for the HUD on the network: {len(out)} found" + "".join(f", {h['ip']}" for h in out))
    return out


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
            try:
                body = recolor.served(path, unquote(rel), recolor.colours(app.config.get()))
            except Exception as e:
                log(f"Couldn't recolour {rel}: {e!r}", "warn")
                body = None
            if body is not None:
                return self._send(body, ctype)
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
            elif path == "/api/observer/find":
                # Observer client: the GFX PCs running the HUD on this network.
                if not _is_local(self.client_address[0]):
                    return self._send('{"error":"forbidden"}', status=403)
                self._send(json.dumps({"huds": find_gfx(app.config.get()["http_port"])}))
            elif path in ("/overlay", "/scoreboard", "/hud", "/hud/", "/scoreboard/"):
                # The overlays are the templates in web/hud and web/scoreboard
                # (their images load relative to their own folder).
                folder = "scoreboard" if path.startswith("/scoreboard") else "hud"
                self.send_response(302)
                self.send_header("Location", f"/{folder}/Console.html" + (f"?{url.query}" if url.query else ""))
                self.end_headers()
            elif path in ("/agent-select", "/agent-select/"):
                # The chosen look (?look= to see another).
                look = (parse_qs(url.query).get("look") or [(app.config.get().get("agent_select") or {}).get("look")])[0]
                page = "/select/Console.html" if look != "champions" else "/agent-select-champions.html"
                self.send_response(302)
                self.send_header("Location", page + (f"?{url.query}" if url.query else ""))
                self.end_headers()
            elif path in ("/map-bans", "/map-bans/"):
                # The map bans graphic (?bo=1 or ?bo=3).
                self.send_response(302)
                self.send_header("Location", "/mapbans/index.html" + (f"?{url.query}" if url.query else ""))
                self.end_headers()
            elif path == "/api/map-bans":
                bo = (parse_qs(url.query).get("bo") or [str(app.config.get().get("best_of") or 3)])[0]
                self._send(json.dumps(mapbans.view(app.config.get(), bo)))
            elif path.startswith("/map-art/"):
                art = app.map_art.path(unquote(path[len("/map-art/"):]))
                if not art:
                    return self._send('{"error":"not found"}', status=404)
                with open(art, "rb") as f:
                    self._send(f.read(), mimetypes.guess_type(art)[0] or "image/png")
            elif path in ("/control", "/start", "/observer"):
                self._static(path[1:] + ".html")
            elif path == "/api/state":
                self._send(json.dumps(app.snapshot()))
            elif path == "/api/engine":
                self._send(json.dumps(app.engine.status()))
            elif path == "/api/log":
                after = int((parse_qs(url.query).get("after") or ["0"])[0])
                self._send(json.dumps(since(after)))
            elif path == "/hud.json":
                self._send(json.dumps([fields]))
            elif path == "/hud.csv":
                self._send(outputs.to_csv(fields), "text/csv; charset=utf-8")
            elif path == "/hud.xml":
                self._send(outputs.to_xml(fields), "application/xml; charset=utf-8")
            elif path == "/api/fonts":
                from . import fonts
                self._send(json.dumps({"fonts": fonts.families()}))
            elif path.startswith("/fonts/local/"):
                # An installed font, for the player cam's name and K / D / A.
                from . import fonts
                file = fonts.path_of(unquote(path[len("/fonts/local/"):]))
                if not file:
                    return self._send('{"error":"not found"}', status=404)
                with open(file, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "font/otf" if file.lower().endswith(".otf") else "font/ttf")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "max-age=3600")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/logos":
                self._send(json.dumps(app.list_logos()))
            else:
                self._static(path.lstrip("/"))

        def do_OPTIONS(self):
            # Player cams post here from the Player Cam app's own page.
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            # Other PCs may read the HUD (when allowed), but only this PC can
            # change it.
            url = urlparse(self.path)
            path = url.path
            if path in ("/api/cam/poll", "/api/cam/send"):
                length = int(self.headers.get("Content-Length") or 0)
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                    return self._send(json.dumps(app.cam_post(path, body)))
                except (ValueError, TypeError, AttributeError) as e:
                    return self._send(json.dumps({"error": str(e)}), status=400)
            # An observer PC's screen reader sends its readings here.
            lan_feed = path == "/api/ingest" and app.config.get().get("allow_network")
            if not _is_local(self.client_address[0]) and not lan_feed:
                return self._send('{"error":"Changes can only be made on the HUD PC"}', status=403)
            length = int(self.headers.get("Content-Length") or 0)
            if path.startswith("/api/engine/"):
                # Connect to GFX Engine (see enginelink.py).
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                    reply = app.engine.handle("POST", path, body)
                    if reply is None:
                        return self._send('{"error":"not found"}', status=404)
                    return self._send(json.dumps(reply))
                except (ValueError, TypeError, KeyError, OSError) as e:
                    return self._send(json.dumps({"error": str(e)}), status=400)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                if path == "/api/config":
                    app.config.update(body)
                elif path == "/api/sponsor":
                    saved = app.save_sponsor(body.get("filename"), body["data"])
                    return self._send(json.dumps({"path": saved}))
                elif path == "/api/sponsors":
                    sponsors = [str(p) for p in body.get("sponsors", []) if web_file(str(p))]
                    seconds = max(1.0, min(60.0, float(body.get("seconds") or 4)))
                    app.config.update({"sponsors": sponsors, "sponsor_seconds": seconds})
                    log(f"Sponsors saved: {len(sponsors)} logo(s), {seconds:g} s each" if sponsors
                        else "Sponsors saved: the template's own logos")
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
                    return self._send(json.dumps(app.ingest(body)))
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
                elif path == "/api/reader/names":
                    names, missed = app.reader.scan_names()
                    current = app.config.get()["player_names"]
                    new = {side: [names[side].get(i + 1) or current[side][i] for i in range(5)] for side in ("left", "right")}
                    app.config.update({"player_names": new})
                    found = sum(len(v) for v in names.values())
                    log(f"Scanned names: {found} of 10 placed"
                        + (f"; couldn't tell whose: {', '.join(missed)}" if missed else ""))
                    app.last_scan = {"found": found, "missed": missed}
                elif path == "/api/reader/save":
                    saved = app.reader.save_frame(os.path.join(DATA_DIR, "frames"))
                    log(f"Saved the screen and what was read from it: {saved}")
                    app.open_folder("frames")
                elif path == "/api/reader/spectate":
                    app.reader.set_spectate(body.get("enabled"))
                elif path == "/api/reader":
                    app.set_reader(body.get("enabled"))
                elif path == "/api/agent-select":
                    app.agent_select_update(body, "control panel")
                elif path == "/api/agent-select/demo":
                    app.agent_select_demo(bool(body.get("on")))
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
    if app.config.get().get("screen_reader"):
        app.reader.set_enabled(True)
    clean_up_old_update()
    app.updater.check_in_background()
    from . import fonts
    threading.Thread(target=fonts.installed, daemon=True).start()   # (the font list, ready for the panel)
    threading.Thread(target=app.run_poller, daemon=True).start()
    log(f"VALORANT HUD {app.updater.current} running - control panel http://localhost:{port}/control")
    log(f"Overlay (browser source, 1920x1080): http://localhost:{port}/overlay")
    log(f"vMix data source: http://localhost:{port}/hud.csv  - file: {app.config.output_dir()}")
    return app.server
