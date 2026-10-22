"""Gold exemplar of the motion-aaa skill: one short piece that exercises every rule of the craft bar.

A small hero ("Pix") runs, crouches (anticipation), jumps along a parabolic arc (stretch along the velocity,
scarf with follow-through), lands (squash, dust burst, ring wave) and settles. The flight is shown in slow motion
whose on-screen tag is DERIVED from the time remap. The world has three parallax layers, a light pool, soft
contact shadows and foreground motes. Every cue is anchored to a word of the narration (estimated alignment here;
a real piece loads the TTS alignment). Events drive particles AND sound. A signature iris wipe leads to the end card.
The same scene model is composed separately for vertical (9:16) and horizontal (16:9); the GIF comes from the render.

    python example_gold.py --out ./motion-out --stills        # stills + contact sheets + event report
    python example_gold.py --out ./motion-out                 # vertical + horizontal MP4 + GIF + measurements
    python example_gold.py --out ./motion-out --format horizontal

Copy this file's SHAPE for a new piece: replace the palette/world/hero (kit), the simulation and the narration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_core as au  # noqa: E402
import motion_core as mc  # noqa: E402
from motion_core import (HORIZ, SS, VERT, Canvas, Remap, View, arc_flight, back_out, burst, clamp, drift_at,  # noqa: E402
                         ease_in_out, ease_out, glow, land_squash, lerp, mix, ring_wave, soft_shadow, span, window)

VERSION = 'v1'
FPS = 30

# ----------------------------------------------------------------- kit: palette tokens (dusk world)
SKY_TOP = (34, 30, 74)
SKY_BOT = (12, 10, 28)
HILL_FAR = (44, 38, 92)
HILL_NEAR = (30, 26, 64)
PLAT = (58, 48, 112)
PLAT_TOP = (126, 112, 214)
PLAT_SIDE = (36, 30, 72)
INK = (8, 6, 18)
CREAM = (250, 244, 232)
MUTE = (172, 164, 206)
HERO = (255, 138, 92)
HERO_HI = (255, 204, 160)
SCARF = (92, 226, 196)
GOLD = (255, 206, 84)
MOON = (255, 226, 170)
ACCENT = GOLD

NARRATION = 'A small crouch first. Slowed down, it stretches along the arc, then lands and squashes.'
UI_STRINGS = ['ANTICIPATION', 'STRETCH', 'SQUASH', 'MOTION AAA', 'GOLD EXEMPLAR', 'procedural demo · seeded',
              'PAUSE', 'REAL SPEED', 'x1/4', 'MOTION KIT', 'one scene model · two canvases · zero stock']

# ----------------------------------------------------------------- simulation (sim time, world units)
GROUND_A, GROUND_B = 6.0, 5.2
X0, X_EDGE, X_LAND = 1.4, 5.7, 11.2
R = .45
S_RUN0, S_GO = .6, 2.06
S_LAND = S_GO + .9


def hero_state(s):
    """(x, y_ground, z, sy, phase) at simulation time s. Deterministic, no randomness."""
    if s < S_RUN0:
        return X0, GROUND_A, .03 * (1 + math.sin(s * 5)), 1 + .03 * math.sin(s * 5), 'idle'
    if s < S_GO - .16:
        k = (s - S_RUN0) / (S_GO - .16 - S_RUN0)
        x = lerp(X0, X_EDGE, ease_in_out(k))
        bob = abs(math.sin((s - S_RUN0) * 13))
        return x, GROUND_A, .07 * bob, 1 + .06 * (bob - .5), 'run'
    if s < S_GO:
        return X_EDGE, GROUND_A, 0.0, mc.anticipation(s, S_GO, .16, .26), 'crouch'
    if s < S_LAND:
        x, y, z, _ = arc_flight(s, S_GO, S_LAND - S_GO, (X_EDGE, GROUND_A), (X_LAND, GROUND_B), h=2.6)
        return x, y, z, 1.0, 'flight'
    return X_LAND, GROUND_B, 0.0, land_squash(s, S_LAND, .3) if s < S_LAND + .3 else 1 + .02 * math.sin((s - S_LAND) * 4),\
        'land'


def hero_pos(s):
    x, y, z, sy, ph = hero_state(s)
    return x, y - z - R * sy


def velocity(s, ds=1 / 240):
    a, b = hero_pos(s - ds), hero_pos(s + ds)
    return (b[0] - a[0]) / (2 * ds), (b[1] - a[1]) / (2 * ds)


def sim_events():
    ev = [(S_RUN0 + .14 * i, 'step', i) for i in range(1, 10) if S_RUN0 + .14 * i < S_GO - .16]
    return ev + [(S_GO, 'jump', None), (S_LAND, 'land', None)]


# ----------------------------------------------------------------- narration anchors -> time remap
_, WORDS = mc.estimate_alignment(NARRATION, t0=.35)


def W(i):
    return WORDS[i]['start']


def E(i):
    return WORDS[i]['end']


R_GO = E(2) + .25                  # launch right after «crouch»
R_LAND = W(12) + .05               # touch-down on «lands»
REMAP = Remap([(0.0, S_GO - R_GO), (R_GO, S_GO), (R_GO + .3, S_GO + .14), (R_LAND - .35, S_LAND - .1),
               (R_LAND, S_LAND), (R_LAND + .7, S_LAND + .7), (60.0, S_LAND + 60 - R_LAND)])
T_END_CARD = max(E(len(WORDS) - 1) + .9, R_LAND + 1.9)
DURATION = round(T_END_CARD + 1.8, 2)
CUES = mc.build_cues(WORDS)


def real_events():
    """Simulation events mapped to real (video) time."""
    out = []
    for s, kind, info in sim_events():
        t = REMAP.inv(s)
        if t is not None:
            out.append((t, kind, info))
    return out


# ----------------------------------------------------------------- per-canvas staging (composed, never cropped)
STAGE = {'h': dict(world_w=13.0, cy=4.55, follow=.55, tag_y=230),
         'v': dict(world_w=7.0, cy=4.4, follow=1.0, tag_y=320)}


def camera_x(s, fmt):
    st = STAGE[fmt.name]
    hx = hero_pos(max(0.0, s - .06))[0]      # small lag = the camera feels operated, the hero stays framed
    lo, hi = st['world_w'] / 2, 16 - st['world_w'] / 2
    base = (lo + hi) / 2
    return clamp(lerp(base, hx, st['follow']), lo, hi)


def make_view(fmt, t, s):
    st = STAGE[fmt.name]
    dr = drift_at(t, seed=1.0, ax=.12, ay=.06)
    return View(fmt.w, fmt.h, world_w=st['world_w'], drift=dr, center=(camera_x(s, fmt), st['cy']))


# ----------------------------------------------------------------- drawing: world layers
def hills(c: Canvas, v: View, color, amp, base_y, freq, seed, par):
    lv = v.layer(par)
    pts = []
    for i in range(0, 61):
        x = -4 + i * 24 / 60
        y = base_y - amp * (.6 * math.sin(x * freq + seed) + .4 * math.sin(x * freq * 2.3 + seed * 2))
        pts.append(lv.p(x, y))
    pts += [lv.p(20, 30), lv.p(-4, 30)]
    c.poly(pts, color)


def platform(img, c: Canvas, v: View, x0, x1, y_top):
    a, b = v.p(x0, y_top), v.p(x1, y_top + 6)
    c.rect(a[0], a[1], b[0], b[1], fill=PLAT, r=v.d(.12))
    c.rect(a[0], a[1], b[0], a[1] + v.d(.16), fill=PLAT_TOP, r=v.d(.08))         # lit top rim
    c.rect(a[0], a[1] + v.d(.16), b[0], a[1] + v.d(.32), fill=mix(PLAT, PLAT_SIDE, .6))   # ambient occlusion
    for i in range(int((x1 - x0) / .9)):                                         # surface studs (texture)
        q = v.p(x0 + .45 + i * .9, y_top + .9 + (i % 2) * .7)
        c.ellipse(q[0], q[1], v.d(.06), fill=mix(PLAT, PLAT_TOP, .25))


def motes(c: Canvas, img, v: View, t, n=22, seed=3):
    """Foreground particles: parallax x1.6, slow drift, twinkle (secondary motion only)."""
    lv = v.layer(1.6)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x0, y0 = rng.uniform(-2, 18), rng.uniform(0, 8)
        sp, ph = rng.uniform(.05, .2), rng.uniform(0, 6.28)
        q = lv.p((x0 + t * sp) % 20 - 2, y0 + .25 * math.sin(t * .6 + ph))
        tw = .5 + .5 * math.sin(t * 2.2 + ph * 3)
        c.ellipse(q[0], q[1], max(1.0, v.d(.025 + .015 * tw)), fill=mix(SKY_BOT, MOON, .35 + .45 * tw))


def blob(c: Canvas, cx, cy, rx, ry, ang, fill, n=36):
    ca, sa = math.cos(ang), math.sin(ang)
    c.poly([(cx + rx * math.cos(2 * math.pi * i / n) * ca - ry * math.sin(2 * math.pi * i / n) * sa,
             cy + rx * math.cos(2 * math.pi * i / n) * sa + ry * math.sin(2 * math.pi * i / n) * ca) for i in range(n)], fill)


def draw_hero(img, c: Canvas, v: View, s):
    x, yg, z, sy, phase = hero_state(s)
    vx, vy = velocity(s)
    speed = math.hypot(vx, vy)
    # contact shadow shrinks and fades with height
    g = v.p(x, yg)
    soft_shadow(img, g[0], g[1] + v.d(.04), v.d(R * 1.3 / (1 + z * .35)), .55 / (1 + z * .8), .32, INK)
    # scarf: secondary motion = the body's own path a few frames earlier (follow-through, never random)
    pts = []
    for k in range(7):
        px, py = hero_pos(s - .022 * k)
        q = v.p(px - .18 * k * (1 if vx >= 0 else -1) * (speed < .5), py - .12 + .02 * k)
        pts.append(q)
    for k in range(len(pts) - 1):
        c.line([pts[k], pts[k + 1]], mix(SKY_BOT, SCARF, 1 - k / 9), max(2, v.d(.13 * (1 - k / 8))))
    # body: squash on the ground, stretch along the velocity in the air (area preserved)
    cx, cy = v.p(*hero_pos(s))
    if phase == 'flight':
        st = 1 + .32 * clamp(speed / 9)
        rx, ry, ang = v.d(R) * st, v.d(R) / st, math.atan2(vy, vx)
    else:
        rx, ry, ang = v.d(R) / math.sqrt(sy), v.d(R) * sy, 0.0
    glow(img, cx, cy, v.d(1.6), HERO, .22)
    blob(c, cx, cy, rx, ry, ang, HERO)
    blob(c, cx - rx * .25, cy - ry * .35, rx * .45, ry * .3, ang, HERO_HI)
    # eyes look where it goes
    look = math.atan2(vy, vx) if speed > .4 else 0.0
    for ex in (-.16, .16):
        q = (cx + v.d(ex + .12), cy - v.d(.08) * sy)
        c.ellipse(q[0], q[1], v.d(.1), v.d(.13) * (sy if phase != 'flight' else 1), fill=CREAM)
        c.ellipse(q[0] + math.cos(look) * v.d(.04), q[1] + math.sin(look) * v.d(.04), v.d(.05), fill=INK)


def callout(c: Canvas, fmt, t, t0, t1, text, accent):
    a = window(t, t0, t1, .22)
    if a <= 0:
        return
    size = c.fit_size(text, 96 if fmt.name == 'h' else 104, fmt.w - 120, 'numc')
    k = back_out(clamp((t - t0) / .35))
    y = fmt.callout_y + (1 - k) * 26
    c.text(fmt.cx, y, text, size, mix(SKY_TOP, CREAM, a), 'numc', anchor='mm')
    tw = c.textlen(text, size, 'numc') * ease_out((t - t0 - .1) / .4)
    c.rect(fmt.cx - tw / 2, y + size * .58, fmt.cx + tw / 2, y + size * .58 + 8, fill=mix(SKY_TOP, accent, a), r=4)


def pill(c: Canvas, x, y, text, size, fg, bg, anchor='r'):
    w = c.textlen(text, size, 'numc') + size * 1.2
    x0 = x - w if anchor == 'r' else x
    c.rect(x0, y - size * .85, x0 + w, y + size * .85, fill=bg, r=size * .85)
    c.text(x0 + w / 2, y, text, size, fg, 'numc', anchor='mm')


# ----------------------------------------------------------------- the scene
class Scene:
    def __init__(self, fmt_name):
        self.fmt = HORIZ if fmt_name == 'h' else VERT
        self.fps = FPS
        self.duration = DURATION
        self.cues = mc.split_long(CUES, (HORIZ, VERT))
        self.events = real_events()

    def compose(self, t):
        fmt = self.fmt
        s = REMAP(t)
        img = mc.gradient_bg(fmt.w, fmt.h, SKY_TOP, SKY_BOT, .24, (60, 40, 30), (.72, .18), 3.0, 7).copy()
        c = Canvas(img)
        v = make_view(fmt, t, s)
        moon = v.layer(.15).p(12.5, 1.4)
        glow(img, moon[0], moon[1], v.d(2.6), MOON, .35)
        c.ellipse(moon[0], moon[1], v.d(.55), fill=MOON)
        hills(c, v, HILL_FAR, .9, 4.6, .55, 1.0, .35)
        hills(c, v, HILL_NEAR, .6, 5.6, .8, 2.4, .6)
        platform(img, c, v, -3, 6.2, GROUND_A)
        platform(img, c, v, 9.8, 20, GROUND_B)
        # particles from events (age in simulation time, so they obey the declared slow motion)
        for te, kind, info in self.events:
            se = REMAP(te)
            if kind == 'step':
                q = v.p(hero_pos(se)[0] - .2, GROUND_A)
                burst(c, q[0], q[1] - v.d(.05), s - se, mix(PLAT, PLAT_TOP, .7), SKY_BOT, n=4, seed=int(info),
                      radius=v.d(.35), life=.35, size=v.d(.05), gravity=-v.d(.15))
            elif kind == 'jump':
                q = v.p(X_EDGE, GROUND_A)
                burst(c, q[0], q[1], s - se, PLAT_TOP, SKY_BOT, n=8, seed=21, radius=v.d(.7), life=.45, size=v.d(.07))
            elif kind == 'land':
                q = v.p(X_LAND, GROUND_B)
                ring_wave(c, q[0], q[1], s - se, GOLD, SKY_BOT, r_max=v.d(1.4), life=.5, width=5)
                burst(c, q[0], q[1] - v.d(.05), s - se, mix(PLAT_TOP, CREAM, .4), SKY_BOT, n=14, seed=33,
                      radius=v.d(1.1), life=.6, size=v.d(.08), gravity=v.d(.3))
        draw_hero(img, c, v, s)
        c = Canvas(img)
        motes(c, img, v, t)
        self.overlays(img, c, t)
        return img

    def overlays(self, img, c, t):
        fmt = self.fmt
        tag_y = STAGE[fmt.name]['tag_y']
        rate = REMAP.rate(t)
        if t < T_END_CARD:
            lab = mc.speed_label(rate)
            hot = rate < .9
            pill(c, fmt.w - 40, tag_y, lab, 32, CREAM if hot else MUTE, mix(SKY_BOT, GOLD if hot else PLAT, .5))
            c.text(40, fmt.h - 30, 'procedural demo · seeded', 20, mix(SKY_BOT, MUTE, .8), 'mono', anchor='lm')
            # header lockup (identity layer)
            c.ellipse(52, fmt.header_y, 12, fill=HERO)
            c.text(76, fmt.header_y, 'MOTION KIT', 30, CREAM, 'numc', anchor='lm')
        callout(c, fmt, t, W(1) - .1, R_GO + .35, 'ANTICIPATION', GOLD)
        callout(c, fmt, t, R_GO + .35, R_LAND - .15, 'STRETCH', SCARF)
        callout(c, fmt, t, R_LAND - .15, T_END_CARD - .2, 'SQUASH', HERO)
        cue, a = mc.caption_at(self.cues, t)
        if cue and t < T_END_CARD:
            mc.draw_caption(c, fmt, cue, t, a, base=SKY_BOT, active=GOLD, ink=INK)
        # signature transition: iris closes on the hero, end card opens
        k = span(t, T_END_CARD - .45, T_END_CARD)
        if k > 0:
            v = make_view(fmt, t, REMAP(t))
            hx, hy = v.p(*hero_pos(REMAP(t)))
            rmax = math.hypot(fmt.w, fmt.h)
            r = rmax * (1 - ease_in_out(k))
            m = mc.Image.new('L', img.size, 255)
            mc.ImageDraw.Draw(m).ellipse(((hx - r) * SS, (hy - r) * SS, (hx + r) * SS, (hy + r) * SS), fill=0)
            img.paste(INK, (0, 0), m)
            Canvas(img).ellipse(hx, hy, r, outline=mix(INK, GOLD, 1 - k * .5), width=6)
        if t >= T_END_CARD:
            u = t - T_END_CARD
            a = span(u, .05, .45)
            kk = back_out(clamp((u - .05) / .45))
            c = Canvas(img)
            c.text(fmt.cx, fmt.h * .44 + (1 - kk) * 40, 'MOTION AAA', 150 if fmt.name == 'h' else 130,
                   mix(INK, CREAM, a), 'numc', anchor='mm')
            c.text(fmt.cx, fmt.h * .44 + 110, 'GOLD EXEMPLAR', 56, mix(INK, GOLD, a), 'numc', anchor='mm')
            c.text(fmt.cx, fmt.h * .44 + 180, 'one scene model · two canvases · zero stock', 32,
                   mix(INK, MUTE, span(u, .4, .8)), 'numc', anchor='mm')


def make_scene(fmt_name):
    """Top-level factory: each render worker builds its own scene."""
    return Scene(fmt_name)


# ----------------------------------------------------------------- audio (music + event SFX)
def build_audio(scene: Scene):
    dur = scene.duration
    L = au.new_tracks(dur)
    bpm = 100
    beat = 60 / bpm
    prog = [(60, 'M'), (57, 'm'), (53, 'M'), (55, 'M')]          # I-vi-IV-V
    for b in range(int(dur / (4 * beat)) + 1):
        tb = b * 4 * beat
        root, q = prog[b % 4]
        ch = [root, root + (3 if q == 'm' else 4), root + 7]
        au.place(L['pad'], au.pad([m - 12 for m in ch], 4 * beat + .3, seed=b, cutoff=1100), tb, .7)
        for j, n_ in enumerate([ch[0], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[2], ch[1] + 12, ch[2]]):
            au.place(L['pluck'], au.stereo(au.pluck(au.midi_hz(n_ + 12), .5, .55, seed=j), -.4 + .8 * (j % 2)),
                     tb + j * beat / 2, .45)
        for i in (0, 2):
            au.place(L['bass'], au.stereo(au.bass(au.midi_hz(root - 24), beat * 1.6)), tb + i * beat, .8)
        au.place(L['drums'], au.stereo(au.kick(b)), tb, .7)
        for i in range(8):
            au.place(L['drums'], au.stereo(au.hat(b * 8 + i), .25 if i % 2 else -.25), tb + i * beat / 2, .25)
    music = au.master_music(L, dur, gains={'pad': 1.0, 'pluck': .9, 'bass': .8, 'drums': .7, 'fx': .6})
    n = len(music)
    sfx = np.zeros((n, 2))
    lib = {'step': au.match(au.sfx_click(), -36), 'jump': au.match(au.sfx_jump(), -26),
           'land': au.match(au.sfx_thud(), -24), 'pop': au.match(au.sfx_pop(), -30),
           'whoosh': au.match(au.sfx_whoosh(.3), -27), 'chime': au.match(au.sfx_chime(), -27)}
    cue_times = [W(1) - .1, R_GO + .35, R_LAND - .15]
    placed = [(t, k) for t, k, _ in scene.events] + [(t, 'pop') for t in cue_times] + \
        [(T_END_CARD - .45, 'whoosh'), (T_END_CARD + .1, 'chime')]
    for t, kind in placed:
        au.place(sfx, au.stereo(lib[kind], .1), t)
    # the bed dips a little under the slow-motion flight so the moment reads as suspended
    dip = np.interp(np.arange(n) / au.SR, [0, R_GO, R_GO + .3, R_LAND - .2, R_LAND + .2, dur + 5],
                       [1, 1, .55, .55, 1, 1])
    music = music * dip[:, None]
    return au.mix_master(dur, music=music, sfx=sfx)


# ----------------------------------------------------------------- CLI
def sample_times(n=12):
    return [round(DURATION * (i + .5) / n, 2) for i in range(n)] + [round(R_GO - .05, 2), round(R_LAND + .05, 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=Path('motion-out'))
    ap.add_argument('--format', choices=['vertical', 'horizontal', 'all'], default='all')
    ap.add_argument('--stills', action='store_true')
    ap.add_argument('--workers', type=int)
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    mc.check_glyphs(UI_STRINGS + [NARRATION])
    fmts = {'vertical': ['v'], 'horizontal': ['h'], 'all': ['v', 'h']}[a.format]
    a.out.mkdir(parents=True, exist_ok=True)
    report = mc.events_report(real_events(), WORDS)
    (a.out / 'events-report.txt').write_text(report + '\n', encoding='utf-8')
    print(report)
    for f in fmts:
        sc = Scene(f)
        folder = a.out / ('vertical' if f == 'v' else 'horizontal')
        for cue in sc.cues:
            assert len(mc.wrap_words(Canvas(mc.Image.new('RGB', (8, 8))), cue['words'], sc.fmt.cap_size,
                                     sc.fmt.cap_maxw)) <= 2, cue['text']
        paths = mc.stills(sc, sample_times(), folder / 'qa')
        mc.contact_sheet(paths, folder / 'contacto.png')
        if a.stills:
            print('stills ->', folder)
            continue
        name = f'gold-{folder.name}-{VERSION}'
        mixd, ainfo = build_audio(sc)
        wav = folder / f'{name}-mix.wav'
        au.write_wav(wav, mixd)
        (folder / 'captions.srt').write_text(mc.to_srt(sc.cues), encoding='utf-8')
        mp4 = folder / f'{name}.mp4'
        rinfo = mc.render(make_scene, (f,), mp4, wav, workers=a.workers)
        wav.unlink()
        lufs, peak = au.loudness_report(mp4)
        meas = {'video': mp4.name, 'duration_seconds': DURATION, 'resolution': [sc.fmt.w, sc.fmt.h], 'fps': FPS,
                'final_lufs_ebur128': lufs, 'final_true_peak_dbtp': peak, 'audio': ainfo,
                'sha256': hashlib.sha256(mp4.read_bytes()).hexdigest(), 'size_bytes': mp4.stat().st_size, **rinfo}
        (folder / 'mediciones.json').write_text(json.dumps(meas, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in meas.items() if k != 'command'}, indent=2))
        if f == 'h':
            gif = a.out / 'gif' / f'gold-{VERSION}.gif'
            gif.parent.mkdir(exist_ok=True)
            mc.export_gif(mp4, gif, 0.2, round(R_LAND + 1.4, 2), width=720, fps=15)
            print('gif ->', gif, gif.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
