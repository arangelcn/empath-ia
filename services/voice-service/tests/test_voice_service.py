import pytest
from fastapi.testclient import TestClient
import os
import sys

# Adicionar o diretório pai ao path para importar o módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

client = TestClient(app)

def test_health_check():
    """Teste do endpoint de health check"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "voice-service"
    assert "timestamp" in data
    assert "tts_model_loaded" in data

def test_root_endpoint():
    """Teste do endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "empatIA Voice Service"
    assert "endpoints" in data

def test_config_endpoint():
    """Teste do endpoint de configuração"""
    response = client.get("/config")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service_name"] == "voice-service"
    assert "service_port" in data
    assert "base_url" in data

def test_model_status():
    """Teste do endpoint de status do modelo"""
    response = client.get("/api/voice/models/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "model_name" in data
    assert "device" in data
    assert "model_loaded" in data

def test_speak_endpoint_validation():
    """Teste de validação do endpoint speak"""
    # Teste com texto vazio
    response = client.post("/api/voice/speak", json={"text": ""})
    assert response.status_code == 422  # Validation error
    
    # Teste com texto muito longo
    long_text = "a" * 6000
    response = client.post("/api/voice/speak", json={"text": long_text})
    assert response.status_code == 422  # Validation error

def test_speak_direct_endpoint():
    """Teste do endpoint speak direto"""
    response = client.post("/speak", json={"text": "Olá, teste de voz"})
    # Pode retornar 500 se o modelo não estiver carregado, mas deve retornar uma resposta
    assert response.status_code in [200, 500]
    
    data = response.json()
    assert "success" in data
    assert "message" in data

if __name__ == "__main__":
    pytest.main([__file__]) 