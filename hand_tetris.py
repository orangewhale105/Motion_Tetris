# -*- coding: utf-8 -*-
"""
モーションテトリス(旧称 Hand Tetris) - 全身ジェスチャーで遊ぶARテトリス
======================================================================

【概要】
ノートPCのカメラで全身を認識し、足のステップ・ハーフスクワット・万歳(両手を
上げて下ろす)動作でブロックを操作するテトリスです。カメラ映像の上にテトリス
盤面と全身のワイヤーフレームを半透明で重ねて表示します。両手のワイヤーフレーム
は視覚効果のみで、ブロックの操作には使用しません。

【画面の流れ】
  タイトル → カウントダウン(3・2・1・START) → プレイ → リザルト(スコア発表)
  → ジャンプ または 'S'キーで再スタート

【操作方法】(カメラに向かって全身が映る距離に立ってください)
  ・ジャンプ / キーボード 'S'           : ゲームスタート(タイトル・リザルト画面)
  ・両足を揃えて両手を横に伸ばす(1秒) : 基準姿勢のキャリブレーション(いつでも)
  ・右足を右へ踏み出す(右ステップ)     : ブロックが1マス右へ移動。
                                            足を揃えてから次のステップでさらに1マス。
  ・左足を左へ踏み出す(左ステップ)     : 同様にブロックが1マス左へ移動。
  ・軽くしゃがむ(ハーフスクワット)     : ブロックが時計回りに90度回転。
  ・両手を万歳して下ろす                : ハードドロップ(一気に着地)。
                                            両手を肩より高く上げ、肩の高さ付近まで
                                            下ろした瞬間に発動します。
  ・キーボード 'q' / 'Esc'、ウィンドウの「×」 : 終了
  ・キーボード 'p'                      : 一時停止
  ・キーボード 'c'                      : 基準姿勢を取り直す
                                            (直立して足を揃えた状態で押してください)

【キャリブレーションについて】
  起動直後(および 'c' キー / 両手を横に伸ばすポーズの後)の約1秒間は、直立して
  足を揃えた姿勢を基準として自動的に取得する期間です。この間はジェスチャーの
  判定を行いません。画面左上の灰色の [debug] 行に実測値としきい値を表示します。

【ゲームの演出】
  ・ライン消去: 消える行の点滅アニメーション、ブロックの破片、SINGLE〜TETRIS表示、
    連続でラインを消すと「連鎖」ボーナスと効果音。
  ・ブロックが上まで積み上がると、BGMのテンポが上がり心音と警告表示が出ます。
  ・ゲーム終了時: 結果発表(スコアのカウントアップ・ランク表示)と、ランクに応じた
    桜吹雪・花火・歓声。
  ・運動の記録: ステップ数・スクワット数・上肢挙上(万歳)数・肩の最大角度・プレイ
    時間を表示します。

【起動のしかた】
    GitHub の Releases(https://github.com/orangewhale105/Motion_Tetris/releases/latest)から
    hand_tetris.py をダウンロードし、ダブルクリックするだけで起動します(Pythonが必要)。
    初回は、足りないライブラリを自動でインストールし、モデルファイルを自動で
    ダウンロードしてこのファイルと同じフォルダに保存します(インターネット接続が必要)。

【必要なライブラリ】(自動でインストールされます)
    pip install opencv-python mediapipe numpy pygame pillow

【必要なモデルファイル】
    (1) hand_landmarker.task (手のワイヤーフレーム表示用)
        https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
    (2) pose_landmarker_lite.task (全身ジェスチャー操作・肩関節角度の計測用)
        https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
    無ければ起動時に自動でダウンロードします(手動で同じフォルダに置いてもよい)。

【日本語フォント】
    Windowsなら C:/Windows/Fonts/meiryo.ttc(太字は meiryob.ttc)を使います。
"""

# 版の番号。変更して main に取り込むと、GitHub の Releases に新しい版として自動で置かれる
# (.github/workflows/release.yml)。変更内容は CHANGELOG.md に書く。
VERSION = "2.1"

import os
import sys
import time
import math
import random
import threading
import traceback
import subprocess
import importlib.util
from collections import deque


def show_error(message):
    """エラーを表示する。ダブルクリック起動やexe化ではコンソールが見えない/すぐ閉じるため、
    Windowsではメッセージボックスでも通知する。"""
    print(message)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "モーションテトリス", 0x10)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 起動準備: 足りないライブラリを自動インストール(exe版では不要なので行わない)
# ---------------------------------------------------------------------------
REQUIRED_PACKAGES = [("cv2", "opencv-python"), ("mediapipe", "mediapipe"), ("numpy", "numpy"),
                     ("pygame", "pygame"), ("PIL", "pillow")]


def ensure_packages():
    if getattr(sys, "frozen", False):
        return
    missing = [pip_name for mod, pip_name in REQUIRED_PACKAGES if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    print("必要なライブラリをインストールしています(初回のみ・数分かかります):", " ".join(missing))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    except Exception:
        show_error("ライブラリのインストールに失敗しました:\n  " + " ".join(missing) +
                   "\n\nインターネット接続を確認してから、もう一度起動してください。\n"
                   "(手動の場合: python -m pip install " + " ".join(missing) + ")")
        sys.exit(1)
    importlib.invalidate_caches()


ensure_packages()

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# 日本語テキスト描画
# PILへの変換は1フレームに1回だけ行う(TextLayerに文字列を溜めてまとめて描く)。
# 以前は文字列ごとに変換していたため、文字が増えるほどフレームレートが落ちていた。
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
_BOLD_FONT_CANDIDATES = [
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]

_font_cache = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    font = None
    candidates = (_BOLD_FONT_CANDIDATES + _FONT_CANDIDATES) if bold else _FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


class TextLayer:
    """1フレーム分の文字列を溜めて、render()でまとめて描画する。
    色はOpenCVと同じBGR順で指定する(BGRのままPILに渡すので変換不要)。"""

    def __init__(self):
        self.items = []

    def add(self, text, xy, size=24, color=(255, 255, 255), align="left", valign="top",
            stroke=0, stroke_color=(0, 0, 0), bold=False):
        self.items.append((text, xy, int(max(8, round(size))), color, align, valign,
                           int(max(0, round(stroke))), stroke_color, bold))

    def render(self, frame_bgr):
        if not self.items:
            return frame_bgr
        img = Image.fromarray(frame_bgr)
        draw = ImageDraw.Draw(img)
        for text, (x, y), size, color, align, valign, stroke, stroke_color, bold in self.items:
            font = get_font(size, bold)
            if align != "left" or valign != "top":
                l, t, r, b = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
                if align == "center":
                    x -= l + (r - l) / 2
                elif align == "right":
                    x -= r
                if valign == "middle":
                    y -= t + (b - t) / 2
            draw.text((x, y), text, font=font, fill=tuple(color),
                      stroke_width=stroke, stroke_fill=tuple(stroke_color))
        self.items = []
        return np.array(img)


def shade_rect(frame, x0, y0, x1, y1, alpha=0.55, color=(0, 0, 0)):
    """矩形領域を半透明の色で暗くする(パネルの背景用)"""
    fh, fw = frame.shape[:2]
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(fw, int(x1)), min(fh, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    roi = frame[y0:y1, x0:x1]
    bg = np.empty_like(roi)
    bg[:] = color
    frame[y0:y1, x0:x1] = cv2.addWeighted(bg, alpha, roi, 1 - alpha, 0)


# ---------------------------------------------------------------------------
# サウンド (外部音源ファイル無し。全て波形をその場で生成する)
# ---------------------------------------------------------------------------
import pygame

pygame.mixer.init(frequency=44100, size=-16, channels=2)
pygame.mixer.set_num_channels(32)

SAMPLE_RATE = 44100
_rng = np.random.default_rng(20261121)  # 効果音のノイズ生成用(毎回同じ音になるよう固定シード)


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


def _tone_array(freq, duration, wave="square", fade=0.006):
    """波形をnumpy配列(-1〜1、フェード込み)で返す内部ヘルパー"""
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
    """notes: [(周波数Hz, 長さ秒), ...] を順につなげたフレーズをひとつのSoundにする"""
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
    """周波数が滑らかに変化するスイープ音"""
    return _sound_from(_sweep_arr(freq_start, freq_end, duration, wave), volume)


def _sound_from(mono, volume):
    """-1〜1程度の配列を、ピークをそろえてからvolumeの音量でSoundにする"""
    mono = np.asarray(mono, dtype=float)
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    if peak < 1e-9:
        mono = np.zeros(max(1, mono.size))
        peak = 1.0
    data = (mono / peak * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _seq_arr(notes, wave="square"):
    return np.concatenate([_tone_array(f, d, wave=wave) for f, d in notes])


def _chord_arr(freqs, duration, wave="square"):
    return sum(_tone_array(f, duration, wave=wave) for f in freqs) / len(freqs)


def _sweep_arr(f0, f1, duration, wave="sine"):
    n = max(1, int(SAMPLE_RATE * duration))
    freq = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    arr = np.sign(np.sin(phase)) if wave == "square" else np.sin(phase)
    fade_n = max(1, min(n // 2, int(SAMPLE_RATE * 0.01)))
    arr[:fade_n] *= np.linspace(0, 1, fade_n)
    arr[-fade_n:] *= np.linspace(1, 0, fade_n)
    return arr


def _bandpass(x, lo, hi):
    """FFTで指定帯域以外を落とす簡易バンドパス"""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SAMPLE_RATE)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, n=len(x))


def _thud(duration, lo, hi, tau):
    """帯域制限したノイズを指数減衰させた打撃音(ドン・ジャーン等)"""
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n) / SAMPLE_RATE
    return _bandpass(_rng.standard_normal(n), lo, hi) * np.exp(-t / tau)


def _mix(parts):
    """parts: [(配列, 開始秒, ゲイン), ...] を重ね合わせる"""
    end = max(int(st * SAMPLE_RATE) + len(a) for a, st, g in parts)
    out = np.zeros(end)
    for a, st, g in parts:
        s = int(st * SAMPLE_RATE)
        out[s:s + len(a)] += a * g
    return out


def make_crowd_cheer(duration=4.0):
    """歓声(「わー!」)の合成。帯域制限ノイズ+音程が上がる多数の声を重ねる。
    録音素材ではないため、あくまで「それらしい」音。"""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n) / SAMPLE_RATE
    hiss = _bandpass(_rng.standard_normal(n), 500, 3500)
    hiss *= 0.7 + 0.3 * np.sin(2 * np.pi * 2.3 * t) * np.sin(2 * np.pi * 0.7 * t)
    hiss /= np.max(np.abs(hiss)) + 1e-9
    voices = np.zeros(n)
    for _ in range(30):
        f0 = _rng.uniform(200, 600)
        st = _rng.uniform(0, 0.8)
        ln = _rng.uniform(1.0, duration - st)
        vib = 1 + 0.02 * np.sin(2 * np.pi * _rng.uniform(4, 8) * t + _rng.uniform(0, 6.28))
        glide = 1 + _rng.uniform(0.1, 0.35) * np.clip((t - st) / 0.4, 0, 1)
        ph = 2 * np.pi * np.cumsum(f0 * vib * glide) / SAMPLE_RATE
        tone = np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.15 * np.sin(4 * ph)
        flutter = 0.6 + 0.4 * np.sin(2 * np.pi * _rng.uniform(3, 6) * t + _rng.uniform(0, 6.28))
        env = np.clip((t - st) / 0.15, 0, 1) * np.clip((st + ln - t) / 0.5, 0, 1)
        voices += tone * env * flutter * _rng.uniform(0.5, 1.0)
    voices = _bandpass(voices, 250, 3000)
    voices /= np.max(np.abs(voices)) + 1e-9
    overall = np.clip(t / 0.25, 0, 1) * np.clip((duration - t) / 1.5, 0, 1)
    return (0.55 * hiss + 0.6 * voices) * overall


def make_applause(duration=3.0, claps_per_sec=60):
    """拍手の合成。短いノイズバーストをランダムに多数重ねる。"""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n) / SAMPLE_RATE
    clap_n = int(0.02 * SAMPLE_RATE)
    templates = [_thud(0.02, 800, 6000, 0.004) for _ in range(8)]
    out = np.zeros(n)
    for _ in range(int(duration * claps_per_sec)):
        pos = int(_rng.integers(0, n - clap_n))
        out[pos:pos + clap_n] += templates[int(_rng.integers(0, 8))] * _rng.uniform(0.3, 1.0)
    overall = np.clip(t / 0.1, 0, 1) * np.clip((duration - t) / 1.0, 0, 1)
    return out * overall


