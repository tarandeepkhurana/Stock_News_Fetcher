from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings  
from langchain_openai import OpenAIEmbeddings
from src2.news_ingestion.fetch_all_sources_news import fetch_all_sources_news
from langchain.schema import Document
import os
from dotenv import load_dotenv

load_dotenv()

def convert_news_to_documents(news_items):
    docs = []
    for item in news_items:
        content = item.get("content", "")
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        published_at = item.get("published_at", "")

        text = f"{title}\n\n{content}"
        
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "title": title,
                    "url": url,
                    "published_at": published_at,
                    "source": source
                }
            )
        )
    return docs

# Save to FAISS vector store
def save_to_vector_store(documents, db_path="faiss_news_store"):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if os.path.exists(db_path):
        db = FAISS.load_local(db_path, embeddings)
        db.add_documents(documents)
    else:
        db = FAISS.from_documents(documents, embeddings)
    db.save_local(db_path)
    return db

if __name__ == "__main__":
    item = {}
    rss_urls = [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    result = fetch_all_sources_news(rss_urls)
    docs = convert_news_to_documents(result)
    save_to_vector_store(docs)

    