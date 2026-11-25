#!/usr/bin/env python3
"""Unit test of scripts/audit-h1.py: what it lists and what it lets through."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("audit_h1", Path(__file__).resolve().parents[1] / "scripts/audit-h1.py")
audit_h1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_h1)


class AuditH1Tests(unittest.TestCase):
    def audit(self, css: str = "", html: str = "", js: str = "") -> list:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.css").write_text(css)
            (root / "index.html").write_text(html)
            (root / "app.js").write_text(js)
            return audit_h1.audit(root)

    def test_nothing_to_list_passes(self):
        self.assertEqual(self.audit(".card { font-size: 1rem; } h2 { font-size: 1.5rem; }", "<h1 class='page-title'>Title</h1>"), [])

    def test_a_font_size_on_h1_is_listed(self):
        self.assertEqual(len(self.audit(".reader-header h1 { font-size: 2.25rem; }")), 1)
        self.assertEqual(len(self.audit("h1 { font-size: 2rem; }")), 1)

    def test_a_font_size_in_a_media_query_is_listed(self):
        self.assertEqual(len(self.audit("@media (max-width: 600px) { .reader-header h1 { font-size: 1.75rem; } }")), 1)

    def test_a_class_used_on_an_h1_is_listed(self):
        self.assertEqual(len(self.audit(".gate__title { font-size: 1.5rem; }", '<h1 class="gate__title">Marin Budget</h1>')), 1)
        self.assertEqual(self.audit(".gate__title { font-size: 1.5rem; }", '<h2 class="gate__title">Marin Budget</h2>'), [])

    def test_a_class_used_on_an_h1_in_script_is_listed(self):
        self.assertEqual(len(self.audit(".mm-title { font-size: 2rem; }", js="root.append(h('h1', { class: 'mm-title', text: 'x' }));")), 1)

    def test_other_properties_on_h1_pass(self):
        self.assertEqual(self.audit("h1 { margin: 0; color: red; }"), [])

    def test_a_selector_that_only_contains_h1_in_its_path_is_checked_by_its_last_part(self):
        self.assertEqual(self.audit("h1 .note { font-size: 0.9rem; }"), [])

    def test_comments_are_ignored(self):
        self.assertEqual(self.audit("/* h1 { font-size: 2rem; } */"), [])


if __name__ == "__main__":
    unittest.main()
