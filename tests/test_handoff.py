from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_SCRIPT = ROOT / "scripts" / "handoff.py"
SCANNER_SCRIPT = ROOT / "scripts" / "scan_secrets.py"

VALID_HANDOFF = '''---
schema_version: 2
updated: "2026-10-14T16:45:00-07:00"
git:
  branch: feat/example
  head: abc1234
  dirty: true
  scope: "snapshot before handoff write"
captured: log
tasks:
  - id: TASK-001
    name: example task
    status: blocked
---

# 1. Task & user intent
Create a sample parser and preserve compatibility.
> "Do not change the public API." — user, 2026-10-14

# 2. User-rejected approaches
- ❌ Add a dependency — rejected 2026-10-14: no new packages.

# 3. Completed / claims
- [verified] ✅ lexer added → `src/lexer.py`; evidence: `pytest tests/test_lexer.py -q` → 12 passed; scope: working tree at WRITE.

# 4. Current blocker
- Status: blocked
- Symptom: `KeyError: 'tag'`.
- Location: `src/parser.py:123`
- Repro / evidence: `pytest tests/test_parser.py -x` → same error observed.

# 5. Next steps
1. Fix missing tag guard → expected: reproduction passes; verify: `pytest tests/test_parser.py -x -q`.

# 6. Pitfalls & bans
- [pitfall] 10-14 `pytest -q` hid skips — root cause: quiet output. Ban: use `pytest -rs`.

# 7. Environment quickref
- Test: `pytest -x -q` · Build: `python -m build` · Python 3.12.

# 8. Open questions / PROMOTE candidates
- Candidate: Windows path behavior → `AGENTS.md`; confirm duplication and scope.
'''


class HandoffToolTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HANDOFF_SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_handoff_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text(VALID_HANDOFF, encoding="utf-8")
            result = self.run_script("validate", str(path))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS:", result.stdout)

    def test_missing_required_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text(VALID_HANDOFF.replace("# 6. Pitfalls & bans", "# 6. Pitfalls removed"), encoding="utf-8")
            result = self.run_script("validate", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("required heading missing", result.stdout)

    def test_unresolved_template_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text(VALID_HANDOFF.replace("Create a sample parser", "<exact user requirement>"), encoding="utf-8")
            result = self.run_script("validate", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("unresolved template placeholder", result.stdout)

    def test_over_120_lines_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text(VALID_HANDOFF + "\n" * 130, encoding="utf-8")
            result = self.run_script("validate", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("limit is 120", result.stdout)

    def test_safe_write_saves_if_fingerprint_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "HANDOFF.md"
            candidate = root / "HANDOFF.candidate.md"
            target.write_text(VALID_HANDOFF.replace("first", "old"), encoding="utf-8")
            candidate.write_text(VALID_HANDOFF, encoding="utf-8")
            fingerprint = self.run_script("fingerprint", str(target)).stdout.strip()
            result = self.run_script(
                "safe-write", "--target", str(target), "--candidate", str(candidate), "--expected-sha", fingerprint
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), VALID_HANDOFF)
            self.assertIn("SAVED:", result.stdout)

    def test_safe_write_refuses_stale_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "HANDOFF.md"
            candidate = root / "HANDOFF.candidate.md"
            target.write_text(VALID_HANDOFF, encoding="utf-8")
            candidate.write_text(VALID_HANDOFF.replace("Create a sample", "Prepare a sample"), encoding="utf-8")
            stale_fingerprint = self.run_script("fingerprint", str(target)).stdout.strip()
            target.write_text(VALID_HANDOFF.replace("preserve compatibility", "break compatibility"), encoding="utf-8")
            result = self.run_script(
                "safe-write", "--target", str(target), "--candidate", str(candidate), "--expected-sha", stale_fingerprint
            )
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("CONFLICT:", result.stderr)
            self.assertIn("break compatibility", target.read_text(encoding="utf-8"))


    def test_safe_write_blocks_unapproved_secret_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "HANDOFF.md"
            candidate = root / "HANDOFF.candidate.md"
            target.write_text(VALID_HANDOFF, encoding="utf-8")
            fake_secret = "ghp_" + "A" * 36
            candidate.write_text(VALID_HANDOFF.replace("Python 3.12.", f"Python 3.12. Example api note: {fake_secret}"), encoding="utf-8")
            fingerprint = self.run_script("fingerprint", str(target)).stdout.strip()
            result = self.run_script(
                "safe-write", "--target", str(target), "--candidate", str(candidate), "--expected-sha", fingerprint
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("unapproved scan findings", result.stderr)
            self.assertNotIn(fake_secret, result.stdout + result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), VALID_HANDOFF)

    def test_safe_write_refuses_invalid_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "HANDOFF.md"
            candidate = root / "candidate.md"
            target.write_text("old handoff\n", encoding="utf-8")
            candidate.write_text("not a handoff\n", encoding="utf-8")
            fingerprint = self.run_script("fingerprint", str(target)).stdout.strip()
            result = self.run_script(
                "safe-write", "--target", str(target), "--candidate", str(candidate), "--expected-sha", fingerprint
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "old handoff\n")


class SecretScannerTests(unittest.TestCase):
    def test_detects_token_but_does_not_print_secret(self) -> None:
        fake_secret = "ghp_" + "A" * 36
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text(f"fake token: {fake_secret}\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCANNER_SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("github-token", result.stdout)
            self.assertIn("matched value redacted", result.stdout)
            self.assertNotIn(fake_secret, result.stdout)

    def test_no_match_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "HANDOFF.md"
            path.write_text("ordinary project note\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCANNER_SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("0 configured-pattern matches", result.stdout)


if __name__ == "__main__":
    unittest.main()
