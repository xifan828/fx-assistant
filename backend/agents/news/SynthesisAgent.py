from backend.utils.llm_helper import OpenAIClient
from backend.utils.keep_time import time_it
from typing import List, Dict
from pydantic import BaseModel, Field

class NewsSynthesis(BaseModel):
    recurring_themes: str = Field(..., description="Recurring themes and narratives across the articles.")
    market_sentiment: str = Field(..., description="Overall market sentiment, **giving weight to the opinions expressed by finance professionals.**")
    major_factors: str = Field(..., description="Major factors currently influencing currency movements, **especially as highlighted by industry experts.**")
    conflicting_information: str = Field(..., description="Conflicting information or differing perspectives presented in the articles, **including any disagreements among industry commentators.**")
    short_medium_term_outlook: str = Field(..., description="Potential short-term and medium-term outlook for the forex market based on the news.")
    summary: str = Field(..., description="**Concise** and insightful summary that is valuable for forex traders. Maximum 3 sentences.")

class SynthesisAgent:

    synthesis_system_template = """You are a highly skilled {currency_pair} forex market analyst specializing in synthesizing information from multiple news articles to provide a comprehensive market overview. 
Your primary input is a collection of key information extractions from recent news articles, each analyzed by another agent. 
Your goal is to synthesize these individual extractions into a cohesive summary that identifies the key drivers and themes impacting the {currency_pair} market, **paying particular attention to the opinions and insights shared by finance industry professionals**."""

    def __init__(self, currency_pair: str, model_name: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):

        self.currency_pair = currency_pair
        self.openai_client = OpenAIClient(model=model_name, temperature=temperature)
    
    def _format_summaries(self, news: List[Dict[str, str]]) -> str:
        formatted_summaries = []
        for article in news:
            url = article.get("url", "No url")
            summary = article.get("summary", "No Summary")
            formatted_summaries.append(f"```\nUrl: {url}\nSummary: {summary}\n```")
        return "\n".join(formatted_summaries)
    
    async def synthesize_summaries(self, news: List[Dict[str, str]]) -> NewsSynthesis:

        formatted_summaries = self._format_summaries(news)

        messages = [
            {"role": "system", "content": self.synthesis_system_template.format(currency_pair=self.currency_pair)},
            {"role": "user", "content": formatted_summaries}

        ]

        synthesis = await self.openai_client.structured_chat_completion(messages=messages, response_format=NewsSynthesis)

        return synthesis