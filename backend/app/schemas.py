"""Schemas Pydantic para validação e serialização."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Config ----------
class ConfigBase(BaseModel):
    instagram: str
    email: str
    assinatura_nome: str
    assinatura_cargo: str
    assinatura_cpf: str
    assinatura_rg: str
    encargos_padrao: float
    logo_path: str
    contato_logo_path: str = "contato.png"


class ConfigUpdate(BaseModel):
    instagram: Optional[str] = None
    email: Optional[str] = None
    assinatura_nome: Optional[str] = None
    assinatura_cargo: Optional[str] = None
    assinatura_cpf: Optional[str] = None
    assinatura_rg: Optional[str] = None
    encargos_padrao: Optional[float] = None


class ConfigOut(ConfigBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Cliente ----------
class ClienteBase(BaseModel):
    razao_social: str
    endereco: str = ""
    cnpj_cpf: str = ""
    inscricao_estadual: str = ""
    telefone: str = ""
    contato_comercial: str = ""


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    razao_social: Optional[str] = None
    endereco: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    telefone: Optional[str] = None
    contato_comercial: Optional[str] = None


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    total_orcamentos: int = 0
    logo_path: Optional[str] = None


# ---------- Catálogo ----------
class CatalogoBase(BaseModel):
    nome: str
    descritivo: str = ""
    valor_unitario_padrao: float = 0.0
    quantidade_sugerida: float = 1.0
    diarias_sugeridas: float = 1.0


class CatalogoCreate(CatalogoBase):
    pass


class CatalogoUpdate(BaseModel):
    nome: Optional[str] = None
    descritivo: Optional[str] = None
    valor_unitario_padrao: Optional[float] = None
    quantidade_sugerida: Optional[float] = None
    diarias_sugeridas: Optional[float] = None


class CatalogoOut(CatalogoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Itens de orçamento ----------
class ItemBase(BaseModel):
    item: str = ""
    descritivo: str = ""
    quantidade: float = 0.0
    diarias: float = 0.0
    valor_unitario: float = 0.0
    encargos_percentual: Optional[float] = None
    ordem: int = 0


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    # Valores calculados.
    total: float = 0.0
    encargos: float = 0.0
    total_final: float = 0.0


# ---------- Orçamento ----------
class OrcamentoBase(BaseModel):
    cliente_id: int
    cliente_nome: str = ""
    evento_nome: str = ""
    evento_data: str = ""
    evento_local: str = ""
    encargos_percentual: float = 15.0
    data_entrega: str = ""
    especificacoes: str = ""
    vencimento: str = ""
    prazo: str = ""
    validade: str = ""
    status: str = "rascunho"


class OrcamentoCreate(OrcamentoBase):
    itens: list[ItemBase] = []


class OrcamentoUpdate(BaseModel):
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = None
    evento_nome: Optional[str] = None
    evento_data: Optional[str] = None
    evento_local: Optional[str] = None
    encargos_percentual: Optional[float] = None
    data_entrega: Optional[str] = None
    especificacoes: Optional[str] = None
    vencimento: Optional[str] = None
    prazo: Optional[str] = None
    validade: Optional[str] = None
    status: Optional[str] = None
    itens: Optional[list[ItemBase]] = None


class OrcamentoListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: str
    cliente_id: int
    cliente_razao_social: str = ""
    cliente_nome: str = ""
    evento_nome: str
    evento_data: str
    status: str
    previsao_investimento: float = 0.0
    created_at: datetime


class OrcamentoOut(OrcamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: str
    created_at: datetime
    updated_at: datetime
    cliente: ClienteOut
    itens: list[ItemOut] = []
    soma_total: float = 0.0
    soma_encargos: float = 0.0
    previsao_investimento: float = 0.0
