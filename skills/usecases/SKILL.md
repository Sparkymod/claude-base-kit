---
name: usecases
description: "Reverse-engineer the use cases an existing codebase actually implements into UseCases.md at the project root: one UC per actor-goal, with main scenario, extensions, data structures, and business rules extracted from code evidence — plus a coverage table proving no entry point was dropped. Use on any already-built project, ideally after /analyze — triggers: /usecases, 'extrae los casos de uso', 'genera el UseCases.md', 'what use cases does this system implement'."
---

# usecases — extract implemented use cases into UseCases.md

Run from the root of the host project. The outcome: a single `UseCases.md` at the project
root documenting the use cases the system ALREADY implements — extracted from code
behavior, never from wishful requirements. Read-only over source: the ONLY file this
skill writes is `UseCases.md`.

## Guard

- If the repo has no observable behavior entry points (pure library with no exposed
  surface, or no source code at all), stop and report what was found instead.
- If `UseCases.md` already exists, do NOT silently overwrite: re-extract, present a short
  changed-UCs summary (new / removed / behavior-changed), then rewrite.

## Step 1 — Entry point inventory

Use cases are anchored to entry points, so the inventory must be exhaustive:

- If `Analyze.md` exists at the root, start from its **Entry Points** section and verify
  each entry still exists in code (drop stale ones, note them).
- Otherwise run a discovery pass over the code: exposed endpoints/routes, UI
  screens/actions, CLI commands, message/event consumers, scheduled or background jobs,
  public API surface of the host's outermost layer. Suggest running `/analyze` after,
  but do not block on it.

## Step 2 — Group entry points into use cases

An entry point is not a use case; a use case is **one actor pursuing one goal**:

- Infer the **actor** from the entry point's authentication/authorization evidence, its
  UI placement, or its caller (a scheduler or another system is also an actor).
- Group entry points serving the same actor-goal (e.g. the create/read/update/delete
  surface of one concept → one "Manage {Concept}" UC; a multi-step flow → one UC with
  steps).
- Assign stable IDs `UC-001…UC-NNN` ordered by domain area, not discovery order.

## Step 3 — Fill each UC from code evidence

For every UC, extraction rules — never invent, always cite:

| UC section | Extracted from |
|---|---|
| Preconditions | auth guards, required state checked before the flow runs |
| Postconditions | what is persisted/emitted/returned on success |
| Main Scenario | the success path through the handler(s), ≤10 steps, actor-visible actions only |
| Extensions | error paths, validation rejections, branches, compensations found in code |
| Data Structures | the shapes validated/accepted at the boundary and what defines them |
| Business Rules | invariants enforced in code: validations, limits, state-transition guards |
| Pending Issues | what code CANNOT reveal: intent, priority, whether behavior is a bug or a rule — mark `TBD (human)` |

Anything not evidenced in code is `TBD` — a use case document with honest TBDs beats a
plausible fiction.

## Output — `UseCases.md`

```markdown
# Use Cases — {project name}

> Reverse-engineered from code evidence on {date}. `TBD (human)` marks what code cannot
> reveal. Regenerate with /usecases.

## Index

| UC ID | Title | Primary Actor | Entry Points | Evidence |
|---|---|---|---|---|

## UC-{NNN}: {Title}

| Item | Content |
|---|---|
| **Primary Actor** | {actor} (evidence: {how inferred}) |
| **Scope / Area** | {domain area} |
| **Entry Points** | {list, each with handler location} |
| **Preconditions** | {…} |
| **Postconditions** | {…} |

### Main Scenario
| Step | Actor | Action | Evidence |
|---|---|---|---|

### Extensions / Alternatives
| Step | Condition | Behavior | Evidence |
|---|---|---|---|

### Data Structures
| Concept | Defined by | Defining location |
|---|---|---|

### Business Rules
| # | Rule | Enforced at |
|---|---|---|

### Pending Issues
| # | Question for a human |
|---|---|

{repeat per UC}

## Coverage — no entry point dropped

| Entry point | Covered by | Status |
|---|---|---|
{every inventoried entry point → its UC, or ⚠️ UNCOVERED with a one-line reason}
```

The Coverage table is the quality gate: extraction is not COMPLETE while an entry point
is uncovered and unexplained.

## Report and confirm (single batched message)

End with ONE message: where `UseCases.md` was written, the Index table verbatim, the
coverage summary (N entry points → N UCs, uncovered count), and ALL `TBD (human)` items
batched as questions — never a drip of one-question turns.
