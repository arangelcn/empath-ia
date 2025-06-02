#!/bin/bash

# Script para desenvolvimento com hot reload

echo "🚀 Iniciando empatIA em modo de desenvolvimento..."
echo "📁 Hot reload ativado para mudanças nos arquivos"
echo ""

# Verifica se docker compose watch está disponível
if docker compose version | grep -q "v2"; then
    echo "✨ Usando Docker Compose Watch (hot reload automático)"
    docker compose up --build --watch
else
    echo "⚡ Usando volumes com reload manual"
    docker compose up --build
fi 