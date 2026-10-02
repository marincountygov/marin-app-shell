#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
BROWSER=0
FONT_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --browser) BROWSER=1; shift ;;
    --font-source)
      [[ $# -ge 2 ]] || { printf 'Missing --font-source path\n' >&2; exit 2; }
      FONT_ARGS=(--font-source "$2"); shift 2 ;;
    -h|--help)
      printf 'Usage: bash scripts/check.sh [--browser] [--font-source /path/to/marin-ui]\n'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
printf 'Checking shell syntax...\n'
for script in "$SCRIPT_DIR"/*.sh; do bash -n "$script"; done
printf 'Checking deterministic distribution and brand policy (no rebuild)...\n'
python3 "$ROOT_DIR/tests/validate_dist.py"
if command -v node >/dev/null 2>&1; then
  node --check "$ROOT_DIR/src/marinos.js"
  node --check "$ROOT_DIR/dist/marinos.js"
  node --check "$ROOT_DIR/demo/app.js"
else
  printf 'SKIP: Node unavailable; JavaScript syntax check not performed.\n' >&2
fi
printf 'Running release and installer regression tests...\n'
python3 "$ROOT_DIR/tests/test_release.py"
if [[ "$BROWSER" == 1 ]]; then
  python3 "$ROOT_DIR/tests/browser_smoke.py" "${FONT_ARGS[@]}"
else
  printf 'SKIP: Browser/font rendering not requested; add --browser for fixture checks.\n'
fi
printf 'Requested checks passed.\n'
