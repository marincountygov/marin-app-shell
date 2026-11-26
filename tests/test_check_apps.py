#!/usr/bin/env python3
"""Unit test of scripts/check-apps.py: which apps it lets through and which it fails."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("check_apps", SCRIPTS / "check-apps.py")
check_apps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_apps)


def make(root: Path, name: str, declared: str | None, installed: str | None = None, kind: str = "app") -> None:
    folder = root / name
    folder.mkdir()
    platform = f"platform:\n  shell: {declared}\n" if declared else ""
    (folder / "marin.yml").write_text(f"schema: 1\n\nproject:\n  name: {name}\n  type: {kind}\n\n{platform}")
    if installed:
        (folder / "vendor/marinos").mkdir(parents=True)
        (folder / "vendor/marinos/manifest.json").write_text(json.dumps({"shellVersion": installed}))


class CheckAppsTests(unittest.TestCase):
    def audit(self, build) -> tuple[list, list]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build(root)
            return check_apps.audit(root, "2.10.0")

    def test_an_app_on_the_current_shell_passes(self):
        ok, problems = self.audit(lambda r: make(r, "marin-a", "2.10.0", "2.10.0"))
        self.assertEqual((ok, problems), ([("marin-a", "2.10.0")], []))

    def test_an_app_behind_fails_with_the_install_command(self):
        ok, problems = self.audit(lambda r: make(r, "marin-a", "2.8.0", "2.8.0"))
        self.assertEqual(ok, [])
        self.assertEqual(len(problems), 1)
        self.assertIn("install.sh ../marin-a", problems[0])

    def test_versions_compare_as_numbers(self):
        ok, problems = self.audit(lambda r: make(r, "marin-a", "2.9.0", "2.9.0"))
        self.assertEqual(len(problems), 1)
        ok, problems = self.audit(lambda r: make(r, "marin-a", "2.100.0", "2.100.0"))
        self.assertIn("newer than this checkout", problems[0])

    def test_the_yml_and_the_installed_manifest_must_agree(self):
        self.assertEqual(len(self.audit(lambda r: make(r, "marin-a", "2.10.0", "2.8.0"))[1]), 1)

    def test_a_missing_installed_manifest_fails(self):
        self.assertEqual(len(self.audit(lambda r: make(r, "marin-a", "2.10.0"))[1]), 1)

    def test_a_library_a_platform_repo_and_a_repo_without_a_shell_are_skipped(self):
        def build(root: Path) -> None:
            make(root, "marin-ui", "1.24.0", "1.24.0", kind="library")
            make(root, "marin-os", "2.8.0", "2.8.0", kind="platform")
            make(root, "marin-data", None)
        self.assertEqual(self.audit(build), ([], []))

    def test_one_behind_among_current_apps_is_the_only_problem(self):
        def build(root: Path) -> None:
            make(root, "marin-a", "2.10.0", "2.10.0")
            make(root, "marin-b", "2.8.0", "2.8.0")
        ok, problems = self.audit(build)
        self.assertEqual([name for name, _ in ok], ["marin-a"])
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
