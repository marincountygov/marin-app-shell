# Changelog

## 1.20.0 - 2026-10-28

- The pinned Marin UI baseline moves from 1.30.0 to 1.31.0. The "On this page" list (`.toc`) is a bordered box with a ruled heading and stacked links, and the page content (`.content`) is a plain bordered box with no shadow. Why: Marin Docs guide pages and the Marin Learn notes reader showed two different looks for the same part of the page. An app that installs this release should delete its own `.toc` and `.content` shadow rules.
- A lone `.action-button` (one that is not inside an `.action-group`) now has a visible border, `--app-border`, and an accent border when pointed at. It was borderless until pointed at, so a text button such as Browse files, Copy text or Copy HTML looked like plain text. Buttons inside a group are unchanged: they share the group's border.

## 1.19.0 - 2026-10-27

- The pinned Marin UI baseline moves from 1.29.2 to 1.30.0, which defines the filter column's fields and filter groups: `.search-input-field` (the search box is a rounded rectangle, not Pico's pill), `.search-facet-group`, `.search-facet-list`, `.search-facet-count` and `.mm-facet-group`. Why: `marin-mentions` and `marin-docs` each kept a copy of these rules by eye, and the copies drifted. An app that installs this release should delete its own copies. Documented in Marin UI's "Filter column" section.

## 1.18.0 - 2026-10-23

- The pinned Marin UI baseline moves from 1.29.1 to 1.29.2, which adds contrast pairs for the new button kinds to its checker.
- Fix: text on the accent tint now uses `--app-accent-on-tint`. A pressed `.action-button` or `.chip-button` and a hovered button in an `.action-group` used plain `--app-accent`, which is 3.8:1 on the 14% tint and 4.2:1 on the 8% hover tint in light mode (minimum 4.5:1). A new test, `tests/test_contrast_tokens.py`, reads the rules so a plain accent cannot come back.
- The audit sees more: buttons an app builds in script (`createElement("button")` and then `.className`), content marked `data-button-kind="content"` or `"menu-item"`, and disclosures (`aria-expanded`); it skips listbox, tab and menu parts and ignores comments in script.
- `audit-buttons.py` now ships in the release: `vendor/marinos/audit-buttons.py` in every app that installs it. An app's check script runs it from there, so the audit always matches the installed shell and nothing needs copying by hand. Why: `marin-app-template` carried its own copy that had to be refreshed whenever the shell's changed.

## 1.17.3 - 2026-10-23

- A visually hidden form control (`input.visually-hidden`, and `select` and `textarea`) stays 1 px wide and tall. Pico's rule makes every input as wide as its row and at least 44 px tall, and it was more specific than `.visually-hidden`, so a hidden file input made the page scroll sideways: 33 px in Marin Magic, 317 px in Marin Zipper and 549 px in Marin Unzipper at a 1100 px window. Why: found by the new browser tests; WCAG 1.4.10 (reflow) expects no sideways scrolling for content that fits.

## 1.17.2 - 2026-10-23

- The narrow-screen "Menu" button the header builds is now a quiet button (a border, no fill) instead of Pico's solid secondary button, and the shell no longer gives it the `secondary` class. The look comes from Marin UI 1.29.1. Why: every other button in the apps is quiet unless it submits a form, and this one showed on every page of every app at phone width.

## 1.17.1 - 2026-10-23

- New `.chip-group`: a row of filter chips. Pico turns any `role="group"` into one joined, full-width control, which stretched the chips across the page and drew a focus ring around the whole row; `.chip-group` gives each chip its own size and a pill shape. Why: found when converting the Personnel Management Regulations filters in `marin-docs`.

## 1.17.0 - 2026-10-23

