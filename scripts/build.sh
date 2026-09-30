#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
VERSION=$(tr -d '[:space:]' < "$ROOT_DIR/SHELL_VERSION")
MARIN_UI_VERSION=$(tr -d '[:space:]' < "$ROOT_DIR/MARIN_UI_VERSION")
DIST_DIR="$ROOT_DIR/dist"
TEMP_DIR=$(mktemp -d "$ROOT_DIR/.dist.XXXXXX")
trap 'rm -rf "$TEMP_DIR"' EXIT

replace_versions() {
  sed \
    -e "s/__SHELL_VERSION__/$VERSION/g" \
    -e "s/__MARIN_UI_VERSION__/$MARIN_UI_VERSION/g"
}

mkdir -p "$TEMP_DIR/licenses"

{
  printf '/* Pico CSS plus Marin App Shell. See licenses/ and manifest.json. */\n'
  cat "$ROOT_DIR/vendor/pico.min.css"
  printf '\n'
  replace_versions < "$ROOT_DIR/src/marinos.css"
} > "$TEMP_DIR/marinos.css"

replace_versions < "$ROOT_DIR/src/marinos.js" > "$TEMP_DIR/marinos.js"
replace_versions < "$ROOT_DIR/src/DIST_README.md" > "$TEMP_DIR/README.md"
cp "$ROOT_DIR/LICENSE" "$TEMP_DIR/licenses/MARIN_APP_SHELL_LICENSE.txt"
cp "$ROOT_DIR/vendor/licenses/LUCIDE_LICENSE.txt" "$TEMP_DIR/licenses/LUCIDE_LICENSE.txt"
cp "$ROOT_DIR/vendor/licenses/OPEN_SANS_OFL.txt" "$TEMP_DIR/licenses/OPEN_SANS_OFL.txt"

python3 - "$TEMP_DIR" "$VERSION" "$MARIN_UI_VERSION" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
version = sys.argv[2]
ui_version = sys.argv[3]
files: dict[str, dict[str, object]] = {}
for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"):
    data = path.read_bytes()
    files[path.relative_to(root).as_posix()] = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }

manifest = {
    "schema": 1,
    "name": "Marin App Shell",
    "shellVersion": version,
    "marinUiVersion": ui_version,
    "installPath": "vendor/marinos",
    "fontPathContract": [
        "../fonts/Jost-wght.ttf",
        "../fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2",
    ],
    "files": files,
}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

rm -rf "$DIST_DIR"
mv "$TEMP_DIR" "$DIST_DIR"
trap - EXIT
printf 'Built Marin App Shell %s in %s\n' "$VERSION" "$DIST_DIR"