def make_firework():
    """花火の「ドーン…パチパチ」"""
    n = int(SAMPLE_RATE * 1.0)
    out = np.zeros(n)
    boom = _thud(0.8, 40, 500, 0.25)
    out[:len(boom)] += boom / (np.max(np.abs(boom)) + 1e-9)
    click = int(0.004 * SAMPLE_RATE)
    for _ in range(60):
        pos = int(SAMPLE_RATE * _rng.uniform(0.15, 0.95)) - click
        c = _thud(0.004, 2000, 9000, 0.001)
        out[pos:pos + len(c)] += c / (np.max(np.abs(c)) + 1e-9) * _rng.uniform(0.1, 0.4)
    return out


# --- 操作の効果音 ---
SE_MOVE_RIGHT = make_sequence([(659, 0.05), (880, 0.06)], volume=0.28, wave="square")   # 右ステップ: 上昇2音
SE_MOVE_LEFT = make_sequence([(880, 0.05), (659, 0.06)], volume=0.28, wave="square")    # 左ステップ: 下降2音
SE_ROTATE = make_sequence([(523, 0.045), (659, 0.045), (880, 0.07)], volume=0.3, wave="triangle")  # スクワット回転
SE_HARDDROP = _sound_from(_mix([(_sweep_arr(1200, 220, 0.16, "square"), 0, 0.5),
                                (_thud(0.25, 40, 500, 0.06), 0.13, 1.0)]), 0.42)  # シュッ+ドン
SE_LOCK = make_tone(147, 0.1, volume=0.28, wave="square")              # 着地のコツン

# --- ライン消去(消した本数で音を変える) ---
SE_CLEAR = {
    1: _sound_from(_seq_arr([(523, 0.06), (659, 0.06), (784, 0.06), (1046, 0.16)], "triangle"), 0.35),
    2: _sound_from(_mix([(_seq_arr([(587, 0.055), (740, 0.055), (880, 0.055), (1175, 0.055), (1480, 0.2)], "triangle"), 0, 1.0),
                         (_chord_arr([740, 880, 1175], 0.25, "square"), 0.22, 0.25)]), 0.38),
    3: _sound_from(_mix([(_seq_arr([(659, 0.05), (831, 0.05), (988, 0.05), (1319, 0.05), (1661, 0.05), (1976, 0.24)], "triangle"), 0, 1.0),
                         (_chord_arr([659, 831, 988, 1319], 0.35, "square"), 0.25, 0.3)]), 0.4),
    4: _sound_from(_mix([(_seq_arr([(523, 0.07), (659, 0.07), (784, 0.07), (1046, 0.07), (784, 0.07),
                                    (1046, 0.07), (1319, 0.07), (1568, 0.4)], "triangle"), 0, 1.0),
                         (_chord_arr([523, 659, 784, 1046], 0.8, "square"), 0.49, 0.35),
                         (_thud(0.9, 1500, 9000, 0.3), 0.0, 0.5)]), 0.46),
}
# --- 連鎖(連続でラインを消す)。連鎖数が増えるほど音程が上がる ---
SE_CHAIN = {}
for _k in range(2, 11):
    _b = 880 * 2 ** ((_k - 2) * 2 / 12)
    SE_CHAIN[_k] = _sound_from(_seq_arr([(_b, 0.05), (_b * 1.5, 0.05), (_b * 2, 0.16)], "sine"), 0.38)
SE_LEVELUP = _sound_from(_mix([(_seq_arr([(523, 0.08), (659, 0.08), (784, 0.08), (1046, 0.08), (1319, 0.3)], "square"), 0, 1.0),
                               (_chord_arr([659, 784, 1046], 0.3, "triangle"), 0.32, 0.5)]), 0.32)

# --- ピンチ時の心音(ドクン、ドクン) ---
SE_HEARTBEAT = _sound_from(_mix([(_sweep_arr(150, 55, 0.12, "sine"), 0, 1.0),
                                 (_sweep_arr(130, 50, 0.10, "sine"), 0.2, 0.7)]), 0.6)

# --- 画面遷移・キャリブレーション ---
SE_COUNT = make_tone(660, 0.15, volume=0.3, wave="square")
SE_GO = _sound_from(_chord_arr([784, 988, 1175, 1568], 0.5, "square"), 0.35)
SE_CALIB_START = make_tone(880, 0.08, volume=0.25, wave="sine")
SE_CALIB_OK = _sound_from(_seq_arr([(1046, 0.08), (1568, 0.18)], "sine"), 0.35)

# --- リザルト(結果発表) ---
SE_GAMEOVER = _sound_from(_seq_arr([(659, 0.22), (622, 0.22), (587, 0.22), (554, 0.7)], "triangle"), 0.32)
SE_BLIP = _sound_from(_seq_arr([(1319, 0.04), (1760, 0.05)], "square"), 0.2)
SE_TICK = make_tone(2093, 0.02, volume=0.12, wave="square")
SE_STAMP = _sound_from(_mix([(_sweep_arr(300, 60, 0.25, "sine"), 0, 1.0), (_thud(0.3, 100, 3000, 0.08), 0, 0.8)]), 0.55)
SE_NEWRECORD = _sound_from(_seq_arr([(1046, 0.05), (1319, 0.05), (1568, 0.05), (2093, 0.05), (1568, 0.05), (2093, 0.25)], "square"), 0.25)
SE_FANFARE_BIG = _sound_from(_mix([
    (_seq_arr([(392, 0.14), (523, 0.14), (659, 0.14), (784, 0.28), (659, 0.14), (784, 0.14), (1046, 0.8)], "square"), 0, 1.0),
    (_chord_arr([262, 330, 392], 0.56, "triangle"), 0.0, 0.6),
    (_chord_arr([349, 440, 523], 0.42, "triangle"), 0.56, 0.6),
    (_chord_arr([392, 523, 659, 784], 0.9, "triangle"), 0.98, 0.7),
]), 0.34)
SE_FANFARE = _sound_from(_mix([
    (_seq_arr([(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.5)], "square"), 0, 1.0),
    (_chord_arr([523, 659, 784], 0.5, "triangle"), 0.36, 0.6),
]), 0.32)
SE_JINGLE = _sound_from(_seq_arr([(784, 0.1), (988, 0.1), (1175, 0.28)], "triangle"), 0.32)
SE_DONMAI = _sound_from(_seq_arr([(523, 0.15), (494, 0.15), (523, 0.15), (392, 0.45)], "sine"), 0.32)
SE_CHEER = _sound_from(make_crowd_cheer(4.0), 0.5)
SE_APPLAUSE = _sound_from(make_applause(3.0), 0.45)
SE_FIREWORK = _sound_from(make_firework(), 0.4)

# BGM (周波数Hz, 長さ秒)
_BGM_NOTES = [
    (784, 0.14), (784, 0.10), (988, 0.14), (1046, 0.22),
    (988, 0.14), (880, 0.10), (784, 0.14), (659, 0.22),
    (698, 0.14), (698, 0.10), (880, 0.14), (932, 0.22),
    (880, 0.14), (784, 0.10), (698, 0.14), (659, 0.22),
]
BGM_TEMPOS = (1.0, 1.25, 1.5)  # ピンチ度 0/1/2 のときのテンポ倍率


