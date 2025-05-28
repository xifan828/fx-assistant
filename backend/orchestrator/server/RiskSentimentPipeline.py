from backend.agents.sentiment.RiskSentimentAgent import RiskSentimentAgent, RiskSentimentAnalysis, AssetData, ExtractAssetAgent
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.utils.parameters import CURRENCY_PAIRS, INVESTING_ASSETS
from backend.utils.logger_config import get_logger
from typing import List, Dict, Union
import pandas as pd
import os
import asyncio
from datetime import datetime
import aiohttp
from backend.service.JinaAIScrapper import JinaAIScrapper
from collections import defaultdict


logger = get_logger(__name__)


class RiskSentimentPipeline(ProcessPipeline):
    def __init__(self, extraction_model_name: str = "gpt-4.1-mini-2025-04-14", synthesis_model_name: str = "gpt-4.1-mini-2025-04-14", temperature: float = 0.2):
        super().__init__()
        self.synthesis_model_name = synthesis_model_name
        self.extraction_model_name = extraction_model_name
        self.temperature = temperature
        self.dir_path = os.path.join("data", "process", "risk_sentiment")
        os.makedirs(self.dir_path, exist_ok=True)
    
    def _compute_spreads(self, results_df: pd.DataFrame, currency_pair: str) -> str:
        us_2y_yield = float(results_df[results_df['Asset'] == 'US 2Y Yield']['Last Price'].values[0])
        us_10y_yield = float(results_df[results_df['Asset'] == 'US 10Y Yield']['Last Price'].values[0])
        if currency_pair == "EUR/USD":
            germany_2y_yield = float(results_df[results_df['Asset'] == 'Germany 2Y Yield']['Last Price'].values[0])
            germany_10y_yield = float(results_df[results_df['Asset'] == 'Germany 10Y Yield']['Last Price'].values[0])
            us_germany_2y_spread = us_2y_yield - germany_2y_yield
            us_germany_10y_spread = us_10y_yield - germany_10y_yield
            spread_str = f"US 2Y - Germany 2Y spread: {us_germany_2y_spread:.2f} bps\nUS 10Y - Germany 10Y spread: {us_germany_10y_spread:.2f} bps"
        elif currency_pair == "USD/JPY":
            japan_2y_yield = float(results_df[results_df['Asset'] == 'Japan 2Y Yield']['Last Price'].values[0])
            japan_10y_yield = float(results_df[results_df['Asset'] == 'Japan 10Y Yield']['Last Price'].values[0])
            us_japan_2y_spread = us_2y_yield - japan_2y_yield
            us_japan_10y_spread = us_10y_yield - japan_10y_yield
            spread_str = f"US 2Y - Japan 2Y spread: {us_japan_2y_spread:.2f} bps\nUS 10Y - Japan 10Y spread: {us_japan_10y_spread:.2f} bps"
        elif currency_pair == "GBP/USD":
            uk_2y_yield = float(results_df[results_df['Asset'] == 'UK 2Y Yield']['Last Price'].values[0])
            uk_10y_yield = float(results_df[results_df['Asset'] == 'UK 10Y Yield']['Last Price'].values[0])
            us_uk_2y_spread = us_2y_yield - uk_2y_yield
            us_uk_10y_spread = us_10y_yield - uk_10y_yield
            spread_str = f"US 2Y - UK 2Y spread: {us_uk_2y_spread:.2f} bps\nUS 10Y - UK 10Y spread: {us_uk_10y_spread:.2f} bps"
        elif currency_pair == "USD/CNH":
            china_2y_yield = float(results_df[results_df['Asset'] == 'China 2Y Yield']['Last Price'].values[0])
            china_10y_yield = float(results_df[results_df['Asset'] == 'China 10Y Yield']['Last Price'].values[0])
            us_china_2y_spread = us_2y_yield - china_2y_yield
            us_china_10y_spread = us_10y_yield - china_10y_yield
            spread_str = f"US 2Y - China 2Y spread: {us_china_2y_spread:.2f} bps\nUS 10Y - China 10Y spread: {us_china_10y_spread:.2f} bps"
        return spread_str
    
    def _prepare_assets_data(self, currency_pair: str, asset_data: Dict[str, Dict[str, str]]) -> str:
        try:
            symbol = currency_pair.split("/")[0]
            currency = currency_pair.split("/")[1]
            general_asset_names = INVESTING_ASSETS["general"].keys()
            symbol_asset_names = INVESTING_ASSETS[symbol].keys()
            currency_asset_names = INVESTING_ASSETS[currency].keys()
            all_asset_names = list(general_asset_names) + list(symbol_asset_names) + list(currency_asset_names)

            data = [{"Asset": name, **asset_data.get(name, None)} for name in all_asset_names]
            df = pd.DataFrame(data)
            df.columns = ["Asset", "Last Price", "Change", "Change Percentage"]
            assests_str = str(data) + "\n\n" + self._compute_spreads(df, currency_pair)
        except Exception as e:
            logger.error(f"Error preparaing asset data for {currency_pair} for risk sentiment synthetis: {e}")
            assests_str = f"Error preparaing asset data for {currency_pair}: {e}"
        return assests_str

    async def _scrape_and_extract_asset_data(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape data from Investing.com using JinaAI and extract asset data using OpenAI
        """
        asset_data: Dict[str, Dict[str, str]] = defaultdict(lambda: defaultdict(dict))
        extra_headers = {
            "X-Return-Format": "text",
            "X-No-Cache": "true",
            "X-With-Links-Summary": "true"
        }
        scrapper = JinaAIScrapper(extra_headers)
        extractor = ExtractAssetAgent(model_name=self.extraction_model_name, temperature=self.temperature)

        async with aiohttp.ClientSession() as session:
            
            async def work(category: str, asset_name: str, url: str):
                try:
                    raw: str = await scrapper.aget(session, url)
                    assetdata: AssetData = await extractor.extract_asset_data(asset_name=asset_name, scrape_results=raw)
                except Exception as e:
                    logger.error(f"Error extracting asset data for {asset_name}: {e}")
                    assetdata: AssetData = AssetData(
                        last_price=0.0,
                        change=0.0,
                        change_percentage=0.0
                    )
                return category, asset_name, assetdata
            
            tasks = [
                work(category, asset_name, url)
                for category, category_dict in INVESTING_ASSETS.items()
                for asset_name, url in category_dict.items()
            ]

            try: 
                all_results = await asyncio.gather(*tasks)
                logger.info(f"Extracted asset data for {len(all_results)} assets")
            except Exception as e:
                logger.error(f"Error during gathering tasks: {e}")
                raise

        for category, asset_name, assetdata in all_results:
            asset_data[asset_name] = assetdata.dict()
        
        # save asset data
        asset_data_file_path = os.path.join(self.dir_path, "asset_data.json")
        self._save_results(data=asset_data, file_path=asset_data_file_path, truncate=True, limit=5)
        return asset_data

    def _fetch_news_synthesis(self, currency_pair: str) -> Union[str, Dict[str, str]]:
        currency_pair = currency_pair.replace("/", "_").lower()
        news_summary_file_path = os.path.join("data", "process", "news", f"{currency_pair}_news_synthesis.json")
        try:
            if os.path.exists(news_summary_file_path):
                news_synthesis: Dict[str, str] = self._load_json(news_summary_file_path)[-1]
            else:
                news_synthesis = "No news summary available."
        except Exception as e:
            logger.error(f"Error loading news synthesis for {currency_pair}: {e}")
            news_synthesis = f"Error loading news synthesis for {currency_pair}: {e}"
        return news_synthesis

    async def synthesize_sentiments(self) -> Dict[str, Dict[str, str]]:
        
        agent_map = {
            pair: RiskSentimentAgent(currency_pair=pair, model_name=self.synthesis_model_name, temperature=self.temperature)
            for pair in CURRENCY_PAIRS
        }

        all_assets = await self._scrape_and_extract_asset_data()

        tasks = []

        async def safe_synthesize(pair: str, assets_data: str, news_summary: str):
            try:
                return await agent_map[pair].analyze_risk_sentiment(assets_data=assets_data, news_summary=news_summary)
            except Exception as e:
                logger.error(f"Error synthesizing sentiment for {pair}: {e}")
                # Return a default synthesis indicating an error
                return RiskSentimentAnalysis(
                            risk_sentiment_analysis="Analysis failed",
                            key_market_drivers="",
                            implications_for_trading="",
                            conclusion="",
                            risk_sentiment="neutral")

        for pair in CURRENCY_PAIRS:
            assets_data = self._prepare_assets_data(pair, all_assets)
            news_summary = self._fetch_news_synthesis(pair)
            tasks.append(safe_synthesize(pair, assets_data, news_summary))
        
        results = await asyncio.gather(*tasks)

        sentiment_results = {}
        for pair, result in zip(CURRENCY_PAIRS, results):

            result = result.dict()
            result["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            sentiment_results[pair] = result
        
        self._save_risk_sentiment_json(sentiment_results, os.path.join(self.dir_path, "risk_sentiment.json"))
        logger.info(f"Risk sentiment analysis results saved to json")
        
        return sentiment_results

    async def run(self):
        result = await self.synthesize_sentiments()
        return result

if __name__ == "__main__":
    pipeline = RiskSentimentPipeline()
    #asset_data = asyncio.run(pipeline._scrape_and_extract_asset_data())

    asyncio.run(pipeline.synthesize_sentiments())