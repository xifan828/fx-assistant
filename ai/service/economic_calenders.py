import os
from ai.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from ai.service.technical_indicators import TechnicalIndicators
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
    def __init__(self, analysis_model = None, synthesis_model = None):
        self.analysis_model = analysis_model if analysis_model is not None else Config(model_name="gpt-4o-mini", temperature=0.2, max_tokens=1024).get_model()
        self.synthesis_model = synthesis_model if synthesis_model is not None else Config(model_name="gpt-4o-mini", temperature=0.2, max_tokens=1024).get_model()

        self.system_prompt_analysis = """You are an advanced AI agent specialized in analyzing EUR/USD economic calendars. Your primary function is to process economic calendars and provide concise, actionable summaries for traders. You will economic events happaned today, upcoming economic events and the current date and time as input.

## Your tasks:
1. Compare the events in the calendar with the provided current date and time.
2. Generate a concise summary that includes:
   a. A brief overview of significant past events and their outcomes.
   b. Upcoming important events, focusing on high-impact indicators.
   c. Analysis of the time gap between past and future events.

## Guidelines for your analysis:

- For past events, focus on actual results versus forecasts and their potential market impact.
- For future events, highlight the expected impact and any notable forecasts.
- Consider the time gap between events and how it might affect market dynamics.
- Use clear, concise language suitable for traders.
- Limit your summary to key points; aim for brevity without sacrificing crucial information.

## Output format:

1. Past Events Summary (2-3 sentences)
2. Future Events Summary (2-3 sentences)
3. Time Gap Analysis (1-2 sentences)
4. Key Takeaway (1 sentence)

Remember, your goal is to provide valuable, actionable insights that traders can quickly digest and use in their decision-making process."""

        self.system_prompt_extraction = """You are an AI agent specialized in extracting structured data from EUR/USD economic calendar images. Your task is to analyze the provided image and extract specific information in a JSON format.

## Your task:

1. Analyze the provided economic calendar image.
2. Extract the following information for each event in the calendar:
   - Time (date and time): MM-DD HH:MM
   - Area 
   - Event name
   - Actual value (if available)
   - Forecast value
   - Prior value

3. Output the extracted information in a JSON format.

## Guidelines for data extraction:

- Ensure accuracy in reading and transcribing the data from the image.
- If a field is not available or not applicable for a particular event, use null as the value.
- Maintain the chronological order of events as shown in the calendar.
- Be consistent in formatting dates and times.
- If the exact time of an event is not specified, use null for the time field.

## Output format:

Your output should be ONLY a valid JSON array of objects, where each object represents an event:

```json
[
  {{
    "time": "MM-DD HH:MM",
    "area": ,
    "event_name": "Name of the economic event",
    "actual": "Actual value or null",
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
                {"type": "text", "text": "{file_name} is uploaded"},
                {"type": "image_url", "image_url": {"url": "{encoded_image}"}},  # Use base64 string here
            ]
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message.content),
            ("user", user_message.content)
        ])
        chain = prompt | self.analysis_model | StrOutputParser()
        return chain
    
    def create_event_extraction_tasks(self):
        encoded_images = {}
        for file_name in os.listdir("data/calender/"):
            if file_name.endswith("png"):
                encoded_images[file_name.split(".")[0]] = self.encoded_image_template.format(base64_image=self.encode_image(f"data/calender/{file_name}"))

        
        tasks = [{"file_name": k, "encoded_image": v} for k, v in encoded_images.items()]
        #print(tasks)
        return tasks
    
    def extract_economic_events(self):
        tasks = self.create_event_extraction_tasks()
        extraction_chain = self.create_events_extraction_chain()
        results = extraction_chain.batch(tasks)
        for task in tasks:
            if task["file_name"] == "today":
                events_today = f"Important events happaned today: \n {results[0]}"
                events_upcoming = f"Upcoming important events : \n {results[1]}"
            else:
                events_today = f"Important events happaned today: \n {results[1]}"
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

    
#     def create_analysis_tasks(self, rates, technical_indicators):
#         now = datetime.now()
#         formatted_date = now.strftime("Today is %A, %d %B, %Y")

#         tasks = []
#         tasks.append({
#             "date": formatted_date, "rates_period": "1 day", "rates_interval": "15 minutes", "rates": rates["1_day"], "ti_interval": "15 minutes", "technical_indicators": technical_indicators["15_min"]
#         })
#         tasks.append({
#             "date": formatted_date, "rates_period": "5 days", "rates_interval": "1 hour", "rates": rates["5_day"], "ti_interval": "1 hour", "technical_indicators": technical_indicators["1_hour"]
#         })
#         tasks.append({
#             "date": formatted_date, "rates_period": "3 months", "rates_interval": "1 day", "rates": rates["3_month"], "ti_interval": "1 day", "technical_indicators": technical_indicators["1_day"]
#         })
#         return tasks

#     def create_analysis(self, rates, technical_indicators):
#         tasks = self.create_analysis_tasks(rates, technical_indicators)
#         analysis_chain = self.create_analysis_chain()
#         results = analysis_chain.batch(tasks)
#         analysis = "\n".join(results)
#         return analysis
    
#     def create_synthesis_chain(self):
#         prompt_synthesis = ChatPromptTemplate.from_messages([
#             ("system", self.system_prompt_synthesis),
#             ("user", "{results}")
#         ])

#         synthesis_chain = prompt_synthesis | self.synthesis_model | StrOutputParser()
#         return synthesis_chain
    
#     def create_synthesis(self, analysis):
#         synthesis_chain = self.create_synthesis_chain()
#         results = synthesis_chain.invoke({"results": analysis})
#         return results
    
#     def run(self):
#         print("extracting ti")
#         technical_indicators = self.extract_technical_indicators()
#         print(type(technical_indicators))
#         print(technical_indicators)
#         rates = self.extract_eur_usd_rate()
#         analysis = self.create_analysis(rates=rates, technical_indicators=technical_indicators)
#         #synthesis = self.create_synthesis(analysis=analysis)
#         synthesis = analysis
#         return synthesis

if __name__ == "__main__":
    ec = EconomicCalenders()
    results = ec.run()
    print(results)
