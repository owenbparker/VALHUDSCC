import json
import os
import tempfile
import threading
import unittest
import urllib.request

from valhud import game
from valhud.config import DEFAULTS, Config, web_file
from valhud.demo import DemoGame


class GameTests(unittest.TestCase):
    def test_merge_partial_update(self):
        s = game.merge(game.empty_state(), {
            "match": {"round": 5, "phase": "combat", "score": {"left": 3}},
            "players": [{"team": "right", "slot": 2, "agent": "KAY/O", "health": 140, "weapon": "vandal",
                         "shield": 30, "abilities": {"Q": [1, 2]}}]})
        self.assertEqual(s["match"]["round"], 5)
        self.assertEqual(s["match"]["score"], {"left": 3, "right": 0})
        p = s["players"][6]
        self.assertEqual((p["team"], p["slot"]), ("right", 2))
        self.assertEqual(p["agent"], "Kayo")          # our folder name
        self.assertEqual(p["ult_max"], game.ULT_MAX["Kayo"])
        self.assertEqual(p["health"], 100)           # clamped
        self.assertEqual(p["weapon"], "Vandal")
        self.assertEqual(p["shield"], 25)            # only 0 / 25 / 50
        self.assertEqual(p["abilities"]["Q"], [1, 2])
        self.assertEqual(p["abilities"]["C"], [0, 1])  # untouched

    def test_health_zero_means_dead(self):
        s = game.merge(game.empty_state(), {"players": [{"team": "left", "slot": 1, "health": 0}]})
        self.assertFalse(s["players"][0]["alive"])

    def test_bad_players_ignored(self):
        s = game.merge(game.empty_state(), {"players": [{"team": "blue", "slot": 1, "health": 1},
                                                        {"team": "left", "slot": 9, "health": 1}]})
        self.assertTrue(all(p["health"] == 100 for p in s["players"]))

    def test_typed_names_win(self):
        cfg = json.loads(json.dumps(DEFAULTS))
        cfg["player_names"]["left"][0] = "TenZ"
        s = game.merge(game.empty_state(), {"players": [{"team": "left", "slot": 1, "name": "feedname"},
                                                        {"team": "left", "slot": 2, "name": "other"}]})
        s = game.with_overrides(s, cfg)
        self.assertEqual(s["players"][0]["name"], "TenZ")
        self.assertEqual(s["players"][1]["name"], "other")

    def test_fields(self):
        f = game.fields(game.empty_state(), DEFAULTS)
        for key in ("SCORE LEFT", "TEAM RIGHT", "LEFT P1 HP", "RIGHT P5 CREDITS", "ROUND", "SPIKE"):
            self.assertIn(key, f)


class DemoTests(unittest.TestCase):
    def test_plays_a_whole_match(self):
        d = DemoGame(seed=3)
        winners, seen_plant, sides = set(), False, set()
        for _ in range(20000):
            d.advance(1)
            m = d.state["match"]
            seen_plant |= m["spike"]["state"] == "planted"
            sides.add((m["round"] > 12, m["attackers"]))
            for p in d.state["players"]:
                self.assertTrue(0 <= p["health"] <= 100)
                self.assertTrue(0 <= p["credits"] <= 9000)
                self.assertLessEqual(p["ult_points"], p["ult_max"])
            if max(m["score"].values()) >= 13 and m["phase"] == "end":
                winners.add(max(m["score"], key=m["score"].get))
                break
        self.assertTrue(winners, "the demo match should finish")
        self.assertTrue(seen_plant)
        self.assertIn((False, "left"), sides)
        self.assertIn((True, "right"), sides)   # sides swap at half time
        self.assertEqual(len(m["rounds"]), m["score"]["left"] + m["score"]["right"])


class ServerTests(unittest.TestCase):
    def test_ingest_and_state(self):
        from valhud.app import HudApp, start
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"http_port": 8795, "output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            app.updater.check_in_background = lambda: None
            start(app)
            try:
                def post(path, body):
                    req = urllib.request.Request(f"http://127.0.0.1:8795{path}", json.dumps(body).encode(),
                                                 {"Content-Type": "application/json"})
                    return json.loads(urllib.request.urlopen(req, timeout=5).read())

                post("/api/ingest", {"source": "test", "match": {"map": "Bind", "round": 3},
                                     "players": [{"team": "left", "slot": 1, "agent": "Jett", "credits": 4200}]})
                state = json.loads(urllib.request.urlopen("http://127.0.0.1:8795/api/state", timeout=5).read())
                self.assertTrue(state["game"]["connected"])
                self.assertEqual(state["game"]["match"]["map"], "Bind")
                self.assertEqual(state["game"]["players"][0]["credits"], 4200)
                self.assertIn("test", state["app"]["feed"]["sources"])
                csv = urllib.request.urlopen("http://127.0.0.1:8795/hud.csv", timeout=5).read().decode()
                self.assertIn("LEFT P1 CREDITS", csv)
                for path in ("/overlay", "/scoreboard"):
                    page = urllib.request.urlopen(f"http://127.0.0.1:8795{path}", timeout=5)
                    self.assertIn("/Console.html", page.geturl())
                    self.assertIn(b"/driver.js", page.read())
            finally:
                app.stop()


