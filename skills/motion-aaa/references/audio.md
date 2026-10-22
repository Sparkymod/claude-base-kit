# Audio — voice, procedural music, event SFX and the mix

All functions referenced here exist in `scripts/audio_core.py` (alignment helpers in
`scripts/motion_core.py`). Sample rate 48 kHz, float64
buffers, stereo as `(n, 2)`.

## Voice

- **One TTS call per block**, with character-level alignment (`characters`,
  `character_start_times_seconds`, `character_end_times_seconds`). Store `voz.mp3` +
  `tiempos.json` per block; shorts reuse their block's voice.
- **Expressive tags** (e.g. `[softly]`, `[excited]`) are blanked out of the alignment before
  building words and captions (`load_alignment` does it without shifting positions).
- **Before paying for voice**, build an animatic from `estimate_alignment(text)` (calm
  Spanish explainer measured ≈ 0.0635 s per character inside words, pauses ≈ 0.67 s after
  ".", 0.26 s after ",", 0.60 s after ":"). Re-measure for each voice/language.
- **Pauses** for staging are inserted by cutting the voice between two words
  (`shift_words` + `voice_block`); scene anchors use the shifted word times.
- Voice normalized to **−16 LUFS** per block before mixing.
- Never regenerate approved narration to fix timing; never read credentials files for a
  render; record character counts and reported cost when a TTS call is made.

## Procedural music

Write one module per piece with: `BPM`, chord progressions by mode, a `MOODS` table (root,
progression, active layers) per block/section, and `compose_section(mood, t0, t1, tracks)`
that walks bars and places notes. Layers live on separate tracks (`pad`, `pluck`, `bass`,
`drums`, `fx`) so they can be gained and automated.

Instrument recipes available in the engine (vary them per piece so every episode has its
own color): Karplus–Strong pluck, additive mallet (marimba/handpan/kalimba-like partials),
detuned-saw pad with low-pass, sine/triangle bass with soft attack, noise-based percussion
(kick, snare, hat, shaker, tambourine), bell, riser, whoosh.

Seeding: every stochastic voice takes an explicit `seed`. A module-level RNG that is
consumed by each composition makes a theme depend on what was composed before it in the same
process — compose one piece per process or pass seeds explicitly.

Master the music bus: high-pass ~45 Hz, short seeded noise reverb (0.2–0.3 s decay, low-passed),
fade out over the last 2.5 s.

## Event SFX

- Each event kind maps to a short synthesized sound; each sound is **loudness-matched per
  kind** with `short_loudness` to a target table (e.g. ticks −33, impacts −27, specials −24
  LUFS-ish short-term), so a soft tick never jumps over a hit.
- Place SFX from the same event list that draws particles; skip events from panels that are
  not visible; de-duplicate same-kind events closer than 80 ms.
- Pan slightly by screen position for width; keep SFX mono-compatible.

## The mix chain (numbers that shipped)

1. Voice track at −16 LUFS (per block).
2. Music bed normalized to **−23.5 LUFS**, then **ducked 9 dB** under speech using
   `speech_envelope(words)` (300 ms hold, 50 ms attack, 500 ms release).
3. Optional musical gestures: dips on impacts, mutes during A/B listening windows, stings on
   block cards.
4. Sum voice·√2 (mono to center) + music + SFX.
5. Normalize the sum to **−16 LUFS** integrated (BS.1770, gated).
6. **True-peak limiter at −1.6 dBTP** (look-ahead on ×4 oversampled peak).
7. Report stems LUFS, SFX peak, pre-limit gain, numpy LUFS and true peak into
   `mediciones.json`; re-measure LUFS/true peak on the encoded file with FFmpeg `ebur128`.

Acceptance: |LUFS + 16| ≤ 0.5 and true peak ≤ −1.5 dBTP on the encoded file.

GIFs carry no audio; silent shorts still get music + SFX unless the brief says otherwise.
