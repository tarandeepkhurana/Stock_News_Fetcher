import feedparser

def fetch_rss_entries(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"❌ Failed to parse feed {feed_url}:", feed.bozo_exception)
        return []

    entries = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        description = entry.get("description", "").strip()
        link = entry.get("link", "").strip()
        published = entry.get("published", "").strip()

        entries.append({
            "title": title,
            "content": description,
            "url": link,
            "source": "RSS-EconomicTimes",
            "published_at": published
        })

    return entries

if __name__ == "__main__":
    result = fetch_rss_entries("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms")
    print(len(result))
    print(result)