---
name: Orchestrator Verification Protocol
description: "Two-layer verification for delegated work: agents self-verify (Layer 1), and the orchestrating thread independently verifies claimed deliverables with its own read-only tool calls (Layer 2). A completion report is a claim, not evidence. Verification commands come from the host's stack contract."
---

# Orchestrator Verification Protocol

## Problem

When a sub-agent hallucinates success ("file updated, tests green"), its own verification
step hallucinated too. The dispatching thread is the only actor positioned to catch it.
Accepting a completion report at face value ships the failure to the user.

## Two-layer model

| Layer | Actor | Obligation |
|---|---|---|
| **1 — Self-verification** | The agent | Produce fresh evidence (build/test output, file content) before reporting COMPLETE |
| **2 — Independent verification** | The dispatching thread | Verify each claimed deliverable with its OWN tool calls before accepting |

**Never trust, always verify.** Layer 2 is read-only *observation* — inspect the result,
don't redo the work. All build/test/lint commands used as evidence are the ones named by
the host's **stack contract** (`stack-contract-protocol.md`) — never guessed.

## Verification matrix (by deliverable type)

| Claimed deliverable | Verify by | Evidence |
|---|---|---|
| File created | Read the file | Content visible, expected shape |
| File modified | Read the changed section | Diff matches the claim |
| Code change | Read changed files + run the contract's build command | Build output quoted |
| Tests added | Read test file + run the contract's test command (scoped where possible) | New tests visible in the pass count |
| Requirements/design artifact | Read it; check its schema sections are populated and its quality gate items hold | Structure + traceability present |
| Documentation | Read it; spot-check documented commands/examples against the repo | Docs match reality |
| Deletion | Glob confirms absence + grep confirms no dangling references | Absence + zero referrers |
| "Suite is green" | Re-run the contract's verification-before-done command(s) | Output quoted verbatim |

Hosts extend this matrix in their own KB with their codebase's silent-failure points —
the mismatches that compile fine but fail at runtime are exactly what Layer 2 exists to catch.

## Protocol

```
1. Receive the completion report
2. Extract the claimed deliverables (paths, changes, test counts)
3. Apply the matrix to EACH claim
4. All pass → accept and advance
5. Any fail → do NOT advance; re-dispatch with the discrepancy, or take over explicitly
```

## Rules

1. "Tests pass" without quoted output is not acceptance-worthy — in either layer.
2. Verification commands run synchronously; no orphaned processes left behind.
3. A partially-verified pipeline stage does not advance — the gates in
   [pipelines/sdlc-feature.md](../pipelines/sdlc-feature.md) are hard.
4. This applies to human-delegated work too: a pre-PR review sweep is Layer 2 for a human session.

## See Also

- `rationalization-prevention.md` — rows 8/9: "passed" and "reported success" are pre-rejected as completion proof
- `scope-enforcement-protocol.md` — reviewers stay read-only precisely so Layer 2 stays independent
- `stack-contract-protocol.md` — where the verification commands come from
