# Changelog

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
