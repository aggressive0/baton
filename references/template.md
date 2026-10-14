# HANDOFF.md Template

Copy the skeleton below, then follow the per-field rules. Target: ≤ 120
lines total. Sections marked **[protected]** are append-only during the
session and carried forward verbatim on every rebuild — never compressed,
never paraphrased.

## Skeleton

```markdown
---
updated: <pasted from `date +%Y-%m-%dT%H:%M%z`>
git: { branch: <branch>, head: <short hash|none>, dirty: <bool> }
tasks: [{ name: <short name>, status: active|blocked|review|done }]
---

# 1. Task & user intent                                   <!-- ≤10 lines -->
<2-4 lines: what is being built and why it matters>
> "<hard requirement in the user's exact words>" — user, <date>   [protected]

# 2. User-rejected approaches                        <!-- ≤10, protected -->
- ❌ <approach> — rejected by user: <their reason>

# 3. Completed                                            <!-- ≤15 lines -->
- ✅ <what> → <commit hash | file path>, <verification result>

# 4. Current blocker                                      <!-- ≤10 lines -->
- Symptom: <verbatim error message, untruncated>
- Location: <file:line>
- Repro: <exact command that reproduces it>

# 5. Next steps                                           <!-- ≤15 lines -->
1. <action> → expected: <observable result>; verify: <command>

# 6. Pitfalls & bans                            <!-- ≤30, protected -->
- [pitfall] <phenomenon> — root cause: <cause>. Ban: <rule for the next session>

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
command (`wc -l HANDOFF.md`; PowerShell: `(gc HANDOFF.md | measure
-Line).Lines`), never by eye.

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

- `updated`: run `date +%Y-%m-%dT%H:%M%z` (PowerShell:
  `Get-Date -Format "yyyy-MM-ddTHH:mmzzz"`) and paste the output. Models
  guess clocks badly; never write a time from memory.
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
- One line each: approach + the user's reason. Append-only. If the user
  reverses a decision, append the reversal — never edit or delete the
  original entry.

### 3. Completed

- Evidence only: commit hash or file path + verification result. One line
  per item. Process narrative ("we tried X, then Y") is deleted on
  rebuild — git history holds it.
- First section to compress when over the line cap.

### 4. Current blocker

- Symptom: **verbatim** error message. Not "KeyError: something" — the
  full message, untruncated.
- Location as `file:line`. Repro must be a runnable command. If no repro
  exists, write what you tried and why it failed.
- When the blocker resolves, rewrite this section on the next WRITE.
  Resolved blockers never accumulate here — they become Section 3 or 6.

### 5. Next steps

- Priority order. Each step: action → expected observable result → verify
  command. A step without a verify command is a wish, not a step.
- Carry unfinished steps forward from the previous handoff; delete
  finished ones. This section must shrink as often as it grows.

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

### 7. Environment quickref

- Only what a fresh session needs to run, verify, or build **this task**.
- Long-lived environment facts belong in CLAUDE.md/AGENTS.md (PROMOTE),
  not here.

### 8. Open questions

- Anything you would otherwise interrupt the user to ask mid-session.
  Parked here, they can be answered asynchronously.

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
