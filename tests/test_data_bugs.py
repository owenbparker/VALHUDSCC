"""The overnight data bug hunt (2026-11-14): each test is a bug the HUD had
reading the game."""

import os
import tempfile
import time
import unittest

from valhud import game
from valhud.agentselect import AgentSelect, map_name
from valhud.config import Config

HERE = os.path.dirname(__file__)
SELECT = os.path.join(HERE, "fixtures", "agent_select")


def frame(*path):
    from PIL import Image
    return Image.open(os.path.join(HERE, "fixtures", *path))


def make_app(tmp, **cfg):
    from valhud.app import HudApp
    c = Config(os.path.join(tmp, "config.json"))
    c.update(dict({"output_dir": os.path.join(tmp, "out")}, **cfg))
    return HudApp(c)


class HeaderIsNotTheMatchTests(unittest.TestCase):
    """Agent select's teal/red header sits where the match's top bar does:
    it read as the match (attackers on the right), so agent select ended at
    the first frame its timer box wasn't recognised, every player read dead
    and a death was counted for each."""

    def setUp(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")

    def test_agent_select_is_not_the_top_bar(self):
        from valhud.reader import Frame, attacking_side, in_match, select_header
        for name in ("locked_00.webp", "mixed_38.webp", "hover_62.webp", "empty_70_taskbar.webp"):
            f = Frame(frame("agent_select", name))
            self.assertTrue(select_header(f), name)
            self.assertIsNone(attacking_side(f), name)
            self.assertFalse(in_match(f), name)
        f = Frame(frame("agent_select", "loading.webp"))
        self.assertFalse(in_match(f))
        for path in (("spectate", "card_gora46_cypher.webp"), ("tab_scoreboard.png",), ("tab_scoreboard_rifles.png",)):
            f = Frame(frame(*path))
            self.assertFalse(select_header(f), path)
            self.assertTrue(in_match(f), path)

    def test_agent_select_not_ended_by_a_frame_it_cant_read(self):
        from PIL import Image
        from valhud.reader import SelectTracker
        sent = []
        t = SelectTracker(sent.append)
        t.check(frame("agent_select", "locked_00.webp"), None)
        # The same screen with the timer box covered: not read as agent
        # select, but not the match either.
        img = frame("agent_select", "locked_00.webp").convert("RGB")
        img.paste(Image.new("RGB", (200, 80), (20, 20, 20)), (860, 40))
        self.assertTrue(t.check(img, None))
        self.assertTrue(t.active)
        self.assertNotEqual(sent[-1]["agent_select"], {"active": False})


class LockedPicksStayTests(unittest.TestCase):
    """A locked pick was wiped by a card read empty for two frames (or an
    agent the source didn't know): York's first player lost Killjoy."""

    def test_locked_pick_kept_through_empty_readings(self):
        s = AgentSelect()
        s.apply({"active": True, "players": [{"team": "left", "slot": 1, "agent": "Killjoy", "locked": True}]}, "riot")
        s.apply({"players": [{"team": "left", "slot": 1, "agent": "", "locked": False}]}, "riot")
        s.apply({"players": [{"team": "left", "slot": 1, "agent": "Mystery", "locked": True}]}, "riot")
        self.assertEqual(s.state["players"]["left"][0], {"agent": "Killjoy", "locked": True, "name": ""})
        # Another locked agent corrects it; the control panel can change anything.
        s.apply({"players": [{"team": "left", "slot": 1, "agent": "Cypher", "locked": True}]}, "screen")
        self.assertEqual(s.state["players"]["left"][0]["agent"], "Cypher")
        s.apply({"players": [{"team": "left", "slot": 1, "agent": "", "locked": False}]}, "control panel")
        self.assertEqual(s.state["players"]["left"][0]["agent"], "")
        # Hovering still changes freely.
        s.apply({"players": [{"team": "left", "slot": 2, "agent": "Jett", "locked": False}]}, "screen")
        s.apply({"players": [{"team": "left", "slot": 2, "agent": "", "locked": False}]}, "screen")
        self.assertEqual(s.state["players"]["left"][1]["agent"], "")

    def test_tracker_keeps_a_lock_through_misreads(self):
        from valhud import selectreader
        from valhud.reader import SelectTracker
        sent = []
        t = SelectTracker(sent.append)
        readings = iter([[("Killjoy", True)], [("Killjoy", True)], [("", False)], [("", False)], [("", False)]])
        real = selectreader.read
        selectreader.read = lambda *a, **k: {"active": True, "players": [
            {"team": "defenders", "slot": 1, "agent": a_, "locked": l_} for a_, l_ in next(readings)]}
        try:
            for _ in range(5):
                t.check(None, None)
        finally:
            selectreader.read = real
        p = sent[-1]["agent_select"]["players"][0]
        self.assertEqual((p["agent"], p["locked"]), ("Killjoy", True))


class RemadeAgentSelectTests(unittest.TestCase):
    def test_names_start_again_when_agent_select_comes_back(self):
        from valhud import selectreader
        from valhud.reader import SelectTracker
        t = SelectTracker(lambda u: None)
        real = selectreader.read
        selectreader.read = lambda *a, **k: {"active": True, "players": []}
        try:
            t.check(None, None)
            t._names[("defenders", 0)] = "OldSeatName"
            t.seen_at = time.time() - 60   # off screen a minute (a remake), now back
            t.check(None, None)
        finally:
            selectreader.read = real
        self.assertEqual(t._names, {})


class SummitTests(unittest.TestCase):
    def test_summit_is_a_map_everywhere(self):
        from valhud import riotclient
        self.assertEqual(map_name("SUMMIT"), "Summit")
        self.assertEqual(riotclient.map_from_id("/Game/Maps/Plummet/Plummet"), "Summit")
        self.assertTrue(os.path.isfile(os.path.join(HERE, "..", "web", "hud", "Resources", "Maps", "Summit.png")))
        self.assertTrue(os.path.isfile(os.path.join(HERE, "..", "web", "reader_refs", "select", "maps", "Summit.png")))

    def test_riot_map_list_learns_new_maps(self):
        from valhud import riotclient
        rc = riotclient.RiotClient(lambda u: None, Config(os.path.join(tempfile.mkdtemp(), "c.json")), tempfile.mkdtemp())
        rc._get = lambda *a, **k: {"data": [{"displayName": "Summit", "mapUrl": "/Game/Maps/NewCode/NewCode"},
                                            {"displayName": "Gauntlet", "mapUrl": "/Game/Maps/AbilityDraft/AbilityDraft"}]}
        rc._load_maps()
        self.assertEqual(riotclient.map_from_id("/Game/Maps/NewCode/NewCode"), "Summit")
        self.assertEqual(riotclient.map_from_id("/Game/Maps/AbilityDraft/AbilityDraft"), "")


class RiotOneTeamTests(unittest.TestCase):
    """The Riot Client's agent select had only its own account's team (a
    player's account sees only its team): the screen was shut out for two
    minutes, so the other team stayed empty."""

    def test_screen_fills_the_team_the_riot_client_lacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, attack_first="left")
            app.ingest({"source": "riot", "agent_select": {"active": True, "players": [
                {"team": "left", "slot": 1, "agent": "Killjoy", "locked": True, "name": "RiotName"}]}})
            app.ingest({"source": "screen", "agent_select": {"active": True, "players": [
                {"team": "attackers", "slot": 1, "agent": "Jett", "locked": True, "name": "ScreenL"},
                {"team": "defenders", "slot": 1, "agent": "Sova", "locked": True, "name": "ScreenR"}]}})
            v = app.agent_select.view([])["players"]
            self.assertEqual((v["left"][0]["agent"], v["left"][0]["name"]), ("Killjoy", "RiotName"))   # the Riot Client's
            self.assertEqual((v["right"][0]["agent"], v["right"][0]["name"]), ("Sova", "ScreenR"))     # off the screen


