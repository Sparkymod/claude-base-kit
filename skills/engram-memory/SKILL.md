---
name: engram-memory
description: "Persistent cross-session memory protocol over the Engram MCP server: session lifecycle (start → save proactively → summarize → end), PROJECT_NAME/SESSION_ID derivation, workspace discovery into an architecture baseline, structured What/Why/Where/Learned observations, topic-key upserts, a quality filter for what must never be saved, conflict handling when memory disagrees with the code, and progressive disclosure for token-efficient recall. Use at session start, after significant work (decisions, bugfixes, discoveries), after a context compaction, or when the user asks to remember or recall something — triggers: /engram-memory, 'guarda en memoria', 'qué recuerdas de', 'recupera el contexto', 'save this to memory'."
---

# engram-memory — persistent memory protocol (Engram MCP)

**Requires** the `engram` MCP server connected to the session (tools named `mem_*`).
If the tools are absent, say so and skip — never fake a save, and never invent a `mem_*`
tool that this environment does not actually expose.

Memory persists across ALL projects, sessions, and conversations. The protocol below is
what makes it useful instead of a junk drawer: every observation is attributed to a
project + session, structured, filtered for signal, and deduplicated via topic keys.

## Session variables (derive ONCE per conversation)

- **PROJECT_NAME** = the workspace folder name (e.g. workspace `…/repos/Admin-panel`
  → `Admin-panel`).
- **SESSION_ID** = `{PROJECT_NAME}-{YYYY-MM-DD}` (e.g. `Admin-panel-2026-03-16`).

Pass `project` and `session_id` to EVERY `mem_save`, `mem_session_summary`,
`mem_save_prompt`, and `mem_capture_passive` call. Omitting them strands the observation
in a "manual-save" bucket disconnected from the project's timeline.

`scope` is a separate axis from `project`: `project` for codebase-bound facts
(architecture, decisions, bugs, commands, setup, conventions, domain logic), `personal`
only for cross-project preferences, habits, reusable workflows, global environment notes.

## Lifecycle

**On session start**
1. `mem_session_start` with `id=SESSION_ID`, `project=PROJECT_NAME`, `directory=<path>`.
2. `mem_context` with `project=PROJECT_NAME` — recover where the last session left off.
3. `mem_search` with keywords of the current task and `project=PROJECT_NAME`.

Never start cold on a task that may have prior context.

**During work — save proactively, don't wait to be asked.** Call `mem_save` right after:
architectural decisions and their tradeoffs, bugfixes (root cause + fix), non-obvious
discoveries or gotchas, new conventions, config/environment changes, and domain logic
(business rules, workflows, invariants, permissions, edge cases). Always include `type`
(one of `decision`, `architecture`, `bugfix`, `pattern`, `config`, `discovery`,
`learning`) and `scope`. Structure the content:

```
**What**: [what was done]
**Why**: [the reasoning or problem that drove it]
**Where**: [files/modules affected]
**Learned**: [gotchas, edge cases — omit if none]
```

```
mem_save(
  title: "Fixed timezone bug in dashboard charts",
  content: "**What**: …\n**Why**: …\n**Where**: …\n**Learned**: …",
  type: "bugfix",
  session_id: "Admin-panel-2026-03-16",
  project: "Admin-panel",
  scope: "project"
)
```

**On session close**
1. `mem_session_summary` (`session_id`, `project`, content: goal / discoveries /
   accomplished / next steps / relevant files).
2. `mem_session_end` with `id=SESSION_ID`.

**After a context reset or compaction** — re-derive the session variables, then
`mem_context` (`project`) + `mem_search` for the current task, and continue from what
came back instead of restarting. This is the recovery path; memory exists so compaction
loses nothing that mattered.

## Workspace discovery → architecture baseline

Before making implementation decisions in an unfamiliar project, read enough of the repo
to stop guessing. Look at whatever is present — these are recognition signals, not a
required stack:

- **Manifests and dependencies** — e.g. `package.json`, `*.sln`/`*.csproj`,
  `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `composer.json`.
- **Build and tooling config** — the compiler/bundler/test config, and the CI definitions
  (e.g. `.github/workflows/`, a pipelines file) — these name the real commands.
- **Infrastructure and environment** — container/compose files, app settings, `.env`
  examples, deployment manifests.
- **Architecture signals** — folder structure, naming conventions, state management, API
  shape, data-access style, test layout.

Then persist it once, not per session: `mem_suggest_topic_key` for something like
`architecture_baseline`, then `mem_save` with that `topic_key`, `type: "architecture"`,
`scope: "project"`, plus `project` and `session_id`. Keep it concise and describe the
repo's current reality, never guesses. Later sessions update the same key instead of
re-deriving the map.

**Evolving topics** — always `mem_suggest_topic_key` first, then `mem_save` with that
`topic_key`: same key = upsert (the topic stays ONE observation instead of N duplicates).
Worth a topic key: architecture baseline, authentication model, deployment process,
data-layer conventions, testing strategy, project UI/component patterns, recurring bug
classes.

## Quality filter — what earns a memory

Memory stays useful only while it stays high-signal.

**Save**: architecture decisions and tradeoffs · stack, data-layer, deployment and
tooling facts · non-obvious bugfixes *with root cause* · reusable patterns and
conventions · complex domain rules · environment/setup gotchas that will cost time again
· cross-project user preferences (as `scope: "personal"`).

**Never save**: secrets, tokens, passwords, keys, connection strings · code dumps or
whole files · command output with no lasting value · speculation stated as fact · simple
syntax slips that reveal no reusable gotcha · large payloads that were never distilled ·
status lines like "tests failed on step 3" without the root cause.

For a secret-adjacent discovery, save the **mechanism, location pattern, or vault/config
name** — never the value.

## Conflict handling — the code wins

When a memory disagrees with the current codebase, the codebase is authoritative.

1. Verify the repo's current state by reading the relevant files.
2. `mem_search` the conflicting topic for every observation that carries the stale claim.
3. `mem_save` the corrected observation under a stable `topic_key` (upsert, not a new
   duplicate that leaves both versions alive).
4. Say that the old memory was outdated when a future agent would otherwise trust it.
5. `mem_delete` only when the old memory is actively harmful, sensitive, or plainly wrong
   — a superseded-but-harmless memory is history, not garbage.

## Progressive disclosure (token-efficient recall)

1. `mem_search "query"` → compact hits with IDs — start here, always.
2. `mem_timeline observation_id=N` → what happened around that observation.
3. `mem_get_observation id=N` → full untruncated content — only when needed.

## Rules

- Check memory BEFORE starting work on a topic that might have prior context.
- ALWAYS pass `session_id` + `project` to `mem_save` and `mem_session_summary`, and
  `project` to `mem_context` and task-related `mem_search`.
- Save proactively — but only durable knowledge (see the quality filter).
- Save in the language the content is written in; answer the user in their language.
- Don't save what the repo already records (code structure, git history) — save the
  non-obvious: decisions, reasons, gotchas, preferences.
- Current code beats old memory when they disagree; fix the memory the moment you notice.

## Composes with

- **agent-in-the-loop** — each batch's baselines, outcomes, and FLAGs are saved per
  session so the next batch starts from evidence.
- **tareas-delegadas** — the anchor map, per-batch baselines and the named integration
  decisions are saved here, so planning batch N+1 is recall instead of archaeology.
- **patron-oro** — resolved checklist items leave the living document; their history
  lands here.
