# Pipeline: sdlc-feature

Feature-sized work flows through five staged agents connected by disk artifacts and hard
gates. The orchestrating thread (the main conversation) dispatches every stage and
verifies every claim — agents never dispatch agents.

## When to run it — and when not to

- **Run it** for feature-sized work: new capability, new user-facing flow, cross-cutting
  change with design decisions.
- **Skip it** for typos, config toggles, single-file bounded fixes — the host's
  orchestration rules (its `CLAUDE.md` task classification) decide the threshold, not effort feelings.
- A **stack contract** must exist and be filled before stage 2 (see
  `principles/stack-contract-protocol.md`); stage 1 can run without it.

## Stages

| # | Stage | Agent | Input | Output (artifact contract) |
|---|---|---|---|---|
| 1 | Requirements | `requirements-analyst` | Raw request / backlog item | `artifacts/requirements-{id}.md` + `traceability-{id}.json` |
| 2 | Design | `solution-designer` | requirements-{id} + stack contract + host KB | `artifacts/design-{id}.md` + `roadmap-{id}.md` |
| 3 | Test design | `test-designer` | requirements-{id} + design-{id} | `artifacts/test-plan-{id}.md` + test shells |
| 4 | Implementation | `code-implementer` (or host specialist — see routing) | design-{id} + test-plan-{id} | Code + `artifacts/implementation-{id}.md` |
| 5 | Documentation | `technical-writer` | The approved, implemented artifacts | Docs + `artifacts/docs-{id}.md` |

Stage 3 before stage 4 is deliberate: the test plan derives from requirements and design,
never from implementation code.

## Routing rules

- **Host specialists win.** If the host KB defines an executor specialized for the task
  type (an entity scaffolder, a page builder, a migration planner…), stage 4 routes there
  instead of `code-implementer`. Same for a host test agent at stage 3 — the kit's
  `test-designer` then hands its plan's rows to the specialist for authoring.
- **Stages can be skipped explicitly, never silently.** Skipping stage 1 (requirements
  already exist) or 5 (no doc surface) is an orchestrator decision recorded in the
  dispatch, with the rationale.

## Gates (between every stage)

```
agent signals STATUS  →  orchestrator verifies (Layer 2)  →  advance | re-dispatch | escalate
```

1. `STATUS: COMPLETE` → the orchestrator applies `principles/orchestrator-verification-protocol.md`
   to each claimed deliverable. All pass → next stage. Any fail → re-dispatch with the
   discrepancy. **A partially verified stage never advances.**
2. `STATUS: BLOCKED` → obtain the named input (usually from the human), re-dispatch.
3. `STATUS: NEEDS-REVIEW` → the orchestrator decides: fix upstream (re-dispatch the owning
   stage), adjust scope, or accept with recorded rationale. Downstream agents never edit
   upstream artifacts.

## Completion definition

The pipeline is done when: all stage artifacts exist and were Layer-2 verified, the stack
contract's **verification-before-done** commands pass with output quoted, and deviations
and debt from stage 4 are either resolved or explicitly accepted by the human.

## See Also

- `principles/dispatch-status-signals.md` — signals + artifact contracts
- `principles/orchestrator-verification-protocol.md` — the gate mechanics
- `templates/CLAUDE.skeleton.md` — host-side orchestration that invokes this pipeline
