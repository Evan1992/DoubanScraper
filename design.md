# DoubanScraper Microservice Design

## Overview

A microservice that receives a search name, crawls Douban to find the most-reviewed matching title, and returns its cover image to the client. The client is responsible for uploading the image to the database.

## Architecture

```
Client → [POST /crawl] → Microservice → Search Douban → Pick top result → Fetch detail page → Return cover image → Client → DB
```

## Crawling Flow

1. Search `https://www.douban.com/search?q={name}`
2. In 相关书影音, pick the result with the most reviews
3. Follow the link to its detail page
4. Extract the main cover image from `#mainpic`

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python | Best scraping ecosystem |
| Framework | FastAPI | Async-native, fast, auto-generated docs |
| HTTP client | httpx | Async HTTP requests |
| HTML parsing | BeautifulSoup4 | Extract tags from HTML |
| JS rendering | Playwright (optional) | For JavaScript-rendered pages |
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
- **Async by default** — FastAPI + httpx handle concurrent requests efficiently
- **Stateless** — no internal state; each request is fully independent

## Constraints & Best Practices

- **Rate limiting** — 0.5s delay between requests to avoid hammering Douban
- **Timeouts** — 15s request timeout to prevent hanging on slow responses

## Project Structure

```
DoubanScraper/
├── main.py           # FastAPI app entry point
├── crawler.py        # Crawling and image extraction logic
├── models.py         # Pydantic request/response models
├── Dockerfile
└── requirements.txt
```
