#!/usr/bin/env python3
"""Installer fault injection uses synthetic font fixtures; rendered tests use real locked fonts."""
from __future__ import annotations
import contextlib
import io
import json
import os
import signal
import stat
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
from marin_manifest import parse_manifest


def shell_version(root: Path) -> str:
    return (root / "SHELL_VERSION").read_text(encoding="utf-8").strip()


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
        self.assertEqual((self.app / "marin.yml").read_text(),
                         "schema: 1\nplatform:\n  shell: " + (self.root / "SHELL_VERSION").read_text().strip() + "\n")
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

    def test_manifest_version_is_updated_automatically(self):
        self.run_install()
        self.assertEqual(
            parse_manifest((self.app / "marin.yml").read_bytes()).version,
            shell_version(self.root),
        )
        installer.check_app(self.app, self.root)

    def test_manifest_bytes_and_permissions_are_preserved(self):
        original = (b'\xef\xbb\xbf# release config\r\nschema: 1\r\nproject:\r\n'
                    b'  name: "Example app"\r\nplatform: # shared runtime\r\n'
                    b'  shell: \'1.0.1\'  # keep this note\r\n  custom: true\r\n'
                    b'deployment:\r\n  url: https://example.test/app/\r\n# no final newline')
        path = self.app / "marin.yml"
        path.write_bytes(original)
        path.chmod(0o640)
        self.run_install()
        target = shell_version(self.root).encode("utf-8")
        expected = original.replace(b"'1.0.1'", b"'" + target + b"'")
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_manifest_missing_or_invalid_refused_before_writes(self):
        cases = [None, b"schema: 1\nplatform:\n  template: manual\n",
                 b"platform:\n  shell: 1.0.1\n  shell: 1.0.0\n",
                 b"platform: {shell: 1.0.1}\n", b"platform:\n  shell: null\n"]
        for data in cases:
            for dry_run in (False, True):
                with self.subTest(data=data, dry_run=dry_run):
                    path = self.app / "marin.yml"
                    if data is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(data)
                    before = snapshot(self.app)
                    with self.assertRaises(AssetError): self.run_install(dry_run=dry_run)
                    self.assertEqual(before, snapshot(self.app))
                    self.assertFalse((self.app / "vendor").exists())
                    self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_manifest_symlink_is_rejected_without_changing_external_file(self):
        path = self.app / "marin.yml"
        external = self.area / "external.yml"
        path.rename(external)
        original = external.read_bytes()
        path.symlink_to(external)
        with self.assertRaises(AssetError): self.run_install()
        self.assertEqual(external.read_bytes(), original)
        self.assertFalse((self.app / "vendor").exists())

    def test_manifest_directory_is_rejected(self):
        (self.app / "marin.yml").unlink()
        (self.app / "marin.yml").mkdir()
        with self.assertRaises(AssetError): self.run_install()
        self.assertFalse((self.app / "vendor").exists())

    def test_dry_run_reports_metadata_transition(self):
        before = snapshot(self.app)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            installer.install(self.app, root=self.root, dry_run=True)
        self.assertIn(
            f"platform.shell: 1.0.1 -> {shell_version(self.root)}",
            output.getvalue(),
        )
        self.assertIn("  marin.yml\n", output.getvalue())
        self.assertIn("No files changed", output.getvalue())
        self.assertEqual(before, snapshot(self.app))

    def test_check_rejects_stale_manifest_and_makes_no_changes(self):
        self.run_install()
        path = self.app / "marin.yml"
        current = shell_version(self.root).encode("utf-8")
        path.write_bytes(path.read_bytes().replace(current, b"1.0.1"))
        before = snapshot(self.app)
        with self.assertRaisesRegex(AssetError, "platform.shell is 1.0.1"):
            installer.check_app(self.app, self.root)
        self.assertEqual(before, snapshot(self.app))

    def test_cli_check_requires_no_font_source(self):
        self.run_install()
        shutil.rmtree(self.ui)
        result = subprocess.run(["bash", str(self.root / "scripts/install.sh"), str(self.app), "--check"],
                                cwd=self.area, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("marin.yml integrity: PASS", result.stdout)

    def test_cli_check_rejects_active_lock(self):
        self.run_install()
        (self.app / ".marinos-install.lock").mkdir()
        result = subprocess.run(["bash", str(self.root / "scripts/install.sh"), str(self.app), "--check"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Install lock exists", result.stderr)
        self.assertTrue((self.app / ".marinos-install.lock").exists())

    def test_staged_metadata_tamper_is_detected(self):
        before = snapshot(self.app)
        real_write = Path.write_bytes
        def tamper(path, data):
            if str(path).endswith("new/marin.yml"):
                data += b"unexpected: true\n"
            return real_write(path, data)
        with patch.object(Path, "write_bytes", tamper):
            with self.assertRaisesRegex(AssetError, "prepared scalar-only update"):
                self.run_install()
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse((self.app / "vendor").exists())

    def test_manifest_edit_during_staging_is_not_overwritten(self):
        self.seeded()
        original = (self.app / "marin.yml").read_bytes()
        changed = original + b"# edit from another process\n"
        before = snapshot(self.app)
        real_copy = shutil.copy2
        def edit(src, dst, *args, **kwargs):
            result = real_copy(src, dst, *args, **kwargs)
            if str(dst).endswith("new/" + FONT_PATHS[0]):
                (self.app / "marin.yml").write_bytes(changed)
            return result
        with patch.object(installer.shutil, "copy2", side_effect=edit):
            with self.assertRaisesRegex(AssetError, "changed while installation"):
                self.run_install()
        before["marin.yml"] = ("file", changed)
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_manifest_edit_during_commit_preserved_and_assets_rolled_back(self):
        self.seeded()
        changed = (self.app / "marin.yml").read_bytes() + b"# concurrent edit\n"
        before = snapshot(self.app)
        real_replace = os.replace
        def edit(src, dst):
            result = real_replace(src, dst)
            if str(src).endswith("new/vendor/marinos"):
                (self.app / "marin.yml").write_bytes(changed)
            return result
        with patch.object(installer.os, "replace", side_effect=edit):
            with self.assertRaisesRegex(AssetError, "changed while installation"):
                self.run_install()
        before["marin.yml"] = ("file", changed)
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def manifest_failure(self, when, after=False, error=None):
        self.seeded()
        before = snapshot(self.app)
        mode = stat.S_IMODE((self.app / "marin.yml").stat().st_mode)
        real_replace = os.replace
        triggered = False
        def fail(src, dst):
            nonlocal triggered
            matches = (str(src).endswith("new/marin.yml") if when == "new"
                       else str(dst).endswith("old/marin.yml"))
            if matches and not triggered:
                triggered = True
                if after:
                    real_replace(src, dst)
                raise error if error is not None else OSError("injected metadata rename failure")
            return real_replace(src, dst)
        with patch.object(installer.os, "replace", side_effect=fail):
            with self.assertRaises(type(error) if error is not None else OSError):
                self.run_install()
        self.assertTrue(triggered)
        self.assertEqual(before, snapshot(self.app))
        self.assertEqual(mode, stat.S_IMODE((self.app / "marin.yml").stat().st_mode))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_failure_before_manifest_write_rolls_back_all_assets(self):
        self.manifest_failure("new")

    def test_failure_after_manifest_write_rolls_back_manifest_and_assets(self):
        self.manifest_failure("new", after=True)

    def test_interrupt_after_manifest_write_rolls_back_manifest_and_assets(self):
        self.manifest_failure("new", after=True, error=KeyboardInterrupt())

    def test_interrupt_after_manifest_backup_restores_original(self):
        self.manifest_failure("backup", after=True, error=KeyboardInterrupt())

    def test_final_validation_failure_rolls_back_manifest_and_assets(self):
        self.seeded()
        before = snapshot(self.app)
        real_check = installer.check_app
        def fail(app, root):
            real_check(app, root)
            if app == self.app:
                self.assertEqual(
                    parse_manifest((app / "marin.yml").read_bytes()).version,
                    shell_version(self.root),
                )
                raise AssetError("injected final validation failure")
        with patch.object(installer, "check_app", side_effect=fail):
            with self.assertRaisesRegex(AssetError, "injected final validation"):
                self.run_install()
        self.assertEqual(before, snapshot(self.app))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_real_sigterm_after_metadata_write_rolls_back(self):
        self.seeded()
        before = snapshot(self.app)
        old_handler = signal.getsignal(signal.SIGTERM)
        real_replace = os.replace
        def terminate(src, dst):
            result = real_replace(src, dst)
            if str(src).endswith("new/marin.yml"):
                os.kill(os.getpid(), signal.SIGTERM)
            return result
        with patch.object(installer.os, "replace", side_effect=terminate):
            with self.assertRaises(installer.InstallInterrupted):
                self.run_install()
        self.assertEqual(before, snapshot(self.app))
        self.assertEqual(old_handler, signal.getsignal(signal.SIGTERM))
        self.assertFalse(list(self.app.glob(".marinos-install*")))

    def test_failed_rollback_retains_recovery_and_lock(self):
        self.seeded()
        original = (self.app / "marin.yml").read_bytes()
        real_replace = os.replace
        def fail(src, dst):
            if str(src).endswith("new/marin.yml") or str(src).endswith("old/marin.yml"):
                raise OSError("injected filesystem error")
            return real_replace(src, dst)
        errors = io.StringIO()
        with patch.object(installer.os, "replace", side_effect=fail), contextlib.redirect_stderr(errors):
            with self.assertRaises(OSError): self.run_install()
        lock = self.app / ".marinos-install.lock"
        self.assertTrue(lock.is_dir())
        recovery = Path((lock / "transaction.txt").read_text().strip())
        self.assertEqual((recovery / "old/marin.yml").read_bytes(), original)
        self.assertIn("Recovery needs inspection", errors.getvalue())


    def test_every_commit_rename_boundary_rolls_back(self):
        # Test failures just before AND just after each rename, with both fresh
        # and existing managed assets. This catches signal/bookkeeping gaps.
        for existing in (False, True):
            shutil.rmtree(self.app)
            self.app.mkdir()
            (self.app / "marin.yml").write_text("schema: 1\nplatform:\n  shell: 1.0.1\n")
            (self.app / "index.html").write_text("untouched\n")
            if existing:
                self.seeded()
            saved = self.area / ("snapshot-existing" if existing else "snapshot-fresh")
            shutil.copytree(self.app, saved)
            before = snapshot(self.app)
            directories = {str(p.relative_to(self.app)) for p in self.app.rglob("*") if p.is_dir()}
            real_replace = os.replace
            calls = []
            def record(src, dst):
                calls.append((str(src), str(dst)))
                return real_replace(src, dst)
            with patch.object(installer.os, "replace", side_effect=record):
                self.run_install()
            for boundary in range(1, len(calls) + 1):
                for after in (False, True):
                    with self.subTest(existing=existing, boundary=boundary, after=after):
                        shutil.rmtree(self.app)
                        shutil.copytree(saved, self.app)
                        count = 0
                        fired = False
                        def fail(src, dst):
                            nonlocal count, fired
                            count += 1
                            if not fired and count == boundary:
                                fired = True
                                if after:
                                    real_replace(src, dst)
                                raise OSError("injected rename boundary failure")
                            return real_replace(src, dst)
                        with patch.object(installer.os, "replace", side_effect=fail):
                            with self.assertRaises(OSError): self.run_install()
                        self.assertTrue(fired)
                        self.assertEqual(before, snapshot(self.app))
                        self.assertEqual(directories, {str(p.relative_to(self.app))
                                                      for p in self.app.rglob("*") if p.is_dir()})


class ManifestTests(unittest.TestCase):
    def test_scalar_only_replacement_across_supported_formats(self):
        for ending in ("\n", "\r\n"):
            for quote in ("", "'", '"'):
                for bom in (b"", b"\xef\xbb\xbf"):
                    with self.subTest(ending=ending, quote=quote, bom=bom):
                        text = ending.join((
                            "# header", "---", "schema: 1", "project:", "  name: County caf\u00e9",
                            "  shell: 9.9.9 # unrelated", "'platform': # keep",
                            f'  "shell": {quote}1.0.1{quote}   # release note',
                            "  template: manual", "deployment:", "  url: https://example.test/app/", "..."))
                        data = bom + text.encode("utf-8")
                        document = parse_manifest(data)
                        self.assertEqual(document.version, "1.0.1")
                        self.assertEqual(document.updated("1.1.0"), data.replace(b"1.0.1", b"1.1.0"))
                        self.assertEqual(document.updated("1.0.1"), data)

    def test_nested_lookalike_is_not_the_managed_key(self):
        data = (b"metadata:\n  platform:\n    shell: 4.0.0\n"
                b"platform:\n  options:\n    shell: 3.0.0\n  shell: 1.0.1\n")
        self.assertEqual(parse_manifest(data).updated("1.1.0"), data.replace(b"1.0.1", b"1.1.0"))

    def test_semver_prerelease_and_build_metadata(self):
        for version in ("0.0.0", "1.0.0-rc.1", "1.0.0+build.001", "1.0.0-beta.0+git.abc"):
            data = f"platform:\n  shell: '{version}'\n".encode()
            self.assertEqual(parse_manifest(data).version, version)
            self.assertEqual(parse_manifest(data).updated("1.1.0"), b"platform:\n  shell: '1.1.0'\n")

    def test_ambiguous_and_unsupported_yaml_is_rejected(self):
        cases = [
            "", "schema: 1\n", "platform:\n  template: manual\n",
            "platform:\n  shell: 1.0.1\nplatform:\n  shell: 1.0.0\n",
            "platform:\n  shell: 1.0.1\n  'shell': 1.0.0\n",
            "platform:\n  shell: 1.0.1\n'platform':\n  shell: 1.0.0\n",
            "platform: {shell: 1.0.1}\n", "platform:\n  shell: null\n",
            "platform:\n  shell:\n", "platform:\n  shell: 1.0\n",
            "platform:\n  shell: 01.0.1\n", "platform:\n  shell: v1.0.1\n",
            "platform:\n  shell: 1.0.0-01\n",
            "platform: &shared\n  shell: 1.0.1\n", "platform: *shared\n",
            "platform:\n  <<: *shared\n  shell: 1.0.1\n",
            "platform:\n  shell: !!str 1.0.1\n",
            "platform:\n\tshell: 1.0.1\n", "platform:\n  shell: [1.0.1]\n",
            "platform:\n  shell: 1.0.1\n---\nplatform:\n  shell: 1.0.0\n",
            "platform:\n  shell: 1.0.1\n...\nplatform:\n  shell: 1.0.0\n",
            "description: |\n  platform:\n    shell: 1.0.1\n",
            'description: "multiline\nplatform:\n  shell: 1.0.1\n"\n',
            'platform:\n  shell: "1.0.1"oops\n',
            'platform:\n  shell: "1.0.1"# no whitespace\n',
            "platform:\n  shell:1.0.1\n", "%YAML 1.2\nplatform:\n  shell: 1.0.1\n",
            "schema: 1\n  platform:\n    shell: 1.0.1\n",
            "platform:\n  shell: 1.0.1\n other: value\n",
            "platform:\n  shell: 1.0.1\nitems:\n  - value\n",
            "platform:\n  shell: 1.0.1\nsettings: [a, b]\n",
            'platform:\n  shell: "1.0.1\\q"\n',
            "platform:\n  shell: 1.0.1\nschema: 1\nschema: 2\n",
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(AssetError): parse_manifest(text.encode())

    def test_non_utf8_and_control_characters_rejected(self):
        for data in (b"\xff", b"platform:\n  shell: 1.0.1\x00\n"):
            with self.assertRaises(AssetError): parse_manifest(data)

    def test_invalid_target_version_rejected(self):
        manifest = parse_manifest(b"platform:\n  shell: 1.0.1\n")
        for version in ("v1.1.0", "1.1", "1.1.0\nother: true", "01.1.0"):
            with self.assertRaises(AssetError): manifest.updated(version)


if __name__ == "__main__":
    unittest.main(verbosity=2)
