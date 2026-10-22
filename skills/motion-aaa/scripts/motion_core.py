"""motion_core — generic engine for procedural AAA motion (motion-aaa skill).

Everything is drawn by code with Pillow + NumPy at 2x supersampling and encoded with FFmpeg.
Coordinates are LOGICAL pixels of the final video; `Canvas` scales by SS internally and
`finish()` box-downscales. A piece supplies a scene object with `compose(t) -> PIL.Image`
(supersampled, size fmt.w*SS x fmt.h*SS); this module renders it in parallel, extracts stills,
builds contact sheets and exports GIFs.

No network, no third-party assets. Fonts are resolved from the operating system.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from multiprocessing import Pool
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 2          # supersampling factor
FPS = 30

# ----------------------------------------------------------------- fonts (OS resolution with fallbacks)
_FONT_CANDIDATES = {
    # heavy display face for callouts and captions
    'black': ['C:/Windows/Fonts/seguibl.ttf', '/System/Library/Fonts/Supplemental/Arial Black.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'],
    'bold': ['C:/Windows/Fonts/segoeuib.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'],
    'semi': ['C:/Windows/Fonts/seguisb.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans.ttf'],
    # condensed numeric face for data and labels
    'numc': ['C:/Windows/Fonts/bahnschrift.ttf', '/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf',
             '/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf'],
    'mono': ['C:/Windows/Fonts/CascadiaMono.ttf', 'C:/Windows/Fonts/consola.ttf', '/System/Library/Fonts/Menlo.ttc',
             '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', '/usr/share/fonts/TTF/DejaVuSansMono.ttf'],
}
_VARIATION = {'numc': 'Bold Condensed'}     # applied only to variable fonts that expose it (Bahnschrift)


@lru_cache(maxsize=None)
def font_path(kind: str):
    env = os.environ.get(f'MOTION_FONT_{kind.upper()}')
    for p in ([env] if env else []) + _FONT_CANDIDATES[kind]:
        if p and Path(p).exists():
            return p
    return None


@lru_cache(maxsize=128)
def font(size: int, kind: str = 'bold'):
    p = font_path(kind)
    if p is None:
        return ImageFont.load_default(size)
    f = ImageFont.truetype(p, size)
    if kind in _VARIATION:
        try:
            f.set_variation_by_name(_VARIATION[kind])
        except Exception:  # not a variable font: use as is
            pass
    return f


# ----------------------------------------------------------------- time and easing
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, x):
    return a + (b - a) * x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x, k=1.70158):
    """Entry with overshoot (follow-through)."""
    x = clamp(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def spring(x, freq=2.2, damping=5.0):
    """Damped spring settling 0 -> 1 (overshoot then settle); x in seconds since release."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-damping * x) * math.cos(2 * math.pi * freq * x)


def span(t, a, b):
    """Smooth 0 -> 1 between a and b."""
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


def window(t, a, b, fade=.25):
    """Visibility 0..1: fades in at a, holds, fades out at b."""
    return min(span(t, a, a + fade), 1 - span(t, b - fade, b))


def mix(c0, c1, a):
    a = clamp(a)
    return tuple(int(round(p + (q - p) * a)) for p, q in zip(c0, c1))


def arc_flight(t, t0, dur, p0, p1, h=1.4):
    """Parabolic flight p0 -> p1 between t0 and t0+dur: (x, y, z, k). z is height above the ground."""
    k = clamp((t - t0) / dur)
    e = ease_in_out(k)
    return lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e), 4 * h * k * (1 - k), k


def land_squash(t, t_land, d=.22):
    """Landing curve: 1 -> .72 -> 1.08 -> 1 (scale on y; use 1/sqrt(sy) on x to keep area)."""
    a = t - t_land
    if a < 0 or a > d:
        return 1.0
    k = a / d
    return 1 - .28 * math.sin(math.pi * min(1, k * 1.6)) + (.08 * math.sin(math.pi * max(0, k * 1.6 - .6)) if k > .4 else 0)


