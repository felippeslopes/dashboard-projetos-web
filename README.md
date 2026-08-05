# Dashboard de Projetos Web

SaaS multiusuário para analistas e gerentes de projetos. Cada usuário
conecta sua própria planilha do Google Sheets (fonte de verdade dos
dados) e o sistema calcula indicadores, tabela de tarefas e gráfico de
status — sem banco relacional para os dados de projeto.

> **Status:** v0.1. Decisões de arquitetura e segurança completas em
> [docs/decisoes.md](docs/decisoes.md) — leia antes de mexer no código.

## Stack

- **Backend:** FastAPI (Python 3.11+), Pydantic, Google Sheets API, Supabase (auth + config)
- **Frontend:** React 18 + TypeScript (strict) + Vite, React Router, Recharts, Supabase Auth JS
- **Auth:** Google OAuth via Supabase (JWT verificado por JWKS no backend)

## Pré-requisitos

- Python 3.11+ e Node.js 18+
- Um projeto no [Supabase](https://supabase.com) com login Google (provider OAuth) ativado
- Um projeto no Google Cloud com:
  - uma **service account** com acesso à Google Sheets API (gera o `GOOGLE_SHEETS_CREDENTIALS_JSON`)
  - um **OAuth Client ID** (tipo Web) configurado no provider Google do Supabase

## Configuração

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows (Git Bash): .venv/Scripts/activate | Linux/Mac: .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha o `.env`:

| Variável | Onde conseguir |
|---|---|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | JSON da service account (Google Cloud → IAM → Contas de serviço → Chaves) |
| `SUPABASE_URL` | Painel Supabase → Project Settings → API |
| `SUPABASE_ANON_KEY` | Painel Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Painel Supabase → Project Settings → API (nunca expor ao frontend) |
| `FRONTEND_ORIGIN` | URL do frontend (`http://localhost:5173` em dev) |

Rodar:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Preencha o `.env`:

| Variável | Onde conseguir |
|---|---|
| `VITE_SUPABASE_URL` | Mesma URL do backend |
| `VITE_SUPABASE_ANON_KEY` | Mesma anon key do backend (pública por design) |
| `VITE_API_BASE_URL` | URL do backend (`http://localhost:8000` em dev) |

Rodar:

```bash
npm run dev
```

### Estrutura da planilha do Google Sheets

Cada usuário conecta uma planilha com uma linha por **tarefa** (uma
tarefa pertence a um projeto). Cabeçalho esperado na primeira linha —
tolerante a reordenação, acento e maiúsculas/minúsculas:

| Coluna | Tipo | Observação |
|---|---|---|
| `Projeto` | texto | A qual projeto a tarefa pertence |
| `Tarefa` | texto | Nome da tarefa (único campo obrigatório) |
| `Status` | categórico | `Planejado / Em andamento / Concluído / Atrasado / Cancelado` |
| `Responsável` | texto | |
| `Prazo` | data (`dd/mm/aaaa`) | Usado para calcular o card "Atrasadas" |

A planilha precisa ser compartilhada com o e-mail da service account
(exibido na tela "Conectar Planilha" do sistema).

## Testes

```bash
cd backend
python -m pytest
```

## Roadmap

- **v0.1 (atual):** login Google, 1 planilha por usuário, 5 cards, tabela de tarefas, gráfico de pizza por status
- **v0.2:** Excel Online / Microsoft Graph, demais gráficos, riscos, marcos, página de Configurações, sincronização automática
- **v1.0:** Docker Compose, testes completos, tratamento de erro com download de modelo, dark/light mode

Detalhes completos de cada decisão de arquitetura e segurança em
[docs/decisoes.md](docs/decisoes.md).
