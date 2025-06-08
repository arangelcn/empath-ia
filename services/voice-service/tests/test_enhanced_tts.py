#!/usr/bin/env python3
"""
Script de teste para validar as melhorias do serviço TTS
com suporte a modelos brasileiros e clonagem de voz
"""

import asyncio
import aiohttp
import json
import time
import os
from pathlib import Path
import argparse

# Configurações
BASE_URL = "http://localhost:8004"
TEST_TEXTS = {
    "brazilian_casual": "Oi, tudo bem? Como você está hoje? Espero que esteja tudo certo por aí!",
    "brazilian_formal": "Prezado usuário, gostaríamos de informar que o sistema está funcionando perfeitamente.",
    "brazilian_regional": "Uai, que legal esse sistema! Tá funcionando direitinho, sô!",
    "technical": "A síntese de voz em português brasileiro utiliza modelos avançados de deep learning.",
    "numbers": "Hoje é dia 15 de dezembro de 2024, são 14 horas e 30 minutos.",
    "emotions": "Que maravilha! Estou super feliz com os resultados. Isso é fantástico!"
}

class TTSEnhancedTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_service_health(self):
        """Testa se o serviço está funcionando"""
        print("🔍 Testando saúde do serviço...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Serviço OK - TTS carregado: {data.get('tts_model_loaded', False)}")
                    return True
                else:
                    print(f"❌ Serviço com problemas - Status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    async def test_model_status(self):
        """Testa informações do modelo atual"""
        print("\n🔍 Verificando status do modelo...")
        try:
            async with self.session.get(f"{self.base_url}/api/voice/models/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Modelo atual: {data.get('current_model', 'N/A')}")
                    print(f"   Nome: {data.get('model_name', 'N/A')}")
                    print(f"   Dispositivo: {data.get('device', 'N/A')}")
                    print(f"   Carregado: {data.get('model_loaded', False)}")
                    return data
        except Exception as e:
            print(f"❌ Erro ao verificar modelo: {e}")
            return None
    
    async def test_available_models(self):
        """Lista modelos disponíveis"""
        print("\n🔍 Verificando modelos disponíveis...")
        try:
            async with self.session.get(f"{self.base_url}/api/voice/models/available") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Modelos disponíveis:")
                    for model, desc in data.get('descriptions', {}).items():
                        current = "🔥" if model == data.get('current_model') else "  "
                        print(f"   {current} {model}: {desc}")
                    return data
        except Exception as e:
            print(f"❌ Erro ao listar modelos: {e}")
            return None
    
    async def test_text_to_speech(self, text: str, test_name: str):
        """Testa conversão de texto para fala"""
        print(f"\n🎤 Testando TTS: {test_name}")
        print(f"   Texto: '{text[:50]}...'")
        
        try:
            start_time = time.time()
            
            payload = {
                "text": text,
                "language": "pt",
                "voice_speed": 1.0
            }
            
            async with self.session.post(
                f"{self.base_url}/api/voice/speak",
                json=payload
            ) as response:
                
                processing_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Sucesso em {processing_time:.2f}s")
                    print(f"   URL: {data.get('audio_url', 'N/A')}")
                    print(f"   Duração: {data.get('duration', 0):.2f}s")
                    
                    self.results[test_name] = {
                        "success": True,
                        "processing_time": processing_time,
                        "audio_duration": data.get('duration', 0),
                        "audio_url": data.get('audio_url')
                    }
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Erro {response.status}: {error_text}")
                    self.results[test_name] = {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "processing_time": processing_time
                    }
                    
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            self.results[test_name] = {
                "success": False,
                "error": str(e)
            }
    
    async def test_model_switching(self):
        """Testa troca de modelos"""
        print("\n🔄 Testando troca de modelos...")
        
        # Obter modelos disponíveis
        models_data = await self.test_available_models()
        if not models_data:
            print("❌ Não foi possível obter lista de modelos")
            return
        
        available_models = list(models_data.get('available_models', {}).keys())
        original_model = models_data.get('current_model')
        
        for model in available_models:
            if model != original_model:
                print(f"\n🔄 Trocando para modelo: {model}")
                try:
                    payload = {"model_key": model}
                    async with self.session.post(
                        f"{self.base_url}/api/voice/models/change",
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ Modelo alterado: {data.get('message')}")
                            
                            # Testar uma frase com o novo modelo
                            await self.test_text_to_speech(
                                "Testando novo modelo de voz brasileira!",
                                f"model_test_{model}"
                            )
                        else:
                            error_text = await response.text()
                            print(f"❌ Erro ao trocar modelo: {error_text}")
                            
                except Exception as e:
                    print(f"❌ Erro ao trocar modelo: {e}")
        
        # Voltar ao modelo original
        if original_model:
            print(f"\n🔄 Voltando ao modelo original: {original_model}")
            try:
                payload = {"model_key": original_model}
                async with self.session.post(
                    f"{self.base_url}/api/voice/models/change",
                    json=payload
                ) as response:
                    if response.status == 200:
                        print("✅ Modelo original restaurado")
            except Exception as e:
                print(f"❌ Erro ao restaurar modelo: {e}")
    
    async def test_all_models_batch(self):
        """Testa todos os modelos de uma vez"""
        print("\n🚀 Testando todos os modelos em lote...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/voice/test-models") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Teste em lote concluído")
                    print(f"   Texto teste: '{data.get('test_text', '')}'")
                    print(f"   Modelo restaurado: {data.get('restored_model', 'N/A')}")
                    
                    results = data.get('results', {})
                    for model, result in results.items():
                        status = "✅" if result.get('success') else "❌"
                        print(f"   {status} {model}: {result.get('message', '')}")
                        if result.get('audio_url'):
                            print(f"      Áudio: {result['audio_url']}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Erro no teste em lote: {error_text}")
                    
        except Exception as e:
            print(f"❌ Erro no teste em lote: {e}")
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        print("🎯 Iniciando bateria de testes do TTS Aprimorado")
        print("=" * 60)
        
        # Teste básico de saúde
        if not await self.test_service_health():
            print("❌ Serviço não está funcionando. Abortando testes.")
            return
        
        # Informações do sistema
        await self.test_model_status()
        await self.test_available_models()
        
        # Testes de texto para fala
        print("\n🎤 Testando diferentes tipos de texto...")
        for test_name, text in TEST_TEXTS.items():
            await self.test_text_to_speech(text, test_name)
            await asyncio.sleep(1)  # Pausa entre testes
        
        # Teste de troca de modelos
        await self.test_model_switching()
        
        # Teste em lote
        await self.test_all_models_batch()
        
        # Resumo final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo dos resultados"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r.get('success', False))
        
        print(f"Total de testes: {total_tests}")
        print(f"Sucessos: {successful_tests}")
        print(f"Falhas: {total_tests - successful_tests}")
        print(f"Taxa de sucesso: {(successful_tests/total_tests*100):.1f}%")
        
        if successful_tests > 0:
            avg_processing_time = sum(
                r.get('processing_time', 0) 
                for r in self.results.values() 
                if r.get('success', False)
            ) / successful_tests
            
            avg_audio_duration = sum(
                r.get('audio_duration', 0) 
                for r in self.results.values() 
                if r.get('success', False) and r.get('audio_duration', 0) > 0
            ) / successful_tests
            
            print(f"Tempo médio de processamento: {avg_processing_time:.2f}s")
            print(f"Duração média do áudio: {avg_audio_duration:.2f}s")
        
        print("\nDetalhes por teste:")
        for test_name, result in self.results.items():
            status = "✅" if result.get('success', False) else "❌"
            processing_time = result.get('processing_time', 0)
            print(f"  {status} {test_name}: {processing_time:.2f}s")
            if not result.get('success', False):
                print(f"      Erro: {result.get('error', 'N/A')}")

async def main():
    parser = argparse.ArgumentParser(description="Teste do TTS Aprimorado")
    parser.add_argument("--url", default=BASE_URL, help="URL base do serviço")
    parser.add_argument("--quick", action="store_true", help="Teste rápido (apenas básico)")
    args = parser.parse_args()
    
    async with TTSEnhancedTester(args.url) as tester:
        if args.quick:
            # Teste rápido
            await tester.test_service_health()
            await tester.test_model_status()
            await tester.test_text_to_speech(
                TEST_TEXTS["brazilian_casual"], 
                "quick_test"
            )
        else:
            # Teste completo
            await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 