import pandas as pd
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)

def aggregate_multi_stock_tick_data(csv_path: str) -> dict:
    df = pd.read_csv(csv_path)
    
    df['readable_time'] = pd.to_datetime(df['readable_time'])
    df.sort_values(['id', 'readable_time'], inplace=True)

    # Drop invalid volumes and convert to numeric
    df = df.dropna(subset=["day_volume"])
    df["day_volume"] = pd.to_numeric(df["day_volume"], errors="coerce")

    # Prepare output dictionary
    result = {}

    for stock_id, group in df.groupby('id'):
        group = group.copy()
        group["volume"] = group["day_volume"].diff().fillna(0)
        group["volume"] = group["volume"].clip(lower=0)

        group.set_index("readable_time", inplace=True)

        # Resample per 1-minute window
        ohlc = group["price"].resample("1min").ohlc()
        vol = group["volume"].resample("1min").sum()

        aggregated = ohlc.copy()
        aggregated["volume"] = vol

        aggregated = aggregated.reset_index().rename(columns={"readable_time": "timestamp"})
        result[stock_id] = aggregated
    
    logger.info("Aggregated live tick data of the stocks.")
    return result

if __name__ == "__main__":
    result = aggregate_multi_stock_tick_data("tick_data_all_stocks_combined.csv")
    # print(result)
    result_rel = result["RELIANCE.NS"]
    result_df = pd.DataFrame(result_rel)
    result_markdown = result_df.to_markdown(index=False)
    print(result_markdown)