- The pinned Marin UI baseline moves from 1.28.1 to 1.29.0, which adds 35 Lucide icons. The shell bundles them with its six existing icons.
- Declarative icons: `data-icon="name"` draws a bundled icon before an element's content, `data-icon-end` after it, including elements added later. `window.MarinAppShell.icon(name)` returns the markup. Why: every app pasted its own copy of the same icon shapes; one source keeps them identical.
- New button kinds: `.tab-list` and `.tab-button`, `.chip-button`, `.sort-button`, `.dialog-actions`, `.is-danger`, and `.action-button.menu-toggle`. Why: tabs, filter chips, sortable headers, dialog buttons and menu buttons are not action buttons and each app was styling its own.
- New `scripts/audit-buttons.py` lists buttons that do not follow the standard in an app, with `--fail` for check scripts.

## 1.16.0 - 2026-10-22

- New `.action-group--spaced` modifier for `.action-group`: separate bordered buttons, 44 px square at minimum, with a 0.75rem gap. Why: a joined group sets small targets edge to edge, so a person with limited fine motor control or wide fingers can press the wrong one. Use it for pairs pressed often, such as Previous and Next. Joined groups are unchanged.

## 1.15.0 - 2026-10-22

- New action buttons. `.action-button` is the one look for a secondary button that does something other than submit a form (Copy, Link, CSV, RSS, Reset, PNG): no fill, muted text, a border on hover, an accent tint when pressed, like the `.copy-button` on a listing. It is icon-only: an SVG and no visible text, named by `aria-label` and `title`. Only a button that submits a form stays solid blue or dark. `.action-toolbar` holds a row of `.action-group` clusters (a bordered group, like a Bootstrap button toolbar) and hides a group whose buttons are all hidden. `.action-search` is a search field for the end of the row; its label is visually hidden and its wrapper is `role="search"`.
- `.search-panel-header` and `.search-panel-title`: the filter panel's visible name and its Reset button on one line. The panel is named by it with `aria-labelledby`.
- On screens up to 850 px the filter button now sits beside the first element of `.search-results` (the tab row) instead of on a row of its own, which removes a band of empty space. The open panel takes the full row below. Wide screens are unchanged.

## 1.14.0 - 2026-10-22

- The pinned Marin UI baseline moves from 1.27.0 to 1.28.1, and the shell takes the matching collapsible filter panel. A `button[data-filter-toggle]` at the top of a filter column (inside a `.search-layout`) hides and shows the panel named by its `aria-controls`. The shell draws the Lucide `panel-right-open` icon while the panel is open and `panel-left-open` while it is hidden, sets `aria-expanded`, `data-open` and `data-filters`, starts open on wide screens and closed up to 850 px, remembers a wide-screen choice per app and toggle in `localStorage`, names the button "Filters" plus ", N active" from `data-filter-active`, and fires a bubbling `marin-filters-change` event so an app can resize anything sized by the results. Hiding a panel never changes a filter. A page with no such button is unaffected. Why: `marin-reach` and `marin-mentions` each carried their own copy of this CSS and script; one owner means one fix. Documented in `docs/components.md`.
- The two icons are added to the shell's managed Lucide icons (`panel-left-open`, `panel-right-open`, now six), embedded from the vendored SVG files like the others. The installer now also installs them into each app's `vendor/icons/lucide/`.
- New `tests/browser_filter_panel.py` covers the behavior in the built shell.

## 1.13.0 - 2026-10-15

- The pinned Marin UI baseline moves from 1.25.0 to 1.27.0, and the shell takes the matching "On this page" behavior. A table of contents (`.docs-toc` or `.toc`) now works for every list on a page, not just the first, and the last section is marked when the reader reaches the bottom of the page. A list can set where its reading line sits with `data-on-this-page-line` (pixels from the top), which suits a page of short sections. A new `window.marinOnThisPage(nav)` lets an app that builds its sections with JavaScript start a list it adds after the page loads. Before, Marin Learn carried its own copy of this code. Marin UI's CSS had no change, so nothing looks different.

## 1.12.2 - 2026-10-14

