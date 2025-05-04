from backend.agents.calender.CalenderAgent import CalenderExtractionAgent, CalenderAnalysisAgent, EconomicEvent
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.utils.parameters import PAIRS
from backend.utils.logger_config import get_logger
from typing import List, Dict
import asyncio
import os

logger = get_logger(__name__)

class CalenderPipeline(ProcessPipeline):

    def __init__(self, extraction_model: str = "gemini-2.0-flash", analysis_model: str = "gemini-2.0-flash"):
        super().__init__()
        self.extraction_model = extraction_model
        self.analysis_model = analysis_model
        pass

    async def extract_calender_data(self) -> Dict[str, List[EconomicEvent]]:
        generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
        "response_schema": list[EconomicEvent]
        }

        tasks = []

        async def safe_extraction(chat_path: str, model: str, config: Dict):
            try:
                extraction_agent = CalenderExtractionAgent(
                    chart_path=chat_path,
                    gemini_model=model,
                    generation_config=config,
                )
                return await extraction_agent.run()
            except Exception as e:
                logger.error(f"Error in extracting calendar data: {e}")
                return None

        for currency_pair in PAIRS:
            pair_formatted = currency_pair.replace("/", "_").lower()
            today_chat_path = os.path.join("data", "calender", pair_formatted, "today.png")
            upcoming_chat_path = os.path.join("data", "calender", pair_formatted, "upcoming.png")


            extraction_agent_today = CalenderExtractionAgent(
                chart_path=today_chat_path,
                gemini_model=self.extraction_model,
                generation_config=generation_config,
            )

            extraction_agent_upcoming = CalenderExtractionAgent(
                chart_path=upcoming_chat_path,
                gemini_model=self.extraction_model,
                generation_config=generation_config,
            )

            tasks.append(extraction_agent_today.run())
            tasks.append(extraction_agent_upcoming.run())
        
        results = await asyncio.gather(*tasks)

        calender_data = {}

        for i, currency_pair in enumerate(PAIRS):
            pair_formatted = currency_pair.replace("/", "_").lower()
            today_events = [i.dict() for i in results[i * 2]]
            upcoming_events = [i.dict() for i in results[i * 2 + 1]]	

            calender_data[currency_pair] = {
                "today": today_events,
                "upcoming": upcoming_events
            }
        
        return calender_data

if __name__ == "__main__":
    calender_pipeline = CalenderPipeline()
    calender_data = asyncio.run(calender_pipeline.extract_calender_data())
    for currency_pair, events in calender_data.items():
        print(currency_pair)
        print(events)

        print("\n\n")

