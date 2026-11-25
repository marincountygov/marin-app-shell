# Versioning and releases

Component names, required attributes, standard routes, and `vendor/marinos/`
remain the public API. Version 1.1.0 added installer-managed companion assets and
corrected shared presentation without requiring new component markup. Version
1.1.1 keeps that runtime API and presentation unchanged while making the installer
synchronize the consuming app's existing `marin.yml` `platform.shell` value with
the installed release. Version 1.2.0 adds catalog-backed Alpha/Beta/Live status
rendering and adopts the reviewed Marin UI 1.19.0 baseline. Version 1.11.0 refreshes that baseline to Marin UI 1.24.0 (1.12.1 to 1.25.0, 1.13.0 to 1.27.0, 1.14.0 to 1.28.1, and 1.17.0 to 1.29.0) and removes the shell's compatibility copies of fixes that Marin UI now contains. Version 1.5.0 adds
compatible footer-extension API for app-specific links and optional platform-link
suppression while making the four standard information destinations mandatory.

Version 2.0.0 is the first major release since 1.0: the filter column is drawn from an app's `filters.json`, so an app with a filter column removes its own markup in the same pull request that installs it.

Version 2.1.0 adds matching and counting to the filter column (`field`, `search.fields`, `filter`, `matchesRecord`, `updateCounts`) without changing anything an existing app relies on.

Version 2.2.0 adds the search-result helpers (`marinSearchWords`, `marinSearchSnippet`, `marinSearchRemember`, and a highlighter that runs when a page loads) and adopts the Marin UI 1.38.0 baseline, without changing anything an existing app relies on.

Version 2.3.0 adds the report core (`window.marinReports`) without changing anything an existing app relies on.

Version 2.8.0 adopts the Marin UI 1.43.0 baseline: `.app-card` takes its background, edge color and shadow from three custom properties with the usual look as the default. It changes nothing for an app that does not set them.

Version 2.7.0 adds the shared card list and record card (`.search-results-list`, `.mm-card` and its parts) at the sizes the standard states, adopts the Marin UI 1.42.0 baseline, and adds `audit-cards.py`. An app that still carries its own copy of these rules keeps working, but its cards may differ slightly from the shared ones, so each app should delete its copy and review its cards.

Version 2.6.0 takes About and Updates out of the default header (`standard-links` now defaults to none), draws no Menu button when the header has no links, opens the MarinOS menu as a wide panel on large screens, leaves unlisted apps out of that menu, and adds `audit-h1.py`. It is compatible in markup, but every app's header looks different, so each needs a visual review.

Version 2.5.0 adds the steps layout (`nav[data-steps]`, `window.marinSteps`) and adopts the Marin UI 1.40.0 baseline without changing anything an existing app relies on.

Version 2.4.0 adopts the Marin UI 1.39.0 baseline (a checked checkbox shows in Windows forced colors) without changing anything an existing app relies on.

Patch releases fix compatible defects. Minor releases add compatible capabilities
or intentionally change presentation and therefore still require visual review.
Major releases change required component markup, routes, or deployment paths.

## Release procedure

1. Review source changes and any explicit `sync-ui.sh` input refresh.
2. Update `SHELL_VERSION`; review `MARIN_UI_VERSION`, `marin.yml`, docs and demo when changing the UI baseline.
3. Keep the UI input lock and icon/font hashes consistent; do not edit vendor input files independently.
4. Update the changelog and root demo release display, then run `bash scripts/build.sh` and `bash scripts/check.sh`.
5. Run `bash scripts/check.sh --browser --font-source ../marin-ui` and the separate HTTP check in an environment that permits it when runtime/browser behavior changes.
6. Review the root demo and a consuming app in light/dark and narrow/desktop layouts when presentation changes. Compare actual loaded fonts, not just token definitions.
7. Review the demo header/favicon/catalog icon parity and any separate real catalog update when brand/icon inputs change.
8. Commit source and generated distribution together; tag `vX.Y.Z` after review.
9. Open one shell update PR per consumer. A source handoff requires a matching local UI checkout or verified font cache; apps are standalone after install.

## Consumer changes

For a compatible 1.2.0 install, expected managed changes are:

```text
vendor/marinos/**
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
vendor/fonts/open-sans/OFL.txt
vendor/icons/lucide/{layout-grid,chevron-down,copy,check,panel-left-open,panel-right-open}.svg
vendor/icons/lucide/LICENSE
marin.yml -> platform.shell only
```

The installer updates the existing `platform.shell` scalar to the release being
installed and validates that it matches `vendor/marinos/manifest.json`. Supported
unrelated manifest content, comments, quoting, line endings, and permissions are
preserved. Missing or duplicate `platform.shell` keys and unsupported YAML
structures are rejected rather than rewritten.

The installer does not stage, commit, or push application changes; delete unrelated
fonts/icons; or rewrite app code, CSS, security policies, or other manifest fields.
Font and icon companions are part of the release contract, so copying only `dist/`
is not a sufficient installation procedure.