class BgmPlayer:
    """バックグラウンドスレッドでBGMをループ再生。set_tempo_level()でテンポを変える。
    世代番号でスレッドを管理し、stop()→start()を素早く行っても二重再生にならないようにする。"""

    def __init__(self):
        self._caches = {t: [make_tone(f, d / t, volume=0.14, wave="triangle") for f, d in _BGM_NOTES]
                        for t in BGM_TEMPOS}
        self.tempo_level = 0
        self._gen = 0

    def start(self):
        self._gen += 1
        threading.Thread(target=self._loop, args=(self._gen,), daemon=True).start()

    def stop(self):
        self._gen += 1

    def set_tempo_level(self, level):
        self.tempo_level = max(0, min(len(BGM_TEMPOS) - 1, level))

    def _loop(self, gen):
        while gen == self._gen:
            for i, (_, dur) in enumerate(_BGM_NOTES):
                if gen != self._gen:
                    return
                tempo = BGM_TEMPOS[self.tempo_level]
                self._caches[tempo][i].play()
                time.sleep(dur / tempo * 0.92)


# ---------------------------------------------------------------------------
# テトリス ロジック
# ---------------------------------------------------------------------------
BOARD_W, BOARD_H = 10, 20
CELL = 26  # 1マスのピクセルサイズ(実行時にウィンドウの縦幅いっぱいを使うよう動的に再計算される)
CLEAR_ANIM_SEC = 0.35     # ライン消去アニメーションの長さ(この間は操作・落下を止める)
GAMEOVER_FILL_SEC = 1.0   # ゲームオーバー時に盤面を下から灰色で埋める演出の長さ
CHAIN_BONUS = 50          # 連鎖ボーナス: 50 ×(連鎖数−1)×(レベル+1)

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
        self.rotation_index = 0

    def rotated_cells(self):
        return rotate_cells_cw(self.cells, self.size)

    def occupied(self, row_off=0, col_off=0, cells=None):
        cells = cells if cells is not None else self.cells
        return [(self.row + r + row_off, self.col + c + col_off) for (r, c) in cells]


class TetrisGame:
    """盤面ロジック。演出用の出来事は self.events に溜め、メインループが pop_events() で取り出す。
    イベント: lock / hard_drop(cells) / clear_start(rows, colors) /
              clear(count, points, chain, level_up, level) / game_over"""

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
        self.game_over_time = None
        self.paused = False
        self.last_drop_time = time.time()
        self.lock_timer = None
        self.chain = 0          # 連続でラインを消したロック回数(消さずにロックすると0に戻る)
        self.max_chain = 0
        self.tetris_count = 0   # 4ライン同時消しの回数
        self.clearing_rows = []
        self.clear_start = 0.0
        self.events = []

    def pop_events(self):
        ev, self.events = self.events, []
        return ev

    def _next_kind(self):
        if not self.bag:
            self.bag = list(TETROMINOES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    @property
    def drop_interval(self):
        # 全身の動作は時間がかかるため、最初はゆっくり(1.3秒間隔)落下させ、
        # レベルが上がるごとに緩やかに加速する(最速0.35秒)。
        base_interval = 1.3
        speed_up_per_level = 0.07
        min_interval = 0.35
        return max(min_interval, base_interval - self.level * speed_up_per_level)

    def busy(self):
        return self.game_over or self.paused or bool(self.clearing_rows)

    def clear_progress(self, now=None):
        if not self.clearing_rows:
            return 0.0
        now = time.time() if now is None else now
        return min(1.0, (now - self.clear_start) / CLEAR_ANIM_SEC)

    def stack_height(self):
        """積み上がっているブロックの高さ(行数)"""
        for r in range(BOARD_H):
            if any(v is not None for v in self.grid[r]):
                return BOARD_H - r
        return 0

    def valid(self, cells_positions):
        for (r, c) in cells_positions:
            if c < 0 or c >= BOARD_W or r >= BOARD_H:
                return False
            if r >= 0 and self.grid[r][c] is not None:
                return False
        return True

    def try_move(self, d_col):
        if self.busy():
            return False
        positions = self.current.occupied(col_off=d_col)
        if self.valid(positions):
            self.current.col += d_col
            return True
        return False

    def try_rotate(self):
        if self.busy():
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
        if self.busy():
            return False
        positions = self.current.occupied(row_off=1)
        if self.valid(positions):
            self.current.row += 1
            self.lock_timer = None
            return True
        return False

    def hard_drop(self):
        if self.busy():
            return
        while self.soft_drop_step():
            pass
        self.events.append({"type": "hard_drop", "cells": self.current.occupied()})
        self._lock_piece()

    def update(self):
        """毎フレーム呼ぶ。ライン消去アニメーションの進行と自然落下を処理する。"""
        if self.game_over or self.paused:
            return
        if self.clearing_rows:
            if time.time() - self.clear_start >= CLEAR_ANIM_SEC:
                self._finish_clear()
            return
        self.gravity_tick()

    def gravity_tick(self):
        if self.busy():
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
        for (r, c) in self.current.occupied():
            if 0 <= r < BOARD_H and 0 <= c < BOARD_W:
                self.grid[r][c] = self.current.color
        self.events.append({"type": "lock"})
        full_rows = [r for r in range(BOARD_H) if all(self.grid[r][c] is not None for c in range(BOARD_W))]
        if full_rows:
            # すぐには消さず、CLEAR_ANIM_SEC の間アニメーションを見せてから消す
            self.clearing_rows = full_rows
            self.clear_start = time.time()
            self.events.append({"type": "clear_start", "rows": list(full_rows),
                                "colors": {r: list(self.grid[r]) for r in full_rows}})
        else:
            self.chain = 0
            self._spawn_next()

    def _finish_clear(self):
        rows = self.clearing_rows
        self.clearing_rows = []
        for r in rows:  # 昇順に削除して先頭に空行を足すので、残りの行番号はずれない
            del self.grid[r]
            self.grid.insert(0, [None for _ in range(BOARD_W)])
        count = len(rows)
        self.chain += 1
        self.max_chain = max(self.max_chain, self.chain)
        if count >= 4:
            self.tetris_count += 1
        base = {1: 100, 2: 300, 3: 500, 4: 800}.get(count, 800) * (self.level + 1)
        bonus = CHAIN_BONUS * (self.chain - 1) * (self.level + 1)
        points = base + bonus
        self.score += points
        self.lines += count
        old_level = self.level
        self.level = self.lines // 10
        self.events.append({"type": "clear", "count": count, "points": points, "chain": self.chain,
                            "level_up": self.level > old_level, "level": self.level})
        self._spawn_next()

    def _spawn_next(self):
        self.current = Piece(self.next_kind)
        self.next_kind = self._next_kind()
        self.lock_timer = None
        self.last_drop_time = time.time()
        if not self.valid(self.current.occupied()):
            self.game_over = True
            self.game_over_time = time.time()
            self.events.append({"type": "game_over"})

    def ghost_row(self):
        """ハードドロップ着地予定位置(ゴースト表示用)"""
        test_row = self.current.row
        while self.valid(self.current.occupied(row_off=(test_row - self.current.row) + 1)):
            test_row += 1
        return test_row


# ---------------------------------------------------------------------------
# 手のランドマーク検出 (MediaPipe Tasks API - HandLandmarker, VIDEO mode)
# 表示(ワイヤーフレーム)専用。操作には使わない。
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
HAND_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                  "hand_landmarker/float16/latest/hand_landmarker.task")
POSE_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                  "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")


def ensure_model(path, url):
    """モデルファイルが無ければダウンロードして path に保存する(exe版は同梱済みなので行わない)。
    失敗しても例外は出さず、後のFileNotFoundErrorで手動ダウンロードの案内を出す。"""
    if os.path.exists(path) or getattr(sys, "frozen", False):
        return
    print(f"モデルファイルをダウンロードしています: {os.path.basename(path)}")
    tmp = path + ".download"
    try:
        import urllib.request
        urllib.request.urlretrieve(url, tmp)
        os.replace(tmp, path)
    except Exception as e:
        print("ダウンロードに失敗しました:", e)
        try:
            os.remove(tmp)
        except OSError:
            pass

