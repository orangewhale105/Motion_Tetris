# -*- coding: utf-8 -*-
"""
Sea Turtle Colony(ウミガメ群体)— デスクトップで動く人工生命の小さなペット

・標準ライブラリだけで動く(tkinter)。pip install 不要。画面の表示は英語。
・上から見た南国の海(ターコイズブルー)と砂浜。サンゴ礁と岩場、熱帯魚、寄せる波。
・ドット絵のウミガメ(インベーダー風)。パステルカラー(水色・ピンク・ミント・レモン・ラベンダー・ピーチ)が基本で、
  まれに濃い色の個体が生まれる。甲羅の模様は 8 種類(無地・水玉・しま・亀甲・リング・まだら・市松・ハート)。
・遺伝的アルゴリズム: 色・模様・速さ・寿命・大きさ・食性(草食/雑食)・性格(活発さ・食欲・カーソルの好き嫌い・
  群れたがり・無頓着さ・気まま・気の短さ)・産卵数。交尾で交叉(スクランブル)+突然変異。系統(Lineage)は母系。
・時間の進み方: 1日(実時間)でおよそ 1〜3 世代が入れ替わる(大人まで約5時間、寿命 12〜24時間)。
  朝・昼・夕・夜の見た目はパソコンの時計に合わせる(夏の日のイメージ: 日の出 4:36、日の入り 18:54)。
・暮らし(ウミガメの生態に合わせた1日):
    朝(5〜10時)と夕方(15〜19時)によく食べる。昼(11〜14時)はサンゴでくつろぎ、熱帯魚にクリーニングしてもらう。
    夜は岩場やサンゴのそばで眠る。産卵は夜、メスが砂浜に上がって行う。子ガメも夜にふ化して海へ向かう。
    ときどき海面に浮上して首を出して息継ぎ。大波でひっくり返ったり、波に乗ってサーフィンしたりする。
・生態系: 水草は群生して広がり、食べられると減る(根は残って再生。死骸は水草の栄養になる)。
  クラゲは沖から流れてくる。カメが増えすぎると餌が減って餓死が増える。右上のグラフで増減が見える。
・関係: 近くで過ごすと友達になり、交尾した相手はパートナーになる。仲良しは一緒に泳ぎ、会うと喜ぶ。
  仲間が死ぬと悲しむ。R キーで関係の線を表示。
・訪問者: イルカ・マンタ(友好的。カメが集まって一緒に遊ぶ)、ヤドカリ、ヤシガニ(夜の砂浜)、サメ(大きなカメを狙う)。
・マウス:
    カメをクリック       → ステータスがカメについて回る。もう一度で消える
    カメをダブルクリック → ひっくり返る(その後、喜ぶか怒る)
    カメの上でカーソルを動かす → なでる(性格しだいで喜ぶ/嫌がる)
    近づける             → 性格に応じて寄ってくる / 嫌がって逃げる / 気にしない
    卵・水草・サンゴ・岩・魚・クラゲ・訪問者に重ねる → 説明を表示
    水をクリック → クラゲを落とす   Shift+クリック → 水草を植える
    右クリック → 最前面に固定の切り替え   L キー → 系統の文字   R キー → 友達・パートナーの線
・音: 波の音と効果音(標準ライブラリで合成)。砂浜右下のボタンか W / F キーで、それぞれ ON/OFF。
  音量はボタンの左右の −/+ かマウスホイールで、それぞれ 0〜100%。
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

VERSION = "4.5.0"

# ---------------------------------------------------------------- 定数
TICK_MS = 100                 # 画面更新の間隔(10fps)。最小化中は 1秒ごとに計算だけ
MAX_TURTLES = 40              # 安全のための上限(カメ+卵)。普段は餌の量で頭打ちになる
HOUR = 3600.0
JUVENILE_AGE = 1 * HOUR       # これより若いと一番小さい姿
ADULT_AGE = 5 * HOUR          # 大人になる年齢。寿命 12〜24 時間 → 1日に 1〜3 世代
MATE_COOLDOWN = 2 * HOUR
EGG_TIME = 1.5 * HOUR         # 卵がかえるまで(その後、夜を待ってふ化)
LAY_TIME = 4.0
EGG_COST = 0.09               # 卵1個に母親が使う栄養
HATCH_ENERGY = 0.45           # 子ガメの最初の栄養
MAX_SCALE = 6                 # ドットの拡大率の上限(合体で大きくなる)
MERGE_KIN = 0.12              # この遺伝距離より近い個体どうしが合体候補
CORPSE_TIME = 10.0            # 死骸が残る時間(その後、分解されて近くの水草の栄養になる)
CORPSE_FERTILIZE = 0.25

PLANT_START = 32
N_MEADOWS = 5                 # 水草が群生する藻場の数
MEADOW_R = (26, 40)
PLANT_MAX = 50
PLANT_GROWTH = 0.00045        # 水草のロジスティック成長率(1/秒)
PLANT_MIN = 0.08              # 食べ尽くされても根が残る量
PLANT_EDIBLE = 0.18           # これより少ない水草は食べられない(根からの再生を待つ)
PLANT_BASE = 0.00003           # 根からの再生(1/秒)
PLANT_BITE = 0.12             # ひとくち(小さくして、少しずつ減るのが見えるように)
EAT_TIME = 0.8                # ひとくちにかかる時間(もぐもぐ)
PLANT_SCARS = 3              # 根元まで食べられるのがこの回数続くと枯れる(食べ過ぎで藻場が消える)
PLANT_HEAL = 20 * 60         # これだけ食べられなければ、傷が1つ治る
SPROUT_GAP = (300, 600)       # ひとりでに芽が出る間隔(秒)。食べられなければ育って新しい藻場になる
PLANT_SPREAD = 1 / 120.0       # 茂った水草がすぐ隣に広がる確率(1/秒)→ 群生する
JELLY_INTERVAL = 180.0
JELLY_MAX = 5
JELLY_DROP_MAX = 12
JELLY_ENERGY = 0.40

SHARK_GAP = (25 * 60, 35 * 60)      # 約30分に1回(いちばんまれ)
SHARK_STAY = 70.0
SHARK_PREY_SCALE = 4
SHARK_SIGHT = 140.0
TURTLE_ALERT = 170.0
SHARK_ZONE = 0.6

VISITORS = {   # 間隔(秒)・滞在(秒)・場所・出る時間帯。サメ(SHARK_GAP)→イルカ→マンタ→ヤシガニ→ヤドカリ の順にまれ
    "dolphin": {"gap": (15 * 60, 25 * 60), "stay": 90, "zone": "sea", "when": "day", "friendly": True},
    "manta": {"gap": (12 * 60, 18 * 60), "stay": 110, "zone": "sea", "when": "daydusk", "friendly": True},
    "coconut": {"gap": (60, 120), "stay": 45, "zone": "beach", "when": "night", "friendly": False},
    "hermit": {"gap": (40, 80), "stay": 45, "zone": "beach", "when": "any", "friendly": False},
}
VISIT_LOG_GAP = 300           # よく来る訪問者は、イベント欄には5分に1回だけ書く
BIG_WAVE_GAP = (15 * 60, 40 * 60)
N_WAVES = 8
N_SCHOOLS = 3
FISH_PER_SCHOOL = 6
FRIEND_AFF = 1.0              # この親しさ以上で友達

BREATH_GAP = (180, 480)
SLEEP_METAB = 0.12            # 眠っている間の代謝(起きている時の割合)。満腹なら一晩眠れる
BREATH_TIME = 3.0
PET_STROKE = 60.0

SUNRISE = 4.6                 # 夏の日のイメージ(4:36)
SUNSET = 18.9                 # (18:54)

OFFLINE_STEP = 60.0
OFFLINE_MAX = 7 * 24 * 3600
HISTORY_DT = 20.0
HISTORY_LEN = 60
AUTOSAVE_SEC = 300
SAVE_NAME = "colony.json"

FLOAT_GENES = ("hue", "hue2", "speed", "life", "size", "diet",
               "activity", "appetite", "cursor", "flock", "care", "whim",
               "temper", "fertility", "style", "dark")
PATTERN_BITS = 28

PASTEL = (0.55, 0.93, 0.38, 0.14, 0.76, 0.06)     # 水色・ピンク・ミント・レモン・ラベンダー・ピーチ
PASTEL_NAMES = ("sky blue", "pink", "mint", "lemon", "lavender", "peach")
STYLES = ("plain", "polka dots", "stripes", "tortoiseshell", "ring", "mottled", "checker", "heart")


# ---------------------------------------------------------------- 遺伝子
def random_genome(rng=random):
    g = {k: rng.random() for k in FLOAT_GENES}
    g["dark"] = rng.random() ** 3          # 濃い色(>0.9)はまれ
    g["pattern"] = [rng.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def fill_genome(g):
    """古い保存データなど、足りない遺伝子を補う。"""
    g = dict(g)
    for k in FLOAT_GENES:
        if k not in g:
            g[k] = random.random() ** 3 if k == "dark" else random.random()
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


def pastel_index(h):
    return min(len(PASTEL) - 1, int((h % 1.0) * len(PASTEL)))


def pastel_hue(h):
    """遺伝子の色相を、かわいいパステルの色の近くに寄せる。"""
    i = pastel_index(h)
    frac = (h % 1.0) * len(PASTEL) - i
    return (PASTEL[i] + (frac - 0.5) * 0.06) % 1.0


def is_dark(g):
    return g["dark"] > 0.9


def style_of(g):
    s = g["style"]
    return 7 if s > 0.96 else min(6, int(s / 0.96 * 7))


def color_name(g):
    n = PASTEL_NAMES[pastel_index(g["hue"])]
    return ("deep " + n.replace("sky ", "")) if is_dark(g) else ("pastel " + n)


def lineage_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = string.ascii_uppercase[r] + s
    return s


# ---------------------------------------------------------------- 昼と夜(パソコンの時計に合わせる)
TINTS = {"night": (0.22, 0.28, 0.45), "twilight": (0.50, 0.58, 0.85), "sunrise": (1.00, 0.84, 0.74),
         "day": (1.00, 1.00, 1.00), "noon": (1.04, 1.04, 1.0), "sunset": (1.08, 0.74, 0.52),
         "dusk": (0.58, 0.48, 0.74)}
PHASE_MSG = {
    "Dawn twilight": "Dawn twilight - the sky is getting lighter",
    "Sunrise": "Sunrise! The turtles wake up and look for breakfast",
    "Daytime": "Daytime - turtles eat, rest at the reef and get cleaned",
    "Sunset": "Sunset - the sea turns orange, time for an evening snack",
    "Dusk": "Dusk - turtles gather and head for their beds",
    "Night": "Night - turtles sleep by the rocks; mothers lay eggs on the beach",
}


def sun_times(ts=None):
    """日の出・日の入り(時)。夏の日をイメージした固定の時刻。"""
    return SUNRISE, SUNSET


def daylight(ts):
    """(時間帯の名前, 夜らしさ 0〜1, 色み, 時刻[時]) を返す。"""
    lt = time.localtime(ts)
    h = lt.tm_hour + lt.tm_min / 60.0 + lt.tm_sec / 3600.0
    sr, ss = sun_times(ts)
    keys = [(sr - 1.0, "night"), (sr - 0.5, "twilight"), (sr, "sunrise"), (sr + 1.2, "day"),
            (12.5, "noon"), (ss - 1.2, "day"), (ss - 0.2, "sunset"), (ss + 0.5, "dusk"), (ss + 1.2, "night")]
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
        self.mate_cd = MATE_COOLDOWN * 0.1
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
        self.bed = None           # 眠る場所(岩場・サンゴのそば)
        self.bed_kind = None
        self.goal = None          # クリーニングに行くサンゴ
        self.surf = None          # 乗っている波
        self.vis = None           # 一緒に遊んでいる訪問者
        self.orbit = random.uniform(0, math.tau)
        self.dead_t = 0.0
        self.cause = ""
        self.anim = random.random()
        self.dir = 0              # 0上 1右 2下 3左
        self.nb = None
        self.air = random.uniform(0.3, 1.0) * self.breath_gap
        self.pet_acc = 0.0
        self.pets = 0
        self.aff = {}             # 親しさ: 相手の id → 値
        self.partner = None
        self.lonely_t = 0.0
        self.clean_cd = random.uniform(0, 3600)

    @property
    def adult(self):
        return self.age >= ADULT_AGE

    @property
    def base_scale(self):
        return 3 if self.g["size"] < 0.5 else 4

    @property
    def scale(self):
        if self.age < JUVENILE_AGE:
            return 2                       # 子ガメでも見分けられる大きさ
        if not self.adult:
            return self.base_scale - 1
        return min(MAX_SCALE, self.base_scale + self.extra)

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
        return (12 + 12 * self.g["life"]) * HOUR * (1 + 0.2 * self.extra)

    @property
    def metab(self):
        g = self.g
        return (0.00012 + 0.00015 * g["appetite"] + 0.00008 * g["speed"]
                + 0.00005 * g["activity"]) * (1 + 0.15 * self.extra) * (1.0 if self.adult else 0.6)

    @property
    def eat_below(self):
        return 0.35 + 0.5 * self.g["appetite"]

    def night_pull(self, night):
        """夜の眠気。活発な個体ほど夜でも起きている(夜ふかし)。"""
        return night * (1.0 - 0.7 * self.g["activity"])

    @property
    def awake_len(self):
        return 900 + 2700 * self.g["activity"]

    @property
    def sleep_len(self):
        return 120 + 480 * (1 - self.g["activity"])

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

    def head(self):
        """頭の位置(息継ぎの波紋用)。"""
        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[self.dir]
        return self.x + dx * self.radius * 0.95, self.y + dy * self.radius * 0.95

    def say(self, emote, sec=1.6, force=True):
        if force or self.emote is None:
            self.emote, self.emote_t = emote, sec

    def best_friend(self, by_id):
        best, bv = None, FRIEND_AFF
        for i, v in self.aff.items():
            if v >= bv and i in by_id and i != self.partner:
                best, bv = by_id[i], v
        return best

    def to_dict(self):
        return {"id": self.id, "g": self.g, "x": self.x, "y": self.y, "gen": self.generation,
                "age": self.age, "energy": self.energy, "fatigue": self.fatigue,
                "mate_cd": self.mate_cd, "sex": self.sex, "lin": self.lineage,
                "par": self.parents, "extra": self.extra, "clutch": self.clutch,
                "sleep": self.state == "sleep", "joy": self.joy, "annoy": self.annoy,
                "partner": self.partner, "aff": {str(k): round(v, 3) for k, v in self.aff.items()},
                "pets": self.pets}

    @classmethod
    def from_dict(cls, d):
        t = cls(fill_genome(d["g"]), d["x"], d["y"], d.get("gen", 1), d.get("age", 0.0),
                d["id"], d.get("sex"), d.get("lin", "A"), d.get("par", ""), d.get("extra", 0))
        t.energy = d.get("energy", 0.7)
        t.fatigue = d.get("fatigue", 0.3)
        t.mate_cd = d.get("mate_cd", 0.0)
        t.joy, t.annoy = d.get("joy", 0.3), d.get("annoy", 0.0)
        t.clutch = d.get("clutch")
        t.partner = d.get("partner")
        t.aff = {int(k): v for k, v in d.get("aff", {}).items()}
        t.pets = d.get("pets", 0)
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

    def __init__(self, x, y, b=0.3, m=None):
        self.x, self.y, self.b = x, y, b
        self.m = m                # 属する藻場の番号
        self.bitten = -1e9        # 最後にかじられた時刻(揺れの演出)
        self.scars = 0            # 根元まで食べられた回数(3回で枯れる)
        self.scar_t = 0.0
        self.age = 0.0
        self.life = random.uniform(4, 8) * HOUR   # 寿命がくると枯れて、藻場は少しずつ移動する
        self.gone = False

    @property
    def stage(self):
        b = self.b
        return 0 if b < 0.15 else 1 if b < 0.4 else 2 if b < 0.7 else 3


class Reef:
    """サンゴ礁(coral)と岩場(rock)。カメの寝床、熱帯魚のすみか、クリーニングの場所。"""

    def __init__(self, x, y, kind, seed):
        self.x, self.y, self.kind, self.seed = x, y, kind, seed
        rnd = random.Random(seed)
        n = rnd.randint(7, 10) if kind == "coral" else rnd.randint(4, 6)
        r = 34 if kind == "coral" else 26
        self.parts = []           # (dx, dy, 部品の種類, 色の番号)
        for i in range(n):
            a = rnd.uniform(0, math.tau)
            d = rnd.uniform(0, r) if i else 0
            if kind == "coral":
                piece = rnd.choice(("branch", "branch", "brain", "fan", "table"))
            else:
                piece = rnd.choice(("rock1", "rock2")) if i < n - 1 or rnd.random() < 0.5 else "brain"
            self.parts.append((math.cos(a) * d, math.sin(a) * d * 0.75, piece, rnd.randrange(4)))
        self.radius = r + 8

    def bed_point(self):
        a = random.uniform(0, math.tau)
        d = random.uniform(self.radius * 0.6, self.radius * 1.05)
        return self.x + math.cos(a) * d, self.y + math.sin(a) * d * 0.8

    def to_list(self):
        return [self.x, self.y, self.kind, self.seed]


class Shark:
    kind = "shark"

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx, self.vy = x, y, vx, 0.0
        self.t = 0.0
        self.target = None
        self.leaving = False
        self.anim = 0.0
        self.dir = 1 if vx > 0 else 3


class Visitor:
    """まれに来る生き物(イルカ・マンタ・ヤドカリ・ヤシガニ)。"""

    def __init__(self, kind, x, y, vx):
        self.kind, self.x, self.y, self.vx, self.vy = kind, x, y, vx, 0.0
        self.y0 = y
        self.t = 0.0
        self.anim = 0.0
        self.leaving = False
        self.gone = False
        self.players = set()
        self.announced = False

    @property
    def dir(self):
        return 1 if self.vx >= 0 else 3


class Jelly:
    kind = "jelly"

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx = x, y, vx
        self.phase = random.random() * math.tau
        self.gone = False


class Wave:
    """沖から砂浜へ寄せる波。大波(big)はカメをひっくり返したり、サーフィンさせたりする。"""

    def __init__(self, world, first=False, big=False):
        self.big = big
        self.hit = set()
        self.riders = set()
        self.wiped = set()
        self.flipped = 0
        self.done = False
        self.reset(world, first)

    def reset(self, world, first=False):
        w = world
        self.hit.clear()
        self.riders.clear()
        self.wiped.clear()
        self.flipped = 0
        if self.big:
            self.x, self.len, self.amp, self.sp = -w.w * 0.1, w.w * 1.2, 7.0, 22.0
            self.y0 = 6.0
        else:
            self.x = random.uniform(-20, w.w - 40)
            self.len, self.amp = random.uniform(50, 120), random.uniform(2, 5)
            self.sp = random.uniform(6, 12)
            self.y0 = random.uniform(8, w.land_top * 0.35)
        self.y = random.uniform(self.y0, w.land_top * 0.9) if first else self.y0
        self.ph = random.uniform(0, math.tau)


class School:
    def __init__(self, home, kind):
        self.home, self.kind = home, kind
        self.ang = random.uniform(0, math.tau)
        self.cleaning = None


class Fish:
    def __init__(self, school, x, y):
        self.school = school
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-10, 10), random.uniform(-5, 5)
        self.ox, self.oy = random.uniform(-1, 1), random.uniform(-1, 1)
        self.t = random.uniform(0, 3)


# ---------------------------------------------------------------- 世界(描画と無関係)
class World:
    def __init__(self, w=700, h=440):
        self.w, self.h = w, h
        self.turtles = []
        self.eggs = []
        self.plants = []
        self.reefs = []
        self.meadows = {}         # 藻場の番号 → {x, y, r, n, dir, big}
        self.next_meadow = 0
        self.meadow_changed = False
        self.meadow_t = 5.0
        self.sprout_t = random.uniform(*SPROUT_GAP)
        self.schools = []
        self.fish = []
        self.jellies = []
        self.visitors = []
        self.vis_t = {k: random.uniform(*v["gap"]) * random.uniform(0.1, 0.6) for k, v in VISITORS.items()}
        self.vis_log = {}
        self.shark = None
        self.shark_t = random.uniform(*SHARK_GAP)
        self.waves = [Wave(self, first=True) for _ in range(N_WAVES)]
        self.big_wave = None
        self.big_t = random.uniform(*BIG_WAVE_GAP)
        self.clock = time.time    # テストでは差し替える
        self.phase, self.night, self.tint, self.hour = daylight(self.clock())
        self.now_ts = self.clock()
        self.phase_msg = None
        self.fx = []              # 描画側への演出 (種類, x, y)
        self.sfx = []             # 描画側への効果音の名前
        self.n_events = 0
        self.settings = {"waves": True, "fx": True, "waves_vol": 6, "fx_vol": 7}
        self.time = 0.0
        self.jelly_t = 0.0
        self.births = self.deaths = self.laid = self.merges = self.splits = 0
        self.max_gen = 1
        self.n_lineages = 0
        self.gene_pool = []
        self.cursor = None
        self.cursor_speed = 0.0
        self.events = []
        self.history = []
        self.hist_t = 0.0
        self.aff_t = 0.0
        self.surf_log_t = 0.0
        self.clean_log_t = 0.0
        self._pop = 0
        self.by_id = {}

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
        self.seed_reefs()
        for i in range(n):
            x, y = self.water_point(40)
            t = Turtle(random_genome(), x, y, sex="FM"[i % 2], lineage=self.new_lineage())
            t.age = ADULT_AGE + random.uniform(0.0, 0.1) * t.lifespan
            t.mate_cd = random.uniform(0, MATE_COOLDOWN * 0.5)
            self.turtles.append(t)
        self.seed_plants()

    def seed_reefs(self):
        lt = self.land_top
        spots = [(0.16, 0.55, "coral"), (0.42, 0.78, "rock"), (0.58, 0.42, "coral"),
                 (0.85, 0.72, "coral"), (0.30, 0.30, "rock")]
        self.reefs = [Reef(self.w * fx + random.uniform(-15, 15), lt * fy + random.uniform(-10, 10),
                           kind, random.randrange(10 ** 6)) for fx, fy, kind in spots]
        self.seed_fish()

    def seed_fish(self):
        corals = [r for r in self.reefs if r.kind == "coral"] or self.reefs
        self.schools, self.fish = [], []
        for i in range(N_SCHOOLS):
            s = School(corals[i % len(corals)], ("yellow", "blue", "clown")[i % 3])
            self.schools.append(s)
            for _ in range(FISH_PER_SCHOOL):
                self.fish.append(Fish(s, s.home.x + random.uniform(-20, 20), s.home.y + random.uniform(-15, 15)))

    def _free_spot(self, x, y, spacing=10):
        return (self.in_water(x, y + 12) and 12 < x < self.w - 12 and y > 12 and not self._near_reef(x, y)
                and all((q.x - x) ** 2 + (q.y - y) ** 2 > spacing * spacing for q in self.plants))

    def new_meadow(self, x, y):
        self.next_meadow += 1
        self.meadows[self.next_meadow] = {"x": x, "y": y, "r": 8.0, "n": 1,
                                          "dir": random.uniform(0, math.tau), "big": False}
        return self.next_meadow

    def seed_meadows(self):
        """最初の藻場の中心を決める(サンゴ・岩・ほかの藻場と重ならない所)。"""
        centers = []
        for _ in range(200):
            if len(centers) >= N_MEADOWS:
                break
            rr = random.uniform(*MEADOW_R)
            x = random.uniform(rr + 10, self.w - rr - 10)
            y = random.uniform(self.land_top * 0.2 + rr * 0.7, self.land_top * 0.92 - rr * 0.7)
            if any(math.hypot(rf.x - x, rf.y - y) < rf.radius + rr + 6 for rf in self.reefs):
                continue
            if any(math.hypot(cx - x, cy - y) < cr + rr + 12 for cx, cy, cr in centers):
                continue
            centers.append((x, y, rr))
        return [(self.new_meadow(x, y), x, y, rr) for x, y, rr in centers]

    def meadow_at(self, x, y):
        for mid, m in self.meadows.items():
            if m["n"] >= 3 and (m["x"] - x) ** 2 + ((m["y"] - y) / 0.75) ** 2 < (m["r"] + 6) ** 2:
                return mid
        return None

    def seed_plants(self, n=PLANT_START):
        """水草は藻場にかたまって(群生して)生える。"""
        groups = self.seed_meadows()
        for i in range(n):
            mid, cx, cy, rr = groups[i % len(groups)]
            for _ in range(15):
                a, d = random.uniform(0, math.tau), rr * math.sqrt(random.random()) * 0.9
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.7
                if self._free_spot(x, y, 11):
                    self.plants.append(Plant(x, y, random.uniform(0.4, 0.95), mid))
                    break
        self._update_meadows(log=False)

    def _update_meadows(self, log=True):
        """藻場の形を水草の株から計算し直す(株が増えたり食べられたりすると、藻場は少しずつ動く)。"""
        members = {}
        for p in self.plants:
            members.setdefault(p.m, []).append(p)
        for mid in list(self.meadows):
            ps = members.get(mid)
            m = self.meadows[mid]
            if not ps:
                if m["big"] and log:
                    self.event("seaweed", "A seaweed meadow was eaten away...")
                del self.meadows[mid]
                continue
            cx = sum(p.x for p in ps) / len(ps)
            cy = sum(p.y for p in ps) / len(ps)
            m["x"], m["y"], m["n"] = cx, cy, len(ps)
            m["r"] = max(8.0, max(math.hypot(p.x - cx, (p.y - cy) / 0.75) for p in ps) + 4)
            m["dir"] += random.gauss(0, 0.35)                # 広がる向きがゆっくり変わる
            if len(ps) >= 3 and not m["big"]:
                m["big"] = True
                if log and len(self.meadows) > 1:
                    self.event("seaweed", "A lone seaweed survived and grew into a new meadow!")
        self.meadow_changed = True

    def _near_reef(self, x, y):
        return any(math.hypot(r.x - x, r.y - y) < r.radius for r in self.reefs)

    def alive(self):
        return [t for t in self.turtles if t.alive]

    def population(self):
        return sum(t.alive for t in self.turtles) + len(self.eggs)

    def event(self, kind, text):
        ts = getattr(self, "now_ts", None) or time.time()
        self.events.append((time.strftime("%H:%M", time.localtime(ts)), kind, text))
        self.events = self.events[-8:]
        self.n_events += 1

    @staticmethod
    def tag(t):
        return "#%d (%s)" % (t.id, t.lineage)

    # ---- 時間帯
    def update_daylight(self, ts, log=True):
        self.now_ts = ts
        phase, self.night, self.tint, self.hour = daylight(ts)
        if phase != self.phase:
            self.phase = phase
            if log:
                self.phase_msg = PHASE_MSG[phase]
                self.event("time", PHASE_MSG[phase])

    def appetite_shift(self):
        """ウミガメの1日: 朝と夕方によく食べ、昼はくつろぎ、夜はほとんど食べない。"""
        h = self.hour
        if 5 <= h < 10 or 15 <= h < 19:
            return 0.15
        if 11 <= h < 14:
            return -0.05
        if self.night > 0.6:
            return -0.25
        return 0.0

    # ---- 1フレーム
    def step(self, dt):
        dt = min(dt, 0.5)
        self.time += dt
        self.update_daylight(self.clock())
        self._grow_plants(dt)
        self._jellies(dt)
        self._waves(dt)
        self._fish_step(dt)
        self._visitors_step(dt)
        self._shark_step(dt)
        self._hatch(dt)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        self.by_id = {t.id: t for t in alive}
        self._neighbors(alive, dt)
        for t in list(self.turtles):
            self._update_turtle(t, dt)
        self._pairs(alive, dt)
        self._decompose()
        if not self.alive() and not self.eggs:
            self._refound()
        self._decay_aff(dt)
        self._record(dt)

    # ---- 生態系
    def _grow_plants(self, dt):
        new, dead = [], []
        for p in self.plants:
            p.b += (PLANT_GROWTH * p.b + PLANT_BASE) * (1 - p.b) * dt
            p.b = min(1.0, max(PLANT_MIN, p.b))
            p.age += dt
            if p.scars >= PLANT_SCARS or p.age > p.life:       # 食べられ過ぎ・寿命で枯れる
                dead.append(p)
                continue
            if p.scars and self.time - p.scar_t > PLANT_HEAL:
                p.scars -= 1
                p.scar_t = self.time
            if (p.b > 0.8 and len(self.plants) + len(new) < PLANT_MAX
                    and random.random() < min(1.0, dt * PLANT_SPREAD)):
                m = self.meadows.get(p.m)
                for _ in range(6):                           # すぐ隣へ。藻場の「進む向き」に広がりやすい
                    a = (m["dir"] + random.gauss(0, 1.1)) if m and random.random() < 0.65 else random.uniform(0, math.tau)
                    d = random.uniform(10, 17)
                    x, y = p.x + math.cos(a) * d, p.y + math.sin(a) * d * 0.75
                    crowd = sum(1 for q in self.plants if (q.x - x) ** 2 + (q.y - y) ** 2 < 22 * 22)
                    if crowd < 5 and self._free_spot(x, y) and all((q.x - x) ** 2 + (q.y - y) ** 2 > 100 for q in new):
                        new.append(Plant(x, y, 0.12, p.m))
                        p.b -= 0.15
                        break
        if dead:
            self.plants = [p for p in self.plants if p not in dead]
        self.plants += new
        self.sprout_t -= dt                                  # ひとりでに芽が出る
        if self.sprout_t <= 0:
            self.sprout_t = random.uniform(*SPROUT_GAP)
            if len(self.plants) < PLANT_MAX:                # 空きがあるときだけ
                for _ in range(10):
                    x, y = self.water_point(20)
                    if self._free_spot(x, y, 25):
                        self.plants.append(Plant(x, y, 0.12, self.new_meadow(x, y)))
                        break
        self.meadow_t -= dt
        if self.meadow_t <= 0 or dead:
            self.meadow_t = 5.0
            self._update_meadows()

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
            self.jellies.append(Jelly(x, y, random.choice((-3, 3))))
            self.fx.append(("splash", x, y))

    def drop_plant(self, x, y):
        """Shift+クリック: 水草を植える。藻場の中ならその藻場に、外なら新しい芽になる。"""
        if len(self.plants) >= PLANT_MAX + 6 or not self.in_water(x, y + 10):
            return
        mid = self.meadow_at(x, y)
        self.plants.append(Plant(x, y, 0.3, mid if mid is not None else self.new_meadow(x, y)))
        self._update_meadows(log=False)

    # ---- 波(大波・サーフィン)
    def _waves(self, dt):
        self.big_t -= dt
        if self.big_wave is None and self.big_t <= 0:
            self.big_t = random.uniform(*BIG_WAVE_GAP)
            self.big_wave = Wave(self, big=True)
            self.event("wave", "A big wave is coming!")
        waves = self.waves + ([self.big_wave] if self.big_wave else [])
        alive = [t for t in self.turtles if t.alive]
        bw = self.big_wave
        if bw is not None:                   # 大波が来たら、遊び好きのカメは波をつかまえに行く
            for t in alive:
                if (t.state == "swim" and self.playful(t) and t.energy > 0.3 and t.id not in bw.hit
                        and t.y > bw.y + 10 and self.in_water(t.x, t.y)):
                    t.state, t.surf = "catch", bw
                    t.say("star", 1.2)
        for wv in waves:
            wv.y += wv.sp * dt
            wv.x += math.sin(self.time * 0.3 + wv.ph) * 2 * dt
            end = self.shore(wv.x + wv.len / 2) - 6 if not wv.big else self.land_top - 4
            if wv.y > end:
                self._wave_end(wv)
                continue
            for t in alive:
                if t.id in wv.hit or not (wv.x <= t.x <= wv.x + wv.len) or abs(t.y - wv.y) > 6:
                    continue
                if not self.in_water(t.x, t.y):
                    continue
                wv.hit.add(t.id)
                self._wave_hits(wv, t)

    @staticmethod
    def playful(t):
        """遊び好き: 活発・気まま・ごきげんなカメ。"""
        g = t.g
        return g["whim"] > 0.55 or g["activity"] > 0.65 or (t.joy > 0.6 and g["care"] > 0.3)

    def _wave_hits(self, wv, t):
        if t.state in ("lay", "nest", "flee_shark", "surf", "wipeout", "dead"):
            return
        g = t.g
        if wv.big and t.y > self.land_top * 0.3 and t.state != "catch":
            # 大波: 小さいカメほどひっくり返りやすい(寝ているカメも)
            if random.random() < (0.45 if t.scale <= 2 else 0.2):
                t.state, t.state_t = "flipped", 3.0
                t.say("surprise", 1.5)
                t.annoy = min(1.0, t.annoy + 0.1 * g["temper"])
                wv.flipped += 1
                self.sfx.append("flip")
                return
        if t.state == "catch" or (t.state == "swim" and self.playful(t) and t.energy > 0.4
                                  and random.random() < (0.6 if wv.big else 0.07)):
            t.state, t.surf = "surf", wv               # 波に乗って岸へ向かう
            end = self.land_top - 4 if wv.big else self.shore(t.x) - 6
            # たいていは途中でワイプアウト(岸まで乗り切れるのは4匹に1匹くらい)
            t.wipe_at = None if random.random() < 0.25 else random.uniform(t.y + 12, max(t.y + 14, end - 8))
            wv.riders.add(t.id)
            t.say("star", 1.5)
            self.sfx.append("whoosh")
            if not wv.big and self.time - self.surf_log_t > 180:
                self.surf_log_t = self.time
                self.event("surf", "%s is surfing!" % self.tag(t))

    def _wave_end(self, wv):
        for tid in list(wv.riders):
            t = self.by_id.get(tid)
            if t and t.state == "surf":
                t.state, t.state_t, t.surf = "dance", 1.2, None
                t.joy = min(1.0, t.joy + 0.3)
                t.say("star", 1.5)
        if wv.big:
            if wv.riders or wv.wiped:
                ids = sorted(wv.riders)
                msg = ("%s rode all the way to the shore!" % (
                    ", ".join("#%d" % i for i in ids[:4]) + (" and %d more" % (len(ids) - 4) if len(ids) > 4 else ""))
                       if ids else "Nobody made it to the shore")
                if wv.wiped:
                    msg += "  %d wiped out" % len(wv.wiped)
                self.event("surf", msg)
            for t in self.turtles:
                if t.state == "catch":
                    t.state, t.surf = "swim", None
            if wv.flipped:
                self.event("wave", "The big wave flipped %d turtle%s over!"
                           % (wv.flipped, "s" if wv.flipped > 1 else ""))
            self.big_wave = None
        else:
            wv.reset(self)

    # ---- 熱帯魚(群れでサンゴのまわりを泳ぎ、カメをクリーニングする)
    def _fish_step(self, dt):
        night = self.night
        for s in self.schools:
            t = s.cleaning
            if t is not None and (not t.alive or t.state != "cleaning"):
                s.cleaning = t = None
            if t is not None:
                s.cx, s.cy, s.spread = t.x, t.y, t.radius
            else:
                s.ang += dt * (0.45 - 0.35 * night)
                s.cx = s.home.x + math.cos(s.ang) * (32 - 20 * night)
                s.cy = s.home.y + math.sin(s.ang) * (20 - 12 * night)
                s.spread = 16 - 8 * night
        cur = self.cursor
        for f in self.fish:
            s = f.school
            f.t -= dt
            if s.cleaning is not None:
                # クリーニング: 甲羅やひれの上の一点へ行ってつつき、また別の場所へ
                if f.t <= 0:
                    f.t = random.uniform(0.6, 1.3)
                    a = random.uniform(0, math.tau)
                    rr = s.spread * random.uniform(0.3, 0.95)
                    f.ox, f.oy = math.cos(a) * rr, math.sin(a) * rr
                    f.pecked = False
                tx, ty = s.cx + f.ox, s.cy + f.oy
                ax, ay = (tx - f.x) * 6.0, (ty - f.y) * 6.0
                if not getattr(f, "pecked", True) and abs(tx - f.x) < 2.5 and abs(ty - f.y) < 2.5:
                    f.pecked = True
                    self.fx.append(("peck", tx + (2 if f.vx >= 0 else -2), ty))
            else:
                if f.t <= 0:
                    f.t = random.uniform(1.5, 4)
                    f.ox, f.oy = random.uniform(-1, 1), random.uniform(-1, 1)
                tx, ty = s.cx + f.ox * s.spread, s.cy + f.oy * s.spread * 0.7
                ax, ay = (tx - f.x) * 1.8, (ty - f.y) * 1.8
            if cur and abs(cur[0] - f.x) < 50 and abs(cur[1] - f.y) < 50:
                d = math.hypot(f.x - cur[0], f.y - cur[1]) or 1.0
                if d < 50:                                 # カーソルが来ると散る
                    ax += (f.x - cur[0]) / d * 250
                    ay += (f.y - cur[1]) / d * 250
            f.vx += (ax - f.vx) * min(1.0, dt * 2)
            f.vy += (ay - f.vy) * min(1.0, dt * 2)
            sp = math.hypot(f.vx, f.vy)
            if sp > 70:
                f.vx, f.vy = f.vx / sp * 70, f.vy / sp * 70
            f.x += f.vx * dt
            f.y += f.vy * dt

    # ---- 訪問者
    def _visitors_step(self, dt):
        for kind, cfg in VISITORS.items():
            self.vis_t[kind] -= dt
            if self.vis_t[kind] > 0 or any(v.kind == kind for v in self.visitors):
                continue
            ok = {"day": self.night < 0.2, "daydusk": self.night < 0.6,
                  "night": self.night > 0.6, "any": True}[cfg["when"]]
            if not ok:
                self.vis_t[kind] = 120.0
                continue
            self.vis_t[kind] = random.uniform(*cfg["gap"])
            self._spawn_visitor(kind)
        keep = []
        for v in self.visitors:
            self._move_visitor(v, dt)
            if not v.gone:
                keep.append(v)
        self.visitors = keep

    def _spawn_visitor(self, kind):
        left = random.random() < 0.5
        if VISITORS[kind]["zone"] == "sea":
            y = random.uniform(30, self.land_top * 0.7)
            sp = 55 if kind == "dolphin" else 16
            v = Visitor(kind, -40 if left else self.w + 40, y, sp if left else -sp)
            msg = {"dolphin": "A dolphin came to visit!", "manta": "A manta ray is gliding by"}[kind]
        else:
            sx = random.uniform(40, self.w - 40)
            sh = self.shore(sx)
            y = sh + (self.h - sh) * random.uniform(0.18, 0.32)    # 砂浜の上の方(表示と重ならない)
            v = Visitor(kind, -15 if left else self.w + 15, y, 9 if left else -9)
            msg = {"hermit": "A hermit crab is walking on the beach",
                   "coconut": "A coconut crab came out on the night beach"}[kind]
        self.visitors.append(v)
        v.flavor_t = random.uniform(15, 50)
        if self.time - self.vis_log.get(kind, -1e9) > (VISIT_LOG_GAP if kind in ("hermit", "coconut") else 0):
            self.vis_log[kind] = self.time
            self.event("visitor", msg)

    def _move_visitor(self, v, dt):
        v.t += dt
        v.anim += dt
        cfg = VISITORS[v.kind]
        if v.t > cfg["stay"] or (v.kind == "coconut" and self.night < 0.3):
            v.leaving = True
        v.flavor_t = getattr(v, "flavor_t", 30.0) - dt
        if v.flavor_t <= 0 and not v.leaving:
            v.flavor_t = 1e9
            self._visitor_moment(v)
        if cfg["zone"] == "sea":
            if v.kind == "dolphin":
                v.y = v.y0 + 30 * math.sin(v.t * 1.3)
                if not v.leaving and (v.x < 40 and v.vx < 0 or v.x > self.w - 40 and v.vx > 0):
                    v.vx = -v.vx                          # 行ったり来たり
            else:
                v.y = v.y0 + 18 * math.sin(v.t * 0.35)
                if not v.leaving and (v.x < 60 and v.vx < 0 or v.x > self.w - 60 and v.vx > 0):
                    v.vx = -v.vx
            v.x += v.vx * dt
            if cfg["friendly"] and not v.leaving:
                self._recruit_players(v)
        else:
            if random.random() < dt / 6 and not v.leaving:
                v.vx = -v.vx
            if v.leaving:
                v.vx = (abs(v.vx) if v.x > self.w / 2 else -abs(v.vx))
            v.x += v.vx * dt
            if not v.leaving:
                v.x = min(max(10, v.x), self.w - 10)
            for t in self.turtles:   # 子ガメはびっくり(ヤシガニ)/興味しんしん(ヤドカリ)
                if t.alive and not t.adult and math.hypot(t.x - v.x, t.y - v.y) < 45:
                    t.say("bang" if v.kind == "coconut" else "question", 1.0, force=False)
        if v.leaving and (v.x < -60 or v.x > self.w + 60):
            v.gone = True
        if v.t > 6 and v.players and not v.announced:
            v.announced = True
            self.event("play", "%d turtle%s joined the %s to play!" % (
                len(v.players), "s" if len(v.players) > 1 else "", "dolphin" if v.kind == "dolphin" else "manta"))

    def _visitor_moment(self, v):
        """訪問者のちょっとした出来事(イルカのジャンプ、マンタの宙返り、ヤドカリの引っ越しなど)。"""
        k = v.kind
        if k in ("hermit", "coconut") and self.time - self.vis_log.get(k + "!", -1e9) < VISIT_LOG_GAP:
            return
        self.vis_log[k + "!"] = self.time
        if k == "dolphin":
            self.fx += [("splash", v.x, v.y), ("splash", v.x + 12, v.y + 4)]
            self.event("visitor", "The dolphin leaped out of the water!")
            for t in self.turtles:
                if t.alive and math.hypot(t.x - v.x, t.y - v.y) < 200:
                    t.say("star", 1.2, force=False)
        elif k == "manta":
            self.fx.append(("ripple", v.x, v.y))
            self.event("visitor", "The manta ray did a graceful somersault")
        elif k == "hermit":
            v.shell = 1 - getattr(v, "shell", 0)
            self.event("visitor", "The hermit crab moved into a new shell!")
        elif k == "coconut":
            self.event("visitor", "The coconut crab is dragging a coconut across the sand")

    def _recruit_players(self, v):
        for t in self.turtles:
            if (not t.alive or t.state != "swim" or t.id in v.players or t.energy < 0.35
                    or not self.in_water(t.x, t.y)):
                continue
            g = t.g
            if g["care"] < 0.2 or max(g["flock"], g["cursor"], g["whim"]) < 0.45:
                continue
            if math.hypot(t.x - v.x, t.y - v.y) < 170:
                t.state, t.vis, t.state_t = "play", v, random.uniform(15, 35)
                v.players.add(t.id)
                t.say("star", 1.5)

    # ---- サメ(まれに沖に現れ、大きなカメを狙う)
    def _shark_step(self, dt):
        if self.shark is None:
            self.shark_t -= dt * (1.0 + 0.3 * self.night)
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
        if 20 <= sh.t < 20 + dt and sh.target is None:
            self.event("shark", "The shark is circling offshore...")
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
                if random.random() < 0.35:
                    self._kill(tg, "a shark attack")
                    tg.dead_t = CORPSE_TIME - 1.0
                    self.fx.append(("bite", tg.x, tg.y))
                else:                                      # 間一髪で逃げる
                    tg.say("surprise", 1.5)
                    tg.state, tg.state_t = "flee_shark", 3.0
                    self.fx.append(("splash", tg.x, tg.y))
                    self.sfx.append("chomp")
                    self.event("shark", "%s narrowly escaped the shark!" % self.tag(tg))
                sh.leaving, sh.target = True, None
        else:
            dx = 1.0 if sh.vx >= 0 else -1.0
            dy = -0.2 if sh.leaving else math.sin(sh.t * 0.7) * 0.4
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
            if e.t <= 0 and self.night > 0.5:          # 子ガメは夜にふ化して海へ
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
                                 EGG_TIME * 0.1, "FM"[i % 2]))
        self.event("hatch", "The colony died out... 4 eggs drifted ashore (Lineage %s)" % lin)

    def _kill(self, t, cause):
        t.state, t.dead_t, t.cause = "dead", 0.0, cause
        t.emote, t.emote_t = "ghost", 3.0
        t.clutch = None
        self.deaths += 1
        self.gene_pool.append(t.g)
        self.gene_pool = self.gene_pool[-10:]
        self.event("death", "%s died of %s at %s" % (self.tag(t), cause, fmt_dur(t.age)))
        mourners = []
        for o in self.turtles:
            if o.target is t:
                o.target, o.state = None, "swim"
            if o.alive and o is not t and (o.partner == t.id or o.aff.get(t.id, 0) >= FRIEND_AFF):
                o.say("cry", 4.0)                         # 仲間が死ぬと悲しむ
                o.joy = 0.0
                mourners.append(o)
                if o.partner == t.id:
                    o.partner = None
            o.aff.pop(t.id, None)
        if mourners:
            self.event("sad", "%s %s sad about %s" % (
                ", ".join("#%d" % o.id for o in mourners[:3]), "is" if len(mourners) == 1 else "are",
                "#%d" % t.id))

    def _decompose(self, force=False):
        keep = []
        for t in self.turtles:
            if t.state == "dead" and (force or t.dead_t > CORPSE_TIME):
                if t.adult and self.plants:
                    p = min(self.plants, key=lambda p: (p.x - t.x) ** 2 + (p.y - t.y) ** 2)
                    p.b = min(1.0, p.b + CORPSE_FERTILIZE)
                continue
            keep.append(t)
        self.turtles = keep

    # ---- 仲間・友達・パートナー
    def _neighbors(self, alive, dt):
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
                    if d2 < 60 * 60 and t.state != "sleep":      # 近くで過ごすと仲良くなる
                        compat = 1.0 - abs(t.g["flock"] - o.g["flock"]) + (0.3 if o.lineage == t.lineage else 0)
                        t.aff[o.id] = t.aff.get(o.id, 0.0) + dt * 0.003 * (0.4 + compat)
                        if d2 < 35 * 35 and t.emote is None:
                            if o.id == t.partner and random.random() < dt / 25:
                                t.say("heart", 1.2)
                            elif t.aff[o.id] >= FRIEND_AFF and random.random() < dt / 40:
                                t.say(random.choice(("note", "blush")), 1.2)
            t.nb = (cx / n, cy / n, vx / n, vy / n, n, math.sqrt(near)) if n else None
            # さみしい・混みすぎ
            g = t.g
            if t.state == "swim" and g["care"] > 0.3:
                if g["flock"] > 0.7 and n == 0:
                    t.lonely_t += dt
                    if t.lonely_t > 120 and t.emote is None:
                        t.say("dots" if t.lonely_t < 240 else "cry", 2.0)
                        t.lonely_t = 60 if t.lonely_t > 240 else t.lonely_t
                else:
                    t.lonely_t = 0.0
                if g["flock"] < 0.3 and n >= 4 and random.random() < dt / 20:
                    t.say("sweat" if g["temper"] < 0.5 else "anger", 1.2, force=False)

    def _decay_aff(self, dt):
        self.aff_t += dt
        if self.aff_t < 30:
            return
        self.aff_t = 0.0
        for t in self.turtles:
            t.aff = {k: v * 0.97 for k, v in t.aff.items() if v > 0.05}
            if len(t.aff) > 10:
                t.aff = dict(sorted(t.aff.items(), key=lambda kv: -kv[1])[:10])

    def friends(self, t):
        return [self.by_id[i] for i, v in sorted(t.aff.items(), key=lambda kv: -kv[1])
                if v >= FRIEND_AFF and i in self.by_id and i != t.partner]

    # ---- 個体の行動
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
        t.clean_cd -= dt
        t.joy = max(0.0, t.joy - 0.015 * dt)
        t.annoy = max(0.0, t.annoy - 0.02 * dt)
        sleeping = t.state == "sleep"
        t.air -= dt * (0.4 if sleeping else 1.0)
        t.energy -= t.metab * dt * (SLEEP_METAB if sleeping else 1.0)
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
                if t.surf:
                    t.surf.riders.discard(t.id)
                    t.surf = None
            t.state, t.state_t = "flee_shark", 1.5

        st = t.state
        if st in ("flipped", "dance", "lay", "breathe", "petted", "cleaning", "wipeout"):
            if t.state_t <= 0:
                if st == "wipeout":                           # 照れ笑い、またはしょんぼり
                    t.state = "swim"
                    t.say(random.choice(("blush", "note", "sweat", "dots")), 1.5)
                elif st == "flipped":
                    if t.annoy > 0.5:
                        t.say("anger")
                        t.state, t.state_t = "flee", 2.0
                    else:
                        t.joy = min(1.0, t.joy + 0.4)
                        t.say("note")
                        t.state, t.state_t = "dance", 1.2
                elif st == "lay":
                    self._lay(t)
                elif st == "breathe":
                    t.air = t.breath_gap * random.uniform(0.8, 1.2)
                    t.state = "sleep" if t.bed and t.night_pull(self.night) > 0.5 else "swim"
                elif st == "cleaning":
                    t.state = "swim"
                    t.clean_cd = random.uniform(2, 5) * HOUR
                    t.say("flower", 1.5)
                else:
                    t.state = "swim"
            elif st == "cleaning":
                t.joy = min(1.0, t.joy + 0.05 * dt)
                t.annoy = max(0.0, t.annoy - 0.1 * dt)
                t.energy = min(1.0, t.energy + 0.004 * dt)   # 寄生虫を取ってもらう
                if random.random() < dt / 3:
                    t.say(random.choice(("flower", "note", "blush")), 1.2, force=False)
        elif st == "surf":
            wv = t.surf
            if wv is None or t.id not in wv.riders or not water:
                t.state, t.surf = "swim", None
        elif st == "catch":
            wv = t.surf
            if wv is None or wv is not self.big_wave or t.id in wv.hit or wv.y > t.y + 8:
                t.state, t.surf = "swim", None
        elif st == "play":
            v = t.vis
            if v is None or v.gone or v.leaving or t.state_t <= 0 or t.energy < 0.25:
                t.state, t.vis = "swim", None
                t.say("note", 1.0)
            elif random.random() < dt / 3:
                t.say(random.choice(("star", "note", "heart")), 1.0, force=False)
        elif st == "sleep":
            t.fatigue = max(t.fatigue, -0.2)
            if t.fatigue <= 0 and t.night_pull(self.night) < 0.5:
                t.state, t.bed = "swim", None                # 朝になったら起きる
                if self.night < 0.4 and self.phase in ("Sunrise", "Dawn twilight"):
                    t.say("note", 1.5)
            elif t.air <= 0 and water:                       # 寝ていても息継ぎに浮上する
                self._start_breathe(t)
            elif random.random() < dt / 3:
                t.say("zzz", 1.5)
        elif st in ("flee", "flee_shark") and t.state_t > 0:
            pass
        else:
            self._decide(t, dt, water)
        self._steer(t, dt, water)

    def _start_breathe(self, t):
        t.state, t.state_t = "breathe", BREATH_TIME
        hx, hy = t.head()
        self.fx.append(("ripple", hx, hy))

    def _decide(self, t, dt, water):
        prev = t.state
        t.state = "swim"
        sleepy = t.fatigue + t.night_pull(self.night) > 1 and t.energy > 0.15
        hungry_line = t.eat_below + self.appetite_shift()
        if t.clutch and self.night > 0.5:
            t.state = "nest"                                  # 産卵は夜(ウミガメの習性)
            if t.nest is None:
                t.nest = self.beach_point()
        elif not water:
            pass                                              # 砂浜から海へ戻る途中
        elif t.air <= 0:
            self._start_breathe(t)
        elif sleepy and not t.clutch:
            if prev == "to_bed" and t.bed:
                t.state = "to_bed"
            elif self.reefs and (t.adult or random.random() < 0.7):   # 岩場やサンゴのそばで眠る
                r = min(self.reefs, key=lambda r: (r.x - t.x) ** 2 + (r.y - t.y) ** 2 *
                        (0.7 if r.kind == "rock" else 1.0))
                t.bed, t.bed_kind = r.bed_point(), r.kind
                t.state = "to_bed"
            else:
                t.bed, t.bed_kind = None, None
                t.state = "sleep"
                t.say("zzz", 2)
        elif t.energy < hungry_line and (prev == "food" or t.energy < hungry_line - 0.05):
            if t.food is None or t.food.gone or t.food_t <= 0:
                t.food = self._choose_food(t)
                t.food_t = 1.0
            t.food_t -= dt
            if t.food is not None:
                t.state = "food"
        elif prev == "court" and t.target is not None and t.target.alive:
            t.state = "court"
        elif prev == "to_clean" and t.goal is not None:
            t.state = "to_clean"
        elif self._can_mate(t) and self.night < 0.6:
            p = self._find_partner(t)
            if p:
                t.state, t.target = "court", p
        elif (t.adult and t.clean_cd <= 0 and 9 <= self.hour < 16 and t.energy > 0.45
              and random.random() < dt / (90 if 11 <= self.hour < 14 else 240)):
            school = self._free_school()
            if school:                                        # サンゴで熱帯魚にクリーニングしてもらう
                t.goal = school
                t.state = "to_clean"
        if t.state == "swim" and t.g["whim"] > 0.7 and t.joy > 0.4 and random.random() < dt / 120:
            t.state, t.state_t = "dance", 1.0
            t.say("note", 1.0)
        if t.state == "swim" and self.phase in ("Sunset", "Dusk") and random.random() < dt / 200:
            t.say("flower", 1.2, force=False)               # 夕焼けがきれい
        if t.energy < 0.2 and random.random() < dt / 6:
            t.say("sweat")

    def _free_school(self):
        free = [s for s in self.schools if s.cleaning is None]
        return random.choice(free) if free else None

    def _can_mate(self, t):
        return (t.alive and t.state in ("swim", "court") and t.adult and t.energy > 0.5
                and t.mate_cd <= 0 and not t.clutch and self.in_water(t.x, t.y)
                and self._pop < MAX_TURTLES - 1)

    def _find_partner(self, t):
        best, bd = None, 450.0
        for o in self.turtles:
            if o is t or o.sex == t.sex or not self._can_mate(o):
                continue
            d = math.hypot(o.x - t.x, o.y - t.y)
            if distance(t.g, o.g) < 0.04:
                d *= 3
            if o.id == t.partner:              # いつものパートナーを選びやすい
                d *= 0.3
            elif t.aff.get(o.id, 0) >= FRIEND_AFF:
                d *= 0.6
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
        self.sfx.append("munch")
        a = math.atan2(f.y - t.y, f.x - t.x)              # 食べ物の方を向く
        t.dir = (1 if math.cos(a) > 0 else 3) if abs(math.cos(a)) > abs(math.sin(a)) else (2 if math.sin(a) > 0 else 0)
        if f.kind == "plant":
            if f.b < PLANT_EDIBLE:
                t.food = None
                return
            bite = min(PLANT_BITE, f.b - PLANT_MIN)
            f.b -= bite
            f.bitten = self.time
            self.fx.append(("leaf", f.x, f.y))            # ちぎれた葉が舞う
            if f.b <= PLANT_MIN + 0.02:
                f.scars += 1
                f.scar_t = self.time
            t.energy += bite * (1.5 if t.herbivore else 0.9)
        else:
            f.gone = True
            t.energy += JELLY_ENERGY
            self.fx.append(("pop", f.x, f.y))
        t.energy = min(1.0, t.energy)
        t.joy = min(1.0, t.joy + 0.06)
        t.eat_cd = EAT_TIME
        t.food_t = 2.0 if f.kind == "plant" and f.b > PLANT_EDIBLE else 0.0   # 同じ株をもう一口
        if t.energy > 0.92:
            t.say("flower", 1.2)                    # おなかいっぱい
        elif random.random() < 0.3:
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
        self.event("lay", "%s laid %d egg%s on the night beach" % (self.tag(t), n, "s" if n != 1 else ""))

    def _steer(self, t, dt, water):
        sp = t.max_speed
        dx = dy = 0.0
        mul = 1.0
        st = t.state
        if st == "wipeout":                                  # 波にもまれて流される
            t.y += 10 * dt
            t.dir = int(t.anim / 0.12) % 4
            mul = 0.0
        elif st in ("sleep", "flipped", "lay", "breathe", "petted", "cleaning"):
            mul = 0.0
        elif st == "flee_shark" and self.shark:
            sh = self.shark
            dx, dy = t.x - sh.x, t.y - sh.y
            n0 = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n0, dy / n0 + 0.9
            mul = 1.6
        elif st == "catch" and t.surf:
            dx, dy = random.uniform(-0.1, 0.1), (t.surf.y + 2 - t.y)     # 沖の大波へ向かって泳ぐ
            mul = 1.5
        elif st == "surf" and t.surf:
            wv = t.surf
            t.y += (wv.y + 4 - t.y) * min(1.0, dt * 6)      # 波頭に乗って砂浜の方へ
            t.vy = wv.sp
            t.vx *= 0.9
            t.x += t.vx * dt
            t.dir = 2
            if not (wv.x - 10 <= t.x <= wv.x + wv.len + 10):
                wv.riders.discard(t.id)
            if getattr(t, "wipe_at", None) is not None and t.y >= t.wipe_at:
                wv.riders.discard(t.id)                       # ワイプアウト! 波にのまれてくるくる
                wv.wiped.add(t.id)
                t.state, t.state_t, t.surf, t.wipe_at = "wipeout", 1.6, None, None
                t.say("surprise", 1.2)
                self.fx.append(("splash", t.x, t.y))
                self.sfx.append("splash")
            return
        elif st == "play" and t.vis:
            v = t.vis
            t.orbit += dt * (2.2 if v.kind == "dolphin" else 0.8)
            if v.kind == "dolphin":                        # イルカのまわりをくるくる
                tx, ty = v.x + math.cos(t.orbit) * 38, v.y + math.sin(t.orbit) * 28
            else:                                          # マンタの後ろについて泳ぐ
                tx = v.x - (1 if v.vx >= 0 else -1) * (30 + 12 * math.cos(t.orbit))
                ty = v.y + 18 * math.sin(t.orbit)
            dx, dy = tx - t.x, ty - t.y
            mul = 1.5
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
            dx, dy = random.uniform(-0.2, 0.2), -1.0
        elif st == "to_bed" and t.bed:
            dx, dy = t.bed[0] - t.x, t.bed[1] - t.y
            mul = 0.8
            if math.hypot(dx, dy) < 6:
                t.state = "sleep"
                t.say("zzz", 2)
                mul = 0.0
        elif st == "to_clean" and t.goal:
            s = t.goal
            dx, dy = s.home.x - t.x, s.home.y - t.y
            if s.cleaning not in (None, t):
                t.state, t.goal = "swim", None
            elif math.hypot(dx, dy) < s.home.radius * 0.8:
                t.state, t.state_t = "cleaning", random.uniform(10, 18)
                s.cleaning = t
                t.goal = None
                t.say("flower", 1.5)
                mul = 0.0
                if self.time - self.clean_log_t > 240:
                    self.clean_log_t = self.time
                    self.event("clean", "%s is being cleaned by tropical fish" % self.tag(t))
        elif st == "food":
            f = t.food
            if f is None or f.gone:
                t.state, t.food = "swim", None
            else:
                dx, dy = f.x - t.x, f.y - t.y
                # 株のふちで止まり、首だけのばして食べる(水草が隠れないように)
                reach = (t.radius * 0.75 + 3 * (0.8 + 0.62 * plant_level(f.b)) * 0.6) if f.kind == "plant" else t.radius + 5
                d = math.hypot(dx, dy)
                if t.eat_cd > 0 or d < reach * 0.8:
                    mul = 0.0
                    if d < reach * 0.8:              # 近すぎたら少し下がる
                        dx, dy, mul = -dx, -dy, 0.3
                    if t.eat_cd <= 0:
                        self._eat(t, f)
                elif d < reach:
                    self._eat(t, f)
                    mul = 0.0
                else:
                    mul = 1.1
        elif st == "court":
            o = t.target
            if o is None or not o.alive or not self._can_mate(o):
                t.state, t.target = "swim", None
            else:
                dx, dy = o.x - t.x, o.y - t.y
                if random.random() < dt / 2:
                    t.say("heart" if o.id != t.partner or random.random() < 0.5 else "blush", 1.0)
        elif st == "flee" and self.cursor:
            dx, dy = t.x - self.cursor[0], t.y - self.cursor[1]
            mul = 1.5

        care = t.g["care"]
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
                if d < 45:
                    t.annoy = min(1.0, t.annoy + max(0.0, t.g["temper"] - 0.3) * 0.08 * dt)

        if dx == 0 and dy == 0 and mul > 0:
            jitter = 0.4 + 2.0 * t.g["whim"] + 2.5 * t.annoy
            t.heading += random.gauss(0, jitter) * dt
            dx, dy = math.cos(t.heading), math.sin(t.heading)
            nb = t.nb
            fw = (t.g["flock"] - 0.5) * 2 * care
            if self.phase in ("Sunset", "Dusk"):
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
            # パートナーや友達のそばにいたがる
            for other, pull, gap in ((self.by_id.get(t.partner), 0.6, 60), (t.best_friend(self.by_id), 0.4, 55)):
                if other is not None and other.state not in ("sleep", "dead"):
                    ox, oy = other.x - t.x, other.y - t.y
                    od = math.hypot(ox, oy) or 1.0
                    if od > gap:
                        dx += ox / od * pull
                        dy += oy / od * pull
            mul *= 0.55 + 0.4 * t.joy
            t.heading = math.atan2(dy, dx) if (dx or dy) else t.heading
        elif dx or dy:
            t.heading = math.atan2(dy, dx)
        if not water:
            mul *= 0.35
        elif st not in ("flee_shark", "nest", "play"):
            mul *= 1.0 - 0.3 * self.night
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
        if water and st not in ("nest",):
            s = self.shore(t.x) - m
            if t.y > s:
                t.y = s
                t.vy = -abs(t.vy)
                t.heading = -abs(t.heading)
        eating = st == "food" and t.food is not None and (t.eat_cd > 0 or mul == 0.0 or mul == 0.3)
        if eating:                                      # 食べている間は食べ物の方を向いたまま
            a = math.atan2(t.food.y - t.y, t.food.x - t.x)
            t.dir = (1 if math.cos(a) > 0 else 3) if abs(math.cos(a)) > abs(math.sin(a)) else (2 if math.sin(a) > 0 else 0)
        elif st != "dance" and abs(t.vx) + abs(t.vy) > 2:
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
                if not (a.state == "sleep" and b.state == "sleep"):
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
        for t in alive:
            if (t.id not in removed and t.alive and t.extra >= 1 and t.energy > 0.85
                    and t.state == "swim" and random.random() < dt / 600):
                self._split(t)

    def _mate(self, a, b):
        mom, dad = (a, b) if a.sex == "F" else (b, a)
        room = MAX_TURTLES - self.population()
        n = min(room, 3 + int(mom.g["fertility"] * 3.99),
                int((mom.energy - 0.12) / EGG_COST))        # 産める数は母親の栄養しだい
        if n <= 0:
            return
        again = mom.partner == dad.id
        for t in (a, b):
            t.mate_cd = MATE_COOLDOWN * (0.8 + 0.4 * random.random())
            t.energy -= EGG_COST * n if t is mom else 0.2
            t.state, t.target = "swim", None
            t.say("heart", 2.0)
        mom.partner, dad.partner = dad.id, mom.id
        mom.clutch = [{"g": mutate(crossover(mom.g, dad.g)),
                       "gen": max(mom.generation, dad.generation) + 1,
                       "par": "#%d x #%d" % (mom.id, dad.id)} for _ in range(n)]
        mom.nest = None
        self.event("mate", "%s and %s %s" % (self.tag(mom), self.tag(dad),
                                             "renewed their bond" if again else "fell in love and mated"))

    def _merge(self, a, b):
        t = Turtle(blend(a.g, b.g), (a.x + b.x) / 2, (a.y + b.y) / 2,
                   max(a.generation, b.generation), max(ADULT_AGE, min(a.age, b.age)),
                   sex=a.sex, lineage=a.lineage, parents="merged #%d + #%d" % (a.id, b.id),
                   extra=max(a.extra, b.extra) + 1)
        t.energy = min(1.0, a.energy + b.energy)
        t.joy = 0.8
        t.say("sparkle", 2.5)
        t.aff = {k: v for k, v in list(a.aff.items()) + list(b.aff.items()) if k not in (a.id, b.id)}
        self.turtles = [x for x in self.turtles if x is not a and x is not b]
        self.turtles.append(t)
        for o in self.turtles:
            if o.target in (a, b):
                o.target, o.state = None, "swim"
            if o.partner in (a.id, b.id):
                o.partner = t.id
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
        kids[0].aff[kids[1].id] = kids[1].aff[kids[0].id] = FRIEND_AFF * 1.5   # 分かれた2体は友達
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
        if not t.alive or t.state in ("lay", "flipped", "flee_shark", "surf"):
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
                t.say("zzz", 1.2)
                return
            t.state, t.bed = "swim", None
            t.fatigue = min(t.fatigue, 0.6)
        if like > 0:
            t.joy = min(1.0, t.joy + 0.15)
            t.annoy = max(0.0, t.annoy - 0.1)
            t.state, t.state_t = "petted", 1.5
            t.say("heart" if t.joy > 0.6 else random.choice(("note", "blush")), 1.2)
        else:
            t.annoy = min(1.0, t.annoy + 0.12 + 0.2 * t.g["temper"])
            t.say("anger" if t.annoy > 0.4 else "sweat", 1.2)
            if t.annoy > 0.5:
                t.state, t.state_t = "flee", 1.5

    def poke(self, t):
        self.sfx.append("flip")
        if t.state == "lay":
            t.say("anger", 1.0)
            return
        if t.surf:
            t.surf.riders.discard(t.id)
            t.surf = None
        if t.state == "sleep":
            t.annoy = min(1.0, t.annoy + 0.25 + 0.4 * t.g["temper"])
            t.fatigue = min(t.fatigue, 0.6)
            t.state, t.state_t, t.bed = "flipped", 1.5, None
            t.say("anger" if t.annoy > 0.5 else "question", 1.5)
            return
        t.annoy = min(1.0, t.annoy + 0.1 + 0.35 * t.g["temper"] * t.g["care"])
        t.state, t.state_t = "flipped", 2.5
        t.say("surprise", 1.0)

    def turtle_info(self, t):
        """カメのステータス(英語の行のリスト)。"""
        if not t.alive:
            return ["#%d  Lineage %s  Gen %d" % (t.id, t.lineage, t.generation),
                    "Died of %s at %s" % (t.cause, fmt_dur(t.age))]
        e = t.energy
        health = "Good" if e > 0.7 else "OK" if e > 0.4 else "Hungry" if e > 0.2 else "Starving"
        mood = ("sad" if t.emote == "cry" else "annoyed" if t.annoy > 0.5
                else "happy" if t.joy > 0.6 else "calm")
        bed = {"rock": "sleeping by the rocks", "coral": "sleeping in the coral"}.get(t.bed_kind, "sleeping")
        now = {"swim": "swimming", "food": "looking for food", "court": "courting",
               "nest": "going ashore to lay eggs", "lay": "laying eggs", "sleep": bed,
               "flipped": "flipped over!", "dance": "dancing with joy", "flee": "running away",
               "flee_shark": "fleeing from the shark!", "breathe": "poking its head out for air",
               "petted": "enjoying being petted", "to_bed": "heading to bed",
               "to_clean": "going to the cleaning station", "cleaning": "being cleaned by fish",
               "surf": "surfing!", "catch": "paddling out to catch the big wave", "wipeout": "wiped out!", "play": "playing with the visitor"}
        if not self.in_water(t.x, t.y) and t.state == "swim":
            st = "crawling to the sea"
        else:
            st = now.get(t.state, t.state)
        style = STYLES[style_of(t.g)]
        lines = ["#%d  %s  Lineage %s  Gen %d" % (t.id, "Female" if t.sex == "F" else "Male",
                                                   t.lineage, t.generation),
                 "Age %s / %s%s" % (fmt_dur(t.age), fmt_dur(t.lifespan),
                                    "" if t.adult else "  (young)"),
                 "Health %d%% (%s)   Mood: %s" % (round(e * 100), health, mood),
                 "%s   Size x%d%s" % ("Herbivore" if t.herbivore else "Omnivore", t.scale,
                                      "  (shark target)" if t.scale >= SHARK_PREY_SCALE else ""),
                 "Look: %s, %s%s" % (color_name(t.g), style, "  (rare!)" if is_dark(t.g) or style == "heart" else ""),
                 "Traits: " + (", ".join(traits(t.g)) or "Average")]
        p = self.by_id.get(t.partner)
        fr = self.friends(t)
        if p or fr:
            lines.append(("Partner: %s   " % self.tag(p) if p else "") +
                         ("Friends: " + ", ".join("#%d" % f.id for f in fr[:4]) if fr else ""))
        if t.parents:
            lines.append("Origin: " + t.parents)
        if t.clutch:
            lines.append("Carrying %d eggs%s" % (len(t.clutch),
                                                 "" if self.night > 0.5 else " (waits for night to nest)"))
        if t.pets:
            lines.append("Petted %d time%s" % (t.pets, "s" if t.pets != 1 else ""))
        lines.append("Now: " + st)
        return lines

    def hover_info(self, x, y):
        """マウスの下にあるもの(カメ以外)の説明。"""
        for e in self.eggs:
            if math.hypot(e.x - x, e.y - y) < 7:
                return ["Egg  Lineage %s  Gen %d" % (e.lineage, e.generation),
                        "Parents: %s" % e.parents,
                        ("Ready - hatches at night" if e.t <= 0 else "Hatches in %s (at night)" % fmt_dur(e.t))]
        sh = self.shark
        if sh and math.hypot(sh.x - x, sh.y - y) < 32:
            return ["Shark!", "Hunts turtles of size x%d or bigger offshore" % SHARK_PREY_SCALE,
                    "Small turtles and the shallows are safe"]
        for v in self.visitors:
            if math.hypot(v.x - x, v.y - y) < 26:
                return {"dolphin": ["Dolphin", "Friendly! Turtles gather to play with it"],
                        "manta": ["Manta ray", "A gentle giant. Turtles follow it around"],
                        "hermit": ["Hermit crab", "Just passing by on the beach"],
                        "coconut": ["Coconut crab", "Comes out on the beach at night",
                                    "Hatchlings get startled"]}[v.kind]
        for f in self.fish:
            if abs(f.x - x) < 6 and abs(f.y - y) < 5:
                return ["Tropical fish", "They live around the coral and",
                        "clean the turtles' shells and skin"]
        for j in self.jellies:
            if math.hypot(j.x - x, j.y - y) < 8:
                return ["Jellyfish", "Food for omnivores"]
        for r in self.reefs:
            if math.hypot(r.x - x, r.y - y) < r.radius:
                if r.kind == "coral":
                    return ["Coral reef", "Home of tropical fish. Turtles rest,",
                            "sleep and get cleaned here"]
                return ["Rocks", "A quiet place for turtles to sleep at night"]
        for p in self.plants:
            if math.hypot(p.x - x, p.y - y) < 5 + 4 * p.stage:
                m = self.meadows.get(p.m)
                lone = m is None or m["n"] < 3
                return ["%s  %d%%" % ("Lone seaweed sprout" if lone else "Seaweed", round(p.b * 100)),
                        "If not eaten, it grows into a new meadow" if lone else
                        ("Overgrazed! It may die" if p.scars else "Grows back when left alone")]
        mid = self.meadow_at(x, y)
        if mid is not None:
            return ["Seaweed meadow (%d plants)" % self.meadows[mid]["n"],
                    "It grows, gets eaten and slowly creeps along"]
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
        self.visitors = []
        self.update_daylight(self.clock(), log=False)
        for t in self.turtles:
            t.emote, t.food, t.target, t.surf, t.vis, t.goal = None, None, None, None, None, None
            if t.state not in ("sleep", "dead"):
                t.state = "swim"
        self._decompose(force=True)
        return self.births - b0, self.deaths - d0, self.laid - l0

    def _offline_step(self, dt):
        self.time += dt
        self._off_ts = getattr(self, "_off_ts", self.clock()) + dt
        self.update_daylight(self._off_ts, log=False)
        self._grow_plants(dt)
        jelly_in = min(JELLY_MAX, dt / JELLY_INTERVAL)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        self.by_id = {t.id: t for t in alive}
        random.shuffle(alive)
        shift = self.appetite_shift()
        for t in alive:
            t.age += dt
            t.mate_cd -= dt
            awake = t.awake_len / (t.awake_len + t.sleep_len) * (1 - 0.8 * t.night_pull(self.night))
            t.energy -= t.metab * dt * (awake + SLEEP_METAB * (1 - awake))
            t.joy = max(0.0, t.joy - 0.015 * dt)
            t.annoy = max(0.0, t.annoy - 0.02 * dt)
            tries = 0
            while t.energy < t.eat_below + shift and tries < 6:
                tries += 1
                if not t.herbivore and (jelly_in >= 1 or random.random() < jelly_in):
                    jelly_in = max(0.0, jelly_in - 1)
                    t.energy += JELLY_ENERGY
                    continue
                p = max(self.plants, key=lambda p: p.b, default=None)
                if p is None or p.b < PLANT_EDIBLE:
                    break
                bite = min(PLANT_BITE, p.b - PLANT_MIN)
                p.b -= bite
                if p.b <= PLANT_MIN + 0.02:
                    p.scars += 1
                    p.scar_t = self.time
                t.energy += bite * (1.5 if t.herbivore else 0.9)
            t.energy = min(1.0, t.energy)
            if t.energy <= 0:
                self._kill(t, "starvation")
            elif t.age >= t.lifespan:
                self._kill(t, "old age")
        if random.random() < dt / (sum(SHARK_GAP) / 2) * 0.12:      # サメに食べられるのはまれ
            big = [t for t in self.turtles if t.alive and t.scale >= SHARK_PREY_SCALE]
            if big:
                self._kill(random.choice(big), "a shark attack")
        self._decompose(force=True)
        if self.night > 0.5:
            for e in list(self.eggs):                  # 卵がかえるのは夜
                if e.t - dt <= 0:
                    self.eggs.remove(e)
                    t = Turtle(e.g, e.x, self.shore(e.x) - 15, e.generation, age=0.0, sex=e.sex,
                               lineage=e.lineage, parents=e.parents)
                    t.energy = HATCH_ENERGY
                    self.turtles.append(t)
                    self.births += 1
                    self.max_gen = max(self.max_gen, e.generation)
            for t in self.turtles:                     # 産卵も夜
                if t.alive and t.clutch:
                    t.x, t.y = self.beach_point(t.x)
                    self._lay(t)
                    t.x, t.y = self.water_point(30)
        for e in self.eggs:
            e.t = max(0.0, e.t - dt)
        if self.night < 0.6:
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
                "plants": [[p.x, p.y, p.b, p.m] for p in self.plants],
                "meadows": {str(k): v for k, v in self.meadows.items()}, "next_meadow": self.next_meadow,
                "reefs": [r.to_list() for r in self.reefs],
                "births": self.births, "deaths": self.deaths, "laid": self.laid,
                "merges": self.merges, "splits": self.splits, "max_gen": self.max_gen,
                "n_lineages": self.n_lineages, "gene_pool": self.gene_pool,
                "events": self.events, "history": self.history, "settings": self.settings}

    @classmethod
    def from_dict(cls, d):
        wd = cls(d.get("w", 700), d.get("h", 440))
        if d.get("reefs"):
            wd.reefs = [Reef(*r) for r in d["reefs"]]
            wd.seed_fish()
        else:
            wd.seed_reefs()
        wd.turtles = [Turtle.from_dict(x) for x in d.get("turtles", [])]
        for t in wd.turtles:
            if wd.in_water(t.x, t.y) is False and not t.clutch:
                t.y = wd.shore(t.x) - 20
        wd.eggs = [Egg.from_dict(e) for e in d.get("eggs", [])]
        for e in wd.eggs:
            if wd.in_water(e.x, e.y):
                e.x, e.y = wd.beach_point(e.x)
        wd.plants = [Plant(*p[:4]) for p in d.get("plants", [])]
        old = d.get("meadows")
        if isinstance(old, dict) and old:
            wd.meadows = {int(k): v for k, v in old.items()}
            wd.next_meadow = d.get("next_meadow", max(wd.meadows))
        else:                                    # 旧版: 近い株どうしを同じ藻場にまとめる
            wd.meadows, wd.next_meadow = {}, 0
            for p in wd.plants:
                near = [q for q in wd.plants if q.m is not None and (q.x - p.x) ** 2 + (q.y - p.y) ** 2 < 30 * 30]
                p.m = near[0].m if near else wd.new_meadow(p.x, p.y)
        for p in wd.plants:
            if p.m not in wd.meadows:
                p.m = wd.new_meadow(p.x, p.y)
        if len(wd.plants) < 8:
            wd.seed_plants()
        wd._update_meadows(log=False)
        for k in ("births", "deaths", "laid", "merges", "splits"):
            setattr(wd, k, d.get(k, 0))
        wd.max_gen = d.get("max_gen", 1)
        wd.gene_pool = [fill_genome(g) for g in d.get("gene_pool", [])]
        wd.n_lineages = d.get("n_lineages", 0) or max(1, len({t.lineage for t in wd.turtles}))
        wd.events = [tuple(e) for e in d.get("events", []) if len(e) == 3]
        wd.history = [tuple(h) for h in d.get("history", [])]
        wd.settings.update(d.get("settings", {}))
        wd.by_id = {t.id: t for t in wd.turtles}
        return wd

    def resize(self, w, h):
        if w < 100 or h < 100:
            return
        old_lt, old_h = self.land_top, self.h
        sx = w / self.w
        self.w, self.h = w, h
        new_lt = self.land_top

        def my(y):
            if y <= old_lt:
                return y * new_lt / old_lt
            return new_lt + (y - old_lt) * (h - new_lt) / max(1.0, old_h - old_lt)
        objs = (self.turtles + self.eggs + self.plants + self.jellies + self.reefs + self.fish
                + self.visitors + ([self.shark] if self.shark else []))
        for o in objs:
            o.x *= sx
            o.y = my(o.y)
        for v in self.visitors:
            v.y0 = my(v.y0)
        self._update_meadows(log=False)
        for t in self.turtles:
            if t.nest:
                t.nest = (t.nest[0] * sx, my(t.nest[1]))
            if t.bed:
                t.bed = (t.bed[0] * sx, my(t.bed[1]))
        for wv in self.waves:
            wv.reset(self, first=True)
        self.big_wave = None


# ---------------------------------------------------------------- 保存先(Google ドライブ)
def find_save_dir(env_name="UMIGAME_SAVE_DIR", folder="UmigamePet"):
    """(フォルダ, Googleドライブかどうか) を返す。"""
    env = os.environ.get(env_name)
    if env:
        return env, True
    home = os.path.expanduser("~")
    names = ("マイドライブ", "My Drive")
    cands = []
    if sys.platform.startswith("win"):
        for letter in string.ascii_uppercase[3:]:
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
                return os.path.join(c, folder), True
        except OSError:
            pass
    return os.path.join(home, folder), False


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
# 息継ぎ: 首をのばして頭を水面に出す(W=水面の輪)。甲羅は水の中で薄く見える
EAT_HEAD = (("...........",            # 口を閉じる
             "....HHH....",
             "....EHE...."),
            ("...H...H...",            # 口を開けて葉をくわえる
             "...HMLMH...",
             "....EHE...."))
BREATHE_HEAD = ("...WWWWW...",
                "..W.EHE.W..",
                "...WHHHW...",
                "....HHH....")

# 表情: (色の対応, 形)。X は1色目
EMOTES = {
    "heart": ({"X": "#ff6f96"}, (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X...")),
    "note": ({"X": "#ffd23f"}, ("...XXX.", "...X.X.", "...X...", "...X...", ".XXX...", "XXXX...", ".XX....")),
    "anger": ({"X": "#ff3a3a"}, (".X...X.", "XX...XX", ".......", ".......", "XX...XX", ".X...X.")),
    "zzz": ({"X": "#ffffff"}, ("XXXXX", "...X.", "..X..", ".X...", "XXXXX")),
    "bang": ({"X": "#ffffff"}, (".X.", ".X.", ".X.", ".X.", "...", ".X.")),
    "question": ({"X": "#ffffff"}, (".XXX.", "X...X", "...X.", "..X..", ".....", "..X..")),
    "surprise": ({"X": "#ffffff"}, (".X..XXX.", ".X.X...X", ".X....X.", ".X...X..", "........", ".X...X..")),
    "sparkle": ({"X": "#fff7a8"}, ("...X...", "...X...", "..XXX..", "XXXXXXX", "..XXX..", "...X...", "...X...")),
    "star": ({"X": "#ffe14d", "o": "#fff6b8"}, ("...X...", "..XoX..", "XXXoXXX", ".XoooX.", "..XoX..", ".XX.XX.", "X.....X")),
    "sweat": ({"X": "#5aa8ff"}, ("..X..", ".XXX.", "XXXXX", "XXXXX", ".XXX.")),
    "cry": ({"X": "#7cc4ff"}, ("X...X", "X...X", "XX.XX", "XX.XX", ".....", "X...X")),
    "blush": ({"X": "#ff9cc0"}, ("XX...XX", "XXX.XXX", ".X...X.")),
    "flower": ({"X": "#ffb3d1", "o": "#ffe066"}, (".X.X.", "XXoXX", ".XoX.", "XXoXX", ".X.X.")),
    "dots": ({"X": "#ffffff"}, ("X.X.X",)),
    "egg": ({"X": "#fffdf0"}, (".XX.", "XXXX", "XXXX", "XXXX", ".XX.")),
    "ghost": ({"X": "#f4f4ff"}, (".XXX.", "XXXXX", "X.X.X", "XXXXX", "XXXXX", "X.X.X")),
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
# サンゴ・岩(上から見た形)。X=色 x=影 o=明るい所
REEF_ART = {
    "branch": ("..X.X..", ".XoXoX.", "X.XxX.X", ".XxXxX.", "XX.X.XX", ".X.x.X.", "...X..."),
    "brain": (".XXXX.", "XoxXxX", "XxXoxX", "XXxXoX", ".XXXX."),
    "fan": ("X.X.X.X", "XoXoXoX", ".XxXxX.", "..XXX..", "...x..."),
    "table": (".XXXXX.", "XoXoXoX", "XXXXXXX", "XxXxXxX", ".XXXXX."),
    "rock1": ("..oooo..", ".oXXXXo.", "oXXXXXXx", "XXXXXxXx", ".XXxxxx.", "..xxxx.."),
    "rock2": ("...oooo...", "..oXXXXo..", ".oXXXXXXo.", "oXXXXXXXXx", "XXXXXXxXxx", ".XXXxxxxx.", "..xxxxxx.."),
}
CORAL_COLORS = (("#ff9fb4", "#d9708a", "#ffd0dc"), ("#ffb27a", "#d9844a", "#ffd9b8"),
                ("#c9a2ff", "#9a72d6", "#e7d6ff"), ("#ffe27a", "#d6b64a", "#fff2b8"))
ROCK_COLORS = ("#8395a6", "#5f7182", "#aebdca")
FISH_ART = {   # 右向き(左が尾びれ、右が頭)
    "yellow": ({"X": "#ffe04a", "e": "#222222"}, ("X.XXX..", "XXXXXeX", "X.XXX..")),
    "blue": ({"X": "#3f7fff", "y": "#ffe04a", "e": "#111111"}, ("y.XXX..", "yXXXXeX", "y.XXX..")),
    "clown": ({"X": "#ff8a2a", "w": "#ffffff", "e": "#222222"}, ("X.XwXw.", "XXXwXeX", "X.XwXw.")),
}
VIS_ART = {   # どれも右向き(右が頭)。左向きは左右反転して使う
    # イルカ(上から): 左に尾びれ、頭の近くに胸びれ、右端にくちばし
    "dolphin": ({"X": "#86b4dc", "o": "#cfe6f7", "e": "#1c2530"},
                (("X.............XX........", "XX...........XXX........", ".XX.XXXXXXXXXXXXXXXXX...",
                  "..XXXoooooooooooooooeXXX", ".XX.XXXXXXXXXXXXXXXXX...", "XX...........XXX........",
                  "X.............XX........"),
                 ("..............XX........", "X............XXX........", "XXX.XXXXXXXXXXXXXXXXX...",
                  "..XXXoooooooooooooooeXXX", "XXX.XXXXXXXXXXXXXXXXX...", "X............XXX........",
                  "..............XX........"))),
    # マンタ(上から): 左に細い尾、右に頭びれ(2本)、大きな胸びれがはばたく
    "manta": ({"X": "#3b4a66", "o": "#5a6c8c", "w": "#2c3850", "c": "#4a5c80"},
              (("........X.........", ".......XXX........", "......XXoXX.......", ".....XXoooXXXc....",
                "wwwwwXXoooooXXX...", ".....XXoooXXXc....", "......XXoXX.......", ".......XXX........",
                "........X........."),
               ("..................", "........X.........", "......XXXX........", ".....XXoooXXXc....",
                "wwwwwXXoooooXXX...", ".....XXoooXXXc....", "......XXXX........", "........X.........",
                ".................."))),
    # ヤドカリ(横から): 左に貝殻、右に目とはさみ
    "hermit": ({"X": "#f2a6c0", "x": "#c97a96", "r": "#e2503c", "e": "#222222"},
               (("..XXX...", ".XxXXX..", "XXxXXXr.", "XXXXXrer", ".rrrrrr.", "r.r.r.r."),
                ("..XXX...", ".XxXXX..", "XXxXXXr.", "XXXXXrer", ".rrrrrr.", ".r.r.r.r"))),
    # ヤシガニ(上から、頭が上の絵を右へ回して使う。ヤシガニは前へ歩く)
    "coconut": ({"X": "#5f5fb8", "x": "#3f3f8c", "o": "#8f8fe0", "e": "#ffffff"},
                (("X.......X", ".X.eee.X.", "..XoooX..", "XXXxxxXXX", "..XxxxX..", ".X.XXX.X.",
                  "X...X...X"),
                 (".X.....X.", "X..eee..X", "..XoooX..", "XXXxxxXXX", "..XxxxX..", "X..XXX..X",
                  ".X..X..X."))),
}
JELLY_ART = (".XXX.", "XXXXX", "X.X.X", "X.X.X")
EGG_ART = (".XX.", "XXXX", "XXXX", ".XX.")
STAR_ART = ("..X..", "..X..", "XXXXX", ".XXX.", "X...X")
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

WATER_DEEP = (0x14, 0xb3, 0xc8)
WATER_SHALLOW = (0x8c, 0xf0, 0xdf)
WATER_MID = "#3fc9d0"
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


def pattern_on(style, x, y, bits):
    """甲羅の内側 (x 3〜7, y 3〜8) で模様の色にするかどうか。左右対称。"""
    mx = x if x <= 5 else 10 - x
    ix, iy = mx - 2, y - 2                   # ix 1〜3, iy 1〜6
    idx = iy * 4 + ix
    bit = 0 <= idx < PATTERN_BITS and bits[idx]
    if style == 0:                            # 無地(真ん中に小さな線)
        return mx == 5 and iy in (2, 4)
    if style == 1:                            # 水玉
        return (ix + iy) % 3 == 0 and (bit or (ix + iy) % 2 == 0)
    if style == 2:                            # しま
        return iy % 2 == 0
    if style == 3:                            # 亀甲(甲羅の板の線)
        return iy % 3 == 0 or (ix == 1 and iy % 3 != 0) or mx == 5 and iy % 3 == 0
    if style == 4:                            # リング
        return (ix == 1 and 2 <= iy <= 5) or (iy in (2, 5) and ix >= 1) and not (mx == 5 and iy in (3, 4))
    if style == 5:                            # まだら(遺伝子のビットそのまま)
        return bit
    if style == 6:                            # 市松
        return (ix + iy) % 2 == 0
    heart = {(4, 3), (6, 3), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (4, 5), (5, 5), (6, 5), (5, 6)}
    return (x, y) in heart                    # ハート(とてもまれ)


def shell_colors(g):
    h = pastel_hue(g["hue"])
    h2 = pastel_hue(g["hue2"])
    if is_dark(g):                            # まれに生まれる濃い色
        return (hexcol(h, 0.62, 0.52), hexcol(h, 0.7, 0.34), hexcol(h2, 0.55, 0.85),
                hexcol(h + 0.04, 0.3, 0.72))
    return (hexcol(h, 0.30, 0.96), hexcol(h, 0.45, 0.72), hexcol(h2, 0.42, 0.84),
            hexcol(h + 0.04, 0.14, 0.97))


def turtle_pixels(g, frame, mode):
    """mode: normal / belly / dead / breathe。上向きの色の格子(breathe は縦に長い)。"""
    base = FRAMES[frame]
    shell, rim, pat, skin = shell_colors(g)
    eye = "#3a3344"
    if mode == "belly":
        shell, rim, pat = "#fbf2d2", "#c9b98a", "#eadcae"
    if mode == "dead":
        shell, rim, pat, skin, eye = "#a8a8a8", "#787878", "#989898", "#c0c0c0", "#505050"
    style = style_of(g)
    out = []
    rows = base
    shift = 0
    if mode == "breathe":
        rows = BREATHE_HEAD + base[2:]
        shift = len(BREATHE_HEAD) - 2
    elif mode == "eat":                       # もぐもぐ: 首をのばして口を開け閉め
        rows = (EAT_HEAD[frame] + FRAMES[0][2:])
        shift = 1
    for y0, row in enumerate(rows):
        y = y0 - shift
        line = []
        for x, c in enumerate(row):
            if c == "S":
                edge = x == 0 or x == 10 or row[x - 1] != "S" or row[x + 1] != "S"
                if edge or y == 2 or y == 9:
                    col = rim
                elif mode == "belly":
                    col = pat if (x + y) % 3 == 0 else shell
                else:
                    col = pat if pattern_on(style, x, y, g["pattern"]) else shell
                if mode == "breathe":
                    col = mix_hex(col, WATER_MID, 0.45)       # 水の中の甲羅
                line.append(col)
            elif c in "HFT":
                col = skin
                if mode == "breathe" and c == "F":
                    col = mix_hex(col, WATER_MID, 0.45)
                line.append(col)
            elif c == "E":
                line.append(eye)
            elif c == "W":
                line.append("#ffffff")
            elif c == "M":
                line.append("#7a3846")                    # 開いた口
            elif c == "L":
                line.append("#4fc27a")                    # くわえた葉
            else:
                line.append(None)
        out.append(line)
    return out


def plant_level(b):
    """水草の量 → 絵の段階(0: 根だけ、1〜8: 小さい→大きい)。食べると1段ずつ小さくなるのが見える。"""
    if b < 0.12:
        return 0
    return min(8, 1 + int((b - 0.12) / 0.88 * 8))


def plant_rows(level):
    """茂った水草の絵を、中心から level に応じた大きさだけ残す。"""
    if level == 0:
        return PLANT_ART[0]
    full = PLANT_ART[3]
    rr = 0.8 + level * 0.62
    return tuple("".join(ch if math.hypot(x - 5, y - 5) <= rr else "." for x, ch in enumerate(row))
                 for y, row in enumerate(full))


def mix_hex(c1, c2, f):
    a, b = hex_rgb(c1), hex_rgb(c2)
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * f) for x, y in zip(a, b))


def tint_rgb(rgb, k):
    return tuple(min(255, int(c * m)) for c, m in zip(rgb, k))


def hex_rgb(col):
    return tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))


def tint_hex(col, k):
    return "#%02x%02x%02x" % tint_rgb(hex_rgb(col), k)


def mix(c1, c2, f):
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


def water_color(world, y, k=(1, 1, 1)):
    f = min(1.0, max(0.0, y / max(1.0, world.land_top + 8)))
    return tint_rgb(tuple(int(a + (b - a) * f) for a, b in zip(WATER_DEEP, WATER_SHALLOW)), k)


def sparkle_amount(world):
    """水面のきらめきの量(夏の真昼がいちばん多い)。"""
    h = world.hour
    if world.phase == "Daytime":
        return 0.35 + 0.65 * max(0.0, math.sin(math.pi * (h - SUNRISE - 0.8) / (SUNSET - SUNRISE - 1.8)))
    return {"Sunrise": 0.55, "Sunset": 0.7, "Dusk": 0.3, "Dawn twilight": 0.25, "Night": 0.35}.get(world.phase, 0.3)


# ---------------------------------------------------------------- サウンド(標準ライブラリで合成)
SR = 22050                     # サンプリング周波数
SOUND_VER = 1                  # 音を作り直したら上げる(キャッシュのファイル名に入る)
WAVE_LOOP_SEC = 12.0


def _env(i, n, attack=0.01, release=None):
    """簡単な包絡線(立ち上がり→指数的に減衰)。"""
    t = i / SR
    a = min(1.0, t / attack) if attack > 0 else 1.0
    if release:
        a *= math.exp(-t / release)
    return a


def _tone(freq, dur, vol=0.3, attack=0.005, release=0.12, freq2=None, harm=0.0):
    n = int(SR * dur)
    out = []
    ph = 0.0
    for i in range(n):
        f = freq if freq2 is None else freq + (freq2 - freq) * i / n
        ph += 2 * math.pi * f / SR
        v = math.sin(ph) + harm * math.sin(2 * ph)
        out.append(v * vol * _env(i, n, attack, release))
    return out


def _noise(dur, vol=0.3, lp=0.2, attack=0.01, release=0.15, lp2=None, rnd=None):
    """ローパスをかけた雑音(しぶき・波・ざわめき)。lp2 があると音色が変化する。"""
    rnd = rnd or random.Random(1)
    n = int(SR * dur)
    out, y = [], 0.0
    for i in range(n):
        a = lp if lp2 is None else lp + (lp2 - lp) * i / n
        y += a * (rnd.uniform(-1, 1) - y)
        out.append(y * vol * _env(i, n, attack, release) * (1.0 / max(0.15, math.sqrt(a))))
    return out


def _seq(*parts, gap=0.0):
    out = []
    for p in parts:
        out += p + [0.0] * int(SR * gap)
    return out


def _add(a, b, offset=0.0):
    o = int(SR * offset)
    out = list(a) + [0.0] * max(0, o + len(b) - len(a))
    for i, v in enumerate(b):
        out[o + i] += v
    return out


def make_wave_loop(sec=WAVE_LOOP_SEC):
    """寄せては返す波の音(12秒で切れ目なくつながる)。"""
    rnd = random.Random(7)
    fade = int(SR * 0.4)
    n = int(SR * sec) + fade
    out = []
    lo = hi = 0.0
    for i in range(n):
        t = i / SR
        x = rnd.uniform(-1, 1)
        lo += 0.015 * (x - lo)          # 遠くのうなり
        hi += 0.18 * (x - hi)           # 波打ち際のざわめき
        swell = (max(0.0, math.sin(2 * math.pi * t / 6.0)) ** 2 * 0.7
                 + max(0.0, math.sin(2 * math.pi * t / 4.0 + 1.3)) ** 3 * 0.45)
        out.append(lo * 2.2 * (0.6 + 0.4 * swell) + hi * 0.55 * swell)
    body = out[:n - fade]
    for i in range(fade):                # 終わりを始まりに重ねてつなぎ目を消す
        f = i / fade
        body[i] = body[i] * f + out[n - fade + i] * (1 - f)
    peak = max(abs(v) for v in body) or 1.0
    return [v / peak * 0.32 for v in body]


def make_sounds():
    """効果音(名前 → サンプルの列)。"""
    s = {}
    s["splash"] = _add(_noise(0.35, 0.35, 0.35, 0.003, 0.08), _tone(320, 0.2, 0.12, 0.003, 0.06, freq2=120))
    s["breath"] = _noise(0.6, 0.12, 0.05, 0.15, 0.25)
    s["note"] = _seq(_tone(880, 0.1, 0.16, 0.003, 0.06), _tone(1175, 0.16, 0.16, 0.003, 0.08))
    s["heart"] = _seq(_tone(660, 0.08, 0.13, 0.003, 0.05), _tone(990, 0.08, 0.13, 0.003, 0.05),
                      _tone(1320, 0.2, 0.13, 0.003, 0.1))
    s["anger"] = _tone(150, 0.25, 0.14, 0.005, 0.12, freq2=120, harm=0.6)
    s["surprise"] = _tone(420, 0.18, 0.15, 0.003, 0.12, freq2=1250)
    s["flip"] = _add(_tone(95, 0.18, 0.3, 0.002, 0.06), _tone(300, 0.3, 0.12, 0.003, 0.15, freq2=620), 0.05)
    s["munch"] = _seq(_noise(0.04, 0.2, 0.5, 0.001, 0.015), _noise(0.04, 0.2, 0.5, 0.001, 0.015),
                      _noise(0.04, 0.18, 0.5, 0.001, 0.015), gap=0.05)
    s["hatch"] = _seq(*[_tone(f, 0.07, 0.1, 0.002, 0.05) for f in (1319, 1568, 1976, 2637)])
    s["lay"] = _add(_tone(120, 0.2, 0.25, 0.003, 0.08), _noise(0.25, 0.1, 0.12, 0.01, 0.1))
    s["death"] = _tone(660, 0.9, 0.12, 0.02, 0.5, freq2=330)
    s["shark"] = _seq(_tone(82, 0.32, 0.32, 0.01, 0.2, harm=0.7), _tone(87, 0.5, 0.32, 0.01, 0.3, harm=0.7), gap=0.12)
    s["dolphin"] = _seq(_tone(2000, 0.12, 0.08, 0.003, 0.1, freq2=3400), _tone(3400, 0.14, 0.08, 0.003, 0.1, freq2=2500),
                        _noise(0.02, 0.15, 0.6, 0.001, 0.01), _noise(0.02, 0.15, 0.6, 0.001, 0.01), gap=0.04)
    s["whoosh"] = _noise(0.6, 0.22, 0.03, 0.15, 0.3, lp2=0.35)
    s["bell"] = _add(_tone(1046, 1.2, 0.1, 0.003, 0.5), _tone(2093, 0.8, 0.04, 0.003, 0.3))
    s["bigwave"] = _noise(2.6, 0.55, 0.02, 0.6, 1.0, lp2=0.25, rnd=random.Random(3))
    s["chomp"] = _add(_noise(0.2, 0.35, 0.25, 0.002, 0.06), _tone(60, 0.25, 0.35, 0.002, 0.1))
    s["sparkle"] = _seq(*[_tone(f, 0.06, 0.08, 0.002, 0.04) for f in (2093, 2637, 3136)])
    return s


def write_wav(path, samples):
    import array
    import wave
    data = array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in samples))
    if sys.byteorder == "big":
        data.byteswap()
    tmp = path + ".tmp"
    with wave.open(tmp, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())
    os.replace(tmp, path)


def sound_cache_dir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "umigame_sounds_v%d" % SOUND_VER)


def build_sound_files(folder=None):
    """音のファイルを作る(作ってあれば作らない)。{名前: パス} を返す。"""
    folder = folder or sound_cache_dir()
    os.makedirs(folder, exist_ok=True)
    names = ["waves", "splash", "breath", "note", "heart", "anger", "surprise", "flip", "munch",
             "hatch", "lay", "death", "shark", "dolphin", "whoosh", "bell", "bigwave", "chomp", "sparkle"]
    paths = {n: os.path.join(folder, n + ".wav") for n in names}
    if not all(os.path.exists(p) for p in paths.values()):
        sounds = make_sounds()
        sounds["waves"] = make_wave_loop()
        for n in names:
            write_wav(paths[n], sounds[n])
    return paths


def scaled_wav(path, level):
    """音量 level(0〜10)に下げた WAV を作って、そのパスを返す(作ってあれば作らない)。
    winmm や afplay は音量を変えられないので、音量ごとのファイルで鳴らす。"""
    if level >= 10:
        return path
    out = path[:-4] + "_v%d.wav" % level
    if not os.path.exists(out):
        import array
        import wave
        with wave.open(path) as f:
            params = f.getparams()
            data = array.array("h", f.readframes(f.getnframes()))
        if sys.byteorder == "big":
            data.byteswap()
        k = (level / 10.0) ** 1.6                 # 耳に自然な変化(小さい音量を細かく)
        data = array.array("h", (int(v * k) for v in data))
        if sys.byteorder == "big":
            data.byteswap()
        tmp = out + ".tmp"
        with wave.open(tmp, "wb") as f:
            f.setparams(params)
            f.writeframes(data.tobytes())
        os.replace(tmp, out)
    return out


def vol_gain(level):
    return (max(0, min(10, level)) / 10.0) ** 1.6


class _PygameBackend:
    name = "pygame"

    def __init__(self, paths):
        import pygame
        pygame.mixer.init(SR, -16, 1, 512)
        pygame.mixer.set_num_channels(12)
        self.pg = pygame
        self.snd = {n: pygame.mixer.Sound(p) for n, p in paths.items()}
        self.wave_ch = None

    def play(self, name, level):
        ch = self.snd[name].play()
        if ch is not None:
            ch.set_volume(vol_gain(level))

    def waves(self, on, level):
        if on and level > 0:
            if self.wave_ch is None:
                self.wave_ch = self.snd["waves"].play(loops=-1)
            if self.wave_ch is not None:
                self.wave_ch.set_volume(vol_gain(level))
        elif self.wave_ch is not None:
            self.wave_ch.stop()
            self.wave_ch = None

    def tick(self):
        pass

    def close(self):
        self.pg.mixer.quit()


class _MciBackend:
    """Windows 標準の winmm(MCI)。複数の音を同時に鳴らせる。"""
    name = "winmm"

    def __init__(self, paths):
        import ctypes
        self.mci = ctypes.windll.winmm.mciSendStringW
        self.buf = ctypes.create_unicode_buffer(64)
        self.paths = paths
        self.live = []
        self.n = 0
        self.wave_on = False
        self.wave_open = None
        self.lengths = {n: self._length(p) for n, p in paths.items()}

    def _cmd(self, s):
        return self.mci(s, self.buf, 64, 0)

    @staticmethod
    def _length(path):
        import wave
        try:
            with wave.open(path) as f:
                return f.getnframes() / f.getframerate()
        except Exception:
            return 2.0

    def play(self, name, level):
        if len(self.live) >= 8 or level <= 0:
            return
        self.n += 1
        alias = "umifx%d" % self.n
        path = scaled_wav(self.paths[name], level)
        if self._cmd('open "%s" type waveaudio alias %s' % (path, alias)) == 0:
            self._cmd("play %s" % alias)
            self.live.append((alias, time.monotonic() + self.lengths[name] + 0.5))

    def waves(self, on, level):
        self.wave_on = on and level > 0
        if self.wave_open is not None:
            self._cmd("close umiwaves")
            self.wave_open = None
        if self.wave_on:
            self._cmd('open "%s" type waveaudio alias umiwaves' % scaled_wav(self.paths["waves"], level))
            self.wave_open = level
            self._cmd("play umiwaves from 0")

    def tick(self):
        now = time.monotonic()
        keep = []
        for alias, end in self.live:
            if now > end:
                self._cmd("close %s" % alias)
            else:
                keep.append((alias, end))
        self.live = keep
        if self.wave_on:
            self._cmd("status umiwaves mode")
            if self.buf.value == "stopped":
                self._cmd("play umiwaves from 0")

    def close(self):
        self._cmd("close all")


class _ProcessBackend:
    """macOS(afplay)/ Linux(paplay, aplay)。"""
    name = "process"

    def __init__(self, paths, player):
        import subprocess
        self.sp = subprocess
        self.paths, self.player = paths, player
        self.wave_proc = None
        self.wave_on = False
        self.wave_level = 10
        self.procs = []

    def _run(self, path):
        return self.sp.Popen([self.player, path], stdout=self.sp.DEVNULL, stderr=self.sp.DEVNULL)

    def play(self, name, level):
        self.procs = [p for p in self.procs if p.poll() is None]
        if len(self.procs) < 6 and level > 0:
            self.procs.append(self._run(scaled_wav(self.paths[name], level)))

    def waves(self, on, level):
        self.wave_on, self.wave_level = on and level > 0, level
        if self.wave_proc and self.wave_proc.poll() is None:
            self.wave_proc.terminate()
        self.wave_proc = None
        self.tick()

    def tick(self):
        if self.wave_on and (self.wave_proc is None or self.wave_proc.poll() is not None):
            self.wave_proc = self._run(scaled_wav(self.paths["waves"], self.wave_level))

    def close(self):
        for p in self.procs + ([self.wave_proc] if self.wave_proc else []):
            if p.poll() is None:
                p.terminate()


class SoundSystem:
    """波の音(ループ)と効果音。使える方法を順に試す: pygame → Windows の winmm → afplay/aplay → 無音。
    音のファイルは最初に一度だけ合成して一時フォルダに置く(別スレッドで作るので起動は遅くならない)。
    音量は波の音・効果音それぞれ 0〜10(10段階)。"""

    MIN_GAP = {"note": 0.6, "heart": 0.6, "breath": 2.0, "munch": 0.8, "anger": 0.8, "surprise": 0.5,
               "splash": 0.2, "sparkle": 0.6, "whoosh": 1.0, "bell": 2.0}

    def __init__(self, waves_on=True, fx_on=True, backend=None, waves_vol=6, fx_vol=7):
        self.waves_on, self.fx_on = waves_on, fx_on
        self.waves_vol, self.fx_vol = waves_vol, fx_vol
        self.backend = backend
        self.status = "loading"
        self.last = {}
        self.recent = []
        if backend is None:
            import threading
            threading.Thread(target=self._load, daemon=True).start()
        else:
            self.status = "ready"
            self.backend.waves(self.waves_on, self.waves_vol)

    def _load(self):
        try:
            paths = build_sound_files()
        except Exception as ex:
            self.status = "off (%s)" % ex
            return
        self._paths = paths
        self.status = "files"

    def _start_backend(self):
        paths = self._paths
        for make in (lambda: _PygameBackend(paths),
                     (lambda: _MciBackend(paths)) if sys.platform.startswith("win") else None,
                     self._process_backend):
            if make is None:
                continue
            try:
                b = make()
                if b is not None:
                    self.backend = b
                    break
            except Exception:
                continue
        if self.backend is None:
            self.status = "off (no audio player)"
            return
        self.status = "ready"
        self._safe(self.backend.waves, self.waves_on, self.waves_vol)

    def _process_backend(self):
        import shutil
        for player in (("afplay",) if sys.platform == "darwin" else ("paplay", "aplay")):
            if shutil.which(player):
                return _ProcessBackend(self._paths, player)
        return None

    @staticmethod
    def _safe(fn, *args):
        try:
            fn(*args)
        except Exception:
            pass

    def tick(self):
        if self.status == "files":
            self._start_backend()
        if self.backend is not None:
            self._safe(self.backend.tick)

    def play(self, name):
        if not self.fx_on or self.fx_vol <= 0 or self.backend is None:
            return
        now = time.monotonic()
        if now - self.last.get(name, -99) < self.MIN_GAP.get(name, 0.3):
            return
        self.recent = [t for t in self.recent if now - t < 1.0]
        if len(self.recent) >= 4:
            return
        self.last[name] = now
        self.recent.append(now)
        self._safe(self.backend.play, name, self.fx_vol)

    def set_waves(self, on, vol=None):
        self.waves_on = on
        if vol is not None:
            self.waves_vol = max(0, min(10, vol))
        if self.backend is not None:
            self._safe(self.backend.waves, self.waves_on, self.waves_vol)

    def set_fx(self, on, vol=None):
        self.fx_on = on
        if vol is not None:
            self.fx_vol = max(0, min(10, vol))

    def close(self):
        if self.backend is not None:
            self._safe(self.backend.close)


# 出来事・表情 → 効果音
EVENT_SOUND = {"mate": "heart", "lay": "lay", "hatch": "hatch", "death": "death", "surf": "whoosh",
               "merge": "sparkle", "split": "sparkle", "time": "bell", "clean": "note", "sad": "death"}
EMOTE_SOUND = {"note": "note", "flower": "note", "star": "note", "heart": "heart", "blush": "heart",
               "anger": "anger", "surprise": "surprise", "bang": "surprise", "sparkle": "sparkle"}


def event_sound(kind, text):
    if kind == "shark":
        return "shark" if text.startswith("A shark appeared") else None
    if kind == "wave":
        return "bigwave" if "coming" in text else None
    if kind == "visitor":
        return "dolphin" if "dolphin" in text else "whoosh" if "manta" in text else None
    if kind == "play":
        return "dolphin" if "dolphin" in text else "note"
    return EVENT_SOUND.get(kind)


# ---------------------------------------------------------------- 画面(tkinter)
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
        self.show_rel = False

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
        self.tables = {"plant": {}, "jelly": {}, "egg": {}, "fish": {}, "visitor": {}}
        self.emote_img = {k: self._img(px, cols, 2) for k, (cols, px) in EMOTES.items()}
        self.jelly_img = self._img(JELLY_ART, {"X": "#ffc4ee"}, 2)
        self.bg_tint = None
        self.make_tinted_images((1, 1, 1))
        self.shark_item = None
        self.bg_items = []
        self.reef_items = []
        self.foam = c.create_line(0, 0, 1, 1, fill="#ffffff", width=2, tags="bg2")
        self.wave_items = [c.create_line(0, 0, 1, 1, fill="#ffffff", width=2, smooth=True,
                                         capstyle="round", tags="wave") for _ in range(N_WAVES)]
        self.big_items = [c.create_line(0, 0, 1, 1, fill="#ffffff", width=w, smooth=True, state="hidden",
                                        capstyle="round", tags="wave") for w in (5, 2)]
        self.glitter = [c.create_line(0, 0, 1, 1, width=2, state="hidden", tags="glit") for _ in range(30)]
        self.rel_lines = []
        self.glit_t = 0.0
        self.light_t = 0.0
        self.rel_t = 0.0
        self.fx_items = []
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
                                  text="Click: status  Dbl-click: flip  Stroke: pet  Click water: jellyfish  "
                                       "Shift+Click: seaweed  Right-click: on top  L: lineage  R: friends")
        # 音(波の音・効果音)と ON/OFF ボタン
        st = self.world.settings
        self.sound = SoundSystem(st["waves"], st["fx"], waves_vol=st["waves_vol"], fx_vol=st["fx_vol"])
        self.sound_ui = {}       # "waves"/"fx" → (−, 名前, ＋) の文字
        for key in ("waves", "fx"):
            items = tuple(c.create_text(0, 0, anchor="se", font=("", 9, "bold"), tags=("ui", "btn"))
                          for _ in range(3))
            self.sound_ui[key] = items
            minus, label, plus = items
            c.tag_bind(label, "<Button-1>", lambda e, k=key: self.toggle_sound(k))
            c.tag_bind(minus, "<Button-1>", lambda e, k=key: self.change_volume(k, -1))
            c.tag_bind(plus, "<Button-1>", lambda e, k=key: self.change_volume(k, +1))
        # ボタンの上でマウスホイール → 音量
        c.bind("<MouseWheel>", lambda e: self.on_wheel(e, 1 if e.delta > 0 else -1))
        c.bind("<Button-4>", lambda e: self.on_wheel(e, +1))
        c.bind("<Button-5>", lambda e: self.on_wheel(e, -1))
        self.update_buttons()
        self.last_event_n = self.world.n_events
        self.follow = None
        self.panel_line = c.create_line(0, 0, 1, 1, fill="#0a6e78", state="hidden", tags="panel")
        self.panel_box = c.create_rectangle(0, 0, 1, 1, fill="#fffef6", outline="#0a6e78",
                                            state="hidden", tags="panel")
        self.panel_text = c.create_text(0, 0, anchor="nw", fill="#073b42", font=("", 9),
                                        state="hidden", tags="panel")
        self.panel_size = (0, 0)
        self.panel_t = 0.0
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
        for k in ("l", "L"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_lineage)
        for k in ("r", "R"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_rel)
        for k in ("w", "W"):
            self.root.bind("<KeyPress-%s>" % k, lambda e: self.toggle_sound("waves"))
        for k in ("f", "F"):
            self.root.bind("<KeyPress-%s>" % k, lambda e: self.toggle_sound("fx"))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(TICK_MS, self.tick)

    # ---- 画像
    def _img(self, rows, colors, scale, k=None):
        img = self.tk.PhotoImage(width=max(len(r) for r in rows), height=len(rows))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch in colors:
                    img.put(tint_hex(colors[ch], k) if k else colors[ch], to=(x, y))
        return img.zoom(scale) if scale > 1 else img

    def make_tinted_images(self, bg):
        """時間帯の色みに合わせて画像を作り直す(色みが変わったときだけ)。"""
        self.bg_tint = bg
        sp = tuple(0.45 + 0.55 * min(1.1, x) for x in bg)
        self.sprite_tint = sp
        pc = {"g": "#2fa86a", "G": "#7be8a2"}
        self.plant_img = [self._img(PLANT_ART[0], {"g": "#4e9a72"}, 3, sp)] + \
                         [self._img(plant_rows(lv), pc, 3, sp) for lv in range(1, 9)]
        self.egg_img = self._img(EGG_ART, {"X": "#fffdf2"}, 2, sp)
        self.star_img = self._img(STAR_ART, {"X": "#ff8a4c"}, 2, bg)
        sc = {"B": "#5d7b8c", "b": "#c9d6dc", "E": "#111111", "F": "#4a6676"}
        self.shark_img = {}
        for f, art in enumerate(SHARK_ART):
            self.shark_img[(1, f)] = self._img(art, sc, 3, sp)
            self.shark_img[(3, f)] = self._img(tuple(r[::-1] for r in art), sc, 3, sp)
        self.fish_img = {}
        for kind, (cols, art) in FISH_ART.items():
            self.fish_img[(kind, 1)] = self._img(art, cols, 2, sp)
            self.fish_img[(kind, 3)] = self._img(tuple(r[::-1] for r in art), cols, 2, sp)
        self.vis_img = {}
        for kind, (cols, frames) in VIS_ART.items():
            for f, art in enumerate(frames):
                if kind == "coconut":                     # 頭を進む向き(右)に
                    art = tuple("".join(r) for r in rotate(art, 1))
                sc2 = 3 if kind in ("dolphin", "manta") else 2
                self.vis_img[(kind, 1, f)] = self._img(art, cols, sc2, sp)
                self.vis_img[(kind, 3, f)] = self._img(tuple(r[::-1] for r in art), cols, sc2, sp)
                if kind == "hermit":                     # 引っ越した後の貝殻の色
                    c2 = dict(cols, X="#ffe08a", x="#d8b050")
                    self.vis_img[(kind + "2", 1, f)] = self._img(art, c2, sc2, sp)
                    self.vis_img[(kind + "2", 3, f)] = self._img(tuple(r[::-1] for r in art), c2, sc2, sp)
        self.reef_img = {}
        for piece, art in REEF_ART.items():
            for ci in range(4):
                if piece.startswith("rock"):
                    cols = dict(zip("Xxo", ROCK_COLORS))
                else:
                    cols = dict(zip("Xxo", CORAL_COLORS[ci]))
                self.reef_img[(piece, ci)] = self._img(art, cols, 3, sp)
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
        sea_dark = lum(tint_rgb(WATER_DEEP, q)) < 0.48
        sand_dark = lum(tint_rgb(hex_rgb(SAND_DRY), q)) < 0.6
        self.canvas.itemconfigure(self.hud, fill="#f2fbff" if sea_dark else "#04505c")
        for it in self.log_items:
            self.canvas.itemconfigure(it, fill="#fff3d6" if sand_dark else "#6b4a12")
        self.canvas.itemconfigure(self.help, fill="#eadcb8" if sand_dark else "#9a7a3c")
        self.canvas.itemconfigure(self.foam, fill=tint_hex("#ffffff", q))

    def update_glitter(self):
        """太陽・月が水面に映ってきらめく。夏の真昼は海全体がキラキラ、朝夕は金色の光の道。"""
        c, w = self.canvas, self.world
        amount = sparkle_amount(w)
        n = int(len(self.glitter) * amount)
        col = {"Daytime": "#fbffff", "Sunrise": "#ffe3a6", "Sunset": "#ffc46e", "Dusk": "#e9c2ff",
               "Dawn twilight": "#d6e4ff", "Night": "#f2f6ff"}.get(w.phase, "#ffffff")
        spread = w.phase == "Daytime"
        cx = w.w * (0.15 + 0.7 * (((w.hour % 24) / 24.0 * 2) % 1.0))
        for i, it in enumerate(self.glitter):
            if i >= n or random.random() < 0.3:
                c.itemconfigure(it, state="hidden")
                continue
            if spread:
                x, y = random.uniform(0, w.w), random.uniform(6, w.land_top * 0.95)
                ln = random.uniform(1.5, 5)
            else:
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
            raw = self.tk.PhotoImage(width=len(px[0]), height=len(px))
            k = self.sprite_tint
            for y, row in enumerate(px):
                for x, col in enumerate(row):
                    if col:
                        raw.put(tint_hex(col, k), to=(x, y))
            img = raw.zoom(scale) if scale > 1 else raw
            cache[key] = img
        return img

    # ---- 背景(海・砂浜・ヒトデ・サンゴ・岩)
    def draw_background(self):
        c, w = self.canvas, self.world
        for it in self.bg_items + self.reef_items:
            c.delete(it)
        self.bg_items, self.reef_items = [], []
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
        for _ in range(14):
            x = rnd.uniform(0, w.w)
            y = rnd.uniform(w.shore(x) + 12, w.h - 2)
            self.bg_items.append(c.create_rectangle(x, y, x + 2, y + 2, fill=tint_hex("#e3c98a", k),
                                                    width=0, tags="bg"))
        for it in getattr(self, "meadow_items", {}).values():
            c.delete(it)
        self.meadow_items = {}
        self.update_meadows()
        for r in w.reefs:
            base = mix(water_color(w, r.y, k), (40, 60, 70), 0.18) if r.kind == "coral" else \
                mix(water_color(w, r.y, k), (60, 70, 80), 0.12)
            rr = r.radius
            self.reef_items.append(c.create_oval(r.x - rr, r.y - rr * 0.7, r.x + rr, r.y + rr * 0.7,
                                                 fill=base, outline="", tags="reef"))
            for dx, dy, piece, ci in sorted(r.parts, key=lambda p: p[1]):
                self.reef_items.append(c.create_image(round(r.x + dx), round(r.y + dy),
                                                      image=self.reef_img[(piece, ci)], tags="reef"))
        self.order_dirty = True
        self.layout_ui()

    def update_meadows(self):
        """藻場の地面(緑がかった砂地)。藻場が動いたり消えたりすると形も変わる。"""
        c, w, k = self.canvas, self.world, self.bg_tint
        w.meadow_changed = False
        seen = set()
        for mid, m in w.meadows.items():
            if m["n"] < 3:
                continue
            seen.add(mid)
            x, y, r = m["x"], m["y"], m["r"]
            box = (x - r - 6, y - r * 0.75 - 5, x + r + 6, y + r * 0.75 + 5)
            it = self.meadow_items.get(mid)
            if it is None:
                base = mix(water_color(w, y, k), tint_rgb((70, 150, 110), k), 0.35)
                self.meadow_items[mid] = c.create_oval(*box, fill=base, outline="", tags="meadow")
                self.order_dirty = True
            else:
                c.coords(it, *box)
        for mid in list(self.meadow_items):
            if mid not in seen:
                c.delete(self.meadow_items.pop(mid))

    def layout_ui(self):
        c, w = self.canvas, self.world
        gx1, gy0 = w.w - 8, 50
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
        if hasattr(self, "sound_ui"):
            self.update_buttons()
        c.coords(self.bann, w.w / 2, w.land_top / 2)
        self.draw_graph()

    # ---- 波(World の波を描く)
    def draw_waves(self, recolor):
        c, w = self.canvas, self.world
        k = self.bg_tint

        def pts(wv, amp_mul=1.0, dy=0.0):
            amp = wv.amp * amp_mul * (1 + 0.3 * math.sin(w.time * 1.5 + wv.ph))
            n = 7 if not wv.big else 15
            out = []
            for i in range(n):
                f = i / (n - 1)
                out += [wv.x + wv.len * f, wv.y + dy - amp * math.sin(math.pi * f * (1 if not wv.big else 3))]
            return out
        for wv, it in zip(w.waves, self.wave_items):
            c.coords(it, *pts(wv))
            if recolor:
                end = w.shore(wv.x + wv.len / 2) - 6
                f = (wv.y - wv.y0) / max(1.0, end - wv.y0)
                fade = math.sin(math.pi * min(1.0, max(0.0, f))) ** 0.7
                c.itemconfigure(it, fill=mix(water_color(w, wv.y, k), tint_rgb((255, 255, 255), k), 0.75 * fade))
        bw = w.big_wave
        if bw:
            c.coords(self.big_items[0], *pts(bw))
            c.coords(self.big_items[1], *pts(bw, 0.7, 7))
            for it in self.big_items:
                c.itemconfigure(it, state="normal", fill=tint_hex("#ffffff", k))
        else:
            for it in self.big_items:
                c.itemconfigure(it, state="hidden")

    # ---- 演出(息継ぎの波紋・クラゲのしぶき・サメのひと噛み)
    def add_fx(self, kind, x, y):
        if len(self.fx_items) > 40:
            return
        c = self.canvas
        if kind == "leaf":                          # ちぎれた葉が舞う
            for _ in range(5):
                it = c.create_rectangle(x, y, x + 3, y + 3, fill=random.choice(("#5ee08a", "#2fa86a", "#8ff0b0")),
                                        width=0, tags="fx")
                a = random.uniform(0, math.tau)
                sp = random.uniform(15, 35)
                self.fx_items.append([it, kind, x, y, 0.0, random.uniform(0.5, 0.8), math.cos(a) * sp, math.sin(a) * sp])
            self.order_dirty = True
            return
        if kind == "peck":                          # 魚がつつくとキラッ
            it = c.create_line(x - 3, y, x + 3, y, fill="#ffffff", tags="fx")
            it2 = c.create_line(x, y - 3, x, y + 3, fill="#ffffff", tags="fx")
            self.fx_items.append([it, kind, x, y, 0.0, 0.35, 0, 0])
            self.fx_items.append([it2, kind, x, y, 0.0, 0.35, 0, 0])
            self.order_dirty = True
            return
        if kind == "pop":
            it = c.create_oval(x, y, x, y, outline="#ffc4ee", width=2, tags="fx")
            self.fx_items.append([it, kind, x, y, 0.0, 0.4])
            self.order_dirty = True
            return
        col = {"ripple": "#ffffff", "splash": "#ffffff", "bite": "#ff3434"}.get(kind, "#ffffff")
        n = 3 if kind == "ripple" else 2 if kind == "bite" else 1
        for k in range(n):
            it = self.canvas.create_oval(x, y, x, y, outline=col, width=2 if kind == "bite" else 1, tags="fx")
            life = 1.8 if kind == "ripple" else 1.3 if kind == "bite" else 0.6
            self.fx_items.append([it, kind, x, y, -0.45 * k, life])
        self.order_dirty = True

    def update_fx(self, dt):
        c = self.canvas
        keep = []
        for f in self.fx_items:
            f[4] += dt
            it, kind, x, y, t, life = f[:6]
            if t > life:
                c.delete(it)
                continue
            if kind == "leaf":
                px, py = x + f[6] * t, y + f[7] * t - 6 * t
                c.coords(it, px, py, px + 3, py + 3)
                keep.append(f)
                continue
            if kind == "peck":
                keep.append(f)
                continue
            if t >= 0:
                r = 2 + t / life * ({"splash": 10, "ripple": 16}.get(kind, 22))
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
        if 0 < dist < 80:
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
        if self.click_job:
            self.root.after_cancel(self.click_job)
        t = self.world.hit(e.x, e.y, pad=6)
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

    def toggle_rel(self, e=None):
        self.show_rel = not self.show_rel
        if not self.show_rel:
            for it in self.rel_lines:
                self.canvas.delete(it)
            self.rel_lines = []

    def on_resize(self, e):
        if (e.width, e.height) == (int(self.world.w), int(self.world.h)):
            return
        self.world.resize(e.width, e.height)
        for tab in self.tables.values():
            for ent in tab.values():
                self.canvas.delete(ent[0])
            tab.clear()
        self.draw_background()

    def update_buttons(self):
        """砂浜の右下: [− Waves (W) 60% +]  [− Sound FX (F) 70% +]"""
        st, c, w = self.world.settings, self.canvas, self.world
        x = w.w - 8
        for key, name in (("fx", "Sound FX (F)"), ("waves", "Waves (W)")):
            minus, label, plus = self.sound_ui[key]
            on, vol = st[key], st[key + "_vol"]
            col = "#0a7f8c" if on and vol > 0 else "#a08a6a"
            c.itemconfigure(plus, text=" + ", fill=col)
            c.itemconfigure(label, text="%s %s" % (name, ("%d%%" % (vol * 10)) if on else "OFF"), fill=col)
            c.itemconfigure(minus, text=" − ", fill=col)
            for it in (plus, label, minus):
                c.coords(it, x, w.h - 16)
                bb = c.bbox(it)
                x -= (bb[2] - bb[0]) if bb else 30
            x -= 14

    def on_wheel(self, e, step):
        near = set(self.canvas.find_overlapping(e.x - 3, e.y - 3, e.x + 3, e.y + 3))
        for key, items in self.sound_ui.items():
            if near & set(items):
                self.change_volume(key, step)

    def toggle_sound(self, key):
        st = self.world.settings
        st[key] = not st[key]
        self.apply_sound(key)
        label = "Wave sound" if key == "waves" else "Sound effects"
        self.banner, self.banner_t = "%s: %s" % (label, "ON" if st[key] else "OFF"), 1.5

    def change_volume(self, key, step):
        st = self.world.settings
        st[key + "_vol"] = max(0, min(10, st[key + "_vol"] + step))
        st[key] = True
        self.apply_sound(key)
        label = "Wave sound" if key == "waves" else "Sound effects"
        self.banner, self.banner_t = "%s volume: %d%%" % (label, st[key + "_vol"] * 10), 1.2

    def apply_sound(self, key):
        st = self.world.settings
        if key == "waves":
            self.sound.set_waves(st["waves"], st["waves_vol"])
        else:
            self.sound.set_fx(st["fx"], st["fx_vol"])
            if st["fx"]:
                self.sound.last.pop("note", None)
                self.sound.play("note")                  # 試し聞き
        self.update_buttons()

    def play_sounds(self):
        """世界で起きたこと(出来事・演出・表情)を効果音にする。"""
        w, snd = self.world, self.sound
        new = w.n_events - self.last_event_n
        self.last_event_n = w.n_events
        for _, kind, text in w.events[-min(new, len(w.events)):] if new > 0 else []:
            name = event_sound(kind, text)
            if name:
                snd.play(name)
        for kind, x, y in w.fx:
            name = {"splash": "splash", "ripple": "breath", "bite": "chomp"}.get(kind)
            if name:
                snd.play(name)
        for name in w.sfx:
            snd.play(name)
        w.sfx.clear()

    def on_close(self):
        try:
            save_world(self.world, self.save_dir)
        except OSError as ex:
            print("Could not save:", ex, file=sys.stderr)
        self.sound.close()
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
        self.sound.tick()
        if self.root.state() == "iconic":
            self.world.fx.clear()
            self.world.sfx.clear()
            self.last_event_n = self.world.n_events
            self.root.after(1000, self.tick)
            return
        self.render(dt)
        self.root.after(TICK_MS, self.tick)

    def turtle_key(self, t):
        w = self.world
        if t.state == "dead":
            return (2, 0, "dead", t.scale)
        if t.state == "flipped":
            return (t.dir, int(t.anim / 0.12) % 2, "belly", t.scale)
        if t.state == "wipeout":                       # くるくる回って、ときどきおなかが見える
            return (t.dir, int(t.anim / 0.12) % 2, "belly" if int(t.anim / 0.24) % 2 else "normal", t.scale)
        if t.state == "breathe":
            return (t.dir, 0, "breathe", t.scale)
        if t.state == "food" and t.eat_cd > 0:
            return (t.dir, int(t.anim / 0.14) % 2, "eat", t.scale)
        if t.state == "cleaning":                       # 気持ちよさそうに、ひれをゆっくり
            return (t.dir, int(t.anim / 0.9) % 2, "normal", t.scale)
        if t.state in ("sleep", "lay", "petted"):
            return (t.dir, 0, "normal", t.scale)
        if t.state == "surf":
            return (t.dir, 1, "normal", t.scale)
        water = w.in_water(t.x, t.y)
        period = 0.2 if t.state in ("flee", "food", "flee_shark", "play") else (0.6 if not water else 0.45)
        return (t.dir, int(t.anim / period) % 2, "normal", t.scale)

    def render(self, dt):
        c, w = self.canvas, self.world
        if w.meadow_changed:
            self.update_meadows()
        self._sync("plant", w.plants, lambda p: self.plant_img[plant_level(p.b)], move=False)
        ptab = self.tables["plant"]
        for p in w.plants:                              # かじられた株がふるえる
            age = w.time - p.bitten
            if age < 0.7:
                ent = ptab.get(id(p))
                if ent:
                    off = math.sin(age * 45) * 2.5 * (1 - age / 0.7) if age < 0.65 else 0
                    c.coords(ent[0], round(p.x + off), round(p.y))
        self._sync("egg", w.eggs, lambda e: self.egg_img, move=False)
        self._sync("jelly", w.jellies, lambda o: self.jelly_img)
        self._sync("fish", w.fish, lambda f: self.fish_img[(f.school.kind, 1 if f.vx >= 0 else 3)])
        ftab = self.tables["fish"]
        for f in w.fish:                                # クリーニング中の魚はカメの上に
            ent = ftab.get(id(f))
            want = "fishtop" if f.school.cleaning is not None else "fish"
            if ent and (len(ent) < 3 or ent[2] != want):
                c.itemconfigure(ent[0], tags=(want,))
                ent[2:] = [want]
                self.order_dirty = True
        self._sync("visitor", w.visitors,
                   lambda v: self.vis_img[(v.kind + ("2" if getattr(v, "shell", 0) else ""), v.dir,
                                           int(v.anim / (0.25 if v.kind == "dolphin" else 0.5)) % 2)])

        seen = set()
        for t in w.turtles:
            seen.add(t.id)
            ent = self.items.get(t.id)
            if ent is None:
                ent = [c.create_image(t.x, t.y, tags="turtle"), None, None, {}, None, None]
                self.items[t.id] = ent
                self.order_dirty = True
            key = self.turtle_key(t)
            if key != ent[4]:
                c.itemconfigure(ent[0], image=self.turtle_img(t, ent[3], key))
                ent[4] = key
            c.coords(ent[0], round(t.x), round(t.y))
            ey = t.y - t.radius - 9
            if t.emote != ent[5]:                       # 表情が変わったら、ときどき効果音
                ent[5] = t.emote
                name = EMOTE_SOUND.get(t.emote)
                if name and (t.id == self.follow or random.random() < 0.35):
                    self.sound.play(name)
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

        self.play_sounds()
        for kind, x, y in w.fx:
            self.add_fx(kind, x, y)
        w.fx.clear()
        self.update_fx(dt)
        self.wave_t += dt
        recolor = self.wave_t > 0.3
        if recolor:
            self.wave_t = 0.0
        self.draw_waves(recolor)
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
        if self.show_rel:
            self.draw_relations(dt)

        if self.order_dirty:
            for tag in ("bg", "glit", "meadow", "plant", "reef", "wave", "bg2", "egg", "fish", "jelly",
                        "rel", "turtle", "fishtop", "visitor", "shark", "fx", "ui", "panel", "tip"):
                c.tag_raise(tag)
            self.order_dirty = False

        self.hud_t -= dt
        if self.hud_t <= 0:
            self.hud_t = 1.0
            alive = w.alive()
            nf = sum(t.sex == "F" for t in alive)
            herb = sum(t.herbivore for t in alive)
            vis = [{"dolphin": "Dolphin", "manta": "Manta", "hermit": "Hermit crab",
                    "coconut": "Coconut crab"}[v.kind] for v in w.visitors]
            if w.shark:
                vis.append("SHARK!")
            c.itemconfigure(self.hud, text=(
                "%s %s   Turtles %d (F%d M%d, herb %d / omni %d)   Eggs %d   Gen %d\n"
                "Seaweed %d   Jellyfish %d   Born %d   Died %d   Merged %d   Split %d\n%s"
                % (time.strftime("%H:%M", time.localtime(w.now_ts)), w.phase, len(alive), nf,
                   len(alive) - nf, herb, len(alive) - herb, len(w.eggs), w.max_gen,
                   len(w.plants), len(w.jellies), w.births, w.deaths, w.merges, w.splits,
                   ("Visitors: " + ", ".join(vis)) if vis else "")))
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

    def draw_relations(self, dt):
        """パートナー(ピンク)と友達(黄色)を線で結ぶ。"""
        c, w = self.canvas, self.world
        pairs = []
        done = set()
        for t in w.alive():
            for other, col in ((w.by_id.get(t.partner), "#ff7aa8"), ):
                if other and (other.id, t.id) not in done:
                    pairs.append((t, other, col, 2))
                    done.add((t.id, other.id))
            for f in w.friends(t)[:3]:
                if (f.id, t.id) not in done and (t.id, f.id) not in done:
                    pairs.append((t, f, "#fff08a", 1))
                    done.add((t.id, f.id))
        while len(self.rel_lines) < len(pairs):
            self.rel_lines.append(c.create_line(0, 0, 1, 1, dash=(3, 3), tags="rel"))
            self.order_dirty = True
        for i, it in enumerate(self.rel_lines):
            if i < len(pairs):
                a, b, col, wd = pairs[i]
                c.coords(it, a.x, a.y, b.x, b.y)
                c.itemconfigure(it, fill=col, width=wd, state="normal")
            else:
                c.itemconfigure(it, state="hidden")

    def update_panel(self, dt):
        if self.follow is None:
            return
        c, w = self.canvas, self.world
        t = next((x for x in w.turtles if x.id == self.follow), None)
        if t is None:
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
        try:
            import tkinter.messagebox as mb
            mb.showerror("Sea Turtle Colony", msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
