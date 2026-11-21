"""hand_tetris.py の自動テスト(カメラ・MediaPipeのモデルは使わない。合成した姿勢データで確認)
実行: python -m unittest discover tests"""
import os
import sys
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")  # 音の出ない環境でも動かす
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import hand_tetris as ht  # noqa: E402


class LM:
    def __init__(self, x, y, z=0.0, v=0.99):
        self.x, self.y, self.z, self.visibility = x, y, z, v


def pose(kind, dy=0.0, feet_apart=0.0):
    """画像座標の合成姿勢。kind: stand / tpose / jump / banzai_up"""
    p = {11: (0.52, 0.35), 12: (0.42, 0.35), 23: (0.50, 0.55), 24: (0.44, 0.55),
         25: (0.50, 0.72), 26: (0.44, 0.72), 27: (0.485 + feet_apart, 0.88), 28: (0.455 - feet_apart, 0.88),
         13: (0.54, 0.45), 14: (0.40, 0.45), 15: (0.545, 0.55), 16: (0.395, 0.55)}
    if kind == "tpose":
        p.update({13: (0.60, 0.35), 14: (0.34, 0.35), 15: (0.68, 0.36), 16: (0.26, 0.36)})
    elif kind == "jump":
        dy -= 0.05
    elif kind == "banzai_up":
        p.update({13: (0.54, 0.25), 14: (0.40, 0.25), 15: (0.55, 0.15), 16: (0.39, 0.15)})
    lms = [LM(0.47, 0.3) for _ in range(33)]
    for k, (x, y) in p.items():
        lms[k] = LM(x, y + dy)
    return lms


class GestureTest(unittest.TestCase):
    def setUp(self):
        self.clock = 0.0
        self._orig_time = ht.time.time
        ht.time.time = lambda: self.clock

    def tearDown(self):
        ht.time.time = self._orig_time

    def run_seq(self, seq, fps=30):
        ctrl = ht.BodyGestureController()
        total = {k: 0 for k in ht.BodyGestureController.empty_events() if k != "tpose_progress"}
        for kind, sec, kw in seq:
            for _ in range(int(sec * fps)):
                self.clock += 1 / fps
                ev = ctrl.update(pose(kind, **kw))
                for k in total:
                    total[k] += int(bool(ev[k]))
        return total

    def test_jump_once(self):
        t = self.run_seq([("stand", 1.5, {}), ("jump", 0.3, {}), ("stand", 1, {})])
        self.assertEqual(t["jump"], 1)

    def test_walking_away_is_not_jump(self):
        seq = [("stand", 1.5, {})] + [("stand", 0.1, {"dy": -0.005 * i}) for i in range(12)]
        seq.append(("stand", 3, {"dy": -0.06}))
        self.assertEqual(self.run_seq(seq)["jump"], 0)

    def test_tpose_fires_once_per_hold(self):
        t = self.run_seq([("stand", 1.5, {}), ("tpose", 3, {}), ("stand", 1.5, {}), ("tpose", 1.5, {})])
        self.assertEqual(t["tpose_trigger"], 2)

    def test_short_tpose_does_not_fire(self):
        t = self.run_seq([("stand", 1.5, {}), ("tpose", 0.5, {}), ("stand", 1, {})])
        self.assertEqual(t["tpose_trigger"], 0)

    def test_tpose_with_feet_apart_does_not_fire(self):
        t = self.run_seq([("stand", 1.5, {"feet_apart": 0.05}), ("tpose", 2, {"feet_apart": 0.05})])
        self.assertEqual(t["tpose_trigger"], 0)

    def test_banzai_counts(self):
        t = self.run_seq([("stand", 1.5, {})] + [("banzai_up", 0.4, {}), ("stand", 0.4, {})] * 3)
        self.assertEqual((t["arm_raise"], t["hard_drop"], t["tpose_trigger"]), (3, 3, 0))


class GameTest(unittest.TestCase):
    def make_game(self, rows):
        g = ht.TetrisGame()
        for r in rows:
            for c in range(ht.BOARD_W):
                if c not in (4, 5):
                    g.grid[r][c] = (128, 128, 128)
        g.current = ht.Piece("O")
        return g

    def finish(self, g):
        g.clear_start -= ht.CLEAR_ANIM_SEC + 0.1
        g.update()

    def test_double_and_chain_bonus(self):
        g = self.make_game([16, 17, 18, 19])
        g.hard_drop()
        self.assertEqual(g.clearing_rows, [18, 19])
        self.finish(g)
        self.assertEqual((g.score, g.lines, g.chain), (300, 2, 1))
        g.current = ht.Piece("O")
        g.hard_drop()
        self.finish(g)
        self.assertEqual((g.score, g.lines, g.chain), (300 + 300 + 50, 4, 2))  # 連鎖ボーナス 50
        types = [e["type"] for e in g.pop_events()]
        self.assertIn("clear_start", types)
        self.assertIn("clear", types)

    def test_lock_without_clear_resets_chain(self):
        g = self.make_game([18, 19])
        g.hard_drop()
        self.finish(g)
        g.current = ht.Piece("O")
        g.hard_drop()  # 空の盤面の底に置くだけ
        self.assertEqual(g.chain, 0)

    def test_rank_table(self):
        self.assertEqual(ht.score_rank(0)["rank"], "D")
        self.assertEqual(ht.score_rank(3000)["rank"], "S")

    def test_bgm_bars(self):
        for tempo in ht.BGM_TEMPOS:
            bars = ht.render_bgm_bars(tempo)
            self.assertEqual(len(bars), 8)
            loop_sec = sum(len(b) for b in bars) / ht.SAMPLE_RATE
            self.assertAlmostEqual(loop_sec, 8 * 4 * 60 / ht.BGM_BPM / tempo, places=2)
            self.assertLessEqual(max(abs(b).max() for b in bars), ht.BGM_VOLUME + 1e-6)

    def test_exercise_praise_is_positive(self):
        st = ht.ExerciseStats()
        self.assertEqual(ht.exercise_praise(st)[0], "遊んでくれてありがとう!")
        st.counts.update(step_right=10, step_left=9, squat=5, arm_raise=6)
        lines = ht.exercise_praise(st)
        self.assertIn("特に右ステップをよくがんばりました!", lines)
        self.assertIn("左右バランスよく踏み出せました!", lines)
        st.counts.update(step_right=1, step_left=0, squat=0, arm_raise=0)
        self.assertEqual(ht.exercise_praise(st)[:2], ["体を動かす第一歩、", "ナイスチャレンジです!"])

    def test_version_format(self):
        self.assertRegex(ht.VERSION, r"^\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
