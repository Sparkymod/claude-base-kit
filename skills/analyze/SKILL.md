---
name: analyze
description: "Surgically extract what an existing codebase contains into an evidence-backed Analyze.md at the project root: stack, structure, entry points, domain model, integrations, patterns, tests, and observed gaps — every claim cites a file (and line where it matters). Use on any already-built project, typically right after /genesis on a brownfield repo — triggers: /analyze, 'analiza este proyecto', 'genera el Analyze.md', 'what does this codebase contain', 'map this codebase'."
---

# analyze — extract an existing codebase into Analyze.md

Run from the root of the host project. The outcome: a single `Analyze.md` at the project
root that tells a human (or an agent) what this codebase IS — extracted from evidence,
never from ecosystem assumptions. Read-only over source: the ONLY file this skill writes
is `Analyze.md`.

## Guard

- If the repo contains no source code (only docs, configs, or an empty scaffold), stop
  and report exactly what WAS found instead of producing a hollow document.
- If `Analyze.md` already exists, do NOT silently overwrite: re-run the analysis, then
  present a short summary of what changed (new/removed/renamed areas) and rewrite the
  file only after stating that summary.

## Method — the evidence ladder

Fill every section using ONLY what the repo evidences, in this priority order:

1. **Manifests and lockfiles** — e.g. `package.json`, `*.sln`/`*.csproj`, `pyproject.toml`,
   `go.mod`, `Cargo.toml`, `project.godot`, `composer.json`, `Gemfile`, `Makefile`/`justfile`
   (detection signals only — the analysis itself stays in the host's vocabulary).
2. **CI workflows** — the commands CI actually runs are the truest build/test/run answers.
3. **The code itself** — folder layout, entry points, dependency direction, naming.
4. **Existing docs** — README, CONTRIBUTING, ADRs: record them, but where docs and code
   disagree, the code wins and the disagreement is reported as drift.

Rules:

- **Never invent.** No evidence for a section → write `(not evidenced in repo)` and move on.
- Every non-obvious claim carries its evidence inline: `path/to/file` or `path/to/file:line`.
- Distinguish **observed** (what the code does) from **declared** (what docs/configs say).
- If `.claude/rules/stack-contract.md` exists and is filled, reuse its confirmed answers
  for the Stack section instead of re-deriving them.

## Analysis passes

Execute all passes; a pass with nothing to report states "No findings" — never omit it.

1. **Inventory** — top-level layout, module/package boundaries, generated-vs-authored
   areas, rough size per area (file counts, not guesses).
2. **Entry points** — every way execution enters the system: executables/main routines,
   exposed endpoints or routes, message/event consumers, scheduled or background jobs,
   CLI commands, UI screens/scenes. This list feeds `/usecases` — be exhaustive.
3. **Domain and data** — core domain concepts (the nouns the code is organized around),
   persistence surfaces (schemas, migrations, data files), and where state lives.
4. **External integrations** — outbound dependencies on other systems: APIs called,
   queues, third-party services, environment variables/secrets consumed.
5. **Architecture and patterns** — layering and dependency direction as observed,
   recurring structural patterns (3+ same-shape implementations), and the host's error
   and validation idioms.
6. **Tests and verification** — test areas, taxonomy (unit/integration/e2e as the host
   names them), how they run, and visible coverage gaps (source areas with no tests).
7. **Health observations** — drift between declared and observed architecture, dead or
   unreachable areas, TODO/FIXME clusters. Findings only, with evidence — no fixes, no
   prioritization.

## Output — `Analyze.md`

```markdown
# Analyze — {project name}

> Extracted from repo evidence on {date}. Every claim cites its source; sections without
> evidence say so. Regenerate with /analyze.

## Snapshot
{2–4 sentences: what this system is, in the host's own vocabulary} | key counts (modules, entry points, tests)

## Stack (detected)
| Aspect | Answer | Evidence |
{language/runtime, frameworks, build/test/run commands, package manager — from the ladder}

## Structure
{annotated top-level tree: area → responsibility → evidence}

## Entry Points
| # | Kind | Name / Route | Handler location | Notes |

## Domain & Data
{core concepts with defining files; persistence surfaces; state ownership}

## External Integrations
| System | Direction | Where wired | Config/secret consumed |

## Architecture & Patterns
{observed layering + dependency direction; recurring patterns with instance lists;
error/validation idioms}

## Tests & Verification
{test areas, how to run them, gaps table: source area → missing coverage}

## Health Observations
| # | Observation | Kind (drift / dead code / gap) | Evidence |

## Not Evidenced
{explicit list of sections/questions the repo gave no answer to}
```

## Report and confirm (single batched message)

End with ONE message: where `Analyze.md` was written, the Snapshot section verbatim, the
count of findings per pass, and the `Not Evidenced` list as batched questions the human
may optionally answer to enrich the document. Suggest `/usecases` as the natural next
step — it consumes the Entry Points inventory.
