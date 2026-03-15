import asyncio
import re
from typing import List, Optional, Tuple
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from models import ImageResult

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_DELAY = 1.0  # seconds between requests

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]


async def _stealth_page(browser):
    """Create a page with basic stealth settings to avoid bot detection."""
    context = await browser.new_context(
        user_agent=HEADERS["User-Agent"],
        viewport={"width": 1280, "height": 800},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return page


async def _fetch(url: str, wait_until: str = "networkidle") -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=STEALTH_ARGS)
        page = await _stealth_page(browser)
        await page.goto(url, wait_until=wait_until, timeout=30000)
        html = await page.content()
        await browser.close()
    return html


# ---------------------------------------------------------------------------
# Primary: www.douban.com/search (covers movies, books, music)
# ---------------------------------------------------------------------------

def _extract_top_result_general(html: str) -> Optional[Tuple[str, str, int]]:
    """Parse www.douban.com/search results.

    Returns (subject_url, image_url, review_count) or None if unavailable
    (e.g. error 103 when not logged in).
    """
    soup = BeautifulSoup(html, "html.parser")

    best: Optional[Tuple[str, str, int]] = None

    for card in soup.select(".DouWeb-SR-subject-card"):
        link = card.select_one("a.DouWeb-SR-subject-info-name")
        if not link:
            continue
        href = link.get("href", "")
        subject_url = _dispatch_to_subject_url(href)
        if not subject_url:
            continue

        img_tag = card.select_one("img")
        img_src = img_tag.get("src", "") if img_tag else ""

        rating_count = card.select_one(".DouWeb-SR-subject-info-rating-count")
        count = 0
        if rating_count:
            m = re.search(r"([\d,]+)", rating_count.get_text())
            if m:
                count = int(m.group(1).replace(",", ""))

        if best is None or count > best[2]:
            best = (subject_url, img_src, count)

    return best


def _dispatch_to_subject_url(dispatch_href: str) -> Optional[str]:
    """Convert /doubanapp/dispatch?uri=/movie/123 → https://movie.douban.com/subject/123/"""
    match = re.search(r"uri=/(movie|book|music)/(\d+)", dispatch_href)
    if not match:
        return None
    category, subject_id = match.group(1), match.group(2)
    return f"https://{category}.douban.com/subject/{subject_id}/"


async def _fetch_detail_image(subject_url: str) -> Optional[str]:
    """Fetch the detail page and extract the main cover image URL."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=STEALTH_ARGS)
        page = await _stealth_page(browser)
        await page.goto(subject_url, wait_until="domcontentloaded", timeout=30000)
        # Challenge solves itself; wait for #mainpic as signal we're on the real page
        await page.wait_for_selector("#mainpic", timeout=30000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    mainpic = soup.select_one("#mainpic img")
    if mainpic:
        src = mainpic.get("src", "")
        if src:
            return src.replace("s_ratio_poster", "l_ratio_poster")
    return None


# ---------------------------------------------------------------------------
# Fallback: movie.douban.com/subject_search (no login required, image inline)
# ---------------------------------------------------------------------------

def _extract_top_result_movie(html: str) -> Optional[Tuple[str, str, int]]:
    """Parse movie.douban.com/subject_search results.

    Returns (subject_url, image_url, review_count) or None.
    """
    soup = BeautifulSoup(html, "html.parser")

    best: Optional[Tuple[str, str, int]] = None

    for item in soup.select(".item-root"):
        link = item.select_one("a.cover-link")
        img = item.select_one("img.cover")
        pl = item.select_one(".pl")

        if not link or not img:
            continue

        subject_url = link.get("href", "")
        img_src = img.get("src", "")

        count = 0
        if pl:
            m = re.search(r"([\d,]+)", pl.get_text())
            if m:
                count = int(m.group(1).replace(",", ""))

        if best is None or count > best[2]:
            best = (subject_url, img_src, count)

    if best:
        subject_url, img_src, count = best
        img_src = img_src.replace("s_ratio_poster", "l_ratio_poster")
        return subject_url, img_src, count

    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def crawl(name: str) -> List[ImageResult]:
    # Step 1: Try the general Douban search (all categories)
    general_url = "https://www.douban.com/search?" + urlencode({"q": name})
    print(f"Trying general search: {general_url}")
    general_html = await _fetch(general_url)

    with open("/tmp/douban_rendered.html", "w") as f:
        f.write(general_html)

    result = _extract_top_result_general(general_html)

    if result:
        subject_url, img_src, count = result
        print(f"General search succeeded: {subject_url} ({count} reviews)")

        # If the search result doesn't include an inline image, fetch the detail page
        if not img_src:
            await asyncio.sleep(REQUEST_DELAY)
            img_src = await _fetch_detail_image(subject_url)

        if img_src:
            img_src = img_src.replace("s_ratio_poster", "l_ratio_poster")
            return [ImageResult(url=img_src, referer=subject_url)]

    # Step 2: Fallback to movie-specific search (no login required)
    print("General search unavailable, falling back to movie search")
    fallback_url = "https://movie.douban.com/subject_search?" + urlencode({
        "search_text": name,
        "cat": "1002",
    })
    fallback_html = await _fetch(fallback_url)

    result = _extract_top_result_movie(fallback_html)
    if result:
        subject_url, img_src, count = result
        print(f"Fallback search succeeded: {subject_url} ({count} reviews)")
        return [ImageResult(url=img_src, referer=subject_url)]

    return []
