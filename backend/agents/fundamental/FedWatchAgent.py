from backend.agents.GeminiChartAgent import GeminiChartAgent    
from pydantic import BaseModel, Field
from typing import List

class TargetRate(BaseModel):
    target_rate: str
    probability_now: float
    probablity_1_day_ago: float
    probability_1_week_ago: float
    probability_1_month_ago: float

class FedWatchData(BaseModel):
    target_rates_probs: List[TargetRate]
    mid_price: float


class FedWatchParser(GeminiChartAgent):

    @property
    def system_message(self):
        return f"""Extact the Fed Watch data from the provided chart image. Be accurate and concise."""


class FedWatchAgent(GeminiChartAgent):

    @property
    def system_message(self):
        return f"""You are a macro strategist for a financial intelligence app. Your job is to write a concise and insightful Fed Outlook Summary based on the latest market-implied rate probabilities.

Please write a summary (~100–130 words) that:

1. Describes how expectations have shifted compared to one month ago.  
2. Highlights the most likely path and current consensus.  
3. Uses clear, professional tone suitable for fund managers or traders.  
4. Suggests the macro/trading implication if appropriate """