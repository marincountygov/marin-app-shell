#!/usr/bin/env python3
"""Install the pinned shell, companion assets, and marin.yml platform.shell together."""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import os
import shutil
import signal
import stat
import sys
import tempfile
import threading
from pathlib import Path
from typing import Callable
from assets import (ROOT, FONT_PATHS, ICON_NAMES, AssetError, require, require_plain_path,
                    resolve_fonts, verify_file)
from build import verify_distribution
from marin_manifest import parse_manifest


@dataclass(frozen=True)
class GeneratedFile:
    """A prepared file staged with the original destination's permission bits."""
    data: bytes
    mode: int


@dataclass(frozen=True)
class FileState:
    data: bytes
    identity: tuple[int, ...]
    mode: int


class InstallInterrupted(AssetError):
    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"Installation interrupted by signal {signum}")


Source = Path | GeneratedFile


def read_file_state(path: Path, boundary: Path) -> FileState:
    """Detect replacement, permission changes, or edits during preparation."""
    require_plain_path(path, boundary)
    def identity(st: os.stat_result) -> tuple[int, ...]:
        return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f"Expected a regular file: {path}")
    data = path.read_bytes()
    after = path.lstat()
    require(identity(before) == identity(after), f"File changed while reading: {path}; retry after review")
    return FileState(data, identity(after), stat.S_IMODE(after.st_mode))


@contextlib.contextmanager
def interruption_guard():
    """Convert normal termination signals into exceptions the transaction can undo.

    SIGKILL and power loss cannot be handled. Recovery remains on disk in that case.
    Only the main thread may install process signal handlers.
    """
    saved = {}
    if threading.current_thread() is threading.main_thread():
        def interrupted(signum, _frame):
            # Do not let repeated Ctrl+C/TERM interrupt rollback itself.
            for number in saved:
                signal.signal(number, signal.SIG_IGN)
            raise InstallInterrupted(signum)
        for name in ("SIGINT", "SIGTERM", "SIGHUP"):
            number = getattr(signal, name, None)
            if number is not None:
                saved[number] = signal.getsignal(number)
                signal.signal(number, interrupted)
    try:
        yield
    except BaseException:
        for number in saved:
            signal.signal(number, signal.SIG_IGN)
        raise
    finally:
        for number, handler in saved.items():
            signal.signal(number, handler)


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def preflight_destinations(base: Path, sources: dict[str, Source]) -> None:
    for relative, source in sources.items():
        target = base / relative
        require_plain_path(target, base)
        parent = target.parent
        while parent != base:
            require(not parent.exists() or parent.is_dir(), f"Expected a directory: {parent}")
            parent = parent.parent
        if target.exists():
            want_directory = isinstance(source, Path) and source.is_dir()
            require(target.is_dir() if want_directory else target.is_file(),
                    f"Destination has wrong type: {target}")


def replace_many(base: Path, sources: dict[str, Source], validate: Callable | None = None,
                 expected_files: dict[str, FileState] | None = None) -> None:
    """Stage and validate inputs, then roll back handled failures as one operation.

    This is NOT a filesystem-wide atomic transaction: concurrent readers can see
    intermediate states. Power loss/SIGKILL can leave a recovery directory and
    lock, retained rather than guessed away. Shared callers (font/UI sync) may
    still pass ordinary Path sources and omit expected_files/validate.
    """
    expected_files = expected_files or {}
    def unchanged(relative: str) -> None:
        if relative in expected_files:
            require(read_file_state(base / relative, base) == expected_files[relative],
                    f"{relative} changed while installation was being prepared; "
                    "refusing to overwrite it. Review changes and retry")
    preflight_destinations(base, sources)
    lock = base / ".marinos-install.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise AssetError(f"Install lock exists: {lock}. Check for another process or unfinished recovery.") from exc
    work: Path | None = None
    # Record intent before each rename; rollback inspects backup/stage presence.
    # This also handles an interrupt immediately after os.replace succeeds.
    attempted: list[tuple[str, bool]] = []
    created: list[Path] = []
    preserve_recovery = False
    with interruption_guard():
        try:
            for relative in expected_files:
                unchanged(relative)
            work = Path(tempfile.mkdtemp(prefix=".marinos-install.", dir=base))
            (lock / "transaction.txt").write_text(str(work) + "\n", encoding="utf-8")
            for relative, source in sources.items():
                stage = work / "new" / relative
                stage.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(source, GeneratedFile):
                    stage.write_bytes(source.data)
                    stage.chmod(source.mode)
                elif source.is_dir():
                    shutil.copytree(source, stage)
                else:
                    shutil.copy2(source, stage)
            if validate is not None:
                validate(work / "new")
            # All inputs (including updated YAML) have now passed validation.
            # Check again before changing ANY managed destination.
            for relative in expected_files:
                unchanged(relative)
            preflight_destinations(base, sources)
            for relative in sources:
                unchanged(relative)
                target = base / relative
                parent = target.parent
                missing = []
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for path in reversed(missing):
                    path.mkdir()
                    created.append(path)
                had_original = target.exists()
                attempted.append((relative, had_original))
                if had_original:
                    backup = work / "old" / relative
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(target, backup)
                os.replace(work / "new" / relative, target)
            if validate is not None:
                validate(base)
        except BaseException:
            # Ignore repeat signals while restoring backups.
            if threading.current_thread() is threading.main_thread():
                for name in ("SIGINT", "SIGTERM", "SIGHUP"):
                    number = getattr(signal, name, None)
                    if number is not None:
                        signal.signal(number, signal.SIG_IGN)
            try:
                for relative, had_original in reversed(attempted):
                    backup = work / "old" / relative
                    stage = work / "new" / relative
                    target = base / relative
                    if backup.exists():
                        remove(target)
                        os.replace(backup, target)
                    elif not had_original and not stage.exists():
                        remove(target)
                for path in reversed(created):
                    if path.exists():
                        path.rmdir()
            except BaseException as recovery_error:
                preserve_recovery = True
                print(f"ERROR: Recovery needs inspection: {work}; lock retained. {recovery_error}", file=sys.stderr)
            raise
        finally:
            # Once validation/rollback has finished, do not interrupt removal of
            # the recovery data and lock. The guard restores handlers on exit.
            if threading.current_thread() is threading.main_thread():
                for name in ("SIGINT", "SIGTERM", "SIGHUP"):
                    number = getattr(signal, name, None)
                    if number is not None:
                        signal.signal(number, signal.SIG_IGN)
            if not preserve_recovery:
                if work is not None:
                    shutil.rmtree(work)
                shutil.rmtree(lock)


