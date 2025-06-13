import os
from elasticsearch import Elasticsearch
from src.core.rag_engine import RAGEngine
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Indexer:
    def __init__(self):
        self.es = Elasticsearch(
            os.getenv("ELASTICSEARCH_URL"),
            api_key=os.getenv("ELASTICSEARCH_API_KEY")
        )
        self.index_name = os.getenv("ELASTICSEARCH_INDEX_NAME")
        self.rag_engine = RAGEngine()

    def index_document(self, document) -> bool:
        try:
            embeddings = self.rag_engine.generate_embeddings(document.content)
            doc_to_index = document.model_dump()
            doc_to_index["embeddings"] = embeddings

            response = self.es.index(
                index=self.index_name,
                document=doc_to_index
            )
            return response["result"] == "created"
        except Exception as e:
            print(f"Erro ao indexar documento: {e}")
            return False


