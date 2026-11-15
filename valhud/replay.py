"""Replay report: how well the reader read a recorded match, checked against
Riot's own record of it (the answer key, answerkey.py).

    python -m valhud.replay recordings/20261115-193012-Lotus
    python -m valhud.replay recordings/*  --json report.json

For each recording with a match-details.json it scores the readings the HUD
got live (events.jsonl): did the score show every real score, and nothing
else; were each player's kills / deaths / assists right after each round;
were the names right. Later readers are scored the same way by replaying the
recording's frames through them (score_readings takes any list of readings),
so a fix only ships if its numbers go up.
"""

import argparse
import glob
import json
import os
import sys

from .answerkey import AnswerKey

SETTLE = 3.0   # seconds after a round's score shows that its K/D/A are checked


def load_readings(folder):
    """[(t, update)] from a recording's events.jsonl (screen readings only)."""
    out = []
    path = os.path.join(folder, "events.jsonl")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                d = e.get("data")
                if e.get("kind") == "reading" and isinstance(d, dict) and d.get("source") in ("screen", None):
                    out.append((float(e.get("t") or 0), d))
    except OSError:
        pass
    return out


def _norm(name):
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def which_side(readings, key):
    """{"left": "Red"/"Blue", "right": ...}: the team whose agents the top bar
    shows on that side (most readings agreeing)."""
    seen = {"left": {}, "right": {}}
    for _, u in readings:
        for p in u.get("players") or []:
            if p.get("agent") and p.get("team") in seen:
                seen[p["team"]][(p["team"], p.get("slot"))] = p["agent"]
    left = sorted(seen["left"].values())
    red, blue = key.team_agents("Red"), key.team_agents("Blue")
    overlap = lambda a, b: sum(min(a.count(x), b.count(x)) for x in set(a))
    if overlap(left, red) >= overlap(left, blue):
        return {"left": "Red", "right": "Blue"}
    return {"left": "Blue", "right": "Red"}


def seat_players(readings, key, sides):
    """(side, slot) -> puuid, by agent (agents are unique within a team)."""
    agents = {}
    for _, u in readings:
        for p in u.get("players") or []:
            if p.get("agent") and p.get("team") in sides:
                agents[(p["team"], p["slot"])] = p["agent"]
    out = {}
    for seat, agent in agents.items():
        team = sides[seat[0]]
        match = [pid for pid, p in key.players.items() if p["team"] == team and p["agent"] == agent]
        if len(match) == 1:
            out[seat] = match[0]
    return out


def score_readings(readings, key):
    """The report for one list of readings against the key."""
    sides = which_side(readings, key)
    seats = seat_players(readings, key, sides)
    n_rounds = len(key.rounds)
    real = [key.score_after(n) for n in range(n_rounds + 1)]
    real_lr = [(s[sides["left"]], s[sides["right"]]) for s in real]

    # Score: every score the HUD showed, in order (repeats dropped).
    shown, first_at = [], {}
    for t, u in readings:
        s = (u.get("match") or {}).get("score")
        if not s or s.get("left") is None or s.get("right") is None:
            continue
        v = (int(s["left"]), int(s["right"]))
        if not shown or shown[-1] != v:
            shown.append(v)
        first_at.setdefault(v, t)
    wrong = [v for v in shown if v not in real_lr]
    rounds_shown = sum(1 for v in real_lr[1:] if v in first_at)

    # K/D/A: a few seconds after each round's score first shows.
    latest, timeline = {}, []
    for t, u in readings:
        for p in u.get("players") or []:
            seat = (p.get("team"), p.get("slot"))
            if all(p.get(k) is not None for k in ("kills", "deaths", "assists")):
                latest[seat] = [int(p["kills"]), int(p["deaths"]), int(p["assists"])]
        timeline.append((t, {k: list(v) for k, v in latest.items()}))
    checked = right = 0
    kill_error = 0
    per_round = []
    for n in range(1, n_rounds + 1):
        at = first_at.get(real_lr[n])
        if at is None:
            continue
        snap = None
        for t, state in timeline:
            if t > at + SETTLE:
                break
            snap = state
        if not snap:
            continue
        truth = key.kda_after(n)
        ok = 0
        for seat, pid in seats.items():
            if seat in snap:
                checked += 1
                if snap[seat] == truth[pid]:
                    right += 1
                    ok += 1
                kill_error += abs(snap[seat][0] - truth[pid][0])
        per_round.append({"round": n, "players_right": ok, "players": len(seats)})

    # Names: the last name each seat had.
    names = {}
    for _, u in readings:
        for p in u.get("players") or []:
            if p.get("name"):
                names[(p.get("team"), p.get("slot"))] = p["name"]
    name_right = sum(1 for seat, pid in seats.items() if _norm(names.get(seat)) == _norm(key.players[pid]["name"]))

    return {
        "rounds": n_rounds, "sides": sides, "players_matched": len(seats),
        "score": {"rounds_shown": rounds_shown, "wrong_scores_shown": len(wrong), "wrong": wrong[:20]},
        "kda": {"checked": checked, "right": right, "kill_error": kill_error, "per_round": per_round},
        "names": {"right": name_right, "of": len(seats)},
    }


def report(folder, agents=None):
    details = os.path.join(folder, "match-details.json")
    if not os.path.isfile(details):
        return {"recording": os.path.basename(folder), "error": "no match-details.json (no answer key)"}
    key = AnswerKey.load(details, agents)
    out = score_readings(load_readings(folder), key)
    out["recording"] = os.path.basename(folder.rstrip("/\\"))
    return out


def summary(r):
    if r.get("error"):
        return f"{r['recording']}: {r['error']}"
    s, k, n = r["score"], r["kda"], r["names"]
    pct = lambda a, b: f"{100 * a / b:.0f}%" if b else "-"
    return (f"{r['recording']}: score showed {s['rounds_shown']} of {r['rounds']} rounds, "
            f"{s['wrong_scores_shown']} wrong scores shown; K/D/A right {pct(k['right'], k['checked'])} "
            f"({k['kill_error']} kills off in total); names right {n['right']} of {n['of']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--agents", help="riot-agents.json (agent ids -> names), from the app's folder")
    ap.add_argument("--json", help="write the full report here")
    a = ap.parse_args(argv)
    agents = None
    if a.agents:
        with open(a.agents, encoding="utf-8") as f:
            agents = json.load(f)
    folders = [p for pat in a.recordings for p in (glob.glob(pat) or [pat]) if os.path.isdir(p)]
    reports = [report(f, agents) for f in folders]
    for r in reports:
        print(summary(r))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
