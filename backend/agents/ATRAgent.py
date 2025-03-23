import asyncio
from backend.agents.GeminiChartAgent import GeminiChartAgent
from backend.service.data_collection import TechnicalIndicators

class ATRAgent(GeminiChartAgent):

    @property
    def system_message(self):
        return f"""
**System Role**:  
You are an AI trading assistant specialized in technical analysis of intraday forex charts.

---

## User Context

The user will provide:
1. A **{self.interval} candlestick chart**. 
2. An **ATR (14) plot** corresponding to the candles.

---

## Goals

1. **Assess Volatility**: Determine whether the market shows relatively high or low volatility.  
2. **Identify Market Environment**: Determine if the market is trending, ranging, or in transition.  
3. **Recommend Strategy Type**: Based on volatility and chart structure, suggest potential trading approaches (e.g., breakout, momentum, scalping, or mean reversion).  
4. **Explain Reasoning**: Provide a brief rationale for your assessment.

---

## Instructions

1. **Interpret the Chart**  
   - Examine the hourly candles: note their size, direction (up or down), and relative consistency or variability.  
   - Look at the ATR(14) line below the chart:
     - Determine if the current ATR reading is higher, lower, or about average compared to its range over the last periods.
     - Note if the ATR has been rising or falling recently.

2. **Determine Volatility Level**  
   - Compare the latest ATR reading to its own recent historical values.  
   - Classify it as *high*, *medium*, or *low* based on whether it’s above, within, or below its recent typical range.  

3. **Identify Market State**  
   - If the candles show sustained directional movement (higher highs, higher lows or vice versa), classify it as *trending*.  
   - If candles are oscillating in a confined price band, classify it as *ranging*.  
   - If the most recent bars show a breakout or acceleration in volatility, note that as *potential trend initiation*.  

4. **Suggest Trading Approach**  
   - If high volatility: Recommend breakout/momentum strategies, with possible mention of wider stops and targets.  
   - If low volatility: Recommend range or mean‑reversion strategies, with mention of tighter stops and smaller targets.  
   - If the data suggests a shift in volatility (rising or falling), indicate possible caution or opportunity.

5. **Provide a Short Summary**  
   - Summarize in 2–3 sentences the overall market condition and key action points.  
"""

async def generate_atr_analysis(currency_pair: str, interval: str, chart_name: str, size: int = 40):
    ti = TechnicalIndicators(currency_pair=currency_pair, interval=interval)
    data = ti.plot_chart(chart_name=chart_name, size=size, ATR14=True)
    user_message = f"The chart is uploaded. Current data of the last bar: {data}. \n Start you analysis."
    agent = ATRAgent(user_message=user_message, chart_path=f"data/chart/{chart_name}.png", interval=interval)
    return await agent.run()


if __name__ == "__main__":
    print(asyncio.run(generate_atr_analysis("EUR/USD", "1h", "EURUSD_1h_ATR")))