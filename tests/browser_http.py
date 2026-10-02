#!/usr/bin/env python3
"""Separate real-HTTP app integration check. Requires a browser allowed to reach localhost."""
from __future__ import annotations
import argparse
import contextlib
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from assets import require
from install import install
from browser_smoke import chrome_path, platform_fonts


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-source", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="marinos-http-") as temp:
        webroot = Path(temp)
        app = webroot / "test-app"
        app.mkdir()
        (app / "marin.yml").write_text("schema: 1\nplatform:\n  shell: 1.1.0\n")
        install(app, args.font_source)
        shutil.copytree(ROOT / "demo", app / "demo")
        shutil.copy2(ROOT / "security.json", app / "security.json")
        html = (ROOT / "index.html").read_text().replace('href="dist/', 'href="vendor/marinos/').replace('src="dist/', 'src="vendor/marinos/')
        (app / "index.html").write_text(html)
        handler = functools.partial(QuietHandler, directory=str(webroot))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=chrome_path(), headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                try:
                    page = browser.new_page(viewport={"width":1440,"height":1000})
                    errors, failures, font_responses = [], [], []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.on("requestfailed", lambda r: failures.append(r.url))
                    page.on("response", lambda r: font_responses.append((r.url, r.status)) if r.request.resource_type == "font" else None)
                    # Data/API calls are fixtures. All HTML, CSS, JS and fonts really load over local HTTP.
                    page.route("https://api.github.com/**", lambda route: route.fulfill(status=200,
                        content_type="application/json", headers={"Access-Control-Allow-Origin":"*"}, body="[]"))
                    base = f"http://127.0.0.1:{server.server_port}/test-app/"
                    page.goto(base, wait_until="networkidle")
                    page.wait_for_function("window.MarinAppShell?.version === '1.1.0'")
                    page.evaluate("document.fonts.ready")
                    for suffix in ("Jost-wght.ttf", "OpenSans-VariableFont_wdth,wght.woff2"):
                        require(any(suffix in url and status == 200 for url, status in font_responses), f"Local font not served: {suffix}")
                    for selector, family in ((".app-title","Jost"),(".demo-lede","Open Sans")):
                        fonts = platform_fonts(page,selector)
                        require(any(f["isCustomFont"] and f["glyphCount"] > 0 and family.replace(" ","").lower() in f["familyName"].replace(" ","").lower() for f in fonts),
                                f"Actual rendered font mismatch: {selector}: {fonts}")
                    page.locator("#app-nav a[href='#about']").click()
                    page.wait_for_function("!document.getElementById('about').hidden")
                    page.evaluate("window.__homeNavigationProbe = true")
                    page.locator(".app-identity__home").click()
                    page.wait_for_url(base)
                    page.wait_for_function("Boolean(window.MarinAppShell) && !document.getElementById('start').hidden")
                    require(page.evaluate("window.__homeNavigationProbe === undefined"), "Identity did not do a full home navigation")
                    require(not errors and not failures, f"HTTP errors: {errors}; failed requests: {failures}")
                    print("browser_http.py: PASS (local HTTP assets/fonts, project subpath, full identity-to-home navigation)")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
