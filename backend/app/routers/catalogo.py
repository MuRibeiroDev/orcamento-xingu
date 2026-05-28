"""Rotas do catálogo de itens/serviços reutilizáveis."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import usuario_atual
from ..database import get_db

router = APIRouter(prefix="/api/catalogo", tags=["catalogo"])


@router.get("", response_model=list[schemas.CatalogoOut])
def listar(db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    return db.query(models.CatalogoItem).order_by(models.CatalogoItem.nome).all()


@router.post("", response_model=schemas.CatalogoOut, status_code=201)
def criar(
    dados: schemas.CatalogoCreate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    item = models.CatalogoItem(**dados.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.CatalogoOut)
def atualizar(
    item_id: int,
    dados: schemas.CatalogoUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    item = db.get(models.CatalogoItem, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def excluir(item_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    item = db.get(models.CatalogoItem, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    db.delete(item)
    db.commit()
