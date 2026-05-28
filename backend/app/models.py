"""Modelos do banco de dados."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
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

    orcamento = relationship("Orcamento", back_populates="itens")
