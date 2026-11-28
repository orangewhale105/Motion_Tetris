import math
import os
import random
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import whale_fall as wf  # noqa: E402


def at(month, day, hour, minute=0):
    return time.mktime((2026, month, day, hour, minute, 0, 0, 0, -1))


def make(hour=12):
    w = wf.World()
    w.clock = lambda: at(6, 21, hour)
    w.update_daylight(w.clock(), log=False)
    w.seed_rocks()
    return w


class TestGenome(unittest.TestCase):
    def test_ranges_and_pixels(self):
        random.seed(1)
        gs = [wf.random_genome() for _ in range(2000)]
        for g in gs[:200]:
            c = wf.mutate(wf.crossover(g, gs[1]))
            for k in wf.FLOAT_GENES:
                self.assertTrue(0.0 <= c[k] <= 1.0)
        dark = sum(wf.is_dark(g) for g in gs)
        self.assertTrue(10 < dark < 150)
        self.assertEqual({wf.style_of(g) for g in gs}, set(range(7)))
        for mode in ("normal", "umbrella", "brood", "dead", "glow"):
            px = wf.dumbo_pixels(gs[0], 0, mode)
            self.assertEqual(len(px[0]), 13)
        self.assertTrue(wf.traits(dict(gs[0], care=0.1)))


class TestWorld(unittest.TestCase):
    def test_whale_falls_and_stages(self):
        random.seed(2)
        w = make()
        w.seed()
        self.assertTrue(w.whale.falling)
        for _ in range(int(wf.FALL_TIME / 0.5) + 2):
            w.step(0.5)
        self.assertFalse(w.whale.falling)
        self.assertAlmostEqual(w.whale.y, w.floor(w.whale.x) - 12, delta=1)
        stages = set()
        first = w.whale
        for _ in range(6 * 24):
            w.advance_offline(3600, start=w.clock())
            stages.add(w.whale.stage if w.whale is first else "new whale")
        self.assertEqual(len(stages), 5)          # 4 段階 + 次のクジラ
        self.assertGreater(w.births, 0)

    def test_run_half_day_with_mouse(self):
        random.seed(3)
        w = wf.World()
        base = at(6, 21, 8)
        w.clock = lambda: base + w.time
        w.update_daylight(w.clock(), log=False)
        w.seed()
        for i in range(int(12 * 3600 / 0.5)):
            if i % 60 == 0:
                w.cursor = (random.uniform(0, w.w), random.uniform(0, w.h))
                w.cursor_speed = random.choice([0, 100, 1500])
                t = w.hit(*w.cursor, pad=30)
                if t:
                    (w.poke if i % 120 == 0 else lambda x: w.pet(x, 70))(t)
                elif i % 300 == 0:
                    w.add_crusts(*w.cursor)
                if i % 2000 == 0:
                    w.drop_foodfall(*w.cursor)
                w.hover_info(*w.cursor)
                for t in w.dumbos:
                    w.dumbo_info(t)
            w.step(0.5)
            self.assertLessEqual(w.population(), wf.MAX_DUMBOS + 10)
        self.assertGreater(w.laid, 0)
        self.assertGreater(len(w.dumbos) + len(w.eggs), 0)

    def test_brood_and_hatch(self):
        random.seed(4)
        w = make()
        mom = wf.Dumbo(wf.random_genome(), 200, 380, age=wf.ADULT_AGE, sex="F")
        mom.energy, mom.fatigue = 1.0, 0
        mom.clutch = [{"g": wf.random_genome(), "gen": 2, "par": "#1 x #2"} for _ in range(3)]
        w.dumbos = [mom]
        for _ in range(4000):
            w.step(0.5)
            if mom.state == "brood":
                break
        self.assertEqual(mom.state, "brood")
        self.assertEqual(len(w.eggs), 1)
        w.eggs[0].t = 0.5
        for _ in range(5):
            w.step(0.5)
        self.assertEqual(w.births, 3)
        self.assertNotEqual(mom.state, "brood")

    def test_predators_and_friends(self):
        random.seed(5)
        w = make()
        ts = []
        for i in range(6):
            g = wf.random_genome()
            g.update(whim=0.9, care=0.9, flock=0.9, cursor=0.9)
            t = wf.Dumbo(g, 300 + i * 10, 320, age=wf.ADULT_AGE)
            t.energy, t.fatigue, t.mate_cd = 1.0, 0, 1e9
            ts.append(t)
        w.dumbos = ts
        w._spawn_visitor("vampire")
        v = w.visitors[0]
        v.x, v.y, v.y0 = 320, 330, 330
        played = False
        for _ in range(200):
            w.step(0.1)
            played = played or any(t.state == "play" for t in ts)
        self.assertTrue(played)
        w.visitors = []
        w._spawn_visitor("angler")
        a = w.visitors[0]
        a.x, a.y, a.y0 = 310, 330, 330
        lured = False
        for _ in range(3000):
            w.step(0.1)
            lured = lured or any(t.state == "lured" for t in w.dumbos)
            if a.ate or a.gone:
                break
        self.assertTrue(lured)
        for kind in ("sleeper", "sperm", "isopod", "hagfish"):
            w._spawn_visitor(kind)
        for _ in range(300):
            w.step(0.1)

    def test_save_load_offline(self):
        random.seed(6)
        w = make()
        w.seed()
        with tempfile.TemporaryDirectory() as d:
            wf.save_world(w, d)
            w2, away = wf.load_world(d)
            self.assertEqual(len(w2.dumbos), len(w.dumbos))
            self.assertLess(away, 5)
            b, dd, laid = w2.advance_offline(2 * 24 * 3600)
            self.assertGreater(b, 0)
            self.assertGreater(laid, 0)
            wf.save_world(w2, d)
            w3, _ = wf.load_world(d)
            self.assertEqual(len(w3.dumbos), len(w2.dumbos))
            for _ in range(50):
                w3.step(0.2)


if __name__ == "__main__":
    unittest.main()
