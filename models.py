from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_images: int = 50


class ImageResult(BaseModel):
    url: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class CrawlResponse(BaseModel):
    images: List[ImageResult]
