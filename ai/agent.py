from openai import OpenAI
from ai.service.web_scrapping import TradingEconomicsScraper, TechnicalNewsScrapper
from ai.service.web_scrapping_image import scrape_economic_calenders, scrape_technical_indicators, scrape_aastocks_chart
from ai.service.technical_analysis import TechnicalAnalysis
from ai.service.technical_indicators import TechnicalIndicators
from ai.service.economic_calenders import EconomicCalenders
from ai.parameters import *
from ai.config import Config
import asyncio
from typing import List, Dict, Literal
from langchain_core.pydantic_v1 import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from ai.models.data_model import TradingReasoning
import os

class FXAgent():
    SYSTEM_MESSAGE = """Objective:
    You are an assistant designed to analyze financial information relevant to the {currency_pair} exchange rate and provide informed trading strategies based on the analysis of various data sources.

    Functionality:
    1. Data Input:
    - The user will provide information from various categories such as economic indicators, recent financial news, technical analysis, central bank announcements, and economic events. Each category of information is delimted with triple hashtags.
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
    - Economic Indicators:
    ###
    {economic_indicators}
    ###

    - Most recent news:
    ###
    {technical_news}
    ###

    - Technical Indicator:
    ###
    {technical_analysis}
    ###

    - Central bank announcements:
    ###
    {central_bank}
    ###

    - Economic Events:
    {economic_events}
    """

    def __init__(self, currency_pair: str = "EUR/USD" ,model_name: str = "gpt-4o-mini", temperature: float = 1.0):
        self.client = OpenAI()
        self.model_name = model_name
        self.temperature = temperature
        self.currency_pair = currency_pair
    
    def run(self, messages):
        return self.chat_completions(messages)

    def formulate_first_round_messages(self, economic_indicators, technical_news, technical_analysis, central_bank, economic_events):
        system_message = self.SYSTEM_MESSAGE.format(
            currency_pair = self.currency_pair
        )
        user_message = self.USER_MESSAGE_TEMPLATE.format(
            economic_indicators = economic_indicators,
            technical_news = technical_news,
            technical_analysis = technical_analysis,
            central_bank = central_bank,
            economic_events = economic_events
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

# class NaiveStrategyAgent:
#     def __init__(self, knowledge: dict, model_name: str = "gpt-4o", temperature: float = 1.0, currency_pair: str = "EUR/USD"):
#         self.model_name = model_name
#         self.temperature = temperature
#         self.currency_pair = currency_pair
#         self.knowledege = knowledge
#         self.system_message = f"""You are a seasoned Forex trader specializing in the {self.currency_pair} currency pair. Your expertise lies in analyzing diverse information sources and developing profitable trading strategies. 
# Your should read information from multiple sources and analyze the collected information to identify potential trading opportunities.
# Your goal will be to propose profitable trading strategies following the schema provided.
# Here is a description of the parameters:
# - rationale: A short rationale behind this trade strategy.
# - strategy: sell, buy
# - entry_point: entry price of the trade
# - take_profit: exit price when taking profit
# - stop_loss: exit price when cutting loss
# - confidence_score: how confident is this trading strategy based on current market situation. Score should be integer from 1 to 5, with 1 being the lowest and 5 being the highest.
# You will be rewarded with 100 % of the profits generated."""
#         self.user_message_template = """Below are collected information. Make a trading strategy the best you can. 
# - Economic Indicators:
# ###
# {economic_indicators}
# ###

# - Most recent news:
# ###
# {technical_news}
# ###

# - Central bank announcements:
# ###
# {central_bank}
# ###

# - Technical analysis:
# ###
# {technical_analysis}
# ###

# - Economic Events:
# ###
# {economic_events}
# ###
# """
#     def generate_strategy(self):
#         load_dotenv()
#         client = OpenAI()
#         messages = [
#             {"role": "system", "content": self.system_message},
#             {"role": "user", "content": self.user_message_template.format(
#                 economic_indicators = self.knowledege["Economic Indicators"],
#                 technical_news = self.knowledege["Technical News"],
#                 central_bank = self.knowledege["Central Bank"],
#                 technical_analysis = self.knowledege["Technical Analysis"],
#                 economic_events = self.knowledege["Economic Events"]
#             )}
#         ]
#         completion = client.beta.chat.completions.parse(
#         model=self.model_name,
#         messages=messages,
#         response_format=TradingStrategy,
#         )

#         strategy = completion.choices[0].message.parsed
#         return strategy

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
    def __init__(self, currency_pair : str = "EUR/USD", economic_indicators_websites: Dict = None, news_root_website: str = None, technical_indicators_websites: Dict = None, currency_tickers: Dict = None, central_banks : Dict = None):
        self.economic_indicators_websites = economic_indicators_websites if economic_indicators_websites is not None else ECONOMIC_INDICATORS_WEBSITES
        self.news_root_website = news_root_website if news_root_website is not None else NEWS_ROOT_WEBSITE
        self.technical_indicators_websites = technical_indicators_websites if technical_indicators_websites is not None else TECHNICAL_INDICATORS_WEBSITES
        self.currency_tickers = currency_tickers if currency_tickers is not None else CURRENCY_TICKERS
        self.central_banks = central_banks if central_banks is not None else CENTRAL_BANKS
        self.currency_pair = currency_pair
        self.currency_a = currency_pair.split("/")[0]
        self.currency_b = currency_pair.split("/")[-1]
        self.currency_ticker = self.currency_tickers[self.currency_pair]
    
    def prepare_figures(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_data = {
            executor.submit(scrape_economic_calenders, calender_url=self.technical_indicators_websites[self.currency_pair]["calender"]): "Economic Calenders",
            executor.submit(scrape_technical_indicators, indicator_url=self.technical_indicators_websites[self.currency_pair]["indicator"]): "Technical Indicators",
            }
            for future in as_completed(future_to_data):
                data_name = future_to_data[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f'{data_name} generated an exception: {exc}')
        # scrape_economic_calenders(
        #     calender_url=self.technical_indicators_websites[self.currency_pair]["calender"]
        # )
        # scrape_technical_indicators(
        # indicator_url=self.technical_indicators_websites[self.currency_pair]["indicator"]
        # )
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="4h")
        ti.run()
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="1h")
        ti.run()
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="15min")
        ti.run()

    def get_economic_indicators(self) -> Dict:
        te_scrapper = TradingEconomicsScraper()
        websites = {**self.economic_indicators_websites[self.currency_a], **self.economic_indicators_websites[self.currency_b]}
        scrapped_content = asyncio.run(te_scrapper.scrape_websites(websites))
        return scrapped_content
    
    def get_news(self) -> List[Dict]:
        website = self.news_root_website[self.currency_pair]
        te_scrapper = TechnicalNewsScrapper(root_page_url=website, top_k=10, currency_pair=self.currency_pair)
        results = te_scrapper.scrape_news()
        return results
    
    def get_technical_analysis(self) -> str:
        ta_scrapper = TechnicalAnalysis(
        currency_pair=self.currency_pair,
        ticker=self.currency_ticker
        )
        results = asyncio.run(ta_scrapper.run())
        return results
    
    def get_central_bank(self) -> List[str]:
        bank_a = self.central_banks[self.currency_a]
        bank_b = self.central_banks[self.currency_b]
        bank_a_results = bank_a.run()
        bank_b_results = bank_b.run()
        results = f"{bank_a_results}\n\n{bank_b_results}"
        return results
    
    def get_economic_events(self) -> str:
        ec = EconomicCalenders(currency_pair=self.currency_pair)
        results = ec.run()
        return results
    
    def get_all_data(self):
        self.prepare_figures()
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_data = {
                executor.submit(self.get_economic_indicators): "Economic Indicators",
                executor.submit(self.get_news): "Technical News",
                executor.submit(self.get_technical_analysis): "Technical Analysis",
                executor.submit(self.get_central_bank): "Central Bank",
                executor.submit(self.get_economic_events): "Economic Events"
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
    
    def get_partial_data(self):
        self.prepare_figures()
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_data = {
                #executor.submit(self.get_economic_indicators): "Economic Indicators",
                executor.submit(self.get_news): "Technical News",
                executor.submit(self.get_technical_analysis): "Technical Analysis",
                #executor.submit(self.get_central_bank): "Central Bank",
                executor.submit(self.get_economic_events): "Economic Events"
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

if __name__ == "__main__":
    kb = KnowledgeBase(
        #currency_pair="USD/JPY",
        currency_pair="EUR/USD"
    )
    kb.prepare_figures()
    # knowledge = kb.get_partial_data()   
    # print(knowledge)




    


    


    
