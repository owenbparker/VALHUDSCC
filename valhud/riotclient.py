"""Agent select and the roster from the Riot Client's local API, on the PC
that runs VALORANT (unofficial: the same calls the game's menus and
community tools like rank checkers make).

What it gives, sent through the screen reader's path to the HUD:
  agent select: every player's Riot ID, agent, locked or not, the map and the
      timer -> {"source": "riot", "agent_select": {...}}
  in the match: each player's Riot ID by team and agent, and the map
      -> {"source": "riot", "riot_roster": {"left": [{"name", "agent"}], ...},
          "match": {"map": ...}}
It has nothing live from the round (alive, health, kills, credits): those
stay with the screen reader.

How: the Riot Client's lockfile gives a local port and password; the local
API gives the account (PUUID), its tokens and the region; the game servers
(glz-<region>-1.<shard>.a.pvp.net) give the pregame and in-game match; the
name service turns PUUIDs into Riot IDs. Agent ids come from valorant-api.com.
Red is the team that attacks first.
"""

import base64
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

from . import game

# Internal map names (MapID's last part) -> ours.
MAP_IDS = {"Infinity": "Abyss", "Triad": "Haven", "Duality": "Bind", "Bonsai": "Split", "Ascent": "Ascent",
           "Port": "Icebox", "Foxtrot": "Breeze", "Canyon": "Fracture", "Pitt": "Pearl", "Jam": "Lotus",
           "Juliett": "Sunset", "Rook": "Corrode", "Range": "Range", "HURM_Alley": "District",
           "HURM_Yard": "Piazza", "HURM_Bowl": "Kasbah", "HURM_Helix": "Drift", "HURM_HighTide": "Glitch"}

PLATFORM = base64.b64encode(json.dumps({
    "platformType": "PC", "platformOS": "Windows", "platformOSVersion": "10.0.19042.1.256.64bit",
    "platformChipset": "Unknown"}).encode()).decode()


def lockfile_path():
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Riot Games", "Riot Client", "Config", "lockfile")


def read_lockfile(path=None):
    """(port, password) from the Riot Client's lockfile, or None."""
    try:
        with open(path or lockfile_path(), encoding="utf-8") as f:
            parts = f.read().strip().split(":")
        return int(parts[2]), parts[3]
    except (OSError, IndexError, ValueError):
        return None


def map_from_id(map_id):
    """"/Game/Maps/Ascent/Ascent" -> "Ascent"; "/Game/Maps/Triad/Triad" -> "Haven"."""
    code = str(map_id or "").rstrip("/").split("/")[-1]
    return MAP_IDS.get(code, "")


def region_of(sessions):
    """(region, shard) from the game's launch arguments (product-session)."""
    for s in (sessions or {}).values() if isinstance(sessions, dict) else []:
        if not isinstance(s, dict) or s.get("productId") != "valorant":
            continue
        args = (s.get("launchConfiguration") or {}).get("arguments") or []
        region = shard = None
        for a in args:
            if a.startswith("-ares-deployment="):
                region = a.split("=", 1)[1]
            elif a.startswith("-config-endpoint="):
                host = a.split("://", 1)[-1]
                parts = host.split(".")
                if len(parts) > 2 and parts[0] == "shared":
                    shard = parts[1]
        if region:
            shard = shard or {"latam": "na", "br": "na"}.get(region, region)
            return region, shard
    return None


def _side(team_id, attack_first):
    """Red attacks first: it's the side set to attack first."""
    other = "right" if attack_first == "left" else "left"
    return attack_first if str(team_id).lower() == "red" else other if str(team_id).lower() == "blue" else None


