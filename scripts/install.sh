#!/usr/bin/env bash
# The Python installer owns the asset and marin.yml transaction together.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
command -v python3 >/dev/null 2>&1 || {
  printf 'ERROR: Python 3.10 or later is required.\n' >&2
  exit 1
}
exec python3 -B "$SCRIPT_DIR/install.py" "$@"
