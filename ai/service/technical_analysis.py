import os
from ai.config import Config, GeminiClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from ai.service.technical_indicators import TechnicalIndicators
from datetime import datetime
from ai.parameters import CURRENCY_TICKERS
import google.generativeai as genai
import asyncio


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
        
        self.system_prompt_long_term_analysis = f"""
**Role:** You are a highly skilled forex {self.currency_pair} technical analyst specializing in understanding long-term trends and identifying key support and resistance levels.

**Context (Inputs):**
- 4 Hourly price chart data

**Goal:** To provide a comprehensive technical analysis of the long-term trend that will serve as context for medium-term analysis by another agent.

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
        self.system_prompt_medium_term_analysis = f"""
**Role:** You are a highly skilled forex {self.currency_pair} technical analyst specializing in refining the understanding of medium-term trends and identifying potential trade setups.

**Context (Inputs):**
- 1-Hourly price chart data.
- Output from the 4-hour analysis agent, which includes:
    - The prevailing trend on the 4-hour timeframe (bullish, bearish, or sideways).
    - Analysis of recent 4-hour price action, momentum, and potential trend reversal points.
    - Key support and resistance zones identified on the 4-hour chart.

**Goal:** To refine the directional bias established by the 4-hour analysis, identify nearer-term structure, and pinpoint potential trade setups on the 1-hour timeframe. Your analysis will serve as a bridge to the shorter-term (15M/5M) analysis agent.

**Tasks (Analytical Focus):**

1. **Trend Confirmation/Refinement:**
   - **Compare H1 Trend with H4 Trend:**
     - If H1 and H4 trends are aligned, state how this reinforces the established bias.
     - If H1 contradicts H4, describe the nature of the contradiction.
     - If both timeframes are sideways, characterize the range (e.g., "Both H4 and H1 are in a sideways range between [price] and [price].").
   - **Moving Average Analysis:**
     - Use the 20 EMA, 50 EMA, and 100 EMA to assess the short- to medium-term trend on H1.
     - Describe the relationship between the EMAs.
     - Note any significant crosses or slopes of the EMAs.
   - **Momentum Indicator Analysis:**
     - Analyze momentum indicators of RSI (14), MACD (12, 26, 9) and ROC (12) on the H1 chart.
       - RSI (14): State whether RSI is above or below 50 and how this relates to the trend bias.
       - MACD (12, 26, 9): Describe the position of the MACD line relative to the signal line and the zero line, and note any crossovers or histogram direction as confirmation of momentum.
       - ROC (12): Interpret the rate of change indicator in the context of momentum confirmation.

2. **Structure and Setup Identification:**
   - **Identify Intraday S/R:** Look for if any newly formed support/resistance levels on the H1 chart not highlighted in the H4 analysis.
   - **Chart Patterns:** Identify any short-term chart patterns (e.g., channels, triangles, head and shoulders) that could indicate potential continuation or reversal.
   - **Breakout/Pullback Scenarios:** Describe potential trade setups based on price action:
     - Breakout: "If price breaks above [price] with strong momentum, it might signal a continuation of the uptrend."
     - Pullback: "If price pulls back to the 20 EMA or [support level] and shows a bullish reversal candle, it could offer a buying opportunity."

3. **Alignment with H4 Bias:**
   - Explicitly state whether the H1 analysis confirms the H4 bias.
   - If there's a contradiction, outline the conditions under which the H1 analysis would align with the H4 bias, or vice versa.

**Guidelines for Output:**
- Be concise and focus on actionable insights for the next stage (15M/5M analysis).
- Provide specific price levels for identified support/resistance, pattern boundaries, and potential entry/exit points.
- Clearly articulate the relationship between the H1 and H4 analyses.
- Use clear and objective language, avoiding overly subjective or ambiguous statements.
- Your output should serve as a clear roadmap for the lower timeframe agent to identify precise entry and exit points.
"""

        self.system_prompt_5_min_analysis = f"""
