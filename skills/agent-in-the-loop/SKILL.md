---
name: agent-in-the-loop
description: "Agent-in-the-loop delegation: split autonomous work into bounded scopes, dispatch parallel implementer agents (isolated worktrees, one scope each), then the ORCHESTRATOR — the strongest model in the session — adversarially reviews every claim with its own evidence and re-dispatches whatever failed, looping until verified done. Also use to DECIDE whether delegating is worth it at all. Triggers: /agent-in-the-loop, 'delega en paralelo', 'asigna scopes a agentes', 'batch de agentes', 'trabaja esto con agentes en paralelo', 'run this with parallel agents'."
---

# Agent in the loop — parallel delegation with the orchestrator as reviewer

> In classic *human-in-the-loop*, a person reviews what the agent produced. Here the
> reviewing seat inside the loop is taken by the **orchestrating agent itself** — the
> strongest model available in the session — while the human moves **on** the loop:
> they set direction, ratify design decisions, and approve merges. The loop closes when
> the orchestrator's own independent verification passes — never when a worker *claims*
> it is done.

This composes two canonical patterns from Anthropic's *Building Effective Agents*:
**orchestrator-workers** (a lead dynamically decomposes and delegates) wrapped around an
**evaluator-optimizer** loop (generate → evaluate → feed the findings back → regenerate),
with the orchestrator playing the evaluator. Field-validated across 6 batches / 22 scopes
of production work (2026), all delivered green.

## Step 0 — Decide: delegate or do it inline

This skill is also the decision rubric. **Delegate** when ALL of these hold:

1. The work splits into **≥2 scopes with no runtime dependency between them** (they may
   share a repo, not a file).
2. Each scope fits comfortably in one agent's context (one system, a handful of files).
3. "Done" is **mechanically checkable** per scope (tests, build, a reproducible smoke) —
   if done is a matter of taste, the loop cannot close by itself.
4. The scopes are implementable **autonomously**: no blocking decision that belongs to
   the user/designer sits in the critical path (see the autonomy filter below).

**Do it inline** when any of these hold: it is one tightly-coupled change; it is
exploration where each finding reshapes the plan; the handoff cost (explaining context)
exceeds the work itself; or fewer than 2 scopes survive the autonomy filter. Delegating
one scope to one agent is fine — the *loop* still applies; only the parallelism goes.

## Step 1 — Scope the batch

Write the batch plan **before** dispatching anything. Per scope:

- **ID + objective** — one sentence of value, not activity.
- **Concrete surface** — real files/symbols it may touch. This is a whitelist, not a hint.
- **Done criteria** — observable and checkable (which tests, which smoke, which behavior).
- **Dependencies** — scopes that must land first; everything else parallelizes.

Apply the **autonomy filter**: only work an agent can finish alone enters the batch.
Owner decisions, content/art direction, and the user's infrastructure stay OUT, listed
explicitly in an "excluded" section so the boundary is documented. Where a scope brushes
against a provisional decision, the rule is **default-and-flag**: implement the sensible
documented default and leave a `FLAG:` note for async ratification — **never block
waiting for the human**.

## Step 2 — Dispatch parallel implementers

One implementer agent per scope, all launched in parallel, each in an **isolated
worktree** cut from the same HEAD (never let workers share a mutable tree with other
sessions). Give workers the strongest *implementation-capable* model available; the
orchestrator keeps the strongest *judgment* model for itself (e.g. Opus-tier workers
under a Fable-tier orchestrator — an example, not a requirement).

Every implementer gets the same contract in its prompt:

1. Record YOUR baseline (test counts, pre-existing failures) from HEAD before touching
   anything — otherwise you cannot prove you broke nothing.
2. Touch nothing outside your scope's whitelist; if you must, stop and report it.
3. Run the **full suite**, not just your scope's tests, before claiming done
   (cross-scope breakage is the #1 silent failure).
4. Report **evidence, not claims**: quoted test output, file paths, counts.
5. On a decision you cannot make: default-and-flag, never stall.

## Step 3 — The loop: adversarial review + independent verification

When workers report back, the orchestrator becomes the agent in the loop:

- **Adversarial review per branch** — a read-only reviewer (or the orchestrator itself)
  actively tries to find what is wrong, missing, or out of scope in each branch. Its job
  is to refute "done", not to confirm it.
- **Independent verification** — the orchestrator checks each claimed deliverable with
  its OWN tool calls: read the files, re-run the verification commands, compare against
  the scope's done criteria. **A completion report is a claim, not evidence.** If the
  host has the base kit installed, apply the full matrix in
  `.claude/principles/orchestrator-verification-protocol.md`; verification commands come
  from the host's stack contract, never guessed.

## Step 4 — Re-dispatch what failed

For every finding: send the scope back to an implementer **with the discrepancy quoted**
(what was claimed vs what was observed), or take it over explicitly — never silently
accept a partial result, and never mark a scope done "because the agent said so".
Iterate Step 3 ↔ Step 4 until a review pass comes back **dry** (no findings). This is
the evaluator-optimizer loop: the generator's next attempt is conditioned on the
evaluator's findings.

## Step 5 — Integrate, verify, record

- Merge the scope branches into one **batch branch**; expect and budget an
  **integration pass** — cross-scope interactions only surface here, and the fixes made
  during integration get reviewed like any other change.
- Run the full suite on the integrated result and quote the output. Green means the
  batch's number, not "probably fine".
- Record the outcome where the project tracks pending work (resolved items LEAVE the
  checklist; lessons go to the knowledge base / persistent memory).
- **The human stays on the loop**: merging the batch to the main branch, pushing, and
  ratifying flagged decisions are theirs unless explicitly pre-authorized.

## Failure modes this loop exists to catch

| Symptom | Countermeasure |
|---|---|
| Worker hallucinates success ("tests green") | Step 3 independent verification — its self-check hallucinated too |
| Worker ran only its own tests | Contract rule 3: full suite per worker, again at integration |
| Cross-scope conflict invisible per-branch | Dedicated integration pass with its own review |
| Scope drift (worker "improves" neighbors) | Whitelisted surface + reviewer flags out-of-scope diffs |
| Loop never closes (taste-based done) | Step 0 rule 3 — don't delegate what can't be mechanically verified |
| Worker blocks on an owner decision | Default-and-flag; the batch never waits on a human mid-flight |

## Composes with

- **patron-oro** — pilot ONE scope end-to-end to gold level first, then replicate the
  batch shape; the first batch is itself the gold pattern for later batches.
- **engram-memory / persistent memory** — each batch's outcome, baselines, and flags are
  saved so the next batch starts from evidence, not archaeology.
- Base-kit principles when installed: `orchestrator-verification-protocol` (the
  verification matrix), `scope-enforcement-protocol` (hard whitelists),
  `dispatch-status-signals` (worker report format).
