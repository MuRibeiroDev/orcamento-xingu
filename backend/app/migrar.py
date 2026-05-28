"""Migra os dados de um banco SQLite para o banco configurado em DATABASE_URL (PostgreSQL).

Uso (dentro do container backend), com o arquivo SQLite montado em /seed/orcamentos.db:
    python -m app.migrar --from sqlite:////seed/orcamentos.db

Copia todas as tabelas preservando os IDs e ajusta as sequências do PostgreSQL no final.
"""
import argparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from . import models
from .config import settings
from .database import Base

# Ordem que respeita as chaves estrangeiras.
ORDEM = [
    models.Config,
    models.Cliente,
    models.CatalogoItem,
    models.Orcamento,
    models.OrcamentoItem,
]


def migrar(origem_url: str, destino_url: str):
    origem = create_engine(
        origem_url,
        connect_args={"check_same_thread": False} if origem_url.startswith("sqlite") else {},
    )
    destino = create_engine(destino_url)
    Base.metadata.create_all(destino)

    SessaoOrigem = sessionmaker(bind=origem)
    SessaoDestino = sessionmaker(bind=destino)
    so, de = SessaoOrigem(), SessaoDestino()
    try:
        for Model in ORDEM:
            registros = so.query(Model).all()
            for r in registros:
                dados = {c.name: getattr(r, c.name) for c in Model.__table__.columns}
                de.merge(Model(**dados))
            de.commit()
            print(f"{Model.__tablename__}: {len(registros)} registros migrados")

        # Ajusta as sequências (inserimos os IDs manualmente).
        if destino_url.startswith("postgres"):
            for Model in ORDEM:
                tbl = Model.__tablename__
                de.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {tbl}), 1), true)"
                    )
                )
            de.commit()
        print("Migração concluída com sucesso.")
    finally:
        so.close()
        de.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Migra dados SQLite -> PostgreSQL")
    p.add_argument("--from", dest="origem", default="sqlite:////seed/orcamentos.db")
    p.add_argument("--to", dest="destino", default=settings.database_url)
    args = p.parse_args()
    migrar(args.origem, args.destino)
