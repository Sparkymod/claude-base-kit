---
name: Rationalization Prevention
description: "The dominant failure mode of agent workflows is rationalizing boundary violations ('this time it's different'). Defines the universal table of pre-rejected rationalizations and the pattern for hosts and agents to add their own observed-excuse tables."
---

# Rationalization Prevention

Agents rationalize boundary violations — not occasionally, structurally. Every excuse in
the table below has been **pre-evaluated and rejected**: if reasoning matches a row, the
reasoning is already known to be invalid. The correct move is to follow the boundary, not
to re-litigate whether "this time is different".

## Universal base table

| # | Rationalization | Why It Fails |
|---|---|---|
| 1 | "It would be faster to do it myself" | Speed is not a routing criterion. Quality gates exist for auditability and separation of concerns. |
| 2 | "It's just one small change" | Size is not a criterion. Scope thresholds are objective, set by the host's orchestration rules. |
| 3 | "I already know the codebase" | Context familiarity does not exempt routing. |
| 4 | "The user said to just do it" | Urgency doesn't exempt quality gates. Route and execute quickly — but still route. |
| 5 | "The agent would just do what I'd do" | The agent applies specialized gates the main thread skips under time pressure. |
| 6 | "This is a minor tweak, not a real deliverable" | All artifact changes are deliverables; size does not change the rules. |
| 7 | "I'll fix it now and formalize later" | "Later" does not arrive. Informal fixes bypass review and leave no trail — capture a lesson or do it properly. |
| 8 | "The build/test passed, so the work is done" | Passing is necessary, not sufficient. Green output must be quoted AND the change must serve the stated goal. |
| 9 | "The sub-agent reported success, so it's done" | Self-reporting is a claim, not evidence. See `orchestrator-verification-protocol.md`. |
| 10 | "This ecosystem usually does it another way" | The stack contract wins over training priors. The host chose its idiom deliberately. See `stack-contract-protocol.md`. |

## Host-specific and agent-specific tables

- **Hosts** keep their own table (in their `CLAUDE.md` or project KB) for excuses observed
  in THEIR codebase's domain — e.g., "this entity is trivial, I'll skip recipe steps".
- **Agents** MAY carry a short table (2–5 rows) for their role's recurring excuses,
  referencing this file.

Keep all tables evidence-based: a row enters after the excuse has actually been observed
(capture it as a lesson first — see `knowledge-evolution.md` — promote it here on repetition).

## See Also

- `scope-enforcement-protocol.md` — the whitelist mechanism these tables defend
- `orchestrator-verification-protocol.md` — verification as the antidote to claim-trusting
- `stack-contract-protocol.md` — row 10's authority chain