def select_reading(match, agents, names, attack_first="left"):
    """A pregame match -> an agent select reading for AgentSelect.apply."""
    players, slots = [], {"left": 0, "right": 0}
    teams = match.get("Teams") or []
    if not teams and isinstance(match.get("AllyTeam"), dict):
        teams = [match["AllyTeam"]]
    for team in teams:
        side = _side(team.get("TeamID"), attack_first)
        if not side:
            continue
        for p in team.get("Players") or []:
            slots[side] += 1
            if slots[side] > 5:
                break
            agent = agents.get(str(p.get("CharacterID") or "").lower(), "")
            state = str(p.get("CharacterSelectionState") or "").lower()
            q = {"team": side, "slot": slots[side], "agent": agent, "locked": state == "locked" and bool(agent)}
            name = names.get(p.get("Subject"))
            if name:
                q["name"] = name
            players.append(q)
    reading = {"active": True, "players": players}
    m = map_from_id(match.get("MapID"))
    if m:
        reading["map"] = m
    ns = match.get("PhaseTimeRemainingNS")
    if isinstance(ns, (int, float)) and ns > 0:
        reading["timer"] = ns / 1e9
    return reading


def roster(match, agents, names, attack_first="left"):
    """An in-game match -> {"left": [{"name", "agent"}], "right": [...]}."""
    out = {"left": [], "right": []}
    for p in match.get("Players") or []:
        side = _side(p.get("TeamID"), attack_first)
        if not side or (p.get("PlayerIdentity") or {}).get("IsObserver"):
            continue
        out[side].append({"name": names.get(p.get("Subject"), ""),
                          "agent": agents.get(str(p.get("CharacterID") or "").lower(), "")})
    return out


