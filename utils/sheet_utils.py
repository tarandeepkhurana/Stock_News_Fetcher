import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logging.basicConfig(level=logging.INFO)

def connect_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google-sheets-key.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Stock_News")
        logging.info("Connected with the google sheets.")

        return {
            "stock_news_details": sheet.worksheet("Stock_News_Details"),
            "stock_news_insights": sheet.worksheet("Stock_News_Insights"),
            "nifty50_1month_data": sheet.worksheet("Nifty50_1Month_Data"),
            "reliance_stocks_data": sheet.worksheet("RELIANCE.NS")
        }
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while connecting with the sheets: {e}")
        raise 
    
def clear_and_initialize_sheet(sheet):
    # Clear existing content
    sheet.clear()
    
    HEADERS = ["Timestamp", "Source", "Headline", "Summary", "URL"]
    sheet.append_row(HEADERS)
    logging.info("Sheet cleared and initialized.")

if __name__ == "__main__":
    connect_google_sheets()
