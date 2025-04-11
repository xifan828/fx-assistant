from openai import OpenAI
from backend.utils.parameters import *
import asyncio
from typing import List, Dict, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from backend.models.data_model import TradingReasoning
import os
from backend.orchestrator.RiskSentimentPipeline import RiskSentimentPipeline
from backend.orchestrator.NewsPipeline import NewsPipeline
from backend.orchestrator.TechnicalAnalysisPipeline import TechnicalAnalysisPipeline
from backend.utils.keep_time import time_it

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

class NaiveStrategyAgent:
    def __init__(self, knowledge: dict, provider: Literal["openai", "google"] = "openai", model_name: str = "gpt-4o", temperature: float = 0.5, currency_pair: str = "EUR/USD"):
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.currency_pair = currency_pair
        self.knowledege = knowledge
#         self.system_message = f"""You are a seasoned daily self-employed Forex trader specializing in the {self.currency_pair} currency pair. Your excel in analyzing diverse information sources and developing profitable trading strategies. 
# Your goal is to propose profitable trading strategy based on user provided information. Think step by step before you create the final strategy.
# """     
        self.system_message = f"""You are a highly experienced and methodical self-employed Forex trader specializing in the {self.currency_pair} currency pair. Your expertise lies in developing well-reasoned and profitable trading strategies based on a comprehensive analysis of technical indicators, recent news, and upcoming economic events.

Your process involves a step-by-step analysis of the provided information to formulate a trading strategy. For each step, explicitly state the information you are considering and how it influences your understanding of the market.

**Crucially, consider the following in your analysis:**

* **Technical Analysis:** Identify key trends, support and resistance levels, and potential entry/exit points suggested by the technical analysis.
* **Recent News:** Analyze the sentiment and potential impact of recent news articles on the {self.currency_pair}. Consider both bullish and bearish implications.
* **Economic Events:**  Evaluate how upcoming or recent economic events might affect volatility and the direction of the {self.currency_pair}.

**Your goal is to propose a specific trading strategy (buy, sell or wait) with clearly defined entry point, take profit, stop loss, and a confidence score reflecting your assessment of the strategy's potential.** Explain the rationale behind each element of your strategy.
If the strategy is wait, fill entry point, take profit, stop loss and confidence score with None.

Think carefully and methodically before finalizing your strategy. Ensure all aspects of the provided information are considered in your reasoning.
"""
        self.user_message = f"""Below is information collected for the {self.currency_pair} currency pair. Develop a detailed trading strategy based on this information.
Recent news
<Recent news>
{knowledge["Technical News"]}
</Recent news>

Technical analysis
<Technical analysis>
{knowledge["Technical Analysis"]}
</Technical analysis>

Economic Events
<Economic Events>
{knowledge["Economic Events"]}
</Economic Events>
"""
    def generate_strategy(self):
        if self.provider == "openai":
            load_dotenv()
            client = OpenAI()
        elif self.provider == "google":
            client = OpenAI(
                api_key=os.environ["GEMINI_API_KEY_CONG"],
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.user_message}
        ]
        completion = client.beta.chat.completions.parse(
        model=self.model_name,
        temperature=self.temperature,
        messages=messages,
        response_format=TradingReasoning,
        )

        strategy = completion.choices[0].message.parsed
        return strategy

class KnowledgeBase:
    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        
    
    def create_risk_sentiment_analysis(self):
        pipeline = RiskSentimentPipeline(currency_pair=self.currency_pair)
        return pipeline.run()
    
    def create_news_analysis(self, k: int = 5):
        pipeline = NewsPipelie(currency_pair=self.currency_pair, k=k)
        return pipeline.run()
    
    def create_technical_analysis(self, interval: str = "1h", size: int = 48, analysis_types: List[str] = ["ema", "macd", "rsi", "atr"]):
        pipeline = TechnicalAnalysisPipeline(currency_pair=self.currency_pair, interval=interval, size=size, analysis_types=analysis_types)
        return asyncio.run(pipeline.run())
    
    @time_it
    def create_all_analysis_parallel(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_data = {
                #executor.submit(self.create_risk_sentiment_analysis): "Risk Sentiment",
                executor.submit(self.create_news_analysis): "News Analysis",
                executor.submit(self.create_technical_analysis): "Technical Analysis"
            }
            
            results = {}
            for future in as_completed(future_to_data):
                data_name = future_to_data[future]
                try:
                    results[data_name] = future.result()
                except Exception as exc:
                    print(f'{data_name} generated an exception: {exc}')
                    results[data_name] = None
            
            return results
    
    @time_it
    def create_all_analysis(self):
        risk_sentiment = self.create_risk_sentiment_analysis()
        news_analysis = self.create_news_analysis()
        technical_analysis = self.create_technical_analysis()
        return {
            "Risk Sentiment": risk_sentiment,
            "News Analysis": news_analysis,
            "Technical Analysis": technical_analysis
        }

if __name__ == "__main__":
    kb = KnowledgeBase(
        #currency_pair="USD/JPY",
        currency_pair="EUR/USD"
    )
    results = kb.create_all_analysis_parallel()
    for k, v in results.items():
        print(f"{k}: {v}")



    


    


    
