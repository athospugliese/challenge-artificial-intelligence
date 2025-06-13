import openai
import os
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class RAGEngine:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_embeddings(self, text: str) -> list[float]:
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embeddings: {e}")
            return []

    def process_query(self, query: str):

        pass


