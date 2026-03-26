import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from models import ImageResult
from fetch import fetch
from strategies.base import SearchStrategy

logger = logging.getLogger(__name__)


class MobileSearchStrategy(SearchStrategy):
    """Fallback: m.douban.com/search (mobile site, no login required)."""

    async def search(self, name: str) -> List[ImageResult]:
        url = "https://m.douban.com/search/?" + urlencode({"query": name})
        logger.info(f"Trying mobile search: {url}")
        html = await fetch(url)

        result = self._extract_top_result(html)
        if not result:
            return []

        subject_url, img_src = result
        logger.info(f"Mobile search succeeded: {subject_url}")
        return [ImageResult(url=img_src, referer=subject_url)]

    def _extract_top_result(self, html: str) -> Optional[Tuple[str, str]]:
        """Returns (subject_url, image_url) for the first result, or None.

        Page structure (from m.douban.com/search):
          ul.search_results_subjects > li
            a[href="/movie/subject/123/"]
              img[src="...s_ratio_poster..."]
        """
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.select("ul.search_results_subjects > li"):
            link = item.select_one("a")
            img = item.select_one("img")

            if not link:
                continue

            href = link.get("href", "")
            subject_url = self._to_full_url(href)
            if not subject_url:
                continue

            img_src = img.get("src", "") if img else ""
            if img_src:
                img_src = img_src.replace("s_ratio_poster", "l_ratio_poster")

            return subject_url, img_src

        return None

    def _to_full_url(self, href: str) -> Optional[str]:
        """Convert /movie/subject/123/ → https://movie.douban.com/subject/123/"""
        m = re.match(r"/(movie|book|music)/subject/(\d+)/", href)
        if not m:
            return None
        category, subject_id = m.group(1), m.group(2)
        return f"https://{category}.douban.com/subject/{subject_id}/"
