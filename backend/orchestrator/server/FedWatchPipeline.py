from backend.agents.fundamental.FedWatchAgent import FedWatchAgent
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.utils.logger_config import get_logger
import os
from datetime import datetime
import pandas as pd
from backend.utils.logger_config import get_logger
logger = get_logger(__name__)

class FedWatchPipeline(ProcessPipeline):
    def __init__(self, analysis_model: str = "gemini-2.5-flash-preview-04-17"):
        super().__init__()
        self.analysis_model = analysis_model
        self.analysis_path = os.path.join("data", "process", "fedwatch")
        os.makedirs(self.analysis_path, exist_ok=True)
    
    def get_fed_watch_update(self) -> bool:
        analysis_file_path = os.path.join(self.analysis_path, "analysis.json")
        if not os.path.exists(analysis_file_path):
            return True
        
        fed_watch_curr = self.scrape_results_curr["fed_watch"]

        if self.scrape_results_prev:
            fed_watch_prev = self.scrape_results_prev["fed_watch"]
            if fed_watch_curr == fed_watch_prev:
                return False
        return True

    def prepare_data(self) -> str:

        rates_next = self.scrape_results_curr["fed_watch"]["target_rates_probs"]

        current_rate = ""
        for rate in rates_next:
            if "Current" in rate["target_rate"]:
                current_rate = rate["target_rate"]
                break

        implied_rate_next = 100 - float(self.scrape_results_curr["fed_watch"]["mid_price"])

        context = f"""
# FedWatch data

## For the next FOMC meeting

The current rate before the next FOMC meeting is {current_rate}.

The current implied rate is {implied_rate_next:.2f}%.

Market expectations are as follows:
{rates_next}
"""
        return context
    
    async def analyze_fed(self) -> str:
        try:
            agent = FedWatchAgent(
                gemini_model=self.analysis_model,
                gemini_api_key=os.getenv("GEMINI_API_KEY_XIFAN_4"),
                user_message=self.prepare_data()
            )
            return await agent.run_text()
        except Exception as e:
            logger.error(f"Error in analyzing FedWatch data: {e}")
            return "Error in analyzing FedWatch data"

    async def run(self):
        try:
            
            if not self.get_fed_watch_update():
                logger.info("No new FedWatch data to analyze.")
                return "No new FedWatch data to analyze."
            
            logger.info("New FedWatch data found. Starting analysis.")

            result = await self.analyze_fed()

            result_dict = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "analysis": result
            }

            analysis_file_path = os.path.join(self.analysis_path, "analysis.json")

            self._save_results(
                data=result_dict,
                file_path=analysis_file_path,
                truncate=True,
            )

            logger.info(f"Saved FedWatch analysis to {analysis_file_path}")

            return result
        
        except Exception as e:
            logger.error(f"Error in FedWatchPipeline: {e}")
            return "Error in FedWatchPipeline"
        
        
if __name__ == "__main__":
    pipeline = FedWatchPipeline()
    #print(pipeline.prepare_data())
    import asyncio
    result = asyncio.run(pipeline.run())
    #print(result)
    