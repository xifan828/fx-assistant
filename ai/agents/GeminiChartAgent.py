from abc import ABC, abstractmethod
import os
from ai.config import GeminiClient

class GeminiChartAgent(ABC):

    def __init__(self, chart_path: str, gemini_model: str = None, gemini_api_key: str = None, generation_config: dict = None, user_message: str = None):
        self.gemini_model = gemini_model if gemini_model is not None else "gemini-2.0-flash"

        self.gemini_api_key = gemini_api_key if gemini_api_key is not None else os.environ["GEMINI_API_KEY_XIFAN"]

        if generation_config is None:
            self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        else:
            self.generation_config = generation_config

        self.chart_path = chart_path

        self.user_message = user_message if user_message is not None else "The chart is provided. Please start your analysis."

    @property
    @abstractmethod
    def system_message(self):
        """Return the custom system message for the agent."""
        pass

    async def run(self):
        client = GeminiClient(
            model_name=self.gemini_model,
            generation_config=self.generation_config,
            api_key=self.gemini_api_key,
            system_instruction=self.system_message
        )
        try:
            response, _ = await client.call_gemini_vision_api(
                user_message=self.user_message,
                image_path=self.chart_path
            )
            return response
        except Exception as e:
            print(f"Error in analyzing chart: {e}")
            return None
