#!/usr/bin/env python3
"""Browser test of the steps layout in the built shell (dist/marinos.js and dist/marinos.css): one step at a time, state
words, progress line, "On this page", Previous and Next with the shell's arrows, the address and Back, narrow screens,
no JavaScript and print.

The page is served from a fake https origin through Playwright routes. Needs Playwright for Python and Chromium.
Run: python3 tests/browser_steps.py
"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/"
HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Steps fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture">
<main id="main" class="container app-main">
    <h1 class="visually-hidden">Steps layout fixture</h1>
    <div class="search-layout">
      <div class="search-side">
        <button type="button" class="filter-toggle" data-filter-toggle="steps" data-filter-label="Steps" aria-controls="steps-panel" hidden></button>
        <aside id="steps-panel" class="search-sidebar" aria-labelledby="steps-title">
          <div class="search-panel-header">
            <h2 class="search-panel-title" id="steps-title">Steps</h2>
          </div>
          <nav class="steps" data-steps aria-labelledby="steps-title">
            <ol>
              <li><a href="#gather">1. Gather</a></li>
              <li><a href="#answer">2. Answer</a></li>
              <li><a href="#send">3. Send</a></li>
            </ol>
          </nav>
        </aside>
      </div>
      <div class="search-results">
        <div class="steps-progress" hidden></div>
        <div class="steps-body">
          <div class="steps-toc-holder" data-steps-toc></div>
          <div class="steps-main">
            <section id="gather" class="step" aria-labelledby="gather-heading">
              <h2 id="gather-heading">Gather</h2>
              <p>Collect what you need.</p>
              <div class="step-box"><h3>What you do</h3><p>List the documents.</p></div>
              <div class="step-box"><h3>What you get back</h3><p>A checklist.</p></div>
              <p class="steps-pager"><button type="button" class="primary" data-next-step="answer" data-icon-end="arrow-right" hidden>Next: answer</button></p>
            </section>
            <section id="answer" class="step" aria-labelledby="answer-heading">
              <h2 id="answer-heading">Answer</h2>
              <div class="step-box"><h3>Your name</h3><label for="name">Name</label><input id="name" type="text"></div>
              <div class="step-box"><h3>Your notes</h3><p>Write them.</p></div>
              <p class="steps-pager"><button type="button" class="action-button" data-prev-step="gather" data-icon="arrow-left" aria-label="Previous: gather" title="Previous: gather" hidden></button><button type="button" class="primary" data-next-step="send" data-icon-end="arrow-right" hidden>Next: send</button></p>
            </section>
            <section id="send" class="step" aria-labelledby="send-heading">
              <h2 id="send-heading">Send</h2>
              <div class="step-box"><h3>Send it</h3><p>Done.</p></div>
              <p class="steps-pager"><button type="button" class="action-button" data-prev-step="answer" data-icon="arrow-left" aria-label="Previous: answer" title="Previous: answer" hidden></button></p>
            </section>
          </div>
        </div>
      </div>
    </div>
  </main>
</body></html>"""


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


def states(page):
    return page.eval_on_selector_all("nav.steps a", "els => els.map(e => e.dataset.stepState)")


def words(page):
    return page.eval_on_selector_all("nav.steps .step-state", "els => els.map(e => e.textContent)")


def visible_steps(page):
    return page.eval_on_selector_all(".step", "els => els.filter(e => !e.hidden).map(e => e.id)")


def load(page, hash_=""):
    page.goto(PAGE + hash_)
    page.wait_for_selector("nav.steps[data-steps-ready]", state="attached")


def run(page):
    load(page)
    require(states(page) == ["current", "upcoming", "upcoming"], f"Initial states: {states(page)}")
    require(words(page) == ["Current", "Up next", "Up next"], f"State words: {words(page)}")
    require(page.locator("nav.steps a[aria-current='step']").count() == 1, "One link is the current step")
    require(visible_steps(page) == ["gather"], "One step shows at a time")
    require(page.inner_text(".steps-progress p") == "Step 1 of 3: Gather", "The progress line names the step")
    require(page.is_visible(".filter-toggle") and page.get_attribute(".filter-toggle", "aria-label") == "Steps", "The Steps toggle shows once JavaScript runs")
    require(page.evaluate("document.querySelectorAll('nav.steps svg, nav.steps img, nav.steps canvas').length") == 0, "No icons or images in the list")
    require(page.evaluate("(() => { const side = document.querySelector('.search-sidebar').getBoundingClientRect(); return [...document.querySelectorAll('nav.steps a')].every(a => a.getBoundingClientRect().left >= side.left && a.getBoundingClientRect().right <= side.right); })()"), "Step links stay inside the column")
    require(page.evaluate("getComputedStyle(document.querySelector('nav.steps a[aria-current]')).borderLeftWidth") == "4px", "The current step has its bar")
    require(page.eval_on_selector_all(".steps-toc a", "els => els.map(e => e.textContent)") == ["What you do (1. Gather)", "What you get back (1. Gather)"], "On this page lists the step's parts")

    # The shell draws the arrow on Next.
    require(page.locator("[data-next-step=answer] svg").count() == 1, "Next ends with the shell's arrow")
    page.click("[data-next-step=answer]")
    require(states(page) == ["complete", "current", "upcoming"], f"After Next: {states(page)}")
    require(page.locator("[data-prev-step=gather] svg").count() == 1, "Previous has the arrow icon")
    require(page.get_attribute("[data-prev-step=gather]", "aria-label") == "Previous: gather", "Previous is named")
    require(page.evaluate("document.activeElement.id") == "answer-heading", "Focus moves to the step heading")
    require(page.url.endswith("#answer"), "The address names the step")

    page.click("nav.steps a[href='#send']")
    require(states(page) == ["complete", "complete", "current"], f"After skipping ahead: {states(page)}")
    page.click("[data-prev-step=answer]")
    require(states(page) == ["complete", "current", "upcoming"], f"After Previous: {states(page)}")
    page.go_back()
    require(states(page) == ["complete", "complete", "current"], f"After Back: {states(page)}")

    load(page, "#answer-your-notes")
    require(visible_steps(page) == ["answer"], "A box hash opens its step")

    page.set_viewport_size({"width": 320, "height": 700})
    load(page)
    require(page.is_visible(".steps-progress"), "The progress line shows on a narrow screen")
    require(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "No horizontal scroll at 320 px")
    page.click(".filter-toggle")
    require(page.is_visible("nav.steps"), "The toggle opens the steps")
    page.set_viewport_size({"width": 1100, "height": 800})

    load(page)
    page.emulate_media(media="print")
    require(page.evaluate("[...document.querySelectorAll('.step')].every(e => getComputedStyle(e).display !== 'none')"), "Print shows every step")
    require(not page.is_visible("nav.steps"), "Print hides the step list")
    page.emulate_media(media="screen")


def run_without_script(browser):
    context = browser.new_context(java_script_enabled=False)
    context.route(f"{ORIGIN}/**", serve)
    page = context.new_page()
    page.goto(PAGE)
    require(page.locator(".step:visible").count() == 3, "Without JavaScript every step shows")
    require(not page.is_visible(".filter-toggle"), "Without JavaScript the toggle stays hidden")
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
        run_without_script(browser)
        browser.close()
    require(not problems, f"Console or page errors: {problems}")
    print("Shell steps layout browser test (light and dark): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
