#!/usr/bin/env python3
"""Fail when an app checked out next to this repo is on an older shell than this release.

An app is any sibling folder with a marin.yml that names `platform.shell`, except a library or
the platform repo itself (`project.type` of `library` or `platform`). Each app is compared with
SHELL_VERSION in two places: the `platform.shell` in its marin.yml and the `shellVersion` in its
installed vendor/marinos/manifest.json. An app is behind when either is older, and its two
numbers must agree. An app newer than this checkout also fails: update the checkout.

This is a check of the whole set, run from here. It is not part of an app's own check, so a new
shell release never makes an app's local check fail (see "Tooling" in CHANGELOG.md).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from assets import ROOT, AssetError
from install import version_key
from marin_manifest import parse_manifest

SKIPPED_TYPES = {"library", "platform"}


def project_type(text: str) -> str | None:
    in_project = False
    for line in text.splitlines():
        if re.match(r"project:\s*(#.*)?$", line):
            in_project = True
        elif in_project and re.match(r"\S", line):
            in_project = False
        elif in_project:
            match = re.match(r"\s+type:\s*['\"]?([A-Za-z-]+)", line)
            if match:
                return match[1]
    return None


def installed_version(app: Path) -> str | None:
    try:
        return json.loads((app / "vendor/marinos/manifest.json").read_bytes()).get("shellVersion")
    except (OSError, ValueError):
        return None


def audit(apps_dir: Path, current: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Return (the apps that are current, as (name, version)) and (a problem line for each that is not)."""
    ok: list[tuple[str, str]] = []
    problems: list[str] = []
    for marin_yml in sorted(apps_dir.glob("*/marin.yml")):
        app = marin_yml.parent
        data = marin_yml.read_bytes()
        try:
            declared = parse_manifest(data).version
        except AssetError:
            continue  # no platform.shell: not an app on the shell
        if project_type(data.decode("utf-8", "replace")) in SKIPPED_TYPES:
            continue
        installed = installed_version(app)
        if installed is None:
            problems.append(f"{app.name}: marin.yml says {declared} but vendor/marinos/manifest.json is missing or unreadable")
        elif installed != declared:
            problems.append(f"{app.name}: marin.yml says {declared} but the installed shell is {installed}")
        elif version_key(declared) > version_key(current):
            problems.append(f"{app.name}: shell {declared} is newer than this checkout ({current}); update the checkout")
        elif version_key(declared) < version_key(current):
            problems.append(f"{app.name}: shell {declared}, behind {current}: bash scripts/install.sh ../{app.name}")
        else:
            ok.append((app.name, declared))
    return ok, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apps-dir", type=Path, default=ROOT.parent, help="folder that holds the app checkouts (default: next to this repo)")
    args = parser.parse_args()
    current = (ROOT / "SHELL_VERSION").read_text().strip()
    ok, problems = audit(args.apps_dir.resolve(), current)
    if not ok and not problems:
        print(f"ERROR: no apps found in {args.apps_dir}", file=sys.stderr)
        return 1
    for name, version in ok:
        print(f"  {name}: {version}")
    if problems:
        print(f"{len(problems)} of {len(ok) + len(problems)} apps are not on shell {current}:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"All {len(ok)} apps are on shell {current}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
