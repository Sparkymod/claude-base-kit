"""audio_core — loudness, limiter, synthesis and mix for procedural motion (motion-aaa skill).

48 kHz float64. Mono buffers are 1-D, stereo buffers are (n, 2). Every stochastic voice takes an explicit
seed, so a piece's music is identical no matter what was composed before it in the same process.

Mix targets that shipped: voice -16 LUFS, music bed -23.5 LUFS ducked 9 dB under speech, master -16 LUFS,
true-peak limiter -1.6 dBTP. Acceptance on the encoded file: |LUFS + 16| <= 0.5, true peak <= -1.5 dBTP.
"""
from __future__ import annotations

from functools import lru_cache
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from scipy.ndimage import maximum_filter1d, minimum_filter1d
from scipy.signal import butter, lfilter, resample_poly, sosfilt

SR = 48000


# ----------------------------------------------------------------- io and basics
def decode(path: Path) -> np.ndarray:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<f4').astype(np.float64)


def write_wav(path: Path, x: np.ndarray):
    x = x[:, None] if x.ndim == 1 else x
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def stereo(x, pan=0.0):
    """Mono -> stereo with constant-power pan (-1..1)."""
    a = (pan + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], axis=1)


def place(buf, sig, t, gain=1.0):
    """Add sig into buf starting at t seconds (clipped to the buffer)."""
    i = int(round(t * SR))
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j0, j1 = max(0, -i), min(len(sig), len(buf) - i)
    buf[i + j0:i + j1] += sig[j0:j1] * gain


def env(n, attack, decay, sustain=0.0, release=None):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(attack, 1e-4)) * (sustain + (1 - sustain) * np.exp(-np.maximum(0, t - attack) / decay))
    if release:
        e *= np.clip((n / SR - t) / release, 0, 1)
    return e


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def lowpass(x, hz, order=2):
    return sosfilt(butter(order, hz, 'lowpass', fs=SR, output='sos'), x, axis=0)


def highpass(x, hz, order=2):
    return sosfilt(butter(order, hz, 'highpass', fs=SR, output='sos'), x, axis=0)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x, axis=0)


