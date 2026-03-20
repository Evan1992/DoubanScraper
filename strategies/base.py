from abc import ABC, abstractmethod
from typing import List
from models import ImageResult


class SearchStrategy(ABC):
    @abstractmethod
    async def search(self, name: str) -> List[ImageResult]:
        ...
