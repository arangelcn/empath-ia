import os
import requests
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_avatar_video(text):
    """Generate avatar video using DID-AI API"""
    api_username = os.getenv("DID_API_USERNAME")
    api_password = os.getenv("DID_API_PASSWORD")
    
    if not api_username or not api_password:
        logger.warning("DID_API_USERNAME ou DID_API_PASSWORD não encontradas nas variáveis de ambiente")
        return None
    
    if not text:
        logger.warning("Texto vazio fornecido para geração do vídeo")
        return None

    # DID-AI uses Basic Authentication with base64 encoding
    # Combine username:password and encode in base64
    try:
        # Combine username and password with colon
        credentials = f"{api_username}:{api_password}"
        # Encode the credentials in base64 for Basic auth
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        logger.info(f"API credentials encoded for Basic auth")
    except Exception as e:
        logger.error(f"Erro ao codificar credenciais: {str(e)}")
        return None

    avatar_url = "https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg"

    payload = {
        "source_url": "https://img.freepik.com/free-vector/smiling-young-man-illustration_1308-174669.jpg",
        "script": {
            "type": "text",
            "input": "Olá! Como você está se sentindo hoje?",
            "provider": {
            "type": "microsoft",
            "voice_id": "pt-BR-FranciscaNeural"
            }
        }
    }


    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Enviando requisição para DID-AI com texto: {text[:50]}...")
        
        response = requests.post(
            "https://api.d-id.com/talks",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Resposta DID-AI: Status {response.status_code}")
        
        if response.status_code == 201:  # DID-AI retorna 201 para criação
            data = response.json()
            talk_id = data.get("id")
            
            if talk_id:
                logger.info(f"Vídeo criado com ID: {talk_id}")
                # Retorna o ID para polling posterior ou URL se disponível
                return data.get("result_url") or f"https://api.d-id.com/talks/{talk_id}"
            
        else:
            logger.error(f"Erro na API DID-AI: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao chamar DID-AI: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado no DID-AI: {str(e)}")
        return None
