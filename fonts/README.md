# Verified local font cache

Prepare a cache for the demo or offline installation:

```bash
bash scripts/sync-fonts.sh ../marin-ui
```

The command verifies both fonts and the Open Sans license against
`vendor/marin-ui/lock.json`, then copies them here. `install.sh` can also read the
sibling `marin-ui` directly; a pre-existing cache must be complete and hash-valid.
The root demo's `dist/marinos.css` resolves its `../fonts/` URLs to this directory.
Applications receive the same files at their standard `vendor/fonts/` paths.

Cache binaries are ignored by Git. Missing fonts are a validation failure for
installation/render testing, not an approved fallback-font release. No network
font fetch is implemented. Preserve any separate source licensing notices when
preparing a release; the existing Jost font carries its embedded OFL notice.
