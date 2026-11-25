#!/usr/bin/env python3
"""Browser test of the steps layout in the built shell (dist/marinos.js and dist/marinos.css): one step at a time, state
words, progress line, "On this page", Previous and Next with the shell's arrows, the address and Back, narrow screens,
no JavaScript and print.

The page is served from a fake https origin through Playwright routes. Needs Playwright for Python and Chromium.
Run: python3 tests/browser_steps.py
"""
from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/"
HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Steps fixture | County of Marin</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture">
<main id="main" class="container app-main">
    <h1 class="visually-hidden">Steps layout fixture</h1>
    <section id="start">
    <div class="search-layout">
      <div class="search-side">
        <button type="button" class="filter-toggle" data-filter-toggle="steps" data-filter-label="Steps" aria-controls="steps-panel" hidden></button>
        <aside id="steps-panel" class="search-sidebar" data-filter-column-exempt="steps" aria-labelledby="steps-title">
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
            </section>
            <section id="answer" class="step" aria-labelledby="answer-heading">
              <h2 id="answer-heading">Answer</h2>
              <div class="step-box"><h3>Your name</h3><label for="name">Name</label><input id="name" type="text"></div>
              <div class="step-box"><h3>Your notes</h3><p>Write them.</p></div>
            </section>
            <section id="send" class="step" aria-labelledby="send-heading">
              <h2 id="send-heading">Send</h2>
              <div class="step-box"><h3>Send it</h3><p>Done.</p></div>
            </section>
          </div>
        </div>
      </div>
    </div>
    </section>
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


def pager_checks(page):
    """Previous and Next on step 2: names, group, size, spacing, keyboard, focus ring, forced colors."""
    require(page.locator(".step:not([hidden]) .steps-pager").count() == 1, "Each step has one pager")
    group = page.locator(".step:not([hidden]) .steps-pager")
    require(group.evaluate("e => e.tagName") == "NAV" and group.get_attribute("aria-label") == "Previous and next step", "The pager is a named nav")
    previous, following = group.locator("[data-prev-step]"), group.locator("[data-next-step]")
    require(previous.get_attribute("aria-label") == "Previous: gather" and previous.get_attribute("title") == "Previous: gather", "Previous is named by aria-label and title")
    require(previous.inner_text().strip() == "" and previous.locator("svg[aria-hidden='true']").count() == 1, "Previous is icon-only with a hidden arrow")
    require(following.inner_text().strip() == "Next: send", "Next keeps its words and names the next step in lowercase")
    require(following.get_attribute("aria-label") is None, "Next is named by its visible words, so the name matches the label (WCAG 2.5.3)")
    require(following.locator("svg[aria-hidden='true']").count() == 1 and following.evaluate("e => e.lastElementChild.tagName.toLowerCase() === 'svg'"), "Next ends with a hidden arrow")
    require(following.evaluate("e => e.classList.contains('primary')") and not previous.evaluate("e => e.classList.contains('primary')"), "Next is the one solid button")
    boxes = [previous.bounding_box(), following.bounding_box()]
    require(all(b["width"] >= 44 and b["height"] >= 44 for b in boxes), f"Both targets are at least 44 px: {boxes}")
    require(boxes[0]["width"] < 60 and boxes[1]["width"] < 400, f"The buttons keep their own size, not stretched or joined: {boxes}")
    require(boxes[1]["x"] - (boxes[0]["x"] + boxes[0]["width"]) >= 8, "The buttons have a gap between them")
    require(group.locator("[disabled], [aria-disabled]").count() == 0, "Nothing is disabled")
    # Keyboard: Previous then Next in the tab order, a visible focus ring, Space and Enter work.
    previous.focus()
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    require(page.evaluate("document.activeElement.dataset.prevStep") == "gather", "Previous takes focus")
    ring = previous.evaluate("e => { const c = getComputedStyle(e); return [c.outlineStyle, parseFloat(c.outlineWidth)]; }")
    require(ring[0] != "none" and ring[1] >= 2, f"Previous shows a focus ring: {ring}")
    page.keyboard.press("Tab")
    require(page.evaluate("document.activeElement.dataset.nextStep") == "send", "Next follows Previous in the tab order")
    ring = following.evaluate("e => { const c = getComputedStyle(e); return [c.outlineStyle, parseFloat(c.outlineWidth)]; }")
    require(ring[0] != "none" and ring[1] >= 2, f"Next shows a focus ring: {ring}")
    # Windows forced colors: both keep a border and their arrows.
    page.emulate_media(forced_colors="active")
    require(all(group.locator(f"[data-{n}-step]").evaluate("e => parseFloat(getComputedStyle(e).borderTopWidth) >= 1") for n in ("prev", "next")), "Both buttons keep a border in forced colors")
    page.keyboard.press("Shift+Tab")
    require(page.evaluate("document.activeElement.dataset.prevStep") == "gather", "Shift+Tab goes back to Previous")
    require(previous.evaluate("e => getComputedStyle(e).outlineStyle") != "none", "The focus ring shows in forced colors")
    page.emulate_media(forced_colors="none")
    # The ends of the flow: no Previous on the first step, no Next on the last, and neither is disabled.
    require(page.locator("#gather .steps-pager [data-prev-step]").count() == 0 and page.locator("#gather .steps-pager [data-next-step]").count() == 1, "The first step has Next only")
    require(page.locator("#send .steps-pager [data-next-step]").count() == 0 and page.locator("#send .steps-pager [data-prev-step]").count() == 1, "The last step has Previous only")
    # Enter on Next moves on, Space on Previous goes back, and focus follows to the step heading.
    following.focus()
    page.keyboard.press("Enter")
    require(visible_steps(page) == ["send"] and page.evaluate("document.activeElement.id") == "send-heading", "Enter on Next opens the next step and moves focus to its heading")
    page.focus("#send [data-prev-step]")
    page.keyboard.press("Space")
    require(visible_steps(page) == ["answer"] and page.evaluate("document.activeElement.id") == "answer-heading", "Space on Previous goes back and moves focus to the heading")


