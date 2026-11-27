# -*- coding: utf-8 -*-
"""
ウミガメ群体 — デスクトップで動く人工生命の小さなペット

・標準ライブラリだけで動く(tkinter)。pip install 不要。
・ドット絵(上から見たウミガメ、インベーダー風)。スプライトは個体ごとに1回だけ作って使い回す。
・遺伝的アルゴリズム: 遺伝子(色・模様・速さ・寿命・代謝・社交性・気性・眠りやすさ・大きさ)を
  交尾で交叉+突然変異して子に渡す。えさを取れない個体は餓死し、よく食べる個体が子を残す(自然選択)。
・泳ぐ / 寝る / 食べる / 交尾して卵を産む / 近縁どうしで合体する / 寿命で死ぬ。
・マウス: 近づけると寄ってくる(または嫌がって逃げる)。カメをクリック=ひっくり返る。
  水をクリック=えさ(クラゲ)を落とす。右クリック=最前面に固定の切り替え。
・ウインドウを閉じると群体を Google ドライブ(パソコン版 Google ドライブの同期フォルダ)に保存。
  次に起動すると、閉じていた実時間ぶん群体の時間を進める(留守中の誕生・死亡もまとめて計算)。

保存先の優先順:
  1) 環境変数 UMIGAME_SAVE_DIR
  2) Google ドライブの同期フォルダ(G:\\マイドライブ, G:\\My Drive, ~/Google Drive/My Drive,
     macOS の ~/Library/CloudStorage/GoogleDrive-*/My Drive など)の下の UmigamePet/
  3) 見つからなければ ホーム/UmigamePet/ (ウインドウのタイトルに「ローカル保存」と出る)
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

VERSION = "1.0.0"

# ---------------------------------------------------------------- 時間・世界の定数
TICK_MS = 100                 # 画面更新の間隔(10fps)。最小化中は 1秒ごとに処理だけ進める
MAX_POP = 24                  # 個体+卵の上限(処理を軽く保つため)
ADULT_AGE = 20 * 60           # 大人になる年齢(秒)
MATE_COOLDOWN = 15 * 60       # 交尾後の休み(秒)
EGG_TIME = 3 * 60             # 卵がかえるまで(秒)
FOOD_INTERVAL = 14.0          # えさが自然に湧く間隔(秒)
FOOD_MAX = 6
FOOD_ENERGY = 0.35
MERGE_KIN = 0.13              # この遺伝距離より近い個体どうしが合体候補
MAX_SCALE = 5                 # ドットの拡大率の上限(合体で大きくなる)
OFFLINE_STEP = 60.0           # 留守中の計算の刻み(秒)
OFFLINE_MAX = 7 * 24 * 3600   # 留守中の計算は最大7日分
AUTOSAVE_SEC = 300
SAVE_NAME = "colony.json"

FLOAT_GENES = ("hue", "hue2", "speed", "life", "metab", "social",
               "temper", "sleepy", "size")
PATTERN_BITS = 28             # 甲羅の模様(左半分 4列 x 7行、左右対称にする)


# ---------------------------------------------------------------- 遺伝子
def random_genome(rng=random):
    g = {k: rng.random() for k in FLOAT_GENES}
    g["pattern"] = [rng.random() < 0.4 for _ in range(PATTERN_BITS)]
    return g


def crossover(a, b, rng=random):
    """一様交叉。模様は1点交叉(親の模様の塊が残るように)。"""
    child = {k: (a[k] if rng.random() < 0.5 else b[k]) for k in FLOAT_GENES}
    cut = rng.randrange(PATTERN_BITS)
    child["pattern"] = a["pattern"][:cut] + b["pattern"][cut:]
    return child


def mutate(g, rate=0.15, sigma=0.08, rng=random):
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
        if k in ("hue", "hue2"):   # 色相は円なので近い側で平均
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


# ---------------------------------------------------------------- 個体
class Turtle:
    _ids = 0

    def __init__(self, genome, x, y, generation=1, age=0.0, scale=None, tid=None):
        if tid is None:
            Turtle._ids += 1
            tid = Turtle._ids
        else:
            Turtle._ids = max(Turtle._ids, tid)
        self.id = tid
        self.g = genome
        self.x, self.y = x, y
        a = random.uniform(0, math.tau)
        self.vx, self.vy = math.cos(a) * 10, math.sin(a) * 10
        self.heading = a
        self.generation = generation
        self.age = age
        self.energy = 0.7
        self.fatigue = random.random() * 0.6
        self.mate_cd = MATE_COOLDOWN * 0.3
        self.scale = scale if scale else (2 if genome["size"] < 0.5 else 3)
        self.state = "swim"
        self.state_t = 0.0
        self.joy = 0.3
        self.annoy = 0.0
        self.emote = None
        self.emote_t = 0.0
        self.target = None
        self.dead_t = 0.0
        self.anim = random.random()
        self.dir = 0           # 0上 1右 2下 3左
        self.contact = 0.0

    # 遺伝子から決まる性質
    @property
    def max_speed(self):
        return (14 + 34 * self.g["speed"]) * (1.0 - 0.08 * (self.scale - 2))

    @property
    def lifespan(self):
        return (4 + 8 * self.g["life"]) * 3600 * (1 + 0.2 * (self.scale - 2))

    @property
    def metab(self):
        return 0.0005 + 0.0007 * self.g["metab"] + 0.0003 * self.g["speed"]

    @property
    def awake_len(self):
        return 500 + 1000 * (1 - self.g["sleepy"])

    @property
    def sleep_len(self):
        return 90 + 240 * self.g["sleepy"]

    @property
    def radius(self):
        return 5.5 * self.scale

    @property
    def alive(self):
        return self.state != "dead"

    def can_mate(self):
        return (self.alive and self.state in ("swim", "court") and self.age > ADULT_AGE
                and self.energy > 0.6 and self.mate_cd <= 0)

    def say(self, emote, sec=1.6):
        self.emote, self.emote_t = emote, sec

    def to_dict(self):
        return {"id": self.id, "g": self.g, "x": self.x, "y": self.y, "gen": self.generation,
                "age": self.age, "energy": self.energy, "fatigue": self.fatigue,
                "mate_cd": self.mate_cd, "scale": self.scale,
                "sleep": self.state == "sleep", "joy": self.joy, "annoy": self.annoy}

    @classmethod
    def from_dict(cls, d):
        t = cls(d["g"], d["x"], d["y"], d["gen"], d["age"], d["scale"], d["id"])
        t.energy, t.fatigue, t.mate_cd = d["energy"], d["fatigue"], d["mate_cd"]
        t.joy, t.annoy = d.get("joy", 0.3), d.get("annoy", 0.0)
        if d.get("sleep"):
            t.state = "sleep"
        return t


class Egg:
    def __init__(self, genome, x, y, generation, t=EGG_TIME):
        self.g, self.x, self.y, self.generation, self.t = genome, x, y, generation, t

    def to_dict(self):
        return {"g": self.g, "x": self.x, "y": self.y, "gen": self.generation, "t": self.t}


class Food:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.phase = random.random() * math.tau


# ---------------------------------------------------------------- 世界(描画と無関係な部分)
class World:
    def __init__(self, w=520, h=340):
        self.w, self.h = w, h
        self.turtles = []
        self.eggs = []
        self.foods = []
        self.food_t = 0.0
        self.births = 0
        self.deaths = 0
        self.merges = 0
        self.max_gen = 1
        self.gene_pool = []      # 絶滅したときの再出発用
        self.cursor = None       # (x, y) / None
        self.cursor_speed = 0.0
        self.log = []            # 描画側へのイベント(合体・誕生など)

    # ---- 初期化
    def seed(self, n=6):
        for _ in range(n):
            t = Turtle(random_genome(), random.uniform(40, self.w - 40),
                       random.uniform(40, self.h - 40))
            t.age = random.uniform(0.05, 0.3) * t.lifespan
            t.mate_cd = random.uniform(0, MATE_COOLDOWN)
            self.turtles.append(t)

    def population(self):
        return sum(t.alive for t in self.turtles) + len(self.eggs)

    def oldest(self):
        alive = [t for t in self.turtles if t.alive]
        return max(alive, key=lambda t: t.age) if alive else None

    # ---- 1フレーム分
    def step(self, dt):
        dt = min(dt, 0.5)
        self._spawn_food(dt)
        for f in self.foods:
            f.phase += dt
            f.y = min(self.h - 6, f.y + 3 * dt)
            f.x += math.sin(f.phase * 1.3) * 4 * dt
        self._hatch(dt)
        alive = [t for t in self.turtles if t.alive]
        for t in list(self.turtles):
            self._update_turtle(t, dt, alive)
        self._pairs(alive, dt)
        self.turtles = [t for t in self.turtles if not (t.state == "dead" and t.dead_t > 9)]
        if not self.turtles and not self.eggs:
            self._refound()

    def _spawn_food(self, dt):
        self.food_t += dt
        if self.food_t >= FOOD_INTERVAL:
            self.food_t = 0.0
            if len(self.foods) < FOOD_MAX:
                self.foods.append(Food(random.uniform(15, self.w - 15), random.uniform(10, self.h * 0.4)))

    def drop_food(self, x, y):
        if len(self.foods) < FOOD_MAX + 6:
            self.foods.append(Food(x, y))

    def _hatch(self, dt):
        for e in list(self.eggs):
            e.t -= dt
            if e.t <= 0:
                self.eggs.remove(e)
                t = Turtle(e.g, e.x, e.y, e.generation)
                t.energy = 0.6
                t.say("sparkle", 2.5)
                self.turtles.append(t)
                self.births += 1
                self.max_gen = max(self.max_gen, e.generation)
                self.log.append(("hatch", t))

    def _refound(self):
        """絶滅したら、遺伝子の記憶から卵が2つ流れ着く。"""
        pool = self.gene_pool or [random_genome(), random_genome()]
        for _ in range(2):
            g = mutate(random.choice(pool), rate=0.4)
            self.eggs.append(Egg(g, random.uniform(40, self.w - 40),
                                 random.uniform(40, self.h - 40), self.max_gen + 1, EGG_TIME * 0.3))

    def _remember(self, g):
        self.gene_pool.append(g)
        self.gene_pool = self.gene_pool[-10:]

    def _kill(self, t):
        t.state, t.dead_t = "dead", 0.0
        t.emote = None
        self.deaths += 1
        self._remember(t.g)

    # ---- 1体の行動
    def _update_turtle(self, t, dt, alive):
        t.anim += dt
        if t.emote_t > 0:
            t.emote_t -= dt
            if t.emote_t <= 0:
                t.emote = None
        if t.state == "dead":
            t.dead_t += dt
            t.vx *= 0.95
            t.vy = -6          # 仰向けで浮き上がっていく
            t.x += t.vx * dt
            t.y = max(-20, t.y + t.vy * dt)
            return

        t.age += dt
        t.mate_cd -= dt
        t.joy = max(0.0, t.joy - 0.015 * dt)
        t.annoy = max(0.0, t.annoy - 0.02 * dt)
        sleeping = t.state == "sleep"
        t.energy -= t.metab * dt * (0.35 if sleeping else 1.0)
        if sleeping:
            t.fatigue -= dt / t.sleep_len
        else:
            t.fatigue += dt / t.awake_len
        if t.energy <= 0 or t.age >= t.lifespan:
            self._kill(t)
            return

        t.state_t -= dt
        # 状態の切り替え
        if t.state in ("flipped", "dance"):
            if t.state_t <= 0:
                if t.state == "flipped":
                    if t.annoy > 0.5:
                        t.say("anger")
                        t.state, t.state_t = "flee", 2.0
                    else:
                        t.joy = min(1.0, t.joy + 0.4)
                        t.say("note")
                        t.state, t.state_t = "dance", 1.2
                else:
                    t.state = "swim"
        elif t.state == "sleep":
            if t.fatigue <= 0:
                t.state = "swim"
            elif random.random() < dt / 3:
                t.say("zzz", 1.5)
        elif t.state == "flee" and t.state_t > 0:
            pass
        else:
            t.state = "swim"
            if t.fatigue > 1 and t.energy > 0.12:
                t.state = "sleep"
                t.say("zzz", 2)
            elif t.energy < 0.55 and self.foods:
                t.state = "food"
            elif t.can_mate() and self.population() < MAX_POP:
                partner = self._find_partner(t, alive)
                if partner:
                    t.state, t.target = "court", partner
            if t.energy < 0.2 and random.random() < dt / 6:
                t.say("sweat")

        self._steer(t, dt)

    def _find_partner(self, t, alive):
        best, bd = None, 260.0
        for o in alive:
            if o is t or not o.can_mate():
                continue
            d = math.hypot(o.x - t.x, o.y - t.y)
            # 近すぎる近縁とは交尾しにくい(近交を避ける)
            if distance(t.g, o.g) < 0.04:
                d *= 3
            if d < bd:
                best, bd = o, d
        return best

    def _steer(self, t, dt):
        sp = t.max_speed
        dx = dy = 0.0
        speed_mul = 1.0
        if t.state == "sleep":
            speed_mul = 0.0
        elif t.state == "flipped":
            speed_mul = 0.0
        elif t.state == "dance":
            speed_mul = 0.2
            t.dir = int(t.anim / 0.15) % 4
        elif t.state == "food" and not self.foods:   # 先に食べられた
            t.state = "swim"
        elif t.state == "food":
            f = min(self.foods, key=lambda f: (f.x - t.x) ** 2 + (f.y - t.y) ** 2)
            dx, dy = f.x - t.x, f.y - t.y
            speed_mul = 1.2
            if math.hypot(dx, dy) < t.radius + 4:
                self.foods.remove(f)
                t.energy = min(1.0, t.energy + FOOD_ENERGY)
                t.joy = min(1.0, t.joy + 0.15)
                if random.random() < 0.4:
                    t.say("note", 1.2)
        elif t.state == "court":
            o = t.target
            if o is None or not o.alive or not o.can_mate():
                t.state, t.target = "swim", None
            else:
                dx, dy = o.x - t.x, o.y - t.y
                if random.random() < dt / 2:
                    t.say("heart", 1.0)
        elif t.state == "flee" and self.cursor:
            dx, dy = t.x - self.cursor[0], t.y - self.cursor[1]
            speed_mul = 1.5

        # マウスへの反応(寝ている・ひっくり返っている時は無視)
        if self.cursor and t.state in ("swim", "court", "food"):
            cx, cy = self.cursor
            d = math.hypot(cx - t.x, cy - t.y)
            if d < 160:
                like = t.g["social"] * 0.8 + t.joy * 0.3 - t.annoy * 1.1
                if self.cursor_speed > 900 and d < 90:   # 急に動かすとびっくり
                    t.say("bang", 0.8)
                    t.annoy = min(1.0, t.annoy + 0.12 * t.g["temper"] + 0.02)
                    t.state, t.state_t = "flee", 0.8
                elif like > 0.3 and t.state == "swim":
                    if d > 22:
                        dx, dy = cx - t.x, cy - t.y
                        speed_mul = 1.1
                    else:
                        speed_mul = 0.15
                        t.joy = min(1.0, t.joy + 0.08 * dt)
                        if random.random() < dt / 2.5:
                            t.say("heart" if t.joy > 0.6 else "note", 1.2)
                elif like < 0.05:
                    dx, dy = t.x - cx, t.y - cy
                    speed_mul = 1.3
                    if t.annoy > 0.45 and random.random() < dt / 2:
                        t.say("anger", 1.2)
                if d < 45:  # 近くにずっといると、気の短い個体はうっとうしがる
                    t.annoy = min(1.0, t.annoy + max(0.0, t.g["temper"] - 0.3) * 0.08 * dt)

        if dx == 0 and dy == 0:
            # 気ままに泳ぐ(機嫌が良いと少し速く、イライラしているとジグザグ)
            jitter = 0.6 + 2.5 * t.annoy
            t.heading += random.gauss(0, jitter) * dt
            dx, dy = math.cos(t.heading), math.sin(t.heading)
            speed_mul *= 0.55 + 0.4 * t.joy
        else:
            t.heading = math.atan2(dy, dx)
        n = math.hypot(dx, dy) or 1.0
        tx, ty = dx / n * sp * speed_mul, dy / n * sp * speed_mul
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
        if t.y < m or t.y > self.h - m:
            t.vy = -t.vy
            t.heading = -t.heading
            t.y = min(max(t.y, m), self.h - m)
        if t.state not in ("dance",) and abs(t.vx) + abs(t.vy) > 2:
            if abs(t.vx) > abs(t.vy):
                t.dir = 1 if t.vx > 0 else 3
            else:
                t.dir = 2 if t.vy > 0 else 0

    # ---- 個体どうし(交尾・合体・押し合い)
    def _pairs(self, alive, dt):
        n = len(alive)
        removed = set()
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
                # 押し合い
                push = (r - d) * 0.5
                a.x -= dx / d * push * 0.5
                a.y -= dy / d * push * 0.5
                b.x += dx / d * push * 0.5
                b.y += dy / d * push * 0.5
                if a.state == "court" and a.target is b and b.can_mate() and a.can_mate():
                    self._mate(a, b)
                    continue
                if (a.state in ("swim", "food") and b.state in ("swim", "food")
                        and max(a.scale, b.scale) < MAX_SCALE
                        and distance(a.g, b.g) < MERGE_KIN):
                    hungry = a.energy < 0.3 and b.energy < 0.3
                    if random.random() < dt * (0.5 if hungry else 0.01):
                        removed.update((a.id, b.id))
                        self._merge(a, b)
                        break

    def _mate(self, a, b):
        a.mate_cd = MATE_COOLDOWN * (0.8 + 0.4 * random.random())
        b.mate_cd = MATE_COOLDOWN * (0.8 + 0.4 * random.random())
        a.energy -= 0.2
        b.energy -= 0.2
        a.state = b.state = "swim"
        a.target = b.target = None
        a.say("heart", 2.0)
        b.say("heart", 2.0)
        n = 1 + (random.random() < 0.35)
        for _ in range(n):
            if self.population() >= MAX_POP:
                break
            g = mutate(crossover(a.g, b.g))
            self.eggs.append(Egg(g, (a.x + b.x) / 2 + random.uniform(-8, 8),
                                 (a.y + b.y) / 2 + random.uniform(-8, 8),
                                 max(a.generation, b.generation) + 1))
        self.log.append(("mate", a))

    def _merge(self, a, b):
        g = blend(a.g, b.g)
        t = Turtle(g, (a.x + b.x) / 2, (a.y + b.y) / 2,
                   max(a.generation, b.generation), min(a.age, b.age),
                   min(MAX_SCALE, max(a.scale, b.scale) + 1))
        t.energy = min(1.0, a.energy + b.energy)
        t.joy = 0.8
        t.say("sparkle", 2.5)
        self.turtles = [x for x in self.turtles if x is not a and x is not b]
        self.turtles.append(t)
        for o in self.turtles:
            if o.target in (a, b):
                o.target, o.state = None, "swim"
        self.merges += 1
        self.log.append(("merge", t))

    # ---- マウス操作
    def hit(self, x, y):
        best, bd = None, 1e9
        for t in self.turtles:
            if not t.alive:
                continue
            d = math.hypot(t.x - x, t.y - y)
            if d < t.radius + 4 and d < bd:
                best, bd = t, d
        return best

    def poke(self, t):
        if t.state == "sleep":
            t.annoy = min(1.0, t.annoy + 0.25 + 0.4 * t.g["temper"])
            t.fatigue = min(t.fatigue, 0.6)
            t.state, t.state_t = "flipped", 1.5
            t.say("anger" if t.annoy > 0.5 else "question", 1.5)
            return
        t.annoy = min(1.0, t.annoy + 0.1 + 0.35 * t.g["temper"])
        t.state, t.state_t = "flipped", 2.5
        t.say("bang", 1.0)

    # ---- 留守中の時間経過(粗い刻みでまとめて計算)
    def advance_offline(self, seconds):
        seconds = min(max(0.0, seconds), OFFLINE_MAX)
        b0, d0 = self.births, self.deaths
        steps = int(seconds // OFFLINE_STEP)
        rest = seconds - steps * OFFLINE_STEP
        for i in range(steps + 1):
            dt = OFFLINE_STEP if i < steps else rest
            if dt <= 0:
                continue
            self._offline_step(dt)
        # 戻ってきたときの状態を整える
        self.foods = []
        for t in self.turtles:
            t.emote = None
            if t.state not in ("sleep", "dead"):
                t.state = "swim"
        self.turtles = [t for t in self.turtles if t.state != "dead"]
        return self.births - b0, self.deaths - d0

    def _offline_step(self, dt):
        alive = [t for t in self.turtles if t.alive]
        # えさは平均的な湧き方で、お腹のすいた個体から配る
        supply = FOOD_ENERGY * dt / FOOD_INTERVAL
        for t in sorted(alive, key=lambda t: t.energy):
            if supply <= 0:
                break
            need = min(1.0 - t.energy, supply, FOOD_ENERGY)
            if t.energy < 0.55:
                t.energy += need
                supply -= need
        for t in alive:
            t.age += dt
            t.mate_cd -= dt
            # 起きている時間と寝ている時間の比で平均した代謝
            awake = t.awake_len / (t.awake_len + t.sleep_len)
            t.energy -= t.metab * dt * (awake + 0.35 * (1 - awake))
            t.joy = max(0.0, t.joy - 0.015 * dt)
            t.annoy = max(0.0, t.annoy - 0.02 * dt)
            if t.energy <= 0 or t.age >= t.lifespan:
                self._kill(t)
        for e in list(self.eggs):
            e.t -= dt
            if e.t <= 0:
                self.eggs.remove(e)
                t = Turtle(e.g, random.uniform(30, self.w - 30), random.uniform(30, self.h - 30),
                           e.generation, age=-e.t)
                self.turtles.append(t)
                self.births += 1
                self.max_gen = max(self.max_gen, e.generation)
        mates = [t for t in self.turtles if t.can_mate()]
        random.shuffle(mates)
        while len(mates) >= 2 and self.population() < MAX_POP:
            a = mates.pop()
            b = min(mates, key=lambda o: abs(distance(a.g, o.g) - 0.2))
            mates.remove(b)
            if random.random() < 0.5:
                self._mate(a, b)
        self.turtles = [t for t in self.turtles if t.alive]
        if not self.turtles and not self.eggs:
            self._refound()
        self.log.clear()

    # ---- 保存
    def to_dict(self):
        return {"version": VERSION, "w": self.w, "h": self.h,
                "turtles": [t.to_dict() for t in self.turtles if t.alive],
                "eggs": [e.to_dict() for e in self.eggs],
                "births": self.births, "deaths": self.deaths, "merges": self.merges,
                "max_gen": self.max_gen, "gene_pool": self.gene_pool}

    @classmethod
    def from_dict(cls, d, w=None, h=None):
        wd = cls(d.get("w", 520), d.get("h", 340))
        wd.turtles = [Turtle.from_dict(x) for x in d.get("turtles", [])]
        wd.eggs = [Egg(e["g"], e["x"], e["y"], e["gen"], e["t"]) for e in d.get("eggs", [])]
        wd.births, wd.deaths = d.get("births", 0), d.get("deaths", 0)
        wd.merges, wd.max_gen = d.get("merges", 0), d.get("max_gen", 1)
        wd.gene_pool = d.get("gene_pool", [])
        if w and h:
            wd.resize(w, h)
        return wd

    def resize(self, w, h):
        if w < 50 or h < 50:
            return
        sx, sy = w / self.w, h / self.h
        for o in self.turtles + self.eggs + self.foods:
            o.x *= sx
            o.y *= sy
        self.w, self.h = w, h


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
    "heart": ("#ff5a7a", (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X...")),
    "note": ("#ffe066", ("...XXX.", "...X.X.", "...X...", "...X...", ".XXX...", "XXXX...", ".XX....")),
    "anger": ("#ff3030", (".X...X.", "XX...XX", ".......", ".......", "XX...XX", ".X...X.")),
    "zzz": ("#9fd8ff", ("XXXXX", "...X.", "..X..", ".X...", "XXXXX")),
    "bang": ("#ffffff", (".X.", ".X.", ".X.", ".X.", "...", ".X.")),
    "question": ("#ffffff", (".XXX.", "X...X", "...X.", "..X..", ".....", "..X..")),
    "sparkle": ("#7ff9ff", ("...X...", "...X...", "..XXX..", "XXXXXXX", "..XXX..", "...X...", "...X...")),
    "sweat": ("#5aa8ff", ("..X..", ".XXX.", "XXXXX", "XXXXX", ".XXX.")),
}
JELLY = (".XXX.", "XXXXX", "X.X.X", "X.X.X")
EGG = (".XX.", "XXXX", "XXXX", ".XX.")


def rotate(grid, d):
    """上向きの格子を d(0上 1右 2下 3左)の向きへ回す。"""
    g = [list(r) for r in grid]
    for _ in range(d):
        g = [list(r) for r in zip(*g[::-1])]   # 時計回り90度
    return g


def hexcol(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def turtle_pixels(g, frame, mode):
    """mode: normal / belly(ひっくり返り)/ dead。上向き 11x11 の色の格子を返す。"""
    base = FRAMES[frame]
    shell = hexcol(g["hue"], 0.55, 0.62)
    rim = hexcol(g["hue"], 0.6, 0.38)
    pat = hexcol(g["hue2"], 0.6, 0.9)
    skin = hexcol(g["hue"] + 0.08, 0.35, 0.78)
    eye = "#101010"
    if mode == "belly":
        shell, rim, pat = "#f2e6b0", "#b8a870", "#d9c98e"
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
                else:
                    if mode == "belly":
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
class App:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.save_dir, self.on_drive = find_save_dir()
        self.root = tk.Tk()
        self.root.title("ウミガメ群体" + ("" if self.on_drive else "(ローカル保存)"))
        self.root.geometry("520x340")
        self.root.minsize(240, 160)
        self.canvas = tk.Canvas(self.root, width=520, height=340, bg="#0b2a4a",
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self.topmost = False

        world, away = load_world(self.save_dir)
        self.banner = None
        if world is None:
            self.world = World(520, 340)
            self.world.seed()
            self.banner = "ようこそ。ウミガメの群体が生まれました"
        else:
            self.world = world
            b, d = world.advance_offline(away)
            self.banner = "留守の間に %s 経過   誕生 %d   死亡 %d" % (fmt_dur(away), b, d)
        self.banner_t = 8.0

        self.items = {}       # turtle.id -> (image_item, emote_item, cache dict, last_key)
        self.food_items = {}
        self.egg_items = {}
        self.emote_img = {k: self._make_img(px, col, 2) for k, (col, px) in EMOTES.items()}
        self.jelly_img = self._make_img(JELLY, "#ff9ad5", 2)
        self.egg_img = self._make_img(EGG, "#f5f0e0", 2)
        self.bubbles = []
        for _ in range(5):
            x, y = random.uniform(0, 520), random.uniform(0, 340)
            self.bubbles.append([self.canvas.create_oval(x, y, x + 4, y + 4, outline="#3d6f99"), x, y,
                                 random.uniform(8, 20)])
        self.hud = self.canvas.create_text(6, 6, anchor="nw", fill="#6f93b5", font=("", 9))
        self.bann = self.canvas.create_text(260, 170, fill="#e8f4ff", font=("", 11, "bold"))
        self.hud_t = 0.0
        self.last = time.monotonic()
        self.last_save = time.monotonic()
        self.prev_cursor = None

        c = self.canvas
        c.bind("<Motion>", self.on_motion)
        c.bind("<Leave>", lambda e: setattr(self.world, "cursor", None))
        c.bind("<Button-1>", self.on_click)
        c.bind("<Button-3>", self.toggle_topmost)
        c.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(TICK_MS, self.tick)

    def _make_img(self, rows, color, scale):
        img = self.tk.PhotoImage(width=len(rows[0]), height=len(rows))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch == "X":
                    img.put(color, to=(x, y))
        return img.zoom(scale)

    def turtle_img(self, t, cache, key):
        img = cache.get(key)
        if img is None:
            d, frame, mode = key
            px = rotate(turtle_pixels(t.g, frame, mode), d)
            raw = self.tk.PhotoImage(width=11, height=11)
            for y, row in enumerate(px):
                for x, col in enumerate(row):
                    if col:
                        raw.put(col, to=(x, y))
            img = raw.zoom(t.scale)
            cache[key] = img
        return img

    # ---- イベント
    def on_motion(self, e):
        now = time.monotonic()
        if self.prev_cursor:
            px, py, pt = self.prev_cursor
            dtm = max(1e-3, now - pt)
            self.world.cursor_speed = math.hypot(e.x - px, e.y - py) / dtm
        self.prev_cursor = (e.x, e.y, now)
        self.world.cursor = (e.x, e.y)

    def on_click(self, e):
        t = self.world.hit(e.x, e.y)
        if t:
            self.world.poke(t)
        else:
            self.world.drop_food(e.x, e.y)

    def toggle_topmost(self, e=None):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.banner, self.banner_t = ("最前面に固定" if self.topmost else "最前面を解除"), 1.5

    def on_resize(self, e):
        self.world.resize(e.width, e.height)
        self.canvas.coords(self.bann, e.width / 2, e.height / 2)

    def on_close(self):
        try:
            save_world(self.world, self.save_dir)
        except OSError as ex:
            print("保存できませんでした:", ex, file=sys.stderr)
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
        if self.root.state() == "iconic":        # 最小化中は描画しない
            self.world.step(dt)
            self.world.log.clear()
            self.root.after(1000, self.tick)
            return
        self.world.step(dt)
        self.world.cursor_speed *= 0.5
        self.world.log.clear()
        self.render(dt)
        self.root.after(TICK_MS, self.tick)

    def render(self, dt):
        c, w = self.canvas, self.world
        seen = set()
        for t in w.turtles:
            seen.add(t.id)
            ent = self.items.get(t.id)
            if ent is None:
                ent = [c.create_image(t.x, t.y), None, {}, None]
                self.items[t.id] = ent
            if t.state == "dead":
                key = (2, 0, "dead")
            elif t.state == "flipped":
                key = (t.dir, int(t.anim / 0.12) % 2, "belly")
            elif t.state == "sleep":
                key = (t.dir, 0, "normal")
            else:
                period = 0.25 if t.state in ("flee", "food") else 0.45
                key = (t.dir, int(t.anim / period) % 2, "normal")
            if key != ent[3]:
                c.itemconfigure(ent[0], image=self.turtle_img(t, ent[2], key))
                ent[3] = key
            c.coords(ent[0], round(t.x), round(t.y))
            if t.emote:
                ey = t.y - t.radius - 10
                if ent[1] is None:
                    ent[1] = c.create_image(t.x, ey, image=self.emote_img[t.emote])
                else:
                    c.itemconfigure(ent[1], image=self.emote_img[t.emote])
                    c.coords(ent[1], round(t.x), round(ey))
            elif ent[1] is not None:
                c.delete(ent[1])
                ent[1] = None
        for tid in list(self.items):
            if tid not in seen:
                ent = self.items.pop(tid)
                c.delete(ent[0])
                if ent[1] is not None:
                    c.delete(ent[1])

        self._sync(self.food_items, w.foods, self.jelly_img)
        self._sync(self.egg_items, w.eggs, self.egg_img)

        for b in self.bubbles:
            b[2] -= b[3] * dt
            if b[2] < -6:
                b[1], b[2] = random.uniform(0, w.w), w.h + 4
            c.coords(b[0], b[1], b[2], b[1] + 4, b[2] + 4)

        self.hud_t -= dt
        if self.hud_t <= 0:
            self.hud_t = 1.0
            n = sum(t.alive for t in w.turtles)
            o = w.oldest()
            c.itemconfigure(self.hud, text="個体 %d  卵 %d  最大世代 %d  誕生 %d  死亡 %d  合体 %d%s" % (
                n, len(w.eggs), w.max_gen, w.births, w.deaths, w.merges,
                ("  最長老 %s" % fmt_dur(o.age)) if o else ""))
        if self.banner:
            self.banner_t -= dt
            c.itemconfigure(self.bann, text=self.banner if self.banner_t > 0 else "")
            c.tag_raise(self.bann)
            if self.banner_t <= 0:
                self.banner = None

    def _sync(self, table, objs, img):
        c = self.canvas
        ids = set()
        for o in objs:
            k = id(o)
            ids.add(k)
            it = table.get(k)
            if it is None:
                table[k] = c.create_image(round(o.x), round(o.y), image=img)
            else:
                c.coords(it, round(o.x), round(o.y))
        for k in list(table):
            if k not in ids:
                c.delete(table.pop(k))

    def run(self):
        self.root.mainloop()


def fmt_dur(sec):
    sec = int(sec)
    if sec < 60:
        return "%d秒" % sec
    if sec < 3600:
        return "%d分" % (sec // 60)
    if sec < 86400:
        return "%d時間%d分" % (sec // 3600, sec % 3600 // 60)
    return "%d日%d時間" % (sec // 86400, sec % 86400 // 3600)


def main():
    try:
        App().run()
    except Exception:
        import traceback
        msg = traceback.format_exc()
        print(msg, file=sys.stderr)
        try:   # ダブルクリック起動ではコンソールがすぐ閉じるので画面に出す
            import tkinter.messagebox as mb
            mb.showerror("ウミガメ群体", msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
