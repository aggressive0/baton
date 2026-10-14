# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.1] — 2026-10-14

### Fixed

- `safe-write` now validates, scans, and writes a single candidate byte snapshot rather than reopening the candidate after scanning.
- Post-save verification confirms the destination bytes exactly match the reviewed snapshot.
- False-positive allowances now include a SHA-256 digest of the entire matching line, so content changes invalidate prior approvals.
- Secret scanning now recognizes common compound environment variable assignments such as `OPENAI_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `CLIENT_SECRET`, and `GITHUB_TOKEN`.
- Added regression tests for candidate mutation after scanning, changed-content approvals, and compound environment variable names.

## [0.2.0] — 2026-10-14

### Added

- Explicit evidence statuses for completion claims: `verified`, `reported`, `unverified`, and `blocked`.
- `scripts/handoff.py` for structural validation, SHA-256 fingerprints, and safe-write with a cooperative lock and stale-version check.
- `scripts/scan_secrets.py`, which reports finding categories and line numbers without printing matched credential values.
- Optional append-only `HANDOFF.archive.md` for resolved pitfalls, so the active handoff can retain a real 120-line total cap.
- Risk-based READ behavior distinguishing reversible local work from destructive or external side effects.
- Regression-test scaffold for the validator, scanner, and write-conflict behavior.
- `MIGRATION.md` with the one-time v0.1.x to v0.2.0 handoff migration procedure.

### Changed

- READ no longer requires confirmation for every low-risk, reversible step; it pauses when intent, state, or action risk requires it.
- WRITE builds a candidate separately, validates/scans before save, checks a content fingerprint, and verifies the saved result.
- Documentation now states the limits of LOG, Git evidence, and secret scanning explicitly.
- PROMOTE now requires deduplication, conflict review, user confirmation, and post-edit verification.
- The active handoff limit includes frontmatter, blanks, and every other line. Resolved pitfalls move to a separate archive instead of an unbounded tail.

### Notes

- `safe-write` coordinates writers that use the helper; it cannot prevent a race with a manual editor or agent that bypasses it.
- The validator checks deterministic structure, not the truth of natural-language claims.
- The secret scanner detects configured patterns only and is not a substitute for manual review.

## [0.1.0] — 2026-10-13

Initial release. Two-way LOG / WRITE / READ / PROMOTE protocol, eight-section
handoff template, evidence-based rebuild, protected decision/pitfall entries,
line budgeting, optional secret scan guidance, Git drift checks, stale-write
policy, and worked good/bad examples.
