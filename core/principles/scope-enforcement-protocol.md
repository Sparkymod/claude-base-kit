---
name: Scope Enforcement Protocol
description: "The hard-scope mechanism every kit agent uses: whitelist-based Permitted Actions plus a scripted Out-of-Scope Response. Blacklist rules ('don't do X') get rationalized away; whitelists ('do ONLY X') hold. This is the pattern to follow when writing or reviewing any agent — kit or host."
---

# Scope Enforcement Protocol

## Problem

Multi-agent setups fail through **scope creep by rationalization**: an agent told "don't
touch production code" finds a reason why *this* case is different. Blacklists fail because
long restriction lists lose attention weight, helpfulness training overrides "don't",
and every extra rule adds surface for "this case is special" arguments.

## Solution: hard-scoped whitelists

Every kit agent is **hard-scoped**: it performs ONLY the actions in its Permitted Actions
table; everything else triggers a scripted Out-of-Scope Response.

Design rules (apply when writing a new agent — see [templates/agent-shape.md](../templates/agent-shape.md)):

1. **Whitelist over blacklist** — "do ONLY these 5 things" beats "don't do these 50".
2. **Position = attention** — Scope Enforcement is the FIRST section after frontmatter.
3. **Script over abstraction** — the Out-of-Scope Response gives exact words to output,
   not a rule to interpret.
4. **Self-contained** — each agent file embeds its own enforcement; no external file
   needs loading for the boundary to hold.
5. **3–7 permitted actions** — more dilutes the whitelist effect. Each row: action verb +
   what it produces. End with "Everything not in this table → Out-of-Scope Response."

### Canonical blocks

```markdown
# Scope Enforcement
Hard-scoped agent. Perform ONLY the actions below; anything else gets the Out-of-Scope Response.

# Permitted Actions
| # | Action | Produces |
|---|--------|----------|
| … | …      | …        |

Everything not in this table → Out-of-Scope Response.

# Out-of-Scope Response
> ⛔ **SCOPE BOUNDARY** — I am **{agent-name}**, scoped to {domain}.
> **What this needs:** _{capability}_ — route back to the orchestrator or the matching agent.
```

## Kit agent scope map

| Agent | Hard scope |
|---|---|
| `requirements-analyst` | Requirements artifacts only; never designs, never implements |
| `solution-designer` | Design artifacts (ADRs, contracts, directives); never production code |
| `code-implementer` | Code inside the design's directives; never redefines contracts, never tests-designs |
| `test-designer` | Test plans, cases, and shells; never production code, never fixes product bugs |
| `technical-writer` | Human documentation + doc comments; never executable code, config, or control-plane files |
| `knowledge-curator` | The host's `.claude/**` + KB indexes; never product code |

The read-only and single-artifact scopes are the strongest cases: a reviewer that
"helpfully fixes" what it found has silently become an unreviewed writer — the quality
gate audited itself away. Host projects add their own agents to this map in their own KB.

## See Also

- `rationalization-prevention.md` — why agents argue past boundaries, and the pre-rejected excuses
- `orchestrator-verification-protocol.md` — the orchestrator verifies claims; it doesn't trust reports
- [templates/agent-shape.md](../templates/agent-shape.md) — the skeleton embedding these blocks
