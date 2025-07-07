"""
Serviço de chat - orquestra conversas e mensagens
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.database import get_collection

logger = logging.getLogger(__name__)

class ChatService:
    """Serviço de chat com persistência MongoDB"""
    
    def __init__(self):
        self.ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")
        self.base_voice_url = "http://voice-service:8004"
        # self.voice_service_url = os.getenv("VOICE_SERVICE_URL", "http://voice-service:8004")  # Comentado temporariamente
    
    async def start_or_get_conversation(self, session_id: str) -> Dict[str, Any]:
        """Iniciar ou recuperar conversa existente"""
        try:
            conversations = get_collection("conversations")
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username do session_id 
            username = None
            if "_" in session_id:
                try:
                    username = session_id.split("_", 1)[0]
                except:
                    logger.warning(f"⚠️ Não foi possível extrair username do session_id: {session_id}")
            
            # Verificar se a conversa já existe
            existing = await conversations.find_one({"session_id": session_id})
            
            if existing:
                logger.info(f"📖 Recuperando conversa existente: {session_id} (username: {username})")
                return {
                    "session_id": session_id,
                    "exists": True,
                    "user_preferences": existing.get("user_preferences", {}),
                    "created_at": existing.get("created_at"),
                    "updated_at": existing.get("updated_at")
                }
            else:
                # Criar nova conversa
                conversation_data = {
                    "session_id": session_id,
                    "username": username,  # 🔒 Adicionar username para auditoria
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "user_preferences": {},
                    "message_count": 0
                }
                
                await conversations.insert_one(conversation_data)
                logger.info(f"🆕 Nova conversa criada: {session_id} (username: {username})")
                
                return {
                    "session_id": session_id,
                    "exists": False,
                    "created_at": conversation_data["created_at"]
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar/recuperar conversa: {e}")
            raise
    
    async def process_user_message(self, session_id: str, user_message: str, session_objective: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processar mensagem do usuário e gerar resposta da IA
        """
        try:
            logger.info(f"💬 PROCESSANDO MENSAGEM para sessão {session_id}")
            logger.info(f"📝 Mensagem do usuário: {user_message[:100]}...")
            
            # ✅ NOVO: Detectar se é sessão de cadastro (session-1)
            # Extrair session_id original para verificar se é session-1
            original_session_id = session_id
            username_part = ""
            
            if "_" in session_id:
                try:
                    last_underscore_index = session_id.rfind("_")
                    if last_underscore_index != -1:
                        username_part = session_id[:last_underscore_index]
                        original_session_id = session_id[last_underscore_index + 1:]
                        logger.info(f"🔍 DETECÇÃO: session_id='{session_id}' -> username='{username_part}', original='{original_session_id}'")
                    else:
                        logger.warning(f"⚠️ Underscore não encontrado em: {session_id}")
                except Exception as ex:
                    logger.error(f"❌ Erro ao extrair session_id: {ex}")
            else:
                logger.info(f"🔍 DETECÇÃO: session_id='{session_id}' (sem underscore)")
            
            # Log da verificação de session-1
            is_registration_session = original_session_id == "session-1"
            logger.info(f"🎯 VERIFICAÇÃO: original_session_id='{original_session_id}', is_registration={is_registration_session}")
            
            # Se for session-1, usar nossa função de cadastro
            if is_registration_session:
                logger.info(f"🔒 DETECTADA SESSÃO DE CADASTRO - usando função própria para {session_id}")
                return await self._handle_registration_session(session_id, user_message)
            
            # Para outras sessões, usar fluxo normal com OpenAI
            logger.info(f"🤖 SESSÃO NORMAL - usando OpenAI para {session_id}")
            
            # Criar ou recuperar conversa
            await self.start_or_get_conversation(session_id)
            
            # Extrair username do session_id para buscar preferências
            username = session_id.split('_')[0] if '_' in session_id else 'default'
            
            # Carregar preferências do usuário (voz, etc.)
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            
            selected_voice = "pt-BR-Neural2-A"  # padrão
            voice_enabled = True
            
            if user and user.get("preferences"):
                preferences = user["preferences"]
                selected_voice = preferences.get("selected_voice", selected_voice)
                voice_enabled = preferences.get("voice_enabled", voice_enabled)
            
            # Buscar initial_prompt se não foi fornecido via session_objective
            initial_prompt = None
            if not session_objective:
                initial_prompt = await self._get_session_initial_prompt(session_id)
                if initial_prompt:
                    logger.info(f"📋 Initial prompt encontrado para sessão {session_id}")
                else:
                    logger.warning(f"⚠️ Initial prompt não encontrado para sessão {session_id}")
            
            # Gerar resposta da IA
            ai_response_data = await self._get_ai_response(
                user_message, 
                session_id, 
                selected_voice, 
                voice_enabled,
                session_objective,
                initial_prompt
            )
            
            # Salvar mensagem do usuário
            user_message_id = await self._save_message(session_id, "user", user_message)
            
            # Salvar resposta da IA
            ai_message_id = await self._save_message(
                session_id, 
                "ai", 
                ai_response_data["content"], 
                ai_response_data.get("audio_url")
            )
            
            # Atualizar contador de mensagens
            await self._update_message_count(session_id)
            
            return {
                "success": True,
                "data": {
                    "user_message": {
                        "id": user_message_id,
                        "content": user_message
                    },
                    "ai_response": {
                        "id": ai_message_id,
                        "content": ai_response_data["content"],
                        "audioUrl": ai_response_data.get("audio_url"),
                        "provider": ai_response_data.get("provider", "unknown"),
                        "model": ai_response_data.get("model", "unknown")
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar mensagem: {str(e)}"
            }
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        try:
            messages = get_collection("messages")
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = None
            if "_" in session_id:
                try:
                    username = session_id.split("_", 1)[0]
                except:
                    logger.warning(f"⚠️ Não foi possível extrair username do session_id: {session_id}")
            
            # Construir query com dupla validação
            query = {"session_id": session_id}
            if username:
                # 🔒 Adicionar filtro por username para segurança adicional
                query["username"] = username
                logger.info(f"📖 Carregando histórico com validação dupla - session_id: {session_id}, username: {username}")
            else:
                logger.warning(f"⚠️ Carregando histórico apenas por session_id (legado): {session_id}")
            
            # Buscar todas as mensagens da sessão com validação de usuário
            cursor = messages.find(
                query,
                sort=[("created_at", 1)]
            )
            
            history = []
            async for msg in cursor:
                history.append({
                    "id": str(msg["_id"]),
                    "type": msg["type"],
                    "content": msg["content"],
                    "audio_url": msg.get("audio_url"),
                    "created_at": msg["created_at"]
                })
            
            logger.info(f"📖 Histórico carregado para {session_id}: {len(history)} mensagens (username: {username})")
            
            return {
                "session_id": session_id,
                "history": history,
                "message_count": len(history)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico: {e}")
            raise
    
    async def update_conversation_data(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualizar dados da conversa"""
        try:
            conversations = get_collection("conversations")
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await conversations.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0 or result.matched_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar conversa: {e}")
            raise
    
    async def _save_message(self, session_id: str, message_type: str, content: str, audio_url: Optional[str] = None) -> str:
        """Salvar mensagem no MongoDB"""
        try:
            messages = get_collection("messages")
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username do session_id para validação adicional
            # Formato esperado: "username_original_session_id"
            username = None
            if "_" in session_id:
                try:
                    username = session_id.split("_", 1)[0]
                except:
                    logger.warning(f"⚠️ Não foi possível extrair username do session_id: {session_id}")
            
            message_data = {
                "session_id": session_id,
                "username": username,  # 🔒 Adicionar username para dupla validação
                "type": message_type,
                "content": content,
                "audio_url": audio_url,
                "created_at": datetime.utcnow()
            }
            
            result = await messages.insert_one(message_data)
            
            # Log de auditoria para rastreamento
            logger.info(f"💾 Mensagem salva - session_id: {session_id}, username: {username}, type: {message_type}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            raise
    
    async def _get_ai_response(self, user_message: str, session_id: str, selected_voice: str, voice_enabled: bool = True, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Obter resposta da IA (versão simplificada sem httpx)"""
        try:
            # Para agora, retornar uma resposta padrão já que httpx não está disponível
            # TODO: Implementar chamada HTTP adequada quando httpx estiver disponível
            
            logger.info(f"🤖 Gerando resposta para: {user_message[:50]}...")
            
            # Resposta padrão empática baseada na abordagem Rogers
            default_responses = [
                "Entendo como você está se sentindo. Pode me contar mais sobre isso?",
                "Isso parece ser muito importante para você. Como isso te afeta?",
                "Percebo que há algo significativo no que você está compartilhando. Gostaria de explorar isso mais?",
                "Suas palavras me mostram muito sobre seus sentimentos. O que mais vem à sua mente sobre isso?",
                "Compreendo que isso é parte da sua experiência. Como você se sente em relação a isso agora?",
                "Obrigada por compartilhar isso comigo. Que sentimentos isso desperta em você?",
                "Vejo que isso tem um significado especial para você. Pode me ajudar a entender melhor?",
                "Suas reflexões são muito valiosas. O que você pensa sobre essa situação?",
                "Sinto que há algo profundo no que você está expressando. Como isso se conecta com você?",
                "Agradeço sua abertura em compartilhar isso. O que isso representa para você?"
            ]
            
            # Escolher resposta baseada no hash da mensagem para consistência
            import hashlib
            hash_obj = hashlib.md5(user_message.encode())
            response_index = int(hash_obj.hexdigest(), 16) % len(default_responses)
            ai_response_text = default_responses[response_index]
            
            return {
                "content": ai_response_text,
                "audio_url": None,  # Não geramos áudio por enquanto
                "provider": "internal",
                "model": "empathic_fallback"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta da IA: {e}")
            return {
                "content": "Desculpe, estou aqui para te escutar. Pode me contar como você está se sentindo?",
                "audio_url": None,
                "provider": "fallback",
                "model": "fallback"
            }
    
    async def _get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter contexto da conversa para enviar ao AI Service"""
        try:
            messages = get_collection("messages")
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = None
            if "_" in session_id:
                try:
                    username = session_id.split("_", 1)[0]
                except:
                    logger.warning(f"⚠️ Não foi possível extrair username do session_id: {session_id}")
            
            # Construir query com dupla validação
            query = {"session_id": session_id}
            if username:
                # 🔒 Adicionar filtro por username para segurança adicional
                query["username"] = username
                logger.info(f"🔍 Buscando mensagens com validação dupla - session_id: {session_id}, username: {username}")
            else:
                logger.warning(f"⚠️ Buscando mensagens apenas por session_id (legado): {session_id}")
            
            # Buscar mensagens da sessão com validação de usuário
            cursor = messages.find(
                query,
                sort=[("created_at", 1)]
            )
            
            context = []
            async for msg in cursor:
                # Converter para formato esperado pelo AI Service
                context.append({
                    "type": msg["type"],
                    "content": msg["content"]
                })
            
            logger.info(f"🔍 Contexto da conversa {session_id}: {len(context)} mensagens (username: {username})")
            return context
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto da conversa: {e}")
            return []
    
    async def _get_session_initial_prompt(self, session_id: str) -> Optional[str]:
        """Buscar o initial_prompt da sessão terapêutica do usuário"""
        try:
            # 🔒 Extrair username do session_id para buscar na coleção correta
            username = None
            original_session_id = session_id
            
            if "_" in session_id:
                try:
                    # Formato: "teste_01_session-1" -> username="teste_01", original="session-1"
                    # Precisamos encontrar o último "_" e dividir por aí
                    last_underscore_index = session_id.rfind("_")
                    if last_underscore_index != -1:
                        username = session_id[:last_underscore_index]  # "teste_01"
                        original_session_id = session_id[last_underscore_index + 1:]  # "session-1"
                    else:
                        # Fallback se não encontrar underscore
                        username = session_id
                        original_session_id = session_id
                    
                    logger.info(f"🔍 Extraído - username: {username}, original_session_id: {original_session_id}")
                except Exception as ex:
                    logger.warning(f"⚠️ Erro ao extrair username do session_id: {session_id} - {ex}")
            
            # Buscar na coleção user_therapeutic_sessions primeiro (sessão específica do usuário)
            if username:
                user_sessions = get_collection("user_therapeutic_sessions")
                user_session = await user_sessions.find_one({
                    "username": username,
                    "session_id": original_session_id
                })
                
                if user_session and user_session.get("initial_prompt"):
                    logger.info(f"✅ Initial prompt encontrado na user_therapeutic_sessions para {username}:{original_session_id}")
                    return user_session["initial_prompt"]
                else:
                    logger.warning(f"⚠️ User session não encontrada: username={username}, session_id={original_session_id}")
            
            # Se não encontrar na sessão do usuário, buscar na coleção therapeutic_sessions (template)
            sessions = get_collection("therapeutic_sessions")
            session = await sessions.find_one({"session_id": original_session_id})
            
            if session and session.get("initial_prompt"):
                logger.info(f"✅ Initial prompt encontrado no template: {original_session_id}")
                return session["initial_prompt"]
            else:
                logger.warning(f"⚠️ Template session não encontrada: {original_session_id}")
            
            logger.warning(f"⚠️ Nenhum initial_prompt encontrado para session_id: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar initial_prompt para sessão {session_id}: {e}")
            return None
    
    # async def _generate_audio(self, text: str, session_id: str, voice: str) -> Optional[str]:
    #     """Gerar áudio via Voice Service - COMENTADO TEMPORARIAMENTE"""
    #     try:
    #         async with httpx.AsyncClient(timeout=60.0) as client:
    #             response = await client.post(
    #                 f"{self.voice_service_url}/api/v1/synthesize",
    #                 json={
    #                     "text": text,
    #                     "voice": voice,
    #                     "speed": 1.0,
    #                     "pitch": 0.0
    #             }
    #             )
    #             
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 audio_url = data.get("audio_url")
    #                 if audio_url:
    #                     # Extrair o nome do arquivo da URL completa
    #                     audio_filename = audio_url.split("/")[-1]
    #                     # Retornar URL para acessar o áudio via gateway
    #                     return f"/api/voice/audio/{audio_filename}"
    #                 else:
    #                     logger.warning("⚠️ Voice Service não retornou URL do áudio")
    #                     return None
    #             else:
    #                 logger.warning(f"⚠️ Voice Service retornou {response.status_code}: {response.text}")
    #                 return None
    #                 
    #     except Exception as e:
    #         logger.error(f"❌ Erro ao gerar áudio: {e}")
    #         return None
    
    async def _update_message_count(self, session_id: str):
        """Atualizar contador de mensagens da conversa"""
        try:
            conversations = get_collection("conversations")
            await conversations.update_one(
                {"session_id": session_id},
                {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar contador: {e}")
    
    async def list_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Listar conversas recentes
        """
        try:
            conversations = get_collection("conversations")
            
            cursor = conversations.find(
                {},
                sort=[("updated_at", -1)],
                limit=limit
            )
            
            result = []
            async for conv in cursor:
                result.append({
                    "session_id": conv["session_id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": conv.get("message_count", 0)
                })
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar conversas: {e}")
            raise

    async def get_conversation_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma conversa pelo session_id e retorna como dicionário."""
        try:
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})
            
            if conversation:
                return {
                    "session_id": conversation["session_id"],
                    "created_at": conversation["created_at"],
                    "updated_at": conversation["updated_at"],
                    "message_count": conversation.get("message_count", 0),
                    "user_preferences": conversation.get("user_preferences", {})
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversa por session_id: {e}")
            raise

    # ✅ NOVO: Sistema de cadastro/onboarding para session-1
    async def _handle_registration_session(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Gerenciar a sessão de cadastro (session-1) com perguntas próprias, sem OpenAI
        """
        try:
            logger.info(f"🔍 PROCESSANDO SESSÃO DE CADASTRO para {session_id}")
            
            # Extrair username do session_id
            username = session_id.split('_')[0] if '_' in session_id else 'usuario'
            
            # Buscar dados existentes do usuário
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})
            
            # Inicializar dados de cadastro se não existir
            if not conversation:
                conversation = {
                    "session_id": session_id,
                    "username": username,
                    "started_at": datetime.now(),
                    "messages": [],
                    "registration_data": {},
                    "registration_step": 0,
                    "is_registration_complete": False
                }
                await conversations.insert_one(conversation)
            
            # Recuperar dados de cadastro
            registration_data = conversation.get("registration_data", {})
            current_step = conversation.get("registration_step", 0)
            
            # Definir perguntas de cadastro
            registration_questions = [
                {
                    "step": 0,
                    "question": f"Olá! Eu sou sua assistente terapêutica. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você. Primeiro, me conta: qual é a sua idade?",
                    "field": "idade",
                    "type": "number"
                },
                {
                    "step": 1,
                    "question": "Obrigada! Agora me conta: como você se identifica em relação ao seu gênero? (Por exemplo: feminino, masculino, não-binário, prefiro não responder, etc.)",
                    "field": "genero",
                    "type": "text"
                },
                {
                    "step": 2,
                    "question": "Perfeito! E como você se identifica em relação à sua cor/raça? (Por exemplo: branco, negro, pardo, indígena, asiático, prefiro não responder, etc.)",
                    "field": "cor_raca",
                    "type": "text"
                },
                {
                    "step": 3,
                    "question": "Obrigada por compartilhar! Agora me conta: em que cidade e estado você mora atualmente?",
                    "field": "localizacao",
                    "type": "text"
                },
                {
                    "step": 4,
                    "question": "Ótimo! Como é sua situação de moradia? Você mora sozinho(a), com família, amigos, companheiro(a)? Me conta um pouco sobre isso.",
                    "field": "situacao_moradia",
                    "type": "text"
                },
                {
                    "step": 5,
                    "question": "Entendi! E como você descreveria sua relação com sua família? Vocês são próximos, há conflitos, moram longe? Fique à vontade para compartilhar o que se sentir confortável.",
                    "field": "relacao_familia",
                    "type": "text"
                },
                {
                    "step": 6,
                    "question": "Obrigada por compartilhar! Agora me conta: qual é sua ocupação atual? Você trabalha, estuda, está desempregado(a)? Como é sua rotina?",
                    "field": "ocupacao",
                    "type": "text"
                },
                {
                    "step": 7,
                    "question": "Interessante! E o que te trouxe até aqui? O que você espera dessas nossas conversas? Há algo específico que gostaria de trabalhar ou simplesmente quer ter um espaço para se expressar?",
                    "field": "motivacao_terapia",
                    "type": "text"
                },
                {
                    "step": 8,
                    "question": "Muito obrigada por compartilhar todas essas informações comigo! Isso me ajuda muito a te conhecer melhor. Há mais alguma coisa sobre você que gostaria de me contar? Algo que considera importante para nossa conversa?",
                    "field": "informacoes_adicionais",
                    "type": "text"
                }
            ]
            
            # Se é a primeira mensagem (step 0), fazer a primeira pergunta
            if current_step == 0 and not conversation.get("messages"):
                ai_response = registration_questions[0]["question"]
                
                # Salvar mensagem do usuário e resposta
                user_message_id = await self._save_message(session_id, "user", user_message)
                ai_message_id = await self._save_message(session_id, "ai", ai_response)
                
                # Atualizar step
                await conversations.update_one(
                    {"session_id": session_id},
                    {"$set": {"registration_step": 1}}
                )
                
                logger.info(f"✅ CADASTRO: Primeira pergunta enviada para {username}")
                
                # ✅ CORREÇÃO: Retornar no mesmo formato que process_user_message
                return {
                    "success": True,
                    "data": {
                        "user_message": {
                            "id": user_message_id,
                            "content": user_message
                        },
                        "ai_response": {
                            "id": ai_message_id,
                            "content": ai_response,
                            "audioUrl": None,
                            "provider": "registration_system",
                            "model": "cadastro_v1"
                        }
                    }
                }
            
            # Processar resposta do usuário e fazer próxima pergunta
            if current_step > 0 and current_step <= len(registration_questions):
                # Salvar resposta do usuário
                user_message_id = await self._save_message(session_id, "user", user_message)
                
                # Armazenar a resposta no campo correspondente
                if current_step <= len(registration_questions):
                    field = registration_questions[current_step - 1]["field"]
                    registration_data[field] = user_message.strip()
                    
                    # Atualizar dados no banco
                    await conversations.update_one(
                        {"session_id": session_id},
                        {"$set": {"registration_data": registration_data}}
                    )
                    
                    logger.info(f"📝 CADASTRO: Campo '{field}' salvo para {username}")
                
                # Verificar se há próxima pergunta
                if current_step < len(registration_questions):
                    ai_response = registration_questions[current_step]["question"]
                    next_step = current_step + 1
                    logger.info(f"❓ CADASTRO: Pergunta {current_step + 1} para {username}")
                else:
                    # Finalizar cadastro
                    ai_response = f"""Perfeito! Muito obrigada por compartilhar todas essas informações comigo, {username}! 

Agora eu te conheço melhor e posso oferecer um apoio mais personalizado. Suas informações estão seguras e serão usadas apenas para tornar nossas conversas mais significativas.

Seu cadastro foi finalizado com sucesso! 🎉

Você agora pode acessar as outras sessões terapêuticas na sua jornada de autoconhecimento. Cada sessão foi cuidadosamente desenvolvida para te apoiar em diferentes aspectos da sua vida."""
                    
                    next_step = current_step + 1
                    
                    # Marcar cadastro como completo
                    await conversations.update_one(
                        {"session_id": session_id},
                        {"$set": {"is_registration_complete": True}}
                    )
                    
                    # Criar perfil do usuário na coleção users
                    await self._save_user_profile(username, registration_data)
                    
                    # ✅ NOVO: Criar sessões terapêuticas para o usuário se não existirem
                    try:
                        from .user_therapeutic_session_service import UserTherapeuticSessionService
                        user_session_service = UserTherapeuticSessionService()
                        
                        # Verificar se o usuário já tem sessões
                        existing_sessions = await user_session_service.get_user_sessions(username)
                        
                        if not existing_sessions:
                            # Criar todas as sessões terapêuticas para o usuário
                            clone_result = await user_session_service.clone_sessions_for_user(username)
                            logger.info(f"🔄 Sessões criadas para usuário {username}: {clone_result}")
                        
                        # Agora marcar session-1 como completed
                        completion_success = await user_session_service.complete_session(username, "session-1", 100, status="completed")
                        if completion_success:
                            logger.info(f"✅ Session-1 marcada como COMPLETED para {username}")
                            
                            # Desbloquear próxima sessão automaticamente
                            unlock_success = await user_session_service.unlock_session(username, "session-2")
                            if unlock_success:
                                logger.info(f"🔓 Session-2 desbloqueada para {username}")
                        else:
                            logger.warning(f"⚠️ Falha ao marcar session-1 como completed para {username}")
                            
                    except Exception as session_error:
                        logger.error(f"❌ Erro ao finalizar session-1: {session_error}")
                    
                    logger.info(f"🎉 CADASTRO: Finalizado para {username}")
                
                # Salvar resposta da IA
                ai_message_id = await self._save_message(session_id, "ai", ai_response)
                
                # Atualizar step
                await conversations.update_one(
                    {"session_id": session_id},
                    {"$set": {"registration_step": next_step}}
                )
                
                # ✅ NOVO: Se o cadastro foi finalizado, adicionar flags específicos
                response_data = {
                    "success": True,
                    "data": {
                        "user_message": {
                            "id": user_message_id,
                            "content": user_message
                        },
                        "ai_response": {
                            "id": ai_message_id,
                            "content": ai_response,
                            "audioUrl": None,
                            "provider": "registration_system",
                            "model": "cadastro_v1"
                        }
                    }
                }
                
                # Se o cadastro foi finalizado, adicionar flags específicos
                if current_step == len(registration_questions):
                    response_data["data"]["registration_completed"] = True
                    response_data["data"]["session_finished"] = True
                    response_data["data"]["session_status"] = "completed"
                    response_data["data"]["redirect_to_home"] = True
                    response_data["data"]["completion_message"] = "Cadastro finalizado com sucesso! Esta sessão está agora concluída. Você pode revisar a conversa, mas não pode enviar mais mensagens."
                
                return response_data
            
            # Se o cadastro já foi completado, usar mensagem padrão
            ai_response = f"Olá novamente, {username}! Como posso te ajudar hoje?"
            user_message_id = await self._save_message(session_id, "user", user_message)
            ai_message_id = await self._save_message(session_id, "ai", ai_response)
            
            logger.info(f"💬 CADASTRO: Conversa normal pós-cadastro para {username}")
            
            # ✅ CORREÇÃO: Retornar no mesmo formato que process_user_message
            return {
                "success": True,
                "data": {
                    "user_message": {
                        "id": user_message_id,
                        "content": user_message
                    },
                    "ai_response": {
                        "id": ai_message_id,
                        "content": ai_response,
                        "audioUrl": None,
                        "provider": "registration_system",
                        "model": "cadastro_v1"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na sessão de cadastro: {e}")
            return {
                "success": False,
                "error": f"Erro na sessão de cadastro: {str(e)}"
            }
    
    async def _save_user_profile(self, username: str, registration_data: Dict[str, Any]):
        """
        Salvar perfil completo e padronizado do usuário na coleção users
        """
        try:
            users = get_collection("users")
            
            # ✅ NOVO: Padronizar e estruturar os dados do usuário
            user_profile = self._create_standardized_profile(username, registration_data)
            
            # Atualizar ou criar usuário com perfil padronizado
            await users.update_one(
                {"username": username},
                {
                    "$set": {
                        "username": username,
                        "user_profile": user_profile,
                        "profile_completed": True,
                        "profile_completed_at": datetime.now(),
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Perfil padronizado do usuário {username} salvo com sucesso")
            logger.info(f"📊 Dados salvos: {user_profile}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar perfil do usuário: {e}")

    def _create_standardized_profile(self, username: str, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar perfil padronizado a partir dos dados de cadastro
        """
        # Dados pessoais básicos
        personal_info = {
            "idade": self._normalize_age(registration_data.get("idade", "")),
            "genero": self._normalize_gender(registration_data.get("genero", "")),
            "cor_raca": self._normalize_race(registration_data.get("cor_raca", "")),
            "localizacao": self._normalize_location(registration_data.get("localizacao", ""))
        }
        
        # Situação social e familiar
        social_info = {
            "situacao_moradia": self._normalize_text(registration_data.get("situacao_moradia", "")),
            "relacao_familia": self._normalize_text(registration_data.get("relacao_familia", "")),
            "ocupacao": self._normalize_text(registration_data.get("ocupacao", ""))
        }
        
        # Motivação e objetivos terapêuticos
        therapeutic_info = {
            "motivacao_terapia": self._normalize_text(registration_data.get("motivacao_terapia", "")),
            "informacoes_adicionais": self._normalize_text(registration_data.get("informacoes_adicionais", "")),
            "objetivos_identificados": self._extract_objectives(registration_data)
        }
        
        # Perfil completo estruturado
        standardized_profile = {
            "personal_info": personal_info,
            "social_info": social_info,
            "therapeutic_info": therapeutic_info,
            "profile_summary": self._generate_profile_summary(personal_info, social_info, therapeutic_info),
            "keywords": self._extract_keywords(registration_data),
            "risk_factors": self._identify_risk_factors(registration_data),
            "strengths": self._identify_strengths(registration_data),
            "created_at": datetime.now().isoformat(),
            "data_source": "session-1_registration"
        }
        
        return standardized_profile

    def _normalize_age(self, age_input: str) -> Dict[str, Any]:
        """Normalizar idade"""
        try:
            age_text = str(age_input).strip().lower()
            
            # Extrair número da idade
            import re
            age_numbers = re.findall(r'\d+', age_text)
            
            if age_numbers:
                age = int(age_numbers[0])
                
                # Categorizar por faixa etária
                if age < 18:
                    category = "menor_idade"
                elif age < 25:
                    category = "jovem_adulto"
                elif age < 35:
                    category = "adulto_jovem"
                elif age < 50:
                    category = "adulto"
                elif age < 65:
                    category = "adulto_maduro"
                else:
                    category = "idoso"
                
                return {
                    "valor": age,
                    "categoria": category,
                    "original": age_input.strip()
                }
            else:
                return {
                    "valor": None,
                    "categoria": "nao_informado",
                    "original": age_input.strip()
                }
                
        except Exception:
            return {
                "valor": None,
                "categoria": "erro_processamento",
                "original": age_input.strip()
            }

    def _normalize_gender(self, gender_input: str) -> Dict[str, Any]:
        """Normalizar gênero"""
        gender_text = str(gender_input).strip().lower()
        
        # Mapeamento de termos comuns
        gender_mapping = {
            "feminino": "feminino",
            "mulher": "feminino", 
            "f": "feminino",
            "masculino": "masculino",
            "homem": "masculino",
            "m": "masculino",
            "não-binário": "nao_binario",
            "nao binario": "nao_binario",
            "não binário": "nao_binario",
            "nao-binario": "nao_binario",
            "nb": "nao_binario",
            "trans": "trans",
            "transgender": "trans",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder",
            "não responder": "prefere_nao_responder"
        }
        
        normalized = gender_mapping.get(gender_text, "outros")
        
        return {
            "categoria": normalized,
            "original": gender_input.strip()
        }

    def _normalize_race(self, race_input: str) -> Dict[str, Any]:
        """Normalizar cor/raça"""
        race_text = str(race_input).strip().lower()
        
        # Mapeamento baseado no IBGE
        race_mapping = {
            "branco": "branco",
            "branca": "branco",
            "negro": "negro",
            "negra": "negro",
            "preto": "negro",
            "preta": "negro",
            "pardo": "pardo",
            "parda": "pardo",
            "amarelo": "amarelo",
            "amarela": "amarelo",
            "asiático": "amarelo",
            "asiática": "amarelo",
            "indígena": "indigena",
            "índio": "indigena",
            "índia": "indigena",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder"
        }
        
        normalized = race_mapping.get(race_text, "outros")
        
        return {
            "categoria": normalized,
            "original": race_input.strip()
        }

    def _normalize_location(self, location_input: str) -> Dict[str, Any]:
        """Normalizar localização"""
        location_text = str(location_input).strip()
        
        # Tentar extrair cidade e estado
        import re
        
        # Padrões comuns: "Cidade, Estado" ou "Cidade - Estado"
        patterns = [
            r"(.+?)[,\-]\s*(.+?)$",  # Cidade, Estado ou Cidade - Estado
            r"(.+?)\s+(\w{2})$",     # Cidade SP (sigla do estado)
        ]
        
        city = ""
        state = ""
        
        for pattern in patterns:
            match = re.search(pattern, location_text)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                break
        
        if not city and not state:
            city = location_text
        
        return {
            "cidade": city,
            "estado": state,
            "original": location_input.strip(),
            "formatted": f"{city}, {state}" if state else city
        }

    def _normalize_text(self, text_input: str) -> Dict[str, Any]:
        """Normalizar texto geral"""
        text = str(text_input).strip()
        
        return {
            "content": text,
            "length": len(text),
            "words": len(text.split()) if text else 0,
            "has_content": len(text) > 0
        }

    def _extract_objectives(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair objetivos terapêuticos baseados nas respostas"""
        objectives = []
        
        # Analisar motivação para terapia
        motivation = registration_data.get("motivacao_terapia", "").lower()
        
        # Palavras-chave que indicam objetivos específicos
        objective_keywords = {
            "ansiedade": "Trabalhar questões de ansiedade",
            "depressão": "Apoio para questões depressivas",
            "relacionamento": "Melhorar relacionamentos",
            "família": "Resolver questões familiares",
            "trabalho": "Questões profissionais e carreira",
            "autoestima": "Fortalecer autoestima",
            "stress": "Gerenciar stress e pressão",
            "luto": "Processar perdas e luto",
            "mudança": "Lidar com mudanças de vida",
            "crescimento": "Desenvolvimento pessoal"
        }
        
        for keyword, objective in objective_keywords.items():
            if keyword in motivation:
                objectives.append(objective)
        
        # Se não encontrar objetivos específicos, usar objetivo geral
        if not objectives:
            objectives.append("Desenvolvimento pessoal e bem-estar")
        
        return objectives

    def _generate_profile_summary(self, personal_info: Dict, social_info: Dict, therapeutic_info: Dict) -> str:
        """Gerar resumo do perfil do usuário"""
        summary_parts = []
        
        # Informações pessoais
        if personal_info["idade"]["valor"]:
            summary_parts.append(f"Idade: {personal_info['idade']['valor']} anos ({personal_info['idade']['categoria']})")
        
        if personal_info["genero"]["categoria"] != "outros":
            summary_parts.append(f"Gênero: {personal_info['genero']['categoria']}")
        
        if personal_info["localizacao"]["formatted"]:
            summary_parts.append(f"Localização: {personal_info['localizacao']['formatted']}")
        
        # Situação social
        if social_info["ocupacao"]["has_content"]:
            summary_parts.append(f"Ocupação: {social_info['ocupacao']['content'][:50]}...")
        
        # Motivação terapêutica
        if therapeutic_info["motivacao_terapia"]["has_content"]:
            summary_parts.append(f"Motivação: {therapeutic_info['motivacao_terapia']['content'][:100]}...")
        
        return "; ".join(summary_parts)

    def _extract_keywords(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair palavras-chave relevantes do cadastro"""
        keywords = []
        
        # Combinar todas as respostas textuais
        text_fields = [
            registration_data.get("genero", ""),
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]
        
        combined_text = " ".join(text_fields).lower()
        
        # Palavras-chave relevantes para terapia
        relevant_keywords = [
            "ansiedade", "depressão", "stress", "família", "relacionamento",
            "trabalho", "estudos", "autoestima", "confiança", "medo",
            "tristeza", "raiva", "solidão", "conflito", "mudança",
            "crescimento", "desenvolvimento", "apoio", "ajuda"
        ]
        
        for keyword in relevant_keywords:
            if keyword in combined_text:
                keywords.append(keyword)
        
        return keywords

    def _identify_risk_factors(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar possíveis fatores de risco mencionados"""
        risk_factors = []
        
        # Combinar respostas para análise
        all_responses = " ".join([
            registration_data.get("relacao_familia", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        
        # Indicadores de possíveis fatores de risco
        risk_indicators = {
            "isolamento": ["sozinho", "isolado", "sem amigos", "sem apoio"],
            "conflitos_familiares": ["conflito", "briga", "problema família", "família difícil"],
            "questoes_profissionais": ["desempregado", "sem trabalho", "stress trabalho", "problema trabalho"],
            "questoes_emocionais": ["deprimido", "triste", "ansioso", "medo", "pânico"],
            "mudancas_significativas": ["separação", "divórcio", "morte", "luto", "mudança"]
        }
        
        for risk_type, indicators in risk_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    risk_factors.append(risk_type)
                    break
        
        return list(set(risk_factors))  # Remove duplicatas

    def _identify_strengths(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar forças e recursos positivos mencionados"""
        strengths = []
        
        # Combinar respostas para análise
        all_responses = " ".join([
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        
        # Indicadores de forças e recursos
        strength_indicators = {
            "apoio_familiar": ["família unida", "apoio família", "família próxima", "bom relacionamento família"],
            "apoio_social": ["amigos", "apoio", "grupo", "comunidade"],
            "estabilidade_profissional": ["trabalho", "empregado", "carreira", "estudando"],
            "autoconsciencia": ["autoconhecimento", "crescimento", "desenvolvimento", "melhorar"],
            "motivacao_mudanca": ["quer mudar", "disposto", "determinado", "esperança"]
        }
        
        for strength_type, indicators in strength_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    strengths.append(strength_type)
                    break
        
        return list(set(strengths))  # Remove duplicatas 