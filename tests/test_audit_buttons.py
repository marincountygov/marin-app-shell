#!/usr/bin/env python3
"""Unit test of scripts/audit-buttons.py: what it lists and what it lets through."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("audit_buttons", Path(__file__).resolve().parents[1] / "scripts/audit-buttons.py")
audit_buttons = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_buttons)


class AuditButtonsTests(unittest.TestCase):
    def audit(self, html: str = "", js: str = "") -> list:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text(html)
            (root / "app.js").write_text(js)
            return audit_buttons.audit(root)

    def test_new_kinds_pass(self):
        html = ('<button class="action-button">A</button><button class="primary">Go</button><button type="submit">Save</button>'
                '<button role="tab">Tab</button><button class="chip-button">Chip</button><button class="sort-button">Sort</button>')
        self.assertEqual(self.audit(html), [])

    def test_old_kinds_are_listed(self):
        found = self.audit('<button class="secondary">One</button><button class="outline">Two</button><button>Three</button>')
        self.assertEqual(len(found), 3)

    def test_buttons_built_in_script_are_checked(self):
        old = 'const b = document.createElement("button");\nb.type = "button";\nb.className = "secondary";\n'
        new = 'const b = document.createElement("button");\nb.className = "action-button";\n'
        self.assertEqual(len(self.audit(js=old)), 1)
        self.assertEqual(self.audit(js=new), [])

    def test_listbox_parts_are_not_action_buttons(self):
        js = 'const o = document.createElement("button");\no.className = "picker__option";\no.setAttribute("role", "option");\n'
        self.assertEqual(self.audit(js=js), [])

    def test_content_buttons_pass(self):
        self.assertEqual(self.audit('<button type="button" class="mm-term" data-button-kind="content">Name</button>'), [])
        self.assertEqual(self.audit(js="h('button', { type: 'button', class: 'event', 'data-button-kind': 'content' }, [])"), [])

    def test_comments_in_script_are_ignored(self):
        self.assertEqual(self.audit(js="/* a real <button class=\"secondary\">x</button> in a comment */\n// <button>y</button>\n"), [])

    def test_vendored_code_and_tests_are_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "vendor").mkdir()
            (root / "vendor/x.html").write_text('<button class="secondary">x</button>')
            self.assertEqual(audit_buttons.audit(root), [])


if __name__ == "__main__":
    unittest.main()
