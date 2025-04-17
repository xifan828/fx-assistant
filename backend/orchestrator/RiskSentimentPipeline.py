from backend.service.InvestingScrapper import InvestingScrapper
from backend.agents.sentiment.RiskSentimentAgent import RiskSentimentAgent, RiskSentimentAnalysis
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

class RiskSentimentPipeline:
    def __init__(self, currency_pair: str, model_name: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):
        self.currency_pair = currency_pair
        self.model_name = model_name
        self.temperature = temperature
    
    def get_assets_data(self) -> str:
        scrapper = InvestingScrapper(self.currency_pair)
        return scrapper.get_all_assets()

    def analyze_sentiment(self, assets_data: str, news_summary: str) -> RiskSentimentAnalysis:
        agent = RiskSentimentAgent(currency_pair=self.currency_pair, model_name=self.model_name, temperature=self.temperature)
        analysis = agent.analyze_risk_sentiment(assets_data=assets_data, news_summary=news_summary)
        return analysis
    
    def run(self, news_summary: str) -> RiskSentimentAnalysis:
        logger.info("Running Risk Sentiment Pipeline")
        assets_data = self.get_assets_data()
        logger.info("Assets data fetched successfully")
        analysis = self.analyze_sentiment(assets_data=assets_data, news_summary=news_summary)
        logger.info("Sentiment analysis completed")
        return analysis
    

if __name__ == "__main__":
    from backend.orchestrator.NewsPipeline import NewsPipeline
    from backend.utils.format_response import basemodel_to_md_str

    currency_pair = "EUR/USD"
    news_pipeline = NewsPipeline(currency_pair=currency_pair, k=5)
    news_synthesis = news_pipeline.run()
    news_synthesis_str = basemodel_to_md_str(news_synthesis)

    risk_pipeline = RiskSentimentPipeline(currency_pair=currency_pair)
    risk_analysis = risk_pipeline.run(news_synthesis_str)
    risk_analysis_str = basemodel_to_md_str(risk_analysis)
    print(risk_analysis_str)