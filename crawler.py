import asyncio
import httpx
from bs4 import BeautifulSoup
from models import ImageResult

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 15  # seconds
CONCURRENCY_LIMIT = 5
REQUEST_DELAY = 0.5  # seconds between requests


async def fetch_page(client: httpx.AsyncClient, url: str) -> str:
    response = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
    response.raise_for_status()
    return response.text


def extract_images(html: str, base_url: str, max_images: int) -> list[ImageResult]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for tag in soup.find_all("img", limit=max_images):
        src = tag.get("src") or tag.get("data-src")
        if not src:
            continue

        # Resolve relative URLs
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"

        width = tag.get("width")
        height = tag.get("height")

        results.append(ImageResult(
            url=src,
            alt=tag.get("alt"),
            width=int(width) if width and width.isdigit() else None,
            height=int(height) if height and height.isdigit() else None,
        ))

    return results


async def crawl(url: str, max_images: int) -> list[ImageResult]:
    await asyncio.sleep(REQUEST_DELAY)
    async with httpx.AsyncClient() as client:
        html = await fetch_page(client, url)
    return extract_images(html, base_url=url, max_images=max_images)
