---
name: Dispatch & Status Signals
description: "The minimal coordination protocol between an orchestrating thread and role agents: single-level dispatch, disk-state artifact contracts (artifacts/{type}-{id}.md), exactly one STATUS signal per agent response (COMPLETE | BLOCKED | NEEDS-REVIEW), and batched questions."
---

# Dispatch & Status Signals

The kit's agents coordinate through three primitives: **dispatch rules**, **artifacts on
disk**, and **status signals**. Nothing else is shared state.

## Dispatch rules

1. **Only the orchestrating thread dispatches agents.** Agents never spawn other agents —
   a needed capability outside scope is signaled, not self-served.
2. **One stage, one agent, one artifact set.** A dispatch names the task, the input
   artifacts (paths), and the expected output artifacts.
3. **Route by task type, not by effort.** Whether work goes to an agent is decided by the
   host's orchestration rules (see [templates/CLAUDE.skeleton.md](../templates/CLAUDE.skeleton.md)),
   never by "it's quicker inline" (`rationalization-prevention.md` row 1).

## Disk-state communication (artifact contracts)

Pipeline stages communicate through files, not conversation memory — files survive context
loss, are diffable, and are independently verifiable.

- Artifacts live in **`artifacts/`** in the host repo (gitignore or commit — host's choice,
  recorded in its stack contract or CLAUDE.md).
- Naming: **`artifacts/{type}-{id}.md`** where `{type}` is the artifact kind
  (`requirements`, `design`, `test-plan`, `implementation`, `docs`, …) and `{id}` is a
  short stable slug for the feature/task (e.g., `user-invites`). One `{id}` threads all
  stages of one piece of work.
- Every artifact starts with a header block: feature, pipeline id, author agent, date,
  input artifact paths. Downstream agents treat upstream artifacts as **read-only inputs**.
- An agent that finds an upstream artifact wrong does not edit it — it signals
  `NEEDS-REVIEW` naming the defect (the upstream owner fixes its own artifact).

## Status signals

Every agent response in a pipeline ends with **exactly one**:

| Signal | Meaning | Orchestrator's move |
|---|---|---|
| `STATUS: COMPLETE` | All quality-gate items hold; evidence produced | Verify (Layer 2), then advance |
| `STATUS: BLOCKED` | Missing input only a human/upstream can provide (named explicitly) | Obtain the input; re-dispatch |
| `STATUS: NEEDS-REVIEW` | Work paused on a found defect, gap, or out-of-scope decision (named explicitly) | Decide: fix upstream, adjust scope, or accept-with-rationale |

Rules:

- `COMPLETE` with unmet gate items is a protocol violation, not an approximation.
- `BLOCKED`/`NEEDS-REVIEW` must name the blocker precisely enough that the orchestrator
  can act without re-deriving the analysis.
- No signal = the response is not a pipeline response (informal Q&A is fine outside pipelines).

## Batched questions

An agent needing human input gathers ALL its questions into a single message (one
round-trip), marks which are blocking vs. optional, and signals `BLOCKED` once — never a
drip of one-question turns.

## See Also

- `orchestrator-verification-protocol.md` — what "verify then advance" means
- [pipelines/sdlc-feature.md](../pipelines/sdlc-feature.md) — these signals wired into stages
- `scope-enforcement-protocol.md` — the Out-of-Scope Response is a specialized NEEDS-REVIEW
