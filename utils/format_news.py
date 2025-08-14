def format_related_news(related_news: list[dict]) -> str:
    formatted = ""

    for idx, news_item in enumerate(related_news, 1):
        date = news_item.get("article_date", "Unknown Date")
        content = news_item["article_content"]

        formatted += f"{idx}. **[{date}]**:\n{content.strip()}\n\n"

    return formatted

def format_latest_news(news: dict) -> str:
    return (
        f"**Title**: {news.get('title', 'N/A')}\n"
        f"**Content**: {news.get('content', '').strip()}\n"
        f"**Date**: {news.get('published_at', 'Unknown')}\n"
        f"**Source**: {news.get('source', 'Unknown')}\n"
        f"**Link**: {news.get('url', 'N/A')}"
    )

test_news = {
    "title": "HDFC Bank Reports Record Q1 Profits Amid Strong Loan Growth",
    "content": "HDFC Bank has posted a record net profit of ₹12,500 crore in Q1 FY26, driven by strong loan disbursement and improved net interest margin. The bank also announced plans to expand its rural lending portfolio.",
    "published_at": "2025-07-27",
    "source": "Moneycontrol",
    "url": "https://www.moneycontrol.com/news/business/hdfc-bank-q1-results-2025-750crore-profit.html"
}
result = format_latest_news(test_news)
print(result)