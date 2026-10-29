#!/usr/bin/env python3
"""Browser test of the shared copy, download, file-reading, text-cleaning and upload helpers in the built shell.

Serves a fixture page from a fake https origin through Playwright routes and loads dist/marinos.js. Needs
Playwright for Python and Chromium.  Run: python3 tests/browser_shared_helpers.py
"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://example.test"
PAGE = f"{ORIGIN}/app/"
HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Shared helpers fixture</title>
<link rel="stylesheet" href="/vendor/marinos/marinos.css"><script src="/vendor/marinos/marinos.js" defer></script></head>
<body data-app-id="fixture"><main id="main" class="container app-main">
<h2 style="font-weight:700">Rustic Bakery</h2>
<div class="doc-actions" data-formats-for="#page" data-file-name="my-page">
  <button type="button" data-copy-format="text">Copy text</button>
  <button type="button" data-copy-format="html">Copy HTML</button>
  <button type="button" data-copy-format="markdown">Copy Markdown</button>
  <button type="button" data-download-format="text">Save text</button>
  <button type="button" data-download-format="html">Save HTML</button>
  <button type="button" data-download-format="markdown">Save Markdown</button>
  <span class="doc-action-status" role="status"></span>
</div>
<article id="page"><h1 class="doc-title">Page title</h1><p class="doc-updated">Updated today</p>
  <p>Intro with <strong>bold</strong> and a <a href="/next.html">link</a>.</p>
  <ul><li>One</li><li>Two <em>nested</em></li></ul>
  <table><thead><tr><th scope="col">A</th><th scope="col">B</th></tr></thead><tbody><tr><td>1</td><td>2</td></tr><tr><td>C:\\data</td><td>a|b</td></tr></tbody></table>
  <p>Line one<br>Line two</p>
  <p data-no-copy>Left out</p><nav>Menu</nav><script>1</script></article>
<button type="button" id="browse" class="action-button">Browse files</button>
<input id="file" type="file" class="visually-hidden" aria-label="Choose a file">
<p id="status" role="status"></p>
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


CLIPBOARD = """async () => {
  const [item] = await navigator.clipboard.read();
  const out = {};
  for (const type of item.types) out[type] = await (await item.getType(type)).text();
  return out;
}"""


def run(page, tmp: Path):
    page.goto(PAGE)
    page.wait_for_function("typeof window.marinCopyRich === 'function' && typeof window.marinUpload === 'function'")

    # Format menus: Text, HTML and Markdown of a page, copied and saved, clean of the page's own look.
    page.click("[data-copy-format=markdown]")
    page.wait_for_function("document.querySelector('.doc-action-status').textContent === 'Copied Markdown.'")
    md = page.evaluate("navigator.clipboard.readText()")
    require(md.startswith("# Page title\n\nIntro with **bold** and a [link](https://example.test/next.html).") and "- One\n- Two *nested*" in md, f"Markdown copy: {md!r}")
    require("| C:\\\\data | a\\|b |" in md, f"Markdown escapes a backslash and a pipe in a table cell: {md!r}")
    require("| A | B |\n| --- | --- |\n| 1 | 2 |" in md and "Left out" not in md and "Menu" not in md and "Updated today" not in md, f"Markdown leaves out the skipped parts and keeps the table: {md!r}")
    require("Line one  \nLine two" in md, f"Markdown keeps a line break inside a paragraph: {md!r}")
    page.click("[data-copy-format=html]")
    page.wait_for_function("document.querySelector('.doc-action-status').textContent === 'Copied HTML.'")
    html_copy = page.evaluate("navigator.clipboard.readText()")
    require(html_copy.startswith("<h1>Page title</h1><p>Intro with <strong>bold</strong> and a <a href=\"https://example.test/next.html\">link</a>.</p>") and "class=" not in html_copy and "style=" not in html_copy and "Left out" not in html_copy, f"HTML copy is clean: {html_copy[:200]}")
    page.click("[data-copy-format=text]")
    page.wait_for_function("document.querySelector('.doc-action-status').textContent === 'Copied rich text.'")
    got = page.evaluate(CLIPBOARD)
    require(got["text/html"] == html_copy and got["text/plain"].startswith("Page title\n\nIntro with bold and a link (https://example.test/next.html)."), f"Rich text copy: {got['text/plain'][:120]}")
    for fmt, name in (("text", "my-page.txt"), ("html", "my-page.html"), ("markdown", "my-page.md")):
        with page.expect_download() as info:
            page.click(f"[data-download-format={fmt}]")
        require(info.value.suggested_filename == name, f"Download {fmt} is named {name}")

    # Copy: the clipboard holds exactly the HTML given (links kept), never this page's styles, by either route.
    html = '<h3>Rustic Bakery</h3><p><b><a href="https://example.org/a">Title</a></b></p><ul><li>dept: Food</li></ul>'
    for route_name, setup in (("copy event", ""), ("Clipboard API", "document.execCommand = () => false;")):
        page.reload()
        page.wait_for_function("typeof window.marinCopyRich === 'function'")
        page.evaluate("async ([setup, html]) => { eval(setup); window.__r = await window.marinCopyRich('Rustic Bakery\\ndept: Food', html); }", [setup, html])
        require(page.evaluate("window.__r") is True, f"Rich copy reports success ({route_name})")
        got = page.evaluate(CLIPBOARD)
        require("https://example.org/a" in got["text/html"] and "<h3>Rustic Bakery</h3>" in got["text/html"], f"The link and heading are kept ({route_name}): {got['text/html'][:160]}")
        require("style=" not in got["text/html"] and "<strong" not in got["text/html"], f"No styles or strong tags ({route_name})")
        require(got["text/plain"] == "Rustic Bakery\ndept: Food", f"Plain text is the given text ({route_name})")
    page.reload()
    page.wait_for_function("typeof window.marinCopyText === 'function'")
    page.evaluate("window.ClipboardItem = undefined; Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true})")
    require(page.evaluate("window.marinCopyRich('plain', '<h3>Plain</h3>')") is True, "Rich copy works with no Clipboard API (the copy event)")
    require(page.evaluate("window.marinCopyText('just text')") is True, "Text copy works with no Clipboard API")
    page.reload()
    page.wait_for_function("typeof window.marinCopyText === 'function'")
    require(page.evaluate("window.marinCopyText('hello')") is True, "Text copy works")
    require(page.evaluate("navigator.clipboard.readText()") == "hello", "Text copy puts the text on the clipboard")

    # Download: a CSV starts with a byte-order mark, other text does not, and the name and type are right.
    def download(script):
        with page.expect_download() as info:
            page.evaluate(script)
        return info.value

    csv = download("window.marinDownload({content: 'a,b\\nJimmy\\u2019s,2', name: 'people.csv'})")
    data = Path(csv.path()).read_bytes()
    require(csv.suggested_filename == "people.csv" and data.startswith(b"\xef\xbb\xbf"), "A CSV download starts with a byte-order mark")
    require("Jimmy’s".encode("utf-8") in data, "A CSV download is UTF-8")
    txt = download("window.marinDownload({content: 'plain', name: 'notes.txt'})")
    require(not Path(txt.path()).read_bytes().startswith(b"\xef\xbb\xbf"), "A text download has no byte-order mark")
    md = download("window.marinDownload({content: '## Ann', name: 'out.md'})")
    require(md.suggested_filename == "out.md" and Path(md.path()).read_text(encoding="utf-8") == "## Ann", "A Markdown download keeps its name and text")
    nobom = download("window.marinDownload({content: 'x', name: 'x.csv', bom: false})")
    require(not Path(nobom.path()).read_bytes().startswith(b"\xef\xbb\xbf"), "bom: false leaves the mark off")

    # Reading: valid UTF-8 as UTF-8, anything else as Windows-1252, never a replacement character.
    result = page.evaluate("""async () => {
      const legacy = await window.marinReadText(new Blob([new Uint8Array([0x4a,0x69,0x6d,0x6d,0x79,0x92,0x73,0x20,0x43,0x61,0x66,0xe9])]));
      const utf8 = await window.marinReadText(new Blob([new Uint8Array([0xef,0xbb,0xbf,0x43,0x61,0x66,0xc3,0xa9])]));
      return {legacy, utf8};
    }""")
    require(result["legacy"] == {"text": "Jimmy’s Café", "encoding": "windows-1252"}, f"Windows-1252 is read correctly: {result['legacy']}")
    require(result["utf8"] == {"text": "Café", "encoding": "utf-8"}, f"UTF-8 is read, and its byte-order mark dropped: {result['utf8']}")

    # Cleaning.
    cleaned = page.evaluate("""() => ['Jimmy\\ufffds', 'It\\u2019s \\u201cfine\\u201d\\u2026', 'a\\u00a0b\\u200bc', '\\u00e2\\u20ac\\u2122ok', 'x\\ufffd ', 42].map(window.marinCleanText)""")
    require(cleaned == ["Jimmy's", 'It\'s "fine"...', "a bc", "'ok", "x ", 42], f"Text is cleaned: {cleaned}")

    # Upload: Browse opens the chooser, a wrong type or a big file gets a plain message, a drop works anywhere.
    page.evaluate("""() => {
      window.__got = []; window.__msg = [];
      window.marinUpload({button: document.getElementById('browse'), input: document.getElementById('file'),
        accept: ['.csv', '.xlsx'], maxBytes: 2048, onFile: (f) => window.__got.push(f.name), onMessage: (m) => window.__msg.push(m)});
    }""")
    with page.expect_file_chooser() as chooser:
        page.click("#browse")
    chooser.value.set_files(tmp / "ok.csv")
    require(page.evaluate("window.__got") == ["ok.csv"], "Browse files passes an accepted file")
    page.set_input_files("#file", tmp / "bad.exe")
    require(page.evaluate("window.__msg").pop() == "Unsupported file type. Upload .csv or .xlsx.", "A wrong file type gets the standard message")
    page.set_input_files("#file", tmp / "big.csv")
    require(page.evaluate("window.__msg").pop() == "That file is too large. The limit is 2 KB.", "A file over the limit gets the standard message")
    drop = """([names]) => {
      const dt = new DataTransfer();
      names.forEach((n) => dt.items.add(new File(['a,b\\n1,2'], n, {type: 'text/csv'})));
      const fire = (type) => window.dispatchEvent(new DragEvent(type, {dataTransfer: dt, bubbles: true, cancelable: true}));
      fire('dragenter');
      const shown = document.querySelector('.upload-drop-overlay').dataset.active;
      fire('drop');
      return [shown, document.querySelector('.upload-drop-overlay').dataset.active];
    }"""
    require(page.evaluate(drop, [["dropped.csv"]]) == ["true", "false"], "The drop layer shows while dragging and hides after the drop")
    require(page.evaluate("window.__got").pop() == "dropped.csv", "A dropped file is passed on")
    page.evaluate(drop, [["one.csv", "two.csv"]])
    require(page.evaluate("window.__msg").pop() == "More than one file was dropped. Using the first file: one.csv.", "Several dropped files use the first and say so")
    require(page.evaluate("window.__got").pop() == "one.csv", "Only the first of several files is used")


def main():
    import tempfile
    problems = []
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        (tmp / "ok.csv").write_text("a,b\n1,2\n")
        (tmp / "bad.exe").write_bytes(b"MZ")
        (tmp / "big.csv").write_text("x" * 5000)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1100, "height": 800}, accept_downloads=True)
            context.grant_permissions(["clipboard-read", "clipboard-write"], origin=ORIGIN)
            context.route(f"{ORIGIN}/**", serve)
            page = context.new_page()
            page.on("pageerror", lambda e: problems.append(str(e)))
            run(page, tmp)
            context.close()
            browser.close()
    require(not problems, f"Page errors: {problems}")
    print("Shared copy, download, file reading, text cleaning and upload helpers: PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
