# Changelog

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
