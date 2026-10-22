#!/usr/bin/env python3
"""Accent text on a tint of the accent must use --app-accent-on-tint. Plain --app-accent is 3.8:1 on a 14% tint and
4.2:1 on an 8% tint in light mode (marin-ui's scripts/check-contrast.js lists the pairs, but it reads token values, so
it cannot see which token a rule uses; this test reads the rules). Run: python3 tests/test_contrast_tokens.py"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / "src/shell.css").read_text(encoding="utf-8")


def rule(selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert match, f"rule not found: {selector}"
    return match.group(1)


class ContrastTokenTests(unittest.TestCase):
    def test_text_on_an_accent_tint_uses_accent_on_tint(self):
        for selector in ('.action-button[aria-pressed="true"]', '.chip-button[aria-pressed="true"]',
                         ".action-group > .action-button:hover", ".action-group > .copy-button:hover"):
            body = rule(selector)
            self.assertIn("color-mix(in srgb, var(--app-accent)", body, f"{selector} sets a tint")
            self.assertIn("color: var(--app-accent-on-tint)", body, f"{selector} must use --app-accent-on-tint for its text")

    def test_the_audit_script_ships_in_the_distribution(self):
        dist = Path(__file__).resolve().parents[1] / "dist/audit-buttons.py"
        self.assertTrue(dist.is_file(), "dist/audit-buttons.py is missing; run scripts/build.sh")


if __name__ == "__main__":
    unittest.main()
