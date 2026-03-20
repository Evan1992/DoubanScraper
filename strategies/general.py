import asyncio
import re
from typing import List, Optional, Tuple
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from models import ImageResult
from fetch import fetch, stealth_page, STEALTH_ARGS, REQUEST_DELAY
from strategies.base import SearchStrategy


class GeneralSearchStrategy(SearchStrategy):
    """Primary: www.douban.com/search (movies, books, music, games, etc.)"""

    async def search(self, name: str) -> List[ImageResult]:
        url = "https://www.douban.com/search?" + urlencode({"q": name})
        print(f"Trying general search: {url}")
        html = await fetch(url)

        # Debug dump for manual inspection
        with open("/tmp/douban_rendered.html", "w") as f:
            f.write(html)

        result = self._extract_top_result(html)
        if not result:
            return []

        subject_url, img_src, count = result
        print(f"General search succeeded: {subject_url} ({count} reviews)")

        if not img_src:
            await asyncio.sleep(REQUEST_DELAY)
            img_src = await self._fetch_detail_image(subject_url)

        if img_src:
            img_src = img_src.replace("s_ratio_poster", "l_ratio_poster")
            return [ImageResult(url=img_src, referer=subject_url)]

        return []

    def _extract_top_result(self, html: str) -> Optional[Tuple[str, str, int]]:
        """Returns (subject_url, image_url, review_count) or None if unavailable
        (e.g. error 103 when not logged in).
        """
        soup = BeautifulSoup(html, "html.parser")
        best: Optional[Tuple[str, str, int]] = None

        for card in soup.select(".DouWeb-SR-subject-card"):
            link = card.select_one("a.DouWeb-SR-subject-info-name")
            if not link:
                continue
            href = link.get("href", "")
            subject_url = self._dispatch_to_subject_url(href)
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

    def _dispatch_to_subject_url(self, dispatch_href: str) -> Optional[str]:
        """Convert /doubanapp/dispatch?uri=/movie/123 → https://movie.douban.com/subject/123/"""
        match = re.search(r"uri=/(movie|book|music)/(\d+)", dispatch_href)
        if not match:
            return None
        category, subject_id = match.group(1), match.group(2)
        return f"https://{category}.douban.com/subject/{subject_id}/"

    async def _fetch_detail_image(self, subject_url: str) -> Optional[str]:
        """Fetch the detail page and extract the main cover image URL."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=STEALTH_ARGS)
            page = await stealth_page(browser)
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