# 手の21ランドマーク間の接続トポロジー(MediaPipe Hand標準の骨格構造)
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
        self.left_state = HandState()
        self.right_state = HandState()
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
    thumb, index = pts[4], pts[8]
    mid = ((thumb[0] + index[0]) // 2, (thumb[1] + index[1]) // 2)
    cv2.line(frame, thumb, index, (0, 0, 255) if pinched else (200, 200, 200), 2, cv2.LINE_AA)
    if pinched:
        cv2.circle(frame, mid, 10, (0, 0, 255), 2, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# 姿勢推定 (MediaPipe Tasks API - PoseLandmarker)
# ---------------------------------------------------------------------------
POSE_MODEL_PATH = resolve_model_path("pose_landmarker_lite.task")

POSE_L_SHOULDER, POSE_R_SHOULDER = 11, 12
POSE_L_ELBOW, POSE_R_ELBOW = 13, 14
POSE_L_HIP, POSE_R_HIP = 23, 24
POSE_L_KNEE, POSE_R_KNEE = 25, 26
POSE_L_ANKLE, POSE_R_ANKLE = 27, 28
POSE_L_WRIST, POSE_R_WRIST = 15, 16


def _to_vec(lm):
    return np.array([lm.x, lm.y, lm.z], dtype=float)


def _normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v


def compute_body_frame(world_landmarks):
    """体幹(肩・股関節)のランドマークから、体に対する下方向・前方向・左右方向の
    正規直交基底ベクトルを求める。"""
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
        a_lat_signed = a_lat if side == "right" else -a_lat

        flexion = math.degrees(math.atan2(a_fwd, a_down))
        abduction = math.degrees(math.atan2(a_lat_signed, a_down))
        results[side] = (flexion, abduction)
    return results


class PoseController:
    """PoseLandmarker(Tasks API, VIDEOモード)"""

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


def draw_pose_overlay(frame, pose_landmarks, w, h, angles, texts):
    """肩-肘・肩-股関節・股関節-膝-足首のラインと、屈曲/外転角度のラベルを描画する。"""
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
            texts.add(f"屈曲{l_flex:.0f}° 外転{l_abd:.0f}°", (lx - 170, ly - 15), 20, (255, 180, 0))
        if r_flex is not None:
            rx, ry = pts[POSE_R_SHOULDER]
            texts.add(f"屈曲{r_flex:.0f}° 外転{r_abd:.0f}°", (rx + 15, ry - 15), 20, (0, 180, 255))


# ---------------------------------------------------------------------------
# 全身ジェスチャー操作 : 右/左ステップで横移動、ハーフスクワットで回転、
#                        万歳(両手を上げて下ろす)でハードドロップ、
#                        ジャンプでゲームスタート、Tポーズでキャリブレーション
# ---------------------------------------------------------------------------
STEP_OUT_THRESH = 0.035     # 足の左右オフセットが基準よりこれだけ離れたら「ステップ」とみなす(画面幅比)
STEP_RESET_THRESH = 0.018   # これより基準へ戻ったら「足を揃えた」とみなす(次のステップの準備完了)
SQUAT_DOWN_THRESH = 0.030   # 股関節の高さが基準よりこれだけ下がったら「しゃがんだ」とみなす(画面高さ比)
SQUAT_UP_THRESH = 0.012
BANZAI_RAISE_MARGIN = 0.12  # 両手首が肩よりこれだけ上に来たら「万歳」とみなす(画面高さ比)
BANZAI_LOWER_MARGIN = 0.04  # 両手首が肩に近いこの範囲まで戻ったら「下ろした」とみなす
BASELINE_EMA_ALPHA = 0.01   # 基準姿勢(直立)を緩やかに追従させる係数
CALIBRATION_FRAMES = 30     # 基準姿勢の平均を取るフレーム数(30fps換算で約1秒)
# ジャンプ(ゲームスタート用): 両足首が基準より JUMP_RISE_THRESH 以上上がり、
# JUMP_MAX_AIR_SEC 以内に JUMP_LAND_THRESH 未満まで戻った(着地した)瞬間に発火する。
# 着地まで待つのは、カメラから遠ざかる動き(足首が画面上で上へ動く)をジャンプと
# 誤認しないため(遠ざかった場合は元の高さに戻らない)。
JUMP_RISE_THRESH = 0.030    # 画面高さ比
JUMP_LAND_THRESH = 0.012
JUMP_MAX_AIR_SEC = 1.0
# Tポーズ(両足を揃えて両手を横に伸ばす)をTPOSE_HOLD_SEC秒続けるとキャリブレーション
TPOSE_HOLD_SEC = 1.0
TPOSE_ARM_Y_TOL = 0.25      # 手首・肘と肩の高さの差の許容(肩〜股関節の長さに対する比)
TPOSE_REACH_RATIO = 1.5     # 手首が肩の中心から「肩幅×この倍率」以上横に離れていること
TPOSE_FEET_RATIO = 1.2      # 足首の間隔が「股関節の間隔×この倍率」以下なら足を揃えたとみなす
TPOSE_MIN_VISIBILITY = 0.5  # 手首・足首などがこの可視度未満なら判定しない


def _visible(p):
    v = getattr(p, "visibility", None)
    return v is None or v >= TPOSE_MIN_VISIBILITY


class BodyGestureController:
    """PoseLandmarkerの結果(画像正規化座標)から各ジェスチャーを検出する。

    ・右/左ステップ: 一度踏み出して足を揃えるたびに1回。踏み出したままでは連続しない。
    ・ハーフスクワット: しゃがみ始めで1回「回転」。
    ・万歳: 両手を肩より高く上げた時点で arm_raise(上肢挙上の回数用)、
      肩付近まで下ろした瞬間に hard_drop。
    ・ジャンプ: 着地した瞬間に jump(ゲームスタート用。プレイ中の操作には使わない)。
    ・Tポーズ: 両足を揃えて両手を横に伸ばした姿勢を1秒続けると tpose_trigger を出し、
      基準姿勢を取り直す。腕を下ろすまでは再発火しない。

    キャリブレーション(起動直後・recalibrate()後のCALIBRATION_FRAMESフレーム)の間は、
    直立・足を揃えた姿勢の平均を基準として求め、ステップ等の判定を行わない。
    """

    def __init__(self):
        self.baseline_hip_y = None
        self.baseline_left_x = None
        self.baseline_right_x = None
        self.baseline_pose_l_ankle_y = None
        self.baseline_pose_r_ankle_y = None
        self.screen_left_is_pose_left = None  # True: MediaPipeのLEFT_ANKLEが画面左側
        self.step_state = "neutral"   # "neutral" / "right_out" / "left_out"
        self.squat_state = "up"       # "up" / "down"
        self.banzai_state = "down"    # "down" / "raised"
        self.jump_state = "ground"    # "ground" / "air"
        self._jump_t = 0.0
        self._tpose_since = None
        self._tpose_armed = True
        self.calibrated = False
        self._calib_buffer = []
        # デバッグ表示用: 直近フレームの実測値
        self.debug = {"right_delta": 0.0, "left_delta": 0.0, "hip_drop": 0.0,
                      "jump_rise": 0.0, "wrist_above": 0.0}

    @staticmethod
    def empty_events():
        return {"step_right": False, "step_left": False, "squat": False, "hard_drop": False,
                "arm_raise": False, "jump": False, "tpose_trigger": False, "tpose_progress": 0.0}

    def recalibrate(self):
        """基準姿勢(直立・足を揃えた状態)を取り直す。"""
        self.calibrated = False
        self._calib_buffer = []
        self.baseline_hip_y = None
        self.baseline_left_x = None
        self.baseline_right_x = None
        self.baseline_pose_l_ankle_y = None
        self.baseline_pose_r_ankle_y = None
        self.screen_left_is_pose_left = None
        self.jump_state = "ground"

    def _is_tpose(self, lm):
        needed = (POSE_L_SHOULDER, POSE_R_SHOULDER, POSE_L_ELBOW, POSE_R_ELBOW, POSE_L_WRIST, POSE_R_WRIST,
                  POSE_L_HIP, POSE_R_HIP, POSE_L_ANKLE, POSE_R_ANKLE)
        if not all(_visible(lm[i]) for i in needed):
            return False
        mid_sh_x = (lm[POSE_L_SHOULDER].x + lm[POSE_R_SHOULDER].x) / 2
        mid_sh_y = (lm[POSE_L_SHOULDER].y + lm[POSE_R_SHOULDER].y) / 2
        mid_hip_y = (lm[POSE_L_HIP].y + lm[POSE_R_HIP].y) / 2
        sh_w = abs(lm[POSE_L_SHOULDER].x - lm[POSE_R_SHOULDER].x)
        hip_w = abs(lm[POSE_L_HIP].x - lm[POSE_R_HIP].x)
        torso = abs(mid_hip_y - mid_sh_y)
        if sh_w < 1e-3 or hip_w < 1e-3 or torso < 1e-3:
            return False
        tol = TPOSE_ARM_Y_TOL * torso
        for idx in (POSE_L_WRIST, POSE_R_WRIST, POSE_L_ELBOW, POSE_R_ELBOW):
            if abs(lm[idx].y - mid_sh_y) > tol:
                return False
        lw = lm[POSE_L_WRIST].x - mid_sh_x
        rw = lm[POSE_R_WRIST].x - mid_sh_x
        if lw * rw >= 0:  # 両手首が体の左右反対側にあること
            return False
        if min(abs(lw), abs(rw)) < TPOSE_REACH_RATIO * sh_w:
            return False
        feet = abs(lm[POSE_L_ANKLE].x - lm[POSE_R_ANKLE].x)
        return feet <= TPOSE_FEET_RATIO * hip_w

    def _update_tpose(self, lm, now, events):
        if self._is_tpose(lm):
            if self._tpose_armed:
                if self._tpose_since is None:
                    self._tpose_since = now
                progress = (now - self._tpose_since) / TPOSE_HOLD_SEC
                events["tpose_progress"] = min(1.0, progress)
                if progress >= 1.0:
                    events["tpose_trigger"] = True
                    self._tpose_armed = False
                    self._tpose_since = None
                    self.recalibrate()
        else:
            self._tpose_since = None
            self._tpose_armed = True

    def update(self, pose_landmarks):
        events = self.empty_events()
        if pose_landmarks is None:
            return events

        lm = pose_landmarks
        now = time.time()
        self._update_tpose(lm, now, events)

        mid_hip_y = (lm[POSE_L_HIP].y + lm[POSE_R_HIP].y) / 2
        pose_left_ankle_x = lm[POSE_L_ANKLE].x
        pose_right_ankle_x = lm[POSE_R_ANKLE].x
        pose_l_ankle_y = lm[POSE_L_ANKLE].y
        pose_r_ankle_y = lm[POSE_R_ANKLE].y

        if not self.calibrated:
            # 直立・足を揃えた状態を数十フレーム分平均して基準とする。
            # 画面上のどちら側がMediaPipeのLEFT_ANKLEかはここで一度だけ確定し、
            # 以降はフレームごとに判定し直さない(足を揃えた付近で左右が入れ替わり、
            # 片方の足の動きがもう片方の動きとして誤カウントされるのを防ぐため)。
            self._calib_buffer.append((mid_hip_y, pose_left_ankle_x, pose_right_ankle_x,
                                       pose_l_ankle_y, pose_r_ankle_y))
            if len(self._calib_buffer) >= CALIBRATION_FRAMES:
                n = len(self._calib_buffer)
                avg = [sum(v[i] for v in self._calib_buffer) / n for i in range(5)]
                self.screen_left_is_pose_left = avg[1] <= avg[2]
                self.baseline_hip_y = avg[0]
                if self.screen_left_is_pose_left:
                    self.baseline_left_x, self.baseline_right_x = avg[1], avg[2]
                else:
                    self.baseline_left_x, self.baseline_right_x = avg[2], avg[1]
                self.baseline_pose_l_ankle_y = avg[3]
                self.baseline_pose_r_ankle_y = avg[4]
                self.jump_state = "ground"
                self.calibrated = True
            return events  # キャリブレーション中はジェスチャー判定を行わない

        # キャリブレーション時に固定した対応関係で、画面上の左足/右足のx座標を得る。
        # 各足自身の基準位置からの絶対移動量を使う(体幹の重心移動の影響を避けるため)。
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
        self.baseline_pose_l_ankle_y += (pose_l_ankle_y - self.baseline_pose_l_ankle_y) * a
        self.baseline_pose_r_ankle_y += (pose_r_ankle_y - self.baseline_pose_r_ankle_y) * a

        # --- 右ステップ / 左ステップ ---
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

        # --- ジャンプ(両足首が上がって、短時間で元の高さに戻ったら着地=発火) ---
        rise = min(self.baseline_pose_l_ankle_y - pose_l_ankle_y,
                   self.baseline_pose_r_ankle_y - pose_r_ankle_y)  # 正の値: 両足首とも基準より上
        self.debug["jump_rise"] = rise
        if self.jump_state == "ground":
            if rise > JUMP_RISE_THRESH:
                self.jump_state = "air"
                self._jump_t = now
        elif rise < JUMP_LAND_THRESH:
            if now - self._jump_t <= JUMP_MAX_AIR_SEC:
                events["jump"] = True
            self.jump_state = "ground"

        # --- 万歳して下ろす動作でハードドロップ ---
        mid_shoulder_y = (lm[POSE_L_SHOULDER].y + lm[POSE_R_SHOULDER].y) / 2
        l_wrist_above = mid_shoulder_y - lm[POSE_L_WRIST].y  # 正の値: 手首が肩より上
        r_wrist_above = mid_shoulder_y - lm[POSE_R_WRIST].y
        self.debug["wrist_above"] = min(l_wrist_above, r_wrist_above)
        both_raised = l_wrist_above > BANZAI_RAISE_MARGIN and r_wrist_above > BANZAI_RAISE_MARGIN
        both_lowered = l_wrist_above < BANZAI_LOWER_MARGIN and r_wrist_above < BANZAI_LOWER_MARGIN

        if self.banzai_state == "down" and both_raised:
            self.banzai_state = "raised"
            events["arm_raise"] = True
        elif self.banzai_state == "raised" and both_lowered:
            events["hard_drop"] = True
            self.banzai_state = "down"

        return events


# ---------------------------------------------------------------------------
# 運動の記録(リハ効果指標)
# ---------------------------------------------------------------------------
class ExerciseStats:
    """プレイ中(一時停止中を除く)の運動量を数える。
    ・ステップ数(右/左)、スクワット数、上肢挙上数(両手を肩より上へ上げた回数)
    ・肩の最大屈曲/外転角度(直近5フレームの中央値の最大。単発のノイズを除くため)
    ・プレイ時間"""
    KEYS = ("step_right", "step_left", "squat", "arm_raise")

    def __init__(self):
        self.reset()

    def reset(self):
        self.counts = {k: 0 for k in self.KEYS}
        self.flash_until = {k: 0.0 for k in self.KEYS}
        self.play_sec = 0.0
        self.max_flex = {"left": None, "right": None}
        self.max_abd = {"left": None, "right": None}
        self._hist = {(s, i): deque(maxlen=5) for s in ("left", "right") for i in (0, 1)}

    def add_events(self, events, now):
        for k in self.KEYS:
            if events.get(k):
                self.counts[k] += 1
                self.flash_until[k] = now + 0.5

    def add_angles(self, angles):
        if not angles:
            return
        for side in ("left", "right"):
            for i, v in enumerate(angles[side]):
                if v is None:
                    continue
                d = self._hist[(side, i)]
                d.append(v)
                if len(d) < d.maxlen:
                    continue
                med = sorted(d)[len(d) // 2]
                target = self.max_flex if i == 0 else self.max_abd
                if target[side] is None or med > target[side]:
                    target[side] = med


def fmt_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def fmt_angle(v):
    return "--" if v is None else f"{v:.0f}°"


# ---------------------------------------------------------------------------
# 演出(パーティクル・桜吹雪・花火・ポップアップ文字・画面の揺れ)
# ---------------------------------------------------------------------------
SAKURA_COLORS = [(203, 192, 255), (193, 182, 255), (180, 105, 255), (225, 215, 255), (147, 112, 219)]
FIREWORK_COLORS = [(0, 220, 255), (255, 120, 255), (120, 255, 120), (255, 255, 120), (80, 160, 255), (255, 255, 255)]
MAX_PARTICLES = 1500


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity", "kind",
                 "angle", "spin", "phase", "drag")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0, kind="spark", drag=1.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.gravity, self.kind, self.drag = color, size, gravity, kind, drag
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-180, 180)
        self.phase = random.uniform(0, 6.28)


class Effects:
    def __init__(self):
        self.clear()

    def clear(self):
        self.particles = []
        self.popups = []
        self.shake_amp = 0.0
        self.shake_dur = 1.0
        self.shake_until = 0.0
        self.sakura_rate = 0.0       # 1秒あたりの花びらの数
        self._sakura_acc = 0.0
        self.firework_until = 0.0
        self._next_firework = 0.0
        self.scale = 1.0

    def shake(self, amp, dur, now):
        if now + dur >= self.shake_until or amp > self.shake_amp:
            self.shake_amp, self.shake_dur, self.shake_until = amp, dur, now + dur

    def shake_offset(self, now):
        if now >= self.shake_until:
            return 0, 0
        a = self.shake_amp * (self.shake_until - now) / self.shake_dur
        return int(random.uniform(-a, a)), int(random.uniform(-a, a))

    def burst(self, x, y, color, n, speed, life, size, gravity=0.0, kind="spark", up_bias=0.0, drag=1.0):
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            sp = random.uniform(0.3, 1.0) * speed
            c = random.choice(color) if isinstance(color, list) else color
            self.particles.append(Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp - up_bias,
                                           life * random.uniform(0.7, 1.0), c,
                                           size * random.uniform(0.7, 1.2), gravity, kind, drag))

    def popup(self, text, x, y, size, color, dur=1.0, rise=50.0, stroke=4, stroke_color=(0, 0, 0)):
        self.popups.append((text, x, y, size, color, time.time(), dur, rise, stroke, stroke_color))

    def update(self, dt, now, w, h, scale):
        self.scale = scale
        # 桜吹雪の花びらを補充
        if self.sakura_rate > 0:
            self._sakura_acc += self.sakura_rate * dt
            while self._sakura_acc >= 1:
                self._sakura_acc -= 1
                self.particles.append(Particle(
                    random.uniform(-0.2 * w, w), random.uniform(-40, -10) * scale,
                    random.uniform(30, 90) * scale, random.uniform(70, 150) * scale,
                    30.0, random.choice(SAKURA_COLORS), random.uniform(9, 17) * scale, 0.0, "petal"))
        # 花火
        if now < self.firework_until and now >= self._next_firework:
            self._next_firework = now + random.uniform(0.4, 0.9)
            fx_x, fx_y = random.uniform(0.15, 0.85) * w, random.uniform(0.12, 0.45) * h
            self.burst(fx_x, fx_y, random.choice(FIREWORK_COLORS), 90, 380 * scale, 1.3, 4 * scale,
                       gravity=180 * scale, drag=0.97)
            SE_FIREWORK.play()

        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            if p.drag != 1.0:
                k = p.drag ** (dt * 60)
                p.vx *= k
                p.vy *= k
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.kind == "petal":
                p.x += math.sin(p.phase) * 40 * scale * dt
                p.phase += dt * 2.5
                p.angle += p.spin * dt
                if p.y > h + 40 * scale:
                    continue
            alive.append(p)
        self.particles = alive[-MAX_PARTICLES:]
        self.popups = [p for p in self.popups if now - p[5] <= p[6]]

    def draw(self, frame):
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if p.kind == "petal":
                a = max(2, int(p.size))
                b = max(1, int(p.size * 0.55 * abs(math.cos(p.phase * 1.3))) + 1)  # ひらひら裏返る
                cv2.ellipse(frame, (x, y), (a, b), p.angle, 0, 360, p.color, -1, cv2.LINE_AA)
            elif p.kind == "square":
                s = max(1, int(p.size * (0.4 + 0.6 * p.life / p.max_life)))
                cv2.rectangle(frame, (x - s, y - s), (x + s, y + s), p.color, -1)
            else:
                r = max(1, int(p.size * p.life / p.max_life))
                cv2.circle(frame, (x, y), r, p.color, -1, cv2.LINE_AA)

    def add_texts(self, texts, now):
        for text, x, y, size, color, t0, dur, rise, stroke, stroke_color in self.popups:
            age = now - t0
            if age > dur - 0.25 and int(age * 16) % 2:  # 消える直前は点滅
                continue
            s = size * (1 + 0.6 * max(0.0, 1 - age / 0.12))  # 出現時にポンと大きく
            texts.add(text, (x, y - rise * age / dur), s, color, "center", "middle",
                      stroke=stroke, stroke_color=stroke_color, bold=True)


