#!/usr/bin/env python3
"""Hash-locked release assets. No network access, package manager, or downloads."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_PATHS = (
    "vendor/fonts/Jost-wght.ttf",
    "vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2",
    "vendor/fonts/open-sans/OFL.txt",
)
ICON_NAMES = ("check", "chevron-down", "copy", "layout-grid")
SVG_ATTRIBUTES = {
    "viewBox": "0 0 24 24", "fill": "none", "stroke": "currentColor",
    "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round",
}


class AssetError(ValueError):
    """A release input is absent, unsafe, stale, or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssetError(message)


def digest(data: bytes) -> dict[str, object]:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def safe_relative(value: str) -> str:
    require(isinstance(value, str) and bool(value), "Empty asset path")
    p = Path(value)
    require(not p.is_absolute() and all(x not in ("..", ".") for x in value.split("/"))
            and "\\" not in value, f"Unsafe asset path: {value}")
    return value


def require_plain_path(path: Path, boundary: Path) -> None:
    """Reject symlink traversal rather than accidentally changing another repo."""
    path = path.absolute()
    boundary = boundary.absolute()
    require(path.is_relative_to(boundary), f"Path escapes boundary: {path}")
    p = path
    while True:
        require(not p.is_symlink(), f"Refusing symbolic link: {p}")
        if p == boundary:
            break
        p = p.parent


def verify_file(path: Path, expected: dict[str, object], label: str = "") -> None:
    require(path.is_file() and not path.is_symlink(), f"Missing regular file: {path}")
    require(isinstance(expected, dict)
            and isinstance(expected.get("bytes"), int)
            and re.fullmatch(r"[0-9a-f]{64}", str(expected.get("sha256", ""))) is not None,
            f"Invalid hash record for {label or path}")
    got = digest(path.read_bytes())
    require(got["bytes"] == expected["bytes"] and got["sha256"] == expected["sha256"],
            f"Release hash mismatch: {label or path}. Use the pinned asset or review an explicit source update.")


def read_lock(root: Path = ROOT) -> dict:
    lock = json.loads((root / "vendor/marin-ui/lock.json").read_text(encoding="utf-8"))
    require(lock.get("schema") == 1, "Unsupported Marin UI lock schema")
    require(lock.get("marinUiVersion") == (root / "MARIN_UI_VERSION").read_text().strip(),
            "MARIN_UI_VERSION does not match the pinned input lock")
    require(set(lock.get("fonts", {})) == set(FONT_PATHS), "Font lock does not match the standard path contract")
    for path, meta in lock["fonts"].items():
        require(meta.get("source") == path, f"Unexpected font source path: {path}")
    return lock


def verify_inputs(root: Path = ROOT) -> dict:
    lock = read_lock(root)
    expected_paths = {"vendor/marin-ui/app-brand.css", "vendor/pico.min.css", "vendor/icons/lucide/LICENSE"}
    expected_paths.update(f"vendor/icons/lucide/{name}.svg" for name in ICON_NAMES)
    require(set(lock.get("files", {})) == expected_paths, "Unexpected locked UI input inventory")
    for path, meta in lock["files"].items():
        safe_relative(path)
        require_plain_path(root / path, root)
        verify_file(root / path, meta, path)
    return lock


def font_map(directory: Path) -> dict[str, Path]:
    """Accept a source checkout or a prepared font-cache directory."""
    base = directory / "vendor/fonts" if (directory / "vendor/fonts").is_dir() else directory
    return {path: base / Path(path).relative_to("vendor/fonts") for path in FONT_PATHS}


def resolve_fonts(root: Path = ROOT, source: str | Path | None = None) -> tuple[dict[str, Path], str]:
    lock = read_lock(root)
    if source is not None:
        directory = Path(source).expanduser().absolute()
    else:
        # An existing cache is authoritative only when complete and hash-valid.
        cache = root / "fonts"
        if any(path.exists() or path.is_symlink() for path in font_map(cache).values()):
            directory = cache
        else:
            directory = root.parent / "marin-ui"
    require(directory.is_dir(),
            "Required font source not found. Supply --font-source /path/to/marin-ui, "
            "place marin-ui beside this shell checkout, or run sync-fonts.sh first.")
    paths = font_map(directory)
    for relative, path in paths.items():
        require_plain_path(path, directory)
        verify_file(path, lock["fonts"][relative], relative)
    require(paths[FONT_PATHS[0]].read_bytes()[:4] in (b"\x00\x01\x00\x00", b"OTTO"), "Jost is not an SFNT font")
    require(paths[FONT_PATHS[1]].read_bytes()[:4] == b"wOF2", "Open Sans is not WOFF2")
    return paths, str(directory)
