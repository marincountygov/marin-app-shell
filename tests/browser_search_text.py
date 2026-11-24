#!/usr/bin/env python3
"""Browser test of the search-result helpers in the built shell: marinSearchWords, marinSearchSnippet, marinSearchRemember and the
highlighter that runs on the page a result opens.

Serves a fixture page from a fake https origin through Playwright routes and loads dist/marinos.js. Needs Playwright for Python and
Chromium.  Run: python3 tests/browser_search_text.py
"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/page.html"
TEXT = ("The County has a long list of rules. " * 4 + "An employee who is on probation may be released during the probationary period. "
        + "The rest of the text goes on for a while so the line is cut on both sides of the match. " * 3)
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Search text fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture"><main id="main" class="container app-main"><div id="start" data-tab-section="start">
<nav>Probation menu</nav>
<article><h1>Probation</h1><p id="body">{TEXT}</p><p id="two">Nothing here. Employees may appeal.</p></article>
</div></main></body></html>"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def serve(route):
    path = route.request.url[len(ORIGIN):].split("?")[0]
    if path == "/app/page.html":
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


def marks(page):
    return page.evaluate("[...document.querySelectorAll('mark.search-hit')].map((m) => m.textContent)")


def run(page):
    page.goto(PAGE)
    page.wait_for_function("typeof window.marinSearchSnippet === 'function' && typeof window.marinSearchRemember === 'function'")

    words = page.evaluate("marinSearchWords('Probationary  EMPLOYÉE!')")
    require(words == ["probationary", "employee"], f"The words are lower case, without accents or punctuation: {words}")

    # The snippet: about a line around the first word that starts with a typed word, those words marked, ellipses on the cut sides.
    html = page.evaluate("(t) => marinSearchSnippet(t, ['probation', 'employee']).outerHTML", TEXT)
    require(html.startswith('<span class="search-snippet">…') and html.endswith("…</span>"), f"Cut on both sides: {html!r}")
    require('<mark class="search-hit">employee</mark>' in html and '<mark class="search-hit">probation</mark>' in html
            and '<mark class="search-hit">probationary</mark>' in html, f"Every word that starts with a typed word is marked, whole: {html!r}")
    plain = page.evaluate("(t) => marinSearchSnippet(t, ['probation']).textContent.length", TEXT)
    require(plain <= 200, f"About a line, not the whole text: {plain}")
    require(page.evaluate("(t) => marinSearchSnippet(t, ['zebra'])", TEXT) is None, "No word starts with a typed word: null")
    short = page.evaluate("marinSearchSnippet('Probation period.', ['probation']).outerHTML")
    require(short == '<span class="search-snippet"><mark class="search-hit">Probation</mark> period.</span>', f"Short text: no ellipsis: {short!r}")

    # Remembered for this page: the words are marked on arrival, in the page's content and not in the navigation.
    page.evaluate("marinSearchRemember('/app/page.html#two', ['probation', 'employee'])")
    page.reload()
    page.wait_for_function("document.querySelectorAll('mark.search-hit').length > 0")
    got = marks(page)
    require(sorted(set(m.lower() for m in got)) == ["employee", "employees", "probation", "probationary"], f"The marked words: {got}")
    require(page.evaluate("document.querySelector('nav mark') === null"), "The navigation is not marked")
    require(page.evaluate("document.getElementById('body').textContent") == TEXT, "Marking leaves the text as it was")
    page.keyboard.press("Escape")
    require(marks(page) == [] and page.evaluate("document.getElementById('body').textContent") == TEXT, "Escape clears the marks and leaves the text")
    page.reload()
    page.wait_for_timeout(200)
    require(marks(page) == [], "The words are read once: a reload shows none")

    # Not for this page, or too old: nothing is marked.
    page.evaluate("marinSearchRemember('/app/other.html', ['probation'])")
    page.reload()
    page.wait_for_timeout(200)
    require(marks(page) == [], "Words kept for another page are not used here")
    page.evaluate("sessionStorage.setItem('marin-search-hit', JSON.stringify({path: '/app/page.html', terms: ['probation'], at: Date.now() - 300000}))")
    page.reload()
    page.wait_for_timeout(200)
    require(marks(page) == [], "Words more than two minutes old are not used")


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1100, "height": 800})
        page = context.new_page()
        page.on("pageerror", lambda e: problems.append(str(e)))
        context.route(f"{ORIGIN}/**", serve)
        try:
            run(page)
        finally:
            context.close()
            browser.close()
    require(not problems, f"Page errors: {problems}")
    print("Search-result helpers (words, snippet, remember, highlight): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
