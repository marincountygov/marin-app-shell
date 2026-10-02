#!/usr/bin/env python3
"""Prepare a verified offline font cache; install.sh also accepts a sibling marin-ui directly."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from assets import ROOT, AssetError, resolve_fonts, require
from install import replace_many


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source checkout with vendor/fonts, or a verified font cache")
    parser.add_argument("destination", nargs="?", type=Path, default=ROOT / "fonts")
    args = parser.parse_args()
    paths, label = resolve_fonts(ROOT, args.source)
    destination = args.destination.expanduser().absolute()
    require(not destination.is_symlink(), "Refusing symlink font-cache destination")
    destination.mkdir(parents=True, exist_ok=True)
    sources = {str(Path(p).relative_to("vendor/fonts")): source for p, source in paths.items()}
    if all(destination / p == source.absolute() for p, source in sources.items()):
        print(f"Font cache already verified: {destination}")
        return
    replace_many(destination, sources)
    print(f"Verified fonts copied from {label} to {destination}")


if __name__ == "__main__":
    try:
        main()
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
