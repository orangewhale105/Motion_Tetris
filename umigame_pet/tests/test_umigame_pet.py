import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import umigame_pet as up  # noqa: E402


class TestGenome(unittest.TestCase):
    def test_crossover_mutate_ranges(self):
        random.seed(1)
        a, b = up.random_genome(), up.random_genome()
        for _ in range(200):
            c = up.mutate(up.crossover(a, b))
            for k in up.FLOAT_GENES:
                self.assertTrue(0.0 <= c[k] <= 1.0)
            self.assertEqual(len(c["pattern"]), up.PATTERN_BITS)

    def test_distance(self):
        a = up.random_genome()
        self.assertEqual(up.distance(a, a), 0.0)
        self.assertLess(up.distance(a, up.blend(a, a)), 1e-9)


class TestWorld(unittest.TestCase):
    def test_run_one_hour_with_cursor_and_clicks(self):
        random.seed(2)
        w = up.World()
        w.seed()
        for i in range(36000):   # 0.1秒 x 1時間
            if i % 50 == 0:
                w.cursor = (random.uniform(0, w.w), random.uniform(0, w.h))
                w.cursor_speed = random.choice([0, 100, 1500])
                t = w.hit(*w.cursor)
                if t:
                    w.poke(t)
                else:
                    w.drop_food(*w.cursor)
            w.step(0.1)
            self.assertLessEqual(w.population(), up.MAX_POP + 2)
        self.assertGreater(len(w.turtles) + len(w.eggs), 0)

    def test_offline_and_save_load(self):
        random.seed(3)
        w = up.World()
        w.seed()
        with tempfile.TemporaryDirectory() as d:
            up.save_world(w, d)
            w2, away = up.load_world(d)
            self.assertEqual(len(w2.turtles), len(w.turtles))
            self.assertLess(away, 5)
            b, dd = w2.advance_offline(3 * 24 * 3600)
            self.assertGreater(b, 0)
            self.assertGreater(dd, 0)
            self.assertGreater(len(w2.turtles) + len(w2.eggs), 0)
            up.save_world(w2, d)

    def test_merge(self):
        random.seed(4)
        w = up.World()
        g = up.random_genome()
        a = up.Turtle(g, 100, 100)
        b = up.Turtle(dict(g), 101, 100)
        a.energy = b.energy = 0.2
        a.fatigue = b.fatigue = 0
        w.turtles = [a, b]
        for _ in range(100):
            w._pairs([t for t in w.turtles if t.alive], 0.1)
            if len(w.turtles) == 1:
                break
        self.assertEqual(len(w.turtles), 1)
        self.assertEqual(w.turtles[0].scale, max(a.scale, b.scale) + 1)


if __name__ == "__main__":
    unittest.main()
