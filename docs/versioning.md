# Versioning and releases

Component names, required attributes, standard routes, and `vendor/marinos/`
remain the public API. Version 1.1.0 added installer-managed companion assets and
corrected shared presentation without requiring new component markup. Version
1.1.1 keeps that runtime API and presentation unchanged while making the installer
synchronize the consuming app's existing `marin.yml` `platform.shell` value with
the installed release. Version 1.2.0 adds catalog-backed Alpha/Beta/Live status
rendering and adopts the reviewed Marin UI 1.19.0 baseline. Version 1.5.0 adds
compatible footer-extension API for app-specific links and optional platform-link
suppression while making the four standard information destinations mandatory.

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
vendor/icons/lucide/{layout-grid,chevron-down,copy,check}.svg
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
