# Architecture — how a piece is built in code

The engine (`scripts/motion_core.py`, `scripts/audio_core.py`) is generic. A piece adds a
**kit**, **scenes**, **blocks** and a **video** module on top. `scripts/example_gold.py`
shows the whole stack in one file; split it into modules once a piece has more than one block.

## Coordinates and canvases

- All drawing happens in **logical pixels of the final video** (1080×1920, 1920×1080…). The
  `Canvas` multiplies by `SS` (supersampling, 2) internally; frames are box-downscaled at the
  end (`finish`). Never draw in device pixels directly.
- `Fmt` describes a canvas: size, named **slots** (`full`, `L`, `R`, `wide`, `c1..c3`,
  `q1..q4`, custom), caption center/size/max width, header and callout rows, info area.
  Vertical and horizontal formats define the *same slot names* with different rectangles, so a
  block's layout keys work on both canvases — composition per canvas, no cropping.
- World units (e.g. "tiles", "meters") map to screen through a `View(sw, sh, drift, zoom,
  center)` per panel; parallax = the same drift multiplied by a per-layer factor.

## Time model

- `compose(t)` is a **pure function of time** → frames are independent and render in any
  order, in parallel, and any instant can be rendered as a still.
- Building blocks: `span(t, a, b)` (smooth 0→1), `window(t, a, b, fade)` (in-hold-out),
  `ease_out`, `ease_in_out`, `back_out`, `spring`, `lerp`, `mix(color0, color1, a)`.
- `Remap(keys)`: real time → simulation time with monotone PCHIP interpolation. This is how
  slow motion, freezes and resumes happen without velocity jumps; `rate(t)` tells the speed
  so the on-screen tag (`x1/4`) is derived, not hand-typed.
- **Anchors are words.** A block loads its words; `W(i)` = start, `E(i)` = end of word *i*.
  Every reveal, callout and layout change is written as `W(17) - .3`, never as a bare second.
  Re-timing the voice moves the whole choreography with it.
- Simulations start **before** the block (`T0 = -3`) so action is already in motion at t=0.

## Simulation and events

- Fixed-step deterministic simulation (e.g. 1/120 s) of the mechanic, data process or
  system; precomputed once per block, sampled at render time.
- Randomness only through a seeded generator owned by the piece (a xorshift32 with seed
  mixing + warm-up discards avoids the small-seed bias; verify distribution over 10⁵ draws).
- Every meaningful moment appends `(t, kind, info)` to the panel's event list. Consumers:
  particles (age = t_now − t_event), SFX placement, badges, and the **event report**
  (`events_report`) that prints each event with the word being spoken — reconcile it with the
  script and save it next to the code before rendering.

## Blocks and layouts

```
class Block:
    voice, number, name, mood, pauses, hook, question, motto, tail
    build():   panels = {...}; layout = [(t, {pid: slot})]; layout_v = optional vertical-only
               focus = [(t0, t1, pid)]; marks = [(t0, t1, pid, ok, text)]; tags = [...]
    draw(frame, canvas, fmt, tb):  layout_at → place each panel → marks/tags → info → overlays
    sound_events(fmt): visible-panel events → [(t, sfx_kind, gain)]
```

`layout_at(keys, t, fmt)` returns `{pid: (rect, alpha)}` with eased transitions between
keyframes; a panel renders its own world into an off-screen image of its rect size and is
pasted with a rounded mask, frame border tinted by focus, and its letter/label header.

## The video timeline

`Video(kind)` builds a list of segments: `title`, `card`, `block`, `end` with global start
times. `compose(t)` finds the segment, converts to local time and draws, then overlays the
caption active at `t`. A short = one block + tail (hook overlay at start, question + CTA at
end). Captions are collected from all blocks shifted by their segment start → SRT.

## Render pipeline

1. Checks: glyph coverage of every string literal, captions ≤ 2 lines on every canvas,
   cues ordered and inside the duration.
2. Audio: build the mix → WAV.
3. Frames: `multiprocessing.Pool(workers, initializer=build_video)` → `imap(frame, range(N),
   chunksize=4)` → raw RGB bytes piped to FFmpeg (`-f rawvideo -pix_fmt rgb24 -s WxH -r FPS
   -i pipe:0`) muxed with the WAV: `libx264 -preset slow -crf 17 -tune animation -pix_fmt
   yuv420p`, `aac 256k 48 kHz`, `-movflags +faststart`, `-n` (never overwrite).
4. On any exception: kill the encoder and delete the partial file.
5. QA: stills at sample times → `qa/` + `contacto.png`; measurements JSON; validation pass on
   the encoded file.

The initializer builds the scene **inside each worker** (no pickling of lambdas or closures;
a factory function at module top level is passed by reference).

## Performance and memory

- Cache everything that depends only on size: backgrounds, radial light masks, shadow masks,
  rounded masks — with small `lru_cache` sizes for size-keyed images (panel sizes change
  every frame during transitions; a large cache exhausts RAM across workers).
- Workers: `min(6, cpu-2)` for 1080p by default; 4 for a 5-minute long video rendered alone;
  expose `RENDER_WORKERS` to override. Record wall time per render.
- Draw particles and textures with few large primitives instead of per-pixel Python loops;
  use NumPy for full-frame fields (gradients, grain, vignette).

## Regression guard for the engine

When the engine changes after pieces were approved, prove nothing moved: hash the raw bytes
of every frame (and the SRT and WAV) with the old and new code and compare. Keep the hashes
of approved pieces in a `verification/` folder and a script that recomputes them.
