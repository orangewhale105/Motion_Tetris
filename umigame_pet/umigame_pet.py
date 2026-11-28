# -*- coding: utf-8 -*-
"""
Sea Turtle Colony(ウミガメ群体)— デスクトップで動く人工生命の小さなペット

・標準ライブラリだけで動く(tkinter)。pip install 不要。画面の表示は英語。
・上から見た南国の海(ターコイズブルー)と砂浜。サンゴ礁と岩場、熱帯魚、寄せる波。
・ドット絵のウミガメ(インベーダー風)。パステルカラー(水色・ピンク・ミント・レモン・ラベンダー・ピーチ)が基本で、
  まれに濃い色の個体が生まれる。甲羅の模様は 8 種類(無地・水玉・しま・亀甲・リング・まだら・市松・ハート)。
・遺伝的アルゴリズム: 色・模様・速さ・寿命・大きさ・食性(草食/雑食)・性格(活発さ・食欲・カーソルの好き嫌い・
  群れたがり・無頓着さ・気まま・気の短さ)・産卵数。交尾で交叉(スクランブル)+突然変異。系統(Lineage)は母系。
・時間の進み方(Ver 7): カメの時間は実時間の36倍(実時間40分 = カメの1日)。
  大人まで約20時間、寿命は平均4〜5日(カメの時間)。泳ぐ速さ・訪問者の間隔などは実時間。
  夏の日のイメージ(日の出 4:36、日の入り 18:54。カメの時刻)。
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
    カメを長押し         → 識別個体にして名前をつけ、一生をたどる(亡くなると亀生のまとめと死因、子孫を選べる)
    カメをダブルクリック → ひっくり返る(その後、喜ぶか怒る)
    カメの上でカーソルを動かす → なでる(性格しだいで喜ぶ/嫌がる)
    近づける             → 性格に応じて寄ってくる / 嫌がって逃げる / 気にしない
    卵・水草・サンゴ・岩・魚・クラゲ・訪問者に重ねる → 説明を表示
    水を左クリック → クラゲを足す   右クリック(または Shift+クリック) → 海藻を植える
    T キー → 最前面に固定の切り替え   L キー → 系統の文字   R キー → 友達・パートナーの線
・音: 波の音と効果音(標準ライブラリで合成)。砂浜右下のボタンか W / F キーで、それぞれ ON/OFF。
  音量はボタンの左右の −/+ かマウスホイールで、それぞれ 0〜100%。
・閉じると群体を Google ドライブ(パソコン版 Google ドライブの同期フォルダ)に保存。
  次に起動すると、閉じていた時間ぶん(カメの時間で最大30日)群体と生態系の時間を進める。

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

VERSION = "7.4.1"

# ---------------------------------------------------------------- 定数
TICK_MS = 100                 # 画面更新の間隔(10fps)。最小化中は 1秒ごとに計算だけ
MAX_TURTLES = 40              # 安全のための上限(カメ+卵)。普段は餌の量で頭打ちになる
HOUR = 3600.0
TIME_SCALE = 36.0             # カメの時間の進み方: 実時間の40分 = カメの1日(24時間)
# 年齢・寿命・おなかのすき具合・眠気・卵・水草の育ち方・朝昼夕夜 は「カメの時間」で進む。
# 泳ぐ速さ・息継ぎ・アニメーション・波・訪問者の来る間隔(サメ30分など)は実時間のまま。
JUVENILE_AGE = 6 * HOUR       # これより若いと一番小さい姿(カメの時間)
ADULT_AGE = 20 * HOUR         # 大人になる年齢。寿命は平均 4〜5 日、最大 1 か月ほど(カメの時間)
MATE_COOLDOWN = 10 * HOUR     # (旧版の互換用)
FEMALE_MATE_GAP = 1.0 * 24 * HOUR   # メスが次に交尾するまで(本物のウミガメは数年に1度。1回の交尾で何度も産む)
MALE_MATE_GAP = 0.8 * 24 * HOUR     # オスが次に交尾するまで
CLUTCH_GAP = 20 * HOUR        # 1回の交尾の後、次の産卵までの間(精子をたくわえて、交尾なしで産む)
MATING_HOURS = (6.0, 10.0)    # 交尾は朝だけ。1日に 1〜2 ペアまで
COURT_CHANCE = 1 / 10.0       # 相手を探し始める確率(実時間1秒あたり)。のんびり過ごすのが基本
EGG_TIME = 6 * HOUR           # 卵がかえるまで(その後、夜を待ってふ化)
LAY_GAME = 1.5 * 3600         # 産卵にかかる時間(本物のウミガメに合わせて約1時間半、カメの時間)
LAY_TIME = LAY_GAME / TIME_SCALE    # 同じ時間を実時間の秒で(穴を掘る → 涙を流しながら産む → 砂をかける)
NEST_HOURS = (20.0, 3.0)      # 産卵は夜 20時〜翌3時(カメの時刻)
MATING_TIME = 2.0             # 交尾(寄りそってハートが1つ出るだけ。実時間の秒)
HATCH_SHAKE = 3.0             # 卵がゆれてから割れるまで(実時間の秒)
DAY = 86400.0
EGG_COST = 0.05               # 卵1個に母親が使う栄養
HATCH_ENERGY = 0.45           # 子ガメの最初の栄養
MAX_SCALE = 6                 # ドットの拡大率の上限(合体で大きくなる)
MERGE_KIN = 0.12              # この遺伝距離より近い個体どうしが合体候補
CORPSE_TIME = 10.0            # 死骸が残る時間(その後、分解されて近くの水草の栄養になる)
CORPSE_FERTILIZE = 0.25

PLANT_START = 32
N_MEADOWS = 5                 # 水草が群生する藻場の数
MEADOW_R = (26, 40)
PLANT_MAX = 50
ECO = 24.0 / 36.0             # 40分で1日にしたとき、食べる・育つ速さを実時間あたり Ver 6 と同じにする係数
PLANT_GROWTH = 0.00035 * ECO  # 水草のロジスティック成長率(1/秒)
PLANT_MIN = 0.08              # 食べ尽くされても根が残る量
PLANT_EDIBLE = 0.55           # これより小さい株は食べない(半分の大きさから広がれるので、藻場が再生できる)
MEADOW_MAX = 12               # ひとつの藻場の株の数の上限(海じゅうが1つの藻場にならないように)
PLANT_BASE = 0.00003 * ECO     # 根からの再生(1/秒)
CALM = 0.4                   # おなかの減り方(Ver 7.3 で約4割に。食事はたまに、のんびり)
PLANT_NIBBLE = 0.11           # ひとくちで食べる量(水草の絵の1段ぶん。1ドットずつ、のんびり)
NIBBLE_FLOOR = 0.25           # ここまでしか食べない(根と葉が残り、すぐまた育つ)
PLANT_BITE = 0.12             # ひとくち(小さくして、少しずつ減るのが見えるように)
EAT_TIME = 2.0                # ひとくちにかかる時間(もぐもぐ)
PLANT_SCARS = 3              # 根元まで食べられるのがこの回数続くと枯れる(食べ過ぎで藻場が消える)
PLANT_HEAL = 20 * 60         # これだけ食べられなければ、傷が1つ治る
SPROUT_GAP = (2 * 3600, 4 * 3600)  # ひとりでに芽が出る間隔(カメの時間)。食べられなければ育って新しい藻場になる
PLANT_SPREAD = 1 / 60.0        # 茂った水草がすぐ隣に広がる確率(1/秒)→ 群生する
JELLY_INTERVAL = 180.0
JELLY_GROW = 0.12             # クラゲがふえる割合(カメの1時間あたり、ロジスティック)
JELLY_K = 14                  # 海が養えるクラゲの数
JELLY_DIE = 0.01              # 自然に死ぬ確率(カメの1時間あたり)
JELLY_START = 6
JELLY_MAX = 5
JELLY_DROP_MAX = 12
JELLY_ENERGY = 0.40

SHARK_GAP = (25 * 60, 35 * 60)      # 約30分に1回(いちばんまれ)
SHARK_STAY = 70.0
SHARK_PREY_SCALE = 4
SHARK_SIGHT = 140.0
TURTLE_ALERT = 170.0
SHARK_ZONE = 0.6

# 訪問者: 間隔(実時間の秒)・滞在・場所・時間帯ごとの出やすさ(生き物の生態に合わせる)
_N, _DW, _SR, _D, _SS, _DK = "Night", "Dawn twilight", "Sunrise", "Daytime", "Sunset", "Dusk"
VISITORS = {
    "dolphin": {"gap": (15 * 60, 25 * 60), "stay": 90, "zone": "sea", "friendly": True,
                "when": {_D: 1.0, _SR: 0.7, _SS: 0.5}},                         # 昼に遊びに来る
    "manta": {"gap": (12 * 60, 18 * 60), "stay": 110, "zone": "sea", "friendly": True,
              "when": {_D: 0.4, _SS: 0.8, _DK: 1.0, _N: 1.0, _DW: 0.6}},     # 夕方〜夜にプランクトンを食べに
    "coconut": {"gap": (60, 120), "stay": 45, "zone": "beach", "when": {_N: 1.0, _DK: 0.4}},
    "hermit": {"gap": (40, 80), "stay": 45, "zone": "beach", "night_max": 3,
               "when": {_N: 1.0, _DK: 0.8, _DW: 0.8, _D: 0.25, _SR: 0.4, _SS: 0.4}},
    # 夜行性の生き物
    "ghost": {"gap": (25, 50), "stay": 35, "zone": "beach", "max": 3,
              "when": {_N: 1.0, _DW: 1.0, _DK: 0.7, _SR: 0.5, _D: 0.1}},
    "octopus": {"gap": (150, 300), "stay": 140, "zone": "reef", "when": {_N: 1.0, _DK: 0.8, _DW: 0.8, _D: 0.15}},
    "comb": {"gap": (40, 90), "stay": 160, "zone": "sea", "max": 3, "when": {_N: 1.0, _DK: 0.4}},
    "moray": {"gap": (90, 180), "stay": 120, "zone": "rock", "max": 2, "when": {_N: 1.0, _DK: 0.6, _DW: 0.5, _D: 0.1}},
    "squid": {"gap": (120, 240), "stay": 70, "zone": "sea", "max": 5, "when": {_N: 1.0, _DK: 0.5}},
    # 海鳥(昼。子ガメが浜にいると狙いに来る)
    "bird": {"gap": (6 * 60, 12 * 60), "stay": 50, "zone": "air", "when": {_SR: 1.0, _D: 0.6, _SS: 0.8}},
}
SHARK_WHEN = {_N: 1.0, _DK: 1.0, _SS: 0.8, _DW: 0.8, _SR: 0.5, _D: 0.35}    # サメは夕方〜夜に多い
VIS_NAMES = {"dolphin": "dolphin", "manta": "manta ray", "coconut": "coconut crab", "hermit": "hermit crab",
             "ghost": "ghost crab", "octopus": "octopus", "comb": "comb jelly", "moray": "moray eel",
             "squid": "squid", "bird": "frigatebird"}
SHARK_KINDS = ("Tiger shark", "Bull shark", "Blacktip reef shark", "Hammerhead")
LUCKY_RATE = 0.1              # 運のよい個体の割合(実時間で1週間ほど生きる)
IMMIGRANT_GAP = (45 * 60, 90 * 60)   # (旧版の互換用。今は IMMIGRANT_RATE を使う)
IMMIGRANT_RATE = 1.0          # 外来ガメが来る頻度: カメの1日あたり 1/(今いる数+1) 回
FOOD_TO_BREED = 1.0           # 1匹あたりの食べられる海藻がこれより少ないと、恋をしない(増えすぎを防ぐ)
POP_TARGET = 8                # ふだんのカメの数(ホメオスタシス: 少ないと子が多く、多いと少ない)
COLONY_SOFT = 13              # これより多いと(卵も数えて)恋をしない
COLONY_CROWD = 18             # これより多いと、ごくまれに旅立つカメが出る
EMIGRATE_FOOD = 1.1           # 1匹あたりの食べられる海藻がこれを下回ると、旅立つカメが出る
EMIGRATE_RATE = 0.06          # 旅立ちの起こりやすさ(カメの1時間・1匹あたり、最大)
EMIGRATE_MIN = 6              # これより少ないときは旅立たない
CRISIS_DAYS = 1000.0          # 絶滅の危機(嵐・赤潮・伝染病・不作)はカメの約1000日(実時間で約1か月)に1度。2匹ほどまで減る
CRISIS_MIN_DAYS = 300.0       # 危機と危機の間は最低これだけあく(実時間で約8日)
CRISIS_FATAL = 1.0 / 6.0      # 危機のうち全滅してしまう割合(実時間でおよそ半年に1度の絶滅)
SICK_RATE = 0.018             # 病気になる確率(カメの1時間あたり、混み合いや空腹で上がる)
VISIT_LOG_GAP = 900           # よく来る訪問者は、イベント欄には5分に1回だけ書く
BIG_WAVE_GAP = (15 * 60, 40 * 60)
N_WAVES = 8
N_SCHOOLS = 3
FISH_PER_SCHOOL = 6
FRIEND_AFF = 1.0              # この親しさ以上で友達

BREATH_GAP = (180, 480)
SLEEP_METAB = 0.08            # 眠っている間の代謝(起きている時の割合)。満腹なら一晩眠れる
BREATH_TIME = 3.0
PET_STROKE = 60.0

SUNRISE = 4.6                 # 夏の日のイメージ(4:36)
SUNSET = 18.9                 # (18:54)

OFFLINE_STEP = 600.0          # 留守中の計算の刻み(カメの時間で10分)
OFFLINE_MAX = 30 * 24 * 3600  # 留守中に進めるのはカメの時間で最大30日(実時間で20時間)
HISTORY_DT = 120.0            # グラフ: 実時間2分(カメの48分)ごと、2日分
HISTORY_LEN = 72
AUTOSAVE_SEC = 300
SAVE_NAME = "colony.json"

FLOAT_GENES = ("hue", "hue2", "speed", "life", "size", "diet",
               "activity", "appetite", "cursor", "flock", "care", "whim",
               "temper", "fertility", "style", "dark",
               "surf", "watch", "depth", "flirt", "clumsy", "nap", "drift")
# 性格の遺伝子(イベントの起こりやすさ): surf=波乗り好き watch=ほかの生き物の観察好き
# depth=浅瀬好き(1)〜沖合好き(0) flirt=メスを追いかけ回す(オス) clumsy=おっちょこちょい
# nap=昼寝好き drift=泳がずにただようのが好き
HOBBIES = ("surf", "watch", "nap", "drift")   # 「趣味」の遺伝子。多くのカメは、どれか1つがとても強い
PATTERN_BITS = 28

PASTEL = (0.55, 0.93, 0.38, 0.14, 0.76, 0.06)     # 水色・ピンク・ミント・レモン・ラベンダー・ピーチ
PASTEL_NAMES = ("sky blue", "pink", "mint", "lemon", "lavender", "peach")
STYLES = ("plain", "polka dots", "stripes", "tortoiseshell", "ring", "mottled", "checker", "heart")


# ---------------------------------------------------------------- 遺伝子
def random_genome(rng=random):
    g = {k: rng.random() for k in FLOAT_GENES}
    g["dark"] = rng.random() ** 3          # 濃い色(>0.9)はまれ
    # のんびり気ままが基本: 怒りっぽい・おっちょこちょい・追いかけ回す個体は少なめ
    g["temper"] = rng.random() ** 1.6
    g["clumsy"] = rng.random() ** 2
    g["flirt"] = rng.random() ** 2.5
    for k in HOBBIES:                      # 趣味: 1つがとても強い個体が多い(波乗りばかり・昼寝ばかり…)
        g[k] = rng.random() * 0.55
    if rng.random() < 0.75:
        g[rng.choice(HOBBIES)] = rng.uniform(0.8, 1.0)
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
    a, b = (x if all(k in x for k in FLOAT_GENES) else fill_genome(x) for x in (a, b))
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
    if g.get("surf", 0) > 0.7:
        out.append("Surf lover")
    if g.get("watch", 0) > 0.7:
        out.append("Naturalist")
    if g.get("depth", 0.5) > 0.75:
        out.append("Shallows lover")
    elif g.get("depth", 0.5) < 0.25:
        out.append("Offshore lover")
    if g.get("flirt", 0) > 0.7:
        out.append("Flirt")
    if g.get("clumsy", 0) > 0.7:
        out.append("Clumsy")
    if g.get("nap", 0) > 0.7:
        out.append("Napper")
    if g.get("drift", 0) > 0.7:
        out.append("Drifter")
    return out


TRAIT_JOKES = {   # クリックしたときの、ちょっとユーモラスな性格の説明
    "Sleepyhead": "Can fall asleep in the middle of a yawn",
    "Energetic": "Has never sat still in its life",
    "Big eater": "Thinks about seaweed 90% of the time",
    "Light eater": "Two bites and it's stuffed",
    "Carefree": "Nothing bothers it. Not even sharks. (It should.)",
    "Cursor lover": "Follows your mouse like a puppy",
    "Cursor shy": "Pretends you are not there",
    "Schooler": "Gets lonely after 3 seconds alone",
    "Loner": "Please respect its personal space",
    "Middle-of-the-road": "Friendly, but not too friendly",
    "Free spirit": "Goes wherever the current feels like",
    "Short-tempered": "Do not poke. Seriously.",
    "Easygoing": "Would smile at a shark",
    "Surf lover": "Lives for the next big wave",
    "Naturalist": "Stares at every crab and octopus for ages",
    "Shallows lover": "Likes to feel the sand under its belly",
    "Offshore lover": "Dreams of the open ocean",
    "Flirt": "Chases every female in sight (they are not impressed)",
    "Clumsy": "Trips over its own flippers",
    "Napper": "Its main hobby is napping. Its second hobby is also napping",
    "Drifter": "Why swim when the sea can carry you?",
}


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
    if is_dark(g):
        return "pearl white" if g["hue2"] > 0.5 else "golden"
    return "pastel " + n


def roman(n):
    out = ""
    for v, sym in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += sym
            n -= v
    return out


def dt_chance(rate_per_hour, hours):
    """1時間あたり rate の確率のことが、hours 時間のうちに起きる確率。"""
    return 1.0 - (1.0 - min(0.999, rate_per_hour)) ** max(0.0, hours)


def lineage_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = string.ascii_uppercase[r] + s
    return s


# ---------------------------------------------------------------- 昼と夜(パソコンの時計に合わせる)
TINTS = {"night": (0.26, 0.33, 0.56), "twilight": (0.62, 0.48, 0.70), "sunrise": (1.22, 0.60, 0.48),
         "day": (1.00, 1.00, 1.00), "noon": (1.04, 1.04, 1.0), "sunset": (1.32, 0.50, 0.34),
         "dusk": (0.62, 0.36, 0.58)}            # 朝焼け・夕焼けは真っ赤に
PHASE_MSG = {
    "Dawn twilight": "Dawn twilight - the sky is getting lighter",
    "Sunrise": "Sunrise! The sea is burning red - the turtles wake up",
    "Daytime": "Daytime - turtles eat, rest at the reef and get cleaned",
    "Sunset": "Sunset - the whole sea glows crimson. Time for an evening snack",
    "Dusk": "Dusk - turtles gather and head for their beds",
    "Night": "Moonlit night - the sea sparkles silver; night creatures come out",
}


def turtle_clock(real_ts):
    """実時刻 → カメの時刻(UNIX時間の形)。40分で1日: 0:00, 0:40, 1:20 … がカメの0:00、その20分後が正午。"""
    lt = time.localtime(real_ts)
    sec = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec + (real_ts % 1)
    midnight = real_ts - sec
    return midnight + (sec * TIME_SCALE) % 86400


def real_for_turtle(day_ts, hour, minute=0):
    """テスト用: その日のうち、カメの時刻が hour:minute になる実時刻。"""
    lt = time.localtime(day_ts)
    midnight = day_ts - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec)
    return midnight + (hour * 3600 + minute * 60) / TIME_SCALE


def sun_times(ts=None):
    """日の出・日の入り(時)。夏の日をイメージした固定の時刻。"""
    return SUNRISE, SUNSET


def daylight(ts):
    """(時間帯の名前, 夜らしさ 0〜1, 色み, 時刻[時]) を返す。"""
    lt = time.localtime(ts)
    h = lt.tm_hour + lt.tm_min / 60.0 + lt.tm_sec / 3600.0
    sr, ss = sun_times(ts)
    keys = [(sr - 1.0, "night"), (sr - 0.5, "twilight"), (sr - 0.1, "sunrise"), (sr + 0.6, "sunrise"),
            (sr + 1.4, "day"), (12.5, "noon"), (ss - 1.4, "day"), (ss - 0.6, "sunset"), (ss + 0.2, "sunset"),
            (ss + 0.7, "dusk"), (ss + 1.3, "night")]      # 真っ赤な時間を長めに
    tint = TINTS["night"]
    for (h0, a), (h1, b) in zip(keys, keys[1:]):
        if h0 <= h < h1:
            f = (h - h0) / (h1 - h0)
            tint = tuple(x + (y - x) * f for x, y in zip(TINTS[a], TINTS[b]))
            break
    if h < sr - 1.0 or h >= ss + 1.2:
        phase = "Night"
    elif h < sr - 0.2:
        phase = "Dawn twilight"
    elif h < sr + 1.0:
        phase = "Sunrise"
    elif h < ss - 0.9:
        phase = "Daytime"
    elif h < ss + 0.4:
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
        self.g = genome if all(k in genome for k in FLOAT_GENES) else fill_genome(genome)   # 旧版の卵など
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
        self.lucky = random.random() < LUCKY_RATE
        # 寿命(カメの時間): ふつうは 2.5〜6.5 日(平均 4〜5 日)、運のよい個体は 15〜30 日
        self.lucky_life = (random.uniform(15, 30) if self.lucky else
                           (2.5 + 4.0 * genome.get("life", 0.5)) * random.uniform(0.6, 1.4)) * DAY
        self.groggy = 0.0         # 寝ぼけている時間(実時間)
        self.mate_with = None
        self.dash_t = random.uniform(0, 8)
        self.origin = "native"    # native / 外から来た群れの名前
        self.watching = None
        self.sick = 0.0           # 病気の重さ(0 = 元気)
        self.name = None          # 識別個体の名前(長押しでつける)
        self.mom = self.dad = None
        self.stats = {"plants": 0, "jelly": 0, "kids": 0, "mates": 0, "surf": 0, "wipe": 0,
                      "clean": 0, "escape": 0, "sick": 0, "born": 0.0}

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
        return self.lucky_life * (1 + 0.2 * self.extra)

    @property
    def metab(self):
        g = self.g
        return (0.00012 + 0.00015 * g["appetite"] + 0.00008 * g["speed"]
                + 0.00005 * g["activity"]) * (1 + 0.15 * self.extra) * (1.0 if self.adult else 0.6) * ECO * CALM

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
                "pets": self.pets, "lucky": self.lucky, "lucky_life": self.lucky_life, "sick": self.sick,
                "origin": self.origin, "stored": getattr(self, "stored", None),
                "name": self.name, "mom": self.mom, "dad": self.dad, "stats": self.stats}

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
        t.lucky = d.get("lucky", t.lucky)
        t.lucky_life = min(d.get("lucky_life", t.lucky_life), 30 * DAY)
        t.origin = d.get("origin", "native")
        t.stored = d.get("stored")
        t.sick = d.get("sick", 0.0)
        t.name = d.get("name")
        t.mom, t.dad = d.get("mom"), d.get("dad")
        t.stats.update(d.get("stats", {}))
        if d.get("sleep"):
            t.state = "sleep"
        return t


class Egg:
    def __init__(self, genome, x, y, generation, lineage, parents, t=EGG_TIME, sex=None, mom=None, dad=None):
        self.g, self.x, self.y = genome, x, y
        self.generation, self.lineage, self.parents = generation, lineage, parents
        self.t, self.sex = t, sex
        self.mom, self.dad = mom, dad

    def to_dict(self):
        return {"g": self.g, "x": self.x, "y": self.y, "gen": self.generation,
                "lin": self.lineage, "par": self.parents, "t": self.t, "sex": self.sex,
                "mom": self.mom, "dad": self.dad}

    @classmethod
    def from_dict(cls, d):
        return cls(fill_genome(d["g"]), d["x"], d["y"], d.get("gen", 1), d.get("lin", "A"),
                   d.get("par", ""), d.get("t", EGG_TIME), d.get("sex"), d.get("mom"), d.get("dad"))


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


def reef_spread(kind, n):
    """岩場・サンゴ礁の広がり。岩場は 4 匹ほどが並んで休めるくらい広い(Ver 7.3)。"""
    return (20 + 4.2 * n) if kind == "coral" else (30 + 7.0 * n)


class Reef:
    """サンゴ礁(coral)と岩場(rock)。カメの寝床、熱帯魚のすみか、クリーニングの場所。"""

    def __init__(self, x, y, kind, seed, parts=None, drift=None, n=None):
        self.x, self.y, self.kind, self.seed = x, y, kind, seed
        rnd = random.Random(seed)
        if n is None:
            n = rnd.randint(6, 9) if kind == "coral" else rnd.randint(3, 4)
        r = reef_spread(kind, n)                                  # 部品が多いほど大きい
        self.drift = drift if drift is not None else rnd.uniform(0, math.tau)
        self.parts = []           # (dx, dy, 部品の種類, 色の番号)
        for i in range(n):
            a = rnd.uniform(0, math.tau)
            d = rnd.uniform(0, r) if i else 0
            if kind == "coral":
                piece = rnd.choice(("branch", "branch", "brain", "fan", "table"))
            else:
                piece = rnd.choice(("rock1", "rock2"))
            self.parts.append((math.cos(a) * d, math.sin(a) * d * 0.75, piece, rnd.randrange(4)))
        if parts:
            self.parts = [tuple(p) for p in parts]
        self.radius = r + 8
        self.recenter()

    def recenter(self):
        """サンゴの部品の重心を中心にする(サンゴが育ったり減ったりすると、少しずつ移動する)。"""
        if not self.parts:
            return
        mx = sum(p[0] for p in self.parts) / len(self.parts)
        my = sum(p[1] for p in self.parts) / len(self.parts)
        self.x += mx
        self.y += my
        self.parts = [(p[0] - mx, p[1] - my, p[2], p[3]) for p in self.parts]
        far = max(math.hypot(p[0], p[1] / 0.75) for p in self.parts)
        self.radius = max(30.0, far + 20)

    def bed_point(self):
        a = random.uniform(0, math.tau)                    # 岩やサンゴの上やまわり
        d = random.uniform(self.radius * 0.15, self.radius * 0.85)
        return self.x + math.cos(a) * d, self.y + math.sin(a) * d * 0.8

    def to_list(self):
        return [self.x, self.y, self.kind, self.seed, [list(p) for p in self.parts], self.drift]


class Shark:
    kind = "shark"

    def __init__(self, x, y, vx, name="Shark"):
        self.name = name
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
        self.vy = 0.0
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
        self.eaten_plants = 0
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
        self.clock = time.time    # テストでは差し替える(実時刻)
        self.bio_time = 0.0       # カメの時間の累計(秒)
        self.phase, self.night, self.tint, self.hour = daylight(turtle_clock(self.clock()))
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
        self.family = {}          # 子 → (母, 父)
        self.kids = {}            # 親 → 生まれた子の数
        self.memorials = []       # 識別個体が亡くなったときのまとめ(描画側が表示する)
        self.trend, self.trend_said, self.deaths_starve = [], {}, 0
        self.reef_changed = False
        self.immigrant_t = 0.0
        self.crisis_t = random.uniform(CRISIS_MIN_DAYS, CRISIS_DAYS * 1.5) * DAY   # 次の危機まで(カメの時間)
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
        for _ in range(JELLY_START):
            x, y = self.water_point(30)
            self.jellies.append(Jelly(x, y, random.choice((-4, 4))))

    def seed_reefs(self):
        """開始時: 岩場は 大(岩8個)・中・小 と、サメの来る沖合に小を1つ。サンゴ礁は4つ。どれもランダムな位置。"""
        lt = self.land_top
        self.reefs = []

        def place(kind, n, y_lo, y_hi, x_hi=None):
            r0 = reef_spread(kind, n) + 12
            for _ in range(200):
                x = random.uniform(r0 + 15, (x_hi or self.w) - r0 - 15)
                y = random.uniform(lt * y_lo, lt * y_hi)
                if x + r0 > self.w - 230 and y - r0 < 130:             # 右上のグラフの下は避ける
                    continue
                if all(math.hypot(o.x - x, o.y - y) > o.radius + r0 + 18 for o in self.reefs):
                    break
            self.reefs.append(Reef(x, y, kind, random.randrange(10 ** 6), n=n))
        place("rock", 3, 0.08, 0.22, self.w - 230)           # 沖合の小さな岩場(右上のグラフの下は避ける)
        for n in (8, 5, 3):                                  # 大・中・小
            place("rock", n, 0.3, 0.85)
        for _ in range(4):
            place("coral", random.randint(7, 10), 0.25, 0.85)
        self.seed_fish()

    def seed_fish(self):
        """熱帯魚: サンゴ礁ごとに群れがあり、数はサンゴの大きさに比例する。"""
        self.schools, self.fish = [], []
        for r in self.reefs:
            if r.kind == "coral":
                s = School(r, random.choice(("yellow", "blue", "clown")))
                self.schools.append(s)
                for _ in range(self.fish_target(r)):
                    self.fish.append(Fish(s, r.x + random.uniform(-20, 20), r.y + random.uniform(-15, 15)))

    @staticmethod
    def fish_target(r):
        return max(1, int(round(len(r.parts) * 0.6)))

    def _fish_population(self):
        """サンゴの増減に合わせて、熱帯魚も少しずつ増えたり減ったりする(遺伝子なし)。"""
        corals = [r for r in self.reefs if r.kind == "coral"]
        have = {id(s.home): s for s in self.schools}
        for r in corals:                                      # 新しいサンゴには新しい群れ
            if id(r) not in have:
                s = School(r, random.choice(("yellow", "blue", "clown")))
                self.schools.append(s)
                have[id(r)] = s
        for s in list(self.schools):
            members = [f for f in self.fish if f.school is s]
            alive_home = s.home in corals
            target = self.fish_target(s.home) if alive_home else 0
            if len(members) < target and random.random() < 0.5:
                self.fish.append(Fish(s, s.home.x + random.uniform(-15, 15), s.home.y + random.uniform(-10, 10)))
            elif len(members) > target and members and random.random() < 0.5:
                f = random.choice(members)
                self.fish.remove(f)
            if not alive_home and not members:
                if s.cleaning is not None:
                    s.cleaning.state = "swim"
                self.schools.remove(s)

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
        if getattr(t, "name", None):
            return "%s #%d (%s)" % (t.name, t.id, t.lineage)
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

    def nest_time(self):
        """産卵に上陸する時間帯(夜 20 時〜翌 3 時)。"""
        a, b = NEST_HOURS
        return self.hour >= a or self.hour < b

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
        bdt = dt * TIME_SCALE                 # カメの時間
        self.time += dt
        self.bio_time += bdt
        self.update_daylight(turtle_clock(self.clock()))
        self._grow_plants(bdt, dt)
        self._jellies(dt, bdt)
        self._waves(dt)
        self._fish_step(dt)
        self._visitors_step(dt)
        self._shark_step(dt)
        self._immigrants(bdt)
        self._hatch(bdt, dt)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        self._food_per = self.edible_food() / max(1, len(alive))   # 1匹あたりの海藻(少ないと恋をしない)
        self.by_id = {t.id: t for t in alive}
        self._neighbors(alive, dt)
        for t in list(self.turtles):
            self._update_turtle(t, dt, bdt)
        self._pairs(alive, dt)
        self._decompose()
        self._crisis(bdt)
        self._emigrate(bdt)
        self._decay_aff(dt)
        self._coral_step(bdt)
        self._trends()
        self._record(dt)

    # ---- 生態系
    def _grow_plants(self, dt, real_dt=None):
        """dt はカメの時間。"""
        real_dt = dt / TIME_SCALE if real_dt is None else real_dt
        new, dead = [], []
        for p in self.plants:
            p.b += (PLANT_GROWTH * p.b + PLANT_BASE) * (1 - p.b) * dt
            p.b = min(1.0, max(PLANT_MIN, p.b))
            p.age += dt
            if p.scars >= PLANT_SCARS or p.age > p.life:       # 食べられ過ぎ・寿命で枯れる
                dead.append(p)
                if p.age > p.life:                           # 寿命: すぐそばに芽を残す(藻場はゆっくり移動しながら続く)
                    a = random.uniform(0, math.tau)
                    x, y = p.x + math.cos(a) * 12, p.y + math.sin(a) * 9
                    if self.in_water(x, y + 10) and self._free_spot(x, y):
                        new.append(Plant(x, y, 0.2, p.m))
                continue
            if p.scars and self.bio_time - p.scar_t > PLANT_HEAL:
                p.scars -= 1
                p.scar_t = self.time
            m = self.meadows.get(p.m)
            if (p.b > NIBBLE_FLOOR + 0.15 and len(self.plants) + len(new) < PLANT_MAX and (m is None or m["n"] < MEADOW_MAX)
                    and random.random() < min(1.0, dt * PLANT_SPREAD)):
                for _ in range(6):                           # すぐ隣へ。藻場の「進む向き」に広がりやすい
                    a = (m["dir"] + random.gauss(0, 1.1)) if m and random.random() < 0.65 else random.uniform(0, math.tau)
                    d = random.uniform(10, 17)
                    x, y = p.x + math.cos(a) * d, p.y + math.sin(a) * d * 0.75
                    crowd = sum(1 for q in self.plants if (q.x - x) ** 2 + (q.y - y) ** 2 < 22 * 22)
                    if crowd < 5 and self._free_spot(x, y) and all((q.x - x) ** 2 + (q.y - y) ** 2 > 100 for q in new):
                        new.append(Plant(x, y, 0.12, p.m))
                        p.b -= 0.1
                        if m:
                            m["n"] += 1
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
        self.meadow_t -= real_dt
        if self.meadow_t <= 0 or dead:
            self.meadow_t = 5.0
            self._update_meadows()

    def _jellies(self, dt, bdt=None):
        """クラゲ: 海の中をただよい、ふえたり(分裂)死んだりする。外からは来ないので、
        カメが食べ過ぎると絶滅することも(水をクリックして足す)。"""
        bdt = dt * TIME_SCALE if bdt is None else bdt
        h = bdt / HOUR
        n = len(self.jellies)
        born = JELLY_GROW * n * max(0.0, 1 - n / JELLY_K) * h
        k = int(born) + (random.random() < born - int(born))
        for j in random.sample(self.jellies, min(k, n)):
            self.jellies.append(Jelly(j.x + random.uniform(-10, 10), j.y + random.uniform(-8, 8), -j.vx))
        keep = []
        for j in self.jellies:
            if random.random() < JELLY_DIE * h:
                continue
            j.phase += dt
            j.vx += random.gauss(0, 2) * dt
            j.vx = max(-6, min(6, j.vx))
            j.x += j.vx * dt
            j.y += math.sin(j.phase * 0.8) * 4 * dt
            if j.x < 10 or j.x > self.w - 10:
                j.vx = -j.vx
                j.x = min(max(10, j.x), self.w - 10)
            j.y = min(max(10, j.y), self.shore(j.x) - 12)
            if not j.gone:
                keep.append(j)
        self.jellies = keep

    def _jellies_offline(self, dt):
        """留守中のクラゲの増減(数だけ)。dt はカメの時間。"""
        h = dt / HOUR
        n = len(self.jellies)
        n2 = n + JELLY_GROW * n * max(0.0, 1 - n / JELLY_K) * h - JELLY_DIE * n * h
        n2 = int(n2) + (random.random() < n2 - int(n2))
        while len(self.jellies) < n2:
            x, y = self.water_point(30)
            self.jellies.append(Jelly(x, y, random.choice((-4, 4))))
        del self.jellies[max(0, n2):]

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
        """遊び好き(波乗りが好き): 遺伝子 surf が中心。活発・気ままなカメも。"""
        g = t.g
        return g["surf"] > 0.55 or (g["whim"] > 0.6 and g["activity"] > 0.6) or (t.joy > 0.7 and g["surf"] > 0.4)

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
                                  and random.random() < (0.6 if wv.big else 0.05 + 0.5 * max(0.0, g["surf"] - 0.7))):
            t.state, t.surf = "surf", wv               # 波に乗って岸へ向かう
            t.stats["surf"] += 1
            end = self.land_top - 4 if wv.big else self.shore(t.x) - 6
            # たいていは途中でワイプアウト(岸まで乗り切れるのは4匹に1匹くらい)
            # おっちょこちょいほどワイプアウトしやすい
            t.wipe_at = None if random.random() < 0.35 - 0.3 * t.g["clumsy"] else \
                random.uniform(t.y + 12, max(t.y + 14, end - 8))
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
    def _immigrants(self, bdt, offline=False, force=False):
        """遠くの海から別の系統のカメがやって来る。来やすさは今いる数に反比例(カメの1日あたり 1/(数+1) 回)。
        絶滅したら 1 日ほどで 1 匹、3 日ほどでペアになれるくらい。bdt はカメの時間。"""
        alive = [t for t in self.turtles if t.alive]
        pop = len(alive) + len(self.eggs)
        if pop >= MAX_TURTLES - 1:
            return
        nf = sum(t.sex == "F" for t in alive)
        nm = len(alive) - nf
        boost = 2.0 if pop < 3 else 1.0
        if alive and (nf == 0 or nm == 0) and pop < POP_TARGET:
            boost = 6.0                                          # オスだけ・メスだけ: すぐに相手がやって来る
        if not force and random.random() >= IMMIGRANT_RATE * boost * bdt / DAY / (pop + 1):
            return
        sex = "F" if nf < nm else "M" if nm < nf else random.choice("FM")   # 少ない方の性
        if offline:
            x, y = self.water_point(30)
        else:
            left = random.random() < 0.5
            x, y = (12 if left else self.w - 12), random.uniform(20, self.land_top * 0.6)
        self.n_groups = getattr(self, "n_groups", 0) + 1
        group = "Wanderers %s" % roman(self.n_groups)          # やって来るたびに別の群れ
        day = int(self.bio_time // DAY) + 1
        lin = self.new_lineage()
        n = 1 if pop < 6 else random.choice((1, 1, 1, 2))
        for i in range(n):
            g = mutate(random_genome(), rate=0.0)
            sx = sex if i == 0 else ("M" if sex == "F" else "F")
            self._make_immigrant(g, x + i * 12 * (1 if x < self.w / 2 else -1), y + i * 10, sx, lin, group, day)
        self.event("visitor", "%s: %d young turtle%s (Lineage %s) arrived from far away!" % (
            group, n, "s" if n > 1 else "", lin))

    def _make_immigrant(self, g, x, y, sex, lin, group, day):
        t = Turtle(g, x, y, 1, sex=sex, lineage=lin, parents="arrived from far away")   # 外来個体は Gen 1
        t.origin = "%s|%d" % (group, day)
        t.age = ADULT_AGE * random.uniform(0.7, 1.15)           # 大人になるかならないかの若い個体
        t.energy = 0.8
        t.mate_cd = 0.0
        t.stats["born"] = self.bio_time - t.age
        t.heading = 0.0 if x < self.w / 2 else math.pi
        t.say("sparkle", 2.5)
        self.turtles.append(t)
        return t

    def _visitors_step(self, dt):
        for kind, cfg in VISITORS.items():
            self.vis_t[kind] -= dt
            n_now = sum(1 for v in self.visitors if v.kind == kind)
            limit = cfg.get("night_max", 1) if self.night > 0.6 else cfg.get("max", 1)
            if self.vis_t[kind] > 0 or n_now >= limit:
                continue
            if random.random() > cfg["when"].get(self.phase, 0.0):   # 時間帯による出やすさ
                self.vis_t[kind] = 60.0
                continue
            self.vis_t[kind] = random.uniform(*cfg["gap"]) * (0.4 if self.night > 0.6 and kind == "hermit" else 1.0)
            self._spawn_visitor(kind)
        keep = []
        for v in self.visitors:
            self._move_visitor(v, dt)
            if not v.gone:
                keep.append(v)
        self.visitors = keep

    def _spawn_visitor(self, kind):
        left = random.random() < 0.5
        zone = VISITORS[kind]["zone"]
        if kind == "squid":                                  # イカの群れ
            y = random.uniform(30, self.land_top * 0.55)
            lead = Visitor(kind, -30 if left else self.w + 30, y, 26 if left else -26)
            self.visitors.append(lead)
            lead.flavor_t = 1e9
            for i in range(random.randint(2, 4)):
                f = Visitor(kind, lead.x - (i + 1) * 14 * (1 if left else -1), y + random.uniform(-14, 14), lead.vx)
                f.leader, f.off = lead, (f.x - lead.x, f.y - lead.y)
                f.flavor_t = 1e9
                self.visitors.append(f)
            if self.time - self.vis_log.get(kind, -1e9) > VISIT_LOG_GAP:
                self.vis_log[kind] = self.time
                self.event("visitor", "A school of squid darted past in the moonlight")
            return
        if zone == "rock":                                   # ウツボ: 岩の穴から顔を出す
            rocks = [r for r in self.reefs if r.kind == "rock"] or self.reefs
            if not rocks:
                return
            r = random.choice(rocks)
            a = random.uniform(0, math.tau)
            v = Visitor(kind, r.x + math.cos(a) * r.radius * 0.6, r.y + math.sin(a) * r.radius * 0.4,
                        random.choice((-1, 1)))
            v.home = r
            self.visitors.append(v)
            v.flavor_t = random.uniform(15, 50)
            if self.time - self.vis_log.get(kind, -1e9) > VISIT_LOG_GAP:
                self.vis_log[kind] = self.time
                self.event("visitor", "A moray eel is peeking out of the rocks")
            return
        if zone == "air":                                    # 海鳥(グンカンドリ)
            self._spawn_bird()
            return
        if zone == "reef":                                   # タコ: 岩場からそっと出てくる
            r = random.choice(self.reefs) if self.reefs else None
            x, y = (r.x, r.y) if r else self.water_point(40)
            v = Visitor(kind, x, y, random.choice((-6, 6)))
            v.home = r
            msg = "An octopus crept out of the reef under the moonlight"
        elif zone == "sea":
            y = random.uniform(30, self.land_top * 0.7)
            sp = {"dolphin": 55, "comb": 5}.get(kind, 16)
            v = Visitor(kind, -40 if left else self.w + 40, y, sp if left else -sp)
            if kind == "comb":
                v.x = random.uniform(40, self.w - 40)
            msg = {"dolphin": "A dolphin came to visit!", "manta": "A manta ray is gliding by",
                   "comb": "Glowing comb jellies drift by, flashing rainbow lights"}[kind]
        else:
            sx = random.uniform(40, self.w - 40)
            sh = self.shore(sx)
            y = sh + (self.h - sh) * random.uniform(0.18, 0.32)    # 砂浜の上の方(表示と重ならない)
            sp = 40 if kind == "ghost" else 9
            v = Visitor(kind, -15 if left else self.w + 15, y, sp if left else -sp)
            if kind == "ghost":                              # スナガニ: 巣穴から出てくる
                v.x = random.uniform(30, self.w - 30)
                self.fx.append(("dust", v.x, v.y))
            msg = {"hermit": "A hermit crab is walking on the beach",
                   "coconut": "A coconut crab came out on the night beach",
                   "ghost": "Ghost crabs are scurrying across the night beach"}[kind]
        self.visitors.append(v)
        v.flavor_t = random.uniform(15, 50)
        if self.time - self.vis_log.get(kind, -1e9) > (VISIT_LOG_GAP if kind in ("hermit", "coconut", "ghost", "comb")
                                                       else 120):
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
        if v.kind == "bird":
            v.anim += dt
            self._move_bird(v, dt)
            return
        if v.kind == "squid":                                 # イカ: すいっ、すいっと進む
            ld = getattr(v, "leader", None)
            if ld is not None:
                v.vx = ld.vx
                v.x, v.y = ld.x + v.off[0], ld.y + v.off[1] + math.sin(v.t * 3 + v.off[1]) * 2
                v.gone = ld.gone
                return
            v.x += v.vx * dt * (1.6 if int(v.t * 1.5) % 2 else 0.4)
            v.y = v.y0 + 20 * math.sin(v.t * 0.6)
            if v.x < -60 or v.x > self.w + 60:
                v.gone = True
            return
        if v.kind == "moray":                                 # ウツボ: 顔を出したり引っこめたり
            r = getattr(v, "home", None)
            if v.leaving:
                v.gone = True
                return
            for t in self.turtles:
                if t.alive and t.state == "swim" and math.hypot(t.x - v.x, t.y - v.y) < 35:
                    t.say("bang", 0.8, force=False)
                    t.state, t.state_t, t.vis = "flee", 1.2, v
            return
        if v.kind == "octopus":
            self._move_octopus(v, dt)
        elif v.kind == "comb":                               # クシクラゲ: ゆらゆら漂い虹色に光る
            v.x += v.vx * dt + math.sin(v.t * 0.7) * 3 * dt
            v.y = v.y0 + 10 * math.sin(v.t * 0.4)
            if v.leaving:
                v.gone = True
                self.fx.append(("ripple", v.x, v.y))
        elif v.kind == "ghost":
            self._move_ghost(v, dt)
        elif cfg["zone"] == "sea":
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

    def _spawn_bird(self, hunting=False):
        if any(v.kind == "bird" for v in self.visitors):
            return None
        left = random.random() < 0.5
        x = -30 if left else self.w + 30
        y = self.land_top + random.uniform(-20, 30)
        v = Visitor("bird", x, y, 55 if left else -55)
        self.n_birds = getattr(self, "n_birds", 0) + 1
        v.name, v.tries, v.flavor_t = "Frigatebird #%d" % self.n_birds, 0, 1e9
        self.visitors.append(v)
        self.event("visitor", "A frigatebird swooped down on the hatchlings!" if hunting else
                   "A frigatebird is circling over the beach")
        return v

    def _move_bird(self, v, dt):
        """海鳥: 浜を這う子ガメを狙って急降下する。何度か失敗したら去る。"""
        prey = [t for t in self.turtles if t.alive and not t.adult and not self.in_water(t.x, t.y)]
        if v.leaving or not prey or v.tries >= 3:
            v.leaving = True
            v.vy = -40
            v.x += v.vx * dt
            v.y += v.vy * dt
            if v.y < -30 or v.x < -40 or v.x > self.w + 40:
                v.gone = True
            return
        tg = min(prey, key=lambda t: (t.x - v.x) ** 2 + (t.y - v.y) ** 2)
        dx, dy = tg.x - v.x, tg.y - v.y
        d = math.hypot(dx, dy) or 1.0
        v.vx += (dx / d * 70 - v.vx) * min(1.0, dt * 2)
        v.vy = dy / d * 70
        v.x += v.vx * dt
        v.y += v.vy * dt
        tg.say("bang", 0.8, force=False)
        if d < 10:                                           # 急降下!
            v.tries += 1
            self.fx.append(("dust", tg.x, tg.y))
            if random.random() < 0.45:
                self._kill(tg, "being eaten", killer=v.name)
                tg.dead_t = CORPSE_TIME - 1.0
                self.fx.append(("bite", tg.x, tg.y))
            else:
                tg.vy -= 60
            v.y -= 40                                        # いったん舞い上がる
            v.vx = -v.vx * 0.6

    def _move_octopus(self, v, dt):
        """タコ: 岩場から岩場へ、海底をはうように移動する(色が変わる)。"""
        if v.leaving:
            r = getattr(v, "home", None)
            tx, ty = (r.x, r.y) if r else (v.x, v.y)
            if math.hypot(tx - v.x, ty - v.y) < 6:
                v.gone = True
                self.fx.append(("ripple", v.x, v.y))
        else:
            if not hasattr(v, "dest") or math.hypot(v.dest[0] - v.x, v.dest[1] - v.y) < 8:
                r = random.choice(self.reefs) if self.reefs else None
                v.dest = r.bed_point() if r else self.water_point(30)
            tx, ty = v.dest
        dx, dy = tx - v.x, ty - v.y
        d = math.hypot(dx, dy) or 1.0
        sp = 9 * (0.6 + 0.4 * abs(math.sin(v.t * 2)))       # のびちぢみしながら進む
        v.vx = dx / d * sp
        v.x += v.vx * dt
        v.y += dy / d * sp * dt
        for t in self.turtles:
            if t.alive and t.state == "swim" and math.hypot(t.x - v.x, t.y - v.y) < 50 and random.random() < dt / 6:
                t.say("question", 1.2, force=False)

    def _move_ghost(self, v, dt):
        """スナガニ: 走っては止まり、子ガメをねらう。最後は巣穴にもぐる。"""
        v.pause = getattr(v, "pause", 0.0) - dt
        if v.pause <= 0 and random.random() < dt / 1.2:
            v.pause = random.uniform(0.3, 1.0)                # ぴたっと止まる
            if random.random() < 0.4:
                v.vx = -v.vx
        if v.pause <= 0:
            v.x += v.vx * dt
        v.x = min(max(8, v.x), self.w - 8)
        sh = self.shore(v.x)
        v.y = min(max(sh + 8, v.y), self.h - 14)
        if v.leaving:
            v.gone = True
            self.fx.append(("dust", v.x, v.y))                # 巣穴にもぐる
            return
        for t in self.turtles:                                # 浜を這う子ガメが危ない
            if (t.alive and not t.adult and not self.in_water(t.x, t.y)
                    and math.hypot(t.x - v.x, t.y - v.y) < 16 and random.random() < dt * 0.35):
                v.n = getattr(v, "n", self.ghost_no())
                self._kill(t, "being eaten", killer="Ghost crab #%d" % v.n)
                t.dead_t = CORPSE_TIME - 1.0
                self.fx.append(("bite", t.x, t.y))
                v.leaving = True
                break
            if t.alive and not t.adult and math.hypot(t.x - v.x, t.y - v.y) < 50:
                t.say("bang", 0.8, force=False)
                if not self.in_water(t.x, t.y):
                    t.vy -= 30 * dt                         # 急いで海へ

    def ghost_no(self):
        self.n_ghost = getattr(self, "n_ghost", 0) + 1
        return self.n_ghost

    def _visitor_moment(self, v):
        """訪問者のちょっとした出来事(イルカのジャンプ、マンタの宙返り、ヤドカリの引っ越しなど)。"""
        k = v.kind
        if self.time - self.vis_log.get(k + "!", -1e9) < (VISIT_LOG_GAP if k in ("hermit", "coconut", "ghost", "comb",
                                                                                 "moray", "squid") else 300):
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
        elif k == "octopus":
            v.color = 1 - getattr(v, "color", 0)
            self.event("visitor", "The octopus changed its color and hid among the rocks")
        elif k == "comb":
            self.event("visitor", "The comb jelly is flashing rainbow lights")
        elif k == "moray":
            self.fx.append(("splash", v.x, v.y))
            self.event("visitor", "The moray eel snapped at a passing fish!")

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
            self.shark_t -= dt * SHARK_WHEN.get(self.phase, 0.5) * 1.3
            if self.shark_t <= 0:
                self.shark_t = random.uniform(*SHARK_GAP)
                left = random.random() < 0.5
                y = random.uniform(20, self.land_top * SHARK_ZONE * 0.6)
                self.n_sharks = getattr(self, "n_sharks", 0) + 1
                name = "%s #%d" % (random.choice(SHARK_KINDS), self.n_sharks)
                self.shark = Shark(-30 if left else self.w + 30, y, 30 if left else -30, name)
                self.event("shark", "A shark appeared offshore! (%s) Big turtles, watch out" % name)
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
            if tg is not None:                             # 襲いかかる!(効果音はイベントの知らせで鳴る)
                if self.log_ok("attack", 120):
                    self.event("shark", "The %s is attacking %s!" % (sh.name, self.tag(tg)))
            sh.target = tg
        if tg is not None:
            dx, dy = tg.x - sh.x, tg.y - sh.y
            d = math.hypot(dx, dy) or 1.0
            sp = 46.0
            if d < 22 + tg.radius:
                if random.random() < (0.15 if tg.lucky else 0.35):
                    self._kill(tg, "being eaten", killer=sh.name)
                    self.sfx.append("attack")
                    tg.dead_t = CORPSE_TIME - 1.0
                    self.fx.append(("bite", tg.x, tg.y))
                else:                                      # 間一髪で逃げる
                    tg.say("surprise", 1.5)
                    tg.state, tg.state_t = "flee_shark", 3.0
                    self.fx.append(("splash", tg.x, tg.y))
                    self.sfx.append("chomp")
                    tg.stats["escape"] += 1
                    self.event("shark", "%s narrowly escaped the %s!" % (self.tag(tg), sh.name))
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

    def _coral_step(self, bdt):
        """サンゴ: 育って広がる向きに部品が増え、反対側が減る(白化することも)。少しずつ移動し、
        新しいサンゴ礁ができたり、小さくなったサンゴ礁が消えたりする(遺伝子なし)。"""
        self.coral_t = getattr(self, "coral_t", 0.0) + bdt
        if self.coral_t < HOUR:
            return
        self.coral_t = 0.0
        corals = [r for r in self.reefs if r.kind == "coral"]
        if len(corals) < 7 and random.random() < (0.05 if corals else 0.3):    # 新しいサンゴ礁
            for _ in range(30):
                x, y = self.water_point(40)
                if all(math.hypot(o.x - x, o.y - y) > o.radius + 40 for o in self.reefs):
                    self.reefs.append(Reef(x, y, "coral", random.randrange(10 ** 6), n=3))
                    self.event("coral", "A new coral colony has settled on the sea floor")
                    self.reef_changed = True
                    break
        for r in corals:
            if len(r.parts) <= 2 and random.random() < 0.3:            # 小さくなったサンゴ礁が消える
                self.reefs.remove(r)
                self.event("coral", "A small coral reef died out...")
                self.reef_changed = True
        self._fish_population()
        for r in self.reefs:
            if r.kind != "coral":
                continue
            r.drift += random.gauss(0, 0.4)
            changed = False
            if len(r.parts) < 13 and random.random() < 0.3:          # 育つ
                a = r.drift + random.gauss(0, 0.8)
                d = r.radius - 10 + random.uniform(-4, 6)
                nx, ny = r.x + math.cos(a) * d, r.y + math.sin(a) * d * 0.75
                if self.in_water(nx, ny + 20) and 15 < nx < self.w - 15 and ny > 15:
                    r.parts.append((nx - r.x, ny - r.y, random.choice(("branch", "branch", "brain", "fan", "table")),
                                    random.randrange(4)))
                    changed = True
            if len(r.parts) > 2 and random.random() < (0.25 if len(r.parts) > 5 else 0.12):   # 反対側が減る
                back = max(r.parts, key=lambda p: -(p[0] * math.cos(r.drift) + p[1] * math.sin(r.drift)))
                if random.random() < 0.1 and back[3] != 4:
                    r.parts[r.parts.index(back)] = (back[0], back[1], back[2], 4)   # 白化
                    if self.time - getattr(self, "bleach_log", -1e9) > 7200:
                        self.bleach_log = self.time
                        self.event("coral", "Part of the coral reef turned white (bleached)...")
                else:
                    r.parts.remove(back)
                changed = True
            if changed:
                r.recenter()
                self.reef_changed = True

    def _trends(self):
        """群れと海藻の増減を、1日前と比べて知らせる(変化が感じられるように)。"""
        self.trend_t = getattr(self, "trend_t", 0.0)
        if self.bio_time - self.trend_t < 3 * HOUR:
            return
        self.trend_t = self.bio_time
        pop = sum(t.alive for t in self.turtles)
        bio = self.edible_food()
        self.trend.append((self.bio_time, pop, bio, self.deaths_starve))
        self.trend = self.trend[-16:]
        old = [x for x in self.trend if self.bio_time - x[0] >= DAY - 1]
        if not old:
            return
        _, p0, b0, s0 = old[-1]
        said = self.trend_said

        def say(key, msg):
            if self.bio_time - said.get(key, -1e9) > DAY:
                said[key] = self.bio_time
                self.event("trend", msg)
        if pop >= p0 * 1.3 and pop - p0 >= 4:
            say("up", "The colony is growing! %d turtles now (+%d since yesterday)" % (pop, pop - p0))
        elif pop <= p0 * 0.7 and p0 - pop >= 4:
            say("down", "Hard times... the colony shrank to %d turtles (-%d since yesterday)" % (pop, p0 - pop))
        if bio <= b0 * 0.65 and b0 - bio > 4:
            say("weed_down", "The seaweed is running out - too many hungry turtles")
        elif bio >= b0 * 1.35 and bio - b0 > 4:
            say("weed_up", "The seaweed meadows are recovering")
        if self.deaths_starve - s0 >= 6:
            say("starve", "Many turtles are starving... (%d starved since yesterday)" % (self.deaths_starve - s0))

    def edible_food(self):
        """食べられる水草の量(グラフと「海藻が減った」の知らせに使う)。根元の分は数えない。"""
        return sum(p.b - NIBBLE_FLOOR for p in self.plants if p.b > NIBBLE_FLOOR) * 1.6

    def _record(self, dt):
        self.hist_t += dt
        if self.hist_t >= HISTORY_DT:
            self.hist_t = 0.0
            self.history.append((sum(t.alive for t in self.turtles),
                                 round(self.edible_food(), 2), len(self.jellies)))
            self.history = self.history[-HISTORY_LEN:]

    # ---- 卵・誕生・死
    def _born(self, t, mom, dad):
        """誕生の記録(家系図と、親の子どもの数)。外から来た群れの子は「その家系」になる。"""
        t.mom, t.dad = mom, dad
        m = self.by_id.get(mom)
        if m is not None and m.origin != "native":
            t.origin = "family:" + m.origin.split("|")[0].replace("family:", "")
        t.stats["born"] = self.bio_time
        self.family[t.id] = (mom, dad)
        for pid in (mom, dad):
            if pid is not None:
                self.kids[pid] = self.kids.get(pid, 0) + 1
                p = self.by_id.get(pid)
                if p:
                    p.stats["kids"] += 1
        if len(self.family) > 6000:                        # 古い記録は捨てる(識別個体の家系は残す)
            keep_roots = {t.id for t in self.turtles if t.name}
            items = list(self.family.items())
            self.family = dict(items[-4000:])
            for k in keep_roots:
                if k in dict(items):
                    self.family[k] = dict(items)[k]

    def ancestors(self, tid, depth=40):
        out, cur = set(), [tid]
        for _ in range(depth):
            nxt = []
            for c in cur:
                for p in self.family.get(c, (None, None)):
                    if p is not None and p not in out:
                        out.add(p)
                        nxt.append(p)
            if not nxt:
                break
            cur = nxt
        return out

    def descendants_alive(self, root):
        return [t for t in self.turtles if t.alive and t.id != root and root in self.ancestors(t.id)]

    def life_story(self, t, departed=False):
        """識別個体が亡くなったときのメッセージ(英語の行)。"""
        if departed:
            cause = None
        elif t.killer:
            cause = "Eaten by %s" % t.killer
        else:
            cause = {"starvation": "Starvation", "illness": "Illness", "old age": "Old age (a full life)"}.get(
                t.cause, t.cause.capitalize())
        desc = self.descendants_alive(t.id)
        st = t.stats
        days = (self.bio_time - st.get("born", 0.0)) / 86400.0
        lines = ["%s left for a faraway sea" % t.name if departed else "In memory of %s" % t.name,
                 "#%d  %s  Lineage %s  Gen %d%s" % (t.id, "Female" if t.sex == "F" else "Male", t.lineage,
                                                     t.generation, "  (born under a lucky star)" if t.lucky else ""),
                 "Lived %s (about %.1f turtle days)" % (fmt_dur(t.age), max(days, t.age / 86400.0)),
                 "Set off for another sea, never to return" if departed else "Cause of death: %s" % cause,
                 "Children: %d   Descendants alive now: %d" % (self.kids.get(t.id, st["kids"]), len(desc)),
                 "Partners: %d   Ate %d seaweed and %d jellyfish" % (st["mates"], st["plants"], st["jelly"]),
                 "Surfed %d times (wiped out %d)   Got cleaned %d times" % (st["surf"], st["wipe"], st["clean"]),
                 "Escaped sharks %d times   Got sick %d times   Petted %d times" % (st["escape"], st["sick"], t.pets)]
        heirs = sorted(desc, key=lambda d: distance(d.g, t.g))[:3]     # 遺伝子と見た目がいちばん近い3匹
        return {"id": t.id, "name": t.name, "lines": lines, "heirs": [d.id for d in heirs]}

    def _hatch(self, dt, real_dt=None):
        """卵: 時間がたつと夜を待ち、ゆれて、割れて、子ガメが海へ向かう。"""
        real_dt = dt / TIME_SCALE if real_dt is None else real_dt
        groups = {}
        for e in list(self.eggs):
            e.t -= dt
            if e.t <= 0 and self.night > 0.5:          # 子ガメは夜にふ化して海へ
                if getattr(e, "shake", None) is None:
                    e.shake = HATCH_SHAKE              # まず卵がゆれる
                    continue
                e.shake -= real_dt
                if e.shake > 0:
                    continue
                self.eggs.remove(e)
                self.fx += [("sparkle", e.x, e.y), ("dust", e.x, e.y)]
                t = Turtle(e.g, e.x, e.y, e.generation, sex=e.sex,
                           lineage=e.lineage, parents=e.parents)
                self._born(t, e.mom, e.dad)
                t.energy = HATCH_ENERGY
                t.say("sparkle", 2.0)
                self.turtles.append(t)
                self.births += 1
                if random.random() < self.hatchling_leave():   # 多くの子ガメはそのまま外洋へ(戻らない)
                    t.state, t.depart_x = "depart", min(max(20, t.x + random.uniform(-60, 60)), self.w - 20)
                    self.departed = getattr(self, "departed", 0) + 1
                self.max_gen = max(self.max_gen, e.generation)
                groups.setdefault((e.lineage, e.generation), []).append(t)
        for (lin, gen), ts in groups.items():
            gone = sum(t.state == "depart" for t in ts)
            self.event("hatch", "Under the moonlight, %d baby turtle%s (Lineage %s, Gen %d) broke out "
                       "and raced to the sea!%s" % (len(ts), "s" if len(ts) > 1 else "", lin, gen,
                                                    (" %d of them swam off to the open ocean." % gone) if gone else ""))
            self.sfx.append("hatch")
            if random.random() < 0.5 and real_dt < 30:     # 海鳥が子ガメを狙いに来る
                self._spawn_bird(hunting=True)

    def hatchling_leave(self):
        """子ガメが外洋へ旅立つ割合。海藻が少ないほど多い(15〜80%)。"""
        fp = getattr(self, "_food_per", 1.5)
        n = len(self.alive())                                 # ふだんはほとんど残る。増えすぎたときだけ外洋へ
        return min(0.7, max(0.0, (n - COLONY_SOFT) / 10.0)) + (0.3 if fp < EMIGRATE_FOOD else 0.0)

    def _emigrate(self, bdt, offline=False):
        """カメが増えて海藻が足りなくなると、何匹かは他の海域へ旅立つ(二度と戻らない)。"""
        alive = [t for t in self.turtles if t.alive and t.state != "depart"]
        if len(alive) < EMIGRATE_MIN:
            return
        food_per = self.edible_food() / len(alive)
        crowd = max(0.0, (len(alive) - COLONY_CROWD) / 6.0)        # ひどく混みあったときだけ(ごくまれ)
        if food_per >= EMIGRATE_FOOD and crowd <= 0:
            return
        p = EMIGRATE_RATE * (max(0.0, 1 - food_per / EMIGRATE_FOOD) + crowd) * bdt / HOUR * len(alive)
        if random.random() >= p:
            return
        cand = [t for t in alive if t.state in ("swim", "food", "court", "watch", "idle") or offline]
        if not cand:
            return
        lead = min(cand, key=lambda t: t.energy + 0.3 * t.g["flock"] * random.random())
        group = [lead] + [o for o in cand if o is not lead and o.lineage == lead.lineage
                          and math.hypot(o.x - lead.x, o.y - lead.y) < 80 and random.random() < 0.5][:2]
        for t in group:
            if offline:
                self.turtles = [o for o in self.turtles if o is not t]
            else:
                t.state, t.target, t.food, t.bed = "depart", None, None, None
                t.depart_x = min(max(20, t.x + random.uniform(-80, 80)), self.w - 20)
                t.say("note", 3.0)
            self.departed = getattr(self, "departed", 0) + 1
            if t.name:
                self.memorials.append(self.life_story(t, departed=True))
        names = ", ".join(self.tag(t) for t in group)
        why = "The seaweed is scarce..." if food_per < EMIGRATE_FOOD else "The sea is getting crowded..."
        self.event("depart", "%s %s set off for a faraway sea, never to return" % (why, names))

    def _crisis(self, bdt):
        """絶滅の危機: 平均 21 日に1度、嵐・赤潮・伝染病・海藻の不作のどれかが起こる。
        たいていは数が大きく減るだけだが、9 回に 1 回くらいは全滅してしまう。"""
        self.crisis_t = getattr(self, "crisis_t", CRISIS_DAYS * DAY) - bdt
        if self.crisis_t > 0:
            return
        self.crisis_t = max(CRISIS_MIN_DAYS, random.expovariate(1.0 / (CRISIS_DAYS - CRISIS_MIN_DAYS))
                            + CRISIS_MIN_DAYS) * DAY
        alive = [t for t in self.turtles if t.alive]
        if not alive and not self.eggs:
            return
        self.start_crisis(random.choice(("storm", "red tide", "epidemic", "famine")),
                          fatal=random.random() < CRISIS_FATAL)

    def start_crisis(self, kind, fatal=False):
        alive = [t for t in self.turtles if t.alive]
        keep = 0 if fatal else random.choice((1, 2, 2, 3))         # 2匹ほどまで減って、ヒヤッとする
        msg = {"storm": "A terrible storm hit the sea!",
               "red tide": "A red tide spread through the water!",
               "epidemic": "A turtle epidemic broke out!",
               "famine": "The seaweed suddenly withered all over the sea!"}[kind]
        self.event("crisis", "CRISIS: " + msg + (" The whole colony is in danger..." if fatal else ""))
        cause = {"storm": "the storm", "red tide": "red tide poisoning", "epidemic": "illness"}.get(kind)
        if kind == "storm":
            self.plants = [p for p in self.plants if random.random() < 0.4]
            self.eggs = [] if fatal else [e for e in self.eggs if random.random() < 0.3]
            self.jellies = [j for j in self.jellies if random.random() < 0.5]
        elif kind == "red tide":
            self.jellies = [j for j in self.jellies if random.random() < 0.2]
            self.fish = [f for f in self.fish if random.random() < 0.5]
        elif kind == "famine":
            self.plants = [p for p in self.plants if random.random() < (0.0 if fatal else 0.12)]
            if fatal:
                self.eggs = []
            cause = "starvation"
        if fatal and kind != "famine":
            self.eggs = []
        spared = set(id(t) for t in random.sample(alive, min(keep, len(alive))))   # 生き残るのは 1〜3 匹
        for t in alive:
            if id(t) not in spared:
                if kind == "epidemic":
                    t.stats["sick"] = t.stats.get("sick", 0) + 1
                self._kill(t, cause)
        self.meadow_changed = True
        self._update_meadows()

    def _kill(self, t, cause, killer=None):
        """cause: starvation / illness / old age / being eaten(killer = 食べた相手)"""
        t.state, t.dead_t, t.cause = "dead", 0.0, cause
        t.killer = killer
        t.emote, t.emote_t = "ghost", 3.0
        t.clutch = None
        self.deaths += 1
        self.gene_pool.append(t.g)
        self.gene_pool = self.gene_pool[-10:]
        if cause == "starvation":
            self.deaths_starve += 1
        if killer:
            self.event("death", "%s was eaten by %s at %s" % (self.tag(t), killer, fmt_dur(t.age)))
        else:
            self.event("death", "%s died of %s at %s" % (self.tag(t), cause, fmt_dur(t.age)))
        if t.name:                                         # 識別個体: 一生のまとめ
            self.memorials.append(self.life_story(t))
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
                            if o.id == t.partner and random.random() < dt / 60:
                                t.say("flower", 1.2)
                            elif t.aff[o.id] >= FRIEND_AFF and random.random() < dt / 40:
                                t.say("bubbles", 1.2)          # 友達: あわを出してあいさつ
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
    def _update_turtle(self, t, dt, bdt=None):
        """dt は実時間(動き・表情)、bdt はカメの時間(年齢・おなか・眠気)。"""
        bdt = dt * TIME_SCALE if bdt is None else bdt
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
        if t.state == "depart":                         # 他の海域へ旅立つ: 沖へまっすぐ泳いで消える
            t.vx, t.vy = t.vx * 0.9 + (t.depart_x - t.x) * 0.02, -max(14.0, t.max_speed * 0.8)
            t.x += t.vx * dt
            t.y += t.vy * dt
            t.dir = 0
            if t.y < -25:
                self.turtles = [o for o in self.turtles if o is not t]
            return

        t.age += bdt
        t.mate_cd -= bdt
        self._stored_clutch(t, bdt)
        t.eat_cd -= dt
        t.clean_cd -= bdt
        t.joy = max(0.0, t.joy - 0.015 * dt)
        t.annoy = max(0.0, t.annoy - 0.02 * dt)
        sleeping = t.state == "sleep"
        t.air -= dt * (0.4 if sleeping else 1.0)
        t.groggy = max(0.0, t.groggy - dt)
        if sleeping or t.state == "lay":               # 眠っている・じっと産卵している間は少しだけ減る
            t.energy -= t.metab * bdt * SLEEP_METAB
        else:                                           # 動くほどおなかが減る
            spd = min(1.5, math.hypot(t.vx, t.vy) / max(1.0, t.max_speed))
            t.energy -= t.metab * bdt * (0.5 + 0.9 * spd)
        t.fatigue += (-bdt / t.sleep_len) if sleeping else (bdt / t.awake_len)
        if self._illness(t, bdt):
            return
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
        if st in ("flipped", "dance", "lay", "breathe", "petted", "cleaning", "wipeout", "mating", "idle",
                  "nap", "drift"):
            if st == "lay" and t.state_t > 0:
                self._laying_scene(t, dt)
            elif st in ("nap", "drift") and t.state_t > 0:
                if t.energy < 0.35 or (t.air <= 0 and water):     # おなかがすいた・息継ぎ
                    t.state_t = 0
                elif st == "nap" and random.random() < dt / 3:
                    t.say("zzz", 1.5, force=False)
                elif st == "drift" and random.random() < dt / 12:
                    t.say(random.choice(("dots", "note")), 1.2, force=False)
            elif st == "idle" and t.state_t > 0 and random.random() < dt * 0.8:
                t.dir = (t.dir + random.choice((1, 3))) % 4   # きょろきょろ
            if t.state_t <= 0:
                if st == "mating":                            # 交尾のアニメーションのあと、実際に交尾
                    p = getattr(t, "mate_with", None)
                    if p is not None and p.alive and p.state == "mating":   # 先に終わった方が(オスでもメスでも)
                        t.state = p.state = "swim"
                        self._mate(t, p)
                    elif t.state == "mating":
                        t.state = "swim"
                    t.mate_with = None
                elif st == "wipeout":                           # 照れ笑い、またはしょんぼり
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
                    t.stats["clean"] += 1
                    if t.sick > 0:                           # クリーニングで病気が治る
                        t.sick = 0.0
                        self.event("sick", "%s felt better after being cleaned" % self.tag(t))
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
                t.say(random.choice(("star", "note")), 1.0, force=False)
        elif st == "buddy":                                  # 友達と並んで泳ぐ
            f = t.target
            if f is None or not f.alive or t.state_t <= 0 or f.state in ("sleep", "lay", "nest", "dead", "depart"):
                t.state, t.target = "swim", None
            elif random.random() < dt / 5:
                t.say("bubbles", 1.4, force=False)
        elif st == "sleep":
            t.fatigue = max(t.fatigue, -0.2)
            if t.energy < 0.2 and self._choose_food(t) is not None:   # おなかがすいて目がさめる(餌を探しに行く)
                t.state, t.bed = "swim", None
                t.fatigue = min(t.fatigue, 0.5)
                t.say("sweat", 1.5)
            elif t.fatigue <= 0 and t.night_pull(self.night) < 0.5:
                t.state, t.bed = "swim", None                # 朝になったら起きる(しばらく寝ぼける)
                t.groggy = 15 + 35 * (1 - t.g["activity"])
                t.say("dots" if t.g["activity"] < 0.5 else "note", 1.5)
            elif t.air <= 0 and water:                       # 寝ていても息継ぎに浮上する
                self._start_breathe(t)
            elif random.random() < dt / 3:
                t.say("zzz", 1.5)
        elif st in ("flee", "flee_shark") and t.state_t > 0:
            pass
        elif st == "watch":
            v = t.vis
            if v is None or v.gone or t.state_t <= 0 or t.energy < t.eat_below - 0.2:
                t.state, t.vis = "swim", None
            elif random.random() < dt / 3:
                t.say(random.choice(("question", "sparkle", "dots")), 1.2, force=False)
        elif st == "flirt":
            f = t.target
            if f is None or not f.alive or t.state_t <= 0 or f.state in ("sleep", "lay", "mating", "nest"):
                t.state, t.target = "swim", None
            else:
                if random.random() < dt / 4:
                    t.say("note", 1.0, force=False)
                if math.hypot(f.x - t.x, f.y - t.y) < t.radius + f.radius + 6 and random.random() < dt:
                    if self._can_mate(t) and self._can_mate(f) and random.random() < 0.3:
                        self._start_mating(t, f)           # しつこさが実ることも
                    else:
                        f.say("anger" if f.g["temper"] > 0.5 else "sweat", 1.2)
                        f.state, f.state_t, f.vis = "flee", 1.5, None
        else:
            self._decide(t, dt, water)
            self._quirks(t, dt, water)
        self._steer(t, dt, water)

    def _quirks(self, t, dt, water):
        """性格の遺伝子で起きるイベント: おっちょこちょい・観察好き・メスを追いかけ回す・無目的にふらふら。"""
        if t.state != "swim" or not water:
            return
        g = t.g
        if random.random() < dt * 0.006 * g["clumsy"] ** 2:      # おっちょこちょい
            kind = random.random()
            if kind < 0.4:
                t.state, t.state_t = "flipped", 2.5                # 勝手にひっくり返ってジタバタ
                t.say("surprise", 1.2)
                self.sfx.append("flip")
                if t.name or self.log_ok("oops", 300):
                    self.event("oops", "Oops! %s flipped itself over for no reason" % self.tag(t))
            elif kind < 0.7 and self.reefs:
                r = min(self.reefs, key=lambda r: (r.x - t.x) ** 2 + (r.y - t.y) ** 2)
                if math.hypot(r.x - t.x, r.y - t.y) < r.radius + 40:
                    t.say("bang", 1.0)                          # 岩に頭をごつん
                    t.vx, t.vy = -t.vx * 2, -t.vy * 2
                    self.fx.append(("splash", t.x, t.y))
                    if t.name or self.log_ok("oops", 300):
                        self.event("oops", "%s bumped its head on the rocks. Ouch!" % self.tag(t))
            else:
                t.state, t.state_t = "idle", 2.5                # どこへ行くんだっけ?
                t.say("question", 1.5)
            return
        if t.energy > 0.45 and not t.clutch:
            day = self.night < 0.5
            if day and random.random() < dt * 0.02 * g["nap"] ** 3:       # 昼寝好き: 昼間もよく眠る
                t.state, t.state_t = "nap", random.uniform(30, 60) * (0.5 + 2.0 * g["nap"])
                t.say("zzz", 1.5)
                if t.name or (g["nap"] > 0.8 and self.log_ok("nap", 900)):
                    self.event("watch", "%s is taking a nap again..." % self.tag(t))
                return
            if random.random() < dt * 0.02 * g["drift"] ** 3:              # ただよい好き: 泳がずに流される
                t.state, t.state_t = "drift", random.uniform(25, 50) * (0.5 + 2.0 * g["drift"])
                if t.name or (g["drift"] > 0.8 and self.log_ok("drift", 900)):
                    self.event("watch", "%s is just drifting with the current" % self.tag(t))
                return
            if random.random() < dt * 0.012 * (0.3 + g["flock"]):         # 友達と並んで泳ぐ
                fr = [o for o in self.friends(t) if o.state in ("swim", "food")
                      and math.hypot(o.x - t.x, o.y - t.y) < 160]
                if fr:
                    f = random.choice(fr)
                    t.state, t.target, t.state_t = "buddy", f, random.uniform(15, 35)
                    t.say("bubbles", 1.5)
                    if t.name or f.name or self.log_ok("buddy", 600):
                        self.event("friend", "%s and %s are swimming side by side (good friends)"
                                   % (self.tag(t), self.tag(f)))
                    return
        if random.random() < dt * 0.05 * g["watch"] ** 2:         # 観察好き(タコが大好き)
            near = [v for v in self.visitors if not v.gone and math.hypot(v.x - t.x, v.y - t.y) < 230]
            if near:
                octo = [v for v in near if v.kind == "octopus"]
                v = random.choice(octo or near)
                t.state, t.vis, t.state_t = "watch", v, random.uniform(10, 20) * (1 + 5 * max(0.0, g["watch"] - 0.7) / 0.3)
                t.say("sparkle", 1.2)
                if t.name or self.log_ok("watch", 600):
                    self.event("watch", "%s is watching the %s with great interest"
                               % (self.tag(t), VIS_NAMES.get(v.kind, v.kind)))
                return
        if (t.sex == "M" and t.adult and random.random() < dt * 0.008 * max(0.0, g["flirt"] - 0.5)
                and t.energy > 0.45):                           # メスを追いかけ回す
            fem = [f for f in self.turtles if f.alive and f.sex == "F" and f.adult and f.state in ("swim", "food")
                   and math.hypot(f.x - t.x, f.y - t.y) < 180]
            if fem:
                f = random.choice(fem)
                t.state, t.target, t.state_t = "flirt", f, random.uniform(6, 12)
                if t.name or f.name or self.log_ok("flirt", 600):
                    self.event("flirt", "%s keeps chasing %s around..." % (self.tag(t), self.tag(f)))
                return
        if g["whim"] > 0.65 and random.random() < dt * 0.04 * g["whim"]:   # 無目的にふらふら、立ち止まる
            t.state, t.state_t = "idle", random.uniform(1.5, 3.5)
            t.say(random.choice(("dots", "question", "note")), 1.2, force=False)

    def log_ok(self, key, gap):
        """よくある出来事は、イベント欄に書く間隔をあける(実時間 gap 秒)。"""
        last = self.vis_log.get("log:" + key, -1e9)
        if self.time - last < gap:
            return False
        self.vis_log["log:" + key] = self.time
        return True

    def weak(self, t):
        """弱っている: おなかがすいた・病気・年寄り。動きがゆっくり、色が薄く、ふらつく。"""
        return t.energy < 0.25 or t.sick > 0 or t.age > 0.85 * t.lifespan

    def _laying_scene(self, t, dt):
        """産卵: 穴を掘る → 涙を流しながら産む → 砂をかける。"""
        ph = t.state_t
        if ph > LAY_TIME * 0.7:                              # 穴を掘る(最初の3割)
            if random.random() < dt * 4:
                self.fx.append(("dust", t.x + random.uniform(-6, 6), t.y + t.radius * 0.6))
            t.say("egg", 1.0, force=False)
        elif ph > LAY_TIME * 0.25:                           # 涙を流しながら産む
            t.say("cry", 1.0)
            if random.random() < dt * 2.5:
                hx, hy = t.head()
                self.fx.append(("tear", hx + random.uniform(-3, 3), hy))
            if not getattr(t, "tear_snd", False):
                t.tear_snd = True
                self.sfx.append("bell")
        else:                                                # 砂をかける
            t.tear_snd = False
            if random.random() < dt * 4:
                self.fx.append(("dust", t.x + random.uniform(-8, 8), t.y + random.uniform(-4, 6)))

    def _start_mating(self, a, b):
        """交尾: 寄りそって、ハートが1つ出るだけ(あっさり)。"""
        self.mating_open()
        self.mates_today = getattr(self, "mates_today", 0) + 1
        for x, y in ((a, b), (b, a)):
            x.state, x.state_t, x.mate_with, x.target = "mating", MATING_TIME, y, None
        f = a if a.sex == "F" else b
        f.say("heart", MATING_TIME)
        self.sfx.append("heart")

    def _illness(self, t, bdt):
        """病気: 混み合い・空腹・年をとると、かかりやすい。治ることも、亡くなることも。
        True を返したら亡くなった。"""
        h = bdt / HOUR
        if t.sick <= 0:
            crowd = t.nb[4] if t.nb else 0
            risk = SICK_RATE * (1 + crowd / 4) * (2.0 if t.energy < 0.3 else 1.0) * (0.5 + t.age / max(1.0, t.lifespan))
            if t.lucky:
                risk *= 0.3
            if random.random() < risk * h:
                t.sick = random.uniform(0.4, 1.0)
                t.stats["sick"] += 1
                t.say("sweat", 2.0)
                if t.name or random.random() < 0.3:
                    self.event("sick", "%s got sick..." % self.tag(t))
            return False
        t.energy -= t.metab * bdt * 0.3                     # 病気だと体力をつかう
        if random.random() < dt_chance(0.25, h):            # 治る
            t.sick = 0.0
            t.say("note", 1.5)
            if t.name:
                self.event("sick", "%s got well again" % self.tag(t))
            return False
        if random.random() < dt_chance(0.05 * t.sick * (2 if t.energy < 0.3 else 1), h):
            self._kill(t, "illness")
            return True
        if random.random() < h * 0.5:
            t.say(random.choice(("sweat", "dots")), 1.5, force=False)
        return False

    def _start_breathe(self, t):
        t.state, t.state_t = "breathe", BREATH_TIME
        hx, hy = t.head()
        self.fx.append(("ripple", hx, hy))

    def _decide(self, t, dt, water):
        prev = t.state
        t.state = "swim"
        sleepy = t.fatigue + t.night_pull(self.night) > 1 and t.energy > 0.3   # 腹ぺこでは眠らない
        # 株を丸ごと食べるので、ちゃんとお腹がすいてから。夕方は寝る前にしっかり食べる
        hungry_line = max(0.45, min(0.92 if 15 <= self.hour < 20 else 0.7, t.eat_below + self.appetite_shift()))
        # ↑ 夜でも小食でも、半分を切ったらきちんと餌を探す(以前は夜に探し始めるのが遅すぎて餓死していた)
        if t.clutch:
            hungry_line = max(hungry_line, 0.8)              # 卵を抱えたメスは、上陸の前にしっかり食べる
        if t.clutch and self.nest_time() and (t.energy > 0.5 or prev == "nest"):   # おなかを満たしてから上陸
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
                t.bed, t.bed_kind = self.choose_bed(t)
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
        elif self._can_mate(t) and self.night < 0.6 and random.random() < dt * COURT_CHANCE * (1 + t.g["flirt"]):
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

    def choose_bed(self, t):
        """寝床: 近くて空いている岩場(サンゴも)。ほかのカメの寝床とは離れた場所を選ぶ(押し合わない)。"""
        beds = [o.bed for o in self.turtles if o is not t and o.alive and o.bed and o.state in ("sleep", "to_bed")]

        def crowd(r):
            return sum(1 for b in beds if math.hypot(b[0] - r.x, b[1] - r.y) < r.radius + 10)
        r = min(self.reefs, key=lambda r: math.hypot(r.x - t.x, r.y - t.y) * (0.8 if r.kind == "rock" else 1.0)
                + 120 * max(0, crowd(r) - (4 if r.kind == "rock" else 2)))
        best, bd = None, -1.0
        for _ in range(14):
            p = r.bed_point()
            if not self.in_water(*p):
                continue
            d = min((math.hypot(b[0] - p[0], b[1] - p[1]) for b in beds), default=999.0)
            d = min(d, 2 * min((math.hypot(q.x - p[0], q.y - p[1]) for q in self.plants), default=999.0))  # 海藻の上では寝ない
            if d > bd:
                best, bd = p, d
        return (best or r.bed_point()), r.kind

    def _free_school(self):
        free = [s for s in self.schools if s.cleaning is None]
        return random.choice(free) if free else None

    def mating_open(self):
        """今日まだ交尾できるか(朝だけ、1日に 1〜2 ペア)。"""
        a, b = MATING_HOURS
        few = getattr(self, "_pop", POP_TARGET) < POP_TARGET - 3
        if few and 16 <= self.hour < 18 and getattr(self, "mates_today", 0) < getattr(self, "mate_quota", 2):
            return True                                           # 数が少ないときは夕方にも
        if not (a <= self.hour < b):
            if self.hour < a or self.hour >= b + 2:
                self._mate_new = True                     # 次の朝は、また 1〜2 ペア
            return False
        if getattr(self, "_mate_new", True):
            self._mate_new, self.mates_today = False, 0
            n = getattr(self, "_pop", POP_TARGET)                 # 卵も数える
            if n < POP_TARGET - 3:
                self.mate_quota = 3 if n < POP_TARGET - 4 else 2  # 少ないときは 2〜3 ペア
            elif n < POP_TARGET + 1:
                self.mate_quota = random.choice((1, 1, 2))
            elif n < COLONY_SOFT:
                self.mate_quota = 1 if random.random() < 0.5 else 0
            else:
                self.mate_quota = 0
        return self.mates_today < self.mate_quota

    def _can_mate(self, t):
        return (t.alive and t.state in ("swim", "court", "flirt", "drift", "idle", "watch", "nap", "food")
                and t.adult and t.energy > 0.5
                and self.mating_open()
                and t.mate_cd <= 0 and not t.clutch and self.in_water(t.x, t.y)
                and self._pop < COLONY_SOFT and getattr(self, "_food_per", 9.0) > FOOD_TO_BREED)

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

    def edible_line(self, t):
        """おなかがすくほど、小さな株でも食べる。"""
        if t.energy < 0.25:
            return NIBBLE_FLOOR + 0.03
        if t.energy < 0.4:
            return NIBBLE_FLOOR + 0.08
        return NIBBLE_FLOOR + 0.15

    def _choose_food(self, t):
        best, bs = None, 1e18
        line = self.edible_line(t)
        items = [p for p in self.plants if p.b > line]
        if not t.herbivore:
            items += self.jellies
        for f in items:
            if f.kind == "plant":
                gain = f.b * (1.5 if t.herbivore else 0.9)       # 株を丸ごと食べる
            else:
                gain = JELLY_ENERGY
            d = math.hypot(f.x - t.x, f.y - t.y) + 20
            need = 1.0 - t.energy
            s = d / max(min(gain, need + 0.1), 0.01)            # 食べすぎない大きさを選ぶ
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
            if f.b < NIBBLE_FLOOR + 0.01:
                t.food = None
                return
            bite = min(PLANT_NIBBLE, f.b - NIBBLE_FLOOR)     # 1ドットずつ、のんびりかじる(株は残る)
            if bite <= 0.005:
                t.food = None
                return
            f.b -= bite
            f.bitten = self.time
            if random.random() < 0.5:
                self.fx.append(("leaf", f.x, f.y))
            t.energy += bite * (1.5 if t.herbivore else 0.9)
            self.eaten_plants += bite
            t.stats["plants"] += bite
            if f.b - NIBBLE_FLOOR < 0.01 or t.energy > 0.95:
                t.food = None                              # 次の株へ(または、おなかいっぱい)
        else:
            f.gone = True
            t.energy += JELLY_ENERGY
            t.stats["jelly"] += 1
            self.fx.append(("pop", f.x, f.y))
        t.energy = min(1.0, t.energy)
        t.joy = min(1.0, t.joy + 0.06)
        t.eat_cd = EAT_TIME
        t.food_t = 0.0
        if t.energy > 0.92:
            t.say("flower", 1.2)                    # おなかいっぱい
        elif random.random() < 0.3:
            t.say("note", 1.0)

    def clutch_size(self, mom):
        """1回に産む卵の数。カメが少ないほど多く、多いほど少ない(ホメオスタシス)。"""
        base = 2 + int(mom.g["fertility"] * 2.99)                 # 2〜4個
        n = getattr(self, "_pop", POP_TARGET)
        if n < POP_TARGET - 4:
            base += 3
        elif n < POP_TARGET - 3:
            base += 2
        elif n > POP_TARGET + 2:
            base -= 1
        return max(1, base)

    def _stored_clutch(self, t, bdt):
        """たくわえた精子で、交尾なしで次の卵を準備する(本物のウミガメは1シーズンに何度も産卵する)。"""
        st = getattr(t, "stored", None)
        if not st or t.clutch or t.sex != "F":
            return
        if st["left"] <= 0:
            t.stored = None
            return
        st["t"] -= bdt
        if st["t"] > 0 or t.energy < 0.5:
            return
        n = min(MAX_TURTLES - self.population(), self.clutch_size(t), int((t.energy - 0.12) / EGG_COST))
        if n <= 0:
            st["t"] = HOUR
            return
        t.energy -= EGG_COST * n
        t.clutch = [{"g": mutate(crossover(t.g, st["dg"])), "dad": st["dad"],
                     "gen": max(t.generation, st["dgen"]) + 1, "par": "#%d x #%d" % (t.id, st["dad"])}
                    for _ in range(n)]
        t.nest = None
        st["left"] -= 1
        st["t"] = CLUTCH_GAP * random.uniform(0.8, 1.2)
        if st["left"] <= 0:
            t.stored = None

    def _lay(self, t):
        n = 0
        for g in t.clutch or []:
            if self.population() >= MAX_TURTLES:
                break
            self.eggs.append(Egg(g["g"], t.x + random.uniform(-10, 10), t.y + random.uniform(-6, 6),
                                 g["gen"], t.lineage, g["par"], mom=t.id, dad=g.get("dad")))
            n += 1
        t.clutch, t.nest = None, None
        t.state = "swim"
        self.laid += n
        t.say("sparkle", 1.5)
        self.event("lay", "%s shed tears as she laid %d egg%s on the night beach" % (
            self.tag(t), n, "s" if n != 1 else ""))

    def _steer(self, t, dt, water):
        sp = t.max_speed
        dx = dy = 0.0
        mul = 1.0
        st = t.state
        if st == "wipeout":                                  # 波にもまれて流される
            t.y += 10 * dt
            t.dir = int(t.anim / 0.12) % 4
            mul = 0.0
        elif st == "drift":                                 # ひれを動かさず、流れにまかせる
            dx = math.cos(t.anim * 0.15 + t.id) + 0.4
            dy = 0.5 * math.sin(t.anim * 0.4 + t.id)
            mul = 0.1
        elif st == "buddy" and t.target is not None:        # 友達のとなりを、同じ向きで
            f = t.target
            side = 16 if t.id < f.id else -16
            hx, hy = math.cos(f.heading), math.sin(f.heading)
            dx, dy = f.x - hy * side + hx * 6 - t.x, f.y + hx * side + hy * 6 - t.y
            mul = 0.9 if math.hypot(dx, dy) > 10 else 0.5
        elif st in ("sleep", "flipped", "lay", "breathe", "petted", "cleaning", "idle", "nap"):
            mul = 0.0
        elif st == "mating" and getattr(t, "mate_with", None):
            p = t.mate_with                                 # 寄りそってくるくる回る
            mx, my = (t.x + p.x) / 2, (t.y + p.y) / 2
            t.orbit += dt * 2.0
            sgn = 1 if t.sex == "F" else -1
            tx, ty = mx + sgn * math.cos(t.orbit) * 12, my + sgn * math.sin(t.orbit) * 9
            dx, dy = tx - t.x, ty - t.y
            mul = 0.5
        elif st == "watch" and t.vis:
            v = t.vis                                       # 少し離れて、じっと見る
            d = math.hypot(v.x - t.x, v.y - t.y) or 1.0
            dx, dy = (v.x - t.x) * (1 if d > 60 else -0.6), (v.y - t.y) * (1 if d > 60 else -0.6)
            mul = 0.5 if d > 60 else 0.15
        elif st == "flirt" and t.target:
            f = t.target
            dx, dy = f.x - t.x, f.y - t.y
            mul = 1.25
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
                t.stats["wipe"] += 1
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
                elif d < reach or (d < reach + 14 and math.hypot(t.vx, t.vy) < 12):   # 寝ているカメがじゃまでも、首をのばして
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
            # 浅瀬好き・沖合好き
            pref = (t.g["depth"] - 0.5) * 2
            ty = self.land_top * (0.5 + 0.38 * pref)
            dy += max(-0.7, min(0.7, (ty - t.y) / 120.0)) * abs(pref)
            if t.g["whim"] > 0.65:                          # 気ままにふらふら(くねくね)
                t.heading += math.sin(t.anim * 1.7) * 2.0 * dt
            mul *= 0.55 + 0.4 * t.joy
            t.heading = math.atan2(dy, dx) if (dx or dy) else t.heading
        elif dx or dy:
            t.heading = math.atan2(dy, dx)
        if st not in ("flee_shark", "flee", "nest"):
            if self.weak(t):                                # 弱っている: ゆっくり、ときどき止まる
                if st == "food":                            # 餌に向かうときは、ふらつきながらも必死に
                    mul *= 0.8
                else:
                    mul *= 0.45 if int(t.anim / 1.5) % 3 else 0.1
                if random.random() < dt / 8:
                    t.say("sweat", 1.0, force=False)
            if t.groggy > 0 and st in ("swim", "food"):     # 寝ぼけ: ゆっくり、よろよろ
                mul *= 0.35
                t.heading += math.sin(t.anim * 3) * 1.5 * dt
                if random.random() < dt / 6:
                    t.say("zzz", 1.0, force=False)
            if st == "swim" and t.g["activity"] > 0.65 and t.energy > 0.5 and not self.weak(t):
                t.dash_t -= dt                              # 元気: ときどきダッシュ
                if t.dash_t < 1.0:
                    mul *= 1.9
                    if t.dash_t <= 0:
                        t.dash_t = random.uniform(20, 45)
        chewing = t.eat_cd > 0 and st in ("swim", "food")
        if chewing:
            mul = 0.0                                       # 噛んでいる間は止まる
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
        elif st != "dance" and not chewing and abs(t.vx) + abs(t.vy) > 2:
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
                sa, sb = a.state == "sleep", b.state == "sleep"
                if not (sa and sb):                          # 眠っているカメは押されない(起きている方がよける)
                    push = (r - d) * 0.25 * (1.6 if sa or sb else 1)
                    if not sa:
                        a.x -= dx / d * push
                        a.y -= dy / d * push
                    if not sb:
                        b.x += dx / d * push
                        b.y += dy / d * push
                if ((a.state == "court" and a.target is b) or (b.state == "court" and b.target is a)) \
                        and a.sex != b.sex and self._can_mate(a) and self._can_mate(b):
                    self._start_mating(a, b)
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
        n = min(room, self.clutch_size(mom),
                int((mom.energy - 0.12) / EGG_COST))        # 産める数は母親の栄養しだい
        if n <= 0:                                           # 産めなくても、しばらくは交尾しない
            for t in (a, b):
                t.mate_cd = max(t.mate_cd, MALE_MATE_GAP * 0.5)
                t.state, t.target = "swim", None
            return
        again = mom.partner == dad.id
        for t in (a, b):
            t.mate_cd = (FEMALE_MATE_GAP if t is mom else MALE_MATE_GAP) * (0.8 + 0.4 * random.random())
            t.energy -= EGG_COST * n if t is mom else 0.2
            t.state, t.target = "swim", None
            t.say("heart", 2.0)
        mom.partner, dad.partner = dad.id, mom.id
        mom.stats["mates"] += 1
        dad.stats["mates"] += 1
        mom.clutch = [{"g": mutate(crossover(mom.g, dad.g)), "dad": dad.id,
                       "gen": max(mom.generation, dad.generation) + 1,
                       "par": "#%d x #%d" % (mom.id, dad.id)} for _ in range(n)]
        mom.nest = None
        mom.stored = {"dg": dad.g, "dad": dad.id, "dgen": dad.generation,
                      "left": 2 if self._pop < POP_TARGET - 2 else 1 if self._pop < POP_TARGET + 2 else 0,
                      "t": CLUTCH_GAP * random.uniform(0.8, 1.2)}      # 次の産卵も、この父親の子
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
            why = ("eaten by %s" % t.killer) if getattr(t, "killer", None) else ("died of %s" % t.cause)
            return ["%s  Lineage %s  Gen %d" % (("\u2605 %s #%d" % (t.name, t.id)) if t.name else "#%d" % t.id,
                                                 t.lineage, t.generation),
                    "%s at %s" % (why[0].upper() + why[1:], fmt_dur(t.age))]
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
               "depart": "leaving for a faraway sea", "nap": "taking a nap", "drift": "drifting with the current",
               "buddy": "swimming with a friend",
               "to_clean": "going to the cleaning station", "cleaning": "being cleaned by fish",
               "surf": "surfing!", "catch": "paddling out to catch the big wave", "wipeout": "wiped out!", "play": "playing with the visitor"}
        if not self.in_water(t.x, t.y) and t.state == "swim":
            st = "crawling to the sea"
        else:
            st = now.get(t.state, t.state)
        style = STYLES[style_of(t.g)]
        head = ("\u2605 %s  #%d" % (t.name, t.id)) if t.name else "#%d" % t.id
        lines = ["%s  %s  Lineage %s  Gen %d" % (head, "Female" if t.sex == "F" else "Male",
                                                  t.lineage, t.generation),
                 "Age %s%s%s" % (fmt_dur(t.age), (" / " + fmt_dur(t.lifespan)) if not t.lucky else "",
                                 "  (young)" if not t.adult else ""),
                 "Health %d%% (%s%s)   Mood: %s" % (round(e * 100), health, ", sick" if t.sick > 0 else "", mood),
                 "%s   Size x%d%s" % ("Herbivore" if t.herbivore else "Omnivore", t.scale,
                                      "  (shark target)" if t.scale >= SHARK_PREY_SCALE else ""),
                 "Look: %s, %s%s" % (color_name(t.g), style, "  (rare!)" if is_dark(t.g) or style == "heart" else ""),
                 "Traits: " + (", ".join(traits(t.g)) or "Average")]
        jokes = [TRAIT_JOKES[k] for k in traits(t.g) if k in TRAIT_JOKES]
        if jokes:                                             # ちょっとユーモラスな性格の説明
            random.Random(t.id).shuffle(jokes)
            lines += ["  \u2022 " + j for j in jokes[:3]]
        if t.name:                                            # 識別個体: これまでの一生
            sv = t.stats
            lines.append("Life so far: ate %d seaweed, %d jellyfish; %d children, %d descendants alive" % (
                sv["plants"], sv["jelly"], self.kids.get(t.id, sv["kids"]), len(self.descendants_alive(t.id))))
            lines.append("Surfed %d, cleaned %d, escaped sharks %d, got sick %d%s" % (
                sv["surf"], sv["clean"], sv["escape"], sv["sick"], "   \u2606 Born under a lucky star" if t.lucky else ""))
        p = self.by_id.get(t.partner)
        fr = self.friends(t)
        if p or fr:
            lines.append(("Partner: %s   " % self.tag(p) if p else "") +
                         ("Friends: " + ", ".join("#%d" % f.id for f in fr[:4]) if fr else ""))
        o = t.origin
        if o == "native":
            org = "Native (born on this beach)"
        elif o.startswith("family:"):
            org = "Born here - family of the %s" % o[7:]
        else:
            grp, _, day = o.partition("|")
            org = "Newcomer: %s (arrived on Day %s)" % (grp, day or "?")
        lines.append("Group: " + org)
        if t.parents and t.parents != "arrived from far away":
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
                                    "Hatchlings get startled"],
                        "ghost": ["Ghost crab", "A fast night runner. It hunts hatchlings",
                                  "crawling to the sea!"],
                        "octopus": ["Octopus", "A clever night hunter that changes color"],
                        "comb": ["Comb jelly", "Its rows of tiny paddles flash rainbow lights"],
                        "moray": ["Moray eel", "Lives in the rocks. Turtles keep their distance"],
                        "squid": ["Squid", "A school out hunting in the moonlight"],
                        "bird": ["Frigatebird", "A seabird. It hunts hatchlings on the beach!"]}[v.kind]
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
        if start is None:
            start = self.clock() - seconds
        self._off_ts = start                                  # 実時刻
        seconds = min(max(0.0, seconds) * TIME_SCALE, OFFLINE_MAX)   # カメの時間に直す
        if seconds >= OFFLINE_MAX:                            # 長すぎる留守は最後の30日分だけ計算する
            self._off_ts = self.clock() - OFFLINE_MAX / TIME_SCALE
        b0, d0, l0 = self.births, self.deaths, self.laid
        steps = int(seconds // OFFLINE_STEP)
        rest = seconds - steps * OFFLINE_STEP
        for i in range(steps + 1):
            dt = OFFLINE_STEP if i < steps else rest
            if dt > 0:
                self._offline_step(dt)
        n_j = len(self.jellies)                               # クラゲは数だけ引き継ぎ、海の中に散らばす
        self.jellies = []
        for _ in range(n_j):
            x, y = self.water_point(30)
            self.jellies.append(Jelly(x, y, random.choice((-4, 4))))
        self.shark = None
        self.visitors = []
        self.update_daylight(turtle_clock(self.clock()), log=False)
        for t in self.turtles:
            t.emote, t.food, t.target, t.surf, t.vis, t.goal = None, None, None, None, None, None
            if t.state not in ("sleep", "dead"):
                t.state = "swim"
        self._decompose(force=True)
        return self.births - b0, self.deaths - d0, self.laid - l0

    def _offline_step(self, dt):
        """dt はカメの時間。"""
        self.time += dt / TIME_SCALE
        self.bio_time += dt
        self._off_ts = getattr(self, "_off_ts", self.clock()) + dt / TIME_SCALE
        self.update_daylight(turtle_clock(self._off_ts), log=False)
        self._grow_plants(dt)
        self._jellies_offline(dt)
        alive = self.alive()
        self._pop = len(alive) + len(self.eggs)
        self._food_per = self.edible_food() / max(1, len(alive))
        self.by_id = {t.id: t for t in alive}
        random.shuffle(alive)
        shift = self.appetite_shift()
        for t in alive:
            t.age += dt
            t.mate_cd -= dt
            self._stored_clutch(t, dt)
            awake = t.awake_len / (t.awake_len + t.sleep_len) * (1 - 0.8 * t.night_pull(self.night))
            t.energy -= t.metab * dt * (awake + SLEEP_METAB * (1 - awake))
            t.joy = max(0.0, t.joy - 0.015 * dt)
            t.annoy = max(0.0, t.annoy - 0.02 * dt)
            if self._illness(t, dt):
                continue
            tries = 0
            while t.energy < min(0.92 if 15 <= self.hour < 20 else 0.7, t.eat_below + shift) and tries < 6:
                tries += 1
                if not t.herbivore and len(self.jellies) > 2 and random.random() < 0.25:
                    self.jellies.pop()
                    t.energy += JELLY_ENERGY
                    t.stats["jelly"] += 1
                    continue
                p = max(self.plants, key=lambda p: p.b, default=None)
                if p is None or p.b < self.edible_line(t):
                    break
                bite = p.b - NIBBLE_FLOOR                   # 根元は残す
                p.b = NIBBLE_FLOOR
                t.energy += bite * (1.5 if t.herbivore else 0.9)
                t.stats["plants"] += bite
            t.energy = min(1.0, t.energy)
            if t.energy <= 0:
                self._kill(t, "starvation")
            elif t.age >= t.lifespan:
                self._kill(t, "old age")
        if random.random() < dt / TIME_SCALE / (sum(SHARK_GAP) / 2) * 0.12:   # サメに食べられるのはまれ
            big = [t for t in self.turtles if t.alive and t.scale >= SHARK_PREY_SCALE]
            if big:
                self._kill(random.choice(big), "being eaten", killer="a shark")
        self._decompose(force=True)
        if self.night > 0.5:
            for e in list(self.eggs):                  # 卵がかえるのは夜
                if e.t - dt <= 0:
                    self.eggs.remove(e)
                    t = Turtle(e.g, e.x, self.shore(e.x) - 15, e.generation, age=0.0, sex=e.sex,
                               lineage=e.lineage, parents=e.parents)
                    self._born(t, e.mom, e.dad)
                    t.energy = HATCH_ENERGY
                    self.births += 1
                    if random.random() < self.hatchling_leave():
                        self.departed = getattr(self, "departed", 0) + 1
                    else:
                        self.turtles.append(t)
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
                if random.random() < 0.3 and self._can_mate(f) and self._can_mate(m):
                    self.mates_today = getattr(self, "mates_today", 0) + 1
                    self._mate(f, m)
        self._immigrants(dt, offline=True)
        self._crisis(dt)
        self._emigrate(dt, offline=True)
        self._decompose(force=True)
        self._record(dt)

    # ---- 保存
    def to_dict(self):
        return {"version": VERSION, "w": self.w, "h": self.h,
                "turtles": [t.to_dict() for t in self.turtles if t.alive and t.state != "depart"],
                "eggs": [e.to_dict() for e in self.eggs],
                "plants": [[p.x, p.y, p.b, p.m] for p in self.plants],
                "meadows": {str(k): v for k, v in self.meadows.items()}, "next_meadow": self.next_meadow,
                "reefs": [r.to_list() for r in self.reefs],
                "births": self.births, "deaths": self.deaths, "laid": self.laid,
                "merges": self.merges, "splits": self.splits, "max_gen": self.max_gen,
                "n_lineages": self.n_lineages, "gene_pool": self.gene_pool,
                "events": self.events, "history": self.history, "settings": self.settings,
                "bio_time": self.bio_time,
                "family": {str(k): v for k, v in list(self.family.items())[-4000:]},
                "kids": {str(k): v for k, v in self.kids.items() if k in self.family or
                         any(t.id == k for t in self.turtles)},
                "memorials": self.memorials[-20:], "n_sharks": getattr(self, "n_sharks", 0)}

    @classmethod
    def from_dict(cls, d):
        wd = cls(d.get("w", 700), d.get("h", 440))
        if d.get("reefs"):
            wd.reefs = [Reef(*r) for r in d["reefs"]]
            ver = tuple(int(x) for x in str(d.get("version", "0")).split(".")[:2] if x.isdigit())
            for rf in wd.reefs:                                      # 旧版: 部品の間隔を広げる
                k = (1.35 if ver < (7, 2) else 1.0) * (1.5 if ver < (7, 3) and rf.kind == "rock" else 1.0)
                if k != 1.0:
                    rf.parts = [(p[0] * k, p[1] * k, p[2], p[3]) for p in rf.parts]
                    rf.recenter()
            if sum(r.kind == "rock" for r in wd.reefs) < 5:        # 旧版: 岩場を 5 か所に
                lt = wd.land_top
                for fx, fy in ((0.70, 0.18), (0.05, 0.80), (0.95, 0.40))[:5 - sum(r.kind == "rock" for r in wd.reefs)]:
                    wd.reefs.append(Reef(wd.w * fx, lt * fy, "rock", random.randrange(10 ** 6)))
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
        wd.bio_time = d.get("bio_time", 0.0)
        wd.family = {int(k): tuple(v) for k, v in d.get("family", {}).items()}
        wd.kids = {int(k): v for k, v in d.get("kids", {}).items()}
        wd.memorials = d.get("memorials", [])
        wd.n_sharks = d.get("n_sharks", 0)
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


CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".umigame_pet_config.json")


def choose_save_dir(root, ask=False, current=None):
    """保存先のフォルダ。初回(設定ファイルが無いとき)は、フォルダを選ぶ画面を出して聞く。
    選んだ場所は ホーム/.umigame_pet_config.json に覚えておく(O キーで変えられる)。"""
    env = os.environ.get("UMIGAME_SAVE_DIR")
    if env and not ask:
        return env, True
    default, on_drive = find_save_dir()
    if not ask:
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                d = json.load(f).get("save_dir")
            if d:
                return d, ("Google" in d or "マイドライブ" in d or "My Drive" in d)
        except (OSError, ValueError):
            pass
    try:
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        if not ask:
            mb.showinfo("Sea Turtle Colony",
                        "Choose a folder to save your turtle colony.\n"
                        "(A Google Drive folder lets the colony follow you to other PCs.)\n\n"
                        "Suggested: %s" % default, parent=root)
        base = os.path.dirname(current or default)
        d = fd.askdirectory(title="Where should the turtle colony be saved?",
                            initialdir=base if os.path.isdir(base) else os.path.expanduser("~"),
                            parent=root)
    except Exception:
        d = ""
    if not d:
        if ask:
            return current, True
        d = default
    elif os.path.basename(d) != "UmigamePet":
        d = os.path.join(d, "UmigamePet")
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"save_dir": d}, f, ensure_ascii=False)
    except OSError:
        pass
    return d, ("Google" in d or "マイドライブ" in d or "My Drive" in d or d == default and on_drive)


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
    "bubbles": ({"X": "#e6fbff", "o": "#9fe2ff"}, ("...XX", "..X.oX", "...XX.", ".X....", "XoX...", ".X....")),
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
                ("#c9a2ff", "#9a72d6", "#e7d6ff"), ("#ffe27a", "#d6b64a", "#fff2b8"),
                ("#f4f4f0", "#c8c8c0", "#ffffff"))          # 最後は白化したサンゴ
ROCK_COLORS = ("#8395a6", "#5f7182", "#aebdca")
FISH_ART = {   # 右向き(左が尾びれ、右が頭)
    "yellow": ({"X": "#ffe04a", "e": "#222222"}, ("X.XXX..", "XXXXXeX", "X.XXX..")),
    "blue": ({"X": "#3f7fff", "y": "#ffe04a", "e": "#111111"}, ("y.XXX..", "yXXXXeX", "y.XXX..")),
    "clown": ({"X": "#ff8a2a", "w": "#ffffff", "e": "#222222"}, ("X.XwXw.", "XXXwXeX", "X.XwXw.")),
}
EGG_CRACK = (".X..", "XX.X", "X.XX", ".XX.")
SEABIRD_ART = (                 # グンカンドリ(上から見た、上向き)。右向きに回して使う
    (".....X.....", "XX..XXX..XX", ".XXXXXXXXX.", "..XX.X.XX..", ".....X.....", "....X.X...."),
    (".....X.....", "....XXX....", "..XXXXXXX..", ".XX..X..XX.", "XX...X...XX", "....X.X...."))
NIGHT_ART = {   # 夜行性の生き物(右向き)
    # スナガニ(上から。横歩き)
    "ghost": ({"X": "#efe2c0", "x": "#c9b88f", "e": "#222222"},
              (("x.e...e.x", ".xXXXXXx.", "xXXXXXXXx", ".xXXXXXx.", "x.x...x.x"),
               (".xe...ex.", "x.XXXXX.x", "xXXXXXXXx", "x.XXXXX.x", ".x.x.x.x."))),
    # タコ(上から。右が頭、うしろに8本の腕)
    # ウツボ(岩から顔を出す)
    "moray": ({"X": "#9aa23a", "x": "#6a7a2a", "e": "#ffef9a", "w": "#ffffff"},
              ((".xXXXX...", "xXXXXeX..", "XXXXXXwX.", ".xXXXXXX."),
               (".xXXX....", "xXXXeXX..", "XXXXXwXX.", ".xXXXX..."))),
    # イカ(上から。右が頭)
    "squid": ({"X": "#e8c8d8", "x": "#c09ab0", "e": "#7ff8ff"},
              (("x.xXXXX.", "xxXXXXeX", "x.xXXXX."), (".x.XXXX.", "xxXXXXeX", ".x.XXXX."))),
    "octopus": ({"X": "#c0563c", "x": "#9a3e2a", "e": "#ffe9a0"},
                (("x.x.x.......", ".xxxxx.XXX..", "xxxxxXXXXXX.", "..xxXXXeXXXX", "xxxxxXXXXXX.",
                  ".xxxxx.XXX..", "x.x.x......."),
                 (".x.x.x......", "x.xxxx.XXX..", ".xxxxXXXXXX.", "xxxxXXXeXXXX", ".xxxxXXXXXX.",
                  "x.xxxx.XXX..", ".x.x.x......"))),
}
COMB_ART = (".XXX.", "XaXbX", "XbXcX", "XcXaX", "XaXbX", ".XXX.")
COMB_COLORS = ("#ff6b9d", "#6bffb8", "#6bb8ff", "#fff36b")
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
    """甲羅の色。パステルを基本に、模様は同じ系統の少し濃い色(補色にしないので毒々しくならない)。
    まれな個体(dark 遺伝子が高い)は、真珠色か金色。"""
    h = pastel_hue(g["hue"])
    h2 = (h + (g["hue2"] - 0.5) * 0.14) % 1.0          # 近い色相だけ
    if is_dark(g):
        if g["hue2"] > 0.5:                           # 真珠色
            return ("#f7f4ee", "#d8d2c8", "#ece4f4", "#fbf8f2")
        return (hexcol(0.12, 0.42, 1.0), hexcol(0.11, 0.5, 0.82), hexcol(0.09, 0.5, 0.95),   # 金色
                hexcol(0.13, 0.16, 0.98))
    return (hexcol(h, 0.28, 0.97), hexcol(h, 0.40, 0.80), hexcol(h2, 0.40, 0.88),
            hexcol(h + 0.03, 0.12, 0.98))


def turtle_pixels(g, frame, mode):
    """mode: normal / belly / dead / breathe / eat / weak。上向きの色の格子(breathe は縦に長い)。"""
    if mode == "weak":                        # 弱っている: 色が薄く、くすむ
        px = turtle_pixels(g, frame, "normal")
        return [[(mix_hex(c, "#a0a4aa", 0.45) if c else None) for c in row] for row in px]
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
    """k = (R倍率, G倍率, B倍率[, 光の赤, 緑, 青, 強さ])。朝焼け・夕焼けは真っ赤な光を重ねる。"""
    out = tuple(min(255, int(c * m)) for c, m in zip(rgb, k[:3]))
    if len(k) > 3 and k[6] > 0:
        a = k[6]
        out = tuple(min(255, int(c + (g - c) * a)) for c, g in zip(out, k[3:6]))
    return out


def sky_glow(h):
    """朝焼け・夕焼けの赤い光 (R, G, B, 強さ)。"""
    sr, ss = SUNRISE, SUNSET
    a1 = 0.42 * math.exp(-((h - (sr + 0.25)) / 0.6) ** 2)
    a2 = 0.52 * math.exp(-((h - (ss - 0.05)) / 0.65) ** 2)
    if a1 >= a2:
        return (255, 70, 40, a1)
    return (255, 38, 24, a2)


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
    return {"Sunrise": 1.0, "Sunset": 1.0, "Dusk": 0.45, "Dawn twilight": 0.35, "Night": 0.9}.get(world.phase, 0.3)


# ---------------------------------------------------------------- サウンド(標準ライブラリで合成)
SR = 22050                     # サンプリング周波数
SOUND_VER = 3                  # 音を作り直したら上げる(キャッシュのファイル名に入る)
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
    # サメ: 低い半音の繰り返しがだんだん速くなり、不協和なうなりが重なる(おどろおどろしい)
    pulses = []
    for i, gap in enumerate((0.42, 0.34, 0.27, 0.2, 0.15, 0.11, 0.08, 0.06)):
        f = 82 if i % 2 == 0 else 87
        pulses.append(_tone(f, 0.16, 0.36, 0.005, 0.1, harm=0.8) + [0.0] * int(SR * gap))
    drone = _add(_tone(58, 2.6, 0.16, 0.6, 0.8, harm=0.5), _tone(82, 2.6, 0.08, 0.8, 0.8, freq2=79))
    drone = _add(drone, _tone(116, 2.4, 0.06, 1.0, 0.6, freq2=123), 0.2)               # 増4度のうなり
    s["shark"] = _add(drone, _seq(*pulses))
    # サメの襲撃: 不協和な強打と、高く引きつる音、低い衝撃
    stab = _add(_tone(110, 0.9, 0.26, 0.003, 0.6, harm=0.9), _tone(155.6, 0.9, 0.2, 0.003, 0.6, harm=0.6))
    stab = _add(stab, _tone(1480, 0.7, 0.08, 0.003, 0.5, freq2=1570))
    stab = _add(stab, _tone(2093, 0.5, 0.05, 0.003, 0.4, freq2=2217), 0.05)
    s["attack"] = _add(_add(stab, _noise(0.5, 0.3, 0.08, 0.002, 0.3)), _tone(45, 0.7, 0.4, 0.002, 0.5), 0.0)
    # イルカ: キュイキュイと口笛、クリック音のはずむ遊び声
    whistle = [_tone(f0, d, 0.09, 0.005, 0.06, freq2=f1)
               for f0, f1, d in ((1800, 3200, 0.12), (3000, 2200, 0.1), (2200, 3600, 0.14), (3400, 2600, 0.12))]
    clicks = _seq(*[_noise(0.012, 0.2, 0.7, 0.001, 0.005) for _ in range(7)], gap=0.03)
    s["dolphin"] = _add(_seq(*whistle, gap=0.05), clicks, 0.62)
    # マンタ: ゆったり楽しげな、マリンバのような上りのアルペジオ
    s["manta"] = _seq(*[_add(_tone(f, 0.28, 0.12, 0.003, 0.22), _tone(f * 4, 0.12, 0.03, 0.002, 0.08))
                        for f in (523, 659, 784, 880, 1047, 1319)], gap=0.0)
    s["whoosh"] = _noise(0.6, 0.22, 0.03, 0.15, 0.3, lp2=0.35)
    s["bell"] = _add(_tone(1046, 1.2, 0.1, 0.003, 0.5), _tone(2093, 0.8, 0.04, 0.003, 0.3))
    # 大波: 遠くから低いうなりが近づき、大きく砕ける
    roar = _noise(4.0, 0.7, 0.008, 1.6, 1.2, lp2=0.06, rnd=random.Random(3))
    s["bigwave"] = _add(roar, _noise(2.2, 0.55, 0.05, 0.05, 1.6, lp2=0.4, rnd=random.Random(4)), 1.8)
    s["crash"] = _add(_noise(2.0, 0.65, 0.3, 0.01, 1.4, lp2=0.04, rnd=random.Random(5)),
                      _tone(55, 0.8, 0.35, 0.005, 0.6))
    s["chomp"] = _add(_noise(0.2, 0.35, 0.25, 0.002, 0.06), _tone(60, 0.25, 0.35, 0.002, 0.1))
    s["sparkle"] = _seq(*[_tone(f, 0.06, 0.08, 0.002, 0.04) for f in (2093, 2637, 3136)])
    # 交尾: ゆったりした恋の和音(ふるえる音)ときらきら
    love = _seq(*[_tone(f, 0.22, 0.10, 0.02, 0.25, harm=0.2) for f in (523, 659, 784, 1047)])
    s["love"] = _add(love, s["sparkle"], 0.75)
    for k, v in s.items():                                     # 音割れしないように
        peak = max(abs(x) for x in v) or 1.0
        if peak > 0.9:
            s[k] = [x * 0.9 / peak for x in v]
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
             "hatch", "lay", "death", "shark", "dolphin", "whoosh", "bell", "bigwave", "chomp", "sparkle", "love",
             "attack", "manta", "crash"]
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
               "merge": "sparkle", "split": "sparkle", "time": "bell", "clean": "note", "sad": "death",
               "depart": "whoosh", "crisis": "bigwave", "coral": None}
EMOTE_SOUND = {"note": "note", "flower": "note", "star": "note", "heart": "heart", "blush": "heart",
               "anger": "anger", "surprise": "surprise", "bang": "surprise", "sparkle": "sparkle"}


def event_sound(kind, text):
    if kind == "shark":
        if text.startswith("A shark appeared"):
            return "shark"
        return "attack" if ("escaped" in text or "attacking" in text) else None
    if kind == "wave":
        return "bigwave" if "coming" in text else "crash" if "flipped" in text else None
    if kind == "visitor":
        return "dolphin" if "dolphin" in text else "manta" if "manta" in text else None
    if kind == "play":
        return "dolphin" if "dolphin" in text else "manta" if "manta" in text else "note"
    return EVENT_SOUND.get(kind)


# ---------------------------------------------------------------- 画面(tkinter)
class App:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk()
        self.save_dir, self.on_drive = choose_save_dir(self.root)   # 初回は保存先を聞く
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
            self.banner = ("While you were away: %s passed (%s in turtle time)\nBorn %d   Died %d   Eggs laid %d"
                           % (fmt_dur(away), fmt_dur(min(away * TIME_SCALE, OFFLINE_MAX)), b, d, l))
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
        self.glitter = [c.create_line(0, 0, 1, 1, width=2, state="hidden", tags="glit") for _ in range(44)]
        self.rel_lines = []
        self.glit_t = 0.0
        self.light_t = 0.0
        self.rel_t = 0.0
        self.fx_items = []
        self.hud = c.create_text(8, 6, anchor="nw", fill="#04505c", font=("", 9), tags="ui")
        self.graph_box = c.create_rectangle(0, 0, 1, 1, fill="#e9fbf8", outline="#6cc9c9", tags="ui")
        self.graph_title = c.create_text(0, 0, anchor="nw", text="Ecosystem (last 2 days)",
                                         fill="#04505c", font=("", 8), tags="ui")
        self.graph_lines = [c.create_line(0, 0, 1, 1, fill=col, width=2, tags="ui")
                            for col in ("#1d4e89", "#21a35a", "#d24fa8")]
        self.graph_legend = [c.create_text(0, 0, anchor="nw", fill=col, font=("", 8), tags="ui")
                             for col in ("#1d4e89", "#16864a", "#b0338a")]
        self.log_items = [c.create_text(8, 0, anchor="sw", fill="#6b4a12", font=("", 9), tags="ui")
                          for _ in range(3)]
        self.help = c.create_text(0, 0, anchor="sw", fill="#9a7a3c", font=("", 8), tags="ui",
                                  text="Click: status  Dbl-click: flip  Stroke: pet  Click water: jellyfish  "
                                       "Right-click water: seaweed  T: on top  L: lineage  R: friends")
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
        self.long_job = None
        self.press = None
        self.memo_items = []
        self.memo_seen = len(self.world.memorials)
        self.draw_background()

        c.bind("<Motion>", self.on_motion)
        c.bind("<Leave>", self.on_leave)
        c.bind("<Button-1>", self.on_click)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Double-Button-1>", self.on_double)
        c.bind("<Shift-Button-1>", self.on_shift_click)
        c.bind("<Button-3>", self.on_shift_click)             # 右クリック: 海藻を植える
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            c.bind("<Button-2>", self.on_shift_click)         # macOS の右クリック
        for k in ("t", "T"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_topmost)
        c.bind("<Configure>", self.on_resize)
        for k in ("l", "L"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_lineage)
        for k in ("r", "R"):
            self.root.bind("<KeyPress-%s>" % k, self.toggle_rel)
        for k in ("w", "W"):
            self.root.bind("<KeyPress-%s>" % k, lambda e: self.toggle_sound("waves"))
        for k in ("o", "O"):                     # 保存先を変える
            self.root.bind("<KeyPress-%s>" % k, lambda e: self.change_save_dir())
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
        glow = tuple(bg[3:6]) + (bg[6] * 0.5,) if len(bg) > 3 else (0, 0, 0, 0.0)
        sp = tuple(0.45 + 0.55 * min(1.1, x) for x in bg[:3]) + glow     # 生き物は背景より少し明るく、赤みは半分
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
        nk = tuple(max(0.8, x) for x in sp[:3]) + sp[3:]     # 夜の生き物は夜でも見えるように
        for kind, (cols, frames) in NIGHT_ART.items():
            for f, art in enumerate(frames):
                self.vis_img[(kind, 1, f)] = self._img(art, cols, 2, nk)
                self.vis_img[(kind, 3, f)] = self._img(tuple(r[::-1] for r in art), cols, 2, nk)
                if kind == "octopus":                    # 色を変えたタコ
                    c2 = dict(cols, X="#e8c8a8", x="#b89878")
                    self.vis_img[(kind + "2", 1, f)] = self._img(art, c2, 2, nk)
                    self.vis_img[(kind + "2", 3, f)] = self._img(tuple(r[::-1] for r in art), c2, 2, nk)
        for f, art in enumerate(SEABIRD_ART):            # 海鳥(右向き)
            rart = tuple("".join(rw) for rw in rotate(art, 1))
            cols = {"X": "#2c2c36"}
            self.vis_img[("bird", 1, f)] = self._img(rart, cols, 2, sp)
            self.vis_img[("bird", 3, f)] = self._img(tuple(rw[::-1] for rw in rart), cols, 2, sp)
        self.egg_crack_img = self._img(EGG_CRACK, {"X": "#fffdf2"}, 2, sp)
        for f in range(2):                               # クシクラゲ: 虹色が流れる(光るので色みをかけない)
            cc = COMB_COLORS[f:] + COMB_COLORS[:f]
            img = self._img(COMB_ART, {"X": "#d8f0ff", "a": cc[0], "b": cc[1], "c": cc[2]}, 2)
            self.vis_img[("comb", 1, f)] = self.vis_img[("comb", 3, f)] = img
        self.reef_img = {}
        for piece, art in REEF_ART.items():
            for ci in range(5):
                if piece.startswith("rock"):
                    cols = dict(zip("Xxo", ROCK_COLORS))
                else:
                    cols = dict(zip("Xxo", CORAL_COLORS[ci]))
                self.reef_img[(piece, ci)] = self._img(art, cols, 5 if piece.startswith("rock") else 4, sp)
        for ent in getattr(self, "items", {}).values():
            ent[3].clear()
            ent[4] = None
        for tab in getattr(self, "tables", {}).values():
            for ent in tab.values():
                ent[1] = None

    def apply_light(self):
        w = self.world
        gr, gg, gb, ga = sky_glow(w.hour)
        q = tuple(round(x * 20) / 20 for x in w.tint) + (gr, gg, gb, round(ga * 20) / 20)
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
        """水面のきらめき。夏の真昼は海全体がキラキラ、朝焼け・夕焼けは真っ赤な光の道、夜は月光で銀色にきらめく。"""
        c, w = self.canvas, self.world
        amount = sparkle_amount(w)
        n = int(len(self.glitter) * amount)
        pal = {"Daytime": ("#fbffff", "#ffffe0"), "Sunrise": ("#ff6a3a", "#ffb347", "#ffd27a", "#ff8a5a"),
               "Sunset": ("#ff4a2a", "#ff8a3a", "#ffc060", "#ff6a4a"), "Dusk": ("#e9a2d8", "#ffb0a0"),
               "Dawn twilight": ("#d6e4ff", "#ffc8d8"), "Night": ("#f4f8ff", "#cfe0ff", "#ffffff", "#e0e8ff")}
        cols = pal.get(w.phase, ("#ffffff",))
        spread = w.phase == "Daytime"
        cx = w.w * (0.15 + 0.7 * (((w.hour % 24) / 24.0 * 2) % 1.0))
        for i, it in enumerate(self.glitter):
            if i >= n or random.random() < 0.3:
                c.itemconfigure(it, state="hidden")
                continue
            if spread or (w.phase == "Night" and i % 3 == 0):     # 夜は月の道のほかに、海じゅうに銀の粒
                x, y = random.uniform(0, w.w), random.uniform(6, w.land_top * 0.95)
                ln = random.uniform(1.0, 4)
            else:
                y = random.uniform(8, w.land_top * 0.9)
                width = 18 + y * (0.25 if w.phase in ("Sunrise", "Sunset") else 0.12)
                x = cx + random.gauss(0, width)
                ln = random.uniform(3, 12)
            c.coords(it, x - ln, y, x + ln, y)
            c.itemconfigure(it, fill=random.choice(cols), state="normal")

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
        self.draw_reefs()
        self.order_dirty = True
        self.layout_ui()

    def draw_reefs(self):
        """サンゴ礁と岩場(サンゴが育ったり減ったりしたら描き直す)。"""
        c, w, k = self.canvas, self.world, self.bg_tint
        for it in getattr(self, "reef_items2", []):
            c.delete(it)
        self.reef_items2 = []
        w.reef_changed = False
        for r in w.reefs:
            for dx, dy, piece, ci in sorted(r.parts, key=lambda p: p[1]):
                self.reef_items2.append(c.create_image(round(r.x + dx), round(r.y + dy),
                                                       image=self.reef_img[(piece, ci)], tags="reef"))
        self.order_dirty = True

    def update_meadows(self):
        """藻場の地面の楕円は描かない(陸地まではみ出して見苦しいため、Ver 7.0 で廃止)。"""
        c, w = self.canvas, self.world
        w.meadow_changed = False
        for mid in list(self.meadow_items):
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
        if kind == "hearts":                        # 交尾: ハートがふわふわ立ちのぼる
            for _ in range(3):
                it = c.create_image(x, y, image=self.emote_img["heart"], tags="fx")
                self.fx_items.append([it, kind, x + random.uniform(-14, 14), y, 0.0, random.uniform(1.2, 1.8),
                                      random.uniform(-8, 8), random.uniform(-30, -18)])
            self.order_dirty = True
            return
        if kind == "tear":                          # 産卵: 涙がこぼれる
            it = c.create_oval(x - 1.5, y - 2, x + 1.5, y + 2, fill="#9fdcff", outline="#ffffff", tags="fx")
            self.fx_items.append([it, kind, x, y, 0.0, 0.9, random.uniform(-4, 4), 14])
            self.order_dirty = True
            return
        if kind == "sparkle":                       # ふ化: きらきら
            for _ in range(5):
                a = random.uniform(0, math.tau)
                px, py = x + math.cos(a) * random.uniform(4, 14), y + math.sin(a) * random.uniform(4, 10)
                for dx1, dy1, dx2, dy2 in ((-3, 0, 3, 0), (0, -3, 0, 3)):
                    it = c.create_line(px + dx1, py + dy1, px + dx2, py + dy2, fill="#fff7a8", tags="fx")
                    self.fx_items.append([it, "peck", px, py, 0.0, 0.7, 0, 0])
            self.order_dirty = True
            return
        if kind == "plankton":                      # 夜光虫: 泳いだあとが青く光る
            it = c.create_rectangle(x, y, x + 3, y + 3, fill=random.choice(("#8ff8ff", "#5fe0ff", "#c8ffff")),
                                    width=0, tags="fx")
            self.fx_items.append([it, kind, x, y, 0.0, random.uniform(0.6, 1.1), 0, 0])
            self.order_dirty = True
            return
        if kind == "gulp":                          # 株を丸ごと食べた: 緑の輪
            it = c.create_oval(x, y, x, y, outline="#5ee08a", width=2, tags="fx")
            self.fx_items.append([it, "pop", x, y, 0.0, 0.5])
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
            if kind in ("hearts", "tear"):
                px, py = x + f[6] * t, y + f[7] * t
                if kind == "hearts":
                    c.coords(it, round(px), round(py))
                else:
                    c.coords(it, px - 1.5, py - 2, px + 1.5, py + 2)
                keep.append(f)
                continue
            if kind == "plankton":
                sz = 3 * (1 - t / life) + 0.5
                c.coords(it, x, y, x + sz, y + sz)
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
        """押した瞬間: 長押し(0.7秒)の準備。離したときにクリックとして扱う。"""
        if self.click_job:
            self.root.after_cancel(self.click_job)
            self.click_job = None
        t = self.world.hit(e.x, e.y, pad=6)
        self.press = (t, e.x, e.y)
        if self.long_job:
            self.root.after_cancel(self.long_job)
        self.long_job = self.root.after(700, lambda: self.on_long(t)) if t else None

    def on_release(self, e):
        if self.press is None:
            return
        t, x, y = self.press
        self.press = None
        if self.long_job:                         # 長押しになる前に離した = ふつうのクリック
            self.root.after_cancel(self.long_job)
            self.long_job = None
            self.click_job = self.root.after(280, lambda: self.on_single(t, x, y))
        elif t is None:
            self.click_job = self.root.after(280, lambda: self.on_single(None, x, y))

    def on_long(self, t):
        """長押し: 気に入った個体を識別個体にして名前をつける。"""
        self.long_job = None
        if t is None or not t.alive:
            return
        self.name_turtle(t)

    def name_turtle(self, t, heir_of=None):
        import tkinter.simpledialog as sd
        default = t.name or random.choice(("Kame", "Umi", "Sango", "Nami", "Hoshi", "Sora", "Mochi", "Kai",
                                           "Luna", "Coral", "Pearl", "Marin", "Taro", "Hana"))
        title = "Follow an heir" if heir_of else "Name this turtle"
        prompt = ("Name for #%d, a descendant of %s:" % (t.id, heir_of)) if heir_of else \
            ("Give #%d (%s, Lineage %s) a name.\nYou can follow its whole life." % (
                t.id, "female" if t.sex == "F" else "male", t.lineage))
        name = sd.askstring(title, prompt, initialvalue=default, parent=self.root)
        if name:
            t.name = name.strip()[:16] or default
            self.follow = t.id
            self.panel_t = 0.0
            self.world.event("name", "%s is now being followed" % self.world.tag(t))
            self.sound.play("sparkle")

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
        if self.long_job:
            self.root.after_cancel(self.long_job)
            self.long_job = None
        self.press = None
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

    def change_save_dir(self):
        d = choose_save_dir(self.root, ask=True, current=self.save_dir)[0]
        if d and d != self.save_dir:
            self.save_dir = d
            try:
                save_world(self.world, d)
            except OSError:
                pass
            self.banner, self.banner_t = "Now saving to:\n%s" % d, 3.0

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
        """1コマ進める。思わぬエラーが起きても止まらず、内容を一度だけ表示して記録する。"""
        try:
            self._tick()
        except Exception:
            import traceback
            msg = traceback.format_exc()
            print(msg, file=sys.stderr)
            try:
                with open(os.path.join(self.save_dir, "error_log.txt"), "a", encoding="utf-8") as f:
                    f.write("%s  Ver %s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), VERSION, msg))
            except OSError:
                pass
            if not getattr(self, "error_shown", False):
                self.error_shown = True
                try:
                    import tkinter.messagebox as mb
                    mb.showerror("Sea Turtle Colony", "An error occurred (the colony keeps running).\n\n" + msg[-1500:])
                except Exception:
                    pass
            self.last = time.monotonic()
            self.root.after(TICK_MS, self.tick)

    def _tick(self):
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
        if t.eat_cd > 0 and t.state in ("food", "swim"):      # もぐもぐ(食べ終わってもしばらく噛む)
            return (t.dir, int(t.anim / 0.14) % 2, "eat", t.scale)
        if t.state == "cleaning":                       # 気持ちよさそうに、ひれをゆっくり
            return (t.dir, int(t.anim / 0.9) % 2, "normal", t.scale)
        if t.state == "lay":                            # 産卵: 掘る・砂をかける間はひれを速く動かす
            digging = t.state_t > LAY_TIME * 0.7 or t.state_t < LAY_TIME * 0.25
            return (t.dir, int(t.anim / 0.12) % 2 if digging else 0, "normal", t.scale)
        if t.state in ("sleep", "petted", "idle", "nap", "drift"):
            return (t.dir, 0, "weak" if w.weak(t) else "normal", t.scale)
        if t.state == "surf":
            return (t.dir, 1, "normal", t.scale)
        water = w.in_water(t.x, t.y)
        period = 0.2 if t.state in ("flee", "food", "flee_shark", "play", "flirt", "mating") else \
            (0.6 if not water else 0.45)
        if w.weak(t):
            return (t.dir, int(t.anim / 0.9) % 2, "weak", t.scale)
        if t.groggy > 0:
            period = 0.9
        return (t.dir, int(t.anim / period) % 2, "normal", t.scale)

    def render(self, dt):
        c, w = self.canvas, self.world
        if w.reef_changed:
            self.draw_reefs()
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
        self._sync("egg", w.eggs, lambda e: self.egg_crack_img if (getattr(e, "shake", None) or 9) < 1.2
                   else self.egg_img, move=False)
        etab = self.tables["egg"]
        for e in w.eggs:                                # ふ化の前に卵がゆれる
            sh = getattr(e, "shake", None)
            if sh is not None:
                ent = etab.get(id(e))
                if ent:
                    c.coords(ent[0], round(e.x + math.sin(w.time * 30) * 1.5), round(e.y))
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
                   lambda v: self.vis_img[(v.kind + ("2" if getattr(v, "shell", 0) or getattr(v, "color", 0) else ""),
                                           v.dir, int(v.anim / (0.25 if v.kind in ("dolphin", "ghost") else 0.5)) % 2)])

        seen = set()
        for t in w.turtles:
            seen.add(t.id)
            ent = self.items.get(t.id)
            if ent is None:
                ent = [c.create_image(t.x, t.y, tags="turtle"), None, None, {}, None, None, None]
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
            if t.name:                                   # 識別個体の名前(星つき)
                nx, ny = round(t.x), round(t.y + t.radius + 8)
                if ent[6] is None:
                    ent[6] = (c.create_text(nx + 1, ny + 1, text="\u2605 " + t.name, fill="#3a2a10",
                                            font=("", 9, "bold"), tags="fx"),
                              c.create_text(nx, ny, text="\u2605 " + t.name, fill="#fff2a0",
                                            font=("", 9, "bold"), tags="fx"))
                    self.order_dirty = True
                else:
                    c.coords(ent[6][0], nx + 1, ny + 1)
                    c.coords(ent[6][1], nx, ny)
        for tid in list(self.items):
            if tid not in seen:
                ent = self.items.pop(tid)
                if ent[6]:
                    for it in ent[6]:
                        c.delete(it)
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

        if self.order_dirty:                                          # カメはいつも一番手前(見やすく)
            for tag in ("bg", "glit", "meadow", "plant", "reef", "wave", "bg2", "egg", "fish", "jelly",
                        "rel", "visitor", "shark", "turtle", "fishtop", "fx", "ui", "panel", "tip", "memo"):
                c.tag_raise(tag)
            self.order_dirty = False

        self.hud_t -= dt
        if self.hud_t <= 0:
            self.hud_t = 1.0
            alive = w.alive()
            nf = sum(t.sex == "F" for t in alive)
            herb = sum(t.herbivore for t in alive)
            names = {"dolphin": "Dolphin", "manta": "Manta", "hermit": "Hermit crab", "ghost": "Ghost crab",
                     "octopus": "Octopus", "comb": "Comb jelly", "coconut": "Coconut crab",
                     "moray": "Moray eel", "squid": "Squid", "bird": "Frigatebird"}
            cnt = {}
            for v in w.visitors:
                cnt[names[v.kind]] = cnt.get(names[v.kind], 0) + 1
            vis = [n + (" x%d" % k if k > 1 else "") for n, k in cnt.items()]
            if w.shark:
                vis.append("SHARK!")
            c.itemconfigure(self.hud, text=(
                "Day %d  %s %s   Turtles %d (F%d M%d, herb %d / omni %d)   Eggs %d   Gen %d\n"
                "Seaweed %d   Jellyfish %d   Born %d   Died %d   Merged %d   Split %d\n%s"
                % (int(w.bio_time // 86400) + 1, time.strftime("%H:%M", time.localtime(w.now_ts)), w.phase,
                   len(alive), nf,
                   len(alive) - nf, herb, len(alive) - herb, len(w.eggs), w.max_gen,
                   len(w.plants), len(w.jellies), w.births, w.deaths, w.merges, w.splits,
                   ("Visitors: " + ", ".join(vis)) if vis else "")))
            for i, it in enumerate(self.log_items):
                k = len(w.events) - len(self.log_items) + i
                line = ("%s  %s" % (w.events[k][0], w.events[k][2])) if k >= 0 else ""
                room = max(30, int((w.w - 300) / 6.2))            # 右下の音量表示と重ならない長さ
                c.itemconfigure(it, text=line if len(line) <= room else line[:room - 1] + "\u2026")
            self.draw_graph()

        self.update_panel(dt)
        if w.night > 0.55:                              # 夜光虫
            for t in w.turtles:
                if t.alive and abs(t.vx) + abs(t.vy) > 6 and random.random() < dt * 3 and w.in_water(t.x, t.y):
                    hx, hy = t.head()
                    self.add_fx("plankton", 2 * t.x - hx + random.uniform(-4, 4), 2 * t.y - hy + random.uniform(-4, 4))
            for v in w.visitors:
                if v.kind in ("octopus", "comb", "dolphin", "manta") and random.random() < dt * 2:
                    self.add_fx("plankton", v.x + random.uniform(-8, 8), v.y + random.uniform(-6, 6))
        if len(w.memorials) > self.memo_seen and not self.memo_items:
            self.show_memorial(w.memorials[self.memo_seen])
            self.memo_seen += 1
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

    def show_memorial(self, m):
        """識別個体が亡くなったときのメッセージ。子孫を選んで追いかけることもできる。"""
        c, w = self.canvas, self.world
        self.close_memorial()
        self.sound.play("death")
        lines = m["lines"]
        heirs = [w.by_id[i] for i in m.get("heirs", []) if i in w.by_id][:3]
        txt = c.create_text(0, 0, anchor="nw", fill="#3a2e1e", font=("", 10), text="\n".join(lines[1:]),
                            tags="memo")
        title = c.create_text(0, 0, anchor="nw", fill="#6a3a10", font=("", 13, "bold"),
                              text="\u2605 " + lines[0], tags="memo")
        bb = c.bbox(txt)
        wid = max(bb[2] - bb[0], c.bbox(title)[2] - c.bbox(title)[0]) + 28
        hgt = (bb[3] - bb[1]) + 82
        x0, y0 = (w.w - wid) / 2, max(8, (w.h - hgt) / 2 - 20)
        box = c.create_rectangle(x0, y0, x0 + wid, y0 + hgt, fill="#fff8e6", outline="#c8963c", width=3, tags="memo")
        c.tag_lower(box, txt)                         # 文字を箱の上に
        c.coords(title, x0 + 14, y0 + 10)
        c.coords(txt, x0 + 14, y0 + 38)
        items = [box, title, txt]
        bx, by = x0 + 14, y0 + hgt - 26
        label = c.create_text(bx, by, anchor="w", fill="#6a5a40", font=("", 9),
                              text="Mark one of the closest descendants?" if heirs else "No descendants alive.",
                              tags="memo")
        items.append(label)
        bx = c.bbox(label)[2] + 10
        for h in heirs:
            b = c.create_text(bx, by, anchor="w", fill="#0a6e78", font=("", 10, "bold"),
                              text="[#%d %s]" % (h.id, "F" if h.sex == "F" else "M"), tags="memo")
            c.tag_bind(b, "<Button-1>", lambda e, h=h, n=m["name"]: self.follow_heir(h, n))
            items.append(b)
            bx = c.bbox(b)[2] + 8
        close = c.create_text(x0 + wid - 14, by, anchor="e", fill="#a0502a", font=("", 10, "bold"),
                              text="[No, thanks]" if heirs else "[Close]", tags="memo")
        c.tag_bind(close, "<Button-1>", lambda e: self.close_memorial())
        items.append(close)
        self.memo_items = items
        c.tag_raise("memo")

    def close_memorial(self):
        for it in self.memo_items:
            self.canvas.delete(it)
        self.memo_items = []
        self.press = None
        if self.click_job:
            self.root.after_cancel(self.click_job)
            self.click_job = None

    def follow_heir(self, h, ancestor):
        self.close_memorial()
        self.root.after(50, lambda: self.name_turtle(h, heir_of=ancestor) if h.alive else None)

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
        x = min(max(4, x), w.w - pw - 4)
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
        cur = (sum(t.alive for t in self.world.turtles), self.world.edible_food(),
               len(self.world.jellies))
        data = list(h) + [cur]
        names = ("Turtles %d", "Food %.1f", "Jellyfish %d")
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
