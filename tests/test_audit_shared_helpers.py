#!/usr/bin/env python3
"""Tests for scripts/audit-shared-helpers.py."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_shared_helpers", ROOT / "scripts/audit-shared-helpers.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def scan(self, files: dict[str, str]):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return audit.scan(root)

    def test_finds_own_copy_download_reading_and_upload(self):
        found = self.scan({"assets/app.js": 'document.execCommand("copy");\nURL.createObjectURL(b);\nreader.readAsText(f);\n',
                           "index.html": '<input type="file">'})
        self.assertEqual(sorted({kind for kind, *_ in found}), ["copy", "download", "file reading", "upload"])

    def test_clean_app_has_no_findings(self):
        self.assertEqual(self.scan({"assets/app.js": "marinCopyRich(t, h); marinDownload({name:'a.csv', content:c});",
                                    "index.html": '<input type="file"><script>marinUpload({})</script>'}), [])

    def test_a_marked_line_is_allowed(self):
        self.assertEqual(self.scan({"assets/engine.js": '// marin-shared-helpers: allow (refuses non-UTF-8)\nnew TextDecoder("utf-8", { fatal: true });\n'}), [])

    def test_third_party_libraries_are_skipped(self):
        self.assertEqual(self.scan({"libs/xlsx.js": "URL.createObjectURL(b)", "assets/papaparse.min.js": 'reader.readAsText(f)'}), [])

    def test_vendor_and_tests_are_skipped(self):
        self.assertEqual(self.scan({"vendor/marinos/marinos.js": 'document.execCommand("copy")', "tests/x.js": "URL.createObjectURL(b)"}), [])


if __name__ == "__main__":
    unittest.main()
