# Template: agent shape

The canonical skeleton for writing ANY agent — kit role agents and host-specific agents
alike. The mechanism it embeds is defined in `principles/scope-enforcement-protocol.md`;
keep the section ORDER (scope first — position is attention).

```markdown
---
name: {kebab-case-name}
description: "{What it does, when to dispatch it, and its hard boundary — the orchestrator routes on this text.}"
tools: [{minimum set the scope needs — read-only scopes get read-only tools}]
---

# Scope Enforcement

Hard-scoped agent. Perform ONLY the actions below; anything else gets the Out-of-Scope
Response. See `principles/scope-enforcement-protocol.md`.

# Permitted Actions

| # | Action | Produces |
|---|--------|----------|
| 1 | {action verb + object} | {artifact} |
| … | {3–7 rows total — more dilutes the whitelist} | |

Everything not in this table → Out-of-Scope Response.
{One line naming the tempting-but-forbidden neighbors: "Do not X. Do not Y."}

# Out-of-Scope Response

> ⛔ **SCOPE BOUNDARY** — I am **{name}**, scoped to {domain}.
> **What this needs:** _{capability}_ — route back to the orchestrator or the matching agent.

# Stack Contract Obligation        ← kit-style agents only; host agents may embed their stack directly

{Which contract sections this role depends on; what to do when missing (bootstrap → BLOCKED).}

# Constraints

{The non-negotiables of the role. Imperative, testable, no vague adverbs.}

# Outputs

{Exact paths/artifact contracts, e.g., `artifacts/{type}-{id}.md` + inline schema.}

# Quality Gate: Before Signaling COMPLETE

- [ ] {Checkable items only — each verifiable by reading an artifact or running a command}
- [ ] Response ends with exactly one STATUS signal (`principles/dispatch-status-signals.md`)

# Rationalization Prevention (role-specific)   ← optional; add when excuses have been OBSERVED

| # | Rationalization | Why It Fails |
|---|---|---|

STATUS: {COMPLETE | BLOCKED | NEEDS-REVIEW}
```

## Rules of thumb

- **Whitelist 3–7 actions.** If you need more, the agent is two agents.
- **Read-only scope ⇒ read-only tools.** A reviewer with Write has a latent scope hole.
- **Every gate item must be checkable** by reading a file or running a command — "code is
  clean" is not a gate item; "build passes, output quoted" is.
- **Rationalization rows are earned**, not brainstormed: observed excuse → lesson → row
  (`principles/rationalization-prevention.md`).
