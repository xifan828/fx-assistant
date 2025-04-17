
from backend.utils.llm_helper import Config
from typing import List, Dict
from backend.utils.llm_helper import OpenAIClient
import asyncio

class SummaryAgent:

    summarize_system_template = """You are a {currency_pair} forex news analyst tasked with identifying the most important and relevant information from news articles that could impact the forex market. 
For each article you receive, extract the key information, insights, and opinions that a forex trader would find valuable.

Pay particular attention to:
- Information likely to influence {currency_pair} valuations.
- Expert opinions and analysis from finance industry professionals.
- Key data points and their potential implications.
- Shifts in market sentiment or risk appetite.

Be **concise** and focus on the most impactful information.
"""

    def __init__(self, currency_pair: str, model_name: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):
        self.currency_pair = currency_pair
        self.openai_client = OpenAIClient(model=model_name, temperature=temperature)
    
    async def summarize_news(self, news: List[Dict[str, str]]) -> List[Dict[str, str]]:


        system_message = self.summarize_system_template.format(currency_pair=self.currency_pair)

        tasks = {
            news_dict["url"]: self.openai_client.chat_completion(
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": news_dict["content"]}
                ]
            )
            for news_dict in news
        }

        responses = await asyncio.gather(*tasks.values())

        for nd, summary in zip(news, responses):
            nd["summary"] = summary
        return news


if __name__ == "__main__":

    from backend.service.TradingViewScrapper import TradingViewScrapper
    tv_scrapper = TradingViewScrapper("EUR/USD")
    news_links = tv_scrapper.get_news_websites()
    tv_scrapper.quit_driver()
    news = tv_scrapper.get_news(news_links, 5)

    news_agent = SummaryAgent("EUR/USD", model_name="gpt-4.1-mini-2025-04-14")
    news = asyncio.run(news_agent.summarize_news(news))

    for news_dict in news:
        print(news_dict["url"])
        print(news_dict["summary"])
        print("="*20)
        print("\n")

