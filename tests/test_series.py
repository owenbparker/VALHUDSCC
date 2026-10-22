"""The series moving on by itself: maps from Map Bans, won maps, clearing."""

import os
import tempfile
import unittest

from valhud import game, series
from valhud.config import Config


def state(left, right):
    s = game.empty_state()
    s["connected"] = True
    s["match"]["score"] = {"left": left, "right": right}
    s["players"][0]["name"] = "Bolt"
    return s


class SeriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config(os.path.join(self.tmp.name, "config.json"))
        self.series = series.Series(self.cfg, lambda *a: None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_map_winner(self):
        self.assertIsNone(series.map_winner({"left": 12, "right": 12}))
        self.assertIsNone(series.map_winner({"left": 13, "right": 12}))
        self.assertEqual(series.map_winner({"left": 13, "right": 11}), "left")
        self.assertEqual(series.map_winner({"left": 5, "right": 13}), "right")
        self.assertEqual(series.map_winner({"left": 15, "right": 13}), "left")
        self.assertIsNone(series.map_winner({"left": 14, "right": 13}))

    def test_maps_from_bans(self):
        steps = [{"map": m} for m in ("Abyss", "Bind", "Haven", "Lotus", "Corrode", "Summit", "")]
        self.cfg.update({"best_of": 3, "map_bans": {"team_a": "left", "bo3": {"steps": steps}}})
        self.series.sync_maps()
        maps = self.cfg.get()["maps"]
        self.assertEqual([m["name"] for m in maps], ["Haven", "Lotus", "Sunset"])   # Sunset: the one left
        self.assertEqual([m["picked_by"] for m in maps], ["left", "right", ""])

    def test_a_won_map_and_the_next_agent_select(self):
        self.cfg.update({"best_of": 3, "current_map": 0})
        fields = {"LEFT P1 K": 20}
        for score in ((10, 11), (11, 11), (12, 11)):
            self.series.watch(state(*score), fields)
        self.assertEqual(self.cfg.get()["left"]["wins"], 0)
        shown = self.series.watch(state(13, 11), fields)
        cfg = self.cfg.get()
        self.assertEqual(cfg["left"]["wins"], 1)
        self.assertEqual(cfg["maps"][0]["winner"], "left")
        self.assertEqual(cfg["maps"][0]["score"], {"left": 13, "right": 11})
        self.assertEqual(shown["players"][0]["name"], "Bolt")      # not cleared yet
        self.series.watch(state(13, 11), fields)
        self.assertEqual(self.cfg.get()["left"]["wins"], 1)          # counted once
        # A minute later the HUD clears; the stats stay.
        self.series.won_at -= series.CLEAR_AFTER
        shown = self.series.watch(state(13, 11), {"LEFT P1 K": 0})
        self.assertEqual(shown["players"][0]["name"], "")
        self.assertEqual(self.series.stats, fields)
        # The next map's agent select.
        self.assertTrue(self.series.agent_select_started())
        self.assertEqual(self.cfg.get()["current_map"], 1)
        self.assertIsNone(self.series.stats)
        self.assertEqual(self.series.watch(state(0, 0), fields)["players"][0]["name"], "Bolt")

    def test_a_misread_score_wins_nothing(self):
        self.series.watch(state(3, 2), {})
        self.series.watch(state(13, 2), {})
        self.assertEqual(self.cfg.get()["left"]["wins"], 0)

    def test_round_kills(self):
        s = state(0, 0)
        s["match"]["phase"] = "combat"
        s["players"][0]["kills"] = 4
        self.series.round_kills(s)
        self.assertEqual(s["players"][0]["round_kills"], 0)
        s["players"][0]["kills"] = 6
        self.series.round_kills(s)
        self.assertEqual(s["players"][0]["round_kills"], 2)
        s["match"]["score"] = {"left": 1, "right": 0}
        s["match"]["round"] = 2
        s["match"]["phase"] = "buy"
        self.series.round_kills(s)
        self.assertEqual(s["players"][0]["round_kills"], 0)


if __name__ == "__main__":
    unittest.main()
