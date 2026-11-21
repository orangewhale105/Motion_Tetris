# -*- coding: utf-8 -*-
"""
Hand Tetris - 全身ジェスチャーで遊ぶARテトリス
============================================

【概要】
ノートPCのカメラで全身を認識し、足のステップ・ハーフスクワット・万歳(両手を
上げて下ろす)動作でブロックを操作するテトリスです。カメラ映像の上にテトリス
盤面と全身のワイヤーフレームを半透明で重ねて表示し、現実とゲーム画面が融合
したAR的な操作感を出します。両手のワイヤーフレームも視覚効果として表示され
ますが、ブロックの操作そのものには使用しません(操作は全身の動きで行います)。

【操作方法】(カメラに向かって全身が映る距離に立ってください)
  ・右足を右へ踏み出す(右ステップ)     : ブロックが1マス右へ移動。
                                            踏み出した足をまた揃えると、
                                            次の右ステップでさらに1マス移動。
  ・左足を左へ踏み出す(左ステップ)     : 同様にブロックが1マス左へ移動。
  ・軽くしゃがむ(ハーフスクワット)     : ブロックが時計回りに90度回転。
  ・両手を万歳して下ろす                : ハードドロップ(一気に着地)。
                                            両手を肩より高く上げ、その後
                                            肩の高さ付近まで下ろした瞬間に
                                            発動します(上げている間は
                                            発動しません)。
  ・キーボード 'q' / 'Esc'、ウィンドウの「×」 : 終了
  ・キーボード 'r'                      : ゲームオーバー後にリスタート
  ・キーボード 'p'                      : 一時停止
  ・キーボード 'c'                      : 全身ジェスチャーの基準姿勢を取り直す
                                            (直立して足を揃えた状態で押してください)

【キャリブレーションについて】
  起動直後の約1秒間(および 'c' キーを押した直後の約1秒間)は、直立して
  足を揃えた姿勢を基準として自動的に取得する「キャリブレーション」期間です。
  この間は画面に「キャリブレーション中...」と表示され、ステップ/スクワット
  の判定は行われません。ステップ/スクワットが反応しない場合は、直立して
  足を揃えた状態で 'c' キーを押して基準を取り直してみてください。画面には
  実測値としきい値を表示するデバッグ行(薄い灰色の文字)もあるので、
  数値が動いているのに閾値を超えない場合はしきい値(STEP_OUT_THRESH,
  SQUAT_DOWN_THRESHなど)を調整してください。

【肩関節角度の表示】
  画面上部と、映像に重ねた肩の位置にリアルタイムで左右の肩関節の
  屈曲角度・外転角度を表示します。上半身がカメラに映っている必要が
  あります(全身操作のため、通常はステップ/スクワットが検出できる
  距離であれば同時に表示されます)。

【必要なライブラリ】
    pip install opencv-python mediapipe numpy pygame pillow

【必要なモデルファイル】
    (1) MediaPipe Hand Landmarker のモデルファイル (hand_landmarker.task)
        ※手のワイヤーフレーム表示(視覚効果のみ)に使用
        https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
    (2) MediaPipe Pose Landmarker のモデルファイル (pose_landmarker_lite.task)
        ※全身ジェスチャー操作・肩関節角度の計測に使用
        https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
    いずれもこのスクリプトと同じフォルダに置いてください。

【カメラの設置について】
    足のステップとハーフスクワット、万歳を検出するため、股関節から
    足首まで、かつ両手を頭上に上げても収まる高さがカメラに映る距離
    (全身が入る距離)に立ってプレイしてください。各ジェスチャーの
    検出しきい値はBodyGestureController付近の定数(STEP_OUT_THRESHや
    BANZAI_RAISE_MARGINなど)で調整できます。

【日本語フォント】
    スコア表示などの日本語を描画するために、Windowsなら通常
    C:/Windows/Fonts/meiryo.ttc が自動で使われます。見つからない場合は
    fallback で英数字のみの表示になります(動作には支障ありません)。
"""

import os
import sys
import time
import math
import random
import threading

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# 日本語テキスト描画 (PILを使ってOpenCVフレームに日本語を焼き込む)
# ---------------------------------------------------------------------------
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

_font_cache = {}


