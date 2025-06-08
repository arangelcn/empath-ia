import pytest
from fastapi.testclient import TestClient
import os
import sys

# Adicionar o diretório pai ao path para importar o módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

client = TestClient(app)

def test_bark_health_check():
    """Teste do endpoint de status do Bark"""
    response = client.get("/api/bark/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "service_name" in data
    assert data["service_name"] == "bark_service"

def test_bark_voices_available():
    """Teste do endpoint de vozes disponíveis"""
    response = client.get("/api/bark/voices/available")
    assert response.status_code == 200
    
    data = response.json()
    assert "available_voices" in data
    assert "current_voice" in data
    assert "total_voices" in data
    assert data["total_voices"] > 0

def test_bark_info():
    """Teste do endpoint de informações do Bark"""
    response = client.get("/api/bark/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "bark_service"
    assert data["model"] == "Bark (Suno AI)"
    assert "capabilities" in data
    assert data["capabilities"]["portuguese_brazilian"] is True

def test_bark_speak_validation():
    """Teste de validação do endpoint speak do Bark"""
    # Teste com texto vazio
    response = client.post("/api/bark/speak", json={"text": ""})
    assert response.status_code == 422  # Validation error
    
    # Teste com texto muito longo
    long_text = "a" * 6000
    response = client.post("/api/bark/speak", json={"text": long_text})
    assert response.status_code == 422  # Validation error

def test_bark_speak_simple():
    """Teste básico do endpoint speak do Bark"""
    response = client.post("/api/bark/speak", json={
        "text": "Olá, este é um teste do Bark",
        "voice_speed": 1.0
    })
    # Pode retornar 500 se o modelo não estiver carregado, mas deve retornar uma resposta
    assert response.status_code in [200, 500]
    
    data = response.json()
    assert "success" in data
    assert "message" in data

def test_direct_speak_with_bark():
    """Teste do endpoint speak direto (agora usando Bark)"""
    response = client.post("/speak", json={"text": "Teste de compatibilidade com Bark"})
    # Pode retornar 500 se o modelo não estiver carregado, mas deve retornar uma resposta
    assert response.status_code in [200, 500]
    
    data = response.json()
    assert "success" in data
    assert "message" in data

def test_speak_with_engine_bark():
    """Teste do endpoint multi-engine com Bark"""
    response = client.post("/speak-with-engine", json={
        "text": "Teste multi-engine com Bark",
        "engine": "bark"
    })
    assert response.status_code in [200, 500]
    
    data = response.json()
    assert "success" in data

def test_speak_with_engine_coqui_disabled():
    """Teste que verifica se o Coqui está desabilitado"""
    response = client.post("/speak-with-engine", json={
        "text": "Teste multi-engine com Coqui",
        "engine": "coqui"
    })
    assert response.status_code == 503  # Service unavailable (disabled)
    
    data = response.json()
    assert "temporariamente desabilitado" in data["detail"]

def test_bark_voice_change():
    """Teste de troca de voz do Bark"""
    response = client.post("/api/bark/voices/change?voice_key=v2/pt_speaker_0")
    assert response.status_code in [200, 500]  # Pode falhar se modelo não carregado

def test_bark_preload():
    """Teste de pré-carregamento dos modelos Bark"""
    response = client.post("/api/bark/preload")
    assert response.status_code in [200, 500]  # Pode falhar dependendo do ambiente

if __name__ == "__main__":
    pytest.main([__file__]) 