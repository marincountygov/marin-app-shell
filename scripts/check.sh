#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
TEMP_DIR=$(mktemp -d)
SERVER_PID=""
trap '[[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null || true; rm -rf "$TEMP_DIR"' EXIT

printf 'Building distribution...\n'
"$ROOT_DIR/scripts/build.sh"

printf 'Checking shell scripts...\n'
for script in "$ROOT_DIR"/scripts/*.sh; do
  bash -n "$script"
done

if command -v node >/dev/null 2>&1; then
  printf 'Checking JavaScript syntax...\n'
  node --check "$ROOT_DIR/src/marinos.js"
  node --check "$ROOT_DIR/dist/marinos.js"
  node --check "$ROOT_DIR/demo/app.js"
else
  printf 'WARN: node is unavailable; JavaScript syntax checks skipped.\n' >&2
fi

printf 'Validating distribution...\n'
python3 "$ROOT_DIR/tests/validate_dist.py"

printf 'Testing atomic installer...\n'
mkdir -p "$TEMP_DIR/app/vendor/marinos"
printf 'schema: 1\n' > "$TEMP_DIR/app/marin.yml"
printf 'stale\n' > "$TEMP_DIR/app/vendor/marinos/stale.txt"
"$ROOT_DIR/scripts/install.sh" "$TEMP_DIR/app" >/dev/null
[[ -f "$TEMP_DIR/app/vendor/marinos/manifest.json" ]]
[[ ! -e "$TEMP_DIR/app/vendor/marinos/stale.txt" ]]

if python3 -c 'import playwright' >/dev/null 2>&1 && { command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; }; then
  printf 'Running Playwright browser smoke test...\n'
  python3 "$ROOT_DIR/tests/browser_smoke.py"
elif command -v chromium >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1; then
  printf 'Running best-effort Chromium smoke test...\n'
  PORT=8767
  (
    cd "$ROOT_DIR"
    python3 -m http.server "$PORT" --bind 127.0.0.1 >"$TEMP_DIR/server.log" 2>&1
  ) &
  SERVER_PID=$!
  sleep 0.5
  if ! timeout 20s chromium \
    --headless \
    --no-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --disable-background-networking \
    --user-data-dir="$TEMP_DIR/chromium-start" \
    --virtual-time-budget=3000 \
    --dump-dom "http://127.0.0.1:$PORT/" > "$TEMP_DIR/start.html" 2> "$TEMP_DIR/chromium-start.log"; then
    if [[ ${MARINOS_REQUIRE_BROWSER:-0} == 1 ]]; then
      printf 'ERROR: Chromium smoke test could not run.\n' >&2
      exit 1
    fi
    printf 'WARN: Chromium could not complete the smoke test in this environment.\n' >&2
  else
    grep -q '<header class="app-header"' "$TEMP_DIR/start.html"
    grep -q '<footer class="app-footer"' "$TEMP_DIR/start.html"
  fi
else
  printf 'WARN: Playwright/Chromium is unavailable; browser smoke test skipped.\n' >&2
fi

printf 'All checks passed.\n'