AXE = os.environ.get("AXE_CORE")
SPACING = "* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; } p { margin-bottom: 2em !important; }"


def fits(page, what):
    require(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"No horizontal scroll {what}")
    require(page.evaluate("[...document.querySelectorAll('.step:not([hidden]) .steps-pager button')].every(b => b.scrollWidth <= b.clientWidth + 1 && b.getBoundingClientRect().right <= window.innerWidth)"), f"The step buttons are not clipped {what}")


def reflow_checks(page, reload):
    """Text spacing (WCAG 1.4.12), 200% and 400% zoom (1.4.4, 1.4.10) and axe-core, on the second step."""
    original = page.viewport_size
    reload("#answer")
    page.add_style_tag(content=SPACING)
    fits(page, "with the text spacing overrides")
    require(page.evaluate("(() => { const side = document.querySelector('.search-sidebar').getBoundingClientRect(); return [...document.querySelectorAll('nav.steps a')].every(a => a.getBoundingClientRect().right <= side.right + 1 && a.scrollWidth <= a.clientWidth + 1); })()"), "Step names are not clipped with the text spacing overrides")
    for width, height, name in ((640, 400, "200% zoom"), (320, 256, "400% zoom")):
        page.set_viewport_size({"width": width, "height": height})
        reload("#answer")
        fits(page, f"at {name}")
        page.locator(".step:not([hidden]) [data-next-step]").scroll_into_view_if_needed()
        require(page.locator(".step:not([hidden]) [data-next-step]").is_visible(), f"Next can be reached at {name}")
    page.set_viewport_size(original)
    reload("#answer")
    if not AXE:
        print("SKIP: axe-core scan (set AXE_CORE to axe.min.js).")
        return
    page.add_script_tag(path=AXE)
    result = page.evaluate("axe.run(document.querySelector('main'), { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] })")
    found = [(v["id"], [n["target"] for n in v["nodes"]]) for v in result["violations"]]
    require(not found, f"axe-core: {found}")


def run(page):
    load(page)
    require(states(page) == ["current", "upcoming", "upcoming"], f"Initial states: {states(page)}")
    require(words(page) == ["Current", "Up next", "Up next"], f"State words: {words(page)}")
    require(page.locator("nav.steps a[aria-current='step']").count() == 1, "One link is the current step")
    require(visible_steps(page) == ["gather"], "One step shows at a time")
    require(page.inner_text(".steps-progress p") == "Step 1 of 3: Gather", "The progress line names the step")
    # One announcement per step change: the status role is gone and the heading is described by the position.
    require(page.locator(".steps-progress [role='status'], .steps-progress [aria-live]").count() == 0, "The progress line is not a live region")
    require(page.evaluate("document.querySelectorAll('.step > h2[aria-describedby]').length") == 1, "Only the current step's heading is described")
    require(page.evaluate("(() => { const h = document.querySelector('.step:not([hidden]) > h2'); return document.getElementById(h.getAttribute('aria-describedby')).textContent; })()") == "Step 1 of 3", "The heading is described by its position")
    require(page.title() == "Steps fixture: Gather (step 1 of 3)", f"The page title names the step: {page.title()}")
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
    require(page.title() == "Steps fixture: Answer (step 2 of 3)", f"The page title follows the step: {page.title()}")
    require(page.evaluate("document.getElementById(document.getElementById('answer-heading').getAttribute('aria-describedby')).textContent") == "Step 2 of 3", "The new heading is described by its position")
    page.evaluate("document.getElementById('start').hidden = true")
    page.wait_for_function("document.title === 'Steps fixture | County of Marin'", timeout=3000)
    page.evaluate("document.getElementById('start').hidden = false")
    page.wait_for_function("document.title === 'Steps fixture: Answer (step 2 of 3)'", timeout=3000)

    pager_checks(page)

    page.click("nav.steps a[href='#send']")
    require(states(page) == ["complete", "complete", "current"], f"After skipping ahead: {states(page)}")
    page.click("[data-prev-step=answer]")
    require(states(page) == ["complete", "current", "upcoming"], f"After Previous: {states(page)}")
    page.go_back()
    require(states(page) == ["complete", "complete", "current"], f"After Back: {states(page)}")
    page.wait_for_function("document.activeElement.id === 'send-heading'", timeout=3000)

    load(page, "#answer-your-notes")
    require(visible_steps(page) == ["answer"], "A box hash opens its step")

    page.set_viewport_size({"width": 320, "height": 700})
    load(page)
    require(page.is_visible(".steps-progress"), "The progress line shows on a narrow screen")
    require(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "No horizontal scroll at 320 px")
    page.click(".filter-toggle")
    require(page.is_visible("nav.steps"), "The toggle opens the steps")
    page.set_viewport_size({"width": 1100, "height": 800})

    reflow_checks(page, lambda hash_="": load(page, hash_))

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
