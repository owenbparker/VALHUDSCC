"""The new reader's rules (tracker.py): score, sides, players."""

import unittest

from valhud.tracker import ScoreKeeper, SideKeeper, Tracker

ROSTER = [{"puuid": "r1", "name": "TenZ", "team": "Red", "agent": "Jett"},
          {"puuid": "r2", "name": "Zekken", "team": "Red", "agent": "Omen"},
          {"puuid": "b1", "name": "Derke", "team": "Blue", "agent": "Sova"},
          {"puuid": "b2", "name": "Boaster", "team": "Blue", "agent": "Omen"}]   # (Omen on both: fine)


def frame(score=None, left=("Sova", "Omen"), right=("Jett", "Omen"), alive=None, names=None, rounds=None):
    players, seen = [], []
    for side, agents in (("left", left), ("right", right)):
        for i, a in enumerate(agents, 1):
            p = {"team": side, "slot": i, "alive": True if alive is None else alive.get((side, i), True)}
            if (names or {}).get((side, i)):
                p["name"] = names[(side, i)]
            players.append(p)
            seen.append((side, i, a))
    m = {}
    if score:
        m["score"] = {"left": score[0], "right": score[1]}
    if rounds:
        m["rounds"] = rounds
    return {"source": "screen", "match": m, "players": players, "seen_agents": seen}


class ScoreTests(unittest.TestCase):
    def feed(self, k, reads, t0=0.0):
        out = None
        for i, s in enumerate(reads):
            out = k.offer(*s, now=t0 + i * 0.5)
        return out

    def test_round_won_counts_at_the_second_read(self):
        k = ScoreKeeper()
        self.assertEqual(self.feed(k, [(5, 4), (5, 4)]), (5, 4))
        self.assertEqual(k.offer(6, 4, now=2), (5, 4))
        self.assertEqual(k.offer(6, 4, now=2.5), (6, 4))

    def test_misread_doesnt_get_through(self):
        k = ScoreKeeper()
        self.feed(k, [(12, 11), (12, 11)])
        # "12-11" read as "1-1" a few times, then right again
        self.assertEqual(self.feed(k, [(1, 1)] * 5 + [(12, 11)], t0=5), (12, 11))
        self.assertEqual(self.feed(k, [(1, 0), (10, 11), (12, 1)], t0=10), (12, 11))
        self.assertGreaterEqual(k.rejected, 3)

    def test_new_map_after_agent_select(self):
        k = ScoreKeeper()
        self.feed(k, [(13, 9), (13, 9)])
        self.assertEqual(self.feed(k, [(0, 0), (0, 0)], t0=5), (13, 9))   # (no agent select seen)
        k.agent_select()
        self.assertEqual(self.feed(k, [(0, 0), (0, 0)], t0=10), (0, 0))

    def test_a_real_jump_still_gets_through_slowly(self):
        k = ScoreKeeper()
        self.feed(k, [(3, 3), (3, 3)])
        self.assertEqual(self.feed(k, [(5, 3)] * 11, t0=2), (3, 3))
        self.assertEqual(k.offer(5, 3, now=8), (5, 3))

    def test_elimination_and_round_history(self):
        k = ScoreKeeper()
        self.feed(k, [(2, 2), (2, 2)])
        self.assertEqual(k.offer(3, 2, now=2, eliminated="right"), (3, 2))   # (right all dead: left won)
        self.assertEqual(k.offer(3, 4, now=3, history=(3, 4)), (3, 4))       # (odd, but the history agrees)

    def test_gap_starts_afresh(self):
        k = ScoreKeeper()
        self.feed(k, [(2, 2), (2, 2)])
        self.assertEqual(self.feed(k, [(7, 5), (7, 5)], t0=500), (7, 5))


class SideTests(unittest.TestCase):
    def test_sides_from_agents(self):
        s = SideKeeper()
        for _ in range(3):
            s.observe({("left", 1): "Sova", ("left", 2): "Omen", ("right", 1): "Jett"}, ROSTER)
        self.assertEqual((s.team_of("left"), s.team_of("right")), ("Blue", "Red"))

    def test_mirror_comp_stays_unknown(self):
        s = SideKeeper()
        roster = [{"team": "Red", "agent": "Jett"}, {"team": "Blue", "agent": "Jett"}]
        for _ in range(5):
            s.observe({("left", 1): "Jett"}, roster)
        self.assertIsNone(s.left)


class TrackerTests(unittest.TestCase):
    def test_names_come_from_the_roster_by_agent(self):
        t = Tracker()
        t.riot_roster(ROSTER)
        for i in range(6):   # (agents steady after 3 reads, then sides after 3 more)
            t.observe(frame((0, 0), names={("left", 1): "Derk", ("right", 2): "Zek"}), now=i)
        v = t.view()
        by = {(p["team"], p["slot"]): p for p in v["players"]}
        self.assertEqual(by[("left", 1)]["name"], "Derke")     # (Riot ID beats the cut-off OCR name)
        self.assertEqual(by[("left", 2)]["name"], "Boaster")   # (Omen on the left = Blue's Omen)
        self.assertEqual(by[("right", 2)]["name"], "Zekken")
        self.assertEqual(v["match"]["score"], {"left": 0, "right": 0})
        self.assertEqual(v["match"]["left_team"], "Blue")

    def test_without_the_roster_names_need_two_reads(self):
        t = Tracker()
        t.observe(frame((0, 0), names={("left", 1): "chr"}), now=0)
        t.observe(frame((0, 0), names={("left", 1): "chronicle"}), now=1)
        self.assertNotIn("name", t.view()["players"][0])
        t.observe(frame((0, 0), names={("left", 1): "chronicle"}), now=2)
        self.assertEqual(t.view()["players"][0]["name"], "chronicle")

    def test_agent_select_starts_a_new_map(self):
        t = Tracker()
        t.riot_roster(ROSTER)
        for i in range(3):
            t.observe(frame((13, 7)), now=i)
        t.agent_select()
        self.assertEqual(t.agents, {})
        for i in range(3):
            t.observe(frame((0, 0)), now=10 + i)
        self.assertEqual(t.view()["match"]["score"], {"left": 0, "right": 0})

    def test_round_history_settles_the_score(self):
        t = Tracker()
        t.observe(frame((1, 1)), now=0)
        t.observe(frame((1, 1)), now=1)
        rounds = [{"winner": "left"}, {"winner": "right"}, {"winner": "right"}]
        t.observe(frame((1, 2), rounds=rounds), now=2)
        self.assertEqual(t.view()["match"]["score"], {"left": 1, "right": 2})


if __name__ == "__main__":
    unittest.main()
