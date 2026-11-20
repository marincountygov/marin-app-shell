#!/usr/bin/env python3
"""Unit test of scripts/audit-filter-column.py: what it lists and what it lets through.

Reads the schema from the pinned Marin UI copy (vendor/marin-ui/filter-panel.schema.json) when it has been
imported, otherwise from a sibling ../marin-ui checkout.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_filter_column", ROOT / "scripts/audit-filter-column.py")
audit_filter_column = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_filter_column)
SCHEMA = next((p for p in (ROOT / "vendor/marin-ui/filter-panel.schema.json", ROOT.parent / "marin-ui/schemas/filter-panel.schema.json") if p.is_file()), None)

GOOD = {"schemaVersion": "1.0.0", "search": {"id": "q-box"}, "groups": [
    {"type": "checkbox", "id": "dept", "label": "Departments", "allLabel": "All departments", "options": {"values": [{"value": "a", "label": "A"}]}}]}


@unittest.skipIf(SCHEMA is None, "no filter-panel.schema.json to check against")
class AuditFilterColumnTests(unittest.TestCase):
    def audit(self, html: str = "", filters: dict | None = None, js: str = "") -> list:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text(html)
            (root / "app.js").write_text(js)
            if filters is not None:
                (root / "filters.json").write_text(json.dumps(filters))
            return audit_filter_column.audit(root, SCHEMA)

    PAGE = '<div class="search-side" data-filter-column="filters.json"></div>'

    def test_a_drawn_column_passes(self):
        self.assertEqual(self.audit(self.PAGE, GOOD), [])

    def test_a_hand_written_column_is_listed(self):
        self.assertEqual(len(self.audit('<aside id="p" class="search-sidebar"></aside>')), 1)
        self.assertEqual(len(self.audit(js='el.className = "search-sidebar";')), 1)

    def test_a_steps_panel_can_say_it_is_not_a_filter(self):
        self.assertEqual(self.audit('<aside class="search-sidebar" data-filter-column-exempt="steps"></aside>'), [])

    def test_missing_file_is_listed(self):
        self.assertEqual(len(self.audit(self.PAGE)), 1)

    def test_rules_the_schema_holds(self):
        def with_group(**change):
            group = {**GOOD["groups"][0], **change}
            return {**GOOD, "groups": [group]}
        cases = {
            "any status": with_group(allLabel="Any status"),
            "filter by label": with_group(label="Filter by source"),
            "lowercase label": with_group(label="departments"),
            "colon label": with_group(label="Departments:"),
            "unknown key": with_group(placeholder="x"),
            "no options": {k: v for k, v in with_group().items()},
        }
        del cases["no options"]["groups"][0]["options"]
        cases["placeholder on search"] = {**GOOD, "search": {"id": "q", "placeholder": "Search…"}}
        cases["search label"] = {**GOOD, "search": {"id": "q", "label": "Find"}}
        cases["no groups"] = {**GOOD, "groups": []}
        for name, filters in cases.items():
            with self.subTest(name):
                self.assertTrue(self.audit(self.PAGE, filters), f"{name} should be listed")

    def test_duplicates_and_missing_data_are_listed(self):
        twice = {**GOOD, "groups": GOOD["groups"] + [{**GOOD["groups"][0]}]}
        self.assertTrue(any("more than once" in p for p in self.audit(self.PAGE, twice)))
        from_file = {**GOOD, "groups": [{**GOOD["groups"][0], "options": {"from": "nope.json", "valueField": "x"}}]}
        self.assertTrue(any("does not exist" in p for p in self.audit(self.PAGE, from_file)))

    def test_select_needs_an_all_label_or_a_default(self):
        select = {"type": "select", "id": "t", "label": "Times", "options": {"values": [{"value": "1", "label": "One"}]}}
        self.assertTrue(self.audit(self.PAGE, {**GOOD, "groups": [select]}))
        self.assertEqual(self.audit(self.PAGE, {**GOOD, "groups": [{**select, "default": "1"}]}), [])


try:
    from jsonschema import Draft202012Validator
except ImportError:  # the parity test needs the full validator; the audit itself does not
    Draft202012Validator = None
FIXTURES = ROOT.parent / "marin-ui/tests/fixtures/filters"


@unittest.skipIf(SCHEMA is None or Draft202012Validator is None or not FIXTURES.is_dir(), "needs the jsonschema package and a ../marin-ui checkout")
class ValidatorParityTests(unittest.TestCase):
    """The audit carries its own small validator so an app needs nothing installed. It must reach the same verdict
    as the full JSON Schema validator on every example file and on the cases above."""

    def verdicts(self, data):
        schema = json.loads(SCHEMA.read_text())
        full = bool(list(Draft202012Validator(schema).iter_errors(data)))
        small = bool(audit_filter_column.validate(schema, data, schema))
        return full, small

    def test_every_example_file_gets_the_same_verdict(self):
        files = sorted(FIXTURES.glob("valid-*.json")) + sorted(FIXTURES.glob("invalid-*.json"))
        self.assertGreater(len(files), 8)
        for path in files:
            with self.subTest(path.name):
                full, small = self.verdicts(json.loads(path.read_text()))
                self.assertEqual(full, small, f"{path.name}: full validator says {'fail' if full else 'pass'}, the audit says {'fail' if small else 'pass'}")

    def test_hand_made_cases_get_the_same_verdict(self):
        group = GOOD["groups"][0]
        select = {"type": "select", "id": "t", "label": "Times", "options": {"values": [{"value": "1", "label": "One"}]}}
        cases = [
            GOOD,
            {**GOOD, "groups": [{**group, "allLabel": "Any status"}]},
            {**GOOD, "groups": [{**group, "label": "Filter by x"}]},
            {**GOOD, "groups": [{**group, "label": "lower"}]},
            {**GOOD, "groups": [{**group, "extra": 1}]},
            {**GOOD, "groups": [{"type": "nope", "id": "x", "label": "X"}]},
            {**GOOD, "groups": [select]},
            {**GOOD, "groups": [{**select, "default": "1"}]},
            {**GOOD, "groups": [{**select, "default": "1", "allLabel": "All times"}]},
            {**GOOD, "groups": [{**group, "collapsed": False, "allLabel": "All departments"}]},
            {**GOOD, "groups": [{k: v for k, v in group.items() if k != "allLabel"}]},
            {**GOOD, "groups": [{k: v for k, v in group.items() if k != "allLabel"} | {"collapsed": False}]},
            {**GOOD, "groups": [{"type": "nested-checkbox", "id": "n", "label": "Ns", "groupBy": ["a", "b", "c"], "options": {"from": "f.json", "valueField": "v"}}]},
            {**GOOD, "groups": [{**group, "options": {"from": "f.json", "valueField": "v", "parentField": "p"}}]},
            {**GOOD, "groups": [{**group, "options": {"values": []}}]},
            {**GOOD, "groups": [{"type": "radio", "id": "r", "label": "Rs", "default": "a", "options": {"values": [{"value": "a", "label": "A", "hidden": True}]}}]},
            {**GOOD, "schemaVersion": "2.0.0"},
            {"schemaVersion": "1.0.0", "groups": GOOD["groups"]},
            {**GOOD, "search": {"id": "Bad Id"}},
            [],
        ]
        for index, data in enumerate(cases):
            with self.subTest(index):
                full, small = self.verdicts(data)
                self.assertEqual(full, small, f"case {index} {json.dumps(data)[:120]}: full={full}, audit={small}")


if __name__ == "__main__":
    unittest.main()
