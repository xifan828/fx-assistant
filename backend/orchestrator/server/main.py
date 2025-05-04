from backend.orchestrator.server.ScrapePipeline import ScrapePipeline
from backend.utils.parameters import CURRENCY_PAIRS, PAIRS
from backend.utils.logger_config import get_logger
from backend.orchestrator.server.NewsPipeline import NewsPipeline
import asyncio

def main():
    logger = get_logger(__name__)

    logger.info("Starting the scraping process")
    currency_pair = "EUR/USD"
    pipeline = ScrapePipeline(currency_pair)
    _ = pipeline.fetch_all()
    logger.info(f"Finished scraping")

    logger.info("Starting the news pipeline process")
    news_pipeline = NewsPipeline(k=7)
    asyncio.run(news_pipeline.run())
    logger.info("Finished the news pipeline process")

if __name__ == "__main__":
    main()