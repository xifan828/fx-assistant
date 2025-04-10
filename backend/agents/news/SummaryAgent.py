from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from backend.utils.llm_helper import Config
from backend.utils.keep_time import time_it
from typing import List, Dict

class SummaryAgent:

    summarize_system_template = """You are a {currency_pair} forex news analyst tasked with identifying the most important and relevant information from news articles that could impact the forex market. 
For each article you receive, extract the key information, insights, and opinions that a forex trader would find valuable.

Pay particular attention to:
- Information likely to influence {currency_pair} valuations.
- Expert opinions and analysis from finance industry professionals.
- Key data points and their potential implications.
- Shifts in market sentiment or risk appetite.

Be concise and focus on the most impactful information.
"""

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        self.summarize_llm = Config(model_name="gpt-4o-mini", temperature=0.2).get_model()
    
    @time_it    
    def summarize_news(self, news: List[Dict[str, str]]) -> List[Dict[str, str]]:
        user_prompt = """
         <content>
         {content}
         </content>"""

        prompt = ChatPromptTemplate.from_messages([
        ("system", self.summarize_system_template),
        ("user", user_prompt)])

        chain = prompt | self.summarize_llm | StrOutputParser()
        results = chain.batch([{"content": news_dict["content"], "currency_pair": self.currency_pair} for news_dict in news])

        for i, news_dict in enumerate(news):
            news_dict["summary"] = results[i]

        return news


if __name__ == "__main__":

    from backend.service.TradingViewScrapper import TradingViewScrapper
    tv_scrapper = TradingViewScrapper("EUR/USD")
    news_links = tv_scrapper.get_news_websites()
    tv_scrapper.quit_driver()
    news = tv_scrapper.get_news(news_links, 5)

    news_agent = SummaryAgent("EUR/USD")
    news = news_agent.summarize_news(news)

    for news_dict in news:
        print(news_dict["url"])
        print(news_dict["summary"])
        print("="*20)
        print("\n")

