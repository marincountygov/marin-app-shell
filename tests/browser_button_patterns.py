#!/usr/bin/env python3
"""Browser test of the shell's button kinds: declarative icons, tabs, chips, sort headers, dialog buttons, danger.

Serves the built shell (dist/marinos.js and dist/marinos.css) from a fake https origin through Playwright routes.
Needs Playwright for Python and Chromium.  Run: python3 tests/browser_button_patterns.py
"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/"
HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Button patterns fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture"><main id="main" class="container app-main">
<div class="action-group" role="group" aria-label="Tools">
  <button type="button" id="dl" class="action-button" data-icon="download" aria-label="Download CSV" title="Download CSV"></button>
  <button type="button" id="del" class="action-button is-danger" data-icon="trash" aria-label="Delete row" title="Delete row"></button>
</div>
<a id="more" class="action-button" href="#more" data-icon-end="arrow-right">Learn more</a>
<button type="button" id="typo" class="action-button" data-icon="no-such-icon" aria-label="Typo"></button>
<div class="tab-list" role="tablist" aria-label="Views">
  <button type="button" id="t1" class="tab-button" role="tab" aria-selected="true">List</button>
  <button type="button" id="t2" class="tab-button" role="tab" aria-selected="false">Map</button>
</div>
<button type="button" id="chip-on" class="chip-button" aria-pressed="true">Required</button>
<button type="button" id="chip-off" class="chip-button" aria-pressed="false">Permitted</button>
<table><thead><tr><th id="th1" aria-sort="ascending"><button type="button" id="sort1" class="sort-button">Title</button></th></tr></thead></table>
<div class="dialog-actions" id="dlg"><button type="button" class="action-button">Cancel</button><button type="submit" class="primary" id="save">Save</button></div>
<input id="hidden-file" class="visually-hidden" type="file" aria-label="Choose a file">
<div id="slot"></div>
</main></body></html>"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def serve(route):
    path = route.request.url[len(ORIGIN):].split("?")[0]
    if path == "/app/":
        route.fulfill(status=200, content_type="text/html", body=HTML)
        return
    if path == "/app/marin.yml":
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


def style(page, selector, prop):
    return page.evaluate("([s, p]) => getComputedStyle(document.querySelector(s))[p]", [selector, prop])


def run(page):
    page.goto(PAGE)
    page.wait_for_selector("#dl svg", state="attached")
    require(page.locator("#dl > svg[data-shell-icon=start]").count() == 1 and page.locator("#del > svg").count() == 1, "data-icon draws the icon")
    require(page.locator("#dl svg").get_attribute("aria-hidden") == "true", "The icon is hidden from assistive technology")
    require(page.locator("#more > svg[data-shell-icon=end]").count() == 1 and page.evaluate("document.getElementById('more').lastElementChild.tagName") == "svg",
            "data-icon-end draws the icon after the text")
    require(page.locator("#typo svg").count() == 0, "An unknown icon name draws nothing")
    page.evaluate("document.getElementById('slot').innerHTML = '<button type=\"button\" id=\"late\" class=\"action-button\" data-icon=\"copy\" aria-label=\"Copy\"></button>'")
    page.wait_for_selector("#late svg", state="attached")
    require(page.locator("#late svg").count() == 1, "A button added later gets its icon")
    require(page.evaluate("window.MarinAppShell.icon('copy').startsWith('<svg')"), "MarinAppShell.icon returns markup")
    box = page.locator("#dl svg").bounding_box()
    require(abs(box["width"] - 16) < 1 and abs(box["height"] - 16) < 1, f"Icons are 16 px: {box}")
    require(page.locator("#dl").bounding_box()["height"] >= 35, "Action buttons are at least 36 px tall")

    page.hover("#del")
    page.wait_for_timeout(400)  # Pico eases colors in over 0.2 s
    require(style(page, "#del", "color") != style(page, "#dl", "color") and style(page, "#del", "borderTopColor") != "rgba(0, 0, 0, 0)",
            "The danger button turns red on hover")
    require(page.locator(".tab-button[aria-selected=true]").evaluate("e => getComputedStyle(e).fontWeight") in ("700", "bold"), "The chosen tab is bold")
    require(style(page, "#t1", "backgroundColor") != style(page, "#t2", "backgroundColor"), "The chosen tab is solid")
    require(style(page, "#chip-on", "fontWeight") in ("700", "bold") and style(page, "#chip-off", "fontWeight") not in ("700", "bold"), "A pressed chip is bold")
    require(style(page, "#chip-on", "borderTopLeftRadius") != "0px", "Chips are rounded")
    after = page.evaluate("getComputedStyle(document.getElementById('sort1'), '::after').content")
    require("▲" in after, f"A sort header shows its arrow: {after}")
    require(style(page, "#dlg", "justifyContent") == "flex-end", "Dialog buttons sit at the end")
    require(page.locator("#dlg .action-button").bounding_box()["height"] >= 43, "Dialog buttons are 44 px targets")
    hidden = page.locator("#hidden-file").bounding_box()
    require(hidden["width"] <= 2 and hidden["height"] <= 2, f"A visually hidden input stays 1 px: {hidden}")
    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "A hidden input does not make the page wider than the window")
    page.keyboard.press("Tab")


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
        browser.close()
    require(not problems, f"Console or page errors: {problems}")
    print("Shell button patterns browser test (light and dark): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