def anticipation(t, t_go, d=.16, depth=.2):
    """Crouch before a launch at t_go: returns y-scale (1 -> 1-depth -> 1 at launch)."""
    a = t_go - t
    if a < 0 or a > d:
        return 1.0
    return 1 - depth * math.sin(math.pi * (1 - a / d) * .5)


class Remap:
    """Real time -> simulation time with monotone piecewise-cubic (PCHIP) interpolation.
    Slow motion, freezes and resumes without velocity jumps. keys = [(t_real, t_sim), ...]."""

    def __init__(self, keys):
        self.t = [k[0] for k in keys]
        self.v = [k[1] for k in keys]
        n = len(keys)
        h = [self.t[i + 1] - self.t[i] for i in range(n - 1)]
        d = [(self.v[i + 1] - self.v[i]) / h[i] for i in range(n - 1)]
        m = [0.0] * n
        if n == 2:
            m = [d[0], d[0]]
        else:
            m[0], m[-1] = d[0], d[-1]
            for i in range(1, n - 1):
                if d[i - 1] * d[i] <= 0:
                    m[i] = 0.0
                else:
                    w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                    m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
            for i in (0, n - 1):
                j = 0 if i == 0 else n - 2
                if m[i] * d[j] <= 0:
                    m[i] = 0.0
        self.h, self.m = h, m

    def __call__(self, t):
        if t <= self.t[0]:
            return self.v[0]
        if t >= self.t[-1]:
            return self.v[-1]
        i = bisect_right(self.t, t) - 1
        h = self.h[i]
        s = (t - self.t[i]) / h
        h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
        h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        return h00 * self.v[i] + h10 * h * self.m[i] + h01 * self.v[i + 1] + h11 * h * self.m[i + 1]

    def rate(self, t, dt=1 / 60):
        """Simulation speed at real time t (1 = real speed). Use it to derive the on-screen 'x1/4' tag."""
        return (self(t + dt) - self(t - dt)) / (2 * dt)

    def inv(self, value, step=1 / 600):
        """First real time at which the simulation reaches `value` (None if never)."""
        x = self.t[0]
        while x <= self.t[-1]:
            if self(x) >= value:
                return x
            x += step
        return None


def speed_label(rate, steps=(2, 3, 4, 6, 8, 12)):
    """Declared-speed tag derived from Remap.rate(t), quantized to readable fractions."""
    if rate < .02:
        return 'PAUSE'
    if rate > .85:
        return 'REAL SPEED' if rate < 1.15 else f'x{rate:.1f}'
    return f'x1/{min(steps, key=lambda d: abs(1 / d - rate))}'


# ----------------------------------------------------------------- canvas
@lru_cache(maxsize=64)
def round_mask(w: int, h: int, r: int):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


