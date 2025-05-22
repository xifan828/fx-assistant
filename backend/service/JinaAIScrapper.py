import requests
import os
import aiohttp
import asyncio
from typing import List, Dict
from backend.utils.logger_config import get_logger
from dotenv import load_dotenv

logger = get_logger(__name__)

class JinaAIScrapper:

    def __init__(self):
        load_dotenv()
        self.prefix_url = "https://r.jina.ai/"
        self.jina_api_key = os.getenv("JINA_AI_API_KEY")

        self.headers = {
            'Authorization': f"Bearer {self.jina_api_key}",
            'X-Return-Format': 'text'
        }
    
    def get(self, url):
        try:
            response = requests.get(self.prefix_url + url, headers=self.headers)
            return response.text
        except Exception as e:
            print(f"Exception occured for {url}: {e}")
            return ""
    
    async def aget(self, session: aiohttp.ClientSession, url: str, retries: int = 3, backoff_factor: float = 0.5):
        if "macenews" in url:
            return url
        for attempt in range(retries):
            try:
                async with session.get(self.prefix_url + url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {url}: {response.status}")
                        raise Exception(f"Failed to fetch {url}: {response.status}")
                    else:
                        logger.info(f"Fetched {url}: {response.status}")
                    return await response.text()
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(backoff_factor * (2 ** attempt))
                else:
                    logger.error(f"All {retries} attempts failed for {url}")
                    return f"Failed to fetch data from {url}"
    
    async def aget_multiple(self, urls) -> List[Dict]:
        contents = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                if "macenews" in url:
                    tasks.append(asyncio.sleep(0, result=url))
                else:
                    tasks.append(self.aget(session, url))

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    print(f"Exception occurred for {urls[i]}: {response}")
                    contents.append("")
                else:
                    contents.append(response)
        results = [
            {"url": url, "content": content} for url, content in zip(urls, contents)
        ]   
        return results


        


if __name__ == "__main__":
    import time
    jina_ai = JinaAIScrapper()

    urls = [
        "https://cn.investing.com/news/stock-market-news/article-2737375",
        "https://cn.investing.com/news/stock-market-news/article-2737263",
        "https://cn.investing.com/news/forex-news/article-2737251"
    ]
    begin_time = time.time()

    # for url in urls:
    #     print(jina_ai.get(url))

    results = asyncio.run(jina_ai.aget_multiple(urls))
    print(results)

    end_time = time.time()

    print(f"Duration: {end_time - begin_time:.2f} seconds")






