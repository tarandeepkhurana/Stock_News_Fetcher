from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

load_dotenv()

def clean_old_documents(db_path="faiss_news_store", days_to_keep=30):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    db = FAISS.load_local(db_path, embeddings)
    
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days_to_keep)
    docs = db.docstore._dict.values()
    fresh_docs = []

    for doc in docs:
        utc_date = doc.metadata.get("published_at", "") #published_at needs to exist compulsorily otherwise that news won't be removed which is a problem for us as we don't want old news articles
        try:
            doc_time = datetime.fromisoformat(utc_date)
            if doc_time >= cutoff_date:
                fresh_docs.append(doc)
        except:
            continue

    new_db = FAISS.from_documents(fresh_docs, embeddings)
    new_db.save_local(db_path)
    print(f"✅ Cleaned FAISS. Retained {len(fresh_docs)} recent documents.")

if __name__ == "__main__":
    clean_old_documents()