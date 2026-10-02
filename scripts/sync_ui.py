#!/usr/bin/env python3
"""Explicitly refresh pinned UI inputs. Never pulls, changes, or builds the source repo."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from assets import ROOT, FONT_PATHS, ICON_NAMES, AssetError, digest, require, require_plain_path
from install import replace_many
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Reviewed local marin-ui checkout")
    args = parser.parse_args()
    source = args.source.expanduser().absolute()
    require(source.is_dir() and not source.is_symlink(), f"Expected a regular source directory: {source}")
    require(source.resolve() != ROOT.resolve(), "Source cannot be this shell checkout")
    version = (source / "BRAND_VERSION").read_text().strip()
    require(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None, "Invalid Marin UI BRAND_VERSION")
    mapping = {"vendor/marin-ui/app-brand.css": "shared/app-brand.css", "vendor/pico.min.css": "vendor/pico.min.css",
               "vendor/icons/lucide/LICENSE": "vendor/icons/lucide/LICENSE"}
    mapping.update({f"vendor/icons/lucide/{n}.svg": f"vendor/icons/lucide/{n}.svg" for n in ICON_NAMES})
    for path in [*mapping.values(), *FONT_PATHS]:
        require_plain_path(source / path, source)
        require((source / path).is_file(), f"Missing source asset: {path}")
    # Record a commit only for a clean git checkout. A dirty input must not masquerade as that commit.
    commit = None
    try:
        result = subprocess.run(["git", "-C", str(source), "status", "--porcelain"], capture_output=True, text=True, check=True)
        require(not result.stdout.strip(), "Review/commit local marin-ui changes before importing a new baseline")
        commit = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    lock = {"schema": 1, "marinUiVersion": version, "upstream": "https://github.com/marincountygov/marin-ui",
            "provenance": {"source": "Explicitly imported local marin-ui checkout", "gitCommit": commit},
            "files": {dst: {"source": src, **digest((source / src).read_bytes())} for dst, src in sorted(mapping.items())},
            "fonts": {p: {"source": p, **digest((source / p).read_bytes())} for p in FONT_PATHS}}
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        (tmp / "lock.json").write_text(json.dumps(lock, indent=2) + "\n")
        (tmp / "version").write_text(version + "\n")
        updates = {dst: source / src for dst, src in mapping.items()}
        updates["vendor/marin-ui/lock.json"] = tmp / "lock.json"
        updates["MARIN_UI_VERSION"] = tmp / "version"
        updates["vendor/licenses/LUCIDE_LICENSE.txt"] = source / "vendor/icons/lucide/LICENSE"
        updates["vendor/licenses/OPEN_SANS_OFL.txt"] = source / "vendor/fonts/open-sans/OFL.txt"
        updates.update({str(Path("fonts") / Path(p).relative_to("vendor/fonts")): source / p for p in FONT_PATHS})
        replace_many(ROOT, updates)
    print(f"Imported reviewed Marin UI {version}. Review the staged-source diff (not automatically git-staged).")
    print("Update any compatibility adapters, marin.yml and documentation as needed; then build and test before release.")


if __name__ == "__main__":
    try:
        main()
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
