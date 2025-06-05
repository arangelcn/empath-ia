# Serviço OpenFace - empatIA

Este serviço utiliza o [OpenFace 2.0](https://github.com/TadasBaltrusaitis/OpenFace) para detectar expressões faciais e extrair Unidades de Ação (AUs) de imagens.

## Funcionalidade

O serviço processa uma imagem e gera um arquivo CSV com as Unidades de Ação detectadas, que são fundamentais para análise de expressões faciais e emoções.

## Como usar

### 1. Build do container (primeira vez)
```bash
docker compose build openface
```

### 2. Preparar a imagem de entrada
Copie sua imagem para o diretório `shared_data` com o nome `input.jpg`:
```bash
cp sua_imagem.jpg shared_data/input.jpg
```

### 3. Executar o processamento
```bash
docker compose run --rm openface
```

### 4. Verificar resultado
O arquivo `AU_output.csv` será gerado em `shared_data/AU_output.csv`.

## Exemplo de uso programático

```python
import os
import subprocess
import pandas as pd

def process_facial_expression(image_path):
    """
    Processa uma imagem para extrair Unidades de Ação usando OpenFace
    """
    # Copiar imagem para o diretório compartilhado
    shared_input = "shared_data/input.jpg"
    shared_output = "shared_data/AU_output.csv"
    
    # Limpar arquivos anteriores
    if os.path.exists(shared_output):
        os.remove(shared_output)
    
    # Copiar imagem de entrada
    os.system(f"cp {image_path} {shared_input}")
    
    # Executar OpenFace
    result = subprocess.run([
        "docker", "compose", "run", "--rm", "openface"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(shared_output):
        # Ler e retornar resultados
        au_data = pd.read_csv(shared_output)
        return au_data
    else:
        raise Exception(f"Erro no processamento: {result.stderr}")

# Exemplo de uso
# au_results = process_facial_expression("minha_imagem.jpg")
# print(au_results.head())
```

## Unidades de Ação (AUs) detectadas

O OpenFace detecta as seguintes Unidades de Ação principais:

- **AU01**: Inner Brow Raiser
- **AU02**: Outer Brow Raiser  
- **AU04**: Brow Lowerer
- **AU05**: Upper Lid Raiser
- **AU06**: Cheek Raiser
- **AU07**: Lid Tightener
- **AU09**: Nose Wrinkler
- **AU10**: Upper Lip Raiser
- **AU12**: Lip Corner Puller
- **AU14**: Dimpler
- **AU15**: Lip Corner Depressor
- **AU17**: Chin Raiser
- **AU20**: Lip Stretcher
- **AU23**: Lip Tightener
- **AU25**: Lips Part
- **AU26**: Jaw Drop
- **AU45**: Blink

## Estrutura do arquivo de saída

O arquivo `AU_output.csv` contém:
- **frame**: Número do frame (sempre 0 para imagens estáticas)
- **face_id**: ID da face detectada
- **timestamp**: Timestamp do processamento
- **confidence**: Confiança da detecção facial
- **success**: Se a detecção foi bem-sucedida
- **AU01_r, AU02_r, ...**: Intensidade de cada AU (valores regressivos)
- **AU01_c, AU02_c, ...**: Presença de cada AU (valores classificatórios 0/1)

## Troubleshooting

### Container não inicia
```bash
docker compose logs openface
```

### Imagem não processada
- Verifique se `shared_data/input.jpg` existe
- Confirme que a imagem está em formato JPG válido
- Verifique permissões do diretório `shared_data`

### Resultados incorretos
- Certifique-se que há uma face visível na imagem
- Imagens muito pequenas ou de baixa qualidade podem falhar
- Faces muito inclinadas ou parcialmente ocultas podem não ser detectadas

## Integração com o projeto empatIA

Este serviço está integrado ao projeto empatIA e pode ser chamado tanto pelo backend FastAPI quanto pelo frontend Streamlit para processamento de imagens enviadas pelos usuários. 