**Role:** You are a skilled forex {self.currency_pair} technical analyst specializing in providing short-term trading outlooks based on recent price action.

**Context (Inputs):**
- Current 15-minute price chart
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
- Conclude your analysis by stating whether, based on the available information, a trade can be confidently executed at this time (either long, short or wait).
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
        ti = TechnicalIndicators(ticker=self.ticker, interval="1m")
        # def transform(data):
        #     data['Close_str'] = data['Close'].map(lambda x: f'{x:.4f}')
        #     data = data["Close_str"].to_dict()
        #     new_data = {key.strftime('%Y-%m-%d %H:%M:%S'): value for key, value in data.items()}
        #     return new_data
        # current_price = ti.download_data(period="1d", interval="1m")["Close"].iloc[-1].round(4)
        # rate_1_day = transform(ti.download_data(period="5d", interval="15m").iloc[-4*24:])
        # rate_5_day = transform(ti.download_data(period="5d", interval="1h"))
        # rate_3_month = transform(ti.download_data(period="3mo", interval="1d"))
        # rates = {"1_day": rate_1_day, "5_day": rate_5_day, "3_month": rate_3_month, "current_price": current_price}
        current_price = ti.download_data()["Close"].iloc[-1].round(4)
        return current_price

        
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
    
    async def extract_technical_indicators_with_gemini(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY_CONG"])
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            system_instruction=self.system_prompt_technicals
        )
        client = GeminiClient()
        tasks = []
        for file_name in os.listdir("data/technical_indicators/"):
            if file_name.endswith("png") and "pivot" in file_name:
                task = client.call_gemini_api(model, f"{file_name} is uploaded", image_path=f"data/technical_indicators/{file_name}")
                tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results

        
    async def create_gemini_analysis(self, pivot_points, current_price):
        genai.configure(api_key=os.environ["GEMINI_API_KEY_CONG"])
        # model_name = "gemini-2.0-flash-exp"
        model_name = "gemini-2.0-flash-thinking-exp-1219"

        generation_config = {
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=self.system_prompt_long_term_analysis
        )

        client = GeminiClient()

        query = f"Analyze the following 4 hourly chart data for {self.currency_pair} from the last 3 months."
        response_long_term = await client.call_gemini_api(
            model, query, image_path="data/chart/4h.png"
        )
        print("Long term analysis \n", response_long_term)
        print("\n\n")


        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=self.system_prompt_medium_term_analysis
        )
        query = f"""Here is the previous 4 hourly chart analysis provided by another analyst:
        <4 Hourly chart analysis>
        {response_long_term}
        </4 Hourly chart analysis>

        Now, analyze the uploaded hourly chart data for {self.currency_pair} from the last 20 days.
        """
        response_medium_term = await client.call_gemini_api(
            model, query, image_path="data/chart/1h.png"
        )

        print("Medium term analysis \n", response_medium_term)
        print("\n\n")

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=self.system_prompt_5_min_analysis
        )
        query = f"""Here is the previous hourly chart analysis provided by another analyst:
        <Hourly chart analysis>
        {response_medium_term}
        </Hourly chart analysis>

        Here are the 15-minute pivot points.
        <Pivot points>
        {pivot_points}
        </Pivot points>

        The currrent price is {current_price}. 
        
        Analyze the uploaded 15-min chart data from the last 3 days."""
        response_short_term = await client.call_gemini_api(
            model, query, image_path="data/chart/15m.png"
        )
        print("5 min analysis \n", response_short_term)

        return response_short_term

    async def run(self):
        technical_indicators = await self.extract_technical_indicators_with_gemini()

        pivot_points = technical_indicators[0]
        print(pivot_points)
        current_price = self.extract_eur_usd_rate()
        print(current_price)

        analysis = await self.create_gemini_analysis(pivot_points, current_price)
        synthesis = analysis
        return synthesis

if __name__ == "__main__":
    ta = TechnicalAnalysis(
        #currency_pair="EUR/USD",
        currency_pair="USD/JPY",
    )

    asyncio.run(ta.run())



