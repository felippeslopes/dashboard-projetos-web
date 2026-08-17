# Decisões do Projeto — Dashboard de Projetos Web

Este documento registra as decisões de arquitetura e segurança tomadas
antes do início da implementação. Deve ser atualizado a cada nova
decisão relevante.

## Versão e escopo

- **v0.1 (atual):** login Google (Supabase Auth) + 1 planilha Google
  Sheets + 5 cards + tabela de tarefas (agrupadas por projeto) + gráfico
  de pizza por status
- **v0.2:** Excel Online / Microsoft Graph, demais gráficos, riscos,
  marcos, página de Configurações, sincronização automática
- **v1.0:** Docker Compose, testes completos, tratamento de erro com
  download de modelo, dark/light mode, README final

## Arquitetura

- Frontend nunca acessa Google Sheets ou Microsoft Graph diretamente —
  toda comunicação passa exclusivamente pelo backend (FastAPI)
- Planilha é a fonte de verdade dos dados de projeto — não há banco
  relacional para isso
- Supabase armazena apenas identidade e configuração do usuário
  (usuário → planilha conectada → preferências), nunca dados de projeto
- Repository Pattern + Service Layer: `repositories/` isola acesso a
  dados, `services/` concentra regra de negócio, `routes/` apenas orquestra
- Camada de abstração de provedores de dados, permitindo trocar/adicionar
  fontes (Excel Online, banco relacional) sem alterar o frontend

## Escrita na planilha (exceção ao read-only)

O sistema era estritamente leitura até a introdução do Kanban. Avaliamos e
**adiamos deliberadamente** edição livre de qualquer célula, histórico de
edições e múltiplos usuários na mesma planilha — todas exigiriam banco
relacional e/ou controle de concorrência que não valem o custo nesta fase
do produto. A única escrita implementada é estreita por design:

- **Escopo único:** só o campo `Status` de uma linha, só a partir da
  interação de arrastar um card entre colunas no Kanban — nenhum outro
  campo é editável pelo SaaS
- **`SCOPES`** em `sheets_provider.py` mudou de
  `spreadsheets.readonly` para `spreadsheets` (leitura+escrita). A
  service account passa a precisar de permissão de **Editor** na
  planilha do usuário, não mais só Leitor — instrução atualizada na tela
  "Conectar Planilha"
- **Conflito, não sobrescrita silenciosa:** antes de escrever,
  `update_status` lê o valor atual da célula e compara com o status que o
  frontend tinha no momento em que o usuário começou a arrastar o card
  (`status_esperado`). Se divergir — alguém mudou o dado nesse meio tempo,
  seja por outro usuário do SaaS ou editando a planilha diretamente — a
  escrita é recusada (HTTP 409) em vez de sobrescrever; o frontend desfaz
  o movimento otimista do card e avisa o usuário. É a estratégia
  "last-write-wins com aviso", não silenciosa

## Autenticação

- Login exclusivamente via OAuth (Google / Microsoft), sem senha própria
  no sistema — elimina risco de senha fraca, credential stuffing e
  reset de senha malicioso
- Row Level Security (RLS) ativo no Supabase desde o primeiro dia:
  cada usuário só lê/escreve a própria configuração
- Verificação do JWT do Supabase no backend via **JWKS** (JWT Signing
  Keys assimétricas, ES256) — sem segredo compartilhado no backend;
  `security.py` valida assinatura e extrai `user_id` (`sub`) a partir de
  `https://<projeto>.supabase.co/auth/v1/.well-known/jwks.json`
- RLS é o mecanismo de isolamento de fato, não só documentação: o
  backend usa a **anon key** + o **JWT do próprio usuário** (repassado
  via `postgrest.auth(token)`) para consultar `user_config` — não filtra
  por `user_id` manualmente com a service key. A `SUPABASE_SERVICE_KEY`
  fica reservada para tarefas administrativas (migrations), não é usada
  em requisições normais
- Acesso à planilha do usuário é feito por uma **service account** única
  do backend (`GOOGLE_SHEETS_CREDENTIALS_JSON`), não por OAuth por
  usuário — o usuário precisa compartilhar a planilha com o e-mail dessa
  service account para o backend conseguir lê-la (instrução exibida na
  tela "Conectar Planilha")

