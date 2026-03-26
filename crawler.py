import logging
from typing import List
from models import ImageResult
from strategies.base import SearchStrategy
from strategies.general import GeneralSearchStrategy
from strategies.mobile import MobileSearchStrategy
from strategies.movie import MovieSearchStrategy

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
