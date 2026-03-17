# DoubanScraper Microservice Design

## Overview

A microservice that receives a search name, crawls Douban to find the most-reviewed matching title, and returns its cover image to the client. The client is responsible for uploading the image to the database.

## Architecture

```
Client → [POST /crawl] → Microservice → Search Douban → Pick top result → Fetch detail page → Return cover image → Client → DB
```

## Crawling Flow

**Primary (general search):**
1. Load `https://www.douban.com/search?q={name}` via Playwright (JS-rendered)
2. Parse `.DouWeb-SR-subject-card` cards; pick the one with the most reviews
3. If the card has no inline image, follow its link and extract `#mainpic` from the detail page
4. Return the large-format poster URL (`l_ratio_poster`)

**Fallback (movie-only search, no login required):**
1. If the general search returns an error 103 (login wall), load `https://movie.douban.com/subject_search?search_text={name}&cat=1002`
2. Parse `.item-root` cards; pick the one with the most reviews
3. Return the large-format poster URL directly (image is inline in results)

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python | Best scraping ecosystem |
| Framework | FastAPI | Async-native, fast, auto-generated docs |
| HTML parsing | BeautifulSoup4 | Extract tags from rendered HTML |
| JS rendering | Playwright | Douban search results are JavaScript-rendered; a real browser is required to get the populated DOM |
| Containerization | Docker | Portable, deployable anywhere |

## API Design

### Endpoint

```
POST /crawl
```

### Request Body

```json
{
  "name": "肖申克的救赎"
}
```

### Response

```json
{
  "images": [
    {
      "url": "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p xxx.jpg",
      "alt": "肖申克的救赎"
    }
  ]
}
```

Returns a single cover image (the main poster from the detail page).

### What the service returns

The service returns the **cover image URL and alt text** of the top-matched Douban title. The client downloads and stores the image. This keeps the microservice lightweight and stateless.

## Key Design Decisions

- **Single cover image** — only the main `#mainpic` image is returned, not all images on the page
- **Top result by review count** — picks the most-reviewed result from 相关书影音 to ensure relevance
- **Return URLs, not binaries** — minimizes bandwidth and keeps the service simple
- **Async by default** — FastAPI + Playwright async API handle concurrent requests efficiently
- **Stateless** — no internal state; each request is fully independent

## Constraints & Best Practices

- **Rate limiting** — 1s delay between requests to avoid hammering Douban
- **Timeouts** — 30s browser navigation timeout to handle slow page loads
- **Stealth** — browser launched with `--disable-blink-features=AutomationControlled` and `navigator.webdriver` masked to reduce bot detection

## Project Structure

```
DoubanScraper/
├── main.py           # FastAPI app entry point
├── crawler.py        # Crawling and image extraction logic
├── models.py         # Pydantic request/response models
├── Dockerfile
└── requirements.txt
```
