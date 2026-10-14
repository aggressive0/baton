# HANDOFF.md template and field rules

The active `HANDOFF.md` must contain **120 lines or fewer in total**, including
frontmatter, headings, and blank lines. Resolved pitfall history belongs in the
separate, optional `HANDOFF.archive.md`; do not append an unbounded archive to
the active handoff.

## Skeleton

Copy this skeleton and replace every placeholder. Keep the eight numbered
sections in this order.

```markdown
---
schema_version: 2
updated: "<actual ISO-8601 timestamp from system command>"
git:
  branch: <branch-or-none>
  head: <short-hash-or-none>
  dirty: <true-or-false>
  scope: "snapshot before handoff write"
captured: log
tasks:
  - id: TASK-001
    name: <short task name>
    status: active
---

# 1. Task & user intent
<2-4 lines: what is being built and why it matters>
> "<exact user requirement>" — user, <date>

# 2. User-rejected approaches
- ❌ <approach> — rejected <date>: <reason>

# 3. Completed / claims
- [verified] ✅ <claim> → <file-or-commit>; evidence: `<command>` → <result>; scope: <commit/state>
- [reported] <historical claim>; evidence: <report/log>; not rechecked in this WRITE

# 4. Current blocker
- Status: <blocked|none>
- Symptom: <verbatim, untruncated error or observed behavior>
- Location: <file:line or search scope>
- Repro / evidence: `<exact command>` → <observed result>

# 5. Next steps
1. <action> → expected: <observable result>; verify: `<command>`

# 6. Pitfalls & bans
- [pitfall] <date> <symptom> — root cause: <cause|unknown>. Ban: <prevention rule>

# 7. Environment quickref
- Test: `<command>` · Build: `<command>` · Run: `<command>`
- <task-relevant version/OS constraint not yet promoted>

# 8. Open questions / PROMOTE candidates
- <unanswered question or candidate + destination + decision pending>
```

## Frontmatter rules

- `schema_version`: use `2` for this template. If the format later changes,
  increment the version and document migration in `CHANGELOG.md`.
- `updated`: paste the output of a clock command; do not guess. POSIX:
  `date +%Y-%m-%dT%H:%M%z`; PowerShell:
  `Get-Date -Format "yyyy-MM-ddTHH:mmzzz"`; portable fallback:
  `python -c "import datetime;print(datetime.datetime.now().astimezone().isoformat())"`.
- `git.branch`, `git.head`, and `git.dirty` must come from actual commands.
  For a non-Git directory, use `branch: none`, `head: none`, and `dirty: false`
  with `scope: "no Git repository; file checks only"`.
- `git.dirty` records the state observed **before the handoff write**. State
  the scope because saving the handoff itself can change Git status.
- `captured` is `log` only if protected entries were actually appended during
  the current session and their persistence was checked. Otherwise use
  `reconstructed`. Do not infer capture history from how polished the file is.
- Use one `tasks` entry per in-flight task. `status` must be `active`, `blocked`,
  `review`, or `done`. A done task must not have active next steps unless the
  task is explicitly reopened.
- The validator checks required headings, frontmatter basics, timestamps,
  placeholders, and line count. It does not validate the truth of natural-language
  claims or fully parse arbitrary YAML.

## Section rules

### 1. Task & user intent [user quotes protected]

- State what is being built and why, not the entire process history.
- Keep hard requirements in the user's original wording whenever practical.
  Attribute quotes and add the date. Do not turn an ambiguous paraphrase into a
  stricter requirement than the user actually gave.
- Do not store credentials, secrets, private customer details, or unnecessary
  personal information. Redact and keep only the requirement that matters.

### 2. User-rejected approaches [append-only]

- Record approach, reason, and date as close to the event as possible.
- Do not delete a rejection because a later decision changes. Append a dated
  reversal and label which decision is current. A newer explicit user
  instruction supersedes an older instruction when they conflict.
- Do not archive this section merely because an approach is old; task context
  may make the decision relevant again.

### 3. Completed / claims [evidence status required]

- `verified`: checked in this WRITE, with evidence and a scope that can be
  identified (commit, file state, command output, test report, or external result).
