import json
import os
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request

from valhud.cams import CamHub, cam_links, clean_link, clean_riot_id, match_players, name_matches
from valhud.config import Config


class RiotIdTests(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(clean_riot_id("  leaf #NA1 "), "leaf#NA1")
        for bad in ("leaf", "#NA1", "leaf#", "averyveryverylongname#NA1"):
            with self.assertRaises(ValueError):
                clean_riot_id(bad)

    def test_names(self):
        self.assertTrue(name_matches("valyn", "valyn"))
        self.assertTrue(name_matches("valyn", "G2 valyn"))          # team tag in front
        self.assertTrue(name_matches("BABYBAY", "babybay"))
        self.assertTrue(name_matches("Timotino", "Timotin0"))       # misread letter
        self.assertFalse(name_matches("leaf", "bang"))
        self.assertFalse(name_matches("ab", "cab"))

    def test_match_players(self):
        players = [{"team": "left", "slot": 2, "name": "leaf"}, {"team": "right", "slot": 5, "name": "Timotino"}]
        got = match_players(["Timotino#100T", "leaf#NA1", "nobody#X"], players)
        self.assertEqual(got["leaf#NA1"], {"team": "left", "slot": 2, "name": "leaf"})
        self.assertEqual(got["Timotino#100T"]["slot"], 5)
        self.assertNotIn("nobody#X", got)


class CamLinkTests(unittest.TestCase):
    def test_clean_link(self):
        self.assertEqual(clean_link(" vdo.ninja/?view=abc "), "https://vdo.ninja/?view=abc")
        self.assertEqual(clean_link("https://vdo.ninja/?view=abc"), "https://vdo.ninja/?view=abc")
        for bad in ("", "not a link", "javascript:alert(1)", "ftp://x.com/a"):
            self.assertEqual(clean_link(bad), "")

    def test_links_found_by_riot_id(self):
        players = [{"team": "left", "slot": 2, "name": "leaf"}, {"team": "right", "slot": 5, "name": "Timotino"}]
        rows = cam_links([{"riot_id": "LEAF #na1", "link": "vdo.ninja/?view=leaf"},
                          {"riot_id": "Timotino#100T", "link": "nope"},
                          {"riot_id": "nobody#X", "link": "https://vdo.ninja/?view=x"},
                          {"riot_id": "no tag", "link": "https://vdo.ninja/?view=y"}, "junk"], players)
        self.assertEqual(rows[0], {"riot_id": "LEAF#na1", "link": "https://vdo.ninja/?view=leaf",
                                   "player": {"team": "left", "slot": 2, "name": "leaf"}})
        self.assertEqual((rows[1]["link"], rows[1]["player"]["slot"]), ("", 5))
        self.assertIsNone(rows[2]["player"])
        self.assertEqual(len(rows), 3)


class HubTests(unittest.TestCase):
    def test_messages_and_one_cam_per_player(self):
        hub = CamHub()
        self.assertEqual(hub.poll("cam1", "leaf#NA1", "Logitech", wait=0)["riot_id"], "leaf#NA1")
        hub.poll("overlay", wait=0)
        got = []
        t = threading.Thread(target=lambda: got.append(hub.poll("cam1", wait=5)))
        t.start()
        hub.send("cam1", "overlay", {"type": "offer", "sdp": "x"})
        t.join(5)
        self.assertEqual(got[0]["messages"][0]["type"], "offer")
        # The same player on another PC takes over.
        hub.poll("cam2", "LEAF#na1", wait=0)
        self.assertEqual(hub.poll("cam1", wait=0)["messages"][0]["type"], "replaced")
        pubs = hub.publishers([{"team": "left", "slot": 1, "name": "leaf"}])
        self.assertEqual([p["id"] for p in pubs], ["cam2"])
        self.assertEqual(pubs[0]["player"]["slot"], 1)
        hub.poll("cam2", "", wait=0)          # left
        self.assertEqual(hub.publishers(), [])


class ServerTests(unittest.TestCase):
    def test_cam_endpoints(self):
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"http_port": 8796, "output_dir": os.path.join(tmp, "out"),
                        "player_names": {"left": ["Ace", "Bolt", "", "", ""], "right": ["", "Grit", "", "", ""]}})
            app = HudApp(cfg)
            app.updater.check_in_background = lambda: None
            start(app)
            try:
                def post(path, body):
                    req = urllib.request.Request(f"http://127.0.0.1:8796{path}", json.dumps(body).encode(),
                                                 {"Content-Type": "application/json"})
                    return json.loads(urllib.request.urlopen(req, timeout=5).read())

                post("/api/ingest", {"source": "test", "players": [{"team": "right", "slot": 2, "agent": "Jett"}]})
                reply = post("/api/cam/poll", {"id": "cam1", "riot_id": "Grit#EUW", "label": "Cam", "wait": 0})
                self.assertEqual(reply["riot_id"], "Grit#EUW")
                self.assertEqual(reply["player"]["team"], "right")
                state = json.loads(urllib.request.urlopen("http://127.0.0.1:8796/api/state", timeout=5).read())
                self.assertEqual(state["cams"]["publishers"][0]["player"]["slot"], 2)
                # A cam link typed beside a Riot ID in the control panel.
                post("/api/config", {"cams": {"links": [{"riot_id": "grit#euw", "link": "vdo.ninja/?view=grit"}]}})
                state = json.loads(urllib.request.urlopen("http://127.0.0.1:8796/api/state", timeout=5).read())
                self.assertEqual(state["cams"]["links"][0]["link"], "https://vdo.ninja/?view=grit")
                self.assertEqual(state["cams"]["links"][0]["player"]["team"], "right")
                self.assertFalse(state["cams"]["links"][0]["hidden"])
                # Hidden (not working): both the link and the Player Cam.
                post("/api/config", {"cams": {"hidden": ["grit#euw"]}})
                state = json.loads(urllib.request.urlopen("http://127.0.0.1:8796/api/state", timeout=5).read())
                self.assertTrue(state["cams"]["links"][0]["hidden"])
                self.assertTrue(state["cams"]["publishers"][0]["hidden"])
                # The Player Cam app's page posts from another origin: preflight.
                req = urllib.request.Request("http://127.0.0.1:8796/api/cam/poll", method="OPTIONS")
                with urllib.request.urlopen(req, timeout=5) as r:
                    self.assertEqual(r.headers["Access-Control-Allow-Origin"], "*")
                with self.assertRaises(urllib.error.HTTPError):
                    post("/api/cam/poll", {"id": "cam2", "riot_id": "no tag", "wait": 0})
                page = urllib.request.urlopen("http://127.0.0.1:8796/overlay", timeout=5).read()
                self.assertIn(b"/cams.js", page)
            finally:
                app.stop()


if __name__ == "__main__":
    unittest.main()


class FontTests(unittest.TestCase):
    def test_installed_fonts_listed_and_served(self):
        from valhud import fonts
        found = fonts.installed()
        if not found:
            self.skipTest("no fonts installed here")
        family = sorted(found)[0]
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"http_port": 8798, "output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            app.updater.check_in_background = lambda: None
            start(app)
            try:
                listed = json.loads(urllib.request.urlopen("http://127.0.0.1:8798/api/fonts", timeout=20).read())["fonts"]
                self.assertIn(family, listed)
                url = "http://127.0.0.1:8798/fonts/local/" + urllib.parse.quote(family)
                with urllib.request.urlopen(url, timeout=5) as r:
                    self.assertGreater(len(r.read()), 1000)
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen("http://127.0.0.1:8798/fonts/local/..%2F..%2Fetc%2Fpasswd", timeout=5)
                self.assertEqual(cfg.get()["cams"]["name_size"], 18)
            finally:
                app.stop()