class FreshAgentSelectTests(unittest.TestCase):
    """A new agent select only cleared the last map's data when that map was
    recorded as won: otherwise its players lent their names to this agent
    select's cards (by agent)."""

    def test_last_maps_players_dont_name_the_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp)
            app.ingest({"source": "screen", "players": [{"team": "left", "slot": 1, "agent": "Killjoy", "name": "LastMap"}]})
            app.ingest({"source": "screen", "agent_select": {"active": True, "players": [
                {"team": "defenders", "slot": 1, "agent": "Killjoy", "locked": True}]}})
            app.refresh()
            v = app.snapshot()["agent_select"]["players"]
            self.assertEqual(v["right"][0]["agent"], "Killjoy")
            self.assertEqual(v["right"][0]["name"], "")


class SidesFromNamesTests(unittest.TestCase):
    """Who attacks first left set the wrong way round put every agent select
    name and agent under the other team."""

    def test_agent_select_turned_round_by_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, attack_first="left", left={"name": "York"}, right={"name": "Saints"})
            app.rosters.names = {"york": {"yorkone", "yorktwo", "yorkthree"}, "saints": {"saintone", "sainttwo"}}
            # Defenders (shown left) are York's players: York defends first.
            app.ingest({"source": "screen", "agent_select": {"active": True, "players": [
                {"team": "defenders", "slot": 1, "agent": "Killjoy", "locked": True, "name": "YorkOne"},
                {"team": "defenders", "slot": 2, "agent": "Omen", "locked": True, "name": "YorkTwo"},
                {"team": "attackers", "slot": 1, "agent": "Jett", "locked": True, "name": "SaintOne"}]}})
            self.assertEqual(app.config.get()["attack_first"], "right")
            v = app.agent_select.view([])["players"]
            self.assertEqual(v["left"][0]["name"], "YorkOne")
            self.assertEqual(v["right"][0]["name"], "SaintOne")

    def test_attack_first_from_the_top_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, attack_first="left")
            for _ in range(6):
                app.ingest({"source": "screen", "match": {"attackers": "right", "score": {"left": 2, "right": 1}, "round": 4}})
            self.assertEqual(app.config.get()["attack_first"], "right")
            # Second half: the attackers have swapped, who attacked first hasn't.
            for _ in range(6):
                app.ingest({"source": "screen", "match": {"attackers": "left", "score": {"left": 8, "right": 6}, "round": 15}})
            self.assertEqual(app.config.get()["attack_first"], "right")

    def test_riot_roster_turned_round_by_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, attack_first="left")
            app.ingest({"source": "screen", "players": [
                {"team": "left", "slot": i + 1, "agent": a} for i, a in enumerate(["Jett", "Sova", "Omen"])] + [
                {"team": "right", "slot": i + 1, "agent": a} for i, a in enumerate(["Raze", "Viper", "Sage"])]})
            app.ingest({"source": "riot", "riot_roster": {
                "left": [{"name": "R1", "agent": "Raze"}, {"name": "R2", "agent": "Viper"}, {"name": "R3", "agent": "Sage"}],
                "right": [{"name": "L1", "agent": "Jett"}, {"name": "L2", "agent": "Sova"}, {"name": "L3", "agent": "Omen"}]}})
            by = {(p["team"], p["slot"]): p["name"] for p in app.state["players"]}
            self.assertEqual(by[("left", 1)], "L1")
            self.assertEqual(by[("right", 3)], "R3")


