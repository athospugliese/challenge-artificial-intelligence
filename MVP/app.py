import streamlit as st
import os
import json
import base64
from dotenv import load_dotenv
from typing import List, Dict, Any
import openai
import google.generativeai as genai
from elasticsearch import Elasticsearch
import pymupdf
from io import BytesIO
import tempfile

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

es_client = Elasticsearch(
    [os.getenv("ELASTICSEARCH_URL")],
    api_key=os.getenv("ELASTICSEARCH_API_KEY"),
    verify_certs=True
)

INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "search-4ehj")

class DataIndexer:
    """Classe responsável pela indexação de diferentes tipos de dados"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI()
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        self.gemini_vision_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Gera embeddings usando OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            st.error(f"Erro ao gerar embeddings: {e}")
            return []
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extrai texto de arquivo PDF usando PyMuPDF"""
        try:
            doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def transcribe_audio_with_whisper(self, audio_file) -> str:
        """Transcreve áudio usando Whisper da OpenAI"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name
            
            with open(tmp_file_path, "rb") as audio:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            
            os.unlink(tmp_file_path)
            
            return transcript.text
        except Exception as e:
            st.error(f"Erro ao transcrever áudio: {e}")
            return ""
    
    def extract_text_from_image(self, image_file) -> str:
        """Extrai texto de imagem usando Gemini Vision"""
        try:

            image_data = image_file.read()
            
            prompt = "Extraia todo o texto visível nesta imagem e forneça também uma descrição detalhada do conteúdo visual."
            
            response = self.gemini_vision_model.generate_content([
                prompt,
                {"mime_type": image_file.type, "data": base64.b64encode(image_data).decode()}
            ])
            
            return response.text
        except Exception as e:
            st.error(f"Erro ao extrair texto da imagem: {e}")
            return ""
    
    def index_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Indexa documento no Elasticsearch"""
        try:
            embeddings = self.generate_embeddings(content)
            
            doc = {
                "content": content,
                "embeddings": embeddings,
                "metadata": metadata,
                "timestamp": "2025-01-06T12:00:00Z"
            }
            
            response = es_client.index(
                index=INDEX_NAME,
                body=doc
            )
            
            return response["result"] == "created"
        except Exception as e:
            st.error(f"Erro ao indexar documento: {e}")
            return False

class AdaptiveLearningSystem:
    """Sistema principal de aprendizagem adaptativa"""
    
    def __init__(self):
        self.indexer = DataIndexer()
        self.openai_client = openai.OpenAI()
    
    def search_content(self, query: str, content_type: str = None) -> List[Dict]:
        """Busca conteúdo no Elasticsearch"""
        try:
            query_embeddings = self.indexer.generate_embeddings(query)
            
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": query
                                }
                            },
                            {
                                "script_score": {
                                    "query": {"match_all": {}},
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'embeddings') + 1.0",
                                        "params": {"query_vector": query_embeddings}
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 5
            }
            
            if content_type:
                search_body["query"]["bool"]["filter"] = [
                    {"term": {"metadata.type": content_type}}
                ]
            
            response = es_client.search(
                index=INDEX_NAME,
                body=search_body
            )
            
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            st.error(f"Erro na busca: {e}")
            return []
    
    def generate_adaptive_content(self, user_profile: Dict, topic: str) -> str:
        """Gera conteúdo adaptativo baseado no perfil do usuário"""
        try:
            related_content = self.search_content(topic)
            
            context = "\n".join([content["content"][:500] for content in related_content])
            
            prompt = f"""
            Baseado no perfil do usuário e no conteúdo disponível, gere uma explicação adaptativa sobre {topic}.
            
            Perfil do usuário:
            - Nível de conhecimento: {user_profile.get('knowledge_level', 'iniciante')}
            - Preferência de aprendizado: {user_profile.get('learning_preference', 'texto')}
            - Dificuldades identificadas: {user_profile.get('difficulties', [])}
            
            Conteúdo de referência:
            {context}
            
            Gere uma explicação clara e adaptada ao perfil do usuário.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um tutor especializado em criar conteúdo educacional adaptativo."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Erro ao gerar conteúdo adaptativo: {e}")
            return "Erro ao gerar conteúdo."

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
                            
                            # Processar baseado no tipo de arquivo
                            if file_type == "text/plain":
                                content = str(uploaded_file.read(), "utf-8")
                            elif file_type == "application/pdf":
                                content = st.session_state.learning_system.indexer.extract_text_from_pdf(uploaded_file)
                            elif file_type.startswith("video/"):
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
                            
                            # Indexar
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
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Faça uma pergunta sobre o que você quer aprender..."):

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Gerando resposta adaptativa..."):
                    response = st.session_state.learning_system.generate_adaptive_content(
                        st.session_state.user_profile, 
                        prompt
                    )
                    st.markdown(response)
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

