from backend.orchestrator.server.ScrapePipeline import ScrapePipeline
from backend.utils.parameters import CURRENCY_PAIRS, PAIRS
from backend.utils.logger_config import get_logger
from backend.orchestrator.server.NewsPipeline import NewsPipeline
from backend.orchestrator.server.RiskSentimentPipeline import RiskSentimentPipeline
from backend.orchestrator.server.CalenderPipeline import CalenderPipeline
from backend.orchestrator.server.FundamentalPipeline import FundamentalPipeline
from backend.orchestrator.server.FedWatchPipeline import FedWatchPipeline
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()

    logger = get_logger(__name__)

    # logger.info("Starting the scraping pipeline")
    # currency_pair = "EUR/USD"
    # pipeline = ScrapePipeline(currency_pair)
    # _ = pipeline.fetch_all()
    # logger.info(f"Finished scraping pipeline")

    logger.info("Starting the news pipeline")
    news_pipeline = NewsPipeline(k=7)
    await news_pipeline.run()
    logger.info("Finished the news pipeline")

    logger.info("Starting the risk sentiment, calender, fedwatch and fundamental pipeline")
    risk_sentiment_pipeline = RiskSentimentPipeline()
    calender_pipeline = CalenderPipeline()
    fund_pipeline = FundamentalPipeline()
    fed_watch_pipeline = FedWatchPipeline()
    tasks = [
        risk_sentiment_pipeline.run(),
        calender_pipeline.run(),
        fund_pipeline.run(),
        fed_watch_pipeline.run()
    ]
    await asyncio.gather(*tasks)
    logger.info("Finished the risk sentiment, calender, fedwatch and fundamental pipeline")



if __name__ == "__main__":
    
    asyncio.run(main())