class ReaderTests(unittest.TestCase):
    def test_reads_tab_scoreboard_screenshot(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        from PIL import Image
        from valhud.reader import TEXT_FIELDS, read_frame
        here = os.path.join(os.path.dirname(__file__), "fixtures")
        with open(os.path.join(here, "tab_scoreboard.json"), encoding="utf-8") as f:
            expected = json.load(f)
        update = read_frame(Image.open(os.path.join(here, "tab_scoreboard.png")))  # no text recognition here
        by_slot = {(p["team"], p["slot"]): p for p in update["players"]}
        for e in expected["players"]:
            p = by_slot[(e["team"], e["slot"])]
            for key, value in e.items():
                if key not in ("team", "slot") and key not in TEXT_FIELDS:
                    self.assertEqual(p.get(key), value, f"{e['team']} {e['slot']} {key}")
        self.assertEqual(update["match"]["spike"]["state"], "")
        self.assertTrue(update["match"]["scoreboard_open"])

    def test_reads_rifles_and_seats_rows_by_agent(self):
        # A real spectator frame (round 3, buy phase): rifles, SMGs and the
        # Bandit; scoreboard rows in score order, not top-bar order.
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        from PIL import Image
        from valhud.reader import read_frame
        frame = Image.open(os.path.join(os.path.dirname(__file__), "fixtures", "tab_scoreboard_rifles.png"))
        update = read_frame(frame)
        got = {(p["team"], p["slot"]): (p.get("agent"), p.get("weapon")) for p in update["players"]}
        self.assertEqual(got[("left", 1)], ("Phoenix", "Bulldog"))
        self.assertEqual(got[("left", 2)], ("Neon", "Bandit"))
        self.assertEqual(got[("left", 3)], ("Brimstone", "Ghost"))
        self.assertEqual(got[("left", 4)], ("Cypher", "Stinger"))
        self.assertEqual(got[("left", 5)], ("Fade", "Guardian"))
        self.assertEqual([got[("right", s)][1] for s in range(1, 6)], ["Phantom", "Vandal", "Vandal", "Phantom", "Vandal"])
        self.assertEqual(got[("right", 4)][0], "Chamber")   # from a real portrait (web/reader_refs)
        # The left team's half of the top bar is teal: they defend.
        self.assertEqual(update["match"]["attackers"], "right")
        self.assertEqual(update["match"]["phase"], "buy")   # the BUY PHASE banner is up
        # Wrong agents remembered for a seat are corrected from the top bar.
        update = read_frame(frame, known_agents={("left", 1): "Omen"})
        self.assertIn(("left", 1, "Phoenix"), update["seen_agents"])

    def test_round_history(self):
        # Part of a real Tab scoreboard after 11 rounds (DEF 7, ATK 4), placed
        # where it sits on a 1920x1080 screen.
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        from PIL import Image
        from valhud.reader import Frame, round_history
        frame = Image.new("RGB", (1920, 1080))
        frame.paste(Image.open(os.path.join(os.path.dirname(__file__), "fixtures", "round_history.png")).convert("RGB"),
                    (514, 442))
        rounds = round_history(Frame(frame))
        self.assertEqual("".join(r["winner"][0] for r in rounds), "rrlllllrlrl")
        self.assertEqual([r["win_type"] for r in rounds[:5]],
                         ["Elimination", "Elimination", "Deactivation", "Deactivation", "Elimination"])

    def test_buy_phase_follows_the_banner(self):
        from valhud.reader import BuyBanner
        b = BuyBanner()
        got = [b.seen(x) for x in (False, True, True, False, True, False, False, False)]
        # On at once; one missed read (a flicker) doesn't end it; two do.
        self.assertEqual(got, ["combat", "buy", "buy", "buy", "buy", "buy", "combat", "combat"])

    def test_history_never_longer_than_rounds_played(self):
        s = game.merge(game.empty_state(), {"match": {"score": {"left": 7, "right": 5},
                                                      "rounds": [{"winner": "left", "win_type": "Elimination"}] * 12}})
        self.assertEqual(len(s["match"]["rounds"]), 12)
        s = game.merge(s, {"match": {"score": {"left": 0, "right": 2}}})   # next game
        self.assertEqual(len(s["match"]["rounds"]), 2)

    def test_player_names_lose_team_tags(self):
        from valhud.reader import player_name
        self.assertEqual(player_name("FIT | Panda Nate"), "Panda Nate")
        self.assertEqual(player_name("HII I Panda Nate"), "Panda Nate")
        self.assertEqual(player_name("woddy"), "woddy")

    def test_feed_turns_into_state(self):
        s = game.merge(game.empty_state(), {"players": [{"team": "left", "slot": 3, "alive": False, "health": 0}]})
        self.assertFalse(s["players"][2]["alive"])


class FileTests(unittest.TestCase):
    def test_template_paths(self):
        # The templates use both "Resources" and "resources".
        self.assertTrue(web_file("hud/resources/Logos/banner1.png"))
        self.assertTrue(web_file("hud/Resources/Agentes/Jett/Jett.png"))
        # The scoreboard borrows the HUD's agent images.
        self.assertTrue(web_file("scoreboard/Resources/Agentes/Kayo/X.png"))
        self.assertTrue(web_file("scoreboard/resources/logos/Elimination.png"))
        self.assertIsNone(web_file("hud/../../valhud/config.py"))

    def test_every_agent_and_weapon_has_images(self):
        for agent in game.AGENTS:
            for f in (agent, "C", "Q", "E", "X"):
                self.assertTrue(web_file(f"hud/Resources/Agentes/{agent}/{f}.png"), f"{agent}/{f}")
        for weapon in game.WEAPONS:
            self.assertTrue(web_file(f"hud/Resources/Armas/{weapon}.png"), weapon)

    def test_gfx_address(self):
        from valhud.overlay_window import gfx_base_url
        self.assertEqual(gfx_base_url("192.168.2.40"), "http://192.168.2.40:8778")
        self.assertEqual(gfx_base_url("http://192.168.2.40:8778/overlay"), "http://192.168.2.40:8778")


if __name__ == "__main__":
    unittest.main()
