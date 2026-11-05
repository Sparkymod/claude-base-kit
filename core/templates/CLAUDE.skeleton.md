# Template: host CLAUDE.md skeleton

Starter orchestration file for a host project adopting the kit. Copy the block below to
the host's root `CLAUDE.md`, replace `{…}` placeholders, delete what the host doesn't need.

```markdown
# ⚠️ Task Classification Before Action

BEFORE any file creation or modification that produces a deliverable, emit:

​```
TASK: {one-line description}
SCOPE: {estimated file count} file(s), {complexity tier}
ACTION: INLINE | DELEGATE → {agent-name}
​```

Delegation is REQUIRED when: the task creates/modifies ≥{5} files, OR it splits into ≥2
independent scopes that will genuinely run in parallel.
Below that threshold, work INLINE — the main thread already holds the context, and every
dispatch re-pays it (.claude/principles/context-economics.md). A specialist MAY take a
bounded task in its domain when its gates add real value; existing is not a reason to dispatch.
Execute directly (no classification) when: single-file edit ≤{20} lines, typo, rename,
config toggle, answering a question.

When delegating: one implementer per phase (not per subtask), one review pass per batch
(not per agent), resume the same agent on re-dispatch.

Feature-sized work runs the `sdlc-feature` pipeline (.claude/pipelines/sdlc-feature.md);
below the threshold its stages run inline.

# Authority Chain

1. `.claude/rules/stack-contract.md` — THE stack answers (build/test/idioms). Agents never guess past it.
2. {host's own coding standards doc, if any}
3. `.claude/` knowledge base — skills, rules, lessons. When silent, search the code.

# Rationalization Prevention (short table — full: .claude/principles/rationalization-prevention.md)

| # | Rationalization | Why It Fails |
|---|---|---|
| 1 | "Faster to do it myself" | Speed is not a routing criterion; quality gates exist for a reason. |
| 2 | "It's just one small change" | Size is not a criterion; the threshold is objective. |
| 3 | "The sub-agent said it's done" | Claims are not evidence — verify (orchestrator-verification-protocol). |
| 4 | "Delegating is always the safer choice" | Each dispatch re-pays the context; below the threshold, inline is the rule (context-economics). |

# Verification Before "Done"

​```
{the stack contract's verification-before-done command sequence}
​```
Quote real output; never claim green without running.

# Available Agents

| Agent | Delegate when |
|---|---|
| `requirements-analyst` | Raw request needs structuring into testable requirements |
| `solution-designer` | Design decisions, contracts, ADRs needed before code |
| `code-implementer` | Implementing a committed design (general executor) |
| `test-designer` | Test plan/cases/shells for a feature |
| `technical-writer` | Human documentation of approved artifacts |
| `knowledge-curator` | KB maintenance, lesson capture, drift audits |
| {host-specific agents here — specialists take precedence over `code-implementer`} | |

Constraint: only the main thread dispatches agents. Agents cannot spawn agents.
```

## Notes for the adopter

- If the host already HAS a `CLAUDE.md`, merge — don't replace: keep the host's authority
  chain on top, add the classification block and the agent catalog.
- The classification thresholds (≥5 files or genuine parallelism, ≤20 lines) are defaults —
  tune them, but keep them **objective** (countable), or rationalization eats them. Lowering
  the file threshold multiplies dispatches; measure first (`principles/context-economics.md`).
- Keep the always-apply rules short: they are re-read on every step of every agent.
