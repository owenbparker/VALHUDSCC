"""The screen reader mid-round: low health, the kill feed and K/D/A."""

import os
import unittest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def frame_with(path, at=(0, 0)):
    """A black 1920x1080 frame with a cut-out pasted in."""
    from PIL import Image
    img = Image.new("RGB", (1920, 1080))
    img.paste(Image.open(os.path.join(FIXTURES, path)).convert("RGB"), at)
    return img


class HealthBarTests(unittest.TestCase):
    def test_a_few_hp_is_alive(self):
        from PIL import Image, ImageDraw
        from valhud import reader
        img = Image.open(os.path.join(FIXTURES, "tab_scoreboard_rifles.png")).convert("RGB")
        x = reader.TOP_X["left"][0]
        d = ImageDraw.Draw(img)
        # 3 HP: the bar's fill is a sliver of red; the rest is empty.
        d.rectangle((x - 18, 77, x + 18, 82), fill=(0, 0, 0))
        d.rectangle((x - 19, 77, x - 19, 82), fill=(170, 45, 45))
        # Dead: no bar at all.
        x2 = reader.TOP_X["left"][1]
        d.rectangle((x2 - 22, 74, x2 + 22, 86), fill=(0, 0, 0))
        frame = reader.Frame(img)
        alive, health = reader.health_bar(frame, "left", 1)
        self.assertTrue(alive)
        self.assertLessEqual(health, 5)
        self.assertEqual(reader.health_bar(frame, "left", 2), (False, 0))
        self.assertEqual(reader.health_bar(frame, "left", 3), (True, 100))


class KillFeedTests(unittest.TestCase):
    SEATS = {("right", 1): "Sova", ("right", 2): "Jett", ("right", 3): "Omen", ("right", 4): "Killjoy",
             ("right", 5): "Skye", ("left", 1): "Reyna", ("left", 2): "Neon", ("left", 3): "Brimstone",
             ("left", 4): "Viper", ("left", 5): "Fade"}

    def test_a_real_kill_bar(self):
        # From a broadcast: a Sova (teal, defending) kills a Neon with a Vandal.
        from valhud import killfeed, reader
        frame = reader.Frame(frame_with("kill_feed_bar.png", (1400, 80)))
        bars = killfeed.read(frame, self.SEATS, attackers="left")
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0]["killer"], ("right", 1))
        self.assertEqual(bars[0]["victim"], ("left", 2))
        self.assertEqual(bars[0]["weapon"], "Vandal")
        self.assertFalse(bars[0]["team_kill"])

    def test_nothing_on_a_scoreboard_frame(self):
        from PIL import Image
        from valhud import killfeed, reader
        frame = reader.Frame(Image.open(os.path.join(FIXTURES, "tab_scoreboard_rifles.png")))
        self.assertEqual(killfeed.find_bars(frame), [])


class LiveKdaTests(unittest.TestCase):
    def test_counts_each_death_and_kill_once(self):
        from valhud.killfeed import LiveKda
        kda = LiveKda()
        a, b = ("left", 1), ("right", 2)
        self.assertIsNone(kda.values(a))          # nothing until the scoreboard's read
        kda.board(a, 2, 2, 0)
        kda.board(b, 1, 0, 3)
        for seat in (a, b):
            kda.alive(seat, True)
        # b dies: the top bar sees it, then the kill bar is read (many times).
        self.assertTrue(kda.alive(b, False))
        self.assertFalse(kda.alive(b, False))
        for _ in range(3):
            kda.kill(a, b)
        self.assertEqual(kda.values(a), (3, 2, 0))
        self.assertEqual(kda.values(b), (1, 1, 3))
        # Next round: the old bar's still up while b is alive again: no kill.
        kda.alive(b, True)
        self.assertFalse(kda.kill(a, b))
        self.assertEqual(kda.values(a), (3, 2, 0))
        # The scoreboard read in the buy phase is the truth again.
        kda.board(a, 3, 2, 1)
        self.assertEqual(kda.values(a), (3, 2, 1))
        # A kill bar read before the top bar caught the death still counts both.
        kda.alive(b, False)
        kda.kill(a, b)
        self.assertEqual(kda.values(a), (4, 2, 1))
        self.assertEqual(kda.values(b), (1, 2, 3))

    def test_team_kill_gives_no_kill(self):
        from valhud.killfeed import LiveKda
        kda = LiveKda()
        a, b = ("left", 1), ("left", 2)
        kda.board(a, 0, 0, 0)
        kda.board(b, 0, 0, 0)
        kda.alive(b, True)
        kda.alive(b, False)
        kda.kill(a, b)
        self.assertEqual(kda.values(a), (0, 0, 0))
        self.assertEqual(kda.values(b), (0, 1, 0))


if __name__ == "__main__":
    unittest.main()
