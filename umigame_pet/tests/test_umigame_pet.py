import os
import random
import sys
import math
import tempfile
import time
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


def clock_at(month, day, hour, minute=0):
    return time.mktime((2026, month, day, hour, minute, 0, 0, 0, -1))


def at(month, day, hour, minute=0):
    """カメの時刻が hour:minute になる実時刻(1時間 = カメの1日)。"""
    return up.real_for_turtle(clock_at(month, day, 0), hour, minute)


class TestDaylight(unittest.TestCase):
    def test_phases(self):
        self.assertEqual(up.daylight(clock_at(6, 21, 12))[0], "Daytime")
        self.assertEqual(up.daylight(clock_at(6, 21, 0))[0], "Night")
        self.assertEqual(up.daylight(clock_at(6, 21, 4, 40))[0], "Sunrise")      # 夏の日のイメージ
        self.assertEqual(up.daylight(clock_at(12, 21, 4, 40))[0], "Sunrise")     # 季節によらない
        self.assertEqual(up.daylight(clock_at(12, 21, 18, 30))[0], "Sunset")
        self.assertEqual(up.daylight(clock_at(6, 21, 19, 30))[0], "Dusk")
        self.assertGreater(up.daylight(clock_at(6, 21, 0))[1], 0.95)
        self.assertLess(up.daylight(clock_at(6, 21, 12))[1], 0.01)

    def test_turtle_clock(self):
        """実時間の40分 = カメの1日。10:00 が0:00、20分後が正午、30分後が18時、40分後がまた0:00。"""
        base = clock_at(6, 21, 10, 0)
        self.assertEqual(time.localtime(up.turtle_clock(base)).tm_hour, 0)
        self.assertEqual(time.localtime(up.turtle_clock(base + 20 * 60)).tm_hour, 12)
        self.assertEqual(time.localtime(up.turtle_clock(base + 30 * 60)).tm_hour, 18)
        self.assertEqual(time.localtime(up.turtle_clock(base + 40 * 60)).tm_hour, 0)
        self.assertEqual(time.localtime(up.turtle_clock(at(6, 21, 7, 30))).tm_hour, 7)

    def test_night_sleep_and_nesting(self):
        random.seed(8)
        for hour, expect_sleep in ((1, True), (12, False)):
            w = up.World()
            w.clock = lambda: at(6, 21, hour)
            w.update_daylight(w.clock(), log=False)
            w.seed_plants()
            ts = []
            for i in range(10):
                g = up.random_genome()
                g["activity"] = 0.2
                t = up.Turtle(g, 60 + i * 50, 120, age=up.ADULT_AGE, sex="F")
                t.energy, t.fatigue, t.air = 1.0, 0.3, 999
                ts.append(t)
            ts[0].clutch = [{"g": up.random_genome(), "gen": 2, "par": "x"}]
            w.turtles = ts
            for _ in range(50):
                w.step(0.2)
            sleeping = sum(t.state in ("sleep", "to_bed") for t in ts[1:])
            if expect_sleep:
                self.assertGreaterEqual(sleeping, 8)
                self.assertIn(ts[0].state, ("nest", "lay"))
            else:
                self.assertEqual(sleeping, 0)
                self.assertNotIn(ts[0].state, ("nest", "lay"))


