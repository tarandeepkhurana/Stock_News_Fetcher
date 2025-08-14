import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re

def fetch_financial_express_articles_headless():
    url = "https://www.financialexpress.com/market/"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    for _ in range(4):  # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text(separator="\n")

    # Split based on timestamp-like indicators
    article_chunks = re.split(r"\n(?=\w+ \d{1,2}, 2025.*IST)", full_text)

    articles = []
    for chunk in article_chunks:
        lines = [line.strip() for line in chunk.strip().split("\n") if len(line.strip()) > 0]
        if len(lines) >= 2:
            timestamp_candidate = lines[0]
            # Check if first line is a timestamp
            if re.search(r"\w+ \d{1,2}, 2025.*IST", timestamp_candidate):
                timestamp = timestamp_candidate
                title = lines[1]  # 2nd line is now title
                description_lines = lines[2:]  # everything after title
            else:
                timestamp = ""
                title = lines[0]
                description_lines = lines[1:]

            description = " ".join(description_lines).strip()
            articles.append({
                "title": title,
                "content": description,
                "url": url,
                "source": "Web",
                "published_at": timestamp
            })

    return articles

def fetch_economic_times_articles_headless():
    url = "https://economictimes.indiatimes.com/markets/stocks/news"

    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Scroll to load more content
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        articles = []
    elements = driver.find_elements(By.CLASS_NAME, "eachStory")
    # print(f"🧪 Found {len(elements)} article blocks")

    for e in elements:
        try:
            full_text = e.text.strip()
            lines = full_text.split("\n")

            # Usually: [title, published_at, description...]
            if len(lines) >= 3:
                title = lines[0]
                published = lines[1]
                description = " ".join(lines[2:])

                # Link
                link_el = e.find_element(By.TAG_NAME, "a")
                link = link_el.get_attribute("href")

                if len(title) > 40 and len(description) > 40:
                    articles.append({
                        "title": title,
                        "content": description,
                        "url": link,
                        "source": "Web",
                        "published_at": published
                    })
        except Exception as ex:
            print("⚠️ Skipped due to:", ex)
            continue


    driver.quit()
    return articles