## Schema da planilha (v0.1)

Cada linha da planilha é uma **Tarefa** (não um projeto inteiro — um
projeto pode ter várias tarefas). Cabeçalho esperado na primeira linha
(nomes tolerantes a reordenação, acento e maiúsculas/minúsculas):

| Coluna | Tipo | Papel |
|---|---|---|
| `Projeto` | texto | A qual projeto a tarefa pertence — agrupamento, sem lista fixa |
| `Tarefa` | texto | Nome da tarefa — único campo obrigatório |
| `Status` | categórico | `Planejado / Em andamento / Concluído / Atrasado / Cancelado` — alimenta o gráfico de pizza |
| `Responsável` | texto | Informativo, aparece na tabela |
| `Prazo` | data | Base do cálculo do card "Tarefas Atrasadas" |

Os 5 cards do v0.1: Total de Tarefas, Tarefas em Andamento, Tarefas
Concluídas, Tarefas Atrasadas (**calculado** por `prazo < hoje` e status
não `Concluído`/`Cancelado` — não depende do usuário marcar "Atrasado"
manualmente) e Taxa de Conclusão (%). O gráfico de pizza usa o `Status`
bruto da planilha, com um bucket `"Outros"` para valores não reconhecidos
— é uma métrica deliberadamente diferente do card "Atrasadas".

Tolerância a erro linha a linha: linha em branco é ignorada
silenciosamente; falta de `Tarefa` ignora a linha com aviso; `Prazo`
vazio ou não parseável nunca derruba a linha (fica sem data, com aviso
se o texto não era vazio); falta de qualquer uma das 5 colunas no
cabeçalho é erro de configuração da planilha (422), não erro de linha.
Limite de 2000 linhas processadas por requisição, com aviso de
truncamento na resposta.

## Segurança — validação de entrada

| Vetor | Risco | Mitigação |
|---|---|---|
| Link da planilha | SSRF (backend usado como proxy de ataque) | Extrair apenas o ID via regex; nunca fazer fetch da URL crua; chamar somente a API oficial (Google Sheets API / Microsoft Graph) com esse ID |
| Conteúdo da planilha | Formula Injection (células iniciando com `=`, `+`, `-`, `@`) | Leitura via Google Sheets API com `valueRenderOption="FORMATTED_VALUE"` — o backend sempre recebe o valor já calculado pelo Google, nunca a fórmula bruta, e nunca faz `eval`/interpretação do conteúdo |
| Conteúdo da planilha | XSS via nome de projeto/campo livre | Nunca usar `dangerouslySetInnerHTML` com dado vindo da planilha; renderização padrão do React (que já escapa texto) |
| Planilha muito grande | DoS por volume de linhas | Limite de linhas processadas + paginação, com mensagem amigável se exceder |
| Cadastro/conexão | Automação abusiva (criação em massa) | Rate limiting nos endpoints de cadastro e conexão de planilha |
| Link do SaaS | Open redirect / phishing | CORS restrito ao domínio do frontend; validação de qualquer redirect contra lista fixa de URLs permitidas |
| Transporte | Interceptação de dados | HTTPS obrigatório em produção; headers de segurança (CSP, X-Content-Type-Options) |

Dependências de frontend têm `npm audit` verificado a cada instalação. Uma
vulnerabilidade conhecida foi aceita conscientemente: `react-router@7.18.2`
(mais recente disponível) tem um CVE de "RSC Mode CSRF Bypass"
(7.12.0–8.2.0) que não se aplica ao nosso uso — SPA puro via Vite, sem
Server Components/data router/actions. Reavaliar quando uma versão
corrigida for publicada.

## Segredos e variáveis de ambiente

- Backend: `GOOGLE_SHEETS_CREDENTIALS_JSON`, `SUPABASE_URL`,
  `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `FRONTEND_ORIGIN` —
  nunca versionados, sempre via `.env`
- Frontend: apenas `SUPABASE_ANON_KEY` (pública por design, protegida
  por RLS) — nenhum secret sensível no cliente

## LGPD

- Minimização de dados: nenhum dado de projeto é replicado/persistido
  fora da planilha do próprio usuário
- Dados pessoais armazenados no Supabase limitados ao necessário para
  autenticação e configuração da conta
