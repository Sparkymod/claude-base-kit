# Template: lesson

One file = one lesson, in the host's `.claude/lessons/`. Lessons record REAL incidents —
a bug, a surprising failure, a verified decision — never speculation
(`principles/knowledge-evolution.md`).

```markdown
---
name: {kebab-case-slug}
date: {YYYY-MM-DD}
trigger: {bug | surprising-failure | user-correction | review-recurrence | verified-decision}
---

# {One-line title stating the lesson, not the story}

## What happened

{2–5 lines. The observable incident: what was attempted, what actually occurred.
Include the error text / wrong output verbatim where short.}

## Root cause

{The actual mechanism — not the symptom. If unknown, say "not established" and what was
ruled out; a lesson with a guessed root cause is worse than none.}

## Rule going forward

{Imperative, testable. What to do differently next time — phrased so it could be lifted
verbatim into a rule file on promotion.}

## Evidence

{Commit / file / test / command output that grounds this — at least one.}
```

## Promotion path

Same lesson observed **2+ times** → promote to `.claude/rules/` (and mechanize it as an
executable check if the host has convention tests). Rule grows a reusable recipe → skill.
If the lesson names **no host type or tool**, flag it for upstream promotion to the base
kit (`knowledge-curator` § Permitted Action 6).
