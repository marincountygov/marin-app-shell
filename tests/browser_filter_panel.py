#!/usr/bin/env python3
"""Browser test of the collapsible filter panel in the built shell (dist/marinos.js and dist/marinos.css).

The page is served from a fake https origin through Playwright routes so localStorage works and fonts load from this
repository. Needs Playwright for Python and Chromium.  Run: python3 tests/browser_filter_panel.py
"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/"
HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Filter panel fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture"><main id="main" class="container app-main">
<form class="search-layout" id="layout-a" aria-label="Filter things">
  <div class="search-side">
    <button type="button" id="toggle-a" class="filter-toggle" data-filter-toggle="things" aria-controls="panel-a"></button>
    <aside id="panel-a" class="search-sidebar" aria-label="Filters"><label for="search-a">Search</label><input id="search-a" type="search"></aside>
  </div>
  <div class="search-results"><p>Results A</p></div>
</form>
<form class="search-layout" id="layout-b" aria-label="Filter other things">
  <div class="search-side">
    <button type="button" id="toggle-b" class="filter-toggle" data-filter-toggle="others" data-filter-label="Source filters" aria-controls="panel-b">
      <svg data-filter-icon="open" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3h18v18H3z"/></svg>
      <svg data-filter-icon="closed" viewBox="0 0 24 24" aria-hidden="true" hidden><path d="M5 5h14v14H5z"/></svg>
    </button>
    <aside id="panel-b" class="search-sidebar" aria-label="Source filters"><label for="search-b">Other</label><input id="search-b" type="search"></aside>
  </div>
  <div class="search-results"><p>Results B</p></div>
</form>
<button type="button" id="toggle-orphan" class="filter-toggle" data-filter-toggle="orphan" aria-controls="no-such-panel"></button>
</main>
<script>document.addEventListener("marin-filters-change", (e) => { window.__filterEvents = (window.__filterEvents || []).concat([[e.detail.button.id, e.detail.open]]); });</script>
</body></html>"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def serve(route):
    path = route.request.url[len(ORIGIN):].split("?")[0]
    if path == "/app/":
        route.fulfill(status=200, content_type="text/html", body=HTML)
        return
    if path == "/app/marin.yml":  # the shell reads the app's manifest for its status badge
        route.fulfill(status=200, content_type="text/yaml", body="project:\n  status: alpha\n")
        return
    mapping = {"/vendor/marinos/marinos.css": ROOT / "dist/marinos.css", "/vendor/marinos/marinos.js": ROOT / "dist/marinos.js"}
    target = mapping.get(path)
    if target is None and path.startswith("/vendor/fonts/"):
        target = ROOT / "fonts" / path[len("/vendor/fonts/"):]
    if target is not None and target.is_file():
        route.fulfill(status=200, content_type=mimetypes.guess_type(str(target))[0] or "application/octet-stream", body=target.read_bytes())
    else:
        route.fulfill(status=404, body="")


def state(page, key="a"):
    return page.evaluate(
        """key => {
            const button = document.getElementById('toggle-' + key), layout = document.getElementById('layout-' + key), panel = document.getElementById('panel-' + key);
            return { expanded: button.getAttribute('aria-expanded'), filters: layout.dataset.filters, open: panel.dataset.open,
                     label: button.getAttribute('aria-label'), title: button.title,
                     icons: [...button.querySelectorAll('svg')].map(s => [s.dataset.filterIcon, s.hasAttribute('hidden')]) };
        }""",
        key,
    )


def run(page):
    page.goto(PAGE)
    page.evaluate("localStorage.clear()")
    page.goto(PAGE)
    page.wait_for_selector("#toggle-a svg", state="attached")

    # The shell draws its bundled Lucide icons (stroked, 24x24) and names the button.
    s = state(page)
    require(s["expanded"] == "true" and s["filters"] == "open" and s["open"] == "true", f"Starts open: {s}")
    require(s["label"] == "Filters" and s["title"] == "Filters", f"Default name: {s}")
    require(s["icons"] == [["open", False], ["closed", True]], f"Open shows the panel-right-open icon: {s['icons']}")
    require(page.locator("#toggle-a svg").first.evaluate("e => [e.getAttribute('viewBox'), e.getAttribute('stroke'), e.getAttribute('aria-hidden'), getComputedStyle(e).fill]") == ["0 0 24 24", "currentColor", "true", "none"],
            "The bundled icon is a stroked 24x24 Lucide SVG hidden from assistive technology")
    require(page.is_visible("#panel-a") and page.inner_text("#toggle-a").strip() == "", "Panel visible, button has no text")
    require(page.locator("#toggle-a").evaluate("e => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)", "The button has a solid background")
    gap = page.evaluate("document.getElementById('toggle-a').getBoundingClientRect().right - document.getElementById('panel-a').getBoundingClientRect().right")
    require(abs(gap) < 1, "Open, the button sits at the right edge of the column")

    page.click("#toggle-a")
    s = state(page)
    require(s["expanded"] == "false" and s["filters"] == "closed" and s["open"] == "false", f"Click hides: {s}")
    require(s["icons"] == [["open", True], ["closed", False]], f"Hidden shows the panel-left-open icon: {s['icons']}")
    require(not page.is_visible("#panel-a") and page.evaluate("document.activeElement.id") == "toggle-a", "Panel hidden, the button keeps focus")
    require(page.evaluate("document.getElementById('toggle-a').getBoundingClientRect().left") < 100, "Hidden, the button is at the left edge")
    page.keyboard.press("Enter")
    require(state(page)["expanded"] == "true", "Enter shows the panel")
    page.keyboard.press("Space")
    require(state(page)["expanded"] == "false", "Space hides the panel")
    page.keyboard.press("Tab")
    require(page.evaluate("document.activeElement.id") != "search-a", "A hidden panel is not in the tab order")
    page.focus("#toggle-a")
    page.keyboard.press("Enter")

    page.evaluate("document.getElementById('toggle-a').dataset.filterActive = '3'")
    page.wait_for_function("document.getElementById('toggle-a').getAttribute('aria-label') === 'Filters, 3 active'", timeout=3000)
    require(page.get_attribute("#toggle-a", "title") == "Filters, 3 active", "The title matches the name")
    page.evaluate("document.getElementById('toggle-a').dataset.filterActive = '0'")
    page.wait_for_function("document.getElementById('toggle-a').getAttribute('aria-label') === 'Filters'", timeout=3000)

    page.click("#toggle-a")
    require(page.evaluate("localStorage.getItem('marinos.filters.fixture.things')") == "closed", "The choice is saved under the app id and toggle name")
    page.reload()
    page.wait_for_selector("#toggle-a svg", state="attached")
    require(state(page)["filters"] == "closed" and state(page, "b")["filters"] == "open", "Reload keeps this choice and leaves the other toggle alone")
    require(state(page, "b")["label"] == "Source filters", "data-filter-label sets the name")
    page.click("#toggle-b")
    require(state(page, "b")["icons"] == [["open", True], ["closed", False]], "Supplied icons are swapped too")
    require(["toggle-b", False] in page.evaluate("window.__filterEvents"), "marin-filters-change fired for the toggle")

    page.evaluate("localStorage.clear()")
    page.set_viewport_size({"width": 360, "height": 700})
    page.goto(PAGE)
    page.wait_for_selector("#toggle-a svg", state="attached")
    require(state(page)["filters"] == "closed" and not page.is_visible("#panel-a"), "Narrow screens start closed")
    page.click("#toggle-a")
    require(page.is_visible("#panel-a") and page.evaluate("document.getElementById('toggle-a').getBoundingClientRect().bottom <= document.getElementById('panel-a').getBoundingClientRect().top"), "Narrow, the panel opens below the button")
    require(page.evaluate("localStorage.getItem('marinos.filters.fixture.things')") is None, "A narrow-screen choice is not saved")
    require(not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"), "No horizontal scroll at 360 px")
    page.set_viewport_size({"width": 1100, "height": 800})
    page.wait_for_timeout(200)
    require(state(page)["filters"] == "open", "Wide screens return to their default")


def run_storage_blocked(browser):
    context = browser.new_context(viewport={"width": 1100, "height": 800})
    context.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });")
    context.route(f"{ORIGIN}/**", serve)
    page = context.new_page()
    page.goto(PAGE)
    page.wait_for_selector("#toggle-a svg", state="attached")
    require(state(page)["filters"] == "open", "Opens by default when storage is blocked")
    page.click("#toggle-a")
    require(state(page)["filters"] == "closed", "Still toggles when storage is blocked")
    context.close()


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("light", "dark"):
            context = browser.new_context(color_scheme=scheme, viewport={"width": 1100, "height": 800})
            context.route(f"{ORIGIN}/**", serve)
            page = context.new_page()
            page.on("pageerror", lambda e: problems.append(str(e)))
            page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
            run(page)
            context.close()
        run_storage_blocked(browser)
        browser.close()
    require(not problems, f"Console or page errors: {problems}")
    print("Shell filter panel browser test (light and dark): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
