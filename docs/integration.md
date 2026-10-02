> **1.1.0 installation:** Use `bash scripts/install.sh /path/to/app`, not a
> manual `dist/`-only copy. The installer also synchronizes hash-verified fonts,
> their supplied Open Sans license, and shell Lucide assets at standard app paths.
> Read the current README for local source/cache requirements and recovery behavior.

# Integration contract

## Required document structure

A shell-based app should contain, in order:

1. `marin-os-banner`, unless the app has an approved reason to omit the MarinOS banner.
2. `marin-app-header`.
3. `main#main` containing the application-owned default section and `marin-app-info`.
4. `marin-app-footer`.
5. `marin-app-feedback`.

The primary application workflow must be inside a named tab section:

```html
<section id="start" data-tab-section="start">
  ...
</section>
```

The first `data-tab-section` in document order is the default when the URL has no recognized hash. Shell-generated information sections share the same routing group.

## Asset order

```html
<link rel="stylesheet" href="vendor/marinos/marinos.css">
<link rel="stylesheet" href="assets/app.css">
<script src="vendor/marinos/marinos.js" defer></script>
<script src="assets/app.js" defer></script>
```

App CSS loads after the shell to support legitimate app-specific rules. App CSS must not redefine shell-owned selectors such as `.app-header`, `.app-footer`, `.marinos-banner`, or their descendants. Scope application rules to application-specific classes or a workflow container.

## Font path contract

The vendored shell lives at `vendor/marinos/`. Its CSS resolves fonts one directory above:

```text
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
vendor/fonts/open-sans/OFL.txt
```

The installer verifies and synchronizes these files automatically from the release's
pinned local source. They remain outside `vendor/marinos/`, so URLs are stable and
unrelated fonts are preserved. Missing or mismatched required assets block installation.
Use the installer for each upgrade rather than copying only `dist/`.

## Content Security Policy

The shell itself is same-origin. Optional features can make these requests:

- MarinOS catalog menu: `https://marincountygov.github.io/marin-os/catalog.json`
- Updates section: `https://api.github.com`
- Security section: the app's same-origin `security.json`

A meta-delivered CSP that enables all shell features needs an appropriate `connect-src`, for example:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://api.github.com https://marincountygov.github.io; object-src 'none'; base-uri 'self'; form-action 'self'"
>
```

An app that disables the catalog or Updates behavior can use a narrower policy.

## Application metadata

Use the pinned shell version in `marin.yml`:

```yaml
platform:
  shell: 1.1.0
```

The release in `vendor/marinos/manifest.json` must match `platform.shell`. Maintenance automation should reject a mismatch.

## No runtime central dependency

Do not link an app directly to files hosted from the `marin-app-shell` GitHub Pages site. Each app must vendor the release locally so a shell change cannot alter already deployed apps without review.
