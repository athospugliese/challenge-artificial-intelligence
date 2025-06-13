import os
from elasticsearch import Elasticsearch
from src.core.rag_engine import RAGEngine
from typing import List, Dict, Any

class Retriever:
    def __init__(self):
        self.es = Elasticsearch(
            os.getenv("ELASTICSEARCH_URL"),
            api_key=os.getenv("ELASTICSEARCH_API_KEY")
        )
        self.index_name = os.getenv("ELASTICSEARCH_INDEX_NAME")
        self.rag_engine = RAGEngine()

    def retrieve_documents(self, query: str, content_type: str = None) -> List[Dict]:
        query_embeddings = self.rag_engine.generate_embeddings(query)

        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embeddings') + 1.0",
                                    "params": {"query_vector": query_embeddings}
                                }
                            }
                        }
                    ],
                    "should": [
                        {
                            "match": {
                                "content": {
                                    "query": query,
                                    "boost": 0.5 
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 0 
                }
            },
            "size": 5, 
            "min_score": 1.0 
        }

        if content_type and content_type != "Todos":

            search_body["query"]["bool"]["filter"] = [
                {"term": {"metadata.type.keyword": content_type}}
            ]

        try:
            response = self.es.search(
                index=self.index_name,
                body=search_body
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []


