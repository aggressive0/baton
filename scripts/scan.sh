#!/bin/sh
# Portable POSIX/Git Bash wrapper; Python 3 is required.
set -eu
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3 is required; run: py -3 scripts/scan_secrets.py <files> on Windows." >&2
  exit 2
fi
exec python3 "$(dirname "$0")/scan_secrets.py" "$@"
