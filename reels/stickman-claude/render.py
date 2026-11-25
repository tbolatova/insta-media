"""Стикмен-Reels: сверху бизнесмен в операционке, снизу я + Claude.
Запуск: python3 render.py  -> stickman.mp4 (1080x1920, 30fps, 15 c, без звука)
"""
import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 17.0
SS = 2  # суперсэмплинг для сглаживания
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def font(size, bold=True):
    k = (int(size * SS), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, max(4, k[0]))
    return _fc[k]

INK = (25, 25, 25)
GREY = (95, 95, 105)
CLAUDE = (217, 119, 87)
PINK = (255, 92, 168)
RED = (226, 59, 59)
GREEN = (38, 166, 91)
HAIR = (60, 38, 30)

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def prog(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def pop(t, a, d=0.35):
    """0 -> 1 с лёгким перелётом (эффект появления)"""
    x = clamp((t - a) / d)
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k


class C:
    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), (255, 255, 255))
        self.d = ImageDraw.Draw(self.im)
    def S(self, *v): return [x * SS for x in v]
    def rect(self, x0, y0, x1, y1, fill, r=0, outline=None, w=0):
        self.d.rounded_rectangle(self.S(x0, y0, x1, y1), radius=r * SS, fill=fill,
                                 outline=outline, width=int(w * SS))
    def circle(self, x, y, r, fill=None, outline=None, w=0):
        self.d.ellipse(self.S(x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=int(w * SS))
    def ellipse(self, x0, y0, x1, y1, fill):
        self.d.ellipse(self.S(x0, y0, x1, y1), fill=fill)
    def seg(self, p, q, col, w):
        self.d.line(self.S(*p, *q), fill=col, width=int(w * SS))
        self.circle(p[0], p[1], w / 2, fill=col)
        self.circle(q[0], q[1], w / 2, fill=col)
    def poly(self, pts, fill, outline=None):
        self.d.polygon([c * SS for p in pts for c in p], fill=fill, outline=outline)
    def arc(self, x, y, r, a0, a1, col, w):
        self.d.arc(self.S(x - r, y - r, x + r, y + r), a0, a1, fill=col, width=int(w * SS))
    def text(self, x, y, s, size, col, bold=True, anchor="mm"):
        self.d.text((x * SS, y * SS), s, font=font(size, bold), fill=col, anchor=anchor)
    def tw(self, s, size, bold=True):
        b = font(size, bold).getbbox(s)
        return (b[2] - b[0]) / SS


def limb(o, a, L):
    r = math.radians(a)
    return (o[0] + math.sin(r) * L, o[1] + math.cos(r) * L)

STAND = dict(la1=-18, la2=-8, ra1=18, ra2=8, ll1=-9, ll2=-9, rl1=9, rl2=9)

def stick(c, x, hip_y, s=1.0, pose=None, col=INK, face="smile", tilt=0,
          extra=None, hair=False, bow=False, tie=False, skirt=False, legs=True):
    p = dict(STAND); p.update(pose or {})
    w = 7 * s
    hip = (x, hip_y)
    sh = (x + tilt * 0.4 * s, hip_y - 72 * s)
    hr = 24 * s
    hc = (sh[0] + tilt * 0.3 * s, sh[1] - hr - 9 * s)
    # ноги
    if legs:
        for a1, a2 in ((p["ll1"], p["ll2"]), (p["rl1"], p["rl2"])):
            k = limb(hip, a1, 42 * s); f = limb(k, a2, 42 * s)
            c.seg(hip, k, col, w); c.seg(k, f, col, w)
    if skirt:
        c.poly([(sh[0], sh[1] + 30 * s), (hip[0] - 26 * s, hip[1] + 14 * s),
                (hip[0] + 26 * s, hip[1] + 14 * s)], fill=(255, 190, 220))
    c.seg(sh, hip, col, w)
    if tie:
        c.poly([(sh[0] - 6 * s, sh[1] + 4 * s), (sh[0] + 6 * s, sh[1] + 4 * s),
                (sh[0] + 7 * s, sh[1] + 42 * s), (sh[0], sh[1] + 52 * s),
                (sh[0] - 7 * s, sh[1] + 42 * s)], fill=RED)
    hands = []
    for a1, a2 in ((p["la1"], p["la2"]), (p["ra1"], p["ra2"])):
        e = limb(sh, a1, 36 * s); hnd = limb(e, a2, 34 * s)
        c.seg(sh, e, col, w); c.seg(e, hnd, col, w)
        hands.append(hnd)
    # голова
    if hair:
        c.rect(hc[0] - hr * 1.22, hc[1] - hr * 1.2, hc[0] + hr * 1.22, hc[1] + hr * 1.75,
               fill=HAIR, r=hr * 1.1)
    c.circle(hc[0], hc[1], hr, fill=(255, 255, 255), outline=col, w=w * 0.85)
    if hair:
        c.d.chord(c.S(hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr), 195, 345, fill=HAIR)
    ex, ey = hc[0], hc[1] + 2 * s
    if face == "panic":
        c.circle(ex - 8 * s, ey - 3 * s, 4 * s, fill=(255, 255, 255), outline=INK, w=2 * s)
        c.circle(ex + 8 * s, ey - 3 * s, 4 * s, fill=(255, 255, 255), outline=INK, w=2 * s)
        c.circle(ex - 8 * s, ey - 3 * s, 1.6 * s, fill=INK); c.circle(ex + 8 * s, ey - 3 * s, 1.6 * s, fill=INK)
        c.seg((ex - 14 * s, ey - 13 * s), (ex - 4 * s, ey - 9 * s), INK, 2.4 * s)
        c.seg((ex + 14 * s, ey - 13 * s), (ex + 4 * s, ey - 9 * s), INK, 2.4 * s)
        c.ellipse(ex - 6 * s, ey + 7 * s, ex + 6 * s, ey + 15 * s, fill=INK)
    else:
        c.circle(ex - 8 * s, ey - 3 * s, 2.6 * s, fill=INK)
        c.circle(ex + 8 * s, ey - 3 * s, 2.6 * s, fill=INK)
        if face == "smile":
            c.arc(ex, ey + 1 * s, 10 * s, 25, 155, INK, 2.6 * s)
        elif face == "o":
            c.circle(ex, ey + 10 * s, 3.5 * s, fill=INK)
        elif face == "sad":
            c.arc(ex, ey + 16 * s, 9 * s, 210, 330, INK, 2.6 * s)
    if bow:
        bx, by = hc[0] + hr * 0.65, hc[1] - hr * 0.85
        c.poly([(bx, by), (bx - 20 * s, by - 13 * s), (bx - 18 * s, by + 12 * s)], fill=PINK)
        c.poly([(bx, by), (bx + 20 * s, by - 13 * s), (bx + 18 * s, by + 12 * s)], fill=PINK)
        c.circle(bx, by, 6 * s, fill=(230, 40, 130))
    return dict(head=hc, hr=hr, hands=hands, hip=hip, sh=sh)


def bubble(c, cx, cy, txt, k, tail=None, size=30, fill=(255, 255, 255), col=INK,
           border=INK, think=False):
    if k <= 0.02: return
    lines = txt.split("\n")
    tw = max(c.tw(l, size) for l in lines)
    lh = size * 1.25
    bw, bh = (tw + 44) * k, (lh * len(lines) + 30) * k
    if tail and not think:
        tx, ty = lerp(cx, tail[0], k), lerp(cy, tail[1], k)
        c.poly([(cx - 16 * k, cy), (cx + 16 * k, cy), (tx, ty)], fill=border)
    c.rect(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, fill=fill, r=22 * k,
           outline=border, w=4 * k)
    if tail and not think:
        c.poly([(cx - 12 * k, cy + bh / 2 - 6 * k), (cx + 12 * k, cy + bh / 2 - 6 * k),
                (lerp(cx, tail[0], k * 0.92), lerp(cy, tail[1], k * 0.92) - 4)], fill=fill)
    if tail and think:
        for i, r in enumerate((10, 7, 5)):
            f = 0.45 + i * 0.2
            c.circle(lerp(cx, tail[0], f), lerp(cy + bh / 2, tail[1], f), r * k,
                     fill=fill, outline=border, w=3 * k)
    if k > 0.55:
        y0 = cy - lh * (len(lines) - 1) / 2
        for i, l in enumerate(lines):
            c.text(cx, y0 + i * lh, l, size * k, col)


def pill(c, cx, cy, txt, size, bg, fg=(255, 255, 255)):
    w = c.tw(txt, size) + 48
    c.rect(cx - w / 2, cy - size * 0.95, cx + w / 2, cy + size * 0.95, fill=bg, r=size)
    c.text(cx, cy, txt, size, fg)


def meter(c, x, y, label, val, col, w=300):
    c.text(x, y, label, 26, INK, anchor="lm")
    lx = x + c.tw(label, 26) + 16
    c.rect(lx, y - 14, lx + w, y + 14, fill=(255, 255, 255), r=14, outline=INK, w=3)
    if val > 0.02:
        c.rect(lx + 4, y - 10, lx + 4 + (w - 8) * val, y + 10, fill=col, r=10)
    c.text(lx + w + 14, y, f"{int(round(val * 100))}%", 26, col, anchor="lm")


def walk(ph, amp=26):
    a = math.sin(ph) * amp
    return dict(ll1=-a, ll2=-a - 8 * (1 + math.sin(ph)), rl1=a, rl2=a - 8 * (1 - math.sin(ph)),
                la1=a * 0.8, la2=a * 0.8 - 10, ra1=-a * 0.8, ra2=-a * 0.8 + 10)


SUIT = (40, 46, 62)
SUIT_D = (26, 30, 42)
TIE = (42, 78, 145)
M_SKIN = (238, 203, 172)
M_HAIR = (52, 36, 28)

def boss(c, x, hip_y, s=1.0, pose=None, face="sad", tilt=0):
    """Бизнесмен по фото: тёмно-синий костюм, белая рубашка, синий галстук, тёмные волосы, щетина."""
    p = dict(STAND); p.update(pose or {})
    hip = (x, hip_y)
    sh = (x + tilt * 0.3 * s, hip_y - 74 * s)
    hr = 26 * s
    hc = (sh[0] + tilt * 0.35 * s, sh[1] - hr - 8 * s)
    # пиджак
    c.poly([(sh[0] - 27 * s, sh[1] - 2 * s), (sh[0] + 27 * s, sh[1] - 2 * s), (hip[0] + 24 * s, hip[1] + 6 * s),
            (hip[0] - 24 * s, hip[1] + 6 * s)], fill=SUIT)
    # рубашка + галстук
    c.poly([(sh[0] - 11 * s, sh[1] - 3 * s), (sh[0] + 11 * s, sh[1] - 3 * s), (sh[0] + 2 * s, sh[1] + 48 * s),
            (sh[0] - 2 * s, sh[1] + 48 * s)], fill=(255, 255, 255))
    c.poly([(sh[0] - 4 * s, sh[1] + 1 * s), (sh[0] + 4 * s, sh[1] + 1 * s), (sh[0] + 5 * s, sh[1] + 40 * s),
            (sh[0], sh[1] + 47 * s), (sh[0] - 5 * s, sh[1] + 40 * s)], fill=TIE)
    c.rect(sh[0] - 4.5 * s, sh[1] - 1 * s, sh[0] + 4.5 * s, sh[1] + 6 * s, fill=(30, 58, 115), r=2 * s)
    # лацканы
    for d in (-1, 1):
        c.seg((sh[0] + d * 11 * s, sh[1] - 2 * s), (sh[0] + d * 2.5 * s, sh[1] + 48 * s), SUIT_D, 2.5 * s)
        c.seg((sh[0] + d * 11 * s, sh[1] - 2 * s), (sh[0] + d * 17 * s, sh[1] + 16 * s), SUIT_D, 2 * s)
    c.circle(sh[0] + 3 * s, sh[1] + 58 * s, 2 * s, fill=SUIT_D)
    # шея и воротник
    c.rect(hc[0] - 7 * s, hc[1] + hr * 0.6, hc[0] + 7 * s, sh[1], fill=M_SKIN)
    for d in (-1, 1):
        c.poly([(sh[0], sh[1] + 2 * s), (sh[0] + d * 10 * s, sh[1] - 6 * s), (sh[0] + d * 11 * s, sh[1] + 3 * s)],
               fill=(245, 245, 248))
    # руки
    hands = []
    for side, a1, a2 in ((-1, p["la1"], p["la2"]), (1, p["ra1"], p["ra2"])):
        so = (sh[0] + side * 22 * s, sh[1] + 4 * s)
        e = limb(so, a1, 36 * s); hnd = limb(e, a2, 33 * s)
        c.seg(so, e, SUIT_D, 16 * s); c.seg(so, e, SUIT, 13 * s)
        c.seg(e, hnd, SUIT_D, 15 * s); c.seg(e, hnd, SUIT, 12 * s)
        c.circle(hnd[0], hnd[1], 6.5 * s, fill=(255, 255, 255))  # манжета
        c.circle(hnd[0] + (hnd[0] - e[0]) * 0.12, hnd[1] + (hnd[1] - e[1]) * 0.12, 6.5 * s, fill=M_SKIN,
                 outline=(200, 160, 130), w=1)
        hands.append(hnd)
    # голова
    fx, fy = hc
    for d in (-1, 1):  # уши
        c.ellipse(fx + d * hr * 0.88 - 5 * s, fy - 3 * s, fx + d * hr * 0.88 + 5 * s, fy + 9 * s, fill=M_SKIN)
    c.ellipse(fx - hr * 0.88, fy - hr * 0.95, fx + hr * 0.88, fy + hr * 1.05, fill=M_SKIN)
    # щетина
    c.d.chord(c.S(fx - hr * 0.88, fy - hr * 0.95, fx + hr * 0.88, fy + hr * 1.05), 28, 152, fill=(214, 180, 152))
    c.ellipse(fx - 9 * s, fy + 6 * s, fx + 9 * s, fy + 12 * s, fill=(205, 168, 140))  # усы
    # волосы — объёмная укладка
    c.d.chord(c.S(fx - hr * 0.95, fy - hr * 1.15, fx + hr * 0.95, fy + hr * 0.05), 180, 360, fill=M_HAIR)
    for ox, oy, r in ((-0.45, -0.95, 0.36), (0.1, -1.1, 0.4), (0.55, -0.95, 0.33), (0.86, -0.45, 0.16), (-0.86, -0.45, 0.16)):
        c.circle(fx + ox * hr, fy + oy * hr, r * hr, fill=M_HAIR)
    c.poly([(fx - hr * 0.3, fy - hr * 0.8), (fx + hr * 0.75, fy - hr * 0.7), (fx + hr * 0.2, fy - hr * 0.55)], fill=M_HAIR)
    # лицо
    ey = fy + 1 * s
    if face == "panic":
        for d in (-1, 1):
            ex = fx + d * 9 * s
            c.circle(ex, ey, 5 * s, fill=(255, 255, 255), outline=(40, 30, 25), w=1.5 * s)
            c.circle(ex, ey, 2 * s, fill=(40, 30, 25))
            c.seg((ex - d * 6 * s, ey - 11 * s), (ex + d * 5 * s, ey - 7 * s), M_HAIR, 2.6 * s)
        c.ellipse(fx - 6 * s, fy + 13 * s, fx + 6 * s, fy + 21 * s, fill=(120, 40, 40))
    else:
        for d in (-1, 1):
            ex = fx + d * 9 * s
            c.ellipse(ex - 3.5 * s, ey - 2.5 * s, ex + 3.5 * s, ey + 3 * s, fill=(40, 30, 25))
            c.seg((ex - d * 5 * s, ey - 10 * s), (ex + d * 5 * s, ey - 7 * s), M_HAIR, 2.6 * s)
        c.arc(fx, fy + 24 * s, 8 * s, 220, 320, (120, 50, 50), 2.6 * s)
    return dict(head=hc, hr=hr, hands=hands, hip=hip, sh=sh)


# ---------------- ВЕРХ: бизнесмен в операционке ----------------
EMPL = [  # время, откуда x, куда x, hip_y, масштаб, вопрос, позиция пузыря
    (0.6, -120, 135, 830, 1.05, "Шеф, где счёт?", (205, 450)),
    (1.6, 1200, 945, 830, 1.05, "Клиент ждёт\nответ!", (870, 450)),
    (2.8, -120, 285, 905, 1.15, "Что постим\nсегодня?", (300, 600)),
    (4.0, 1200, 800, 905, 1.15, "Поставщик из\nКитая звонит!", (780, 600)),
]
EXTRA = [  # пузыри без человечков — нарастающий хаос
    (5.4, "Согласуй ТЗ!", (540, 400)),
    (6.6, "Где отчёт по WB?", (200, 330 + 25)),
    (7.6, "А можно вопрос?", (880, 355)),
    (8.6, "СРОЧНО!!!", (540, 505)),
    (9.4, "Шеф?!", (125, 690)),
    (10.0, "Шеф??", (955, 690)),
]

def top(c, t):
    c.rect(0, 0, W, 960, fill=(253, 236, 232))
    # пол
    c.rect(0, 905, W, 960, fill=(246, 221, 214))
    pill(c, W / 2, 225, "БЕЗ ИИ: я в операционке", 34, RED)
    # часы
    mins = int(lerp(9 * 60, 23 * 60 + 47, prog(t, 0.3, 12.5)))
    c.circle(78, 295, 17, fill=(255, 255, 255), outline=INK, w=3)
    ang = mins / 60 * 30
    c.seg((78, 295), limb((78, 295), 180 - ang, 10), INK, 3)
    c.seg((78, 295), limb((78, 295), 180 - (mins % 60) * 6, 14), INK, 2.5)
    c.text(104, 295, f"{mins // 60:02d}:{mins % 60:02d}", 28, INK, anchor="lm")
    meter(c, 500, 295, "Стресс", lerp(0.15, 0.99, prog(t, 0.5, 11.5)), RED, w=290)

    # стол
    stress = prog(t, 0.5, 11.5)
    shake = math.sin(t * (10 + 25 * stress)) * (2 + 9 * stress)
    bx = 540 + shake * 0.6
    # кого слушает: последний спросивший
    asks = [e for e in EMPL if t > e[0] + 0.6]
    look = 0
    if asks:
        look = -14 if asks[-1][2] < 540 else 14
    if t > 9.0:
        look = math.sin(t * 9) * 16
    if t < 8.2:
        pose = dict(la1=-35, la2=-60 + 20 * math.sin(t * 6), ra1=35, ra2=60 + 20 * math.sin(t * 6 + 1.3))
        if asks:  # разводит руками в сторону спросившего
            side = 1 if asks[-1][2] > 540 else -1
            pose.update({("ra1" if side > 0 else "la1"): 95 * side,
                         ("ra2" if side > 0 else "la2"): (110 + 15 * math.sin(t * 8)) * side})
    else:  # хватается за голову
        pose = dict(la1=-150, la2=118, ra1=150, ra2=-118)
    face = "sad" if t < 5 else "panic"
    b = boss(c, bx, 790, 1.4, pose, face=face, tilt=look)
    c.rect(345, 760, 735, 790, fill=(120, 80, 55), r=6)
    c.rect(365, 790, 715, 905, fill=(150, 104, 72), r=4)
    # бумаги на столе — растут
    n = int(1 + 7 * prog(t, 1, 11))
    for i in range(n):
        c.rect(380 + (i % 2) * 6, 748 - i * 9, 470 + (i % 2) * 6, 760 - i * 9, fill=(255, 255, 255),
               outline=GREY, w=2)
    c.rect(580, 712, 690, 760, fill=(60, 60, 70), r=6)  # ноутбук
    c.rect(588, 719, 682, 753, fill=(130, 190, 255) if int(t * 4) % 2 else (255, 120, 120), r=3)
    # пот
    if t > 4.5:
        for i in range(3):
            ph = (t * 1.4 + i / 3) % 1
            sx = b["head"][0] + (-1 if i % 2 else 1) * (b["hr"] + 8)
            sy = b["head"][1] - 10 + ph * 50
            c.ellipse(sx - 5, sy - 9, sx + 5, sy + 7, fill=(90, 170, 255))
    if t > 9.0:
        k = pop(t, 9.0)
        c.text(b["head"][0] + 58, b["head"][1] - 52, "!!!", 44 * k + 1, RED)

    # сотрудники
    for (t0, x0, x1, hy, s, q, bp) in EMPL:
        if t < t0: continue
        k = prog(t, t0, t0 + 0.9)
        x = lerp(x0, x1, k)
        if k < 1:
            pose = walk((t - t0) * 14)
        else:
            side = 1 if x1 < 540 else -1  # рука в сторону шефа
            pose = dict(STAND)
            pose.update({("ra1" if side > 0 else "la1"): 150 * side,
                         ("ra2" if side > 0 else "la2"): (165 + 22 * math.sin(t * 9 + x1)) * side})
        h = stick(c, x, hy, s, pose, GREY, face="o", tilt=0)
        bk = pop(t, t0 + 0.9)
        jit = math.sin(t * 13 + x1) * 3 * stress
        bubble(c, bp[0] + jit, bp[1], q, bk, tail=(h["head"][0], h["head"][1] - h["hr"]), size=28)
    for (t0, q, bp) in EXTRA:
        jit = math.sin(t * 15 + bp[0]) * 4 * stress
        bubble(c, bp[0] + jit, bp[1], q, pop(t, t0), size=28,
               fill=(255, 245, 160) if "СРОЧНО" in q else (255, 255, 255))


SKIN = (247, 222, 204)
HAIR_L = (203, 166, 114)
HAIR_D = (146, 108, 72)
JEANS = (62, 64, 72)

def girl(c, x, hip_y, s=1.0, pose=None, wink=False, thumb=False):
    """Я по фото: длинные светло-русые волосы, белый лонгслив, кулон, тёмные широкие джинсы."""
    p = dict(STAND); p.update(pose or {})
    hip = (x, hip_y)
    sh = (x, hip_y - 72 * s)
    hr = 27 * s
    hc = (x, sh[1] - hr - 5 * s)
    # волосы сзади
    c.circle(hc[0], hc[1] - 2 * s, hr * 1.14, fill=HAIR_L)
    c.poly([(hc[0] - hr * 1.14, hc[1]), (hc[0] - hr * 1.3, sh[1] + 62 * s), (hc[0] - hr * 0.9, sh[1] + 72 * s),
            (hc[0] + hr * 0.9, sh[1] + 72 * s), (hc[0] + hr * 1.3, sh[1] + 62 * s), (hc[0] + hr * 1.14, hc[1])],
           fill=HAIR_L)
    # ноги — широкие джинсы
    for dx, a1, a2 in ((-8, p["ll1"], p["ll2"]), (8, p["rl1"], p["rl2"])):
        h0 = (hip[0] + dx * s, hip[1])
        k = limb(h0, a1, 42 * s); f = limb(k, a2, 42 * s)
        c.seg(h0, k, JEANS, 21 * s); c.seg(k, f, JEANS, 24 * s)
        c.ellipse(f[0] - 13 * s, f[1] + 4 * s, f[0] + 15 * s, f[1] + 15 * s, fill=(235, 235, 238))
    # пояс джинсов + полоска живота
    c.rect(hip[0] - 19 * s, hip[1] - 9 * s, hip[0] + 19 * s, hip[1] + 8 * s, fill=JEANS, r=5 * s)
    c.rect(hip[0] - 16 * s, hip[1] - 14 * s, hip[0] + 16 * s, hip[1] - 8 * s, fill=SKIN)
    # белый лонгслив
    c.poly([(sh[0] - 19 * s, sh[1] - 1 * s), (sh[0] + 19 * s, sh[1] - 1 * s), (hip[0] + 17 * s, hip[1] - 13 * s),
            (hip[0] - 17 * s, hip[1] - 13 * s)], fill=(255, 255, 255), outline=(190, 190, 198))
    for i in range(3):  # складки ткани
        yy = sh[1] + (30 + i * 11) * s
        c.arc(sh[0], yy - 14 * s, 15 * s, 60, 120, (215, 215, 222), 1.5 * s)
    # шея и вырез
    c.rect(sh[0] - 6 * s, hc[1] + hr * 0.6, sh[0] + 6 * s, sh[1] + 3 * s, fill=SKIN)
    c.rect(sh[0] - 15 * s, sh[1] - 1 * s, sh[0] + 15 * s, sh[1] + 9 * s, fill=SKIN, r=3 * s)
    c.arc(sh[0], sh[1] - 4 * s, 11 * s, 30, 150, (205, 205, 210), 0.6 * s)  # цепочка
    c.rect(sh[0] - 3 * s, sh[1] + 6 * s, sh[0] + 3 * s, sh[1] + 12 * s, fill=(250, 250, 250),
           outline=(170, 170, 175), w=1)
    # руки в рукавах
    hands = []
    for side, a1, a2 in ((-1, p["la1"], p["la2"]), (1, p["ra1"], p["ra2"])):
        so = (sh[0] + side * 15 * s, sh[1] + 5 * s)
        e = limb(so, a1, 35 * s); hnd = limb(e, a2, 32 * s)
        for col, ww in (((190, 190, 198), 15 * s), ((255, 255, 255), 12 * s)):
            c.seg(so, e, col, ww); c.seg(e, hnd, col, ww)
        if thumb and side == 1:  # большой палец вверх
            c.rect(hnd[0] - 2.5 * s, hnd[1] - 13 * s, hnd[0] + 2.5 * s, hnd[1], fill=SKIN, r=2.5 * s,
                   outline=(215, 180, 160), w=1)
        c.circle(hnd[0], hnd[1], 6.5 * s, fill=SKIN, outline=(215, 180, 160), w=1)
        hands.append(hnd)
    # лицо
    fx, fy = hc
    c.ellipse(fx - hr * 0.86, fy - hr * 0.95, fx + hr * 0.86, fy + hr * 1.0, fill=SKIN)
    for d in (-1, 1):
        ex, ey = fx + d * 10 * s, fy + 3 * s
        if wink and d == 1:  # подмигивание
            c.arc(ex, ey - 4 * s, 6 * s, 30, 150, (45, 32, 28), 2.4 * s)
        else:
            c.d.chord(c.S(ex - 6 * s, ey - 4 * s, ex + 6 * s, ey + 4 * s), 180, 360, fill=(45, 32, 28))
            c.ellipse(ex - 4 * s, ey - 3.5 * s, ex + 4 * s, ey + 2.5 * s, fill=(45, 32, 28))
            c.circle(ex + 1.5 * s, ey - 1.5 * s, 1.2 * s, fill=(255, 255, 255))
            c.seg((ex - 6 * s * d * -1, ey - 2 * s), (ex + 7.5 * s * d, ey - 4.5 * s), (35, 25, 22), 1.8 * s)  # стрелка
        c.arc(ex, ey - 4 * s, 7 * s, 215, 325, (120, 88, 62), 2 * s)  # бровь
        c.ellipse(fx + d * 15 * s - 5 * s, fy + 10 * s, fx + d * 15 * s + 5 * s, fy + 14 * s, fill=(246, 196, 190))
    c.arc(fx, fy + 9 * s, 6 * s, 50, 130, (205, 110, 120), 2.6 * s)  # улыбка
    # чёлка-пробор и пряди спереди
    c.d.chord(c.S(fx - hr * 1.05, fy - hr * 1.15, fx + hr * 1.05, fy + hr * 0.85), 195, 345, fill=HAIR_D)
    c.poly([(fx - hr * 0.2, fy - hr * 0.95), (fx - hr * 0.95, fy - hr * 0.55), (fx - hr * 0.78, fy + hr * 0.1)],
           fill=HAIR_L)
    for d in (-1, 1):
        c.poly([(fx + d * hr * 0.92, fy - hr * 0.55), (fx + d * hr * 0.72, fy + hr * 0.2),
                (fx + d * hr * 0.62, sh[1] + 10 * s), (fx + d * hr * 0.55, sh[1] + 58 * s),
                (fx + d * hr * 0.95, sh[1] + 64 * s), (fx + d * hr * 1.25, sh[1] + 50 * s),
                (fx + d * hr * 1.18, fy + hr * 0.1)], fill=HAIR_L)
        c.seg((fx + d * hr * 0.88, fy + hr * 0.3), (fx + d * hr * 0.85, sh[1] + 50 * s), (185, 148, 98), 1.6 * s)
    return dict(head=hc, hr=hr, hands=hands, hip=hip, sh=sh)


# ---------------- НИЗ: я + Claude ----------------
TASKS = ["Контент-план на месяц", "Ответы клиентам: 27", "Отчёт по продажам", "5 сценариев Reels"]
TASK_T = [7.0, 8.4, 9.8, 11.2]
THOUGHTS = [(6.0, 8.6, "Новый продукт"), (8.9, 11.4, "Стратегия"), (11.7, 13.4, "Запись Reels")]

def bottom(c, t):
    Y = 960
    c.rect(0, Y, W, H, fill=(232, 246, 238))
    c.rect(0, Y + 640, W, H, fill=(214, 236, 223))  # пол
    pill(c, W / 2, Y + 70, "С ИИ: задачу — Claude, я — в стратегии", 30, GREEN)
    meter(c, 40, Y + 140, "Стресс", lerp(0.15, 0.05, prog(t, 4, 8)), GREEN, w=200)
    floor = Y + 640

    # мебель
    cx_chair = 205
    c.rect(cx_chair - 95, floor - 210, cx_chair - 60, floor - 2, fill=(110, 150, 200), r=12)  # спинка
    c.rect(cx_chair - 95, floor - 75, cx_chair + 115, floor - 35, fill=(130, 170, 220), r=12)  # сиденье
    c.rect(cx_chair + 100, floor - 105, cx_chair + 130, floor - 2, fill=(110, 150, 200), r=10)  # подлокотник
    # столик Claude
    c.rect(700, floor - 150, 990, floor - 132, fill=(120, 80, 55), r=5)
    c.rect(720, floor - 132, 738, floor, fill=(120, 80, 55)); c.rect(952, floor - 132, 970, floor, fill=(120, 80, 55))
    c.poly([(790, floor - 150), (880, floor - 150), (905, floor - 215), (815, floor - 215)], fill=(60, 60, 70))
    screen_on = t > 5.0
    c.poly([(800, floor - 155), (875, floor - 155), (897, floor - 208), (822, floor - 208)],
           fill=(140, 220, 170) if screen_on else (90, 90, 100))

    # --- Claude ---
    ck = prog(t, 3.9, 5.0)
    cx = lerp(640, 735, ck)
    if 3.9 < t < 5.0:
        cp = walk((t - 3.9) * 14, 22)
    elif t <= 3.9:
        cp = dict(STAND)
        if t > 3.0:  # «принято» — рука вверх
            cp.update(ra1=135, ra2=170)
    elif t < 13.0:
        ty = math.sin(t * 22)
        cp = dict(STAND, la1=55, la2=95 + 10 * ty, ra1=65, ra2=100 - 10 * ty)
    else:
        cp = dict(STAND, ra1=135, ra2=170)
    ch = stick(c, cx, floor - 88, 1.15, cp, CLAUDE, face="smile", bow=True, skirt=True)
    c.text(cx, floor + 30, "Claude", 26, CLAUDE)

    # --- я ---
    mk = prog(t, 4.2, 5.4)
    sit = prog(t, 5.3, 5.8)
    mx = lerp(400, cx_chair + 5, mk)
    if t < 3.1:
        mp = dict(STAND, ra1=80, ra2=88)  # указываю на Claude
    elif t < 4.2:
        mp = dict(STAND)
    elif t < 5.4:
        mp = walk((t - 4.2) * 14, 22)
        mp = {k: -v for k, v in mp.items()}  # иду влево
    else:
        cup = 0.5 + 0.5 * math.sin(t * 1.6)
        mp = dict(la1=-10, la2=40, ra1=lerp(25, 10, cup), ra2=lerp(75, 160, cup),
                  ll1=lerp(-9, 90, sit), ll2=lerp(-9, 0, sit), rl1=lerp(9, 80, sit), rl2=lerp(9, 5, sit))
        if t > 13.0:
            mp.update(la1=-60, la2=-170)  # «класс!» рукой вверх
    hip_y = lerp(floor - 120, floor - 78, sit)
    me = girl(c, mx, hip_y, 1.5, mp)
    c.text(mx, floor + 30, "Я", 26, INK)
    if t > 5.4:  # чашка кофе
        hx, hy = me["hands"][1]
        c.rect(hx - 4, hy - 26, hx + 22, hy + 2, fill=(255, 255, 255), r=4, outline=INK, w=3)
        c.arc(hx + 24, hy - 12, 8, -90, 90, INK, 3)
        if t % 1.4 < 0.9:
            c.arc(hx + 9, hy - 40, 7, 200, 340, (160, 160, 160), 2.5)

    # реплики
    k1 = pop(t, 0.5) * (1 - prog(t, 3.0, 3.25))
    bubble(c, 400, Y + 235,
           "Claude, сделай контент-план,\nответь клиентам\nи собери отчёт", k1,
           tail=(me["head"][0] + 10, me["head"][1] - me["hr"] - 4), size=27)
    k2 = pop(t, 3.1) * (1 - prog(t, 4.6, 4.9))
    bubble(c, 760, Y + 320, "Принято ✓", k2, tail=(ch["head"][0], ch["head"][1] - ch["hr"]), size=30)
    for (a, b_, s) in THOUGHTS:
        k = pop(t, a) * (1 - prog(t, b_ - 0.25, b_))
        bubble(c, 230, Y + 255, s, k, tail=(me["head"][0] + 5, me["head"][1] - me["hr"]), size=28,
               think=True, fill=(255, 250, 235))
    # чек-лист Claude
    if t > 5.6:
        pk = pop(t, 5.6, 0.4)
        px0, py0 = 600, Y + 120
        if pk > 0.5:
            c.rect(px0, py0, px0 + 420 * pk, py0 + (58 + 44 * len(TASKS)) * pk, fill=(255, 255, 255),
                   r=20, outline=CLAUDE, w=4)
        if pk > 0.95:
            c.text(px0 + 22, py0 + 30, "Claude делает:", 26, CLAUDE, anchor="lm")
            for i, (task, tt) in enumerate(zip(TASKS, TASK_T)):
                y = py0 + 74 + i * 44
                done = t > tt
                c.rect(px0 + 22, y - 15, px0 + 52, y + 15, fill=GREEN if done else (255, 255, 255),
                       r=6, outline=GREEN if done else GREY, w=3)
                if done:
                    kk = prog(t, tt, tt + 0.2)
                    c.seg((px0 + 29, y), (px0 + 35, y + 7), (255, 255, 255), 4)
                    if kk > 0.5:
                        c.seg((px0 + 35, y + 7), (px0 + 46, y - 8), (255, 255, 255), 4)
                elif t > tt - 1.4:  # в процессе
                    dots = "." * (1 + int(t * 4) % 3)
                    c.text(px0 + 392, y, dots, 24, GREY, anchor="rm")
                c.text(px0 + 66, y, task, 24, INK if done or t > tt - 1.4 else GREY, bold=done, anchor="lm")
    k3 = pop(t, 12.9)
    bubble(c, 540, Y + 480, "Всё готово ✓", k3,
           tail=(ch["head"][0] - ch["hr"], ch["head"][1]), size=28, fill=(255, 238, 230), border=CLAUDE)


def closeup(t):
    """Финал: я крупно, подмигиваю и показываю «класс»."""
    c = C()
    c.rect(0, 0, W, H, fill=(232, 246, 238))
    for i, (x, y, r) in enumerate(((150, 620, 90), (950, 560, 60), (120, 1500, 70), (960, 1380, 110))):
        c.circle(x, y + 10 * math.sin(t * 2 + i), r, fill=(214, 236, 223))
    k = pop(t, 15.0, 0.5)
    sc = lerp(5.0, 7.0, k)
    hip = 920 + 104 * sc
    g = girl(c, 540, hip, sc, dict(la1=-12, la2=-6, ra1=lerp(20, 38, k), ra2=lerp(10, 176, k)),
             wink=15.7 < t < 16.35, thumb=k > 0.8)
    tk = pop(t, 15.25, 0.4)
    if tk > 0.05:
        c.text(W / 2, 330, "Хочешь так же?", 76 * tk, INK)
        c.text(W / 2, 430, "Внедряю ИИ в бизнес под ключ", 40 * tk, GREEN)
    img = c.im.resize((W, H), Image.LANCZOS)
    if t < 15.35:
        img = Image.blend(frame(14.999), img, (t - 15.0) / 0.35)
    return img


def frame(t):
    if t >= 15.0:
        return closeup(t)
    c = C()
    top(c, t)
    bottom(c, t)
    c.rect(0, 954, W, 966, fill=INK)
    # финальная плашка
    fk = pop(t, 13.3, 0.45)
    if fk > 0.02:
        bw, bh = 960 * fk, 150 * fk
        c.rect(W / 2 - bw / 2, 960 - bh / 2, W / 2 + bw / 2, 960 + bh / 2, fill=INK, r=28 * fk)
        if fk > 0.6:
            c.text(W / 2, 960 - 30 * fk, "Дай задачу ИИ —", 48 * fk, (255, 255, 255))
            c.text(W / 2, 960 + 32 * fk, "и занимайся своим делом", 44 * fk, (255, 200, 225))
    # плавное появление
    img = c.im.resize((W, H), Image.LANCZOS)
    if t < 0.3:
        img = Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), img, t / 0.3)
    return img


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:  # превью кадров: python3 render.py 2 6 10 14
        for s in sys.argv[1:]:
            frame(float(s)).save(os.path.join(here, f"preview_{s}.png"))
        sys.exit()
    out = os.path.join(here, "stickman.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("ok", out)
