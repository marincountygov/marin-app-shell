#!/usr/bin/env python3
"""Browser test of the filter column the built shell draws from filters.json (dist/marinos.js and dist/marinos.css),
served over HTTP: the page and its JSON files come from tests/fixtures, the shell from dist/.

Needs Playwright for Python and Chromium:  python3 -m pip install playwright && python3 -m playwright install chromium
For the axe-core accessibility scan, point AXE_CORE at axe.min.js (npm pack axe-core, then package/axe.min.js);
without it the scan is skipped and says so.
Run:  python3 tests/browser_filter_column.py
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "tests/fixtures/filter-column.html"
ASSETS = {"/vendor/marinos/": ROOT / "dist", "/vendor/fonts/": ROOT / "fonts"}
AXE = os.environ.get("AXE_CORE")
EXPECTING_ERRORS = {"on": False}  # a test that fails a request on purpose expects the console to say so


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def translate_path(self, path):
        clean = path.split("?")[0]
        if clean.endswith("/marin.yml"):
            return str(ROOT / "marin.yml")  # the shell reads the page's app manifest for its status badge
        for prefix, folder in ASSETS.items():
            if clean.startswith(prefix):
                return str(folder / clean[len(prefix):])
        return super().translate_path(path)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(page, base, query=""):
    page.goto(base + FIXTURE + query)
    page.wait_for_selector("#items-filter-panel .search-input-field", state="attached")


def toggle_name(page):
    return page.get_attribute("#items-filter-panel-toggle", "aria-label")


def drawn(page, base):
    load(page, base)
    require(page.inner_text("#items-filter-panel-title") == "Filter", "The title is the word Filter")
    require(page.inner_text("#items-filter-panel .search-input-field label") == "Search", "The search label is Search")
    require(page.evaluate("document.querySelectorAll('#items-filter-panel [placeholder]').length") == 0, "No control has a placeholder")
    require(page.evaluate("document.querySelectorAll('#items-filter-panel [disabled]').length") == 0, "Nothing is disabled")
    legends = page.eval_on_selector_all("#items-filter-panel legend", "els => els.map(e => e.textContent)")
    require(legends == ["Times", "Measures", "Years", "Departments", "Statuses", "Units", "Tags", "Dates", "Monitors", "Owners"], f"Every group shows its name: {legends}")
    require(page.evaluate("[...document.querySelectorAll('#items-filter-panel legend')].every(e => e.getBoundingClientRect().width > 0 && !e.closest('.visually-hidden'))"), "No legend is hidden")
    require(page.inner_text("#department-summary") == "All departments", "A group with nothing chosen reads All and its plural noun")
    require(page.locator("#department-options input").count() == 40, "Options come from the data file")
    first = page.text_content("#department-options li >> nth=0")
    require(first.startswith("Department 01") and "(2)" in first, f"Options are sorted and counted from the data: {first!r}")
    require(page.locator("#year-options input[value='2026']").is_checked(), "A radio group starts on its latest value")
    tags = page.eval_on_selector_all("#items-filter-panel-tag option", "els => els.map(e => e.textContent)")
    require(tags == ["All tags", "a", "b", "c"], f"A field holding a list gives one choice per item: {tags}")
    require(page.get_attribute("#items-filter-panel-tag", "aria-labelledby") == "items-filter-panel-tag-legend", "The select is named by its group name")
    require(toggle_name(page) == "Filter", f"Nothing active: {toggle_name(page)}")


def group_types(page, base):
    load(page, base)
    # A drop-down with no "All" choice starts on its default; a hidden choice is not listed but can be set by the app.
    require(page.input_value("#items-filter-panel-time") == "60d", "A select starts on its default")
    listed = page.eval_on_selector_all("#items-filter-panel-time option:not([hidden])", "els => els.map(e => e.value)")
    require(listed == ["24h", "60d"], f"A hidden choice is not listed: {listed}")
    page.evaluate("document.querySelector('[data-filter-column]').setValue('time', 'report')")
    require(page.input_value("#items-filter-panel-time") == "report", "The app can set a hidden choice")
    require("time=" not in page.url and toggle_name(page) == "Filter", f"A hidden choice is the app's display, not a filter: it stays out of the address and the active count ({page.url}, {toggle_name(page)})")
    page.evaluate("document.querySelector('[data-filter-column]').setValue('time', '24h')")
    require("time=24h" in page.url and toggle_name(page) == "Filter, 1 active", f"A real choice set by the app reaches the address and the count: {page.url}")
    page.evaluate("document.querySelector('[data-filter-column]').setValue('time', '60d')")
    # An always-showing checkbox group: no summary, and its default is checked.
    require(page.locator("#show-facet details").count() == 0 and page.locator("#show-options input:checked").count() == 1, "An open list has no summary and starts on its default")
    page.uncheck("#show-options li:first-child input")
    require("show=" in page.url and page.evaluate("document.querySelector('[data-filter-column]').filterState.groups.show.length") == 0, "Unchecking the default is remembered, not reset by the address")
    page.reload()
    page.wait_for_selector("#show-options", state="attached")
    require(page.locator("#show-options input:checked").count() == 0, "An emptied open list stays empty after a reload")
    # Nested groups: Facet, then group, then the choices, with counts of what is chosen.
    names = page.eval_on_selector_all("#monitor-facet > div > details > summary", "els => els.map(e => e.textContent)")
    require(names == ["Organization", "Person", "Place"] or names == ["Place", "Organization", "Person"], f"One group for each value of the first field: {names}")
    page.click("#monitor-facet > div > details:first-child > summary")
    page.click("#monitor-facet > div > details:first-child > div > details:first-child > summary")
    page.check("#monitor-facet > div > details:first-child > div > details:first-child li:first-child input")
    text = page.text_content("#monitor-facet > div > details:first-child > summary")
    require("(1 selected)" in text, f"A group says how many choices are inside it: {text!r}")
    require("monitor=" in page.url, "A nested choice reaches the address")
    page.click("#items-filter-panel .action-button")
    require(page.locator("#monitor-facet input:checked").count() == 0 and page.input_value("#items-filter-panel-time") == "60d" and page.locator("#show-options input:checked").count() == 1, "Reset restores every default")


def hierarchy(page, base):
    load(page, base)
    page.click("#unit-summary")
    top = page.eval_on_selector_all("#unit-options > li > label > span:nth-of-type(1)", "els => els.map(e => e.textContent)")
    require("Department 02" not in top and "Department 03" not in top and "Department 04" not in top, f"A choice with a parent is not listed at the top: {top[:4]}")
    under = page.eval_on_selector_all("#unit-options > li:first-child > ul > li > label > span:nth-of-type(1)", "els => els.map(e => e.textContent)")
    require(under == ["Department 02", "Department 03"], f"Children are listed under their parent: {under}")
    grand = page.eval_on_selector_all("#unit-options > li:first-child > ul > li:first-child > ul > li > label > span:nth-of-type(1)", "els => els.map(e => e.textContent)")
    require(grand == ["Department 04"], f"A child can have children: {grand}")
    # Parent and child are separate boxes; tab order follows the page (parent, then its children).
    page.check("#unit-options > li:first-child > ul > li:first-child > label input")
    require(page.evaluate("document.querySelector('[data-filter-column]').filterState.groups.unit") == ["Department 02"], "Choosing a child does not choose its parent")
    page.evaluate("document.querySelector('[data-filter-column]').setCounts('unit', { 'Department 01': 5, 'Department 02': 7 })")
    counts = page.eval_on_selector_all("#unit-options > li:first-child > label .search-facet-count, #unit-options > li:first-child > ul > li:first-child > label .search-facet-count", "els => els.map(e => e.textContent)")
    require(counts == ["(5)", "(7)"], f"Counts go to the right row, parent and child: {counts}")
    # A loop of parents has no top: its choices are still listed, at the top, not lost.
    def loop(route):
        data = json.loads(Path(ROOT / "tests/fixtures/filters/column-data.json").read_text())
        for record in data["records"]:
            if record["department"] == "Department 01":
                record["parent_department"] = "Department 02"
            if record["department"] == "Department 02":
                record["parent_department"] = "Department 01"
        route.fulfill(json=data)
    page.route("**/filters/column-data.json", loop)
    load(page, base)
    page.click("#unit-summary")
    require(page.locator("#unit-options input[value='Department 01']").count() == 1 and page.locator("#unit-options input[value='Department 02']").count() == 1, "Both choices of a parent loop are still listed")
    page.unroute("**/filters/column-data.json")


def app_options(page, base):
    # A group with {"app": true} starts empty; the app supplies its choices when it has them. A choice held in the
    # address before they arrive stays chosen, and one that is not among them is dropped.
    load(page, base, "?owner=b&owner=gone")
    require(page.locator("#owner-options input").count() == 0 and page.inner_text("#owner-summary") == "2 selected", "Before the app supplies choices, the group is empty but keeps the address's choices")
    page.evaluate("document.querySelector('[data-filter-column]').setOptions('owner', [{ value: 'a', label: 'Alpha', count: 3 }, { value: 'b', label: 'Beta', count: 1 }, { value: 'c', label: 'Gamma' }])")
    labels = page.eval_on_selector_all("#owner-options li", "els => els.map(e => e.textContent.trim())")
    require(labels == ["Alpha (3)", "Beta (1)", "Gamma"], f"The supplied choices are drawn: {labels}")
    require(page.locator("#owner-options input[value='b']").is_checked() and not page.locator("#owner-options input[value='a']").is_checked(), "The remembered choice is checked")
    require(page.inner_text("#owner-summary") == "1 selected" and "owner=b" in page.url and "gone" not in page.url, "A choice that is not among them is dropped, from the group and the address")
    page.check("#owner-options input[value='c']")
    page.evaluate("document.querySelector('[data-filter-column]').setOptions('owner', [{ value: 'a', label: 'Alpha' }, { value: 'b', label: 'Beta' }, { value: 'c', label: 'Gamma' }])")
    require(page.locator("#owner-options input:checked").count() == 2, "Supplying choices again keeps what is chosen")
    require(page.evaluate("document.querySelector('[data-filter-column]').filterState.groups.owner").__len__() == 2, "The state matches the screen")


def small_columns(page, base):
    # No search in the file: no search box. address false: nothing reaches the address. Variable depth: a facet with one
    # group lists its choices directly; one with two groups nests. Group counts, and a disabled group.
    page.goto(base + "tests/fixtures/filter-column-small.html?admin=a")
    page.wait_for_selector("#admin-filter-panel", state="attached")
    require(page.locator("#admin-filter-panel .search-input-field").count() == 0 and page.locator("#admin-filter-panel input[type=search]").count() == 0, "No search box when the file has none")
    page.evaluate("document.querySelector('[data-filter-name=admin]').setOptions('admin', [{ value: 'a', label: 'Alpha', path: ['News'] }, { value: 'b', label: 'Beta', path: ['News'] }, { value: 'c', label: 'Gamma', path: ['Video'] }])")
    require(page.locator("#admin-facet input").count() == 3 and page.locator("#admin-facet input:checked").count() == 0, "address:false ignores the address on load")
    page.click("#admin-facet summary >> nth=0")
    page.check("#admin-facet input[value='a']")
    require(page.url.endswith("?admin=a"), f"address:false leaves the address as it was: {page.url}")
    page.evaluate("document.querySelector('[data-filter-name=admin]').setGroupCounts('admin', { News: 5, Video: 2 })")
    texts = page.eval_on_selector_all("#admin-facet > div > details > summary", "els => els.map(e => e.textContent)")
    require(texts == ["News (5) (1 selected)", "Video (2)"], f"Group counts and selected counts show: {texts}")

    # Disabled group: dimmed, out of the tab order, keeps what it holds, survives new options.
    page.evaluate("document.querySelector('[data-filter-name=admin]').setDisabled('admin', true)")
    require(page.evaluate("document.getElementById('admin-facet').disabled") and page.evaluate("document.querySelector('#admin-facet input').matches(':disabled')"), "A disabled group disables its fields")
    page.evaluate("document.querySelector('[data-filter-name=admin]').setOptions('admin', [{ value: 'a', label: 'Alpha', path: ['News'] }])")
    require(page.evaluate("document.getElementById('admin-facet').disabled") and page.locator("#admin-facet input:checked").count() == 1, "Disabled and chosen survive new options")
    page.evaluate("document.querySelector('[data-filter-name=admin]').setDisabled('admin', false)")
    require(not page.evaluate("document.getElementById('admin-facet').disabled"), "Enabling puts it back")

    # Separator: a list in one parameter is read and written the same way.
    page.goto(base + "tests/fixtures/filter-column-small.html?monitors=x")
    page.goto(base + "tests/fixtures/filter-column-small.html?monitor=m1,m3")
    page.wait_for_selector("#feed-filter-panel", state="attached")
    page.evaluate("document.querySelector('[data-filter-name=feed]').setOptions('monitor', [{ value: 'm1', label: 'One', path: ['Place', 'North'] }, { value: 'm2', label: 'Two', path: ['Place', 'South'] }, { value: 'm3', label: 'Three', path: ['Person'] }])")
    require(page.evaluate("document.querySelector('[data-filter-name=feed]').filterState.groups.monitor") == ["m1", "m3"], "A comma-joined parameter is read as a list")
    shape = page.evaluate(
        """() => [...document.querySelectorAll('#monitor-facet > div > details')].map(d => [d.querySelector('summary').textContent.split(' (')[0], d.querySelectorAll(':scope > div > details').length, d.querySelectorAll(':scope > div > ul > li').length])"""
    )
    require(shape == [["Place", 2, 0], ["Person", 0, 1]], f"A facet with two groups nests; one with a single group lists its choices directly: {shape}")
    page.evaluate("document.querySelectorAll('#monitor-facet details').forEach((d) => { d.open = true; })")
    page.check("#monitor-facet input[value='m2']")
    require("monitor=m1%2Cm2%2Cm3" in page.url or "monitor=m1,m2,m3" in page.url, f"Choices are written back joined in one parameter: {page.url}")


def behaves(page, base):
    load(page, base)
    page.click("#department-summary")
    page.check("#department-options li:nth-child(2) input")
    require(page.inner_text("#department-summary") == "1 selected", "The summary counts the choice")
    page.wait_for_function("document.getElementById('items-filter-panel-toggle').getAttribute('aria-label') === 'Filter, 1 active'")
    require("department=Department+02" in page.url, f"The choice is in the address: {page.url}")
    require(page.evaluate("window.__changes.at(-1).source") == "department", "A change event names its group")

    # Searching waits for a pause: three quick keystrokes make one event.
    before = page.evaluate("window.__changes.length")
    page.click("#item-search")
    page.keyboard.type("abc", delay=30)
    page.wait_for_function("window.__changes.at(-1).source === 'search'")
    require(page.evaluate("window.__changes.length") - before == 1, "Typing sends one change, after a pause")
    require("q=abc" in page.url, "The search is in the address")

    # A reload restores everything from the address, and opens the group that holds a choice.
    page.reload()
    page.wait_for_selector("#department-options", state="attached")
    require(page.locator("#department-options li:nth-child(2) input").is_checked() and page.input_value("#item-search") == "abc", "Reload restores the choices")
    require(page.evaluate("document.querySelector('#department-summary').parentElement.open"), "A group holding a choice starts open")

    # Zero counts stay reachable.
    page.evaluate("document.querySelector('[data-filter-column]').setCounts('department', { 'Department 01': 0 })")
    require("(0)" in page.text_content("#department-options li:nth-child(1)"), "A count of 0 shows")
    require(page.evaluate("!document.querySelector('#department-options li input').disabled && document.querySelector('#department-options li input').tabIndex >= 0"), "A zero-count option stays focusable")

    # Reset puts everything back, says so once, and keeps focus.
    page.click("#items-filter-panel .action-button")
    require(page.input_value("#item-search") == "" and not page.locator("#department-options input:checked").count(), "Reset clears search and choices")
    require(page.inner_text("#department-summary") == "All departments" and not page.evaluate("document.querySelector('#department-summary').parentElement.open"), "Reset collapses the groups")
    require("?" not in page.url, f"Reset clears the address: {page.url}")
    page.wait_for_function("document.getElementById('results-status').textContent === 'Filters reset. 12 results.'")
    require(page.evaluate("document.activeElement.classList.contains('action-button')"), "Focus stays on the Reset button")
    require(toggle_name(page) == "Filter", "Reset clears the active count")


def results_and_errors(page, base):
    load(page, base)
    # The column says how many results are left, once, in the results area.
    page.click("#department-summary")
    page.check("#department-options li:nth-child(2) input")
    page.wait_for_function("document.getElementById('results-status').textContent === '12 results.'")
    require(page.get_attribute("#results-status", "role") == "status" and page.get_attribute("#results-status", "aria-live") == "polite", "The results area is a polite status")
    page.evaluate("window.__count = 1")
    page.check("#department-options li:nth-child(3) input")
    page.wait_for_function("document.getElementById('results-status').textContent === '1 result.'")
    # Nothing left: it says so and offers Reset, which puts everything back and says both in one message.
    page.evaluate("window.__count = 0")
    page.check("#department-options li:nth-child(4) input")
    page.wait_for_function("document.getElementById('results-status').textContent.startsWith('No results.')")
    require(page.locator("#results-status button", has_text="Reset filters").count() == 1, "Zero results offers Reset filters")
    page.evaluate("window.__count = 12")
    page.click("#results-status button")
    page.wait_for_function("document.getElementById('results-status').textContent === 'Filters reset. 12 results.'")
    require(not page.locator("#department-options input:checked").count(), "Reset from the empty state clears the choices")
    # An app that does not call setResults still hears "Filters reset." on its own.
    page.evaluate("window.__skipResults = true")
    page.click("#items-filter-panel .action-button")
    page.wait_for_function("document.querySelector('[data-filter-column] [role=status]').textContent === 'Filters reset.'")
    page.evaluate("window.__skipResults = false")

    # A date range that ends before it starts is not applied, and says why.
    changes = page.evaluate("window.__changes.length")
    page.fill("#items-filter-panel-date-from", "2026-02-01")
    page.fill("#items-filter-panel-date-to", "2026-01-01")
    page.dispatch_event("#items-filter-panel-date-to", "change")
    require(page.is_visible("#items-filter-panel-date-error") and page.get_attribute("#items-filter-panel-date-error", "role") == "alert", "A backwards range shows an alert")
    require(page.get_attribute("#items-filter-panel-date-to", "aria-invalid") == "true" and page.get_attribute("#items-filter-panel-date-to", "aria-describedby") == "items-filter-panel-date-error", "Both fields are marked invalid and tied to the message")
    require(page.evaluate("window.__changes.length") - changes == 1, "A backwards range sends no change (only the valid From did)")
    page.fill("#items-filter-panel-date-to", "2026-03-01")
    page.dispatch_event("#items-filter-panel-date-to", "change")
    require(not page.is_visible("#items-filter-panel-date-error") and page.get_attribute("#items-filter-panel-date-to", "aria-invalid") is None, "Fixing the range clears the error")
    page.fill("#items-filter-panel-date-to", "2026-01-01")
    page.dispatch_event("#items-filter-panel-date-to", "change")
    page.click("#items-filter-panel .action-button")
    require(not page.is_visible("#items-filter-panel-date-error") and page.input_value("#items-filter-panel-date-to") == "", "Reset clears the error and the fields")

    # A file that will not load shows a message and a Retry, not an empty column.
    EXPECTING_ERRORS["on"] = True
    page.route("**/filters/valid-column.json", lambda route: route.fulfill(status=500, body="no"))
    page.goto(base + FIXTURE)
    page.wait_for_selector("[data-filter-column] [role=alert]")
    require(page.inner_text("[data-filter-column] [role=alert]").startswith("Could not load the filters."), "A load failure says so")
    page.unroute("**/filters/valid-column.json")
    EXPECTING_ERRORS["on"] = False
    page.click("[data-filter-column] [role=alert] button")
    page.wait_for_selector("#item-search", state="attached")
    require(page.locator("[data-filter-column] .app-alert").count() == 0, "Retry draws the column and clears the message")


def focus_not_obscured(page, base):
    load(page, base)
    page.click("#department-summary")
    page.evaluate("document.getElementById('items-filter-panel').scrollTop = 0")
    page.focus("#department-summary")
    probe = """() => { const a = document.activeElement, p = document.getElementById('items-filter-panel'), h = p.querySelector('.search-panel-header');
        if (!p.contains(a)) return null;
        if (h.contains(a)) return { inHeader: true };
        return { gap: a.getBoundingClientRect().top - h.getBoundingClientRect().bottom, visible: a.getBoundingClientRect().bottom <= p.getBoundingClientRect().bottom + 1 }; }"""
    # Down with Tab (fields enter from below), then back up with Shift+Tab (fields enter from under the title).
    for key in ("Tab", "Shift+Tab"):
        for _ in range(46):
            page.keyboard.press(key)
            info = page.evaluate(probe)
            if info is None:
                break
            if info.get("inHeader"):
                continue
            require(info["gap"] >= -1 and info["visible"], f"A field reached with {key} is not under the pinned title: {info}")
        if key == "Tab":
            require(page.evaluate("document.getElementById('items-filter-panel').scrollTop") > 0, "The test tabbed far enough to scroll the panel")
            page.focus("#department-options li:last-child input")


def sizes(page, base):
    load(page, base)
    page.click("#department-summary")
    small = page.evaluate("[...document.querySelectorAll('.search-facet-list label')].filter(l => l.getBoundingClientRect().height < 24 || l.getBoundingClientRect().width < 24).length")
    require(small == 0, f"{small} option rows are smaller than 24 px")
    row = page.evaluate("(() => { const l = document.querySelector('#department-options label'), r = l.getBoundingClientRect(), s = document.getElementById('items-filter-panel').getBoundingClientRect(); return r.width / s.width; })()")
    require(row > 0.8, f"The whole row is the click target: {row:.2f} of the column")


def narrow(browser, base):
    context = browser.new_context(viewport={"width": 320, "height": 700})
    page = context.new_page()
    load(page, base)
    require(page.get_attribute("#items-filter-panel-toggle", "aria-expanded") == "false", "Narrow screens start closed")
    page.click("#items-filter-panel-toggle")
    page.click("#department-summary")
    require(not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"), "No sideways scrolling at 320 px with the panel and a group open")
    page.focus("#item-search")
    page.keyboard.press("Escape")
    require(page.get_attribute("#items-filter-panel-toggle", "aria-expanded") == "false", "Escape closes the panel on a narrow screen")
    require(page.evaluate("document.activeElement.id") == "items-filter-panel-toggle", "Focus returns to the button")
    require(not page.is_visible("#item-search"), "The closed panel leaves the tab order")
    context.close()


def forced_colors(browser, base):
    context = browser.new_context(viewport={"width": 1100, "height": 800}, forced_colors="active")
    page = context.new_page()
    load(page, base)
    page.focus("#department-summary")
    ring = page.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, parseFloat(s.outlineWidth)]; })()")
    require(ring[0] != "none" and ring[1] >= 2, f"Focus ring shows in forced colors: {ring}")
    # Forced colors repaints everything in system colors, so what must survive is shape: the toggle keeps its border,
    # icons keep a stroke, fields and the pinned header keep a border or an edge, and nothing is clipped away.
    look = page.evaluate(
        """() => {
            const css = (sel, props) => { const el = document.querySelector(sel), s = getComputedStyle(el); return props.map(p => s[p]); };
            const stroke = getComputedStyle(document.querySelector('#items-filter-panel-toggle svg:not([hidden])')).stroke;
            return { toggle: css('#items-filter-panel-toggle', ['borderTopStyle', 'borderTopWidth']), stroke,
                     search: css('#item-search', ['borderTopStyle', 'borderTopWidth']), select: css('#items-filter-panel-tag', ['borderTopStyle', 'borderTopWidth']),
                     reset: css('#items-filter-panel .action-button', ['borderTopStyle', 'borderTopWidth']),
                     legend: document.querySelector('#items-filter-panel legend').getBoundingClientRect().width > 0 };
        }"""
    )
    for name in ("toggle", "search", "select", "reset"):
        require(look[name][0] != "none" and float(look[name][1].replace("px", "")) >= 1, f"{name} keeps a border in forced colors: {look[name]}")
    require(look["stroke"] not in ("none", "") and look["legend"], f"Icons keep a stroke and group names show in forced colors: {look}")
    context.close()


def axe(page, base, scheme):
    if not AXE:
        print("SKIP: axe-core scan (set AXE_CORE to axe.min.js).")
        return
    load(page, base)
    page.click("#department-summary")
    page.add_script_tag(path=AXE)
    result = page.evaluate("axe.run(document.querySelector('main'), { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] })")
    found = [f"{v['id']}: {v['help']} ({', '.join(n['target'][0] for n in v['nodes'][:3])})" for v in result["violations"]]
    require(not found, f"axe-core ({scheme}): {found}")
    # The same scan with a date range error showing, and with the load-failure message showing.
    page.fill("#items-filter-panel-date-from", "2026-02-01")
    page.fill("#items-filter-panel-date-to", "2026-01-01")
    page.dispatch_event("#items-filter-panel-date-to", "change")
    result = page.evaluate("axe.run(document.querySelector('main'), { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] })")
    found = [f"{v['id']}: {v['help']}" for v in result["violations"]]
    require(not found, f"axe-core with a range error ({scheme}): {found}")
    EXPECTING_ERRORS["on"] = True
    page.route("**/filters/valid-column.json", lambda route: route.fulfill(status=500, body="no"))
    page.goto(base + FIXTURE)
    page.wait_for_selector("[data-filter-column] .app-alert")
    page.add_script_tag(path=AXE)
    result = page.evaluate("axe.run(document.querySelector('main'), { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] })")
    found = [f"{v['id']}: {v['help']}" for v in result["violations"]]
    page.unroute("**/filters/valid-column.json")
    EXPECTING_ERRORS["on"] = False
    require(not found, f"axe-core with the load error ({scheme}): {found}")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/"
    problems = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for scheme in ("light", "dark"):
                context = browser.new_context(color_scheme=scheme, viewport={"width": 1100, "height": 800})
                page = context.new_page()
                page.on("pageerror", lambda e: problems.append(str(e)))
                page.on("console", lambda m: problems.append(m.text) if m.type == "error" and not EXPECTING_ERRORS["on"] else None)
                for check in (drawn, group_types, hierarchy, app_options, small_columns, results_and_errors, behaves, focus_not_obscured, sizes):
                    check(page, base)
                axe(page, base, scheme)
                context.close()
            narrow(browser, base)
            forced_colors(browser, base)
            browser.close()
    finally:
        server.shutdown()
    require(not problems, f"Console or page errors: {problems}")
    print("Filter column browser test (light and dark): PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
