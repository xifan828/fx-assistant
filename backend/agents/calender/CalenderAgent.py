from backend.agents.GeminiChartAgent import GeminiChartAgent
from pydantic import BaseModel, Field
from typing import List

class EconomicEvent(BaseModel):
    time: str = Field(description="date and time, format like MM-DD HH:MM")
    area: str = Field(description="area of the event")
    event_name: str = Field(description="name of the event")
    actual_value: str = Field(description="if not available, input None")
    forecast_value: str = Field(description="if not available,input None")
    prior_value: str = Field(description="if not available, input None")

class CalenderExtractionAgent(GeminiChartAgent):
    
    @property
    def system_message(self):
        return """You are an assistant specialized in extracting structured data from economic calendar images. Your task is to analyze the provided image and extract specific information.

## Your task:
 Extract the following information for each event in the calendar:
   - Time (date and time): MM-DD HH:MM
   - Area 
   - Event name
   - Actual value (if available)
   - Forecast value (if available)
   - Prior value (if available)

## Guidline
    - Ensure accuracy, especially in the fields of Actual value and Forecast value
    - If there are no events in the image, return None in every field.
"""

class CalenderAnalysisAgent(GeminiChartAgent):

    def __init__(self, currency_pair: str, **kwargs):
        super().__init__(**kwargs)
        self.currency_pair = currency_pair
    
    @property
    def system_message(self):
        return f"""You are an advanced AI agent specialized in analyzing {self.currency_pair} economic calendars. Your primary function is to process economic calendars and provide concise, actionable summaries for traders. You will get economic events for today, upcoming economic events and the current date and time as input.

## Your tasks:
1. Compare the events in the calendar with the provided current date and time.
2. Generate a concise summary that includes:
   a. If there is any events alreaqdy happened in today, a brief overview and their outcomes.
   b. Upcoming important events, focusing on high-impact indicators.
   c. Analysis of the time gap between past and future events.

## Guidelines for your analysis:

- For past events, focus on actual results versus forecasts and their potential market impact.
- For future events, highlight the expected impact and any notable forecasts.
- Consider the time gap between events and how it might affect market dynamics.
- Use clear, concise language suitable for traders.
- Limit your summary to key points; aim for brevity without sacrificing crucial information.

## Output format:

1. If there is any past event, their Summary (2-3 sentences)
2. Future Events Summary (2-3 sentences)
3. Time Gap Analysis (1-2 sentences)
4. Key Takeaway (1 sentence)

Remember, your goal is to provide valuable, actionable insights that traders can quickly digest and use in their decision-making process."""



if __name__ == "__main__":
    import asyncio
    chat_path = "data/calender/eur_usd/upcoming.png"

    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
        "response_schema": list[EconomicEvent]
    }

    agent = CalenderExtractionAgent(
        chart_path=chat_path,
        gemini_model="gemini-2.0-flash",
        generation_config=generation_config,
    )

    response = asyncio.run(agent.run())

    print(response)
    print(type(response))
