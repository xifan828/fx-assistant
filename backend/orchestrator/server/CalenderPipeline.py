from backend.agents.calender.CalenderAgent import CalenderExtractionAgent, CalenderAnalysisAgent, EconomicEvent
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.utils.parameters import PAIRS
from backend.utils.logger_config import get_logger
from typing import List, Dict, Union
import asyncio
import os
from datetime import datetime

logger = get_logger(__name__)

class CalenderPipeline(ProcessPipeline):

    def __init__(self, extraction_model: str = "gemini-2.0-flash", analysis_model: str = "gemini-2.0-flash"):
        super().__init__()
        self.extraction_model = extraction_model
        self.analysis_model = analysis_model
        
    async def extract_calender_data(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
        "response_schema": list[EconomicEvent]
        }

        tasks = []

        async def safe_extraction(chat_path: str, model: str, config: Dict) -> Union[EconomicEvent, None]:
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

            tasks.append(safe_extraction(today_chat_path, self.extraction_model, generation_config))
            tasks.append(safe_extraction(upcoming_chat_path, self.extraction_model, generation_config))
        
        results = await asyncio.gather(*tasks)

        calender_data = {}

        for i, currency_pair in enumerate(PAIRS):
            pair_formatted = currency_pair.replace("/", "_").lower()
            today_events = [i.dict() for i in results[i * 2]][:5]  # Limit to 5 events
            upcoming_events = [i.dict() for i in results[i * 2 + 1]][:5] # Limit to 5 events

            if today_events is None or upcoming_events is None:
                continue
            
            logger.info(f"Extracted calendar data for {currency_pair}")
            calender_data[currency_pair] = {
                "today": today_events,
                "upcoming": upcoming_events
            }
        
        self._save_results(calender_data, os.path.join("data", "process", "calender.json"), truncate=True, limit=5)
        logger.info(f"Calendar data saved to json")
        
        return calender_data

    def get_new_calender(self):
        calender_data = self._load_json(os.path.join("data", "process", "calender.json"))
        latest_calender = calender_data[-1]
        previous_calender = calender_data[-2] if len(calender_data) > 1 else None

        if os.path.exists(os.path.join("data", "process", "calender_synthesis.json")):
            return latest_calender

        if previous_calender is None:
            return latest_calender
        else:
            new_calender = {}
            for currency_pair in PAIRS:
                pair = currency_pair.replace("/", "_").lower()
                if latest_calender[pair] != previous_calender[pair]:
                    new_calender[pair] = latest_calender[pair]
            return new_calender
    
    async def analyze_calender_data(self, calender_data: Dict) -> Dict[str, str]:
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
            "response_mime_type": "text/plain",
        }

        tasks = []

        async def safe_analysis(pair: str, config: Dict, user_message: str) -> Union[str, None]:
            try:
                analysis_agent = CalenderAnalysisAgent(
                    currency_pair=pair,
                    gemini_model=self.analysis_model,
                    generation_config=config,
                    gemini_api_key=os.environ["GEMINI_API_KEY_KIEN"],
                    user_message=user_message,
                )
                return await analysis_agent.run()
            except Exception as e:
                logger.error(f"Error in analyzing calendar data: {e}")
                return None
        
        for pair, events in calender_data.items():
            today_events = events["today"]
            upcoming_events = events["upcoming"]

            user_message = f"Today: {today_events}, Upcoming: {upcoming_events}"
            tasks.append(safe_analysis(pair, generation_config, user_message))

        results = await asyncio.gather(*tasks)

        calender_analysis = {}
        for i, (pair, events) in enumerate(calender_data.items()):
            if results[i] is None:
                continue
            calender_analysis[pair] = results[i]
            logger.info(f"Analyzed calendar data for {pair}")
        return calender_analysis

    def save_calender_analysis(self, calender_analysis: Dict[str, str]) -> None:
        for pair, analysis in calender_analysis.items():
            file_path = os.path.join("data", "process", f"{pair}_calender_analysis.json")
            analysis_dict = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "analysis": analysis
            }
            self._save_results(analysis_dict, file_path, truncate=True, limit=5)
            logger.info(f"Saved calendar analysis for {pair} to json")
    
    async def run(self) -> Dict[str, str]:
        _ = await self.extract_calender_data()
        
        new_calender = self.get_new_calender()
        if not new_calender:
            logger.info("No new calendar data to analyze")
            return {}
        
        calender_analysis = await self.analyze_calender_data(new_calender)
        self.save_calender_analysis(calender_analysis)
        return calender_analysis


if __name__ == "__main__":
    calender_pipeline = CalenderPipeline()
    calender_analysis = asyncio.run(calender_pipeline.run())

