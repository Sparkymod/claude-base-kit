# CLAUDE.md — maintaining the claude-base-kit itself

This repo IS the product: a stack-agnostic knowledge kit. These rules gate every change here.

## The agnosticism gate (non-negotiable)

Before committing any artifact change, check every line against:

> **No artifact in `core/` may name a language, framework, runtime, package manager, build
> tool, test framework, database, engine, or concrete type.**

- ❌ "run `dotnet test`", "MediatR handler", "npm", "AggregateRoot", "GDScript", "xUnit"
- ✅ "run the test command named by the stack contract", "the host's error-result idiom"

**Single exception:** illustrative example rows that are explicitly labeled as examples of
*host answers* (e.g., inside `templates/stack-contract.md` or a "for example, a host might
answer…" clause). Examples must always show ≥2 different stacks so no single stack reads as
the default.

## Artifact hygiene

- **1 file = 1 unit of knowledge.** No omnibus files.
- **English only** — agents consume these files.
- **No broken references.** Everything an artifact cites (principle, template, agent) must
  exist in this repo. Citing host-side files is allowed only via the defined interface
  points: `.claude/rules/stack-contract.md`, `.claude/lessons/`, host `CLAUDE.md`.
- **Honest counts.** Any doc citing inventory counts states counts of actual files —
  count them, never infer from another doc.
- **README inventory** stays in sync with the file tree in the same commit.

## Structure contract

```
core/principles/   how agents work (governance + design) — no roles, no stacks
core/agents/       role agents — frontmatter: name, description, tools only
core/pipelines/    multi-agent workflows wiring the roles
core/templates/    fill-in artifacts copied to hosts
install/           idempotent, never-overwrite installers (ps1 + sh, feature parity)
```

- Agent frontmatter stays minimal (`name`, `description`, `tools`) for maximum
  Claude Code compatibility across versions and hosts. No `model`, no `skills:` refs.
- Both installers must keep feature parity — a change to one edits the other in the same commit.

## Verification before "done"

- Grep `core/` for stack vocabulary after editing (the agnosticism gate above).
- Follow every relative link you touched; confirm the target exists.
- If you changed installer behavior, run it against a scratch directory and quote the output.

## Relationship to host projects

Hosts consume this kit read-only via `install/`. The kit never depends on any host.
Knowledge flows upstream only as universal lessons (see
`core/principles/knowledge-evolution.md` § Upstream promotion).
