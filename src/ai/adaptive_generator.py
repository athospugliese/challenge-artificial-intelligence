import openai
from typing import Dict
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class AdaptiveGenerator:
    def __init__(self):
        self.openai_client = openai.OpenAI()

    def generate_content(self, user_profile: Dict, topic: str, related_content: str = "") -> str:
        knowledge_level = user_profile.get("knowledge_level", "iniciante")
        learning_preference = user_profile.get("learning_preference", "texto")
        difficulties = user_profile.get("difficulties", [])

        interactive_prompt_part = ""
        if not difficulties: 
            interactive_prompt_part = f"""
Para entender melhor suas necessidades, por favor, responda:
1. Qual aspecto de \'{topic}\' você considera mais desafiador ou confuso?
2. Você prefere aprender este tópico através de um texto explicativo, um resumo em áudio, ou um infográfico/vídeo curto?
"""
        else:
            interactive_prompt_part = f"""
Com base nas suas dificuldades anteriores ({", ".join(difficulties)}), vou focar em explicar \'{topic}\' de forma clara.
"""

        prompt = f"""
Você é um tutor especializado em criar conteúdo educacional adaptativo. Seu objetivo é identificar as dificuldades e lacunas de conhecimento dos usuários em um diálogo fluido e intuitivo, e então gerar conteúdos dinâmicos curtos e relevantes, adaptados ao nível de conhecimento e preferência de aprendizado do usuário. O escopo deve estar limitado ao conteúdo fornecido. **NÃO INVENTE INFORMAÇÕES.**

--- Conteúdo de Referência do Elasticsearch ---
{related_content}
---

Baseado no perfil do usuário e no conteúdo de referência acima, gere uma explicação adaptativa sobre \'{topic}\'.

**Sua resposta DEVE começar apresentando o conteúdo original relevante do Elasticsearch que você utilizou, seguido pela sua explicação adaptada.**

Perfil do usuário:
- Nível de conhecimento: {knowledge_level}
- Preferência de aprendizado: {learning_preference}
- Dificuldades identificadas: {", ".join(difficulties) if difficulties else 'Nenhuma'}

{interactive_prompt_part}

Sua resposta deve ser concisa, relevante e informativa. Se a preferência for vídeo ou áudio, descreva como o conteúdo seria apresentado nesse formato, já que você só pode gerar texto.

Exemplo de formato de resposta para vídeo/áudio:
"Aqui está uma explicação em texto. Se fosse um vídeo/áudio, ele abordaria [pontos chave] com [elementos visuais/sonoros]."

Por favor, comece sua resposta com o conteúdo original relevante e, em seguida, a explicação direta do tópico, e se for o caso, adicione a sugestão de formato no final.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt}
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro ao gerar conteúdo adaptativo: {e}")
            return "Erro ao gerar conteúdo."


