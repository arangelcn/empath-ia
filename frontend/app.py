import streamlit as st
import requests
import time
from typing import List, Dict

st.set_page_config(page_title="empatIA", layout="centered")

st.title("🧠 empatIA - Psicólogo Virtual com Avatar")
st.markdown("Converse com um psicólogo virtual animado e empático.")

def call_backend(message: str, history: List[Dict[str, str]], max_retries: int = 3, delay: int = 2):
    """Call backend with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://backend:8000/chat",
                json={"message": message, "history": history},
                timeout=30
            )
            return response
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                st.warning(f"Tentativa {attempt + 1} falhou. Tentando novamente em {delay} segundos...")
                time.sleep(delay)
            else:
                raise e
        except Exception as e:
            raise e

# Initialize conversation history in session state
if "history" not in st.session_state:
    st.session_state["history"] = []  # type: List[Dict[str, str]]

user_input = st.text_input("Digite sua mensagem:")

if st.button("Limpar conversa"):
    st.session_state["history"] = []

# Exibir conversa existente
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        st.markdown(f"**Você:** {msg['content']}")
    else:
        st.markdown(f"**empatIA:** {msg['content']}")

if st.button("Enviar") and user_input:
    with st.spinner("Pensando..."):
        try:
            response = call_backend(user_input, st.session_state["history"])
            if response.status_code == 200:
                data = response.json()

                # Save user and assistant messages
                st.session_state["history"].append({"role": "user", "content": user_input})
                st.session_state["history"].append({"role": "assistant", "content": data["text"]})
                # Tratar vídeo do avatar
                if data.get("has_video") and data.get("video_url"):
                    st.success("🎬 Vídeo do avatar gerado com sucesso!")
                    try:
                        st.video(data["video_url"])
                    except Exception as video_error:
                        st.warning(f"⚠️ Erro ao exibir vídeo: {str(video_error)}")
                        st.info("💬 Resposta em texto disponível acima.")
                elif data.get("video_url") is None:
                    st.info("💬 Resposta em texto (vídeo do avatar não disponível)")
                    st.caption("🔧 Verifique se a DID_API_KEY está configurada corretamente.")
                else:
                    st.warning("⚠️ Vídeo do avatar não foi gerado")
                    
            else:
                st.error(f"Erro ao obter resposta do backend. Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço está rodando.")
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout na conexão com o backend.")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")

# Adicionar informações sobre configuração
with st.expander("ℹ️ Informações sobre configuração"):
    st.markdown("""
    **Para o vídeo do avatar funcionar:**
    1. Configure `DID_API_USERNAME` e `DID_API_PASSWORD` no arquivo `.env`
    2. Obtenha suas credenciais em: https://www.d-id.com/ → Account Settings
    3. Se a chave vier no formato `username:password`, separe em duas variáveis
    4. Reinicie os containers após configurar
    
    **Arquivo .env exemplo:**
    ```
    OPENAI_API_KEY=sua_chave_openai
    DID_API_USERNAME=seu_username
    DID_API_PASSWORD=sua_senha
    MODEL_NAME=gpt-4o
    ```
    
    **⚠️ Erro Status 500**: Verifique se as credenciais DID-AI estão corretas
    **⚠️ Erro 401/403**: Credenciais inválidas ou expiradas
    """)
