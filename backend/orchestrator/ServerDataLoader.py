import os
import json
from typing import List, Dict, Literal
import aiofiles
from fastapi import HTTPException


class AsyncDataLoader:
    def __init__(self):
        self.scrape_dir = os.path.join("data", "scrape")
        self.process_dir = os.path.join("data", "process")
        self.news_dir = os.path.join(self.process_dir, "news")
        self.calendar_dir = os.path.join(self.process_dir, "calender")
        self.fundamental_dir = os.path.join(self.process_dir, "fundamental")
        self.fedwatch_dir = os.path.join(self.process_dir, "fedwatch")
        self.risk_sentiment_dir = os.path.join(self.process_dir, "risk_sentiment")

    async def _load_json(self, file_path: str) -> List[Dict]:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()
            return json.loads(content)
    
    def catch_json_errors(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=f"File not found: {e}.")
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"JSON decode error: {e}.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}.")
        return wrapper
    
    @catch_json_errors
    async def get_scrape_results(self) -> Dict:
        file_path = os.path.join(self.scrape_dir, "results.json")
        scrape_results: Dict = await self._load_json(file_path)
        return scrape_results[-1]

    @catch_json_errors
    async def get_news_synthesis(self, currency_pair: Literal["eur_usd", "gbp_usd", "usd_jpy", "usd_cnh"]) -> Dict[str, str]:
        file_path = os.path.join(self.news_dir, f"{currency_pair}_news_synthesis.json")
        news_data: Dict[str, str] = await self._load_json(file_path)
        return news_data[-1]
    
    @catch_json_errors
    async def get_calender_synthesis(self, currency_pair: Literal["eur_usd", "gbp_usd", "usd_jpy", "usd_cnh"]) -> Dict[str, str]:
        file_path = os.path.join(self.calendar_dir, f"{currency_pair}_calender_analysis.json")
        calendar_data: Dict[str, str] = await self._load_json(file_path)
        return calendar_data[-1]
    
    @catch_json_errors
    async def get_fedwatch_synthesis(self) -> Dict[str, str]:
        file_path = os.path.join(self.fedwatch_dir, "analysis.json")
        fedwatch_analysis: Dict[str, str] = await self._load_json(file_path)
        fedwatch_analysis = fedwatch_analysis[-1]

        scrape_results = await self.get_scrape_results()
        fedwatch_data = scrape_results["data"]["fed_watch"]

        fedwatch_analysis["data"] = fedwatch_data

        return fedwatch_analysis
    
    @catch_json_errors
    async def get_fundamental_synthesis(self, currency_pair: Literal["eur_usd", "gbp_usd", "usd_jpy", "usd_cnh"]) -> Dict[str, str]:
        file_path = os.path.join(self.fundamental_dir, f"{currency_pair}_analysis.json")
        fundamental_analysis: Dict[str, str] = await self._load_json(file_path)
        return fundamental_analysis[-1]
    
    @catch_json_errors
    async def get_risk_sentiment_synthesis(self, currency_pair: Literal["eur_usd", "gbp_usd", "usd_jpy", "usd_cnh"]) -> Dict[str, str]:
        file_path = os.path.join(self.risk_sentiment_dir, "risk_sentiment.json")
        asset_data_path = os.path.join(self.risk_sentiment_dir, "asset_data.json")

        risk_sentiment_analysis: List[Dict] = await self._load_json(file_path)
        risk_sentiment_analysis = risk_sentiment_analysis[-1]

        asset_data: List[Dict] = await self._load_json(asset_data_path)
        asset_data = asset_data[-1]
    
        currency_pair_formatted = currency_pair.replace("_", "/").upper()
        risk_sentiment_analysis = risk_sentiment_analysis[currency_pair_formatted]
        risk_sentiment_analysis["data"] = asset_data

        return risk_sentiment_analysis
    

if __name__ == "__main__":
    import asyncio

    data_loader = AsyncDataLoader()

    result = asyncio.run(data_loader.get_risk_sentiment_synthesis("eur_usd"))

    #result = asyncio.run(data_loader.get_fedwatch_synthesis())

    print(result)

    