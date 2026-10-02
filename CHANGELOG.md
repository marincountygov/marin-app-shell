# Changelog

## 1.1.0

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
