---
name: Knowledge Evolution
description: "How a host's knowledge base discovers, captures, validates and retires knowledge: discovery triggers, the lesson → rule → skill/command promotion ladder, demotion rules, inventory-count honesty, and upstream promotion of universal lessons to the base kit. Operated by the knowledge-curator agent."
---

# Knowledge Evolution

A knowledge base is not static. Knowledge flows through a deliberate lifecycle so the KB
stays true to the codebase instead of decaying into folklore.

## The promotion ladder

```
observation (session)  →  lesson  →  rule  →  skill / command
                          1 file     always-apply   executable recipe
```

| Stage | Enters when | Lives in (host repo) |
|---|---|---|
| **Lesson** | A real incident: bug, surprising failure, verified decision. Never speculation. | `.claude/lessons/` — what happened → root cause → rule going forward ([template](../templates/lesson.md)) |
| **Rule** | The same lesson repeats (2+) or a convention must gate every change | `.claude/rules/` — short, imperative, always-apply |
| **Skill** | A rule grows a reusable recipe with decisions/gotchas worth teaching | `.claude/skills/<name>/SKILL.md` |
| **Command** | The recipe is executable as a deterministic N-step flow | `.claude/commands/` |

Promotion is conservative: improving an existing artifact beats minting a near-duplicate.

## Discovery triggers

1. **Agent observation** — a pattern/anti-pattern/gap the KB doesn't encode.
2. **User correction** — behavior corrected or a better approach shown.
3. **Review recurrence** — the same finding in 2+ reviews → codify as rule (and if the
   host has executable convention checks, mechanize it there too).
4. **Convention change in code** — the KB artifact describing it must change in the same PR.

## Capture protocol

1. Classify: lesson, rule amendment, skill, command, or correction to an existing artifact.
2. Corrections are applied **in place** — never a second artifact contradicting the first.
3. Quality gate: grounded in evidence (commit, test, file), links resolve, no references
   to other projects — a host KB serves its repo "as is".
4. Update the inventory (the host's KB index / CLAUDE.md catalog) — same PR.

## Demotion and deprecation

- An artifact describing a pattern that no longer exists is **retired with rationale**
  (git history is the archive — no "deprecated" corpses in the KB).
- If code contradicts an artifact: the code wins and the artifact is fixed — UNLESS the
  code violates a committed rule, which is a finding, not doc-drift.
- Two artifacts overlapping >50% → merge into one, redirect referrers.

## Upstream promotion (host → base kit)

A lesson/rule that names **no host type, tool, or convention** is universal — it belongs
to the base kit, not the host silo. The knowledge-curator flags such artifacts; the human
decides whether to PR them upstream to the kit repo. Direction matters: hosts pull the kit
via install; knowledge climbs upstream only through deliberate, reviewed promotion.

## Inventory count verification

Any doc citing counts ("18 skills, 7 agents…") states counts of **actual files** — count
them, never infer from another doc. Stale counts are how index files rot first.

## See Also

- [agents/knowledge-curator.md](../agents/knowledge-curator.md) — the operator of this lifecycle
- [templates/lesson.md](../templates/lesson.md) — the capture format
- `rationalization-prevention.md` — row 7: "formalize later" is pre-rejected; capture now
