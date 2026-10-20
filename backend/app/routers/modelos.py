"""Rotas do banco de modelos (pessoas do casting) e suas fotos."""
import os
import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import usuario_atual
from ..database import get_db

router = APIRouter(prefix="/api/modelos", tags=["modelos"])

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
FOTOS_SUBDIR = "modelos"
MAX_FOTOS = 4                   # o card do casting mostra até 4 fotos (grade 2x2)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_LADO_PX = 2000              # fotos são reduzidas para no máximo 2000px no maior lado

Image.MAX_IMAGE_PIXELS = 60_000_000  # protege contra "bombas" de descompressão


def _obter(db: Session, modelo_id: int) -> models.Modelo:
    modelo = db.get(models.Modelo, modelo_id)
    if not modelo:
        raise HTTPException(404, "Modelo não encontrada")
    return modelo


def _caminho(arquivo: str) -> str:
    return os.path.join(STATIC_DIR, arquivo)


def _apagar_arquivo(arquivo: str):
    try:
        os.remove(_caminho(arquivo))
    except FileNotFoundError:
        pass


def _salvar_foto(conteudo: bytes) -> str:
    """Valida a imagem, corrige a rotação (EXIF) e salva como JPEG com nome aleatório."""
    try:
        with Image.open(BytesIO(conteudo)) as im:
            im = ImageOps.exif_transpose(im)
            im = im.convert("RGB")
            im.thumbnail((MAX_LADO_PX, MAX_LADO_PX))
            os.makedirs(_caminho(FOTOS_SUBDIR), exist_ok=True)
            arquivo = f"{FOTOS_SUBDIR}/{uuid.uuid4().hex}.jpg"
            im.save(_caminho(arquivo), "JPEG", quality=88)
            return arquivo
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise HTTPException(400, "Arquivo inválido: envie uma imagem (JPG, PNG, WEBP...)")


@router.get("", response_model=list[schemas.ModeloOut])
def listar(db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    return db.query(models.Modelo).order_by(models.Modelo.nome).all()


@router.post("", response_model=schemas.ModeloOut, status_code=201)
def criar(
    dados: schemas.ModeloCreate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    modelo = models.Modelo(**dados.model_dump())
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


@router.put("/{modelo_id}", response_model=schemas.ModeloOut)
def atualizar(
    modelo_id: int,
    dados: schemas.ModeloUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    modelo = _obter(db, modelo_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(modelo, campo, valor)
    db.commit()
    db.refresh(modelo)
    return modelo


@router.delete("/{modelo_id}", status_code=204)
def excluir(modelo_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    modelo = _obter(db, modelo_id)
    arquivos = [f.arquivo for f in modelo.fotos]
    # Remove a modelo dos castings em que ela aparece.
    db.query(models.CastingModelo).filter(models.CastingModelo.modelo_id == modelo_id).delete()
    db.delete(modelo)
    db.commit()
    for arquivo in arquivos:
        _apagar_arquivo(arquivo)


@router.post("/{modelo_id}/fotos", response_model=schemas.ModeloOut)
def enviar_foto(
    modelo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    modelo = _obter(db, modelo_id)
    if len(modelo.fotos) >= MAX_FOTOS:
        raise HTTPException(400, f"Cada modelo pode ter no máximo {MAX_FOTOS} fotos")
    conteudo = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(conteudo) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Imagem muito grande (máximo 15 MB)")
    arquivo = _salvar_foto(conteudo)
    proxima = max((f.ordem for f in modelo.fotos), default=-1) + 1
    modelo.fotos.append(models.ModeloFoto(arquivo=arquivo, ordem=proxima))
    db.commit()
    db.refresh(modelo)
    return modelo


@router.put("/{modelo_id}/fotos/ordem", response_model=schemas.ModeloOut)
def ordenar_fotos(
    modelo_id: int,
    foto_ids: list[int],
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    """Define a ordem das fotos no card (1ª = superior esquerda, 2ª = superior direita...)."""
    modelo = _obter(db, modelo_id)
    por_id = {f.id: f for f in modelo.fotos}
    if sorted(foto_ids) != sorted(por_id):
        raise HTTPException(400, "Lista de fotos não confere com as fotos da modelo")
    for ordem, foto_id in enumerate(foto_ids):
        por_id[foto_id].ordem = ordem
    db.commit()
    db.refresh(modelo)
    return modelo


@router.delete("/{modelo_id}/fotos/{foto_id}", response_model=schemas.ModeloOut)
def remover_foto(
    modelo_id: int,
    foto_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    modelo = _obter(db, modelo_id)
    foto = next((f for f in modelo.fotos if f.id == foto_id), None)
    if not foto:
        raise HTTPException(404, "Foto não encontrada")
    arquivo = foto.arquivo
    modelo.fotos.remove(foto)
    db.commit()
    _apagar_arquivo(arquivo)
    db.refresh(modelo)
    return modelo
