# Formats, encoding, GIFs, validation and delivery

## Canvas presets (`motion_core.py`)

| Preset | Size | Slots | Caption band | Notes |
|---|---|---|---|---|
| `VERT` | 1080×1920 | full, wide, L(top), R(bottom), c1–c3 stacked, q1–q4 | cy≈1484, 58 px, max 940 | keep 0–220 px top and ~380 px bottom clear of platform UI |
| `HORIZ` | 1920×1080 | full, wide, L, R side by side, c1–c3 columns, q1–q4 | cy≈960, 52 px, max 1500 | subtitles also shipped as SRT |
| `SQUARE` | 1080×1080 | full, L, R, q1–q4 | cy≈960, 48 px | feeds |

If the narration uses spatial words ("top/bottom"), the horizontal layout must respect them
(stacked panels), not the default side-by-side.

## Duration budgets

| Format | Budget | Structure |
|---|---|---|
| GIF | 2–15 s | one loop: establish → action → payoff → return to the first frame |
| Short | 15–60 s | hook 0–3 s · context to ~10 s · demo · result/limit · end card 3–5 s |
| Long | 1–10 min | title 2.8 s · per block: card 1.8 s + block 30–45 s · end card 4.5 s |

10 minutes is a hard cap for this skill: beyond it, split into parts.

## Encoding

- Video: H.264 (`libx264 -preset slow -crf 17 -tune animation -pix_fmt yuv420p`), 30 fps
  (60 fps only for fast motion demos), `-movflags +faststart`.
- Audio: AAC 256 kb/s, 48 kHz, stereo.
- Never `-y`. Version suffix `-vN`; a fix is a new version, the old file stays.

## GIF export (from the rendered MP4 or a silent render)

```
ffmpeg -ss T0 -to T1 -i in.mp4 -filter_complex \
 "fps=15,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" \
 -loop 0 out.gif
```

- 12–20 fps, 480–960 px wide; `stats_mode=diff` + `diff_mode=rectangle` keep size down for
  mostly static backgrounds. Optional crop before `fps` to frame the action.
- Seamless loop: design the piece so the last frame equals the first (cyclic time `t % T`,
  periodic drift with period T, particles that respawn).
- Target < 5 MB for blogs/READMEs; reduce fps, width or colors in that order.

## Validation (on the delivered file — `scripts/validate.py`)

1. `ffmpeg -v error -i file -f null -` → **0 decode errors**.
2. `ffprobe` → width, height, fps, duration match the timeline.
3. `ebur128=peak=true` → integrated LUFS within ±0.5 of −16, true peak ≤ −1.5 dBTP (MP4).
4. 12 frames (< 60 s) or 24 frames (longer) extracted **from the file** at uniform times →
   `qa/mp4/` + `qa-mp4-contacto.png`; the model opens the sheet and inspects it.
5. Write `validacion.json` with all of the above and `ok`.

Exit non-zero if anything fails; a failing piece is fixed as a new version, never patched in
place or shipped "almost".

## Delivery checklist

- [ ] Final file(s) with version suffix
- [ ] Captions SRT (narrated pieces) and `timeline.json` (segments, chapters, cues)
- [ ] `mediciones.json` (probe, LUFS, true peak, stems, render seconds, workers, SHA-256, command)
- [ ] `validacion.json` + `qa-mp4-contacto.png` (from the file) + `contacto.png` (stills)
- [ ] Event report reconciled with the script
- [ ] README: what changed and why, how to reproduce, dependencies + licenses, what was and
      was not inspected, next step
- [ ] Nothing published or uploaded — publishing is a separate, explicitly authorized step
