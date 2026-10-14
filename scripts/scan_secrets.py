#!/usr/bin/env python3
"""Scan handoff files for common credential patterns without printing secrets."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    path: str
    line: int
    category: str
    line_sha256: str


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai-like-key", _compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", _compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws-access-key-id", _compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", _compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("jwt-like-token", _compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b")),
    ("private-key-header", _compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("authorization-bearer", _compile(r"\bAuthorization\s*:\s*Bearer\s+\S+")),
    # Match both standalone and prefixed environment variable names, e.g.
    # OPENAI_API_KEY, AWS_SECRET_ACCESS_KEY, CLIENT_SECRET, GITHUB_TOKEN.
    # Keep this assignment-based to avoid flagging ordinary prose that names a variable.
    (
        "secret-environment-variable",
        _compile(
            r"\b(?:[A-Z][A-Z0-9]*_)*(?:API_KEY|SECRET(?:_ACCESS_KEY)?|PASSWORD|PASSWD|TOKEN|"
            r"ACCESS_TOKEN|REFRESH_TOKEN|PRIVATE_KEY)\b\s*[:=]\s*[\"']?[^\s\"']{4,}"
        ),
    ),
    (
        "credential-assignment",
        _compile(r"\b(?:api[_-]?key|secret|password|passwd|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*[\"']?[^\s\"']{8,}"),
    ),
]


def scan_text(path_name: str, content: str) -> list[Finding]:
    """Scan an immutable text snapshot. Hash each full line for approval binding."""
    findings: list[Finding] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
        for category, pattern in PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path_name, line_no, category, line_hash))
    return findings


def scan_bytes(path_name: str, content: bytes) -> tuple[list[Finding], str | None]:
    """Scan exact bytes, rejecting invalid UTF-8 instead of silently replacing it."""
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        return [], f"cannot scan non-UTF-8 file {path_name}: {exc}"
    return scan_text(path_name, text), None


def scan_path(path: Path) -> tuple[list[Finding], str | None]:
    if not path.is_file():
        return [], f"cannot read file (not found): {path}"
    try:
        content = path.read_bytes()
    except OSError as exc:
        return [], f"cannot read file {path}: {exc}"
    return scan_bytes(path.name, content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="files to scan; usually HANDOFF.md and HANDOFF.archive.md if it exists")
    args = parser.parse_args()
    all_findings: list[Finding] = []
    errors: list[str] = []
    for path in args.paths:
        findings, error = scan_path(path)
        all_findings.extend(findings)
        if error:
            errors.append(error)

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for finding in all_findings:
        # The line hash lets a reviewed false-positive exception bind to the
        # exact full line without displaying that line or any matched value.
        print(
            f"HIT: {finding.path}:{finding.line}: category={finding.category}; "
            f"line_sha256={finding.line_sha256}; matched value redacted"
        )
    if errors:
        return 2
    if all_findings:
        print(f"RESULT: {len(all_findings)} finding(s); inspect/redact locally. No matched values were printed.")
        return 1
    print(f"PASS: 0 configured-pattern matches across {len(args.paths)} file(s). This is not a guarantee that no secrets exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
