"""Rotas de castings (apresentação em PDF com as modelos selecionadas)."""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import usuario_atual
from ..casting_pdf import Pessoa, gerar_casting_pdf
from ..database import get_db

router = APIRouter(prefix="/api/castings", tags=["castings"])


def _obter(db: Session, casting_id: int) -> models.Casting:
    casting = db.get(models.Casting, casting_id)
    if not casting:
        raise HTTPException(404, "Casting não encontrado")
    return casting


def serializar(casting: models.Casting) -> schemas.CastingOut:
    out = schemas.CastingOut.model_validate(casting)
    out.modelos = [schemas.ModeloOut.model_validate(i.modelo) for i in casting.itens]
    return out


def _aplicar(db: Session, casting: models.Casting, dados: schemas.CastingSalvar):
    """Grava título, marca e a lista ordenada de modelos (ignora IDs repetidos)."""
    ids = list(dict.fromkeys(dados.modelo_ids))
    existentes = {m.id for m in db.query(models.Modelo.id).filter(models.Modelo.id.in_(ids))}
    faltando = [i for i in ids if i not in existentes]
    if faltando:
        raise HTTPException(400, f"Modelos não encontradas: {faltando}")
    casting.titulo = dados.titulo
    casting.marca = dados.marca
    casting.itens = [models.CastingModelo(modelo_id=mid, ordem=n) for n, mid in enumerate(ids)]


@router.get("", response_model=list[schemas.CastingListOut])
def listar(db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    castings = db.query(models.Casting).order_by(models.Casting.updated_at.desc()).all()
    return [
        schemas.CastingListOut(
            id=c.id, titulo=c.titulo, marca=c.marca,
            total_modelos=len(c.itens), updated_at=c.updated_at,
        )
        for c in castings
    ]


@router.post("", response_model=schemas.CastingOut, status_code=201)
def criar(
    dados: schemas.CastingSalvar,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    casting = models.Casting()
    _aplicar(db, casting, dados)
    db.add(casting)
    db.commit()
    db.refresh(casting)
    return serializar(casting)


@router.get("/{casting_id}", response_model=schemas.CastingOut)
def obter(casting_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    return serializar(_obter(db, casting_id))


@router.put("/{casting_id}", response_model=schemas.CastingOut)
def atualizar(
    casting_id: int,
    dados: schemas.CastingSalvar,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    casting = _obter(db, casting_id)
    _aplicar(db, casting, dados)
    db.commit()
    db.refresh(casting)
    return serializar(casting)


@router.delete("/{casting_id}", status_code=204)
def excluir(casting_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    db.delete(_obter(db, casting_id))
    db.commit()


@router.get("/{casting_id}/pdf")
def pdf(casting_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    casting = _obter(db, casting_id)
    pessoas = [
        Pessoa(
            nome=i.modelo.nome,
            idade=i.modelo.idade or "",
            manequim=i.modelo.manequim or "",
            altura=i.modelo.altura or "",
            destaque=i.modelo.destaque or "",
            fotos=tuple(f.arquivo for f in i.modelo.fotos),
        )
        for i in casting.itens
    ]
    buffer = gerar_casting_pdf(casting.titulo, casting.marca, pessoas, ano=casting.created_at.year)
    # Nome de arquivo ASCII-safe para o header HTTP (ex.: "SIC - CRESOL" -> Casting_SIC-CRESOL.pdf).
    base = unicodedata.normalize("NFKD", casting.titulo).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-") or "casting"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="Casting_{base}.pdf"'},
    )
