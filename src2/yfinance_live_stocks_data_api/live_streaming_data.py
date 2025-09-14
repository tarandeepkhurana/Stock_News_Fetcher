from utils.sheet_utils import connect_google_sheets
from gspread_dataframe import set_with_dataframe
from utils.logger_setup import setup_logger
import threading
import asyncio
from yfinance import AsyncWebSocket
from datetime import datetime, timedelta
import pandas as pd
import time

logger = setup_logger(__name__)

async def capture_live_stocks_data(symbols: list, duration_sec: int, csv_filename: str) -> bool:
    collected_ticks = []

    async def handler(msg):
        ts = int(msg.get("time", "0")) // 1000  
        msg["readable_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        collected_ticks.append(msg)
    
    # ⏱ Align to the start of the next minute
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_seconds = (next_minute - now).total_seconds()
    logger.info(f"🕒 Waiting {wait_seconds:.1f}s to align with next minute...")
    time.sleep(wait_seconds)

    ws = AsyncWebSocket()
    await ws.subscribe(symbols)

    logger.info(f"✅ Connected & subscribed to {symbols}")
    logger.info(f"⏱️  Collecting data for {duration_sec} seconds...")

    listener_task = asyncio.create_task(ws.listen(handler))

    try:
        await asyncio.sleep(duration_sec)
    finally:
        logger.info("⛔ Duration ended. Closing WebSocket...")
        listener_task.cancel()
        await ws.close()

    logger.info(f"✅ Finished collecting {len(collected_ticks)} ticks.")

    # Save to CSV
    if collected_ticks:
        df = pd.json_normalize(collected_ticks)

        df = df.sort_values(by='time', ignore_index=True)

        wanted_columns = [
            'id', 'price', 'time', 'exchange', 'quote_type', 'market_hours',
            'change_percent', 'day_volume', 'change', 'last_size', 'price_hint', 'readable_time'
        ]

        df = df[[col for col in wanted_columns if col in df.columns]]

        df.to_csv(csv_filename, index=False)
        logger.info(f"📁 Saved to {csv_filename}")
        return True
    else:
        logger.info("⚠️ No ticks collected.")
        return False


    # sys.exit(0)  # Auto exit

def run_tick_capture_in_thread(symbols: list, duration_sec: int, csv_filename: str):
    def thread_target():
        try:
            asyncio.run(capture_live_stocks_data(symbols, duration_sec, csv_filename))
        except Exception as e:
            print(f"Error in WebSocket thread: {e}")

    t = threading.Thread(target=thread_target)
    t.start()
    return t

def upload_csv_to_gsheet(csv_path):
    sheet = connect_google_sheets()

    worksheet = sheet['reliance_stocks_data']  # Use the first sheet

    # Read CSV
    df = pd.read_csv(csv_path)

    # Upload to sheet
    worksheet.clear()  # Optional: Clear existing contents
    set_with_dataframe(worksheet, df)

    print("✅ CSV uploaded to Google Sheets successfully!")

if __name__ == "__main__":
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    t = run_tick_capture_in_thread(symbols, 300, "tick_data_all_stocks_combined.csv")
    
    # ✅ Wait for thread to finish before exiting
    t.join()

    print("✅ Main script complete.")