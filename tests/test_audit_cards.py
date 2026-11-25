#!/usr/bin/env python3
"""Unit test of scripts/audit-cards.py: what it lists and what it lets through."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("audit_cards", Path(__file__).resolve().parents[1] / "scripts/audit-cards.py")
audit_cards = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_cards)


class AuditCardsTests(unittest.TestCase):
    def audit(self, css: str) -> list:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.css").write_text(css)
            return audit_cards.audit(root)

    def test_nothing_to_list_passes(self):
        self.assertEqual(self.audit(".job-card-header { display: flex; gap: 1rem; } .mm-card__source { font-weight: 400; } .mm-card__favicon { width: 1rem; }"), [])

    def test_a_copy_of_a_shared_rule_is_listed(self):
        for css in (".search-results-list { gap: 1rem; }", ".search-results-list > .app-card { margin-bottom: 0; }", ".mm-card { display: flex; }",
                    ".mm-card__title { margin: 0; }", ".mm-card__byline { font-size: 0.9375rem; }", ".mm-card__image { width: 9rem; }"):
            self.assertEqual(len(self.audit(css)), 1, css)

    def test_a_rule_in_a_media_query_is_listed(self):
        self.assertEqual(len(self.audit("@media (max-width: 480px) { .mm-card { flex-direction: column; } }")), 1)

    def test_something_inside_a_shared_part_passes(self):
        self.assertEqual(self.audit(".mm-card__meta .app-badge { font-weight: 400; } .mm-card__byline time { font-style: italic; } .mm-card__title a { color: red; }"), [])

    def test_a_redrawn_surface_is_listed(self):
        self.assertEqual(len(self.audit(".job-card { padding: 1rem; border: 1px solid #ccc; border-radius: 4px; background: #fff; }")), 1)
        self.assertEqual(len(self.audit(".card { box-shadow: none; }")), 1)
        self.assertEqual(len(self.audit(".app-card { background: #eee; }")), 1)

    def test_layout_on_a_card_class_passes(self):
        self.assertEqual(self.audit(".job-card { display: grid; gap: 0.5rem; } .app-card { margin-bottom: 0; }"), [])

    def test_a_part_of_a_card_may_have_a_surface(self):
        self.assertEqual(self.audit(".logo-card__preview { border: 1px solid #ccc; background: #fafafa; }"), [])

    def test_the_learn_editor_is_left_out(self):
        self.assertEqual(self.audit(".editor-task-card { border: 1px solid #ccc; padding: 1.5rem; }"), [])

    def test_an_exempt_comment_lets_a_rule_stay(self):
        self.assertEqual(self.audit("/* audit-cards: exempt (a brand's own logo card) */\n.logo-card { border: 1px solid #ccc; }"), [])
        self.assertEqual(len(self.audit("/* a note */\n.logo-card { border: 1px solid #ccc; }")), 1)

    def test_comments_are_ignored(self):
        self.assertEqual(self.audit("/* .mm-card { display: flex; } */"), [])


if __name__ == "__main__":
    unittest.main()
