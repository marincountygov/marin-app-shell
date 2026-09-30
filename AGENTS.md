# Agent instructions

Marin App Shell is the versioned runtime used by multiple independently deployed MarinOS applications.

## Boundaries

- Shared shell behavior belongs in `src/marinos.js` and `src/marinos.css`.
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
