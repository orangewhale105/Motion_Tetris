# -*- coding: utf-8 -*-
"""
Sea Turtle Colony(ウミガメ群体)— デスクトップで動く人工生命の小さなペット

・標準ライブラリだけで動く(tkinter)。pip install 不要。画面の表示は英語。
・上から見た南国の海(ターコイズブルー)と砂浜。沖から白い波が寄せてくる。
・ドット絵のウミガメ(インベーダー風)。スプライトは個体ごとに作って使い回す。
・遺伝的アルゴリズム:
    色(hue, hue2)・甲羅の模様(28bit)・速さ・寿命・大きさ・食性(草食/雑食)・
    性格(活発さ・食欲・カーソルへの好き嫌い・群れたがり・無頓着さ・気まま・気の短さ)・産卵数。
  交尾で両親の遺伝子を交叉(スクランブル)+突然変異。甲羅の色と模様で系統が見分けられる。
  系統(Lineage)は母系で受け継ぐ。
・生態系: 水草は増えて広がり、食べられると減る(根は残って再生。死骸は水草の栄養になる)。
  クラゲは沖から流れてくる(雑食のカメの餌)。カメが増えすぎると餌が減って餓死が増える。
  右上のグラフでカメ・水草・クラゲの増減が見える。
・イベント: 交尾 → メスが砂浜に上がって産卵 → ふ化した子ガメは海へ。合体・分裂・死(老衰/餓死/サメ)。
  まれに沖にサメが現れ、大きなカメ(x3以上)を狙う。カメは浅瀬へ逃げる。
  カメはときどき海面に浮上して息継ぎをする(波紋が広がる)。
・マウス:
    カメをクリック       → ステータス(世代・健康・系統・性格など)がカメについて回る。もう一度で消える
    カメをダブルクリック → ひっくり返る(その後、喜ぶか怒る)
    カメの上でカーソルを動かす → なでる(性格しだいで喜ぶ/嫌がる)
    近づける             → 性格に応じて寄ってくる / 嫌がって逃げる / 気にしない
    卵・水草・クラゲ・サメに重ねる → 説明を表示
    水をクリック → クラゲを落とす   Shift+クリック → 水草を植える
    右クリック → 最前面に固定の切り替え   L キー → 系統の文字を表示
・昼と夜: パソコンの時計に合わせて 薄明・日の出・昼・夕焼け・薄暮・夜 の色になり、
  カメは夜に眠り、暗くなってから産卵し、夕方は寄り集まる(日の出・日の入りは東京付近の近似)。
・閉じると群体を Google ドライブ(パソコン版 Google ドライブの同期フォルダ)に保存。
  次に起動すると、閉じていた実時間ぶん(最大7日)群体と生態系の時間を進める。

保存先の優先順:
  1) 環境変数 UMIGAME_SAVE_DIR
  2) Google ドライブの同期フォルダ(G:\\マイドライブ, G:\\My Drive, ~/Google Drive/My Drive,
     macOS の ~/Library/CloudStorage/GoogleDrive-*/My Drive など)の下の UmigamePet/
  3) 見つからなければ ホーム/UmigamePet/ (ウインドウのタイトルに「(saved locally)」と出る)
"""

import colorsys
import glob
import json
import math
import os
import random
import string
import sys
import time

VERSION = "3.1.0"

# ---------------------------------------------------------------- 定数
TICK_MS = 100                 # 画面更新の間隔(10fps)。最小化中は 1秒ごとに計算だけ
MAX_TURTLES = 40              # 安全のための上限(カメ+卵)。普段は餌の量で頭打ちになる
ADULT_AGE = 20 * 60           # 大人になる年齢(秒)
MATE_COOLDOWN = 20 * 60
EGG_TIME = 3 * 60             # 卵がかえるまで(秒)
LAY_TIME = 3.0
EGG_COST = 0.22              # 卵1個に母親が使う栄養
HATCH_ENERGY = 0.35          # 子ガメの最初の栄養                # 産卵にかかる時間(秒)
MAX_SCALE = 5                 # ドットの拡大率の上限(合体で大きくなる)
MERGE_KIN = 0.12              # この遺伝距離より近い個体どうしが合体候補
CORPSE_TIME = 10.0            # 死骸が残る時間(その後、分解されて近くの水草の栄養になる)
CORPSE_FERTILIZE = 0.25

PLANT_START = 10
PLANT_MAX = 18
PLANT_GROWTH = 0.003          # 水草のロジスティック成長率(1/秒)
PLANT_MIN = 0.08              # 食べ尽くされても根が残る量
PLANT_EDIBLE = 0.18           # これより少ない水草は食べられない(根からの再生を待つ)
PLANT_BASE = 0.0002           # 根からの再生(1/秒)
PLANT_BITE = 0.22
PLANT_SPREAD = 1 / 90.0       # 茂った水草が隣に広がる確率(1/秒)
JELLY_INTERVAL = 60.0         # クラゲが流れてくる間隔(秒)
JELLY_MAX = 5                 # 自然に流れてくるクラゲの上限
JELLY_DROP_MAX = 12           # クリックで落とす分も含めた上限
JELLY_ENERGY = 0.40

SHARK_GAP = (20 * 60, 45 * 60)  # サメが現れる間隔(秒、この範囲でランダム)
SHARK_STAY = 70.0             # サメが沖にいる時間(秒)
SHARK_PREY_SCALE = 3          # この大きさ以上のカメが狙われる
SHARK_SIGHT = 140.0           # サメが獲物に気づく距離
TURTLE_ALERT = 170.0          # カメがサメに気づいて逃げる距離
SHARK_ZONE = 0.6              # サメが入ってくるのは海の上(沖)から 60% まで

BREATH_GAP = (180, 480)       # 息継ぎの間隔(秒)。活発な個体ほど短い
BREATH_TIME = 2.5
PET_STROKE = 60.0             # なでた距離(px)がこれだけたまると1回なでたことになる

OFFLINE_STEP = 60.0
OFFLINE_MAX = 7 * 24 * 3600
HISTORY_DT = 20.0             # グラフの記録間隔(秒)
HISTORY_LEN = 60
AUTOSAVE_SEC = 300
SAVE_NAME = "colony.json"

FLOAT_GENES = ("hue", "hue2", "speed", "life", "size", "diet",
               "activity", "appetite", "cursor", "flock", "care", "whim",
               "temper", "fertility")
PATTERN_BITS = 28             # 甲羅の模様(左半分 4列 x 7行、左右対称)


