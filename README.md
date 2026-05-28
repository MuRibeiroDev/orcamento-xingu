# Sistema de Orçamentos — XINGU Produções e Eventos

Sistema web para substituir a planilha de orçamentos: cadastro de clientes, catálogo de
itens reutilizáveis, montagem de orçamentos com cálculo automático de encargos e geração
de PDF fiel ao modelo da XINGU (com logo).

## Funcionalidades

- **Login** de usuário único (JWT).
- **Clientes**: cadastro completo e histórico de orçamentos por cliente.
- **Catálogo**: itens/serviços reutilizáveis com valor padrão, editáveis.
- **Orçamentos**: cabeçalho do cliente/evento, itens (do catálogo ou avulsos), cálculo em
  tempo real, **encargos flexíveis por orçamento e por linha**, numeração automática
  (`ORÇ-AAAA-NNN`), status (rascunho/enviado/aprovado), validade da proposta, duplicação.
- **PDF**: layout idêntico ao modelo, com logo, contato, tabela "Previsão de Investimento",
  condições e assinatura. Cada cliente pode ter sua **própria logo**, e ao gerar o PDF há a
  opção de incluir **as duas logos** (XINGU + cliente) no cabeçalho.
- **Configurações**: dados fixos da empresa e upload de logo.

### Regra de cálculo

```
TOTAL       = quantidade × diárias × valor_unitário
ENCARGOS    = TOTAL × (percentual / 100)        (padrão 15%, ajustável)
TOTAL FINAL = TOTAL + ENCARGOS
PREVISÃO DE INVESTIMENTO = soma dos TOTAL FINAL de todas as linhas
```

## Tecnologias

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + componentes shadcn/ui + fonte Outfit (servido por nginx no Docker).
- **Backend**: Python + FastAPI + SQLAlchemy.
- **Banco**: PostgreSQL (no Docker). Em dev sem Docker, usa SQLite por padrão.
- **PDF**: xhtml2pdf (Python puro).

---

## Como rodar com Docker (recomendado)

Sobe os 3 serviços: **frontend** (nginx), **backend** (FastAPI) e **banco** (PostgreSQL).

```bash
docker compose up -d --build
```

- Sistema: **http://localhost**  (porta 80)
- API: **http://localhost:8000**  (docs em `/docs`)
- Login: usuário `glaucia` / senha definida em `docker-compose.yml` (`ADMIN_PASSWORD`).

Os dados ficam no volume `db_data` (PostgreSQL) e as logos enviadas no volume `static_data` —
**não se perdem** ao reiniciar (`docker compose down` mantém os volumes; só `down -v` apaga).

Comandos úteis:
```bash
docker compose logs -f backend     # ver logs
docker compose down                # parar (mantém os dados)
docker compose down -v             # parar e APAGAR os dados
```

### Migrar dados de um SQLite existente para o PostgreSQL

Para trazer os dados de um banco SQLite (`backend/orcamentos.db`) para o PostgreSQL do Docker,
com a stack no ar:

```bash
docker compose run --rm \
  -v "$(pwd)/backend/orcamentos.db:/seed/orcamentos.db:ro" \
  backend python -m app.migrar
```

Copia todas as tabelas preservando os IDs e ajustando as sequências do PostgreSQL.

> ⚠️ Antes de publicar, troque `ADMIN_PASSWORD`, `SECRET_KEY` e a senha do PostgreSQL no
> `docker-compose.yml`.

---

## Como rodar localmente (sem Docker)

### Pré-requisitos
- Python 3.9+
- Node.js 18+
- macOS: o `xhtml2pdf` precisa da lib `cairo`. Instale com Homebrew:
  ```bash
  brew install pkg-config cairo
  ```

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ajuste a senha e a SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

A API sobe em `http://localhost:8000` (documentação interativa em `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev
```

Abra o endereço mostrado pelo Vite (ex.: `http://localhost:5173`).

### Login padrão
- Usuário: `glaucia`
- Senha: a definida em `backend/.env` (`ADMIN_PASSWORD`).

---

## Variáveis de ambiente (backend/.env)

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | Conexão do banco | `sqlite:///./orcamentos.db` |
| `ADMIN_USER` | Usuário do sistema | `glaucia` |
| `ADMIN_PASSWORD` | Senha do sistema | — (troque!) |
| `SECRET_KEY` | Chave para assinar os tokens JWT | — (troque!) |
| `CORS_ORIGINS` | Origens do frontend permitidas | `http://localhost:5173,...` |

---

## Deploy em produção (Supabase + nuvem)

1. Crie um projeto no [Supabase](https://supabase.com) e copie a *connection string* do Postgres.
2. Instale o driver do Postgres no backend:
   ```bash
   pip install -r requirements-postgres.txt
   ```
3. No `.env` de produção, defina:
   ```
   DATABASE_URL=postgresql+psycopg://postgres:SENHA@HOST:5432/postgres
   SECRET_KEY=<chave-aleatoria-forte>
   ADMIN_PASSWORD=<senha-forte>
   CORS_ORIGINS=https://seu-frontend.com
   ```
4. As tabelas são criadas automaticamente na primeira execução.
5. **Backend**: publique em Render, Railway, Fly.io ou similar (`uvicorn app.main:app`).
   Em Linux o `xhtml2pdf` requer as libs do sistema:
   `apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0`.
6. **Frontend**: `npm run build` gera a pasta `dist/`; publique em Vercel, Netlify ou
   no mesmo servidor. Defina `VITE_API_URL` apontando para a URL pública da API.

---

## Estrutura

```
docker-compose.yml   # orquestra db (PostgreSQL) + backend + frontend
backend/
  Dockerfile
  requirements.txt / requirements-postgres.txt
  app/
    main.py          # app FastAPI + CORS + estáticos + espera do banco
    config.py        # variáveis de ambiente
    database.py      # SQLAlchemy
    models.py        # Cliente(=Agência), Orcamento, OrcamentoItem, CatalogoItem, Config
    schemas.py       # Pydantic
    calc.py          # regras de cálculo (fonte única)
    auth.py          # login JWT
    pdf.py           # geração do PDF
    migrar.py        # migração SQLite -> PostgreSQL
    routers/         # auth, config, clientes, catalogo, orcamentos
    static/          # logos (logo.png, contato.png, cliente_*.png)
frontend/
  Dockerfile         # build (node) + nginx
  nginx.conf         # serve a SPA e faz proxy de /api e /static -> backend
  public/assets/     # logos do sistema (logo-xingu, logo-boom, contato)
  src/
    pages/           # Login, Dashboard, Clientes, ClienteDetalhe, Catalogo, OrcamentoEditor, Configuracoes
    components/ui/   # componentes shadcn-style (inclui currency-input e number-input)
    lib/             # api, format, utils
```
