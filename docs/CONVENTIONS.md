# Convenções e Padrões — Empat.IA

> Como o código é organizado, quais padrões seguir, e como adicionar novas funcionalidades sem quebrar o que já existe.

---

## Índice

1. [Padrões Python (FastAPI)](#1-padrões-python-fastapi)
2. [Padrões React (Frontend)](#2-padrões-react-frontend)
3. [Como adicionar um endpoint no Gateway](#3-como-adicionar-um-endpoint-no-gateway)
4. [Como adicionar um novo serviço de domínio](#4-como-adicionar-um-novo-serviço-de-domínio)
5. [Como adicionar uma nova página no Admin Panel](#5-como-adicionar-uma-nova-página-no-admin-panel)
6. [Como adicionar um novo componente no Web UI](#6-como-adicionar-um-novo-componente-no-web-ui)
7. [Padrões de banco de dados (MongoDB + Motor)](#7-padrões-de-banco-de-dados-mongodb--motor)
8. [Tratamento de erros](#8-tratamento-de-erros)
9. [Logging](#9-logging)
10. [Git e commits](#10-git-e-commits)

---

## 1. Padrões Python (FastAPI)

### Formatação
- **PEP 8** + **Black** para formatação automática
- Type hints em todas as funções de serviço
- Docstrings em funções públicas (uma linha é suficiente)

### Modelos Pydantic para requests

Definir modelos Pydantic no topo do `main.py` ou em `models/` para requests:

```python
class MinhaRequest(BaseModel):
    campo_obrigatorio: str
    campo_opcional: Optional[str] = None
    campo_com_default: bool = False
```

Nunca usar `request: Request` + `await request.json()` para dados tipados — usar Pydantic.  
Usar `request: Request` + `await request.json()` apenas quando o schema é genuinamente dinâmico.

### Estrutura de um endpoint

```python
@app.post("/api/meu-endpoint")
async def meu_endpoint(request: MinhaRequest):
    """Descrição em uma linha do que faz."""
    try:
        resultado = await meu_service.fazer_algo(request.campo)
        
        if not resultado:
            raise HTTPException(status_code=404, detail="Recurso não encontrado")
        
        return {
            "success": True,
            "data": resultado
        }
        
    except HTTPException:
        raise  # Re-raise HTTPException sem logar como erro
    except Exception as e:
        logger.error(f"Erro ao processar meu endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
```

**Padrão de resposta:**
- Sucesso: `{ "success": True, "data": ... }`
- Erro HTTP semântico: `HTTPException` com código e `detail`
- Erros inesperados: 500 com mensagem genérica

### Imports no gateway

Novos routers devem ser adicionados em `src/api/` e incluídos em `main.py`:

```python
from .api.meu_router import router as meu_router
app.include_router(meu_router)
```

Novos services devem ser instanciados junto com os demais no topo de `main.py`.

---

## 2. Padrões React (Frontend)

### Linguagem e extensões
- Novos componentes podem usar `.jsx` ou `.tsx` (TypeScript parcial)
- Preferir `.tsx` para componentes com props complexas — type safety ajuda
- `App.jsx` e utilitários usam `.jsx` / `.js`

### Estrutura de componente

```jsx
import React, { useState, useEffect } from 'react';
import { algumServico } from '../../services/api.js';

// Props tipadas quando TypeScript
interface Props {
  username: string;
  onLogout: () => void;
}

export default function MeuComponente({ username, onLogout }: Props) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      const resp = await algumServico(username);
      setDados(resp.data);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
    } finally {
      setCarregando(false);
    }
  };

  if (carregando) return <div>Carregando...</div>;

  return (
    <div className="...">
      {/* conteúdo */}
    </div>
  );
}
```

### Estilização
- **Tailwind CSS** — classes utilitárias inline são o padrão
- **MUI** (`@mui/material`) para componentes complexos: Dialog, Drawer, TextField, etc.
- **Framer Motion** (web-ui) para animações de entrada/saída
- Evitar CSS Modules ou styled-components — manter consistência com Tailwind

### Estado
- Estado local com `useState` e `useReducer`
- Sem Redux — o projeto não usa gerenciamento de estado global complexo
- `AuthContext` no admin-panel é o único Context API em uso
- Dados de sessão persistidos em `localStorage` (ver [`FRONTEND.md#5-localstorage`](FRONTEND.md#5-localstorage--chaves-utilizadas))

### Chamadas de API
- Todas as chamadas passam pelos services em `src/services/api.js`
- Nunca chamar `fetch` ou `axios` diretamente nos componentes
- Adicionar nova função no `api.js` para cada endpoint novo

---

## 3. Como adicionar um endpoint no Gateway

### Passo a passo

**1. Definir o modelo Pydantic** (se necessário) no topo de `main.py`:

```python
class MinhaNovaRequest(BaseModel):
    session_id: str
    dados: Optional[Dict[str, Any]] = None
```

**2. Adicionar o endpoint** em `main.py` (para rotas inline) ou em um arquivo de router em `src/api/`:

```python
@app.post("/api/minha-feature/{param}")
async def minha_nova_rota(param: str, request: MinhaNovaRequest):
    """Descrição da nova rota."""
    try:
        resultado = await meu_service.processar(param, request.dados)
        return {"success": True, "data": resultado}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em minha_nova_rota: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**3. Adicionar função correspondente no `api.js` do frontend:**

```js
export const minhaNovaFuncao = async (param, dados) => {
  const response = await api.post(`/api/minha-feature/${param}`, { dados });
  return response.data;
};
```

**4. Atualizar `TECHNICAL.md`** com o novo endpoint na seção de API Reference.

---

## 4. Como adicionar um novo serviço de domínio

Um "service de domínio" é uma classe Python em `services/gateway-service/src/services/`.

**1. Criar o arquivo** `src/services/meu_servico.py`:

```python
from ..models.database import get_collection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MeuServico:
    
    async def criar(self, dados: dict) -> dict:
        """Cria um novo recurso."""
        colecao = get_collection("minha_colecao")
        
        documento = {
            **dados,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        resultado = await colecao.insert_one(documento)
        documento["_id"] = str(resultado.inserted_id)
        return documento
    
    async def buscar(self, id: str) -> dict | None:
        """Busca recurso por ID."""
        colecao = get_collection("minha_colecao")
        return await colecao.find_one({"_id": id})
```

**2. Instanciar em `main.py`:**

```python
from .services.meu_servico import MeuServico
meu_servico = MeuServico()
```

**3. Usar nos endpoints:**

```python
@app.post("/api/meu-recurso")
async def criar_recurso(dados: dict):
    return await meu_servico.criar(dados)
```

---

## 5. Como adicionar uma nova página no Admin Panel

**1. Criar o arquivo** `apps/admin-panel/src/pages/MinhaPagina.js`:

```jsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function MinhaPagina() {
  const [dados, setDados] = useState([]);

  useEffect(() => {
    api.get('/api/admin/meu-recurso').then(r => setDados(r.data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Título da Página</h1>
      {/* conteúdo */}
    </div>
  );
}
```

**2. Adicionar a rota em `App.js`:**

```jsx
import MinhaPagina from './pages/MinhaPagina';

// Dentro do componente de rotas:
<Route path="/minha-pagina" element={<MinhaPagina />} />
```

**3. Adicionar link no menu lateral** (componente de navegação do admin).

---

## 6. Como adicionar um novo componente no Web UI

**1. Criar o arquivo** em `apps/web-ui/src/components/`:

Organizar em subpastas por área: `Chat/`, `Home/`, etc.

```tsx
// apps/web-ui/src/components/MeuComponente.tsx
interface Props {
  titulo: string;
  aoClicar: () => void;
}

export default function MeuComponente({ titulo, aoClicar }: Props) {
  return (
    <button
      onClick={aoClicar}
      className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
    >
      {titulo}
    </button>
  );
}
```

**2. Importar onde necessário:**

```jsx
import MeuComponente from '../MeuComponente';
```

---

## 7. Padrões de banco de dados (MongoDB + Motor)

### Acessar coleções

```python
from .models.database import get_collection

colecao = get_collection("nome_da_colecao")
```

### Queries básicas

```python
# Buscar um documento
doc = await colecao.find_one({"campo": valor})

# Buscar vários
cursor = colecao.find({"campo": valor}).sort("created_at", -1).limit(50)
docs = [doc async for doc in cursor]

# Inserir
resultado = await colecao.insert_one({"campo": "valor", "created_at": datetime.utcnow()})

# Atualizar
await colecao.update_one(
    {"_id": id},
    {"$set": {"campo": novo_valor, "updated_at": datetime.utcnow()}}
)

# Deletar (preferir soft delete com is_active=False)
await colecao.update_one({"_id": id}, {"$set": {"is_active": False}})
```

### Regras críticas de segurança

**Sempre incluir `username` no filtro de queries em `messages` e `conversations`:**

```python
# CERTO — isolamento por usuário
doc = await colecao.find_one({
    "session_id": session_id,
    "username": username  # OBRIGATÓRIO
})

# ERRADO — pode retornar dados de outro usuário
doc = await colecao.find_one({"session_id": session_id})
```

Veja também a seção de sessões terapêuticas em [`TECHNICAL.md`](TECHNICAL.md) para o formato atual de `chat_id`, `session_id` e isolamento por usuário.

### Serialização de ObjectId

MongoDB retorna `ObjectId` que não é serializável em JSON. Converter para string:

```python
documento["_id"] = str(documento["_id"])
```

Ou usar uma função helper:

```python
def serialize_doc(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc
```

### Timestamps

Sempre usar `datetime.utcnow()` para timestamps (não `datetime.now()`):

```python
from datetime import datetime

documento = {
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}
```

---

## 8. Tratamento de erros

### Backend (Python)

```python
try:
    resultado = await service.operacao()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Não encontrado")
    
    return {"success": True, "data": resultado}
    
except HTTPException:
    raise  # Re-raise sem logar — HTTPException é esperado
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Erro inesperado em [nome_da_função]: {e}")
    raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

**Nunca expor detalhes de exceções internas em produção** — usar mensagem genérica no `detail` quando for 500.

### Frontend (React)

```js
const carregarDados = async () => {
  try {
    setCarregando(true);
    const resp = await algumServico();
    setDados(resp.data);
  } catch (err) {
    console.error('Erro ao carregar:', err);
    // Mostrar feedback visual ao usuário (toast, mensagem de erro)
    setErro('Não foi possível carregar os dados. Tente novamente.');
  } finally {
    setCarregando(false);
  }
};
```

---

## 9. Logging

### Backend

```python
import logging
logger = logging.getLogger(__name__)

# Prefixos de emoji por severidade (padrão do projeto):
logger.info("✅ Operação concluída com sucesso")
logger.warning("⚠️ Situação inesperada mas não crítica")
logger.error("❌ Erro que precisa de atenção")

# Incluir contexto relevante:
logger.info(f"🌐 Processando mensagem: session_id={session_id}, username={username}")
```

**Nível de log:** controlado por `LOG_LEVEL` no `.env` (padrão `INFO`).

### Frontend

```js
console.error('Erro ao processar:', err);  // para erros
// console.log em desenvolvimento apenas — remover antes de PR
```

---

## 10. Git e commits

### Conventional Commits

```
feat: adiciona endpoint de análise de sentimento
fix: corrige rewrite de audio_url no proxy do voice service
docs: atualiza API reference com novos endpoints de emoção
refactor: extrai lógica de session_id para helper separado
chore: atualiza dependências do gateway service
test: adiciona testes para UserTherapeuticSessionService
```

### Branches

```
feature/nome-da-feature
fix/descricao-do-bug
docs/o-que-esta-documentando
refactor/o-que-esta-refatorando
```

### Pull Requests

- PRs para `main` acionam o pipeline de CI/CD completo
- Build das imagens + deploy automático no GKE Autopilot
- Verificar `GET /health/all` em produção após deploy

---

*Última atualização: Abril 2026*
