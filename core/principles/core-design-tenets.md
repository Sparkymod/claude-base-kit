---
name: Core Design Tenets
description: "Six stack-agnostic design tenets that kit agents apply through the host's stack contract: program to an interface, command-query separation, design by contract, cohesive modules, self-sufficient packages, and result-style handling for expected failures. Includes the failure-class table that drives error-handling decisions in any stack."
---

# Core Design Tenets

These tenets are universal; **how** each is realized is a stack-contract answer. Agents
apply the tenet; the contract supplies the idiom.

| # | Tenet | What it demands in any stack |
|---|---|---|
| 1 | **Program to an interface, not an implementation** | Consumers depend on declared contracts (interfaces, protocols, ports, signatures, schemas) — never on a concrete collaborator they could swap. The contract is designed first; implementations satisfy it. |
| 2 | **Command-Query Separation** | Queries never mutate; predicates never mutate; commands change state and report outcome. Accepted exceptions (e.g., atomic create-and-return of the new id) are documented per host, not accidental. |
| 3 | **Design by Contract** | Preconditions checked at entry; broken invariants fail fast as bugs; boundary inputs are validated as data (returned as validation failures, not crashes). |
| 4 | **Cohesive modules** | One unit of code owns one concern: one type per file, one resource per endpoint group, one job per worker/scene/module — per the host's granularity conventions. |
| 5 | **Self-sufficient packages** | A component ships with everything needed to adopt it: its wiring/registration, its configuration surface, its docs. Adding it never requires editing its internals. |
| 6 | **Result-style handling for expected failures** | Failures that are part of the domain contract travel as values/states the caller must handle; see the failure-class table. |

## The failure-class table (tenet 6 — decide by class, not by habit)

| Failure class | Treatment | Examples |
|---|---|---|
| **Expected business failure** | Return/emit it as a value or state the caller handles — it is part of the contract | "email already registered", validation errors, invalid state transition |
| **Programmer error** | Fail fast — this is a bug; surface it loudly at the point of breakage | null/absent required argument, broken invariant, impossible enum branch |
| **Infrastructure failure** | Raise at source; catch at the boundary; convert to the user-facing idiom with a correlation id; log full detail privately | storage/network timeout, external service down |

Why both directions matter: treating expected failures as crashes pollutes every caller
with recovery scaffolding and defeats type/flow tracking; treating bugs as handleable
values hides them behind ignorable results.

The concrete mechanisms (result object, error tuple, exception policy, error signal +
fallback state, …) are named by the host's stack contract — the classification above is
what the kit's agents enforce.

## See Also

- `unix-philosophy.md` — "fail noisily" is the loud half of the failure-class table
- `stack-contract-protocol.md` — where each tenet's concrete idiom is answered
- [agents/solution-designer.md](../agents/solution-designer.md) — designs are checked against these tenets
