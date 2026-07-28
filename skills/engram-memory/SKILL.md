---
name: engram-memory
description: "Persistent cross-session memory protocol over the Engram MCP server: session lifecycle (start → save proactively → summarize → end), PROJECT_NAME/SESSION_ID derivation, structured What/Why/Where/Learned observations, topic-key upserts, and progressive disclosure for token-efficient recall. Use at session start, after significant work (decisions, bugfixes, discoveries), after a context compaction, or when the user asks to remember or recall something — triggers: /engram-memory, 'guarda en memoria', 'qué recuerdas de', 'recupera el contexto', 'save this to memory'."
---

# engram-memory — persistent memory protocol (Engram MCP)

**Requires** the `engram` MCP server connected to the session (tools named `mem_*`).
If the tools are absent, say so and skip — never fake a save.

Memory persists across ALL projects, sessions, and conversations. The protocol below is
what makes it useful instead of a junk drawer: every observation is attributed to a
project + session, structured, and deduplicated via topic keys.

## Session variables (derive ONCE per conversation)

- **PROJECT_NAME** = the workspace folder name (e.g. workspace `…/repos/Admin-panel`
  → `Admin-panel`).
- **SESSION_ID** = `{PROJECT_NAME}-{YYYY-MM-DD}` (e.g. `Admin-panel-2026-03-16`).

Pass `project` and `session_id` to EVERY `mem_save`, `mem_session_summary`,
`mem_save_prompt`, and `mem_capture_passive` call. Omitting them strands the observation
in a "manual-save" bucket disconnected from the project's timeline.

## Lifecycle

**On session start**
1. `mem_session_start` with `id=SESSION_ID`, `project=PROJECT_NAME`, `directory=<path>`.
2. `mem_context` with `project=PROJECT_NAME` — recover where the last session left off.
3. `mem_search` with keywords of the current task — check for prior context BEFORE
   starting work on any topic that might have history.

**During work — save proactively, don't wait to be asked.** Call `mem_save` right after:
architectural decisions, bugfixes (root cause + fix), non-obvious discoveries or gotchas,
new conventions, config/environment changes. Always include `type` (one of `decision`,
`architecture`, `bugfix`, `pattern`, `config`, `discovery`, `learning`) and `scope`
(`project` for project-bound facts, `personal` for cross-project preferences). Structure
the content:

```
**What**: [what was done]
**Why**: [the reasoning or problem that drove it]
**Where**: [files/modules affected]
**Learned**: [gotchas, edge cases — omit if none]
```

**Evolving topics** — call `mem_suggest_topic_key` first, then `mem_save` with that
`topic_key`: same key = upsert (the topic stays ONE observation instead of N duplicates).

**On session close**
1. `mem_session_summary` (`session_id`, `project`, content: goal / discoveries /
   accomplished / next steps / relevant files).
2. `mem_session_end` with `id=SESSION_ID`.

**After a context reset or compaction** — `mem_context` + `mem_search` for the task,
re-derive the session variables, continue. This is the recovery path; memory exists so
compaction loses nothing that mattered.

## Progressive disclosure (token-efficient recall)

1. `mem_search "query"` → compact hits with IDs — start here, always.
2. `mem_timeline observation_id=N` → what happened around that observation.
3. `mem_get_observation id=N` → full untruncated content — only when needed.

## Rules

- Check memory BEFORE starting work on a topic that might have prior context.
- Save in the language the content is written in; answer the user in their language.
- Don't save what the repo already records (code structure, git history) — save the
  non-obvious: decisions, reasons, gotchas, preferences.
- Wrong memory found → update or delete it (`mem_update`/`mem_delete`); stale memory is
  worse than none.

## Composes with

- **agent-in-the-loop** — each batch's baselines, outcomes, and FLAGs are saved per
  session so the next batch starts from evidence.
- **tareas-delegadas** — the anchor map, per-batch baselines and the named integration
  decisions are saved here, so planning batch N+1 is recall instead of archaeology.
- **patron-oro** — resolved checklist items leave the living document; their history
  lands here.
