from typing import List, Dict, Literal
from backend.utils.llm_helper import OpenAIClient
from pydantic import BaseModel


class RiskSentimentAnalysis(BaseModel):
    risk_sentiment_analysis: str
    key_market_drivers: str
    implications_for_trading: str
    conclusion: str
    risk_sentiment: Literal["risk-on", "slightly risk-on", "neutral", "slightly risk-off", "risk-off"]


class RiskSentimentAgent:

    sentiment_system_prompt_template = """You are a financial market analyst specializing in foreign exchange (FX). 
    You will be given various assets data and a summary of recent news.
    Your task is to **take the news summary as context**:
    - Assess Overall Risk Sentiment Analysis
        - Examine global equity indices (S&P 500, Nasdaq, STOXX50, MSCI EM) to determine whether the market is risk-on or risk-off.
        - Consider commodity prices (Gold, Brent Oil) and their impact on risk sentiment.
        - Analyze changes in bond yields and yield spreads to gauge interest-rate differentials and policy expectations.

    - Identify Key Market Drivers
        - Discuss which indicators (equities, yields, commodity prices, currency pairs) appear to be the primary forces shaping the current market environment.
    
    - Implications for {currency_pair} Trading
        - Explain how the observed risk sentiment and yield spreads might influence currency pairs, especially USD/JPY and other major FX pairs.
        - Highlight potential trading opportunities or risks arising from these movements.

    - Provide a Concise Conclusion in maximum 1-2 sentences.
        - Summarize the overall market tone and any notable divergences or points of caution.
        - offer a clear, action-oriented perspective on what might come next for {currency_pair} traders.
    """

    def __init__(self, currency_pair: str, model_name: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):
        self.currency_pair = currency_pair
        self.openai_client = OpenAIClient(model=model_name, temperature=temperature)
    
    async def analyze_risk_sentiment(self, assets_data: str, news_summary: str) -> RiskSentimentAnalysis:
        user_prompt = f"""
         <assets data>
         {assets_data}
         </assets data>
         
         <news summary>
         {news_summary}
         </news summary>
         """

        messages = [
            {"role": "system", "content": self.sentiment_system_prompt_template.format(currency_pair=self.currency_pair)},
            {"role": "user", "content": user_prompt}
        ]

        analysis = await self.openai_client.structured_chat_completion(
            messages=messages,
            response_format=RiskSentimentAnalysis
        )
        
        return analysis
