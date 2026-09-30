# Versioning and releases

Marin App Shell uses semantic versioning.

## Patch release

A patch release fixes a defect without changing the component contract. Examples:

- correct footer spacing;
- fix mobile menu focus behavior;
- correct a Security renderer error;
- improve a fallback without changing markup requirements.

Apps can normally update by replacing `vendor/marinos/` and reviewing the result.

## Minor release

A minor release adds backward-compatible capability or deliberately changes shared presentation without requiring app markup changes. Examples:

- add an optional component attribute;
- add an optional component;
- add a shared utility;
- update the Marin UI baseline while preserving component APIs.

Apps still update by replacing `vendor/marinos/`, but visual review remains required.

## Major release

A major release changes the integration contract. Examples:

- rename a custom element;
- remove or rename an attribute;
- change required section IDs;
- change `vendor/marinos/` paths;
- require new app-authored markup;
- change light-DOM output in a way that breaks documented app integration.

A major release must include an explicit app migration guide.

## Release procedure

1. Update source and documentation.
2. Update `SHELL_VERSION` and, when applicable, `MARIN_UI_VERSION`.
3. Add CHANGELOG entries.
4. Run `./scripts/build.sh`.
5. Run `./scripts/check.sh`.
6. Review the root demonstration in supported browsers and viewport sizes.
7. Commit source and generated `dist/` together.
8. Tag the release as `vX.Y.Z`.
9. Use maintenance automation to open one shell-update PR per consuming app.

## Application update rule

A consuming app's `platform.shell` value and `vendor/marinos/manifest.json` `shellVersion` must match. Update tooling should stage only:

```text
vendor/marinos/**
marin.yml
```

for ordinary compatible shell releases. Any additional changed application files indicate a major migration or an app-specific correction and require separate review.
