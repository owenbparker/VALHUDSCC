"""Match recorder, answer key and replay report."""

import json
import os
import tempfile
import time
import unittest

from PIL import Image

from valhud.answerkey import AnswerKey
from valhud.recorder import MatchRecorder
from valhud import replay

AGENTS = {"jett": "Jett", "omen": "Omen", "sova": "Sova", "sage": "Sage"}


def details():
    """A 2v2, three rounds: Red 2 - Blue 1."""
    players = [{"subject": "r1", "gameName": "TenZ", "tagLine": "NA1", "teamId": "Red", "characterId": "JETT"},
               {"subject": "r2", "gameName": "Zekken", "tagLine": "1", "teamId": "Red", "characterId": "omen"},
               {"subject": "b1", "gameName": "Derke", "tagLine": "FNC", "teamId": "Blue", "characterId": "sova"},
               {"subject": "b2", "gameName": "Boaster", "tagLine": "FNC", "teamId": "Blue", "characterId": "sage"},
               {"subject": "obs", "gameName": "Observer", "teamId": "Neutral", "characterId": ""}]
    rounds = [{"roundNum": 0, "winningTeam": "Red", "roundResult": "Eliminated"},
              {"roundNum": 1, "winningTeam": "Blue", "roundResult": "Bomb detonated"},
              {"roundNum": 2, "winningTeam": "Red", "roundResult": "Eliminated"}]
    kills = [{"round": 0, "roundTime": 20000, "killer": "r1", "victim": "b1", "assistants": ["r2"]},
             {"round": 0, "roundTime": 25000, "killer": "r1", "victim": "b2", "assistants": []},
             {"round": 1, "roundTime": 30000, "killer": "b1", "victim": "r2", "assistants": []},
             {"round": 2, "roundTime": 15000, "killer": "r2", "victim": "b2", "assistants": ["r1"]},
             {"round": 2, "roundTime": 18000, "killer": "r2", "victim": "b1", "assistants": []}]
    return {"matchInfo": {"matchId": "m1", "mapId": "/Game/Maps/Jam/Jam"}, "players": players,
            "roundResults": rounds, "kills": kills}


class AnswerKeyTests(unittest.TestCase):
    def test_scores_and_kda(self):
        key = AnswerKey(details(), AGENTS)
        self.assertEqual(set(key.players), {"r1", "r2", "b1", "b2"})      # (no observer)
        self.assertEqual(key.players["r1"]["agent"], "Jett")
        self.assertEqual(key.score_after(0), {"Red": 0, "Blue": 0})
        self.assertEqual(key.score_after(2), {"Red": 1, "Blue": 1})
        self.assertEqual(key.score_after(3), {"Red": 2, "Blue": 1})
        self.assertEqual(key.kda_after(1)["r1"], [2, 0, 0])
        self.assertEqual(key.kda_after(1)["r2"], [0, 0, 1])
        self.assertEqual(key.kda_after(3)["b1"], [1, 2, 0])
        self.assertEqual(key.team_agents("Blue"), ["Sage", "Sova"])


def reading(t, score=None, players=()):
    u = {"source": "screen", "match": {}, "players": list(players)}
    if score:
        u["match"]["score"] = {"left": score[0], "right": score[1]}
    return (t, u)


def p(team, slot, agent=None, kda=None, name=None):
    d = {"team": team, "slot": slot}
    if agent:
        d["agent"] = agent
    if kda:
        d["kills"], d["deaths"], d["assists"] = kda
    if name:
        d["name"] = name
    return d


class ReplayTests(unittest.TestCase):
    def test_perfect_and_misread(self):
        key = AnswerKey(details(), AGENTS)
        seats = [p("left", 1, "Sova", name="Derke"), p("left", 2, "Sage", name="Boaster"),
                 p("right", 1, "Jett", name="TenZ"), p("right", 2, "Omen", name="Zekk")]
        r = [reading(0, (0, 0), seats),
             reading(30, (0, 1), [p("right", 1, kda=(2, 0, 0)), p("right", 2, kda=(0, 0, 1)),
                                  p("left", 1, kda=(0, 1, 0)), p("left", 2, kda=(0, 1, 0))]),
             reading(60, (0, 11)),          # a misread that got through
             reading(61, (1, 1), [p("right", 2, kda=(0, 1, 1)), p("left", 1, kda=(1, 1, 0))]),
             reading(90, (1, 2), [p("right", 2, kda=(3, 1, 1))])]   # (double counted: should be 2)
        out = replay.score_readings(r, key)
        self.assertEqual(out["sides"], {"left": "Blue", "right": "Red"})
        self.assertEqual(out["players_matched"], 4)
        self.assertEqual(out["score"]["rounds_shown"], 3)
        self.assertEqual(out["score"]["wrong_scores_shown"], 1)
        self.assertEqual(out["kda"]["per_round"][0]["players_right"], 4)
        self.assertEqual(out["kda"]["kill_error"], 1)
        self.assertEqual(out["names"], {"right": 3, "of": 4})
        self.assertIn("3 of 3 rounds", replay.summary(dict(out, recording="x")))


