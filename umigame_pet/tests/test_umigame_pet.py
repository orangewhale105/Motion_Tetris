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

    def test_distance_and_traits(self):
        a = up.random_genome()
        self.assertEqual(up.distance(a, a), 0.0)
        g = dict(a, activity=0.1, appetite=0.9, care=0.1, whim=0.9)
        t = up.traits(g)
        self.assertIn("Sleepyhead", t)
        self.assertIn("Big eater", t)
        self.assertIn("Carefree", t)
        self.assertIn("Free spirit", t)
        g = dict(a, care=0.9, flock=0.1, cursor=0.9)
        self.assertIn("Loner", up.traits(g))
        self.assertIn("Cursor lover", up.traits(g))

    def test_lineage_names(self):
        self.assertEqual(up.lineage_name(0), "A")
        self.assertEqual(up.lineage_name(25), "Z")
        self.assertEqual(up.lineage_name(26), "AA")


class TestWorld(unittest.TestCase):
    def test_run_one_hour_with_mouse(self):
        random.seed(2)
        w = up.World()
        w.seed()
        for i in range(18000):   # 0.2秒 x 1時間
            if i % 50 == 0:
                w.cursor = (random.uniform(0, w.w), random.uniform(0, w.h))
                w.cursor_speed = random.choice([0, 100, 1500])
                t = w.hit(*w.cursor)
                if t:
                    w.poke(t)
                elif i % 200 == 0:
                    w.drop_jelly(*w.cursor)
                w.hover_info(*w.cursor)
                for t in w.turtles:
                    w.turtle_info(t)
                tt = w.hit(*w.cursor, pad=40)
                if tt:
                    w.pet(tt, 70)
            w.step(0.2)
            self.assertLessEqual(w.population(), up.MAX_TURTLES + 3)
        self.assertGreater(w.births, 0)
        self.assertGreater(w.laid, 0)
        self.assertGreater(len(w.turtles) + len(w.eggs), 0)
        for e in w.eggs:            # 卵は砂浜にある
            self.assertFalse(w.in_water(e.x, e.y))

    def test_shark_eats_big_turtle(self):
        random.seed(6)
        w = up.World()
        w.seed_plants()
        big = up.Turtle(up.random_genome(), 300, 60, age=up.ADULT_AGE, extra=1)
        small = up.Turtle(up.random_genome(), 320, 60, age=0)
        w.turtles = [big, small]
        self.assertGreaterEqual(big.scale, up.SHARK_PREY_SCALE)
        w.shark_t = 0
        w.step(0.1)
        self.assertIsNotNone(w.shark)
        w.shark.x, w.shark.y = 200, 60
        fled = False
        for _ in range(600):
            big.x, big.y, big.energy = 300, 60, 1.0     # 逃げられないように固定
            w.step(0.1)
            fled = fled or small.state == "flee_shark"
            if not big.alive:
                break
        self.assertFalse(big.alive)
        self.assertEqual(big.cause, "a shark attack")
        self.assertTrue(fled)

    def test_breathe_and_pet(self):
        random.seed(7)
        w = up.World()
        w.seed_plants()
        t = up.Turtle(up.random_genome(), 200, 150, age=up.ADULT_AGE)
        t.energy, t.fatigue, t.air = 1.0, 0.0, 0.0
        w.turtles = [t]
        w.step(0.1)
        self.assertEqual(t.state, "breathe")
        self.assertTrue(any(f[0] == "ripple" for f in w.fx))
        for _ in range(40):
            w.step(0.1)
        self.assertGreater(t.air, 0)
        t.g.update(cursor=1.0, care=1.0)
        t.state = "swim"
        w.pet(t, up.PET_STROKE)
        self.assertEqual(t.state, "petted")
        self.assertEqual(t.pets, 1)
        t.g.update(cursor=0.0, care=1.0, temper=1.0)
        t.state, t.joy = "swim", 0.0
        for _ in range(5):
            w.pet(t, up.PET_STROKE)
        self.assertGreater(t.annoy, 0.4)

    def test_overpopulation_starves(self):
        """餌が足りないほど増えると、水草が減って餓死が起きる。"""
        random.seed(5)
        w = up.World()
        w.seed_plants()
        for i in range(38):
            x, y = w.water_point()
            t = up.Turtle(up.random_genome(), x, y, sex="FM"[i % 2], lineage="A")
            t.age = up.ADULT_AGE
            t.energy = 0.5
            w.turtles.append(t)
        b0 = sum(p.b for p in w.plants)
        for _ in range(9000):
            w.step(0.2)
        self.assertLess(sum(p.b for p in w.plants), b0)
        self.assertGreater(w.deaths, 0)

    def test_offline_and_save_load(self):
        random.seed(3)
        w = up.World()
        w.seed()
        with tempfile.TemporaryDirectory() as d:
            up.save_world(w, d)
            w2, away = up.load_world(d)
            self.assertEqual(len(w2.turtles), len(w.turtles))
            self.assertEqual(len(w2.plants), len(w.plants))
            self.assertLess(away, 5)
            b, dd, laid = w2.advance_offline(2 * 24 * 3600)
            self.assertGreater(b, 0)
            self.assertGreater(dd, 0)
            self.assertGreater(laid, 0)
            self.assertGreater(len(w2.turtles) + len(w2.eggs), 0)
            up.save_world(w2, d)

    def test_old_save_format(self):
        """Ver 1 の保存データ(遺伝子が少ない・水草なし)も読める。"""
        old = {"w": 520, "h": 340, "turtles": [{"id": 1, "g": {"hue": 0.3, "pattern": [True] * 28},
                                                "x": 100, "y": 300, "gen": 2, "age": 5000.0,
                                                "energy": 0.5, "fatigue": 0.2, "mate_cd": 0,
                                                "scale": 3}], "eggs": []}
        w = up.World.from_dict(old)
        self.assertEqual(len(w.turtles), 1)
        self.assertTrue(w.plants)
        for _ in range(100):
            w.step(0.2)

    def test_merge_and_split(self):
        random.seed(4)
        w = up.World()
        g = up.random_genome()
        a = up.Turtle(g, 100, 100, age=up.ADULT_AGE)
        b = up.Turtle(dict(g), 101, 100, age=up.ADULT_AGE)
        a.energy = b.energy = 0.2
        w.turtles = [a, b]
        for _ in range(200):
            w._pairs(w.alive(), 0.1)
            if len(w.turtles) == 1:
                break
        self.assertEqual(len(w.turtles), 1)
        m = w.turtles[0]
        self.assertEqual(m.extra, 1)
        self.assertEqual(m.scale, max(a.scale, b.scale) + 1)
        m.energy = 1.0
        w._split(m)
        self.assertEqual(len(w.turtles), 2)
        self.assertTrue(all(t.extra == 0 for t in w.turtles))


if __name__ == "__main__":
    unittest.main()
