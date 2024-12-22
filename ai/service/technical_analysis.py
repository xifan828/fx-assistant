import os
from ai.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from ai.service.technical_indicators import TechnicalIndicators
from datetime import datetime
from ai.parameters import CURRENCY_TICKERS
from ai.config import upload_to_gemini
import google.generativeai as genai


class TechnicalAnalysis:
    def __init__(self, analysis_model = None, synthesis_model = None, currency_pair: str = "EUR/USD", ticker: str = "EURUSD=X"):
        self.analysis_model = analysis_model if analysis_model is not None else Config(model_name="gpt-4o", temperature=0.2, max_tokens=512).get_model()
        self.synthesis_model = synthesis_model if synthesis_model is not None else Config(model_name="gpt-4o", temperature=0.2, max_tokens=1024).get_model()
        self.currency_pair = currency_pair
        self.ticker = CURRENCY_TICKERS[self.currency_pair]

        self.system_prompt_analysis = f"""As an expert forex analyst specializing in {self.currency_pair} pair technical analysis. You will be provided with data of {self.currency_pair} rates and technical indicators.
 You taks is to:
- Recognize significant price patterns. 
- Determine overall trend direction.
- Provide short-term price outlook
You should provide clear, concise, and actionable analysis. Use professional terminology with brief explanations. AVOID making forex trading risks and the importance of personal research.
Retail Forex traders will use your analysis to make informed trading decisions and manage risk. 
Start you output with `### {self.currency_pair} Technical Analysis within <period, 1 day, 5 days or 3 month>`"""

        self.system_prompt_technicals = f"""You are an expert forex analyst specializing in {self.currency_pair} pair technical indicators analysis. You will be provided with an image of the {self.currency_pair} technical indicators. 
Your task is ONLY to extract the key indicators, their value, and their signal. 
Your output should look like this.
### Oscillators
Relative Strength Index (14), <actual value>, <actual signal>
...

### Moving Averages
Exponential Moving Average (10), <actual value>, <actual signal>
...
"""

        self.system_prompt_synthesis = f"""You are an advanced forex analysis synthesizer specializing in the {self.currency_pair} pair. Your role is to integrate and interpret multiple analyses across various timeframes. Retail Forex traders will use your synthesized insights to make informed trading decisions and manage risk.
For the synthesized analysis:
- Compile and evaluate analyses from 1-day, 5-day, and 1-month timeframes.
- Identify consistent patterns or conflicting signals across timeframes.
- Determine the overall market sentiment and potential trend direction.
- Highlight key support and resistance levels that align across multiple analyses.
- Provide a comprehensive short to medium-term outlook for {self.currency_pair}.
Deliver a clear, concise, and actionable synthesis. Prioritize the most significant insights that emerge from combining multiple analyses. Use professional terminology with brief explanations when necessary. AVOID discussing forex trading risks and the importance of personal research."""
        
        self.system_prompt_hourly_analysis = f"""
**Role:** You are a highly skilled forex {self.currency_pair} technical analyst specializing in understanding medium-term trends and identifying key support and resistance levels.

**Context (Inputs):**
- Hourly price chart data

**Goal:** To provide a comprehensive technical analysis of the medium-term trend that will serve as context for shorter-term analysis by another agent.

**Tasks (Analytical Focus):**
- Identify the prevailing trends present in the hourly chart data over the last 10 days.
- Analyze the momentum and character of **recent** price action within the 10-day period.
- Identify potential points or zones where the prevailing trend might change direction.
- Determine key support and resistance zones, providing specific price levels where possible.
- Analyze signals from relevant technical indicators included in the data.

**Guidelines for Output:**
- Be concise and focus on the most impactful observations for understanding the medium-term context.
- Provide specific numerical values for key support and resistance levels/zones where possible.
- Remember that your analysis will be used by another agent for further short-term analysis.
"""
        self.system_prompt_5_min_analysis = f"""
**Role:** You are a skilled forex {self.currency_pair} technical analyst specializing in providing short-term trading outlooks based on recent price action.

**Context (Inputs):**
- Current 5-minute price chart
- 15-minute interval pivot points
- Exact current price
- Previous hourly chart analysis

**Goal:** To synthesize the provided information to understand the immediate trend of the {self.currency_pair} pair and provide a short-term trading outlook for the next few hours.

**Tasks (Analytical Focus):**
- Identify the prevailing trends present in the 5-minute chart.
- Analyze the momentum and character of **recent** price action.
- Identify immediate support and resistance levels, considering both price action on the 5-minute chart and the provided 15-minute pivot points.
- Identify potential entry and exit points for short-term trades.
- Confirm or contradict the trends and key levels identified in the previous hourly chart analysis.
- Analyze how the current price relates to the identified support and resistance levels, as well as the 15-minute pivot points and recent 5-minute price action.

**Guidelines for Output:**
- Be specific and actionable in your outlook, providing concrete levels or price areas to watch.
- Remember to always consider the context provided by the previous hourly analysis.
- Conclude your analysis by stating whether, based on the available information, a trade can be confidently executed at this time (either long or short).
- If a trade cannot be confidently executed, explain what specific observations or signals would be needed to increase confidence in a potential trade in the near future.
"""

        self.encoded_image_template = "data:image/png;base64,{base64_image}"
    
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def create_technicals_extraction_chain(self):
        system_message = SystemMessage(content=self.system_prompt_technicals)
        user_message = HumanMessage(
            content=[
                {"type": "text", "text": "{file_name} is uploaded"},
                {"type": "image_url", "image_url": {"url": "{encoded_image}"}},  # Use base64 string here
            ]
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message.content),
            ("user", user_message.content)
        ])
        chain = prompt | self.analysis_model | StrOutputParser()
        return chain
    
    def create_technicals_extraction_tasks(self):
        encoded_images = {}
        for file_name in os.listdir("data/technical_indicators/"):
            if file_name.endswith("png"):
                encoded_images[file_name.split(".")[0]] = self.encoded_image_template.format(base64_image=self.encode_image(f"data/technical_indicators/{file_name}"))
        
        tasks = [{"file_name": k, "encoded_image": v} for k, v in encoded_images.items()]
        return tasks
    
    def extract_technical_indicators(self):
        tasks = self.create_technicals_extraction_tasks()
        extraction_chain = self.create_technicals_extraction_chain()
        results = extraction_chain.batch(tasks)
        technical_indicators = {"1_day": "", "1_hour": "", "15_min": ""}

        for task, result in zip(tasks, results):
            if "1_day" in task["file_name"]:
                technical_indicators["1_day"] += result + "\n"
            elif "1_hour" in task["file_name"]:
                technical_indicators["1_hour"] += result + "\n"
            else:
                technical_indicators["15_min"] += result + "\n"
        return technical_indicators
    
    def extract_eur_usd_rate(self):
        ti = TechnicalIndicators(ticker_symbol=self.ticker)
        def transform(data):
            data['Close_str'] = data['Close'].map(lambda x: f'{x:.4f}')
            data = data["Close_str"].to_dict()
            new_data = {key.strftime('%Y-%m-%d %H:%M:%S'): value for key, value in data.items()}
            return new_data
        current_price = ti.download_data(period="1d", interval="1m")["Close"].iloc[-1].round(4)
        rate_1_day = transform(ti.download_data(period="5d", interval="15m").iloc[-4*24:])
        rate_5_day = transform(ti.download_data(period="5d", interval="1h"))
        rate_3_month = transform(ti.download_data(period="3mo", interval="1d"))
        rates = {"1_day": rate_1_day, "5_day": rate_5_day, "3_month": rate_3_month, "current_price": current_price}
        return rates

        
    def create_analysis_chain(self):
        user_message_template = """{date}. The {currency_pair} is currently trading at price of {current_price}. 
Below are the latest data of {currency_pair} rates with a period of {rates_period} and interval of {rates_interval}.
{rates}
Below are the technical indicators with an interval of {ti_interval}.
{technical_indicators}
"""
        prompt_analysis = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt_analysis),
            ("user", user_message_template)
        ])

        chain = prompt_analysis | self.analysis_model | StrOutputParser()
        return chain
    
    def create_analysis_tasks(self, rates, technical_indicators):
        now = datetime.now()
        formatted_date = now.strftime("Today is %A, %d %B, %Y")

        tasks = []
        tasks.append({
            "date": formatted_date, "rates_period": "1 day", "rates_interval": "15 minutes", "rates": rates["1_day"], "ti_interval": "15 minutes", "technical_indicators": technical_indicators["15_min"], 
            "currency_pair": self.currency_pair, "current_price": rates["current_price"]
        })
        tasks.append({
            "date": formatted_date, "rates_period": "5 days", "rates_interval": "1 hour", "rates": rates["5_day"], "ti_interval": "1 hour", "technical_indicators": technical_indicators["1_hour"], 
            "currency_pair": self.currency_pair, "current_price": rates["current_price"]
        })
        tasks.append({
            "date": formatted_date, "rates_period": "3 months", "rates_interval": "1 day", "rates": rates["3_month"], "ti_interval": "1 day", "technical_indicators": technical_indicators["1_day"], 
            "currency_pair": self.currency_pair, "current_price": rates["current_price"]
        })
        return tasks

    def create_analysis(self, rates, technical_indicators):
        tasks = self.create_analysis_tasks(rates, technical_indicators)
        analysis_chain = self.create_analysis_chain()
        results = analysis_chain.batch(tasks)
        analysis = "\n".join(results)
        return analysis
    
    def create_synthesis_chain(self):
        prompt_synthesis = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt_synthesis),
            ("user", "{results}")
        ])

        synthesis_chain = prompt_synthesis | self.synthesis_model | StrOutputParser()
        return synthesis_chain
    
    def create_synthesis(self, analysis):
        synthesis_chain = self.create_synthesis_chain()
        results = synthesis_chain.invoke({"results": analysis})
        return results
    
    def create_gemini_analysis(self, pivot_points, current_price):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        generation_config = {
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            #model_name="gemini-2.0-flash-thinking-exp-1219",
            generation_config=generation_config,
            system_instruction=self.system_prompt_hourly_analysis
        )
        files = [
        upload_to_gemini("data/chart/10_days_cropped.png", mime_type="image/png"),
        ]
        query = f"Analyze the following hourly chart data for {self.currency_pair} from the last 10 days."
        chat_session = model.start_chat(history=[])
        response_hourly = chat_session.send_message([query, files[0]]).text

        model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        #model_name="gemini-2.0-flash-thinking-exp-1219",
        generation_config=generation_config,
        system_instruction=self.system_prompt_5_min_analysis
        )
        files = [
        upload_to_gemini("data/chart/1_day_cropped.png", mime_type="image/png"),
        ]

        query = f"""Here is the previous hourly chart analysis provided by another analyst:
        <Hourly chart analysis>
        {response_hourly}
        </Hourly chart analysis>

        Here are the 15-minute interval pivot points:
        <15-Minute Pivot Points>
        {pivot_points}
        </15-Minute Pivot Points>

        The current price is: {current_price}

        Now, analyze the uploaded 5-minute chart data for {self.currency_pair} from today.
        """
        chat_session = model.start_chat(history=[])
        final_response = chat_session.send_message([query, files[0]]).text

        return final_response

    def run(self):
        technical_indicators = self.extract_technical_indicators()
        for i in technical_indicators["15_min"].split("###"):
            if "pivot" in i.lower():
                pivot_points = i
                break
            else:
                pivot_points = "Not available"
        print(pivot_points)
        rates = self.extract_eur_usd_rate()
        current_price = rates["current_price"]
        print(current_price)
        #analysis = self.create_analysis(rates=rates, technical_indicators=technical_indicators)
        #synthesis = self.create_synthesis(analysis=analysis)
        analysis = self.create_gemini_analysis(pivot_points, current_price)
        synthesis = analysis
        return synthesis

if __name__ == "__main__":
    ta = TechnicalAnalysis(
        currency_pair="EUR/USD"
    )
    import time 
    begin_time = time.time()
    #rates = ta.extract_eur_usd_rate()
    #technical_indicators = ta.extract_technical_indicators()
    #print(technical_indicators)
    #analysis = ta.create_analysis(rates=rates, technical_indicators=technical_indicators)
    #synthesis = ta.run()
    #print(analysis)
    print(ta.run())

    end_time = time.time()

    print(f"Used {end_time-begin_time:.2f}")

