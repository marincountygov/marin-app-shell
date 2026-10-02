#!/usr/bin/env python3
"""Install a pinned shell and its managed companion assets without touching app code."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from assets import (ROOT, FONT_PATHS, ICON_NAMES, AssetError, require, require_plain_path,
                    resolve_fonts, verify_file)
from build import verify_distribution


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def preflight_destinations(base: Path, sources: dict[str, Path]) -> None:
    for relative, source in sources.items():
        target = base / relative
        require_plain_path(target, base)
        parent = target.parent
        while parent != base:
            require(not parent.exists() or parent.is_dir(), f"Expected a directory: {parent}")
            parent = parent.parent
        if target.exists():
            require(target.is_dir() == source.is_dir(), f"Destination has wrong type: {target}")


def replace_many(base: Path, sources: dict[str, Path], validate=None) -> None:
    """Stage all inputs first; roll back handled failures, never erase other assets.

    This is NOT a filesystem-wide atomic transaction. Power loss/SIGKILL can leave
    a recovery directory and lock, which are retained rather than guessed away.
    """
    preflight_destinations(base, sources)
    lock = base / ".marinos-install.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise AssetError(f"Install lock exists: {lock}. Check for another process or unfinished recovery.") from exc
    work: Path | None = None
    old_moved: list[str] = []
    new_moved: list[str] = []
    created: list[Path] = []
    preserve_recovery = False
    try:
        work = Path(tempfile.mkdtemp(prefix=".marinos-install.", dir=base))
        (lock / "transaction.txt").write_text(str(work) + "\n")
        for relative, source in sources.items():
            stage = work / "new" / relative
            stage.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, stage)
            else:
                shutil.copy2(source, stage)
        if validate is not None:
            validate(work / "new")
        # Inputs are now fully staged; only now touch managed destinations.
        for relative in sources:
            target = base / relative
            parent = target.parent
            missing = []
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for path in reversed(missing):
                path.mkdir()
                created.append(path)
            if target.exists():
                backup = work / "old" / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)
                old_moved.append(relative)
            os.replace(work / "new" / relative, target)
            new_moved.append(relative)
        if validate is not None:
            validate(base)
    except BaseException:
        try:
            for relative in reversed(list(sources)):
                if relative in new_moved:
                    remove(base / relative)
                if relative in old_moved:
                    os.replace(work / "old" / relative, base / relative)
            for path in reversed(created):
                if path.exists():
                    path.rmdir()
        except BaseException as recovery_error:
            preserve_recovery = True
            print(f"ERROR: Recovery needs inspection: {work}; lock retained. {recovery_error}", file=sys.stderr)
        raise
    finally:
        if not preserve_recovery:
            if work is not None:
                shutil.rmtree(work)
            shutil.rmtree(lock)


def app_root(value: str | Path, root: Path) -> Path:
    app = Path(value).expanduser().absolute()
    require(app.is_dir() and not app.is_symlink(), f"Application directory missing or a symlink: {app}")
    require((app / "marin.yml").is_file(), f"Expected {app}/marin.yml; refusing unknown directory")
    actual, shell = app.resolve(), root.resolve()
    require(not actual.is_relative_to(shell) and not shell.is_relative_to(actual),
            "Install target must be an independent app directory, not the shell or its ancestor")
    return app


def check_app(app: Path, root: Path = ROOT) -> None:
    manifest = verify_distribution(root)
    shell = app / "vendor/marinos"
    require_plain_path(shell, app)
    require(shell.is_dir(), f"Installed shell missing: {shell}")
    required = set(manifest["files"]) | {"manifest.json"}
    actual = {p.relative_to(shell).as_posix() for p in shell.rglob("*") if p.is_file() or p.is_symlink()}
    require(actual == required, "Installed shell file inventory differs from the pinned release")
    require((shell / "manifest.json").read_bytes() == (root / "dist/manifest.json").read_bytes(),
            "Installed shell manifest differs from this release")
    for relative, meta in manifest["files"].items():
        require_plain_path(shell / relative, app)
        verify_file(shell / relative, meta, relative)
    for relative, meta in {**manifest["fontAssets"], **manifest["companionIcons"]}.items():
        require_plain_path(app / relative, app)
        verify_file(app / relative, meta, relative)


def install(app: Path, source: str | Path | None = None, dry_run: bool = False,
            root: Path = ROOT) -> None:
    app = app_root(app, root)
    manifest = verify_distribution(root)
    fonts, source_description = resolve_fonts(root, source)
    sources = {"vendor/marinos": root / "dist", **fonts}
    expected_icons = {f"vendor/icons/lucide/{name}.svg" for name in ICON_NAMES} | {"vendor/icons/lucide/LICENSE"}
    require(set(manifest.get("companionIcons", {})) == expected_icons, "Unexpected companion icon destinations")
    for relative, meta in manifest["companionIcons"].items():
        path = root / "dist" / meta["source"]
        verify_file(path, meta, relative)
        sources[relative] = path
    require(set(manifest["fontAssets"]) == set(FONT_PATHS), "Unexpected font destinations")
    preflight_destinations(app, sources)
    print(f"Verified font source: {source_description}")
    if dry_run:
        print("Would replace only these managed paths:")
        for path in sources:
            print(f"  {path}")
        return
    replace_many(app, sources, validate=lambda stage: check_app(stage, root))
    print(f"Installed Marin App Shell {manifest['shellVersion']} in {app}")
    print("Synchronized both font files, Open Sans license, and four shell Lucide icons/license.")
    print(f"Set platform.shell: {manifest['shellVersion']} in marin.yml, then review and commit the app.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--font-source", type=Path, help="Marin UI checkout (or prepared font cache); must match pinned hashes")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preflight and list paths without writing")
    mode.add_argument("--check", action="store_true", help="Verify an existing install without writing or needing a font source")
    args = parser.parse_args()
    if args.check:
        check_app(app_root(args.app, ROOT))
        print("Installed shell, font, and icon integrity: PASS (review marin.yml separately)")
    else:
        install(args.app, args.font_source, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
