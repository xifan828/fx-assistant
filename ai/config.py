from langchain_openai import ChatOpenAI
import google.generativeai as genai
import os

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

    async def call_gemini_vision_api(self, user_message, history=[], image_path=None):
        try:
            if image_path:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at path: {image_path}")
                    return None
                files = [
                self.upload_to_gemini(image_path, mime_type="image/png"),
                ]
            chat_session = self.model.start_chat(history=history)
            response = chat_session.send_message([user_message, files[0]]).text
            return response, chat_session.history
        
        except Exception as e:
            print(f"Error in call_api: {e}")
            return None
    
    async def call_gemini_text_api(self, user_message, history=[]):
        try:
            chat_session = self.model.start_chat(history=history)
            response = chat_session.send_message(user_message).text
            return response, chat_session.history
        
        except Exception as e:
            print(f"Error in call_api: {e}")
            return None