class RerunTests(unittest.TestCase):
    def test_new_reader_rerun_over_a_recording(self):
        """Today's reader let a misread score through; the new reader, run
        again over the same raw readings, doesn't."""
        roster = {"left": [{"name": "Derke", "agent": "Sova", "puuid": "b1", "team_id": "Blue"},
                           {"name": "Boaster", "agent": "Sage", "puuid": "b2", "team_id": "Blue"}],
                  "right": [{"name": "TenZ", "agent": "Jett", "puuid": "r1", "team_id": "Red"},
                            {"name": "Zekken", "agent": "Omen", "puuid": "r2", "team_id": "Red"}]}
        seen = [["left", 1, "Sova"], ["left", 2, "Sage"], ["right", 1, "Jett"], ["right", 2, "Omen"]]
        events, t = [(0, "reading", {"source": "riot", "riot_roster": roster})], 1.0
        for score in [(0, 0)] * 8 + [(0, 1)] * 3 + [(0, 11)] * 3 + [(0, 1)] * 2 + [(1, 1)] * 3 + [(1, 2)] * 3:
            obs = {"source": "screen", "match": {"score": {"left": score[0], "right": score[1]}},
                   "players": [{"team": a, "slot": b, "alive": True} for a, b, _ in seen], "seen_agents": seen}
            events.append((t, "obs", obs))
            events.append((t, "reading", {"source": "screen", "match": {"score": obs["match"]["score"]},
                                          "players": [{"team": a, "slot": b, "agent": c} for a, b, c in seen]}))
            t += 0.5
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "events.jsonl"), "w") as f:
                for t_, kind, data in events:
                    f.write(json.dumps({"t": t_, "kind": kind, "data": data}) + "\n")
            with open(os.path.join(tmp, "match-details.json"), "w") as f:
                json.dump(details(), f)
            live = replay.report(tmp, AGENTS, "reading")
            new = replay.report(tmp, AGENTS, "rerun")
        self.assertEqual(live["score"]["wrong_scores_shown"], 1)
        self.assertEqual(new["score"]["wrong_scores_shown"], 0)
        self.assertEqual(new["score"]["rounds_shown"], 3)
        self.assertEqual(new["names"], {"right": 4, "of": 4})


class RecorderTests(unittest.TestCase):
    def test_records_a_match_and_keeps_the_answer_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = MatchRecorder(os.path.join(tmp, "recordings"), version="v1")
            rec.FRAME_EVERY = 0
            rec.frame(Image.new("RGB", (64, 36)))          # nothing running: not kept
            rec.seen("select")
            folder = rec.current
            self.assertTrue(folder)
            rec.attach("riot-core-game.json", {"MatchID": "m1"})
            rec.seen("match", "Lotus")
            for _ in range(3):
                rec.frame(Image.new("RGB", (64, 36)))
            rec.event("reading", {"source": "screen", "match": {"score": {"left": 1, "right": 0}}})
            deadline = time.time() + 5
            while rec.frames < 3 and time.time() < deadline:
                time.sleep(0.05)
            self.assertEqual(rec.frames, 3)
            rec.stop("test")
            rec.attach("match-details.json", details(), match_id="m1")   # (arrives after the match)
            self.assertTrue(os.path.isfile(os.path.join(folder, "match-details.json")))
            self.assertEqual(len(os.listdir(os.path.join(folder, "frames"))), 3)
            info = json.load(open(os.path.join(folder, "info.json")))
            self.assertEqual((info["map"], info["match_id"]), ("Lotus", "m1"))
            self.assertEqual(len(replay.load_readings(folder)), 1)
            self.assertIn("rounds", replay.report(folder, AGENTS))

    def test_off_records_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = MatchRecorder(os.path.join(tmp, "r"), enabled=lambda: False)
            rec.seen("select")
            self.assertIsNone(rec.current)

    def test_old_recordings_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = MatchRecorder(tmp)
            old = os.path.join(tmp, "20200101-000000")
            os.makedirs(old)
            os.utime(old, (0, 0))
            os.makedirs(os.path.join(tmp, "29990101-000000"))
            rec.prune()
            self.assertEqual(os.listdir(tmp), ["29990101-000000"])


if __name__ == "__main__":
    unittest.main()
