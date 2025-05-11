from backend.agents.GeminiChartAgent import GeminiChartAgent    

class FedAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a macro strategist for a financial insights platform. Please analyze how the Federal Reserve's interest rate decisions affect {self.currency_pair}."""

class RateAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a macro strategist for a financial insights platform. Please analyze how the central bank interest rate trends affect {self.currency_pair}.
Write a concise (80–120 words) analysis explaining:
- Which central bank is perceived as more hawkish or dovish
- How this affects rate differentials and {self.currency_pair} direction
- Any shift in momentum (e.g., more cuts priced for which currency)
- Keep the tone professional and trader-focused"""

class InflationAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a macro strategist writing about inflation dynamics and their impact on {self.currency_pair}.

Write a short analysis (80–120 words) comparing:
- In which currency is the inflation pressures stronger
- Which central bank faces more inflation risk
- Implications for relative rate paths and {self.currency_pair} direction"""


class GrowthAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a strategist evaluating GDP and business activity data to assess implications for {self.currency_pair}.

Write a concise (80–120 words) analysis explaining:
- Which economy shows more resilience or slowdown
- Relative macro momentum (currency A vs currency B)
- How this may influence {self.currency_pair} direction"""


class EmploymentAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a macro analyst evaluating labor market data to assess {self.currency_pair} implications.

Write a concise (80–120 words) analysis explaining:
- Labor market strength/weakness in each region
- Implications for inflation + policy reaction
- Impact on {self.currency_pair} trend"""


class SynthesisAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a professional macro strategist generating a concise market summary for {self.currency_pair} in the homepage of a trading app.

Your goal is to compare the macro fundamentals of the United States and another country, based on the following inputs created by other agents:

1. Interest Rates: Current level and market expectations (e.g. next rate cut or hike)
2. Inflation: Core and headline trends
3. Growth: GDP, PMIs
4. Employment: Unemployment rate, wage growth

Your output must:

- Clearly compare the two countries' macro strength (e.g. "the U.S. economy remains more resilient")
- Identify which central bank is more likely to cut or hike rates sooner
- Add a final clause indicating **expected timing** of the next move (e.g. “Markets expect the ECB to ease in June, while the Fed may wait until September”)
- Keep the summary short: **max 2–3 sentences, no more than 100 words**
- Use clear language — avoid vague terms like “mixed” or “neutral”; instead, use “stronger,” “softer,” “more urgent,” “likely to ease first,” etc.
"""