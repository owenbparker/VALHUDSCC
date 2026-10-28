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
import difflib
import re

SIDES = ("left", "right")

# Agent folder names in web/hud/Resources/Agentes (KAY/O is "Kayo").
AGENTS = ["Astra", "Breach", "Brimstone", "Chamber", "Clove", "Cypher", "Deadlock", "Fade", "Gekko", "Harbor",
          "Iso", "Jett", "Kayo", "Killjoy", "Miks", "Neon", "Omen", "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova",
          "Tejo", "Veto", "Viper", "Vyse", "Waylay", "Yoru"]

# Ultimate points needed (only a fallback: live data gives the real value).
ULT_MAX = {"Astra": 7, "Breach": 8, "Brimstone": 8, "Chamber": 8, "Clove": 8, "Cypher": 6, "Deadlock": 7,
           "Fade": 8, "Gekko": 8, "Harbor": 7, "Iso": 7, "Jett": 8, "Kayo": 8, "Killjoy": 9, "Miks": 8, "Neon": 8,
           "Omen": 7, "Phoenix": 6, "Raze": 8, "Reyna": 7, "Sage": 8, "Skye": 8, "Sova": 8, "Tejo": 8, "Veto": 8,
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


# A 2v2 on the spectator top bar: each team's two players sit next to the
# score, in the left team's seats 4 and 5 and the right team's 1 and 2. The
# HUD shows them as each team's players 1 and 2.
SEATS_2V2 = {("left", 4): 1, ("left", 5): 2, ("right", 1): 1, ("right", 2): 2}


def two_a_side(update):
    """A screen reading (seats as on the top bar) with a 2v2's seats moved to
    players 1 and 2 of each team, and the empty seats left out."""
    out = dict(update)
    if isinstance(update.get("players"), list):
        out["players"] = [dict(p, slot=SEATS_2V2[(p.get("team"), p.get("slot"))]) for p in update["players"]
                          if isinstance(p, dict) and (p.get("team"), p.get("slot")) in SEATS_2V2]
    spike = (update.get("match") or {}).get("spike")
    if isinstance(spike, dict) and spike.get("carrier"):
        seat = SEATS_2V2.get(tuple(spike["carrier"]))
        out["match"] = dict(update["match"], spike=dict(spike, carrier=[spike["carrier"][0], seat] if seat else None))
    return out


def round_won(state, update):
    """The update with this round added to the round history when its score
    is one round on from the state's (for screens whose history isn't read,
    e.g. a 2v2's Tab scoreboard). How it was won is told from the spike."""
    m, new = state.get("match") or {}, (update.get("match") or {}).get("score")
    if not isinstance(new, dict) or "rounds" in update["match"]:
        return update
    old, rounds = m.get("score") or {}, list(m.get("rounds") or [])
    up = [side for side in SIDES if (new.get(side) or 0) == (old.get(side) or 0) + 1]
    others = [side for side in SIDES if side not in up and (new.get(side) or 0) == (old.get(side) or 0)]
    if len(up) != 1 or len(others) != 1 or len(rounds) != sum(old.get(side) or 0 for side in SIDES):
        return update
    winner, spike = up[0], (m.get("spike") or {}).get("state")
    how = ("Detonation" if winner == m.get("attackers") else "Deactivation") if spike in ("planted", "defused", "detonated") \
        else "Elimination"
    return dict(update, match=dict(update["match"], rounds=rounds + [{"winner": winner, "win_type": how}]))


def empty_player(team, slot):
    return {"team": team, "slot": slot, "name": "", "agent": "", "alive": True, "health": 100, "shield": 0,
            "regen_shield": False, "credits": 800, "weapon": "Classic", "kills": 0, "deaths": 0, "assists": 0,
            "ult_points": 0, "ult_max": 7, "abilities": {"C": [0, 1], "Q": [0, 1], "E": [0, 1]}, "spike": False}


def empty_state():
    return {"connected": False,
            "match": {"map": "", "round": 0, "phase": "", "timer": 0, "score": {"left": 0, "right": 0},
                      "attackers": "left", "spike": {"state": "", "timer": 0, "carrier": None},
                      "round_winner": "", "win_type": "", "rounds": [],
                      "observed": None},   # {"team", "slot"}: who the observer is spectating
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
    o = m.get("observed", False)
    if o is None or (isinstance(o, dict) and o.get("team") in SIDES and o.get("slot") in range(1, 6)):
        out["match"]["observed"] = {"team": o["team"], "slot": o["slot"]} if o else None
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


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def observed_player(state, text):
    """{"team", "slot"} of the player whose name is in `text` (what the
    observer client read by the spectated player's health, team tag and all),
    or None. Close spellings count (text recognition slips a letter)."""
    words = [_norm(w) for w in re.split(r"[\s/|]+", str(text or ""))]
    words = [w for w in words if w]
    if not words:
        return None
    joined = "".join(words)
    best, best_score = None, 0.0
    for p in state["players"]:
        name = _norm(p["name"])
        if len(name) < 2:
            continue
        if name in joined and (len(name) >= 3 or name in words):
            score = 1.0 + len(name) / 100   # the longest name inside wins
        else:
            # The name against each run of words (names can have spaces).
            parts = [_norm(w) for w in str(p["name"]).split()] or [name]
            k = max(1, len(parts))
            score = max((difflib.SequenceMatcher(None, name, "".join(words[i:i + k])).ratio()
                         for i in range(len(words))), default=0.0)
        if score > best_score:
            best, best_score = p, score
    if best is None or best_score < 0.8:
        return None
    return {"team": best["team"], "slot": best["slot"]}


def observed_by_agent(state, agent, side=None):
    """{"team", "slot"} of the player on that agent ("attackers" /
    "defenders" says which team when both have one), or None."""
    agent = agent_name(agent) if agent else ""
    if not agent:
        return None
    attackers = state["match"].get("attackers") or "left"
    team = {"attackers": attackers, "defenders": "right" if attackers == "left" else "left"}.get(side)
    found = [p for p in state["players"] if p.get("agent") == agent and (team is None or p["team"] == team)]
    return {"team": found[0]["team"], "slot": found[0]["slot"]} if len(found) == 1 else None


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
