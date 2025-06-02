from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
from openai import OpenAI
from did_client import generate_avatar_video
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Initialize OpenAI client with the new v1.0+ API
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
model_name = os.getenv("MODEL_NAME", "gpt-4o")

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")

    if not message:
        return {"error": "Message is required"}

    try:
        # Generate text response from OpenAI
        logger.info(f"Processando mensagem: {message[:50]}...")
        
        chat_response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Você é um psicólogo virtual empático, baseado em Carl Rogers. Responda com escuta ativa, validação emocional e acolhimento."},
                {"role": "user", "content": message}
            ]
        )

        reply = chat_response.choices[0].message.content
        logger.info(f"Resposta gerada: {reply[:50]}...")

        # Try to generate avatar video
        video_url = None
        try:
            video_url = generate_avatar_video(reply)
            if video_url:
                logger.info(f"Vídeo gerado: {video_url}")
            else:
                logger.warning("Não foi possível gerar o vídeo do avatar")
        except Exception as video_error:
            logger.error(f"Erro ao gerar vídeo: {str(video_error)}")

        return {
            "text": reply, 
            "video_url": video_url,
            "has_video": video_url is not None
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        return {"error": f"Erro ao processar requisição: {str(e)}"}
