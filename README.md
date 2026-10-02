# Marin App Shell

Marin App Shell is the pinned, locally installed runtime for independent MarinOS
apps. It owns the banner, header, standard information sections, footer, navigation,
shared styling, and shared behavior. Apps own their workflows, content, security
configuration, and app-specific CSS/JavaScript.

## Version 1.1.0

This release restores the brand contract: first-party Open Sans for body/UI text,
Jost for headings, canonical local Lucide geometry, and the established header
spacing. The header identity remains a link to `./` (a full navigation that can
reset unsaved in-memory work). Existing component names and attributes are unchanged.

## Install into an app

Keep this checkout and `marin-ui` beside each other, then run:

```bash
bash scripts/install.sh ../marin-unzipper
```

The installer automatically synchronizes the required fonts; no separate per-app
font-copy step is needed. For another source location:

```bash
bash scripts/install.sh ../marin-unzipper --font-source /path/to/marin-ui
```

Font sources must match the release's locked byte counts and SHA-256 hashes.
A matching local cache at `fonts/` is preferred over a sibling checkout; an explicit
`--font-source` takes precedence. An incomplete/mismatched cache fails with a clear
error rather than silently substituting another typeface. Prepare a verified
cache (also used by the root demo) when needed:

```bash
bash scripts/sync-fonts.sh ../marin-ui
```

Font binaries are hydrated from local source and ignored by Git. A fresh
checkout needs either a matching local `marin-ui` checkout or a prepared cache.
No script fetches fonts from the network. After installation the **app is fully
self-contained** and needs neither source repository at runtime.

### Managed paths

The installer replaces `vendor/marinos/` and synchronizes only these companion files:

```text
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
vendor/fonts/open-sans/OFL.txt
vendor/icons/lucide/layout-grid.svg
vendor/icons/lucide/chevron-down.svg
vendor/icons/lucide/copy.svg
vendor/icons/lucide/check.svg
vendor/icons/lucide/LICENSE
```

Unrelated fonts, app-specific icons, other vendor libraries, `index.html`, app code,
security files, and `marin.yml` are not changed. Update the app's version manually:

```yaml
platform:
  shell: 1.1.0
```

Inspect or verify without writing:

```bash
bash scripts/install.sh ../marin-unzipper --dry-run
bash scripts/install.sh ../marin-unzipper --check
```

`--check` verifies the installed shell and companion hashes; it does not claim the
app metadata, icon/catalog parity, deployment, or accessibility has been reviewed.

All inputs are checked and staged before replacement. Handled filesystem errors
and interrupts roll back managed paths. This is not a multi-directory atomic
transaction: a power failure or forced kill can leave a `.marinos-install.*`
backup directory and `.marinos-install.lock`. Stop concurrent work, inspect the
lock's `transaction.txt`, and recover the saved `old/` paths before removing them.
Never automatically delete a leftover backup or another process's lock.

## Minimal integration

```html
<link rel="stylesheet" href="vendor/marinos/marinos.css">
<link rel="stylesheet" href="assets/app.css">
<script src="vendor/marinos/marinos.js" defer></script>
<script src="assets/app.js" defer></script>

<marin-os-banner></marin-os-banner>
<marin-app-header app-name="APP_NAME" app-description="APP_DESCRIPTION">
  <!-- Supply template[data-icon] from the app's vendored Lucide SVG. -->
</marin-app-header>
<main id="main" class="container app-main">
  <section id="start" data-tab-section="start"><!-- App workflow --></section>
  <marin-app-info app-name="APP_NAME" repo="APP_REPO" security-src="security.json">
    <template data-about><p>App-specific About content.</p></template>
  </marin-app-info>
</main>
<marin-app-footer app-name="APP_NAME"></marin-app-footer>
<marin-app-feedback></marin-app-feedback>
```

Use one app-selected Lucide icon consistently in its header, favicon, and catalog
entry. A missing custom icon uses the bundled Lucide `layout-grid`, not invented
geometry. The shell does not rewrite app-specific icons or the separate MarinOS
catalog. See [components](docs/components.md) and [integration](docs/integration.md).

## Source layers and reproducible builds

```text
vendor/pico.min.css                    pinned base
vendor/marin-ui/app-brand.css          byte-identical reviewed UI snapshot
vendor/marin-ui/lock.json              provenance and hashes, including fonts
vendor/icons/lucide/                   only the four shell-owned icons + license
src/brand-compat.css                   documented policy corrections pending upstream
src/shell.css                         web-component integration and footer
src/marinos.js                        behavior; icon map generated from SVG files
             -> scripts/build.sh -> dist/
```

The current UI input is the supplied Marin Mentions 1.18.0 consumer snapshot,
not an assertion that upstream `main` remains identical. The build uses only
these pinned inputs, never whatever a sibling repo happens to contain.
Font URL rebasing and removal of legacy SVG stroke CSS are counted adapters;
upstream structure changes fail and require review rather than a fuzzy rewrite.

An intentional upstream refresh is separate from an app installation:

```bash
bash scripts/sync-ui.sh ../marin-ui
# Review the locked inputs, compatibility adapters, demo icon parity and metadata.
bash scripts/build.sh
bash scripts/check.sh
```

The source checkout is read-only. If it is a Git checkout, commit/review its changes
before importing. Update `MARIN_UI_VERSION`, `marin.yml`, demo references and docs
when adopting another version; the import updates the version pin and lock but
does not manufacture a completed visual review.

## Validation and local review

```bash
bash scripts/check.sh
bash scripts/check.sh --browser --font-source ../marin-ui
```

The default checks do not mutate `dist/`: they verify reproducibility, input hashes,
brand policy, source/manifest integrity, installer preflight, rollback, preservation
of unrelated files, and deterministic output. Python 3.10+ and Bash are required.
JavaScript syntax checks use Node when available and explicitly report a skip.
No production Node/runtime package manager is introduced.

`--browser` requires Python Playwright, Chromium and real, hash-verified fonts. It
runs an in-memory browser fixture: real local font bytes are loaded via Blob URLs,
then decoded/rendered fonts, header geometry, icons, routes, menus, dark mode and
focus are inspected. It is **not** a localhost navigation, network/CSP or deployed
HTTP test. `tests/browser_http.py` provides a separate HTTP-loading check:

```bash
python3 tests/browser_http.py --font-source ../marin-ui
```

For manual review of this repository, prepare the font cache, then serve the root:

```bash
bash scripts/sync-fonts.sh ../marin-ui
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Confirm local font requests succeed, the app identity
returns home, information routes work, and the page is usable with a keyboard at
narrow widths in light/dark modes. Keep `font-src 'self'` in consuming apps; the
production CSS contains no `local()`, CDN, Blob, or data font sources.

See [versioning](docs/versioning.md), [migration](docs/migration.md) and
[brand implementation](docs/brand.md). Generated `dist/` is committed unchanged;
never patch vendor files in individual applications.