class TestWorld(unittest.TestCase):
    def test_run_with_mouse_through_a_night(self):
        random.seed(2)
        w = up.World()
        base = at(6, 21, 5, 0)
        w.clock = lambda: base + w.time          # 朝5時から(交尾は朝、産卵は夜)
        w.update_daylight(w.clock(), log=False)
        w.seed()
        for t in w.turtles:
            t.mate_cd = 0
        for i in range(int(0.75 * 3600 / 0.5)):      # 実時間45分 = カメの18時間(夕方→翌朝)
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
            w.step(0.5)
            self.assertLessEqual(w.population(), up.MAX_TURTLES + 3)
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
            if not big.alive or any("narrowly escaped" in e[2] for e in w.events):
                break
        escaped = any("narrowly escaped" in e[2] for e in w.events)
        self.assertTrue((not big.alive and big.cause == "being eaten" and any(k in big.killer for k in up.SHARK_KINDS))
                        or escaped)
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
        w.clock = lambda: at(6, 21, 8, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_plants()
        for i in range(38):
            x, y = w.water_point()
            t = up.Turtle(up.random_genome(), x, y, sex="FM"[i % 2], lineage="A")
            t.age = up.ADULT_AGE
            t.energy, t.fatigue = 0.3, 0.0
            w.turtles.append(t)
        b0 = sum(p.b for p in w.plants)
        low = b0
        for _ in range(int(0.5 * 3600 / 0.5)):        # 実時間30分 = カメの12時間
            w.step(0.5)
            low = min(low, sum(p.b for p in w.plants))
        self.assertLess(low, b0 * 0.6)                 # 食べ尽くされて減る
        self.assertGreater(w.deaths, 5)                # 餓死が起きる

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


class TestNewFeatures(unittest.TestCase):
    def make(self, hour=12):
        w = up.World()
        w.clock = lambda: at(6, 21, hour, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        return w

    def test_pastel_and_rare_dark(self):
        random.seed(10)
        gs = [up.random_genome() for _ in range(2000)]
        dark = sum(up.is_dark(g) for g in gs)
        self.assertLess(dark, 150)                       # 濃い色はまれ
        self.assertGreater(dark, 10)
        styles = {up.style_of(g) for g in gs}
        self.assertEqual(styles, set(range(8)))          # 模様 8 種類
        g = gs[0]
        for frame in (0, 1):
            for mode in ("normal", "belly", "dead", "breathe"):
                px = up.turtle_pixels(g, frame, mode)
                self.assertTrue(px)
        self.assertEqual(len(up.turtle_pixels(g, 0, "breathe")), 13)

    def test_big_wave_flips_and_surf(self):
        random.seed(11)
        w = self.make()
        ts = []
        for i in range(12):
            g = up.random_genome()
            g.update(activity=0.9, whim=0.9) if i % 2 else g.update(activity=0.1, whim=0.1, size=0.1)
            t = up.Turtle(g, 50 + i * 50, w.land_top * 0.6, age=up.ADULT_AGE)
            t.energy, t.joy, t.air, t.fatigue = 1.0, 0.8, 999, 0
            ts.append(t)
        w.turtles = ts
        w.big_t = 0
        seen = set()
        for _ in range(1500):
            if w.big_wave is None:
                w.big_t = 0                       # 大波を続けて起こす
            w.step(0.1)
            for t in ts:
                seen.add(t.state)
                t.air, t.joy, t.energy = 999, 0.8, 1.0
        self.assertIn("surf", seen)
        self.assertIn("flipped", seen)

    def test_cleaning_station(self):
        random.seed(12)
        w = self.make(12)
        t = up.Turtle(up.random_genome(), 300, 150, age=up.ADULT_AGE)
        t.energy, t.air, t.fatigue, t.clean_cd = 0.95, 999, 0, 0
        t.g["appetite"] = 0.0
        w.turtles = [t]
        t.goal, t.state = w.schools[0], "to_clean"
        cleaned = False
        for _ in range(3000):
            w.step(0.1)
            t.air = 999
            if t.state == "cleaning":
                cleaned = True
                break
        self.assertTrue(cleaned)
        for _ in range(20):
            w.step(0.1)
        s = w.schools[0]
        near = sum(math.hypot(f.x - t.x, f.y - t.y) < 30 for f in w.fish if f.school is s)
        self.assertGreaterEqual(near, 4)                  # 魚がカメに集まっている

    def test_dolphin_play_and_friends(self):
        random.seed(13)
        w = self.make(12)
        ts = []
        for i in range(6):
            g = up.random_genome()
            g.update(flock=0.9, care=0.9)
            t = up.Turtle(g, 200 + i * 15, 150, age=up.ADULT_AGE)
            t.energy, t.air, t.fatigue, t.mate_cd = 1.0, 999, 0, 99999
            ts.append(t)
        w.turtles = ts
        w._spawn_visitor("dolphin")
        v = w.visitors[0]
        v.x, v.y, v.y0 = 230, 150, 150
        played = False
        for _ in range(300):
            w.step(0.1)
            played = played or any(t.state == "play" for t in ts)
        self.assertTrue(played)
        w.visitors, w.big_t, w.shark_t = [], 1e9, 1e9
        w.vis_t = {k: 1e9 for k in w.vis_t}
        for _ in range(6000):                             # 一緒にいると友達になる
            for i, t in enumerate(ts):
                t.air, t.energy, t.fatigue, t.clean_cd = 999, 1.0, 0.0, 1e9
                t.x, t.y = 300 + i * 12, 150                    # 近くで過ごさせる
            w.step(0.1)
        self.assertTrue(any(w.friends(t) for t in ts))
        for kind in ("manta", "hermit", "coconut"):
            w._spawn_visitor(kind)
        for _ in range(50):
            w.step(0.1)

    def test_eggs_hatch_only_at_night(self):
        random.seed(14)
        w = self.make(12)
        w.eggs = [up.Egg(up.random_genome(), 100, w.h - 20, 2, "A", "x", t=0.0)]
        for _ in range(20):
            w.step(0.1)
        self.assertEqual(len(w.eggs), 1)
        w.clock = lambda: at(6, 21, 23, 0)
        for _ in range(40):                         # ゆれてから割れる(3秒)
            w.step(0.1)
        self.assertEqual(len(w.eggs), 0)
        self.assertEqual(w.births, 1)

    def test_generations_per_day(self):
        """世代交代: カメの1〜3日に1世代くらい。"""
        random.seed(15)
        w = up.World()
        base = at(6, 21, 12, 0)
        w.clock = lambda: base
        w.update_daylight(base, log=False)
        w.seed()
        g0 = w.max_gen
        w.advance_offline(3 * 3600, start=base - 3 * 3600)   # 実時間3時間 = カメの3日
        per_day = (w.max_gen - g0) / 3.0
        self.assertGreaterEqual(per_day, 0.25)
        self.assertLessEqual(per_day, 2.0)


class TestSeaweedAndVisitors(unittest.TestCase):
    def make(self, hour=12):
        w = up.World()
        w.clock = lambda: at(6, 21, hour, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        return w

    def test_meadows_grow_get_eaten_and_move(self):
        random.seed(20)
        w = self.make()
        mid, m = next((k, v) for k, v in w.meadows.items() if v["n"] >= 3)
        x0, y0 = m["x"], m["y"]
        for p in w.plants:                     # 根元まで何度も食べられた株は枯れる
            if p.m == mid:
                p.scars = up.PLANT_SCARS
        w._grow_plants(1.0)
        w._update_meadows()
        self.assertNotIn(mid, w.meadows)
        w2 = self.make()
        for p in w2.plants:
            p.b = 1.0
        start = {k: (v["x"], v["y"]) for k, v in w2.meadows.items()}
        n0 = len(w2.plants)
        for _ in range(int(6 * 3600 / 10)):     # 6時間: 広がり、寿命で枯れ、少しずつ動く
            w2._grow_plants(10.0)
        self.assertGreater(len(w2.plants), n0)
        moved = [math.hypot(v["x"] - start[k][0], v["y"] - start[k][1]) for k, v in w2.meadows.items() if k in start]
        self.assertTrue(moved and max(moved) > 5)

    def test_lone_sprout(self):
        random.seed(21)
        w = self.make()
        w.plants = []
        w.meadows = {}
        w.sprout_t = 0
        w._grow_plants(0.1)
        self.assertEqual(len(w.plants), 1)
        info = w.hover_info(w.plants[0].x, w.plants[0].y)
        self.assertIn("Lone seaweed", info[0])

    def test_playful_turtles_catch_big_wave(self):
        random.seed(22)
        w = self.make()
        g = up.random_genome()
        g.update(whim=0.9, activity=0.9)
        t = up.Turtle(g, 300, w.land_top * 0.7, age=up.ADULT_AGE)
        t.energy, t.air, t.fatigue = 1.0, 999, 0
        w.turtles = [t]
        w.big_t = 0
        seen = set()
        for _ in range(600):
            w.step(0.1)
            t.air = 999
            seen.add(t.state)
            if w.big_wave is None and "surf" in seen:
                break
        self.assertIn("catch", seen)
        self.assertIn("surf", seen)

    def test_visitor_frequency_order(self):
        gap = lambda k: sum(up.VISITORS[k]["gap"]) / 2
        self.assertGreater(sum(up.SHARK_GAP) / 2, gap("dolphin"))
        self.assertGreater(gap("dolphin"), gap("manta"))
        self.assertGreater(gap("manta"), gap("coconut"))
        self.assertGreaterEqual(gap("coconut"), gap("hermit"))
        self.assertAlmostEqual(sum(up.SHARK_GAP) / 2, 30 * 60, delta=60)
        self.assertAlmostEqual(gap("manta"), 15 * 60, delta=60)
        self.assertAlmostEqual(gap("hermit"), 60, delta=10)


class TestAnimations(unittest.TestCase):
    def test_plant_disappears_when_eaten(self):
        """クラゲと同じく、水草も食べたら消える(もぐもぐしてから)。"""
        random.seed(30)
        w = up.World()
        w.clock = lambda: at(6, 21, 8, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        p = w.plants[0]
        p.b = 1.0
        t = up.Turtle(up.random_genome(), p.x - 30, p.y, age=up.ADULT_AGE)
        t.g["diet"] = 0.1
        t.energy, t.air, t.fatigue = 0.2, 999, 0
        w.turtles, w.plants = [t], [p]
        chew, fx = set(), set()
        for _ in range(300):
            w.step(0.1)
            t.air = 999
            fx.update(f[0] for f in w.fx)
            if t.eat_cd > 0:
                chew.add(int(t.anim / 0.14) % 2)
            w.fx.clear()
            if p not in w.plants and t.eat_cd <= 0:
                break
        self.assertNotIn(p, w.plants)
        self.assertGreater(t.energy, 0.9)
        self.assertEqual(chew, {0, 1})                 # 口を開け閉め
        self.assertIn("leaf", fx)
        self.assertNotIn("gulp", fx)                   # 緑の輪は出さない
        self.assertEqual(len(up.turtle_pixels(t.g, 1, "eat")), 12)

    def test_cleaning_fish_peck(self):
        random.seed(31)
        w = up.World()
        w.clock = lambda: at(6, 21, 12, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        s = w.schools[0]
        t = up.Turtle(up.random_genome(), s.home.x, s.home.y, age=up.ADULT_AGE)
        t.state, t.state_t, t.energy, t.air = "cleaning", 99, 0.9, 999
        s.cleaning = t
        w.turtles = [t]
        pecks = 0
        for _ in range(100):
            w.step(0.1)
            pecks += sum(1 for f in w.fx if f[0] == "peck")
            w.fx.clear()
        self.assertGreater(pecks, 5)
        near = [math.hypot(f.x - t.x, f.y - t.y) for f in w.fish if f.school is s]
        self.assertLess(max(near), t.radius + 10)             # 魚がカメの体の上にいる

    def test_surfers_mostly_wipe_out(self):
        random.seed(32)
        w = up.World()
        w.clock = lambda: at(6, 21, 12, 0)
        w.update_daylight(w.clock(), log=False)
        ts = []
        for i in range(12):
            g = up.random_genome()
            g.update(whim=0.95, activity=0.95)
            t = up.Turtle(g, 40 + i * 52, w.land_top * 0.75, age=up.ADULT_AGE)
            t.energy, t.air, t.fatigue, t.joy = 1.0, 999, 0, 0.8
            ts.append(t)
        w.turtles = ts
        w.waves = []
        w.big_t = 0
        seen = set()
        for _ in range(800):
            w.step(0.1)
            for t in ts:
                t.air = 999
                seen.add(t.state)
            if w.big_wave is None and seen & {"surf"}:
                break
        msg = [e[2] for e in w.events if "shore" in e[2]]
        self.assertIn("wipeout", seen)
        self.assertTrue(msg and "wiped out" in msg[-1])


class TestLifeAndNight(unittest.TestCase):
    def make(self, hour=12):
        w = up.World()
        w.clock = lambda: at(6, 21, hour, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        return w

    def test_lifespans(self):
        """寿命: 平均 4〜5 日、運のよい個体(約1/10)は最大 1 か月ほど(どれもカメの時間)。"""
        random.seed(40)
        ts = [up.Turtle(up.random_genome(), 0, 0) for _ in range(2000)]
        lucky = [t for t in ts if t.lucky]
        self.assertTrue(150 < len(lucky) < 260)
        self.assertTrue(all(15 <= t.lifespan / up.DAY <= 30 for t in lucky))
        normal = [t.lifespan / up.DAY for t in ts if not t.lucky]
        self.assertTrue(4.0 <= sum(normal) / len(normal) <= 5.0)
        self.assertTrue(all(2 <= d <= 8 for d in normal))

    def test_named_turtle_life_story(self):
        random.seed(41)
        w = self.make()
        mom = up.Turtle(up.random_genome(), 200, 150, age=up.ADULT_AGE, sex="F", lineage="A")
        dad = up.Turtle(up.random_genome(), 210, 150, age=up.ADULT_AGE, sex="M", lineage="B")
        mom.name = "Hana"
        w.turtles = [mom, dad]
        w.by_id = {mom.id: mom, dad.id: dad}
        kid = up.Turtle(up.random_genome(), 220, 150)
        w.turtles.append(kid)
        w._born(kid, mom.id, dad.id)
        grand = up.Turtle(up.random_genome(), 230, 150)
        w.turtles.append(grand)
        w._born(grand, kid.id, None)
        mom.stats["plants"] = 12
        self.assertTrue(any("Life so far" in l for l in w.turtle_info(mom)))
        self.assertEqual({t.id for t in w.descendants_alive(mom.id)}, {kid.id, grand.id})
        w._kill(mom, "being eaten", killer="Tiger shark #3")
        self.assertEqual(len(w.memorials), 1)
        text = "\n".join(w.memorials[0]["lines"])
        self.assertIn("Hana", text)
        self.assertIn("Tiger shark #3", text)
        self.assertIn("Children: 1", text)
        self.assertIn("Descendants alive now: 2", text)
        self.assertIn("12 seaweed", text)
        self.assertEqual(set(w.memorials[0]["heirs"]), {kid.id, grand.id})

    def test_causes_of_death(self):
        random.seed(42)
        w = self.make(23)
        t = up.Turtle(up.random_genome(), 100, 100, age=up.ADULT_AGE)
        t.sick, t.energy = 1.0, 0.1
        w.turtles = [t]
        for _ in range(200):
            if w._illness(t, 3600):
                break
            t.sick = 1.0
        self.assertEqual(t.cause, "illness")
        # スナガニが浜の子ガメを食べる(食べた相手が記録される)
        w2 = self.make(23)
        x = 300
        baby = up.Turtle(up.random_genome(), x, w2.shore(x) + 20, age=0)
        w2.turtles = [baby]
        v = up.Visitor("ghost", x, baby.y, 0.0)
        w2.visitors = [v]
        for _ in range(300):
            v.x, v.y, v.pause = baby.x, baby.y, 1.0
            w2._move_ghost(v, 0.1)
            if not baby.alive:
                break
        self.assertFalse(baby.alive)
        self.assertTrue(baby.killer.startswith("Ghost crab #"))

    def test_immigrant_balances_sex(self):
        random.seed(43)
        w = self.make()
        w.turtles = [up.Turtle(up.random_genome(), 100 + i * 30, 120, age=up.ADULT_AGE, sex="M") for i in range(4)]
        w._immigrants(0.1, force=True)
        newcomer = w.turtles[-1]
        self.assertEqual(newcomer.sex, "F")
        self.assertEqual(newcomer.parents, "arrived from far away")
        self.assertTrue(any("from far away" in e[2] for e in w.events))

    def test_night_creatures(self):
        random.seed(44)
        w = self.make(23)
        w.vis_t = {k: 0.0 for k in w.vis_t}
        for _ in range(20):
            w.step(0.1)
            w.vis_t = {k: 0.0 for k in w.vis_t}
        kinds = {v.kind for v in w.visitors}
        self.assertTrue({"ghost", "octopus", "comb", "coconut", "hermit"} <= kinds)
        self.assertGreaterEqual(sum(v.kind == "hermit" for v in w.visitors), 2)   # 夜はヤドカリがたくさん
        self.assertNotIn("dolphin", kinds)
        for kind in ("ghost", "octopus", "comb"):
            v = next(v for v in w.visitors if v.kind == kind)
            self.assertTrue(w.hover_info(v.x, v.y))

    def test_red_sunset_and_moonlight(self):
        sr = up.daylight(clock_at(6, 21, 4, 40))
        ss = up.daylight(clock_at(6, 21, 18, 50))
        self.assertEqual(sr[0], "Sunrise")
        self.assertEqual(ss[0], "Sunset")
        self.assertGreater(ss[2][0], 1.2)                          # 赤が強い
        self.assertLess(ss[2][2], 0.45)
        w = up.World()
        w.phase = "Night"
        self.assertGreater(up.sparkle_amount(w), 0.8)              # 月光できらめく


class TestV6(unittest.TestCase):
    def make(self, hour=12):
        w = up.World()
        w.clock = lambda: at(6, 21, hour, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        w.vis_t = {k: 1e9 for k in w.vis_t}
        w.shark_t = w.big_t = w.immigrant_t = 1e9
        return w

    def test_mating_animation_then_eggs(self):
        random.seed(50)
        w = self.make(10)
        f = up.Turtle(up.random_genome(), 200, 150, age=up.ADULT_AGE, sex="F")
        m = up.Turtle(up.random_genome(), 205, 150, age=up.ADULT_AGE, sex="M")
        for t in (f, m):
            t.energy, t.mate_cd, t.air, t.fatigue = 1.0, 0, 999, 0
        w.turtles = [f, m]
        w._start_mating(f, m)
        self.assertEqual((f.state, m.state), ("mating", "mating"))
        self.assertIn("heart", w.sfx)                       # ハート1つのあっさりした交尾
        hearts = 0
        for _ in range(50):
            w.step(0.1)
            hearts += sum(1 for x in w.fx if x[0] == "hearts")
            w.fx.clear()
        self.assertTrue(f.clutch)
        self.assertEqual(hearts, 0)                         # ハートがあふれる演出はやめた

    def test_laying_tears_and_hatching_shake_and_bird(self):
        random.seed(51)
        w = self.make(23)
        mom = up.Turtle(up.random_genome(), 300, w.shore(300) + 20, age=up.ADULT_AGE, sex="F")
        mom.clutch = [{"g": up.random_genome(), "gen": 2, "par": "x", "dad": None} for _ in range(4)]
        mom.state, mom.state_t, mom.air = "lay", up.LAY_TIME, 999
        w.turtles = [mom]
        kinds = set()
        for _ in range(int(up.LAY_TIME / 0.1) + 5):
            w.step(0.1)
            kinds.update(x[0] for x in w.fx)
            w.fx.clear()
        self.assertIn("tear", kinds)
        self.assertIn("dust", kinds)
        self.assertEqual(len(w.eggs), 4)
        self.assertTrue(any("shed tears" in e[2] for e in w.events))
        for e in w.eggs:
            e.t = 0
        random.seed(3)
        shook = False
        for _ in range(60):
            w.step(0.1)
            shook = shook or any(getattr(e, "shake", None) for e in w.eggs)
        self.assertTrue(shook)
        self.assertEqual(len(w.eggs), 0)
        w._spawn_bird(hunting=True)
        bird = next(v for v in w.visitors if v.kind == "bird")
        babies = [t for t in w.turtles if not t.adult]
        for _ in range(300):
            for b in babies:
                if b.alive:
                    b.y = w.shore(b.x) + 20                    # 浜にとどめる
            w._move_bird(bird, 0.1)
            if bird.tries >= 3 or bird.gone:
                break
        self.assertGreater(bird.tries, 0)

    def test_quirks_and_weak(self):
        random.seed(52)
        w = self.make(10)
        g = up.random_genome()
        g.update(clumsy=1.0, watch=1.0, whim=0.9)
        t = up.Turtle(g, 300, 150, age=up.ADULT_AGE)
        t.energy, t.air, t.fatigue = 1.0, 999, 0
        w.turtles = [t]
        w.visitors = [up.Visitor("octopus", 320, 160, 1)]
        seen = set()
        for _ in range(4000):
            t.state = "swim" if t.state in ("swim", "food") else t.state
            w._quirks(t, 0.5, True)
            seen.add(t.state)
            t.state_t = 0
            t.state = "swim"
        self.assertTrue({"flipped", "watch", "idle"} <= seen)
        t.energy = 0.1
        self.assertTrue(w.weak(t))
        self.assertTrue(up.turtle_pixels(g, 0, "weak"))

    def test_origin_and_jokes(self):
        random.seed(53)
        w = self.make(10)
        w.turtles = [up.Turtle(up.random_genome(), 100, 100, age=up.ADULT_AGE, sex="M")]
        w._immigrants(0.1, force=True)
        newc = [t for t in w.turtles if t.origin != "native"]
        self.assertTrue(newc)
        info = "\n".join(w.turtle_info(newc[0]))
        self.assertIn("Newcomer: Wanderers I", info)
        kid = up.Turtle(up.random_genome(), 120, 100)
        w.by_id = {t.id: t for t in w.turtles}
        w._born(kid, newc[0].id if newc[0].sex == "F" else None, None)
        native = w.turtles[0]
        self.assertIn("Native", "\n".join(w.turtle_info(native)))
        g = dict(native.g, clumsy=0.9, surf=0.9)
        native.g = g
        info = "\n".join(w.turtle_info(native))
        self.assertTrue(any(j in info for j in up.TRAIT_JOKES.values()))   # ユーモラスな説明

    def test_coral_moves_and_trends(self):
        random.seed(54)
        w = self.make(10)
        coral = next(r for r in w.reefs if r.kind == "coral")
        x0, y0 = coral.x, coral.y
        for _ in range(200):
            w._coral_step(up.HOUR)
        self.assertGreater(math.hypot(coral.x - x0, coral.y - y0), 3)
        self.assertEqual(sum(r.kind == "rock" for r in w.reefs), 4)
        w.turtles = [up.Turtle(up.random_genome(), 100 + i, 100, age=up.ADULT_AGE) for i in range(5)]
        w.trend_t = -1e9
        w._trends()
        w.bio_time += up.DAY
        w.turtles += [up.Turtle(up.random_genome(), 200 + i, 100, age=up.ADULT_AGE) for i in range(10)]
        w.trend_t = -1e9
        w._trends()
        self.assertTrue(any("growing" in e[2] for e in w.events))

    def test_save_dir_config(self):
        with tempfile.TemporaryDirectory() as d:
            old = up.CONFIG_PATH
            up.CONFIG_PATH = os.path.join(d, "cfg.json")
            env = os.environ.pop("UMIGAME_SAVE_DIR", None)
            try:
                with open(up.CONFIG_PATH, "w") as f:
                    import json
                    json.dump({"save_dir": os.path.join(d, "UmigamePet")}, f)
                self.assertEqual(up.choose_save_dir(None)[0], os.path.join(d, "UmigamePet"))
            finally:
                up.CONFIG_PATH = old
                if env:
                    os.environ["UMIGAME_SAVE_DIR"] = env


class FakeBackend:
    def __init__(self):
        self.played, self.wave_state = [], None

    def play(self, name, level):
        self.played.append(name)
        self.level = level

    def waves(self, on, level):
        self.wave_state = on
        self.wave_level = level

    def tick(self):
        pass

    def close(self):
        pass


class TestSound(unittest.TestCase):
    def test_sound_files(self):
        import wave
        with tempfile.TemporaryDirectory() as d:
            paths = up.build_sound_files(d)
            for name, p in paths.items():
                with wave.open(p) as f:
                    self.assertEqual(f.getframerate(), up.SR)
                    self.assertGreater(f.getnframes(), 0)
        for name, smp in up.make_sounds().items():
            self.assertLessEqual(max(abs(v) for v in smp), 1.0, name)    # 音割れしない
        loop = up.make_wave_loop()
        self.assertLess(abs(loop[-1] - loop[0]), 0.05)                    # つなぎ目がなめらか
        self.assertAlmostEqual(len(loop) / up.SR, up.WAVE_LOOP_SEC, delta=0.01)

    def test_toggles_and_rate_limit(self):
        fb = FakeBackend()
        snd = up.SoundSystem(True, True, backend=fb)
        self.assertTrue(fb.wave_state)
        snd.play("note")
        snd.play("note")                              # すぐ同じ音は鳴らさない
        self.assertEqual(fb.played, ["note"])
        for n in ("flip", "hatch", "lay", "death", "shark"):
            snd.play(n)
        self.assertLessEqual(len(fb.played), 4)       # 1秒に4つまで
        snd.set_fx(False)
        fb.played.clear()
        time.sleep(1.05)
        snd.play("splash")
        self.assertEqual(fb.played, [])
        snd.set_waves(False)
        self.assertFalse(fb.wave_state)
        snd.set_waves(True, 3)
        self.assertEqual(fb.wave_level, 3)
        snd.set_fx(True, 4)
        snd.last.clear()
        snd.recent.clear()
        snd.play("splash")
        self.assertEqual(fb.level, 4)
        snd.set_fx(True, 0)                          # 音量 0 なら鳴らさない
        fb.played.clear()
        snd.last.clear()
        snd.play("note")
        self.assertEqual(fb.played, [])

    def test_scaled_wav(self):
        import array
        import wave
        with tempfile.TemporaryDirectory() as d:
            p = up.build_sound_files(d)["splash"]
            q = up.scaled_wav(p, 5)
            self.assertNotEqual(p, q)
            self.assertEqual(up.scaled_wav(p, 10), p)

            def peak(path):
                with wave.open(path) as f:
                    return max(abs(v) for v in array.array("h", f.readframes(f.getnframes())))
            self.assertLess(peak(q), peak(p) * 0.5)
            self.assertEqual(peak(up.scaled_wav(p, 0)), 0)

    def test_event_mapping_and_world_sfx(self):
        self.assertEqual(up.event_sound("shark", "A shark appeared offshore! Big turtles, watch out"), "shark")
        self.assertIsNone(up.event_sound("shark", "The shark swam away"))
        self.assertEqual(up.event_sound("wave", "A big wave is coming!"), "bigwave")
        self.assertEqual(up.event_sound("visitor", "A dolphin came to visit!"), "dolphin")
        self.assertEqual(up.event_sound("lay", "x"), "lay")
        w = up.World()
        t = up.Turtle(up.random_genome(), 100, 100, age=up.ADULT_AGE)
        w.turtles = [t]
        w.poke(t)
        self.assertIn("flip", w.sfx)
        n = w.n_events
        w.event("mate", "x")
        self.assertEqual(w.n_events, n + 1)

    def test_settings_saved(self):
        w = up.World()
        w.seed()
        w.settings["waves"] = False
        w.settings["fx_vol"] = 3
        with tempfile.TemporaryDirectory() as d:
            up.save_world(w, d)
            w2, _ = up.load_world(d)
        self.assertFalse(w2.settings["waves"])
        self.assertTrue(w2.settings["fx"])
        self.assertEqual(w2.settings["fx_vol"], 3)
        self.assertEqual(w2.settings["waves_vol"], 6)


class TestV7(unittest.TestCase):
    def make(self, hour=12):
        w = up.World()
        w.clock = lambda: at(6, 21, hour, 0)
        w.update_daylight(w.clock(), log=False)
        w.seed_reefs()
        w.seed_plants()
        return w

    def test_forty_minutes_a_day(self):
        self.assertAlmostEqual(up.TIME_SCALE * 40 * 60, up.DAY)
        self.assertAlmostEqual(up.LAY_TIME * up.TIME_SCALE, 1.5 * up.HOUR)   # 産卵は約1時間半

    def test_no_complementary_colours(self):
        """模様の色相は地の色に近い(補色にならない)。まれな色は真珠色か金色。"""
        import colorsys
        random.seed(70)
        for _ in range(500):
            g = up.random_genome()
            cols = up.shell_colors(g)
            hs = []
            for c in cols[:3]:
                r, gg, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
                h, l, sat = colorsys.rgb_to_hls(r, gg, b)
                hs.append((h, sat))
            if not up.is_dark(g) and hs[0][1] > 0.1 and hs[2][1] > 0.1:
                d = abs(hs[0][0] - hs[2][0])
                self.assertLess(min(d, 1 - d), 0.12)
            if up.is_dark(g):
                self.assertIn(up.color_name(g), ("pearl white", "golden"))

    def test_rocks_and_corals_at_start(self):
        random.seed(71)
        w = self.make()
        rocks = sorted(len(r.parts) for r in w.reefs if r.kind == "rock")
        self.assertEqual(rocks, [3, 3, 5, 8])                     # 大・中・小と、沖合の小
        self.assertTrue(any(r.y < w.land_top * 0.25 for r in w.reefs if r.kind == "rock"))
        corals = [r for r in w.reefs if r.kind == "coral"]
        self.assertEqual(len(corals), 4)
        n_parts = sum(len(r.parts) for r in corals)
        self.assertAlmostEqual(len(w.fish), sum(w.fish_target(r) for r in corals))
        self.assertGreater(len(w.fish), n_parts * 0.5)

    def test_corals_and_fish_change(self):
        random.seed(72)
        w = self.make()
        counts = set()
        for _ in range(24 * 40):
            w._coral_step(up.HOUR)
            corals = [r for r in w.reefs if r.kind == "coral"]
            counts.add(len(corals))
            self.assertLessEqual(len(w.fish), sum(w.fish_target(r) for r in corals) + len(w.schools) + 2)
        self.assertGreater(len(counts), 1)                         # サンゴ礁の数が変わる

    def test_jellies_breed_and_can_die_out(self):
        random.seed(73)
        w = self.make()
        w.jellies = [up.Jelly(300, 150, 3) for _ in range(3)]
        for _ in range(5000):
            w._jellies(0.5, 0.5 * up.TIME_SCALE)
        self.assertGreater(len(w.jellies), 6)                      # ふえる
        self.assertLessEqual(len(w.jellies), up.JELLY_K + 2)
        for j in w.jellies:
            self.assertTrue(0 <= j.x <= w.w)                       # 海から出ていかない
        w.jellies = []
        w._jellies(0.5)
        self.assertEqual(w.jellies, [])                            # 外からは来ない(人が足す)

    def test_immigrants_young_gen1_and_rate(self):
        random.seed(74)
        w = self.make()
        w.max_gen = 7
        w.turtles = []
        w._immigrants(1.0, force=True)
        t = w.turtles[0]
        self.assertEqual(t.generation, 1)
        self.assertTrue(up.ADULT_AGE * 0.69 <= t.age <= up.ADULT_AGE * 1.16)
        arrivals = []                                                # 絶滅したら 1 日ほどで 1 匹
        for _ in range(200):
            w.turtles, n, days = [], 0, 0.0
            while not w.turtles:
                w._immigrants(600.0)
                days += 600.0 / up.DAY
            arrivals.append(days)
        self.assertTrue(0.6 < sum(arrivals) / len(arrivals) < 1.5)

    def test_crisis_kills_and_fatal(self):
        random.seed(75)
        w = self.make()
        w.turtles = [up.Turtle(up.random_genome(), 100 + i * 20, 120, age=up.ADULT_AGE) for i in range(10)]
        w.start_crisis("epidemic")
        n = len(w.alive())
        self.assertTrue(0 < n < 10)
        w.start_crisis("storm", fatal=True)
        self.assertEqual(len(w.alive()), 0)
        self.assertEqual(w.eggs, [])
        self.assertTrue(any("CRISIS" in e[2] for e in w.events))
        hits = 0                                                     # 平均 21 日に 1 度くらい
        w.crisis_t = 0
        w.start_crisis = lambda kind, fatal=False: None
        w.turtles = [up.Turtle(up.random_genome(), 100, 120, age=up.ADULT_AGE)]
        for _ in range(420):
            w.crisis_t_before = w.crisis_t
            w._crisis(up.DAY)
            hits += w.crisis_t > w.crisis_t_before
        self.assertTrue(10 <= hits <= 32)

    def test_lay_only_at_night_window(self):
        random.seed(76)
        for hour, expect in ((21, True), (1, True), (5, False), (18, False)):
            w = self.make(hour)
            w.update_daylight(up.turtle_clock(w.clock()), log=False)
            self.assertEqual(w.nest_time(), expect)

    def test_hungry_turtle_eats_small_plants_and_wakes(self):
        random.seed(77)
        w = self.make(1)
        t = up.Turtle(up.random_genome(), 300, 150, age=up.ADULT_AGE)
        w.turtles = [t]
        w.plants = [up.Plant(320, 160, 0.5, w.new_meadow(320, 160))]
        t.energy = 0.9
        self.assertIsNone(w._choose_food(t))
        t.energy = 0.3
        self.assertIsNotNone(w._choose_food(t))
        t.energy, t.state, t.fatigue = 0.15, "sleep", 1.0
        w._update_turtle(t, 0.1)
        self.assertNotEqual(t.state, "sleep")

    def test_memorial_heirs_are_three_closest(self):
        random.seed(78)
        w = self.make()
        mom = up.Turtle(up.random_genome(), 100, 100, age=up.ADULT_AGE, sex="F")
        mom.name, mom.killer, mom.cause = "Momo", None, "old age"
        w.turtles = [mom]
        w.by_id = {mom.id: mom}
        kids = []
        for i in range(6):
            k = up.Turtle(up.mutate(mom.g, rate=0.1 * (i + 1)), 120 + i, 100)
            w._born(k, mom.id, None)
            w.turtles.append(k)
            kids.append(k)
        story = w.life_story(mom)
        self.assertEqual(len(story["heirs"]), 3)
        best = sorted(kids, key=lambda k: up.distance(k.g, mom.g))[:3]
        self.assertEqual(story["heirs"], [k.id for k in best])

    def test_emigration_when_seaweed_is_scarce(self):
        random.seed(79)
        w = self.make()
        w.turtles = [up.Turtle(up.random_genome(), 100 + i * 20, 120, age=up.ADULT_AGE) for i in range(14)]
        w.plants = w.plants[:3]
        for _ in range(200):
            w._emigrate(up.HOUR)
        gone = [t for t in w.turtles if t.state == "depart"]
        self.assertTrue(gone)
        self.assertTrue(any("never to return" in e[2] for e in w.events))
        t = gone[0]
        for _ in range(400):
            w._update_turtle(t, 0.1)
        self.assertNotIn(t, w.turtles)                            # 二度と戻らない
        self.assertNotIn(t.id, [x["id"] for x in w.to_dict()["turtles"]])
        w2 = self.make()                                          # 海藻が十分なら旅立たない
        w2.turtles = [up.Turtle(up.random_genome(), 100 + i * 20, 120, age=up.ADULT_AGE) for i in range(8)]
        for _ in range(200):
            w2._emigrate(up.HOUR)
        self.assertFalse(any(t.state == "depart" for t in w2.turtles))

    def test_mating_is_rare_and_stored_clutches(self):
        """交尾はまれ(メスは約1日、オスは約0.8日あける)。1回の交尾のあと、交尾なしでもう1〜2回産む。"""
        random.seed(80)
        w = self.make()
        f = up.Turtle(up.random_genome(), 300, 150, age=up.ADULT_AGE, sex="F")
        m = up.Turtle(up.random_genome(), 310, 150, age=up.ADULT_AGE, sex="M")
        f.energy = m.energy = 1.0
        f.mate_cd = m.mate_cd = 0
        w.turtles = [f, m]
        w._pop = 2
        w._mate(f, m)
        self.assertGreater(f.mate_cd, 0.79 * up.DAY)
        self.assertGreater(m.mate_cd, 0.63 * up.DAY)
        self.assertTrue(f.clutch)
        f.clutch = None                                          # 産んだことにする
        f.energy = 1.0
        w._stored_clutch(f, up.CLUTCH_GAP * 1.3)
        self.assertTrue(f.clutch)                                # 交尾なしで次の卵
        self.assertEqual(f.clutch[0]["dad"], m.id)

    def test_new_sounds(self):
        s = up.make_sounds()
        for k in ("attack", "manta", "crash", "shark", "dolphin", "bigwave"):
            self.assertTrue(s[k])
        self.assertGreater(len(s["bigwave"]), up.SR * 3.5)       # 大波は長く大きく
        self.assertEqual(up.event_sound("shark", "The Tiger shark is attacking #3 (A)!"), "attack")
        self.assertEqual(up.event_sound("visitor", "A manta ray is gliding by"), "manta")
        self.assertEqual(up.event_sound("wave", "The big wave flipped 2 turtles over!"), "crash")

    def test_mating_quota_and_hobbies(self):
        """交尾は朝だけ、1日に 1〜2 ペアまで。趣味の遺伝子で昼寝・ただよう。"""
        random.seed(81)
        w = self.make()
        w.update_daylight(up.turtle_clock(at(6, 21, 7, 0)), log=False)
        t = up.Turtle(up.random_genome(), 300, 150, age=up.ADULT_AGE, sex="F")
        t.energy, t.mate_cd = 1.0, 0
        w.turtles, w._pop = [t], 1
        self.assertTrue(w._can_mate(t))
        w.mates_today = 2
        self.assertFalse(w._can_mate(t))
        w.update_daylight(up.turtle_clock(at(6, 21, 13, 0)), log=False)
        w.mates_today = 0
        self.assertFalse(w._can_mate(t))                          # 昼は交尾しない
        gs = [up.random_genome() for _ in range(400)]
        for k in up.HOBBIES:
            self.assertGreater(sum(g[k] > 0.8 for g in gs), 40)   # 趣味のはっきりした個体がいる
        self.assertLess(sum(g["flirt"] > 0.7 for g in gs), 80)
        for hobby, state in (("nap", "nap"), ("drift", "drift")):
            g = dict(up.random_genome(), nap=0.0, drift=0.0, watch=0.0, clumsy=0.0, flirt=0.0, flock=0.0)
            g[hobby] = 1.0
            x = up.Turtle(g, 300, 150, age=up.ADULT_AGE)
            x.energy = 0.9
            seen = False
            for _ in range(3000):
                x.state = "swim"
                w._quirks(x, 0.5, True)
                if x.state == state:
                    seen = True
                    break
            self.assertTrue(seen, hobby)
        self.assertIn("Napper", up.traits(dict(up.random_genome(), nap=0.9)))


if __name__ == "__main__":
    unittest.main()