- Loading messages in the Security, Accessibility, Tech and Updates sections now all say "Loading {app name}…", for example "Loading Marin Reach…", instead of "Loading security information…" and similar. They come from one helper, `window.MarinAppShell.loadingMessage()`, which apps can use for their own loading text so the wording is the same everywhere.

## 1.12.1 - 2026-10-14

- The pinned Marin UI baseline moves from 1.24.0 to 1.25.0. Marin UI now has the MarinOS banner colors that the shell carried as its own compatibility block in 1.12.0, so that block is removed. Computed styles were compared before and after across the demo page and a real app in light and dark mode, and are identical.

## 1.12.0 - 2026-10-14

- The MarinOS banner now has the same background and text colors as the footer in light and dark mode: a surface-colored bar with muted text and a line under it, instead of solid black with white text. The "MarinOS" menu button takes the bar's text color and turns accent blue on hover.
- Carried in the shell as a narrowly scoped compatibility addition. Marin UI stays pinned at 1.24.0; the same change ships upstream in Marin UI 1.25.0 and can be dropped here when the pinned baseline is refreshed.

## 1.11.1 - 2026-10-13

- The Security section links `security.txt` once (under "Report an issue") and the Accessibility section links the WCAG 2.2 standard once (under "Accessibility standard"). Both were linked twice in nearby text, which web accessibility scanners flag as a redundant link.
- `scripts/check.sh` warns, without failing, when a sibling `marin-ui` checkout has a newer `BRAND_VERSION` than the pinned `MARIN_UI_VERSION`, so the baseline does not fall behind unnoticed.

## 1.11.0 - 2026-10-13

- The pinned Marin UI baseline moves from 1.19.0 to 1.24.0.
- The shell no longer carries its own copies of fixes that Marin UI now contains: the score gauge (1.4.0), accent text on a tint (1.5.1), the lighter page background (1.6.0), the form control border (1.10.1), and the dark-mode Alpha badge (1.2.2). Computed styles were compared before and after across the demo page and a real app, in light and dark mode: light mode is identical, and the only dark-mode difference is the Beta badge, which now uses the lighter blue text Marin UI always intended (its override had been in the wrong place in the file and never applied). The dark-mode Alpha badge is unchanged.
- `docs/brand.md` explains how to add and later remove a compatibility block.
- The floating Feedback button now hides when the page is scrolled until the footer appears, so it no longer covers footer links (it hid the Updates link on narrow screens). On a page too short to scroll, it stays. It remains in the keyboard order and shows itself when focused.

## 1.10.1 - 2026-10-13

- Form control borders now reach 3:1 contrast in light and dark mode. Text inputs, date inputs, selects, checkboxes and radio buttons had a border of about 1.4:1 in light mode and 2.7:1 on a card in dark mode, below the 3:1 that WCAG 1.4.11 asks for the edge of a control. This adds Marin UI's new `--app-control-border` token (`#737d8c` light, `#7a8896` dark) and maps Pico's form border to it.
- `scripts/check.sh --browser` no longer stops on macOS's default bash when no font source is given.
- Carried in the shell as a narrowly scoped compatibility addition. Marin UI stays pinned at 1.19.0; the same fix ships upstream in Marin UI 1.23.0 and can be dropped here when the pinned baseline is refreshed.

## 1.10.0 - 2026-10-08

- Tech pages show license names as GitHub reports them ("MIT License", not "MIT"). `data/tech.json` carries a `licenseNames` map from SPDX id to name; an id with no known name is shown as it is.
- Marin App Shell and Marin UI have their own Tech details on MarinOS. In every app's Bundled components table, those two names link to them.
- A hash that names an element inside a tab section (for example `#tech-marin-ui`) now opens that section and scrolls to the element. Before, any hash that was not a section name showed the first section.
- New optional `data-tech-heading-level` on a Tech block sets its top heading level (default 3), so MarinOS can nest several apps' details on one page.

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
