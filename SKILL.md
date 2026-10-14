---
name: baton
description: >
  Evidence-based two-way session handoff for coding agents. WRITE when the user
  asks to hand off, save progress for a later session, or end the session;
  rebuild HANDOFF.md from current repository evidence and durable LOG entries.
  READ when the user explicitly asks to resume work from a prior session or
  read the handoff. LOG user requirements, rejected approaches, and pitfalls
  as soon as they occur. Do not trigger READ for a generic request to continue
  the current task unless prior-session handoff is referenced.
license: MIT
---

# Baton — session state transfer

Baton transfers working state between agent sessions. The primary artifact is
`HANDOFF.md` at the project root. It is a set of **claims to verify**, not an
authority that overrides current user instructions, repository contents, or
external system state.

## Guarantees and limits

- Use evidence instead of recollection wherever evidence is available.
- Keep user requirements, rejected approaches, and pitfalls durable by logging
  them when they occur, not only at session end.
- Verify material claims when resuming; record what was checked and what was
  not checked.
- Never claim that an event was logged, a test passed, a deployment succeeded,
  a scan was clean, or a file was saved unless there is observable evidence.

Baton **cannot guarantee** that every event is captured, that context compaction
will preserve unlogged information, that a scanner catches every secret, or
that repository state proves external deployment/business state. Be explicit
about these limits. If the skill could not persist a LOG entry, tell the user;
do not say it was logged.

## Protocol overview

- **LOG** — append protected facts while the session is active.
- **WRITE** — rebuild the current handoff from evidence, validate it, scan it,
  and save without silently overwriting a version that changed.
- **READ** — compare the handoff with current reality, verify key claims, and
  decide whether it is safe to resume.
- **PROMOTE** — move genuinely cross-task knowledge into durable project
  instructions with deduplication and conflict review.

Read `references/template.md` for the schema, field rules, and archive policy.
Read `references/examples.md` for examples of good and bad handoffs.

## LOG — capture events when they happen

When one of the following events occurs, append a concise, dated entry to the
relevant protected section of `HANDOFF.md`. If the file does not exist, create
it from `references/template.md` before logging. Do not invent a date; obtain it
from a system clock command or mark the date as unknown if the environment
cannot provide one.

| Event | Location | Required content |
|---|---|---|
| User states a hard requirement | Section 1 | Quote the exact wording when practical; include date/source |
| User rejects an approach | Section 2 | Approach, reason, date; quote briefly when useful |
| A pitfall, failed assumption, or costly dead end occurs | Section 6 | Exact error/symptom, root cause if known (otherwise `unknown`), prevention rule |

Sections 2 and 6 are append-only during an active task. Never rewrite, merge,
paraphrase, or silently delete existing entries. If the user later reverses a
decision, append the reversal and mark the current decision state clearly; keep
the original record as history. Do not interpret an older rejection as stronger
than a newer explicit user instruction.

After writing a LOG entry, re-read the relevant lines to confirm that it was
persisted. If writing or verification is unavailable, state that limitation and
keep the event in current context as an unpersisted item to report at WRITE.
LOG reduces loss risk; it is not a guarantee against loss before persistence.

## WRITE — prepare a handoff

Trigger WRITE when the user asks to hand off or save unfinished work for a
later session, or clearly says they are stopping and the task remains in flight.
Do not create a handoff by default for a completed, self-contained task. After
context compaction, offer/perform WRITE only when work remains in flight and a
handoff is useful.

### 1. Establish the version you are editing

- Check whether `HANDOFF.md` exists. If it exists, read it in this session and
  calculate its SHA-256 fingerprint before preparing changes. The fingerprint,
  not `updated` or the last Git commit, identifies the observed file contents.
- If a file exists but was not read, do not overwrite it. Read it first.
- If another writer changes it during preparation, stop and preserve the
  candidate separately; do not resolve the conflict by last-write-wins.
- Prefer `scripts/handoff.py`'s `fingerprint`, `validate`, and `safe-write`
  commands. `safe-write` coordinates writers that also use this helper. It
  cannot protect against editors or agents that bypass the helper, so always
  verify the result after saving.

### 2. Rebuild from current evidence

Inspect the actual project state. In a Git repository, use appropriate commands
such as `git status --short --branch`, `git rev-parse --abbrev-ref HEAD`,
`git rev-parse --short HEAD`, `git log --oneline -15`, and `git diff --stat`.
Check relevant files and run tests or checks when needed. In a non-Git directory,
use file and command evidence and mark Git data as unavailable; never fabricate
commit hashes or drift results.