class Canvas:
    """Drawing in logical coordinates on a supersampled image."""

    def __init__(self, img: Image.Image, ox=0.0, oy=0.0):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.ox, self.oy = ox, oy

    def p(self, x, y):
        return ((x - self.ox) * SS, (y - self.oy) * SS)

    def box(self, x0, y0, x1, y1):
        a, b = self.p(x0, y0)
        c, d = self.p(x1, y1)
        return (min(a, c), min(b, d), max(a, c), max(b, d))

    def rect(self, x0, y0, x1, y1, fill=None, r=0, outline=None, width=0):
        bx = self.box(x0, y0, x1, y1)
        if bx[2] - bx[0] < 1 or bx[3] - bx[1] < 1:
            return
        if r:
            r = min(r * SS, (bx[2] - bx[0]) / 2, (bx[3] - bx[1]) / 2)
            self.d.rounded_rectangle(bx, radius=r, fill=fill, outline=outline, width=int(width * SS))
        else:
            self.d.rectangle(bx, fill=fill, outline=outline, width=int(width * SS))

    def ellipse(self, cx, cy, rx, ry=None, fill=None, outline=None, width=0):
        ry = rx if ry is None else ry
        if rx <= 0 or ry <= 0:
            return
        self.d.ellipse(self.box(cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=int(width * SS))

    def line(self, pts, fill, width=2, joint='curve'):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=max(1, int(width * SS)), joint=joint)

    def poly(self, pts, fill, outline=None):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=outline)

    def arc(self, cx, cy, r, start, end, fill, width):
        """Arc in degrees (0 = right, clockwise)."""
        if end > start:
            self.d.arc(self.box(cx - r, cy - r, cx + r, cy + r), start, end, fill=fill, width=max(1, int(width * SS)))

    def text(self, x, y, value, size, color, kind='bold', anchor='la', stroke=0, stroke_color=(0, 0, 0)):
        self.d.text(self.p(x, y), value, font=font(int(size * SS), kind), fill=color, anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=stroke_color)

    def textlen(self, value, size, kind='bold'):
        return self.d.textlength(value, font=font(int(size * SS), kind)) / SS

    def fit_size(self, value, size, max_w, kind='bold'):
        w = self.textlen(value, size, kind)
        return size if w <= max_w else size * max_w / w

    def dashed(self, x0, y0, x1, y1, fill, width=3, dash=14, gap=10):
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        s = 0.0
        while s < length:
            e = min(length, s + dash)
            self.line([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)], fill, width)
            s += dash + gap

    def check(self, cx, cy, size, color, width=7):
        s = size
        self.line([(cx - s * .5, cy), (cx - s * .12, cy + s * .38), (cx + s * .55, cy - s * .4)], color, width)

    def cross(self, cx, cy, size, color, width=7):
        s = size * .42
        self.line([(cx - s, cy - s), (cx + s, cy + s)], color, width)
        self.line([(cx - s, cy + s), (cx + s, cy - s)], color, width)

    def arrow(self, x0, y0, x1, y1, color, w=4, head=14):
        """Arrow drawn as geometry (never rely on a font for arrows)."""
        self.line([(x0, y0), (x1, y1)], color, w)
        ang = math.atan2(y1 - y0, x1 - x0)
        for s in (-1, 1):
            a = ang + math.pi + s * .5
            self.line([(x1, y1), (x1 + math.cos(a) * head, y1 + math.sin(a) * head)], color, w)


def new_frame(fmt, color=(0, 0, 0)):
    return Image.new('RGB', (fmt.w * SS, fmt.h * SS), color)


