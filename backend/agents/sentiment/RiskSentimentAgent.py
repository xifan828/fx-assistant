from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.utils.llm_helper import Config
from typing import List, Dict

class RiskSentimentAgent:

    sentiment_system_prompt_template = """You are a financial market analyst specializing in foreign exchange (FX). 
    You will be given various assets data.
    Your task is to:
    - Assess Overall Risk Sentiment
        - Examine global equity indices (S&P 500, Nasdaq, STOXX50, MSCI EM) to determine whether the market is risk-on or risk-off.
        - Consider commodity prices (Gold, Brent Oil) and their impact on risk sentiment.
        - Analyze changes in bond yields and yield spreads to gauge interest-rate differentials and policy expectations.

    - Identify Key Market Drivers
        - Discuss which indicators (equities, yields, commodity prices, currency pairs) appear to be the primary forces shaping the current market environment.
    
    - Implications for {currency_pair} Trading
        - Explain how the observed risk sentiment and yield spreads might influence currency pairs, especially USD/JPY and other major FX pairs.
        - Highlight potential trading opportunities or risks arising from these movements.

    - Provide a Concise Conclusion
        - Summarize the overall market tone and any notable divergences or points of caution.
        - offer a clear, action-oriented perspective on what might come next for {currency_pair} traders.
    """

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        self.analysis_llm = Config(model_name="gpt-4o", temperature=0.2).get_model()
    
    def analyze_assets(self, assets_data: str) -> List[Dict[str, str]]:
        user_prompt = """
         <assets data>
         {content}
         </assets data>"""

        prompt = ChatPromptTemplate.from_messages([
        ("system", self.sentiment_system_prompt_template),
        ("user", user_prompt)])

        chain = prompt | self.analysis_llm | StrOutputParser()
        results = chain.invoke({"content": assets_data, "currency_pair": self.currency_pair})

        return results
