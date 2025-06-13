from .base_processor import BaseProcessor
import openai
import tempfile
import os

class AudioProcessor(BaseProcessor):
    def __init__(self):
        self.openai_client = openai.OpenAI()

    def process(self, file_content: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            with open(tmp_file_path, "rb") as audio:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            
            os.unlink(tmp_file_path)
            
            return transcript.text
        except Exception as e:
            print(f"Erro ao transcrever áudio: {e}")
            return ""


