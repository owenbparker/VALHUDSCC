"""The answer key for a recorded match: Riot's own record of the finished
match (match-details.json, fetched by riotclient.py after the match), turned
into what the HUD should have shown.

    key = AnswerKey.load("recordings/20261115-193012-Lotus/match-details.json")
    key.score_after(5)   -> {"Red": 3, "Blue": 2}
    key.kda_after(5)     -> {puuid: [kills, deaths, assists]}
    key.players          -> {puuid: {"name", "tag", "team", "agent"}}

Rounds are counted from 1 (Riot's roundNum starts at 0). Red attacks first.
"""

import json

TEAMS = ("Red", "Blue")


class AnswerKey:
    def __init__(self, details, agents=None):
        agents = {str(k).lower(): v for k, v in (agents or {}).items()}
        info = details.get("matchInfo") or {}
        self.match_id = info.get("matchId")
        self.map_id = info.get("mapId")
        self.players = {}
        for p in details.get("players") or []:
            team = p.get("teamId")
            if team not in TEAMS:
                continue   # (observers, coaches)
            self.players[p["subject"]] = {
                "name": p.get("gameName") or "", "tag": p.get("tagLine") or "", "team": team,
                "agent": agents.get(str(p.get("characterId") or "").lower(), str(p.get("characterId") or "")),
                "final": [(p.get("stats") or {}).get(k) for k in ("kills", "deaths", "assists")]}
        self.rounds = []
        score = {t: 0 for t in TEAMS}
        for r in sorted(details.get("roundResults") or [], key=lambda r: r.get("roundNum", 0)):
            winner = r.get("winningTeam")
            if winner in score:
                score[winner] += 1
            self.rounds.append({"n": r.get("roundNum", 0) + 1, "winner": winner, "result": r.get("roundResult"),
                                "score": dict(score)})
        self.kills = []
        kills = details.get("kills")
        if kills is None:   # (older answers: kills only inside each round's player stats)
            kills = [dict(k, round=r.get("roundNum", 0)) for r in details.get("roundResults") or []
                     for ps in r.get("playerStats") or [] for k in ps.get("kills") or []]
        for k in kills:
            self.kills.append({"round": int(k.get("round", 0)) + 1, "time": k.get("roundTime"),
                               "killer": k.get("killer"), "victim": k.get("victim"),
                               "assistants": list(k.get("assistants") or [])})
        self.kills.sort(key=lambda k: (k["round"], k["time"] or 0))

    @classmethod
    def load(cls, path, agents=None):
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f), agents)

    def score_after(self, n):
        """The score once round n is over (0: before the first)."""
        if n <= 0 or not self.rounds:
            return {t: 0 for t in TEAMS}
        return dict(self.rounds[min(n, len(self.rounds)) - 1]["score"])

    def kda_after(self, n):
        """Each player's [kills, deaths, assists] once round n is over."""
        out = {p: [0, 0, 0] for p in self.players}
        for k in self.kills:
            if k["round"] > n:
                break
            killer, victim = k["killer"], k["victim"]
            if victim in out:
                out[victim][1] += 1
            if killer in out and killer != victim and \
                    self.players.get(killer, {}).get("team") != self.players.get(victim, {}).get("team"):
                out[killer][0] += 1
            for a in k["assistants"]:
                if a in out:
                    out[a][2] += 1
        return out

    def team_agents(self, team):
        return sorted(p["agent"] for p in self.players.values() if p["team"] == team)
