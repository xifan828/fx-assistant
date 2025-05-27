from backend.service.TradingViewScrapper import TradingViewJinaScrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.utils.parameters import INVESTING_ASSETS, CURRENCY_PAIRS, ECONOMIC_INDICATORS_WEBSITES, CURRENCIES
from backend.utils.logger_config import get_logger
from backend.service.web_scrapping import TradingEconomicsScraper
from backend.service.FedWatchScrapper import FedWatchScrapper
import json
import os
from datetime import datetime
from typing import List, Dict
import asyncio
import aiohttp

logger = get_logger(__name__)

class ScrapePipeline:

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        self.dir_path = os.path.join("data", "scrape")
        os.makedirs(self.dir_path, exist_ok=True)
    
    async def _fetch_tv_websites(self, currency_pair: str, session: aiohttp.ClientSession) -> List[str]:
        scr = TradingViewJinaScrapper(currency_pair=currency_pair)
        try:
            logger.info(f"Fetching news websites for {currency_pair}")
            links = await scr.get_news_websites(session=session)
            logger.info(f"Fetched news links for {currency_pair}")
            return links
        except Exception as e:
            logger.error(f"Error fetching news websites for {currency_pair}: {e}")
            return []

    
    async def _fetech_fundamental(self, session) -> Dict:
        """
        Fetch fundamental data from TradingEconomics
        """
        try:
            results = {}
            for curr in CURRENCIES:
                results[curr.lower()] = {}
                logger.info(f"Fetching fundamental data for {curr}")
                url_dict = ECONOMIC_INDICATORS_WEBSITES[curr.upper()]
                scr = TradingEconomicsScraper()
                pair_results = await scr.scrape_websites(url_dict, session=session)
                results[curr.lower()] = pair_results
                logger.info(f"Fetched fundamental data for {curr}")

        except Exception as e:
            logger.error(f"Error fetching fundamental data: {e}")
            results = {}
        return results
    
    async def _fetech_fed_watch(self, session) -> Dict[str, Dict[str, str]]:
        """
        Fetch Fed Watch data from CME Group
        """
        try:
            scr = FedWatchScrapper()
            results = await scr.run(session=session)
            results = results.model_dump()

            return results
        except Exception as e:
            logger.error(f"Error fetching Fed Watch data: {e}")
            return {}
        
            
    async def fetch_all(self) -> Dict: 

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_tv_websites(currency_pair, session)
                for currency_pair in CURRENCY_PAIRS
            ]
            tasks.append(self._fetech_fundamental(session))
            tasks.append(self._fetech_fed_watch(session))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        
        # dir_path = os.path.join("data", "scrape")
        # if not os.path.exists(dir_path):
        #     os.makedirs(dir_path)

        # self.save_to_json(results, filename=os.path.join(dir_path, "results.json"))
        # logger.info(f"Results saved to JSON file")

        return results
    
    def save_to_json(self, data: dict, filename: str):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                records = json.load(f)
        else:
            records = []
        
        if len(records) >= 5:
            records.pop(0)
            
        records.append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })

        temp_filename = filename + ".tmp"
        with open(temp_filename, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
        
        os.replace(temp_filename, filename)
    


if __name__ == "__main__":
    import time

    begin_time = time.time()
    currency_pair = "EUR/USD"
    pipeline = ScrapePipeline(currency_pair)
    result = asyncio.run(pipeline.fetch_all())
    print(result)
    #results = pipeline._fetech_fundamental()
    end_time = time.time()
    
    print(f"Time taken: {end_time - begin_time} seconds")
    
    # for k, v in results.items():
    #     print(f"{k}: {v}")
    #     print("\n\n")

