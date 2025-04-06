
from backend.service.TradingViewScrapper import TradingViewScrapper
from backend.agents.news.SummaryAgent import SummaryAgent
from backend.agents.news.SynthesisAgent import SynthesisAgent
from typing import List, Dict

class NewsPipelie:

    def __init__(self, currency_pair: str, k: int = 5):
        self.currency_pair = currency_pair
        self.k = k
    
    def get_news(self) -> List[Dict]:

        tv_scrapper = TradingViewScrapper(self.currency_pair)
        links = tv_scrapper.get_news_websites()
        print("get news websites")
        tv_scrapper.quit_driver()
        news = tv_scrapper.get_news(links, self.k)
        return news

    def get_news_summary(self, news: List[Dict]):

        summary_agent = SummaryAgent(currency_pair=self.currency_pair)
        summaries = summary_agent.summarize_news(news)
        return summaries

    def synthesize_summary(self, summaries: List[Dict]):

        synthesis_agent = SynthesisAgent(currency_pair=self.currency_pair)
        synthesis = synthesis_agent.synthesize_summaries(summaries)
        return synthesis

    def run(self) -> str:
        news = self.get_news()
        print("get news content")
        summaries = self.get_news_summary(news)
        print("summarize news")
        synthesis = self.synthesize_summary(summaries)
        print("synthesize summary")
        return synthesis

if __name__ == "__main__":
    currency_pair = "USD/JPY"
    k = 5
    news_pipeline = NewsPipelie(currency_pair, k)
    synthesis = news_pipeline.run()
    print(synthesis)


    
