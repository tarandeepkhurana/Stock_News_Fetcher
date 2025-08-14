from apscheduler.schedulers.background import BackgroundScheduler
from src2.news_ingestion.news_webscrape import fetch_economic_times_articles_headless, fetch_financial_express_articles_headless
from src2.news_ingestion.news_rss import fetch_rss_entries
from utils.normalize_dates import normalize_date
from utils.logger_setup import setup_logger
import json
import hashlib
import signal
import time
import sys

logger = setup_logger(__name__)

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def fetch_all_sources_news(rss_urls, known_hashes_path="seen_hashes.json") -> list[dict]:
    try:
        with open(known_hashes_path, "r") as f:
            old_hashes = json.load(f)
    except FileNotFoundError:
        old_hashes = {}

    new_items = []
    new_hashes = {}

    # 1. Financial Express (Web scraping)
    try:
        fe_articles = fetch_financial_express_articles_headless()
        for item in fe_articles:
            raw_date = item.get("published_at", "")
            normalized_date = normalize_date(raw_date)
            item["published_at"] = normalized_date
            content_hash = hash_text(item["title"] + item["url"])
            if content_hash not in old_hashes:
                logger.info(f"🆕 New content from Financial Express: {item['title']}")
                new_items.append(item)
                new_hashes[content_hash] = item["url"]
    except Exception as e:
        logger.warning("⚠️ Error fetching Financial Express: %s", e)

    # 2. Economic Times (Web scraping)
    try:
        et_articles = fetch_economic_times_articles_headless()
        for item in et_articles:
            raw_date = item.get("published_at", "")
            normalized_date = normalize_date(raw_date)
            item["published_at"] = normalized_date
            content_hash = hash_text(item["title"] + item["url"])
            if content_hash not in old_hashes:
                logger.info(f"🆕 New content from Economic Times: {item['title']}")
                new_items.append(item)
                new_hashes[content_hash] = item["url"]
    except Exception as e:
        logger.warning("⚠️ Error fetching Economic Times: %s", e)

    # 3. RSS feeds using feedparser
    for rss_url in rss_urls:
        try:
            rss_articles = fetch_rss_entries(rss_url)
            for item in rss_articles:
                raw_date = item.get("published_at", "")
                normalized_date = normalize_date(raw_date)
                item["published_at"] = normalized_date
                content_hash = hash_text(item["title"] + item["url"])
                if content_hash not in old_hashes:
                    logger.info(f"🆕 New content from RSS: {item['title']}")
                    new_items.append(item)
                    new_hashes[content_hash] = item["url"]
        except Exception as e:
            logger.warning("⚠️ Error fetching RSS feed %s: %s", rss_url, e)

    # Merge and save updated hash list
    old_hashes.update(new_hashes)
    with open(known_hashes_path, "w") as f:
        json.dump(old_hashes, f)
    
    logger.info(f"✅ Found {len(new_items)} new articles")
    return new_items

# def job_runner():
#     rss_urls = [
#         "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
#     ]
#     new_articles = fetch_all_sources_news(rss_urls)
#     return new_articles

# def graceful_shutdown(scheduler):
#     logger.info("Shutting down scheduler...")
#     scheduler.shutdown(wait=True)
#     sys.exit(0)

if __name__ == "__main__":
    rss_urls = [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    result = fetch_all_sources_news(rss_urls)
    print(result[:10])
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(job_runner, "interval", minutes=7) 

    # scheduler.start()
    # logger.info("🕒 Scheduler started. Press Ctrl+C to exit.")

    # # Graceful shutdown on Ctrl+C
    # signal.signal(signal.SIGINT, lambda sig, frame: graceful_shutdown(scheduler))
    # signal.signal(signal.SIGTERM, lambda sig, frame: graceful_shutdown(scheduler))

    # try:
    #     while True:
    #         time.sleep(1)
    # except (KeyboardInterrupt, SystemExit):
    #     graceful_shutdown(scheduler)