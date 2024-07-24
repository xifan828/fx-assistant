import os
from ai.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from ai.service.technical_indicators import TechnicalIndicators

class TechnicalAnalysis:
    def __init__(self, analysis_model = None, synthesis_model = None):
        self.analysis_model = analysis_model if analysis_model is not None else Config(model_name="gpt-4o-mini", temperature=1.0, max_tokens=512).get_model()
        self.synthesis_model = synthesis_model if synthesis_model is not None else Config(model_name="gpt-4o-mini", temperature=1.0, max_tokens=1024).get_model()

        self.system_prompt_chart = """You are an expert forex analyst specializing in EUR/USD pair technical analysis. You will analyze the user's EUR/USD price chart images. Retail Forex traders will use your analysis to make informed trading decisions and manage risk.
For the chart:
- Recognize significant chart patterns.
- Determine overall trend direction.
- Provide short-term price outlook
Provide clear, concise, and actionable analysis. Use professional terminology with brief explanations. AVOID making forex trading risks and the importance of personal research."""

        self.system_prompt_technicals = """You are an expert forex analyst specializing in EUR/USD pair technical indicators analysis. You will analyze the user's EUR/USD technical indicator images. Retail Forex traders will use your analysis to make informed trading decisions and manage risk.
For the technical indicators:
- Interpret moving averages (e.g., Simple, Exponential) and their crossovers.
- Analyze oscillators (e.g., RSI, MACD, Stochastic) for overbought/oversold conditions and divergences.
- Evaluate trend strength indicators (e.g., ADX).
- Provide short-term trading sentiment based on indicator readings.
Provide clear, concise, and actionable analysis. Use professional terminology with brief explanations. AVOID discussing forex trading risks and the importance of personal research."""

        self.system_prompt_pivot = """You are an expert forex analyst specializing in EUR/USD pair technical analysis, with a focus on pivot points. You will analyze the user's EUR/USD pivot point chart images. Retail Forex traders will use your analysis to make informed trading decisions and manage risk. 
For the pivot point chart:
- Identify the standard pivot point (P) and key support/resistance levels (S1, S2, S3, R1, R2, R3).
- Determine how current price relates to these pivot levels.
- Recognize potential breakouts or reversals near pivot levels.
- Assess overall trend direction based on price action around pivot points.
- Provide short-term price outlook considering pivot level interactions. 
Provide clear, concise, and actionable analysis. Use professional terminology with brief explanations. AVOID making forex trading risks and the importance of personal research."""

        self.system_prompt_synthesis = """You are an advanced forex analysis synthesizer specializing in the EUR/USD pair. Your role is to integrate and interpret multiple analyses across various timeframes and technical indicators. Retail Forex traders will use your synthesized insights to make informed trading decisions and manage risk.
For the synthesized analysis:
- Compile and evaluate chart analyses from 1-day, 5-day, and 1-month timeframes.
- Integrate technical indicator readings from 1-hour, 4-hour, and 1-day intervals.
- Identify consistent patterns or conflicting signals across timeframes.
- Determine the overall market sentiment and potential trend direction.
- Highlight key support and resistance levels that align across multiple analyses.
- Provide a comprehensive short to medium-term outlook for EUR/USD.
Deliver a clear, concise, and actionable synthesis. Prioritize the most significant insights that emerge from combining multiple analyses. Use professional terminology with brief explanations when necessary. AVOID discussing forex trading risks and the importance of personal research."""

        self.encoded_image_template = "data:image/png;base64,{base64_image}"
    
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def create_analysis_chain(self):
        system_message = SystemMessage(content="{system_prompt}")
        user_message = HumanMessage(
            content=[
                {"type": "text", "text": "{file_name} is uploaded. The current EUR/USD price is {price_now}. In today, open price is {price_open}, daily highest is {daily_high}, daily lowest is {daily_low}"},
                {"type": "image_url", "image_url": {"url": "{encoded_image}"}},  # Use base64 string here
            ]
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message.content),
            ("user", user_message.content)
        ])
        chain = prompt | self.analysis_model | StrOutputParser()
        return chain
    
    def create_analysis_tasks(self):
        encoded_images = {}
        for file_name in os.listdir("data/"):
            if file_name.endswith("png"):
                encoded_images[file_name.split(".")[0]] = self.encoded_image_template.format(base64_image=self.encode_image(f"data/{file_name}"))

        ti = TechnicalIndicators(interval="1m", period="1d")
        ti.download_data()
        data = ti.data
        price_open = data.iloc[0, 0].round(4)
        price_now = data.iloc[-1, 0].round(4)
        daily_low = data["Close"].min().round(4)
        daily_high = data["Close"].max().round(4)

        tasks = []
        for file_name, encoded_image in encoded_images.items():
            if "eur_usd" in file_name:
                input_dic = {
                    "file_name": file_name, "price_now": price_now, "price_open": price_open, "daily_high": daily_high, "daily_low": daily_low, "system_prompt": self.system_prompt_chart, "encoded_image": encoded_image
                }
            if "technicals" in file_name:
                input_dic = {
                    "file_name": file_name, "price_now": price_now, "price_open": price_open, "daily_high": daily_high, "daily_low": daily_low, "system_prompt": self.system_prompt_technicals, "encoded_image": encoded_image
                }
            if "pivot" in file_name:
                input_dic = {
                    "file_name": file_name, "price_now": price_now, "price_open": price_open, "daily_high": daily_high, "daily_low": daily_low, "system_prompt": self.system_prompt_pivot, "encoded_image": encoded_image
                }
            tasks.append(input_dic)
        return tasks
    
    def formulate_analysis_results(self, tasks, results):
        results_formulated = ""
        for task, result in zip(tasks, results):
            image_name = task["file_name"]
            if "eur_usd" in image_name:
                chart_range = " ".join(image_name.split("_")[-2:])
                temp_str = f"```\nAnalysis on the EUR USD chart within {chart_range}\n{result}\n```\n"
            if "technicals" in image_name:
                technical_interval = " ".join(image_name.split("_")[-3:])
                temp_str = f"```\nAnalysis on the EUR USD technical indicators with {technical_interval}\n{result}\n```\n"
            if "pivot" in image_name:
                technical_interval = " ".join(image_name.split("_")[-3:])
                temp_str = f"```\nAnalysis on the EUR USD pivot points with {technical_interval}\n{result}\n```\n"
            results_formulated += temp_str
        return results_formulated
    
    def create_synthesis_chain(self):
        prompt_synthesis = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt_synthesis),
            ("user", "{results}")
        ])

        synthesis_chain = prompt_synthesis | self.synthesis_model | StrOutputParser()
        return synthesis_chain
    
    def run(self):
        analysis_chain = self.create_analysis_chain()
        analysis_tasks = self.create_analysis_tasks()
        analysis_results = analysis_chain.batch(analysis_tasks)
        analysis_results_formulated = self.formulate_analysis_results(analysis_tasks ,analysis_results)
        synthesis_chain = self.create_synthesis_chain()
        synthesis_result = synthesis_chain.invoke({"results": analysis_results_formulated})
        return synthesis_result

if __name__ == "__main__":
    ta = TechnicalAnalysis()
    print(ta.run())


