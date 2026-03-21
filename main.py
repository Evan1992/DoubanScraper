import logging
from fastapi import FastAPI, HTTPException
from models import CrawlRequest, CrawlResponse
from crawler import crawl

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="DoubanScraper", description="Image crawling microservice")


# async allows the handler to pause at `await` without blocking the server
@app.post("/crawl", response_model=CrawlResponse)
async def crawl_images(request: CrawlRequest):
    try:
        images = await crawl(request.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return CrawlResponse(images=images)


@app.get("/health")
async def health():
    return {"status": "ok"}
