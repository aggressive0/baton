# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-10-13

Initial release.

- Two-way protocol: WRITE (evidence-based rebuild at session end) and READ
  (git drift check, claim spot-checks, echo-back-and-confirm in new
  sessions)
- LOG: append-only protected sections for user-rejected approaches and
  pitfalls & bans, captured at event time (compaction-resilient)
- PROMOTE: durable knowledge moves to CLAUDE.md/AGENTS.md, keeping the
  handoff transient
- Anti-bloat rules: 120-line hard cap, rebuild-from-evidence on every
  write, protected content carried forward verbatim
- Secret scan before every write (HANDOFF.md is designed to be committed)
- `references/template.md` — 8-section template with per-field rules and
  compression order
- `references/examples.md` — worked good/bad examples with failure-cost
  analysis
- Stale-write check: WRITE refuses to overwrite a handoff that changed
  since the session last read it
- Protected-section exit valve: fixed pitfalls move to a tail
  `## Archived` section — outside the line budget, still append-only
- Per-section line budgets; timestamps and line counts captured by
  command (`date`, `wc -l`), never estimated
- Secret scan: full pattern list + human disposition flow in
  template.md; optional `scripts/scan.sh` for deterministic evidence
- Git edge cases: empty repo (`head: none`); no-git drift via content
  spot-checks, mtimes advisory only
- Branch-strategy guidance: merge often / personal-branch-only / optional
  `HANDOFF.<branch>.md`
