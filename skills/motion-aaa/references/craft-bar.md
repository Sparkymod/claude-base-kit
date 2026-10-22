# Craft bar — what "AAA motion" means, checkable

Use this file twice: when designing the aesthetic kit and direction, and as the scoring rubric
during the stills loop. A frame or a beat that fails a line is reworked, not shipped.

## 1. Direction

- **One idea of direction per piece**, stated in a sentence before any code. Examples that
  worked: "one instant, looked at four times" (the same 80 ms shown as hook, comparison,
  inside view, abstract rule, real speed); "the rules are on the table" (every random result
  physically drawn from a box/bag/spinner the viewer can see).
- **The effect before the name.** Show the failure and the success, then name the technique.
- **Honest comparisons.** A/B panels receive the *same* input and conditions; only the rule
  under comparison differs. While one side is explained, the other dims and shows a visible
  pause icon — it never disappears.
- **One protagonist per shot.** Focus = brighter border, full saturation; others dim ~60 %.
- **Hook in 0–3 s** with a visible result, not a title card. The promise is paid in the piece.
- **Few words on screen.** Callouts 2–4 words (max ~7), data in a numeric face. No
  paragraphs. Labels must be readable on a phone (≥ 20 px at 1080 wide; captions 52–58 px).

## 2. Animation principles (each one has a concrete implementation)

| Principle | Implementation |
|---|---|
| Anticipation | 0.10–0.20 s crouch/squash (scale y 0.8, x 1.15) before jumps, launches, swings |
| Squash & stretch | stretch along velocity in flight; landing curve 1 → 0.72 → 1.08 → 1 over ~0.22 s; preserve area (x ≈ 1/√y) |
| Follow-through & overlap | `back_out` overshoot on entries; damped spring for settling; secondary parts lag the body (scarf, antenna, cloth) |
| Arcs | flights are parabolic (`z = 4h·k(1−k)`), never straight lines between two points |
| Slow-in/slow-out | `ease_in_out` for travel, `ease_out` for entries, never linear for UI or camera |
| Secondary action | dust in light beams, idle bob, breathing glow, drifting particles — always subordinate |
| Timing | hold readable states ≥ 0.6 s; transitions 0.4–0.5 s; nothing static > ~2 s |
| Exaggeration | in scale and timing only — never in the mechanic's outcome |
| Staging | silhouette readable at thumbnail size; protagonist against its highest-contrast background |
| Solid drawing | consistent light direction, contact shadows, bevels/rims on props |
| Appeal | a hero with a face or a gesture (eyes, scarf, bounce) people can follow |

## 3. Depth, light and texture

- **Parallax:** ≥ 3 layers driven by one slow, deterministic camera drift
  (`sum of slow sines`): background ×0.5, props ×1, foreground particles ×1.6.
- **Light:** a key light pool (radial mask, warm or cool by world), glow halos on emissive
  things (pre-computed radial masks, cached), vignette, ambient occlusion at wall/prop bases.
- **Shadows:** soft elliptical contact shadows that shrink and fade with height.
- **Texture:** procedural grain/wood/tiles/paper from layered sines + seeded noise — subtle,
  never louder than the content.
- **Supersampling:** draw at ×2, downscale with a box filter. Clean edges are non-negotiable.

## 4. Events → feedback (the "juice" contract)

Every simulation event can drive four outputs from ONE record `(t, kind, info)`:
particles (puff, sparks, ring wave), a micro-motion (squash, shake ≤ 0.05 units), a sound
(loudness-matched per kind), and optionally an on-screen mark (✓/✗ badge drawn as geometry,
state pill). If two visible panels emit the same event within 80 ms, it sounds once.

## 5. Transitions and structure

- **A signature transition per piece** that belongs to its world (fan of cards, flashlight
  sweep, paper wipe, iris, shutter). 0.35–0.45 s in, same out.
- **Block card** (long videos): big number, block name, one-line motto, progress dots.
- **Layout transitions:** slots interpolate with `ease_in_out` over ~0.5 s; entering panels
  scale from 0.92 with alpha; leaving panels shrink 6 % while fading.
- **End card:** the question the piece raised + next action. Shorts: dark overlay + question
  + pointer to the long video; long: comment prompt + grid of the blocks.

## 6. Typography and captions

- Two faces: a heavy display face for callouts/captions, a condensed numeric face for data;
  a mono face only for "machine" readouts.
- Karaoke captions: spoken words full color, active word in the accent inside a soft
  capsule, upcoming words muted; enter with 12–14 px rise over 0.16 s; common baseline.
- Captions in the vertical middle-lower band for shorts (out of platform UI), lower band for
  long videos; split recursively until ≤ 2 lines on every canvas; never break after a weak
  word (articles, prepositions, conjunctions).

## 7. Aesthetic kit (series identity vs. episode variation)

Identity layer (constant across a series): header lockup, caption system, label pills, A/B
panel frame with letter badges, end-card structure, loudness targets.
Variation layer (new every episode): world (desk at night, top-down office, desert, arena…),
palette tokens, hero design, props, texture, signature transition, music instrument family,
tempo and modes. Write the kit's docstring as a one-paragraph art direction and list the
previous worlds it must differ from.

Palette tokens: `BG0/BG1` (two darks), `INK`, `CREAM/MUTE/DIM` (text tiers), 3 category
colors that also differ by **shape** (color-blind safe: circle / diamond / triangle),
`GOOD/BAD/WARN`, one accent for the active caption word.

## 8. Stills-loop rubric (score every contact sheet)

1. Is the protagonist obvious in each frame at thumbnail size?
2. Does each frame match what is being said at that time (check the event log)?
3. Any text overflow, clipping, overlap, tofu, or > 2 caption lines?
4. Any frame where nothing moves? Any linear or popping motion between adjacent samples?
5. Are slow-motion/pauses/chosen seeds labeled where they happen?
6. Depth present (parallax, shadows, light) without hurting legibility?
7. Transition frames: no half-drawn garbage, no flash of the wrong block?
8. Last frame / end card complete and readable?
Record what was inspected and what was not.
