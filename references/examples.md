# Worked Examples

A bad handoff reads like a diary. A good handoff reads like a bug report
plus a runbook. Same session, both ways.

## BAD — typical failure

```markdown
# Handoff

## What we did
We spent the session refactoring the parser. The old code was pretty messy,
so we discussed a few approaches and finally went with a lexer rewrite.
Most things work now but nested tags are still sometimes broken. I also
touched some tests. Earlier in the session we had some path issues on
Windows but I think we fixed them.

## Problem
Nested tags throw an error sometimes. Needs debugging.

## Next steps
- Finish the parser
- Maybe add more tests later
```

Why it fails:

| Flaw | Cost in the next session |
|---|---|
| "discussed a few approaches" — none recorded | Re-proposes every rejected approach; user re-argues from zero |
| "sometimes broken" — no verbatim error, no repro | Session burned on reproducing what was already known |
| "I also touched some tests" — no hashes, no results | Cannot tell done from claimed-done; re-verifies everything |
| "I think we fixed them" — pitfall recalled from memory at session end | The one ban that mattered ("never use os.path") is lost |
| No frontmatter | No drift detection; the repo may have moved on since the write |
| No verify commands | "finish the parser" is not a step, it is a wish |

## GOOD — same session, protocol applied

```markdown
---
updated: 2026-10-13T21:30+08:00  # pasted from `date +%Y-%m-%dT%H:%M%z`
git: { branch: feat/parser, head: a1b2c3d, dirty: true }
tasks: [{ name: parser rewrite, status: blocked }]
---

# 1. Task & user intent
Replace regex-based HTML parser with a tokenizer/lexer split before the
v0.4 release; unblocks table rendering.
> "必须保持向后兼容，API 签名不能动" — user, 2026-10-13
> "不要引入新依赖" — user, 2026-10-13

# 2. User-rejected approaches
- ❌ Third-party parser lib (html5ever) — rejected by user: 不引入新依赖
- ❌ Incremental regex patching — rejected by user: 嵌套结构会继续崩

# 3. Completed
- ✅ lexer rewrite → a1b2c3d, 42/42 tests pass
- ✅ parser API surface frozen → src/parser.py, signature review done

# 4. Current blocker
- Symptom: `KeyError: 'tag'` in test_nested_table
  (full message: `File "src/parser.py", line 123, in _parse_open:
   KeyError: 'tag'`)
- Location: src/parser.py:123
- Repro: `pytest tests/test_parser.py::test_nested_table -x`

# 5. Next steps
1. Guard missing `tag` key in `_parse_open()` → expected: repro passes;
   verify: `pytest tests/test_parser.py -x -q`
2. Wire lexer into `Document.from_html` → expected: table fixture renders;
   verify: `pytest tests/test_render.py -k table -q`
3. Delete dead regex paths → expected: no references to legacy parser;
   verify: `grep -r legacy_parser src/` empty + full suite green

# 6. Pitfalls & bans
- [pitfall] os.path joins broke on Windows CI — root cause: mixed
  separators in fixture paths. Ban: pathlib everywhere, never os.path.
- [pitfall] `pytest -q` alone hid 2 skipped tests — root cause: skipif
  markers on py<3.10. Ban: run `pytest -rs` before claiming green.

# 7. Environment quickref
- Test: `pytest -x -q` · Build: `python -m build` · Lint: `ruff check src`
- Python 3.12, WSL; CI also runs Windows (see ban above)

# 8. Open questions
- Keep `parse_fragment()` public or make it private in v0.4?
```

Note: the protected sections (1 quotes, 2, 6) carry entries that were
appended **during** the session, at the moment they happened — not
recalled at write time. Section 4's repro command runs as-is.

## Over-cap compression example

The GOOD example is ~45 lines — fine. If a write lands at 130 lines,
compress in the template's order. Section 3, before → after:

```markdown
# before
- ✅ lexer rewrite → commit a1b2c3d, 42/42 tests pass, 3 files changed,
  2 skipped (py<3.10 markers)

# after
- ✅ lexer rewrite → a1b2c3d, 42/42
```

And a 10-line narrative about the lexer design discussion: deleted
entirely. It lives in git history; whatever survived as a rule is already
in Section 6 as a ban.

## Resolving a pitfall (the protected exit valve)

During the session, Section 6 gains:

```markdown
- [pitfall] `pytest -q` hid 2 skipped tests — root cause: skipif markers.
  Ban: run `pytest -rs` before claiming green.
```

Later the pipeline is fixed (commit d4e5f6a). At WRITE, the entry moves
to the tail — tagged, never edited:

```markdown
## Archived
- [pitfall][resolved: d4e5f6a] `pytest -q` hid 2 skipped tests — root
  cause: skipif markers. Ban: run `pytest -rs` before claiming green.
```

Archived lines do not count toward the 120-line budget and stay
append-only until the task closes; then the section may be emptied in the
same commit — git history is the archive.
