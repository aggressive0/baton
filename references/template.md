# HANDOFF.md Template

Copy the skeleton below, then follow the per-field rules. Target: ≤ 120
lines total. Sections marked **[protected]** are append-only during the
session and carried forward verbatim on every rebuild — never compressed,
never paraphrased.

## Skeleton

```markdown
---
updated: <pasted output of a time command — see frontmatter rules>
git: { branch: <branch>, head: <short hash|none>, dirty: <bool> }
captured: log|reconstructed
tasks: [{ name: <short name>, status: active|blocked|review|done }]
---

# 1. Task & user intent                                   <!-- ≤10 lines -->
<2-4 lines: what is being built and why it matters>
> "<hard requirement in the user's exact words>" — user, <date>   [protected]

# 2. User-rejected approaches                        <!-- ≤10, protected -->
- ❌ <approach> — rejected <MM-DD>: <their reason>

# 3. Completed                                            <!-- ≤15 lines -->
- ✅ <what> → <commit hash | file path>, <verification result>

# 4. Current blocker                                      <!-- ≤10 lines -->
- Symptom: <verbatim error message, untruncated>
- Location: <file:line>
- Repro: <exact command that reproduces it>

# 5. Next steps                                           <!-- ≤15 lines -->
1. <action> [前置: <step#>] → expected: <observable result>; verify: <command>

# 6. Pitfalls & bans                            <!-- ≤30, protected -->
- [pitfall] <MM-DD> <phenomenon> — root cause: <cause>. Ban: <rule for the next session>

# 7. Environment quickref                                  <!-- ≤6 lines -->
- Test: `<cmd>` · Build: `<cmd>` · Run: `<cmd>`
- <versions / OS constraints not yet promoted to CLAUDE.md/AGENTS.md>

# 8. Open questions                                        <!-- ≤5 lines -->
- <question the user has not answered yet>

## Archived                                    <!-- excluded from budget -->
- [pitfall][resolved: <commit|date>] <original entry, unchanged>
```

## Section line budgets

Budgets include each section heading. Active total ≈ 106 lines plus blank
lines — comfortably under the 120 hard cap, which is checked with a
command, never by eye: `wc -l HANDOFF.md` (POSIX) · `(gc HANDOFF.md |
measure -Line).Lines` (PowerShell) · `python -c "print(sum(1 for _ in
open('HANDOFF.md')))"` (portable fallback).

| Part | Budget |
|---|---|
| Frontmatter | ≤ 5 |
| 1 Task & user intent | ≤ 10 — never cut the quotes |
| 2 User-rejected approaches | ≤ 10 |
| 3 Completed | ≤ 15 |
| 4 Current blocker | ≤ 10 |
| 5 Next steps | ≤ 15 |
| 6 Pitfalls & bans (active) | ≤ 30 |
| 7 Environment quickref | ≤ 6 |
| 8 Open questions | ≤ 5 |
| `## Archived` | excluded from all budgets |

Over budget? See "Compression order" at the bottom.

## Field rules

### Frontmatter

- `updated`: run a time command and paste the output. Models guess clocks
  badly; never write a time from memory. `date +%Y-%m-%dT%H:%M%z` (POSIX) ·
  `Get-Date -Format "yyyy-MM-ddTHH:mmzzz"` (PowerShell) · `python -c
  "import datetime;print(datetime.datetime.now().astimezone().isoformat())"`
  (portable fallback where coreutils are unavailable).
- `captured`: `log` if Sections 2/6 were appended by LOG during the
  session; `reconstructed` if rebuilt from memory (first adoption on an
  ongoing project). Self-reported — READ weights entry dates over this
  flag — but lying here defeats the trust model. `reconstructed` triggers
  wider spot-checks on READ.
- `git`: fill from actual `git status` / `git rev-parse --short HEAD`,
  never from memory. `dirty: true` if any uncommitted changes exist.
  No repo → `git: none`. Empty repo (no commits) → `head: none`.
- `tasks`: one entry per task in flight. `status` ∈ active | blocked |
  review | done. A task marked `done` must not still appear in Section 5.

### 1. Task & user intent

- Two to four lines. A reader with zero context must learn **what and
  why** — not how (that is Sections 3 and 5).
- Hard requirements go in as **verbatim quotes**. Paraphrase loses intent:
  "keep it backwards compatible" is not "API 签名不能动". Quotes survive
  every rebuild.

### 2. User-rejected approaches [protected]

- The highest-value, most-often-omitted section. Without it, the next
  session will politely re-propose the rejected approach and burn the
  user's patience re-arguing from zero.
- One line each: approach + the user's reason + the date, written at LOG
  time (`rejected 10-13`). An undated entry cannot be told apart from a
  deathbed recollection. In a `reconstructed` file, coarse dates are
  acceptable (`约 2026-09 上旬`) — an empty date is not. Append-only. If
  the user reverses a decision, append the reversal — never edit or
  delete the original entry.

### 3. Completed

- Evidence only: commit hash or file path + verification result. One line
  per item. Process narrative ("we tried X, then Y") is deleted on
  rebuild — git history holds it.
