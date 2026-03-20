from typing import List
from models import ImageResult
from strategies import SearchStrategy, GeneralSearchStrategy, MovieSearchStrategy

_STRATEGIES: List[SearchStrategy] = [
    GeneralSearchStrategy(),
    MovieSearchStrategy(),
]


async def crawl(name: str) -> List[ImageResult]:
    for strategy in _STRATEGIES:
        results = await strategy.search(name)
        if results:
            return results
    print("All search strategies exhausted, no results found")
    return []
