from backend.agents.GeminiChartAgent import GeminiChartAgent    


class RateAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are a macro strategist for a financial insights platform. Please analyze how the central bank interest rate trends affect {self.currency_pair}.
Write a concise (80–120 words) analysis explaining:
- Which central bank is perceived as more hawkish or dovish
- How this affects rate differentials and GBPUSD direction
- Any shift in momentum (e.g., more cuts priced for BOE than Fed)
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