class RiotClient:
    """Polls the Riot Client and hands each reading to `send`."""

    EVERY = 1.0
    INGAME_EVERY = 5.0

    def __init__(self, send, config, cache_dir, log=None):
        self.send, self.config, self.cache_dir = send, config, cache_dir
        self.log = log or (lambda *a, **k: None)
        self.status = "off"
        self.sent_at = 0.0
        self._stop = threading.Event()
        self._thread = None
        self._local = None       # (port, password)
        self._auth = None        # (access token, entitlement, puuid, got at)
        self._region = None
        self._version = None
        self._agents = None
        self._names = {}
        self._was = ""           # "pregame" / "ingame" / ""
        self._ingame_at = 0.0
        self._ctx = ssl.create_default_context()
        self._local_ctx = ssl._create_unverified_context()   # (the Riot Client's own certificate, on 127.0.0.1)

    def start(self):
        if sys.platform != "win32" or (self._thread and self._thread.is_alive()):
            if sys.platform != "win32":
                self.status = "Only on Windows"
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def info(self):
        return {"status": self.status, "age": round(time.time() - self.sent_at, 1) if self.sent_at else None}

    # --- requests -------------------------------------------------------------

    def _get(self, url, headers=None, local=False, method="GET", body=None, timeout=4):
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers=dict(headers or {}, **({"Content-Type": "application/json"} if body is not None else {})),
                                     method=method)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                             urllib.request.HTTPSHandler(context=self._local_ctx if local else self._ctx))
        with opener.open(req, timeout=timeout) as r:
            return json.loads(r.read() or b"null")

    def _local_get(self, path):
        port, password = self._local
        auth = base64.b64encode(f"riot:{password}".encode()).decode()
        return self._get(f"https://127.0.0.1:{port}{path}", {"Authorization": f"Basic {auth}"}, local=True)

    def _headers(self):
        token, ent, _, _ = self._auth
        return {"Authorization": f"Bearer {token}", "X-Riot-Entitlements-JWT": ent,
                "X-Riot-ClientPlatform": PLATFORM, "X-Riot-ClientVersion": self._version or ""}

    def _glz(self, path):
        region, shard = self._region
        return self._get(f"https://glz-{region}-1.{shard}.a.pvp.net{path}", self._headers())

    # --- what's needed once -------------------------------------------------------

    def _load_agents(self):
        """Agent uuid -> our name (valorant-api.com, kept in a file for next time)."""
        path = os.path.join(self.cache_dir, "riot-agents.json")
        try:
            data = self._get("https://valorant-api.com/v1/agents?isPlayableCharacter=true", timeout=8)["data"]
            agents = {a["uuid"].lower(): game.agent_name(a["displayName"]) for a in data}
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(agents, f)
            except OSError:
                pass
            return agents
        except Exception:
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError):
                return None

    def _load_version(self):
        try:
            return self._get("https://valorant-api.com/v1/version", timeout=8)["data"]["riotClientVersion"]
        except Exception:
            return None

    def _ready(self):
        """Everything needed to ask the game servers, or the reason it isn't there."""
        local = read_lockfile()
        if not local:
            self._local = self._auth = self._region = None
            return "Riot Client not running"
        if local != self._local:
            self._local, self._auth, self._region = local, None, None
        if not self._auth or time.time() - self._auth[3] > 240:
            t = self._local_get("/entitlements/v1/token")
            self._auth = (t["accessToken"], t["token"], t["subject"], time.time())
        if not self._region:
            self._region = region_of(self._local_get("/product-session/v1/external-sessions"))
            if not self._region:
                return "VALORANT not running"
        if self._agents is None:
            self._agents = self._load_agents()
            if self._agents is None:
                return "Couldn't get the agent list (valorant-api.com)"
        if not self._version:
            self._version = self._load_version()
        return None

    def _name_all(self, subjects):
        missing = [s for s in subjects if s and s not in self._names]
        if not missing:
            return
        _, shard = self._region
        try:
            rows = self._get(f"https://pd.{shard}.a.pvp.net/name-service/v2/players", self._headers(),
                             method="PUT", body=missing)
            for r in rows or []:
                if r.get("GameName"):
                    self._names[r["Subject"]] = r["GameName"]   # (no tag: the HUD shows names without)
        except Exception:
            pass

    # --- the loop -------------------------------------------------------------------

    def _match_id(self, kind):
        _, _, puuid, _ = self._auth
        try:
            return (self._glz(f"/{kind}/v1/players/{puuid}") or {}).get("MatchID")
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return None   # (not in one)
            raise

    def _step(self):
        why = self._ready()
        if why:
            if self._was == "pregame":
                self.send({"source": "riot", "agent_select": {"active": False}})
            self._was = ""
            return why
        attack_first = self.config.get().get("attack_first") or "left"
        pre = self._match_id("pregame")
        if pre:
            match = self._glz(f"/pregame/v1/matches/{pre}")
            subjects = [p.get("Subject") for t in (match.get("Teams") or [match.get("AllyTeam") or {}])
                        for p in (t.get("Players") or [])]
            self._name_all(subjects)
            self.send({"source": "riot", "agent_select": select_reading(match, self._agents, self._names, attack_first)})
            if self._was != "pregame":
                self.log("Riot Client: agent select")
            self._was, self.sent_at = "pregame", time.time()
            return "Agent select"
        if self._was == "pregame":
            self.send({"source": "riot", "agent_select": {"active": False}})
        if time.time() - self._ingame_at < self.INGAME_EVERY and self._was == "ingame":
            return "In a match"
        self._ingame_at = time.time()
        core = self._match_id("core-game")
        if not core:
            self._was = ""
            return "Not in a match"
        match = self._glz(f"/core-game/v1/matches/{core}")
        self._name_all([p.get("Subject") for p in match.get("Players") or []])
        update = {"source": "riot", "riot_roster": roster(match, self._agents, self._names, attack_first)}
        m = map_from_id(match.get("MapID"))
        if m and m != "Range":
            update["match"] = {"map": m}
        self.send(update)
        if self._was != "ingame":
            self.log("Riot Client: in a match, roster read")
        self._was, self.sent_at = "ingame", time.time()
        return "In a match"

    def _run(self):
        last = None
        while not self._stop.is_set():
            try:
                self.status = self._step()
            except urllib.error.HTTPError as e:
                self.status = f"Riot servers answered {e.code}"
                if e.code in (400, 401, 403):
                    self._auth = None   # (a stale token or client version: get them again)
                    self._version = None
            except Exception as e:
                self.status = f"Riot Client read failed: {e!r}"[:200]
            if self.status != last:
                if last is not None and ("failed" in self.status or "answered" in self.status):
                    self.log(self.status, "warn")
                last = self.status
            self._stop.wait(self.EVERY if self._was == "pregame" else 2.0)
