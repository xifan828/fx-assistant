from pydantic import BaseModel

class TradingStrategy(BaseModel):
    """Trading strategy output format"""

    rationale: str 
    strategy: str 
    entry_point: float 
    take_profit: float
    stop_loss: float
    confidence_score: int