def get_font(size):
    if size in _font_cache:
        return _font_cache[size]
    font = None
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def put_text_jp(frame_bgr, text, xy, size=24, color=(255, 255, 255)):
    """OpenCV(BGR ndarray)フレームに日本語文字列を描画して返す"""
    img_pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    # PILはRGB順
    rgb_color = (color[2], color[1], color[0])
    draw.text(xy, text, font=get_font(size), fill=rgb_color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# サウンド (外部音源ファイル無し。全て波形をその場で生成する8bit風SE/BGM)
# ---------------------------------------------------------------------------
import pygame

pygame.mixer.init(frequency=44100, size=-16, channels=2)
pygame.mixer.set_num_channels(16)

SAMPLE_RATE = 44100


def make_tone(freq, duration, volume=0.35, wave="square", fade=0.01):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    if wave == "square":
        arr = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "triangle":
        arr = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    else:
        arr = np.sin(2 * np.pi * freq * t)
    # フェードイン/アウトでプチノイズを防ぐ
    fade_n = max(1, int(SAMPLE_RATE * fade))
    envelope = np.ones(n)
    envelope[:fade_n] = np.linspace(0, 1, fade_n)
    envelope[-fade_n:] = np.linspace(1, 0, fade_n)
    mono = (arr * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([mono, mono])  # pygameのミキサーがステレオ初期化される環境向けに2ch化
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def make_chord(freqs, duration, volume=0.25, wave="square"):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    mix = np.zeros(n)
    for f in freqs:
        if wave == "square":
            mix += np.sign(np.sin(2 * np.pi * f * t))
        else:
            mix += np.sin(2 * np.pi * f * t)
    mix /= len(freqs)
    fade_n = int(SAMPLE_RATE * 0.01)
    envelope = np.ones(n)
    envelope[:fade_n] = np.linspace(0, 1, fade_n)
    envelope[-fade_n:] = np.linspace(1, 0, fade_n)
    mono = (mix * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([mono, mono])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _tone_array(freq, duration, wave="square", fade=0.006):
    """make_toneの波形部分だけをnumpy配列(-1〜1、フェード込み)で返す内部ヘルパー。
    make_sequenceで複数の音をつなげてひとつのSoundにするために使う。"""
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.linspace(0, duration, n, False)
    if wave == "square":
        arr = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "triangle":
        arr = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    else:
        arr = np.sin(2 * np.pi * freq * t)
    fade_n = max(1, min(n // 2, int(SAMPLE_RATE * fade)))
    envelope = np.ones(n)
    envelope[:fade_n] = np.linspace(0, 1, fade_n)
    envelope[-fade_n:] = np.linspace(1, 0, fade_n)
    return arr * envelope


def make_sequence(notes, volume=0.3, wave="square", gap=0.0):
    """notes: [(周波数Hz, 長さ秒), ...] を順につなげた短いメロディ/フレーズを
    ひとつのpygame.Soundとして生成する(陽気な効果音のフレーズ作りに使う)。"""
    segments = []
    gap_n = int(SAMPLE_RATE * gap)
    for freq, dur in notes:
        segments.append(_tone_array(freq, dur, wave=wave))
        if gap_n > 0:
            segments.append(np.zeros(gap_n))
    mono = np.concatenate(segments) if segments else np.zeros(1)
    mono = (mono * volume * 32767).astype(np.int16)
    stereo = np.column_stack([mono, mono])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def make_sweep(freq_start, freq_end, duration, volume=0.3, wave="sine"):
    """周波数がfreq_startからfreq_endへ滑らかに変化する"シュッ"というスイープ音を作る
    (万歳して下ろす=ハードドロップ用の効果音に使う)。"""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    freq_t = np.linspace(freq_start, freq_end, n)
    phase = 2 * np.pi * np.cumsum(freq_t) / SAMPLE_RATE
    if wave == "square":
        arr = np.sign(np.sin(phase))
    else:
        arr = np.sin(phase)
    fade_n = max(1, int(SAMPLE_RATE * 0.01))
    envelope = np.ones(n)
    envelope[:fade_n] = np.linspace(0, 1, fade_n)
    envelope[-fade_n:] = np.linspace(1, 0, fade_n)
    mono = (arr * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([mono, mono])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


# --- 各動作が判定されたときの効果音(すべて陽気なチップチューン風の短いフレーズ) ---
SE_MOVE_RIGHT = make_sequence([(659, 0.05), (880, 0.06)], volume=0.28, wave="square")   # 右ステップ: 上昇2音
SE_MOVE_LEFT = make_sequence([(880, 0.05), (659, 0.06)], volume=0.28, wave="square")    # 左ステップ: 下降2音
SE_ROTATE = make_sequence([(523, 0.045), (659, 0.045), (880, 0.07)], volume=0.3, wave="triangle")  # スクワット回転: くるっと上昇
SE_HARDDROP = make_sweep(1200, 220, 0.16, volume=0.32, wave="square")  # 万歳→下ろす: シュッと下降するスイープ
SE_LOCK = make_tone(147, 0.1, volume=0.28, wave="square")              # 着地のコツン
# ライン消去: 明るく弾む短いファンファーレ(1〜3ライン)
SE_CLEAR = make_sequence(
    [(523, 0.07), (659, 0.07), (784, 0.07), (1046, 0.16)],
    volume=0.35, wave="triangle", gap=0.0,
)
# 4ライン(テトリス): さらに華やかな長めのファンファーレ
SE_TETRIS = make_sequence(
    [(523, 0.06), (659, 0.06), (784, 0.06), (1046, 0.06), (1318, 0.06), (1568, 0.22)],
    volume=0.4, wave="triangle", gap=0.0,
)
SE_GAMEOVER = make_tone(98, 0.6, volume=0.3, wave="triangle")

# 陽気で弾むリズムの8ビット風BGMループ (周波数Hz, 長さ秒)。付点音符ふうに長短をつけて
# 単調にならないようにしている。
_BGM_NOTES = [
    (784, 0.14), (784, 0.10), (988, 0.14), (1046, 0.22),
    (988, 0.14), (880, 0.10), (784, 0.14), (659, 0.22),
    (698, 0.14), (698, 0.10), (880, 0.14), (932, 0.22),
    (880, 0.14), (784, 0.10), (698, 0.14), (659, 0.22),
]


class BgmPlayer:
    """バックグラウンドスレッドで軽快なチップチューン風BGMをループ再生"""

    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._notes_cache = [make_tone(f, d, volume=0.14, wave="triangle") for f, d in _BGM_NOTES]

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            for sound, (_, dur) in zip(self._notes_cache, _BGM_NOTES):
                if self._stop.is_set():
                    return
                sound.play()
                time.sleep(dur * 0.92)


# ---------------------------------------------------------------------------
# テトリス ロジック
# ---------------------------------------------------------------------------
BOARD_W, BOARD_H = 10, 20
CELL = 26  # 1マスのピクセルサイズ(既定値。実行時にウィンドウの縦幅いっぱいを使うよう動的に再計算される)

# 形状は size x size のグリッド内の (row, col) セル座標(スポーン時の向き)
TETROMINOES = {
    "I": {"cells": [(1, 0), (1, 1), (1, 2), (1, 3)], "size": 4, "color": (255, 255, 0)},   # シアン(BGR)
    "O": {"cells": [(0, 0), (0, 1), (1, 0), (1, 1)], "size": 2, "color": (0, 255, 255)},   # 黄色
    "T": {"cells": [(0, 1), (1, 0), (1, 1), (1, 2)], "size": 3, "color": (255, 0, 255)},   # マゼンタ
    "S": {"cells": [(0, 1), (0, 2), (1, 0), (1, 1)], "size": 3, "color": (0, 200, 0)},     # 緑
    "Z": {"cells": [(0, 0), (0, 1), (1, 1), (1, 2)], "size": 3, "color": (0, 0, 255)},     # 赤
    "J": {"cells": [(0, 0), (1, 0), (1, 1), (1, 2)], "size": 3, "color": (255, 128, 0)},   # 青系オレンジ
    "L": {"cells": [(0, 2), (1, 0), (1, 1), (1, 2)], "size": 3, "color": (0, 128, 255)},   # オレンジ
}


def rotate_cells_cw(cells, size):
    """(row,col)セル群をsize x sizeグリッド内で時計回りに90度回転"""
    return [(c, size - 1 - r) for (r, c) in cells]


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.size = TETROMINOES[kind]["size"]
        self.cells = list(TETROMINOES[kind]["cells"])
        self.color = TETROMINOES[kind]["color"]
        self.row = -1
        self.col = BOARD_W // 2 - self.size // 2
        self.rotation_index = 0  # 0-3: 現在の絶対回転状態(手の回転角度との1:1対応に使う)

    def rotated_cells(self):
        return rotate_cells_cw(self.cells, self.size)

    def occupied(self, row_off=0, col_off=0, cells=None):
        cells = cells if cells is not None else self.cells
        return [(self.row + r + row_off, self.col + c + col_off) for (r, c) in cells]


class TetrisGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[None for _ in range(BOARD_W)] for _ in range(BOARD_H)]
        self.bag = []
        self.current = Piece(self._next_kind())
        self.next_kind = self._next_kind()
        self.score = 0
        self.lines = 0
        self.level = 0
        self.game_over = False
        self.paused = False
        self.last_drop_time = time.time()
        self.lock_timer = None

    def _next_kind(self):
        if not self.bag:
            self.bag = list(TETROMINOES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    @property
    def drop_interval(self):
        # 全身の動作(ステップ・スクワット・万歳)は手の操作より時間がかかるため、
        # 最初はゆっくり(1.3秒間隔)落下させ、レベルが上がるごとに緩やかに加速する。
        # 最速でも0.35秒を下回らないようにして、体の動作が追いつく余地を残す。
        base_interval = 1.3
        speed_up_per_level = 0.07
        min_interval = 0.35
        return max(min_interval, base_interval - self.level * speed_up_per_level)

    def valid(self, cells_positions):
        for (r, c) in cells_positions:
            if c < 0 or c >= BOARD_W or r >= BOARD_H:
                return False
            if r >= 0 and self.grid[r][c] is not None:
                return False
        return True

    def try_move(self, d_col):
        if self.game_over or self.paused:
            return False
        positions = self.current.occupied(col_off=d_col)
        if self.valid(positions):
            self.current.col += d_col
            return True
        return False

    def try_set_col(self, target_col):
        """連続的な横位置指定(手の位置に追従)。無効なら最も近い有効位置へ"""
        if self.game_over or self.paused:
            return
        d = target_col - self.current.col
        step = 1 if d > 0 else -1
        for _ in range(abs(d)):
            if not self.try_move(step):
                break

    def try_rotate(self):
        if self.game_over or self.paused:
            return False
        new_cells = self.current.rotated_cells()
        # シンプルなウォールキック: 0, -1, 1, -2, 2 列ずらして試す
        for kick in (0, -1, 1, -2, 2):
            positions = self.current.occupied(col_off=kick, cells=new_cells)
            if self.valid(positions):
                self.current.cells = new_cells
                self.current.col += kick
                self.current.rotation_index = (self.current.rotation_index + 1) % 4
                return True
        return False

    def soft_drop_step(self):
        if self.game_over or self.paused:
            return False
        positions = self.current.occupied(row_off=1)
        if self.valid(positions):
            self.current.row += 1
            self.lock_timer = None
            return True
        return False

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        while self.soft_drop_step():
            pass
        self._lock_piece()

    def gravity_tick(self):
        if self.game_over or self.paused:
            return
        now = time.time()
        if now - self.last_drop_time >= self.drop_interval:
            self.last_drop_time = now
            if not self.soft_drop_step():
                # 着地: 少し猶予(ロックディレイ)を与える
                if self.lock_timer is None:
                    self.lock_timer = now
                elif now - self.lock_timer > 0.4:
                    self._lock_piece()

    def _lock_piece(self):
        positions = self.current.occupied()
        for (r, c) in positions:
            if 0 <= r < BOARD_H and 0 <= c < BOARD_W:
                self.grid[r][c] = self.current.color
        SE_LOCK.play()
        cleared = self._clear_lines()
        self._spawn_next()
        return cleared

    def _clear_lines(self):
        full_rows = [r for r in range(BOARD_H) if all(self.grid[r][c] is not None for c in range(BOARD_W))]
        for r in full_rows:
            del self.grid[r]
            self.grid.insert(0, [None for _ in range(BOARD_W)])
        count = len(full_rows)
        if count > 0:
            points = {1: 100, 2: 300, 3: 500, 4: 800}.get(count, 0) * (self.level + 1)
            self.score += points
            self.lines += count
            self.level = self.lines // 10
            if count >= 4:
                SE_TETRIS.play()
            else:
                SE_CLEAR.play()
        return count

    def _spawn_next(self):
        self.current = Piece(self.next_kind)
        self.next_kind = self._next_kind()
        self.lock_timer = None
        if not self.valid(self.current.occupied()):
            self.game_over = True

    def ghost_row(self):
        """ハードドロップ着地予定位置(ゴースト表示用)"""
        test_row = self.current.row
        while self.valid(self.current.occupied(row_off=(test_row - self.current.row) + 1)):
            test_row += 1
        return test_row


# ---------------------------------------------------------------------------
# 手のジェスチャー認識 (MediaPipe Tasks API - HandLandmarker, VIDEO mode)
# ---------------------------------------------------------------------------
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

def resolve_model_path(filename):
    """モデルファイルの場所を解決する。
    ・PyInstallerでexe化した場合: exeに同梱したモデル(sys._MEIPASS)を最優先し、
      なければexeと同じフォルダを探す。
    ・通常のPython実行の場合: このスクリプトと同じフォルダ。"""
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(os.path.join(meipass, filename))
        candidates.append(os.path.join(os.path.dirname(sys.executable), filename))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename))
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]  # 見つからない場合も、エラーメッセージ用に既定の場所を返す


MODEL_PATH = resolve_model_path("hand_landmarker.task")

# 手の21ランドマーク間の接続トポロジー(MediaPipe Hand標準の骨格構造)
# mp.solutions への依存を避けるため直接定義する
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # 親指
    (0, 5), (5, 6), (6, 7), (7, 8),          # 人差し指
    (5, 9), (9, 10), (10, 11), (11, 12),     # 中指
    (9, 13), (13, 14), (14, 15), (15, 16),   # 薬指
    (13, 17), (17, 18), (18, 19), (19, 20),  # 小指
    (0, 17),                                 # 手のひら
]

PINCH_ON_THRESH = 0.42   # つまみ判定(閉じる)しきい値 ※手サイズで正規化
PINCH_OFF_THRESH = 0.55  # 開放判定(ヒステリシスでチラつき防止)


def landmark_dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


class HandState:
    """片手ぶんのジェスチャー状態(現在はワイヤーフレーム表示上のつまみ検出のみに使用)"""

    def __init__(self):
        self.pinched = False
        self.grab_active = False

    def update_pinch(self, landmarks):
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        hand_size = max(landmark_dist(wrist, middle_mcp), 1e-4)
        ratio = landmark_dist(thumb_tip, index_tip) / hand_size
        was_pinched = self.pinched
        if not self.pinched and ratio < PINCH_ON_THRESH:
            self.pinched = True
        elif self.pinched and ratio > PINCH_OFF_THRESH:
            self.pinched = False
        just_pinched = self.pinched and not was_pinched
        just_released = (not self.pinched) and was_pinched
        return just_pinched, just_released


class HandController:
    def __init__(self, model_path=MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "hand_landmarker.task が見つかりません。\n"
                "以下のURLからダウンロードして、このスクリプトと同じフォルダに置いてください:\n"
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                "hand_landmarker/float16/latest/hand_landmarker.task"
            )
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp_vision.HandLandmarker.create_from_options(options)
        self.left_state = HandState()   # 画面左側の手 -> 回転
        self.right_state = HandState()  # 画面右側の手 -> 移動/ドロップ
        self._start_time = time.time()

    def process(self, frame_rgb):
        ts_ms = int((time.time() - self._start_time) * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self.landmarker.detect_for_video(mp_image, ts_ms)

        hands = result.hand_landmarks or []
        if not hands:
            return {"left": None, "right": None, "both_just_pinched": False}

        # 画面上のx座標(手首)でソートして「左側の手」「右側の手」を決める
        hands_sorted = sorted(hands, key=lambda lm: lm[0].x)
        left_lm = hands_sorted[0] if len(hands_sorted) >= 1 else None
        right_lm = hands_sorted[-1] if len(hands_sorted) >= 1 else None
        if len(hands_sorted) == 1:
            # 手が1つだけの時は画面のどちら半分にあるかで役割を決める
            if left_lm[0].x < 0.5:
                right_lm = None
            else:
                left_lm = None

        left_just_pinch = left_just_release = False
        right_just_pinch = right_just_release = False

        if left_lm is not None:
            left_just_pinch, left_just_release = self.left_state.update_pinch(left_lm)
        if right_lm is not None:
            right_just_pinch, right_just_release = self.right_state.update_pinch(right_lm)

        both_just_pinched = left_just_pinch and right_just_pinch

        return {
            "left": {"lm": left_lm, "pinched": self.left_state.pinched,
                     "just_pinch": left_just_pinch, "just_release": left_just_release},
            "right": {"lm": right_lm, "pinched": self.right_state.pinched,
                      "just_pinch": right_just_pinch, "just_release": right_just_release},
            "both_just_pinched": both_just_pinched,
        }

    def close(self):
        self.landmarker.close()


def draw_hand_skeleton(frame, landmarks, w, h, pinched):
    color = (0, 255, 120) if pinched else (255, 200, 0)
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for i, p in enumerate(pts):
        r = 6 if i in (4, 8) else 3
        cv2.circle(frame, p, r, color, -1, cv2.LINE_AA)
    # つまみ位置を強調
    thumb, index = pts[4], pts[8]
    mid = ((thumb[0] + index[0]) // 2, (thumb[1] + index[1]) // 2)
    cv2.line(frame, thumb, index, (0, 0, 255) if pinched else (200, 200, 200), 2, cv2.LINE_AA)
    if pinched:
        cv2.circle(frame, mid, 10, (0, 0, 255), 2, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# 姿勢推定 (MediaPipe Tasks API - PoseLandmarker) : 肩関節角度の計測用
# ---------------------------------------------------------------------------
POSE_MODEL_PATH = resolve_model_path("pose_landmarker_lite.task")

# MediaPipe Pose の33ランドマークのうち、肩関節角度の計算に使うインデックス
POSE_L_SHOULDER, POSE_R_SHOULDER = 11, 12
POSE_L_ELBOW, POSE_R_ELBOW = 13, 14
POSE_L_HIP, POSE_R_HIP = 23, 24
# 全身ジェスチャー(ステップ・スクワット)操作 & 脚の描画に使うインデックス
POSE_L_KNEE, POSE_R_KNEE = 25, 26
POSE_L_ANKLE, POSE_R_ANKLE = 27, 28
# 万歳(ハードドロップ)ジェスチャー & 腕の描画に使うインデックス
POSE_L_WRIST, POSE_R_WRIST = 15, 16


def _to_vec(lm):
    return np.array([lm.x, lm.y, lm.z], dtype=float)


def _normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v


def compute_body_frame(world_landmarks):
    """体幹(肩・股関節)のランドマークから、体に対する下方向・前方向・左右方向の
    正規直交基底ベクトルを求める。カメラの向きに依存せず、体自体を基準にするため
    どんな向きで映っていても安定する。"""
    lm = world_landmarks
    l_hip = _to_vec(lm[POSE_L_HIP])
    r_hip = _to_vec(lm[POSE_R_HIP])
    l_sh = _to_vec(lm[POSE_L_SHOULDER])
    r_sh = _to_vec(lm[POSE_R_SHOULDER])
    mid_hip = (l_hip + r_hip) / 2
    mid_shoulder = (l_sh + r_sh) / 2

    down = _normalize(mid_hip - mid_shoulder)       # 体幹の"下"方向(肩->股関節)
    lateral = _normalize(r_sh - l_sh)               # 体幹の"左->右"方向
    forward = _normalize(np.cross(down, lateral))   # 体幹の"前"方向
    lateral = _normalize(np.cross(forward, down))   # 直交性を保つよう再計算
    return down, forward, lateral


def shoulder_flexion_abduction(world_landmarks):
    """左右の肩関節について、屈曲角度(前方挙上)と外転角度(側方挙上)を度で返す。
    戻り値: {"left": (flexion, abduction), "right": (flexion, abduction)}
    ・屈曲: 腕を体側から前方に上げる動き。0度=体側に下ろした状態、90度=前方水平、
            180度=真上(挙上)。負の値は後方への伸展を意味する。
    ・外転: 腕を体側から側方に上げる動き。0度=体側に下ろした状態、90度=側方水平。
            負の値は体の正中線を越える内転方向を意味する。
    検出できない場合はNoneを返す。"""
    if world_landmarks is None:
        return None
    down, forward, lateral = compute_body_frame(world_landmarks)
    results = {}
    for side, shoulder_idx, elbow_idx in (
        ("left", POSE_L_SHOULDER, POSE_L_ELBOW),
        ("right", POSE_R_SHOULDER, POSE_R_ELBOW),
    ):
        shoulder = _to_vec(world_landmarks[shoulder_idx])
        elbow = _to_vec(world_landmarks[elbow_idx])
        arm = elbow - shoulder
        if np.linalg.norm(arm) < 1e-6:
            results[side] = (None, None)
            continue
        a_down = np.dot(arm, down)
        a_fwd = np.dot(arm, forward)
        a_lat = np.dot(arm, lateral)
        # 外転は左右の腕で"体の外側"の符号が逆になるため、右腕はそのまま、左腕は反転させる
        a_lat_signed = a_lat if side == "right" else -a_lat

        flexion = math.degrees(math.atan2(a_fwd, a_down))
        abduction = math.degrees(math.atan2(a_lat_signed, a_down))
        results[side] = (flexion, abduction)
    return results


class PoseController:
    """肩関節角度を推定するためのPoseLandmarker(Tasks API, VIDEOモード)"""

    def __init__(self, model_path=POSE_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "pose_landmarker_lite.task が見つかりません。\n"
                "以下のURLからダウンロードして、このスクリプトと同じフォルダに置いてください:\n"
                "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
            )
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        self._start_time = time.time()

    def process(self, frame_rgb):
        ts_ms = int((time.time() - self._start_time) * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self.landmarker.detect_for_video(mp_image, ts_ms)
        if not result.pose_landmarks:
            return None
        return {
            "landmarks": result.pose_landmarks[0],  # 画像正規化座標(描画用)
            "world_landmarks": result.pose_world_landmarks[0] if result.pose_world_landmarks else None,
        }

    def close(self):
        self.landmarker.close()


def draw_pose_overlay(frame, pose_landmarks, w, h, angles):
    """肩-肘・肩-股関節・股関節-膝-足首のラインと、屈曲/外転角度のラベルを
    フレームに描画して返す。angles は shoulder_flexion_abduction() の戻り値。"""
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in pose_landmarks]
    segments = [
        (POSE_L_HIP, POSE_L_SHOULDER, (255, 180, 0)),
        (POSE_L_SHOULDER, POSE_L_ELBOW, (255, 180, 0)),
        (POSE_L_ELBOW, POSE_L_WRIST, (255, 180, 0)),
        (POSE_R_HIP, POSE_R_SHOULDER, (0, 180, 255)),
        (POSE_R_SHOULDER, POSE_R_ELBOW, (0, 180, 255)),
        (POSE_R_ELBOW, POSE_R_WRIST, (0, 180, 255)),
        (POSE_L_HIP, POSE_R_HIP, (200, 200, 200)),
        (POSE_L_HIP, POSE_L_KNEE, (255, 180, 0)),
        (POSE_L_KNEE, POSE_L_ANKLE, (255, 180, 0)),
        (POSE_R_HIP, POSE_R_KNEE, (0, 180, 255)),
        (POSE_R_KNEE, POSE_R_ANKLE, (0, 180, 255)),
    ]
    for a, b, color in segments:
        cv2.line(frame, pts[a], pts[b], color, 3, cv2.LINE_AA)
    for idx in (POSE_L_SHOULDER, POSE_R_SHOULDER, POSE_L_ELBOW, POSE_R_ELBOW, POSE_L_WRIST, POSE_R_WRIST,
                POSE_L_HIP, POSE_R_HIP, POSE_L_KNEE, POSE_R_KNEE, POSE_L_ANKLE, POSE_R_ANKLE):
        cv2.circle(frame, pts[idx], 7, (255, 255, 255), -1, cv2.LINE_AA)

    if angles is not None:
        l_flex, l_abd = angles["left"]
        r_flex, r_abd = angles["right"]
        if l_flex is not None:
            lx, ly = pts[POSE_L_SHOULDER]
            frame = put_text_jp(frame, f"屈曲{l_flex:.0f}° 外転{l_abd:.0f}°",
                                 (lx - 170, ly - 15), 20, (255, 180, 0))
        if r_flex is not None:
            rx, ry = pts[POSE_R_SHOULDER]
            frame = put_text_jp(frame, f"屈曲{r_flex:.0f}° 外転{r_abd:.0f}°",
                                 (rx + 15, ry - 15), 20, (0, 180, 255))
    return frame


# ---------------------------------------------------------------------------
# 全身ジェスチャー操作 : 右/左ステップで横移動、ハーフスクワットで回転、
#                        万歳(両手を上げて下ろす)でハードドロップ
# ---------------------------------------------------------------------------
STEP_OUT_THRESH = 0.035     # 足の左右オフセットが基準よりこれだけ離れたら「ステップ」とみなす(画面幅比)
STEP_RESET_THRESH = 0.018   # これより基準へ戻ったら「足を揃えた」とみなす(次のステップの準備完了)
SQUAT_DOWN_THRESH = 0.030   # 股関節の高さが基準よりこれだけ下がったら「しゃがんだ」とみなす(画面高さ比)
SQUAT_UP_THRESH = 0.012
BANZAI_RAISE_MARGIN = 0.12  # 両手首が肩よりこれだけ上に来たら「万歳」とみなす(画面高さ比)
BANZAI_LOWER_MARGIN = 0.04  # 両手首が肩に近いこの範囲まで戻ったら「下ろした」とみなす
BASELINE_EMA_ALPHA = 0.01   # 基準姿勢(直立)を緩やかに追従させる係数。値を大きくすると
                            # カメラとの距離変化に素早く追従するが、しゃがみ中などに
                            # 基準がぶれやすくなる。
CALIBRATION_FRAMES = 30     # 起動時/再キャリブレーション時に基準姿勢を安定させるため
                            # 平均を取るフレーム数(30fps換算で約1秒)。


class BodyGestureController:
    """PoseLandmarkerの結果(画像正規化座標)から、右/左ステップ・ハーフスクワット・
    万歳(両手を上げて下ろす)動作を検出し、ブロック操作イベントに変換する。

    ・右ステップ(右足を右へ踏み出す) : 一度踏み出して基準位置(足を揃えた状態)に
      戻るたびに1回だけ「右へ1マス移動」イベントを発生させる。踏み出したまま
      静止していても連続では発生しない(次のステップのために一度足を揃える必要がある)。
    ・左ステップ: 同様に「左へ1マス移動」。
    ・ハーフスクワット(軽くしゃがむ) : しゃがみ始めで1回「回転」イベント。
    ・万歳(両手を頭上に上げてから下ろす) : 両手を肩より高く上げた後、肩付近まで
      下ろした瞬間に1回「ハードドロップ」イベント。上げている間は発火せず、
      "下ろす"動作そのものがトリガーになる。

    起動直後、および recalibrate() 呼び出し後の CALIBRATION_FRAMES フレームは、
    直立・足を揃えた姿勢の平均値を基準として求める「キャリブレーション」期間で、
    この間はステップ/スクワットのジェスチャー判定を行わない(1フレーム目の
    ノイズや中途半端な姿勢がそのまま基準になってしまうのを防ぐため)。
    """

    def __init__(self):
        self.baseline_hip_y = None
        self.baseline_left_x = None
        self.baseline_right_x = None
        self.screen_left_is_pose_left = None  # True: MediaPipeのLEFT_ANKLEが画面左側
        self.step_state = "neutral"   # "neutral" / "right_out" / "left_out"
        self.squat_state = "up"       # "up" / "down"
        self.banzai_state = "down"    # "down"(手を下げている) / "raised"(万歳中)
        self.calibrated = False
        self._calib_buffer = []
        # デバッグ表示用: 直近フレームの実測値としきい値との差(HUDに表示して調整しやすくする)
        self.debug = {"right_delta": 0.0, "left_delta": 0.0, "hip_drop": 0.0}

    def recalibrate(self):
        """基準姿勢(直立・足を揃えた状態)を取り直す。呼び出し後の数フレームで
        再びキャリブレーションが行われる。プレイ中に手動でリセットしたい場合に呼ぶ。"""
        self.calibrated = False
        self._calib_buffer = []
        self.baseline_hip_y = None
        self.baseline_left_x = None
        self.baseline_right_x = None
        self.screen_left_is_pose_left = None

    def update(self, pose_landmarks):
        events = {"step_right": False, "step_left": False, "squat": False, "hard_drop": False}
        if pose_landmarks is None:
            return events

        lm = pose_landmarks
        mid_hip_y = (lm[POSE_L_HIP].y + lm[POSE_R_HIP].y) / 2
        pose_left_ankle_x = lm[POSE_L_ANKLE].x
        pose_right_ankle_x = lm[POSE_R_ANKLE].x

        if not self.calibrated:
            # 直立・足を揃えた状態を数十フレーム分平均して基準とする。
            # このタイミングで「画面上のどちら側がMediaPipeのLEFT_ANKLEか」を
            # 一度だけ確定し、以降はフレームごとに左右を判定し直さない
            # (足を揃えた瞬間などにx座標が接近してノイズで左右が入れ替わり、
            # 片方の足の動きがもう片方の動きとして誤カウントされるのを防ぐため)。
            self._calib_buffer.append((mid_hip_y, pose_left_ankle_x, pose_right_ankle_x))
            if len(self._calib_buffer) >= CALIBRATION_FRAMES:
                n = len(self._calib_buffer)
                avg_hip_y = sum(v[0] for v in self._calib_buffer) / n
                avg_pose_left_x = sum(v[1] for v in self._calib_buffer) / n
                avg_pose_right_x = sum(v[2] for v in self._calib_buffer) / n

                self.screen_left_is_pose_left = avg_pose_left_x <= avg_pose_right_x
                self.baseline_hip_y = avg_hip_y
                if self.screen_left_is_pose_left:
                    self.baseline_left_x = avg_pose_left_x
                    self.baseline_right_x = avg_pose_right_x
                else:
                    self.baseline_left_x = avg_pose_right_x
                    self.baseline_right_x = avg_pose_left_x
                self.calibrated = True
            return events  # キャリブレーション中はジェスチャー判定を行わない

        # キャリブレーション時に固定した対応関係で、画面上の左足/右足のx座標を得る
        # (股関節中心からの相対距離ではなく、各足自身の基準位置からの絶対移動量を
        # 使うことで、ステップ時の体幹の左右の重心移動が反対側の足の判定値に
        # 影響しないようにしている)。
        if self.screen_left_is_pose_left:
            screen_left_x = pose_left_ankle_x
            screen_right_x = pose_right_ankle_x
        else:
            screen_left_x = pose_right_ankle_x
            screen_right_x = pose_left_ankle_x

        a = BASELINE_EMA_ALPHA
        self.baseline_hip_y += (mid_hip_y - self.baseline_hip_y) * a
        self.baseline_left_x += (screen_left_x - self.baseline_left_x) * a
        self.baseline_right_x += (screen_right_x - self.baseline_right_x) * a

        # --- 右ステップ / 左ステップ ---
        # 右足が基準位置より右(x増加)へ、左足が基準位置より左(x減少)へ
        # 動いた量をそれぞれ独立に計算する。
        right_delta = screen_right_x - self.baseline_right_x
        left_delta = self.baseline_left_x - screen_left_x
        self.debug["right_delta"] = right_delta
        self.debug["left_delta"] = left_delta

        if self.step_state == "neutral":
            if right_delta > STEP_OUT_THRESH:
                events["step_right"] = True
                self.step_state = "right_out"
            elif left_delta > STEP_OUT_THRESH:
                events["step_left"] = True
                self.step_state = "left_out"
        elif self.step_state == "right_out":
            if right_delta < STEP_RESET_THRESH:
                self.step_state = "neutral"
        elif self.step_state == "left_out":
            if left_delta < STEP_RESET_THRESH:
                self.step_state = "neutral"

        # --- ハーフスクワットで回転 ---
        hip_drop = mid_hip_y - self.baseline_hip_y  # 正の値: 基準より下(しゃがみ)
        self.debug["hip_drop"] = hip_drop
        if self.squat_state == "up" and hip_drop > SQUAT_DOWN_THRESH:
            events["squat"] = True
            self.squat_state = "down"
        elif self.squat_state == "down" and hip_drop < SQUAT_UP_THRESH:
            self.squat_state = "up"

        # --- 万歳して下ろす動作でハードドロップ ---
        # 肩の高さを基準に、両手首がどれだけ上にあるかで判定する(自己参照のため
        # baseline_hip_yのような追従基準は不要で、カメラ距離が変わっても安定しやすい)。
        mid_shoulder_y = (lm[POSE_L_SHOULDER].y + lm[POSE_R_SHOULDER].y) / 2
        l_wrist_above = mid_shoulder_y - lm[POSE_L_WRIST].y  # 正の値: 手首が肩より上
        r_wrist_above = mid_shoulder_y - lm[POSE_R_WRIST].y
        both_raised = l_wrist_above > BANZAI_RAISE_MARGIN and r_wrist_above > BANZAI_RAISE_MARGIN
        both_lowered = l_wrist_above < BANZAI_LOWER_MARGIN and r_wrist_above < BANZAI_LOWER_MARGIN

        if self.banzai_state == "down" and both_raised:
            self.banzai_state = "raised"
        elif self.banzai_state == "raised" and both_lowered:
            events["hard_drop"] = True
            self.banzai_state = "down"

        return events


# ---------------------------------------------------------------------------
# 盤面のAR風オーバーレイ描画
# ---------------------------------------------------------------------------
def draw_board_overlay(frame, game: TetrisGame, board_x, board_y):
    overlay = frame.copy()

    board_w_px = BOARD_W * CELL
    board_h_px = BOARD_H * CELL

    # 盤面の背景(半透明の黒)
    cv2.rectangle(overlay, (board_x, board_y), (board_x + board_w_px, board_y + board_h_px),
                  (20, 20, 20), -1)

    # 固定されたブロック
    for r in range(BOARD_H):
        for c in range(BOARD_W):
            color = game.grid[r][c]
            if color is not None:
                _draw_cell(overlay, board_x, board_y, r, c, color)

    # ゴースト(着地予測位置)
    if not game.game_over:
        ghost_r = game.ghost_row()
        for (r, c) in game.current.occupied(row_off=(ghost_r - game.current.row)):
            if r >= 0:
                _draw_cell(overlay, board_x, board_y, r, c, game.current.color, ghost=True)

        # 現在のピース
        for (r, c) in game.current.occupied():
            if r >= 0:
                _draw_cell(overlay, board_x, board_y, r, c, game.current.color)

    # 枠線とグリッド線
    for c in range(BOARD_W + 1):
        x = board_x + c * CELL
        cv2.line(overlay, (x, board_y), (x, board_y + board_h_px), (70, 70, 70), 1)
    for r in range(BOARD_H + 1):
        y = board_y + r * CELL
        cv2.line(overlay, (board_x, y), (board_x + board_w_px, y), (70, 70, 70), 1)
    cv2.rectangle(overlay, (board_x, board_y), (board_x + board_w_px, board_y + board_h_px),
                  (255, 255, 255), 2)

    # 半透明合成(現実のカメラ映像とゲーム盤面をブレンド=AR感)
    alpha = 0.72
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # NEXTプレビュー
    next_x = board_x + board_w_px + 20
    next_y = board_y
    cv2.rectangle(frame, (next_x, next_y), (next_x + 4 * CELL, next_y + 4 * CELL), (30, 30, 30), -1)
    cv2.rectangle(frame, (next_x, next_y), (next_x + 4 * CELL, next_y + 4 * CELL), (255, 255, 255), 2)
    nk = game.next_kind
    for (r, c) in TETROMINOES[nk]["cells"]:
        _draw_cell(frame, next_x, next_y, r, c, TETROMINOES[nk]["color"])

    return board_x, board_y, board_w_px, board_h_px, next_x, next_y


def _draw_cell(frame, board_x, board_y, r, c, color, ghost=False):
    x0 = board_x + c * CELL
    y0 = board_y + r * CELL
    x1, y1 = x0 + CELL, y0 + CELL
    if ghost:
        cv2.rectangle(frame, (x0 + 2, y0 + 2), (x1 - 2, y1 - 2), color, 2)
    else:
        cv2.rectangle(frame, (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), color, -1)
        cv2.rectangle(frame, (x0 + 1, y0 + 1), (x1 - 1, y1 - 1), (255, 255, 255), 1)


# ---------------------------------------------------------------------------
# メインループ
# ---------------------------------------------------------------------------
def show_error(message):
    """エラーを表示する。exe化(コンソール無し)ではprintが見えないため、
    Windowsではメッセージボックスでも通知する。"""
    print(message)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "Hand Tetris", 0x10)
        except Exception:
            pass


def main():
    global CELL

    try:
        hand_ctrl = HandController()
    except FileNotFoundError as e:
        show_error(str(e))
        sys.exit(1)

    try:
        pose_ctrl = PoseController()
    except FileNotFoundError as e:
        show_error(str(e))
        sys.exit(1)

    body_ctrl = BodyGestureController()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    if not cap.isOpened():
        show_error("カメラを開けませんでした。他のアプリがカメラを使用していないか確認してください。")
        sys.exit(1)

    game = TetrisGame()
    bgm = BgmPlayer()
    bgm.start()

    was_game_over = False

    window_name = "Hand Tetris - 手でつかんでテトリス"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    window_shown = False  # 最初のimshow後にだけ「×」判定を行う(起動直後の誤判定防止)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # 鏡映しにしてセルフィー感覚に
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ウィンドウ(カメラフレーム)の縦幅いっぱいを使うようセルサイズを毎フレーム再計算する。
        # 上下にスコア表示/操作説明ぶんの余白だけ残し、残りの縦幅を全てBOARD_H等分する。
        TOP_MARGIN = 140
        BOTTOM_MARGIN = 85
        available_h = max(BOARD_H * 10, h - TOP_MARGIN - BOTTOM_MARGIN)
        CELL = max(14, available_h // BOARD_H)
        board_w_px = BOARD_W * CELL
        board_h_px = BOARD_H * CELL
        board_y = TOP_MARGIN + max(0, (h - TOP_MARGIN - BOTTOM_MARGIN - board_h_px) // 2)
        next_box_w = 4 * CELL + 20
        board_x = max(10, w - board_w_px - next_box_w - 30)

        gesture = hand_ctrl.process(rgb)  # 手は視覚効果(ワイヤーフレーム表示)としてのみ使用し、操作には使わない
        pose_data = pose_ctrl.process(rgb)
        shoulder_angles_result = None
        body_events = {"step_right": False, "step_left": False, "squat": False, "hard_drop": False}
        if pose_data is not None:
            shoulder_angles_result = shoulder_flexion_abduction(pose_data["world_landmarks"])
            body_events = body_ctrl.update(pose_data["landmarks"])

        key = cv2.waitKey(1) & 0xFF
        # ウィンドウ右上の「×」で閉じた場合も終了する
        # (OpenCVは「×」を押してもimshowでウィンドウが再生成されてしまうため、明示的に検出する)
        if window_shown:
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
        if key == ord("q") or key == 27:  # Qキー または Escキーで終了
            break
        elif key == ord("r") and game.game_over:
            game = TetrisGame()
            was_game_over = False
            bgm.start()
        elif key == ord("p"):
            game.paused = not game.paused
        elif key == ord("c"):
            body_ctrl.recalibrate()  # 直立・足を揃えた状態で押すと基準姿勢を取り直す

        # --- 全身ジェスチャー -> ゲーム操作へのマッピング ---
        # ・右ステップ(右足を右へ踏み出す)     : ブロックを1マス右へ移動
        # ・左ステップ(左足を左へ踏み出す)     : ブロックを1マス左へ移動
        # ・ハーフスクワット                    : ブロックを回転
        # ・万歳(両手を上げてから下ろす)       : ハードドロップ(一気に着地)
        if not game.game_over and not game.paused:
            if body_events["step_right"]:
                if game.try_move(1):
                    SE_MOVE_RIGHT.play()
            if body_events["step_left"]:
                if game.try_move(-1):
                    SE_MOVE_LEFT.play()
            if body_events["squat"]:
                if game.try_rotate():
                    SE_ROTATE.play()
            if body_events["hard_drop"]:
                SE_HARDDROP.play()
                game.hard_drop()

            game.gravity_tick()

        if game.game_over and not was_game_over:
            was_game_over = True
            SE_GAMEOVER.play()
            bgm.stop()

        # --- 描画 ---
        draw_board_overlay(frame, game, board_x, board_y)

        if pose_data is not None:
            frame = draw_pose_overlay(frame, pose_data["landmarks"], w, h, shoulder_angles_result)

        for side_key in ("left", "right"):
            info = gesture[side_key]
            if info and info["lm"] is not None:
                draw_hand_skeleton(frame, info["lm"], w, h, info["pinched"])

        frame = put_text_jp(frame, f"スコア: {game.score}", (20, 20), 26, (255, 255, 255))
        frame = put_text_jp(frame, f"ライン: {game.lines}  レベル: {game.level}", (20, 55), 22, (200, 200, 200))

        if shoulder_angles_result is not None:
            l_flex, l_abd = shoulder_angles_result["left"]
            r_flex, r_abd = shoulder_angles_result["right"]
            l_txt = f"屈曲{l_flex:.0f}°/外転{l_abd:.0f}°" if l_flex is not None else "--"
            r_txt = f"屈曲{r_flex:.0f}°/外転{r_abd:.0f}°" if r_flex is not None else "--"
        else:
            l_txt = r_txt = "--"
        angle_text = f"肩関節 外転屈曲角度  左: {l_txt}   右: {r_txt}"
        frame = put_text_jp(frame, angle_text, (20, 88), 22, (0, 220, 180))

        # デバッグ用: ステップ/スクワット判定の実測値としきい値を表示(調整の目安に)
        dbg = body_ctrl.debug
        debug_text = (f"[debug] 右足Δ={dbg['right_delta']:+.3f}(閾値{STEP_OUT_THRESH:.3f}) "
                      f"左足Δ={dbg['left_delta']:+.3f}(閾値{STEP_OUT_THRESH:.3f}) "
                      f"腰の下がりΔ={dbg['hip_drop']:+.3f}(閾値{SQUAT_DOWN_THRESH:.3f})")
        frame = put_text_jp(frame, debug_text, (20, 114), 16, (150, 150, 150))

        frame = put_text_jp(frame, "右ステップ=右移動 / 左ステップ=左移動 / ハーフスクワット=回転 / 万歳→下ろす=即落下",
                             (20, h - 65), 20, (180, 220, 255))
        frame = put_text_jp(frame, "Cキー: 直立して足を揃えた状態で押すと基準姿勢を取り直します",
                             (20, h - 35), 18, (150, 200, 150))

        if pose_data is not None and not body_ctrl.calibrated:
            frame = put_text_jp(frame, "キャリブレーション中... 直立して足を揃えてください",
                                 (w // 2 - 320, h // 2 - 60), 30, (0, 255, 255))

        if game.paused:
            frame = put_text_jp(frame, "一時停止中 (Pで再開)", (w // 2 - 150, h // 2), 34, (0, 255, 255))
        if game.game_over:
            frame = put_text_jp(frame, "ゲームオーバー - Rでリスタート / Qで終了(Esc・×でも可)",
                                 (w // 2 - 260, h // 2), 32, (0, 0, 255))

        cv2.imshow(window_name, frame)
        window_shown = True

    bgm.stop()
    hand_ctrl.close()
    pose_ctrl.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