class NextMapWithoutAgentSelectTests(unittest.TestCase):
    """A won map cleared the HUD until the next agent select was seen: with
    the reader off in agent select (or only the Riot Client seeing it) the
    HUD stayed blank the whole next map."""

    def test_next_maps_score_brings_the_hud_back(self):
        from valhud import series
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, maps=[{"name": "Lotus", "winner": ""}, {"name": "Bind", "winner": ""}], current_map=0)
            app.ingest({"source": "screen", "match": {"score": {"left": 12, "right": 10}}})
            app.ingest({"source": "screen", "match": {"score": {"left": 13, "right": 10}}})
            self.assertEqual(app.config.get()["maps"][0]["winner"], "left")
            app.series.won_at -= series.CLEAR_AFTER + 1
            app.refresh()
            self.assertTrue(app.series.cleared)
            app.ingest({"source": "screen", "match": {"score": {"left": 0, "right": 0}},
                        "players": [{"team": "left", "slot": 1, "agent": "Jett"}]})
            self.assertFalse(app.series.cleared)
            self.assertEqual(app.config.get()["current_map"], 1)
            self.assertEqual(app.state["players"][0]["agent"], "Jett")


class NamesNeedTwoReadsTests(unittest.TestCase):
    def test_one_misread_name_doesnt_show(self):
        from valhud.reader import ScreenReader
        r = ScreenReader(lambda u: None)
        up = lambda n: {"players": [{"team": "left", "slot": 1, "name": n}]}
        u = up("chronicle"); r._steady_names(u); self.assertNotIn("name", u["players"][0])
        u = up("chronicle"); r._steady_names(u); self.assertEqual(u["players"][0]["name"], "chronicle")
        u = up("chr"); r._steady_names(u); self.assertEqual(u["players"][0]["name"], "chronicle")
        u = up("chronicle"); r._steady_names(u); self.assertEqual(u["players"][0]["name"], "chronicle")

    def test_riot_id_wins_over_a_read_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, player_names={"left": ["", "Typed", "", "", ""], "right": [""] * 5})
            app.ingest({"source": "screen", "players": [{"team": "left", "slot": 1, "agent": "Jett", "name": "chr"},
                                                        {"team": "left", "slot": 2, "agent": "Sova", "name": "x"}]})
            app.ingest({"source": "riot", "riot_roster": {"left": [{"name": "chronicle", "agent": "Jett"},
                                                                   {"name": "RiotSova", "agent": "Sova"}], "right": []}})
            self.assertEqual(app.state["players"][0]["name"], "chronicle")
            self.assertEqual(app.state["players"][1]["name"], "Typed")


