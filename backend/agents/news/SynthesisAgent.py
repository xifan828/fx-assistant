from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.utils.llm_helper import Config
from backend.utils.keep_time import time_it
from typing import List, Dict

class SynthesisAgent:

    synthesis_system_template = """You are a highly skilled {currency_pair} forex market analyst specializing in synthesizing information from multiple news articles to provide a comprehensive market overview. 
Your primary input is a collection of key information extractions from recent news articles, each analyzed by another agent. 
Your goal is to synthesize these individual extractions into a cohesive summary that identifies the key drivers and themes impacting the {currency_pair} market, **paying particular attention to the opinions and insights shared by finance industry professionals**. Focus on:

- Identifying recurring themes and narratives across the articles.
- Determining the overall market sentiment, **giving weight to the opinions expressed by finance professionals**.
- Identifying the major factors currently influencing currency movements, **especially as highlighted by industry experts**.
- Highlighting any conflicting information or differing perspectives presented in the articles, **including any disagreements among industry commentators**.
- Assessing the potential short-term and medium-term outlook for the forex market based on the news, **considering the forecasts and expectations shared by experts**.

Provide a concise and insightful synthesis that is valuable for forex traders."""

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        self.sysnthesis_llm = Config(model_name="gpt-4o", temperature=0.2).get_model()
    
    def _format_summaries(self, news: List[Dict[str, str]]) -> str:
        formatted_summaries = []
        for article in news:
            url = article.get("url", "No url")
            summary = article.get("summary", "No Summary")
            formatted_summaries.append(f"```\nUrl: {url}\nSummary: {summary}\n```")
        return "\n".join(formatted_summaries)
    
    def synthesize_summaries(self, news: List[Dict[str, str]]) -> str:

        formatted_summaries = self._format_summaries(news)

        user_prompt = """
         <news summaries>
         {summaries}
         </news summaries>"""

        prompt = ChatPromptTemplate.from_messages([
        ("system", self.synthesis_system_template),
        ("user", user_prompt)])

        chain = prompt | self.sysnthesis_llm | StrOutputParser()

        synthesis = chain.invoke({"summaries": formatted_summaries, "currency_pair": self.currency_pair})

        return synthesis