# ----------------------------------------------------------------- loudness (ITU-R BS.1770-4)
def k_weight(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    """Integrated loudness with absolute (-70) and relative (-10) gates."""
    x = x if x.ndim == 2 else x[:, None]
    y = k_weight(x)
    blk, hop = int(.4 * SR), int(.1 * SR)
    p = np.sum(y ** 2, axis=1)
    if len(p) < blk:
        return -0.691 + 10 * math.log10(np.mean(p) + 1e-12)
    cs = np.concatenate([[0], np.cumsum(p)])
    starts = np.arange(0, len(p) - blk + 1, hop)
    z = (cs[starts + blk] - cs[starts]) / blk
    z = z[-0.691 + 10 * np.log10(z + 1e-12) > -70]
    if not len(z):
        return -99.0
    rel = -0.691 + 10 * math.log10(np.mean(z)) - 10
    z = z[(-0.691 + 10 * np.log10(z)) > rel]
    return -0.691 + 10 * math.log10(np.mean(z))


def short_loudness(x):
    """K-weighted loudness of a short sound over its active part (to match SFX kinds to each other)."""
    y = k_weight(x if x.ndim == 1 else x.mean(axis=1))
    active = np.abs(y) > np.abs(y).max() * .05
    return -0.691 + 10 * math.log10(np.mean(y[active] ** 2) + 1e-12)


def match(x, target):
    return x * 10 ** ((target - short_loudness(x)) / 20)


def true_peak_db(x):
    return 20 * math.log10(np.max(np.abs(resample_poly(x, 4, 1, axis=0))) + 1e-12)


def limit(x, ceiling_db=-1.6):
    """Look-ahead limiter on the x4-oversampled peak (true-peak estimate). Fast attack, slow release."""
    x = x if x.ndim == 2 else x[:, None]
    thr = 10 ** (ceiling_db / 20)
    up = np.max(np.abs(resample_poly(x, 4, 1, axis=0)), axis=1)
    peak = np.max(up[:len(up) // 4 * 4].reshape(-1, 4), axis=1)
    peak = np.pad(peak, (0, len(x) - len(peak)), mode='edge')
    need = np.minimum(1.0, thr / np.maximum(peak, 1e-9))
    look = int(.005 * SR)
    need = minimum_filter1d(need, size=2 * look + 1)
    a = math.exp(-1 / (.06 * SR))
    g = np.empty_like(need)
    cur = 1.0
    for i in range(0, len(need), 64):
        m = need[i:i + 64].min()
        cur = m if m < cur else cur * a ** 64 + m * (1 - a ** 64)
        g[i:i + 64] = cur
    g = np.minimum(np.convolve(g, np.ones(look) / look, mode='same'), need)
    return x * g[:, None]


def loudness_report(path: Path):
    """(integrated LUFS, true peak dBTP) measured by FFmpeg ebur128 on an encoded file."""
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    s = out[out.rfind('Summary:'):]
    return float(s.split('I:')[1].split('LUFS')[0]), float(s.split('Peak:')[1].split('dBFS')[0])


# ----------------------------------------------------------------- voice
def speech_envelope(words, n):
    """0..1 envelope that is 1 while words are spoken (hold 300 ms, attack 50 ms, release 500 ms)."""
    active = np.zeros(n)
    for w in words:
        active[max(0, int(w['start'] * SR)):min(n, int(w['end'] * SR))] = 1
    active = maximum_filter1d(active, size=int(SR * .3), origin=-int(SR * .1))
    a_att, a_rel = math.exp(-1 / (SR * .05)), math.exp(-1 / (SR * .5))
    att = lfilter([1 - a_att], [1, -a_att], active)
    rel = lfilter([1 - a_rel], [1, -a_rel], active)
    return np.clip(np.maximum(att, rel), 0, 1)


def pause_cuts(words, pauses):
    """pauses: [(word_index, seconds)] (-1 = at the start) -> cuts in the original voice [(t, seconds)]."""
    cuts = []
    for i, sec in sorted(pauses):
        if i < 0:
            cut = 0.0
        else:
            a = words[i]['end']
            b = words[i + 1]['start'] if i + 1 < len(words) else a + .3
            cut = a + .45 * (b - a)
        cuts.append((cut, sec))
    return cuts


def shift_words(words, pauses):
    """Words moved by the inserted pauses, plus the pause windows in the new time."""
    cuts = pause_cuts(words, pauses)
    shifted = [{**w, 'start': w['start'] + sum(s for c, s in cuts if c <= w['start'] + 1e-6),
                'end': w['end'] + sum(s for c, s in cuts if c <= w['start'] + 1e-6)} for w in words]
    windows, acc = [], 0.0
    for cut, sec in cuts:
        windows.append((cut + acc, cut + acc + sec))
        acc += sec
    return shifted, windows


def voice_block(voice_file: Path, words, pauses):
    """Decoded voice with the same silences that shift_words inserted."""
    audio = decode(voice_file)
    pieces, last = [], 0
    for cut, sec in pause_cuts(words, pauses):
        k = int(round(cut * SR))
        pieces += [audio[last:k], np.zeros(int(round(sec * SR)))]
        last = k
    pieces.append(audio[last:])
    return np.concatenate(pieces)


# ----------------------------------------------------------------- instruments (vary them per piece)
@lru_cache(maxsize=512)
def _pluck(freq_c, dur_c, bright_c, seed):
    """Karplus-Strong plucked string."""
    freq, dur, bright = freq_c / 100, dur_c / 1000, bright_c / 100
    n = int(SR * dur)
    period = max(2, int(round(SR / freq)))
    buf = lowpass(noise(period, seed), 2000 + 8000 * bright, 1)
    out = np.empty(n)
    for i in range(n):
        v = buf[i % period]
        out[i] = v
        buf[i % period] = .996 * .5 * (v + buf[(i + 1) % period])
    return out * env(n, .002, dur * .6, release=.05)


def pluck(freq, dur=.6, bright=.5, seed=0):
    return _pluck(int(freq * 100), int(dur * 1000), int(bright * 100), seed).copy()


def mallet(freq, dur=.7, partials=((1, 1, .9), (2.76, .35, .3), (5.4, .12, .12)), seed=0):
    """Additive mallet (marimba/kalimba/handpan-like by choosing partials: (ratio, amp, decay_s))."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    ph = np.random.default_rng(seed).uniform(0, 6.28, len(partials))
    out = sum(a * np.sin(2 * math.pi * freq * r * t + p) * np.exp(-t / d) for (r, a, d), p in zip(partials, ph))
    return out * np.minimum(1, t / .003)


def pad(midis, dur, seed=0, cutoff=1200, detune=.006, attack=.4):
    """Detuned-saw pad, low-passed, slow attack. Returns stereo."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    L, R = np.zeros(n), np.zeros(n)
    for m in midis:
        f = midi_hz(m)
        for d, side in ((-detune, 0), (detune, 1), (0, 2)):
            ph = rng.uniform(0, 1)
            saw = 2 * ((f * (1 + d) * t + ph) % 1) - 1
            if side in (0, 2):
                L += saw
            if side in (1, 2):
                R += saw
    x = np.stack([L, R], axis=1) / (len(midis) * 2)
    x = lowpass(x, cutoff, 2)
    return x * env(n, attack, 9e9, sustain=1, release=min(.6, dur * .4))[:, None]


def bass(freq, dur, seed=0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * math.pi * freq * t) + .25 * np.sin(4 * math.pi * freq * t)
    return x * env(n, .01, dur * .7, release=.04)


def kick(seed=0):
    n = int(SR * .35)
    t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t / .04)
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / .12) + .2 * noise(n, seed) * np.exp(-t / .005)


def snare(seed=0):
    n = int(SR * .25)
    t = np.arange(n) / SR
    return .6 * bandpass(noise(n, seed), 900, 6000) * np.exp(-t / .07) + .4 * np.sin(2 * math.pi * 190 * t) * np.exp(-t / .05)


def hat(seed=0, open_=False):
    n = int(SR * (.25 if open_ else .06))
    t = np.arange(n) / SR
    return highpass(noise(n, seed), 7000) * np.exp(-t / (.08 if open_ else .015))


def shaker(seed=0):
    n = int(SR * .09)
    t = np.arange(n) / SR
    return bandpass(noise(n, seed), 4000, 11000) * np.sin(math.pi * np.minimum(1, t / .09)) ** 2


def bell(freq, dur=.8):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return sum(a * np.sin(2 * math.pi * freq * r * t) * np.exp(-t / d)
               for r, a, d in ((1, 1, .5), (2.4, .4, .3), (5.95, .2, .12))) * np.minimum(1, t / .002)


def riser(dur, seed=0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    k = t / dur
    sweep = np.sin(2 * math.pi * np.cumsum(200 + 1800 * k ** 2) / SR)
    return (.5 * bandpass(noise(n, seed), 600, 9000) + .3 * sweep) * k ** 2


# ----------------------------------------------------------------- SFX recipes (match each kind to a target)
def sfx_whoosh(dur=.18, seed=4):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return bandpass(noise(n, seed), 500, 5000) * np.sin(math.pi * t / dur) ** 2


def sfx_pop(seed=5):
    n = int(SR * .08)
    t = np.arange(n) / SR
    return np.sin(2 * math.pi * np.cumsum(900 - 600 * t / .08) / SR) * np.exp(-t / .02)


def sfx_thud(seed=6):
    n = int(SR * .2)
    t = np.arange(n) / SR
    return np.sin(2 * math.pi * np.cumsum(120 - 60 * t / .2) / SR) * np.exp(-t / .05) + \
        .3 * lowpass(noise(n, seed), 1500) * np.exp(-t / .02)


def sfx_click(seed=7):
    n = int(SR * .03)
    t = np.arange(n) / SR
    return highpass(noise(n, seed), 2500) * np.exp(-t / .004)


def sfx_chime(freq=1320):
    return bell(freq, .6) * .6 + bell(freq * 1.5, .6) * .3


def sfx_jump(seed=8):
    n = int(SR * .16)
    t = np.arange(n) / SR
    return np.sin(2 * math.pi * np.cumsum(300 + 900 * t / .16) / SR) * np.exp(-t / .07)


# ----------------------------------------------------------------- music bus and mix
def new_tracks(dur, names=('pad', 'pluck', 'bass', 'drums', 'fx')):
    n = int(SR * (dur + 2))
    return {k: np.zeros((n, 2)) for k in names}


def master_music(tracks, dur, gains=None, seed=11, reverb=.18, decay=.22, fade=2.5):
    """Sum tracks, high-pass 45 Hz, short seeded noise reverb, fade out over the last `fade` seconds."""
    gains = gains or {}
    x = sum(tracks[k] * gains.get(k, 1.0) for k in tracks)
    x = highpass(x, 45)
    ir_n = int(SR * 4 * decay)
    ir = np.random.default_rng(seed).standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / decay)[:, None]
    ir = lowpass(ir, 4500)
    ir /= np.sqrt(np.sum(ir ** 2, axis=0))
    n = len(x)
    size = 1 << int(math.ceil(math.log2(n + ir_n)))
    wet = np.fft.irfft(np.fft.rfft(x, size, axis=0) * np.fft.rfft(ir, size, axis=0), size, axis=0)[:n]
    out = (x + reverb * wet)[:int(SR * dur)]
    if fade:
        out *= (np.clip((dur - np.arange(len(out)) / SR) / fade, 0, 1) ** 1.5)[:, None]
    return out


def mix_master(dur, voice=None, words=(), music=None, sfx=None, voice_lufs=-16.0, bed_lufs=-23.5, duck_db=9.0,
               target=-16.0, ceiling=-1.6):
    """voice (mono), music (stereo), sfx (stereo) -> (master stereo, info). Pass the words of the voice
    (already shifted to video time) to duck the bed under speech."""
    n = int(round(dur * SR))
    out = np.zeros((n, 2))
    info = {}
    if voice is not None and len(voice):
        v = np.pad(voice, (0, max(0, n - len(voice))))[:n]
        v = v * 10 ** ((voice_lufs - lufs(v)) / 20)
        out += stereo(v) * math.sqrt(2)
    if music is not None:
        m = np.pad(music, ((0, max(0, n - len(music))), (0, 0)))[:n]
        m = m * 10 ** ((bed_lufs - lufs(m)) / 20)
        if words:
            m = m * (1 - (1 - 10 ** (-duck_db / 20)) * speech_envelope(list(words), n))[:, None]
        out += m
    if sfx is not None:
        out += np.pad(sfx, ((0, max(0, n - len(sfx))), (0, 0)))[:n]
    g = target - lufs(out)
    out = limit(out * 10 ** (g / 20), ceiling)
    info.update({'pre_limit_gain_db': round(g, 2), 'lufs_numpy': round(lufs(out), 2),
                 'true_peak_numpy_dbtp': round(true_peak_db(out), 2)})
    return out, info
