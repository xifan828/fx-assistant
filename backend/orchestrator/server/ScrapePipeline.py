from backend.service.InvestingScrapper import InvestingScrapper
from backend.service.TradingViewScrapper import TradingViewScrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.utils.parameters import INVESTING_ASSETS, CURRENCY_PAIRS
from backend.utils.logger_config import get_logger
import json
import os
from datetime import datetime
from typing import List, Dict

logger = get_logger(__name__)

class ScrapePipeline:

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair

    def _fetch_technicals(self, currency_pair: str):
        scr = TradingViewScrapper(currency_pair)
        try:
            scr.get_technical_indicators()
        finally:
            scr.quit_driver()
        
    def _fetch_economic_calenders(self, currency_pair: str):
        scr = TradingViewScrapper(currency_pair)
        try:
            scr.get_economic_calenders()
        except Exception as e:
            logger.error(f"Error fetching economic calenders for {currency_pair}: {e}")
        finally:
            scr.quit_driver()
    
    def _fetch_tv_websites(self, currency_pair: str) -> List[str]:
        scr = TradingViewScrapper(currency_pair)
        try:
            logger.info(f"Fetching news websites for {currency_pair}")
            links = scr.get_news_websites()
            logger.info(f"Fetched news links for {currency_pair}")
            return links
        except Exception as e:
            logger.error(f"Error fetching news websites for {currency_pair}: {e}")
            return []
        finally:
            scr.quit_driver()
    
    def _fetch_inv_asset(self, name: str, url: str) -> List[str]:
        scr = InvestingScrapper(self.currency_pair)
        try:
            data = scr.get_asset(name, url)
            return data
        finally:
            scr.quit_driver()

    def fetch_all(self) -> Dict: 
        results = {}

        asset_dict = {
            name: url
            for subdict in INVESTING_ASSETS.values()
            for name, url in subdict.items()
        }

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {}
            # tradingview tasks
            for currency_pair in CURRENCY_PAIRS:
                currency_pair_formatted = currency_pair.replace("/", "_").lower()
                futures[executor.submit(self._fetch_economic_calenders, currency_pair)] = f"{currency_pair_formatted}_calenders"
                futures[executor.submit(self._fetch_tv_websites, currency_pair)] = f"{currency_pair_formatted}_news_websites"

            # investing tasks
            for name, url in asset_dict.items():
                futures[executor.submit(self._fetch_inv_asset, name, url)] = name


            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        results[task_name] = result
                    else:
                        logger.warning(f"{task_name} returned None or empty result")
                except Exception as e:
                    print(f"{task_name} generated an exception: {e}")
        
        dir_path = os.path.join("data", "scrape")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        self.save_to_json(results, filename=os.path.join(dir_path, "results.json"))
        logger.info(f"Results saved to JSON file")

        return results
    
    def save_to_json(self, data: dict, filename: str):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                records = json.load(f)
        else:
            records = []
        
        records.append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    import time

    begin_time = time.time()
    currency_pair = "EUR/USD"
    pipeline = ScrapePipeline(currency_pair)
    result = pipeline.fetch_all()
    end_time = time.time()
    
    print(f"Time taken: {end_time - begin_time} seconds")
        

