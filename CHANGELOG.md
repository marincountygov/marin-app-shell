# Changelog

## 1.9.0 - 2026-10-08

- The Tech section now has a **Services used** part, between the software bill of materials and AI. It lists the outside services an app uses, what each is for, whether the visitor's browser or only the build calls it, and whether it receives visitor data. The list is declared in the app's own `marin.yml` (`services:`) and read from MarinOS's `data/tech.json`.
- `services: none` shows "This application does not use outside services of its own." A missing declaration shows "Not documented" and is never treated as none. The shared calls every app makes (MarinOS data files and GitHub's public API for recent changes) are described once, in a note.

## 1.8.0 - 2026-10-07

- New standard **Tech** section and footer link, between Accessibility and Updates. It reads MarinOS's shared `data/tech.json` (by catalog id) and shows the app's languages, dependencies and bundled components, software bill of materials (a link to the stored SPDX file), and whether it uses AI as part of the deployed service.
- Missing or failed data is shown as "Not available", "Not documented" or "Unable to retrieve", never as zero, "No" or "none". A missing AI declaration is never shown as No.
- New optional `<template data-tech>` for app-specific context. Tech is now part of the required footer set.

## 1.7.0 - 2026-10-06

- The Security section's "who is this for" line now comes from `project.audience` in the app's own `marin.yml` (staff, public, or developers) instead of a hand-written string in `security.json`, so it can't drift from the manifest. It reads "Built for: County staff" and so on. If `marin.yml` can't be read it falls back to the security profile's label. `publicSecurity.profile` is no longer shown.

## 1.6.0 - 2026-10-06

- Every `[role="tablist"]` now gets the ARIA tabs keyboard pattern with no per-app JavaScript: one tab in the Tab order at a time (the selected one, or the first), Left/Right (Up/Down for `aria-orientation="vertical"`) with wrap, Home/End, and selection on focus. An app that handles those keys itself calls `preventDefault()` and the shared handler stands down. Apps no longer need their own copy.
- Lighten the light-mode page background (`--app-bg-soft`) from `#f6f7f8` to `#fdfdfe` so accent links directly on it reach 4.54:1 (were 4.30:1). Dark mode is unchanged. Carried as a compatibility override like the 1.5.1 fix.
- Includes the 1.5.1 contrast fix below.
- `scripts/check.sh` also runs Marin UI's `check-contrast.js` against `dist/marinos.css` (both themes) when a `marin-ui` checkout sits next to this repo.

## 1.5.1 - 2026-10-06

- Fix low-contrast accent text on accent-tinted backgrounds: the current header-nav link and hover, hovered or focused menu items, the hovered Updates "Copy" button, and the current topic filter were about 3.6-4.2:1 in light mode (AA needs 4.5:1). They now use a darker blue in light mode (6.2:1 or better) and are unchanged in dark mode.
- Carried in the shell as a narrowly scoped compatibility addition. Marin UI stays pinned at 1.19.0; the same fix ships upstream in Marin UI 1.22.0 and can be dropped here when the pinned baseline is refreshed.

## 1.5.0 - 2026-10-05

- Require the standard About, Security, Accessibility, and Updates footer links for every MarinOS application; legacy `links` ordering is retained but can no longer omit a required destination.
- Add `<template data-footer-links>` for app-specific footer links. Valid top-level anchors are prepended to the required standard set, with duplicate destinations suppressed.
- Add the `hide-platform-link` boolean attribute so platform-level applications such as the MarinOS home app can omit the separate bottom MarinOS link while keeping the local app name and required information links.
- Keep the default footer markup and platform link unchanged for existing applications that do not opt into the new footer capabilities.

## 1.4.0 - 2026-10-05

- The Accessibility section's score now shows as a gauge (a ring with the number inside and the band word beside it): good 90-100 green, needs improvement 50-89 orange, poor 0-49 red, matching Lighthouse. Color is never the only signal; the number and band word are always printed, and the colors keep 4.5:1 contrast in light and dark.
- A "Lighthouse results" link beside the score opens PageSpeed Insights' own report for the tested address (a live re-run, so it can differ slightly from the stored score).
- The `.app-score` styles are carried in the shell as a narrowly scoped compatibility addition. Marin UI stays pinned at 1.19.0; the same styles ship upstream in Marin UI 1.21.0 and can be dropped here when the pinned baseline is refreshed.

## 1.3.0 - 2026-10-05

- The standard Accessibility section in `<marin-app-info>` now shows the app's Google Lighthouse accessibility score, read live from MarinOS's shared `data/lighthouse.json` by catalog id (`app-id` on `<marin-app-info>` or `<marin-app-header>`, `<body data-app-id>`, or URL matching).
- The section states that the app targets WCAG 2.2 Level AA, explains that the score is automated testing and not WCAG conformance, and links to report an accessibility issue.
- A failed scan keeps showing the last successful score with its date, an old score is marked out of date, and an app with no score says so. A failure is never shown as a low score.
- New optional `app-id` attribute on `<marin-app-info>`. Apps that provide their own `<template data-accessibility>` keep that text, shown after the standard line.
- The old default text for this section is replaced.

## 1.2.2 - 2026-10-05

- Improve dark-mode Alpha status badges in App Shell with the County gold background and black text, providing stronger contrast while leaving Beta and Live unchanged.
- Keep Marin UI 1.19.0 pinned unchanged; this is a narrowly scoped App Shell compatibility override that can be removed when the shared UI baseline adopts the same treatment.
- Add static and rendered browser coverage for the dark-mode Alpha treatment.

## 1.2.1 - 2026-10-05

- Read recognized `alpha`, `beta`, and `live` maturity status from the consuming app's local `marin.yml` `project.status` and render the shared status badge beside `.app-title`.
- Keep catalog matching as the compatibility fallback when the local manifest is unavailable or has no recognized maturity value; catalog-backed MarinOS menu badges are unchanged.
- Keep the application-name home link and status-guidance link separate, and add browser coverage for both manifest-backed and catalog-fallback header badges.
- The deferred Alpha dark-mode contrast adjustment is not included.

## 1.2.0 - 2026-10-05

- Import the reviewed Marin UI 1.19.0 baseline, including the shared Alpha/Beta/Live app-status presentation.
- Render catalog-backed app maturity badges in the MarinOS menu and beside the current application's name, with optional `app-id` matching for local development and URL matching as the production fallback.
- Render the MarinOS banner's default Alpha marker with the shared status-badge component while preserving arbitrary legacy `label` values as the existing superscript fallback.
- Change the generated header identity so only the `.app-title` application name links to `./`; the icon, subtitle, and adjacent status badge are not part of the home link.
- Bump the catalog cache shape to v3 and extend browser/static validation for status rendering and the updated header identity.

## 1.1.3 - 2026-10-05

- Default missing SVG stroke widths to 4 for legacy 48x48 viewBoxes; retain 2 for canonical 24x24 Lucide icons. Apply this to header templates, initial app icons, and catalog-rendered icons without changing their geometry.
- Preserve explicit SVG stroke widths and add the matching CSS fallback for late-inserted legacy icons with the canonical `viewBox="0 0 48 48"` spelling.
- Add source/distribution unit tests and rendered browser regressions for both coordinate systems, explicit widths, catalog sanitization, and late-inserted icons.
- Make the separate HTTP browser test read the current release version rather than hard-coding 1.1.0.
- Keep the public component API, installer transaction behavior, and font/icon assets unchanged. The deferred TOC/layout-timing change is not included.

## 1.1.2 - 2026-10-02

- Fix the shared cross-app menu's fallback app list: `FALLBACK_APPS` said `MarinMagic` and `MarinDocs`, squashed CamelCase that didn't match those apps' real display name (`Marin Magic`, `Marin Docs`, as shown everywhere else — MarinOS's own catalog, their own headers and titles). No other change.

