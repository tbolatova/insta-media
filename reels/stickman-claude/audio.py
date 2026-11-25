"""Музыка и звуки для stickman.mp4 — всё синтезировано кодом (без авторских прав).
Запуск: python3 audio.py  -> soundtrack.wav и stickman_sound.mp4
"""
import os, subprocess, wave
import numpy as np

SR, DUR = 44100, 17.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2) * 1.414
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2) * 1.414


def tt(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.005, k=6.0):
    t = tt(d); return np.minimum(1, t / a) * np.exp(-t * k)
def noise(d): return rng.uniform(-1, 1, int(d * SR))
def band(x, lo, hi):
    f = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(x))
def sweep(f0, f1, d):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def hz(m): return 440 * 2 ** ((m - 69) / 12)


# ---------------- МУЗЫКА: лёгкий поп-грув, 120 bpm ----------------
BPM = 120; B = 60 / BPM
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G
def pluck(m, d=0.45, k=7):
    t = tt(d); f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t)) * env(d, 0.003, k)
def kick():
    return sweep(130, 42, 0.32) * env(0.32, 0.002, 11)
def hat(d=0.06):
    return band(noise(d), 7000, 16000) * env(d, 0.001, 60)
def clap():
    return band(noise(0.2), 900, 4000) * env(0.2, 0.002, 22)