def handle_game_events(game, fx, board_x, board_y, now, S):
    """TetrisGameのイベントを効果音・演出に変換する"""
    cx = board_x + BOARD_W * CELL / 2
    bh = BOARD_H * CELL
    for ev in game.pop_events():
        t = ev["type"]
        if t == "lock":
            SE_LOCK.play()
        elif t == "hard_drop":
            SE_HARDDROP.play()
            fx.shake(6 * S, 0.15, now)
            for (r, c) in ev["cells"]:
                if r >= 0:
                    fx.burst(board_x + c * CELL + CELL / 2, board_y + (r + 1) * CELL, (230, 230, 230),
                             4, 220 * S, 0.35, 4 * S, gravity=400 * S, up_bias=120 * S)
        elif t == "clear_start":
            n = len(ev["rows"])
            SE_CLEAR[min(4, n)].play()
            for r in ev["rows"]:
                for c, color in enumerate(ev["colors"][r]):
                    fx.burst(board_x + c * CELL + CELL / 2, board_y + r * CELL + CELL / 2,
                             color or (255, 255, 255), 3, 420 * S, 0.9, CELL * 0.22,
                             gravity=900 * S, kind="square", up_bias=250 * S)
            name, color, size = {1: ("SINGLE!", (255, 255, 255), 56), 2: ("DOUBLE!", (120, 255, 120), 62),
                                 3: ("TRIPLE!", (255, 200, 80), 70)}.get(n, ("TETRIS!!", (0, 220, 255), 90))
            fx.popup(name, cx, board_y + bh * 0.30, size * S, color, dur=1.1, rise=40 * S, stroke=5)
            if n >= 4:
                fx.shake(16 * S, 0.45, now)
                fx.burst(cx, board_y + ev["rows"][0] * CELL, FIREWORK_COLORS, 120, 700 * S, 1.0, 5 * S,
                         gravity=300 * S, drag=0.96)
            elif n >= 2:
                fx.shake(7 * S, 0.2, now)
        elif t == "clear":
            fx.popup(f"+{ev['points']:,}", cx, board_y + bh * 0.42, 46 * S, (0, 255, 255), dur=1.2, rise=60 * S)
            if ev["chain"] >= 2:
                SE_CHAIN[min(10, ev["chain"])].play()
                fx.popup(f"{ev['chain']}連鎖!", cx, board_y + bh * 0.18,
                         (64 + min(ev["chain"], 6) * 6) * S, (80, 160, 255), dur=1.3, rise=30 * S, stroke=6)
                fx.burst(cx, board_y + bh * 0.18, [(80, 160, 255), (0, 255, 255)], 40, 400 * S, 0.8, 4 * S,
                         gravity=200 * S)
            if ev["level_up"]:
                SE_LEVELUP.play()
                fx.popup(f"LEVEL UP!  Lv{ev['level']}", cx, board_y + bh * 0.55, 54 * S, (255, 255, 0),
                         dur=1.6, rise=30 * S, stroke=5)
        elif t == "game_over":
            SE_GAMEOVER.play()


