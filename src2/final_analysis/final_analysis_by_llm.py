from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser
from langchain.output_parsers import ResponseSchema
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

ticker_to_name_map = {
    "HINDUNILVR.NS": "Hindustan Unilever Limited",
    "SBILIFE.NS": "SBI Life Insurance Company Limited",
    "ASIANPAINT.NS": "Asian Paints Limited",
    "SUNPHARMA.NS": "Sun Pharmaceutical Industries Limited",
    "NESTLEIND.NS": "Nestlé India Limited",
    "KOTAKBANK.NS": "Kotak Mahindra Bank Limited",
    "TATACONSUM.NS": "Tata Consumer Products Limited",
    "AXISBANK.NS": "Axis Bank Limited",
    "ULTRACEMCO.NS": "UltraTech Cement Limited",
    "NTPC.NS": "NTPC Limited",
    "GRASIM.NS": "Grasim Industries Limited",
    "JSWSTEEL.NS": "JSW Steel Limited",
    "INDUSINDBK.NS": "IndusInd Bank Limited",
    "DRREDDY.NS": "Dr. Reddy's Laboratories Limited",
    "CIPLA.NS": "Cipla Limited",
    "ITC.NS": "ITC Limited",
    "EICHERMOT.NS": "Eicher Motors Limited",
    "TATASTEEL.NS": "Tata Steel Limited",
    "HDFCLIFE.NS": "HDFC Life Insurance Company Limited",
    "SBIN.NS": "State Bank of India",
    "TECHM.NS": "Tech Mahindra Limited",
    "LT.NS": "Larsen & Toubro Limited",
    "ICICIBANK.NS": "ICICI Bank Limited",
    "ADANIPORTS.NS": "Adani Ports and Special Economic Zone Limited",
    "HEROMOTOCO.NS": "Hero MotoCorp Limited",
    "ADANIENT.NS": "Adani Enterprises Limited",
    "POWERGRID.NS": "Power Grid Corporation of India Limited",
    "COALINDIA.NS": "Coal India Limited",
    "MARUTI.NS": "Maruti Suzuki India Limited",
    "HDFCBANK.NS": "HDFC Bank Limited",
    "TITAN.NS": "Titan Company Limited",
    "ONGC.NS": "Oil and Natural Gas Corporation Limited",
    "SHRIRAMFIN.NS": "Shriram Finance Limited",
    "BAJFINANCE.NS": "Bajaj Finance Limited",
    "HINDALCO.NS": "Hindalco Industries Limited",
    "TRENT.NS": "Trent Limited",
    "TATAMOTORS.NS": "Tata Motors Limited",
    "HCLTECH.NS": "HCL Technologies Limited",
    "BHARTIARTL.NS": "Bharti Airtel Limited",
    "BAJAJ-AUTO.NS": "Bajaj Auto Limited",
    "INFY.NS": "Infosys Limited",
    "RELIANCE.NS": "Reliance Industries Limited",
    "JIOFIN.NS": "Jio Financial Services Limited",
    "BAJAJFINSV.NS": "Bajaj Finserv Limited",
    "APOLLOHOSP.NS": "Apollo Hospitals Enterprise Limited",
    "BEL.NS": "Bharat Electronics Limited",
    "WIPRO.NS": "Wipro Limited",
    "M&M.NS": "Mahindra & Mahindra Limited",
    "TCS.NS": "Tata Consultancy Services Limited",
    "ETERNAL.NS": "Eternal Limited"  
}

# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

response_schemas = [
    ResponseSchema(name="signal_analysis", description="A paragraph explaining the signal (positive/negative/neutral) and why."),
    ResponseSchema(name="potential_analysis", description="Detailed explanation of upside/downside potential."),
    ResponseSchema(name="confidence_analysis", description="Confidence level (High/Medium/Low) with justification."),
    ResponseSchema(name="sector_analysis", description="Sectors affected as per the news.")
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


template = """You are a financial analyst with access to:
- A **latest news summary** affecting a stock
- Past related news (for context)
- Live aggregated stock data in markdown table format (5-minute interval)
- Past 5-day OHLCV data in markdown table format

Your task is to determine whether this latest news significantly affects the stock's behavior. If it does, analyze the impact using price patterns and news content. If not, state clearly that the news is not significant enough for further analysis.

---

**Stock Name**: {stock_name}

**Latest News Summary**:
\"\"\"
{latest_news}
\"\"\"

**Related Past News**:
\"\"\"
{related_news}
\"\"\"

**Live Stock Data (5-minute Aggregation)**:
{live_data_markdown}

**Past 5-Day OHLC Data**:
{past_ohlc_markdown}

---

**Instructions**:

1. **First**, determine whether the latest news is likely to have a **material impact** on the stock. If it is **not significant**, write a short explanation and skip the rest.

2. **If the news is significant**, analyze it in detail using this format:

    - **Signal**: Positive / Negative / Neutral — justify using news sentiment and price patterns from the live + historical data.

    - **Upside/Downside Potential**:
        - If the news gives % movement, use it.
        - If only direction is mentioned, estimate the % based on data.
        - If neither is given, infer a probable % (mention uncertainty and reliability clearly).

    - **Confidence Level**: High / Medium / Low — with explanation (e.g., "sharp rally before news + strong earnings = high confidence").

    - **Sector(s) Affected**: Based solely on news content.

---

**Return your response in this format (as a JSON dictionary):**

- `signal_analysis`: string
- `potential_analysis`: string
- `confidence_analysis`: string
- `sector_analysis`: string

**If the news is not significant**, return:

```json
{{
  "signal_analysis": "News does not indicate material impact on the stock. No further analysis required.",
  "potential_analysis": "",
  "confidence_analysis": "",
  "sector_analysis": ""
}}
"""

prompt = PromptTemplate(
    input_variables=["stock_name", "latest_news", "related_news", "live_data_markdown", "past_ohlc_markdown"],
    template=template,
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

chain = prompt | llm | output_parser


def get_analysis_on_stocks(stock_ticker: str, 
                           latest_news: str, 
                           related_news: str,
                           live_data_markdown: str,
                           past_ohlc_markdown: str) -> dict:
    
    stock_name = ticker_to_name_map.get(stock_ticker)
    
    if not stock_name:
        raise ValueError(f"Unknown stock ticker: {stock_ticker}")
    
    response = chain.invoke({
        "stock_name": stock_name,
        "latest_news": latest_news,
        "related_news": related_news,
        "live_data_markdown": live_data_markdown,
        "past_ohlc_markdown": past_ohlc_markdown
    })

    return {
        "stock_ticker": stock_ticker,
        "stock_name": stock_name,
        "signal_analysis": response.get("signal_analysis", ""),
        "potential_analysis": response.get("potential_analysis", ""),
        "confidence_analysis": response.get("confidence_analysis", ""),
        "sector_analysis": response.get("sector_analysis", "")
    }

