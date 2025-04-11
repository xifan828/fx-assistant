from backend.service.InvestingScrapper import InvestingScrapper
from backend.agents.sentiment.RiskSentimentAgent import RiskSentimentAgent
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

class RiskSentimentPipeline:
    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
    
    def get_assets_data(self) -> str:
        scrapper = InvestingScrapper(self.currency_pair)
        return scrapper.get_all_assets()

    def analyze_sentiment(self, assets_data: str):
        agent = RiskSentimentAgent(currency_pair=self.currency_pair)
        analysis = agent.analyze_assets(assets_data=assets_data)
        return analysis
    
    def run(self):
        logger.info("Running Risk Sentiment Pipeline")
        assets_data = self.get_assets_data()
        logger.info("Assets data fetched successfully")
        analysis = self.analyze_sentiment(assets_data=assets_data)
        return analysis
    

if __name__ == "__main__":
    pipeline = RiskSentimentPipeline(currency_pair="USD/JPY")
    analysis = pipeline.run()
    print(analysis)