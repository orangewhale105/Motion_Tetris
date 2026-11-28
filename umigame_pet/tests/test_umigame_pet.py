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
        """実時間の1時間 = カメの1日。毎時0分が0:00、30分が正午。"""
        base = clock_at(6, 21, 10, 0)
        self.assertEqual(time.localtime(up.turtle_clock(base)).tm_hour, 0)
        self.assertEqual(time.localtime(up.turtle_clock(base + 30 * 60)).tm_hour, 12)
        self.assertEqual(time.localtime(up.turtle_clock(base + 45 * 60)).tm_hour, 18)
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
        base = at(6, 21, 17, 0)
        w.clock = lambda: base + w.time          # 夕方5時から 12 時間(シミュレーションの時計)
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
            if not big.alive or any("narrowly escaped" in e[2] for e in w.events):
                break
        escaped = any("narrowly escaped" in e[2] for e in w.events)
        self.assertTrue((not big.alive and big.cause == "a shark attack") or escaped)
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
            for t in ts:
                t.air, t.energy, t.fatigue = 999, 1.0, 0.0
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
        for _ in range(5):
            w.step(0.1)
        self.assertEqual(len(w.eggs), 0)
        self.assertEqual(w.births, 1)

    def test_generations_per_day(self):
        """カメの1日(実時間1時間)でおよそ 1〜3 世代。"""
        random.seed(15)
        w = up.World()
        base = at(6, 21, 12, 0)
        w.clock = lambda: base
        w.update_daylight(base, log=False)
        w.seed()
        g0 = w.max_gen
        w.advance_offline(3 * 3600, start=base - 3 * 3600)   # 実時間3時間 = カメの3日
        per_day = (w.max_gen - g0) / 3.0
        self.assertGreaterEqual(per_day, 0.7)
        self.assertLessEqual(per_day, 4.0)


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
        self.assertIn("gulp", fx)
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
        self.assertLess(max(near), t.radius + 6)              # 魚がカメの体の上にいる

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


if __name__ == "__main__":
    unittest.main()
