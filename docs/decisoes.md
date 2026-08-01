# Decisões do Projeto — Dashboard de Projetos Web

Este documento registra as decisões de arquitetura e segurança tomadas
antes do início da implementação. Deve ser atualizado a cada nova
decisão relevante.

## Versão e escopo

- **v0.1 (atual):** login Google (Supabase Auth) + 1 planilha Google
  Sheets + 5 cards + tabela de projetos + gráfico de pizza por status
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

## Segurança — validação de entrada

| Vetor | Risco | Mitigação |
|---|---|---|
| Link da planilha | SSRF (backend usado como proxy de ataque) | Extrair apenas o ID via regex; nunca fazer fetch da URL crua; chamar somente a API oficial (Google Sheets API / Microsoft Graph) com esse ID |
| Conteúdo da planilha | Formula Injection (células iniciando com `=`, `+`, `-`, `@`) | Tratar todo conteúdo de célula como texto puro; escapar/prefixar essas células em qualquer export gerado |
| Conteúdo da planilha | XSS via nome de projeto/campo livre | Nunca usar `dangerouslySetInnerHTML` com dado vindo da planilha; renderização padrão do React (que já escapa texto) |
| Planilha muito grande | DoS por volume de linhas | Limite de linhas processadas + paginação, com mensagem amigável se exceder |
| Cadastro/conexão | Automação abusiva (criação em massa) | Rate limiting nos endpoints de cadastro e conexão de planilha |
| Link do SaaS | Open redirect / phishing | CORS restrito ao domínio do frontend; validação de qualquer redirect contra lista fixa de URLs permitidas |
| Transporte | Interceptação de dados | HTTPS obrigatório em produção; headers de segurança (CSP, X-Content-Type-Options) |

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
