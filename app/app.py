import streamlit as st
import os
import json
import base64
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import (
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ELASTICSEARCH_URL,
    ELASTICSEARCH_API_KEY,
    ELASTICSEARCH_INDEX_NAME
)
from src.core.rag_engine import RAGEngine
from src.core.indexer import Indexer
from src.core.retriever import Retriever
from src.ai.adaptive_generator import AdaptiveGenerator
from src.processors.text_processor import TextProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.image_processor import ImageProcessor
from src.processors.audio_processor import AudioProcessor
from src.data.models import Document

load_dotenv()

rag_engine = RAGEngine()
indexer = Indexer()
retriever = Retriever()
adaptive_generator = AdaptiveGenerator()
text_processor = TextProcessor()
pdf_processor = PDFProcessor()
image_processor = ImageProcessor()
audio_processor = AudioProcessor()

class DataIndexer:
    """Classe responsável pela indexação de diferentes tipos de dados"""
    
    def __init__(self):
        self.indexer_core = indexer
        self.text_processor = text_processor
        self.pdf_processor = pdf_processor
        self.image_processor = image_processor
        self.audio_processor = audio_processor

    def extract_text_from_pdf(self, pdf_file) -> str:
        return self.pdf_processor.process(pdf_file.read())
    
    def transcribe_audio_with_whisper(self, audio_file) -> str:
        return self.audio_processor.process(audio_file.read())
    
    def extract_text_from_image(self, image_file) -> str:
        return self.image_processor.process(image_file.read(), image_file.type)
    
    def index_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Indexa documento no Elasticsearch usando o Indexer da nova arquitetura"""
        try:
            doc = Document(id=metadata.get("filename", "unknown"), content=content, metadata=metadata)
            return self.indexer_core.index_document(doc)
        except Exception as e:
            st.error(f"Erro ao indexar documento: {e}")
            return False

class AdaptiveLearningSystem:
    """Sistema principal de aprendizagem adaptativa"""
    
    def __init__(self):
        self.indexer = DataIndexer()
        self.retriever = retriever
        self.adaptive_generator = adaptive_generator
    
    def search_content(self, query: str, content_type: str = None) -> List[Dict]:
        """Busca conteúdo usando o Retriever da nova arquitetura"""
        try:
            return self.retriever.retrieve_documents(query, content_type)
        except Exception as e:
            st.error(f"Erro na busca: {e}")
            return []
    
    def generate_adaptive_content(self, user_profile: Dict, topic: str) -> Tuple[str, List[Dict]]:
        """Gera conteúdo adaptativo usando o AdaptiveGenerator da nova arquitetura e retorna as fontes"""
        try:
            related_content_docs = self.retriever.retrieve_documents(topic)
            context = "\n".join([doc["content"] for doc in related_content_docs])
            
            generated_response = self.adaptive_generator.generate_content(user_profile, topic, related_content=context)
            
            return generated_response, related_content_docs
        except Exception as e:
            st.error(f"Erro ao gerar conteúdo adaptativo: {e}")
            return "Erro ao gerar conteúdo.", []

def main():
    st.set_page_config(
        page_title="Sistema de Aprendizagem Adaptativa",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 Sistema de Aprendizagem Adaptativa")
    st.markdown("---")
    
    if 'learning_system' not in st.session_state:
        st.session_state.learning_system = AdaptiveLearningSystem()
    
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'knowledge_level': 'iniciante',
            'learning_preference': 'texto',
            'difficulties': []
        }
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        st.subheader("Perfil do Usuário")
        knowledge_level = st.selectbox(
            "Nível de Conhecimento",
            ["iniciante", "intermediário", "avançado"],
            index=["iniciante", "intermediário", "avançado"].index(st.session_state.user_profile['knowledge_level'])
        )
        
        learning_preference = st.selectbox(
            "Preferência de Aprendizado",
            ["texto", "vídeo", "imagem", "exercício"],
            index=["texto", "vídeo", "imagem", "exercício"].index(st.session_state.user_profile['learning_preference'])
        )
        
        st.session_state.user_profile.update({
            'knowledge_level': knowledge_level,
            'learning_preference': learning_preference
        })
    
    tab1, tab2, tab3 = st.tabs(["📚 Indexação de Dados", "🤖 Chat Adaptativo", "🔍 Busca de Conteúdo"])
    
    with tab1:
        st.header("📚 Indexação de Dados")
        
        uploaded_files = st.file_uploader(
            "Faça upload dos seus materiais de estudo",
            type=['txt', 'pdf', 'mp4', 'jpg', 'jpeg', 'png', 'json'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.expander(f"Processar: {uploaded_file.name}"):
                    if st.button(f"Indexar {uploaded_file.name}", key=f"index_{uploaded_file.name}"):
                        with st.spinner("Processando arquivo..."):
                            content = ""
                            file_type = uploaded_file.type
                            
                            if file_type == "text/plain":
                                content = text_processor.process(uploaded_file) # Usar o novo processador
                            elif file_type == "application/pdf":
                                content = st.session_state.learning_system.indexer.extract_text_from_pdf(uploaded_file)
                            elif file_type.startswith("video/") or file_type.startswith("audio/"):
                                content = st.session_state.learning_system.indexer.transcribe_audio_with_whisper(uploaded_file)
                            elif file_type.startswith("image/"):
                                content = st.session_state.learning_system.indexer.extract_text_from_image(uploaded_file)
                            elif file_type == "application/json":
                                json_data = json.load(uploaded_file)
                                content = json.dumps(json_data, indent=2)
                            
                            metadata = {
                                "filename": uploaded_file.name,
                                "type": file_type,
                                "size": uploaded_file.size
                            }
                            
                            if content:
                                success = st.session_state.learning_system.indexer.index_document(content, metadata)
                                if success:
                                    st.success(f"✅ {uploaded_file.name} indexado com sucesso!")
                                else:
                                    st.error(f"❌ Erro ao indexar {uploaded_file.name}")
                            else:
                                st.error("❌ Não foi possível extrair conteúdo do arquivo")
    
    with tab2:
        st.header("🤖 Chat Adaptativo")
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Faça uma pergunta sobre o que você quer aprender..."):

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Gerando resposta adaptativa..."):
                    response, sources = st.session_state.learning_system.generate_adaptive_content(
                        st.session_state.user_profile, 
                        prompt
                    )

                    st.markdown(response)
                    if sources:
                        st.markdown("**Fontes:**")
                        for source in sources:
                            st.markdown(f"- {source['metadata']['filename']} (Tipo: {source['metadata']['type']})")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with tab3:
        st.header("🔍 Busca de Conteúdo")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("Digite sua busca:")
        
        with col2:
            content_filter = st.selectbox(
                "Filtrar por tipo:",
                ["Todos", "text/plain", "application/pdf", "video/mp4", "image/jpeg", "application/json"]
            )
        
        if st.button("🔍 Buscar"):
            if search_query:
                with st.spinner("Buscando conteúdo..."):
                    filter_type = None if content_filter == "Todos" else content_filter
                    results = st.session_state.learning_system.search_content(search_query, filter_type)
                    
                    if results:
                        st.success(f"Encontrados {len(results)} resultados:")
                        
                        for i, result in enumerate(results):
                            with st.expander(f"Resultado {i+1}: {result['metadata']['filename']}"):
                                st.write("**Tipo:**", result['metadata']['type'])
                                st.write("**Conteúdo:**")
                                st.text(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                    else:
                        st.warning("Nenhum resultado encontrado.")

if __name__ == "__main__":
    main()


