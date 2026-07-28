---
name: tareas-delegadas
description: Turns any project's backlog or "natural next steps" into bounded scopes and executes them with specialist agents in parallel (isolated worktrees + adversarial review + integration + green suite). Use this skill WHENEVER the user asks to "delegate tasks", "create scopes", "split the work among agents", "autonomous agent work", "batch of scopes", "multi-agent mode", or hands over a backlog/plan/pending list asking to plan or execute it in parallel. Also applies when they ask to "run the batch", "review the scopes" or "report batch status" — triggers: /tareas-delegadas, 'delegar tareas', 'crear scopes', 'divide el trabajo entre agentes', 'batch de scopes', 'ejecuta el batch'.
---

# Tareas Delegadas — scope-based multi-agent planning and execution

A project-agnostic methodology to split pending work into **bounded scopes**, assign each
scope to a **specialist agent**, and execute them in **parallel batches** with adversarial
review and verified integration. Works for any stack (games, web, APIs, data, infra, technical docs).

**Golden rule:** wherever a task brushes against a pending human decision, the agent implements
the **documented sensible default** and leaves a `FLAG:` for asynchronous ratification — it
**never** blocks waiting for the human.

This skill is the **planning + batch-execution machinery**. The reviewing discipline that closes
each batch (why an orchestrator must verify instead of trust) lives in **agent-in-the-loop** —
use both together: this one produces the scopes and runs the batch, that one governs the loop.

## The full pipeline

```
0. Reconnaissance  →  1. Filtering  →  2. Scopes  →  3. Prioritization  →
4. Assignment by specialty  →  5. Batch execution  →  6. Report + user decision
```

