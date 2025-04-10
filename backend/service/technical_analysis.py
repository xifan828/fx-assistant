import os
from backend.utils.llm_helper import Config, GeminiClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from backend.service.data_collection import TechnicalIndicators
from datetime import datetime
from backend.utils.parameters import CURRENCY_TICKERS
import asyncio


class TechnicalAnalysis:
    def __init__(self, analysis_model = None, synthesis_model = None, gemini_model = None, gemini_api_key = None, currency_pair: str = "EUR/USD", ticker: str = "EURUSD=X"):
        self.analysis_model = analysis_model if analysis_model is not None else Config(model_name="gpt-4o", temperature=0.2, max_tokens=512).get_model()
        self.synthesis_model = synthesis_model if synthesis_model is not None else Config(model_name="gpt-4o", temperature=0.2, max_tokens=1024).get_model()
        self.gemini_model = gemini_model if gemini_model is not None else "gemini-2.0-flash-exp"
        self.gemini_api_key = gemini_api_key if gemini_api_key is not None else os.environ["GEMINI_API_KEY_XIFAN"]
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
        
        self.system_prompt_template_techncial_indicators = """**Role:** You are a highly skilled forex technical analyst specializing in interpreting MACD, RSI indicators to understand market momentum and potential trend reversals.

**Context (Inputs):**
- A chart displaying the {interval} interval MACD, RSI, and ROC (maybe missing from the chart) for the {currency_pair} currency pair.

**Goal:** To provide a clear analysis of the MACD, RSI, and ROC indicators, focusing on their implications for the current trend and potential future price movements.

**Tasks (Analytical Focus):**
- **MACD Analysis:**
    - Describe the **most recent** trend of the MACD line and the signal line.
    - Identify any crossovers between the MACD line and the signal line and interpret their significance (bullish or bearish).
    - Predict if any corssovers is looked like going to happen based on the **most recent** period.
    - Analyze the MACD histogram. Is it increasing or decreasing? What does this suggest about the strength of the current trend?
    - Identify any divergences between the MACD and the price action (you will not see price action in this chart, but you can infer it from MACD). What might these divergences indicate?
- **RSI Analysis:**
    - Describe the **most recent** level and movement of the RSI. Is it above 70, below 30, or within the neutral range (30-70)?
    - Identify any overbought or oversold conditions based on the RSI.
    - Analyze the trend of the RSI. Is it increasing, decreasing, or moving sideways?
    - Identify any divergences between the RSI and the price action (you will not see price action in this chart, but you can infer it from RSI). What might these divergences indicate?
- **ROC Analysis:**
    - Describe the **most recent** level and movement of the ROC. Is it above or below zero? What does this indicate about the price momentum?
    - Analyze the trend of the ROC. Is it increasing, decreasing, or moving sideways?
    - Identify any sharp increases or decreases in the ROC, and explain their potential significance.
    - Identify any divergences between the ROC and the price action (you will not see price action in this chart, but you can infer it from ROC). What might these divergences indicate?
- **Combined Analysis:**
    - Based on your analysis of MACD, RSI, and ROC, what is your overall assessment of the current market momentum?
    - Are there any conflicting signals between the indicators? If so, how should they be interpreted?
    - What are the potential implications of your indicator analysis for the future direction of the {currency_pair} price?

**Guidelines for Output:**
- Be concise and focus on the most important observations from the MACD, RSI, and ROC.
- Use clear and specific language to describe the indicator patterns and their potential meanings.
- In the end, provide a concise summary of your analysis using the flowwing format:
    **Summary:**
    etc.
"""

        self.system_prompt_hourly_analysis = f"""
### **Role**  
You are a highly skilled forex {self.currency_pair} trader specializing in **technical analysis**.

### **Context**
The user will provide:
- Hourly candle stick chart with moving averages lines.  
- RSI plot corresponding to the candles.
- MACD plot corresponding to the candles.

### **Objective**  
Provide a **medium-term** technical analysis of {self.currency_pair}, focusing on **price action** and the technical indicators on the **hourly chart**:

- **Moving Averages** (directional bias, potential crossovers)  
- **RSI** (momentum, overbought/oversold levels)  
- **MACD** (momentum shifts, crossovers, divergence)  

Your analysis will serve as context for a **short-term** 5-min timeframe analysis by another agent.

### **Tasks**
1. **Candlestick Patterns**
    - Identify any significant **price patterns** or **candlestick formations**. Examples include bullish or bearish engulfing, doji, hammer, etc.

2. **Trend Analysis**
    - Evaluate how the price interacts with the moving averages, RSI, and MACD to identify the current trend. Discuss whether the trend is bullish, bearish, or neutral based on the convergence or divergence of price from these indicators.

3. **Trend Confirmation vs. Contradiction**  
   - Compare the signals from different indicators to confirm or contradict the identified trend. For example, if moving averages and MACD suggest an uptrend but RSI indicates overbought conditions, discuss the potential for a trend reversal or continuation.

4. **Support & Resistance**  
   - Highlight key levels or zones, providing **specific price points** where possible.

### **Guidelines**

- **Be concise** yet thorough in analyzing price action and each indicator.  
- Include **numerical values** (indicator readings, price levels) wherever it clarifies your points.  
- Remember, **another agent** will use your analysis to inform a shorter-term strategy.
"""
        self.system_prompt_5_min_analysis = f"""
## **Role**  
You are a **skilled forex {self.currency_pair} technical analyst** specializing in **short-term trading outlooks**.

---

## **Context (Inputs)**
1. **Current 15-minute interval candlestick chart** with technical indicators (Moving Averages, MACD)  
2. **15-minute interval pivot points**  
3. **Exact current price**  
4. **Previous hourly chart analysis** (providing a medium-term perspective)

---

## **Goal**  
- **Synthesize** all provided information to determine the **immediate trend** of {self.currency_pair}  
- Offer a **short-term trading outlook** for the **next few hours**.

---

## **Tasks**

1. **Chart Analysis**  
    - Identify any significant **price patterns** or **candlestick formations**.
    - **Trend Analysis**: Evaluate how the price interacts with the moving averages, RSI, and MACD to identify the current trend. Discuss whether the trend is bullish, bearish, or neutral based on the convergence or divergence of price from these indicators.
    - **Trend Confirmation vs. Contradiction**: Compare the signals from different indicators to confirm or contradict the identified trend. 

2. **Price Levels**
    - Compare the current price to the **pivot points** and hourly analysis identified supports and resistance levels to identify potential **support and resistance levels**.
    
3. **Incorporate Hourly Analysis**  
   - Compare findings from the 5-minute chart with **insights from the previous hourly chart analysis**.  
   - Highlight any confirmations or contradictions in the short-term vs. medium-term trends.

4. **Actionable Outlook**  
   - Clearly state if a **short-term trade** (long or short) is viable given current conditions.  
   - If a trade is **not** recommended now, specify **which signals or conditions** would be needed to warrant a future trade.
   
5. **Potential Trade Setup**  
   - Based on the identified trend and support/resistance levels, propose **potential entry and exit points** for a short-term trade.
   - Always choose a **limit order** for the trade. Ensure that for a buy order, the entry price is lower than the current price, and for a short order, the entry price is higher than the current price.

---

## **Guidelines for Output**

- **Clarity and Actionability**: Provide **specific** price levels or indicators (e.g., MA crossovers, RSI extremes, MACD/ROC signals) that inform your short-term outlook.
- **Contextual Integration**: Show how the new short-term findings **align with** or **deviate from** the previous hourly analysis.
- **Decision Justification**: If you suggest a trade, **justify** it with clear reasoning (trend, momentum, key levels). If you advise waiting, specify what **further evidence** (e.g., break of support/resistance, pivot confirmation, indicator crossover) is needed.
- **Entry Point and Order Type**: 
    - Clearly state the recommended **entry point**.  
    - For a **limit order**, ensure that the entry price is set according to the trade direction (buy: below current price; short: above current price).
- **Summary Format**: Conclude with a concise summary, for example:
    **Summary:**
    etc.
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
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="1min", outputsize=100)
        current_price = ti.get_current_price()
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
        generation_config = {
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
            "response_mime_type": "text/plain",
        }
        model_name = "gemini-2.0-flash-exp"
        system_instruction = self.system_prompt_technicals
        client = GeminiClient(
            model_name=model_name,
            generation_config=generation_config,
            api_key=self.gemini_api_key,
            system_instruction=system_instruction
        )

        tasks = []
        for file_name in os.listdir("data/technical_indicators/"):
            if file_name.endswith("png") and "pivot" in file_name:
                task = client.call_gemini_vision_api(f"{file_name} is uploaded", image_path=f"data/technical_indicators/{file_name}")
                tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results

    async def get_technical_indicators_analysis(self, client, image_path):
        query = "The technical indicators chart is uploaded. The latest period should be considred is shaded in grey.\nIn the MACD chart, red line represents MACD, green line represents Signal, balck histogram represents negative and peru histogram represents positive.\nStart your analysis."
        response, _ = await client.call_gemini_vision_api(
        user_message=query, image_path=image_path
        )
        return response

    async def get_technical_analysis(self, client, image_path, previous_analysis = None, current_price = None, pivit_points = None):
        query_prefix = (
        "The candlestick chart is uploaded.\n",
        )

        query_suffix = ("Start your analysis.",)

        if previous_analysis:
            new_text = ("The summary of the previous longer time frame analysis is provided below by another agent:",
                        "<Previous longer time frame analysis>\n",
                        f"{previous_analysis}\n",
                        "</Previous longer time frame analysis>\n"
            )
            query_prefix += new_text
        
        if current_price and pivit_points:
            new_text = (
                "Current price is provided below:\n",
                "<current price>\n",
                f"{current_price}\n",
                "</current price>\n"
            )
            query_prefix += new_text
            new_text = (
                "Pivot points is provided below:\n",
                "<pivot points>\n",
                f"{pivit_points}"
                "</pivot points>\n",
            )
            query_prefix += new_text
        
        query_tuple = query_prefix + query_suffix
        query = "".join(query_tuple)
            
        response, chat_session = await client.call_gemini_vision_api(
        user_message=query, image_path=image_path
        )
        return response, chat_session

        
    async def create_gemini_analysis(self, pivot_points, current_price):
        model_name = self.gemini_model
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        chart_files = ["data/chart/1h.png", "data/chart/15min.png"]
        # hourly analysis
        client = GeminiClient(
            model_name=model_name,
            generation_config=generation_config,
            api_key=self.gemini_api_key,
            system_instruction=self.system_prompt_hourly_analysis
        )
        analysis_1h, _ = await self.get_technical_analysis(client, chart_files[0])

        # 5 min analysis
        client = GeminiClient(
            model_name=model_name,
            generation_config=generation_config,
            api_key=self.gemini_api_key,
            system_instruction=self.system_prompt_5_min_analysis
        )
        analysis_5min, chat_session = await self.get_technical_analysis(client, chart_files[1], previous_analysis=analysis_1h, current_price=current_price, pivit_points=pivot_points)

        summary_5min = analysis_5min.split("**Summary:**")[-1].strip()

        query = """Based on your analysis, please output a trading strategy in json format. Using the following format:
        ```json
        {
            "strategy": "buy", "sell" or "wait",
            "order_type": "limit" or "market" if strategy is "buy" or "sell" else null
            "entry_point": float, if strategy is "buy" or "sell" else null
            "stop_loss": float, if strategy is "buy" or "sell" else null 
            "take_profit": float, if strategy is "buy" or "sell" else null
        }
        ```
        For entry_point, stop_loss and take_profit, output one single float number.
        """
        response_json = await chat_session.send_message(query)
        response_json = response_json.text
        return {"analysis_1h": analysis_1h, "analysis_5min": analysis_5min, "summary_5min": summary_5min, "strategy": response_json}

    async def run(self):
        results = await self.extract_technical_indicators_with_gemini()
        technical_indicators, _  = results[0]
        print(technical_indicators)

        current_price = self.extract_eur_usd_rate()
        print(current_price)

        analysis = await self.create_gemini_analysis(technical_indicators, current_price)
        synthesis = analysis
        return synthesis

if __name__ == "__main__":
    ta = TechnicalAnalysis(
        #currency_pair="EUR/USD",
        currency_pair="USD/JPY",
        gemini_model="gemini-2.0-flash",
        #gemini_model="gemini-2.0-flash-thinking-exp-01-21",
        gemini_api_key=os.environ["GEMINI_API_KEY_KIEN"]
    )

    ans = asyncio.run(ta.run())

    for k, v in ans.items():
        print(k)
        print(v)
        print("\n\n")



