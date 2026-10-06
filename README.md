# Marin App Shell

Marin App Shell is the pinned, locally installed runtime for independent MarinOS
apps. It owns the banner, header, standard information sections, footer, navigation,
shared styling, and shared behavior. Apps own their workflows, content, security
configuration, and app-specific CSS/JavaScript.

## Version 1.6.0

Version 1.6.0 adds the shared ARIA tabs keyboard pattern (arrow keys, Home/End, one Tab stop) to every `role="tablist"`, and includes the 1.5.1 contrast fix.

## Version 1.5.1

Version 1.5.1 fixes low-contrast accent text on tinted backgrounds (current nav link, hovered menu items) in light mode.

## Version 1.5.0

Version 1.5.0 makes About, Security, Accessibility, and Updates required footer
links for every MarinOS app. Apps can prepend app-specific links with
`template[data-footer-links]`, and platform-level apps can omit the separate
bottom MarinOS platform link with `hide-platform-link`. The default footer for
ordinary applications is unchanged.

## Version 1.4.0

Version 1.4.0 shows the accessibility score as a color-banded gauge (with the number and band word always printed).

## Version 1.3.0

Version 1.3.0 adds each app's Google Lighthouse accessibility score, the WCAG 2.2 Level AA statement, and an accessibility issue link to the standard Accessibility section.

## Version 1.2.2

Version 1.2.2 improves the Alpha status badge in dark mode by using the County gold
background with black text. This compatibility override is local to App Shell; Marin UI
1.19.0 remains pinned unchanged, and Beta/Live presentation is unaffected.

Version 1.2.1 makes the local application header read the recognized `alpha`, `beta`,
or `live` value from the app's own `marin.yml` `project.status` and render the shared
status badge beside `.app-title`. Catalog matching remains as the compatibility fallback
when the local manifest is unavailable or does not contain a recognized maturity value.

Version 1.2.0 imports the reviewed Marin UI 1.19.0 baseline and adds MarinOS
application-maturity status rendering. Catalog entries with `alpha`, `beta`, or
`live` status render the shared `.app-status` badge in the MarinOS menu. The current
application receives the same badge beside its name when the shell can match it to
the catalog.

Only the `.app-title` application name now links to `./`; the icon and subtitle are
not part of the home link. This lets the status badge link independently to MarinOS
status guidance without nested links. Existing component elements remain valid; an
optional `app-id` on `marin-app-header` improves local-development matching when the
page URL cannot match the production catalog URL.

Version 1.1.3 fixed legacy 48x48 icon stroke defaults while preserving explicit
widths and canonical 24x24 Lucide icons. See
[Icon stroke compatibility](docs/icon-compatibility.md) for that upgrade contract.

Version 1.1.1 established installer synchronization of the consuming app's existing
`marin.yml` `platform.shell` value. Version 1.1.0 established the pinned brand, font,
and icon pipeline.

## Install into an app

Keep this checkout and `marin-ui` beside each other, then run:

```bash
bash scripts/install.sh ../marin-unzipper
```

The target app must already contain a supported `marin.yml` with one
`platform.shell` scalar. The installer updates only that scalar to the release being
installed. It refuses missing, duplicate, or unsupported manifest structures rather
than attempting a first-time structural migration. See [migration](docs/migration.md)
for the one-time conversion of an older app.

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

The installer replaces `vendor/marinos/`, synchronizes only these companion files,
and updates the existing `marin.yml` shell-version scalar:

```text
vendor/marinos/
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
vendor/fonts/open-sans/OFL.txt
vendor/icons/lucide/layout-grid.svg
vendor/icons/lucide/chevron-down.svg
vendor/icons/lucide/copy.svg
vendor/icons/lucide/check.svg
vendor/icons/lucide/LICENSE
marin.yml -> platform.shell only
```

Unrelated fonts, app-specific icons, other vendor libraries, `index.html`, app code,
and security files are not changed. Within `marin.yml`, unrelated content,
comments, quoting, line endings, and file permissions are preserved wherever the
supported manifest format permits.

Inspect or verify without writing:

```bash
bash scripts/install.sh ../marin-unzipper --dry-run
bash scripts/install.sh ../marin-unzipper --check
```

`--dry-run` reports the `platform.shell` transition and managed asset changes without
writing them. `--check` verifies the installed shell and companion hashes and also
requires `marin.yml` `platform.shell` to match the installed release. It does not
claim icon/catalog parity, deployment, accessibility, or security review has been
completed.

All inputs are checked and staged before replacement. The manifest update is part
of the same rollback-protected installation and is committed last after the managed
assets are prepared. Handled filesystem errors and interrupts roll back managed
paths and the original manifest. This is not a filesystem-wide atomic transaction:
a power failure or forced kill can leave a `.marinos-install.*` backup directory
and `.marinos-install.lock`. Stop concurrent work, inspect the lock's
`transaction.txt`, and recover the saved `old/` paths before removing them. Never
automatically delete a leftover backup or another process's lock.

## Minimal integration

```html
<link rel="stylesheet" href="vendor/marinos/marinos.css">
<link rel="stylesheet" href="assets/app.css">
<script src="vendor/marinos/marinos.js" defer></script>
<script src="assets/app.js" defer></script>

<marin-os-banner></marin-os-banner>
<marin-app-header app-name="APP_NAME" app-description="APP_DESCRIPTION" app-id="APP_ID">
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

The current UI input is an explicit import of the supplied Marin UI 1.19.0 checkout.
The lock records its hashes and provenance. The build uses only these pinned inputs,
never whatever a sibling repo happens to contain.
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
