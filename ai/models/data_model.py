from pydantic import BaseModel, Field
from typing import Literal, List

# class TradingStrategy(BaseModel):
#     """Trading strategy output format"""

#     rationale: str 
#     strategy: str 
#     entry_point: float 
#     take_profit: float
#     stop_loss: float
#     confidence_score: int

class TradingStrategy(BaseModel):
    """Trading strategy output format"""

    rationale: str
    strategy: Literal["sell", "buy", "wait"]
    entry_point: float 
    take_profit: float
    stop_loss: float
    confidence_score: int = Field(..., description="Confidence score from 1 (lowest) to 5 (highest)")

class Step(BaseModel):
    analysis: strs


class TradingReasoning(BaseModel):
    steps: List[Step]
    final_strategy: TradingStrategy
