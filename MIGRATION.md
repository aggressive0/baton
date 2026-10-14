# Migrating existing handoffs for Verifiable Session Handoff from 0.1.x to 0.2.0

This release changes the handoff schema. **Do not expect an existing 0.1.x
`HANDOFF.md` to pass the 0.2 validator unchanged.** Use the first WRITE after
upgrading to rebuild it into schema version 2.

## Before migrating

1. Back up the current `HANDOFF.md` and any existing archive. Do not edit the
   only copy of protected user decisions or pitfalls.
2. In the current project, read the old handoff and compute its fingerprint:

   ```bash
   python scripts/handoff.py fingerprint HANDOFF.md
   ```

3. Keep the old file as the source while preparing a separate schema-v2
   candidate. Do not overwrite the target during drafting.

## Field and section mapping

- Add `schema_version: 2`.
- Replace old `# 3. Completed` with `# 3. Completed / claims`. Treat old
  completion claims as `reported` unless you re-check them now and record
  current evidence and scope. Claims without supporting evidence become
  `unverified` or `blocked`, not `verified`.
- Replace old `# 8. Open questions` with
  `# 8. Open questions / PROMOTE candidates`.
- Convert inline `git: { ... }` frontmatter into a `git` block with `branch`,
  `head`, `dirty`, and `scope`. Re-read these values from the actual repository;
  do not blindly reuse old values. `dirty` describes the snapshot before the
  handoff is saved.
- Set `captured: log` only when the protected entries were actually appended
  during the current session and their persistence was checked. Otherwise use
  `captured: reconstructed`.
- Ensure every verified claim line includes `evidence:` and `scope:`. Evidence
  from an earlier code state should be `reported` until it is checked again.
- Ensure numbered next steps have a `verify:` command or explicitly say
  `manual verification` and explain what result to inspect.

## Preserve protected history

- Carry Section 1 user requirement quotes and all Section 2 rejections forward
  verbatim. Append a reversal if the user later changed a decision; do not erase
  the original decision record.
- Carry unresolved Section 6 pitfalls forward verbatim. If the root cause is
  unknown, keep `root cause: unknown` rather than inventing one.
- If the old file has a trailing `## Archived` section, append those resolved
  pitfall entries to `HANDOFF.archive.md`, preserving their text and resolution
  markers. If the archive already exists, append; do not replace its contents.
  Re-read the archive to confirm the append before removing the old tail from
  the active handoff.
- Keep the new active `HANDOFF.md` at 120 lines or fewer, including frontmatter
  and blank lines. Do not truncate protected facts to achieve the cap. If they
  do not fit, split the task/state with the user's agreement.

## Validate before resuming normal writes

1. Run the configured secret scanner against each file that exists. Redact real
   secrets; the scanner's line/category output intentionally does not print the
   matched values.
2. Run `python scripts/handoff.py validate HANDOFF.candidate.md` (substitute
   your actual candidate path).
3. Save through `safe-write` using the fingerprint captured before drafting. If
   it reports a conflict, keep the candidate and reconcile both versions; do
   not force it over the newer file.
4. Re-read `HANDOFF.md`, validate it again, and check the SHA-256 result.

The migration is not complete merely because the Markdown headings changed.
Re-check user intent, stale task state, next-step commands, evidence statuses,
and archive persistence.
