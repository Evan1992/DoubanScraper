# DoubanScraper Microservice Design

## Overview

A microservice that receives a crawl request, scrapes images from a target website, and returns image metadata to the client. The client is responsible for uploading images to the database.

## Architecture

```
Client → [POST /crawl] → Microservice → Scrape images → Return image list → Client → DB
```

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python | Best scraping ecosystem |
| Framework | FastAPI | Async-native, fast, auto-generated docs |
| HTTP client | httpx | Async HTTP requests |
| HTML parsing | BeautifulSoup4 | Extract `<img>` tags from HTML |
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
  "url": "https://example.com/page",
  "max_images": 50
}
```

### Response

```json
{
  "images": [
    {
      "url": "https://example.com/image.jpg",
      "alt": "description",
      "width": 800,
      "height": 600
    }
  ]
}
```

### What the service returns

The service returns **image URLs and metadata** rather than raw binary data. The client then decides whether to download and store the images, or just store the URLs. This keeps the microservice lightweight and stateless.

## Key Design Decisions

- **Return URLs, not binaries** — minimizes bandwidth and keeps the service simple
- **Async by default** — FastAPI + httpx handle concurrent requests efficiently
- **Stateless** — no internal state; each request is fully independent

## Constraints & Best Practices

- **Rate limiting** — add delays between requests to avoid hammering the target site
- **Robots.txt** — respect crawl rules of the target site
- **Timeouts** — set request timeouts to prevent hanging on slow sites
- **Concurrency** — use `asyncio.gather` with a semaphore when crawling multiple pages

## Project Structure

```
DoubanScraper/
├── main.py           # FastAPI app entry point
├── crawler.py        # Crawling and image extraction logic
├── models.py         # Pydantic request/response models
├── Dockerfile
└── requirements.txt
```
