from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, RootModel
from utils.logger_setup import setup_logger
from dotenv import load_dotenv
import json
import os

load_dotenv()

logger = setup_logger(__name__)

ticker_map = {
    "hindustan unilever": "HINDUNILVR.NS",
    "sbi life": "SBILIFE.NS",
    "asian paints": "ASIANPAINT.NS",
    "sun pharma": "SUNPHARMA.NS",
    "nestle india": "NESTLEIND.NS",
    "kotak bank": "KOTAKBANK.NS",
    "tata consumer": "TATACONSUM.NS",
    "axis bank": "AXISBANK.NS",
    "ultratech cement": "ULTRACEMCO.NS",
    "ntpc": "NTPC.NS",
    "grasim": "GRASIM.NS",
    "jsw steel": "JSWSTEEL.NS",
    "indusind bank": "INDUSINDBK.NS",
    "dr reddy": "DRREDDY.NS",
    "cipla": "CIPLA.NS",
    "itc": "ITC.NS",
    "eicher motors": "EICHERMOT.NS",
    "tata steel": "TATASTEEL.NS",
    "hdfc life": "HDFCLIFE.NS",
    "sbi": "SBIN.NS",
    "tech mahindra": "TECHM.NS",
    "l&t": "LT.NS",
    "icici bank": "ICICIBANK.NS",
    "adani ports": "ADANIPORTS.NS",
    "hero motocorp": "HEROMOTOCO.NS",
    "adani enterprises": "ADANIENT.NS",
    "power grid": "POWERGRID.NS",
    "coal india": "COALINDIA.NS",
    "maruti": "MARUTI.NS",
    "hdfc bank": "HDFCBANK.NS",
    "titan": "TITAN.NS",
    "ongc": "ONGC.NS",
    "shriram finance": "SHRIRAMFIN.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "hindalco": "HINDALCO.NS",
    "trent": "TRENT.NS",
    "tata motors": "TATAMOTORS.NS",
    "hcl tech": "HCLTECH.NS",
    "bharti airtel": "BHARTIARTL.NS",
    "bajaj auto": "BAJAJ-AUTO.NS",
    "infosys": "INFY.NS",
    "reliance": "RELIANCE.NS",
    "jio financial": "JIOFIN.NS",
    "bajaj finserv": "BAJAJFINSV.NS",
    "apollo hospitals": "APOLLOHOSP.NS",
    "bharat electronics": "BEL.NS",
    "wipro": "WIPRO.NS",
    "mahindra & mahindra": "M&M.NS",
    "tcs": "TCS.NS",
    "eternal": "ETERNAL.NS"
}

# llm = ChatGoogleGenerativeAI(
#             model="gemini-1.5-flash"
#         )

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

class StockImpactPrediction(BaseModel):
    ticker: str
    article: dict

class StockImpactList(RootModel[list[StockImpactPrediction]]):
    pass

parser = PydanticOutputParser(pydantic_object=StockImpactList)

stock_identification_prompt = PromptTemplate(
    template="""
    You are a financial analyst AI assistant.

    Your job is to analyze a news article and identify which **Nifty 50 companies** may be impacted by the news or are related to the news.

    Instructions:
    - Use the `ticker_map` below to map company names to their official ticker symbols.
    - Match company names intelligently. For example, "Reliance Industries" or "RIL" → "reliance" → "RELIANCE.NS".
    - Consider indirect references like founders, CEOs, subsidiaries, or related entities that clearly relate to a company in the ticker_map.
    - Example: "Mukesh Ambani" implies "Reliance", "Narayana Murthy" implies "Infosys".
    - If the article discusses broader market events (e.g., "Sensex falls 500 points", "Budget 2025", "RBI hike", "Indian markets rally") **but does not mention specific companies**, then:
    ✅ Return **all ticker mappings** in the dictionary (i.e., all Nifty 50 stocks), as all may be impacted.
    - If the article is **not about Indian companies or stock markets**, return **an empty list: `[]`**.

    {format_instructions}

    Here is the stock-to-ticker mapping (keys are lowercase):
    {ticker_map_json}

    Here is the article:
    {article_json}
    """.strip(),
    input_variables=["ticker_map_json", "article_json"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

stock_identifier_chain = stock_identification_prompt | llm | parser

def identify_stocks_from_news(new_articles: list[dict]) -> list[dict]:
    results = []
    for article in new_articles:
        try:
            response = stock_identifier_chain.invoke({
                "ticker_map_json": json.dumps(ticker_map, indent=2),
                "article_json": json.dumps(article, indent=2)
            })

            if response.root:
                results.extend([r.model_dump() for r in response.root])  #can use .append(response.__root__) as well, results -> list[list[dict]] if you want to group by article
            else:
                logger.info(f"ℹ️ No relevant stocks found for: {article['title']}")

        except Exception as e:
            logger.error(f"❌ Failed to parse LLM response for article: {article['title']}\nError: {e}")
    
    logger.info(f"✅ Found {len(results)} articles for final analysis.")
    return results

if __name__ == "__main__":
    news_for_nifty50 = [
        {
            "ticker": "Reliance",
            "content": "The combined market capitalisation of six out of the ten most valued Indian companies dropped by ₹94,433.12 crore last week, reflecting the overall bearish sentiment in the equity markets. Reliance Industries’ valuation shrank by ₹24,358.45 crore to ₹19,98,543.22 crore",  # from Business Standard/LiveMint summarizing
            "title": "Market Cap Dip: Reliance, TCS among 6 top firms to lose ₹94,433 crore in bearish week",
            "url": "https://www.livemint.com/market/stock-market-news/mcap-of-6-of-top-10-most-valued-firms-falls-by-94-433-crore-tcs-reliance-biggest-laggards-11752990728957.html",
            "source": "LiveMint",
            "published_at": "2 weeks ago"
        },
        {
            "ticker": "TCS",
            "content": "TCS’s decision to lay off over 12,000 employees due to macro uncertainties and AI disruptions has triggered investor concerns, contrasting sharply with other IT firms.",  # from ET article on layoffs
            "title": "TCS to freeze senior hiring, pause annual salary hikes",
            "url": "https://economictimes.indiatimes.com/topic/tcs-infosys",
            "source": "Economic Times",
            "published_at": "31 Jul 2025"
        },
        {
            "ticker": "Infosys",
            "content": "On Tuesday, August 5, 2025, Infosys Ltd. experienced a stock decline of 1.39%, closing at ₹1,459.75. This performance notably lagged behind its competitors and the broader market.",  # from MarketWatch summary
            "title": "Infosys slips Tuesday, underperforms competitors",
            "url": "https://www.marketwatch.com/story/infosys-slips-tuesday-underperforms-competitors-5c44569d-6602e1076a32",
            "source": "MarketWatch",
            "published_at": "2 days ago"
        }
    ]

    result = identify_stocks_from_news(news_for_nifty50)
    print(result)
 