- `reported`: a historical record supports the claim, but it was not checked now.
- `unverified`: claimed in conversation/memory without adequate evidence.
- `blocked`: verification was attempted or is needed but cannot be completed;
  state the reason and a concrete verification action.
- A successful test applies to the tested code state. If relevant files changed
  after the test, rerun it before marking the current state verified.
- Git does not prove external uploads, deployments, remote mutations, or
  business outcomes. Use the external system's result or mark the claim pending.
- Numbers must come from command output or artifacts, never model memory.
- Prefer one line per claim. Remove session narrative during rebuild.

### 4. Current blocker [retain evidence]

- If there is no blocker, write `Status: none` and omit the other fields.
- Record the exact error/output, file and line if available, and the command or
  search scope that produced the finding. Do not paraphrase the only copy of an
  error message.
- For a missing file or absent result, state where and how it was searched.
  Mark similarly named or unrelated files if a successor could confuse them.
- Do not run destructive reproductions just to fill this section. If reproduction
  is unsafe, unavailable, or expensive, state that plainly.

### 5. Next steps [must be actionable]

- Order steps by priority. Each step includes an action, observable expected
  result, and verification method. A step without a verification method is a
  wish, not an executable next step.
- Use commands that work in the next session's shell, or label the required
  shell (for example `PowerShell 7`, `git-bash`, or `POSIX sh`). Prefer portable
  commands where practical.
- Delete completed steps; carry forward unfinished steps only after checking
  they remain relevant. Add dependencies inline, such as `前置: step 1 passes`.
- A prerequisite disguised as an open question is a task. Upgrade it to a
  verification step or cross-reference it from the step it gates.
- Do not refer only to another machine's path. Inline essential content or label
  it `[local-only]` and include an alternative to recover it.

### 6. Pitfalls & bans [active entries append-only]

- Record the symptom/error first, even if the root cause is unknown. Add the
  cause and prevention rule later as a new note or explicit update that does not
  erase the original symptom.
- Keep active entries verbatim during the task. Split any to-do hidden in a
  pitfall into Section 5 and cross-reference it.
- A pitfall resolved by a verified fix may be copied verbatim into
  `HANDOFF.archive.md` with `resolved: <commit-or-date>`; after verifying that
  the archive append succeeded, it may be removed from the active list during
  WRITE. If archive persistence fails, leave it active.
- User-specific rejections are not automatically durable project rules. PROMOTE
  only after checking scope, duplication, conflicts, and obtaining confirmation.

### 7. Environment quickref

- Include only what a fresh session needs to run or verify this task: essential
  commands, versions, platform constraints, and relevant environment state.
- Long-lived conventions belong in the project's durable agent instructions
  after a reviewed PROMOTE, not duplicated indefinitely in this handoff.

### 8. Open questions / PROMOTE candidates

- Questions must be genuinely unanswered and must not duplicate a next step.
- A PROMOTE candidate must include proposed destination and reason it should
  survive a task switch. Keep unconfirmed candidates here and report them at
  each WRITE until decided.

## Secret scan

Run before saving every modified `HANDOFF.md` and `HANDOFF.archive.md`.

```sh
python scripts/scan_secrets.py HANDOFF.md
# If HANDOFF.archive.md exists, include it as an additional argument:
python scripts/scan_secrets.py HANDOFF.md HANDOFF.archive.md
# POSIX / Git Bash wrapper:
sh scripts/scan.sh HANDOFF.md
```

Do not pass `HANDOFF.archive.md` if it does not exist; missing paths are errors.

The scanner reports the file, line number, and finding category but intentionally
redacts the matched value. It exits `0` for no configured-pattern matches, `1`
for one or more findings, and `2` for usage/read errors. A finding is not proof
that the line is a secret; inspect the local file and decide. No matches is not
proof that no sensitive content exists: review the document manually as well.
Redact by default. Do not paste secret values into chat or logs.

## Compression order

1. Move resolved pitfalls to `HANDOFF.archive.md` after confirming the append.
2. Compress Section 3 to concise, scoped evidence.
3. Remove Section 7 prose that is not needed for this task.
4. Shorten nonessential prose in Section 1, but preserve the user's exact quote.

Never silently truncate protected entries or active blocker evidence. If the
protected facts do not fit within the 120-line cap, report the conflict and ask
the user how to split the task/state; do not declare a successful WRITE.