## 1.1.1 - 2026-10-02

- Update the installer to keep `marin.yml` `platform.shell` synchronized with the installed shell version.
- Include `marin.yml` in installer validation and rollback.
- Add conservative manifest editing that preserves unrelated YAML content and refuses unsupported structures rather than rewriting them.
- Extend installer regression tests for manifest updates, rollback, concurrent edits, and version verification.

## 1.1.0 - 2026-10-02

- Replace the copied brand CSS source with a hash-pinned Marin UI 1.18.0 input, named compatibility adapters, and a small shell-only stylesheet.
- Remove `local()` font preferences, enforce body/UI versus heading roles, and automatically synchronize the locked Jost/Open Sans fonts and supplied Open Sans license into standard app paths during installation.
- Generate shell-owned icon constants from vendored Lucide SVGs, remove incompatible CSS stroke overrides, and synchronize the four shell icons/license without deleting app-specific icons.
- Make the identity home anchor the title flex row and restore outer padding lost when Pico's direct-child header/footer selectors stopped matching custom-element hosts.
- Keep component API and `./` home navigation; retain initial legacy icon attribute compatibility without redrawing custom app shapes.
- Add pinned-input provenance, deterministic build verification, staged multi-path installation with rollback, brand/rendered-font tests, and a separate HTTP integration check.
- Normalize the demo's header/favicon/local catalog to the same Lucide layout-grid; provide a catalog fragment for separate upstream review.

## 1.0.1 — 2026-10-01

### Changed

- Made the application identity in `marin-app-header` a home link to `./`, so selecting the app identity returns the application to its default on-load route.
- Preserved the existing header layout and visible keyboard focus treatment for the new link.

## 1.0.0 — 2026-09-29

Initial runtime-shell release.

### Added

- Locally vendored `dist/` package with deterministic manifest and checksums.
- Native light-DOM components for the MarinOS banner, application header, standard information sections, footer, and Feedback control.
- Shared Marin UI 1.18.0 and Pico CSS bundle.
- Standard About, Security, Accessibility, and Updates framework.
- Existing MarinOS menu, routing, Updates, Security, copy, share, table, and documentation utilities.
- Atomic installer for consuming applications.
- Migration, integration, component, and semantic-versioning documentation.
- Automated static validation and Chromium smoke testing.
