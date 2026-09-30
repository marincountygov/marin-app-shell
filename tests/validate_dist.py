#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


version = (ROOT / "SHELL_VERSION").read_text(encoding="utf-8").strip()
ui_version = (ROOT / "MARIN_UI_VERSION").read_text(encoding="utf-8").strip()
manifest_path = DIST / "manifest.json"
require(manifest_path.is_file(), "dist/manifest.json is missing")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
require(manifest.get("shellVersion") == version, "manifest shellVersion does not match SHELL_VERSION")
require(manifest.get("marinUiVersion") == ui_version, "manifest marinUiVersion does not match MARIN_UI_VERSION")
require(manifest.get("installPath") == "vendor/marinos", "manifest installPath changed")

manifest_files = manifest.get("files")
require(isinstance(manifest_files, dict) and manifest_files, "manifest file map is empty")
actual_files = {
    path.relative_to(DIST).as_posix(): path
    for path in DIST.rglob("*")
    if path.is_file() and path.name != "manifest.json"
}
require(set(manifest_files) == set(actual_files), "manifest file map does not match dist contents")

for relative, path in actual_files.items():
    data = path.read_bytes()
    expected = manifest_files[relative]
    require(expected.get("bytes") == len(data), f"byte count mismatch for {relative}")
    require(
        expected.get("sha256") == hashlib.sha256(data).hexdigest(),
        f"SHA-256 mismatch for {relative}",
    )

css = (DIST / "marinos.css").read_text(encoding="utf-8")
js = (DIST / "marinos.js").read_text(encoding="utf-8")
index = (ROOT / "index.html").read_text(encoding="utf-8")

for placeholder in ("__SHELL_VERSION__", "__MARIN_UI_VERSION__"):
    require(placeholder not in css, f"unreplaced placeholder in dist/marinos.css: {placeholder}")
    require(placeholder not in js, f"unreplaced placeholder in dist/marinos.js: {placeholder}")

for component in (
    "marin-os-banner",
    "marin-app-header",
    "marin-app-info",
    "marin-app-footer",
    "marin-app-feedback",
):
    require(f'"{component}"' in js, f"component is not registered in JS: {component}")
    require(f"<{component}" in index, f"root demo does not use component: {component}")

for selector in (
    ".marinos-banner",
    ".app-header",
    ".app-footer__nav",
    ".app-feedback",
):
    require(selector in css, f"required selector missing from CSS: {selector}")

require(f'const SHELL_VERSION = "{version}";' in js, "built JS version constant is incorrect")
require(f'const MARIN_UI_VERSION = "{ui_version}";' in js, "built JS Marin UI version is incorrect")
require("../fonts/Jost-wght.ttf" in css, "Jost font path contract changed")
require(
    "../fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2" in css,
    "Open Sans font path contract changed",
)

json.loads((ROOT / "security.json").read_text(encoding="utf-8"))
json.loads((ROOT / "demo/catalog.json").read_text(encoding="utf-8"))
print("validate_dist.py: PASS")
