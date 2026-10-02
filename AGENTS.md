# Agent instructions

Marin App Shell is the versioned runtime used by multiple independently deployed MarinOS applications.

## Boundaries

- Shared shell behavior belongs in `src/marinos.js` and `src/shell.css`.
- `dist/` is generated and committed. Do not hand-edit it.
- Do not add application-specific workflows or content to the shell.
- Components render into light DOM. Do not introduce Shadow DOM without a major-version design decision.
- Consuming apps must remain static and self-contained; do not add a runtime CDN or package-manager requirement.
- Preserve WCAG 2.2 AA patterns, semantic landmarks, keyboard behavior, visible focus, reduced-motion support, and plain language.

## Required checks

Run:

```bash
./scripts/check.sh
```

A change to component names, required attributes, standard section IDs, or distribution paths is a breaking change.

## Brand and asset rules

- `vendor/marin-ui/` is a locked input, not editable shell source. Review upstream imports explicitly.
- Keep compatibility adapters small and documented in `docs/brand.md`. Do not reintroduce a copied whole-brand CSS source file.
- Fonts must use the standard local app paths, no `local()` preference or external font/CDN services. Installation synchronizes and verifies them.
- Derive owned icon constants from the four vendored Lucide SVG files; never hand-draw geometry in JS.
- Test actual rendered Open Sans/Jost, not merely CSS family names. Never report in-memory fixtures as successful HTTP loading.
- Respect the installer's managed path list and rollback contract; preserve app files and unrelated fonts/icons.
