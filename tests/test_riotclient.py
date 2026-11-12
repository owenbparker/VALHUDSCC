import os
import tempfile
import time
import unittest

from valhud import riotclient
from valhud.config import Config

AGENTS = {"jett-id": "Jett", "omen-id": "Omen", "sage-id": "Sage"}


class RiotClientTests(unittest.TestCase):
    def test_lockfile_and_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "lockfile")
            with open(path, "w") as f:
                f.write("Riot Client:1234:56789:secretpw:https")
            self.assertEqual(riotclient.read_lockfile(path), (56789, "secretpw"))
        self.assertIsNone(riotclient.read_lockfile("/nonexistent/lockfile"))
        sessions = {"abc": {"productId": "valorant", "launchConfiguration": {"arguments": [
            "-ares-deployment=latam", "-config-endpoint=https://shared.na.a.pvp.net"]}}}
        self.assertEqual(riotclient.region_of(sessions), ("latam", "na"))
        self.assertEqual(riotclient.map_from_id("/Game/Maps/Triad/Triad"), "Haven")

    def test_pregame_to_agent_select(self):
        match = {"MapID": "/Game/Maps/Jam/Jam", "PhaseTimeRemainingNS": 42e9, "Teams": [
            {"TeamID": "Blue", "Players": [{"Subject": "b1", "CharacterID": "SAGE-ID", "CharacterSelectionState": "locked"}]},
            {"TeamID": "Red", "Players": [{"Subject": "r1", "CharacterID": "jett-id", "CharacterSelectionState": "selected"},
                                          {"Subject": "r2", "CharacterID": "", "CharacterSelectionState": ""}]}]}
        r = riotclient.select_reading(match, AGENTS, {"r1": "TenZ", "b1": "Boaster"}, attack_first="right")
        self.assertEqual(r["map"], "Lotus")
        self.assertEqual(round(r["timer"]), 42)
        self.assertIn({"team": "left", "slot": 1, "agent": "Sage", "locked": True, "name": "Boaster"}, r["players"])
        self.assertIn({"team": "right", "slot": 1, "agent": "Jett", "locked": False, "name": "TenZ"}, r["players"])
        self.assertIn({"team": "right", "slot": 2, "agent": "", "locked": False}, r["players"])

    def test_roster(self):
        match = {"Players": [{"Subject": "r1", "TeamID": "Red", "CharacterID": "omen-id"},
                             {"Subject": "b1", "TeamID": "Blue", "CharacterID": "jett-id"}]}
        self.assertEqual(riotclient.roster(match, AGENTS, {"r1": "Derke"}),
                         {"left": [{"name": "Derke", "agent": "Omen"}], "right": [{"name": "", "agent": "Jett"}]})


class AppTests(unittest.TestCase):
    def test_riot_names_and_select_priority(self):
        from valhud.app import HudApp
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(os.path.join(tmp, "config.json"))
            cfg.update({"output_dir": os.path.join(tmp, "out")})
            app = HudApp(cfg)
            app.ingest({"source": "screen", "players": [{"team": "left", "slot": 2, "agent": "Omen"}]})
            app.ingest({"source": "riot", "riot_roster": {"left": [{"name": "Derke", "agent": "Omen"}], "right": []}})
            self.assertEqual(app.state["players"][1]["name"], "Derke")
            app.ingest({"source": "riot", "agent_select": {"active": True, "players": [
                {"team": "left", "slot": 1, "agent": "Jett", "locked": True, "name": "TenZ"}]}})
            app.ingest({"source": "screen", "agent_select": {"active": True, "players": [
                {"team": "defenders", "slot": 1, "agent": "Sage"}]}})
            v = app.agent_select.view([])
            self.assertEqual((v["players"]["left"][0]["agent"], v["players"]["left"][0]["name"]), ("Jett", "TenZ"))
            self.assertEqual(v["source"], "riot")
            self.assertLess(app.app_info()["riot"]["received"], 5)


if __name__ == "__main__":
    unittest.main()
