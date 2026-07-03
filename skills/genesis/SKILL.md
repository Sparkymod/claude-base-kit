---
name: genesis
description: "Bootstrap the current project with the claude-base-kit: installs the role agents, principles, pipeline and templates into .claude/ (never overwriting local files), auto-detects the stack from repo evidence to pre-fill the stack contract, and wires CLAUDE.md orchestration. Use as the FIRST command in any project without the kit — triggers: /genesis, 'instala el base kit', 'bootstrap this project with the kit', 'inicializa el .claude'."
---

# genesis — bootstrap a project with the claude-base-kit

Run from the root of the host project (the current working directory). The outcome: a
working `.claude/` with the kit installed, a stack contract pre-filled from evidence, and
orchestration wired — ready for the `sdlc-feature` pipeline.

## Guard

If the current directory IS the kit repo (its README titles `claude-base-kit`), stop:
the kit is not a host. If `.claude/rules/stack-contract.md` already exists AND is filled
(no `{…}` placeholders), report "already bootstrapped" and offer only the update path
(step 2 re-run).

## Step 1 — Locate (or fetch) the kit

1. Preferred local clone: `~/source/repos/claude-base-kit`
   (Windows: `C:\Users\<user>\source\repos\claude-base-kit`). If present, refresh
   best-effort with `git pull --ff-only` (offline failure is non-fatal — use as-is).
2. If absent, clone `https://github.com/Sparkymod/claude-base-kit` to that path.
   If the clone fails (no access), signal BLOCKED naming the repo URL.

## Step 2 — Install

Run the kit installer against the project root and quote its output:

- Windows: `powershell -File <kit>/install/install.ps1 -Target <project-root>`
- POSIX: `sh <kit>/install/install.sh <project-root>`

The installer is idempotent and **never overwrites** — every "skipped (host file wins)"
line is a deliberate local override, not an error. Report installed/skipped counts.

## Step 3 — Pre-fill the stack contract from evidence

Open `.claude/rules/stack-contract.md` and fill it section by section using ONLY what the
repo evidences — never ecosystem assumptions. Detection signals, in priority order:

1. **Manifests:** `package.json` (scripts → build/test/run commands), `*.sln`/`*.csproj`,
   `project.godot`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `composer.json`, `Gemfile`,
   `Makefile`/`justfile` targets.
2. **CI workflows** (`.github/workflows/*`, other CI configs): the commands CI actually
   runs are the truest build/test answers.
3. **Existing docs:** README setup sections, CONTRIBUTING.
4. **Repo shape:** test directories and frameworks in lockfiles → test taxonomy; source
   layout → architecture section draft.

Rules:

- Mark every detected answer **`(auto-detected — confirm)`**.
- A command is only written if evidenced (a script entry, a CI step, a documented
  command). No evidence → leave the section with its `{…}` placeholder and add it to the
  pending list. **Never invent a command.**
- Sections that clearly don't apply (UI in a headless lib, persistence in a stateless
  tool) → propose `N/A` with one-line reasoning, also marked for confirmation.

## Step 4 — Wire CLAUDE.md

- **No root `CLAUDE.md`:** create one from the inner block of
  `.claude/templates/CLAUDE.skeleton.md`, substituting the detected verification commands
  and listing the six kit agents in the catalog.
- **Existing `CLAUDE.md`:** do NOT rewrite it. Append/merge only what's missing — the
  task-classification block, the agent catalog rows for the kit agents, and a pointer to
  the stack contract — preserving all existing content and its authority order. Show the
  proposed additions before applying if the file has a custom structure.

## Step 5 — Report and confirm (single batched message)

End with ONE message containing:

1. Install summary: installed / skipped counts (skips = local overrides).
2. Contract status table: per section → `auto-detected (value)` | `pending` | `proposed N/A`.
3. The batched confirmation request: "confirm the auto-detected answers, provide the
   pending ones" — listing them explicitly.
4. Next steps: feature-sized work runs `.claude/pipelines/sdlc-feature.md`; local lessons
   go to `.claude/lessons/`; universal lessons get promoted upstream to the kit repo.

Per the kit's `dispatch-status-signals` principle: batch ALL questions here — never a
drip of one-question turns. Until the human confirms, the contract remains draft and
kit agents treat unconfirmed sections as missing (they BLOCK on them).
