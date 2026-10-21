import json
import os
import tempfile
import unittest
import urllib.request

from valhud import mapbans
from valhud.config import DEFAULTS, Config, _merge


def cfg(**map_bans):
    return _merge(DEFAULTS, {"map_bans": map_bans})


class VetoTests(unittest.TestCase):
    def test_default_pool_is_the_vct_pool(self):
        pool, team_a = mapbans.settings(cfg())
        self.assertEqual(pool, mapbans.VCT_POOL)
        self.assertEqual(team_a, "left")
        self.assertEqual(len(mapbans.VCT_POOL), 7)

    def test_bo3_order(self):
        steps = mapbans.steps(cfg(team_a="right"), 3)
        self.assertEqual([(s["action"], s["team"]) for s in steps],
                         [("ban", "right"), ("ban", "left"), ("pick", "right"), ("pick", "left"),
                          ("ban", "right"), ("ban", "left"), ("decider", None)])
        # The other team picks the side of a picked map; Team A the decider's.
        self.assertEqual([s["side_team"] for s in steps], [None, None, "left", "right", None, None, "right"])

    def test_bo1_order(self):
        steps = mapbans.steps(cfg(), 1)
        self.assertEqual([(s["action"], s["team"]) for s in steps[:6]], [("ban", "left"), ("ban", "right")] * 3)
        self.assertEqual((steps[6]["action"], steps[6]["side_team"]), ("decider", "left"))

    def test_decider_is_the_last_map_left(self):
        chosen = ["Abyss", "Bind", "Corrode", "Haven", "Lotus", "Summit"]
        steps = mapbans.steps(cfg(bo1={"steps": [{"map": m} for m in chosen] + [{"side": "attack"}]}), "bo1")
        self.assertEqual(steps[6]["map"], "Sunset")
        self.assertTrue(steps[6]["auto"])
        self.assertEqual(steps[6]["side"], "attack")
        # Not before.
        steps = mapbans.steps(cfg(bo1={"steps": [{"map": m} for m in chosen[:5]]}), "bo1")
        self.assertEqual(steps[6]["map"], "")

    def test_any_map_can_be_in_the_pool(self):
        pool, _ = mapbans.settings(cfg(pool=["Split", "Ascent", "Nowhere"]))
        self.assertEqual(pool, ["Ascent", "Split"])


class ServerTests(unittest.TestCase):
    def test_map_bans_endpoints(self):
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            c = Config(os.path.join(tmp, "config.json"))
            c.update({"http_port": 8798, "output_dir": os.path.join(tmp, "out")})
            app = HudApp(c)
            app.updater.check_in_background = lambda: None
            app.map_art.fetch_missing = lambda: None   # (no downloads in tests)
            start(app)
            base = "http://127.0.0.1:8798"
            try:
                req = urllib.request.Request(base + "/api/config", json.dumps({"map_bans": {"team_a": "right", "bo3": {
                    "steps": [{"map": "Abyss"}, {"map": "Bind"}, {"map": "Haven", "side": "defence"}]}}}).encode(),
                    {"Content-Type": "application/json"})
                s = json.loads(urllib.request.urlopen(req, timeout=5).read())
                self.assertEqual(s["map_bans"]["bo3"][2]["map"], "Haven")
                v = json.loads(urllib.request.urlopen(base + "/api/map-bans?bo=3", timeout=5).read())
                self.assertEqual(v["steps"][2]["team"], "right")
                self.assertEqual(v["steps"][0]["art"], "/map-art/Abyss")
                with urllib.request.urlopen(base + "/map-bans?bo=1", timeout=5) as r:
                    self.assertIn(b"MAP BANS", r.read())
                for m in ("Abyss", "Ascent", "Haven"):
                    with urllib.request.urlopen(base + "/map-art/" + m, timeout=5) as r:
                        self.assertTrue(r.read())
                ids = [g["id"] for g in app._engine_snapshot()["hud"]["graphics"]]
                self.assertIn("map-bans-bo1", ids)
                self.assertIn("map-bans-bo3", ids)
            finally:
                app.stop()


if __name__ == "__main__":
    unittest.main()
