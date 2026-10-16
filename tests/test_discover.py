import os
import tempfile
import unittest

from valhud.config import Config
from valhud.discover import find_huds


class DiscoverTests(unittest.TestCase):
    def test_finds_the_gfx_hud_not_observers(self):
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"http_port": 8793, "output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            app.updater.check_in_background = lambda: None
            start(app)
            try:
                def is_gfx(state):
                    return "game" in state and (state.get("app") or {}).get("role") != "observer"
                # "This PC" is 127.0.0.2: the HUD on 127.0.0.1 is on its network.
                hits = find_huds(8793, is_gfx, addresses=["127.0.0.2"])
                self.assertEqual([h["ip"] for h in hits], ["127.0.0.1"])
                self.assertEqual(hits[0]["url"], "http://127.0.0.1:8793")
                app.role = "observer"
                self.assertEqual(find_huds(8793, is_gfx, addresses=["127.0.0.2"]), [])
            finally:
                app.stop()


if __name__ == "__main__":
    unittest.main()
