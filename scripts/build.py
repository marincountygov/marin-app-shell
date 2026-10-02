#!/usr/bin/env python3
"""Build only from reviewed, hash-locked local inputs. Font binaries stay at app paths."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from assets import ROOT, ICON_NAMES, SVG_ATTRIBUTES, AssetError, digest, require, verify_inputs, verify_file


def icons(root: Path) -> dict[str, str]:
    result = {}
    allowed = {"path", "rect", "circle", "line", "polyline", "polygon", "ellipse"}
    attrs = {"d", "x", "y", "x1", "x2", "y1", "y2", "width", "height", "rx", "ry", "cx", "cy", "r", "points"}
    for name in ICON_NAMES:
        text = (root / f"vendor/icons/lucide/{name}.svg").read_text(encoding="utf-8").strip()
        element = ET.fromstring(text)
        require(element.tag == "{http://www.w3.org/2000/svg}svg", f"Invalid SVG root: {name}")
        for key, value in SVG_ATTRIBUTES.items():
            require(element.get(key) == value, f"Noncanonical Lucide {key}: {name}")
        for child in element.iter():
            if child is element:
                continue
            require(child.tag.split("}")[-1] in allowed, f"Unsafe SVG element in {name}")
            require(set(child.attrib) <= attrs and len(child) == 0, f"Unsafe SVG attributes/nesting in {name}")
        match = re.fullmatch(r"<svg\b[^>]*>(.*)</svg>", text, re.S)
        require(match is not None and bool(match[1].strip()), f"No SVG geometry: {name}")
        # Preserve exact original child markup/path data rather than serializing/redrawing it.
        result[name] = match[1].strip()
    return result


def adapt_brand(css: str) -> str:
    """Small, counted adapters only; the input file remains byte-for-byte upstream."""
    require('local(' not in css, "Pinned brand input must not prefer machine-installed fonts")
    for path in ("Jost-wght.ttf", "open-sans/OpenSans-VariableFont_wdth,wght.woff2"):
        old = f'url("../vendor/fonts/{path}")'
        require(css.count(old) == 1, f"Expected exactly one upstream font URL: {path}")
        css = css.replace(old, f'url("../fonts/{path}")')
    selectors = (".marinos-menu__icon svg", ".marinos-banner__icon svg", ".menu-toggle__caret",
                 ".app-icon svg,\n.app-card__icon svg", ".copy-button svg", ".docs-brand-icon svg")
    for selector in selectors:
        pattern = r"^" + re.escape(selector) + r" \{([^{}]*)\}"
        matches = list(re.finditer(pattern, css, re.M))
        require(len(matches) == 1, f"Brand adapter needs review for selector: {selector}")
        original = matches[0]
        declarations = original[1]
        require("stroke-width:" in declarations, f"SVG adapter is stale; review upstream rule: {selector}")
        declarations = re.sub(r"^  (?:fill|stroke|stroke-width|stroke-linecap|stroke-linejoin):[^\n]*\n", "", declarations, flags=re.M)
        css = css[:original.start()] + selector + " {" + declarations + "}" + css[original.end():]
    return css


def expected_distribution(root: Path = ROOT) -> dict[str, bytes]:
    lock = verify_inputs(root)
    verify_file(root / "vendor/licenses/OPEN_SANS_OFL.txt", lock["fonts"]["vendor/fonts/open-sans/OFL.txt"], "Open Sans license input")
    version = (root / "SHELL_VERSION").read_text().strip()
    ui_version = lock["marinUiVersion"]
    require(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None, "Invalid SHELL_VERSION")
    icon_map = icons(root)
    def expand(text: str) -> str:
        return text.replace("__SHELL_VERSION__", version).replace("__MARIN_UI_VERSION__", ui_version)
    css = ("/* Generated: Pico + pinned Marin UI + policy adapters + shell integration. */\n"
           + (root / "vendor/pico.min.css").read_text() + "\n"
           + adapt_brand((root / "vendor/marin-ui/app-brand.css").read_text()) + "\n"
           + (root / "src/brand-compat.css").read_text() + "\n"
           + expand((root / "src/shell.css").read_text()))
    js = expand((root / "src/marinos.js").read_text())
    require(js.count("__LUCIDE_ICONS__") == 1, "Expected one generated Lucide input slot")
    js = js.replace("__LUCIDE_ICONS__", json.dumps(icon_map, ensure_ascii=True, sort_keys=True))
    files = {"marinos.css": css.encode(), "marinos.js": js.encode(),
             "README.md": expand((root / "src/DIST_README.md").read_text()).encode(),
             "brand-source.json": (json.dumps(lock, indent=2) + "\n").encode()}
    for source, dest in (("LICENSE", "licenses/MARIN_APP_SHELL_LICENSE.txt"),
                         ("vendor/icons/lucide/LICENSE", "licenses/LUCIDE_LICENSE.txt"),
                         ("vendor/licenses/OPEN_SANS_OFL.txt", "licenses/OPEN_SANS_OFL.txt")):
        files[dest] = (root / source).read_bytes()
    for name in ICON_NAMES:
        files[f"icons/lucide/{name}.svg"] = (root / f"vendor/icons/lucide/{name}.svg").read_bytes()
    files["icons/lucide/LICENSE"] = (root / "vendor/icons/lucide/LICENSE").read_bytes()
    manifest = {
        "schema": 1, "name": "Marin App Shell", "shellVersion": version,
        "marinUiVersion": ui_version, "installPath": "vendor/marinos",
        "fontPathContract": ["../fonts/Jost-wght.ttf", "../fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2"],
        "fontAssets": {path: {k: v for k, v in meta.items() if k != "source"} for path, meta in lock["fonts"].items()},
        "companionIcons": {f"vendor/{path}": {"source": path, **digest(data)} for path, data in files.items() if path.startswith("icons/lucide/")},
        "files": {path: digest(data) for path, data in sorted(files.items())},
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files


def verify_distribution(root: Path = ROOT) -> dict:
    expected = expected_distribution(root)
    dist = root / "dist"
    require(dist.is_dir() and not dist.is_symlink(), "dist/ is missing or a symlink")
    actual = {p.relative_to(dist).as_posix(): p for p in dist.rglob("*") if p.is_file() or p.is_symlink()}
    require(set(actual) == set(expected), "Distribution file inventory is stale; run scripts/build.sh")
    for relative, data in expected.items():
        require(not actual[relative].is_symlink() and actual[relative].read_bytes() == data,
                f"Generated distribution is stale or modified: {relative}; run scripts/build.sh")
    return json.loads(expected["manifest.json"])


def build(root: Path = ROOT) -> None:
    files = expected_distribution(root)
    dist = root / "dist"
    require(not dist.is_symlink(), "Refusing symlink dist/")
    with tempfile.TemporaryDirectory(prefix=".dist.", dir=root) as temp:
        stage = Path(temp) / "new"
        stage.mkdir()
        for relative, data in files.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        backup = Path(temp) / "old"
        if dist.exists():
            dist.rename(backup)
        try:
            stage.rename(dist)
        except BaseException:
            if backup.exists():
                backup.rename(dist)
            raise
    print(f"Built Marin App Shell {json.loads(files['manifest.json'])['shellVersion']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify deterministic output without writing")
    args = parser.parse_args()
    if args.check:
        verify_distribution()
        print("Deterministic distribution: PASS")
    else:
        build()


if __name__ == "__main__":
    try:
        main()
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
