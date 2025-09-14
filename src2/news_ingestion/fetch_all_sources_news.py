from apscheduler.schedulers.background import BackgroundScheduler
from src2.news_ingestion.news_webscrape import (
    fetch_economic_times_articles_headless, 
    fetch_financial_express_articles_headless, 
    fetch_articles_from_pulse,
    fetch_articles_from_groww
)
from src2.news_ingestion.news_rss import fetch_rss_entries
from langchain_openai import OpenAIEmbeddings
from utils.normalize_dates import normalize_date
from utils.logger_setup import setup_logger

import json
import hashlib
from datetime import datetime, timedelta, timezone
import os
import numpy as np

from dotenv import load_dotenv
load_dotenv()

logger = setup_logger(__name__)

# Params
SIM_THRESHOLD = 0.85   # cosine similarity threshold
TTL_HOURS = 48         # keep last 2 days
DEDUP_PATH = "dedup_store.json"

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")


### ----------------- Utility functions -----------------

def get_hash(text: str) -> str:
    """Fast exact-match hash (MD5)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_dedup_store() -> dict:
    if os.path.exists(DEDUP_PATH):
        with open(DEDUP_PATH, "r") as f:
            return json.load(f)
    return {}

def save_dedup_store(store: dict):
    with open(DEDUP_PATH, "w") as f:
        json.dump(store, f)

def cleanup_store(store: dict, ttl_hours=TTL_HOURS):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
    return {
        k: v for k, v in store.items()
        if datetime.fromisoformat(v["timestamp"]) >= cutoff
    }

def is_duplicate(item, store):
    """
    Check if article is duplicate using:
    1. Hash
    2. Embedding similarity
    """
    text = f"{item.get('title','')} {item.get('content','')}"
    h = get_hash(item.get("title","") + item.get("url",""))

    # 1. Exact hash match
    if h in store:
        return True, store

    # 2. Embedding similarity check
    try:
        new_emb = embeddings_model.embed_query(text)
    except Exception as e:
        logger.error(f"❌ Embedding failed: {e}")
        return False, store

    for old_h, old_data in store.items():
        old_emb = np.array(old_data["embedding"])
        sim = np.dot(new_emb, old_emb) / (np.linalg.norm(new_emb) * np.linalg.norm(old_emb))
        if sim >= SIM_THRESHOLD:
            return True, store

    # If not duplicate → add to store
    store[h] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "embedding": new_emb
    }
    return False, store


### ----------------- Main Fetcher -----------------

def fetch_all_sources_news(rss_urls) -> list[dict]:
    store = load_dedup_store()
    store = cleanup_store(store)

    new_items = []

    # Define priority order
    sources = [
        ("Financial Express", fetch_financial_express_articles_headless),
        ("Economic Times (Web)", fetch_economic_times_articles_headless),
        ("RSS", lambda: sum([fetch_rss_entries(u) for u in rss_urls], [])),
        ("Groww", fetch_articles_from_groww),
        ("Pulse", fetch_articles_from_pulse),
    ]

    for source_name, fetch_fn in sources:
        try:
            articles = fetch_fn()
            for item in articles:
                raw_date = item.get("published_at", "")
                normalized_date = normalize_date(raw_date)
                item["published_at"] = normalized_date or datetime.now(timezone.utc).isoformat()

                dup, store = is_duplicate(item, store)
                if not dup:
                    logger.info(f"🆕 {source_name}: {item['title']}")
                    new_items.append(item)
        except Exception as e:
            logger.warning(f"⚠️ Error fetching {source_name}: {e}")

    save_dedup_store(store)

    logger.info(f"✅ Found {len(new_items)} new unique articles")
    return new_items


if __name__ == "__main__":
    rss_urls = [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    result = fetch_all_sources_news(rss_urls)
    print(result[:5])
