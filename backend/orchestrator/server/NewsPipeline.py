from backend.utils.parameters import CURRENCY_PAIRS, PAIRS
from backend.orchestrator.server.ProcessPipeline import ProcessPipeline
from backend.service.JinaAIScrapper import JinaAIScrapper
from backend.agents.news.SummaryAgent import SummaryAgent
from backend.agents.news.SynthesisAgent import SynthesisAgent
from typing import List, Dict
import os
import asyncio
import aiohttp
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

class NewsPipeline(ProcessPipeline):

    def __init__(self, k: int = 7):
        super().__init__()
        self.k = k
    
    @staticmethod
    def _process_news_urls(urls: List[str]) -> List[str]:
        """
        agg consecutive macenews into one
        """
        new_urls = []
        mace_url = ""

        if urls:
            for url in urls:
                if "macenews" in url:
                    mace_url += f"{url};" 
                else:
                    if mace_url != "":
                        new_urls.append(mace_url)
                        mace_url = ""
                    new_urls.append(url)
        
        return new_urls
    
    def get_news_urls(self):
        news_urls = {}

        for currency_pair in PAIRS:
            news_urls[currency_pair] = self._process_news_urls(self.scrape_results_curr.get(f"{currency_pair}_news_websites", []))[:self.k]
        
        return news_urls
    
    def get_new_news_urls(self) -> Dict[str, List[str]]:
        """
        Compare the current scrape results to existing news url in the summary file
        """
        news_urls = self.get_news_urls()

        new_news_urls = {}

        for currency_pair in PAIRS:

            current_news_urls = news_urls[currency_pair]   

            news_summary_file_path = os.path.join("data", "process", f"{currency_pair}_news_summary.json")

            if os.path.exists(news_summary_file_path):
                news_urls_to_add = []

                news_summary: List[Dict] = self._load_json(news_summary_file_path)
                existed_news_urls = [summary["url"] for summary in news_summary]
                
                for i, news_url in enumerate(current_news_urls):
                    if i == self.k:
                        break
                    if news_url not in existed_news_urls:
                        news_urls_to_add.append(news_url)
            
            else:
                news_urls_to_add = current_news_urls[:self.k]
            
            new_news_urls[currency_pair] = news_urls_to_add

        logger.info(f"New news URLs: {new_news_urls}")
        return new_news_urls
    
    async def fetch_and_summarize(self):
        scrapper = JinaAIScrapper()
        currency_urls = self.get_new_news_urls()
        agent_map: Dict[str, SummaryAgent]  = {
            pair: SummaryAgent(currency_pair=pair)
            for pair in PAIRS
        }

        result: Dict[str, List[Dict[str, str]]] = {
            pair: [None] * len(urls)
            for pair, urls in currency_urls.items()
        }

        async with aiohttp.ClientSession() as session:

            async def work(pair: str, idx: int, url: str):
                raw = await scrapper.aget(session, url)
                summ = await agent_map[pair].run(raw)
                return pair, idx, {"url": url, "summary": summ}
            
            all_tasks = [
                work(pair, idx, url)
                for pair, urls in currency_urls.items()
                for idx, url in enumerate(urls)
            ]

            all_results = await asyncio.gather(*all_tasks)

            for pair, idx, summary_dict in all_results:
                result[pair][idx] = summary_dict
        
        for pair in PAIRS:
            if result[pair]:
                self._save_summary_json(result[pair][::-1], os.path.join("data", "process", f"{pair}_news_summary.json"))
                logger.info(f"Saved {pair} news summary to JSON file")
        
        return result 





if __name__ == "__main__":

    pipeline = NewsPipeline(k=7)

    result = asyncio.run(pipeline.fetch_and_summarize())
