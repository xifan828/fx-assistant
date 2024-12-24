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
    def __init__(self):
        pass

    def upload_to_gemini(self, path, mime_type=None):
        """Uploads the given file to Gemini.

        See https://ai.google.dev/gemini-api/docs/prompting_with_media
        """
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file

    async def call_gemini_api(self, model, user_message, history=[], image_path=None):
        try:
            if image_path:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at path: {image_path}")
                    return None
                files = [
                self.upload_to_gemini(image_path, mime_type="image/png"),
                ]
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message([user_message, files[0]]).text
            return response
        
        except Exception as e:
            print(f"Error in call_api: {e}")
            return None

