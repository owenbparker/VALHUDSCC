import json
import os
import tempfile
import time
import unittest

from valhud import overwolf
from valhud.config import Config

AGENTS = ["Jett", "Sova", "Omen", "Killjoy", "Raze", "Reyna", "Sage", "Viper", "Cypher", "Fade"]


def row(i, **kw):
    r = {"player_id": f"id{i}", "name": f"Player{i} #EUW", "character": AGENTS[i], "team": 0 if i < 5 else 1,
         "alive": True, "kills": i, "deaths": 1, "assists": 2, "money": 1000 + i, "shield": 2,
         "weapon": "TX_Hud_Rifles_Volcano", "ult_points": 3, "ult_max": 8, "spike": False}
    r.update(kw)
    return r


def board(rows, **match):
    info = {f"scoreboard_{i}": json.dumps(r) for i, r in enumerate(rows)}
    info.update({k: json.dumps(v) if isinstance(v, dict) else v for k, v in match.items()})
    return {"heartbeat": {"running": True, "features": ["match_info"]}, "info": {"match_info": info}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config(os.path.join(self.tmp.name, "config.json"))
        self.cfg.update({"output_dir": os.path.join(self.tmp.name, "out")})

    def tearDown(self):
        self.tmp.cleanup()


class TranslateTests(Base):
    def test_names_lookups(self):
        self.assertEqual(overwolf.agent("Clay_PC_C"), "Raze")
        self.assertEqual(overwolf.agent("KAY/O"), "Kayo")
        self.assertEqual(overwolf.agent("TX_Killfeed_Sage1"), "Sage")
        self.assertEqual(overwolf.weapon("TX_Hud_Sniper_Operater"), "Operator")
        self.assertEqual(overwolf.map_name("Jam"), "Lotus")
        self.assertEqual(overwolf.riot_name("TenZ #0505"), "TenZ")

    def test_scoreboard_to_players(self):
        ow = overwolf.Overwolf(self.cfg)
        up, sel = ow.receive(board([row(i) for i in range(10)], round_number="4", round_phase="combat",
                                   map="Jam", match_score={"team_0": 2, "team_1": 1}))
        self.assertIsNone(sel)
        by = {(p["team"], p["slot"]): p for p in up["players"]}
        self.assertEqual(len(by), 10)
        self.assertEqual(by[("left", 1)]["name"], "Player0")      # team 0 attacks first = left (default)
        self.assertEqual(by[("right", 1)]["agent"], "Reyna")
        self.assertEqual(by[("left", 1)]["shield"], 50)
        self.assertEqual(by[("left", 1)]["weapon"], "Vandal")
        self.assertEqual(by[("left", 2)]["credits"], 1001)
        m = up["match"]
        self.assertEqual((m["round"], m["phase"], m["map"]), (4, "combat", "Lotus"))
        self.assertEqual(m["score"], {"left": 2, "right": 1})
        self.assertEqual(m["attackers"], "left")

    def test_seats_follow_the_top_bar(self):
        ow = overwolf.Overwolf(self.cfg)
        # The screen sees the right team's agents in the other order, and team 0 on the right.
        ow.screen({"source": "screen", "players": [{"team": "right", "slot": s + 1, "agent": AGENTS[4 - s]}
                                                   for s in range(5)]})
        up, _ = ow.receive(board([row(i) for i in range(10)]))
        by = {(p["team"], p["slot"]): p for p in up["players"]}
        self.assertEqual(by[("right", 1)]["agent"], "Raze")
        self.assertEqual(by[("right", 5)]["agent"], "Jett")
        self.assertEqual(by[("left", 1)]["agent"], "Reyna")

    def test_screen_keeps_health_only(self):
        ow = overwolf.Overwolf(self.cfg)
        ow.receive(board([row(i, alive=i != 1) for i in range(10)], round_phase="combat"))
        out = ow.screen({"source": "screen", "match": {"phase": "buy", "timer": 30, "spike": {"state": "planted"}},
                         "players": [{"team": "left", "slot": 1, "alive": False, "health": 0, "kills": 9, "name": "x"},
                                     {"team": "left", "slot": 2, "alive": True, "health": 80},
                                     {"team": "left", "slot": 3, "health": 64, "alive": True}]})
        p1, p2, p3 = out["players"]
        self.assertEqual(p1, {"team": "left", "slot": 1, "alive": True})       # a missed bar isn't a death
        self.assertEqual((p2["alive"], p2["health"]), (False, 0))              # Overwolf says dead
        self.assertEqual(p3["health"], 64)
        self.assertNotIn("phase", out["match"])
        self.assertEqual(out["match"]["timer"], 30)                            # Overwolf has no timer

    def test_falls_back_when_quiet(self):
        ow = overwolf.Overwolf(self.cfg)
        ow.receive(board([row(i) for i in range(10)]))
        ow.heard_at = time.time() - overwolf.LIVE_FOR - 1
        update = {"source": "screen", "players": [{"team": "left", "slot": 1, "kills": 9, "health": 50}]}
        self.assertEqual(ow.screen(update), update)
        self.assertIn("screen reader reads everything", ow.status()["status"])
        # VALORANT closed: Overwolf's heard from but has nothing.
        self.assertEqual(ow.receive({"heartbeat": {"running": False}}), (None, None))

    def test_score_disagreement_sets_it_aside(self):
        ow = overwolf.Overwolf(self.cfg)
        ow.receive(board([row(i) for i in range(10)], match_score={"team_0": 3, "team_1": 1}))
        ow.screen({"source": "screen", "match": {"score": {"left": 1, "right": 3}}})
        ow._disagree_since -= overwolf.DISAGREE_FOR + 1
        self.assertFalse(ow.live())
        ow.screen({"source": "screen", "match": {"score": {"left": 3, "right": 1}}})
        self.assertTrue(ow.live())

    def test_round_history(self):
        ow = overwolf.Overwolf(self.cfg)
        rows = [row(i) for i in range(10)]
        ow.receive(board(rows, match_score={"team_0": 0, "team_1": 0}, round_number="1"))
        ow.receive({"events": [{"name": "spike_detonated", "data": ""}]})
        ow.receive(board(rows, match_score={"team_0": 1, "team_1": 0}, round_number="2"))
        dead = [row(i, alive=i >= 5) for i in range(10)]
        up, _ = ow.receive(board(dead, match_score={"team_0": 1, "team_1": 1}, round_number="3", round_phase="end"))
        self.assertEqual(up["match"]["rounds"], [{"winner": "left", "win_type": "Detonation"},
                                                 {"winner": "right", "win_type": "Elimination"}])
        self.assertEqual(up["match"]["round_winner"], "right")

    def test_sides_by_round(self):
        ow = overwolf.Overwolf(self.cfg)
        self.assertEqual([ow._attacking_team(r) for r in (1, 12, 13, 24, 25, 26)], [0, 0, 1, 1, 0, 1])

    def test_agent_select(self):
        ow = overwolf.Overwolf(self.cfg)
        roster = {f"roster_{i}": json.dumps({"name": f"P{i} #NA1", "player_id": f"id{i}", "character": AGENTS[i],
                                             "locked": i % 2 == 0}) for i in range(10)}
        up, sel = ow.receive({"heartbeat": {"running": True},
                              "info": {"game_info": {"scene": "CharacterSelectPersistentLevel"},
                                       "match_info": dict(roster, map="Bonsai")}})
        self.assertIsNone(up)
        self.assertTrue(sel["active"])
        self.assertEqual(sel["map"], "Split")
        self.assertEqual(sel["players"][0], {"team": "left", "slot": 1, "agent": "Jett", "locked": True, "name": "P0"})
        self.assertEqual(sel["players"][5]["team"], "right")
        self.assertTrue(ow.screen_select())
        _, sel = ow.receive({"heartbeat": {"running": True}, "info": {"game_info": {"scene": "Bonsai"}}})
        self.assertEqual(sel, {"active": False})


class AppTests(Base):
    def test_hud_takes_overwolf_and_screen_health(self):
        from valhud.app import HudApp
        app = HudApp(self.cfg)
        app.ingest({"source": "overwolf", "overwolf": board([row(i) for i in range(10)], round_phase="combat")})
        app.ingest({"source": "screen", "players": [{"team": "left", "slot": 1, "alive": True, "health": 42,
                                                     "kills": 7, "name": "misread"}]})
        p = app.state["players"][0]
        self.assertEqual((p["name"], p["kills"], p["health"], p["agent"]), ("Player0", 0, 42, "Jett"))
        self.assertTrue(app.app_info()["overwolf"]["live"])
        # Agent select from Overwolf wins over the screen's reading.
        app.ingest({"source": "overwolf", "overwolf": {"heartbeat": {"running": True}, "info": {
            "game_info": {"scene": "CharacterSelectPersistentLevel"},
            "match_info": {"roster_0": json.dumps({"name": "A #1", "character": "Omen", "locked": True})}}}})
        app.ingest({"source": "screen", "agent_select": {"active": True, "players": [
            {"team": "defenders", "slot": 1, "agent": "Sage"}]}})
        v = app.agent_select.view([])
        self.assertEqual(v["players"]["left"][0]["agent"], "Omen")
        self.assertEqual(v["source"], "overwolf")


if __name__ == "__main__":
    unittest.main()
