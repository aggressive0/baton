#!/usr/bin/env python3
"""Validate, fingerprint, and safely replace a Baton HANDOFF.md (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from scan_secrets import scan_path, scan_text

REQUIRED_HEADINGS = [
    "# 1. Task & user intent",
    "# 2. User-rejected approaches",
    "# 3. Completed / claims",
    "# 4. Current blocker",
    "# 5. Next steps",
    "# 6. Pitfalls & bans",
    "# 7. Environment quickref",
    "# 8. Open questions / PROMOTE candidates",
]
PLACEHOLDER_RE = re.compile(
    r"<(?:actual ISO-8601 timestamp[^>]*|2-4 lines[^>]*|branch-or-none|short-hash-or-none|"
    r"true-or-false|short task name|exact user requirement|approach|date|reason|"
    r"claim|command|exact command|file-or-commit|commit/state|result|expected result|"
    r"commit-or-date|root cause|prevention rule|cause\|unknown|blocked\|none|"
    r"symptom(?:/error)?|verbatim, untruncated error[^>]*|file:line(?: or search scope)?|"
    r"observable result|action|task-relevant version/OS constraint[^>]*|"
    r"question or candidate[^>]*)>",
    re.IGNORECASE,
)
VALID_TASK_STATUSES = {"active", "blocked", "review", "done"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_content(content: str) -> list[str]:
    issues: list[str] = []
    lines = content.splitlines()
    if len(lines) > 120:
        issues.append(f"FAIL: {len(lines)} lines; active HANDOFF.md limit is 120 (includes blanks/frontmatter).")
    if lines and lines[0].strip() != "---":
        issues.append("FAIL: frontmatter must begin on line 1 with '---'.")
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        issues.append("FAIL: frontmatter closing '---' not found.")
        frontmatter = ""
        body = content
    else:
        frontmatter = "\n".join(lines[1:closing])
        body = "\n".join(lines[closing + 1 :])

    if not re.search(r"(?m)^schema_version:\s*2\s*$", frontmatter):
        issues.append("FAIL: frontmatter must declare schema_version: 2.")

    updated_match = re.search(r"(?m)^updated:\s*[\"']?([^\"'\n]+)[\"']?\s*$", frontmatter)
    if not updated_match:
        issues.append("FAIL: frontmatter must include updated with an ISO-8601 timestamp.")
    else:
        raw_timestamp = updated_match.group(1).strip()
        try:
            parsed_timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            if parsed_timestamp.tzinfo is None:
                issues.append("FAIL: updated timestamp must include a UTC offset/time zone.")
        except ValueError:
            issues.append(f"FAIL: updated is not a valid ISO-8601 timestamp: {raw_timestamp}")

    captured_match = re.search(r"(?m)^captured:\s*(\S+)\s*$", frontmatter)
    if not captured_match or captured_match.group(1) not in {"log", "reconstructed"}:
        issues.append("FAIL: captured must be 'log' or 'reconstructed'.")

    for key in ("branch", "head", "dirty", "scope"):
        if not re.search(rf"(?m)^\s*{key}:\s*.+$", frontmatter):
            issues.append(f"FAIL: frontmatter git block is missing '{key}'.")

    if "## Archived" in body:
        issues.append("FAIL: do not keep an unbounded '## Archived' section in HANDOFF.md; move resolved entries to HANDOFF.archive.md.")

    for heading in REQUIRED_HEADINGS:
        count = len(re.findall(rf"(?m)^{re.escape(heading)}\s*$", body))
        if count == 0:
            issues.append(f"FAIL: required heading missing: {heading}")
        elif count > 1:
            issues.append(f"FAIL: duplicate heading: {heading}")

    for match in PLACEHOLDER_RE.finditer(content):
        line_no = content.count("\n", 0, match.start()) + 1
        issues.append(f"FAIL: unresolved template placeholder on line {line_no}: {match.group(0)}")

    for task_status in re.findall(r"(?mi)^\s*status:\s*(\w+)\s*$", frontmatter):
        if task_status not in VALID_TASK_STATUSES:
            issues.append(f"FAIL: invalid task status '{task_status}'. Allowed: {', '.join(sorted(VALID_TASK_STATUSES))}.")

    # Evidence tags are deliberately checked structurally, not semantically.
    for number, line in enumerate(lines, 1):
        if "[verified]" in line and ("evidence:" not in line or "scope:" not in line):
            issues.append(f"FAIL: [verified] claim on line {number} must include evidence: and scope:.")
        if re.match(r"^\s*\d+[.)]\s+", line):
            if "# 5. Next steps" in body:
                in_next_steps = False
                for body_line in body.splitlines():
                    if body_line.strip() == "# 5. Next steps":
                        in_next_steps = True
                        continue
                    if re.match(r"^# \d+\.", body_line):
                        in_next_steps = False
                    if in_next_steps and body_line == line:
                        if not re.search(r"\bverify\s*:", line, re.IGNORECASE) and not re.search(r"\bmanual verification\b", line, re.IGNORECASE):
                            issues.append(f"FAIL: next step on line {number} needs 'verify:' or 'manual verification'.")
                        break

    return issues


def validate_file(path: Path) -> list[str]:
    if not path.is_file():
        return [f"FAIL: file not found: {path}"]
    try:
        content = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"FAIL: cannot read UTF-8 file: {exc}"]
    return validate_content(content)


def acquire_lock(lock_path: Path) -> int | None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(lock_path, flags, 0o600)
    except FileExistsError:
        return None
    os.write(fd, f"pid={os.getpid()}\n".encode("ascii"))
    os.fsync(fd)
    return fd


def _finding_id(finding) -> str:
    return f"{finding.path}:{finding.line}:{finding.category}:{finding.line_sha256}"


def _read_regular_file_snapshot(path: Path) -> bytes:
    """Read once; reject symlinks where O_NOFOLLOW is available and non-regular files."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"not a regular file: {path}")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(fd)


