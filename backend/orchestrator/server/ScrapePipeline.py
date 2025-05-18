from backend.service.InvestingScrapper import InvestingScrapper
from backend.service.TradingViewScrapper import TradingViewScrapper
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.utils.parameters import INVESTING_ASSETS, CURRENCY_PAIRS, ECONOMIC_INDICATORS_WEBSITES, CURRENCIES
from backend.utils.logger_config import get_logger
from backend.service.web_scrapping import TradingEconomicsScraper, FedWatchScrapper
import json
import os
from datetime import datetime
from typing import List, Dict
import asyncio

logger = get_logger(__name__)

class ScrapePipeline:

    def __init__(self, currency_pair: str):
        self.currency_pair = currency_pair
        self.dir_path = os.path.join("data", "scrape")
        os.makedirs(self.dir_path, exist_ok=True)

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
    
    def _fetech_fundamental(self) -> Dict:
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
                pair_results = asyncio.run(scr.scrape_websites(url_dict))
                results[curr.lower()] = pair_results
                logger.info(f"Fetched fundamental data for {curr}")

        except Exception as e:
            logger.error(f"Error fetching fundamental data: {e}")
            results = {}
        return results
    
    def _fetech_fed_watch(self) -> Dict[str, Dict[str, str]]:
        """
        Fetch Fed Watch data from CME Group
        """
        try:
            scr = FedWatchScrapper()
            df_rate_next, df_price_next, df_rate_end, df_price_end = scr.run()
            results = {
                "rate_next": df_rate_next.to_dict(orient="records"),
                "price_next": df_price_next.to_dict(orient="records"),
                "rate_end": df_rate_end.to_dict(orient="records"),
                "price_end": df_price_end.to_dict(orient="records")
            }
            logger.info("Fetched Fed Watch data")

            return results
        except Exception as e:
            logger.error(f"Error fetching Fed Watch data: {e}")
            return {}
        
            
    def fetch_all(self) -> Dict: 
        results = {}
        results["asset"] = {}

        asset_dict = {
            name: url
            for subdict in INVESTING_ASSETS.values()
            for name, url in subdict.items()
        }

        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {}
            # tradingview tasks
            for currency_pair in CURRENCY_PAIRS:
            #for currency_pair in ["EUR/USD"]:
                currency_pair_formatted = currency_pair.replace("/", "_").lower()
                futures[executor.submit(self._fetch_economic_calenders, currency_pair)] = f"{currency_pair_formatted}_calenders"
                #futures[executor.submit(self._fetch_tv_websites, currency_pair)] = f"{currency_pair_formatted}_news_websites"

            # # investing tasks
            # for name, url in asset_dict.items():
            #     futures[executor.submit(self._fetch_inv_asset, name, url)] = f"asset_{name}"
            
            # # economic indicators tasks
            # futures[executor.submit(self._fetech_fundamental)] = "fundamental"

            # # fed watch tasks
            # futures[executor.submit(self._fetech_fed_watch)] = "fed_watch"


            for future in as_completed(futures):
                task_name: str = futures[future]
                try:
                    result = future.result()
                    if result:
                        if "asset_" in task_name:
                            results["asset"][task_name.split("_")[1]] = result
                        else:
                            results[task_name] = result
                    else:
                        logger.warning(f"{task_name} returned None or empty result")
                except Exception as e:
                    logger.error(f"Error in task {task_name}: {e}")
        
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
        
        # delete the first record if len of records is greater than 5
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
    result = pipeline.fetch_all()
    #results = pipeline._fetech_fundamental()
    end_time = time.time()
    
    print(f"Time taken: {end_time - begin_time} seconds")
    
    # for k, v in results.items():
    #     print(f"{k}: {v}")
    #     print("\n\n")

