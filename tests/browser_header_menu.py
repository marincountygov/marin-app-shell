#!/usr/bin/env python3
"""Browser test of the header and the MarinOS menu in the built shell (dist/marinos.js and dist/marinos.css):
the header holds only an app's own tabs (no About or Updates by default, no Menu button when it is empty), and the
MarinOS menu is a vertical list on a narrow screen, a wide horizontal grid on a large one, and leaves out an unlisted app.

The page is served from a fake https origin through Playwright routes. Needs Playwright for Python and Chromium.
Run: python3 tests/browser_header_menu.py
"""
from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
ICON = {"viewBox": "0 0 24 24", "markup": '<rect width="7" height="7" x="3" y="3" rx="1"/>'}
CATALOG = [{"id": f"app-{i}", "name": f"Sample App {i}", "url": f"{ORIGIN}/app-{i}/", "status": "beta" if i % 2 else "alpha", "icon": ICON} for i in range(1, 11)]
CATALOG.append({"id": "hidden-app", "name": "Hidden App", "url": f"{ORIGIN}/hidden/", "status": "alpha", "icon": ICON, "unlisted": True})
CATALOG.append({"id": "page", "name": "Fixture", "url": f"{ORIGIN}/page/", "status": "beta", "icon": ICON})


def page_html(header_attrs: str = "", header_body: str = "") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Header fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="page">
<marin-os-banner label="beta" catalog-url="/catalog.json" browse-url="/"></marin-os-banner>
<marin-app-header app-id="page" app-name="Fixture" app-description="A fixture." {header_attrs}>{header_body}</marin-app-header>
<main id="main" class="container app-main"><section id="start" data-tab-section="start"><h2>Start</h2><p>Content.</p></section>
<marin-app-info app-name="Fixture" repo="fixture" security-src="security.json"><template data-about><p>About.</p></template></marin-app-info></main>
<marin-app-footer app-name="Fixture"></marin-app-footer></body></html>"""


PAGES = {
    "/plain/": page_html(),
    "/tabs/": page_html(header_body='<template data-navigation><a href="#about">About</a></template>'),
    "/explicit/": page_html(header_attrs='standard-links="about updates"'),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def serve(route):
    path = route.request.url[len(ORIGIN):].split("?")[0]
    if path in PAGES:
        route.fulfill(status=200, content_type="text/html", body=PAGES[path])
        return
    if path == "/catalog.json":
        route.fulfill(status=200, content_type="application/json", body=json.dumps(CATALOG))
        return
    if path.endswith("marin.yml"):
        route.fulfill(status=200, content_type="text/yaml", body="project:\n  status: beta\n")
        return
    mapping = {"/vendor/marinos/marinos.css": ROOT / "dist/marinos.css", "/vendor/marinos/marinos.js": ROOT / "dist/marinos.js"}
    target = mapping.get(path)
    if target is None and path.startswith("/vendor/fonts/"):
        target = ROOT / "fonts" / path[len("/vendor/fonts/"):]
    if target is not None and target.is_file():
        route.fulfill(status=200, content_type=mimetypes.guess_type(str(target))[0] or "application/octet-stream", body=target.read_bytes())
    else:
        route.fulfill(status=404, body="")


def load(page, path):
    page.goto(ORIGIN + path)
    page.wait_for_selector(".app-header", state="attached")


def header_checks(page):
    # By default the header holds only the app's name: no About or Updates, no Menu button, no empty navigation.
    for width in (1280, 390):
        page.set_viewport_size({"width": width, "height": 800})
        load(page, "/plain/")
        require(page.locator("#app-nav a").count() == 0, "The default header has no links")
        require(not page.is_visible("#menu-toggle"), f"No Menu button without tabs at {width}px")
        require(not page.is_visible("#app-nav"), f"No empty navigation shows at {width}px")
        require(page.is_visible(".app-title"), "The app name still shows")
        # The standard pages are still in the footer.
        require(page.locator(".app-footer__nav a").all_text_contents()[:2] == ["About", "Security"], f"The footer keeps the standard pages: {page.locator('.app-footer__nav a').all_text_contents()}")
    # An app with its own tab keeps the header menu: the tab on a wide screen, the Menu button on a narrow one.
    page.set_viewport_size({"width": 1280, "height": 800})
    load(page, "/tabs/")
    require(page.is_visible("#app-nav a[href='#about']") and not page.is_visible("#menu-toggle"), "A wide header shows the app's tab and no Menu button")
    page.set_viewport_size({"width": 390, "height": 800})
    load(page, "/tabs/")
    require(page.is_visible("#menu-toggle") and not page.is_visible("#app-nav"), "A narrow header has a Menu button and a closed menu")
    page.click("#menu-toggle")
    require(page.is_visible("#app-nav a[href='#about']"), "The Menu button opens the tab")
    page.keyboard.press("Escape")
    require(page.get_attribute("#menu-toggle", "aria-expanded") == "false", "Escape closes the menu")
    # An app can still name a standard page for its header.
    page.set_viewport_size({"width": 1280, "height": 800})
    load(page, "/explicit/")
    require(page.locator("#app-nav a").all_text_contents() == ["About", "Updates"], "standard-links still works when an app names it")


def menu_checks(page):
    def open_menu(width):
        page.set_viewport_size({"width": width, "height": 900})
        load(page, "/plain/")
        page.wait_for_function("document.querySelectorAll('#marinos-menu-panel .marinos-menu__name').length >= 10")
        page.click(".marinos-menu__toggle")
        require(page.is_visible("#marinos-menu-panel"), f"The MarinOS menu opens at {width}px")
        return page.eval_on_selector_all("#marinos-menu-panel a", "els => els.map(e => { const r = e.getBoundingClientRect(); return { t: e.textContent.trim(), x: r.x, y: r.y, w: r.width, h: r.height, all: e.classList.contains('marinos-menu__all') }; })")

    names = lambda items: [i["t"] for i in items]
    wide = open_menu(1280)
    require(not any("Hidden App" in n for n in names(wide)), "An unlisted app is not in the menu")
    require(sum(1 for n in names(wide) if n.startswith("Sample App")) == 10, f"Every listed app is in the menu: {names(wide)}")
    apps = [i for i in wide if not i["all"]]
    rows = sorted({round(i["y"]) for i in apps})
    columns = sorted({round(i["x"]) for i in apps})
    require(len(columns) >= 3 and len(rows) < len(apps), f"On a large screen the apps sit in a horizontal grid: {len(columns)} columns, {len(rows)} rows")
    require(all(i["h"] >= 44 for i in wide), "Menu items are at least 44 px tall")
    gaps = [b["x"] - (a["x"] + a["w"]) for a, b in zip(apps, apps[1:]) if abs(a["y"] - b["y"]) < 2]
    require(gaps and min(gaps) >= 16, f"There is room between the items: {gaps}")
    browse = next(i for i in wide if i["all"])
    require(browse["w"] >= max(columns) - min(columns), "Browse all runs along the bottom")
    require(page.eval_on_selector("#marinos-menu-panel", "e => e.getBoundingClientRect().right <= window.innerWidth"), "The wide panel stays on the screen")
    page.keyboard.press("Escape")
    require(page.get_attribute(".marinos-menu__toggle", "aria-expanded") == "false" and not page.is_visible("#marinos-menu-panel"), "Escape closes the menu")
    require(page.evaluate("document.activeElement.classList.contains('marinos-menu__toggle')"), "Focus returns to the menu button")

    narrow = open_menu(390)
    apps = [i for i in narrow if not i["all"]]
    require(len({round(i["x"]) for i in apps}) == 1, "On a narrow screen the apps are one vertical list")
    require(page.eval_on_selector("#marinos-menu-panel", "e => e.getBoundingClientRect().right <= window.innerWidth"), "The narrow panel stays on the screen")
    require(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "No horizontal scroll at 390px")


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("light", "dark"):
            context = browser.new_context(color_scheme=scheme, viewport={"width": 1280, "height": 800})
            context.route(f"{ORIGIN}/**", serve)
            page = context.new_page()
            page.on("pageerror", lambda e: problems.append(str(e)))
            page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
            header_checks(page)
            menu_checks(page)
            context.close()
        browser.close()
    require(not problems, f"Console or page errors: {problems}")
    print("Shell header and MarinOS menu browser test (light and dark): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
