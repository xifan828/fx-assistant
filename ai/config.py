from langchain_openai import ChatOpenAI

class Config:
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0):
        self.model_name = model_name
        self.temperature = temperature
    
    def get_model(self):
        return ChatOpenAI(model=self.model_name, temperature=self.temperature)


