# Worked examples

These examples show what the protocol should preserve. Names, paths, hashes,
commands, and outputs below are illustrative, not claims about a real repository.

## Bad: diary-style handoff

```markdown
# Handoff

We spent the session refactoring the parser. We tried some approaches and the
new code mostly works. Nested tags sometimes fail. I think the Windows path
problem is fixed. Need to finish testing and maybe release it.
```

Why it fails:

| Failure | Cost in the next session |
|---|---|
| Rejected approaches are missing | The successor may repeat proposals the user already rejected |
| “Sometimes fail” has no error or reproduction | The successor must rediscover the failure |
| “Mostly works” does not state test scope | A partial test run may be mistaken for full validation |
| “I think fixed” is not evidence | The successor cannot tell a verified fix from a memory claim |
| “Maybe release” has no prerequisite | The next action is ambiguous and could have external side effects |

## Good: evidence-scoped handoff

```markdown
---
schema_version: 2
updated: "2026-10-14T16:45:00-07:00"
git:
  branch: feat/parser
  head: a1b2c3d
  dirty: true
  scope: "snapshot before handoff write"
captured: log
tasks:
  - id: TASK-001
    name: parser rewrite
    status: blocked
---

# 1. Task & user intent
Replace the regex parser with a tokenizer before the v0.4 release.
> "必须保持向后兼容，API 签名不能动" — user, 2026-10-14

# 2. User-rejected approaches
- ❌ Third-party parser library — rejected 10-14: "不要引入新依赖"

# 3. Completed / claims
- [verified] ✅ Lexer rewrite → `src/lexer.py`; evidence: `pytest tests/test_lexer.py -q` → `12 passed`; scope: working tree at WRITE.
- [reported] Migration guide drafted → `docs/migration.md`; historical report exists; not re-read in this WRITE.

# 4. Current blocker
- Status: blocked
- Symptom: `KeyError: 'tag'` in nested-table test.
- Location: `src/parser.py:123`
- Repro / evidence: `pytest tests/test_parser.py::test_nested_table -x` → same error observed.

# 5. Next steps
1. Guard missing `tag` key → expected: nested-table repro passes; verify: `pytest tests/test_parser.py -x -q`.
2. Review public signatures before release → expected: no signature changes; verify: compare `inspect.signature` output with the baseline.

# 6. Pitfalls & bans
- [pitfall] 10-14 `pytest -q` hid skipped tests; root cause: quiet output omitted the skip detail. Ban: use `pytest -rs` when validating skips.

# 7. Environment quickref
- Test: `pytest -x -q` · Build: `python -m build` · Python 3.12; CI includes Windows.

# 8. Open questions / PROMOTE candidates
- Candidate: Windows CI path handling → `AGENTS.md`; confirm scope and whether already documented.
```

Why it is better:

- It preserves a verbatim user constraint and rejection.
- It distinguishes a check run now from a historical report.
- It records the blocker with a reproduction command.
- Each next step has an observable result and verification method.
- A release is not implicitly authorized by the handoff.

## Resolved pitfall archive

After a fix has been verified, move the entry (without rewriting its content)
to `HANDOFF.archive.md`, appending a resolution marker. Confirm the write and
scan the archive before removing the active entry from `HANDOFF.md`.

```markdown
# Resolved handoff pitfalls

- [pitfall][resolved: d4e5f6a] `pytest -q` hid skipped tests — root cause: quiet output omitted skip detail. Ban: use `pytest -rs` when validating skips.
```

Do not load this archive on every READ. Open it only when an active item points
to it or historical detail is needed. The archive is append-only; repository
history remains the durable audit trail.

## Stale-write conflict

Suppose the writer records a fingerprint of the current handoff, prepares a
candidate, and another session edits `HANDOFF.md` before save. `safe-write`
should refuse to replace the target when the current fingerprint differs from
the expected fingerprint. Keep the candidate, inspect both versions, merge the
new information, revalidate, rescan, and retry with the new fingerprint.

Do not force-save the candidate just because its content looks newer. The helper
coordinates only writers that use the helper; a manual editor or an agent that
bypasses it can still race with the save. Re-read and validate after writing.

## A reported claim that cannot be verified

```markdown
# 3. Completed / claims
- [unverified] Upload reportedly completed; no remote receipt or asset URL is available. Verify: inspect the target service before claiming success.
```

This is better than claiming `verified` from memory or from a local file's
existence. A failure to check should remain visible rather than being converted
into success.