def safe_write(target: Path, candidate: Path, expected_sha: str | None, expected_missing: bool, allowed_findings: set[str]) -> int:
    if target.is_symlink():
        print(f"FAIL: refusing to replace symlink target: {target}", file=sys.stderr)
        return 2
    if candidate.is_symlink():
        print(f"FAIL: refusing symlink candidate: {candidate}", file=sys.stderr)
        return 2
    target = target.resolve()
    # Keep candidate path absolute but do not re-open it after snapshotting.
    candidate = Path(os.path.abspath(candidate))
    if target == candidate.resolve():
        print("FAIL: candidate must be a separate file, not the live target.", file=sys.stderr)
        return 2
    if not candidate.is_file():
        print(f"FAIL: candidate not found: {candidate}", file=sys.stderr)
        return 2
    if not target.parent.is_dir():
        print(f"FAIL: target directory does not exist: {target.parent}", file=sys.stderr)
        return 2

    # Freeze candidate bytes exactly once. Validation, scanning, and the final
    # write all consume this same snapshot, so replacing/editing the candidate
    # after scanning cannot smuggle different bytes into the destination.
    try:
        candidate_bytes = _read_regular_file_snapshot(candidate)
        candidate_content = candidate_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"FAIL: cannot safely read candidate snapshot: {exc}", file=sys.stderr)
        return 2

    candidate_issues = validate_content(candidate_content)
    if candidate_issues:
        print("Candidate validation failed; target was not changed:", file=sys.stderr)
        print("\n".join(candidate_issues), file=sys.stderr)
        return 1

    # Scan the exact immutable candidate snapshot; read the archive once too.
    scan_targets: list[tuple[str, list]] = [(candidate.name, scan_text(candidate.name, candidate_content))]
    archive = target.parent / "HANDOFF.archive.md"
    if target.name == "HANDOFF.md" and archive.exists():
        archive_findings, archive_error = scan_path(archive)
        if archive_error:
            print(f"FAIL: secret scan could not complete: {archive_error}", file=sys.stderr)
            return 2
        scan_targets.append((archive.name, archive_findings))

    finding_ids: set[str] = set()
    for _name, findings in scan_targets:
        for finding in findings:
            finding_id = _finding_id(finding)
            finding_ids.add(finding_id)
            print(f"SCAN HIT: {finding_id}; matched value redacted")

    unexpected = finding_ids - allowed_findings
    stale_allowances = allowed_findings - finding_ids
    if stale_allowances:
        print("FAIL: --allow-finding entry no longer matches the exact current line; inspect and remove the stale allowance:", file=sys.stderr)
        print("\n".join(sorted(stale_allowances)), file=sys.stderr)
        return 1
    if unexpected:
        print("FAIL: unapproved scan findings; redact them or explicitly allow each confirmed non-secret finding with --allow-finding FILENAME:LINE:CATEGORY:LINE_SHA256. Target was not changed.", file=sys.stderr)
        print("\n".join(sorted(unexpected)), file=sys.stderr)
        return 1

    lock_path = target.parent / f".{target.name}.baton.lock"
    lock_fd = acquire_lock(lock_path)
    if lock_fd is None:
        print(f"FAIL: writer lock exists: {lock_path}. Check whether a writer is active before removing a stale lock.", file=sys.stderr)
        return 3

    try:
        exists_now = target.exists()
        if expected_missing:
            if exists_now:
                print("CONFLICT: target exists now but was expected to be missing; candidate preserved.", file=sys.stderr)
                return 3
        else:
            if not exists_now:
                print("CONFLICT: target disappeared since it was read; candidate preserved.", file=sys.stderr)
                return 3
            actual_sha = sha256_file(target)
            if actual_sha != expected_sha:
                print(f"CONFLICT: target fingerprint changed. expected={expected_sha} actual={actual_sha}; candidate preserved.", file=sys.stderr)
                return 3

        old_mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
        fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as output:
                # Critical: write the bytes already validated and scanned.
                output.write(candidate_bytes)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(tmp_path, old_mode)
            os.replace(tmp_path, target)
            try:
                dir_fd = os.open(target.parent, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except OSError:
                # Directory fsync is not supported on every platform/filesystem.
                pass
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        # Verify saved bytes equal the reviewed snapshot. This detects many
        # non-cooperating edits/races after replace; it cannot prevent future
        # edits by actors that ignore the cooperative lock.
        try:
            saved_bytes = target.read_bytes()
            saved_content = saved_bytes.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"FAIL: cannot verify saved file: {exc}", file=sys.stderr)
            return 1
        if saved_bytes != candidate_bytes:
            print("FAIL: saved content differs from the validated/scanned snapshot; inspect before continuing.", file=sys.stderr)
            return 1
        final_issues = validate_content(saved_content)
        if final_issues:
            print("FAIL: post-save validation failed; inspect the saved file:", file=sys.stderr)
            print("\n".join(final_issues), file=sys.stderr)
            return 1
        print(f"SAVED: {target}")
        print(f"LINES: {len(saved_content.splitlines())}")
        print(f"SHA256: {hashlib.sha256(saved_bytes).hexdigest()}")
        print("NOTE: lock coordinates only writers using this helper; verify for non-cooperating editors/agents.")
        return 0
    except OSError as exc:
        print(f"FAIL: safe-write failed: {exc}", file=sys.stderr)
        return 2
    finally:
        os.close(lock_fd)
        try:
            lock_path.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate a handoff file")
    validate_parser.add_argument("path", type=Path, nargs="?", default=Path("HANDOFF.md"))
    fp_parser = subparsers.add_parser("fingerprint", help="print SHA-256 of the current file")
    fp_parser.add_argument("path", type=Path, nargs="?", default=Path("HANDOFF.md"))
    write_parser = subparsers.add_parser("safe-write", help="validate and replace a candidate if the target fingerprint still matches")
    write_parser.add_argument("--target", type=Path, required=True)
    write_parser.add_argument("--candidate", type=Path, required=True)
    write_parser.add_argument("--allow-finding", action="append", default=[], metavar="FILENAME:LINE:CATEGORY:LINE_SHA256",
                              help="allow a reviewed non-secret false positive for this exact line content; repeat per finding")
    expected = write_parser.add_mutually_exclusive_group(required=True)
    expected.add_argument("--expected-sha", help="SHA-256 printed by the fingerprint command")
    expected.add_argument("--expected-missing", action="store_true", help="assert that the target did not exist when read")
    args = parser.parse_args()

    if args.command == "validate":
        issues = validate_file(args.path)
        if issues:
            print("\n".join(issues))
            return 1
        print(f"PASS: {args.path} ({len(args.path.read_text(encoding='utf-8').splitlines())} lines)")
        return 0
    if args.command == "fingerprint":
        if not args.path.is_file():
            print(f"FAIL: file not found: {args.path}", file=sys.stderr)
            return 2
        print(sha256_file(args.path))
        return 0
    return safe_write(args.target, args.candidate, args.expected_sha, args.expected_missing, set(args.allow_finding))


if __name__ == "__main__":
    raise SystemExit(main())
