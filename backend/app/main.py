"""Aplicação FastAPI — Sistema de Orçamentos XINGU."""
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from .config import settings
from .database import Base, engine
from .routers import auth, catalogo, clientes, config, orcamentos


def _esperar_banco(tentativas: int = 30, intervalo: float = 2.0):
    """Aguarda o banco aceitar conexões (importante ao subir junto com o Postgres)."""
    for i in range(tentativas):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if i == tentativas - 1:
                raise
            time.sleep(intervalo)


_esperar_banco()

# Cria as tabelas no banco (idempotente).
Base.metadata.create_all(bind=engine)


def _migrar():
    """Migrações leves: adiciona colunas novas em tabelas já existentes."""
    inspetor = inspect(engine)
    cols_cli = {c["name"] for c in inspetor.get_columns("clientes")}
    if "logo_path" not in cols_cli:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE clientes ADD COLUMN logo_path VARCHAR"))
    cols_cfg = {c["name"] for c in inspetor.get_columns("config")}
    if "contato_logo_path" not in cols_cfg:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE config ADD COLUMN contato_logo_path VARCHAR DEFAULT 'contato.png'")
            )
    cols_orc = {c["name"] for c in inspetor.get_columns("orcamentos")}
    if "cliente_nome" not in cols_orc:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE orcamentos ADD COLUMN cliente_nome VARCHAR DEFAULT ''"))


_migrar()

app = FastAPI(title="Sistema de Orçamentos XINGU", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    # Em desenvolvimento, libera qualquer porta de localhost/127.0.0.1.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(config.router)
app.include_router(clientes.router)
app.include_router(catalogo.router)
app.include_router(orcamentos.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
