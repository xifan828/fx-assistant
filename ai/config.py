from langchain_openai import ChatOpenAI
import google.generativeai as genai

class Config:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0, max_tokens: int = None):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def get_model(self):
        return ChatOpenAI(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)


def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

