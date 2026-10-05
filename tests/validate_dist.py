#!/usr/bin/env python3
"""Static release/brand checks, with no external packages or font binary requirement."""
from __future__ import annotations
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from assets import AssetError, ICON_NAMES, SVG_ATTRIBUTES, require
from build import icons, verify_distribution


def validate(root: Path = ROOT) -> None:
    manifest = verify_distribution(root)
    css = (root / "dist/marinos.css").read_text()
    js = (root / "dist/marinos.js").read_text()
    index = (root / "index.html").read_text()
    source = (root / "src/marinos.js").read_text()
    for component in ("marin-os-banner", "marin-app-header", "marin-app-info", "marin-app-footer", "marin-app-feedback"):
        require(f'"{component}"' in js and f"<{component}" in index, f"Component/demo missing: {component}")
    for placeholder in ("__SHELL_VERSION__", "__MARIN_UI_VERSION__", "__LUCIDE_ICONS__"):
        require(placeholder not in js + css, f"Unexpanded placeholder: {placeholder}")
    require(not (root / "src/marinos.css").exists(), "Whole-brand CSS fork has returned")
    faces = re.findall(r"@font-face\s*\{([^{}]+)\}", css)
    require(len(faces) == 2 and all("local(" not in face for face in faces), "Font sources must be the two controlled local assets")
    for expected in manifest["fontPathContract"]:
        require(sum(f'url("{expected}")' in f for f in faces) == 1, f"Wrong font URL: {expected}")
    body_rules = re.findall(r"^body\s*\{([^{}]*)\}", css, re.M)
    require(any("font-family: var(--app-font-body)" in b for b in body_rules), "Body does not consume Open Sans token")
    require(re.search(r"h1,\s*h2,\s*h3,\s*h4,\s*h5,\s*h6,\s*\.app-title\s*\{[^{}]*font-family: var\(--app-font-heading\)", css) is not None,
            "Heading selectors do not consume Jost token")
    for status in ("alpha", "beta", "live"):
        require(f'.app-status[data-status="{status}"]' in css, f"Missing MarinOS {status} status styling")
    require(re.search(r'@media \(prefers-color-scheme: dark\) \{[\s\S]*?\.app-status\[data-status="alpha"\] \{[\s\S]*?background: var\(--app-warning\);[\s\S]*?color: var\(--marin-black\);', css) is not None,
            "Missing App Shell dark-mode Alpha contrast override")
    for marker in ("marinos-menu__status", "app-title__status", "marinos-banner__status", "marinos-catalog-cache-v3"):
        require(marker in js, f"Missing status runtime marker: {marker}")
    for selector in (".marinos-menu__icon svg", ".marinos-banner__icon svg", ".menu-toggle__caret",
                     ".app-icon svg,\n.app-card__icon svg", ".copy-button svg", ".docs-brand-icon svg"):
        blocks = re.findall(r"^" + re.escape(selector) + r"\s*\{([^{}]*)\}", css, re.M)
        require(bool(blocks) and all(re.search(r"(?:fill|stroke(?:-width|-linecap|-linejoin)?):", b) is None for b in blocks),
                f"CSS overrides intrinsic Lucide styling: {selector}")
    require('createGridIcon' not in source and 'setAttribute("d"' not in source, "Hand-built icon geometry has returned")
    require(re.search(r"<(?:path|rect|circle|polyline)\s", source) is None, "Icon geometry must come from the local SVG inputs")
    for domain in ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com"):
        require(domain not in css + js + index, f"External static-asset reference: {domain}")
    icon_map = icons(root)
    svg = (root / "vendor/icons/lucide/layout-grid.svg").read_text().strip()
    require(svg in index, "Demo header does not use the canonical local SVG")
    catalog = json.loads((root / "demo/catalog.json").read_text())
    require(catalog[0]["icon"]["markup"] == icon_map["layout-grid"], "Demo catalog icon drift")
    entry = json.loads((root / "demo/catalog-entry.json").read_text())
    require(entry["icon"] == catalog[0]["icon"], "Catalog review fragment has drifted")
    favicon = ET.fromstring((root / "demo/icon.svg").read_text())
    group = favicon.find("{http://www.w3.org/2000/svg}g")
    canonical = ET.fromstring(svg)
    require(group is not None and group.get("stroke-width") == "2", "Favicon Lucide stroke drift")
    require([(c.tag, c.attrib) for c in group] == [(c.tag, c.attrib) for c in canonical], "Favicon geometry drift")
    require(f"<code>{manifest['shellVersion']}</code>" in index, "Root demo version is stale")
    require(f"marin-ui: {manifest['marinUiVersion']}" in (root / "marin.yml").read_text(), "marin.yml UI baseline is stale")
    json.loads((root / "security.json").read_text())
    print("validate_dist.py: PASS")


if __name__ == "__main__":
    try:
        validate()
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
