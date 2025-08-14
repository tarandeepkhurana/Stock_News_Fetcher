from apscheduler.schedulers.background import BackgroundScheduler
from src2.yfinance_historical_stocks_data_api.get_last_5_days_ohlc_data import get_last_5_days_ohlc_data
from src2.yfinance_live_stocks_data_api.live_streaming_data import capture_live_stocks_data
from src2.yfinance_live_stocks_data_api.aggregate_live_stock_data import aggregate_multi_stock_tick_data
from src2.news_ingestion.fetch_all_sources_news import fetch_all_sources_news
from src2.news_ingestion.filter_news import identify_stocks_from_news
from src2.final_analysis.final_analysis_by_llm import get_analysis_on_stocks
from src2.retriever.fetch_related_past_news import retrieve_related_past_news
from src2.faiss_vector_store.store_news import convert_news_to_documents, save_to_vector_store
from utils.format_news import format_related_news, format_latest_news
from utils.logger_setup import setup_logger
from utils.telegram_alert import send_telegram_message
from datetime import datetime, time as dtime
import pandas as pd
import asyncio
import signal
import time
import sys

logger = setup_logger(__name__)

def job_runner():
    try:
        rss_urls = [
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        ]
        
        print("============== FETCHING LATEST NEWS ==============")
        latest_news_articles = fetch_all_sources_news(rss_urls)
        if not latest_news_articles:
            logger.info("No latest articles found. Skipping execution until next scheduled run.")
            return
        
        print("=========== FILTERING RELEVANT ARTICLES ==========")
        filtered_articles = identify_stocks_from_news(latest_news_articles)
        if not filtered_articles:
            logger.info("No relevant articles after filtering. Skipping execution until next scheduled run.")
            return
        
        unique_tickers = list({item["ticker"] for item in filtered_articles if "ticker" in item})
        
        # Get current time
        now = datetime.now().time()

        # Define market open and close times
        market_open = dtime(9, 15)
        market_close = dtime(15, 30)

        use_live_data = market_open <= now <= market_close

        if use_live_data:
            print("============ COLLECTING LIVE TICK DATA ===========")
            try:
                asyncio.run(capture_live_stocks_data(
                    symbols=unique_tickers, 
                    duration_sec=300, 
                    csv_filename="tick_data_all_stocks_combined.csv"
                ))
            except Exception as e:
                logger.error(f"Error in WebSocket thread: {e}")
                return

            print("=========== AGGREGATING LIVE TICK DATA ===========")
            result = aggregate_multi_stock_tick_data("tick_data_all_stocks_combined.csv")
        else:
            logger.info("⏳ Market is closed. Skipping live data collection.")
            result = {}
        
        NO_IMPACT_TEXT = "News does not indicate material impact on the stock. No further analysis required."

        print("=============== STARTING ANALYSIS ================")
        for article in filtered_articles:
            formatted_latest_news = format_latest_news(article["article"])
            
            related_past_news = retrieve_related_past_news(article["article"])
            formatted_related_news = format_related_news(related_past_news)

            past_ohlc_markdown = get_last_5_days_ohlc_data(article["ticker"])

            live_data = result.get(article["ticker"], [])
            live_data_df = pd.DataFrame(live_data)
            live_data_markdown = (
                live_data_df.to_markdown(index=False)
                if not live_data_df.empty
                else "No live data available (market closed)"
            )

            analysis = get_analysis_on_stocks(
                stock_ticker=article["ticker"],
                latest_news=formatted_latest_news,
                related_news=formatted_related_news,
                live_data_markdown=live_data_markdown,
                past_ohlc_markdown=past_ohlc_markdown
            )

            analysis["article"] = formatted_latest_news

            # ✅ Send Telegram notification if it's relevant
            if NO_IMPACT_TEXT not in analysis.get("signal_analysis", ""):
                message = (
                    f"📊 *Stock Analysis: {article['ticker']}*\n\n"
                    f"Signal: {analysis.get('signal_analysis', '')}\n"
                    f"Potential: {analysis.get('potential_analysis', '')}\n"
                    f"Confidence: {analysis.get('confidence_analysis', '')}\n"
                    f"Sectors: {analysis.get('sector_analysis', '')}\n\n"
                    f"📰 News: {formatted_latest_news}"
                )
                send_telegram_message(message)
                
            # with open("analysis.txt", "a") as file:
            #     file.write(f"Analysis {article['ticker']} : {analysis}\n")
        
        print("=========== SAVING TO VECTOR STORE ==============")
        news_docs = convert_news_to_documents(filtered_articles)
        save_to_vector_store(news_docs)
        logger.info("✅ Execution completed. Waiting for the next scheduled run.")

    except Exception as e:
        logger.error(f"Error occurred in job_runner(): {e}")



def graceful_shutdown(scheduler):
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    sys.exit(0)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        job_runner, 
        "interval", 
        minutes=20,
        coalesce=True,
        max_instances=1
    ) 

    scheduler.start()
    logger.info("🕒 Scheduler started. Press Ctrl+C to exit.")

    # Graceful shutdown on Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: graceful_shutdown(scheduler))
    signal.signal(signal.SIGTERM, lambda sig, frame: graceful_shutdown(scheduler))

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        graceful_shutdown(scheduler)