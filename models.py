from pydantic import BaseModel
from typing import Optional, List


class CrawlRequest(BaseModel):
    name: str


class ImageResult(BaseModel):
    url: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    referer: Optional[str] = None  # Required as Referer header when fetching the image


class CrawlResponse(BaseModel):
    images: List[ImageResult]