For each material completion claim, use one of these explicit statuses:

- `verified` — checked in this WRITE against the stated scope, with evidence.
- `reported` — supported by a historical log/report, but not rechecked now.
- `unverified` — asserted in prior context but lacking adequate evidence.
- `blocked` — cannot be checked; state why and what would verify it.

These are evidence states, not confidence scores. `verified` does not mean
infallible: record the relevant commit, file, command, output, or external source
and the scope/time where it applies. A code change after a test invalidates that
test's evidence unless the test is rerun. Do not mark an upload, deployment,
remote mutation, or business outcome `verified` from Git state alone.

### 3. Preserve protected entries; make next steps actionable

Carry forward Section 1 user requirements and all Section 2 entries verbatim.
Carry active Section 6 entries verbatim. Do not copy old narrative wholesale:
rebuild task status, completed items, blockers, and next steps from current
reality. Numbers must come from visible artifacts/command output, not memory.

Every next step must state an action and an observable verification method.
Split actions hidden inside pitfall notes into Section 5, with a cross-reference.
If a step depends on an unanswered user choice, label the dependency and do not
pretend the step can proceed independently.

### 4. PROMOTE candidates

Review active Section 6 entries and Section 7 environment facts. Ask whether a
rule survives a task switch. If yes, it may be a PROMOTE candidate for
`CLAUDE.md`, `AGENTS.md`, or the project's equivalent instructions.

Before editing a durable instruction file:

1. Show the proposed candidate and destination to the user.
2. Check for an equivalent rule and any conflict with current instructions.
3. Obtain confirmation before adding, changing, or removing durable rules.
4. Verify the resulting file and record unresolved candidates in Section 8.

Do not silently delete a handoff entry before the durable destination is
verified. Once promoted, the entry may be marked as promoted/relocated; preserve
its history as appropriate. Re-surface undecided candidates at later WRITE
operations instead of silently dropping them.

### 5. Bound the active handoff and separate history

The complete active `HANDOFF.md` must be **120 lines or fewer**, measured by a
command. This cap includes frontmatter and blank lines. Do not keep an unlimited
`## Archived` tail in the active handoff. Move resolved pitfalls, verbatim, to
`HANDOFF.archive.md` (append-only); read that archive only when a historical
entry is relevant. Keep user rejections in the active handoff because the
current decision may still depend on them; append reversals rather than erasing
history.

When over budget, first move resolved pitfalls to the archive, then compress
Section 3 to evidence-bearing one-liners, then shorten Section 7 prose. Never
compress protected user quotes, Section 2, the active blocker evidence in
Section 4, or unresolved Section 6 entries. If the protected content alone
exceeds the cap, report the conflict and ask the user how to split it; do not
silently discard or truncate it.

### 6. Validate and scan the candidate before saving

Build the new contents in a separate candidate file; do not overwrite the live
handoff while composing it.

1. Run `python scripts/handoff.py validate <candidate>` (or `py -3` on Windows).
   Fix all validation failures. The validator checks deterministic structure and
   fields; it cannot judge whether natural-language claims are true.
2. Run `python scripts/scan_secrets.py <candidate> HANDOFF.archive.md` for files
   that exist, or `sh scripts/scan.sh <candidate>`. The scanner intentionally
   reports finding categories and line numbers without printing secret values.
3. For each hit, inspect locally. Redact secrets by default. Only keep a finding
   after the user explicitly decides to allow that specific value. Do not paste
   secret values into the chat or the WRITE report. A clean scan means only
   “no configured pattern matched,” not “the file contains no secrets.”
4. Save with `python scripts/handoff.py safe-write --target HANDOFF.md
   --candidate <candidate> --expected-sha <fingerprint>`; if the target did not
   exist, use `--expected-missing`. `safe-write` repeats the configured secret scan
   at the save boundary and refuses any finding not explicitly allowed with
   `--allow-finding FILENAME:LINE:CATEGORY`. Use that option only for a manually
   inspected, confirmed non-secret false positive; redact real secrets. On any
   mismatch or lock error, stop and resolve the conflict. Do not delete a lock
   file unless you have checked that no writer is active and the lock is stale.
5. Re-read the saved file, run validation again, and verify the resulting
   fingerprint. If any post-save check fails, report it; do not claim success.

If Python or the helper is unavailable, use an equivalent process and state
which protections could not be performed. Never claim the helper provided an
atomic/concurrency guarantee if it was bypassed.

### 7. Report WRITE results