The user may ask for just one part ("draft the scope plan") or the full cycle ("plan and
execute"). Detect which phase they are in and enter there. If a previous scopes document
already exists, read it first and continue from its execution state instead of re-planning from scratch.

---

## Phase 0 — Reconnaissance: build the anchor map

Before proposing anything, understand the terrain — and write the terrain down. The output of
this phase is an **anchor map** that every later scope prompt quotes, so no worker burns its
context rediscovering the same things:

1. **Sources of truth**: master plans, the backlog/pending-items doc/issues, design docs,
   lessons learned, and the repo state (branches, last merge).
2. **How the project is verified**: test suite (framework and exact command), E2E smokes,
   linters, builds. **Record the baseline**, including pre-existing failures — see below.
3. **Human roles** (designer, product owner, client, "the user") — their pending decisions
   define the boundary of what is autonomous.
4. **Natural areas** of the project (engine, UI, netcode, ops, data, editor…). These become
   the agents' specialties.
5. **Real anchors per area**: the exact `path/file.ext:line` where each system is created,
   consumed, or extended; which systems are empty; which existing subsystem is the
   **architectural mold** to mirror (the closest well-built analogue in this repo), and the
   **reference test** that shows how that mold is tested.

The anchor map is what makes a scope prompt startable without questions. A scope that says
"add environment presets" costs the worker an hour of archaeology; one that says "the only
place the environment is created today is `world.ext:49-65`; mirror the audio catalog at
`audio_library.ext:25-41`; the reference test is `tests/audio/audio_system_test.ext`" starts
in minutes and lands in the intended shape.

**Baseline discipline.** Write down the exact test count AND any known-flaky or pre-existing
failures (`589 tests / 2 failing = known intermittent, documented`). Two rules follow:
- Green means **no new red versus the baseline**, not necessarily N/N — otherwise workers
  either "fix" unrelated flakiness or hide real breakage behind it.
- **Each worktree records its own baseline from its own HEAD** before touching anything.
  A batch inherits whatever HEAD carried; only per-worktree baselines prove causation.

If there is no test suite nor any way to verify, say so explicitly and propose creating a
minimal smoke as scope #1 — without verification there is no reliable autonomous execution.

## Phase 1 — Filtering (what's IN and what's NOT)

**IN** — tasks an agent can complete autonomously:
- Pure code (engine/business logic, services, tooling, already-designed UI systems).
- Declared bugs and technical debt.
- Closing out already-designed systems where only wiring/implementation is missing.
- Tests, migrations, observability, hardening that needs no external user infra.

**NOT IN** (document it in the "Excluded" section with the reason):
- **Assets/creative**: art, audio, final copy, branding, new visual design.
- **Content**: naming/lore, real catalogs, production data requiring human judgment.
- **Pending human decisions**: any unratified A/B/C, balancing, product policies.
- **User infra**: production deploys, real credentials/secrets, DNS, SMTP,
  off-site backups, payments — anything requiring the user's accounts or access.

The "Excluded" section is mandatory in the scopes document: the boundary must be written
down, not implicit.

**The boundary is the user's to move.** When they explicitly ask for something the document
had excluded, it enters — but you record *why it moved* and *what replaces the exclusion*.
The usual shape: the **engine plus a procedural/greybox exemplar enters**, the artist's final
assets stay out, under a **1:1 replacement contract by id** (dropping the real asset at the
declared id replaces the placeholder with zero code changes). That keeps the exclusion honest
instead of silently deleting it.

## Phase 2 — Scope definition

Each scope is written in this **exact** format (see the full template in
`references/templates.md`):

```
#### `XX-N` · Short title  [backlog origin]
- **Goal:** the why in 1-2 lines (what it unblocks or which bug it fixes).
- **Scope:** REAL files/symbols/paths from the repo (with lines where relevant), what gets touched and what doesn't.
- **Done:** verifiable, binary criterion (concrete test/smoke that must pass).
- **Dep:** dependencies on other scopes, or "none". Mark «Autonomous» / «Autonomous with default».
- **Note:** flags for the human, chosen defaults, what is explicitly out of scope.
```

Rules of a good scope:
- **One scope = one unit deliverable in 1 agent session** (if it's bigger, split it).
- IDs with an area prefix (`ED-`, `MOT-`, `NET-`, `OPS-`, `UI-`, `SOC-`… adapt to the project).
- The scope cites real paths and symbols from the anchor map — an agent with no context must
  be able to start without asking. Name the **mold to mirror** and the **reference test**.
- The "done" always includes automated verification (a new test or an existing smoke).
- Scopes independent of each other whenever possible → maximizes parallelization.
- **State the hard invariants the scope must not violate**, especially when it adds a layer
  next to a deterministic or authoritative core (e.g. "this layer is 100% presentational:
  fire-and-forget, its own randomness source, never touches the core's state, queue, or RNG").
  An invariant that only lives in a design doc will be violated by a worker who never read it.
- **Engine scopes ship one gold exemplar**, not just the mechanism: a generic engine plus ONE
  genuinely polished instance plus a tolerant fallback for missing data. This is `patron-oro`
  applied inside a scope, and it is what makes the following scopes pure data.

**Defensive seams for parallel scopes.** Two scopes in the same batch will sometimes need each
other (one adds the setting, another consumes it). Do not serialize them into different batches
for that — declare a **seam that tolerates absence in both directions**: the consumer reads the
producer's contribution through an optional/defensive lookup and behaves sensibly when it is
missing. Write the seam in **both** scopes' notes. Then either merge order works, and the
integration pass upgrades the seam if it wants to. Scopes touching **neighboring fields of the
same schema** are the classic case: they parallelize fine, they just conflict textually — that
is the integrator's job, not a dependency.

## Phase 3 — Prioritization

Table ordered by **value/unblocking**:

| # | Scope | Area | Value | Risk | Parallel with |
|---|---|---|---|---|---|

Criteria: first whatever unblocks other things or fixes violations of documented invariants;
then security/debt; polish last. Note which scopes must go in later batches due to
dependencies (e.g. `ED-2` after `ED-1`).

## Phase 4 — Assignment by specialization

Group the scopes by area and assign **one specialist agent per area** (Engine Agent, UI Agent,
Ops Agent…). Each batch takes the top N mutually independent scopes (typically 3-5)
and assigns **one agent per scope**, specialized in its area.

**Common contract for all agents (always include it in their prompts):**
1. One scope = one commit (or few) with its smoke/test green; **do not touch files outside your scope**
   without saying so (worktrees/parallel-sessions rule).
2. Respect the project's coding standards (name the standards doc/skill if one exists).
3. Record YOUR baseline from your own HEAD first; then run the **full suite** + the relevant
   smoke before calling it done, and report the exact count (`N/N green`, or the delta against
   a baseline that already had known red). Lesson learned: every implementer runs the full
   suite, not just its own tests — that way conflicts surface before integration.
4. Record the result in the backlog (what's resolved LEAVES the pending list; lessons go to
   their doc) and in the project's memory system if one exists.
5. On brushing against a human decision: implement the **documented default** and leave a `FLAG:`
   in the commit/doc. Never block.

## Phase 5 — Batch execution

Per-batch pattern (the prompts for each role are in `references/agents.md`):

1. **Preparation:** create the batch branch `feat/scopes-batch-N` and an **isolated worktree per scope**.
   A dependent batch is cut from the **previous batch's branch**, not from the main branch —
   that is what lets batch N+1 build on N before either is merged.
2. **Implementation:** one implementer agent per scope, in its worktree, with its scope prompt +
   the common contract. Deliverable: commits on `scope/<id>` + full suite green + report.
3. **Adversarial review:** for each branch, a reviewer agent distinct from the implementer
   actively hunts for bugs, invariant violations, gaps in the "done", and side effects. It does
   not fix: it reports findings classified as blocker / medium / low.
4. **Integration:** an integrator agent merges the scope branches into `feat/scopes-batch-N`,
   applies the fixes for the blocker/medium findings, resolves conflicts, and runs the full
   suite + smokes. *Low* findings may be deferred (document them).
5. **Final verification:** full suite green with the exact count (e.g. `544/544` + secondary
   suites). If anything fails, it gets fixed during integration before reporting.
6. **Delivery:** the batch stays on its branch, **not merged into the main branch**. Merging/pushing
   is ALWAYS the user's explicit decision — report "Pending your decision: merge
   `feat/scopes-batch-N` → `main`".

**Hard rule — nobody commits from the main working tree.** Other sessions (human or agent) may
have uncommitted changes there. Every scope is cut from HEAD into its own worktree, and the
integration happens on the batch branch. This is what makes concurrent sessions survivable.

**Semantic conflicts are the integrator's real job.** Textual merges are the easy half. When two
scopes both shape one behavior, the integrator decides the *composition rule* and writes it down
as a named integration decision (e.g. "the user's intensity setting is a MULTIPLIER over the
per-map artistic value, and the user's on/off always wins"). Unwritten composition rules get
re-litigated in the next batch.

Followups discovered during the batch (derived bugs, process improvements, nice-to-haves) are
recorded as new candidate scopes for the next batch (e.g. `SOC-1b`), never smuggled into the
current batch.

### Harness mechanics (how to actually run the batch)

The pattern above is tool-agnostic; this is how it maps onto a modern agent harness. Adapt the
names to whatever the session offers, and fall back to serial execution when it offers nothing.

- **Dispatch the whole batch in ONE message**, with one agent call per scope. Independent agents
  launched in separate messages serialize; the wall-clock win of the batch comes from this.
- **Prefer the harness's native worktree isolation** (an isolation option on the agent call) over
  hand-rolled `git worktree add`. Hand-roll only when the harness has no such option, and then
  clean up the worktrees when the batch closes.
- **Give each role its own model and effort.** The orchestrator keeps the strongest judgment
  model; implementers get an implementation-capable tier; **reviewers get high effort** —
  refutation is the expensive cognition, not typing. Mechanical scopes (renames, mechanical
  migrations) can run cheaper deliberately, and you say so in the report.
- **Demand a structured report, not prose.** A subagent's final message IS its return value.
  Fix the fields (see `references/agents.md`) so a missing baseline or an unquoted test count is
  visible instead of buried in narrative.
- **Re-dispatch by resuming the SAME agent** with the discrepancy quoted — it still holds the
  scope's context and its own reasoning about the code. Spawn a fresh agent only when the
  problem is the approach itself, or when the original agent is gone.
- **Worker reports are not shown to the user.** The orchestrator relays a verified summary.
  Never paste a worker's claim upward as if it were evidence — verify it first, per
  **agent-in-the-loop** Step 3.
- **Don't poll background agents.** You get notified when they finish; polling burns tokens and
  wall-clock. Do the orchestrator's own reading (anchor map, invariants, integration plan) while
  they run.
- **Keep the batch state in the orchestrator, one scope in each worker.** The orchestrator holds
  the anchor map, the baseline, every finding and every flag; each worker holds only its scope.
  Handing a worker the whole plan makes it drift into its neighbors' work.

## Phase 6 — Status report

Maintain (or create) the scopes document with an **"Execution status"** section at the very top,
updated per batch:

```
**Batch N — DELIVERED <date> (branch `feat/scopes-batch-N`, not merged into `main` yet).**
K implementers in isolated worktrees + K adversarial reviewers (B blockers, M medium, L low)
+ integration pass with fixes. Suite X/X green [+ secondary suites].

| Scope | Status | Branch | Integration notes |
|---|---|---|---|

**Integration decisions:** <named composition rules resolved during the merge>
**Batch N followups** (not bugs): …
**Pending your decision:** merge/push.
```

Report the **finding counts** (`0 blockers, 9 medium, 14 low`): a review pass that found nothing
and a review pass that was never run look identical in a table of green checkmarks. Followups
carry their own state — strike them through with a date when a later batch resolves them, so the
document stays a ledger instead of growing a second backlog.

When the autonomous backlog runs empty, declare it: "Autonomous technical backlog: EMPTY. What
remains is the Excluded block (human decisions/assets/infra) — outside the autonomous scope."

---

## Lessons paid for in production

Each of these cost a real batch to learn. They are already wired into the phases above; this is
the short list to re-read before dispatching.

- **Every implementer runs the full suite**, not just its area's — cross-scope breakage surfaces
  before integration, where it is an order of magnitude cheaper.
- **A scope that turns out already-resolved is not closed falsely.** Investigate, then add the
  test that locks the behavior in, and strike the corresponding loose end in the plans.
- **A scope may legitimately grow when the invariant it enforces has more clauses than the
  scope's author noticed** — implement the whole clause, and say "done + expanded" with the
  reason in the report. That is not scope drift; drift is touching a *neighbor's* system.
- **Followups never enter the in-flight batch.** They get an ID and compete for the next one.
- **Merging to the main branch is never automatic** — every batch ends green on its branch with
  the user's decision pending.
- **Baselines beat absolutes.** A repo with known intermittent red still supports autonomous
  work, as long as every worker's claim is a delta against a written baseline.

## Composes with

- **agent-in-the-loop** — the verification discipline for Step 3/4: the orchestrator refutes
  each claim with its own evidence and re-dispatches what fails, looping until a review pass
  comes back dry.
- **patron-oro** — pilot ONE scope to gold level, then replicate the batch shape; inside a scope,
  ship the generic engine + one gold exemplar + a tolerant fallback.
- **engram-memory** — baselines, integration decisions and flags are saved per batch, so the next
  batch starts from evidence instead of archaeology.

## Skill resources

- `references/templates.md` — full scopes-document template (copyable) and an example of a
  well-written scope. Read it when generating the document for the first time.
- `references/agents.md` — ready-to-use prompts for the three roles (implementer, adversarial
  reviewer, integrator) with their placeholders and the structured report format. Read it when
  starting a batch execution.
