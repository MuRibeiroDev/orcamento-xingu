"""Modelos do banco de dados."""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Config(Base):
    """Dados fixos da empresa (XINGU). Linha única, id=1."""
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    instagram = Column(String, default="@agenciaxingu")
    email = Column(String, default="glauciasiqueira@xinguproducoes.com.br")
    assinatura_nome = Column(String, default="Gláucia Siqueira de Souza")
    assinatura_cargo = Column(String, default="Produtora")
    assinatura_cpf = Column(String, default="005.010.491-85")
    assinatura_rg = Column(String, default="3987619 SPTC GO")
    # Percentual de encargos sugerido como padrão ao criar um orçamento (15%).
    encargos_padrao = Column(Float, default=15.0)
    # Percentual da nota fiscal sugerido ao criar um orçamento (controle interno).
    nota_padrao = Column(Float, default=0.0)
    # Logo principal da XINGU (canto superior esquerdo). Servida em /static.
    logo_path = Column(String, default="logo.png")
    # Imagem de contato @agenciaxingu (canto superior direito). Servida em /static.
    contato_logo_path = Column(String, default="contato.png")


class Cliente(Base):
    """Cliente do orçamento. Um cliente pode ter vários orçamentos."""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    razao_social = Column(String, nullable=False)
    endereco = Column(String, default="")
    cnpj_cpf = Column(String, default="")
    inscricao_estadual = Column(String, default="")
    telefone = Column(String, default="")
    contato_comercial = Column(String, default="")
    # Logo própria do cliente (servida em /static). Opcional.
    logo_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orcamentos = relationship(
        "Orcamento", back_populates="cliente", cascade="all, delete-orphan"
    )


class CatalogoItem(Base):
    """Item/serviço reutilizável com valor fixo padrão."""
    __tablename__ = "catalogo_itens"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descritivo = Column(Text, default="")
    valor_unitario_padrao = Column(Float, default=0.0)
    quantidade_sugerida = Column(Float, default=1.0)
    diarias_sugeridas = Column(Float, default=1.0)
    # Item sem custo próprio (ex.: mão de obra): o valor inteiro conta como lucro.
    sem_custo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Orcamento(Base):
    """Orçamento vinculado a um cliente."""
    __tablename__ = "orcamentos"

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, index=True)  # ORÇ-AAAA-NNN
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    # Cliente final do orçamento (cliente da agência).
    cliente_nome = Column(String, default="")

    # Dados do evento.
    evento_nome = Column(String, default="")
    evento_data = Column(String, default="")  # texto livre, ex: "26 a 30 de maio de 2026"
    evento_local = Column(String, default="")

    # Encargos flexíveis por orçamento (percentual padrão aplicado às linhas).
    encargos_percentual = Column(Float, default=15.0)

    # Condições.
    data_entrega = Column(String, default="")
    especificacoes = Column(Text, default="")
    vencimento = Column(String, default="")
    prazo = Column(String, default="")
    validade = Column(String, default="")  # ex: "Proposta válida por 15 dias"

    status = Column(String, default="rascunho")  # rascunho | enviado | aprovado

    # Controle interno (não aparece no PDF).
    nota_percentual = Column(Float, default=0.0)  # % da nota fiscal sobre o faturamento
    pago = Column(Boolean, default=False)
    data_pagamento = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="orcamentos")
    itens = relationship(
        "OrcamentoItem",
        back_populates="orcamento",
        cascade="all, delete-orphan",
        order_by="OrcamentoItem.ordem",
    )


class OrcamentoItem(Base):
    """Linha de item de um orçamento."""
    __tablename__ = "orcamento_itens"

    id = Column(Integer, primary_key=True)
    orcamento_id = Column(Integer, ForeignKey("orcamentos.id"), nullable=False)
    ordem = Column(Integer, default=0)

    item = Column(String, default="")
    descritivo = Column(Text, default="")
    quantidade = Column(Float, default=0.0)
    diarias = Column(Float, default=0.0)
    valor_unitario = Column(Float, default=0.0)
    # Encargos por linha: se None, usa o percentual do orçamento.
    encargos_percentual = Column(Float, nullable=True)
    # Controle interno: sem custo (ex.: mão de obra) -> o valor inteiro conta como lucro.
    sem_custo = Column(Boolean, default=False)

    orcamento = relationship("Orcamento", back_populates="itens")


class Modelo(Base):
    """Pessoa do banco de casting (modelo/promotora), reutilizável entre castings."""
    __tablename__ = "modelos"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    # Campos exibidos no card do casting, cada um com seu ícone (texto livre).
    idade = Column(String, default="")
    manequim = Column(String, default="")
    altura = Column(String, default="")
    destaque = Column(String, default="")  # ex: "Belo Horizonte - MG", "Bilíngue"
    created_at = Column(DateTime, default=datetime.utcnow)

    fotos = relationship(
        "ModeloFoto",
        back_populates="modelo",
        cascade="all, delete-orphan",
        order_by="ModeloFoto.ordem",
    )


class ModeloFoto(Base):
    """Foto de uma modelo (arquivo em /static/modelos). O card usa até 4."""
    __tablename__ = "modelo_fotos"

    id = Column(Integer, primary_key=True)
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)
    arquivo = Column(String, nullable=False)  # caminho relativo a /static
    ordem = Column(Integer, default=0)

    modelo = relationship("Modelo", back_populates="fotos")


class Casting(Base):
    """Apresentação de casting em PDF: marca (xingu | boom) + pessoas selecionadas."""
    __tablename__ = "castings"

    id = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)  # ex: "SIC - CRESOL" (identificação e nome do arquivo)
    marca = Column(String, default="xingu")  # xingu | boom
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    itens = relationship(
        "CastingModelo",
        back_populates="casting",
        cascade="all, delete-orphan",
        order_by="CastingModelo.ordem",
    )


class CastingModelo(Base):
    """Pessoa incluída num casting, na ordem em que aparece no PDF."""
    __tablename__ = "casting_modelos"

    id = Column(Integer, primary_key=True)
    casting_id = Column(Integer, ForeignKey("castings.id"), nullable=False)
    modelo_id = Column(Integer, ForeignKey("modelos.id", ondelete="CASCADE"), nullable=False)
    ordem = Column(Integer, default=0)

    casting = relationship("Casting", back_populates="itens")
    modelo = relationship("Modelo")
