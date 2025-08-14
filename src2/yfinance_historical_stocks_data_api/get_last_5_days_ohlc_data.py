from utils.logger_setup import setup_logger
import yfinance as yf
import pandas as pd
import datetime

logger = setup_logger(__name__)

def get_last_5_days_ohlc_data(ticker: str):
    try:
        end_date = datetime.datetime.today() - datetime.timedelta(days=1)
        df = yf.download(ticker, end=end_date.strftime('%Y-%m-%d'), period="10d")
        
        df.reset_index(inplace=True)
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        
        if isinstance(df.columns, pd.MultiIndex):
           df.columns = df.columns.get_level_values(0)
        
        df = df.round(2)
        df["Volume"] = df["Volume"].astype(int)

        last_5_days = df.tail(5)
        markdown_table = last_5_days.to_markdown(index=False)

        return markdown_table
    except Exception as e:
        logger.error(f"Error occurred while fetching OHLC data: {e}")

if __name__ == "__main__":
    result = get_last_5_days_ohlc_data("SBIN.NS")
    print(result)