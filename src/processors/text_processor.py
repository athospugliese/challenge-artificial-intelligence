from .base_processor import BaseProcessor
from streamlit.runtime.uploaded_file_manager import UploadedFile

class TextProcessor(BaseProcessor):
    def process(self, uploaded_file: UploadedFile) -> str:
        return uploaded_file.read().decode("utf-8")


