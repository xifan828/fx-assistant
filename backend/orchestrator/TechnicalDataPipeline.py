from backend.service.TwelveData import TwelveData
from backend.service.IBKRData import IBKRData
from backend.utils.technical_indicators import TechnicalIndicators
from backend.utils.technical_charts import TechnicalCharts
from backend.agents.technical_analysis import ATRAgent, MAAgent, MACDAgent, RSIAgent
from typing import List, Dict, Any, Literal
import pandas as pd

class TechnicalDataPipeline:
    def __init__(self, currency_pair: str, interval: str):
        self.currecy_pair = currency_pair
        self.interval = interval

    def get_data_from_td(self, **kwargs) -> pd.DataFrame:
        td = TwelveData(
            currency_pair=self.currecy_pair,
            interval=self.interval,
            **kwargs
        )
        return td.get_data()
    
    def get_data_from_ibkr(self) -> pd.DataFrame:
        ibkr = IBKRData(
            currency_pair=self.currecy_pair,
            interval=self.interval
        )
        return ibkr.get_data()
    
    def get_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        ti = TechnicalIndicators()
        return ti.calculate_technical_indicators(data)
    
    def prepare_data(self, data_source: Literal["TwelveData", "IBKR"], **kwargs) -> pd.DataFrame:
        if data_source == "TwelveData":
            data = self.get_data_from_td(**kwargs)
        elif data_source == "IBKR":
            data = self.get_data_from_ibkr()
        else:
            raise ValueError("Invalid data source. Choose 'TwelveData' or 'IBKR'.")
        
        if data is None or data.empty:
            raise ValueError("No data returned from the source.")
        
        return self.get_technical_indicators(data)  
    
    def prepare_chart(self, df: pd.DataFrame, size: int, analysis_type: Literal["ema", "rsi", "macd", "atr"]):
        chart_name = f"{self.interval}_{analysis_type}"
        chart = TechnicalCharts(
            currency_pair=self.currecy_pair,
            interval=self.interval,
            df=df,
            size=size,
            chart_name=chart_name
        )
        if analysis_type == "ema":
            chart.plot_chart(EMA20=True, EMA50=True, EMA100=True)
        elif analysis_type == "rsi":
            chart.plot_chart(RSI14=True)
        elif analysis_type == "macd":
            chart.plot_chart(MACD=True)
        elif analysis_type == "atr":
            chart.plot_chart(ATR14=True)
        else:
            raise ValueError("Invalid analysis type. Choose 'ema', 'rsi', 'macd', or 'atr'.")


if __name__ == "__main__":
    pipeline = TechnicalDataPipeline(currency_pair="EUR/USD", interval="1h")
    
    # Example usage:
    data = pipeline.prepare_data(data_source="TwelveData")
    pipeline.prepare_chart(data, size=48, analysis_type="ema")
    
    # data = pipeline.prepare_data(data_source="IBKR")
    # pipeline.prepare_chart(data, size=20, analysis_type="rsi")



        
    