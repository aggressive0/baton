#!/bin/sh
# baton — secret scan. Run before every WRITE save.
# Usage: sh scripts/scan.sh [HANDOFF.md]
#
# Exit 0 = no hits (paste this output as evidence).
# Exit 1 = hits found: review every one with the user before saving.
# Exit 2 = file not found.
#
# Note: the bare 40-char class also matches full hashes and base64 blobs;
# a hit is a candidate, the human decides. No regex catches everything —
# also eyeball for pasted .env / config blocks.

set -u
file="${1:-HANDOFF.md}"
[ -f "$file" ] || { echo "not found: $file"; exit 2; }

hits=$(grep -nE \
  'sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-|eyJ[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|[A-Za-z0-9/+=]{40}|\b(api_key|apikey|password|passwd|secret|token)\b|Authorization:' \
  "$file") || true

if [ -n "$hits" ]; then
  echo "HITS — review each with the user before saving:"
  echo "$hits"
  exit 1
fi

echo "0 hits — paste this line as scan evidence."
exit 0
