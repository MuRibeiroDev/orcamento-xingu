"""Rotas de autenticação."""
from fastapi import APIRouter, HTTPException, status

from .. import auth, schemas

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(dados: schemas.LoginIn):
    if not auth.autenticar(dados.username, dados.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )
    return schemas.Token(access_token=auth.criar_token(dados.username))
