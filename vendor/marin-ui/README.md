# Pinned Marin UI input

`app-brand.css` is the unmodified 1.18.0 brand bundle from the supplied
Marin Mentions archive. It is a reviewed consumer snapshot, not a claim that
upstream `main` is frozen at that content. `lock.json` records its provenance,
source file hashes, and the exact required font hashes.

Do not edit this snapshot or the locked Lucide/Pico files by hand. Use
`bash scripts/sync-ui.sh /path/to/marin-ui` for an explicit source upgrade,
review the diff, rebuild, and test. That command does not pull or modify the
source checkout. Repeated builds never read sibling repositories.

The build relocates the two font URLs and removes obsolete SVG paint/stroke
CSS declarations with counted, fail-closed adapters. `src/brand-compat.css`
contains the remaining small policy corrections pending an upstream fix;
`src/shell.css` contains component-host and shell-footer rules only.
