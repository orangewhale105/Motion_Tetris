# -*- coding: utf-8 -*-
"""
Whale Fall(ホエールフォール)— 深海の人工生命ペット(Sea Turtle Colony の深海版)

・標準ライブラリだけで動く(tkinter)。pip install 不要。画面の表示は英語。
・海を横から見た断面(矢状面)。上から 海面(空の色はパソコンの時計に合わせる)→ 有光層 → 中深層(薄明帯)
  → 漸深層(真っ暗)→ 深海底。海底にはクジラの死骸(鯨骨)が横たわり、深海の生き物の暮らしを支えている。
・主役: ジュウモンジダコ(ダンボ・オクトパス)の群体。ドット絵で、パステル(ピンク・ピーチ・ライラック・
  クリーム・アクア・ミント)が基本、まれに深い赤や紫の個体が生まれる。模様は 7 種類。
・遺伝的アルゴリズム: 色・模様・ひれ(耳)の大きさ・発光・速さ・寿命・大きさ・食性(甲殻類を食べる/ゴカイを食べる)・
  性格(活発さ・食欲・ライトの好き嫌い・群れたがり・無頓着さ・気まま・気の短さ)・産卵数。交尾で交叉+突然変異。
・時間の進み方: 1日でおよそ 1〜3 世代(大人まで約5時間、寿命 12〜24時間)。
・鯨骨生物群集の遷移(実時間):
    落下 → 移動性腐肉食者期(約18時間: 肉が多く、ヨコエビが群がる。ヌタウナギ・オンデンザメが来る)
    → 富栄養期(〜42時間: 骨にホネクイハナムシが咲く)→ 化学合成期(〜90時間: バクテリアマット・二枚貝)
    → 鯨骨礁期(骨だけ。餌が少ない)→ 1〜2日後に新しいクジラが落ちてくる。
  餌の量が変わるので、タコの数も増えたり減ったりする(右上のグラフ)。マリンスノーが降り続ける。
・1日の変化(パソコンの時計): 夜になるとハダカイワシの群れが上へ移動し(日周鉛直移動)、マリンスノーが増える。
  タコは昼から夕方によく食べ、夜は海底や鯨骨の上で休む。メスは鯨骨や岩に卵を産みつけ、ふ化まで守る。
・関係: 友達・パートナー・悲しみ・さみしさなど(R キーで関係の線)。合体・分裂もする。
・訪問者: コウモリダコ(友好的。タコが集まって遊ぶ)、マッコウクジラ、ダイオウグソクムシ、ヌタウナギ、
  オンデンザメ(タコを狙う)、チョウチンアンコウ(光る疑似餌で好奇心の強いタコを誘う)。
・マウス: カーソルは潜水艇のライト(近くが明るく見える)。
    タコをクリック → ステータスがついて回る / ダブルクリック → びっくりして「傘」の姿勢になり、光る
    タコの上でカーソルを動かす → なでる / 水をクリック → マリンスノーのかたまり(ヨコエビが湧く)
    Shift+クリック → 魚の死骸を落とす / 右クリック → 最前面 / L → 系統 / R → 関係の線
・閉じると Google ドライブ(パソコン版の同期フォルダ)の WhaleFall/ に保存。次回起動時に経過時間ぶん進める。
  保存先は環境変数 WHALEFALL_SAVE_DIR でも指定できる。
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

VERSION = "1.1.0"

# ---------------------------------------------------------------- 定数
TICK_MS = 100
MAX_DUMBOS = 40
HOUR = 3600.0
JUVENILE_AGE = 1 * HOUR
ADULT_AGE = 5 * HOUR
MATE_COOLDOWN = 2 * HOUR
EGG_TIME = 1.5 * HOUR
LAY_TIME = 4.0
EGG_COST = 0.09
HATCH_ENERGY = 0.45
MAX_SCALE = 5
MERGE_KIN = 0.12
CORPSE_TIME = 12.0
SLEEP_METAB = 0.12
PET_STROKE = 60.0
FRIEND_AFF = 1.0

CRUST_MAX = 50
CRUST_BASE = 0.02             # マリンスノーから湧くヨコエビ(1/秒)
CRUST_FLESH = 0.06            # クジラの肉があると増える
CRUST_ENERGY = 0.16
WORM_RATE = 0.00028           # 骨のゴカイの回復率(上限まで約1時間)
WORM_ENERGY = 0.22

STAGES = (  # (名前, 終わる年齢[時間], ゴカイの上限)
    ("Mobile scavenger stage", 18, 6),
    ("Enrichment opportunist stage", 42, 30),
    ("Sulphophilic stage", 90, 16),
    ("Reef stage", 1e9, 4),
)
STAGE_INFO = {
    "Mobile scavenger stage": "Lots of flesh. Amphipods swarm; hagfish and sleeper sharks visit",
    "Enrichment opportunist stage": "Bone-eating worms bloom on the bones",
    "Sulphophilic stage": "Bacterial mats and mussels live off sulphide from the bones",
    "Reef stage": "Only bare bones remain. Food is scarce",
}
NEXT_WHALE = (12 * HOUR, 48 * HOUR)    # 鯨骨礁期になってから次のクジラが落ちてくるまで
FALL_TIME = 60.0

VISITORS = {
    "vampire": {"gap": (3 * HOUR, 6 * HOUR), "stay": 150, "zone": "mid", "friendly": True},
    "sperm": {"gap": (6 * HOUR, 12 * HOUR), "stay": 80, "zone": "upper", "friendly": False},
    "isopod": {"gap": (2 * HOUR, 4 * HOUR), "stay": 300, "zone": "floor", "friendly": False},
    "hagfish": {"gap": (1 * HOUR, 3 * HOUR), "stay": 240, "zone": "carcass", "friendly": False},
    "sleeper": {"gap": (3 * HOUR, 6 * HOUR), "stay": 120, "zone": "floor", "friendly": False},
    "angler": {"gap": (3 * HOUR, 6 * HOUR), "stay": 180, "zone": "mid", "friendly": False},
}
VIS_NAMES = {"vampire": "Vampire squid", "sperm": "Sperm whale", "isopod": "Giant isopod",
             "hagfish": "Hagfish", "sleeper": "Sleeper shark", "angler": "Anglerfish"}

OFFLINE_STEP = 60.0
OFFLINE_MAX = 7 * 24 * 3600
HISTORY_DT = 20.0
HISTORY_LEN = 60
AUTOSAVE_SEC = 300
SAVE_NAME = "colony.json"

FLOAT_GENES = ("hue", "hue2", "speed", "life", "size", "diet", "ears", "glow",
               "activity", "appetite", "cursor", "flock", "care", "whim",
               "temper", "fertility", "style", "dark")
PATTERN_BITS = 24

PASTEL = (0.95, 0.06, 0.78, 0.12, 0.50, 0.38)
PASTEL_NAMES = ("pink", "peach", "lilac", "cream", "aqua", "mint")
STYLES = ("plain", "freckles", "bands", "glow spots", "two-tone", "speckled", "heart")


# ---------------------------------------------------------------- 遺伝子
def random_genome(rng=random):
    g = {k: rng.random() for k in FLOAT_GENES}
    g["dark"] = rng.random() ** 3
    g["pattern"] = [rng.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def fill_genome(g):
    g = dict(g)
    for k in FLOAT_GENES:
        if k not in g:
            g[k] = random.random() ** 3 if k == "dark" else random.random()
    if len(g.get("pattern", [])) != PATTERN_BITS:
        g["pattern"] = [random.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def crossover(a, b, rng=random):
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
            out.append("Light lover")
        elif g["cursor"] < 0.3:
            out.append("Light shy")
        if g["flock"] > 0.7:
            out.append("Social")
        elif g["flock"] < 0.3:
            out.append("Loner")
        else:
            out.append("Middle-of-the-road")
    if g["whim"] > 0.7:
        out.append("Curious")
    if g["temper"] > 0.75:
        out.append("Short-tempered")
    elif g["temper"] < 0.2:
        out.append("Easygoing")
    return out


def pastel_index(h):
    return min(len(PASTEL) - 1, int((h % 1.0) * len(PASTEL)))


def pastel_hue(h):
    i = pastel_index(h)
    frac = (h % 1.0) * len(PASTEL) - i
    return (PASTEL[i] + (frac - 0.5) * 0.05) % 1.0


def is_dark(g):
    return g["dark"] > 0.9


def style_of(g):
    s = g["style"]
    return 6 if s > 0.96 else min(5, int(s / 0.96 * 6))


def color_name(g):
    n = PASTEL_NAMES[pastel_index(g["hue"])]
    return ("deep " + {"pink": "red", "peach": "orange", "cream": "amber", "aqua": "teal",
                       "mint": "green", "lilac": "purple"}[n]) if is_dark(g) else ("pastel " + n)


def lineage_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = string.ascii_uppercase[r] + s
    return s


def fmt_dur(sec):
    sec = int(sec)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm" % (sec // 60)
    if sec < 86400:
        return "%dh %dm" % (sec // 3600, sec % 3600 // 60)
    return "%dd %dh" % (sec // 86400, sec % 86400 // 3600)


# ---------------------------------------------------------------- 海面の昼と夜(パソコンの時計)
TINTS = {"night": (0.20, 0.24, 0.42), "twilight": (0.50, 0.56, 0.85), "sunrise": (1.0, 0.80, 0.70),
         "day": (1.0, 1.0, 1.0), "sunset": (1.08, 0.70, 0.48), "dusk": (0.55, 0.45, 0.72)}
PHASE_MSG = {
    "Dawn twilight": "Dawn at the surface - lanternfish start sinking back down",
    "Sunrise": "Sunrise at the surface - the lanternfish return to the depths",
    "Daytime": "Daytime - the dumbos are busy hunting near the seafloor",
    "Sunset": "Sunset at the surface - the twilight zone grows dark",
    "Dusk": "Dusk - lanternfish begin their nightly journey upward",
    "Night": "Night - lanternfish feed near the surface; marine snow thickens",
}


def sun_times(ts):
    """日の出・日の入り(時)。日本(東京付近)の季節変化を簡単な式で近似。"""
    doy = time.localtime(ts).tm_yday
    c = math.cos(2 * math.pi * (doy - 172) / 365.0)
    return 5.6 - 1.2 * c, 17.75 + 1.25 * c


def daylight(ts):
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


# ---------------------------------------------------------------- 生き物
class Dumbo:
    """ジュウモンジダコ(ダンボ・オクトパス)。"""
    _ids = 0

    def __init__(self, genome, x, y, generation=1, age=0.0, tid=None,
                 sex=None, lineage="A", parents=None, extra=0):
        if tid is None:
            Dumbo._ids += 1
            tid = Dumbo._ids
        else:
            Dumbo._ids = max(Dumbo._ids, tid)
        self.id = tid
        self.g = genome
        self.sex = sex or random.choice("FM")
        self.lineage = lineage
        self.parents = parents or ""
        self.extra = extra
        self.x, self.y = x, y
        a = random.uniform(0, math.tau)
        self.vx, self.vy = math.cos(a) * 6, math.sin(a) * 3
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
        self.brood = None        # 守っている卵
        self.bed = None
        self.vis = None
        self.orbit = random.uniform(0, math.tau)
        self.dead_t = 0.0
        self.cause = ""
        self.anim = random.random()
        self.nb = None
        self.pet_acc = 0.0
        self.pets = 0
        self.aff = {}
        self.partner = None
        self.lonely_t = 0.0
        self.glow_t = 0.0

    @property
    def adult(self):
        return self.age >= ADULT_AGE

    @property
    def base_scale(self):
        return 2 if self.g["size"] < 0.5 else 3

    @property
    def scale(self):
        if self.age < JUVENILE_AGE:
            return 1
        if not self.adult:
            return max(1, self.base_scale - 1)
        return min(MAX_SCALE, self.base_scale + self.extra)

    @property
    def picker(self):
        """True: 甲殻類(ヨコエビ)を食べるのが得意。False: 骨のゴカイを食べるのが得意。"""
        return self.g["diet"] < 0.5

    @property
    def max_speed(self):
        s = (8 + 20 * self.g["speed"]) * (0.8 + 0.4 * self.g["activity"]) * (0.8 + 0.4 * self.g["ears"])
        return s * (1.0 - 0.07 * (self.scale - 2)) * (0.8 if not self.adult else 1.0)

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
        return night * (1.0 - 0.7 * self.g["activity"])

    @property
    def awake_len(self):
        return 900 + 2700 * self.g["activity"]

    @property
    def sleep_len(self):
        return 120 + 480 * (1 - self.g["activity"])

    @property
    def radius(self):
        return 5.5 * self.scale

    @property
    def alive(self):
        return self.state != "dead"

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


class Eggs:
    """岩や鯨骨に産みつけられた卵のかたまり。母親が守る。"""

    def __init__(self, x, y, genomes, generation, lineage, parents, mother=None, t=EGG_TIME):
        self.x, self.y, self.genomes = x, y, genomes
        self.generation, self.lineage, self.parents = generation, lineage, parents
        self.mother, self.t = mother, t

    def to_dict(self):
        return {"x": self.x, "y": self.y, "gs": self.genomes, "gen": self.generation,
                "lin": self.lineage, "par": self.parents, "mom": self.mother, "t": self.t}

    @classmethod
    def from_dict(cls, d):
        return cls(d["x"], d["y"], [fill_genome(g) for g in d["gs"]], d.get("gen", 1), d.get("lin", "A"),
                   d.get("par", ""), d.get("mom"), d.get("t", EGG_TIME))


class Crust:
    """ヨコエビ(小さな甲殻類)。マリンスノーやクジラの肉を食べて増え、タコの餌になる。"""
    kind = "crust"

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-6, 6), random.uniform(-3, 3)
        self.t = random.uniform(0, 2)
        self.age = 0.0
        self.gone = False


class Whale:
    """海底に横たわるクジラ(鯨骨)。年齢で遷移の段階が進む。"""

    def __init__(self, x, age=0.0, falling=True, flesh=1.0):
        self.x = x
        self.age = age
        self.falling = falling
        self.fall_t = 0.0
        self.flesh = flesh
        self.worms = 0.0
        self.next_t = None
        self.y = 0.0

    @property
    def stage_index(self):
        h = self.age / HOUR
        for i, (_, end, _) in enumerate(STAGES):
            if h < end:
                return i
        return len(STAGES) - 1

    @property
    def stage(self):
        return STAGES[self.stage_index][0]

    @property
    def worm_cap(self):
        return STAGES[self.stage_index][2]

    def to_dict(self):
        return {"x": self.x, "age": self.age, "falling": self.falling, "flesh": self.flesh,
                "worms": self.worms, "next": self.next_t}


class Visitor:
    def __init__(self, kind, x, y, vx):
        self.kind, self.x, self.y, self.vx, self.vy = kind, x, y, vx, 0.0
        self.y0 = y
        self.t = 0.0
        self.anim = random.random()
        self.leaving = False
        self.gone = False
        self.players = set()
        self.announced = False
        self.target = None
        self.ate = False
        self.offset = random.uniform(-20, 20)

    @property
    def dir(self):
        return 1 if self.vx >= 0 else 3


class Lantern:
    """ハダカイワシ(日周鉛直移動: 夜は上へ、昼は下へ)。"""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random.choice((-1, 1)) * random.uniform(8, 16)
        self.dy = random.uniform(-25, 25)


class FoodFall:
    """Shift+クリックで落とす魚の死骸。海底に着くとヨコエビが集まる。"""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.flesh = 1.0
        self.landed = False


# ---------------------------------------------------------------- 世界
class World:
    def __init__(self, w=700, h=480):
        self.w, self.h = w, h
        self.dumbos = []
        self.eggs = []
        self.crusts = []
        self.lanterns = [Lantern(random.uniform(0, w), h * random.uniform(0.3, 0.5)) for _ in range(12)]
        self.whale = None
        self.foodfalls = []
        self.visitors = []
        self.vis_t = {k: random.uniform(*v["gap"]) * random.uniform(0.1, 0.6) for k, v in VISITORS.items()}
        self.rocks = []
        self.clock = time.time
        self.phase, self.night, self.tint, self.hour = daylight(self.clock())
        self.now_ts = self.clock()
        self.phase_msg = None
        self.fx = []
        self.time = 0.0
        self.births = self.deaths = self.laid = self.merges = self.splits = self.whales = 0
        self.max_gen = 1
        self.n_lineages = 0
        self.gene_pool = []
        self.cursor = None
        self.cursor_speed = 0.0
        self.events = []
        self.history = []
        self.hist_t = 0.0
        self.aff_t = 0.0
        self._pop = 0
        self.by_id = {}

    # ---- 地形
    @property
    def surface(self):
        return 16.0

    def floor(self, x):
        return self.h * 0.87 + 4 * math.sin(x / 61.0) + 3 * math.sin(x / 23.0 + 2)

    def depth_m(self, y):
        """画面の y を深さ(m)に(海面 0m、海底およそ 4000m)。"""
        f = max(0.0, (y - self.surface) / (self.floor(self.w / 2) - self.surface))
        return int(4000 * f ** 1.6)

    def deep_point(self, top=0.5):
        x = random.uniform(20, self.w - 20)
        return x, random.uniform(self.h * top, self.floor(x) - 14)

    def floor_point(self, x=None):
        if x is None:
            x = random.uniform(20, self.w - 20)
        return x, self.floor(x) - 4

    # ---- 初期化
    def new_lineage(self):
        name = lineage_name(self.n_lineages)
        self.n_lineages += 1
        return name

    def seed(self, n=8):
        self.seed_rocks()
        for i in range(n):
            x, y = self.deep_point(0.55)
            t = Dumbo(random_genome(), x, y, sex="FM"[i % 2], lineage=self.new_lineage())
            t.age = ADULT_AGE + random.uniform(0.0, 0.1) * t.lifespan
            t.mate_cd = random.uniform(0, MATE_COOLDOWN * 0.5)
            self.dumbos.append(t)
        self.new_whale(first=True)

    def seed_rocks(self):
        rnd = random.Random(random.randrange(10 ** 6))
        self.rocks = []
        for fx in (0.12, 0.32, 0.78, 0.92):
            x = self.w * fx + rnd.uniform(-20, 20)
            self.rocks.append([x, rnd.randrange(3)])

    def new_whale(self, first=False):
        x = random.uniform(self.w * 0.35, self.w * 0.65)
        self.whale = Whale(x)
        self.whale.y = self.surface
        self.whales += 1
        self.event("whale", "A whale is falling from the surface!" if not first else
                   "A whale is sinking toward the seafloor... a feast is coming")

    def alive(self):
        return [t for t in self.dumbos if t.alive]

    def population(self):
        return sum(t.alive for t in self.dumbos) + sum(len(e.genomes) for e in self.eggs)

    def event(self, kind, text):
        ts = getattr(self, "now_ts", None) or time.time()
        self.events.append((time.strftime("%H:%M", time.localtime(ts)), kind, text))
        self.events = self.events[-8:]

    @staticmethod
    def tag(t):
        return "#%d (%s)" % (t.id, t.lineage)

    def update_daylight(self, ts, log=True):
        self.now_ts = ts
        phase, self.night, self.tint, self.hour = daylight(ts)
        if phase != self.phase:
            self.phase = phase
            if log:
                self.phase_msg = PHASE_MSG[phase]
                self.event("time", PHASE_MSG[phase])

    def appetite_shift(self):
        """タコは昼から夕方によく食べ、夜は休む。"""
        h = self.hour
        if 9 <= h < 19:
            return 0.12
        if self.night > 0.6:
            return -0.25
        return 0.0

    # ---- 1フレーム
    def step(self, dt):
        dt = min(dt, 0.5)
        self.time += dt
        self.update_daylight(self.clock())
        self._whale_step(dt)
        self._crust_step(dt)
        self._lantern_step(dt)
        self._foodfall_step(dt)
        self._visitors_step(dt)
        self._eggs_step(dt)
        alive = self.alive()
        self._pop = len(alive) + sum(len(e.genomes) for e in self.eggs)
        self.by_id = {t.id: t for t in alive}
        self._neighbors(alive, dt)
        for t in list(self.dumbos):
            self._update(t, dt)
        self._pairs(alive, dt)
        self._decompose()
        if not self.alive() and not self.eggs:
            self._refound()
        self._decay_aff(dt)
        self._record(dt)

    # ---- 鯨骨の遷移
    def _whale_step(self, dt, offline=False):
        wh = self.whale
        if wh is None:
            return
        if wh.falling:
            wh.fall_t += dt
            fy = self.floor(wh.x) - WHALE_OFF
            wh.y = self.surface + (fy - self.surface) * min(1.0, wh.fall_t / FALL_TIME)
            if int(wh.fall_t / 4) != int((wh.fall_t - dt) / 4):
                self.fx.append(("halo", wh.x, wh.y))          # やわらかな光に包まれて沈む
            if wh.fall_t >= FALL_TIME:
                wh.falling, wh.y = False, fy
                self.fx.append(("dust", wh.x, fy + WHALE_OFF - 4))
                self.event("whale", "The whale reached the seafloor! A whale fall community begins")
            return
        wh.y = self.floor(wh.x) - WHALE_OFF
        prev = wh.stage
        wh.age += dt
        wh.flesh = max(0.0, wh.flesh - dt / (18 * HOUR))
        wh.worms = min(wh.worm_cap, wh.worms + WORM_RATE * wh.worm_cap * dt * (1 - wh.worms / max(1, wh.worm_cap)))
        if wh.stage != prev:
            self.event("whale", "The whale fall entered the %s" % wh.stage.lower())
        if wh.stage == "Reef stage":
            if wh.next_t is None:
                wh.next_t = random.uniform(*NEXT_WHALE)
            wh.next_t -= dt
            if wh.next_t <= 0:
                self.event("whale", "The old bones are buried in the sediment...")
                self.new_whale()

    def food_rate(self):
        wh = self.whale
        snow = CRUST_BASE * (1.4 if self.night > 0.5 else 1.0)       # 夜はマリンスノーが増える
        meat = CRUST_FLESH * (wh.flesh if wh and not wh.falling else 0.0)
        meat += sum(0.03 * f.flesh for f in self.foodfalls if f.landed)
        return snow + meat

    def _crust_step(self, dt):
        expect = self.food_rate() * dt
        n = int(expect) + (random.random() < expect - int(expect))
        wh = self.whale
        for _ in range(n):
            if len(self.crusts) >= CRUST_MAX:
                break
            src = None
            if wh and not wh.falling and wh.flesh > 0 and random.random() < 0.7:
                src = (wh.x + random.uniform(-85, 85), wh.y - random.uniform(-10, 25))
            landed = [f for f in self.foodfalls if f.landed]
            if landed and random.random() < 0.5:
                f = random.choice(landed)
                src = (f.x + random.uniform(-15, 15), f.y - random.uniform(0, 10))
            if src is None:
                src = self.deep_point(0.6)
            self.crusts.append(Crust(*src))
        keep = []
        for c in self.crusts:
            c.age += dt
            c.t -= dt
            if c.t <= 0:
                c.t = random.uniform(0.5, 2)
                c.vx, c.vy = random.uniform(-8, 8), random.uniform(-4, 4)
            c.x += c.vx * dt
            c.y += c.vy * dt
            c.x = min(max(4, c.x), self.w - 4)
            c.y = min(max(self.h * 0.45, c.y), self.floor(c.x) - 3)
            if not c.gone and c.age < 3 * HOUR:
                keep.append(c)
        self.crusts = keep

    def add_crusts(self, x, y, n=4):
        for _ in range(n):
            if len(self.crusts) < CRUST_MAX + 10:
                self.crusts.append(Crust(x + random.uniform(-10, 10), max(self.h * 0.45, y + random.uniform(-6, 6))))
        self.fx.append(("snow", x, y))

    def drop_foodfall(self, x, y):
        if len(self.foodfalls) < 3:
            self.foodfalls.append(FoodFall(x, max(self.surface + 4, y)))

    def _foodfall_step(self, dt):
        keep = []
        for f in self.foodfalls:
            if not f.landed:
                f.y += 25 * dt
                fy = self.floor(f.x) - 4
                if f.y >= fy:
                    f.y, f.landed = fy, True
                    self.fx.append(("dust", f.x, fy + 3))
            else:
                f.flesh -= dt / 1200.0
            if f.flesh > 0:
                keep.append(f)
        self.foodfalls = keep

    def _lantern_step(self, dt):
        """ハダカイワシ: 夜は 150〜400m 付近まで上がり、昼は 500〜1000m に下がる。"""
        top = self.h * (0.18 + 0.22 * (1 - self.night))
        for f in self.lanterns:
            f.x += f.vx * dt
            if f.x < -10 or f.x > self.w + 10:
                f.vx = -f.vx
            ty = top + f.dy
            f.y += (ty - f.y) * min(1.0, dt * 0.05)

    def _record(self, dt):
        self.hist_t += dt
        if self.hist_t >= HISTORY_DT:
            self.hist_t = 0.0
            wh = self.whale
            self.history.append((sum(t.alive for t in self.dumbos), len(self.crusts),
                                 round(wh.worms, 1) if wh else 0))
            self.history = self.history[-HISTORY_LEN:]

    # ---- 訪問者
    def _visitors_step(self, dt):
        wh = self.whale
        for kind, cfg in VISITORS.items():
            self.vis_t[kind] -= dt * (1.5 if kind == "angler" and self.night > 0.5 else 1.0)
            if self.vis_t[kind] > 0 or any(v.kind == kind for v in self.visitors):
                continue
            if cfg["zone"] == "carcass" and not (wh and not wh.falling and wh.stage_index <= 1):
                self.vis_t[kind] = 600.0
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
        x0 = -50 if left else self.w + 50
        zone = VISITORS[kind]["zone"]
        if zone == "upper":
            y, sp = self.h * random.uniform(0.2, 0.35), 30
        elif zone == "mid":
            y, sp = self.h * random.uniform(0.5, 0.7), 10
        elif zone == "carcass":
            wh = self.whale
            y, sp = (wh.y if wh else self.h * 0.8) - 4, 14
        else:
            y, sp = self.floor(self.w / 2) - 8, 8 if kind == "isopod" else 14
        v = Visitor(kind, x0, y, sp if left else -sp)
        self.visitors.append(v)
        msg = {"vampire": "A vampire squid drifted in, glowing softly",
               "sperm": "A sperm whale dove down to hunt squid",
               "isopod": "A giant isopod is crawling along the seafloor",
               "hagfish": "Hagfish came to feast on the whale",
               "sleeper": "A sleeper shark is prowling near the seafloor! Dumbos, beware",
               "angler": "An anglerfish dangles its glowing lure..."}[kind]
        self.event("visitor", msg)

    def _move_visitor(self, v, dt):
        v.t += dt
        v.anim += dt
        cfg = VISITORS[v.kind]
        if v.t > cfg["stay"]:
            v.leaving = True
        k = v.kind
        if k == "sperm":
            v.y = v.y0 + 30 * math.sin(v.t * 0.6)
            v.x += v.vx * dt
        elif k == "vampire":
            v.y = v.y0 + 25 * math.sin(v.t * 0.5)
            if not v.leaving and (v.x < 60 and v.vx < 0 or v.x > self.w - 60 and v.vx > 0):
                v.vx = -v.vx
            v.x += v.vx * dt
            if not v.leaving:
                self._recruit_players(v)
        elif k == "angler":
            if not v.leaving and (v.x < 60 and v.vx < 0 or v.x > self.w - 60 and v.vx > 0):
                v.vx = -v.vx
            v.x += v.vx * dt * (0.3 if not v.leaving else 1.5)
            v.y = v.y0 + 8 * math.sin(v.t * 0.3)
            self._angler_lure(v)
        elif k == "hagfish":
            wh = self.whale
            if wh and not v.leaving:
                tx = wh.x + v.offset
                v.vx = max(-14, min(14, (tx - v.x) * 0.5)) or 0.1
                v.y = wh.y - 4 + 3 * math.sin(v.t * 3)
                if wh.flesh > 0:
                    wh.flesh = max(0.0, wh.flesh - dt / (60 * HOUR))
            v.x += v.vx * dt
            if v.leaving:
                v.vx = 20 if v.x > self.w / 2 else -20
        elif k == "isopod":
            wh = self.whale
            if wh and not v.leaving and abs(wh.x - v.x) < 50:
                v.vx *= 0.98
            v.x += v.vx * dt
            v.y = self.floor(v.x) - 7
            for t in self.dumbos:
                if t.alive and math.hypot(t.x - v.x, t.y - v.y) < 50 and random.random() < dt / 8:
                    t.say("question", 1.2, force=False)
        elif k == "sleeper":
            self._sleeper(v, dt)
        if v.leaving and (v.x < -80 or v.x > self.w + 80):
            v.gone = True
        if v.leaving and k == "vampire" and v.t > cfg["stay"] + 60:
            v.gone = True
        if v.t > 6 and v.players and not v.announced:
            v.announced = True
            self.event("play", "%d dumbo%s gathered around the vampire squid to play!" % (
                len(v.players), "s" if len(v.players) > 1 else ""))

    def _recruit_players(self, v):
        for t in self.dumbos:
            if not t.alive or t.state != "swim" or t.id in v.players or t.energy < 0.35:
                continue
            g = t.g
            if g["care"] < 0.2 or max(g["flock"], g["cursor"], g["whim"]) < 0.45:
                continue
            if math.hypot(t.x - v.x, t.y - v.y) < 180:
                t.state, t.vis, t.state_t = "play", v, random.uniform(15, 35)
                v.players.add(t.id)
                t.say("star", 1.5)

    def _angler_lure(self, v):
        """光る疑似餌。好奇心の強いタコが近づき、ときどき食べられてしまう。"""
        lx, ly = v.x + (14 if v.vx >= 0 else -14), v.y - 14
        for t in self.dumbos:
            if not t.alive or t.state in ("brood", "lay", "dead", "sleep"):
                continue
            d = math.hypot(t.x - lx, t.y - ly)
            if d > 140:
                continue
            curious = t.g["whim"] > 0.6 or (t.g["cursor"] > 0.65 and t.g["care"] > 0.3)
            if curious and t.state in ("swim", "food") and not v.leaving:
                t.state, t.vis, t.state_t = "lured", v, 20.0
                t.say("question", 1.5)
            elif not curious and t.g["care"] > 0.3 and t.state not in ("lured", "flee"):
                t.state, t.state_t, t.vis = "flee", 3.0, v
                t.say("bang", 1.0, force=False)
            if t.state == "lured" and d < 12 and not v.ate:
                if random.random() < 0.35:
                    v.ate = True
                    self._kill(t, "an anglerfish")
                    t.dead_t = CORPSE_TIME - 1
                    self.fx.append(("bite", t.x, t.y))
                    v.leaving = True
                else:
                    t.state, t.state_t, t.vis = "flee", 4.0, v
                    t.say("surprise", 1.5)
                    t.glow_t = 1.5
                    self.fx.append(("glow", t.x, t.y))
                    self.event("escape", "%s got too close to the anglerfish and escaped!" % self.tag(t))

    def _sleeper(self, v, dt):
        tg = v.target
        if not v.leaving and (tg is None or not tg.alive):
            v.target = tg = None
            best = 160.0
            for t in self.dumbos:
                if t.alive and t.adult and t.y > self.h * 0.6:
                    d = math.hypot(t.x - v.x, t.y - v.y)
                    if d < best:
                        tg, best = t, d
            v.target = tg
        if tg is not None and not v.leaving:
            dx, dy = tg.x - v.x, tg.y - v.y
            d = math.hypot(dx, dy) or 1.0
            v.vx += (dx / d * 22 - v.vx) * min(1.0, dt)
            v.vy += (dy / d * 22 - v.vy) * min(1.0, dt)
            if d < 20 + tg.radius:
                if random.random() < 0.5:
                    self._kill(tg, "a sleeper shark")
                    tg.dead_t = CORPSE_TIME - 1
                    self.fx.append(("bite", tg.x, tg.y))
                v.leaving, v.target = True, None
        else:
            v.vy *= 0.95
            if v.leaving:
                v.vx = 25 if v.vx >= 0 else -25
        v.x += v.vx * dt
        v.y = min(max(self.h * 0.55, v.y + v.vy * dt), self.floor(v.x) - 8)
        if not v.leaving and (v.x < 30 and v.vx < 0 or v.x > self.w - 30 and v.vx > 0):
            v.vx = -v.vx
        for t in self.dumbos:      # タコはサメに気づくと逃げる
            if t.alive and t.state not in ("brood", "lay") and math.hypot(t.x - v.x, t.y - v.y) < 150:
                if t.state != "flee":
                    t.say("bang", 1.0)
                t.state, t.state_t, t.vis = "flee", 2.0, v

    # ---- 卵・誕生・死
    def _eggs_step(self, dt):
        for e in list(self.eggs):
            mom = self.by_id.get(e.mother)
            guarded = mom is not None and mom.state == "brood"
            e.t -= dt * (1.0 if guarded else 0.6)       # 守られていない卵は育ちが遅い
            if e.t <= 0:
                self.eggs.remove(e)
                kids = []
                for g in e.genomes:
                    if self.population() >= MAX_DUMBOS + 4:
                        break
                    t = Dumbo(g, e.x + random.uniform(-6, 6), e.y - 6, e.generation,
                              lineage=e.lineage, parents=e.parents)
                    t.energy = HATCH_ENERGY
                    t.say("sparkle", 2.0)
                    self.dumbos.append(t)
                    kids.append(t)
                self.births += len(kids)
                self.max_gen = max(self.max_gen, e.generation)
                if mom is not None and mom.state == "brood":
                    mom.state, mom.brood = "swim", None
                    mom.say("flower", 2.0)
                    for k in kids:
                        k.aff[mom.id] = mom.aff[k.id] = FRIEND_AFF * 0.8
                self.event("hatch", "%d baby dumbo%s of Lineage %s (Gen %d) hatched%s" % (
                    len(kids), "s" if len(kids) != 1 else "", e.lineage, e.generation,
                    " - their mother guarded them" if mom else ""))

    def _refound(self):
        pool = self.gene_pool or [random_genome() for _ in range(3)]
        lin = self.new_lineage()
        x, y = self.floor_point()
        gs = [mutate(random.choice(pool), rate=0.4) for _ in range(4)]
        self.eggs.append(Eggs(x, y, gs, self.max_gen + 1, lin, "drifted in", None, EGG_TIME * 0.1))
        self.event("hatch", "The colony died out... an egg case drifted in (Lineage %s)" % lin)

    def _kill(self, t, cause):
        t.state, t.dead_t, t.cause = "dead", 0.0, cause
        t.emote, t.emote_t = "ghost", 3.0
        t.clutch = None
        t.brood = None
        self.deaths += 1
        self.gene_pool.append(t.g)
        self.gene_pool = self.gene_pool[-10:]
        self.event("death", "%s died of %s at %s" % (self.tag(t), cause, fmt_dur(t.age)))
        mourners = []
        for o in self.dumbos:
            if o.target is t:
                o.target, o.state = None, "swim"
            if o.alive and o is not t and (o.partner == t.id or o.aff.get(t.id, 0) >= FRIEND_AFF):
                o.say("cry", 4.0)
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
        for t in self.dumbos:
            if t.state == "dead" and (force or t.dead_t > CORPSE_TIME):
                if t.adult:                              # 死骸はヨコエビの餌に
                    self.add_crusts(t.x, min(t.y, self.floor(t.x) - 4), 2)
                continue
            keep.append(t)
        self.dumbos = keep

    # ---- 仲間
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
                    if d2 < 60 * 60 and t.state != "sleep":
                        compat = 1.0 - abs(t.g["flock"] - o.g["flock"]) + (0.3 if o.lineage == t.lineage else 0)
                        t.aff[o.id] = t.aff.get(o.id, 0.0) + dt * 0.003 * (0.4 + compat)
                        if d2 < 35 * 35 and t.emote is None:
                            if o.id == t.partner and random.random() < dt / 25:
                                t.say("heart", 1.2)
                            elif t.aff[o.id] >= FRIEND_AFF and random.random() < dt / 40:
                                t.say(random.choice(("note", "blush")), 1.2)
            t.nb = (cx / n, cy / n, vx / n, vy / n, n, math.sqrt(near)) if n else None
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
        for t in self.dumbos:
            t.aff = {k: v * 0.97 for k, v in t.aff.items() if v > 0.05}
            if len(t.aff) > 10:
                t.aff = dict(sorted(t.aff.items(), key=lambda kv: -kv[1])[:10])

    def friends(self, t):
        return [self.by_id[i] for i, v in sorted(t.aff.items(), key=lambda kv: -kv[1])
                if v >= FRIEND_AFF and i in self.by_id and i != t.partner]

    # ---- 個体の行動
    def _update(self, t, dt):
        t.anim += dt
        t.glow_t = max(0.0, t.glow_t - dt)
        if t.emote_t > 0:
            t.emote_t -= dt
            if t.emote_t <= 0:
                t.emote = None
        if t.state == "dead":
            t.dead_t += dt
            t.y = min(self.floor(t.x) - 4, t.y + 6 * dt)     # 海底へ沈む
            return
        t.age += dt
        t.mate_cd -= dt
        t.eat_cd -= dt
        t.joy = max(0.0, t.joy - 0.015 * dt)
        t.annoy = max(0.0, t.annoy - 0.02 * dt)
        resting = t.state in ("sleep", "brood")
        t.energy -= t.metab * dt * (SLEEP_METAB if t.state == "sleep" else 0.25 if resting else 1.0)
        t.fatigue += (-dt / t.sleep_len) if t.state == "sleep" else (dt / t.awake_len)
        if t.energy <= 0:
            self._kill(t, "starvation" if t.state != "brood" else "exhaustion guarding her eggs")
            return
        if t.age >= t.lifespan:
            self._kill(t, "old age")
            return
        t.state_t -= dt
        st = t.state
        if st in ("startled", "dance", "lay", "petted"):
            if t.state_t <= 0:
                if st == "startled":
                    if t.annoy > 0.5:
                        t.say("anger")
                        t.state, t.state_t = "flee", 2.0
                    else:
                        t.state, t.state_t = "dance", 1.2
                        t.say("note")
                elif st == "lay":
                    self._lay(t)
                else:
                    t.state = "swim"
        elif st == "brood":
            if t.brood is None or t.brood not in self.eggs:
                t.state, t.brood = "swim", None
            elif random.random() < dt / 20:
                t.say(random.choice(("heart", "dots", "zzz")), 1.5, force=False)
        elif st == "play":
            v = t.vis
            if v is None or v.gone or v.leaving or t.state_t <= 0 or t.energy < 0.25:
                t.state, t.vis = "swim", None
            elif random.random() < dt / 3:
                t.say(random.choice(("star", "note", "heart")), 1.0, force=False)
        elif st == "lured":
            v = t.vis
            if v is None or v.gone or v.leaving or t.state_t <= 0:
                t.state, t.vis = "swim", None
        elif st == "sleep":
            t.fatigue = max(t.fatigue, -0.2)
            if t.fatigue <= 0 and t.night_pull(self.night) < 0.5:
                t.state, t.bed = "swim", None
                if self.phase in ("Sunrise", "Daytime"):
                    t.say("note", 1.5)
            elif random.random() < dt / 3:
                t.say("zzz", 1.5)
        elif st == "flee" and t.state_t > 0:
            pass
        else:
            self._decide(t, dt)
        self._steer(t, dt)

    def _decide(self, t, dt):
        prev = t.state
        t.state = "swim"
        sleepy = t.fatigue + t.night_pull(self.night) > 1 and t.energy > 0.15
        line = t.eat_below + self.appetite_shift()
        if t.clutch:
            t.state = "nest"                     # 卵は岩か鯨骨に産みつける
            if t.nest is None:
                t.nest = self.nest_point()
        elif sleepy:
            if prev == "to_bed" and t.bed:
                t.state = "to_bed"
            else:
                wh = self.whale
                if wh and not wh.falling and random.random() < 0.5:
                    t.bed = (wh.x + random.uniform(-80, 80), wh.y - random.uniform(16, 26))
                else:
                    t.bed = self.floor_point(t.x + random.uniform(-80, 80))
                t.bed = (min(max(10, t.bed[0]), self.w - 10), t.bed[1] - t.radius * 0.6)
                t.state = "to_bed"
        elif t.energy < line and (prev == "food" or t.energy < line - 0.05):
            if t.food is None or getattr(t.food, "gone", False) or t.food_t <= 0:
                t.food = self._choose_food(t)
                t.food_t = 1.5
            t.food_t -= dt
            if t.food is not None:
                t.state = "food"
        elif prev == "court" and t.target is not None and t.target.alive:
            t.state = "court"
        elif self._can_mate(t) and self.night < 0.7:
            p = self._find_partner(t)
            if p:
                t.state, t.target = "court", p
        if t.state == "swim" and t.g["whim"] > 0.7 and t.joy > 0.4 and random.random() < dt / 120:
            t.state, t.state_t = "dance", 1.2           # ひれをぱたぱた、くるくる
            t.say("note", 1.0)
        if t.energy < 0.2 and random.random() < dt / 6:
            t.say("sweat")

    def nest_point(self):
        wh = self.whale
        if wh and not wh.falling and random.random() < 0.6:
            return wh.x + random.uniform(-70, 70), wh.y - 18
        if self.rocks:
            rx = random.choice(self.rocks)[0]
            return rx + random.uniform(-8, 8), self.floor(rx) - 14
        return self.floor_point()

    def _can_mate(self, t):
        return (t.alive and t.state in ("swim", "court") and t.adult and t.energy > 0.5
                and t.mate_cd <= 0 and not t.clutch and t.brood is None and self._pop < MAX_DUMBOS - 1)

    def _find_partner(self, t):
        best, bd = None, 450.0
        for o in self.dumbos:
            if o is t or o.sex == t.sex or not self._can_mate(o):
                continue
            d = math.hypot(o.x - t.x, o.y - t.y)
            if distance(t.g, o.g) < 0.04:
                d *= 3
            if o.id == t.partner:
                d *= 0.3
            elif t.aff.get(o.id, 0) >= FRIEND_AFF:
                d *= 0.6
            if d < bd:
                best, bd = o, d
        return best

    def _choose_food(self, t):
        best, bs = None, 1e18
        for c in self.crusts:
            d = math.hypot(c.x - t.x, c.y - t.y) + 20
            s = d / (CRUST_ENERGY * (1.0 if t.picker else 0.5))
            if s < bs:
                best, bs = c, s
        wh = self.whale
        if wh and not wh.falling and wh.worms >= 1:
            d = math.hypot(wh.x - t.x, wh.y - t.y) + 20
            s = d / (WORM_ENERGY * (0.5 if t.picker else 1.0))
            if s < bs:
                best = wh
        return best

    def _steer(self, t, dt):
        sp = t.max_speed
        dx = dy = 0.0
        mul = 1.0
        st = t.state
        if st in ("sleep", "lay", "petted", "brood"):
            mul = 0.0
            if st in ("sleep", "brood"):          # 海底や骨の上にふわりと着地
                t.y = min(t.y + 4 * dt, self.floor(t.x) - t.radius * 0.6)
        elif st == "startled":
            mul = 0.0
        elif st == "flee" and t.vis is not None:
            v = t.vis
            dx, dy = t.x - v.x, t.y - v.y
            mul = 1.6
        elif st == "flee" and self.cursor:
            dx, dy = t.x - self.cursor[0], t.y - self.cursor[1]
            mul = 1.5
        elif st == "play" and t.vis:
            v = t.vis
            t.orbit += dt * 1.4
            tx, ty = v.x + math.cos(t.orbit) * 40, v.y + math.sin(t.orbit) * 26
            dx, dy = tx - t.x, ty - t.y
            mul = 1.4
        elif st == "lured" and t.vis:
            v = t.vis
            dx, dy = v.x + (14 if v.vx >= 0 else -14) - t.x, v.y - 14 - t.y
            mul = 0.6
        elif st == "dance":
            mul = 0.15
        elif st == "nest" and t.nest:
            dx, dy = t.nest[0] - t.x, t.nest[1] - t.y
            if math.hypot(dx, dy) < 6:
                t.state, t.state_t = "lay", LAY_TIME
                t.say("egg", LAY_TIME)
                mul = 0.0
        elif st == "to_bed" and t.bed:
            dx, dy = t.bed[0] - t.x, t.bed[1] - t.y
            mul = 0.7
            if math.hypot(dx, dy) < 6:
                t.state = "sleep"
                t.say("zzz", 2)
                mul = 0.0
        elif st == "food":
            f = t.food
            if f is None or getattr(f, "gone", False):
                t.state, t.food = "swim", None
            else:
                if isinstance(f, Whale):
                    fx, fy = f.x + ((t.id * 37) % 100 - 50), f.y - 6
                else:
                    fx, fy = f.x, f.y
                dx, dy = fx - t.x, fy - t.y
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
                    t.say("heart" if o.id != t.partner or random.random() < 0.5 else "blush", 1.0)

        care = t.g["care"]
        if self.cursor and st in ("swim", "court", "food") and care > 0.25:
            cx, cy = self.cursor
            d = math.hypot(cx - t.x, cy - t.y)
            if d < 160:
                like = (t.g["cursor"] - 0.5) * 2 * care + t.joy * 0.3 - t.annoy * 1.2
                if self.cursor_speed > 900 and d < 90 and care > 0.4:
                    t.say("bang", 0.8)
                    t.annoy = min(1.0, t.annoy + 0.12 * t.g["temper"] + 0.02)
                    t.state, t.state_t, t.vis = "flee", 0.8, None
                    t.glow_t = 1.0
                elif like > 0.25 and st == "swim":
                    if d > 22:
                        dx, dy = cx - t.x, cy - t.y
                        mul = 1.0
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
            dx, dy = math.cos(t.heading), math.sin(t.heading) * 0.5
            nb = t.nb
            fw = (t.g["flock"] - 0.5) * 2 * care
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
                else:
                    dx += ox / on * fw * 1.2
                    dy += oy / on * fw * 1.2
            for other, pull, gap in ((self.by_id.get(t.partner), 0.6, 60), (t.best_friend(self.by_id), 0.4, 55)):
                if other is not None and other.state not in ("sleep", "dead"):
                    ox, oy = other.x - t.x, other.y - t.y
                    od = math.hypot(ox, oy) or 1.0
                    if od > gap:
                        dx += ox / od * pull
                        dy += oy / od * pull
            # 好みの深さ(海底の少し上)に戻ろうとする
            pref = self.floor(t.x) - 40 - 60 * t.g["activity"]
            dy += max(-0.6, min(0.6, (pref - t.y) / 80))
            mul *= 0.5 + 0.4 * t.joy
            t.heading = math.atan2(dy, dx) if (dx or dy) else t.heading
        elif dx or dy:
            t.heading = math.atan2(dy, dx)
        if st not in ("flee", "play", "nest"):
            mul *= 1.0 - 0.25 * self.night
        n = math.hypot(dx, dy) or 1.0
        tx, ty = dx / n * sp * mul, dy / n * sp * mul
        k = min(1.0, dt * 1.5)
        t.vx += (tx - t.vx) * k
        t.vy += (ty - t.vy) * k
        t.x += t.vx * dt
        t.y += t.vy * dt
        m = t.radius + 2
        if t.x < m or t.x > self.w - m:
            t.vx = -t.vx
            t.heading = math.pi - t.heading
            t.x = min(max(t.x, m), self.w - m)
        top = self.h * 0.4
        if t.y < top:
            t.y, t.vy = top, abs(t.vy)
        fl = self.floor(t.x) - t.radius * 0.6
        if t.y > fl:
            t.y, t.vy = fl, -abs(t.vy) * 0.5

    def _eat(self, t, f):
        if isinstance(f, Whale):
            if f.worms < 1:
                t.food = None
                return
            f.worms -= 1
            t.energy += WORM_ENERGY * (0.5 if t.picker else 1.0)
        else:
            if f.gone:
                return
            f.gone = True
            t.energy += CRUST_ENERGY * (1.0 if t.picker else 0.5)
        t.energy = min(1.0, t.energy)
        t.joy = min(1.0, t.joy + 0.1)
        t.eat_cd = 1.2
        t.food_t = 0.0
        if t.energy > 0.92:
            t.say("flower", 1.2)
        elif random.random() < 0.3:
            t.say("note", 1.0)

    def _lay(self, t):
        gs = [c["g"] for c in t.clutch or []]
        if gs:
            par = t.clutch[0]["par"]
            gen = t.clutch[0]["gen"]
            e = Eggs(t.x, t.y + t.radius * 0.5, gs, gen, t.lineage, par, t.id)
            self.eggs.append(e)
            t.brood = e
            t.state = "brood"                        # ふ化まで卵を守る
            self.laid += len(gs)
            t.say("heart", 2.0)
            self.event("lay", "%s laid %d eggs and is guarding them" % (self.tag(t), len(gs)))
        else:
            t.state = "swim"
        t.clutch, t.nest = None, None

    # ---- 個体どうし
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
                if a.state not in ("sleep", "brood") or b.state not in ("sleep", "brood"):
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
        room = MAX_DUMBOS - self.population()
        n = min(room, 3 + int(mom.g["fertility"] * 3.99), int((mom.energy - 0.12) / EGG_COST))
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
                                             "renewed their bond" if again else "fell in love"))

    def _merge(self, a, b):
        t = Dumbo(blend(a.g, b.g), (a.x + b.x) / 2, (a.y + b.y) / 2,
                  max(a.generation, b.generation), max(ADULT_AGE, min(a.age, b.age)),
                  sex=a.sex, lineage=a.lineage, parents="merged #%d + #%d" % (a.id, b.id),
                  extra=max(a.extra, b.extra) + 1)
        t.energy = min(1.0, a.energy + b.energy)
        t.joy = 0.8
        t.say("sparkle", 2.5)
        t.aff = {k: v for k, v in list(a.aff.items()) + list(b.aff.items()) if k not in (a.id, b.id)}
        self.dumbos = [x for x in self.dumbos if x is not a and x is not b]
        self.dumbos.append(t)
        for o in self.dumbos:
            if o.target in (a, b):
                o.target, o.state = None, "swim"
            if o.partner in (a.id, b.id):
                o.partner = t.id
        self.merges += 1
        self.event("merge", "%s and %s merged into %s" % (self.tag(a), self.tag(b), self.tag(t)))

    def _split(self, t):
        kids = []
        for i in range(2):
            k = Dumbo(mutate(t.g, rate=0.3), t.x + (i * 2 - 1) * t.radius, t.y, t.generation,
                      t.age, sex=t.sex, lineage=t.lineage, parents="split from #%d" % t.id,
                      extra=t.extra - 1)
            k.energy = t.energy / 2
            k.say("sparkle", 2.0)
            kids.append(k)
        kids[0].aff[kids[1].id] = kids[1].aff[kids[0].id] = FRIEND_AFF * 1.5
        self.dumbos = [x for x in self.dumbos if x is not t] + kids
        for o in self.dumbos:
            if o.target is t:
                o.target, o.state = None, "swim"
        self.splits += 1
        self.event("split", "%s split into #%d and #%d" % (self.tag(t), kids[0].id, kids[1].id))

    # ---- マウス
    def hit(self, x, y, pad=4):
        best, bd = None, 1e9
        for t in self.dumbos:
            if not t.alive:
                continue
            d = math.hypot(t.x - x, t.y - y)
            if d < t.radius + pad and d < bd:
                best, bd = t, d
        return best

    def pet(self, t, dist):
        if not t.alive or t.state in ("lay", "startled", "flee"):
            return
        t.pet_acc += dist
        if t.pet_acc < PET_STROKE:
            return
        t.pet_acc = 0.0
        t.pets += 1
        like = (t.g["cursor"] - 0.5) * 2 * t.g["care"] + 0.35 + t.joy * 0.3 - t.annoy
        if t.state in ("sleep", "brood"):
            if like > 0.3 or t.g["temper"] < 0.3:
                t.joy = min(1.0, t.joy + 0.05)
                t.say("zzz" if t.state == "sleep" else "blush", 1.2)
                return
            if t.state == "sleep":
                t.state, t.bed = "swim", None
                t.fatigue = min(t.fatigue, 0.6)
        if like > 0:
            t.joy = min(1.0, t.joy + 0.15)
            t.annoy = max(0.0, t.annoy - 0.1)
            if t.state != "brood":
                t.state, t.state_t = "petted", 1.5
            t.say("heart" if t.joy > 0.6 else random.choice(("note", "blush")), 1.2)
        else:
            t.annoy = min(1.0, t.annoy + 0.12 + 0.2 * t.g["temper"])
            t.say("anger" if t.annoy > 0.4 else "sweat", 1.2)
            if t.annoy > 0.5 and t.state != "brood":
                t.state, t.state_t, t.vis = "flee", 1.5, None

    def poke(self, t):
        """ダブルクリック: びっくりして腕を反り返らせる「傘」の姿勢になり、発光する。"""
        if t.state == "lay":
            t.say("anger", 1.0)
            return
        if t.state == "brood":
            t.say("anger", 1.2)
            t.annoy = min(1.0, t.annoy + 0.3)
            t.glow_t = 1.5
            self.fx.append(("glow", t.x, t.y))
            return
        t.annoy = min(1.0, t.annoy + 0.1 + 0.35 * t.g["temper"] * t.g["care"])
        t.state, t.state_t, t.bed = "startled", 2.5, None
        t.glow_t = 2.0
        t.say("surprise", 1.0)
        self.fx.append(("glow", t.x, t.y))

    def dumbo_info(self, t):
        if not t.alive:
            return ["#%d  Lineage %s  Gen %d" % (t.id, t.lineage, t.generation),
                    "Died of %s at %s" % (t.cause, fmt_dur(t.age))]
        e = t.energy
        health = "Good" if e > 0.7 else "OK" if e > 0.4 else "Hungry" if e > 0.2 else "Starving"
        mood = ("sad" if t.emote == "cry" else "annoyed" if t.annoy > 0.5
                else "happy" if t.joy > 0.6 else "calm")
        now = {"swim": "drifting", "food": "hunting", "court": "courting", "nest": "looking for a nest site",
               "lay": "laying eggs", "brood": "guarding her eggs", "sleep": "resting on the seafloor",
               "to_bed": "settling down to rest", "startled": "startled! (umbrella pose)",
               "dance": "flapping its ears happily", "flee": "fleeing!", "petted": "enjoying the light touch",
               "play": "playing with the vampire squid", "lured": "drawn to a mysterious light..."}
        style = STYLES[style_of(t.g)]
        lines = ["#%d  %s  Lineage %s  Gen %d" % (t.id, "Female" if t.sex == "F" else "Male",
                                                   t.lineage, t.generation),
                 "Age %s / %s%s" % (fmt_dur(t.age), fmt_dur(t.lifespan), "" if t.adult else "  (young)"),
                 "Health %d%% (%s)   Mood: %s" % (round(e * 100), health, mood),
                 "%s   Size x%d   Depth %d m" % ("Amphipod hunter" if t.picker else "Worm grazer",
                                                 t.scale, self.depth_m(t.y)),
                 "Look: %s, %s, %s ears%s" % (color_name(t.g), style,
                                              "big" if t.g["ears"] > 0.66 else "small" if t.g["ears"] < 0.33 else "medium",
                                              "  (rare!)" if is_dark(t.g) or style == "heart" else ""),
                 "Traits: " + (", ".join(traits(t.g)) or "Average")]
        p = self.by_id.get(t.partner)
        fr = self.friends(t)
        if p or fr:
            lines.append(("Partner: %s   " % self.tag(p) if p else "") +
                         ("Friends: " + ", ".join("#%d" % f.id for f in fr[:4]) if fr else ""))
        if t.parents:
            lines.append("Origin: " + t.parents)
        if t.clutch:
            lines.append("Carrying %d eggs" % len(t.clutch))
        if t.pets:
            lines.append("Petted %d time%s" % (t.pets, "s" if t.pets != 1 else ""))
        lines.append("Now: " + now.get(t.state, t.state))
        return lines

    def hover_info(self, x, y):
        for e in self.eggs:
            if math.hypot(e.x - x, e.y - y) < 9:
                return ["Egg cluster (%d)  Lineage %s  Gen %d" % (len(e.genomes), e.lineage, e.generation),
                        "Parents: %s" % e.parents, "Hatches in %s" % fmt_dur(max(0, e.t))]
        for v in self.visitors:
            if math.hypot(v.x - x, v.y - y) < 30:
                return {"vampire": ["Vampire squid", "Friendly and glowing. Dumbos love to play with it"],
                        "sperm": ["Sperm whale", "Dives down to hunt squid, then returns to breathe"],
                        "isopod": ["Giant isopod", "A slow scavenger of the seafloor"],
                        "hagfish": ["Hagfish", "Scavengers feeding on the whale"],
                        "sleeper": ["Sleeper shark", "Slow, but it hunts dumbos near the floor!"],
                        "angler": ["Anglerfish", "Its glowing lure attracts curious dumbos..."]}[v.kind]
        wh = self.whale
        if wh and abs(wh.x - x) < WHALE_HALF and abs(wh.y - y) < 32:
            if wh.falling:
                return ["Falling whale", "Sinking to the seafloor (about %d m now)" % self.depth_m(wh.y)]
            return ["Whale fall - %s" % wh.stage, STAGE_INFO[wh.stage],
                    "Age %s   Flesh %d%%   Bone worms %d" % (fmt_dur(wh.age), round(wh.flesh * 100), int(wh.worms))]
        for f in self.foodfalls:
            if math.hypot(f.x - x, f.y - y) < 10:
                return ["Dead fish", "A small food fall. Amphipods gather"]
        for c in self.crusts:
            if abs(c.x - x) < 5 and abs(c.y - y) < 5:
                return ["Amphipod", "Tiny crustacean. Food for dumbos"]
        for f in self.lanterns:
            if abs(f.x - x) < 8 and abs(f.y - y) < 5:
                return ["Lanternfish", "Rises toward the surface at night,",
                        "sinks back to the depths by day"]
        if y < self.surface:
            return ["Sea surface", "%s (%02d:%02d)" % (self.phase, int(self.hour), int(self.hour % 1 * 60))]
        if y < self.floor(x):
            return ["Depth %d m" % self.depth_m(y)]
        return None

    # ---- 留守中
    def advance_offline(self, seconds, start=None):
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
        self.visitors = []
        self.foodfalls = []
        self.update_daylight(self.clock(), log=False)
        for t in self.dumbos:
            t.emote, t.food, t.target, t.vis = None, None, None, None
            if t.state not in ("sleep", "dead", "brood"):
                t.state = "swim"
        self._decompose(force=True)
        return self.births - b0, self.deaths - d0, self.laid - l0

    def _offline_step(self, dt):
        self.time += dt
        self._off_ts = getattr(self, "_off_ts", self.clock()) + dt
        self.update_daylight(self._off_ts, log=False)
        wh = self.whale
        if wh and wh.falling:
            wh.falling, wh.y = False, self.floor(wh.x) - WHALE_OFF
        self._whale_step(dt)
        crust_in = self.food_rate() * dt + len(self.crusts)
        self.crusts = []
        alive = self.alive()
        self._pop = len(alive) + sum(len(e.genomes) for e in self.eggs)
        self.by_id = {t.id: t for t in alive}
        random.shuffle(alive)
        shift = self.appetite_shift()
        for t in alive:
            t.age += dt
            t.mate_cd -= dt
            if t.state == "brood":
                t.energy -= t.metab * dt * 0.25
            else:
                awake = t.awake_len / (t.awake_len + t.sleep_len) * (1 - 0.8 * t.night_pull(self.night))
                t.energy -= t.metab * dt * (awake + SLEEP_METAB * (1 - awake))
                tries = 0
                while t.energy < t.eat_below + shift and tries < 8:
                    tries += 1
                    if crust_in >= 1 and (t.picker or not (wh and wh.worms >= 1)):
                        crust_in -= 1
                        t.energy += CRUST_ENERGY * (1.0 if t.picker else 0.5)
                    elif wh and wh.worms >= 1:
                        wh.worms -= 1
                        t.energy += WORM_ENERGY * (0.5 if t.picker else 1.0)
                    else:
                        break
            t.energy = min(1.0, t.energy)
            if t.energy <= 0:
                self._kill(t, "starvation")
            elif t.age >= t.lifespan:
                self._kill(t, "old age")
        for _ in range(int(min(CRUST_MAX, crust_in))):
            self.crusts.append(Crust(*self.deep_point(0.6)))
        if random.random() < dt / 4 / HOUR * 0.4:
            big = [t for t in self.dumbos if t.alive and t.adult]
            if big:
                self._kill(random.choice(big), random.choice(("a sleeper shark", "an anglerfish")))
        self._decompose(force=True)
        self.by_id = {t.id: t for t in self.dumbos if t.alive}
        self._eggs_step(dt)
        for t in self.dumbos:
            if t.alive and t.clutch:
                t.x, t.y = self.nest_point()
                self._lay(t)
        if self.night < 0.7:
            fem = [t for t in self.dumbos if t.sex == "F" and self._can_mate(t)]
            mal = [t for t in self.dumbos if t.sex == "M" and self._can_mate(t)]
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
                "dumbos": [t.to_dict() for t in self.dumbos if t.alive],
                "eggs": [e.to_dict() for e in self.eggs],
                "whale": self.whale.to_dict() if self.whale else None,
                "rocks": self.rocks,
                "births": self.births, "deaths": self.deaths, "laid": self.laid,
                "merges": self.merges, "splits": self.splits, "whales": self.whales,
                "max_gen": self.max_gen, "n_lineages": self.n_lineages, "gene_pool": self.gene_pool,
                "events": self.events, "history": self.history}

    @classmethod
    def from_dict(cls, d):
        wd = cls(d.get("w", 700), d.get("h", 480))
        wd.dumbos = [Dumbo.from_dict(x) for x in d.get("dumbos", [])]
        wd.by_id = {t.id: t for t in wd.dumbos}
        wd.eggs = [Eggs.from_dict(e) for e in d.get("eggs", [])]
        for e in wd.eggs:
            mom = wd.by_id.get(e.mother)
            if mom:
                mom.state, mom.brood = "brood", e
        w = d.get("whale")
        if w:
            wd.whale = Whale(w["x"], w["age"], w.get("falling", False), w.get("flesh", 0.0))
            wd.whale.worms, wd.whale.next_t = w.get("worms", 0.0), w.get("next")
            wd.whale.y = wd.floor(wd.whale.x) - WHALE_OFF if not wd.whale.falling else wd.surface
        wd.rocks = d.get("rocks") or []
        if not wd.rocks:
            wd.seed_rocks()
        for k in ("births", "deaths", "laid", "merges", "splits", "whales"):
            setattr(wd, k, d.get(k, 0))
        wd.max_gen = d.get("max_gen", 1)
        wd.gene_pool = [fill_genome(g) for g in d.get("gene_pool", [])]
        wd.n_lineages = d.get("n_lineages", 0) or max(1, len({t.lineage for t in wd.dumbos}))
        wd.events = [tuple(e) for e in d.get("events", []) if len(e) == 3]
        wd.history = [tuple(h) for h in d.get("history", [])]
        return wd

    def resize(self, w, h):
        if w < 120 or h < 120:
            return
        sx, sy = w / self.w, h / self.h
        objs = self.dumbos + self.eggs + self.crusts + self.lanterns + self.visitors + self.foodfalls
        for o in objs:
            o.x *= sx
            o.y *= sy
        for v in self.visitors:
            v.y0 *= sy
        for r in self.rocks:
            r[0] *= sx
        self.w, self.h = w, h
        if self.whale:
            self.whale.x *= sx
            self.whale.y = self.floor(self.whale.x) - WHALE_OFF if not self.whale.falling else self.whale.y * sy
        for t in self.dumbos:
            for attr in ("nest", "bed"):
                p = getattr(t, attr)
                if p:
                    setattr(t, attr, (p[0] * sx, p[1] * sy))


# ---------------------------------------------------------------- 保存先
def find_save_dir():
    env = os.environ.get("WHALEFALL_SAVE_DIR")
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
                return os.path.join(c, "WhaleFall"), True
        except OSError:
            pass
    return os.path.join(home, "WhaleFall"), False


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
    path = os.path.join(folder, SAVE_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        world = World.from_dict(data)
        return world, max(0.0, time.time() - float(data.get("saved_at", time.time())))
    except (OSError, ValueError, KeyError, TypeError):
        return None, 0.0


# ---------------------------------------------------------------- ドット絵(横から見た姿)
# ジュウモンジダコ。F=ひれ(耳) M=外套膜 E=目 T=腕の膜 t=腕の先
DUMBO = (
    ("..FF.....FF..",
     ".FFFMMMMMFFF.",
     "..FMMMMMMMF..",
     "...MMMMMMM...",
     "...MEMMMEM...",
     "...MMMMMMM...",
     "..TTTTTTTTT..",
     ".TTTTTTTTTTT.",
     ".T.T.T.T.T.T.",
     "t..t..t..t..t"),
    (".............",
     "....MMMMM....",
     "FF.MMMMMMM.FF",
     "FFFMMMMMMMFFF",
     ".F.MEMMMEM.F.",
     "...MMMMMMM...",
     "..TTTTTTTTT..",
     ".TTTTTTTTTTT.",
     "T..T..T..T..T",
     "t..t..t..t..t"),
)
UMBRELLA = ("t..t..t..t..t",
            ".T.T.T.T.T.T.",
            ".TTTTTTTTTTT.",
            "TTTTMMMMMTTTT",
            "TTFMEMMMEMFTT",
            ".TFMMMMMMMFT.",
            "..TMMMMMMMT..",
            "...MMMMMMM...",
            "....MMMMM....",
            ".............")
BROOD = (".............",
         ".............",
         "....MMMMM....",
         "...MMMMMMM...",
         "..FMEMMMEMF..",
         ".FFMMMMMMMFF.",
         "TTTTTTTTTTTTT",
         "T.T.T.T.T.T.T",
         ".............",
         ".............")

EMOTES = {
    "heart": ({"X": "#ff6f96"}, (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X...")),
    "note": ({"X": "#ffd23f"}, ("...XXX.", "...X.X.", "...X...", "...X...", ".XXX...", "XXXX...", ".XX....")),
    "anger": ({"X": "#ff3a3a"}, (".X...X.", "XX...XX", ".......", ".......", "XX...XX", ".X...X.")),
    "zzz": ({"X": "#ffffff"}, ("XXXXX", "...X.", "..X..", ".X...", "XXXXX")),
    "bang": ({"X": "#ffffff"}, (".X.", ".X.", ".X.", ".X.", "...", ".X.")),
    "question": ({"X": "#ffffff"}, (".XXX.", "X...X", "...X.", "..X..", ".....", "..X..")),
    "surprise": ({"X": "#ffffff"}, (".X..XXX.", ".X.X...X", ".X....X.", ".X...X..", "........", ".X...X..")),
    "sparkle": ({"X": "#bff6ff"}, ("...X...", "...X...", "..XXX..", "XXXXXXX", "..XXX..", "...X...", "...X...")),
    "star": ({"X": "#ffe14d", "o": "#fff6b8"}, ("...X...", "..XoX..", "XXXoXXX", ".XoooX.", "..XoX..", ".XX.XX.", "X.....X")),
    "sweat": ({"X": "#5aa8ff"}, ("..X..", ".XXX.", "XXXXX", "XXXXX", ".XXX.")),
    "cry": ({"X": "#7cc4ff"}, ("X...X", "X...X", "XX.XX", "XX.XX", ".....", "X...X")),
    "blush": ({"X": "#ff9cc0"}, ("XX...XX", "XXX.XXX", ".X...X.")),
    "flower": ({"X": "#ffb3d1", "o": "#ffe066"}, (".X.X.", "XXoXX", ".XoX.", "XXoXX", ".X.X.")),
    "dots": ({"X": "#ffffff"}, ("X.X.X",)),
    "egg": ({"X": "#fffdf0"}, (".XX.", "XXXX", "XXXX", "XXXX", ".XX.")),
    "ghost": ({"X": "#f4f4ff"}, (".XXX.", "XXXXX", "X.X.X", "XXXXX", "XXXXX", "X.X.X")),
}
VIS_ART = {   # 右向き
    "vampire": ({"X": "#7a1f3a", "x": "#4e1226", "b": "#7ff3ff", "e": "#ff5a5a"},
                (("..XXX......", ".XXXXX.....", "XXeXXXXXX..", "XXXXXXXXXXb", ".XXXXX.X.X.", "..X.X.X.X.b"),
                 ("..XXX......", ".XXXXX.....", "XXeXXXXXXXb", "XXXXXXXXX..", ".XXXXX.XX..", "..b.X..X.b."))),
    "sperm": ({"X": "#5d6878", "x": "#4a5462", "o": "#8a96a6", "e": "#111111"},
              (("........................XXXXXXXXXXXXX...",
                "X.....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX..",
                "XX..XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXeXXXX.",
                ".XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "XX..XXooooooooooooooooooooooooooooXXXX..",
                "X.....oooooooooooooooooooooo....xxxxxx..",
                "......................................."),
               ("........................XXXXXXXXXXXXX...",
                ".X....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX..",
                "X.X.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXeXXXX.",
                "..XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "X.X.XXooooooooooooooooooooooooooooXXXX..",
                ".X....oooooooooooooooooooooo....xxxxxx..",
                "......................................."))),
    "isopod": ({"X": "#b9a8c8", "x": "#8a7a9c", "e": "#222222"},
               (("..XXXXXXXX..", ".XxXxXxXxXX.", "XXxXxXxXxXeX", "x.x.x.x.x.x."),
                ("..XXXXXXXX..", ".XxXxXxXxXX.", "XXxXxXxXxXeX", ".x.x.x.x.x.x"))),
    "hagfish": ({"X": "#e8a0a8", "e": "#333333"},
                (("..XX....XX", "XX..XXXX.e"), ("XX....XX..", "..XXXX..XXe"))),
    "sleeper": ({"X": "#3d4550", "x": "#2c333c", "o": "#5a6470", "e": "#9fe0ff"},
                (("..........X.................", "X........XXX............X...",
                  "XX.XXXXXXXXXXXXXXXXXXXXXXXX.", ".XXXXXXXXXXXXXXXXXXXXXXXXeXX",
                  "XX.ooooooooooooooooooooooXX.", "X.....X............X........"),
                 ("..........X.................", ".X.......XXX............X...",
                  "X.XXXXXXXXXXXXXXXXXXXXXXXXX.", ".XXXXXXXXXXXXXXXXXXXXXXXXeXX",
                  "X.Xooooooooooooooooooooooxx.", ".X....X............X........"))),
    "angler": ({"X": "#3a2e3e", "x": "#2a2030", "l": "#c8ff9a", "t": "#ffffff", "e": "#ff6a4a"},
               (("........ll..", ".......X.l..", "......X.....", "..XXXXX.....", ".XXXXXXX....",
                 "XXXXXeXXX...", "XXXXXXXXXt.t", ".XXXXXXX.tt.", "..XXXXX....."),
                ("........l...", ".......X.ll.", "......X.....", "..XXXXX.....", ".XXXXXXX....",
                 "XXXXXeXXX...", "XXXXXXXXXtt.", ".XXXXXXX..t.", "..XXXXX....."))),
}
CRUST_ART = ("XXo", ".X.")
LANTERN_ART = (".XXXX.", "XbXbXX", ".XXXX.")
WORM_ART = (".r.", "rrr", ".w.", ".w.")
EGGS_ART = (".ooo.", "ooooo", "ooooo", ".ooo.")
FISH_FALL_ART = ("..XXXXX.", "XXXXXXXe", "..XXXXX.")
ROCK_ART = ("..oooo..", ".oXXXXo.", "oXXXXXXx", "XXXXXxXx", "XXXxxxxx")

SKY = {"day": (0x8f, 0xd6, 0xff), "night": (0x10, 0x18, 0x38)}
WATER_TOP = (0x1e, 0x88, 0xb8)       # 昼の海面近く
WATER_MID = (0x08, 0x24, 0x4c)
WATER_DEEP = (0x01, 0x04, 0x10)
FLOOR_COL = "#3b3530"
FLOOR_LIGHT = "#544a40"
BONE = "#eee6cf"
FLESH = "#c48a86"
SKIN = "#5a6878"


def hexcol(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def hex_rgb(col):
    return tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))


def tint_hex(col, k):
    return "#%02x%02x%02x" % tuple(min(255, int(c * m)) for c, m in zip(hex_rgb(col), k))


def mix(c1, c2, f):
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


def dumbo_colors(g):
    h, h2 = pastel_hue(g["hue"]), pastel_hue(g["hue2"])
    if is_dark(g):
        return hexcol(h, 0.7, 0.62), hexcol(h, 0.75, 0.42), hexcol(h2, 0.5, 0.9), hexcol(h, 0.6, 0.55)
    return hexcol(h, 0.28, 0.97), hexcol(h, 0.42, 0.78), hexcol(h2, 0.45, 0.88), hexcol(h, 0.2, 0.92)


def mantle_pattern(style, x, y, bits, glow_col):
    """外套膜の模様。左右対称。"""
    mx = x if x <= 6 else 12 - x
    idx = (y * 4 + mx) % PATTERN_BITS
    if style == 0:
        return None
    if style == 1:
        return "pat" if (x + y * 2) % 4 == 0 and bits[idx] else None
    if style == 2:
        return "pat" if y in (1, 3, 5) else None
    if style == 3:
        return glow_col if (x + y) % 3 == 0 else None
    if style == 4:
        return "pat" if y <= 2 else None
    if style == 5:
        return "pat" if bits[idx] else None
    return "#ff8fb0" if (x, y) in {(5, 2), (7, 2), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (6, 5)} else None


def dumbo_pixels(g, frame, mode):
    """mode: normal / umbrella / brood / dead / glow。"""
    rows = {"umbrella": UMBRELLA, "brood": BROOD}.get(mode, DUMBO[frame])
    mantle, shade, pat, web = dumbo_colors(g)
    glow_col = hexcol(0.52 + 0.3 * g["glow"], 0.55, 1.0)
    fin = mantle
    tip = pat
    eye = "#2a2438"
    if mode == "dead":
        mantle = shade = pat = web = fin = tip = "#8a8a8a"
        eye = "#555555"
    style = style_of(g)
    out = []
    for y, row in enumerate(rows):
        line = []
        for x, c in enumerate(row):
            if c == "M":
                edge = row[x - 1] != "M" or x + 1 >= len(row) or row[x + 1] != "M"
                col = shade if edge else mantle
                if not edge and mode != "dead":
                    p = mantle_pattern(style, x, y, g["pattern"], glow_col)
                    if p == "pat":
                        col = pat
                    elif p:
                        col = p
                line.append(col)
            elif c == "F":
                line.append(fin if g["ears"] > 0.33 or (x + y) % 2 == 0 else shade)
            elif c == "T":
                line.append(web)
            elif c == "t":
                line.append(glow_col if mode == "glow" or g["glow"] > 0.8 else tip)
            elif c == "E":
                line.append(eye)
            else:
                line.append(None)
        out.append(line)
    if mode == "glow":                     # 驚くと体が光る
        out = [[(mix(hex_rgb(c), hex_rgb(glow_col), 0.45) if c else None) for c in r] for r in out]
    return out


WHALE_W, WHALE_H = 64, 22
WHALE_OFF = 26                # 海底からクジラの中心までの高さ(px)
WHALE_HALF = 96               # クジラの横幅の半分(px)


def _in_whale(x, y):
    """丸い頭・やさしいからだ・持ち上がった尾びれ(絵本のクジラ)。"""
    body = ((x - 34) / 24.0) ** 2 + ((y - 11) / 7.6) ** 2 < 1.0
    head = (x - 50) ** 2 + ((y - 11.5) / 0.95) ** 2 < 9.5 ** 2
    stock = 7 <= x <= 14 and abs(y - 11 + (14 - x) * 0.25) <= 1.2 + (x - 7) * 0.35
    fluke = 1 <= x <= 8 and (abs(y - (9 - (8 - x) * 0.9)) <= 1.1 or abs(y - (11 + (8 - x) * 0.5)) <= 0.9)
    return body or head or stock or fluke


def whale_grid(falling=True):
    """絵本のようなクジラ(横から、右が頭)。O=縁 S=背 W=おなか g=のどのひだ E=閉じた目と口 P=ほっぺ F=ひれ"""
    W, H = WHALE_W, WHALE_H
    grid = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not _in_whale(x, y):
                continue
            edge = any(not (0 <= x + dx < W and 0 <= y + dy < H and _in_whale(x + dx, y + dy))
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                grid[y][x] = "O"
            elif y > 12 + (0 if x > 20 else 2):
                grid[y][x] = "g" if 40 <= x <= 57 and x % 3 == 0 and y > 13 else "W"
            else:
                grid[y][x] = "S"
    for x, y in ((51, 8), (52, 9), (53, 9), (54, 9), (55, 8)):        # やさしく閉じた目
        grid[y][x] = "E"
    for x, y in ((57, 14), (58, 14), (59, 13)):                      # ほほえむ口
        grid[y][x] = "E"
    for x, y in ((53, 11), (54, 11), (55, 11)):                      # ほっぺ
        grid[y][x] = "P"
    for x, y in ((42, 16), (43, 17), (44, 18), (45, 18), (44, 17), (43, 16), (42, 15)):   # 胸びれ
        grid[y][x] = "F"
    for x, y in ((48, 4), (49, 5), (50, 5), (49, 4)):                # 光(つや)
        if grid[y][x] in ("S", "O"):
            grid[y][x] = "L"
    return grid


def whale_body_level(level):
    """海底のクジラ: level(肉の残り 0〜1)に応じて、からだが少しずつ骨に変わっていく。"""
    base = whale_grid()
    out = [[None] * WHALE_W for _ in range(WHALE_H)]
    for y in range(WHALE_H):
        for x in range(WHALE_W):
            c = base[y][x]
            if c is None:
                continue
            n = 0.5 + 0.25 * math.sin(x * 0.37 + y * 0.9) + 0.25 * math.sin(x * 0.13 - y * 0.5 + 1.3)
            face = c in ("E", "P") and level >= 0.2                   # 顔は最後まで穏やか
            if n < level or face:
                out[y][x] = "f" if (level - 0.12 < n < level and not face) else c
    return out


def skeleton_grid():
    """骨(背骨・肋骨・丸い頭骨・尾の骨)。B=骨 b=骨の影"""
    W, H = WHALE_W, WHALE_H
    g = [[None] * W for _ in range(H)]
    for x in range(4, 46):                 # 背骨
        g[11][x] = "B"
        if x % 2 == 0:
            g[10][x] = "B"
            g[12][x] = "b"
    for x in range(18, 45, 3):             # 肋骨(弓なり)
        for y in range(5, 18):
            dx = int(round(math.sin((y - 5) / 12.0 * math.pi) * 2.0))
            if 0 <= x + dx < W:
                g[y][x + dx] = "B" if y < 15 else "b"
    for y in range(H):                     # 丸い頭骨
        for x in range(42, 61):
            d = math.hypot(x - 51, (y - 11.5) / 0.95)
            if 7.4 < d < 8.8 or (y == 14 and 45 <= x <= 58):        # 頭骨のふちとあご
                g[y][x] = "B" if y < 14 else "b"
    for x, y in ((51, 8), (52, 9), (53, 9), (54, 9), (55, 8)):        # 目のくぼみ(やさしい形のまま)
        g[y][x] = "b"
    for x in range(1, 8):                  # 尾の骨
        g[11][x] = "B" if x % 2 else "b"
    return g


# ---------------------------------------------------------------- 画面
class App:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.save_dir, self.on_drive = find_save_dir()
        self.root = tk.Tk()
        self.root.title("Whale Fall" + ("" if self.on_drive else " (saved locally)"))
        self.root.geometry("700x480")
        self.root.minsize(360, 260)
        self.canvas = tk.Canvas(self.root, width=700, height=480, bg="#03081a",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.show_lineage = False
        self.show_rel = False
        self.topmost = False

        world, away = load_world(self.save_dir)
        if world is None:
            self.world = World(700, 480)
            self.world.seed()
            self.banner = "Welcome to the deep sea! A whale is falling..."
        else:
            self.world = world
            b, d, l = world.advance_offline(away)
            self.banner = ("While you were away: %s passed\nBorn %d   Died %d   Eggs laid %d"
                           % (fmt_dur(away), b, d, l))
        self.banner_t = 8.0
        c = self.canvas
        self.items = {}
        self.tables = {"crust": {}, "lantern": {}, "eggs": {}, "visitor": {}, "foodfall": {}}
        self.emote_img = {k: self._img(px, cols, 2) for k, (cols, px) in EMOTES.items()}
        self.crust_img = {lit: self._img(CRUST_ART, {"X": "#ff9a8a", "o": "#ffd0c8"}, 2, (1.2,) * 3 if lit else (0.8,) * 3)
                          for lit in (0, 1)}
        self.lantern_img = {d: self._img(LANTERN_ART if d == 1 else tuple(r[::-1] for r in LANTERN_ART),
                                         {"X": "#46506a", "b": "#7fe8ff"}, 2) for d in (1, 3)}
        self.eggs_img = self._img(EGGS_ART, {"o": "#fff2d8"}, 2)
        self.ff_img = self._img(FISH_FALL_ART, {"X": "#b8c0c8", "e": "#333333"}, 2)
        self.worm_img = self._img(WORM_ART, {"r": "#ff4a5a", "w": "#f4f0e8"}, 2)
        self.rock_img = [self._img(ROCK_ART, dict(zip("Xxo", cols)), 3) for cols in
                         (("#5a5450", "#3e3a36", "#7a726a"), ("#4e5258", "#36393e", "#6e747c"),
                          ("#5c5048", "#40362e", "#7c6c60"))]
        self.vis_img = {}
        for kind, (cols, frames) in VIS_ART.items():
            for f, art in enumerate(frames):
                scl = 3 if kind == "sperm" else 2
                self.vis_img[(kind, 1, f)] = self._img(art, cols, scl)
                self.vis_img[(kind, 3, f)] = self._img(tuple(r[::-1] for r in art), cols, scl)
        self.make_whale_images()
        self.bg_items = []
        self.surface_items = []
        self.whale_items = []
        self.worm_items = []
        self.mat_items = []
        self.whale_key = None
        self.snow = [[c.create_rectangle(0, 0, 1, 1, fill="#cfd8e8", width=0, tags="snow"),
                      random.uniform(0, 700), random.uniform(0, 480), random.uniform(3, 8)] for _ in range(40)]
        self.rays = [c.create_line(0, 0, 1, 1, fill="#5fb8e0", width=1, tags="ray") for _ in range(6)]
        self.light = [c.create_oval(0, 0, 1, 1, outline=col, width=1, state="hidden", tags="light")
                      for col in ("#2f5f80", "#4f8fb0", "#8fd0f0")]
        self.fx_items = []
        self.rel_lines = []
        self.hud = c.create_text(8, 22, anchor="nw", fill="#cfe8ff", font=("", 9), tags="ui")
        self.graph_box = c.create_rectangle(0, 0, 1, 1, fill="#0c1a30", outline="#3a6a8a", tags="ui")
        self.graph_title = c.create_text(0, 0, anchor="nw", text="Ecosystem (last 20 min)",
                                         fill="#9fd0ff", font=("", 8), tags="ui")
        self.graph_lines = [c.create_line(0, 0, 1, 1, fill=col, width=2, tags="ui")
                            for col in ("#ffb3d1", "#ff9a8a", "#ff4a5a")]
        self.graph_legend = [c.create_text(0, 0, anchor="nw", fill=col, font=("", 8), tags="ui")
                             for col in ("#ffb3d1", "#ff9a8a", "#ff6a7a")]
        self.depth_labels = []
        self.log_items = [c.create_text(8, 0, anchor="sw", fill="#d8c8b0", font=("", 9), tags="ui")
                          for _ in range(3)]
        self.help = c.create_text(0, 0, anchor="sw", fill="#a89880", font=("", 8), tags="ui",
                                  text="Click: status  Dbl-click: startle  Stroke: pet  Click: marine snow  "
                                       "Shift+Click: dead fish  Right-click: on top  L: lineage  R: friends")
        self.follow = None
        self.panel_line = c.create_line(0, 0, 1, 1, fill="#7fc8ff", state="hidden", tags="panel")
        self.panel_box = c.create_rectangle(0, 0, 1, 1, fill="#0d1c33", outline="#7fc8ff", state="hidden", tags="panel")
        self.panel_text = c.create_text(0, 0, anchor="nw", fill="#e8f4ff", font=("", 9), state="hidden", tags="panel")
        self.panel_size = (0, 0)
        self.panel_t = 0.0
        self.tip_box = c.create_rectangle(0, 0, 1, 1, fill="#0d1c33", outline="#7fc8ff", state="hidden", tags="tip")
        self.tip_text = c.create_text(0, 0, anchor="nw", fill="#e8f4ff", font=("", 9), state="hidden", tags="tip")
        self.bann = c.create_text(350, 200, fill="#ffffff", font=("", 13, "bold"), justify="center", tags="tip")
        self.hud_t = self.tip_t = self.light_t = self.ray_t = 0.0
        self.sky_key = None
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
            self.root.bind("<KeyPress-%s>" % k, lambda e: setattr(self, "show_lineage", not self.show_lineage))
        for k in ("r", "R"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_rel)
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

    def _grid_img(self, grid, colors, scale):
        img = self.tk.PhotoImage(width=len(grid[0]), height=len(grid))
        for y, r in enumerate(grid):
            for x, ch in enumerate(r):
                if ch and colors.get(ch):
                    img.put(colors[ch], to=(x, y))
        return img.zoom(scale)

    def make_whale_images(self):
        cols = {"O": "#4f6d94", "S": "#7f9fc6", "W": "#dbe7f2", "g": "#b8cadc", "E": "#2c3e58",
                "P": "#f4b4c4", "F": "#5f80a8", "L": "#c8dcf0", "f": FLESH}
        self.whale_fall_img = self._grid_img(whale_grid(), cols, 3)
        self.skeleton_img = self._grid_img(skeleton_grid(), {"B": BONE, "b": "#c9bf9f"}, 3)
        self.flesh_img = [self._grid_img(whale_body_level(lv), cols, 3) for lv in (1.01, 0.72, 0.48, 0.24)]

    def dumbo_img(self, t, cache, key):
        img = cache.get(key)
        if img is None:
            frame, mode, scale, lit = key
            px = dumbo_pixels(t.g, frame, mode)
            raw = self.tk.PhotoImage(width=len(px[0]), height=len(px))
            k = (1.15,) * 3 if lit else (0.82,) * 3
            for y, row in enumerate(px):
                for x, col in enumerate(row):
                    if col:
                        raw.put(tint_hex(col, k), to=(x, y))
            img = raw.zoom(scale) if scale > 1 else raw
            cache[key] = img
        return img

    # ---- 背景(水の層・海底・岩・深さの目盛り)
    def draw_background(self):
        c, w = self.canvas, self.world
        for it in self.bg_items + self.depth_labels:
            c.delete(it)
        self.bg_items, self.depth_labels = [], []
        fl = w.floor(w.w / 2)
        bands = 16
        for i in range(bands):
            f = i / (bands - 1)
            col = mix(WATER_MID, WATER_DEEP, (f - 0.25) / 0.75) if f > 0.25 else mix(WATER_TOP, WATER_MID, f / 0.25)
            y0 = w.surface + (fl - w.surface) * i / bands
            y1 = w.surface + (fl - w.surface) * (i + 1) / bands + 1
            self.bg_items.append(c.create_rectangle(0, y0, w.w, y1, fill=col, width=0, tags="bg"))
        xs = list(range(0, int(w.w) + 12, 12))
        pts = [v for x in xs for v in (x, w.floor(x))] + [w.w, w.h, 0, w.h]
        self.bg_items.append(c.create_polygon(*pts, fill=FLOOR_COL, outline=FLOOR_LIGHT, width=2, tags="bg"))
        rnd = random.Random(5)
        for _ in range(30):
            x = rnd.uniform(0, w.w)
            y = rnd.uniform(w.floor(x) + 4, w.h - 2)
            self.bg_items.append(c.create_rectangle(x, y, x + 2, y + 1, fill=FLOOR_LIGHT, width=0, tags="bg"))
        for rx, ri in w.rocks:
            self.bg_items.append(c.create_image(rx, w.floor(rx) - 6, image=self.rock_img[ri % 3], tags="bg"))
        for depth in (200, 1000, 2000, 3000):
            f = (depth / 4000.0) ** (1 / 1.6)
            y = w.surface + (fl - w.surface) * f
            self.depth_labels.append(c.create_text(w.w - 6, y, anchor="e", text="%d m" % depth,
                                                   fill="#3f6a8a", font=("", 7), tags="bg"))
            self.depth_labels.append(c.create_line(w.w - 40, y + 6, w.w - 4, y + 6, fill="#1f3a55", tags="bg"))
        self.sky_key = None
        self.order_dirty = True
        self.layout_ui()

    def draw_surface(self):
        """海面の帯: 空の色はパソコンの時計に合わせる。"""
        c, w = self.canvas, self.world
        k = tuple(round(x * 20) / 20 for x in w.tint)
        if k == self.sky_key:
            return
        self.sky_key = k
        for it in self.surface_items:
            c.delete(it)
        sky = tuple(min(255, int(a * m)) for a, m in zip(SKY["day"], k))
        top = tuple(min(255, int(a * m)) for a, m in zip(WATER_TOP, k))
        self.surface_items = [
            c.create_rectangle(0, 0, w.w, w.surface * 0.55, fill=mix(sky, sky, 0), width=0, tags="sky"),
            c.create_rectangle(0, w.surface * 0.55, w.w, w.surface + 1, fill=mix(top, sky, 0.3), width=0, tags="sky"),
            c.create_line(0, w.surface * 0.55, w.w, w.surface * 0.55, fill=mix(sky, (255, 255, 255), 0.5), tags="sky"),
        ]
        for it in self.bg_items[:4]:      # いちばん上の水の色も時間で変える
            f = self.bg_items.index(it) / 15
            c.itemconfigure(it, fill=mix(tuple(min(255, int(a * m)) for a, m in zip(WATER_TOP, k)), WATER_MID, f / 0.25))
        if w.night > 0.5:
            mx = w.w * (0.2 + 0.6 * ((w.hour + 6) % 24) / 24)
            self.surface_items.append(c.create_oval(mx - 4, 1, mx + 4, 8, fill="#f4f0d8", outline="", tags="sky"))
        elif w.phase in ("Daytime", "Sunrise", "Sunset"):
            sx = w.w * (0.1 + 0.8 * min(1.0, max(0.0, (w.hour - 5) / 14)))
            col = "#fff2a0" if w.phase == "Daytime" else "#ffb060"
            self.surface_items.append(c.create_oval(sx - 4, 1, sx + 4, 8, fill=col, outline="", tags="sky"))
        self.order_dirty = True

    def layout_ui(self):
        c, w = self.canvas, self.world
        gx1, gy0 = w.w - 8, w.surface + 54
        gx0, gy1 = gx1 - 236, gy0 + 72
        self.graph_rect = (gx0 + 4, gy0 + 16, gx1 - 4, gy1 - 18)
        c.coords(self.graph_box, gx0, gy0, gx1, gy1)
        c.coords(self.graph_title, gx0 + 4, gy0 + 2)
        for i, it in enumerate(self.graph_legend):
            c.coords(it, gx0 + 4 + (0, 64, 152)[i], gy1 - 15)
        n = len(self.log_items)
        for i, it in enumerate(self.log_items):
            c.coords(it, 8, w.h - 16 - (n - 1 - i) * 14)
        c.coords(self.help, 8, w.h - 2)
        c.coords(self.bann, w.w / 2, w.h * 0.3)
        self.draw_graph()

    # ---- 鯨骨
    def draw_whale(self):
        c, w = self.canvas, self.world
        wh = w.whale
        if wh is None:
            key = None
        elif wh.falling:
            key = ("fall",)
        else:
            lvl = 0 if wh.flesh > 0.75 else 1 if wh.flesh > 0.45 else 2 if wh.flesh > 0.2 else 3 if wh.flesh > 0.02 else 4
            key = ("floor", lvl, wh.stage_index, int(wh.worms))
        if key != self.whale_key:
            self.whale_key = key
            for it in self.whale_items + self.worm_items + self.mat_items:
                c.delete(it)
            self.whale_items, self.worm_items, self.mat_items = [], [], []
            if wh is not None and not wh.falling:
                self.whale_items.append(c.create_image(wh.x, wh.y, image=self.skeleton_img, tags="whale"))
                if key[1] < 4:
                    self.whale_items.append(c.create_image(wh.x, wh.y, image=self.flesh_img[key[1]], tags="whale"))
                rnd = random.Random(11)
                if wh.stage_index >= 2:          # バクテリアマットと二枚貝
                    for i in range(10):
                        x = wh.x + rnd.uniform(-95, 85)
                        y = wh.y + rnd.uniform(22, 30)
                        self.mat_items.append(c.create_rectangle(x, y, x + rnd.uniform(6, 14), y + 2,
                                                                 fill=rnd.choice(("#f4f0e0", "#f0e0a0")), width=0, tags="whale"))
                    for i in range(8):
                        x = wh.x + rnd.uniform(-90, 85)
                        y = wh.y + rnd.uniform(24, 30)
                        self.mat_items.append(c.create_oval(x, y, x + 5, y + 3, fill="#2c2a3a", outline="#5a5870", tags="whale"))
                slots = [(rnd.uniform(-85, 80), rnd.uniform(-18, 10)) for _ in range(30)]
                for dx, dy in slots[:int(wh.worms)]:       # ホネクイハナムシ
                    self.worm_items.append(c.create_image(wh.x + dx, wh.y + dy, image=self.worm_img, tags="whale"))
            elif wh is not None:
                self.whale_items.append(c.create_image(wh.x, wh.y, image=self.whale_fall_img, tags="whale"))
            self.order_dirty = True
        if wh is not None and wh.falling and self.whale_items:
            c.coords(self.whale_items[0], round(wh.x), round(wh.y))

    # ---- 演出
    def add_fx(self, kind, x, y):
        if len(self.fx_items) > 24:
            return
        col = {"glow": "#7ff3ff", "dust": "#7a6e62", "bite": "#ff3434", "snow": "#cfd8e8",
               "halo": "#4f7fa8"}[kind]
        n = 3 if kind == "glow" else 1 if kind == "halo" else 2
        for k in range(n):
            it = self.canvas.create_oval(x, y, x, y, outline=col, width=2 if kind != "snow" else 1, tags="fx")
            self.fx_items.append([it, kind, x, y, -0.25 * k, 2.0 if kind in ("dust", "halo") else 1.0])
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
                r = (40 if kind == "halo" else 2) + t / life * {"glow": 20, "dust": 60, "bite": 22, "snow": 10,
                                                                 "halo": 40}[kind]
                c.coords(it, x - r, y - (r * 0.35 if kind == "dust" else r), x + r, y + (r * 0.2 if kind == "dust" else r))
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
        self.canvas.itemconfigure("light", state="hidden")
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
        elif self.world.surface < y < self.world.floor(x):
            self.world.add_crusts(x, y)

    def on_double(self, e):
        if self.click_job:
            self.root.after_cancel(self.click_job)
            self.click_job = None
        t = self.world.hit(e.x, e.y, pad=6)
        if t:
            self.world.poke(t)

    def on_shift_click(self, e):
        if self.world.surface < e.y < self.world.floor(e.x):
            self.world.drop_foodfall(e.x, e.y)

    def toggle_topmost(self, e=None):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.banner, self.banner_t = ("Always on top: ON" if self.topmost else "Always on top: OFF"), 1.5

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
        self.whale_key = None
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
        if self.root.state() == "iconic":
            self.world.fx.clear()
            self.root.after(1000, self.tick)
            return
        self.render(dt)
        self.root.after(TICK_MS, self.tick)

    def lit(self, x, y):
        cur = self.world.cursor
        return 1 if cur and (x - cur[0]) ** 2 + (y - cur[1]) ** 2 < 70 * 70 else 0

    def render(self, dt):
        c, w = self.canvas, self.world
        self.draw_whale()
        self._sync("crust", w.crusts, lambda o: self.crust_img[self.lit(o.x, o.y)])
        self._sync("lantern", w.lanterns, lambda o: self.lantern_img[1 if o.vx >= 0 else 3])
        self._sync("eggs", w.eggs, lambda o: self.eggs_img, move=False)
        self._sync("foodfall", w.foodfalls, lambda o: self.ff_img)
        self._sync("visitor", w.visitors, lambda v: self.vis_img[(v.kind, v.dir, int(v.anim / 0.4) % 2)])
        seen = set()
        for t in w.dumbos:
            seen.add(t.id)
            ent = self.items.get(t.id)
            if ent is None:
                ent = [c.create_image(t.x, t.y, tags="dumbo"), None, None, {}, None]
                self.items[t.id] = ent
                self.order_dirty = True
            if t.state == "dead":
                key = (0, "dead", t.scale, 0)
            elif t.state == "startled":
                key = (0, "umbrella" if t.glow_t <= 0 or int(t.anim / 0.2) % 2 else "glow", t.scale, 1)
            elif t.state == "brood":
                key = (0, "brood", t.scale, self.lit(t.x, t.y))
            elif t.glow_t > 0:
                key = (int(t.anim / 0.2) % 2, "glow", t.scale, 1)
            elif t.state == "sleep":
                key = (1, "normal", t.scale, self.lit(t.x, t.y))
            else:
                period = 0.25 if t.state in ("flee", "food", "play", "dance") else 0.6
                key = (int(t.anim / period) % 2, "normal", t.scale, self.lit(t.x, t.y))
            if key != ent[4]:
                c.itemconfigure(ent[0], image=self.dumbo_img(t, ent[3], key))
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
                    ent[2] = c.create_text(lx, ly, text=t.lineage, fill="#bfe8ff", font=("", 8, "bold"), tags="fx")
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

        for kind, x, y in w.fx:
            self.add_fx(kind, x, y)
        w.fx.clear()
        self.update_fx(dt)
        # マリンスノー(夜は多い)
        n_snow = int(len(self.snow) * (0.55 + 0.45 * w.night))
        for i, s in enumerate(self.snow):
            it = s[0]
            if i >= n_snow:
                c.itemconfigure(it, state="hidden")
                continue
            s[2] += s[3] * dt
            s[1] += math.sin(w.time * 0.5 + i) * 2 * dt
            if s[2] > w.floor(s[1]):
                s[1], s[2] = random.uniform(0, w.w), w.surface + random.uniform(0, 20)
            c.coords(it, s[1], s[2], s[1] + (2 if i % 5 == 0 else 1), s[2] + 1)
            c.itemconfigure(it, state="normal")
        # 昼の光の筋(有光層だけ)
        self.ray_t -= dt
        if self.ray_t <= 0:
            self.ray_t = 0.5
            day = max(0.0, 1.0 - w.night * 1.4)
            for i, it in enumerate(self.rays):
                if day <= 0.05:
                    c.itemconfigure(it, state="hidden")
                    continue
                x = (i + 0.5) * w.w / len(self.rays) + math.sin(w.time * 0.2 + i) * 20
                c.coords(it, x, w.surface, x - 40, w.h * (0.18 + 0.12 * day))
                c.itemconfigure(it, state="normal", fill=mix(WATER_TOP, (190, 235, 255), 0.12 * day))
        # 潜水艇のライト
        cur = w.cursor
        if cur:
            for r, it in zip((70, 50, 30), self.light):
                c.coords(it, cur[0] - r, cur[1] - r, cur[0] + r, cur[1] + r)
                c.itemconfigure(it, state="normal")
        self.light_t -= dt
        if self.light_t <= 0:
            self.light_t = 5.0
            self.draw_surface()
        if w.phase_msg:
            self.banner, self.banner_t = w.phase_msg, 4.0
            w.phase_msg = None
        if self.show_rel:
            self.draw_relations()
        if self.order_dirty:
            for tag in ("bg", "ray", "sky", "lantern", "snow", "whale", "eggs", "foodfall", "crust",
                        "rel", "dumbo", "visitor", "light", "fx", "ui", "panel", "tip"):
                c.tag_raise(tag)
            self.order_dirty = False

        self.hud_t -= dt
        if self.hud_t <= 0:
            self.hud_t = 1.0
            alive = w.alive()
            nf = sum(t.sex == "F" for t in alive)
            pick = sum(t.picker for t in alive)
            wh = w.whale
            whale_txt = ("Whale: falling" if wh and wh.falling else
                         "Whale fall: %s (%s)" % (wh.stage.replace(" stage", ""), fmt_dur(wh.age)) if wh else "No whale")
            vis = [VIS_NAMES[v.kind] for v in w.visitors]
            c.itemconfigure(self.hud, text=(
                "%s %s (surface)   Dumbos %d (F%d M%d, hunters %d / grazers %d)   Eggs %d   Gen %d\n"
                "%s   Amphipods %d   Bone worms %d   Born %d   Died %d\n%s"
                % (time.strftime("%H:%M", time.localtime(w.now_ts)), w.phase, len(alive), nf, len(alive) - nf,
                   pick, len(alive) - pick, sum(len(e.genomes) for e in w.eggs), w.max_gen,
                   whale_txt, len(w.crusts), int(wh.worms) if wh else 0, w.births, w.deaths,
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

    def draw_relations(self):
        c, w = self.canvas, self.world
        pairs, done = [], set()
        for t in w.alive():
            p = w.by_id.get(t.partner)
            if p and (p.id, t.id) not in done:
                pairs.append((t, p, "#ff7aa8", 2))
                done.add((t.id, p.id))
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
        t = next((x for x in w.dumbos if x.id == self.follow), None)
        if t is None:
            self.follow = None
            c.itemconfigure("panel", state="hidden")
            return
        self.panel_t -= dt
        if self.panel_t <= 0:
            self.panel_t = 0.25
            c.itemconfigure(self.panel_text, text="\n".join(w.dumbo_info(t)), state="normal")
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
        wh = self.world.whale
        cur = (sum(t.alive for t in self.world.dumbos), len(self.world.crusts), round(wh.worms, 1) if wh else 0)
        data = list(h) + [cur]
        names = ("Dumbos %d", "Amphipods %d", "Bone worms %d")
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
            mb.showerror("Whale Fall", msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
