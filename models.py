from pydantic import BaseModel, HttpUrl
from typing import Optional


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_images: int = 50


class ImageResult(BaseModel):
    url: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class CrawlResponse(BaseModel):
    images: list[ImageResult]
