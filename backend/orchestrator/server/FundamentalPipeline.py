from backend.utils.parameters import CURRENCY_PAIRS, ECONOMIC_INDICATORS
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.agents.fundamental.FundamentalAgents import RateAgent, InflationAgent, GrowthAgent, EmploymentAgent, SynthesisAgent
from backend.utils.logger_config import get_logger
from backend.utils.parameters import CURRENCIES, CURRENCY_PAIRS
from typing import Dict, Literal, List
from backend.agents.GeminiChartAgent import GeminiChartAgent
import os
import asyncio

logger = get_logger(__name__)

class FundamentalPipeline(ProcessPipeline):
    def __init__(self, analysis_model: str = "gemini-2.5-flash-preview-04-17"):
        super().__init__()
        self.analysis_model = analysis_model
        self.analysis_path = os.path.join("data", "process", "fundamental")
    
    def get_fund_update(self) -> List[str]:
        
        if not os.path.exists(self.analysis_path):
            update_currs = [i.lower() for i in CURRENCIES]
        
        else:
            update_currs = []
            for currency in CURRENCIES:
                currency = currency.lower()
                curr_fund = self.scrape_results_curr["fundamental"][currency]
                if self.scrape_results_prev is not None:
                    prev_fund = self.scrape_results_prev["fundamental"][currency]
                    if curr_fund != prev_fund:
                        update_currs.append(currency)
                else:
                    update_currs.append(currency)

        update_curr_pairs = []
        for curr in update_currs:
            for pair in CURRENCY_PAIRS:
                if curr in pair.lower():
                    update_curr_pairs.append(pair)
        
        update_curr_pairs = list(set(update_curr_pairs))

        return update_curr_pairs
        
    def prepare_data(self, category: str, currency: str) -> Dict[str, Dict[Literal["desc", "table"], str]]:

        indicator_names = ECONOMIC_INDICATORS[category][currency]
        data = {name: self.scrape_results_curr["fundamental"][currency.lower()][name] 
                for name in indicator_names}
        return data
    
    async def analyze_fund(self, currency_pair: str, category: str) -> str:
        agent_map: Dict[str, GeminiChartAgent] = {
            "rate": RateAgent,
            "inflation": InflationAgent,
            "growth": GrowthAgent,
            "employment": EmploymentAgent
        }
        agent_cls = agent_map[category]

        curr_a = currency_pair.split("/")[0]
        curr_b = currency_pair.split("/")[1]

        data_a = self.prepare_data(category, curr_a)
        data_b = self.prepare_data(category, curr_b)
        
        user_message = f"""{category} data
        <{curr_a}>
        {data_a}
        </{curr_a}>

        <{curr_b}>
        {data_b}
        </{curr_b}>
        Please analyze the data and provide insights on the implications for {currency_pair}."""     

        if category in ["rate", "inflation"]:
            key = os.environ["GEMINI_API_KEY_XIFAN_2"]
        else:
            key = os.environ["GEMINI_API_KEY_XIFAN_3"]

        agent: GeminiChartAgent = agent_cls(gemini_model=self.analysis_model,
                                            user_message=user_message, 
                                            gemini_api_key=key,
                                            currency_pair=currency_pair)
        try:
            response = await agent.run_text()
            return response
        except Exception as e:
            logger.error(f"Error in analyzing chart: {e}")
            return "Error in analysis"
    
    async def synthesize_fund(self, currency_pair: str, fund_analysis: Dict[str, str]) -> str:
        user_message = ""

        for category, analysis in fund_analysis.items():
            user_message += f"""<{category}>
            {analysis}
            </{category}>\n\n"""
        
        key = os.environ["GEMINI_API_KEY_XIFAN_3"]

        agent = SynthesisAgent(gemini_model=self.analysis_model,
                               user_message=user_message,
                               gemini_api_key=key,
                               currency_pair=currency_pair)
        
        try:
            response = await agent.run_text()
            return response
        except Exception as e:
            logger.error(f"Error in synthesizing analysis: {e}")
            return "Error in synthesis"

    async def run(self):
        try:
            currency_pairs = self.get_fund_update()

            logger.info(f"Update currency pairs: {currency_pairs}")

            if not currency_pairs:
                return None
            
            tasks = []
            for currency_pair in currency_pairs:
                for category in ECONOMIC_INDICATORS.keys():
                    tasks.append(
                        self.analyze_fund(currency_pair, category)
                    )
                
            results = await asyncio.gather(*tasks)

            analysis_result_dict = {}

            for i, currency_pair in enumerate(currency_pairs):
                analysis_result_dict[currency_pair] = {}
                for category in ECONOMIC_INDICATORS.keys():
                    analysis_result_dict[currency_pair][category] = results[i * len(ECONOMIC_INDICATORS) + list(ECONOMIC_INDICATORS.keys()).index(category)]
                logger.info(f"Analyzed fundamental for {currency_pair}")
            
            tasks = []

            for i, currency_pair in enumerate(currency_pairs):
                tasks.append(
                    self.synthesize_fund(currency_pair, analysis_result_dict[currency_pair])
                )
            
            synthesis_results = await asyncio.gather(*tasks)

            for currency_pair, synthesis_result in zip(currency_pairs, synthesis_results):
                analysis_result_dict[currency_pair]["synthesis"] = synthesis_result
                logger.info(f"Synthesized fundamental for {currency_pair}")

                if not os.path.exists(self.analysis_path):
                    os.makedirs(self.analysis_path)
                
                currency_pair_formated = currency_pair.replace("/", "_").lower()
                file_path = os.path.join(self.analysis_path, f"{currency_pair_formated}_analysis.json")
                self._save_results(data=analysis_result_dict[currency_pair], 
                                file_path=file_path,
                                truncate=True)
                logger.info(f"Saved analysis for {currency_pair} to {file_path}")
            
            return analysis_result_dict
        
        except Exception as e:
            logger.error(f"Error in fundamental pipeline: {e}")
            return None
    

        




if __name__ == "__main__":
    pipeline = FundamentalPipeline()
    #pipeline.prepare_data("inflation", "USD")
    #print(pipeline.get_update())

    result_dict = asyncio.run(pipeline.run())


