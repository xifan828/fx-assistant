from typing import List, Dict
from backend.utils.llm_helper import OpenAIClient
import asyncio
import re
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

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
    
    def extract_content_from_mace_url(self, url: str) -> str:
        elements = url.split(";")
        print(elements)
        contents = []
        for element in elements:
            match = re.search(r":0-(.+?)/?$", element)
            if match:
                content = match.group(1).replace("-", " ")
            else:
                content = element
            contents.append(content)
        return "\n".join(contents)

    async def run(self, content: str) -> str:

        if "macenews" in content:
            content = self.extract_content_from_mace_url(content)
            response = "Mace flash news:\n" + content
        else:
            system_message = self.summarize_system_template.format(currency_pair=self.currency_pair)
            response = await self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": content}
                ]
            )
        logger.info(f"Summarized news for {self.currency_pair}")
        return response


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

    url = "https://www.tradingview.com/news/macenews:804d5dd87094b:0-fed-s-financial-stability-report-in-survey-before-april-2-potential-near-term-risks-were-global-trade-policy-uncertainty-fiscal-debt/;https://www.tradingview.com/news/macenews:8d02f9e25094b:0-fed-s-financial-stability-report-funding-risks-have-declined-over-the-course-of-the-past-yr-to-a-moderate-level-in-line-historically/;"

    agent = SummaryAgent(currency_pair="EUR/USD")
    print(agent.extract_content_from_mace_url(url))


