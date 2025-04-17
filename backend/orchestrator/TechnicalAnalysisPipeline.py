from backend.orchestrator.TechnicalDataPipeline import TechnicalDataPipeline
from backend.utils.technical_indicators import TechnicalIndicators
from typing import List
import asyncio
from backend.agents.technical_analysis.ATRAgent import ATRAgent
from backend.agents.technical_analysis.MACDAgent import MACDAgent
from backend.agents.technical_analysis.MAAgent import MAAgent
from backend.agents.technical_analysis.RSIAgent import RSIAgent
from backend.agents.technical_analysis.AggAgent import AggAgent
from backend.utils.parameters import DECIMAL_PLACES

class TechnicalAnalysisPipeline:
    def __init__(self, currency_pair: str, interval: str, size: int, analysis_types: List[str], data_source: str = "TwelveData"):
        self.currency_pair = currency_pair
        self.decimal_places = DECIMAL_PLACES.get(currency_pair, 4)  
        self.interval = interval
        self.size = size
        self.analysis_types = analysis_types
        self.data_source = data_source
    
    def prepare_technical_data(self):
        data_pipeline = TechnicalDataPipeline(self.currency_pair, self.interval)

        self.df = data_pipeline.prepare_data(data_source=self.data_source)

        for analysis_type in self.analysis_types:
            data_pipeline.prepare_chart(self.df, self.size, analysis_type)

    async def create_individual_analysis(self):
        coroutines = {}

        for analysis_type in self.analysis_types:
            chart_path = f"data/chart/{self.interval}_{analysis_type}.png"
            user_message_template = "The chart is uploaded. \n{context}\nStart you analysis."

            if analysis_type == "ema":
                user_message = user_message_template.format(context=TechnicalIndicators.get_ma_context(self.df, self.decimal_places))
                print(user_message)
                agent = MAAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
            
            if analysis_type == "macd":
                user_message = user_message_template.format(context=TechnicalIndicators.get_macd_context(self.df, self.decimal_places))
                print(user_message)
                agent = MACDAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
     
            if analysis_type == "atr":
                user_message = user_message_template.format(context=TechnicalIndicators.get_atr_context(self.df, self.decimal_places))
                agent = ATRAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
            
            if analysis_type == "rsi":
                user_message = user_message_template.format(context=TechnicalIndicators.get_rsi_context(self.df, self.decimal_places))
                agent = RSIAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)

            coroutines[analysis_type] = agent.run()

        analysis = await asyncio.gather(*coroutines.values())
        
        analysis_dict = dict(zip(coroutines.keys(), analysis))

        return analysis_dict
    
    def format_individual_analysis(self, analysis_dict: dict):
        formatted_analysis = ""

        for indicator, analysis in analysis_dict.items():
            formatted_analysis += f"<{indicator} analysis> \n{analysis}\n</{indicator} analysis> \n\n"
        
        return formatted_analysis
    
    async def aggregate_analysis(self, formatted_analysis: str):
        agent = AggAgent(
            gemini_model="gemini-2.5-flash-preview-04-17",
            user_message=formatted_analysis
        )
        agg_analysis = await agent.run_text()
        return agg_analysis
    
    async def run(self):
        self.prepare_technical_data()
        individual_analysis = await self.create_individual_analysis()
        formatted_analysis = self.format_individual_analysis(individual_analysis)
        print(formatted_analysis)
        #print()
        agg_analysis = await self.aggregate_analysis(formatted_analysis)
        return agg_analysis
    


if __name__ == "__main__":
    # Example usage
    currency_pair = "EUR/USD"
    interval = "1h"
    size = 48
    analysis_types = ["ema", "rsi", "macd"]
    #analysis_types = ["macd"]

    pipeline = TechnicalAnalysisPipeline(currency_pair, interval, size, analysis_types, data_source="TwelveData")
    #pipeline.prepare_technical_data()
    agg_analysis = asyncio.run(pipeline.run())
    print(agg_analysis)