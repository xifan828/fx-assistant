from openai import OpenAI
from service.web_scrapping import TradingEconomicsScraper
from parameters import *
import asyncio

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
    Economic Indicators:
    ###
    {economic_indicators}
    ###

    Technical Analysis:
    ###
    {technical_analysis}
    ###

    Technical Indicator:
    ###
    {technical_indicator}
    ###

    central bank announcements:
    ###
    {central_bank}
    ###

    {question}"""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0):
        self.client = OpenAI()
        self.model_name = model_name
        self.temperature = temperature
    
    def run(self, messages):
        return self.chat_completions(messages)

    def formulate_first_round_messages(self, economic_indicators, technical_analysis, technical_indicator, central_bank, question):
        system_message = self.SYSTEM_MESSAGE
        user_message = self.USER_MESSAGE_TEMPLATE.format(
            economic_indicators = economic_indicators,
            technical_analysis = technical_analysis,
            technical_indicator = technical_indicator,
            central_bank = central_bank,
            question = question
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
    def __init__(self):
        pass

    def get_economic_indicators(self, websites: dict = ECONOMIC_INDICATORS_WEBSITES):
        te_scrapper = TradingEconomicsScraper()
        scrapped_content = asyncio.run(te_scrapper.scrape_websites(websites))
        return scrapped_content
    
    def get_technical_analysis(self, query: str, top_k : int = 10):

        pass
