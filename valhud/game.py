"""The VALORANT game state the HUD draws, and the flat fields for vMix.

A state is a dict:
    {"connected": bool,
     "match": {"map", "round", "phase" ("buy" / "combat" / "end" / ""),
               "timer" (seconds left in the phase), "score": {"left", "right"},
               "attackers" ("left" / "right"), "spike": {"state" ("" / "carried" /
               "planted" / "defused" / "detonated"), "timer", "carrier"},
               "round_winner", "win_type" ("Elimination" / "Detonation" /
               "Deactivation" / "Time"), "rounds": [{"winner", "win_type"}, ...]},
     "players": [10 players: left team slots 1-5, then right team slots 1-5]}

and each player is
    {"team", "slot", "name", "agent", "alive", "health", "shield" (0/25/50),
     "regen_shield" (bool), "credits", "weapon", "kills", "deaths", "assists",
     "ult_points", "ult_max", "abilities": {"C": [charges, max], "Q": [...],
     "E": [...]}, "spike" (carrying it)}

Live data arrives as partial updates (see merge()), from the demo game, the
screen reader or anything that POSTs to /api/ingest.
"""

import copy

SIDES = ("left", "right")

# Agent folder names in web/hud/Resources/Agentes (KAY/O is "Kayo").
AGENTS = ["Astra", "Breach", "Brimstone", "Chamber", "Clove", "Cypher", "Deadlock", "Fade", "Gekko", "Harbor",
          "Iso", "Jett", "Kayo", "Killjoy", "Miks", "Neon", "Omen", "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova",
          "Tejo", "Viper", "Vyse", "Waylay", "Yoru"]

# Ultimate points needed (only a fallback: live data gives the real value).
ULT_MAX = {"Astra": 7, "Breach": 8, "Brimstone": 8, "Chamber": 8, "Clove": 8, "Cypher": 6, "Deadlock": 7,
           "Fade": 8, "Gekko": 8, "Harbor": 7, "Iso": 7, "Jett": 8, "Kayo": 8, "Killjoy": 9, "Miks": 8, "Neon": 8,
           "Omen": 7, "Phoenix": 6, "Raze": 8, "Reyna": 7, "Sage": 8, "Skye": 8, "Sova": 8, "Tejo": 8,
           "Viper": 9, "Vyse": 8, "Waylay": 8, "Yoru": 8}

# Weapon image names in web/hud/Resources/Armas, with their price.
WEAPONS = {"Classic": 0, "Shorty": 300, "Frenzy": 450, "Ghost": 500, "Sheriff": 800, "Stinger": 1100,
           "Spectre": 1600, "Bucky": 850, "Judge": 1850, "Bulldog": 2050, "Guardian": 2250, "Phantom": 2900,
           "Vandal": 2900, "Marshal": 950, "Outlaw": 2400, "Operator": 4700, "Ares": 1600, "Odin": 3200,
           # Added to the game in 2025; its HUD image is traced from a spectator frame.
           "Bandit": 600}

_AGENT_LOOKUP = {a.lower(): a for a in AGENTS} | {"kay/o": "Kayo", "kay-o": "Kayo", "kayo": "Kayo"}
_WEAPON_LOOKUP = {w.lower(): w for w in WEAPONS} | {"melee": "Knife", "knife": "Knife"}


def agent_name(text):
    """Our folder name for an agent, from whatever spelling a feed uses."""
    return _AGENT_LOOKUP.get(str(text or "").strip().lower(), str(text or "").strip())


def weapon_name(text):
    return _WEAPON_LOOKUP.get(str(text or "").strip().lower(), str(text or "").strip())


def empty_player(team, slot):
    return {"team": team, "slot": slot, "name": "", "agent": "", "alive": True, "health": 100, "shield": 0,
            "regen_shield": False, "credits": 800, "weapon": "Classic", "kills": 0, "deaths": 0, "assists": 0,
            "ult_points": 0, "ult_max": 7, "abilities": {"C": [0, 1], "Q": [0, 1], "E": [0, 1]}, "spike": False}


def empty_state():
    return {"connected": False,
            "match": {"map": "", "round": 0, "phase": "", "timer": 0, "score": {"left": 0, "right": 0},
                      "attackers": "left", "spike": {"state": "", "timer": 0, "carrier": None},
                      "round_winner": "", "win_type": "", "rounds": []},
            "players": [empty_player(t, s) for t in SIDES for s in range(1, 6)]}


def _clamp(v, lo, hi):
    try:
        return max(lo, min(hi, int(round(float(v)))))
    except (TypeError, ValueError):
        return lo