# ---------------------------------------------------------------------------
# 盤面のAR風オーバーレイ描画
# ---------------------------------------------------------------------------
def _brighten(color):
    return tuple(min(255, int(v * 0.5 + 128)) for v in color)


def draw_board_overlay(frame, game: TetrisGame, board_x, board_y, show_piece=True, show_next=True,
                       danger=0, now=None):
    now = time.time() if now is None else now
    fh, fw = frame.shape[:2]
    board_w_px = BOARD_W * CELL
    board_h_px = BOARD_H * CELL

    # 盤面の周りだけを切り出して半透明合成する(全画面コピーより軽い)
    x0, y0 = max(0, board_x - 6), max(0, board_y - 6)
    x1, y1 = min(fw, board_x + board_w_px + 7), min(fh, board_y + board_h_px + 7)
    if x1 > x0 and y1 > y0:
        roi = frame[y0:y1, x0:x1]
        overlay = roi.copy()
        bx, by = board_x - x0, board_y - y0
        cv2.rectangle(overlay, (bx, by), (bx + board_w_px, by + board_h_px), (20, 20, 20), -1)

        clearing = set(game.clearing_rows)
        prog = game.clear_progress(now)
        gray_rows = 0
        if game.game_over and game.game_over_time is not None:
            gray_rows = int(BOARD_H * min(1.0, (now - game.game_over_time) / GAMEOVER_FILL_SEC))
        flash_on = int(now * 24) % 2 == 0
        center = (BOARD_W - 1) / 2

        for r in range(BOARD_H):
            for c in range(BOARD_W):
                if gray_rows and r >= BOARD_H - gray_rows:
                    _draw_cell(overlay, bx, by, r, c, (110, 110, 110))  # ゲームオーバー: 下から灰色で埋める
                    continue
                color = game.grid[r][c]
                if color is None:
                    continue
                if r in clearing:
                    if abs(c - center) / (BOARD_W / 2) < prog:
                        continue  # 消える行は中央から外側へ消えていく
                    color = (255, 255, 255) if flash_on else _brighten(color)
                _draw_cell(overlay, bx, by, r, c, color)

        if show_piece and not game.game_over and not clearing:
            ghost_r = game.ghost_row()
            for (r, c) in game.current.occupied(row_off=(ghost_r - game.current.row)):
                if r >= 0:
                    _draw_cell(overlay, bx, by, r, c, game.current.color, ghost=True)
            for (r, c) in game.current.occupied():
                if r >= 0:
                    _draw_cell(overlay, bx, by, r, c, game.current.color)

        for c in range(BOARD_W + 1):
            x = bx + c * CELL
            cv2.line(overlay, (x, by), (x, by + board_h_px), (70, 70, 70), 1)
        for r in range(BOARD_H + 1):
            y = by + r * CELL
            cv2.line(overlay, (bx, y), (bx + board_w_px, y), (70, 70, 70), 1)

        alpha = 0.72
        frame[y0:y1, x0:x1] = cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0)

    # 枠線(ピンチ時は黄色/赤で脈打つ)
    if danger >= 1:
        freq = 2.0 if danger >= 2 else 1.2
        pulse = 0.5 + 0.5 * math.sin(now * 2 * math.pi * freq)
        color = (0, 0, 255) if danger >= 2 else (0, 220, 255)
        thick = int(3 + 6 * pulse)
    else:
        color, thick = (255, 255, 255), 2
    cv2.rectangle(frame, (board_x, board_y), (board_x + board_w_px, board_y + board_h_px), color, thick)

    next_x = board_x + board_w_px + 20
    next_y = board_y
    if show_next:
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
# 画面(タイトル・HUD・カウントダウン・リザルト)
# ---------------------------------------------------------------------------
COUNTDOWN_SEC = 3.0
COUNTDOWN_START_SHOW = 0.7   # 「START!」を見せる時間
DANGER1_HEIGHT = 12          # 積み上がりがこの行数以上: ピンチ1(BGM少し速く・黄色の警告・心音)
DANGER2_HEIGHT = 15          # この行数以上: ピンチ2(BGMさらに速く・赤の警告・速い心音)
HEARTBEAT_INTERVAL = {1: 0.85, 2: 0.55}

# リザルト画面の進行(ゲームオーバーからの経過秒)
RESULT_PANEL_T = 1.4
RESULT_ITEM_T0 = 1.7
RESULT_ITEM_DT = 0.3
RESULT_COUNT_T0 = 3.0
RESULT_COUNT_DUR = 2.0
RESULT_RANK_T = 5.3
RESULT_RECORD_T = 5.8
RESULT_RETRY_T = 6.3         # これ以降、ジャンプで再スタートできる
RESULT_SKEY_SEC = 1.0        # これ以降、Sキーで再スタートできる(結果発表の途中でも可)

# ランクとゲーム終了時の演出(スコアのしきい値は仮。実際のプレイで調整する)
RANK_TABLE = [
    {"rank": "S", "min": 3000, "color": (0, 215, 255), "msg": "すばらしい!!", "sakura": 80, "fireworks": 8.0,
     "sounds": (SE_FANFARE_BIG, SE_CHEER)},
    {"rank": "A", "min": 1500, "color": (80, 80, 255), "msg": "おみごと!", "sakura": 50, "fireworks": 0.0,
     "sounds": (SE_FANFARE, SE_CHEER)},
    {"rank": "B", "min": 600, "color": (80, 220, 80), "msg": "ナイス!", "sakura": 20, "fireworks": 0.0,
     "sounds": (SE_FANFARE, SE_APPLAUSE)},
    {"rank": "C", "min": 200, "color": (255, 200, 80), "msg": "いい調子!", "sakura": 6, "fireworks": 0.0,
     "sounds": (SE_JINGLE, SE_APPLAUSE)},
    {"rank": "D", "min": 0, "color": (200, 200, 200), "msg": "ドンマイ! もう一度!", "sakura": 0, "fireworks": 0.0,
     "sounds": (SE_DONMAI,)},
]


def score_rank(score):
    for info in RANK_TABLE:
        if score >= info["min"]:
            return info
    return RANK_TABLE[-1]


def _ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def draw_title_screen(frame, texts, now, cx, w, h, S, body_ctrl, pose_visible, best_score):
    y = h * 0.16
    texts.add("モーションテトリス", (cx, y), 100 * S, (0, 220, 255), "center", "middle",
              stroke=7 * S + 1, stroke_color=(90, 20, 140), bold=True)
    texts.add("体を動かしてブロックを操作しよう!", (cx, y + 95 * S), 36 * S, (255, 255, 255), "center", "middle",
              stroke=3)

    bw = min(820 * S, cx * 2 - 40)
    bx0, by0, bh = cx - bw / 2, y + 150 * S, 290 * S
    shade_rect(frame, bx0, by0, bx0 + bw, by0 + bh, 0.55)
    rows = [("右ステップ", "1マス右へ"), ("左ステップ", "1マス左へ"),
            ("ハーフスクワット", "回転"), ("万歳して下ろす", "一気に落下")]
    for i, (a, b) in enumerate(rows):
        ly = by0 + 30 * S + i * 62 * S
        texts.add(a, (bx0 + 40 * S, ly), 36 * S, (180, 230, 255), stroke=2)
        texts.add("→ " + b, (bx0 + bw * 0.55, ly), 36 * S, (255, 255, 255), stroke=2)

    sy = by0 + bh + 40 * S
    if not pose_visible:
        msg, col = "カメラに全身(足首〜万歳した手)が映る位置に立ってください", (0, 200, 255)
    elif not body_ctrl.calibrated:
        msg, col = "キャリブレーション中... 直立して足を揃えたまま静止してください", (0, 255, 255)
    else:
        msg, col = "基準姿勢 OK!  取り直し: 足を揃えて両手を横に伸ばし1秒キープ(Cキーでも可)", (120, 255, 120)
    texts.add(msg, (cx, sy), 28 * S, col, "center", "middle", stroke=2)
    if int(now * 2.5) % 2 == 0:
        texts.add("ジャンプ または Sキーで スタート!", (cx, sy + 85 * S), 56 * S, (80, 255, 255), "center", "middle",
                  stroke=5 * S + 1, stroke_color=(0, 0, 160), bold=True)
    if best_score > 0:
        texts.add(f"本日のハイスコア: {best_score:,}", (cx, sy + 155 * S), 30 * S, (200, 220, 255),
                  "center", "middle", stroke=2)
    texts.add(f"Ver {VERSION}    Q / Esc / ×: 終了", (cx, h - 40 * S), 22 * S, (200, 200, 200), "center", "middle", stroke=2)


