---
name: engram-memory
description: "Persistent cross-session memory protocol over the Engram MCP server: session lifecycle (start → save proactively → summarize → end), PROJECT_NAME/SESSION_ID derivation, workspace discovery into an architecture baseline, structured What/Why/Where/Learned observations, topic-key upserts, a quality filter for what must never be saved, conflict handling when memory disagrees with the code, and progressive disclosure for token-efficient recall. Use at session start, after significant work (decisions, bugfixes, discoveries), after a context compaction, or when the user asks to remember or recall something — triggers: /engram-memory, 'guarda en memoria', 'qué recuerdas de', 'recupera el contexto', 'save this to memory'."
---

# Engram Persistent Memory

You have access to **Engram** persistent memory via MCP tools. This memory persists across ALL projects, sessions, and conversations.

**Requires** the `engram` MCP server connected to the session (tools named `mem_*`). If those tools are absent, say so and skip — never fake a save. Do not invent unavailable tools: use only the Engram MCP tools actually available in the current environment.

## CRITICAL — Session Variables

At the start of EVERY conversation, derive these two values and use them in ALL Engram tool calls:

- **PROJECT_NAME**: The workspace folder name, e.g. if workspace is `C:\Users\Rafamod\source\repos\Admin-panel`, then `PROJECT_NAME = "Admin-panel"`
- **SESSION_ID**: `{PROJECT_NAME}-{YYYY-MM-DD}`, e.g. `Admin-panel-2026-03-16`

**You MUST pass `project` and `session_id` to EVERY `mem_save`, `mem_session_summary`, `mem_save_prompt`, and `mem_capture_passive` call.** If you omit them, observations go to a "manual-save" bucket and are NOT linked to the project session.

Use:
- `scope: "project"` for codebase-specific facts, architecture, decisions, bugs, commands, setup, conventions, and domain logic.
- `scope: "personal"` only for cross-project user preferences, developer habits, reusable workflows, or global environment notes.

## Automatic Behavior

### On Session Start
1. Derive `PROJECT_NAME` from the workspace folder name.
2. Derive `SESSION_ID` as `{PROJECT_NAME}-{YYYY-MM-DD}`.
3. Call `mem_session_start` with `id=SESSION_ID`, `project=PROJECT_NAME`, `directory=<workspace path>`.
4. Call `mem_context` with `project=PROJECT_NAME` to recover previous session state.
5. Call `mem_search` with keywords related to the current task and `project=PROJECT_NAME`.

Never start cold if the task may have prior context.

## Workspace Discovery

Before making implementation decisions in a project, inspect the repository enough to avoid assumptions.

Check relevant files when present — these are recognition signals, not a required stack:

