# Stack Contract — {project name}

> **This file is the interface between this project and the base kit's role agents.**
> Every kit agent reads it before producing artifacts and uses ONLY these answers for
> stack-specific decisions (`principles/stack-contract-protocol.md`). Fill every section;
> write `N/A` where a section genuinely does not apply — never leave one blank.
> Illustrative answers below show DIFFERENT stacks on purpose; replace them all.

## Identity

- **Project:** {name and one-line purpose}
- **Domain:** {business/game/tooling domain}
- **Repo layout:** {top-level directories and what lives in each}

## Languages & runtimes

- {e.g., "TypeScript 5.x on Node 22 (API), Next.js 15 (web)" · "GDScript on Godot 4.3" · "C# 13 on .NET 10"}

## Build

- **Command(s):** {e.g., `npm run build` · `dotnet build X.sln -c Release` · "Godot editor import; export via `godot --headless --export-release …`"}

## Test

- **Suites & commands:** {one line per suite: name → command, e.g., "unit → `npm test`", "e2e → `npx playwright test`", "unit → GUT: `godot --headless -s addons/gut/gut_cmdln.gd`"}
- **Test taxonomy:** {what counts as unit / integration / e2e HERE, and where each lives}
- **Test-double idiom:** {mocking library / hand-rolled fakes / scene stubs}

## Run

- **Local run:** {e.g., `npm run dev` · `dotnet run --project …` · `godot --path .`}

## Verification before "done"

- {The exact command sequence that MUST pass — and be quoted — before any completion claim.}

## Architecture & layering

- {The dependency rules: layers/modules/scenes and the allowed direction. What may depend on what; what must stay free of what.}

## Error-handling idiom

- **Expected business failures:** {e.g., result object type · error tuple · error signal + fallback state}
- **Programmer errors:** {e.g., throw/assert immediately}
- **Infrastructure failures:** {boundary where they are caught and converted; correlation id convention}

## Naming

- {Casing per element kind, async suffixes, file naming, test naming — the deltas from ecosystem defaults matter most.}

## Validation

- {Where inputs are validated and with what, e.g., "zod schemas at route boundary" · "annotations + validator helper" · "exported setters with guards"}

## Persistence

- {How state is stored and accessed; the abstraction agents must code against; anything they must never do directly. `N/A` if stateless.}

## UI

- {UI system, component conventions, the sanctioned patterns for new screens/scenes. `N/A` if headless.}

## Doc idiom

- {Doc-comment format for public surface (TSDoc, XML docs, docstrings, `##` comments) + docs directory layout.}

## Interruption/cancellation idiom

- {e.g., `AbortSignal` · `CancellationToken` · context cancellation · "N/A — synchronous frame-based"}

## Glossary

- {Domain terms an outsider would misread — one line each.}
