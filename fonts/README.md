# Local demo fonts

The shell distribution references the existing MarinOS font contract rather than duplicating font binaries:

- `vendor/fonts/Jost-wght.ttf`
- `vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2`

For this repository's root demo, those relative URLs resolve into this `fonts/` directory. Populate it locally from an existing MarinOS checkout:

```bash
./scripts/sync-fonts.sh ../marin-app-template
```

The demo and applications remain usable with system fallback fonts when these files are absent.
