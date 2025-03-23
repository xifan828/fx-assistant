import os
from backend.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from backend.service.data_collection import TechnicalIndicators
from datetime import datetime
from langchain_core.pydantic_v1 import BaseModel, Field
from zoneinfo import ZoneInfo

class EconomicEvent(BaseModel):
    time: str = Field(description="date and time, format like this 02-31T13:30")
    area: str = Field(description="area of the event")
    event_name: str = Field()
    actural_value: str = Field(description="if not available, input none")
    forecast_value: str = Field(description="if not available,input none")
    prior_value: str = Field(description="if not available, input none")

class EconomicCalenders:
    def __init__(self, analysis_model = None, extraction_model = None, currency_pair: str = "EUR/USD"):
        self.analysis_model = analysis_model if analysis_model is not None else Config(model_name="gpt-4o", temperature=0.2, max_tokens=1024).get_model()
        self.extraction_model = extraction_model if extraction_model is not None else Config(model_name="gpt-4o", temperature=0, max_tokens=1024).get_model()
        self.currency_pair = currency_pair

        self.system_prompt_analysis = f"""You are an advanced AI agent specialized in analyzing {self.currency_pair} economic calendars. Your primary function is to process economic calendars and provide concise, actionable summaries for traders. You will get economic events for today, upcoming economic events and the current date and time as input.

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

        self.system_prompt_extraction = """You are an assistant specialized in extracting structured data from economic calendar images. Your task is to analyze the provided image and extract specific information in a JSON format.

## Your task:
 Extract the following information for each event in the calendar:
   - Time (date and time): MM-DD HH:MM
   - Area 
   - Event name
   - Actual value (if available)
   - Forecast value (if available)
   - Prior value (if available)

3. Output the extracted information in a JSON format.

## Guidline
Ensure accuracy, especially in the fields of Actual value and Forecast value

## Output format:

Your output should be ONLY a valid JSON array of objects, where each object represents an event:

```json
[
  {{
    "time": "MM-DD HH:MM",
    "area": ,
    "event_name": "Name of the economic event",
    "actual": "Actual value or null or upcoming",
    "forecast": "Forecast value or null",
    "prior": "Prior value or null"
  }},
  // ... more events
]
```
"""


        self.encoded_image_template = "data:image/png;base64,{base64_image}"
    
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def create_events_extraction_chain(self):
        system_message = SystemMessage(content=self.system_prompt_extraction)
        user_message = HumanMessage(
            content=[
                {"type": "text", "text": "{file_name} is uploaded. \n{comment}"},
                {"type": "image_url", "image_url": {"url": "{encoded_image}"}},  # Use base64 string here
            ]
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message.content),
            ("user", user_message.content)
        ])
        chain = prompt | self.extraction_model | StrOutputParser()
        return chain
    
    def create_event_extraction_tasks(self):
        encoded_images = {}
        for file_name in os.listdir("data/calender/"):
            if file_name.endswith("png"):
                encoded_images[file_name.split(".")[0]] = self.encoded_image_template.format(base64_image=self.encode_image(f"data/calender/{file_name}"))
                
        tasks = []
        for k, v in encoded_images.items():
            if "today" in k:
                comment = "Provided economic calender image is for today. There could be no events, events happened or will happen."
            elif "upcoming" in k:
                comment = "Provided image is for upcoming calenders. All values in the field Actual value shall be null."
            else:
                comment = ""
            tasks.append({"file_name": k, "encoded_image": v, "comment": comment})
        
        return tasks
    
    def extract_economic_events(self):
        tasks = self.create_event_extraction_tasks()
        extraction_chain = self.create_events_extraction_chain()
        results = extraction_chain.batch(tasks)
        for task in tasks:
            if task["file_name"] == "today":
                events_today = f"Important events will happen or happaned today: \n {results[0]}"
                events_upcoming = f"Upcoming important events : \n {results[1]}"
            else:
                events_today = f"Important events will happen or happaned today: \n {results[1]}"
                events_upcoming = f"Upcoming important events : \n {results[0]}"
            break
        results_str = events_today + "\n" + events_upcoming
        return results_str
    
    
    def create_analysis_chain(self):
        user_message_template = """Right now is {date}. Below are the latest data of happaned and upcoming economic events.
{events}
"""
        prompt_analysis = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt_analysis),
            ("user", user_message_template)
        ])

        chain = prompt_analysis | self.analysis_model | StrOutputParser()
        return chain
    
    def create_events_analysis(self, event_extraction: str):
        now = datetime.now(ZoneInfo('Europe/Berlin'))
        analysis_chain = self.create_analysis_chain()
        analysis = analysis_chain.invoke({"date": now, "events": event_extraction})
        return analysis

    def run(self):
        event_extraction = self.extract_economic_events()
        event_analysis = self.create_events_analysis(event_extraction)
        return event_analysis

if __name__ == "__main__":
    ec = EconomicCalenders(currency_pair="EUR/USD")
    results = ec.run()
    print(results)
