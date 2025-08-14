from langchain.vectorstores import FAISS
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from utils.logger_setup import setup_logger
import contextlib
import io
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger(__name__)

# Load embeddings & DB
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.load_local("faiss_news_store", embeddings, allow_dangerous_deserialization=True)

# Set up time-aware retriever
retriever = TimeWeightedVectorStoreRetriever(
    vectorstore=vectorstore,
    decay_rate=0.01,  # how much older docs decay in importance
    k=5,              # top k similar
    score_threshold=0.3,  # optional: remove low-score docs
    metadata_key="published_at"  # important!
)

def retrieve_related_past_news(article: dict) -> list[dict]:
    related_news = []

    article_content = article['content']

    # Suppress unwanted stdout prints
    with contextlib.redirect_stdout(io.StringIO()):
        docs = retriever.invoke(article_content)

    for doc in docs:
        doc_content = doc.page_content
        doc_date = doc.metadata.get('published_at')  

        related_news.append({  
            'article_content': doc_content,
            'article_date': doc_date
        })

    return related_news

