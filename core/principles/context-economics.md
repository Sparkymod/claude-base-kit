---
name: Context Economics
description: "Every agent step re-reads its whole context, so the cost of agent work is driven by how many agents are dispatched and how many steps each takes — not by the size of the kit's definitions. Defines the delegation threshold, batching, one-review-per-batch, and the budget for always-loaded instructions and catalog descriptions."
---

# Context Economics

Every model step re-reads the agent's whole context: the always-loaded instructions (the
host's orchestration file, its always-apply rules, the memory index, the skill and agent
catalogs) plus everything that agent has accumulated so far. Roughly:

```
cost of one agent ≈ (start-up context + accumulated context) × number of steps
```

A dispatch is never free. Each new agent re-pays the start-up context, then re-discovers
code the orchestrator already holds — and every file it reads is re-read on each of its
later steps.

## What the measurement showed

One host, 31 sessions, ~31,000 model steps (2026), effective usage weighted by cost
(cache read ≈ 0.1×, cache write ≈ 2×, output ≈ 5× a fresh input token):

| Driver | Share |
|---|---|
| Subagents, in every large session | 70–80 % of the session |
| The general implementer role alone | 70 % of all subagent spend (161 dispatches, ~100 steps each) |
| Always-loaded instructions (orchestration file + rules + memory index) | ~4–5 % |
| Skill bodies and agent definitions | < 1 % — rarely loaded, cheap when loaded |

The lever is **the number and length of dispatches**. Trimming definitions helps at the
margin; dispatching less moves the total.

## Rules

1. **Delegation threshold — objective and countable.** Delegate when the task creates or
   modifies **≥ 5 files**, OR when it splits into **≥ 2 independent scopes that will
   genuinely run in parallel**. Below that, the orchestrator works inline — it already holds
   the context. A specialist agent MAY still take a bounded task in its domain when its
   gates add real value; existing is not a reason to dispatch it.
2. **One implementer per phase, not per subtask.** Subtasks that share files or context go to
   the same agent, in sequence. Splitting them re-pays the start-up and the archaeology for
   each piece.
3. **One review pass per batch, not per agent.** A single reviewer reads the combined diff.
   Dedicated per-scope reviewers are reserved for scopes touching security, authorization,
   data integrity or schema changes, or when the batch diff is too large for one reader.
4. **Resume, don't respawn.** A re-dispatch goes back to the same agent with the discrepancy
   quoted; a fresh agent re-learns everything.
5. **Hand over anchors.** Real file/line coordinates in the dispatch cost less than the same
   search repeated by every worker.
6. **Budget the always-loaded layer.** Always-apply rules are re-read on every step of every
   agent. Keep them to the invariants that gate every change; move one subsystem's
   procedures, command recipes and incident history into an on-demand skill or reference,
   and leave a one-line pointer in the rule.
7. **Keep catalog descriptions short.** Skill and agent descriptions ride in every step's
   catalog. One sentence of what it does, then the trigger phrases, ≤ ~600 characters in
   all; the body carries the detail.
8. **Measure before tuning.** Read the harness's usage or transcript data to see where the
   tokens went — by dispatch, by tool, by always-loaded layer — before changing any of the
   above.

## See Also

- `rationalization-prevention.md` — row 11: "delegating is always the safer choice"
- `orchestrator-verification-protocol.md` — quality comes from verification, not agent count
- [templates/CLAUDE.skeleton.md](../templates/CLAUDE.skeleton.md) — where a host sets its threshold
- [pipelines/sdlc-feature.md](../pipelines/sdlc-feature.md) — cost-aware execution of the stages
