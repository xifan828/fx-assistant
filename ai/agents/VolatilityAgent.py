import asyncio
from ai.config import Config, GeminiClient
import os

class VolatilityAgent:
    system_message = """
**System Role**:  
You are an AI trading assistant specialized in technical analysis of intraday forex charts.

---

## User Context

The user will provide:
1. A **1‑hour candlestick chart**. 
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
   - Examine the 14 hourly candles: note their size, direction (up or down), and relative consistency or variability.  
   - Look at the ATR(14) line below the chart:
     - Determine if the current ATR reading is higher, lower, or about average compared to its range over the last 14 hours.
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

    def __init__(self, gemini_model = None, gemini_api_key = None):
        self.gemini_model = gemini_model if gemini_model is not None else "gemini-2.0-flash"
        self.gemini_api_key = gemini_api_key if gemini_api_key is not None else os.environ["GEMINI_API_KEY_XIFAN"]

    async def analyze_volatility(self, file_path: str):
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        client = GeminiClient(
            model_name=self.gemini_model,
            generation_config=generation_config,
            api_key=self.gemini_api_key,
            system_instruction=self.system_message
        )
        response, _ = await client.call_gemini_vision_api(
            user_message="The chart is provided. Please start your analysis",
            image_path=file_path
        )
        return response

if __name__ == "__main__":
    agent = VolatilityAgent()
    print(asyncio.run(agent.analyze_volatility("data/chart/1h.png")))