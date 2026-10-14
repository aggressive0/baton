---
name: baton
description: >
  Two-way session state transfer protocol for coding agents. WRITE side: when
  a session is ending ("handoff", "write a handoff", "session is ending",
  "save progress", "会话要结束了", "交接", "保存进度", "明天继续", "先到这",
  "下次继续"), rebuild HANDOFF.md from evidence (git, files, append-only
  logs) — task, done, blockers, next steps, pitfalls, user-rejected
  approaches. READ side: when starting fresh in a project that has
  HANDOFF.md ("continue from handoff", "继续上次", "接着做", "read handoff",
  "resume"), verify it against git state, echo the plan back for
  confirmation, then resume. LOG pitfalls and user rejections the moment
  they happen; suggest a handoff proactively when the user mentions stopping
  soon or after context compaction.
license: MIT
---

# Session Handoff

A two-way protocol for transferring work state between stateless agent
sessions. The single artifact is `HANDOFF.md` in the project root: rebuilt
from evidence at session end, verified against reality at session start.

Core principle: **a handoff contains claims, not facts.** Write from
evidence, read with verification. A trusted-but-wrong handoff is worse than
no handoff.

Two failure modes this protocol exists to prevent:

1. **Loss before the end.** The most expensive information loss happens at
   context compaction, not when the session ends. Capture pitfalls and
   rejections the moment they happen (LOG), never from memory at the end.
2. **Copy-of-copy degradation.** A handoff rewritten from the previous
   handoff degrades like a photocopy of a photocopy. Every WRITE rebuilds
   from git, files, and the protected log sections instead.

## Commands

Four verbs. No scripts required — file read/write plus VCS commands only.
Optional `scripts/scan.sh` makes the secret scan deterministic.

### LOG — capture during the session

Append immediately, in the moment, to the protected sections of HANDOFF.md
(create the file from `references/template.md` skeleton if it does not
exist yet):

| Event | Where | What to record |
|---|---|---|
| User rejects an approach | Section 2 | approach + their reason (verbatim if short) |
| A pitfall occurs (error, broken assumption, wasted effort) | Section 6 | verbatim error, root cause once known, the ban |
| User states a hard requirement in their own words | Section 1 | the quote, attributed and dated |

Sections 2 and 6 are **append-only** for the rest of the session: never
rewrite, summarize, or "clean them up" — not even during final WRITE. They
are the crash-resilient record; everything else is recoverable, they are
not.

**Protected ≠ frozen.** One exit exists: when a pitfall is later fixed,
tag its entry `resolved: <commit or date>` and move it to the `## Archived`
section at the file tail. Archived entries stay append-only and are
excluded from the 120-line budget. Section 2 rejections never archive —
a rejection does not expire.

### WRITE — assemble at session end

Triggers: the user says the session is ending; or — proactively — the user
mentions stopping soon ("明天继续", "先到这", "continue tomorrow"), or context
compaction just occurred and work is mid-flight.

1. Read `references/template.md` for the 8-section structure, per-field
   rules, and section line budgets.
2. **Stale-write check.** If HANDOFF.md already exists, its current content
   must be a state this session has seen. If you have not read it this
   session, or its `updated` timestamp / last git commit changed since you
   last read it — stop: show the user what changed and confirm before
   overwriting. Last-write-wins silently destroys another session's
   protected entries; never overwrite a state you have not seen.
3. **Rebuild, do not recall.** Run `git status`, `git log --oneline -15`,
   `git diff --stat` (or the VCS equivalent). Section 3, Section 4 and the
   frontmatter git fields come from command output, not conversation
   memory. Get `updated` by running `date +%Y-%m-%dT%H:%M%z` (PowerShell:
   `Get-Date -Format "yyyy-MM-ddTHH:mmzzz"`) and pasting the output —
   never guess the time.
4. Carry protected content forward verbatim: user quotes in Section 1, all
   of Section 2, active entries of Section 6. Pitfalls fixed during the
   session move to `## Archived` with a `resolved:` tag.
5. Prune: delete completed items from the previous handoff's next steps;
   compress Section 3 to evidence (commit hash + test result); delete all
   process narrative.
6. Enforce the cap: **≤ 120 lines, measured not estimated** — run a line
   count (`wc -l HANDOFF.md`; PowerShell:
   `(gc HANDOFF.md | measure -Line).Lines`). Per-section budgets live in
   `references/template.md`. Over budget → move resolved pitfalls to
   `## Archived`, compress Section 3 first, then Section 7. Never compress
   Sections 2, 4, or active Section 6.