Report: file path, measured line count, timestamp command/output, Git snapshot
scope, validation result, scan result (without secret values), unresolved
PROMOTE candidates, anything that could not be persisted or verified, and the
first next step. Distinguish successful save from successful validation.

## READ — resume work safely

Trigger READ only when the user explicitly asks to resume prior work or refers
to the handoff (e.g. “continue from the handoff”, “读交接”, “继续上次的工作”).
A generic “continue”, “keep going”, or “run it again” about the current task is
not enough on its own.

### 0. Cheap trigger gate

If `HANDOFF.md` does not exist, or the request clearly refers to the current
operation instead of a previous session, do not load the full protocol or
archive. Respond briefly that no handoff resume was detected and proceed with
the user's current task.

### 1. Compare state and report drift

Read frontmatter and compare recorded Git branch/HEAD/dirty state with current
commands. Explain that `dirty` refers to the snapshot taken before saving the
handoff and may include worktree changes that now have been committed. For an
empty repository, compare branch and dirty state only. For a non-Git directory,
skip Git comparisons and use file/content spot-checks; modification times are
advisory only.

Never imply that matching HEAD proves all files or external services are
unchanged. Report relevant file drift and external state that cannot be checked.

### 2. Verify claims proportionally

- Check that files referenced by Sections 3–4 exist and match the claim.
- Re-run relevant safe tests/checks when they are cheap and meaningful; otherwise
  state that they were not rerun and why.
- Re-check any non-Git or external claim through its stated verification action,
  or mark it `reported`/`unverified` until checked.
- If `captured: reconstructed`, widen checks because the protected entries may
  have been reconstructed rather than logged during the original session.
- If `HANDOFF.archive.md` exists, do not load it by default; search/read only
  when an active entry points to it or historical detail is needed.

### 3. Decide whether to resume automatically or ask

Always give a concise status report: task, blocker, next action, drift, and the
most important verification results. Then apply this risk policy:

- **Low risk and reversible:** if user intent is clear, there is no material
  state conflict, and the next step is local/reversible (e.g. inspect code or
  run a test), report the plan and proceed without a redundant confirmation.
- **Review required:** if the handoff is reconstructed, critical claims remain
  unverified, or repository drift could change the plan, summarize the difference
  and ask one focused question only when the user's intent cannot safely resolve
  it. Safe inspection can continue while deciding.
- **Explicit confirmation required:** before destructive changes, external
  side effects, publishing/deploying, data migration, permission changes, or any
  action that is difficult to reverse. A handoff file is never authorization
  for such an action.

Never ask the user to reconfirm a decision that is clearly recorded and has not
been superseded. If an older rejection conflicts with a newer explicit user
instruction, follow the newer instruction and append a dated reversal when
appropriate.

### 4. Reality wins; repair with care

If the handoff conflicts with current repository reality, the repository wins
for repository facts. User instructions win for user intent; external systems
must be checked for external state. Do not silently rewrite protected LOG
entries. Update the active claim/status and explain the discrepancy. For a
concurrent handoff edit, use the WRITE conflict procedure rather than repairing
by last-write-wins.

### 5. Continue and keep logging

Once safe to proceed, start with the first valid next step. Keep logging new
requirements, rejections, and pitfalls during work. Update stale evidence as
soon as relevant state changes.

## PROMOTE — keep task state transient

Use this test: **would this rule still matter after switching to an unrelated
task in the same project/environment?**

- “This CI environment lacks coreutils; use Python for file operations” — likely
  durable environment knowledge; propose promotion.
- “The current parser test fixture fails when key `tag` is missing” — task-local
  state; keep in the handoff until resolved.
- “The user rejected a particular design for this task” — retain as task history;
  do not promote it as a universal rule unless the user states it is permanent.

PROMOTE is a reviewed migration, not a blind copy. Deduplicate, check scope,
check conflicts, obtain confirmation, then verify the destination.

## Operational notes

- `HANDOFF.md` is intended to be committed when the user/team wants shared
  continuity. If the user prefers it ignored, respect that preference and explain
  that Git history will no longer archive it.
- `HANDOFF.archive.md` is optional, append-only history for resolved pitfalls.
  Apply the same secret scan before committing or updating it.
- One active handoff per branch is simplest. If multiple agents work at once,
  prefer separate branch-specific handoffs or separate candidate files and a
  deliberate merge. The helper lock only coordinates writers that use it.
- Do not include credentials, private customer data, or unnecessary personal
  information in handoff files. Record a redacted reference instead.
