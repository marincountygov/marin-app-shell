# Versioning and releases

Component names, required attributes, standard routes, and `vendor/marinos/`
remain the public API. Version 1.1.0 adds installer-managed companion assets and
corrects shared presentation without requiring new component markup. Apps should
not depend on undocumented internal wrapper elements.

Patch releases fix compatible defects. Minor releases add compatible capabilities
or intentionally change presentation and therefore still require visual review.
Major releases change required component markup, routes, or deployment paths.

## Release procedure

1. Review source changes and any explicit `sync-ui.sh` input refresh.
2. Update `SHELL_VERSION`; review `MARIN_UI_VERSION`, `marin.yml`, docs and demo when changing the UI baseline.
3. Keep the UI input lock and icon/font hashes consistent; do not edit vendor input files independently.
4. Update the changelog, then run `bash scripts/build.sh` and `bash scripts/check.sh`.
5. Run `bash scripts/check.sh --browser --font-source ../marin-ui` and the separate HTTP check in an environment that permits it.
6. Review the root demo and a consuming app in light/dark and narrow/desktop layouts. Compare actual loaded fonts, not just token definitions.
7. Review the demo header/favicon/catalog icon parity and any separate real catalog update.
8. Commit source and generated distribution together; tag `vX.Y.Z` after review.
9. Open one shell update PR per consumer. A source handoff requires a matching local UI checkout or verified font cache; apps are standalone after install.

## Consumer changes

For a compatible 1.1.0 install, expected paths are:

```text
vendor/marinos/**
vendor/fonts/Jost-wght.ttf
vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2
vendor/fonts/open-sans/OFL.txt
vendor/icons/lucide/{layout-grid,chevron-down,copy,check}.svg
vendor/icons/lucide/LICENSE
marin.yml
```

The installer does not stage/commit/push, modify `marin.yml`, delete unrelated
fonts/icons, or rewrite app code/security policies. Set `platform.shell` to match
the installed manifest yourself. Font and icon companions are part of the release
contract; copying only `dist/` is no longer a sufficient installation procedure.
