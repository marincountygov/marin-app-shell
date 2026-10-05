# Pinned Marin UI input

`app-brand.css` is the unmodified stylesheet imported from the supplied Marin UI
1.19.0 checkout. `BRAND_VERSION` is recorded separately in `lock.json`; the source
stylesheet currently retains its own older banner comment. The lock records the
import provenance, source file hashes, and exact required font hashes.

Do not edit this snapshot or the locked Lucide/Pico files by hand. Use
`bash scripts/sync-ui.sh /path/to/marin-ui` for an explicit source upgrade,
review the diff, rebuild, and test. That command does not pull or modify the
source checkout. Repeated builds never read sibling repositories.

The build relocates the two font URLs and removes obsolete SVG paint/stroke
CSS declarations with counted, fail-closed adapters. `src/brand-compat.css`
contains the remaining small policy corrections pending an upstream fix;
`src/shell.css` contains component-host and shell-footer rules only.
