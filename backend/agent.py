from openai import OpenAI
from backend.utils.parameters import *
import asyncio
from typing import List, Dict, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from backend.models.data_model import TradingReasoning
from backend.orchestrator.RiskSentimentPipeline import RiskSentimentPipeline
from backend.orchestrator.NewsPipeline import NewsPipeline
from backend.orchestrator.TechnicalAnalysisPipeline import TechnicalAnalysisPipeline
from backend.utils.keep_time import time_it
from backend.utils.format_response import basemodel_to_md_str
import aiohttp

class FXAgent():
    SYSTEM_MESSAGE = """Objective:
    You are an assistant designed to analyze financial information relevant to the {currency_pair} exchange rate and provide informed trading strategies based on the analysis of various data sources.

    Functionality:
    1. Data Input:
    - The user will provide information from various categories such as recent financial news, technical analysis, risk sentiments. Each category of information is delimted with triple hashtags.
    2. Individual Source Analysis
    - For each piece of information provided, the assistant will analyze its relevance and potential impact on the {currency_pair} exchange rate.
    - The assistant should assess the reliability of the source and the current relevance of the information based on its date and context.
    - It should summarize the key points from the source, highlighting how they could influence the exchange rate.
    3. Cumulative Analysis:
    - After analyzing each individual source, the assistant should synthesize the findings to identify overarching trends or conflicting signals.
    - It should evaluate how the combination of all data sources influences the overall market outlook for the {currency_pair} exchange rate.
    4. Strategic Recommendation:
    - Based on the cumulative analysis, the assistant should formulate a trading strategy. This strategy could range from suggesting buying or selling, maintaining current positions, or suggesting further monitoring of specific indicators.
    - The strategy should include a rationale that ties back to the analyzed data, providing clear reasons for the recommended actions.
    5. User Interaction:
    - The assistant should interact in a clear, professional language suitable for financial advice.
    - It should be capable of handling follow-up questions where it can further clarify its analysis or the rationale behind its recommendations.
    """

    USER_MESSAGE_TEMPLATE = """
    - Most recent news:
    ###
    {news}
    ###

    - Technical Analysis:
    ###
    {technical_analysis}
    ###

    - Risk sentiment analysis:
    ###
    {risk_sentiment}
    ###
    """

    def __init__(self, currency_pair: str = "EUR/USD" ,model_name: str = "gpt-4o-mini", temperature: float = 1.0):
        self.client = OpenAI()
        self.model_name = model_name
        self.temperature = temperature
        self.currency_pair = currency_pair
    
    def run(self, messages):
        return self.chat_completions(messages)

    def formulate_first_round_messages(self, news, technical_analysis, sentiment_analysis):
        system_message = self.SYSTEM_MESSAGE.format(
            currency_pair = self.currency_pair
        )
        user_message = self.USER_MESSAGE_TEMPLATE.format(
            news = news,
            technical_analysis = technical_analysis,
            risk_sentiment = sentiment_analysis
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        return messages


    def chat_completions(self, messages):
        response = self.client.chat.completions.create(
            model = self.model_name,
            temperature= self.temperature,
            messages = messages
        )
        return response.choices[0].message.content



class KnowledgeBase:
    def __init__(self, currency_pair: str):
        load_dotenv()
        self.currency_pair = currency_pair
        self.currency_pair_formatted = currency_pair.replace("/", "_").lower()
        self.api_base_url = "http://3.107.188.19"
        
    async def get_news_synthesis(self):
        url = f"{self.api_base_url}/news_synthesis/{self.currency_pair_formatted}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch news synthesis for {self.currency_pair}. Status code: {response.status}")

    async def get_fedwatch_synthesis(self):
        url = f"{self.api_base_url}/fedwatch_synthesis"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch Fed watch synthesis for {self.currency_pair}. Status code: {response.status}")
    
    async def get_fundamental_synthesis(self):
        url = f"{self.api_base_url}/fundamental_synthesis/{self.currency_pair_formatted}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch fundamental synthesis for {self.currency_pair}. Status code: {response.status}")
    
    async def get_risk_sentiment_synthesis(self):
        url = f"{self.api_base_url}/risk_sentiment_synthesis/{self.currency_pair_formatted}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch risk sentiment synthesis for {self.currency_pair}. Status code: {response.status}")

    async def create_technical_analysis(self, interval: str = "1h", size: int = 48, analysis_types: List[str] = ["ema", "macd", "rsi", "atr"]):
        pipeline = TechnicalAnalysisPipeline(currency_pair=self.currency_pair, interval=interval, size=size, analysis_types=analysis_types)
        return await pipeline.run()
    
    @time_it
    async def get_all_synthesis(self):
        tasks = [
            self.get_news_synthesis(),
            self.get_risk_sentiment_synthesis(),
            self.get_fedwatch_synthesis(),
            self.get_fundamental_synthesis(),
            self.create_technical_analysis()
        ]
        results = await asyncio.gather(*tasks)
        return {
            "News Analysis": results[0],
            "Risk Sentiment": results[1],
            "Fed Watch": results[2],
            "Fundamental Analysis": results[3],
            "Technical Analysis": results[4]
        }

if __name__ == "__main__":
    kb = KnowledgeBase(
        #currency_pair="USD/JPY",
        currency_pair="GBP/USD"
    )
    # results = kb.create_all_analysis_parallel()
    # for k, v in results.items():
    #     print(f"{k}: {v}")

    result = asyncio.run(kb.get_all_synthesis())

    for k, v in result.items():
        print(k)
        print(v)
        print("\n" + "="*50 + "\n")



    


    


    
