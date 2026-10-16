import json
import os
import tempfile
import time
import unittest
import urllib.request

from valhud import agentselect
from valhud.agentselect import AgentSelect, AgentSelectDemo, map_name
from valhud.config import Config


class AgentSelectTests(unittest.TestCase):
    def test_map_names(self):
        self.assertEqual(map_name("ASCENT"), "Ascent")
        self.assertEqual(map_name("Map - Icebox"), "Icebox")
        self.assertEqual(map_name("nothing"), "")

    def test_hover_then_lock(self):
        sel = AgentSelect()
        self.assertEqual(sel.apply({"active": True, "map": "LOTUS", "timer": 80}, "screen"), "Lotus")
        sel.apply({"players": [{"team": "left", "slot": 2, "agent": "jett", "locked": False},
                               {"team": "right", "slot": 5, "agent": "KAY/O", "locked": True},
                               {"team": "right", "slot": 1, "agent": "Nobody"}]})
        v = sel.view([{"team": "left", "slot": 2, "name": "Bolt"}])
        self.assertTrue(v["active"])
        self.assertEqual(v["map"], "Lotus")
        self.assertEqual(v["players"]["left"][1], {"agent": "Jett", "locked": False, "name": "Bolt"})
        self.assertEqual(v["players"]["right"][4]["agent"], "Kayo")
        self.assertTrue(v["players"]["right"][4]["locked"])
        self.assertEqual(v["players"]["right"][0]["agent"], "")      # not an agent
        self.assertIn(v["timer"], (79, 80))
        # A new agent select starts from empty slots.
        sel.apply({"active": False})
        sel.apply({"active": True})
        self.assertEqual(sel.view([])["players"]["left"][1]["agent"], "")

    def test_screen_reading_goes_stale(self):
        sel = AgentSelect()
        sel.apply({"active": True}, "screen")
        sel.updated_at -= agentselect.STALE_AFTER + 1
        self.assertFalse(sel.view([])["active"])

    def test_demo_runs(self):
        sel = AgentSelect()
        demo = AgentSelectDemo(sel, "Bind", speed=40, seed=1).start()
        deadline = time.time() + 10
        while demo.running() and time.time() < deadline:
            time.sleep(0.1)
        demo.stop()
        v = sel.view([])
        self.assertFalse(v["active"])
        self.assertEqual(v["map"], "Bind")
        for side in ("left", "right"):
            agents = [p["agent"] for p in v["players"][side]]
            self.assertTrue(all(p["locked"] for p in v["players"][side]))
            self.assertEqual(len(set(agents)), 5)                 # no agent twice on a team


class ServerTests(unittest.TestCase):
    def test_agent_select_endpoints(self):
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"http_port": 8797, "output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            app.updater.check_in_background = lambda: None
            start(app)
            try:
                def post(path, body):
                    req = urllib.request.Request(f"http://127.0.0.1:8797{path}", json.dumps(body).encode(),
                                                 {"Content-Type": "application/json"})
                    return json.loads(urllib.request.urlopen(req, timeout=5).read())

                post("/api/ingest", {"source": "observer", "agent_select": {
                    "active": True, "map": "SPLIT", "players": [{"team": "left", "slot": 1, "agent": "Omen"}]}})
                s = json.loads(urllib.request.urlopen("http://127.0.0.1:8797/api/state", timeout=5).read())
                self.assertTrue(s["agent_select"]["active"])
                self.assertEqual(s["agent_select"]["players"]["left"][0]["agent"], "Omen")
                # The map read off the screen is the map being played.
                self.assertEqual(s["config"]["maps"][0]["name"], "Split")
                self.assertEqual(s["game"]["match"]["map"], "Split")
                self.assertIn("Veto", s["agent_select"]["agents"])
                for look, page in (("pro", b"select.js"), ("champions", b"Agent select (Champions)")):
                    post("/api/config", {"agent_select": {"look": look}})
                    with urllib.request.urlopen("http://127.0.0.1:8797/agent-select", timeout=5) as r:
                        self.assertIn(page, r.read())
                # The template's art: its own agents, and the HUD's maps.
                for path in ("/select/Resources/Agentes/Veto/Veto.png", "/select/resources/Maps/Corrode.png",
                             "/select/Resources/HUD-ATK.png", "/hud/Resources/Agentes/Veto/X.png"):
                    with urllib.request.urlopen(f"http://127.0.0.1:8797{path}", timeout=5) as r:
                        self.assertTrue(r.read())
            finally:
                app.stop()


