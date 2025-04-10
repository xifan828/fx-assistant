
import requests
import json
from dotenv import load_dotenv
import os
from openai import OpenAI, AsyncOpenAI
import asyncio
import time

class PerplexitySearch:
    def __init__(self, model="llama-3-sonar-large-32k-online", system_message = None):
        # Load environment variables from .env file
        load_dotenv()
        self.url = "https://api.perplexity.ai/chat/completions"
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please set the PERPLEXITY_API_KEY environment variable in the .env file.")
        if system_message:
            self.system_message = system_message
        else:
            self.system_message = """As an financial assistant, your task is to give a comprehensive answer to the user query based on the given information. 
            Your audience is financial experts focused on foreign exchange rates of euro to usd. Your summary will help financial experts make informed and acurate trading decision."""
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")

    def search(self, query, temperature=0.2):
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": query}
        ]
        # chat completion without streaming
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    async def async_search(self, query, temperature=0.2):
        messages = messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": query}
        ]
        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    async def multiple_search(self, queries, temperature=0.2):
        tasks = [self.async_search(query, temperature) for query in queries]
        results = await asyncio.gather(*tasks)
        return results

if __name__ == "__main__":
    ai_search = PerplexitySearch()
    queries = [
        #"Recent FED reserve decisions affecting EUR/USD exchange rate July 2024", 
        #"Recent ECB decisions affecting EUR/USD exchange rate July 2024",
        "Latest technical analysis of EUR/USD"
    ]
    results = asyncio.run(ai_search.multiple_search(queries))
    for x in results:
        print(x)
        print()

