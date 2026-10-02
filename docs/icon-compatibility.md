# Icon stroke compatibility (1.1.2)

## Scope

Shell 1.1.2 corrects a compatibility default introduced in 1.1.0: legacy app
identity SVGs with 48x48 coordinates received the same missing stroke width as
24x24 Lucide SVGs. This patch does not redraw icons, change their viewBoxes,
replace app identities, or alter the canonical Lucide asset standard.

For shell-processed SVGs without an explicit root `stroke-width`:

| Coordinate system | Default stroke width |
| --- | --- |
| 48x48 viewBox | `4` |
| 24x24 viewBox | `2` |
| Missing, unrecognized, or other viewBox sizes | Previous fallback of `2` |

The helper parses numeric viewBox values, including comma/whitespace separators
and decimal spellings. Nonzero viewBox origins do not change the width/height
rule. No rendered geometry is measured. Rectangular and other-sized coordinate
systems are not guessed or automatically rescaled.

These defaults are used when cloning a header's `template[data-icon]`, creating
catalog SVGs, and processing the initial app-owned icon containers. Shell-owned
`layout-grid`, `chevron-down`, `copy`, and `check` remain 24x24 with stroke 2.
Catalog filtering and the primitive/attribute allowlists are unchanged.

## Explicit widths remain authoritative

A root `stroke-width="2"` in a consumer's source stays 2, even on a 48x48 SVG.
Likewise 4, 0, and other explicitly authored values are preserved. Child shapes'
explicit stroke widths, path data, and viewBox attributes are not rewritten.

A width seen only in the browser inspector may have been supplied by the old
shell. A fresh page load under 1.1.2 recomputes defaults from the original source.
If the incorrect value was instead copied into the app's `template[data-icon]`,
fix that app-owned source explicitly. Do not overwrite all SVGs with a global
CSS rule, and do not edit `vendor/marinos/` inside the app.

## Icons inserted by application JavaScript

The existing CSS-only fallback now handles late-inserted icons with the literal
`viewBox="0 0 48 48"` and no root stroke-width, using 4 rather than 2. It is scoped
to the same icon containers as the earlier fallback and does not change unrelated
SVG artwork. The canonical 24x24 fallback remains 2.

This CSS selector deliberately uses the canonical viewBox spelling. For
late-inserted application SVGs using alternative numeric spellings, nested
transforms, or other coordinate systems, include explicit presentation
attributes in the app-owned SVG. There is no new global DOM observer.

## Upgrade

Use a reviewed 1.1.2 shell checkout with a matching font source/cache:

```bash
bash scripts/install.sh ../app-name --dry-run
bash scripts/install.sh ../app-name
bash scripts/install.sh ../app-name --check
```

The installer updates an existing `platform.shell` to 1.1.2. It does not rewrite
app HTML or the separate MarinOS catalog. Review header/favicon/catalog parity;
this patch does not claim a legacy hand-drawn icon becomes a canonical Lucide
asset simply because its default weight is corrected.

## Validation

```bash
bash scripts/build.sh
bash scripts/check.sh
# Focused rendered stroke checks (Python Playwright + Chromium):
python3 tests/browser_icon_strokes.py
# Existing rendered font/navigation tests plus the stroke checks:
bash scripts/check.sh --browser --font-source ../marin-ui
```

The Node unit checks exercise the actual helper declarations from both source
and generated JS. They do not simulate rendering. Browser tests separately
exercise the full distribution, computed styles, header and catalog rendering,
explicit-width preservation, CSS-only late insertion, sanitization, and equivalent
visual stroke weight at equal rendered sizes. Those tests use in-memory fixtures;
`tests/browser_http.py` remains the separate HTTP-loading test and now reads the
release version dynamically.

The TOC/forced-layout timing change is intentionally not part of 1.1.2.
