#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHELL_JS = (ROOT / "dist/marinos.js").read_text(encoding="utf-8")
SHELL_CSS = (ROOT / "dist/marinos.css").read_text(encoding="utf-8")
SECURITY = json.loads((ROOT / "security.json").read_text(encoding="utf-8"))

TEST_HTML = """<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Shell test</title></head>
  <body>
    <marin-os-banner catalog-url="catalog.json"></marin-os-banner>
    <marin-app-header app-name="Test App" app-description="Test description">
      <template data-icon><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/></svg></template>
    </marin-app-header>
    <main id="main" class="container app-main">
      <section id="start" data-tab-section="start"><h2>Start</h2><p>Workflow</p></section>
      <marin-app-info app-name="Test App" repo="test-app" security-src="security.json">
        <template data-about><p>Custom About content.</p></template>
        <template data-accessibility><p>Custom accessibility content.</p></template>
      </marin-app-info>
    </main>
    <marin-app-footer app-name="Test App"></marin-app-footer>
    <marin-app-feedback href="https://example.test/feedback"></marin-app-feedback>
  </body>
</html>"""

CATALOG = [
    {"name": "Test App", "url": "https://example.test/test-app/"},
    {"name": "Another App", "url": "https://example.test/another/"},
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def collect_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def prepare_page(page: Page) -> list[str]:
    errors = collect_errors(page)
    page.set_content(TEST_HTML)
    page.add_style_tag(content=SHELL_CSS)
    page.evaluate(
        """([catalog, security]) => {
          window.fetch = async (input) => {
            const url = String(input);
            if (url.includes('catalog.json')) {
              return new Response(JSON.stringify(catalog), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              });
            }
            if (url.includes('security.json')) {
              return new Response(JSON.stringify(security), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              });
            }
            if (url.includes('api.github.com')) {
              return new Response(JSON.stringify([]), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              });
            }
            return new Response('Not found', { status: 404 });
          };
        }""",
        [CATALOG, SECURITY],
    )
    page.add_script_tag(content=SHELL_JS)
    page.wait_for_function("window.MarinAppShell && window.MarinAppShell.version === '1.0.0'")
    return errors


def run_test(screenshot_dir: Path | None = None) -> None:
    with sync_playwright() as playwright:
        chromium_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
        if not chromium_path:
            raise RuntimeError("A Chromium executable is required for the browser smoke test.")
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=chromium_path,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        context = browser.new_context(viewport={"width": 1440, "height": 1000}, color_scheme="light")
        page = context.new_page()
        errors = prepare_page(page)

        require(page.locator("header.app-header").count() == 1, "application header did not render")
        require(page.locator("footer.app-footer").count() == 1, "application footer did not render")
        require(page.locator(".skip-link").count() == 1, "skip link was not inserted")
        require(page.locator("#app-status-message").count() == 1, "live status region was not inserted")
        require(page.locator("#start").is_visible(), "default start section is not visible")
        require(page.locator("#about").is_hidden(), "About section should start hidden")
        require(
            page.locator(".app-footer__nav a").all_text_contents()
            == ["About", "Security", "Accessibility", "Updates"],
            "footer links are incomplete or out of order",
        )
        require(page.locator(".app-icon svg circle").count() == 1, "custom header icon did not render")

        page.locator("#app-nav a[href='#about']").click()
        page.wait_for_function("!document.querySelector('#about').hidden")
        require(page.locator("#about").is_visible(), "About route did not become visible")
        require(page.locator("#start").is_hidden(), "Start route remained visible after navigation")
        require("Custom About content." in page.locator("#about").inner_text(), "custom About content did not render")

        page.locator(".app-footer__nav a[href='#security']").click()
        page.wait_for_function("!document.querySelector('#security').hidden")
        page.locator("#security [data-security-content]").get_by_text("Static library and demonstration").wait_for()
        require(page.locator("#security").is_visible(), "Security route did not become visible")

        page.locator(".app-footer__nav a[href='#accessibility']").click()
        page.wait_for_function("!document.querySelector('#accessibility').hidden")
        require(page.locator("#accessibility").is_visible(), "Accessibility route did not become visible")
        require(
            "Custom accessibility content." in page.locator("#accessibility").inner_text(),
            "custom accessibility content did not render",
        )

        page.locator(".marinos-menu__toggle").click()
        require(page.locator("#marinos-menu-panel").is_visible(), "MarinOS menu did not open")
        page.get_by_text("Another App", exact=True).wait_for()
        page.keyboard.press("Escape")
        require(page.locator("#marinos-menu-panel").is_hidden(), "MarinOS menu did not close with Escape")

        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            page.locator(".app-footer__nav a[href='#about']").click()
            page.screenshot(path=str(screenshot_dir / "desktop-light.png"), full_page=True)

        require(not errors, f"uncaught page errors: {errors}")
        context.close()

        mobile_context = browser.new_context(viewport={"width": 640, "height": 900}, color_scheme="dark")
        mobile = mobile_context.new_page()
        mobile_errors = prepare_page(mobile)

        require(mobile.locator("#app-nav").is_hidden(), "mobile navigation should start collapsed")
        mobile.locator("#menu-toggle").click()
        mobile.wait_for_function("document.querySelector('#app-nav').hasAttribute('data-open')")
        require(mobile.locator("#app-nav").is_visible(), "mobile navigation did not open")
        require(
            mobile.locator("#menu-toggle").get_attribute("aria-expanded") == "true",
            "mobile menu state is incorrect",
        )
        mobile.keyboard.press("Escape")
        mobile.wait_for_function("!document.querySelector('#app-nav').hasAttribute('data-open')")
        require(mobile.locator("#app-nav").is_hidden(), "mobile navigation did not close with Escape")
        require(
            mobile.locator("#menu-toggle").get_attribute("aria-expanded") == "false",
            "mobile menu state did not reset",
        )

        if screenshot_dir:
            mobile.screenshot(path=str(screenshot_dir / "mobile-dark.png"), full_page=True)

        require(not mobile_errors, f"uncaught mobile page errors: {mobile_errors}")
        mobile_context.close()
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    run_test(args.screenshots)
    print("browser_smoke.py: PASS")


if __name__ == "__main__":
    main()