# ---------------------------------------------------------------- 遺伝子
def random_genome(rng=random):
    g = {k: rng.random() for k in FLOAT_GENES}
    g["pattern"] = [rng.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def fill_genome(g):
    """古い保存データなど、足りない遺伝子を補う。"""
    g = dict(g)
    for k in FLOAT_GENES:
        if k not in g:
            g[k] = random.random()
    if len(g.get("pattern", [])) != PATTERN_BITS:
        g["pattern"] = [random.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def crossover(a, b, rng=random):
    """遺伝子のスクランブル: 一様交叉。模様は1点交叉(親の模様の塊が残る)。"""
    child = {k: (a[k] if rng.random() < 0.5 else b[k]) for k in FLOAT_GENES}
    cut = rng.randrange(PATTERN_BITS)
    child["pattern"] = a["pattern"][:cut] + b["pattern"][cut:]
    return child


def mutate(g, rate=0.12, sigma=0.08, rng=random):
    g = dict(g)
    for k in FLOAT_GENES:
        if rng.random() < rate:
            v = g[k] + rng.gauss(0, sigma)
            g[k] = v % 1.0 if k in ("hue", "hue2") else min(1.0, max(0.0, v))
    g["pattern"] = [(not b) if rng.random() < 0.03 else b for b in g["pattern"]]
    return g


def blend(a, b):
    """合体: 2体の遺伝子の平均。模様は OR(重ね合わせ)。"""
    g = {}
    for k in FLOAT_GENES:
        if k in ("hue", "hue2"):
            d = (b[k] - a[k] + 0.5) % 1.0 - 0.5
            g[k] = (a[k] + d / 2) % 1.0
        else:
            g[k] = (a[k] + b[k]) / 2
    g["pattern"] = [x or y for x, y in zip(a["pattern"], b["pattern"])]
    return g


def distance(a, b):
    d = 0.0
    for k in FLOAT_GENES:
        x = abs(a[k] - b[k])
        if k in ("hue", "hue2"):
            x = min(x, 1 - x) * 2
        d += x
    d /= len(FLOAT_GENES)
    ham = sum(x != y for x, y in zip(a["pattern"], b["pattern"])) / PATTERN_BITS
    return d * 0.7 + ham * 0.3


def traits(g):
    """性格のラベル(英語)。"""
    out = []
    if g["activity"] < 0.3:
        out.append("Sleepyhead")
    elif g["activity"] > 0.7:
        out.append("Energetic")
    if g["appetite"] > 0.7:
        out.append("Big eater")
    elif g["appetite"] < 0.3:
        out.append("Light eater")
    if g["care"] < 0.25:
        out.append("Carefree")
    else:
        if g["cursor"] > 0.7:
            out.append("Cursor lover")
        elif g["cursor"] < 0.3:
            out.append("Cursor shy")
        if g["flock"] > 0.7:
            out.append("Schooler")
        elif g["flock"] < 0.3:
            out.append("Loner")
        else:
            out.append("Middle-of-the-road")
    if g["whim"] > 0.7:
        out.append("Free spirit")
    if g["temper"] > 0.75:
        out.append("Short-tempered")
    elif g["temper"] < 0.2:
        out.append("Easygoing")
    return out


def lineage_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = string.ascii_uppercase[r] + s
    return s


# ---------------------------------------------------------------- 昼と夜(パソコンの時計に合わせる)
# 空の明るさと色み(R, G, B の倍率)
TINTS = {"night": (0.22, 0.28, 0.45), "twilight": (0.50, 0.58, 0.85), "sunrise": (1.00, 0.82, 0.72),
         "day": (1.00, 1.00, 1.00), "sunset": (1.08, 0.72, 0.50), "dusk": (0.55, 0.46, 0.72)}
PHASE_MSG = {
    "Dawn twilight": "Dawn twilight - the sky is getting lighter",
    "Sunrise": "Sunrise! The turtles wake up",
    "Daytime": "Daytime - a good time to eat",
    "Sunset": "Sunset - the sea turns orange",
    "Dusk": "Dusk - mothers head for the beach to lay eggs",
    "Night": "Night - most turtles fall asleep",
}


def sun_times(ts):
    """日の出・日の入りの時刻(時)。日本(東京付近)の季節変化を簡単な式で近似。
    夏至ごろ 4:24 / 19:00、冬至ごろ 6:48 / 16:30。"""
    doy = time.localtime(ts).tm_yday
    c = math.cos(2 * math.pi * (doy - 172) / 365.0)
    return 5.6 - 1.2 * c, 17.75 + 1.25 * c


def daylight(ts):
    """(時間帯の名前, 夜らしさ 0〜1, 色み, 時刻[時]) を返す。"""
    lt = time.localtime(ts)
    h = lt.tm_hour + lt.tm_min / 60.0 + lt.tm_sec / 3600.0
    sr, ss = sun_times(ts)
    keys = [(sr - 1.0, "night"), (sr - 0.5, "twilight"), (sr, "sunrise"), (sr + 1.0, "day"),
            (ss - 1.0, "day"), (ss - 0.2, "sunset"), (ss + 0.5, "dusk"), (ss + 1.2, "night")]
    tint = TINTS["night"]
    for (h0, a), (h1, b) in zip(keys, keys[1:]):
        if h0 <= h < h1:
            f = (h - h0) / (h1 - h0)
            tint = tuple(x + (y - x) * f for x, y in zip(TINTS[a], TINTS[b]))
            break
    if h < sr - 1.0 or h >= ss + 1.0:
        phase = "Night"
    elif h < sr - 0.2:
        phase = "Dawn twilight"
    elif h < sr + 0.8:
        phase = "Sunrise"
    elif h < ss - 1.0:
        phase = "Daytime"
    elif h < ss + 0.2:
        phase = "Sunset"
    else:
        phase = "Dusk"
    bright = sum(min(1.0, x) for x in tint) / 3
    night = max(0.0, min(1.0, (1.0 - bright) / (1.0 - sum(TINTS["night"]) / 3)))
    return phase, night, tint, h


# ---------------------------------------------------------------- 生き物と餌
class Turtle:
    _ids = 0

    def __init__(self, genome, x, y, generation=1, age=0.0, tid=None,
                 sex=None, lineage="A", parents=None, extra=0):
        if tid is None:
            Turtle._ids += 1
            tid = Turtle._ids
        else:
            Turtle._ids = max(Turtle._ids, tid)
        self.id = tid
        self.g = genome
        self.sex = sex or random.choice("FM")
        self.lineage = lineage
        self.parents = parents or ""
        self.extra = extra
        self.x, self.y = x, y
        a = random.uniform(0, math.tau)
        self.vx, self.vy = math.cos(a) * 8, math.sin(a) * 8
        self.heading = a
        self.generation = generation
        self.age = age
        self.energy = 0.7
        self.fatigue = random.random() * 0.6
        self.mate_cd = MATE_COOLDOWN * 0.3
        self.state = "swim"
        self.state_t = 0.0
        self.joy = 0.3
        self.annoy = 0.0
        self.emote = None
        self.emote_t = 0.0
        self.target = None
        self.food = None
        self.food_t = 0.0
        self.eat_cd = 0.0
        self.clutch = None
        self.nest = None
        self.dead_t = 0.0
        self.cause = ""
        self.anim = random.random()
        self.dir = 0           # 0上 1右 2下 3左
        self.nb = None         # 近くの仲間の情報(群れの計算用)
        self.air = random.uniform(0.3, 1.0) * self.breath_gap
        self.pet_acc = 0.0
        self.pets = 0

    @property
    def adult(self):
        return self.age >= ADULT_AGE

    @property
    def scale(self):
        if not self.adult:
            return 1
        return min(MAX_SCALE, (2 if self.g["size"] < 0.5 else 3) + self.extra)

    @property
    def herbivore(self):
        return self.g["diet"] < 0.5

    @property
    def max_speed(self):
        s = (12 + 30 * self.g["speed"]) * (0.8 + 0.4 * self.g["activity"])
        s *= 1.0 - 0.07 * (self.scale - 2)
        return s * (0.8 if not self.adult else 1.0)

    @property
    def lifespan(self):
        return (4 + 8 * self.g["life"]) * 3600 * (1 + 0.2 * self.extra)

    @property
    def metab(self):
        g = self.g
        return (0.0005 + 0.0006 * g["appetite"] + 0.0003 * g["speed"]
                + 0.0002 * g["activity"]) * (1 + 0.15 * self.extra) * (1.0 if self.adult else 0.6)

    @property
    def eat_below(self):
        return 0.35 + 0.5 * self.g["appetite"]

    def night_pull(self, night):
        """夜の眠気。活発な個体ほど夜でも起きている(夜ふかし)。"""
        return night * (1.0 - 0.7 * self.g["activity"])

    @property
    def awake_len(self):
        return 300 + 1500 * self.g["activity"]

    @property
    def sleep_len(self):
        return 60 + 300 * (1 - self.g["activity"])

    @property
    def breath_gap(self):
        a, b = BREATH_GAP
        return a + (b - a) * (1 - self.g["activity"])

    @property
    def radius(self):
        return 5.5 * self.scale

    @property
    def alive(self):
        return self.state != "dead"

    def say(self, emote, sec=1.6):
        self.emote, self.emote_t = emote, sec

    def to_dict(self):
        return {"id": self.id, "g": self.g, "x": self.x, "y": self.y, "gen": self.generation,
                "age": self.age, "energy": self.energy, "fatigue": self.fatigue,
                "mate_cd": self.mate_cd, "sex": self.sex, "lin": self.lineage,
                "par": self.parents, "extra": self.extra, "clutch": self.clutch,
                "sleep": self.state == "sleep", "joy": self.joy, "annoy": self.annoy}

    @classmethod
    def from_dict(cls, d):
        t = cls(fill_genome(d["g"]), d["x"], d["y"], d.get("gen", 1), d.get("age", 0.0),
                d["id"], d.get("sex"), d.get("lin", "A"), d.get("par", ""), d.get("extra", 0))
        t.energy = d.get("energy", 0.7)
        t.fatigue = d.get("fatigue", 0.3)
        t.mate_cd = d.get("mate_cd", 0.0)
        t.joy, t.annoy = d.get("joy", 0.3), d.get("annoy", 0.0)
        t.clutch = d.get("clutch")
        if d.get("sleep"):
            t.state = "sleep"
        return t


class Egg:
    def __init__(self, genome, x, y, generation, lineage, parents, t=EGG_TIME, sex=None):
        self.g, self.x, self.y = genome, x, y
        self.generation, self.lineage, self.parents = generation, lineage, parents
        self.t, self.sex = t, sex

    def to_dict(self):
        return {"g": self.g, "x": self.x, "y": self.y, "gen": self.generation,
                "lin": self.lineage, "par": self.parents, "t": self.t, "sex": self.sex}

    @classmethod
    def from_dict(cls, d):
        return cls(fill_genome(d["g"]), d["x"], d["y"], d.get("gen", 1), d.get("lin", "A"),
                   d.get("par", ""), d.get("t", EGG_TIME), d.get("sex"))


class Plant:
    kind = "plant"

    def __init__(self, x, y, b=0.3):
        self.x, self.y, self.b = x, y, b
        self.gone = False

    @property
    def stage(self):
        b = self.b
        return 0 if b < 0.15 else 1 if b < 0.4 else 2 if b < 0.7 else 3


class Shark:
    kind = "shark"

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx, self.vy = x, y, vx, 0.0
        self.t = 0.0
        self.target = None
        self.leaving = False
        self.anim = 0.0
        self.dir = 1 if vx > 0 else 3


class Jelly:
    kind = "jelly"

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx = x, y, vx
        self.phase = random.random() * math.tau
        self.gone = False


# ---------------------------------------------------------------- 世界(描画と無関係)
class World:
    def __init__(self, w=640, h=420):
        self.w, self.h = w, h
        self.turtles = []
        self.eggs = []
        self.plants = []
        self.shark = None
        self.shark_t = random.uniform(*SHARK_GAP)
        self.clock = time.time    # テストでは差し替える
        self.phase, self.night, self.tint, self.hour = daylight(self.clock())
        self.phase_msg = None
        self.fx = []              # 描画側への演出 (種類, x, y)
        self.jellies = []
        self.time = 0.0
        self.jelly_t = 0.0
        self.births = self.deaths = self.laid = self.merges = self.splits = 0
        self.max_gen = 1
        self.n_lineages = 0
        self.gene_pool = []
        self.cursor = None
        self.cursor_speed = 0.0
        self.events = []          # (時刻の文字列, 種類, 文)
        self.history = []         # (カメ, 水草の総量, ゴカイ)
        self.hist_t = 0.0
        self._pop = 0

    # ---- 地形
    @property
    def land_top(self):
        return self.h - max(40.0, self.h * 0.17)

    def shore(self, x):
        return self.land_top + 4 * math.sin(x / 37.0) + 3 * math.sin(x / 13.0 + 1)

    def in_water(self, x, y):
        return y < self.shore(x) - 2

    def water_point(self, margin=20):
        x = random.uniform(margin, self.w - margin)
        return x, random.uniform(margin, max(margin + 1, self.shore(x) - margin))

    def beach_point(self, x=None):
        if x is None:
            x = random.uniform(30, self.w - 30)
        s = self.shore(x)
        return x, s + (self.h - s) * random.uniform(0.35, 0.7)

    # ---- 初期化
    def new_lineage(self):
        name = lineage_name(self.n_lineages)
        self.n_lineages += 1
        return name

    def seed(self, n=8):
        for i in range(n):
            x, y = self.water_point(40)
            t = Turtle(random_genome(), x, y, sex="FM"[i % 2], lineage=self.new_lineage())
            t.age = ADULT_AGE + random.uniform(0.0, 0.2) * t.lifespan
            t.mate_cd = random.uniform(0, MATE_COOLDOWN)
            self.turtles.append(t)
        self.seed_plants()

    def seed_plants(self, n=PLANT_START):
        for _ in range(n):
            x, y = self.water_point(25)
            self.plants.append(Plant(x, y, random.uniform(0.3, 0.9)))

    def alive(self):
        return [t for t in self.turtles if t.alive]

    def population(self):
        return sum(t.alive for t in self.turtles) + len(self.eggs)

    def event(self, kind, text):
        ts = getattr(self, "now_ts", None) or time.time()
        self.events.append((time.strftime("%H:%M", time.localtime(ts)), kind, text))
        self.events = self.events[-8:]

    @staticmethod
    def tag(t):
        return "#%d (%s)" % (t.id, t.lineage)

    # ---- 1フレーム
    def update_daylight(self, ts, log=True):
        self.now_ts = ts
        phase, self.night, self.tint, self.hour = daylight(ts)
        if phase != self.phase:
            self.phase = phase
            if log:
                self.phase_msg = PHASE_MSG[phase]
                self.event("time", PHASE_MSG[phase])

    def step(self, dt):
        dt = min(dt, 0.5)
        self.time += dt
        self.update_daylight(self.clock())
        self._grow_plants(dt)
        self._jellies(dt)
        self._shark_step(dt)
        self._hatch(dt)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        self._neighbors(alive)
        for t in list(self.turtles):
            self._update_turtle(t, dt)
        self._pairs(alive, dt)
        self._decompose()
        if not self.alive() and not self.eggs:
            self._refound()
        self._record(dt)

    # ---- 生態系
    def _grow_plants(self, dt):
        new = []
        for p in self.plants:
            p.b += (PLANT_GROWTH * p.b + PLANT_BASE) * (1 - p.b) * dt
            p.b = min(1.0, max(PLANT_MIN, p.b))
            if (p.b > 0.85 and len(self.plants) + len(new) < PLANT_MAX
                    and random.random() < min(1.0, dt * PLANT_SPREAD)):
                a = random.uniform(0, math.tau)
                r = random.uniform(25, 50)
                x = min(max(15, p.x + math.cos(a) * r), self.w - 15)
                y = max(15, p.y + math.sin(a) * r)
                if self.in_water(x, y + 15):
                    new.append(Plant(x, y, 0.1))
                    p.b -= 0.2
        self.plants += new

    def _jellies(self, dt):
        self.jelly_t += dt
        if self.jelly_t > JELLY_INTERVAL:
            self.jelly_t = 0.0
            if len(self.jellies) < JELLY_MAX:
                left = random.random() < 0.5
                x, y = self.water_point(30)
                self.jellies.append(Jelly(-8 if left else self.w + 8, y, 7 if left else -7))
        keep = []
        for j in self.jellies:
            j.phase += dt
            j.x += j.vx * dt
            j.y += math.sin(j.phase * 0.8) * 4 * dt
            if not j.gone and -12 <= j.x <= self.w + 12:
                keep.append(j)
        self.jellies = keep

    def drop_jelly(self, x, y):
        if len(self.jellies) < JELLY_DROP_MAX and self.in_water(x, y):
            j = Jelly(x, y, random.choice((-3, 3)))
            self.jellies.append(j)
            self.fx.append(("splash", x, y))

    # ---- サメ(まれに沖に現れ、大きなカメを狙う)
    def _shark_step(self, dt):
        if self.shark is None:
            self.shark_t -= dt * (1.0 + self.night)     # サメは夕方〜夜に現れやすい
            if self.shark_t <= 0:
                self.shark_t = random.uniform(*SHARK_GAP)
                left = random.random() < 0.5
                y = random.uniform(20, self.land_top * SHARK_ZONE * 0.6)
                self.shark = Shark(-30 if left else self.w + 30, y, 30 if left else -30)
                self.event("shark", "A shark appeared offshore! Big turtles, watch out")
            return
        sh = self.shark
        sh.t += dt
        sh.anim += dt
        limit = self.land_top * SHARK_ZONE
        if sh.t > SHARK_STAY and not sh.leaving:
            sh.leaving, sh.target = True, None
        tg = sh.target
        if not sh.leaving and (tg is None or not tg.alive or tg.y > limit + 30):
            sh.target = tg = None
            best = SHARK_SIGHT
            for t in self.turtles:
                if t.alive and t.scale >= SHARK_PREY_SCALE and t.y < limit:
                    d = math.hypot(t.x - sh.x, t.y - sh.y)
                    if d < best:
                        tg, best = t, d
            sh.target = tg
        if tg is not None:
            dx, dy = tg.x - sh.x, tg.y - sh.y
            d = math.hypot(dx, dy) or 1.0
            sp = 46.0
            if d < 22 + tg.radius:
                tg.say("ghost", 3.0)
                self._kill(tg, "a shark attack")
                tg.dead_t = CORPSE_TIME - 1.0          # 食べられたのですぐ消える
                self.fx.append(("bite", tg.x, tg.y))
                sh.leaving, sh.target = True, None
        else:
            if sh.leaving:
                dx, dy = (1.0 if sh.vx >= 0 else -1.0), -0.2
            else:
                dx, dy = (1.0 if sh.vx >= 0 else -1.0), math.sin(sh.t * 0.7) * 0.4
            d = math.hypot(dx, dy)
            sp = 30.0 if not sh.leaving else 40.0
        k = min(1.0, dt * 1.5)
        sh.vx += (dx / d * sp - sh.vx) * k
        sh.vy += (dy / d * sp - sh.vy) * k
        sh.x += sh.vx * dt
        sh.y = min(max(12, sh.y + sh.vy * dt), limit)
        if not sh.leaving and (sh.x < 20 or sh.x > self.w - 20):
            sh.vx = abs(sh.vx) if sh.x < 20 else -abs(sh.vx)
        if abs(sh.vx) > abs(sh.vy) * 0.5:
            sh.dir = 1 if sh.vx > 0 else 3
        if sh.leaving and (sh.x < -40 or sh.x > self.w + 40 or sh.y < -30):
            self.shark = None
            self.event("shark", "The shark swam away")

    def drop_plant(self, x, y):
        if len(self.plants) < PLANT_MAX + 6 and self.in_water(x, y + 10):
            self.plants.append(Plant(x, y, 0.15))

    def _record(self, dt):
        self.hist_t += dt
        if self.hist_t >= HISTORY_DT:
            self.hist_t = 0.0
            self.history.append((sum(t.alive for t in self.turtles),
                                 round(sum(p.b for p in self.plants), 2), len(self.jellies)))
            self.history = self.history[-HISTORY_LEN:]

    # ---- 卵・誕生・死
    def _hatch(self, dt):
        groups = {}
        for e in list(self.eggs):
            e.t -= dt
            if e.t <= 0:
                self.eggs.remove(e)
                t = Turtle(e.g, e.x, e.y, e.generation, sex=e.sex,
                           lineage=e.lineage, parents=e.parents)
                t.energy = HATCH_ENERGY
                t.say("sparkle", 2.0)
                self.turtles.append(t)
                self.births += 1
                self.max_gen = max(self.max_gen, e.generation)
                groups.setdefault((e.lineage, e.generation), []).append(t)
        for (lin, gen), ts in groups.items():
            self.event("hatch", "%d hatchling%s of Lineage %s (Gen %d) head to the sea"
                       % (len(ts), "s" if len(ts) > 1 else "", lin, gen))

    def _refound(self):
        """絶滅したら、遺伝子の記憶から卵が4つ砂浜に流れ着く(新しい系統)。"""
        pool = self.gene_pool or [random_genome() for _ in range(3)]
        lin = self.new_lineage()
        for i in range(4):
            g = mutate(random.choice(pool), rate=0.4)
            x, y = self.beach_point()
            self.eggs.append(Egg(g, x, y, self.max_gen + 1, lin, "drifted ashore",
                                 EGG_TIME * 0.3, "FM"[i % 2]))
        self.event("hatch", "The colony died out... 4 eggs drifted ashore (Lineage %s)" % lin)

    def _kill(self, t, cause):
        t.state, t.dead_t, t.cause = "dead", 0.0, cause
        t.emote = "ghost"
        t.emote_t = 3.0
        t.clutch = None
        self.deaths += 1
        self.gene_pool.append(t.g)
        self.gene_pool = self.gene_pool[-10:]
        self.event("death", "%s died of %s at %s" % (self.tag(t), cause, fmt_dur(t.age)))
        for o in self.turtles:
            if o.target is t:
                o.target, o.state = None, "swim"

    def _decompose(self, force=False):
        keep = []
        for t in self.turtles:
            if t.state == "dead" and (force or t.dead_t > CORPSE_TIME):
                if t.adult and self.plants:        # 死骸は分解されて近くの水草の栄養に
                    p = min(self.plants, key=lambda p: (p.x - t.x) ** 2 + (p.y - t.y) ** 2)
                    p.b = min(1.0, p.b + CORPSE_FERTILIZE)
                continue
            keep.append(t)
        self.turtles = keep

    # ---- 個体の行動
    def _neighbors(self, alive):
        for t in alive:
            cx = cy = vx = vy = 0.0
            n = 0
            near = 1e9
            for o in alive:
                if o is t:
                    continue
                dx, dy = o.x - t.x, o.y - t.y
                d2 = dx * dx + dy * dy
                if d2 < 100 * 100:
                    cx += o.x
                    cy += o.y
                    vx += o.vx
                    vy += o.vy
                    n += 1
                    near = min(near, d2)
            t.nb = (cx / n, cy / n, vx / n, vy / n, n, math.sqrt(near)) if n else None

    def _update_turtle(self, t, dt):
        t.anim += dt
        if t.emote_t > 0:
            t.emote_t -= dt
            if t.emote_t <= 0:
                t.emote = None
        if t.state == "dead":
            t.dead_t += dt
            t.vx *= 0.9
            t.vy *= 0.9
            return

        t.age += dt
        t.mate_cd -= dt
        t.eat_cd -= dt
        t.joy = max(0.0, t.joy - 0.015 * dt)
        t.annoy = max(0.0, t.annoy - 0.02 * dt)
        sleeping = t.state == "sleep"
        t.air -= dt * (0.4 if sleeping else 1.0)
        t.energy -= t.metab * dt * (0.35 if sleeping else 1.0)
        t.fatigue += (-dt / t.sleep_len) if sleeping else (dt / t.awake_len)
        if t.energy <= 0:
            self._kill(t, "starvation")
            return
        if t.age >= t.lifespan:
            self._kill(t, "old age")
            return

        t.state_t -= dt
        water = self.in_water(t.x, t.y)
        if not water:
            t.air = max(t.air, 30.0)
        sh = self.shark
        if (sh and water and t.state not in ("flipped", "lay")
                and math.hypot(sh.x - t.x, sh.y - t.y) < TURTLE_ALERT):
            if t.state != "flee_shark":
                t.say("bang", 1.2)
                t.target = None
            t.state, t.state_t = "flee_shark", 1.5     # サメから逃げる(浅瀬へ)
        if t.state in ("flipped", "dance", "lay", "breathe", "petted"):
            if t.state_t <= 0:
                if t.state == "flipped":
                    if t.annoy > 0.5:
                        t.say("anger")
                        t.state, t.state_t = "flee", 2.0
                    else:
                        t.joy = min(1.0, t.joy + 0.4)
                        t.say("note")
                        t.state, t.state_t = "dance", 1.2
                elif t.state == "lay":
                    self._lay(t)
                elif t.state == "breathe":
                    t.air = t.breath_gap * random.uniform(0.8, 1.2)
                    t.state = "swim"
                else:
                    t.state = "swim"
        elif t.state == "sleep":
            t.fatigue = max(t.fatigue, -0.2)
            if t.fatigue <= 0 and t.night_pull(self.night) < 0.5:
                t.state = "swim"                      # 朝になったら起きる
                if self.night < 0.4 and self.phase in ("Sunrise", "Dawn twilight"):
                    t.say("note", 1.5)
            elif t.air <= 0 and water:                # 寝ていても息継ぎに浮上する
                t.state, t.state_t = "breathe", BREATH_TIME
                t.say("puff", BREATH_TIME)
                self.fx.append(("ripple", t.x, t.y))
            elif random.random() < dt / 3:
                t.say("zzz", 1.5)
        elif t.state in ("flee", "flee_shark") and t.state_t > 0:
            pass
        else:
            prev = t.state
            t.state = "swim"
            if t.clutch and (self.night > 0.3 or t.energy < 0.25):
                t.state = "nest"                      # 産卵は暗くなってから(ウミガメの習性)
                if t.nest is None:
                    t.nest = self.beach_point()
            elif not water:
                pass                                  # 砂浜から海へ戻る途中
            elif t.air <= 0:                          # 海面に浮上して息継ぎ
                t.state, t.state_t = "breathe", BREATH_TIME
                t.say("puff", BREATH_TIME)
                self.fx.append(("ripple", t.x, t.y))
            elif t.fatigue + t.night_pull(self.night) > 1 and t.energy > 0.15 and not t.clutch:
                t.state = "sleep"
                t.say("zzz", 2)
            elif t.energy < t.eat_below + (0.1 if self.phase == "Sunrise" else 0.0) and (prev == "food" or t.energy < t.eat_below - 0.05):
                if t.food is None or t.food.gone or t.food_t <= 0:
                    t.food = self._choose_food(t)
                    t.food_t = 1.0
                t.food_t -= dt
                if t.food is not None:
                    t.state = "food"
            elif prev == "court" and t.target is not None and t.target.alive:
                t.state = "court"
            elif self._can_mate(t):
                p = self._find_partner(t)
                if p:
                    t.state, t.target = "court", p
            if t.state == "swim" and t.g["whim"] > 0.7 and t.joy > 0.4 and random.random() < dt / 120:
                t.state, t.state_t = "dance", 1.0     # 気まま: 気分で急にくるくる回る
                t.say("note", 1.0)
            if t.energy < 0.2 and random.random() < dt / 6:
                t.say("sweat")
        self._steer(t, dt, water)

    def _can_mate(self, t):
        return (t.alive and t.state in ("swim", "court") and t.adult and t.energy > 0.8
                and t.mate_cd <= 0 and not t.clutch and self.in_water(t.x, t.y)
                and self._pop < MAX_TURTLES - 1)

    def _find_partner(self, t):
        best, bd = None, 280.0
        for o in self.turtles:
            if o is t or o.sex == t.sex or not self._can_mate(o):
                continue
            d = math.hypot(o.x - t.x, o.y - t.y)
            if distance(t.g, o.g) < 0.04:   # 近すぎる近縁は避ける
                d *= 3
            if d < bd:
                best, bd = o, d
        return best

    def _choose_food(self, t):
        best, bs = None, 1e18
        items = [p for p in self.plants if p.b > PLANT_EDIBLE]
        if not t.herbivore:
            items += self.jellies
        for f in items:
            if f.kind == "plant":
                gain = min(PLANT_BITE, f.b - PLANT_MIN) * (1.5 if t.herbivore else 0.9)
            else:
                gain = JELLY_ENERGY
            d = math.hypot(f.x - t.x, f.y - t.y) + 20
            s = d / max(gain, 0.01)
            if s < bs:
                best, bs = f, s
        return best

    def _eat(self, t, f):
        if f.gone:
            return
        if f.kind == "plant":
            bite = min(PLANT_BITE, f.b - PLANT_MIN)
            if f.b < PLANT_EDIBLE:
                t.food = None
                return
            f.b -= bite
            t.energy += bite * (1.5 if t.herbivore else 0.9)
        else:
            f.gone = True
            t.energy += JELLY_ENERGY
        t.energy = min(1.0, t.energy)
        t.joy = min(1.0, t.joy + 0.1)
        t.eat_cd = 1.2
        t.food_t = 0.0
        if random.random() < 0.3:
            t.say("note", 1.0)

    def _lay(self, t):
        n = 0
        for g in t.clutch or []:
            if self.population() >= MAX_TURTLES:
                break
            self.eggs.append(Egg(g["g"], t.x + random.uniform(-10, 10), t.y + random.uniform(-6, 6),
                                 g["gen"], t.lineage, g["par"]))
            n += 1
        t.clutch, t.nest = None, None
        t.state = "swim"
        self.laid += n
        t.say("sparkle", 1.5)
        self.event("lay", "%s laid %d egg%s on the beach" % (self.tag(t), n, "s" if n != 1 else ""))

    def _steer(self, t, dt, water):
        sp = t.max_speed
        dx = dy = 0.0
        mul = 1.0
        st = t.state
        if st in ("sleep", "flipped", "lay", "breathe", "petted"):
            mul = 0.0
        elif st == "flee_shark" and self.shark:
            sh = self.shark
            dx, dy = t.x - sh.x, t.y - sh.y
            n0 = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n0, dy / n0 + 0.9             # 離れながら浅瀬(下)へ
            mul = 1.6
        elif st == "dance":
            mul = 0.2
            t.dir = int(t.anim / 0.15) % 4
        elif st == "nest":
            nx, ny = t.nest
            dx, dy = nx - t.x, ny - t.y
            if math.hypot(dx, dy) < 6 and not water:
                t.state, t.state_t = "lay", LAY_TIME
                t.say("egg", LAY_TIME)
                mul = 0.0
        elif not water:
            dx, dy = random.uniform(-0.2, 0.2), -1.0   # 砂浜では海(上)へ向かう
        elif st == "food":
            f = t.food
            if f is None or f.gone:
                t.state, t.food = "swim", None
            else:
                dx, dy = f.x - t.x, f.y - t.y
                if t.eat_cd > 0:
                    mul = 0.1
                elif math.hypot(dx, dy) < t.radius + 5:
                    self._eat(t, f)
                    mul = 0.1
                else:
                    mul = 1.1
        elif st == "court":
            o = t.target
            if o is None or not o.alive or not self._can_mate(o):
                t.state, t.target = "swim", None
            else:
                dx, dy = o.x - t.x, o.y - t.y
                if random.random() < dt / 2:
                    t.say("heart", 1.0)
        elif st == "flee" and self.cursor:
            dx, dy = t.x - self.cursor[0], t.y - self.cursor[1]
            mul = 1.5

        care = t.g["care"]
        # マウスへの反応(無頓着な個体はほとんど気にしない)
        if self.cursor and water and st in ("swim", "court", "food") and care > 0.25:
            cx, cy = self.cursor
            d = math.hypot(cx - t.x, cy - t.y)
            if d < 170:
                like = (t.g["cursor"] - 0.5) * 2 * care + t.joy * 0.3 - t.annoy * 1.2
                if self.cursor_speed > 900 and d < 90 and care > 0.4:
                    t.say("bang", 0.8)
                    t.annoy = min(1.0, t.annoy + 0.12 * t.g["temper"] + 0.02)
                    t.state, t.state_t = "flee", 0.8
                elif like > 0.25 and st == "swim":
                    if d > 22:
                        dx, dy = cx - t.x, cy - t.y
                        mul = 1.1
                    else:
                        mul = 0.15
                        t.joy = min(1.0, t.joy + 0.08 * dt)
                        if random.random() < dt / 2.5:
                            t.say("heart" if t.joy > 0.6 else "note", 1.2)
                elif like < -0.15:
                    dx, dy = t.x - cx, t.y - cy
                    mul = 1.3
                    if t.annoy > 0.4 and random.random() < dt / 2:
                        t.say("anger", 1.2)
                if d < 45:   # 近くにずっといると、気の短い個体はうっとうしがる
                    t.annoy = min(1.0, t.annoy + max(0.0, t.g["temper"] - 0.3) * 0.08 * dt)

        if dx == 0 and dy == 0 and mul > 0:
            # 気ままに泳ぐ + 群れ(群れたがり / 一人が好き / 中庸 / 無頓着)
            jitter = 0.4 + 2.0 * t.g["whim"] + 2.5 * t.annoy
            t.heading += random.gauss(0, jitter) * dt
            dx, dy = math.cos(t.heading), math.sin(t.heading)
            nb = t.nb
            fw = (t.g["flock"] - 0.5) * 2 * care
            if self.phase in ("Sunset", "Dusk"):     # 夕方は寄り集まる
                fw = min(1.0, fw + 0.4 * care)
            if nb and abs(fw) > 0.05:
                cx, cy, avx, avy, n, near = nb
                ox, oy = cx - t.x, cy - t.y
                on = math.hypot(ox, oy) or 1.0
                if fw > 0:
                    if near > t.radius * 3:
                        dx += ox / on * fw * 0.9
                        dy += oy / on * fw * 0.9
                    else:
                        dx -= ox / on * 0.5
                        dy -= oy / on * 0.5
                    an = math.hypot(avx, avy)
                    if an > 1:
                        dx += avx / an * fw * 0.6
                        dy += avy / an * fw * 0.6
                else:
                    dx += ox / on * fw * 1.2
                    dy += oy / on * fw * 1.2
            mul *= 0.55 + 0.4 * t.joy
            t.heading = math.atan2(dy, dx) if (dx or dy) else t.heading
        elif dx or dy:
            t.heading = math.atan2(dy, dx)
        if not water:
            mul *= 0.35                               # 砂浜ではゆっくり這う
        elif st not in ("flee_shark", "nest"):
            mul *= 1.0 - 0.3 * self.night             # 夜はゆっくり
        n = math.hypot(dx, dy) or 1.0
        tx, ty = dx / n * sp * mul, dy / n * sp * mul
        k = min(1.0, dt * 2.0)
        t.vx += (tx - t.vx) * k
        t.vy += (ty - t.vy) * k
        t.x += t.vx * dt
        t.y += t.vy * dt
        m = t.radius + 2
        if t.x < m or t.x > self.w - m:
            t.vx = -t.vx
            t.heading = math.pi - t.heading
            t.x = min(max(t.x, m), self.w - m)
        if t.y < m:
            t.vy = abs(t.vy)
            t.heading = -t.heading
            t.y = m
        if t.y > self.h - m:
            t.y = self.h - m
        if water and st not in ("nest",):              # 泳いでいる個体は砂浜に上がらない
            s = self.shore(t.x) - m
            if t.y > s:
                t.y = s
                t.vy = -abs(t.vy)
                t.heading = -abs(t.heading)
        if st != "dance" and abs(t.vx) + abs(t.vy) > 2:
            if abs(t.vx) > abs(t.vy):
                t.dir = 1 if t.vx > 0 else 3
            else:
                t.dir = 2 if t.vy > 0 else 0

    # ---- 個体どうし(押し合い・交尾・合体・分裂)
    def _pairs(self, alive, dt):
        removed = set()
        n = len(alive)
        for i in range(n):
            a = alive[i]
            if a.id in removed or not a.alive:
                continue
            for j in range(i + 1, n):
                b = alive[j]
                if b.id in removed or not b.alive:
                    continue
                dx, dy = b.x - a.x, b.y - a.y
                d2 = dx * dx + dy * dy
                r = a.radius + b.radius
                if d2 > r * r:
                    continue
                d = math.sqrt(d2) or 0.01
                push = (r - d) * 0.25
                a.x -= dx / d * push
                a.y -= dy / d * push
                b.x += dx / d * push
                b.y += dy / d * push
                if ((a.state == "court" and a.target is b) or (b.state == "court" and b.target is a)) \
                        and a.sex != b.sex and self._can_mate(a) and self._can_mate(b):
                    self._mate(a, b)
                    continue
                if (a.adult and b.adult and a.state in ("swim", "food") and b.state in ("swim", "food")
                        and not a.clutch and not b.clutch
                        and max(a.scale, b.scale) < MAX_SCALE and distance(a.g, b.g) < MERGE_KIN):
                    hungry = a.energy < 0.3 and b.energy < 0.3
                    if random.random() < dt * (0.5 if hungry else 0.01):
                        removed.update((a.id, b.id))
                        self._merge(a, b)
                        break
        for t in alive:     # 分裂: 合体して大きくなった個体が満腹だと2つに分かれる
            if (t.id not in removed and t.alive and t.extra >= 1 and t.energy > 0.85
                    and t.state == "swim" and random.random() < dt / 600):
                self._split(t)

    def _mate(self, a, b):
        mom, dad = (a, b) if a.sex == "F" else (b, a)
        room = MAX_TURTLES - self.population()
        n = min(room, 1 + int(mom.g["fertility"] * 2.99))
        if n <= 0:
            return
        for t in (a, b):
            t.mate_cd = MATE_COOLDOWN * (0.8 + 0.4 * random.random())
            t.energy -= EGG_COST * n if t is mom else 0.2     # 卵の栄養は母親が出す
            t.state, t.target = "swim", None
            t.say("heart", 2.0)
        mom.clutch = [{"g": mutate(crossover(mom.g, dad.g)),
                       "gen": max(mom.generation, dad.generation) + 1,
                       "par": "#%d x #%d" % (mom.id, dad.id)} for _ in range(n)]
        mom.nest = None
        self.event("mate", "%s and %s mated" % (self.tag(mom), self.tag(dad)))

    def _merge(self, a, b):
        t = Turtle(blend(a.g, b.g), (a.x + b.x) / 2, (a.y + b.y) / 2,
                   max(a.generation, b.generation), max(ADULT_AGE, min(a.age, b.age)),
                   sex=a.sex, lineage=a.lineage, parents="merged #%d + #%d" % (a.id, b.id),
                   extra=max(a.extra, b.extra) + 1)
        t.energy = min(1.0, a.energy + b.energy)
        t.joy = 0.8
        t.say("sparkle", 2.5)
        self.turtles = [x for x in self.turtles if x is not a and x is not b]
        self.turtles.append(t)
        for o in self.turtles:
            if o.target in (a, b):
                o.target, o.state = None, "swim"
        self.merges += 1
        self.event("merge", "%s and %s merged into %s" % (self.tag(a), self.tag(b), self.tag(t)))

    def _split(self, t):
        kids = []
        for i in range(2):
            k = Turtle(mutate(t.g, rate=0.3), t.x + (i * 2 - 1) * t.radius, t.y, t.generation,
                       t.age, sex=t.sex, lineage=t.lineage, parents="split from #%d" % t.id,
                       extra=t.extra - 1)
            k.energy = t.energy / 2
            k.say("sparkle", 2.0)
            kids.append(k)
        self.turtles = [x for x in self.turtles if x is not t] + kids
        for o in self.turtles:
            if o.target is t:
                o.target, o.state = None, "swim"
        self.splits += 1
        self.event("split", "%s split into #%d and #%d" % (self.tag(t), kids[0].id, kids[1].id))

    # ---- マウス操作
    def hit(self, x, y, pad=4):
        best, bd = None, 1e9
        for t in self.turtles:
            if not t.alive:
                continue
            d = math.hypot(t.x - x, t.y - y)
            if d < t.radius + pad and d < bd:
                best, bd = t, d
        return best

    def pet(self, t, dist):
        """カメの上でカーソルを動かす = なでる。好き嫌いは性格しだい。"""
        if not t.alive or t.state in ("lay", "flipped", "flee_shark"):
            return
        t.pet_acc += dist
        if t.pet_acc < PET_STROKE:
            return
        t.pet_acc = 0.0
        t.pets += 1
        like = (t.g["cursor"] - 0.5) * 2 * t.g["care"] + 0.35 + t.joy * 0.3 - t.annoy
        if t.state == "sleep":
            if like > 0.3 or t.g["temper"] < 0.3:
                t.joy = min(1.0, t.joy + 0.05)
                t.say("zzz", 1.2)                       # 気持ちよさそうに寝たまま
                return
            t.state = "swim"
            t.fatigue = min(t.fatigue, 0.6)
        if like > 0:
            t.joy = min(1.0, t.joy + 0.15)
            t.annoy = max(0.0, t.annoy - 0.1)
            t.state, t.state_t = "petted", 1.5
            t.say("heart" if t.joy > 0.6 else "note", 1.2)
        else:
            t.annoy = min(1.0, t.annoy + 0.12 + 0.2 * t.g["temper"])
            t.say("anger" if t.annoy > 0.4 else "sweat", 1.2)
            if t.annoy > 0.5:
                t.state, t.state_t = "flee", 1.5

    def poke(self, t):
        if t.state == "lay":
            t.say("anger", 1.0)
            return
        if t.state == "sleep":
            t.annoy = min(1.0, t.annoy + 0.25 + 0.4 * t.g["temper"])
            t.fatigue = min(t.fatigue, 0.6)
            t.state, t.state_t = "flipped", 1.5
            t.say("anger" if t.annoy > 0.5 else "question", 1.5)
            return
        t.annoy = min(1.0, t.annoy + 0.1 + 0.35 * t.g["temper"] * t.g["care"])
        t.state, t.state_t = "flipped", 2.5
        t.say("bang", 1.0)

    def turtle_info(self, t):
        """カメのステータス(英語の行のリスト)。"""
        if not t.alive:
            return ["#%d  Lineage %s  Gen %d" % (t.id, t.lineage, t.generation),
                    "Died of %s at %s" % (t.cause, fmt_dur(t.age))]
        e = t.energy
        health = "Good" if e > 0.7 else "OK" if e > 0.4 else "Hungry" if e > 0.2 else "Starving"
        mood = "annoyed" if t.annoy > 0.5 else "happy" if t.joy > 0.6 else "calm"
        now = {"swim": "swimming", "food": "looking for food", "court": "courting",
               "nest": "going ashore to lay eggs", "lay": "laying eggs", "sleep": "sleeping",
               "flipped": "flipped over!", "dance": "dancing with joy", "flee": "running away",
               "flee_shark": "fleeing from the shark!", "breathe": "surfacing for air",
               "petted": "enjoying being petted"}
        if not self.in_water(t.x, t.y) and t.state == "swim":
            st = "crawling to the sea"
        else:
            st = now.get(t.state, t.state)
        lines = ["#%d  %s  Lineage %s  Gen %d" % (t.id, "Female" if t.sex == "F" else "Male",
                                                   t.lineage, t.generation),
                 "Age %s / %s%s" % (fmt_dur(t.age), fmt_dur(t.lifespan),
                                    "" if t.adult else "  (hatchling)"),
                 "Health %d%% (%s)   Mood: %s" % (round(e * 100), health, mood),
                 "%s   Size x%d%s" % ("Herbivore" if t.herbivore else "Omnivore", t.scale,
                                      "  (shark target)" if t.scale >= SHARK_PREY_SCALE else ""),
                 "Traits: " + (", ".join(traits(t.g)) or "Average")]
        if t.parents:
            lines.append("Origin: " + t.parents)
        if t.clutch:
            lines.append("Carrying %d eggs%s" % (len(t.clutch),
                                                 "" if self.night > 0.3 else " (waits for dark to nest)"))
        if t.pets:
            lines.append("Petted %d time%s" % (t.pets, "s" if t.pets != 1 else ""))
        lines.append("Now: " + st)
        return lines

    def hover_info(self, x, y):
        """マウスの下にある卵・クラゲ・水草・サメの説明(カメはクリックで表示)。"""
        for e in self.eggs:
            if math.hypot(e.x - x, e.y - y) < 7:
                return ["Egg  Lineage %s  Gen %d" % (e.lineage, e.generation),
                        "Parents: %s" % e.parents, "Hatches in %s" % fmt_dur(max(0, e.t))]
        sh = self.shark
        if sh and math.hypot(sh.x - x, sh.y - y) < 32:
            return ["Shark!", "Hunts turtles of size x%d or bigger offshore" % SHARK_PREY_SCALE,
                    "Small turtles and the shallows are safe"]
        for j in self.jellies:
            if math.hypot(j.x - x, j.y - y) < 8:
                return ["Jellyfish", "Food for omnivores"]
        for p in self.plants:
            if math.hypot(p.x - x, p.y - y) < 4 + 3 * p.stage:
                return ["Seaweed  %d%%" % round(p.b * 100),
                        "Regrows when not overgrazed"]
        return None

    # ---- 留守中の時間経過(1分刻みでまとめて計算)
    def advance_offline(self, seconds, start=None):
        """start: 閉じた時刻(UNIX時間)。昼夜をその時刻から再現する。"""
        seconds = min(max(0.0, seconds), OFFLINE_MAX)
        if start is None:
            start = self.clock() - seconds
        self._off_ts = start
        b0, d0, l0 = self.births, self.deaths, self.laid
        steps = int(seconds // OFFLINE_STEP)
        rest = seconds - steps * OFFLINE_STEP
        for i in range(steps + 1):
            dt = OFFLINE_STEP if i < steps else rest
            if dt > 0:
                self._offline_step(dt)
        self.jellies = []
        self.shark = None
        self.update_daylight(self.clock(), log=False)
        for t in self.turtles:
            t.emote, t.food, t.target = None, None, None
            if t.state not in ("sleep", "dead"):
                t.state = "swim"
        self._decompose(force=True)
        return self.births - b0, self.deaths - d0, self.laid - l0

    def _offline_step(self, dt):
        self.time += dt
        self._off_ts = getattr(self, "_off_ts", self.clock()) + dt
        self.update_daylight(self._off_ts, log=False)
        self._grow_plants(dt)
        jelly_in = min(JELLY_MAX, dt / JELLY_INTERVAL)      # 流れてくるクラゲ(平均)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        random.shuffle(alive)
        for t in alive:
            t.age += dt
            t.mate_cd -= dt
            awake = t.awake_len / (t.awake_len + t.sleep_len) * (1 - 0.8 * t.night_pull(self.night))
            t.energy -= t.metab * dt * (awake + 0.35 * (1 - awake))
            t.joy = max(0.0, t.joy - 0.015 * dt)
            t.annoy = max(0.0, t.annoy - 0.02 * dt)
            # 食べる(雑食はクラゲ優先、草食は水草)
            tries = 0
            while t.energy < t.eat_below and tries < 6:
                tries += 1
                if not t.herbivore and jelly_in >= 1 or (not t.herbivore and random.random() < jelly_in):
                    jelly_in = max(0.0, jelly_in - 1)
                    t.energy += JELLY_ENERGY
                    continue
                p = max(self.plants, key=lambda p: p.b, default=None)
                if p is None or p.b < PLANT_EDIBLE:
                    break
                bite = min(PLANT_BITE, p.b - PLANT_MIN)
                p.b -= bite
                t.energy += bite * (1.5 if t.herbivore else 0.9)
            t.energy = min(1.0, t.energy)
            if t.energy <= 0:
                self._kill(t, "starvation")
            elif t.age >= t.lifespan:
                self._kill(t, "old age")
        self._decompose(force=True)
        # サメ(平均 30分に1回現れ、半分の確率で大きなカメを1匹食べる)
        if random.random() < dt / (sum(SHARK_GAP) / 2) * 0.5:
            big = [t for t in self.turtles if t.alive and t.scale >= SHARK_PREY_SCALE]
            if big:
                self._kill(random.choice(big), "a shark attack")
        self._decompose(force=True)
        # 卵がかえる(子ガメは波打ち際の海へ)
        for e in list(self.eggs):
            e.t -= dt
            if e.t <= 0:
                self.eggs.remove(e)
                x = e.x
                t = Turtle(e.g, x, self.shore(x) - 15, e.generation, age=-e.t, sex=e.sex,
                           lineage=e.lineage, parents=e.parents)
                t.energy = HATCH_ENERGY
                self.turtles.append(t)
                self.births += 1
                self.max_gen = max(self.max_gen, e.generation)
        # 交尾 → すぐ砂浜に産卵
        for t in self.turtles:
            if t.clutch:
                t.x, t.y = self.beach_point(t.x)
                self._lay(t)
                t.x, t.y = self.water_point(30)
        fem = [t for t in self.turtles if t.sex == "F" and self._can_mate(t)]
        mal = [t for t in self.turtles if t.sex == "M" and self._can_mate(t)]
        random.shuffle(fem)
        random.shuffle(mal)
        for f, m in zip(fem, mal):
            if random.random() < 0.5 and self._can_mate(f) and self._can_mate(m):
                self._mate(f, m)
        if not self.alive() and not self.eggs:
            self._refound()
        self._record(dt)

    # ---- 保存
    def to_dict(self):
        return {"version": VERSION, "w": self.w, "h": self.h,
                "turtles": [t.to_dict() for t in self.turtles if t.alive],
                "eggs": [e.to_dict() for e in self.eggs],
                "plants": [[p.x, p.y, p.b] for p in self.plants],
                "births": self.births, "deaths": self.deaths, "laid": self.laid,
                "merges": self.merges, "splits": self.splits, "max_gen": self.max_gen,
                "n_lineages": self.n_lineages, "gene_pool": self.gene_pool,
                "events": self.events, "history": self.history}

    @classmethod
    def from_dict(cls, d):
        wd = cls(d.get("w", 640), d.get("h", 420))
        wd.turtles = [Turtle.from_dict(x) for x in d.get("turtles", [])]
        for t in wd.turtles:    # 旧版のデータは陸地の分だけ上にずらす
            if wd.in_water(t.x, t.y) is False and not t.clutch:
                t.y = wd.shore(t.x) - 20
        wd.eggs = [Egg.from_dict(e) for e in d.get("eggs", [])]
        for e in wd.eggs:
            if wd.in_water(e.x, e.y):
                e.x, e.y = wd.beach_point(e.x)
        wd.plants = [Plant(*p) for p in d.get("plants", [])]
        if not wd.plants:
            wd.seed_plants()
        for k in ("births", "deaths", "laid", "merges", "splits"):
            setattr(wd, k, d.get(k, 0))
        wd.max_gen = d.get("max_gen", 1)
        wd.gene_pool = [fill_genome(g) for g in d.get("gene_pool", [])]
        wd.n_lineages = d.get("n_lineages", 0) or max(1, len({t.lineage for t in wd.turtles}))
        wd.events = [tuple(e) for e in d.get("events", []) if len(e) == 3]
        wd.history = [tuple(h) for h in d.get("history", [])]
        return wd

    def resize(self, w, h):
        if w < 100 or h < 100:
            return
        old_lt, old_h = self.land_top, self.h
        sx = w / self.w
        self.w, self.h = w, h
        new_lt = self.land_top

        def my(y):   # 水の部分と陸の部分をそれぞれ伸縮
            if y <= old_lt:
                return y * new_lt / old_lt
            return new_lt + (y - old_lt) * (h - new_lt) / max(1.0, old_h - old_lt)
        for o in self.turtles + self.eggs + self.plants + self.jellies + ([self.shark] if self.shark else []):
            o.x *= sx
            o.y = my(o.y)
        for t in self.turtles:
            if t.nest:
                t.nest = (t.nest[0] * sx, my(t.nest[1]))


# ---------------------------------------------------------------- 保存先(Google ドライブ)
def find_save_dir():
    """(フォルダ, Googleドライブかどうか) を返す。"""
    env = os.environ.get("UMIGAME_SAVE_DIR")
    if env:
        return env, True
    home = os.path.expanduser("~")
    names = ("マイドライブ", "My Drive")
    cands = []
    if sys.platform.startswith("win"):
        for letter in string.ascii_uppercase[3:]:          # D: 〜 Z:(G: が既定)
            for n in names:
                cands.append(f"{letter}:\\{n}")
        for n in names:
            cands.append(os.path.join(home, "Google Drive", n))
        cands.append(os.path.join(home, "Google Drive"))
    else:
        for p in glob.glob(os.path.join(home, "Library", "CloudStorage", "GoogleDrive-*")):
            for n in names:
                cands.append(os.path.join(p, n))
        for n in names:
            cands.append(os.path.join(home, "Google Drive", n))
            cands.append(os.path.join(home, "GoogleDrive", n))
        cands.append(os.path.join(home, "Google Drive"))
    for c in cands:
        try:
            if os.path.isdir(c):
                return os.path.join(c, "UmigamePet"), True
        except OSError:
            pass
    return os.path.join(home, "UmigamePet"), False


def save_world(world, folder):
    os.makedirs(folder, exist_ok=True)
    data = world.to_dict()
    data["saved_at"] = time.time()
    path = os.path.join(folder, SAVE_NAME)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def load_world(folder):
    """(world, 経過秒) を返す。ファイルが無い・壊れているときは (None, 0)。"""
    path = os.path.join(folder, SAVE_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        world = World.from_dict(data)
        return world, max(0.0, time.time() - float(data.get("saved_at", time.time())))
    except (OSError, ValueError, KeyError, TypeError):
        return None, 0.0


def fmt_dur(sec):
    sec = int(sec)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm" % (sec // 60)
    if sec < 86400:
        return "%dh %dm" % (sec // 3600, sec % 3600 // 60)
    return "%dd %dh" % (sec // 86400, sec % 86400 // 3600)


# ---------------------------------------------------------------- ドット絵
# 上から見たウミガメ(上向き)。H=頭 E=目 S=甲羅 F=ひれ T=しっぽ
FRAMES = (
    ("....HHH....",
     "....EHE....",
     "FF..SSS..FF",
     ".FFSSSSSFF.",
     "..SSSSSSS..",
     "..SSSSSSS..",
     "..SSSSSSS..",
     "..SSSSSSS..",
     ".FFSSSSSFF.",
     "F...SSS...F",
     ".....T....."),
    ("....HHH....",
     "....EHE....",
     "....SSS....",
     "FFFSSSSSFFF",
     ".FSSSSSSSF.",
     "..SSSSSSS..",
     "..SSSSSSS..",
     "..SSSSSSS..",
     "..FSSSSSF..",
     ".F..SSS..F.",
     ".....T....."),
)

EMOTES = {
    "heart": ("#ff4f7b", (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X...")),
    "note": ("#ffd23f", ("...XXX.", "...X.X.", "...X...", "...X...", ".XXX...", "XXXX...", ".XX....")),
    "anger": ("#ff2a2a", (".X...X.", "XX...XX", ".......", ".......", "XX...XX", ".X...X.")),
    "zzz": ("#ffffff", ("XXXXX", "...X.", "..X..", ".X...", "XXXXX")),
    "bang": ("#ffffff", (".X.", ".X.", ".X.", ".X.", "...", ".X.")),
    "question": ("#ffffff", (".XXX.", "X...X", "...X.", "..X..", ".....", "..X..")),
    "sparkle": ("#fff7a8", ("...X...", "...X...", "..XXX..", "XXXXXXX", "..XXX..", "...X...", "...X...")),
    "sweat": ("#2f7fff", ("..X..", ".XXX.", "XXXXX", "XXXXX", ".XXX.")),
    "egg": ("#fffdf0", (".XX.", "XXXX", "XXXX", "XXXX", ".XX.")),
    "puff": ("#ffffff", (".XX.X.", "XXXXXX", ".XXXX.")),
    "ghost": ("#f4f4ff", (".XXX.", "XXXXX", "X.X.X", "XXXXX", "XXXXX", "X.X.X")),
}
PLANT_ART = (
    (".g.g.",
     "..g..",
     ".g.g."),
    ("...G...",
     "..gGg..",
     ".GgggG.",
     "..gGg..",
     "...G..."),
    ("...G.G...",
     "....g....",
     ".G.gGg.G.",
     "..ggggg..",
     "GgGgggGgG",
     "..ggggg..",
     ".G.gGg.G.",
     "....g....",
     "...G.G..."),
    ("...G...G...",
     "....g.g....",
     ".G..gGg..G.",
     "..g.ggg.g..",
     "...gGgGg...",
     "GggGgggGggG",
     "...gGgGg...",
     "..g.ggg.g..",
     ".G..gGg..G.",
     "....g.g....",
     "...G...G..."),
)
# サメ(上から見た、右向き)。B=背 b=腹側の縁 E=目 F=ひれ
SHARK_ART = (
    ("...........F..........",
     "..........FF..........",
     "F.......BBBBBBBBB.....",
     "FF..BBBBBBBBBBBBBBBB..",
     ".FBBBBBBBBBBBBBBBBBEb.",
     "FF..BBBBBBBBBBBBBBBB..",
     "F.......BBBBBBBBB.....",
     "..........FF..........",
     "...........F.........."),
    ("..........F...........",
     "..........FF..........",
     ".F......BBBBBBBBB.....",
     "..F.BBBBBBBBBBBBBBBB..",
     "..BBBBBBBBBBBBBBBBBEb.",
     "..F.BBBBBBBBBBBBBBBB..",
     ".F......BBBBBBBBB.....",
     "..........FF..........",
     "..........F..........."),
)
JELLY_ART = (".XXX.", "XXXXX", "X.X.X", "X.X.X")
EGG_ART = (".XX.", "XXXX", "XXXX", ".XX.")
STAR_ART = ("..X..", "..X..", "XXXXX", ".XXX.", "X...X")

WATER_DEEP = (0x14, 0xb3, 0xc8)      # 沖(上)
WATER_SHALLOW = (0x8c, 0xf0, 0xdf)   # 波打ち際
SAND_WET = "#e9cf8d"
SAND_DRY = "#f8e9b8"


def rotate(grid, d):
    """上向きの格子を d(0上 1右 2下 3左)の向きへ回す。"""
    g = [list(r) for r in grid]
    for _ in range(d):
        g = [list(r) for r in zip(*g[::-1])]
    return g


def hexcol(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def turtle_pixels(g, frame, mode):
    """mode: normal / belly(ひっくり返り)/ dead。上向き 11x11 の色の格子。"""
    base = FRAMES[frame]
    shell = hexcol(g["hue"], 0.6, 0.55)
    rim = hexcol(g["hue"], 0.65, 0.32)
    pat = hexcol(g["hue2"], 0.65, 0.92)
    skin = hexcol(g["hue"] + 0.08, 0.4, 0.62)
    eye = "#101010"
    if mode == "belly":
        shell, rim, pat = "#f2e6b0", "#a89860", "#d9c98e"
    if mode == "dead":
        shell, rim, pat, skin, eye = "#9a9a9a", "#6a6a6a", "#8a8a8a", "#b0b0b0", "#505050"
    out = []
    for y, row in enumerate(base):
        line = []
        for x, c in enumerate(row):
            if c == "S":
                edge = x == 0 or x == 10 or row[x - 1] != "S" or row[x + 1] != "S"
                if edge or y == 2 or y == 9:
                    col = rim
                elif mode == "belly":
                    col = pat if (x + y) % 3 == 0 else shell
                else:
                    mx = x if x <= 5 else 10 - x          # 左右対称
                    idx = (y - 2) * 4 + (mx - 2)
                    bit = 0 <= idx < PATTERN_BITS and 2 <= mx <= 5 and g["pattern"][idx]
                    col = pat if bit else shell
                line.append(col)
            elif c in "HFT":
                line.append(skin)
            elif c == "E":
                line.append(eye)
            else:
                line.append(None)
        out.append(line)
    return out


# ---------------------------------------------------------------- 画面(tkinter)
def tint_rgb(rgb, k):
    return tuple(min(255, int(c * m)) for c, m in zip(rgb, k))


def hex_rgb(col):
    return tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))


def tint_hex(col, k):
    return "#%02x%02x%02x" % tint_rgb(hex_rgb(col), k)


def water_color(world, y, k=(1, 1, 1)):
    """海の色(沖ほど濃く、波打ち際ほど明るい)に、時間帯の色みをかける。"""
    f = min(1.0, max(0.0, y / max(1.0, world.land_top + 8)))
    return tint_rgb(tuple(int(a + (b - a) * f) for a, b in zip(WATER_DEEP, WATER_SHALLOW)), k)


GLITTER = {   # 水面のきらめき(太陽・月の反射)の色と数
    "Daytime": ("#f4ffff", 6), "Sunrise": ("#ffe3a6", 14), "Sunset": ("#ffc46e", 16),
    "Dusk": ("#e9c2ff", 10), "Dawn twilight": ("#d6e4ff", 8), "Night": ("#f2f6ff", 12),
}


def mix(c1, c2, f):
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


class App:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.save_dir, self.on_drive = find_save_dir()
        self.root = tk.Tk()
        self.root.title("Sea Turtle Colony" + ("" if self.on_drive else " (saved locally)"))
        self.root.geometry("700x440")
        self.root.minsize(320, 220)
        self.canvas = tk.Canvas(self.root, width=700, height=440, bg="#3fd0d4",
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self.topmost = False
        self.show_lineage = False

        world, away = load_world(self.save_dir)
        if world is None:
            self.world = World(700, 440)
            self.world.seed()
            self.banner = "Welcome! A new sea turtle colony is born"
        else:
            self.world = world
            b, d, l = world.advance_offline(away)
            self.banner = ("While you were away: %s passed\nBorn %d   Died %d   Eggs laid %d"
                           % (fmt_dur(away), b, d, l))
        self.banner_t = 8.0

        c = self.canvas
        self.items = {}       # turtle.id -> [image, emote, lineage_text, cache, last_key]
        self.tables = {"plant": {}, "jelly": {}, "egg": {}}
        self.emote_img = {k: self._img(px, {"X": col}, 2) for k, (col, px) in EMOTES.items()}
        self.jelly_img = self._img(JELLY_ART, {"X": "#ffc4ee"}, 2)   # クラゲは夜も光って見える
        self.bg_tint = None
        self.make_tinted_images((1, 1, 1))
        self.shark_item = None
        self.bg_items = []
        self.foam = c.create_line(0, 0, 1, 1, fill="#ffffff", width=2, tags="bg2")
        self.waves = [self._new_wave(first=True) for _ in range(9)]
        self.glitter = [c.create_line(0, 0, 1, 1, width=2, state="hidden", tags="wave")
                        for _ in range(16)]
        self.glit_t = 0.0
        self.light_t = 0.0
        self.fx_items = []    # [item, kind, x, y, t, life]
        self.hud = c.create_text(8, 6, anchor="nw", fill="#04505c", font=("", 9), tags="ui")
        self.graph_box = c.create_rectangle(0, 0, 1, 1, fill="#e9fbf8", outline="#6cc9c9", tags="ui")
        self.graph_title = c.create_text(0, 0, anchor="nw", text="Ecosystem (last 20 min)",
                                         fill="#04505c", font=("", 8), tags="ui")
        self.graph_lines = [c.create_line(0, 0, 1, 1, fill=col, width=2, tags="ui")
                            for col in ("#1d4e89", "#21a35a", "#d24fa8")]
        self.graph_legend = [c.create_text(0, 0, anchor="nw", fill=col, font=("", 8), tags="ui")
                             for col in ("#1d4e89", "#16864a", "#b0338a")]
        self.log_items = [c.create_text(8, 0, anchor="sw", fill="#6b4a12", font=("", 9), tags="ui")
                          for _ in range(3)]
        self.help = c.create_text(0, 0, anchor="sw", fill="#9a7a3c", font=("", 8), tags="ui",
                                  text="Click: status   Double-click: flip   Stroke: pet   "
                                       "Click water: jellyfish   Shift+Click: seaweed   "
                                       "Right-click: on top   L: lineage")
        # 追いかけるステータス表示(カメをクリック)
        self.follow = None
        self.panel_line = c.create_line(0, 0, 1, 1, fill="#0a6e78", state="hidden", tags="panel")
        self.panel_box = c.create_rectangle(0, 0, 1, 1, fill="#fffef6", outline="#0a6e78",
                                            state="hidden", tags="panel")
        self.panel_text = c.create_text(0, 0, anchor="nw", fill="#073b42", font=("", 9),
                                        state="hidden", tags="panel")
        self.panel_size = (0, 0)
        self.panel_t = 0.0
        # マウスを重ねたときの説明(卵・クラゲ・水草・サメ)
        self.tip_box = c.create_rectangle(0, 0, 1, 1, fill="#fffef6", outline="#0a6e78",
                                          state="hidden", tags="tip")
        self.tip_text = c.create_text(0, 0, anchor="nw", fill="#073b42", font=("", 9),
                                      state="hidden", tags="tip")
        self.bann = c.create_text(350, 190, fill="#ffffff", font=("", 13, "bold"),
                                  justify="center", tags="tip")
        self.hud_t = 0.0
        self.tip_t = 0.0
        self.foam_t = 0.0
        self.wave_t = 0.0
        self.order_dirty = True
        self.last = time.monotonic()
        self.last_save = time.monotonic()
        self.prev_cursor = None
        self.mouse = None
        self.click_job = None
        self.draw_background()

        c.bind("<Motion>", self.on_motion)
        c.bind("<Leave>", self.on_leave)
        c.bind("<Button-1>", self.on_click)
        c.bind("<Double-Button-1>", self.on_double)
        c.bind("<Shift-Button-1>", self.on_shift_click)
        c.bind("<Button-3>", self.toggle_topmost)
        c.bind("<Configure>", self.on_resize)
        self.root.bind("<KeyPress-l>", self.toggle_lineage)
        self.root.bind("<KeyPress-L>", self.toggle_lineage)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(TICK_MS, self.tick)

    # ---- 画像
    def _img(self, rows, colors, scale, k=None):
        img = self.tk.PhotoImage(width=len(rows[0]), height=len(rows))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch in colors:
                    img.put(tint_hex(colors[ch], k) if k else colors[ch], to=(x, y))
        return img.zoom(scale)

    def make_tinted_images(self, bg):
        """時間帯の色みに合わせて画像を作り直す(色みが変わったときだけ)。"""
        self.bg_tint = bg
        sp = tuple(0.45 + 0.55 * min(1.1, x) for x in bg)      # 生き物は背景より少し明るく
        self.sprite_tint = sp
        pc = {"g": "#1d8f55", "G": "#5ee08a"}
        self.plant_img = [self._img(PLANT_ART[0], {"g": "#3d8a62"}, 2, sp)] + \
                         [self._img(a, pc, 2, sp) for a in PLANT_ART[1:]]
        self.egg_img = self._img(EGG_ART, {"X": "#fffdf2"}, 2, sp)
        self.star_img = self._img(STAR_ART, {"X": "#ff8a4c"}, 2, bg)
        sc = {"B": "#5d7b8c", "b": "#c9d6dc", "E": "#111111", "F": "#4a6676"}
        self.shark_img = {}
        for f, art in enumerate(SHARK_ART):
            self.shark_img[(1, f)] = self._img(art, sc, 3, sp)
            self.shark_img[(3, f)] = self._img(tuple(r[::-1] for r in art), sc, 3, sp)
        for ent in getattr(self, "items", {}).values():
            ent[3].clear()
            ent[4] = None
        for tab in getattr(self, "tables", {}).values():
            for ent in tab.values():
                ent[1] = None

    def apply_light(self):
        w = self.world
        q = tuple(round(x * 20) / 20 for x in w.tint)
        if q == self.bg_tint:
            return
        self.make_tinted_images(q)
        self.draw_background()
        def lum(rgb):
            return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        sea_dark = lum(tint_rgb(WATER_DEEP, q)) < 0.48         # 文字の色を背景の明るさで切り替える
        sand_dark = lum(tint_rgb(hex_rgb(SAND_DRY), q)) < 0.6
        self.canvas.itemconfigure(self.hud, fill="#f2fbff" if sea_dark else "#04505c")
        for it in self.log_items:
            self.canvas.itemconfigure(it, fill="#fff3d6" if sand_dark else "#6b4a12")
        self.canvas.itemconfigure(self.help, fill="#eadcb8" if sand_dark else "#9a7a3c")
        self.canvas.itemconfigure(self.foam, fill=tint_hex("#ffffff", q))

    def update_glitter(self):
        """太陽・月が水面に映ってきらめく。朝夕は多く、夜は月明かり。"""
        c, w = self.canvas, self.world
        col, n = GLITTER.get(w.phase, ("#ffffff", 6))
        frac = (w.hour % 24) / 24.0
        cx = w.w * (0.15 + 0.7 * ((frac * 2) % 1.0))           # 時刻で横に動く
        for i, it in enumerate(self.glitter):
            if i >= n or random.random() < 0.25:
                c.itemconfigure(it, state="hidden")
                continue
            y = random.uniform(10, w.land_top * 0.8)
            x = cx + random.gauss(0, 18 + y * 0.12)
            ln = random.uniform(3, 10)
            c.coords(it, x - ln, y, x + ln, y)
            c.itemconfigure(it, fill=col, state="normal")

    def turtle_img(self, t, cache, key):
        img = cache.get(key)
        if img is None:
            d, frame, mode, scale = key
            px = rotate(turtle_pixels(t.g, frame, mode), d)
            raw = self.tk.PhotoImage(width=11, height=11)
            k = self.sprite_tint
            for y, row in enumerate(px):
                for x, col in enumerate(row):
                    if col:
                        raw.put(tint_hex(col, k), to=(x, y))
            img = raw.zoom(scale) if scale > 1 else raw
            cache[key] = img
        return img

    # ---- 背景(海のグラデーション・砂浜・ヒトデ)
    def draw_background(self):
        c, w = self.canvas, self.world
        for it in self.bg_items:
            c.delete(it)
        self.bg_items = []
        bands = 10
        top = w.land_top + 8
        k = self.bg_tint
        for i in range(bands):
            f = i / (bands - 1)
            col = mix(tint_rgb(WATER_DEEP, k), tint_rgb(WATER_SHALLOW, k), f)
            y0, y1 = top * i / bands, top * (i + 1) / bands + 1
            self.bg_items.append(c.create_rectangle(0, y0, w.w, y1, fill=col, width=0, tags="bg"))
        xs = list(range(0, int(w.w) + 16, 16))
        wet = [v for x in xs for v in (x, w.shore(x))] + [w.w, w.h, 0, w.h]
        dry = [v for x in xs for v in (x, w.shore(x) + 9)] + [w.w, w.h, 0, w.h]
        self.bg_items.append(c.create_polygon(*wet, fill=tint_hex(SAND_WET, k), outline="", tags="bg"))
        self.bg_items.append(c.create_polygon(*dry, fill=tint_hex(SAND_DRY, k), outline="", tags="bg"))
        rnd = random.Random(7)
        for _ in range(2):
            x, y = w.beach_point(rnd.uniform(w.w * 0.55, w.w - 30))
            self.bg_items.append(c.create_image(x, min(y, w.h - 12), image=self.star_img, tags="bg"))
        for _ in range(14):     # 砂の粒
            x = rnd.uniform(0, w.w)
            y = rnd.uniform(w.shore(x) + 12, w.h - 2)
            self.bg_items.append(c.create_rectangle(x, y, x + 2, y + 2, fill=tint_hex("#e3c98a", k),
                                                    width=0, tags="bg"))
        self.order_dirty = True
        self.layout_ui()

    def layout_ui(self):
        c, w = self.canvas, self.world
        gx1, gy0 = w.w - 8, 6
        gx0, gy1 = gx1 - 214, gy0 + 72
        self.graph_rect = (gx0 + 4, gy0 + 16, gx1 - 4, gy1 - 18)
        c.coords(self.graph_box, gx0, gy0, gx1, gy1)
        c.coords(self.graph_title, gx0 + 4, gy0 + 2)
        for i, it in enumerate(self.graph_legend):
            c.coords(it, gx0 + 4 + (0, 66, 150)[i], gy1 - 15)
        n = len(self.log_items)
        for i, it in enumerate(self.log_items):
            c.coords(it, 8, w.h - 16 - (n - 1 - i) * 14)
        c.coords(self.help, 8, w.h - 2)
        c.coords(self.bann, w.w / 2, w.land_top / 2)
        self.draw_graph()

    # ---- 波(沖から砂浜へ寄せてくる白い波頭)
    def _new_wave(self, first=False):
        it = self.canvas.create_line(0, 0, 1, 1, fill="#ffffff", width=2, smooth=True,
                                     capstyle="round", tags="wave")
        wv = {"item": it}
        self._reset_wave(wv, first)
        return wv

    def _reset_wave(self, wv, first=False):
        w = self.world
        x = random.uniform(-20, w.w - 40)
        y0 = random.uniform(8, w.land_top * 0.35)
        wv.update(x=x, y0=y0, y=random.uniform(y0, w.land_top * 0.9) if first else y0,
                  len=random.uniform(50, 120), amp=random.uniform(2, 5),
                  sp=random.uniform(6, 12), ph=random.uniform(0, math.tau))

    def update_waves(self, dt, recolor):
        c, w = self.canvas, self.world
        for wv in self.waves:
            wv["y"] += wv["sp"] * dt
            wv["x"] += math.sin(w.time * 0.3 + wv["ph"]) * 2 * dt
            x0, y = wv["x"], wv["y"]
            end = w.shore(x0 + wv["len"] / 2) - 6
            if y > end:
                self._reset_wave(wv)
                continue
            f = (y - wv["y0"]) / max(1.0, end - wv["y0"])
            amp = wv["amp"] * (1 + 0.3 * math.sin(w.time * 1.5 + wv["ph"]))
            pts = []
            for k in range(7):
                pts += [x0 + wv["len"] * k / 6, y - amp * math.sin(math.pi * k / 6)]
            c.coords(wv["item"], *pts)
            if recolor:     # 出てくる時と消える時は海の色に近づける(フェード)
                fade = math.sin(math.pi * min(1.0, max(0.0, f))) ** 0.7
                k = self.bg_tint
                c.itemconfigure(wv["item"], fill=mix(water_color(w, y, k), tint_rgb((255, 255, 255), k),
                                                     0.75 * fade))

    # ---- 演出(息継ぎの波紋・クラゲのしぶき・サメのひと噛み)
    def add_fx(self, kind, x, y):
        if len(self.fx_items) > 24:
            return
        col = {"ripple": "#ffffff", "splash": "#ffffff", "bite": "#ff3434"}.get(kind, "#ffffff")
        n = 2 if kind in ("ripple", "bite") else 1
        for k in range(n):
            it = self.canvas.create_oval(x, y, x, y, outline=col, width=2 if kind == "bite" else 1,
                                         tags="fx")
            self.fx_items.append([it, kind, x, y, -0.35 * k, 1.3 if kind != "splash" else 0.6])
        self.order_dirty = True

    def update_fx(self, dt):
        c = self.canvas
        keep = []
        for f in self.fx_items:
            f[4] += dt
            it, kind, x, y, t, life = f
            if t > life:
                c.delete(it)
                continue
            if t >= 0:
                r = 3 + t / life * (22 if kind != "splash" else 10)
                c.coords(it, x - r, y - r * 0.8, x + r, y + r * 0.8)
            keep.append(f)
        self.fx_items = keep

    # ---- マウス
    def on_motion(self, e):
        now = time.monotonic()
        dist = 0.0
        if self.prev_cursor:
            px, py, pt = self.prev_cursor
            dist = math.hypot(e.x - px, e.y - py)
            self.world.cursor_speed = dist / max(1e-3, now - pt)
        self.prev_cursor = (e.x, e.y, now)
        self.world.cursor = (e.x, e.y)
        self.mouse = (e.x, e.y)
        self.tip_t = 0.0
        if 0 < dist < 80:                     # カメの上でカーソルを動かす = なでる
            t = self.world.hit(e.x, e.y, pad=0)
            if t:
                self.world.pet(t, dist)

    def on_leave(self, e):
        self.world.cursor = None
        self.mouse = None
        self.prev_cursor = None
        self.canvas.itemconfigure("tip", state="hidden")
        self.canvas.itemconfigure(self.bann, state="normal")

    def on_click(self, e):
        # ダブルクリックと区別するため、少し待ってから処理する
        if self.click_job:
            self.root.after_cancel(self.click_job)
        t = self.world.hit(e.x, e.y, pad=6)        # 押した瞬間のカメで判定する
        self.click_job = self.root.after(280, lambda: self.on_single(t, e.x, e.y))

    def on_single(self, t, x, y):
        self.click_job = None
        if t is not None and not t.alive and t.id != self.follow:
            t = None
        if t:
            self.follow = None if self.follow == t.id else t.id
            self.panel_t = 0.0
            if self.follow is None:
                self.canvas.itemconfigure("panel", state="hidden")
        elif self.world.in_water(x, y):
            self.world.drop_jelly(x, y)

    def on_double(self, e):
        if self.click_job:
            self.root.after_cancel(self.click_job)
            self.click_job = None
        t = self.world.hit(e.x, e.y, pad=6)
        if t:
            self.world.poke(t)
        elif self.world.in_water(e.x, e.y):
            self.world.drop_jelly(e.x, e.y)

    def on_shift_click(self, e):
        if not self.world.hit(e.x, e.y):
            self.world.drop_plant(e.x, e.y)

    def toggle_topmost(self, e=None):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.banner, self.banner_t = ("Always on top: ON" if self.topmost else "Always on top: OFF"), 1.5

    def toggle_lineage(self, e=None):
        self.show_lineage = not self.show_lineage

    def on_resize(self, e):
        if (e.width, e.height) == (int(self.world.w), int(self.world.h)):
            return
        self.world.resize(e.width, e.height)
        for tab in self.tables.values():
            for ent in tab.values():
                self.canvas.delete(ent[0])
            tab.clear()
        for wv in self.waves:
            self._reset_wave(wv, first=True)
        self.draw_background()

    def on_close(self):
        try:
            save_world(self.world, self.save_dir)
        except OSError as ex:
            print("Could not save:", ex, file=sys.stderr)
        self.root.destroy()

    # ---- 毎フレーム
    def tick(self):
        now = time.monotonic()
        dt = now - self.last
        self.last = now
        if now - self.last_save > AUTOSAVE_SEC:
            self.last_save = now
            try:
                save_world(self.world, self.save_dir)
            except OSError:
                pass
        self.world.step(dt)
        self.world.cursor_speed *= 0.5
        if self.root.state() == "iconic":        # 最小化中は描画しない
            self.world.fx.clear()
            self.root.after(1000, self.tick)
            return
        self.render(dt)
        self.root.after(TICK_MS, self.tick)

    def render(self, dt):
        c, w = self.canvas, self.world
        self._sync("plant", w.plants, lambda p: self.plant_img[p.stage], move=False)
        self._sync("egg", w.eggs, lambda e: self.egg_img, move=False)
        self._sync("jelly", w.jellies, lambda o: self.jelly_img)

        seen = set()
        for t in w.turtles:
            seen.add(t.id)
            ent = self.items.get(t.id)
            if ent is None:
                ent = [c.create_image(t.x, t.y, tags="turtle"), None, None, {}, None]
                self.items[t.id] = ent
                self.order_dirty = True
            if t.state == "dead":
                key = (2, 0, "dead", t.scale)
            elif t.state == "flipped":
                key = (t.dir, int(t.anim / 0.12) % 2, "belly", t.scale)
            elif t.state in ("sleep", "lay", "petted"):
                key = (t.dir, 0, "normal", t.scale)
            elif t.state == "breathe":
                key = (t.dir, int(t.anim / 0.8) % 2, "normal", t.scale)
            else:
                water = w.in_water(t.x, t.y)
                period = 0.2 if t.state in ("flee", "food", "flee_shark") else (0.6 if not water else 0.45)
                key = (t.dir, int(t.anim / period) % 2, "normal", t.scale)
            if key != ent[4]:
                c.itemconfigure(ent[0], image=self.turtle_img(t, ent[3], key))
                ent[4] = key
            c.coords(ent[0], round(t.x), round(t.y))
            ey = t.y - t.radius - 9
            if t.emote:
                if ent[1] is None:
                    ent[1] = c.create_image(t.x, ey, image=self.emote_img[t.emote], tags="fx")
                    self.order_dirty = True
                else:
                    c.itemconfigure(ent[1], image=self.emote_img[t.emote])
                    c.coords(ent[1], round(t.x), round(ey))
            elif ent[1] is not None:
                c.delete(ent[1])
                ent[1] = None
            if self.show_lineage and t.alive:
                lx, ly = round(t.x + t.radius + 4), round(t.y - t.radius)
                if ent[2] is None:
                    ent[2] = c.create_text(lx, ly, text=t.lineage, fill="#063f47",
                                           font=("", 8, "bold"), tags="fx")
                    self.order_dirty = True
                else:
                    c.coords(ent[2], lx, ly)
            elif ent[2] is not None:
                c.delete(ent[2])
                ent[2] = None
        for tid in list(self.items):
            if tid not in seen:
                ent = self.items.pop(tid)
                for it in ent[:3]:
                    if it is not None:
                        c.delete(it)

        sh = w.shark
        if sh:
            img = self.shark_img[(sh.dir, int(sh.anim / 0.35) % 2)]
            if self.shark_item is None:
                self.shark_item = c.create_image(sh.x, sh.y, image=img, tags="shark")
                self.order_dirty = True
            else:
                c.itemconfigure(self.shark_item, image=img)
                c.coords(self.shark_item, round(sh.x), round(sh.y))
        elif self.shark_item is not None:
            c.delete(self.shark_item)
            self.shark_item = None

        for kind, x, y in w.fx:
            self.add_fx(kind, x, y)
        w.fx.clear()
        self.update_fx(dt)
        self.wave_t += dt
        recolor = self.wave_t > 0.3
        if recolor:
            self.wave_t = 0.0
        self.update_waves(dt, recolor)
        self.glit_t += dt
        if self.glit_t > 0.3:
            self.glit_t = 0.0
            self.update_glitter()
        self.light_t -= dt
        if self.light_t <= 0:
            self.light_t = 5.0
            self.apply_light()
        if w.phase_msg:
            self.banner, self.banner_t = w.phase_msg, 4.0
            w.phase_msg = None
        self.foam_t += dt
        if self.foam_t > 0.2:
            ph = w.time * 1.3
            xs = range(0, int(w.w) + 12, 12)
            pts = [v for x in xs for v in (x, w.shore(x) - 1.5 - 1.5 * math.sin(ph + x / 45.0))]
            c.coords(self.foam, *pts)
            self.foam_t = 0.0

        if self.order_dirty:     # 重なり順
            for tag in ("bg", "wave", "bg2", "plant", "egg", "jelly", "turtle", "shark", "fx",
                        "ui", "panel", "tip"):
                c.tag_raise(tag)
            self.order_dirty = False

        self.hud_t -= dt
        if self.hud_t <= 0:
            self.hud_t = 1.0
            alive = w.alive()
            nf = sum(t.sex == "F" for t in alive)
            herb = sum(t.herbivore for t in alive)
            c.itemconfigure(self.hud, text=(
                "%s %s   Turtles %d (F%d M%d, herb %d / omni %d)   Eggs %d   Gen %d\n"
                "Seaweed %d   Jellyfish %d   Born %d   Died %d   Merged %d   Split %d%s"
                % (time.strftime("%H:%M", time.localtime(w.now_ts)), w.phase, len(alive), nf, len(alive) - nf, herb, len(alive) - herb, len(w.eggs), w.max_gen,
                   len(w.plants), len(w.jellies), w.births, w.deaths, w.merges, w.splits,
                   "   SHARK!" if w.shark else "")))
            for i, it in enumerate(self.log_items):
                k = len(w.events) - len(self.log_items) + i
                c.itemconfigure(it, text=("%s  %s" % (w.events[k][0], w.events[k][2])) if k >= 0 else "")
            self.draw_graph()

        self.update_panel(dt)
        self.tip_t -= dt
        if self.mouse and self.tip_t <= 0:
            self.tip_t = 0.25
            self.update_tip()
        if self.banner:
            self.banner_t -= dt
            c.itemconfigure(self.bann, text=self.banner if self.banner_t > 0 else "")
            if self.banner_t <= 0:
                self.banner = None

    def update_panel(self, dt):
        """クリックしたカメのステータスを、カメについて回るように表示する。"""
        if self.follow is None:
            return
        c, w = self.canvas, self.world
        t = next((x for x in w.turtles if x.id == self.follow), None)
        if t is None:            # 死骸が消えた(または合体・分裂した)
            self.follow = None
            c.itemconfigure("panel", state="hidden")
            return
        self.panel_t -= dt
        if self.panel_t <= 0:
            self.panel_t = 0.25
            c.itemconfigure(self.panel_text, text="\n".join(w.turtle_info(t)), state="normal")
            x0, y0, x1, y1 = c.bbox(self.panel_text)
            self.panel_size = (x1 - x0 + 12, y1 - y0 + 10)
        pw, ph = self.panel_size
        gap = t.radius + 14
        x = t.x + gap if t.x + gap + pw < w.w - 4 else t.x - gap - pw
        y = min(max(4, t.y - ph / 2), w.h - ph - 4)
        c.coords(self.panel_box, x, y, x + pw, y + ph)
        c.coords(self.panel_text, x + 6, y + 5)
        ax = x if x > t.x else x + pw
        c.coords(self.panel_line, t.x, t.y, ax, min(max(y + 6, t.y), y + ph - 6))
        c.itemconfigure(self.panel_box, state="normal")
        c.itemconfigure(self.panel_line, state="normal")

    def update_tip(self):
        c = self.canvas
        mx, my = self.mouse
        info = None if self.world.hit(mx, my, pad=2) else self.world.hover_info(mx, my)
        if not info:
            c.itemconfigure("tip", state="hidden")
            c.itemconfigure(self.bann, state="normal")
            return
        c.itemconfigure(self.tip_text, text="\n".join(info), state="normal")
        x0, y0, x1, y1 = c.bbox(self.tip_text)
        tw, th = x1 - x0 + 12, y1 - y0 + 10
        x = mx + 16 if mx + 16 + tw < self.world.w else mx - 16 - tw
        y = min(max(4, my + 12), self.world.h - th - 4)
        c.coords(self.tip_box, x, y, x + tw, y + th)
        c.coords(self.tip_text, x + 6, y + 5)
        c.itemconfigure(self.tip_box, state="normal")
        c.itemconfigure(self.bann, state="hidden")

    def draw_graph(self):
        c, h = self.canvas, self.world.history
        x0, y0, x1, y1 = self.graph_rect
        cur = (sum(t.alive for t in self.world.turtles), sum(p.b for p in self.world.plants),
               len(self.world.jellies))
        data = list(h) + [cur]
        names = ("Turtles %d", "Seaweed %.1f", "Jellyfish %d")
        for i in range(3):
            vals = [d[i] for d in data]
            top = max(max(vals), 1e-6)
            if len(vals) < 2:
                vals = vals * 2
            pts = []
            for k, v in enumerate(vals):
                pts += [x0 + (x1 - x0) * k / (len(vals) - 1), y1 - (y1 - y0) * v / top]
            c.coords(self.graph_lines[i], *pts)
            c.itemconfigure(self.graph_legend[i], text=names[i] % cur[i])

    def _sync(self, name, objs, img_fn, move=True):
        c, table = self.canvas, self.tables[name]
        ids = set()
        for o in objs:
            k = id(o)
            ids.add(k)
            ent = table.get(k)
            img = img_fn(o)
            if ent is None:
                table[k] = [c.create_image(round(o.x), round(o.y), image=img, tags=name), img]
                self.order_dirty = True
            else:
                if ent[1] is not img:
                    c.itemconfigure(ent[0], image=img)
                    ent[1] = img
                if move:
                    c.coords(ent[0], round(o.x), round(o.y))
        for k in list(table):
            if k not in ids:
                c.delete(table.pop(k)[0])

    def run(self):
        self.root.mainloop()

def main():
    try:
        App().run()
    except Exception:
        import traceback
        msg = traceback.format_exc()
        print(msg, file=sys.stderr)
        try:   # ダブルクリック起動ではコンソールがすぐ閉じるので画面に出す
            import tkinter.messagebox as mb
            mb.showerror("Sea Turtle Colony", msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
