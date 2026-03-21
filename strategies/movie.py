import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from models import ImageResult
from fetch import fetch
from strategies.base import SearchStrategy

logger = logging.getLogger(__name__)


class MovieSearchStrategy(SearchStrategy):
    """Fallback: movie.douban.com/subject_search (no login required, image inline)."""

    def _extract_top_result(self, html: str) -> Optional[Tuple[str, str, int]]:
        """Returns (subject_url, image_url, review_count) or None."""
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

    async def search(self, name: str) -> List[ImageResult]:
        url = "https://movie.douban.com/subject_search?" + urlencode({
            "search_text": name,
            "cat": "1002",
        })
        logger.info(f"Trying movie search: {url}")
        html = await fetch(url)

        result = self._extract_top_result(html)
        if not result:
            return []

        subject_url, img_src, count = result
        logger.info(f"Movie search succeeded: {subject_url} ({count} reviews)")
        return [ImageResult(url=img_src, referer=subject_url)]
