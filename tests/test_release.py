#!/usr/bin/env python3
"""Installer fault injection uses synthetic font fixtures; rendered tests use real locked fonts."""
from __future__ import annotations
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from assets import AssetError, FONT_PATHS, digest, resolve_fonts
from build import build, expected_distribution, verify_distribution
import install as installer


def snapshot(path: Path) -> dict:
    return {str(p.relative_to(path)): ("link", os.readlink(p)) if p.is_symlink() else ("file", p.read_bytes())
            for p in path.rglob("*") if p.is_file() or p.is_symlink()}


class ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.area = Path(self.temp.name)
        self.root = self.area / "shell"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "fonts", ".marinos-install*"))
        # Test-only bytes are not real font files; don't embed/distribute real font binaries in tests.
        fixtures = (b"\0\1\0\0sfnt-test-only", b"wOF2test-only", b"Test license\n")
        self.ui = self.area / "marin-ui"
        lock_path = self.root / "vendor/marin-ui/lock.json"
        lock = json.loads(lock_path.read_text())
        for relative, data in zip(FONT_PATHS, fixtures):
            p = self.ui / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            lock["fonts"][relative] = {"source": relative, **digest(data)}
        (self.root / "vendor/licenses/OPEN_SANS_OFL.txt").write_bytes(fixtures[2])
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        with contextlib.redirect_stdout(io.StringIO()):
            build(self.root)
        self.app = self.area / "app with spaces"
        self.app.mkdir()
        (self.app / "marin.yml").write_text("schema: 1\nplatform:\n  shell: 1.0.1\n")
        (self.app / "index.html").write_text("app content must remain untouched\n")

    def run_install(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(self.app, root=self.root, **kwargs)

    def seeded(self):
        for relative, data in {
            "vendor/marinos/stale.txt": b"old shell", "vendor/fonts/unrelated.dat": b"keep font",
            "vendor/icons/lucide/radar.svg": b"app icon", "vendor/other.js": b"keep library",
            "assets/app.css": b"keep css", "security.json": b"keep security",
            FONT_PATHS[0]: b"old jost", FONT_PATHS[1]: b"old open sans",
        }.items():
            p = self.app / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)

    def test_deterministic_build(self):
        first = expected_distribution(self.root)
        with contextlib.redirect_stdout(io.StringIO()): build(self.root)
        self.assertEqual(first, expected_distribution(self.root))
        verify_distribution(self.root)

    def test_fresh_install_and_standard_paths(self):
        self.run_install()
        installer.check_app(self.app, self.root)
        for path in FONT_PATHS:
            self.assertEqual((self.app / path).read_bytes(), (self.ui / path).read_bytes())

    def test_upgrade_preserves_unrelated_files_and_source(self):
        self.seeded()
        source_before = snapshot(self.ui)
        self.run_install()
        self.assertFalse((self.app / "vendor/marinos/stale.txt").exists())
        for name in ("vendor/fonts/unrelated.dat", "vendor/icons/lucide/radar.svg", "vendor/other.js", "assets/app.css", "security.json"):
            self.assertTrue((self.app / name).exists())
        self.assertEqual((self.app / "index.html").read_text(), "app content must remain untouched\n")
        self.assertIn("1.0.1", (self.app / "marin.yml").read_text())
        self.assertEqual(source_before, snapshot(self.ui))

    def test_idempotent_install(self):
        self.run_install()
        before = snapshot(self.app)
        self.run_install()
        self.assertEqual(before, snapshot(self.app))

    def test_dry_run_does_not_modify(self):
        before = snapshot(self.app)
        self.run_install(dry_run=True)
        self.assertEqual(before, snapshot(self.app))
        self.assertEqual({p.name for p in self.app.iterdir()}, {"marin.yml", "index.html"})

    def test_missing_font_fails_before_app_changes(self):
        (self.ui / FONT_PATHS[1]).unlink()
        before = snapshot(self.app)
        with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse((self.app / "vendor").exists())

    def test_wrong_font_hash_fails_before_app_changes(self):
        (self.ui / FONT_PATHS[0]).write_bytes(b"bad source")
        before = snapshot(self.app)
        with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(before, snapshot(self.app))

    def test_missing_license_fails(self):
        (self.ui / FONT_PATHS[2]).unlink()
        with self.assertRaises(AssetError): self.run_install()
        self.assertFalse((self.app / "vendor").exists())

    def test_explicit_bad_source_is_not_silently_replaced(self):
        with self.assertRaises(AssetError): self.run_install(source=self.area / "absent")

    def test_verified_cache_supported(self):
        for relative in FONT_PATHS:
            p = self.root / "fonts" / Path(relative).relative_to("vendor/fonts")
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.ui / relative, p)
        shutil.rmtree(self.ui)
        self.run_install()
        installer.check_app(self.app, self.root)

    def test_incomplete_cache_fails_instead_of_hiding_problem(self):
        (self.root / "fonts").mkdir()
        shutil.copy2(self.ui / FONT_PATHS[0], self.root / "fonts/Jost-wght.ttf")
        with self.assertRaises(AssetError): self.run_install()

    def test_dist_tamper_fails_without_changes(self):
        with (self.root / "dist/marinos.js").open("a") as f: f.write("tamper")
        with self.assertRaises(AssetError): self.run_install()
        self.assertFalse((self.app / "vendor").exists())

    def test_upstream_input_tamper_fails(self):
        with (self.root / "vendor/marin-ui/app-brand.css").open("a") as f: f.write("\n/* bad */")
        with self.assertRaises(AssetError): self.run_install()

    def test_target_symlink_refused(self):
        outside = self.area / "outside"
        outside.mkdir()
        (outside / "protected").write_text("keep")
        (self.app / "vendor").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(snapshot(outside), {"protected": ("file", b"keep")})

    def test_existing_lock_is_not_deleted(self):
        lock = self.app / ".marinos-install.lock"
        lock.mkdir()
        with self.assertRaises(AssetError): self.run_install()
        self.assertTrue(lock.exists())

    def test_wrong_destination_type_is_refused(self):
        (self.app / "vendor").mkdir()
        (self.app / "vendor/fonts").write_text("not a directory")
        before = snapshot(self.app)
        with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(before, snapshot(self.app))

    def failure_then_compare(self, error):
        self.seeded()
        before = snapshot(self.app)
        real_replace = os.replace
        raised = False
        def failing(src, dst):
            nonlocal raised
            if not raised and str(src).endswith("new/" + FONT_PATHS[1]):
                raised = True
                raise error
            return real_replace(src, dst)
        with patch.object(installer.os, "replace", side_effect=failing):
            with self.assertRaises(type(error)): self.run_install()
        self.assertTrue(raised)
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_mid_commit_failure_rolls_back(self):
        self.failure_then_compare(OSError("injected replace failure"))

    def test_interrupt_rolls_back(self):
        self.failure_then_compare(KeyboardInterrupt())

    def test_installed_integrity_check_catches_font_damage(self):
        self.run_install()
        (self.app / FONT_PATHS[0]).write_bytes(b"corrupt")
        with self.assertRaises(AssetError): installer.check_app(self.app, self.root)

    def test_preflight_rejects_shell_target(self):
        with self.assertRaises(AssetError): installer.install(self.root, source=self.ui, root=self.root)

    def test_input_copy_race_is_caught_before_commit(self):
        before = snapshot(self.app)
        original = shutil.copy2
        def copy_bad(src, dst, *args, **kwargs):
            result = original(src, dst, *args, **kwargs)
            if str(dst).endswith("new/" + FONT_PATHS[0]): Path(dst).write_bytes(b"injected race")
            return result
        with patch.object(installer.shutil, "copy2", side_effect=copy_bad):
            with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse((self.app / "vendor").exists())

    def test_font_cache_command_and_license(self):
        result = subprocess.run([sys.executable, str(self.root / "scripts/sync_fonts.py"), str(self.ui)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in FONT_PATHS:
            self.assertEqual((self.root / "fonts" / Path(relative).relative_to("vendor/fonts")).read_bytes(), (self.ui / relative).read_bytes())
        shutil.rmtree(self.ui)
        self.run_install()

    def test_font_cache_command_missing_source_does_not_write(self):
        (self.ui / FONT_PATHS[1]).unlink()
        result = subprocess.run([sys.executable, str(self.root / "scripts/sync_fonts.py"), str(self.ui)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "fonts").exists())

    def test_input_font_symlink_is_refused(self):
        path = self.ui / FONT_PATHS[0]
        other = self.area / "font-outside"
        path.rename(other)
        path.symlink_to(other)
        with self.assertRaises(AssetError): self.run_install()
        self.assertFalse((self.app / "vendor").exists())

    def test_untrusted_svg_rejected_even_with_updated_hash(self):
        path = self.root / "vendor/icons/lucide/layout-grid.svg"
        path.write_text(path.read_text().replace("</svg>", "<script>bad()</script></svg>"))
        lockpath = self.root / "vendor/marin-ui/lock.json"
        lock = json.loads(lockpath.read_text())
        lock["files"]["vendor/icons/lucide/layout-grid.svg"].update(digest(path.read_bytes()))
        lockpath.write_text(json.dumps(lock))
        with self.assertRaises(AssetError): self.run_install()

    def test_explicit_ui_refresh_is_separate_and_read_only(self):
        lock = json.loads((self.root / "vendor/marin-ui/lock.json").read_text())
        for destination, meta in lock["files"].items():
            src = self.ui / meta["source"]
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / destination, src)
        (self.ui / "BRAND_VERSION").write_text("1.18.0\n")
        before = snapshot(self.ui)
        result = subprocess.run([sys.executable, str(self.root / "scripts/sync_ui.py"), str(self.ui)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, snapshot(self.ui))
        with contextlib.redirect_stdout(io.StringIO()): build(self.root)
        verify_distribution(self.root)
        self.run_install()


if __name__ == "__main__":
    unittest.main(verbosity=2)
