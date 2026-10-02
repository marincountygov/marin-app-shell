> **1.1.0 installation:** Use `bash scripts/install.sh /path/to/app`, not a
> manual `dist/`-only copy. The installer also synchronizes hash-verified fonts,
> their supplied Open Sans license, and shell Lucide assets at standard app paths.
> Read the current README for local source/cache requirements and recovery behavior.

# Migrate an existing MarinOS app

This migration is intentionally structural and should be performed once per app. Future routine updates use the installer to replace `vendor/marinos/` and synchronize its managed font/icon companions rather than rewriting app HTML or CSS.

## 1. Create a branch

```bash
git switch main
git pull --ff-only
git switch -c refactor/marin-app-shell-1.1.0
```

## 2. Install the shell

From a sibling `marin-app-shell` checkout:

```bash
./scripts/install.sh ../marin-unzipper
```

This creates or replaces:

```text
marin-unzipper/vendor/marinos/
```

The installer also synchronizes the two required fonts, Open Sans license, and four
shell-owned Lucide icons/license at standard `vendor/fonts/` and `vendor/icons/lucide/`
paths. It preserves unrelated files. Do not delete those existing directories.
A sibling `marin-ui` (or explicit `--font-source`) supplies the hash-pinned font bytes.

## 3. Replace shared asset references

Remove:

```html
<link rel="stylesheet" href="vendor/pico.min.css">
<link rel="stylesheet" href="shared/app-brand.css">
<script src="shared/app-shell.js"></script>
```

Add:

```html
<link rel="stylesheet" href="vendor/marinos/marinos.css">
<script src="vendor/marinos/marinos.js" defer></script>
```

Keep `assets/app.css` after the shell CSS and `assets/app.js` after the shell script.

## 4. Replace shell-owned markup

Replace the copied MarinOS banner with:

```html
<marin-os-banner></marin-os-banner>
```

Replace the copied application header with:

```html
<marin-app-header
  app-name="APP_NAME"
  app-description="APP_DESCRIPTION"
>
  <template data-icon>
    <!-- Complete SVG from the app-selected local Lucide source, reused in its favicon/catalog -->
  </template>
</marin-app-header>
```

Replace copied About, Security, Accessibility, and Updates sections with one component:

```html
<marin-app-info
  app-name="APP_NAME"
  repo="APP_REPO"
  security-src="security.json"
>
  <template data-about>
    <!-- Preserve app-specific About content, without the h2 heading. -->
  </template>
  <template data-accessibility>
    <!-- Preserve app-specific accessibility content, without the h2 heading. -->
  </template>
</marin-app-info>
```

Replace the copied footer and Feedback link with:

```html
<marin-app-footer app-name="APP_NAME"></marin-app-footer>
<marin-app-feedback></marin-app-feedback>
```

The shell inserts the skip link and status region. Remove their copied versions only after confirming the shell-generated equivalents appear.

## 5. Preserve the application workflow

The primary workflow remains app-owned. Wrap it in the default routing section when it is not already:

```html
<section id="start" data-tab-section="start">
  ...
</section>
```

Do not move application-specific controls or results into shell components.

## 6. Remove obsolete shared files

After local review, delete the app-owned copies that the shell replaced:

```text
shared/app-brand.css
shared/app-shell.js
vendor/pico.min.css
```

Retain:

```text
vendor/fonts/
assets/app.css
assets/app.js
security.json
.well-known/security.txt
```

## 7. Update `marin.yml`

Change the platform metadata to:

```yaml
platform:
  shell: 1.1.0
```

`templateVersion` may remain temporarily as migration provenance but is no longer the update mechanism. Remove `platform.marin-ui` from consuming apps because the shell manifest records its Marin UI baseline.

## 8. Serve and review

```bash
python3 -m http.server 8765
```

Review at minimum:

- primary workflow;
- responsive header, outer padding, and menu;
- local Open Sans/Jost requests and actual rendered fonts;
- app icon parity across header, favicon, and the separate catalog;
- About, Security, Accessibility, and Updates routes;
- footer spacing and links;
- keyboard order and Escape behavior;
- light and dark color schemes;
- browser console and network failures;
- app-specific CSS for accidental shell-selector overrides.

## 9. Validate the pinned release

Confirm:

```bash
python3 - <<'PY'
import json
print(json.load(open('vendor/marinos/manifest.json'))['shellVersion'])
PY
```

The result must match `platform.shell` in `marin.yml`.
