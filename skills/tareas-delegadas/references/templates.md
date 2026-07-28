# Templates — scopes document

## Full document template

Save as `docs/tasks_by_scope.md` (or wherever the project keeps its plans). Copy and fill in:

```markdown
# Tasks by scope for agents — autonomous technical work

**Date:** YYYY-MM-DD · **Author:** <who is planning>
**Purpose:** split the pending work and the *natural next steps* into **bounded scopes**
so that each agent specializes in ONE.

## Execution status

_(empty at the start; updated per batch — see the format at the end)_

## Filtering criterion (what's in and what's NOT)

**IN** — tasks an agent can complete **autonomously**:
- Pure code (…adapt to the project…).
- Declared bugs and technical debt.
- Closing out already-designed systems where only wiring/implementation is missing.

**NOT IN** (left for passes with the human — documented in §"Excluded" at the end):
- **Assets/creative:** …
- **Content:** …
- **Human decisions:** …
- **User infra:** …

> Rule for the agents: where a task brushes against a provisional decision, implement the
> **already documented sensible default** and leave a **flag/note** for async ratification —
> **never** block.

## Current state (minimal context)

- <completed milestones and what remains, with references to the master plans>
- **Baseline:** suite N/N green — or `N tests / K failing = <known pre-existing red, documented where>`.
  Green in this document means **no NEW red versus this baseline**. Each worktree records its own
  baseline from its own HEAD before touching anything.
- Smokes per system: <…>. Last session: <…>

## Anchor map (recon output — every scope prompt quotes from here)

Real coordinates so no worker re-derives them:

- **<Area 1>:** the system is created at `path/file.ext:NN-MM`; consumed at `path/other.ext:NN`.
  Mold to mirror: `<closest well-built analogue>` (`path`). Reference test: `tests/…`.
- **<Area 2>:** … Empty/absent today: `<dirs or systems that do not exist yet>`.
- **Hard invariants in play:** <verbatim rules a worker must not violate>.

---

## The scopes

Each scope: **goal · concrete scope (real files/symbols) · done criterion ·
dependencies · note**. IDs with an area prefix. Backlog origin in brackets.

### Area 1 — <name>

#### `XX-1` · <title>  [<origin>]
- **Goal:** …
- **Scope:** … (`path/file.ext:line`, real symbols) … Mold to mirror: `<path>`. Reference test: `<path>`.
- **Done:** … (verifiable) …
- **Dep:** none. **Autonomous.** _(if it shares a seam with a parallel scope, state the defensive
  contract here AND in the other scope's note — e.g. "reads `<setting>` through an optional lookup;
  works whether or not `YY-2` has landed")_
- **Note:** … invariants that must hold; defaults chosen + `FLAG:`; what is explicitly out.

_(repeat per scope and per area)_

---

## Prioritization and suggested assignment

| # | Scope | Area | Value | Risk | Parallel with |
|---|---|---|---|---|---|
| 1 | `XX-1` … | … | High | Low | everything |

**Split by agent specialization:**
- **<Area 1> Agent:** `XX-1`, `XX-2`.
- **<Area 2> Agent:** …

**Common contract for all agents:**
1. One scope = one commit (or few) with its smoke/test green; do not touch files outside your scope without saying so.
2. Respect <the project's coding standards>.
3. Run the full suite + the relevant smoke before calling it done; report N/N green.
4. Record the result in <backlog> (what's resolved LEAVES it → lesson in <lessons docs>).
5. On brushing against a human decision: implement the documented default and leave `FLAG:` in the commit/doc.

---

## Explicitly excluded (why it is not here)

- **Assets/creative:** <list with references>
- **Content:** <…>
- **Human decisions:** <…>
- **User infra:** <…>
```

## "Execution status" section format (per batch)

```markdown
**Batch N — DELIVERED YYYY-MM-DD (branch `feat/scopes-batch-N`, not merged into `main` yet).**
K implementers in isolated worktrees + K adversarial reviewers (**B blockers, M medium, L low**)
+ integration pass (merge + review fixes).
**Full suite N/N green, exit 0.** [+ secondary suites]

| Scope | Status | Source branch | Integration notes |
|---|---|---|---|
| `XX-1` <title> | ✅ done | `scope/xx-1` | <integration fixes, defaults, flags> |
| `XX-2` <title> | ✅ done + expanded | `scope/xx-2` | <the extra clause of the same rule, and why> |
| `XX-3` <title> | ✅ already closed | `scope/xx-3` | no production change needed; test added to lock it in |

**Integration decisions:** <named composition rule + rationale, for every behavior two scopes
both shaped — e.g. "the user setting is a MULTIPLIER over the per-item authored value; the
user's on/off always wins">
**Batch N followups** (not bugs): <list of derived candidate scopes>
**Pending your decision:** merge `feat/scopes-batch-N` → `main` (and/or push).
```

Report the finding tally: a review pass that found nothing and a review pass that never ran look
identical in a table of checkmarks. A dependent batch is cut from the previous batch's branch,
not from `main` — say so, and say which branch a merge would carry.

When the user approves the merge, update it to:
`**Batch N merged into `main` (`<sha>`, pushed).**`
When a later batch resolves a followup, strike it through in place with the date
(`~~<followup>~~ ✔ YYYY-MM-DD: <what closed it>`) — the document stays a ledger instead of
growing a second backlog.

## Example of a well-written scope (agnostic)

```markdown
#### `API-2` · Real pagination in the orders list  [BL-31]
- **Goal:** the endpoint returns the ENTIRE history (~40k rows today) and the front end
  paginates in memory — production timeouts reported. Close it with cursor pagination.
- **Scope:** `src/api/orders/router.py:88-120` (query + `cursor`/`limit` params),
  `src/api/orders/schemas.py` (response with `next_cursor`), and the
  `web/src/hooks/useOrders.ts` hook to consume it. Do not touch the model or the migration.
- **Done:** integration test: 3 consecutive pages with no duplicates and no gaps using
  fixture data; the front end's contract test passes; full suite green.
- **Dep:** none. **Autonomous.**
- **Note:** default `limit=50` (max 200). FLAG: does the team also want classic offset in
  addition to the cursor? — non-blocking.
```

What makes it good: it cites real paths and lines, delimits what is NOT touched, the done is
binary and automatable, and the product doubt was left as a FLAG with a default.
