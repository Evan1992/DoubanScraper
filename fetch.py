from playwright.async_api import async_playwright

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


async def stealth_page(browser):
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


async def fetch(url: str, wait_until: str = "networkidle") -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=STEALTH_ARGS)
        page = await stealth_page(browser)
        await page.goto(url, wait_until=wait_until, timeout=30000)
        html = await page.content()
        await browser.close()
    return html