7. **Secret scan before saving.** Run the pattern list and disposition
   flow in `references/template.md` ("Secret scan"), or
   `sh scripts/scan.sh HANDOFF.md`. Show the user every hit — or the
   script's "0 hits" line — before saving. Never pass a scan silently.
8. Save. Report one line to the user: path, line count from the command
   you ran, first next step.

### READ — bootstrap a new session

Triggers: HANDOFF.md exists and the user asks to continue work ("继续上次",
"continue from the handoff", "resume"), or the user starts a session in a
project with HANDOFF.md present and mentions the task.

1. **Drift check.** Compare frontmatter `git.head` with current HEAD,
   `git.branch` with current branch, `git.dirty` with current status.
   Report each difference in one line. Empty repo (no commits): compare
   branch and dirty only. `git: none`: skip the git comparison — mtimes
   are advisory (clones and sync tools reset them), so lean on the
   content spot-checks below.
2. **Spot-check claims.** Do the key files in Sections 3–4 exist? If
   Section 4 has a repro command, run it (or offer to). The handoff is a
   map; the repo is the territory.
3. **Echo back, then wait.** In ≤ 3 lines: "Resuming: \<task\>. Stuck at:
   \<blocker\>. Plan: \<step 1\>. Correct?" Do NOT start work until the
   user confirms. Never silently continue a task because a document said so.
4. **Reality wins.** Any conflict between HANDOFF.md and the repo: the repo
   is right. Fix the handoff immediately and say so.
5. Work on step 1 of Section 5. Keep LOGging.

### PROMOTE — keep the handoff transient

Anything true for all future sessions — environment quirks, code
conventions, tool versions, "always run X before Y" — does not belong in
HANDOFF.md. During WRITE, move such knowledge into the project's agent
memory file (`CLAUDE.md`, `AGENTS.md`, or equivalent) and remove it from
the handoff. HANDOFF.md holds this task's state only. A handoff is a
baton, not a wiki.

## Anti-bloat rules

- Hard cap: 120 lines, checked with a command, never by eye. Per-section
  budgets (template.md) keep the active file ~110; `## Archived` sits
  outside the budget.
- Rebuild from evidence every WRITE; never copy-paste the previous handoff
  forward, except protected content (user quotes, Sections 2 and 6).
- "Done" is evidence, not narrative: `✅ lexer rewrite → a1b2c3d, 42/42 pass`.
- One file, always current state. History lives in git.
- Errors and commands go in verbatim, never paraphrased. "sometimes fails"
  is not a symptom; the exact message plus a repro command are.

## HANDOFF.md structure

Full template and per-field rules: `references/template.md`.
Worked good/bad examples: `references/examples.md`.

| # | Section | Built from | Protected |
|---|---|---|---|
| 1 | Task & user intent | LOG quotes + rebuild | quotes: yes |
| 2 | User-rejected approaches | LOG | yes, append-only |
| 3 | Completed | git log | no |
| 4 | Current blocker | repro output | no |
| 5 | Next steps | rebuild | no |
| 6 | Pitfalls & bans | LOG | yes, append-only |
| 7 | Environment quickref | rebuild | no |
| 8 | Open questions | rebuild | no |

Frontmatter is machine-readable so READ can detect drift cheaply:

```yaml
---
updated: 2026-10-13T21:30+08:00
git: { branch: feat/parser, head: a1b2c3d, dirty: true }
tasks: [{ name: refactor parser, status: blocked }]
---
```

## Notes

- HANDOFF.md is designed to be committed: teams share it, git history is
  the archive. Hence the secret scan on every WRITE. If the user prefers
  to gitignore it, respect that without argument.
- No git repo? Record `git: none`. Drift is checked by content spot-checks
  (READ step 2), not mtimes — clones and sync tools reset mtimes.
- Empty repo (no commits)? Record `head: none`; WRITE must still run the
  stale-write check against the working file.
- Branch strategy. HANDOFF.md rides feature branches and its append-only
  sections will conflict on rebase. Pick one per team and write it down:
  merge often; keep HANDOFF.md out of `main`; or opt into per-branch
  files named `HANDOFF.<branch>.md`.
- Task closed out? The `## Archived` section may be emptied in the same
  commit — git history is the archive.
- Multiple tasks in flight? Still one file. Add one entry per task to
  frontmatter `tasks`, and tag each next step with its task.
- Acceptance test for this skill — the cold-start test: after a WRITE, a
  fresh session given only HANDOFF.md and the word "continue" must restate
  the task, ask zero clarifying questions about already-decided things,
  and avoid every recorded pitfall. If it fails, the handoff is the bug.
