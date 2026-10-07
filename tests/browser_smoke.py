#!/usr/bin/env python3
"""In-memory browser fixture. Real pinned fonts; no claim of HTTP/deployment coverage."""
from __future__ import annotations
import argparse
import base64
import json
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from assets import FONT_PATHS, SVG_ATTRIBUTES, require, resolve_fonts
from build import adapt_brand, icons, verify_distribution

ICON = (ROOT / "vendor/icons/lucide/layout-grid.svg").read_text().strip()
HTML = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Shell fixture</title></head><body>
<marin-os-banner catalog-url="catalog.json"></marin-os-banner>
<marin-app-header app-id="test-app" app-name="Test App" app-description="Test description">
<template data-icon>__ICON__</template></marin-app-header>
<main id="main" class="container app-main">
<section id="start" data-tab-section="start"><h2 id="heading-sample">Start</h2>
<p id="body-sample">Ordinary interface copy.</p><label for="test-input">Test input</label><input id="test-input">
<button type="button" id="body-button">Test button</button>
<div class="app-card__icon">__LEGACY_ICON__</div></section>
<marin-app-info app-name="Test App" repo="test-app" security-src="security.json">
<template data-about><p>Custom About content.</p></template>
<template data-accessibility><p>Custom accessibility content.</p></template></marin-app-info>
</main><marin-app-footer app-name="Test App"></marin-app-footer>
<div hidden id="footer-contract-fixtures">
<marin-app-footer id="custom-footer" app-name="MarinOS" hide-platform-link>
<template data-footer-links>
<a href="#projects">Projects</a><a href="#status">Status</a>
<a href="#about">Duplicate About</a><a href="#projects">Duplicate Projects</a>
<span>Ignored non-link</span>
</template></marin-app-footer>
<marin-app-footer id="legacy-footer" app-name="Legacy Footer" links="updates"></marin-app-footer>
</div>
<marin-app-feedback href="https://example.test/feedback"></marin-app-feedback></body></html>'''


def chrome_path() -> str:
    path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    require(path is not None, "Chromium is required for the browser fixture")
    return path


def font_css(page: Page, css: str, fonts: dict[str, Path]) -> str:
    payload = [base64.b64encode(fonts[p].read_bytes()).decode("ascii") for p in FONT_PATHS[:2]]
    urls = page.evaluate('''values => values.map(value => {
      const bytes = Uint8Array.from(atob(value), c => c.charCodeAt(0));
      return URL.createObjectURL(new Blob([bytes]));
    })''', payload)
    # Deliberate test-only URL substitution. Production URL contracts are checked separately.
    for relative, url in zip(("../fonts/Jost-wght.ttf", "../fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2"), urls):
        css = css.replace(relative, url)
    return css


def platform_fonts(page: Page, selector: str) -> list[dict]:
    client = page.context.new_cdp_session(page)
    try:
        client.send("DOM.enable")
        client.send("CSS.enable")
        node = client.send("DOM.getDocument")["root"]["nodeId"]
        selected = client.send("DOM.querySelector", {"nodeId": node, "selector": selector})["nodeId"]
        return client.send("CSS.getPlatformFontsForNode", {"nodeId": selected})["fonts"]
    finally:
        client.detach()


def check_fonts(page: Page) -> None:
    page.evaluate('''async () => {
      await document.fonts.load('16px "Open Sans"');
      await document.fonts.load('600 24px "Jost"');
      await document.fonts.ready;
    }''')
    for selector, expected in (("#body-sample", "Open Sans"), (".app-title", "Jost"),
                               ("#heading-sample", "Jost"), ("#body-button", "Open Sans"),
                               ("#test-input", "Open Sans"), (".marinos-menu__toggle", "Open Sans"),
                               (".app-footer__nav a", "Open Sans")):
        family = page.locator(selector).first.evaluate("el => getComputedStyle(el).fontFamily")
        require(family.split(",")[0].strip(' "') == expected, f"Wrong computed font on {selector}: {family}")
    for selector, expected in (("#body-sample", "Open Sans"), (".app-title", "Jost"), ("#body-button", "Open Sans")):
        rendered = platform_fonts(page, selector)
        require(any(f["isCustomFont"] and f["glyphCount"] > 0 and expected.replace(" ", "").lower() in f["familyName"].replace(" ", "").lower() for f in rendered),
                f"Required font did not actually render on {selector}: {rendered}")
    faces = page.evaluate("Array.from(document.fonts).map(f => ({family:f.family,status:f.status}))")
    require(all(any(f["family"].strip('"') == name and f["status"] == "loaded" for f in faces) for name in ("Open Sans", "Jost")),
            f"Fonts did not decode: {faces}")


def prepare(page: Page, fonts: dict[str, Path], legacy: bool = False) -> list[str]:
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    legacy_icon = re.sub(r'<svg[^>]*>', '<svg viewBox="0 0 24 24">', ICON, count=1)
    page.set_content(HTML.replace("__ICON__", legacy_icon if legacy else ICON).replace("__LEGACY_ICON__", legacy_icon))
    page.add_style_tag(content=font_css(page, (ROOT / "dist/marinos.css").read_text(), fonts))
    catalog = [{"id":"test-app", "name":"Test App", "url":"https://example.test/test-app/", "status":"beta", "icon":{"viewBox":"0 0 24 24", "markup":icons(ROOT)["layout-grid"]}},
               {"id":"another-app", "name":"Another App", "url":"https://example.test/other/", "status":"alpha", "icon":{"viewBox":"0 0 24 24", "markup":icons(ROOT)["layout-grid"]}},
               {"id":"live-app", "name":"Live App", "url":"https://example.test/live/", "status":"live"},
               {"id":"invalid-app", "name":"Invalid App", "url":"https://example.test/invalid/", "status":"active"},
               {"id":"untrusted", "name":"Untrusted icon", "url":"https://example.test/untrusted/", "status":"beta", "icon":{"viewBox":"0 0 24 24", "markup":'<script>window.badIcon=true</script><path d="M0 0" onload="window.badIcon=true"/>'}}]
    security = json.loads((ROOT / "security.json").read_text())
    commits = [{"html_url":"https://example.test/commit", "commit":{"message":"Test release", "author":{"date":"2026-10-01T12:00:00Z"}}}]
    manifest = "schema: 1\nproject:\n  name: Test App\n  status: beta\n"
    page.evaluate('''([catalog, security, commits, manifest, omitManifest]) => {
      window.fetch = async input => {
        const url = String(input);
        if (url.includes('marin.yml')) {
          return new Response(omitManifest ? '' : manifest, {
            status: omitManifest ? 404 : 200,
            headers:{'Content-Type':'text/yaml'}
          });
        }
        const data = url.includes('catalog.json') ? catalog : url.includes('security.json') ? security : url.includes('api.github.com') ? commits : null;
        return new Response(JSON.stringify(data), {status: data ? 200 : 404, headers:{'Content-Type':'application/json'}});
      };
    }''', [catalog, security, commits, manifest, legacy])
    page.add_script_tag(content=(ROOT / "dist/marinos.js").read_text())
    page.wait_for_function("Boolean(window.MarinAppShell)")
    return errors


def header_parity(page: Page, fonts: dict[str, Path]) -> None:
    properties = ["paddingTop", "paddingBottom", "marginTop", "marginBottom", "gap", "display"]
    selectors = [".app-header", ".app-header__inner", ".app-title-row", ".app-title-copy"]
    def measure(p):
        return p.evaluate('''([selectors, properties]) => Object.fromEntries(selectors.map(selector => {
          const style=getComputedStyle(document.querySelector(selector));
          return [selector,Object.fromEntries(properties.map(key=>[key,style[key]]))];
        }))''', [selectors, properties])
    current = measure(page)
    reference = page.context.new_page()
    try:
        reference.set_content("<!doctype html><html><body>" + page.locator(".app-header").evaluate("el=>el.outerHTML") + "</body></html>")
        baseline = (ROOT / "vendor/pico.min.css").read_text() + "\n" + adapt_brand((ROOT / "vendor/marin-ui/app-brand.css").read_text())
        reference.add_style_tag(content=font_css(reference, baseline, fonts))
        expected = measure(reference)
        require(current == expected, f"Header geometry differs from direct-child UI baseline: {current} != {expected}")
    finally:
        reference.close()


def run_test(source: Path | None, screenshots: Path | None) -> None:
    manifest = verify_distribution()
    fonts, label = resolve_fonts(ROOT, source)
    print(f"Browser fixture font source: {label}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chrome_path(), headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for width, scheme in ((1440,"light"), (1440,"dark"), (390,"light"), (390,"dark"), (320,"light")):
                context = browser.new_context(viewport={"width":width,"height":900}, color_scheme=scheme)
                try:
                    page = context.new_page()
                    errors = prepare(page, fonts, legacy=width==320)
                    check_fonts(page)
                    header_parity(page, fonts)
                    require(page.evaluate("window.MarinAppShell.version") == manifest["shellVersion"], "Wrong runtime version")
                    require(page.locator(".skip-link").count()==1 and page.locator("#app-status-message").count()==1, "Shared accessibility infrastructure missing")
                    require(page.locator("#start").is_visible() and page.locator("#about").is_hidden(), "Default route broken")
                    require(page.locator(".app-identity > .app-title-row").count()==1, "Identity title row missing")
                    require(page.locator(".app-title-row > .app-icon").count()==1, "Identity icon placement drift")
                    require(page.locator(".app-title .app-title__link[href='./']").count()==1, "Application name home link missing")
                    require(page.locator(".app-icon").evaluate("el=>el.closest('a')===null"), "Application icon must not be part of the home link")
                    require(page.locator(".app-subtitle").evaluate("el=>el.closest('a')===null"), "Application subtitle must not be part of the home link")
                    require(page.locator(".app-title__status[data-status='beta']").count()==1, "Current app status badge missing")
                    expected_status_source = "catalog" if width == 320 else "manifest"
                    require(page.locator(".app-title__status").get_attribute("data-marinos-status")==expected_status_source, f"Wrong local status source: expected {expected_status_source}")
                    require(page.locator(".app-title__status").get_attribute("href").endswith("/marin-os/#status"), "Current app status link is wrong")
                    require(page.locator(".marinos-banner__status[data-status='alpha']").count()==1, "MarinOS banner status badge missing")
                    if scheme == "dark":
                        alpha = page.locator(".marinos-banner__status[data-status='alpha']")
                        require(alpha.evaluate("el=>getComputedStyle(el).backgroundColor") == "rgb(229, 181, 59)", "Dark-mode Alpha background is not County gold")
                        require(alpha.evaluate("el=>getComputedStyle(el).color") == "rgb(0, 0, 0)", "Dark-mode Alpha text is not black")
                    default_footer = page.locator("marin-app-footer:not(#custom-footer):not(#legacy-footer)")
                    require(default_footer.locator(".app-footer__nav a").all_text_contents() == ["About","Security","Accessibility","Tech","Updates"], "Footer navigation drift")
                    require(default_footer.locator(".app-footer__platform a").all_text_contents() == ["MarinOS"], "Default platform link drift")
                    require(page.locator("#custom-footer .app-footer__nav a").all_text_contents() == ["Projects","Status","About","Security","Accessibility","Tech","Updates"], "Custom footer links are not prepended to the required set")
                    require(page.locator("#custom-footer .app-footer__platform").count() == 0, "hide-platform-link did not suppress the platform link")
                    require(page.locator("#custom-footer .app-footer__app-name").all_text_contents() == ["MarinOS"], "Custom footer app name drift")
                    require(page.locator("#custom-footer template[data-footer-links]").count() == 0, "Footer template remained after render")
                    require(page.locator("#legacy-footer .app-footer__nav a").all_text_contents() == ["Updates","About","Security","Accessibility","Tech"], "Required footer links can still be omitted by legacy links ordering")
                    require(page.locator("#legacy-footer .app-footer__platform a").all_text_contents() == ["MarinOS"], "Legacy footer lost the default platform link")
                    for selector in (".app-icon svg", ".app-card__icon svg", ".marinos-banner__icon svg", ".menu-toggle__caret"):
                        svg = page.locator(selector).first
                        for key, value in SVG_ATTRIBUTES.items():
                            require(svg.get_attribute(key)==value, f"Wrong Lucide attribute {key} on {selector}")
                        require(svg.evaluate("el=>getComputedStyle(el).strokeWidth")=="2px", f"Wrong rendered stroke: {selector}")
                    # Late app-rendered legacy icons must not regress to filled black shapes.
                    page.evaluate("markup => { const x=document.createElement('div'); x.className='app-card__icon'; x.id='late-icon'; x.innerHTML=markup; document.getElementById('start').append(x); }",
                                  re.sub(r'<svg[^>]*>', '<svg viewBox="0 0 24 24">', ICON, count=1))
                    require(page.locator("#late-icon svg").evaluate("el=>getComputedStyle(el).strokeWidth")=="2px", "Late legacy icon fallback failed")
                    require(page.locator("#late-icon svg").evaluate("el=>getComputedStyle(el).fill")=="none", "Late legacy icon filled unexpectedly")
                    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Horizontal overflow at {width}")
                    # Keyboard focus remains visible on the application-name home link.
                    page.keyboard.press("Tab"); page.keyboard.press("Tab"); page.keyboard.press("Tab")
                    require(page.locator(".app-title__link").evaluate("el=>el===document.activeElement"), "Application name is not the third keyboard stop")
                    require(page.locator(".app-title__link").evaluate("el=>getComputedStyle(el).outlineStyle") != "none", "Application name focus is invisible")
                    if width < 721:
                        require(page.locator("#app-nav").is_hidden(), "Mobile menu should be collapsed")
                        page.locator("#menu-toggle").click()
                        require(page.locator("#app-nav").is_visible(), "Mobile menu failed to open")
                        page.keyboard.press("Escape")
                        require(page.locator("#app-nav").is_hidden(), "Escape failed to close mobile menu")
                    for route in ("about","security","accessibility","tech","updates"):
                        default_footer.locator(f".app-footer__nav a[href='#{route}']").click()
                        page.wait_for_function("id=>!document.getElementById(id).hidden",arg=route)
                    page.locator("#updates .copy-icon").first.wait_for()
                    require(page.locator("#updates .copy-icon").first.evaluate("el=>getComputedStyle(el).strokeWidth")=="2px", "Updates icon is not Lucide stroke 2")
                    require(page.locator("#updates .copy-icon").first.get_attribute("fill")=="none", "Updates icon fill incorrect")
                    page.locator(".marinos-menu__toggle").click()
                    page.get_by_text("Another App",exact=True).wait_for()
                    require(page.locator("#marinos-menu-panel .marinos-menu__status[data-status='alpha']").count()==1, "Alpha menu status missing")
                    require(page.locator("#marinos-menu-panel .marinos-menu__status[data-status='beta']").count()==2, "Beta menu statuses missing")
                    require(page.locator("#marinos-menu-panel .marinos-menu__status[data-status='live']").count()==1, "Live menu status missing")
                    require(page.locator("#marinos-menu-panel a[href='https://example.test/invalid/'] .marinos-menu__status").count()==0, "Invalid status should be omitted")
                    require(page.locator("#marinos-menu-panel .marinos-menu__name").count()==5, "Menu names are not wrapped consistently")
                    require(page.locator("#marinos-menu-panel script, #marinos-menu-panel [onload]").count()==0, "Catalog sanitizer regression")
                    require(page.evaluate("!window.badIcon"), "Untrusted catalog script executed")
                    page.keyboard.press("Escape")
                    require(page.locator("#marinos-menu-panel").is_hidden(), "Catalog Escape regression")
                    if screenshots:
                        screenshots.mkdir(parents=True, exist_ok=True)
                        default_footer.locator(".app-footer__nav a[href='#about']").click()
                        page.wait_for_function("!document.getElementById('about').hidden")
                        page.screenshot(path=str(screenshots / f"{width}-{scheme}.png"),full_page=True)
                    require(not errors, f"Uncaught browser errors: {errors}")
                    print(f"  PASS: {width}px {scheme}; rendered fonts, geometry, icons, routing, menus, focus")
                finally:
                    context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-source",type=Path)
    parser.add_argument("--screenshots",type=Path)
    args=parser.parse_args()
    run_test(args.font_source,args.screenshots)
    print("browser_smoke.py: PASS (in-memory fixtures; HTTP loading/navigation not exercised)")
