# claude-base-kit

> A portable, **stack-agnostic** knowledge kit for Claude Code: role agents, governance
> principles, an SDLC pipeline, and templates that work in ANY project — a .NET solution,
> a Node.js/Next.js app, a Godot game, a Python service. The kit knows *how to work*;
> the host project tells it *what the stack is*.

## The idea in one paragraph

Most `.claude/` knowledge bases mix two kinds of knowledge: **universal** (how agents stay in
scope, how work is verified, how requirements become designs become code) and **project-bound**
(this codebase's types, commands, conventions). This kit contains ONLY the first kind. The
second kind stays in each host project, expressed through one file — the **stack contract**
(`.claude/rules/stack-contract.md`) — that every kit agent reads before producing anything.
The role is fixed; the vocabulary is the host's.

## The three layers

| Layer | Lives in | Contains | Example |
|---|---|---|---|
| **0 — Core (this repo)** | `claude-base-kit` | Role agents, governance principles, SDLC pipeline, templates | `requirements-analyst`, scope-enforcement, `sdlc-feature` |
| **1 — Stack contract** | Host repo, one file | The host's answers: build/test/run commands, layering, error idiom, naming | "build: `npm run build`", "errors: `Result<T,E>` from neverthrow" |
| **2 — Project KB** | Host repo `.claude/` | Project-specific skills, agents, rules the host team writes | A CRUD scaffolder for that codebase |

**Boundary rule:** if an artifact names a language, framework, build tool, or concrete type,
it does NOT belong in this kit — it belongs in a host's stack contract or project KB.
Nothing exists in two layers at once.

## Contents

```
core/
├── principles/   8 governance & design principles (the "how we work" layer)
│   ├── stack-contract-protocol.md        ← the portability mechanism (start here)
│   ├── scope-enforcement-protocol.md     ← hard-scoped agents: whitelist + scripted refusal
│   ├── rationalization-prevention.md     ← pre-rejected excuses table
│   ├── orchestrator-verification-protocol.md ← claims are not evidence; two-layer verification
│   ├── dispatch-status-signals.md        ← STATUS signals + artifact contracts between stages
│   ├── knowledge-evolution.md            ← lesson → rule → skill ladder; upstream promotion
│   ├── core-design-tenets.md             ← interface-first, CQS, contracts, failure classes
│   └── unix-philosophy.md                ← one thing well, composition, policy/mechanism
├── agents/       6 role agents (SDLC stages — no stack vocabulary anywhere)
│   ├── requirements-analyst.md           ← raw request → testable requirements + traceability
│   ├── solution-designer.md              ← requirements → ADRs, contracts, scaffold directives
│   ├── code-implementer.md               ← design → code (scaffold + implement modes)
│   ├── test-designer.md                  ← requirements → test plan, cases, shells
│   ├── technical-writer.md               ← approved artifacts → human documentation
│   └── knowledge-curator.md              ← keeps the host KB honest; audits doc-drift
├── pipelines/
│   └── sdlc-feature.md                   ← the stages wired together, with hard gates
└── templates/
    ├── stack-contract.md                 ← the fill-in contract every host completes
    ├── agent-shape.md                    ← canonical skeleton for writing new agents
    ├── CLAUDE.skeleton.md                ← orchestration CLAUDE.md starter for a host
    └── lesson.md                         ← local knowledge capture format
install/
├── install.ps1                           ← copy the kit into a host repo (Windows)
└── install.sh                            ← same (POSIX)
skills/
├── genesis/SKILL.md                      ← global /genesis skill: install + auto-fill contract + wire CLAUDE.md
├── analyze/SKILL.md                      ← global /analyze skill: extract an existing codebase into Analyze.md (evidence-backed)
├── usecases/SKILL.md                     ← global /usecases skill: reverse-engineer implemented use cases into UseCases.md
├── agent-in-the-loop/SKILL.md            ← global /agent-in-the-loop skill: parallel scoped delegation with the orchestrator as in-loop reviewer
├── patron-oro/SKILL.md                   ← global /patron-oro skill: polish 1 → replicate N (gold-pattern content/system methodology)
└── engram-memory/SKILL.md                ← global /engram-memory skill: persistent cross-session memory protocol (requires the Engram MCP server)
```

## Install into a project

**Recommended — the `/genesis` skill.** Copy the folders under `skills/` to your
user-level skills directory once (`~/.claude/skills/`). From then on, in ANY project, run
`/genesis` as the first command: it locates/fetches this kit, runs the installer,
**auto-fills the stack contract from repo evidence** (manifests, CI, docs — marked
`auto-detected — confirm`), wires `CLAUDE.md`, and ends with one batched confirmation.

**For already-built (brownfield) projects**, `/genesis` additionally runs two sibling
extraction skills as its final bootstrap step: `/analyze` writes an evidence-backed
`Analyze.md` (stack, structure, entry points, domain, integrations, patterns, tests,
gaps — every claim cites a file), then `/usecases` writes `UseCases.md` (the use cases
the code actually implements, with a coverage table proving no entry point was dropped).
Both are also standalone skills — re-run them anytime to refresh the docs; `/usecases`
consumes `/analyze`'s entry-point inventory.

**Manual — the installers:**

```powershell
# Windows
.\install\install.ps1 -Target C:\path\to\your-project

# POSIX
./install/install.sh /path/to/your-project
```

The installer copies `core/` content into the host's `.claude/`, **never overwrites an
existing file** (the project always wins on name collisions), seeds
`.claude/rules/stack-contract.md` from the template if absent, and creates `.claude/lessons/`.

Then, in the host project:

1. **Fill the stack contract** — `.claude/rules/stack-contract.md`. Ten minutes; every kit
   agent depends on it. An agent asked to work without a filled contract will bootstrap a
   draft from the repo and signal `BLOCKED` until you confirm it.
2. **Wire orchestration** — if the host has no `CLAUDE.md`, start from
   `.claude/templates/CLAUDE.skeleton.md`.
3. Work normally. For feature-sized tasks, the `sdlc-feature` pipeline routes
   requirements → design → implementation → tests → docs through the role agents.

## Updating a host

Re-run the installer: new kit files are added, existing host files are untouched. Review the
skip list it prints — a skipped file means the host has a local override, which is intentional.

## Contributing knowledge back (upstream)

When a host project captures a lesson that names **no host type or tool**, it is universal —
promote it to this repo via PR instead of leaving it siloed (see
`core/principles/knowledge-evolution.md` § Upstream promotion).

## What this kit deliberately does NOT contain

- Stack-specific skills (caching for EF Core, React hooks patterns, GDScript idioms…) —
  layer 1/2 material.
- Code generators — generation requires stack vocabulary; hosts own their generators.
- A code-review agent for style — style is the host's contract, not the kit's.
