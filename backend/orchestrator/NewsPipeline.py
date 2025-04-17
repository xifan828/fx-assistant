from backend.service.TradingViewScrapper import TradingViewScrapper
from backend.agents.news.SummaryAgent import SummaryAgent
from backend.agents.news.SynthesisAgent import SynthesisAgent, NewsSynthesis
from typing import List, Dict
import logging
import asyncio

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NewsPipeline:

    def __init__(self, currency_pair: str, k: int = 5, summary_model : str = "gpt-4.1-mini-2025-04-14", synthesis_model: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):
        self.currency_pair = currency_pair
        self.k = k
        self.summary_model = summary_model
        self.synthesis_model = synthesis_model
        self.temperature = temperature
    
    def get_news(self) -> List[Dict]:
        logger.info(f"Fetching news for {self.currency_pair}")
        tv_scrapper = TradingViewScrapper(self.currency_pair)

        try:
            links = tv_scrapper.get_news_websites()
            logger.debug(f"News links fetched: {links}")
        except Exception as e:
            logger.error(f"Error getting news websites: {e}")
            raise
        finally:
            tv_scrapper.quit_driver()
            logger.info("Closed web driver")

        try:
            news = tv_scrapper.get_news(links, self.k)
            first_news_snapshot = news[0]["content"][:500]
            logger.info(f"Fetched {len(news)} news articles")
            logger.info(f"News 1: {first_news_snapshot}")
        except Exception as e:
            logger.error(f"Error getting news content: {e}")
            raise

        return news

    def get_news_summary(self, news: List[Dict]) -> List[Dict]:
        logger.info("Summarizing news articles")
        summary_agent = SummaryAgent(currency_pair=self.currency_pair, model_name=self.summary_model, temperature=self.temperature)
        summaries = asyncio.run(summary_agent.summarize_news(news))
        logger.debug(f"Summaries: {summaries}")
        return summaries

    def synthesize_summary(self, summaries: List[Dict]) -> NewsSynthesis:
        logger.info("Synthesizing summaries")
        synthesis_agent = SynthesisAgent(currency_pair=self.currency_pair, model_name=self.synthesis_model, temperature=self.temperature)
        synthesis = asyncio.run(synthesis_agent.synthesize_summaries(summaries))
        logger.debug(f"Synthesis result: {synthesis}")
        return synthesis

    def run(self) -> NewsSynthesis:
        try:
            news = self.get_news()
            summaries = self.get_news_summary(news)
            synthesis = self.synthesize_summary(summaries)
            logger.info("Pipeline completed successfully")
            return synthesis
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            raise

if __name__ == "__main__":
    currency_pair = "GBP/USD"
    k = 5
    news_pipeline = NewsPipeline(currency_pair, k)
    synthesis = news_pipeline.run()
    synthesis = synthesis.dict()
    for key, value in synthesis.items():
        print(f"{key}: {value}")
        print("="*20)
        print("\n")
    
