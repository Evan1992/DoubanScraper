import logging
from typing import List
from models import ImageResult
from strategies import SearchStrategy, GeneralSearchStrategy, MovieSearchStrategy, MobileSearchStrategy

logger = logging.getLogger(__name__)

_STRATEGIES: List[SearchStrategy] = [
    GeneralSearchStrategy(),
    MobileSearchStrategy(),
    MovieSearchStrategy(),
]


async def crawl(name: str) -> List[ImageResult]:
    for strategy in _STRATEGIES:
        results = await strategy.search(name)
        if results:
            logger.info(f"Strategy succeeded: {type(strategy).__name__}")
            return results
    logger.warning("All search strategies exhausted, no results found")
    return []
