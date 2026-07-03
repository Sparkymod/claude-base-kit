---
name: Unix Philosophy
description: "Six Unix-philosophy principles applied to any codebase and to the kit itself: do one thing well, design for composition, separate policy from mechanism, silence is success, fail noisily by failure class, and write programs to write programs."
---

# Unix Philosophy (as the kit applies it)

| # | Principle | What it demands in any stack |
|---|---|---|
| 1 | **Do one thing and do it well** | A module owns one concern; a service one aggregate; a worker one job; a scene one responsibility; a lesson one gotcha. If describing a unit needs "and", split it. |
| 2 | **Design for composition** | Small units combine through declared contracts: composable rules/specifications, middleware chains, node/component trees, pipeline stages composing agents. Prefer combinators over configuration flags. |
| 3 | **Separate policy from mechanism** | Policy = declarations (config, constants, option objects, data tables, transition tables). Mechanism = generic engines that honor them. Changing policy never edits the engine — if it does, the split is fake. |
| 4 | **Silence is success** | Routine success produces data, not narration. Info-level logs are reserved for meaningful state transitions; chatty flow logging is demoted or deleted. |
| 5 | **Fail noisily — by failure class** | Business failures: controlled, typed, visible to the caller. Bugs: immediate loud failure. Infrastructure: full detail in private logs + correlation id, generic message outward. Swallowed errors are review-rejected. (See `core-design-tenets.md` failure-class table.) |
| 6 | **Write programs to write programs** | Conventions strict enough to document are strict enough to generate. When a manual step recurs, the ladder in `knowledge-evolution.md` turns it into a skill or command — the KB itself is this principle applied to knowledge. |

## The two rows that do the most work

**Policy/mechanism (3)** is the highest-leverage review question in any codebase: nearly
every healthy subsystem splits into a declarative surface and a generic engine. When
adding a feature edits an engine instead of adding a declaration, flag it.

**Generation (6)** is why the kit and host KBs exist: a repeated procedure is a program
waiting to be written. Hosts own the generators (they need stack vocabulary); the kit owns
the discipline of noticing the repetition.

## See Also

- `core-design-tenets.md` — the module-level companions to these system-level rules
- `knowledge-evolution.md` — the promotion ladder behind row 6
