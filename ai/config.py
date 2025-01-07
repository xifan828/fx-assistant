from langchain_openai import ChatOpenAI
import google.generativeai as genai
import os
import asyncio
import mimetypes
import aiofiles  # Install with: pip install aiofiles
import google.generativeai as genai
from google.generativeai.types import generation_types

class Config:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0, max_tokens: int = None):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def get_model(self):
        return ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)

class GeminiClient:
    def __init__(self, model_name: str, generation_config: dict, system_instruction: str = None):
        self.model_name = model_name
        self.generation_config = generation_config
        self.system_instruction = "You are a helpful assistant" if system_instruction is None else system_instruction
        self.model = self.get_model()
    
    def get_model(self):
        return genai.GenerativeModel(model_name=self.model_name, generation_config=self.generation_config, system_instruction=self.system_instruction)

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


    async def call_gemini_vision_api(self, user_message, history=[], image_path=None):
        try:
            chat_session = self.model.start_chat(history=history)
            parts = [user_message]
            if image_path:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at path: {image_path}")
                    return None
                
                mime_type, _ = mimetypes.guess_type(image_path)
                image_data = await self.read_file_async(image_path)
                parts.append(
                {"mime_type": mime_type, "data": image_data}
                )

            response = await chat_session.send_message_async(parts)
            response_text = response.text
            return response_text, chat_session.history
        
        except Exception as e:
            print(f"Error in call_api: {e}")
            return None
    
    async def call_gemini_text_api(self, user_message, history=[]):
        try:
            chat_session = self.model.start_chat(history=history)
            response = await chat_session.send_message_async(user_message)
            response_text = response.text
            return response_text, chat_session.history
        
        except Exception as e:
            print(f"Error in call_api: {e}")
            return None
    
    def call_gemini_vision_api_sync(self, user_message, history=None, image_path=None):
        if history is None:
            history = []
        try:
            files = []
            if image_path:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at path: {image_path}")
                    return None
                files = [self.upload_to_gemini(image_path, mime_type="image/png")]
            
            chat_session = self.model.start_chat(history=history)
            # 'files[0]' only applies if we actually have a file
            if files:
                response = chat_session.send_message([user_message, files[0]]).text
            else:
                response = chat_session.send_message(user_message).text
            
            return response, chat_session.history

        except Exception as e:
            print(f"Error in call_api: {e}")
            return None


