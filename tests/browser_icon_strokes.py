#!/usr/bin/env python3
"""Rendered icon regressions using the real dist JS/CSS and in-memory page fixtures.

No font source or live external data is needed for this focused test. This does
not replace browser_smoke.py font checks or browser_http.py HTTP navigation.
"""
from __future__ import annotations

import html
import json
import shutil
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
# User-supplied legacy shape, kept here only as a regression fixture.
LEGACY_SHAPE = ('<circle cx="24" cy="27" r="14"></circle>'
                '<path d="M24 19v8l6 4M18 7h12M24 7v6M36 14l3 3"></path>')
SVG = '<svg viewBox="0 0 48 48">' + LEGACY_SHAPE + '</svg>'
CANONICAL = (ROOT / "vendor/icons/lucide/layout-grid.svg").read_text(encoding="utf-8").strip()
CSS = (ROOT / "dist/marinos.css").read_text(encoding="utf-8")
JS = (ROOT / "dist/marinos.js").read_text(encoding="utf-8")
VERSION = (ROOT / "SHELL_VERSION").read_text(encoding="utf-8").strip()
CONTAINERS = ("app-icon", "app-card__icon", "docs-brand-icon", "copy-button",
              "marinos-menu__icon", "marinos-banner__icon")


class IconStrokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        executable = (shutil.which("chromium") or shutil.which("chromium-browser")
                      or shutil.which("google-chrome"))
        cls.playwright = sync_playwright().start()
        try:
            # With no system executable, Playwright uses its installed Chromium.
            cls.browser = cls.playwright.chromium.launch(
                executable_path=executable, headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        except BaseException:
            cls.playwright.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        # Guard against accidental live requests; feeds below use local fixtures.
        self.page.route("**/*", lambda route: route.abort())

    def load(self, icon=SVG, initial="", catalog=None):
        # Each load needs a new Window/custom-element registry. set_content on
        # an already-upgraded document can connect hosts before parsing children.
        self.assertFalse(self.errors)
        self.page.close()
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route("**/*", lambda route: route.abort())
        page = self.page
        page.set_content('''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Icon compatibility fixture</title></head><body>
<marin-os-banner catalog-url="catalog.json"></marin-os-banner>
<marin-app-header app-name="Test App" app-description="Stroke compatibility">
<template data-icon>''' + icon + '''</template></marin-app-header>
<main id="main"><section id="start" data-tab-section="start">''' + initial + '''</section>
<marin-app-info app-name="Test App" repo="test-app" security-src="security.json"></marin-app-info>
</main><marin-app-footer app-name="Test App"></marin-app-footer></body></html>''')
        page.add_style_tag(content=CSS)
        page.evaluate('''fixtures => {
          window.fetch = async input => {
            const url = String(input);
            const value = url.includes('catalog.json') ? fixtures.catalog :
              url.includes('security.json') ? fixtures.security : [];
            return new Response(JSON.stringify(value), {status: 200});
          };
        }''', {"catalog": catalog or [], "security": json.loads((ROOT / "security.json").read_text())})
        page.add_script_tag(content=JS)
        page.wait_for_function("version => window.MarinAppShell?.version === version", arg=VERSION)
        self.assertFalse(self.errors)

    def assert_width(self, selector, expected, attribute=True):
        svg = self.page.locator(selector).first
        if attribute:
            self.assertEqual(svg.get_attribute("stroke-width"), str(expected), selector)
        self.assertEqual(svg.evaluate("el => getComputedStyle(el).strokeWidth"), f"{expected}px", selector)
        return svg

    def test_legacy_header_defaults_to_four_without_geometry_changes(self):
        self.load()
        svg = self.assert_width("marin-app-header .app-icon svg", 4)
        self.assertEqual(svg.get_attribute("viewBox"), "0 0 48 48")
        self.assertEqual(svg.evaluate("el => el.innerHTML"), LEGACY_SHAPE)
        self.assertEqual(svg.locator("circle").evaluate("el => getComputedStyle(el).strokeWidth"), "4px")
        self.assertEqual(self.page.locator(".app-identity__home").get_attribute("href"), "./")

    def test_canonical_header_and_shell_controls_remain_two(self):
        self.load(CANONICAL)
        for selector in ("marin-app-header .app-icon svg", ".marinos-banner__icon svg", ".menu-toggle__caret"):
            with self.subTest(selector=selector):
                self.assert_width(selector, 2)

    def test_explicit_header_widths_are_preserved(self):
        for width in ("2", "4", "0", "1.5"):
            with self.subTest(width=width):
                self.load(SVG.replace('viewBox="0 0 48 48"', f'viewBox="0 0 48 48" stroke-width="{width}"'))
                self.assert_width("marin-app-header .app-icon svg", width)

    def test_header_accepts_numeric_viewbox_variants(self):
        for viewbox in (" 0  0  48  48 ", "0,0,48,48", "0.0 0.0 48.0 48.0", "-24 -24 48 48"):
            with self.subTest(viewBox=viewbox):
                self.load(SVG.replace("0 0 48 48", html.escape(viewbox, quote=True)))
                self.assert_width("marin-app-header .app-icon svg", 4)

    def test_initial_legacy_card_and_other_containers(self):
        # These are the containers covered by the initial compatibility scan.
        initial = "".join(f'<div class="{name}" id="initial-{index}">{SVG}</div>'
                          for index, name in enumerate(CONTAINERS[:4]))
        self.load(initial=initial)
        for index in range(4):
            self.assert_width(f"#initial-{index} svg", 4)

    def test_late_css_fallbacks_and_explicit_widths(self):
        self.load(CANONICAL)
        for name in CONTAINERS:
            for size, width, expected in ((48, None, 4), (24, None, 2), (48, "2", 2), (48, "4", 4), (48, "0", 0)):
                with self.subTest(container=name, size=size, explicit=width):
                    self.page.evaluate('''([name, size, width]) => {
                      document.getElementById('late')?.remove();
                      const host = document.createElement('div'); host.id = 'late'; host.className = name;
                      const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
                      svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
                      if (width !== null) svg.setAttribute('stroke-width', width);
                      host.append(svg); document.getElementById('start').append(host);
                    }''', [name, size, width])
                    svg = self.assert_width("#late svg", expected, attribute=False)
                    # CSS must not manufacture a DOM attribute or override one.
                    self.assertEqual(svg.get_attribute("stroke-width"), width)

    def test_catalog_48_and_24_use_matching_defaults(self):
        catalog = [{"name": f"Catalog {index}", "url": f"https://example.test/{index}/",
                    "icon": {"viewBox": viewbox, "markup": LEGACY_SHAPE}}
                   for index, viewbox in enumerate(("0 0 48 48", "0 0 24 24", "0,0,48,48"))]
        self.load(catalog=catalog)
        self.page.locator(".marinos-menu__toggle").click()
        self.page.locator("#marinos-menu-panel a[href='https://example.test/2/'] svg").wait_for()
        for index, width in enumerate((4, 2, 4)):
            self.assert_width(f"#marinos-menu-panel a[href='https://example.test/{index}/'] svg", width)

    def test_catalog_sanitization_and_child_width_are_preserved(self):
        markup = ('<script>window.badIcon=true</script><foreignObject><p>bad</p></foreignObject>'
                  '<circle cx="24" cy="24" r="12" stroke-width="3" onload="window.badIcon=true"/>')
        self.load(catalog=[{"name":"Untrusted", "url":"https://example.test/untrusted/",
                            "icon":{"viewBox":"0 0 48 48", "markup":markup}}])
        self.page.locator(".marinos-menu__toggle").click()
        selector = "#marinos-menu-panel a[href='https://example.test/untrusted/'] svg"
        self.page.locator(selector).wait_for()
        svg = self.assert_width(selector, 4)
        self.assertEqual(svg.locator("circle").get_attribute("stroke-width"), "3")
        self.assertEqual(svg.locator("circle").evaluate("el => getComputedStyle(el).strokeWidth"), "3px")
        self.assertEqual(svg.locator("script, foreignObject, [onload]").count(), 0)
        self.assertTrue(self.page.evaluate("!window.badIcon"))

    def test_same_rendered_size_has_equivalent_stroke_weight(self):
        initial = ('<div class="app-card__icon" id="unit24"><svg width="48" height="48" '
                   'viewBox="0 0 24 24"><circle cx="12" cy="12" r="7"/></svg></div>'
                   '<div class="app-card__icon" id="unit48">' + SVG + '</div>')
        self.load(initial=initial)
        result = self.page.evaluate('''() => ['unit24','unit48'].map(id => {
          const svg = document.querySelector(`#${id} svg`);
          return parseFloat(getComputedStyle(svg).strokeWidth) * svg.getScreenCTM().a;
        })''')
        self.assertAlmostEqual(result[0], result[1], places=5)
        self.assertGreater(result[0], 0)

    def test_unrelated_bare_svg_is_not_globally_restyled(self):
        self.load(initial='<svg id="unrelated" viewBox="0 0 48 48"><circle cx="24" cy="24" r="12"/></svg>')
        svg = self.page.locator("#unrelated")
        self.assertIsNone(svg.get_attribute("stroke-width"))
        self.assertEqual(svg.evaluate("el => getComputedStyle(el).strokeWidth"), "1px")


if __name__ == "__main__":
    unittest.main(verbosity=2)