def merge(state, update):
    """Apply a partial update to a state (returns a new state). An update
    looks like {"match": {...any match keys...}, "players": [{"team": "left",
    "slot": 1, ...any player keys...}, ...]}. Unknown keys are ignored."""
    out = copy.deepcopy(state)
    m = update.get("match") or {}
    for key in ("map", "round", "phase", "timer", "attackers", "round_winner", "win_type", "rounds"):
        if key in m:
            out["match"][key] = m[key]
    for key in ("score", "spike"):
        if isinstance(m.get(key), dict):
            out["match"][key].update(m[key])
    # Never more rounds of history than have been played (a new game starts
    # at 0-0; history read before it is dropped).
    played = sum(int(v or 0) for v in out["match"]["score"].values())
    if len(out["match"].get("rounds") or []) > played:
        out["match"]["rounds"] = out["match"]["rounds"][:played]
    for p in update.get("players") or []:
        team, slot = p.get("team"), p.get("slot")
        if team not in SIDES or not isinstance(slot, int) or not 1 <= slot <= 5:
            continue
        target = out["players"][SIDES.index(team) * 5 + slot - 1]
        for key, value in p.items():
            if key in ("team", "slot") or key not in target:
                continue
            if key == "agent":
                value = agent_name(value)
                if value in ULT_MAX and "ult_max" not in p:
                    target["ult_max"] = ULT_MAX[value]
            elif key == "weapon":
                value = weapon_name(value)
            elif key == "health":
                value = _clamp(value, 0, 100)
            elif key == "shield":
                value = 50 if _clamp(value, 0, 50) >= 50 else 25 if _clamp(value, 0, 50) > 0 else 0
            elif key == "abilities":
                value = {k: list(v) for k, v in {**target["abilities"], **value}.items() if k in ("C", "Q", "E")}
            target[key] = value
        if "health" in p and "alive" not in p:
            target["alive"] = target["health"] > 0
    return out


def with_overrides(state, cfg):
    """Names typed in the control panel replace the feed's."""
    out = copy.deepcopy(state)
    names = cfg.get("player_names") or {}
    for p in out["players"]:
        typed = names.get(p["team"]) or []
        typed = typed[p["slot"] - 1].strip() if p["slot"] <= len(typed) else ""
        if typed:
            p["name"] = typed
    return out


def fields(state, cfg):
    """Flat name -> value fields for vMix / GT Title Designer (CSV, JSON, XML)."""
    m = state["match"]
    f = {"CONNECTED": "LIVE" if state["connected"] else "WAITING", "MAP": m["map"], "ROUND": m["round"],
         "PHASE": m["phase"].upper(), "TIMER": f"{int(m['timer']) // 60}:{int(m['timer']) % 60:02d}",
         "SPIKE": m["spike"]["state"].upper(), "ROUND WINNER": m["round_winner"].upper(), "WIN TYPE": m["win_type"]}
    for side in SIDES:
        S = side.upper()
        team = cfg[side]
        f[f"TEAM {S}"] = team["name"]
        f[f"TRI-CODE {S}"] = team["tricode"]
        f[f"TEAM LOGO {S}"] = team["logo"]
        f[f"SCORE {S}"] = m["score"][side]
        f[f"SERIES {S}"] = team.get("wins", 0)
        f[f"SIDE {S}"] = "ATK" if m["attackers"] == side else "DEF"
        f[f"ALIVE {S}"] = sum(1 for p in state["players"] if p["team"] == side and p["alive"])
        f[f"CREDITS {S}"] = sum(p["credits"] for p in state["players"] if p["team"] == side)
    for p in state["players"]:
        k = f"{p['team'].upper()} P{p['slot']}"
        f[f"{k} NAME"] = p["name"]
        f[f"{k} AGENT"] = p["agent"]
        f[f"{k} ALIVE"] = "1" if p["alive"] else "0"
        f[f"{k} HP"] = p["health"] if p["alive"] else 0
        f[f"{k} SHIELD"] = p["shield"]
        f[f"{k} CREDITS"] = p["credits"]
        f[f"{k} WEAPON"] = p["weapon"]
        f[f"{k} K"] = p["kills"]
        f[f"{k} D"] = p["deaths"]
        f[f"{k} A"] = p["assists"]
        f[f"{k} ULT"] = f"{p['ult_points']}/{p['ult_max']}"
        f[f"{k} AGENT IMAGE"] = f"hud/Resources/Agentes/{p['agent']}/{p['agent']}.png" if p["agent"] else ""
    return f