def draw_exercise_panel(frame, texts, stats, x, y, S, now):
    """プレイ中の画面左に出す「運動の記録」パネル"""
    lh = 34 * S
    rows = [
        ("step", f"ステップ  右 {stats.counts['step_right']} / 左 {stats.counts['step_left']}",
         max(stats.flash_until["step_right"], stats.flash_until["step_left"])),
        ("squat", f"スクワット  {stats.counts['squat']} 回", stats.flash_until["squat"]),
        ("arm", f"上肢挙上(万歳)  {stats.counts['arm_raise']} 回", stats.flash_until["arm_raise"]),
        ("flex", f"肩 最大屈曲  左 {fmt_angle(stats.max_flex['left'])}  右 {fmt_angle(stats.max_flex['right'])}", 0),
        ("abd", f"肩 最大外転  左 {fmt_angle(stats.max_abd['left'])}  右 {fmt_angle(stats.max_abd['right'])}", 0),
        ("time", f"プレイ時間  {fmt_time(stats.play_sec)}", 0),
    ]
    shade_rect(frame, x - 10 * S, y - 8 * S, x + 440 * S, y + 46 * S + lh * len(rows), 0.5)
    texts.add("運動の記録", (x, y), 26 * S, (120, 255, 200), stroke=2, bold=True)
    for i, (_, text, flash) in enumerate(rows):
        col = (0, 255, 255) if now < flash else (240, 240, 240)
        texts.add(text, (x, y + 42 * S + i * lh), 24 * S, col, stroke=2)


def draw_play_hud(frame, texts, game, stats, display_score, best_score, angles, body_ctrl, h, S, now):
    texts.add(f"スコア: {int(round(display_score)):,}", (20 * S, 20 * S), 26 * S, (255, 255, 255), stroke=2)
    texts.add(f"ライン: {game.lines}  レベル: {game.level}  ハイスコア: {max(best_score, game.score):,}",
              (20 * S, 55 * S), 22 * S, (200, 200, 200), stroke=2)
    if angles is not None:
        l_flex, l_abd = angles["left"]
        r_flex, r_abd = angles["right"]
        l_txt = f"屈曲{l_flex:.0f}°/外転{l_abd:.0f}°" if l_flex is not None else "--"
        r_txt = f"屈曲{r_flex:.0f}°/外転{r_abd:.0f}°" if r_flex is not None else "--"
    else:
        l_txt = r_txt = "--"
    texts.add(f"肩関節 外転屈曲角度  左: {l_txt}   右: {r_txt}", (20 * S, 88 * S), 22 * S, (0, 220, 180), stroke=2)

    # デバッグ用: 判定の実測値としきい値(調整の目安に)
    dbg = body_ctrl.debug
    texts.add(f"[debug] 右足Δ={dbg['right_delta']:+.3f}(閾値{STEP_OUT_THRESH:.3f}) "
              f"左足Δ={dbg['left_delta']:+.3f}(閾値{STEP_OUT_THRESH:.3f}) "
              f"腰の下がりΔ={dbg['hip_drop']:+.3f}(閾値{SQUAT_DOWN_THRESH:.3f}) "
              f"手首-肩Δ={dbg['wrist_above']:+.3f}(閾値{BANZAI_RAISE_MARGIN:.3f}) "
              f"ジャンプΔ={dbg['jump_rise']:+.3f}(閾値{JUMP_RISE_THRESH:.3f})",
              (20 * S, 114 * S), 16 * S, (150, 150, 150))

    draw_exercise_panel(frame, texts, stats, 24 * S, 160 * S, S, now)

    texts.add("右ステップ=右移動 / 左ステップ=左移動 / ハーフスクワット=回転 / 万歳→下ろす=即落下",
              (20 * S, h - 65 * S), 20 * S, (180, 220, 255), stroke=2)
    texts.add("基準姿勢の取り直し: 足を揃えて両手を横に伸ばす(1秒) または Cキー   P: 一時停止",
              (20 * S, h - 35 * S), 18 * S, (150, 200, 150), stroke=2)


def update_result(result, game, fx, el, now):
    """リザルト画面の進行に合わせて効果音・演出を一度ずつ発火させる"""
    fired = result["fired"]

    def once(name, t):
        if el >= t and name not in fired:
            fired.add(name)
            return True
        return False

    for i in range(4):
        if once(f"item{i}", RESULT_ITEM_T0 + i * RESULT_ITEM_DT):
            SE_BLIP.play()
    if (game.score > 0 and RESULT_COUNT_T0 <= el < RESULT_COUNT_T0 + RESULT_COUNT_DUR
            and now - result["last_tick"] >= 0.07):
        SE_TICK.play()
        result["last_tick"] = now
    if once("rank", RESULT_RANK_T):
        info = result["rank"]
        SE_STAMP.play()
        for snd in info["sounds"]:
            snd.play()
        fx.sakura_rate = info["sakura"]
        if info["fireworks"] > 0:
            fx.firework_until = now + info["fireworks"]
            fx._next_firework = now
    if result["new_record"] and once("record", RESULT_RECORD_T):
        SE_NEWRECORD.play()


def draw_result_screen(frame, texts, game, stats, result, el, now, cx, w, h, S, board_x):
    # GAME OVER の文字が上から落ちてくる
    if el < RESULT_PANEL_T:
        p = _ease_out(el / 0.5)
        y = -100 * S + (h * 0.42 + 100 * S) * p
        texts.add("GAME OVER", (cx, y), 120 * S, (60, 60, 255), "center", "middle",
                  stroke=7 * S + 1, stroke_color=(255, 255, 255), bold=True)
        return

    pw = min(1150 * S, board_x - 30)
    ph = min(760 * S, h - 60 * S)
    px0 = max(10, cx - pw / 2)
    py0 = (h - ph) / 2
    shade_rect(frame, px0, py0, px0 + pw, py0 + ph, 0.68, (40, 20, 10))
    cv2.rectangle(frame, (int(px0), int(py0)), (int(px0 + pw), int(py0 + ph)), (0, 200, 255), max(2, int(3 * S)))

    texts.add("RESULT", (px0 + pw / 2, py0 + 45 * S), 58 * S, (0, 220, 255), "center", "middle",
              stroke=5 * S + 1, stroke_color=(90, 20, 140), bold=True)

    # 左列: ゲームの結果
    lx = px0 + 40 * S
    lvx = px0 + pw * 0.46
    items = [("消したライン", f"{game.lines}"), ("到達レベル", f"{game.level}"),
             ("最大連鎖", f"{game.max_chain}"), ("4ライン消し", f"{game.tetris_count}")]
    for i, (label, value) in enumerate(items):
        if el < RESULT_ITEM_T0 + i * RESULT_ITEM_DT:
            break
        iy = py0 + 115 * S + i * 50 * S
        texts.add(label, (lx, iy), 30 * S, (230, 230, 230), stroke=2)
        texts.add(value, (lvx, iy), 30 * S, (255, 255, 255), "right", stroke=2)

    if el >= RESULT_COUNT_T0:
        p = _ease_out((el - RESULT_COUNT_T0) / RESULT_COUNT_DUR)
        shown = int(round(game.score * p))
        texts.add("SCORE", (lx, py0 + 330 * S), 32 * S, (0, 220, 255), stroke=2, bold=True)
        texts.add(f"{shown:,}", (lx, py0 + 370 * S), 84 * S, (80, 255, 255), stroke=6 * S + 1,
                  stroke_color=(0, 0, 120), bold=True)

    info = result["rank"]
    if el >= RESULT_RANK_T:
        p = min(1.0, (el - RESULT_RANK_T) / 0.25)
        size = 150 * S * (1 + 2.0 * (1 - p))  # 大きい状態からドンと押される
        texts.add(info["rank"], (px0 + pw * 0.40, py0 + 400 * S), size, info["color"], "center", "middle",
                  stroke=8 * S + 1, stroke_color=(255, 255, 255), bold=True)
        texts.add(info["msg"], (lx, py0 + 500 * S), 40 * S, info["color"], stroke=4, bold=True)
    if result["new_record"] and el >= RESULT_RECORD_T and int(now * 4) % 2 == 0:
        texts.add("NEW RECORD!", (lx, py0 + 560 * S), 44 * S, (0, 255, 255), stroke=4,
                  stroke_color=(0, 0, 200), bold=True)

    # 右列: 運動の記録
    rx = px0 + pw * 0.54
    rvx = px0 + pw - 40 * S
    texts.add("運動の記録", (rx, py0 + 110 * S), 34 * S, (120, 255, 200), stroke=3, bold=True)
    rows = [
        ("プレイ時間", fmt_time(stats.play_sec)),
        ("ステップ", f"{stats.counts['step_right'] + stats.counts['step_left']} 歩"),
        ("  (右 / 左)", f"{stats.counts['step_right']} / {stats.counts['step_left']}"),
        ("スクワット", f"{stats.counts['squat']} 回"),
        ("上肢挙上(万歳)", f"{stats.counts['arm_raise']} 回"),
        ("肩 最大屈曲 左/右", f"{fmt_angle(stats.max_flex['left'])} / {fmt_angle(stats.max_flex['right'])}"),
        ("肩 最大外転 左/右", f"{fmt_angle(stats.max_abd['left'])} / {fmt_angle(stats.max_abd['right'])}"),
    ]
    for i, (label, value) in enumerate(rows):
        ry = py0 + 170 * S + i * 46 * S
        texts.add(label, (rx, ry), 27 * S, (230, 230, 230), stroke=2)
        texts.add(value, (rvx, ry), 27 * S, (255, 255, 255), "right", stroke=2)
    texts.add("※肩の角度はカメラからの推定値(参考値)", (rx, py0 + 170 * S + len(rows) * 46 * S), 20 * S,
              (180, 180, 180), stroke=1)

    if el >= RESULT_RETRY_T and int(now * 2.5) % 2 == 0:
        texts.add("ジャンプ または Sキーで もう一度!", (px0 + pw / 2, py0 + ph - 50 * S), 42 * S,
                  (80, 255, 255), "center", "middle", stroke=4, stroke_color=(0, 0, 160), bold=True)


