---
name: Stack Contract Protocol
description: "The portability mechanism of the kit: every role agent reads the host project's stack contract (.claude/rules/stack-contract.md) before producing any artifact, and never hardcodes stack vocabulary. Defines the contract's required sections, the bootstrap procedure when it is missing, and the precedence rules."
---

# Stack Contract Protocol

## Problem

An agent that says "run `dotnet test`" or "return a `Result<T>`" works in exactly one
ecosystem. An agent that says nothing about verification or error handling produces
unverifiable, non-idiomatic work. The resolution is **indirection**: the agent's procedure
is fixed and universal; every stack-specific decision is resolved by looking it up in a
contract the host project owns.

## The contract

One file in the host repo: **`.claude/rules/stack-contract.md`** (template:
[templates/stack-contract.md](../templates/stack-contract.md)). It answers, for THIS project:

| Section | Answers | Example answers (different hosts) |
|---|---|---|
| Identity | Name, domain, repo layout | "e-commerce API", "2D roguelike" |
| Languages & runtimes | What the code is written in | C# 13 / .NET 10 · TypeScript 5 / Node 22 · GDScript / Godot 4 |
| Build | The exact build command(s) | `dotnet build X.sln -c Release` · `npm run build` · (Godot: editor import + export templates) |
| Test | The exact test command(s) per suite | `dotnet test` · `npm test` / `npx playwright test` · GUT/GdUnit run command |
| Run | How to start the app locally | `dotnet run --project …` · `npm run dev` · `godot --path .` |
| Verification before done | What MUST pass + be quoted before claiming complete | build + all suites green · lint + typecheck + tests |
| Architecture & layering | The dependency rules of the codebase | Clean Architecture inward flow · Next.js app-router + services · scenes/autoload boundaries |
| Error-handling idiom | Expected-failure vs bug vs infrastructure treatment | result object · error tuple / thrown `AppError` · pushed error + fallback state |
| Naming | Casing, suffixes, file conventions | PascalCase types, `Async` suffix · camelCase, kebab-case files · snake_case |
| Validation | Where and how inputs are validated | annotations + helper · zod at the boundary · exported setters with guards |
| Persistence | How state is stored and accessed | ORM + repository · Prisma · save-file resources |
| UI | The UI system and its component rules | component library + patterns · design system + server components · scene/theme conventions |
| Doc idiom | The doc-comment format for public surface | XML docs · TSDoc/JSDoc · `##` doc comments |
| Glossary | Domain terms an outsider would misread | — |

A section that genuinely does not apply is marked `N/A` — never left blank (blank means
"nobody answered", `N/A` means "answered: not applicable").

## Agent obligations

1. **Read before producing.** Every kit agent reads the stack contract before its first
   artifact of a task. Its outputs use the contract's vocabulary, commands, and idioms.
2. **Never guess a command.** If the contract lacks the needed answer, the agent does NOT
   infer one from ecosystem familiarity — it follows the bootstrap procedure below.
3. **Never contradict the contract.** If an agent believes a contract answer is wrong
   (e.g., the build command fails), it reports the discrepancy and signals `NEEDS-REVIEW`
   — it does not silently substitute its own answer. The contract is fixed by the host,
   in the contract file, once — not worked around per task.
4. **Contracts over training priors.** When the contract's idiom differs from what is
   "usual" in that ecosystem, the contract wins. The host chose it deliberately.

## Bootstrap procedure (missing or incomplete contract)

When the contract file is absent or a required section is blank:

1. Copy [templates/stack-contract.md](../templates/stack-contract.md) to
   `.claude/rules/stack-contract.md` (if absent).
2. Fill ONLY what is mechanically discoverable from the repo (manifest files, CI configs,
   lockfiles, project files) — mark each such answer `(auto-detected — confirm)`.
3. Leave everything else blank and list the blanks.
4. Signal `STATUS: BLOCKED` naming the sections a human must confirm. Do not proceed with
   the original task on guessed answers.

## Precedence

```
host stack contract  >  host project KB (.claude/rules|skills)  >  this kit's principles
```

The kit's principles govern *process* (scope, verification, signals) and are not
overridable by the contract; the contract governs *stack substance* and is not overridable
by the kit. They cannot genuinely conflict — if they appear to, the artifact confusing
process with substance is the bug (report it).

## See Also

- [templates/stack-contract.md](../templates/stack-contract.md) — the fill-in template
- `orchestrator-verification-protocol.md` — verification commands come FROM the contract
- `dispatch-status-signals.md` — the BLOCKED signal used by the bootstrap procedure