- Non-git artifacts (docx, binaries, deployments) cannot be verified from
  the repo — so the verification action lives inside the claim:
  `✅ paper P0 fixes → 论文.docx, 22 edits, verify: open 摘要 last
  paragraph`. A bare claim is unverifiable by design.
- First section to compress when over the line cap.

### 4. Current blocker

- Symptom: **verbatim** error message. Not "KeyError: something" — the
  full message, untruncated.
- Location as `file:line`. Repro must be a runnable command. If no repro
  exists, write what you tried and why it failed.
- A blocker that is an absence ("file missing", "not uploaded") carries
  evidence of the search, not just the verdict: the command you ran and
  what it returned. Mark unrelated nearby artifacts explicitly, so the
  next session does not hook onto them.
- When the blocker resolves, rewrite this section on the next WRITE.
  Resolved blockers never accumulate here — they become Section 3 or 6.

### 5. Next steps

- Priority order. Each step: action → expected observable result → verify
  command. A step without a verify command is a wish, not a step.
- Carry unfinished steps forward from the previous handoff; delete
  finished ones. This section must shrink as often as it grows.
- Steps that gate each other carry the dependency inline:
  `4. Push release → 前置: step 3 green`. Never let a step depend on an
  open question in Section 8 — upgrade the question to a step, or
  cross-reference it: `5. Make repo public → 前置: Q3 privacy review`.
  A question has no owner; a step does.
- Steps addressed at the reader (tests, checks) say so: "You are the READ
  test for this file: run the READ protocol and report." Never leave a
  step that could mean "do X" or "you are the X".
- No references a fresh session cannot resolve. Anything outside the repo
  (local memory files, another machine) → inline the essential content,
  or mark `[local-only]` and put the essentials in the step itself.
- Verify commands are runnable in the next session's shell: run each
  once at WRITE, or annotate the shell it needs. `grep`/`wc` do not
  exist in PowerShell 5 — use `Select-String` / `Measure-Object -Line`
  there. An unverified verify command is a protocol violation in
  miniature.

### 6. Pitfalls & bans [protected]

- One line each: phenomenon — root cause — ban. The ban is phrased as an
  instruction: "Ban: pathlib everywhere, never os.path for paths that
  reach CI."
- Append-only, survives every rebuild. A pit with no root cause yet is
  still recorded — write `root cause: unknown` and keep the verbatim error.
- Permanent lessons get PROMOTEd to CLAUDE.md/AGENTS.md during WRITE; the
  entry also stays here until the task ends.
- Exit valve: when a pitfall is fixed, tag the entry
  `resolved: <commit|date>` and move it verbatim to `## Archived` —
  outside every budget, still append-only, never edited. Unresolved
  entries never leave Section 6. Section 2 rejections never archive.
- PROMOTE check at WRITE: a ban that survives a task switch (environment,
  tool, or user-behavior fact) moves to CLAUDE.md/AGENTS.md after user
  confirmation — decidable test in SKILL.md. Removal is not an
  append-only violation; the information persists, relocated.
- A to-do hiding inside a pitfall entry gets split: the fact stays here,
  the action becomes a Section 5 step, the two cross-reference each
  other. Readers plan from Section 5; actions buried here do not exist
  for them.

### 7. Environment quickref

- Only what a fresh session needs to run, verify, or build **this task**.
- Long-lived environment facts belong in CLAUDE.md/AGENTS.md (PROMOTE),
  not here.

### 8. Open questions

- Anything you would otherwise interrupt the user to ask mid-session.
  Parked here, they can be answered asynchronously.
- Gate check: a question that is a prerequisite for a next step is not a
  question — upgrade it to a verify-able step or cross-reference it from
  the step it gates (see Section 5 rules).

## Secret scan (before every WRITE save)

HANDOFF.md is designed to be committed, so the scan runs as a command and
its output is shown to the user. A silent pass is a protocol violation.

```sh
sh scripts/scan.sh HANDOFF.md    # preferred: deterministic, prints evidence
# or, by hand:
grep -nE 'sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-|eyJ[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|[A-Za-z0-9/+=]{40}|\b(api_key|apikey|password|passwd|secret|token)\b|Authorization:' HANDOFF.md
```

Pattern notes:

- `eyJ…` catches JWTs; the bare 40-char class catches AWS secret keys and
  also full hashes / base64 blobs — a hit is a **candidate**, the human
  decides.
- Word matches (`token`, `secret`, `password`) false-positive in normal
  technical discussion. That is fine: the scan surfaces, the user disposes.
- No regex catches everything — also eyeball for pasted `.env` / config
  blocks.

Disposition flow:

1. Run the scan; show the user **every hit with its line**, or the
   script's "0 hits" evidence line.
2. The user decides per hit: redact or allow. Never auto-pass.
3. Redact as `<redacted: reason>` — never delete a line silently.

## Compression order (over budget)

0. Move `resolved:`-tagged pitfalls to `## Archived` (outside the budget)
1. Section 3 → commit hashes only
2. Section 7 → keep test/build commands, drop prose
3. Section 1 prose → but never the quotes

Never compress Sections 2, 4, or active Section 6 — unresolved entries
stay in place; that is what Archived is for.