- Manifests and dependencies: `package.json`, `.csproj`/`*.sln`, `angular.json`, `nx.json`, `pom.xml`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`
- Build and tooling config: `tsconfig.json`, `next.config.*`, `vite.config.*`, `.github/workflows`, Azure DevOps pipeline files
- Infrastructure and environment: `docker-compose.*`, `appsettings*.json`, `.env.example`, deployment config
- Architecture signals: folder structure, naming conventions, state management, API patterns, data access style, test structure

After discovering durable stack or architecture facts, save/update an architecture baseline:

1. Call `mem_suggest_topic_key` for a topic like `architecture_baseline`.
2. Call `mem_save` with the suggested `topic_key`, `type: "architecture"`, `scope: "project"`, `project=PROJECT_NAME`, and `session_id=SESSION_ID`.

This baseline should be concise and should describe the current reality of the repo, not guesses.

## During Work — Save Proactively

Call `mem_save` immediately after significant work. **ALWAYS include these parameters**:
- `session_id`: the SESSION_ID from above
- `project`: the PROJECT_NAME from above
- `type`: one of `decision`, `architecture`, `bugfix`, `pattern`, `config`, `discovery`, `learning`
- `scope`: `"project"` for project-specific, `"personal"` for cross-project

Save after:
- **Decisions**: Architecture choices, technology selections, design patterns adopted
- **Bugfixes**: Root cause analysis, non-obvious fixes, workarounds
- **Discoveries**: Patterns, gotchas, user preferences, environment quirks
- **Config changes**: Build configs, environment variables, tool settings
- **Architecture baselines**: stack, frameworks, database/provider, deployment model, repo structure
- **Domain logic**: business rules, workflows, invariants, permissions, edge cases

Use structured content format:
```
What: [brief description]
Why: [reasoning]
Where: [files/modules affected]
Learned: [key takeaway]
```

Example call:
```
mem_save(
  title: "Fixed timezone bug in dashboard charts",
  content: "What: Fixed UTC date grouping...\nWhy: ...\nWhere: ...\nLearned: ...",
  type: "bugfix",
  session_id: "Admin-panel-2026-03-16",
  project: "Admin-panel",
  scope: "project"
)
```

### Topic Key Workflow
For evolving topics, use `mem_suggest_topic_key` first, then `mem_save` with that topic_key. Same topic_key = upsert (updates existing memory instead of creating duplicates).

Use topic keys for:

- Architecture baseline
- Authentication model
- Deployment process
- Database/provider conventions
- Testing strategy
- Project-specific UI/component patterns
- Repeated bug classes

## Memory Quality Filter

Memory should stay high-signal. Save durable knowledge, not noise.

Always save:

- Architecture decisions and tradeoffs
- Framework, database, deployment, and tooling facts
- Non-obvious bugfixes with root cause
- Reusable project patterns and conventions
- Complex domain rules
- Environment or setup gotchas that would save time later
- User preferences that apply across projects, using `scope: "personal"`

Never save:

- Secrets, tokens, passwords, private keys, or connection strings
- Full code dumps or large raw files
- Temporary command output with no lasting value
- Speculation stated as fact
- Simple syntax mistakes unless they reveal a reusable gotcha
- Large JSON payloads unless summarized into durable knowledge
- One-off status updates like "tests failed on step 3" without root cause

Also skip what the repo already records (code structure, git history) — memory is for the non-obvious: decisions, reasons, gotchas, preferences.

If saving a secret-related discovery, save only the mechanism, location pattern, or vault/config name. Never save the secret value.

## Conflict Handling

If memory conflicts with the current codebase, the current codebase is authoritative.

When this happens:

1. Verify the current repo state by reading the relevant files.
2. Search existing memories for the conflicting topic.
3. Save an updated observation with a stable `topic_key` using `mem_save` (or `mem_update`).
4. Mention that the previous memory is outdated if that matters for future agents.
5. Use `mem_delete` only when the old memory is actively harmful or contains sensitive/incorrect information.

## On Session Close

Before finishing any conversation:
1. Call `mem_session_summary` with `session_id=SESSION_ID`, `project=PROJECT_NAME`, and content with: goal, discoveries, accomplished, next steps, relevant files.
2. Call `mem_session_end` with `id=SESSION_ID`.

## After Context Reset / Compaction

If you detect a context reset or compaction:
1. Re-derive `PROJECT_NAME` and `SESSION_ID`.
2. Call `mem_context` with `project=PROJECT_NAME` to recover session state.
3. Call `mem_search` with current task keywords and `project=PROJECT_NAME`.
4. Continue from recovered context instead of restarting from scratch.

## Progressive Disclosure (Token-Efficient)
1. `mem_search "query"` → compact results with IDs
2. `mem_timeline observation_id=N` → what happened before/after
3. `mem_get_observation id=N` → full untruncated content

## Key Rules
- Save proactively, but only durable knowledge.
- ALWAYS pass `session_id` and `project` to `mem_save`.
- ALWAYS pass `session_id` and `project` to `mem_session_summary`.
- ALWAYS pass `project` to `mem_context` and task-related `mem_search`.
- Use `scope: "project"` for project-specific memories.
- Use `scope: "personal"` for cross-project preferences.
- Answer the user in their language (this operator's default is Spanish).
- Save memories in the language the content was produced in.
- Current code beats old memory when they disagree.
- ALWAYS check memory before starting work on a topic that might have prior context.

## Composes with

- **agent-in-the-loop** — each batch's baselines, outcomes, and FLAGs are saved per
  session so the next batch starts from evidence.
- **tareas-delegadas** — the anchor map, per-batch baselines and the named integration
  decisions are saved here, so planning batch N+1 is recall instead of archaeology.
- **patron-oro** — resolved checklist items leave the living document; their history
  lands here.
