---
name: patron-oro
description: "The 'patrón oro' (gold pattern) methodology — polish 1 → replicate N — for building repeatable content, entities, or components in ANY project: build ONE technically complete exemplar per system, guard it with a regression test, then replicate it horizontally as data without reinventing. Use when designing new systems, producing serial content, building catalogs of entities/endpoints/components, or auditing placeholders — triggers: /patron-oro, 'patrón oro', 'pulir uno y replicar', 'gold pattern', 'replicate this exemplar'."
---

# Patrón oro — polish 1 → replicate N

> Build the base system working with ONE complete exemplar. Once it works, replicate
> the exemplar reusing the concept, without reinventing. When a chain is complete,
> bundle it and replicate the whole chain. That scales vertically AND horizontally,
> and adding content becomes "easy".

## The 3 requirements per system (ALWAYS audit before replicating)

1. **Generic engine** — the code assumes no concrete exemplar (nothing hardcoded to the
   first case). Adding a replica = ZERO code.
2. **Complete schema** — the model/template has ALL the fields the final content will
   need (icon, description, rarity, audio, metadata…). A missing field means every
   replica is born lame and you migrate N times.
3. **One gold exemplar** — ONE genuinely polished exemplar that serves as the MOLD.
   Without it nobody knows the required bar, and the catalog fills with greybox.

## What "technically complete" means

Every aspect of the exemplar at FINAL quality, not merely functional: real name and copy
(with the project's tone/lore), art or its hook wired, validated numbers, behavior
connected end to end, feedback (sound/states) where it applies, and tests. If an aspect
is deliberately deferred, it is declared as debt with an ID in the checklist — never
silently.

## The process

1. Base system working with ONE exemplar (deliberate greybox allowed).
2. Complete the SCHEMA before replicating (requirement 2).
3. Polish the exemplar to gold level, aspect by aspect.
4. **Guard the mold with a regression test** that fails if the exemplar (or new
   content) drops below the bar — the pattern's sentinel.
5. Replicate VERTICALLY first (the chain: exemplar → next link), bundle, and only then
   replicate HORIZONTALLY (parallel chains).
6. All final copy/values live EMBEDDED in the authoring source (generator, seed,
   template, tool) — if a generator overwrites manual edits, either embed the final
   content in it or retire the generator. Never leave quality only in the generated
   artifact.

## Translation beyond games

- **Entities/CRUD**: one gold model (validations, migration, serialization,
  permissions, tests, docs) → other entities copy it as schema+data.
- **API endpoints**: one gold endpoint (auth, validation, typed errors, telemetry,
  tests, OpenAPI spec) → the rest replicate the contract.
- **UI components**: one gold component (all states, theming, a11y, stories/tests) →
  the library grows by replication, not invention.
- **Documentation**: one gold page → template for the rest.

## Project maintenance rules

- **ONE living checklist**: pending work lives in a single document with IDs; resolved
  items are STRUCK and leave (history goes to persistent memory or lessons/, it does
  not pile up in the doc). Plans are consolidated as they execute.
- **New content is born AT the mold's level**, never below — the regression test from
  step 4 watches this.
- **Freeze contracts before serial production** (scale, schema, naming): changing them
  later forces reworking N pieces.

## Composes with

- **agent-in-the-loop** — pilot ONE scope to gold, then batch-replicate the shape with
  parallel agents; the reviewer enforces the mold's bar on every replica.
- **engram-memory** — resolved checklist items leave the living document; their history
  is saved to persistent memory.