def app_root(value: str | Path, root: Path) -> Path:
    app = Path(value).expanduser().absolute()
    require(app.is_dir() and not app.is_symlink(), f"Application directory missing or a symlink: {app}")
    require_plain_path(app / "marin.yml", app)
    require((app / "marin.yml").is_file(), f"Expected {app}/marin.yml; refusing unknown directory")
    actual, shell = app.resolve(), root.resolve()
    require(not actual.is_relative_to(shell) and not shell.is_relative_to(actual),
            "Install target must be an independent app directory, not the shell or its ancestor")
    return app


def check_app(app: Path, root: Path = ROOT) -> None:
    manifest = verify_distribution(root)
    state = read_file_state(app / "marin.yml", app)
    declared = parse_manifest(state.data).version
    require(declared == manifest["shellVersion"],
            f"marin.yml platform.shell is {declared}; this release requires {manifest['shellVersion']}")
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
    current = read_file_state(app / "marin.yml", app)
    document = parse_manifest(current.data)
    manifest = verify_distribution(root)
    version = manifest["shellVersion"]
    updated_yaml = document.updated(version)
    # Confirm the generated document before any target write.
    require(parse_manifest(updated_yaml).version == version, "Prepared marin.yml has an incorrect shell version")
    fonts, source_description = resolve_fonts(root, source)
    sources: dict[str, Source] = {"vendor/marinos": root / "dist", **fonts}
    expected_icons = {f"vendor/icons/lucide/{name}.svg" for name in ICON_NAMES} | {"vendor/icons/lucide/LICENSE"}
    require(set(manifest.get("companionIcons", {})) == expected_icons, "Unexpected companion icon destinations")
    for relative, meta in manifest["companionIcons"].items():
        path = root / "dist" / meta["source"]
        verify_file(path, meta, relative)
        sources[relative] = path
    require(set(manifest["fontAssets"]) == set(FONT_PATHS), "Unexpected font destinations")
    # Metadata is committed last, but belongs to the SAME rollback transaction.
    sources["marin.yml"] = GeneratedFile(updated_yaml, current.mode)
    preflight_destinations(app, sources)
    lock = app / ".marinos-install.lock"
    require(not lock.exists() and not lock.is_symlink(),
            f"Install lock exists: {lock}. Check for another process or unfinished recovery")
    print(f"Verified font source: {source_description}")
    print(f"marin.yml platform.shell: {document.version} -> {version}")
    if dry_run:
        print("Would replace only these managed paths:")
        for path in sources:
            print(f"  {path}")
        print("No files changed (--dry-run).")
        return
    def validate(stage: Path) -> None:
        check_app(stage, root)
        state = read_file_state(stage / "marin.yml", stage)
        require(state.data == updated_yaml and state.mode == current.mode,
                "Staged/installed marin.yml differs from the prepared scalar-only update")
    replace_many(app, sources, validate=validate, expected_files={"marin.yml": current})
    print(f"Installed Marin App Shell {version} in {app}")
    print("Synchronized both font files, Open Sans license, and four shell Lucide icons/license.")
    print(f"Updated marin.yml platform.shell to {version}. Review, test, and commit the app.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--font-source", type=Path, help="Marin UI checkout (or prepared font cache); must match pinned hashes")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preflight assets/YAML and list the version change without writing")
    mode.add_argument("--check", action="store_true", help="Verify installed assets and platform.shell without writing or needing a font source")
    args = parser.parse_args()
    if args.check:
        app = app_root(args.app, ROOT)
        lock = app / ".marinos-install.lock"
        require(not lock.exists() and not lock.is_symlink(),
                f"Install lock exists: {lock}; wait for completion or inspect recovery first")
        check_app(app)
        print("Installed shell, font, icon, and marin.yml integrity: PASS")
    else:
        install(args.app, args.font_source, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except InstallInterrupted as exc:
        print(f"ERROR: {exc}. Inspect any reported recovery directory.", file=sys.stderr)
        raise SystemExit(128 + exc.signum)
    except (AssetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("ERROR: Installation interrupted; inspect any reported recovery directory.", file=sys.stderr)
        raise SystemExit(130)
