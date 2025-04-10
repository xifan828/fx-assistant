import requests
import os
import aiohttp
import asyncio

class JinaAIScrapper:

    def __init__(self):
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
    
    async def aget(self, session: aiohttp.ClientSession, url: str):
        async with session.get(self.prefix_url + url, headers = self.headers) as response:
            return await response.text()
    
    async def aget_multiple(self, urls):
        contents = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.aget(session, url) for url in urls]
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
    jina_ai = JinaAIScrapper()

    urls = [
        "https://cn.investing.com/news/stock-market-news/article-2737375",
        "https://cn.investing.com/news/stock-market-news/article-2737263",
        "https://cn.investing.com/news/forex-news/article-2737251"
    ]

    results = asyncio.run(jina_ai.aget_multiple(urls))

    for k, v in results.items():
        print(k)
        print(v[:10000])
        print()





