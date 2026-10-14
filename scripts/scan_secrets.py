#!/usr/bin/env python3
"""Scan handoff files for common credential patterns without printing secrets."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    path: str
    line: int
    category: str


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai-like-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("jwt-like-token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b")),
    ("private-key-header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("authorization-bearer", re.compile(r"\bAuthorization\s*:\s*Bearer\s+\S+", re.IGNORECASE)),
    ("credential-assignment", re.compile(r"\b(?:api[_-]?key|secret|password|passwd|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*[\"']?[^\s\"']{8,}", re.IGNORECASE)),
]


def scan_path(path: Path) -> tuple[list[Finding], str | None]:
    if not path.is_file():
        return [], f"cannot read file (not found): {path}"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [], f"cannot read UTF-8 file {path}: {exc}"
    findings: list[Finding] = []
    for line_no, line in enumerate(lines, start=1):
        for category, pattern in PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path.name, line_no, category))
    return findings, None


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
        # Do not display the actual line or matched text: it may contain a live credential.
        print(f"HIT: {finding.path}:{finding.line}: category={finding.category}; matched value redacted")
    if errors:
        return 2
    if all_findings:
        print(f"RESULT: {len(all_findings)} finding(s); inspect/redact locally. No matched values were printed.")
        return 1
    print(f"PASS: 0 configured-pattern matches across {len(args.paths)} file(s). This is not a guarantee that no secrets exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
