"""Rotas de clientes."""
import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import usuario_atual
from ..database import get_db

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def _to_out(cliente: models.Cliente) -> schemas.ClienteOut:
    out = schemas.ClienteOut.model_validate(cliente)
    out.total_orcamentos = len(cliente.orcamentos)
    return out


@router.get("", response_model=list[schemas.ClienteOut])
def listar(db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    clientes = db.query(models.Cliente).order_by(models.Cliente.razao_social).all()
    return [_to_out(c) for c in clientes]


@router.post("", response_model=schemas.ClienteOut, status_code=201)
def criar(
    dados: schemas.ClienteCreate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    cliente = models.Cliente(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.get("/{cliente_id}", response_model=schemas.ClienteOut)
def obter(cliente_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    return _to_out(cliente)


@router.put("/{cliente_id}", response_model=schemas.ClienteOut)
def atualizar(
    cliente_id: int,
    dados: schemas.ClienteUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.post("/{cliente_id}/logo", response_model=schemas.ClienteOut)
def upload_logo(
    cliente_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    """Salva a logo própria do cliente em /static."""
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".png"
    nome = f"cliente_{cliente_id}{ext}"
    with open(os.path.join(STATIC_DIR, nome), "wb") as f:
        shutil.copyfileobj(file.file, f)
    cliente.logo_path = nome
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.delete("/{cliente_id}/logo", response_model=schemas.ClienteOut)
def remover_logo(cliente_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    cliente.logo_path = None
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.delete("/{cliente_id}", status_code=204)
def excluir(cliente_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    cliente = db.get(models.Cliente, cliente_id)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    db.delete(cliente)
    db.commit()
