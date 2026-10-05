# Brand implementation and provenance

## Controlling requirements

The user-supplied `marin-digital-standards/brand/typography.md` and
`iconography.md` govern this release. Open Sans is body/UI, Jost is headings;
Lucide SVG source attributes and geometry are retained. `identity.md`'s older
four-square-per-app language conflicts with the more specific one-icon-per-app
iconography rule: this release keeps the MarinOS mark as `layout-grid` and does
not replace apps' selected icons. Owners should reconcile that wording upstream.

## What is pinned

`vendor/marin-ui/app-brand.css` is byte-identical to the supplied Marin UI 1.19.0
checkout. `vendor/marin-ui/lock.json` records the imported `BRAND_VERSION`, file
hashes, and provenance. The default build checks those hashes; it does not download
or automatically adopt upstream `main`.

The old shell copied and edited the entire UI stylesheet. Version 1.1.0 removed
that fork (`src/marinos.css`) in favor of an upstream input and small, named adapters.
Version 1.2.0 explicitly refreshes that pinned input to Marin UI 1.19.0 so the shell
uses the canonical Alpha/Beta/Live status-badge presentation rather than copying it
into a shell-specific override. The pending Alpha dark-mode contrast refinement is
not part of this import.

## Font paths and consumption

The release locks Jost, Open Sans and the supplied Open Sans OFL license by hash.
`install.sh` synchronizes those exact files from local Marin UI (or a verified
cache) into standard `APP/vendor/fonts/` paths. Missing/corrupt files fail before
app changes, not merely warn. CSS never prefers a machine-installed `local()` font.
The two URLs are rebased from `../vendor/fonts/` in the source brand bundle to
`../fonts/` in the installed `vendor/marinos/marinos.css`.

In 1.1.1, the app's existing `marin.yml` `platform.shell` scalar is staged and
updated in the same rollback-protected installation as these managed assets. This
does not expand the brand surface: no unrelated app CSS, icons, security content,
or other manifest fields are rewritten.

The upstream body and h1-h6/.app-title selectors actually consume the font tokens.
Both Pico token variants are set in the compatibility layer. Navigation and footer
labels use the body font rather than the old heading-font overrides. CSS/system
fallbacks remain for resilience; they are not a passing release-validation state.

## Icon pipeline

Four shell SVGs are copied verbatim from the supplied local Lucide subset:
`layout-grid`, `chevron-down`, `copy`, and `check`. A build parser validates safe
geometry and the standard attributes, then embeds the original child markup in
JS. No icon geometry is hand-transcribed into `src/marinos.js`. Runtime attributes
carry `fill=none`, `stroke=currentColor`, width 2 and rounded line caps/joins.

The build removes historical paint/stroke declarations from six known SVG CSS
rules; dimension/display rules remain. `src/brand-compat.css` and build adapters
are temporary until the canonical UI source contains equivalent fixes. Apps do
not receive another independent stylesheet to override these.

1.0.x caller-supplied SVGs missing presentation attributes receive defaults,
without altering their paths. Attribute-absence-only compatibility CSS also
covers app-owned icons inserted after initialization; it never overrides an
explicit Lucide presentation attribute. That compatibility measure does not certify custom
geometry as Lucide. New icons must use the complete vendored SVG. Static fallback
catalog links are text-only instead of carrying separate, potentially stale app
icon geometry. Live catalog markup still goes through the SVG allowlist sanitizer.

The shell demo uses the same layout-grid geometry in its header, rounded-square
favicon and local catalog. `demo/catalog-entry.json` supplies that geometry for a
separate review of the real `marin-os/catalog.json`; this release does not edit that
other repository or presume the shell already has a published catalog entry.

## Header identity and status

Marin UI 1.19.0 makes `.app-title-row` a plain flex container. Only the application
name uses `.app-title__link` to navigate to `./`; the icon and subtitle are not part
of that link. This allows `.app-title__status` to be a separate link to MarinOS's
status guidance without invalid nested anchors. The inner header, icon size,
title-row gap, and gold border retain the shared UI values.

Alpha/Beta/Live badge colors come directly from the pinned Marin UI input. The shell
adds no additional status-color override. Catalog status is used at runtime because
a static browser page does not parse `marin.yml`; consuming repositories keep the
catalog value synchronized with their canonical `project.status`.

Pico also used `body > header`/`body > footer` to apply outer block padding.
Custom-element hosts changed that direct-child relationship. `src/shell.css`
explicitly restores the same outer padding on the generated header/footer.

## Scope of validation

Automated source checks cover consumption, hashes, paths, prohibited static CDNs,
canonical owned SVGs, and icon parity. Browser fixtures use the actual fonts and
inspect both FontFace load state and Chromium's rendered-font report, not just a
computed family string. Installer regression tests separately cover the
`platform.shell` metadata update, preservation, failure handling, and rollback.
An HTTP integration check remains separate; a brand check is not a full
accessibility, security, or platform-availability certification.
