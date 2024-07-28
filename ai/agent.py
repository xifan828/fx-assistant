from openai import OpenAI
from ai.service.web_scrapping import TradingEconomicsScraper, TechnicalNewsScrapper
from ai.service.web_scrapping_image import scrape_pair_overview
from ai.service.technical_analysis import TechnicalAnalysis
from ai.service.ai_search import PerplexitySearch
from ai.service.central_banks import ECB, FED
from ai.parameters import *
from ai.config import Config
import asyncio
from typing import List, Dict
import time
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from concurrent.futures import ThreadPoolExecutor, as_completed


class FXAgent():
    SYSTEM_MESSAGE = """Objective:
    You are an assistant designed to analyze financial information relevant to the eur/usd exchange rate and provide informed trading strategies based on the analysis of various data sources.

    Functionality:
    1. Data Input:
    - The user will provide information from various categories such as economic indicators, market sentiment, political events, central bank announcements, and financial news. Each category of information is delimted with triple hashtags.
    2. Individual Source Analysis
    - For each piece of information provided, the assistant will analyze its relevance and potential impact on the eur/usd exchange rate.
    - The assistant should assess the reliability of the source and the current relevance of the information based on its date and context.
    - It should summarize the key points from the source, highlighting how they could influence the exchange rate.
    3. Cumulative Analysis:
    - After analyzing each individual source, the assistant should synthesize the findings to identify overarching trends or conflicting signals.
    - It should evaluate how the combination of all data sources influences the overall market outlook for the eur/usd exchange rate.
    4. Strategic Recommendation:
    - Based on the cumulative analysis, the assistant should formulate a trading strategy. This strategy could range from suggesting buying or selling EUR/USD, maintaining current positions, or suggesting further monitoring of specific indicators.
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
    """

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 1.0):
        self.client = OpenAI()
        self.model_name = model_name
        self.temperature = temperature
    
    def run(self, messages):
        return self.chat_completions(messages)

    def formulate_first_round_messages(self, economic_indicators, technical_news, technical_analysis, central_bank):
        system_message = self.SYSTEM_MESSAGE
        user_message = self.USER_MESSAGE_TEMPLATE.format(
            economic_indicators = economic_indicators,
            technical_news = technical_news,
            technical_analysis = technical_analysis,
            central_bank = central_bank,
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

class TradingStrategy(BaseModel):
    """Trading strategy output format"""

    strtegy: str = Field(description="Shall be either long, short or hold. If hold, leave the Fields `entry_point`, `exit_point`, `stop_loss_point` as 0.")
    entry_point: float = Field()
    exit_point: float = Field()
    stop_loss_point: float = Field()
    rationale: str = Field(description="The rationale behind this trade strategy.")

class StrtegyAgent:
    SYSTEM_MESSAGE = """You are an experienced Forex trader specializing in the EUR/USD currency pair. Your expertise lies in analyzing diverse information sources and developing profitable trading strategies. Your role is to:
1. Read information from multiple sources
2. Analyze the collected information to identify potential trading opportunities.
3. Develop and propose trading strategies based on your analysis. These strategies should include: 
    - Entry and exit points
    - Stop-loss and take-profit levels
    - Rationale 
Your goal is to provide actionable trading advice that, if implemented, would result in profitable trades. And you will be rewarded with half of the profits generated.
Wrap your output in `json` tags
{format_instructions}
Output nothing except the json tags.
"""

    USER_MESSAGE_TEMPLATE = """Below are collected information. Make a trading strategy the best you can. 
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
    ###"""
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 1.0):
        self.model_name = model_name
        self.temperature = temperature
    
    def generate_strategy(self, economic_indicators, technical_analysis, technical_news, central_bank):
        model = Config(model_name=self.model_name, temperature=self.temperature).get_model()
        parser = PydanticOutputParser(pydantic_object=TradingStrategy)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_MESSAGE),
            ("user", self.USER_MESSAGE_TEMPLATE)
        ]).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | model | StrOutputParser()
        response = chain.invoke({"economic_indicators": economic_indicators, "technical_news": technical_news, "technical_analysis": technical_analysis, "central_bank": central_bank}).strip("```json").strip("```").strip()
        return response
    

class KnowledgeBase:
    def __init__(self, economic_indicators_websites: Dict = None, technical_analysis_root_website: str = None, ai_search_queries: List[str] = None):
        self.economic_indicators_websites = economic_indicators_websites if economic_indicators_websites is not None else ECONOMIC_INDICATORS_WEBSITES
        self.technical_analysis_root_website = technical_analysis_root_website if technical_analysis_root_website is not None else TECHNICAL_ANALYSIS_ROOT_WEBSITE
        #self.ai_search_queries = ai_search_queries if ai_search_queries is not None else AI_SEARCH_QUERIES

    def get_economic_indicators(self) -> Dict:
        te_scrapper = TradingEconomicsScraper()
        scrapped_content = asyncio.run(te_scrapper.scrape_websites(self.economic_indicators_websites))
        return scrapped_content
    
    def get_technical_news(self) -> List[Dict]:
        te_scrapper = TechnicalNewsScrapper(root_page_url=self.technical_analysis_root_website, top_k=10)
        results = te_scrapper.scrape_news()
        return results
    
    def get_technical_analysis(self, is_local: bool = False) -> str:
        scrape_pair_overview(is_local)
        ta_scrapper = TechnicalAnalysis()
        results = ta_scrapper.run()
        return results
    
    def get_central_bank(self) -> List[str]:
        # ai_search = PerplexitySearch()
        # results = asyncio.run(ai_search.multiple_search(self.ai_search_queries))
        ecb = ECB()
        fed = FED()
        ecb_results = ecb.run()
        fed_results = fed.run()
        results = f"""# European Central Bank
{ecb_results['date']}
## Statement
{ecb_results['statement']}
## Statement with Q & A
{ecb_results['qa']}
# Federal Reserve System US
{fed_results['date']}
## Statement
{fed_results['statement']}
## Minutes
{fed_results['minutes']}
"""
        return results

    def get_all_data(self, is_local: bool = False):
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_data = {
                executor.submit(self.get_economic_indicators): "Economic Indicators",
                executor.submit(self.get_technical_news): "Technical News",
                executor.submit(self.get_technical_analysis, is_local): "Technical Analysis",
                executor.submit(self.get_central_bank): "Central Bank"
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
    kb = KnowledgeBase()
    kb.get_technical_analysis(is_local=True)
    #print(kb.get_all_data(is_local=True))


    


    
