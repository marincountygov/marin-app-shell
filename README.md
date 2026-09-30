# Marin App Shell

Marin App Shell is the versioned runtime shared by MarinOS applications. It separates the parts that should remain consistent across applications from `marin-app-template`, which remains a starting point for new work.

Applications vendor a pinned shell release into their own repository. They do not fetch a live shell from another site and do not require Node, a package manager, or a deployment build.

## What the shell owns

- MarinOS banner and catalog menu
- Application header and responsive navigation
- About, Security, Accessibility, and Updates section framework
- Footer and Feedback control
- Hash-based section routing
- Shared Marin UI CSS and Pico baseline
- Common copy, share, table sorting, document navigation, Updates, and Security behaviors

Applications continue to own their primary workflow, application-specific content, `security.json`, CSS, JavaScript, and deployment.

## Distribution contract

The committed `dist/` directory is the complete shell package. Copy it unchanged to:

```text
APP_REPOSITORY/vendor/marinos/
```

The package contains:

```text
vendor/marinos/
├── marinos.css
├── marinos.js
├── manifest.json
├── README.md
└── licenses/
```

The shell CSS expects the existing MarinOS font assets at stable application-level paths:

```text
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
```

Applications remain functional with fallback fonts when those files are missing, but published MarinOS apps should retain the self-hosted font files already present in the current template.

Do not edit `vendor/marinos/` inside an application. Upgrade by replacing the entire directory with another tagged shell release.

## Minimal integration

Load the shell before app-specific assets:

```html
<link rel="stylesheet" href="vendor/marinos/marinos.css">
<link rel="stylesheet" href="assets/app.css">
<script src="vendor/marinos/marinos.js" defer></script>
<script src="assets/app.js" defer></script>
```

Use the components in `body`:

```html
<marin-os-banner></marin-os-banner>

<marin-app-header
  app-name="Marin Unzipper"
  app-description="Decrypt and decompress ZIP files locally in your browser."
></marin-app-header>

<main id="main" class="container app-main">
  <section id="start" data-tab-section="start">
    <!-- Application-owned workflow -->
  </section>

  <marin-app-info
    app-name="Marin Unzipper"
    repo="marin-unzipper"
    security-src="security.json"
  >
    <template data-about>
      <p>Application-specific About content.</p>
    </template>
    <template data-accessibility>
      <p>Application-specific accessibility information.</p>
    </template>
  </marin-app-info>
</main>

<marin-app-footer app-name="Marin Unzipper"></marin-app-footer>
<marin-app-feedback></marin-app-feedback>
```

The shell inserts the skip link, the main live-status region, and standard information-section markup. Components render into light DOM so the resulting HTML remains inspectable and standard hash links continue to work.

## Record the dependency

A consuming app should replace template-tracking metadata with its pinned shell release:

```yaml
platform:
  shell: 1.0.0
```

During migration, an app may retain `templateVersion` as provenance, but MarinOS maintenance should use `platform.shell` as the update target.

## Install into an app

From this repository:

```bash
./scripts/install.sh ../marin-unzipper
```

The installer atomically replaces `APP/vendor/marinos/`. It deliberately does not rewrite application HTML or `marin.yml`.

## Local development

No build is required to run a consuming app. Serve it over localhost so `fetch()` works:

```bash
python3 -m http.server 8765
```

For this repository's demonstration:

```bash
python3 -m http.server 8765
```

Then open `http://127.0.0.1:8765/`.

The root demo uses fallback fonts unless the existing MarinOS fonts have been copied locally:

```bash
./scripts/sync-fonts.sh ../marin-app-template
```

## Shell development

The shell source is maintained in:

```text
src/marinos.js
src/marinos.css
```

Pico and license inputs are under `vendor/`. Regenerate `dist/` with:

```bash
./scripts/build.sh
```

Run the complete validation and browser smoke test with:

```bash
./scripts/check.sh
```

The build uses Bash and Python only. JavaScript syntax validation uses Node when available. Browser smoke testing uses Python Playwright with a locally installed Chromium when available, with a best-effort Chromium fallback.

## Component reference

See [docs/components.md](docs/components.md).

## Migration from the copied template structure

See [docs/migration.md](docs/migration.md).

## Versioning

See [docs/versioning.md](docs/versioning.md). The shell begins at `1.0.0` and uses semantic versioning. Component names, required attributes, standard section IDs, and the `vendor/marinos/` distribution contract are public API.
