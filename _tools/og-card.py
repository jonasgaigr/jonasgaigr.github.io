"""Render _tools/og-card.html to img/og-card.jpg (1200 x 630), the image shown
when a page of the site is shared. Needs Playwright: pip install playwright
and playwright install chromium.

    python _tools/og-card.py
"""
import os
import pathlib

from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).resolve().parent
out = here.parent / "img" / "og-card.jpg"
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")   # the installed Chrome
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    page.goto((here / "og-card.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(out), type="jpeg", quality=88)
    browser.close()
print(f"{out.relative_to(here.parent)}: {os.path.getsize(out) // 1024} KB")