if __name__ == "__main__":
    unittest.main()


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "agent_select")


class ScreenTests(unittest.TestCase):
    """Real frames of the observer's agent select screen."""

    def read(self, name):
        from PIL import Image
        from valhud import selectreader
        return selectreader.read(Image.open(os.path.join(FIXTURES, name + ".webp")))

    def cards(self, reading):
        return {(p["team"], p["slot"]): (p["agent"], p["locked"]) for p in reading["players"]}

    def test_everyone_locked(self):
        r = self.read("locked_00")
        self.assertTrue(r["active"])
        self.assertEqual(r["map"], "Ascent")
        cards = self.cards(r)
        self.assertEqual([cards[("defenders", i)][0] for i in range(1, 6)], ["Brimstone", "Omen", "Sage", "Chamber", "Deadlock"])
        self.assertEqual([cards[("attackers", i)][0] for i in range(1, 6)], ["Neon", "Omen", "Gekko", "Raze", "Yoru"])
        self.assertTrue(all(locked for _, locked in cards.values()))

    def test_hovering_locked_and_empty(self):
        cards = self.cards(self.read("mixed_38"))
        self.assertEqual(cards[("defenders", 1)], ("Brimstone", True))
        self.assertEqual(cards[("defenders", 2)], ("", False))           # nothing picked yet
        self.assertEqual(cards[("defenders", 5)], ("Deadlock", False))   # hovering
        self.assertEqual(cards[("attackers", 4)], ("Raze", False))
        self.assertEqual(cards[("attackers", 5)], ("Yoru", True))
        # A portrait still fading in while hovering.
        cards = self.cards(self.read("hover_62"))
        self.assertEqual(cards[("attackers", 5)], ("Yoru", False))
        self.assertFalse(any(locked for _, locked in cards.values()))
        cards = self.cards(self.read("empty_70_taskbar"))
        self.assertTrue(all(agent == "" for agent, _ in cards.values()))

    def test_not_agent_select(self):
        from PIL import Image
        from valhud import selectreader
        for name in ("tab_scoreboard.png", "round_history.png"):
            path = os.path.join(os.path.dirname(__file__), "fixtures", name)
            self.assertIsNone(selectreader.read(Image.open(path)))

    def test_screen_sides_to_teams(self):
        from valhud.app import HudApp
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"attack_first": "left", "output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            reading = self.read("mixed_38")
            reading["players"][0]["name"] = "mimiQ"
            app.ingest({"source": "observer", "agent_select": reading})
            v = app.agent_select.view([])
            # Defenders are the team not attacking first (right, here).
            self.assertEqual(v["players"]["right"][0], {"agent": "Brimstone", "locked": True, "name": "mimiQ"})
            self.assertEqual(v["players"]["left"][4]["agent"], "Yoru")
            self.assertEqual(v["map"], "Ascent")

    def test_tracker_needs_two_reads_to_change(self):
        from PIL import Image
        from valhud.reader import SelectTracker
        sent = []
        t = SelectTracker(sent.append)
        frame = lambda n: Image.open(os.path.join(FIXTURES, n + ".webp"))
        t.check(frame("hover_62"), None)
        t.check(frame("locked_00"), None)      # one read of the locks: not yet
        last = {(p["team"], p["slot"]): p for p in sent[-1]["agent_select"]["players"]}
        self.assertFalse(last[("attackers", 5)]["locked"])
        t.check(frame("locked_00"), None)      # seen again: now it counts
        last = {(p["team"], p["slot"]): p for p in sent[-1]["agent_select"]["players"]}
        self.assertTrue(last[("attackers", 5)]["locked"])
        from valhud.reader import Frame
        self.assertFalse(t.check(Image.open(os.path.join(os.path.dirname(__file__), "fixtures", "tab_scoreboard.png")), None))
        self.assertEqual(sent[-1]["agent_select"], {"active": False})
