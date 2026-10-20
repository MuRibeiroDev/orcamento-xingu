"""Schemas Pydantic para validação e serialização."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    nota_padrao: float = 0.0
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
    nota_padrao: Optional[float] = Field(None, ge=0, le=100)


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
    sem_custo: bool = False


class CatalogoCreate(CatalogoBase):
    pass


class CatalogoUpdate(BaseModel):
    nome: Optional[str] = None
    descritivo: Optional[str] = None
    valor_unitario_padrao: Optional[float] = None
    quantidade_sugerida: Optional[float] = None
    diarias_sugeridas: Optional[float] = None
    sem_custo: Optional[bool] = None


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
    sem_custo: bool = False


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
    # Controle interno (não vai para o PDF).
    nota_percentual: float = Field(0.0, ge=0, le=100)
    pago: bool = False
    data_pagamento: Optional[date] = None


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
    nota_percentual: Optional[float] = Field(None, ge=0, le=100)
    pago: Optional[bool] = None
    data_pagamento: Optional[date] = None
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
    nota_percentual: float = 0.0
    pago: bool = False
    data_pagamento: Optional[date] = None
    faturamento: float = 0.0
    custo: float = 0.0
    lucro_bruto: float = 0.0
    valor_nota: float = 0.0
    recebimento_liquido: float = 0.0
    lucro_liquido: float = 0.0


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
    faturamento: float = 0.0
    custo: float = 0.0
    lucro_bruto: float = 0.0
    valor_nota: float = 0.0
    recebimento_liquido: float = 0.0
    lucro_liquido: float = 0.0


# ---------- Casting ----------
MARCAS = ("xingu", "boom")


class ModeloBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    idade: str = Field("", max_length=60)
    manequim: str = Field("", max_length=60)
    altura: str = Field("", max_length=60)
    destaque: str = Field("", max_length=120)


class ModeloCreate(ModeloBase):
    pass


class ModeloUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=120)
    idade: Optional[str] = Field(None, max_length=60)
    manequim: Optional[str] = Field(None, max_length=60)
    altura: Optional[str] = Field(None, max_length=60)
    destaque: Optional[str] = Field(None, max_length=120)


class ModeloFotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    arquivo: str
    ordem: int


class ModeloOut(ModeloBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    fotos: list[ModeloFotoOut] = []


class CastingBase(BaseModel):
    titulo: str = Field(min_length=1, max_length=120)
    marca: str = "xingu"

    @field_validator("marca")
    @classmethod
    def _marca_valida(cls, v: str) -> str:
        if v not in MARCAS:
            raise ValueError(f"marca deve ser uma de: {', '.join(MARCAS)}")
        return v


class CastingSalvar(CastingBase):
    # IDs das modelos na ordem em que aparecem no PDF.
    modelo_ids: list[int] = []


class CastingListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    marca: str
    total_modelos: int = 0
    updated_at: datetime


class CastingOut(CastingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    modelos: list[ModeloOut] = []
