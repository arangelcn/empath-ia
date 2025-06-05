#!/bin/bash

# Script de entrada para o container OpenFace
# Executa a extração de features e AUs de uma imagem

echo "=== OpenFace Feature Extraction ==="
echo "Verificando arquivos de entrada..."

# Verificar se o arquivo de entrada existe
if [ ! -f "/data/input.jpg" ]; then
    echo "ERRO: Arquivo /data/input.jpg não encontrado!"
    echo "Certifique-se de que a imagem foi copiada para o volume compartilhado."
    exit 1
fi

echo "Arquivo de entrada encontrado: /data/input.jpg"
echo "Iniciando extração de features..."

# Navegar para o diretório dos executáveis
cd /opt/OpenFace/build/bin

# Executar o FeatureExtraction com parâmetros para AUs
./FeatureExtraction -f /data/input.jpg -aus -out_dir /data

# Verificar se o arquivo de saída foi gerado
if [ -f "/data/input_au.csv" ]; then
    # Renomear para o nome esperado
    mv /data/input_au.csv /data/AU_output.csv
    echo "SUCCESS: Arquivo AU_output.csv gerado com sucesso!"
    echo "Caminho: /data/AU_output.csv"
else
    echo "ERRO: Falha na geração do arquivo de AUs"
    echo "Listando arquivos gerados em /data:"
    ls -la /data/
    exit 1
fi

echo "=== Processamento concluído ===" 