def finish(img: Image.Image) -> Image.Image:
    """Box-downscale the supersampled frame to the final size."""
    return img.resize((img.width // SS, img.height // SS), Image.Resampling.BOX)


# ----------------------------------------------------------------- formats and slots
@dataclass(frozen=True)
class Fmt:
    name: str
    w: int
    h: int
    slots: tuple
    cap_cy: int
    cap_size: int
    cap_maxw: int
    callout_y: int
    header_y: int

    def slot(self, name):
        return dict(self.slots)[name]

    @property
    def cx(self):
        return self.w / 2

    @property
    def size(self):
        return f'{self.w}x{self.h}'


HORIZ = Fmt('h', 1920, 1080, (
    ('full', (200, 218, 1720, 886)), ('wide', (60, 226, 1290, 886)),
    ('L', (70, 226, 944, 840)), ('R', (976, 226, 1850, 840)),
    ('c1', (52, 262, 648, 812)), ('c2', (662, 262, 1258, 812)), ('c3', (1272, 262, 1868, 812)),
    ('q1', (432, 222, 952, 552)), ('q2', (968, 222, 1488, 552)),
    ('q3', (432, 558, 952, 888)), ('q4', (968, 558, 1488, 888)),
), cap_cy=960, cap_size=52, cap_maxw=1500, callout_y=140, header_y=58)

VERT = Fmt('v', 1080, 1920, (
    ('full', (40, 350, 1040, 1360)), ('wide', (40, 336, 1040, 946)),
    ('L', (40, 346, 1040, 846)), ('R', (40, 860, 1040, 1360)),
    ('c1', (40, 330, 1040, 670)), ('c2', (40, 680, 1040, 1020)), ('c3', (40, 1030, 1040, 1370)),
    ('q1', (24, 470, 536, 860)), ('q2', (544, 470, 1056, 860)),
    ('q3', (24, 880, 536, 1270)), ('q4', (544, 880, 1056, 1270)),
), cap_cy=1484, cap_size=58, cap_maxw=940, callout_y=226, header_y=150)

SQUARE = Fmt('s', 1080, 1080, (
    ('full', (40, 150, 1040, 870)), ('wide', (40, 150, 1040, 870)),
    ('L', (30, 170, 535, 860)), ('R', (545, 170, 1050, 860)),
    ('q1', (30, 150, 535, 505)), ('q2', (545, 150, 1050, 505)),
    ('q3', (30, 515, 535, 870)), ('q4', (545, 515, 1050, 870)),
), cap_cy=960, cap_size=48, cap_maxw=960, callout_y=90, header_y=46)


def lerp_rect(a, b, k):
    return tuple(lerp(p, q, k) for p, q in zip(a, b))


def shrink(rect, f):
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (cx + (x0 - cx) * f, cy + (y0 - cy) * f, cx + (x1 - cx) * f, cy + (y1 - cy) * f)


def layout_at(keys, t, fmt: Fmt, dur=.5):
    """keys: [(t, {pid: slot_name})] -> {pid: (rect, alpha)} with eased transitions.
    Entering panels grow from 92 % and fade in; leaving panels shrink 6 % and fade out."""
    i = max(0, bisect_right([k[0] for k in keys], t) - 1)
    t1, cur = keys[i]
    prev = keys[i - 1][1] if i > 0 else {}
    k = ease_in_out((t - t1) / dur) if i > 0 else 1.0
    out = {}
    for pid, slot in cur.items():
        r1 = fmt.slot(slot)
        out[pid] = (lerp_rect(fmt.slot(prev[pid]), r1, k), 1.0) if pid in prev else (shrink(r1, .92 + .08 * k), k)
    for pid, slot in prev.items():
        if pid not in cur and k < 1:
            out[pid] = (shrink(fmt.slot(slot), 1 - .06 * k), 1 - k)
    return out


# ----------------------------------------------------------------- world view with parallax
class View:
    """World units -> panel pixels. drift (world units) times `par` gives the parallax of a layer."""

    def __init__(self, sw, sh, world_w=16.0, drift=(0.0, 0.0), par=1.0, zoom=1.0, center=None):
        self.sw, self.sh, self.zoom = sw, sh, zoom
        self.k = sw / world_w * zoom
        self.cx, self.cy = center or (world_w / 2, world_w / 2 * sh / sw)
        self.drift = drift
        self.dx, self.dy = drift[0] * par, drift[1] * par

    def layer(self, par):
        """Same camera, another depth layer (background ~0.5, props 1, foreground particles ~1.6)."""
        v = View.__new__(View)
        v.__dict__.update(self.__dict__)
        v.dx, v.dy = self.drift[0] * par, self.drift[1] * par
        return v

    def p(self, x, y, z=0.0):
        return ((x - self.cx + self.dx) * self.k + self.sw / 2, (y - self.cy + self.dy - z) * self.k + self.sh / 2)

    def d(self, v):
        return v * self.k


def drift_at(t, seed=0.0, ax=.16, ay=.1, period=None):
    """Slow deterministic camera drift (world units). With `period`, it loops exactly every period seconds."""
    if period:
        w = 2 * math.pi / period
        return (ax * math.sin(w * t + seed), ay * math.sin(w * t * 2 + 1.3 + seed) * .7)
    return (ax * math.sin(t * .23 + seed) + ax * .4 * math.sin(t * .61 + 2 * seed), ay * math.sin(t * .19 + 1.3 + seed))


# ----------------------------------------------------------------- light, shadow, gradients, particles
@lru_cache(maxsize=256)
def _radial(rpx: int, power10: int, alpha: int):
    yy, xx = np.mgrid[-rpx:rpx + 1, -rpx:rpx + 1].astype(np.float32)
    d = np.sqrt(xx ** 2 + yy ** 2) / max(1, rpx)
    m = np.clip(1 - d, 0, 1) ** (power10 / 10)
    return Image.fromarray((m * alpha).astype('uint8'), 'L'), 2 * rpx + 1


def glow(img: Image.Image, cx, cy, r, color, strength=1.0, power=2.0):
    """Light halo (radial mask). cx, cy, r in logical coordinates. Quantized so the mask cache stays small."""
    if strength <= .01 or r <= 1:
        return
    rpx = int(max(2, r * SS) // 4 * 4)
    a = int(clamp(strength) * 255 // 8 * 8)
    m, n = _radial(rpx, int(power * 10), a)
    x0, y0 = int(cx * SS) - rpx, int(cy * SS) - rpx
    img.paste(color, (x0, y0, x0 + n, y0 + n), m)


@lru_cache(maxsize=128)
def _shadow(rpx, sq100, alpha):
    ry = max(1, int(rpx * sq100 / 100))
    yy, xx = np.mgrid[-ry:ry + 1, -rpx:rpx + 1].astype(np.float32)
    d = np.sqrt((xx / rpx) ** 2 + (yy / ry) ** 2)
    return Image.fromarray((np.clip(1 - d, 0, 1) ** 1.3 * alpha).astype('uint8'), 'L')


def soft_shadow(img, x, y, r, strength=.5, squash=.45, color=(0, 0, 0)):
    """Soft elliptical contact shadow. Shrink r and strength with the object's height."""
    if strength <= .01 or r <= 1:
        return
    rpx = int(max(2, r * SS) // 2 * 2)
    m = _shadow(rpx, int(squash * 100), int(clamp(strength) * 255 // 8 * 8))
    img.paste(color, (int(x * SS) - rpx, int(y * SS) - int(rpx * squash)), m)


@lru_cache(maxsize=4)
def gradient_bg(w: int, h: int, top: tuple, bottom: tuple, vignette=.22, glow_color=None, glow_pos=(.5, .2),
                grain=0.0, seed=0):
    """Supersampled background: vertical gradient, optional warm/cool light pool, vignette, film grain."""
    H, W = h * SS, w * SS
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    t, b = np.array(top, np.float32), np.array(bottom, np.float32)
    img = b + (t - b) * ((1 - y) ** 1.3)[..., None]
    if glow_color is not None:
        d = np.sqrt(((x - glow_pos[0]) * W / H) ** 2 + (y - glow_pos[1]) ** 2)
        img = img + np.exp(-(d / .8) ** 2)[..., None] * np.array(glow_color, np.float32) * .5
    if grain:
        img = img + np.random.default_rng(seed).normal(0, grain, (H, W, 1)).astype(np.float32)
    v = 1 - vignette * ((x - .5) * 2) ** 2 - vignette * ((y - .5) * 2) ** 2
    img = img * v[..., None]
    return Image.fromarray(img.clip(0, 255).astype('uint8'), 'RGB')


def burst(c: Canvas, x, y, age, color, base, n=10, seed=0, radius=60, life=.55, size=5, gravity=0.0):
    """Deterministic particle burst from an event at (x, y); `age` = t_now - t_event (logical px)."""
    if age < 0 or age > life:
        return
    k = age / life
    rng = np.random.default_rng(seed)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(.45, 1.0)
        dist = radius * sp * ease_out(k)
        px, py = x + math.cos(a) * dist, y + math.sin(a) * dist * .6 + gravity * k * k
        c.ellipse(px, py, max(.8, size * (1 - k) * rng.uniform(.6, 1.2)), fill=mix(base, color, 1 - k))


def ring_wave(c: Canvas, x, y, age, color, base, r_max=90, life=.5, width=4):
    if 0 <= age <= life:
        k = age / life
        c.ellipse(x, y, r_max * ease_out(k), outline=mix(base, color, 1 - k), width=width * (1 - k) + 1)


# ----------------------------------------------------------------- narration: alignment, cues, captions
def load_alignment(path: Path):
    """Character-level TTS alignment ({'alignment': {'characters', 'character_start_times_seconds',
    'character_end_times_seconds'}}) -> (script, words). Expressive tags like [softly] are blanked
    out without moving positions, so they never become words or captions."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    al = data.get('alignment') or data.get('normalized_alignment') or data
    chars, st, en = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
    script = re.sub(r'\[[^\]\n]*\]', lambda m: ' ' * len(m.group()), ''.join(chars))
    words = [{'text': m.group(), 'start': st[m.start()], 'end': en[m.end() - 1], 'pos': m.start()}
             for m in re.finditer(r'\S+', script)]
    return script, words


def estimate_alignment(text, sec_per_char=.0635, word_gap=.055, pauses=None, t0=0.0):
    """Approximate word timings for an animatic before any voice exists (measure your voice and adjust)."""
    pauses = pauses or {'.': .67, ',': .26, ':': .60, ';': .45, '?': .67, '!': .6}
    text = re.sub(r'\[[^\]\n]*\]', '', text)
    t, words = t0, []
    for m in re.finditer(r'\S+', text):
        w = m.group()
        d = len(w) * sec_per_char
        words.append({'text': w, 'start': round(t, 3), 'end': round(t + d, 3), 'pos': m.start()})
        t += d + word_gap + pauses.get(w[-1], 0.0)
    return text, words


WEAK = {'de', 'y', 'el', 'la', 'los', 'las', 'un', 'una', 'que', 'en', 'a', 'se', 'con', 'tu', 'su', 'mi', 'del', 'al',
        'lo', 'le', 'por', 'para', 'no', 'ni', 'o', 'e', 'si', 'sin', 'es',
        'the', 'a', 'an', 'of', 'to', 'and', 'or', 'in', 'on', 'for', 'with', 'is', 'it', 'your', 'at', 'by'}


def build_cues(words, merge_max=34, split_over=40):
    """Whole phrases: cut at punctuation, merge short clauses, halve long ones avoiding weak-word breaks."""
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if w['text'].endswith(('.', ',', ':', ';', '?', '!')):
            clauses.append(cur)
            cur = []
    if cur:
        clauses.append(cur)

    def text(ws):
        return ' '.join(w['text'] for w in ws)

    merged = []
    for cl in clauses:
        if merged and len(text(merged[-1] + cl)) <= merge_max and not text(merged[-1]).endswith(('.', ';', '?', '!')):
            merged[-1] = merged[-1] + cl
        else:
            merged.append(cl)
    cues = []
    for cl in merged:
        if len(text(cl)) > split_over and len(cl) > 1:
            best = min(range(1, len(cl)), key=lambda k: abs(len(text(cl[:k])) - len(text(cl[k:])))
                       + (12 if cl[k - 1]['text'].lower() in WEAK else 0))
            cues += [cl[:best], cl[best:]]
        else:
            cues.append(cl)
    out = []
    for i, ws in enumerate(cues):
        nxt = cues[i + 1][0]['start'] if i + 1 < len(cues) else None
        end = ws[-1]['end'] + .25
        if nxt is not None:
            end = nxt if nxt - ws[-1]['end'] < .7 else min(end, nxt)
        out.append({'start': ws[0]['start'], 'end': end, 'text': text(ws), 'words': ws})
    return out


def wrap_words(c: Canvas, words, size, max_w, kind='black'):
    lines, line = [], []
    for w in words:
        cand = line + [w]
        if c.textlen(' '.join(x['text'] for x in cand), size, kind) > max_w and line:
            lines.append(line)
            line = [w]
        else:
            line = cand
    if line:
        lines.append(line)
    return lines


def split_long(cues, fmts, kind='black'):
    """Recursively split cues that would take more than two lines on ANY of the given canvases."""
    probe = Canvas(Image.new('RGB', (8, 8)))

    def text(ws):
        return ' '.join(w['text'] for w in ws)

    def fits(ws):
        return all(len(wrap_words(probe, ws, f.cap_size, f.cap_maxw, kind)) <= 2 for f in fmts)

    def split(ws):
        if fits(ws) or len(ws) < 2:
            return [ws]
        best = min(range(1, len(ws)), key=lambda k: abs(len(text(ws[:k])) - len(text(ws[k:])))
                   + (12 if ws[k - 1]['text'].lower() in WEAK else 0) - (6 if ws[k - 1]['text'].endswith((',', ';', ':')) else 0))
        return split(ws[:best]) + split(ws[best:])

    out = []
    for cue in cues:
        parts = split(cue['words'])
        for j, ws in enumerate(parts):
            end = parts[j + 1][0]['start'] if j + 1 < len(parts) else cue['end']
            out.append({'start': ws[0]['start'], 'end': end, 'text': text(ws), 'words': ws})
    return out


def draw_caption(c: Canvas, fmt: Fmt, cue, t, alpha=1.0, base=(0, 0, 0), spoken=(250, 246, 238),
                 upcoming=(170, 166, 160), active=(255, 220, 90), capsule=None, ink=(0, 0, 0), kind='black'):
    """Karaoke caption: spoken words full color, active word in the accent inside a soft capsule,
    upcoming words muted; 2 lines max; common baseline; small rise on entry."""
    size, max_w = fmt.cap_size, fmt.cap_maxw
    lines = wrap_words(c, cue['words'], size, max_w, kind)
    if len(lines) > 2:
        raise ValueError(f'caption longer than two lines: {cue["text"]}')
    intro = ease_out((t - cue['start']) / .16)
    lh = size * 1.26
    top = fmt.cap_cy - lh * len(lines) / 2 + (1 - intro) * 12
    a = alpha * intro
    act = None
    for w in cue['words']:
        if w['start'] <= t:
            act = w
    space = c.textlen(' ', size, kind)
    for i, ln in enumerate(lines):
        x = fmt.cx - c.textlen(' '.join(w['text'] for w in ln), size, kind) / 2
        y = top + i * lh + size * .95
        for w in ln:
            wl = c.textlen(w['text'], size, kind)
            if w is act:
                k = ease_out((t - w['start']) / .12)
                c.rect(x - 8, y - size * .92, x + wl + 8, y + size * .2, fill=mix(base, capsule or mix(ink, active, .3), a * k), r=12)
                col = active
            else:
                col = spoken if w['start'] <= t else upcoming
            c.text(x, y, w['text'], size, mix(base, col, a), kind, anchor='ls', stroke=6, stroke_color=mix(base, ink, a))
            x += wl + space


def caption_at(cues, t):
    for cue in cues:
        if cue['start'] <= t < cue['end']:
            return cue, 1 - clamp((t - (cue['end'] - .08)) / .08)
    return None, 0.0


def srt_time(t):
    ms = round(t * 1000)
    hh, ms = divmod(ms, 3600000)
    mm, ms = divmod(ms, 60000)
    ss, ms = divmod(ms, 1000)
    return f'{hh:02}:{mm:02}:{ss:02},{ms:03}'


def to_srt(cues):
    return '\n\n'.join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}"
                       for i, c in enumerate(cues, 1)) + '\n'


# ----------------------------------------------------------------- checks
def check_glyphs(strings, kinds=('black', 'numc')):
    """Every on-screen string must exist in the fonts that draw it (no tofu). Needs fontTools; returns
    {char: [kinds missing it]} and raises if anything is missing. Without fontTools it warns and passes."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print('check_glyphs: fontTools not installed, glyph check skipped', file=sys.stderr)
        return {}
    cmaps = {}
    for k in kinds:
        p = font_path(k)
        if p:
            cmaps[k] = TTFont(p, fontNumber=0).getBestCmap() if p.lower().endswith('.ttc') else TTFont(p).getBestCmap()
    missing = {}
    for s in strings:
        for ch in s:
            if ch.isspace():
                continue
            bad = [k for k, cm in cmaps.items() if ord(ch) not in cm]
            if bad:
                missing.setdefault(ch, bad)
    if missing:
        raise ValueError(f'glyphs missing from fonts (draw them as geometry or change the text): {missing}')
    return missing


def events_report(events, words, t_min=-.5, t_max=None, skip=()):
    """Lines 't  kind  info  «word being spoken»' to reconcile the simulation with the script before rendering."""
    out = []
    for t, kind, info in sorted(events, key=lambda e: e[0]):
        if kind in skip or t < t_min or (t_max is not None and t > t_max):
            continue
        w = None
        for i, x in enumerate(words):
            if x['start'] <= t + 1e-6:
                w = (i, x['text'])
        out.append(f'{t:7.2f}  {kind:12s} {str(info or ""):12s} «{w[1] if w else "-"}» (W{w[0] if w else "-"})')
    return '\n'.join(out)


# ----------------------------------------------------------------- rendering
_SCENE = None


def _init_worker(factory, args):
    global _SCENE
    _SCENE = factory(*args)


def _frame_bytes(i):
    return finish(_SCENE.compose(i / _SCENE.fps)).tobytes()


def default_workers():
    env = int(os.environ.get('RENDER_WORKERS', 0) or 0)
    return env or min(6, max(2, (os.cpu_count() or 4) - 2))


def render(factory, args, out_path: Path, audio_wav: Path | None = None, workers=None, crf=17):
    """Render factory(*args) (an object with .fmt, .fps, .duration, .compose(t)) to an MP4.
    The factory must be a top-level function: each worker builds its own scene (nothing is pickled
    but the reference). Refuses to overwrite; deletes the partial file on any failure."""
    scene = factory(*args)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        raise FileExistsError(f'{out_path.name} exists: render a new version instead of overwriting')
    n = int(math.ceil(scene.duration * scene.fps))
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', scene.fmt.size, '-r', str(scene.fps), '-i', 'pipe:0']
    if audio_wav:
        cmd += ['-i', str(audio_wav), '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
                '-shortest']
    cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-tune', 'animation', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', str(out_path)]
    workers = workers or default_workers()
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        with Pool(workers, initializer=_init_worker, initargs=(factory, args)) as pool:
            for data in pool.imap(_frame_bytes, range(n), chunksize=4):
                proc.stdin.write(data)
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('FFmpeg failed')
    except BaseException:
        proc.kill()
        proc.wait()
        if out_path.exists():
            out_path.unlink()
        raise
    return {'frames': n, 'workers': workers, 'render_wall_seconds': round(time.perf_counter() - t0, 1), 'command': cmd}


def stills(scene, times, dest: Path, prefix='f'):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for t in times:
        p = dest / f'{prefix}{t:07.2f}.png'
        finish(scene.compose(t)).save(p)
        paths.append(p)
    return paths


def contact_sheet(paths, out: Path, cols=6, thumb_w=None):
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    tw = thumb_w or (384 if w > h else 216)
    th = round(tw * h / w)
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new('RGB', (tw * cols, th * rows), (12, 12, 12))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th), Image.Resampling.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    return out


def export_gif(src: Path, out: Path, t0=None, t1=None, width=720, fps=15, colors=128, crop=None):
    """High-quality GIF via palettegen/paletteuse (diff stats, bayer dither). Never overwrites."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f'{out.name} exists: export a new version instead of overwriting')
    vf = (f'{crop + "," if crop else ""}fps={fps},scale={width}:-1:flags=lanczos,split[a][b];'
          f'[a]palettegen=max_colors={colors}:stats_mode=diff[p];'
          '[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle')
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n']
    if t0 is not None:
        cmd += ['-ss', str(t0)]
    if t1 is not None:
        cmd += ['-to', str(t1)]
    cmd += ['-i', str(src), '-filter_complex', vf, '-loop', '0', str(out)]
    subprocess.run(cmd, check=True)
    return out
