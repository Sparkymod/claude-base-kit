---
name: motion-aaa
description: "Direct and render AAA procedural motion as deterministic code — animated GIFs, vertical shorts and horizontal videos up to 10 minutes: a per-piece aesthetic kit, simulation-driven picture and sound, narration-anchored choreography, procedural music, a -16 LUFS mix, and QA on frames of the final file. Triggers: /motion-aaa, 'haz un motion', 'crea un motion', 'animación AAA', 'video animado', 'motion graphics', 'hazme un gif animado', 'video corto animado', 'video largo animado', 'short animado', 'animate this explainer'."
---

# Motion AAA — procedural motion directed and rendered by Claude Code

> The model is the director, the animator, the composer and the first reviewer. Every frame
> is drawn by code, every result comes from a declared simulation, every cut lands on a
> spoken word, and nothing ships until the model has looked at frames pulled from the final
> file. Quality bar: AAA, even when it takes longer.

This is the method that produced a weekly series of explainer videos (6 shorts + 1 long
video per week, a new aesthetic every week, same channel identity) with zero stock footage
and zero generative video. It generalizes to any subject that can be **shown with shapes,
light and motion**: game mechanics, algorithms, product flows, data stories, physics,
UI walkthroughs, brand loops.

## Formats this skill delivers

| Format | Canvas | Duration | Typical use | Audio |
|---|---|---|---|---|
| **GIF** | 480–960 px wide, any aspect | 2–15 s, seamless loop preferred | blog/docs/README, social reply | none |
| **Short** | 1080×1920, 9:16, 30 fps | 15–60 s (platform max ~180 s) | discovery, one idea | voice + music + SFX |
| **Long** | 1920×1080, 16:9, 30 fps | 1–10 min (hard cap 10) | full topic, chapters | voice + music + SFX |
| **Square / custom** | 1080×1080 or as asked | ≤ 60 s | feeds, embeds | optional |

A long video is a **sequence of self-contained blocks** (30–45 s each); every block can be
re-composed as its own short. Each canvas is **composed separately from the same scene
model — never cropped** (a 16:9 frame center-cropped to 9:16 loses the staging).

## Non-negotiables (truth before beauty)

1. **Motion never contradicts the thing it explains.** No floating, cheating, or "cartoon
   physics" that the mechanic/data would not produce. Prettier-but-false is a defect.
2. **Everything is deterministic.** Results come from a declared simulation or a seeded
   generator; no `random()` at render time. A seed *chosen* because it shows a case is
   labeled on screen as chosen. Counts and frequencies state their N.
3. **Time manipulation is declared.** Slow motion, freezes, rewinds carry an on-screen tag
   (`x1/4`, `PAUSE`, `REAL SPEED`).
4. **Illustrative values are labeled illustrative.** Never present demo numbers as
   measurements of a real product. Facts on screen need a source in the brief.
5. **Own or licensed assets only.** Procedural art, own synthesis, system fonts rasterized
   into the frame. No gameplay capture, logos or characters of third parties.
6. **Never overwrite a render.** Renders are versioned (`name-v1.mp4`); a fix is `-v2`; the
   script refuses to write over an existing file.
7. **No glyph tofu.** Every on-screen string is checked against the fonts before rendering.
8. **Captions are ≤ 2 lines**, whole phrases, never covered by platform UI.
9. **QA is done on the delivered file**, not on the pre-render compositor: decode the whole
   file, measure loudness, pull frames out of the MP4/GIF and look at them.
10. **Never claim what was not verified.** The agent cannot hear: say "mix validated by
    measurement", not "sounds good". Distinguish inspected frames from uninspected ones.

## The pipeline (each phase ends in a gate)

0. **Brief & format.** One sentence: what the viewer must understand or feel. Pick the format
   from the table; for a long video, list the blocks. Ask only what cannot be defaulted
   (audience, language, voice yes/no, deadline). *Gate: one-sentence promise + format.*
1. **Dossier.** The one idea, the facts with sources, which values are illustrative, what
   visual proves each claim. *Gate: every on-screen claim has a source or an "illustrative" tag.*
