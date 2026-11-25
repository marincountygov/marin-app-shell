#!/usr/bin/env python3
"""Unit test of scripts/audit-steps.py: what it lists and what it lets through."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("audit_steps", Path(__file__).resolve().parents[1] / "scripts/audit-steps.py")
audit_steps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_steps)

LAYOUT = '<nav class="steps" data-steps><ol><li><a href="#a">1. A</a></li></ol></nav>'


class AuditStepsTests(unittest.TestCase):
    def audit(self, html: str = "", js: str = "") -> list:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text(html)
            (root / "app.js").write_text(js)
            return audit_steps.audit(root)

    def test_the_layout_passes(self):
        self.assertEqual(self.audit(LAYOUT), [])

    def test_an_app_with_no_steps_passes(self):
        self.assertEqual(self.audit("<p>Hello</p>", "const a = 1;"), [])

    def test_a_steps_list_in_the_filter_column_that_is_not_the_layout_is_listed(self):
        self.assertEqual(len(self.audit('<button data-filter-toggle="steps" data-filter-label="Steps"></button>')), 1)
        self.assertEqual(self.audit('<button data-filter-label="Steps"></button>' + LAYOUT), [])

    def test_a_hand_written_step_list_is_listed(self):
        self.assertEqual(len(self.audit('<nav class="spec-steps"><ol></ol></nav>')), 1)
        self.assertEqual(len(self.audit('<ol class="steps"></ol>')), 1)

    def test_a_row_of_tab_buttons_for_a_short_flow_is_not_listed(self):
        self.assertEqual(self.audit('<div class="mm-rp-stages"><button class="tab-button" aria-current="step">One</button></div>'), [])

    def test_hand_written_pager_buttons_are_listed_when_the_layout_is_used(self):
        found = self.audit(LAYOUT + '<button data-next-step="b">Next</button><button data-prev-step="a"></button>')
        self.assertEqual(len(found), 2)

    def test_script_that_marks_the_current_step_is_listed_when_the_layout_is_used(self):
        self.assertEqual(len(self.audit(LAYOUT, 'link.setAttribute("aria-current", "step");')), 1)
        self.assertEqual(self.audit("", 'link.setAttribute("aria-current", "step");'), [])

    def test_comments_are_ignored(self):
        self.assertEqual(self.audit(LAYOUT + "<!-- data-next-step -->", '// data-prev-step\n/* aria-current="step" */'), [])


if __name__ == "__main__":
    unittest.main()
