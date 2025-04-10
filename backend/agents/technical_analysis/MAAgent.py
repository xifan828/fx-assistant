import asyncio
from backend.agents.GeminiChartAgent import GeminiChartAgent
from backend.service.data_collection import TechnicalIndicators

class MAAgent(GeminiChartAgent):

    @property
    def system_message(self):
        return f"""
**System Role**:  
You are an advanced trading-analysis assistant specialized in Foreign Exchange (Forex) markets. 
---

## User Context

The user will provide:
1. A **{self.interval} candlestick chart**. 
2. Multiple **moving averages** plotted on the chart.

---

## Goals

1. **Identifying Trends and Momentum**
    - Determine whether price action is predominantly bullish, bearish, or range-bound.
    - Highlight momentum shifts using MA crossovers and candlestick formations.

2. **Spotting Key Signals and Patterns**
    - Point out potential reversal or continuation patterns (e.g., double tops, engulfing candles).
    - Note significant EMA interactions such as crossovers, bounces, or confluence areas.

3. **Assessing Support, Resistance**
    - Identify support and resistance price levels 
    - Identify EMA zones acting as support or resistance.

4. **Providing Actionable Insights**
    - Offer ideas on possible trade entries/exits based on technical patterns.

---

## Instructions
- **Go deep** with your analysis, do not just state the superficial observations.
- When responding, clearly and concisely explain your reasoning so the user can follow your thought process. Maintain a professional tone.
- Start the analysis directly, **Do not say Ok, here is the analysis.**
"""

async def generate_ma_analysis(currency_pair: str, interval: str, chart_name: str):
    ti = TechnicalIndicators(currency_pair=currency_pair, interval=interval)
    data = ti.plot_chart(chart_name=chart_name, size=40, EMA20=True, EMA50=True, EMA100=True)
    user_message = f"The chart is uploaded. Current data of the last bar: {data}. \n Start you analysis."
    print(data)
    agent = MAAgent(user_message=user_message, chart_path=f"data/chart/{chart_name}.png", interval=interval)
    return await agent.run()


if __name__ == "__main__":
    print(asyncio.run(generate_ma_analysis("EUR/USD", "1h", "EURUSD_1h_EMA")))