2. **Script (if narrated).** Modular blocks; each block understandable alone (no "as we saw
   before"); numbering and transitions live on screen, not in the voice. Budget words from a
   measured speech rate (≈ 13 characters/second for a calm explainer voice; measure yours).
   Hook in the first 3 s; the hook's promise is paid inside the piece.
3. **Voice & timing.** One TTS call per block with **character-level alignment**, or an
   **estimated alignment** for an animatic before paying for voice. Approved voice is reused,
   never regenerated. Inserted pauses shift word times (scene anchors follow automatically).
4. **Direction document.** Diagnosis of the previous version (if any), *the idea of
   direction* (e.g. "one instant, seen four ways"), principles, and a **storyboard table
   anchored to words**: `time | narration | image`. *Gate: every beat has a picture that
   proves it, and one protagonist per shot.*
5. **Aesthetic kit.** A world, a hero, a palette as tokens, a typography pair, a signature
   transition, a music identity. Series work: keep the identity layer (header, captions,
   labels, A/B panels, end card) and vary the world each episode.
   See [references/craft-bar.md](references/craft-bar.md) § Aesthetic kit.
6. **Simulation & event log.** Model the mechanic/data deterministically (fixed step, e.g.
   1/120 s). Every meaningful moment becomes an event `(t, kind, info)` — the single source
   for particles, SFX, badges and the narration cross-check. Print the event log with the
   word being spoken at each event and **reconcile it with the script before rendering**.
7. **Choreography.** Scenes are pure functions of time; anchors are word times (`W(i)` =
   start of word *i*); layouts are keyframed slots that ease between each other; focus dims
   the non-protagonist; callouts rise, underline and fade.
8. **Stills loop.** Render stills at storyboard beats and at uniform samples, build a contact
   sheet, **open the PNGs and look**. Score against the craft bar; fix; repeat until clean.
   This loop is where AAA happens — budget most of the time here.
9. **Audio.** Procedural music per mood/section, SFX placed from the event log and
   loudness-matched, voice at −16 LUFS, music bed at −23.5 LUFS ducked 9 dB under speech,
   master −16 LUFS, true-peak limiter −1.6 dBTP. See [references/audio.md](references/audio.md).
10. **Render, validate, deliver.** Parallel frame render piped to the encoder; full decode
    with 0 errors; loudness and true peak re-measured on the file; frames extracted from the
    file into a contact sheet and inspected; SRT, timeline, chapters, measurements JSON.
    See [references/formats-and-delivery.md](references/formats-and-delivery.md).

## The AAA bar (summary — the full checklist is in references/craft-bar.md)

- **Animation principles applied, not decorative:** anticipation before every big move,
  squash & stretch on impacts, follow-through/overshoot (`back_out`, damped springs), arcs
  for flights, slow-in/slow-out everywhere (never linear UI motion), secondary motion
  (scarf, dust, cloth) driven by the primary's velocity.
- **Depth:** at least three parallax layers (background ×0.5, objects ×1, foreground
  particles ×1.6), soft contact shadows, light pools/glow, vignette, a slow camera drift.
- **Events feel physical:** every impact gets a puff/spark, a micro-squash, a SFX, and
  where it matters a badge — all from the same event.
- **Staging & hierarchy:** one protagonist per shot; others dim/pause *visibly* (never
  vanish, or the comparison stops being honest); big type, few words (2–4 word callouts).
- **Rhythm:** cuts and reveals land on words; layout transitions 0.4–0.5 s; nothing static
  for more than ~2 s; a signature transition between blocks.
- **Craft hygiene:** supersampling ×2 then box-downscale (clean edges), consistent baseline
  for captions, safe areas for platform UI, no text under 20 px at 1080 wide.

## Code shape (and the starter engine in scripts/)

The proven shape is **engine + kit + scenes + blocks + video + audio + validate**:

| Module | Owns |
|---|---|
| engine (`scripts/motion_core.py`) | canvas with supersampling, easing/time functions, PCHIP time remap, light & shadow masks, particles, slot layouts, captions/SRT, glyph check, parallel render → encoder, stills, contact sheet, GIF export |
| audio engine (`scripts/audio_core.py`) | BS.1770 loudness, true peak, look-ahead limiter, envelopes, synth voices, SFX recipes, ducking, mix & master |
| kit (per piece) | palette tokens, world/background, hero drawing, props, signature transition, header/caption styling |
| scenes (per piece) | animated pieces with their own event lists |
| blocks (per piece) | one class per narrated block: panels, layout keys, focus windows, callouts, marks |
| video (per piece) | segment timeline (blocks, cards, title, end card), compose(t), audio build, render, QA |
| validate | decode check, loudness, frames from the file, contact sheet, `validacion.json` |

`scripts/example_gold.py` is the **gold exemplar**: a short piece that exercises every rule
above (anticipation, squash/stretch, arcs, parallax, glow, particles from events, declared
slow motion, karaoke captions from an estimated alignment, signature wipe, procedural music
+ event SFX, −16 LUFS mix) and renders vertical, horizontal and GIF from one scene model.
Start every new piece by copying its shape, then replace the kit and the scenes.
Architecture details: [references/architecture.md](references/architecture.md).

Requirements: Python 3.10+, NumPy, Pillow, SciPy, FFmpeg on PATH; fontTools optional (glyph
check). Fonts resolve from the OS (Windows, macOS, Linux) with a fallback chain.

```bash
python <skill-dir>/scripts/example_gold.py --out ./motion-out --stills
python <skill-dir>/scripts/example_gold.py --out ./motion-out
python <skill-dir>/scripts/validate.py ./motion-out/vertical/gold-vertical-v1.mp4
```

Copy the scripts into the host project (e.g. `motion/`) before modifying them; the skill's
copy is the reference, not a place to keep a project's pieces.

## Scaling to 10 minutes

- **Block engine:** the long video is `title + [card + block]*N + end card`; each block owns
  its voice, words, panels and events with block-local time; the video maps global → local.
- **Render budget:** frames are independent → multiprocessing. Memory, not CPU, is the limit:
  keep per-size caches tiny (`lru_cache(maxsize=4)` for anything sized by panel), use 4–6
  workers for 1080p, render long videos alone. Measure wall time and record it.
- **Parallel authoring:** blocks are independent scopes. For long pieces, the orchestrator
  writes the kit and ONE gold block, then may dispatch one agent per remaining block with the
  gold block as the mold; the orchestrator reviews every block's stills itself before
  integration (see *Composes with*).
- **Chapters** come from block cards; the end card offers the next action (related video,
  comment prompt) without a spoken CTA unless the script approved one.

## Delivery package (per piece)

`name-vN.mp4` (or `.gif`) · `subtitulos.srt`/`captions.srt` · `timeline.json` (segments,
chapters, cues) · `mediciones.json` (duration, frames, resolution, fps, LUFS, true peak,
stems, render time, workers, SHA-256, encoder command) · `validacion.json` · `contacto.png`
(pre-render stills) · `qa-mp4-contacto.png` (frames from the file) · `qa/` · the code that
rendered it · a README with what changed and why, reproducible commands, dependencies and
licenses, limitations (what was not inspected), and the next step.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Two static panels and a paragraph of labels | One protagonist per shot, 2–4 word callouts, the effect before the name |
| Linear tweens, instant appear/disappear | Easing on everything; enter with overshoot, exit with fade + slight scale |
| Randomness at render time | Seeded generator or simulation; event log reconciled with the script |
| Cropping the long video into a short | Separate layout per canvas from the same scene model |
| "Looks fine" from the compositor only | Decode the file, extract frames, open and inspect them |
| Re-rendering over an approved file | New version suffix; keep the approved one byte-identical |
| Regenerating approved narration to tweak timing | Insert pauses / shift anchors; voice is reused |
| Giant caches keyed by panel size | `maxsize=4`; sizes change during transitions and exhaust memory |
| Unicode arrows/symbols the font lacks | Glyph check before render; draw the symbol as geometry |
| Music louder than meaning | Bed −23.5 LUFS, 9 dB duck under speech, SFX matched per kind |

## Composes with

- **patron-oro** — the gold exemplar *is* the mold: polish ONE piece (or ONE block) to the
  AAA bar, guard it (identical-frame regression on the engine), then replicate horizontally
  as data: new kit + new scenes, same engine.
- **agent-in-the-loop** — for long videos, one agent per block on the gold block's shape; the
  orchestrator verifies each block's stills and event log with its own eyes before accepting it.
- **engram-memory** — save each piece's aesthetic, measured speech rate, render budget and
  gotchas so the next piece starts from evidence and never repeats last week's look.
