"""Rotas de configuração da empresa (dados fixos + upload de logo)."""
import os
import shutil

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import usuario_atual
from ..database import get_db

router = APIRouter(prefix="/api/config", tags=["config"])

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def get_config(db: Session) -> models.Config:
    """Retorna a configuração (linha única), criando-a com os padrões se necessário."""
    cfg = db.query(models.Config).first()
    if not cfg:
        cfg = models.Config(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("", response_model=schemas.ConfigOut)
def ler_config(db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    return get_config(db)


@router.put("", response_model=schemas.ConfigOut)
def atualizar_config(
    dados: schemas.ConfigUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    cfg = get_config(db)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cfg, campo, valor)
    db.commit()
    db.refresh(cfg)
    return cfg


def _salvar_imagem(file: UploadFile, base: str) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower() or ".png"
    nome = f"{base}{ext}"
    with open(os.path.join(STATIC_DIR, nome), "wb") as f:
        shutil.copyfileobj(file.file, f)
    return nome


@router.post("/logo", response_model=schemas.ConfigOut)
def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    """Salva a logo principal da XINGU em /static."""
    cfg = get_config(db)
    cfg.logo_path = _salvar_imagem(file, "logo")
    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/contato-logo", response_model=schemas.ConfigOut)
def upload_contato_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    """Salva a imagem de contato (@agenciaxingu) em /static."""
    cfg = get_config(db)
    cfg.contato_logo_path = _salvar_imagem(file, "contato")
    db.commit()
    db.refresh(cfg)
    return cfg
