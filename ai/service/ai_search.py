
import requests
import json
from dotenv import load_dotenv
import os


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

    def search(self, query, temperature=0.2, top_k=5):
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_message
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": temperature,
            "return_citations": True,
            "return_images": True,
            "top_k": top_k
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(self.url, json=payload, headers=headers)
        if response.status_code == 200:
            content = json.loads(response.text)["choices"][0]["message"]["content"]
            return content
        else:
            response.raise_for_status()


if __name__ == "__main__":
    ai_search = PerplexitySearch()
    print(ai_search.search("What are the latest news which could impact euro to usd pair?", top_k=5))