MUS_END = 16.6
beat = 0
while beat * B < MUS_END:
    t0 = beat * B
    bar = int(beat // 4); ch = CHORDS[bar % 4]
    final = t0 >= 13.3
    # бочка на каждую долю, клэп на 2 и 4 (с 2-го такта)
    add(kick(), t0, 0.55)
    if beat % 2 == 1 and beat >= 4:
        add(clap(), t0, 0.22 if not final else 0.3)
    for h in (0, 0.5):
        add(hat(), t0 + h * B, 0.07 if h else 0.04, pan=0.3)
    # бас
    if beat % 4 in (0, 2) or (beat % 4 == 3):
        add(pluck(ch[0] - 24, 0.4, 5) * 0.9, t0, 0.32)
    # арпеджио
    for k_, step in enumerate((0, 1, 2, 1)):
        m = ch[step] + 12
        add(pluck(m, 0.35, 9), t0 + k_ * B / 4, 0.09 if not final else 0.12, pan=-0.25 + 0.5 * (k_ % 2))
    # пэд на начало такта
    if beat % 4 == 0:
        d = 4 * B; t = tt(d)
        pad = sum(np.sin(2 * np.pi * hz(m) * t) + 0.5 * np.sin(2 * np.pi * hz(m) * 1.003 * t) for m in ch)
        pad *= np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
        add(pad, t0, 0.025)
    beat += 1
# общая громкость музыки + затухание в конце
fade = np.ones(N); tN = np.arange(N) / SR
fade[tN > 16.0] = np.clip((DUR - 0.3 - tN[tN > 16.0]) / 0.7, 0, 1)
L *= fade; R *= fade
mL, mR = L.copy(), R.copy()
L[:] = 0; R[:] = 0

# ---------------- ЗВУКИ ----------------
def pop(f=500):
    return sweep(f, f * 2.2, 0.08) * env(0.08, 0.002, 30)
def ring(d=1.3):
    t = tt(d)
    s = (np.sin(2 * np.pi * 1320 * t) + np.sin(2 * np.pi * 1660 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * t)) ** 2
    ph = t % 0.65
    gate = np.clip(ph / 0.01, 0, 1) * np.clip((0.45 - ph) / 0.02, 0, 1)
    return s * gate * 0.5
def alarm():
    out = np.concatenate([np.sign(np.sin(2 * np.pi * f * tt(0.13))) * env(0.13, 0.003, 4) for f in (880, 660, 880, 660)])
    return band(out, 200, 5000)
def boing():
    t = tt(0.5); f = 330 * (1 - 0.5 * t) * (1 + 0.08 * np.sin(2 * np.pi * 14 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.5, 0.005, 5)
def click():
    return band(noise(0.025), 1500, 7000) * env(0.025, 0.0005, 180)
def ding(f=1318.5):
    t = tt(0.7)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * env(0.7, 0.002, 6)
def success():
    out = np.zeros(int(0.9 * SR))
    for i, m in enumerate((84, 88, 91, 96)):
        s = ding(hz(m)) * 0.6; j = int(i * 0.08 * SR)
        out[j:j + len(s)] += s[: len(out) - j]
    return out
def whoosh(d=0.6):
    t = tt(d); x = noise(d)
    e = np.sin(np.pi * t / d) ** 2
    return (band(x, 300, 2500) * 0.6 + band(x, 2500, 7000) * 0.4 * (t / d)) * e
def boom():
    return sweep(90, 35, 0.6) * env(0.6, 0.003, 6)
def blip_up():
    return np.concatenate([np.sin(2 * np.pi * hz(m) * tt(0.07)) * env(0.07, 0.002, 25) for m in (76, 81)])
def step():
    return sweep(180, 90, 0.07) * env(0.07, 0.002, 40)
def sparkle():
    out = np.zeros(int(0.6 * SR))
    for i in range(7):
        s = np.sin(2 * np.pi * rng.uniform(2500, 5000) * tt(0.2)) * env(0.2, 0.002, 18)
        j = int(i * 0.05 * SR); out[j:j + len(s)] += s[: len(out) - j]
    return out

# верх: вопросы сотрудников (левые слева в панораме, правые справа)
for t0, pan in ((1.5, -0.6), (2.5, 0.6), (3.7, -0.4), (4.9, 0.4)):
    add(pop(480), t0, 0.35, pan)
for t0, pan in ((5.4, 0), (7.6, 0.6), (9.4, -0.7), (10.0, 0.7)):
    add(pop(620), t0, 0.32, pan)
add(ring(), 6.6, 0.16, -0.5)            # «Звонок от заказчика!»
add(alarm(), 8.6, 0.12)                 # «СРОЧНО!!!»
add(boing(), 9.0, 0.3)                  # бизнесмен хватается за голову

# низ: я и Claude
add(pop(380), 0.5, 0.3)                 # моя задача
add(blip_up(), 3.1, 0.3, 0.3)           # «Принято ✓»
t = 3.9
while t < 5.0:                          # шаги кубика
    add(step(), t, 0.25, 0.3); t += 0.224
t = 4.2
while t < 5.4:                          # мои шаги
    add(step() * 0.7, t, 0.18, -0.3); t += 0.224
add(whoosh(0.35), 5.55, 0.18, 0.4)      # появляется чек-лист
t = 5.2
while t < 13.0:                         # печать на клавиатуре
    add(click(), t, rng.uniform(0.08, 0.16), 0.4)
    t += rng.uniform(0.06, 0.14)
for t0 in (6.0, 8.9, 11.7):             # мысли
    add(pop(300), t0, 0.18, -0.4)
for i, t0 in enumerate((7.0, 8.4, 9.8, 11.2)):  # галочки
    add(ding(hz(84 + 2 * i)), t0, 0.22, 0.4)
add(success(), 12.9, 0.3, 0.3)          # «Всё готово ✓»
add(whoosh(0.5), 12.95, 0.3)            # плашка
add(boom(), 13.35, 0.5)
add(whoosh(0.45), 14.75, 0.3)           # крупный план
add(sparkle(), 15.7, 0.18)              # подмигивание

sL, sR = L, R
outL = np.tanh((mL * 0.55 + sL) * 1.1)
outR = np.tanh((mR * 0.55 + sR) * 1.1)
peak = max(np.abs(outL).max(), np.abs(outR).max())
st = np.stack([outL, outR], 1) / peak * 0.89

here = os.path.dirname(os.path.abspath(__file__))
wav = os.path.join(here, "soundtrack.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
out = os.path.join(here, "stickman_sound.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(here, "stickman.mp4"), "-i", wav,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", out], check=True)
print("ok", out)
