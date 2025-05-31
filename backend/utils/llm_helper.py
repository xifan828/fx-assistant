from langchain_openai import ChatOpenAI
import os
import asyncio
import mimetypes
import aiofiles  # Install with: pip install aiofiles
from google import genai
from google.genai import types
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel

class Config:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0, max_tokens: int = None):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def get_model(self):
        return ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)

class OpenAIClient:
    def __init__(self, model: str, temperature: float = 0.2, reasoning_effort: str = "medium"):
        load_dotenv()
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
        self.temperature = temperature
        self.reading_effort = reasoning_effort

    async def chat_completion(self, messages,  **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in chat_completion: {e}")
            raise e
    
    async def structured_chat_completion(self, messages: List, response_format: BaseModel, **kwargs) -> BaseModel:
        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=self.temperature,
                **kwargs
            )

            return response.choices[0].message.parsed

        except Exception as e:
            print(f"Error in structured_chat_completion: {e}")
            raise e

class GeminiClient:
    def __init__(self, model_name: str, generation_config: dict, api_key: str, system_instruction: str = None):
        self.model_name = model_name
        self.generation_config = generation_config
        self.system_instruction = "You are a helpful assistant" if system_instruction is None else system_instruction
        self.generation_config["system_instruction"] = self.system_instruction
        self.api_key = api_key
        self.client = self.get_client()
    
    def get_client(self):
        client = genai.Client(api_key=self.api_key)
        return client

    def upload_to_gemini(self, path, mime_type=None):
        """Uploads the given file to Gemini.

        See https://ai.google.dev/gemini-api/docs/prompting_with_media
        """
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    
    async def read_file_async(self, file_path):
        """Reads a file asynchronously and returns its content as bytes."""
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()


    async def call_gemini_vision_api(self, user_message, history=[], image_path=None, image_data=None):
        try:
            chat_session = self.client.aio.chats.create(history=history,
                                                    model=self.model_name,
                                                    config=self.generation_config
                                                    )
            parts = [user_message]
            if image_path:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at path: {image_path}")
                    return None
                
                mime_type, _ = mimetypes.guess_type(image_path)
                image_data = await self.read_file_async(image_path)
            elif image_data:
                mime_type = "image/png" 
                
            parts.append(
            types.Part.from_bytes(data=image_data, mime_type=mime_type)
            )

            response = await chat_session.send_message(parts)
            response_text = response.text
            return response_text, chat_session
        
        except Exception as e:
            print(f"Error in call_api: {e}, api is {self.api_key}")
            raise e
    
    async def call_gemini_api(self, user_message, history=[]):
        try:
            chat_session = self.client.aio.chats.create(
                history=history,
                model=self.model_name,
                config=self.generation_config
            )
            response = await chat_session.send_message(user_message) # Pass user_message directly
            response_text = response.text
            return response_text, chat_session

        except Exception as e:
            print(f"Error in call_gemini_api: {e}, api key is {self.api_key}")
            raise e


async def main():

    generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
    
    model_name = "gemini-2.0-flash-thinking-exp-01-21"

    system_instruction = "Call the user as Dr. Wang."

    client = GeminiClient(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=system_instruction,
        api_key=os.environ["GEMINI_API_KEY_XIFAN"]
    )
    # image_path = "data/chart/1h.png"

    # response, chat_session = await client.call_gemini_vision_api(
    #     user_message="describe this image briefly.", image_path=image_path
    # )

    response, chat_session = await client.call_gemini_api(
        user_message="What is quantitative trading ?"
    )

    print(response)
    return response, chat_session


if __name__ == "__main__":
    asyncio.run(main())
