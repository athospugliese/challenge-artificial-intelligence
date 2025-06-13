from .base_processor import BaseProcessor
import google.generativeai as genai
import base64
import os

class ImageProcessor(BaseProcessor):
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_vision_model = genai.GenerativeModel("gemini-1.5-flash")

    def process(self, file_content: bytes, mime_type: str) -> str:
        try:
            prompt = "Extraia todo o texto visível nesta imagem e forneça também uma descrição detalhada do conteúdo visual."
            response = self.gemini_vision_model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": base64.b64encode(file_content).decode()}
            ])
            return response.text
        except Exception as e:
            print(f"Erro ao extrair texto da imagem: {e}")
            return ""


