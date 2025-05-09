from backend.utils.parameters import CURRENCY_PAIRS, ECONOMIC_INDICATORS
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.agents.fundamental.FundamentalAgents import RateAgent, InflationAgent, GrowthAgent, EmploymentAgent
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

class FundamentalPipeline(ProcessPipeline):
    def __init__(self, analysis_model: str = "gemini-2.5-flash-preview-04-17"):
        super().__init__()
        self.analysis_model = analysis_model
    
    def prepare_data(self, category: str, currency: str):

        indicator_names = ECONOMIC_INDICATORS[category][currency]

        print(indicator_names)

        data = {name: self.scrape_results_curr["fundamental"][currency.lower()][name] 
                for name in indicator_names}

        print(data)




if __name__ == "__main__":
    pipeline = FundamentalPipeline()
    pipeline.prepare_data("inflation", "USD")
    


