import asyncio
from backend.service.data_collection import TechnicalIndicators
from backend.agents.technical_analysis.ATRAgent import ATRAgent
from backend.agents.technical_analysis.MACDAgent import MACDAgent
from backend.agents.technical_analysis.MAAgent import MAAgent
from backend.agents.technical_analysis.RSIAgent import RSIAgent
from backend.agents.technical_analysis.AggAgent import AggAgent

class Aggregate:
    def __init__(self, currency_pair: str, interval: str, size: int = 40, indicators: list = ["EMA", "MACD", "ATR", "RSI"]):
        self.currency_pair = currency_pair
        self.interval = interval
        self.size = size
        self.symbol = currency_pair.split("/")[0]
        self.currency = currency_pair.split("/")[1]
        self.indicators = indicators
    
    def prepare_chart(self):
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval=self.interval)

        chart_data = {}

        for indicator in self.indicators:
            chart_name = f"{self.symbol}{self.currency}_{self.interval}_{indicator}"
            if indicator == "EMA":
                chart_data[indicator] = ti.plot_chart(size=self.size, chart_name=chart_name,EMA20=True, EMA50=True, EMA100=True)    
            if indicator == "MACD":
                chart_data[indicator] = ti.plot_chart(size=self.size, chart_name=chart_name, MACD=True)
            if indicator == "ATR":
                chart_data[indicator] = ti.plot_chart(size=self.size, chart_name=chart_name, ATR14=True)
            if indicator == "RSI":
                chart_data[indicator] = ti.plot_chart(size=self.size, chart_name=chart_name, RSI14=True)
        
        return chart_data
    
    async def create_individual_analysis(self):
        chart_data = self.prepare_chart()

        coroutines = {}

        for indicator in self.indicators:
            data = chart_data[indicator]
            chart_path = f"data/chart/{self.symbol}{self.currency}_{self.interval}_{indicator}.png"
            user_message = f"The chart is uploaded. Current data of the last bar: {data}. \n Start you analysis."

            if indicator == "EMA":
                agent = MAAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
            
            if indicator == "MACD":
                agent = MACDAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
     
            if indicator == "ATR":
                agent = ATRAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)
            
            if indicator == "RSI":
                agent = RSIAgent(user_message=user_message, chart_path=chart_path, interval=self.interval)

            coroutines[indicator] = agent.run()

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
            gemini_model="gemini-2.0-flash-thinking-exp-01-21",
            user_message=formatted_analysis
        )
        agg_analysis = await agent.run_text()
        return agg_analysis

    async def run(self):
        individual_analysis = await self.create_individual_analysis()
        formatted_analysis = self.format_individual_analysis(individual_analysis)
        print(formatted_analysis)
        print()
        agg_analysis = await self.aggregate_analysis(formatted_analysis)
        return agg_analysis

if __name__ == "__main__":
    agent = Aggregate("USD/JPY", "4h")
    results = asyncio.run(agent.run())

    print(results)

    