# ---------------------------------------------------------------------------
# メインループ
# ---------------------------------------------------------------------------
def main():
    global CELL

    ensure_model(MODEL_PATH, HAND_MODEL_URL)
    ensure_model(POSE_MODEL_PATH, POSE_MODEL_URL)

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
    fx = Effects()
    stats = ExerciseStats()
    texts = TextLayer()

    state = "title"         # "title" / "countdown" / "playing" / "result"
    state_t0 = time.time()
    best_score = 0          # 起動中のハイスコア(保存はしない)
    result = None
    display_score = 0.0
    countdown_shown = -1
    heartbeat_next = 0.0
    danger = 0
    was_calibrated = False
    last_time = time.time()

    window_name = "Hand Tetris - 手でつかんでテトリス"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    window_shown = False  # 最初のimshow後にだけ「×」判定を行う(起動直後の誤判定防止)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # 鏡映しにしてセルフィー感覚に
        h, w = frame.shape[:2]
        now = time.time()
        dt = min(0.1, max(0.0, now - last_time))
        last_time = now
        S = h / 1080.0  # 画面の大きさに合わせた文字・演出の倍率
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ウィンドウの縦幅いっぱいを使うようセルサイズを毎フレーム再計算する。
        TOP_MARGIN = 140
        BOTTOM_MARGIN = 85
        available_h = max(BOARD_H * 10, h - TOP_MARGIN - BOTTOM_MARGIN)
        CELL = max(14, available_h // BOARD_H)
        board_w_px = BOARD_W * CELL
        board_h_px = BOARD_H * CELL
        board_y = TOP_MARGIN + max(0, (h - TOP_MARGIN - BOTTOM_MARGIN - board_h_px) // 2)
        next_box_w = 4 * CELL + 20
        board_x = max(10, w - board_w_px - next_box_w - 30)
        region_cx = board_x // 2                    # 盤面の左側の領域の中央(タイトル・リザルト用)
        board_cx = board_x + board_w_px // 2

        gesture = hand_ctrl.process(rgb)  # 手は視覚効果(ワイヤーフレーム表示)としてのみ使用
        pose_data = pose_ctrl.process(rgb)
        shoulder_angles_result = None
        body_events = BodyGestureController.empty_events()
        if pose_data is not None:
            shoulder_angles_result = shoulder_flexion_abduction(pose_data["world_landmarks"])
            body_events = body_ctrl.update(pose_data["landmarks"])

        key = cv2.waitKey(1) & 0xFF
        # ウィンドウ右上の「×」で閉じた場合も終了する
        if window_shown:
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
        start_requested = False
        if key == ord("q") or key == 27:  # Qキー または Escキーで終了
            break
        elif key == ord("s"):
            if state == "title" or (state == "result" and now - state_t0 >= RESULT_SKEY_SEC):
                start_requested = True
        elif key == ord("p"):
            if state == "playing":
                game.paused = not game.paused
        elif key == ord("c"):
            body_ctrl.recalibrate()
            SE_CALIB_START.play()

        # ジャンプでスタート(タイトル画面、またはリザルトの発表が終わった後)
        if body_events["jump"] and (state == "title" or (state == "result" and now - state_t0 >= RESULT_RETRY_T)):
            start_requested = True

        # Tポーズでキャリブレーション開始 → 完了時に合図
        if body_events["tpose_trigger"]:
            SE_CALIB_START.play()
        if body_ctrl.calibrated and not was_calibrated:
            SE_CALIB_OK.play()
            fx.popup("基準姿勢 OK!", (region_cx if state == "title" else w / 2), h * (0.88 if state == "title" else 0.30),
                     48 * S, (120, 255, 120), dur=1.2, rise=30 * S)
        was_calibrated = body_ctrl.calibrated

        if start_requested:
            game = TetrisGame()
            stats.reset()
            fx.clear()
            bgm.stop()
            state, state_t0 = "countdown", now
            countdown_shown = -1
            display_score = 0.0
            danger = 0
            result = None

        # --- 状態ごとの更新 ---
        if state == "countdown":
            el = now - state_t0
            idx = min(3, int(el))
            if idx != countdown_shown:
                countdown_shown = idx
                (SE_COUNT if idx < 3 else SE_GO).play()
            if el >= COUNTDOWN_SEC + COUNTDOWN_START_SHOW:
                state, state_t0 = "playing", now
                game.last_drop_time = now
                bgm.set_tempo_level(0)
                bgm.start()
        elif state == "playing":
            if not game.paused:
                stats.add_events(body_events, now)
                stats.add_angles(shoulder_angles_result)
                stats.play_sec += dt
                # ・右ステップ: 右へ1マス / 左ステップ: 左へ1マス
                # ・ハーフスクワット: 回転 / 万歳→下ろす: ハードドロップ
                if body_events["step_right"] and game.try_move(1):
                    SE_MOVE_RIGHT.play()
                if body_events["step_left"] and game.try_move(-1):
                    SE_MOVE_LEFT.play()
                if body_events["squat"] and game.try_rotate():
                    SE_ROTATE.play()
                if body_events["hard_drop"]:
                    game.hard_drop()
                game.update()
            handle_game_events(game, fx, board_x, board_y, now, S)

            # ピンチ演出: 積み上がりの高さでBGMのテンポと心音を変える
            height = game.stack_height()
            danger = 2 if height >= DANGER2_HEIGHT else (1 if height >= DANGER1_HEIGHT else 0)
            bgm.set_tempo_level(danger)
            if danger and not game.paused and now >= heartbeat_next:
                SE_HEARTBEAT.play()
                heartbeat_next = now + HEARTBEAT_INTERVAL[danger]

            if game.game_over:
                bgm.stop()
                state, state_t0 = "result", now
                danger = 0
                result = {"rank": score_rank(game.score), "fired": set(), "last_tick": 0.0,
                          "new_record": game.score > best_score and game.score > 0}
                best_score = max(best_score, game.score)
        elif state == "result":
            update_result(result, game, fx, now - state_t0, now)

        if abs(game.score - display_score) < 1:
            display_score = float(game.score)
        else:
            display_score += (game.score - display_score) * min(1.0, dt * 8)
        fx.update(dt, now, w, h, S)

        # --- 描画 ---
        sx, sy = fx.shake_offset(now)
        _, _, _, _, next_x, next_y = draw_board_overlay(
            frame, game, board_x + sx, board_y + sy, show_piece=(state == "playing"),
            show_next=(state in ("countdown", "playing")), danger=danger, now=now)
        if state in ("countdown", "playing"):
            texts.add("NEXT", (next_x, next_y - 34 * S), 26 * S, (255, 255, 255), stroke=2, bold=True)
        if danger >= 2:
            pulse = 0.5 + 0.5 * math.sin(now * 2 * math.pi * 2.0)
            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 255), int((6 + 10 * pulse) * S) + 1)
            if int(now * 4) % 2 == 0:
                texts.add("DANGER!!", (board_cx, board_y - 40 * S), 44 * S, (0, 0, 255), "center", "middle",
                          stroke=4, stroke_color=(255, 255, 255), bold=True)

        if pose_data is not None:
            # リザルト画面では肩角度のラベルがパネルに重なるので出さない
            draw_pose_overlay(frame, pose_data["landmarks"], w, h,
                              None if state == "result" else shoulder_angles_result, texts)

        for side_key in ("left", "right"):
            info = gesture[side_key]
            if info and info["lm"] is not None:
                draw_hand_skeleton(frame, info["lm"], w, h, info["pinched"])

        if state == "title":
            draw_title_screen(frame, texts, now, region_cx, w, h, S, body_ctrl, pose_data is not None, best_score)
        elif state in ("countdown", "playing"):
            draw_play_hud(frame, texts, game, stats, display_score, best_score, shoulder_angles_result,
                          body_ctrl, h, S, now)
            if state == "countdown":
                el = now - state_t0
                idx = min(3, int(el))
                frac = el - idx
                label = ["3", "2", "1", "START!"][idx]
                size = (260 if idx < 3 else 130) * S * (1 + 0.6 * max(0.0, 1 - frac / 0.15))
                texts.add(label, (board_cx, board_y + board_h_px * 0.4), size, (0, 230, 255), "center", "middle",
                          stroke=8 * S + 1, stroke_color=(90, 20, 140), bold=True)
            if game.paused:
                texts.add("一時停止中 (Pで再開)", (board_cx, h // 2), 40 * S, (0, 255, 255), "center", "middle",
                          stroke=4)
            if pose_data is not None and not body_ctrl.calibrated:
                texts.add("キャリブレーション中... 直立して足を揃えたまま静止してください",
                          (w / 2, h / 2 - 60 * S), 30 * S, (0, 255, 255), "center", "middle", stroke=3)
        elif state == "result":
            draw_result_screen(frame, texts, game, stats, result, now - state_t0, now, region_cx, w, h, S, board_x)

        # Tポーズのキープ中は進み具合を表示
        prog = body_events["tpose_progress"]
        if 0 < prog < 1:
            bw_, bh_ = 420 * S, 18 * S
            bcx_ = region_cx if state == "title" else w / 2  # タイトルでは操作説明に重ならない位置
            bx_, by_ = bcx_ - bw_ / 2, h * (0.90 if state == "title" else 0.36)
            texts.add("キャリブレーションのポーズ… そのままキープ!", (bcx_, by_ - 30 * S), 32 * S,
                      (120, 255, 120), "center", "middle", stroke=3)
            cv2.rectangle(frame, (int(bx_), int(by_)), (int(bx_ + bw_), int(by_ + bh_)), (255, 255, 255), 2)
            cv2.rectangle(frame, (int(bx_), int(by_)), (int(bx_ + bw_ * prog), int(by_ + bh_)), (120, 255, 120), -1)

        fx.draw(frame)
        fx.add_texts(texts, now)
        frame = texts.render(frame)

        cv2.imshow(window_name, frame)
        window_shown = True

    bgm.stop()
    hand_ctrl.close()
    pose_ctrl.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # ダブルクリック起動では画面がすぐ閉じるので、エラー内容をメッセージボックスで出す
        show_error("エラーが発生しました。この画面の内容を開発者に伝えてください。\n\n" + traceback.format_exc())
        sys.exit(1)