class AttackFirstFromMapBansTests(unittest.TestCase):
    def test_side_pick_sets_who_attacks_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [{"map": "Abyss"}, {"map": "Bind"}, {"map": "Haven", "side": "defence"},
                     {"map": "Lotus", "side": "defence"}, {"map": "Sunset"}, {"map": "Corrode"}, {"side": "attack"}]
            app = make_app(tmp, best_of=3, attack_first="left",
                           map_bans={"team_a": "left", "pool": None, "bo3": {"steps": steps}})
            app.refresh()
            cfg = app.config.get()
            self.assertEqual([m["name"] for m in cfg["maps"]], ["Haven", "Lotus", "Summit"])
            # Haven: Team A's pick, the right team chose to defend -> left attacks.
            self.assertEqual(cfg["attack_first"], "left")
            app.config.update({"current_map": 1})
            app.refresh()   # Lotus: the left team chose defence
            self.assertEqual(app.config.get()["attack_first"], "right")
            app.config.update({"current_map": 2})
            app.refresh()   # the decider: Team A (left) chose attack
            self.assertEqual(app.config.get()["attack_first"], "left")
            app.config.update({"attack_first": "right"})   # set by hand: left alone
            app.refresh()
            self.assertEqual(app.config.get()["attack_first"], "right")


class ObserverPcRiotSidesTests(unittest.TestCase):
    """The Riot Client on the observer PC put teams on sides by that PC's own
    "who attacks first" (never set there), not the GFX PC's."""

    def test_riot_readings_turned_to_this_pcs_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = make_app(tmp, attack_first="right")
            app.ingest({"source": "riot", "agent_select": {"active": True, "attack_first": "left", "players": [
                {"team": "left", "slot": 1, "agent": "Killjoy", "locked": True, "name": "RedPlayer"}]}})
            v = app.agent_select.view([])["players"]
            self.assertEqual(v["right"][0]["name"], "RedPlayer")
            app.ingest({"source": "riot", "attack_first": "left",
                        "riot_roster": {"left": [{"name": "RedPlayer", "agent": "Killjoy"}], "right": []}})
            self.assertEqual(app.riot_roster["right"][0]["name"], "RedPlayer")


class CamMatchTests(unittest.TestCase):
    def test_exact_name_beats_an_earlier_close_one(self):
        from valhud.cams import match_players
        players = [{"team": "left", "slot": 1, "name": "Leafy"}, {"team": "left", "slot": 2, "name": "Leaf"}]
        got = match_players(["Leafy1#NA1", "Leafy#NA1"], players)
        self.assertEqual(got["Leafy#NA1"]["slot"], 1)


class AgentSelectNameCutShortTests(unittest.TestCase):
    """Names confirmed mid-animation stayed cut short ("Juw" for "Juwan")."""

    def test_longer_name_takes_over(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy not installed")
        from valhud import selectreader

        class Ocr:
            calls = 0

            def words(self, img):
                Ocr.calls += 1
                return [("Juw" if Ocr.calls <= 30 else "Juwan", 0, 0)]
        img = frame("agent_select", "locked_00.webp")
        names, ocr, layout = {}, Ocr(), selectreader.Layout()
        for _ in range(2):
            selectreader.read(img, ocr, names, layout)
        self.assertEqual(names[("defenders", 0)], "Juw")
        for _ in range(3):
            for k in [k for k in names if k[0] == "checked"]:
                names[k] = 0   # (as if two seconds had passed)
            selectreader.read(img, ocr, names, layout)
        self.assertEqual(names[("defenders", 0)], "Juwan")


if __name__ == "__main__":
    unittest.main()
