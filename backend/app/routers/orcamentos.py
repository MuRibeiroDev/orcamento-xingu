"""Rotas de orçamentos: CRUD, cálculo, duplicação e geração de PDF."""
import unicodedata
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import calc, models, schemas
from ..auth import usuario_atual
from ..database import get_db
from ..pdf import gerar_pdf
from .clientes import _to_out as cliente_to_out
from .config import get_config

router = APIRouter(prefix="/api/orcamentos", tags=["orcamentos"])


def gerar_numero(db: Session) -> str:
    """Gera o próximo número no formato ORÇ-AAAA-NNN dentro do ano corrente."""
    ano = datetime.utcnow().year
    prefixo = f"ORÇ-{ano}-"
    existentes = (
        db.query(models.Orcamento)
        .filter(models.Orcamento.numero.like(f"{prefixo}%"))
        .all()
    )
    maior = 0
    for o in existentes:
        try:
            n = int(o.numero.rsplit("-", 1)[1])
            maior = max(maior, n)
        except (ValueError, IndexError):
            continue
    return f"{prefixo}{maior + 1:03d}"


def serializar(orcamento: models.Orcamento) -> schemas.OrcamentoOut:
    """Monta o OrcamentoOut incluindo os valores calculados."""
    calculo = calc.calcular_orcamento(orcamento)
    por_id = {l["id"]: l for l in calculo["linhas"]}

    out = schemas.OrcamentoOut.model_validate(orcamento)
    out.cliente = cliente_to_out(orcamento.cliente)
    itens_out = []
    for item in orcamento.itens:
        item_out = schemas.ItemOut.model_validate(item)
        c = por_id.get(item.id, {})
        item_out.total = c.get("total", 0.0)
        item_out.encargos = c.get("encargos", 0.0)
        item_out.total_final = c.get("total_final", 0.0)
        itens_out.append(item_out)
    out.itens = itens_out
    out.soma_total = calculo["soma_total"]
    out.soma_encargos = calculo["soma_encargos"]
    out.previsao_investimento = calculo["previsao_investimento"]
    return out


@router.get("", response_model=list[schemas.OrcamentoListOut])
def listar(
    cliente_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    """Lista orçamentos; filtra por cliente quando cliente_id é informado."""
    query = db.query(models.Orcamento)
    if cliente_id is not None:
        query = query.filter(models.Orcamento.cliente_id == cliente_id)
    orcamentos = query.order_by(models.Orcamento.created_at.desc()).all()
    resultado = []
    for o in orcamentos:
        calculo = calc.calcular_orcamento(o)
        resultado.append(
            schemas.OrcamentoListOut(
                id=o.id,
                numero=o.numero,
                cliente_id=o.cliente_id,
                cliente_razao_social=o.cliente.razao_social if o.cliente else "",
                cliente_nome=o.cliente_nome,
                evento_nome=o.evento_nome,
                evento_data=o.evento_data,
                status=o.status,
                previsao_investimento=calculo["previsao_investimento"],
                created_at=o.created_at,
            )
        )
    return resultado


@router.post("", response_model=schemas.OrcamentoOut, status_code=201)
def criar(
    dados: schemas.OrcamentoCreate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    if not db.get(models.Cliente, dados.cliente_id):
        raise HTTPException(400, "Cliente inexistente")
    payload = dados.model_dump()
    itens = payload.pop("itens", [])
    orcamento = models.Orcamento(**payload, numero=gerar_numero(db))
    for i, item in enumerate(itens):
        item["ordem"] = item.get("ordem") or i
        orcamento.itens.append(models.OrcamentoItem(**item))
    db.add(orcamento)
    db.commit()
    db.refresh(orcamento)
    return serializar(orcamento)


@router.get("/{orcamento_id}", response_model=schemas.OrcamentoOut)
def obter(orcamento_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    orcamento = db.get(models.Orcamento, orcamento_id)
    if not orcamento:
        raise HTTPException(404, "Orçamento não encontrado")
    return serializar(orcamento)


@router.put("/{orcamento_id}", response_model=schemas.OrcamentoOut)
def atualizar(
    orcamento_id: int,
    dados: schemas.OrcamentoUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    orcamento = db.get(models.Orcamento, orcamento_id)
    if not orcamento:
        raise HTTPException(404, "Orçamento não encontrado")
    payload = dados.model_dump(exclude_unset=True)
    itens = payload.pop("itens", None)
    for campo, valor in payload.items():
        setattr(orcamento, campo, valor)
    # Substitui as linhas inteiras quando "itens" é enviado.
    if itens is not None:
        orcamento.itens.clear()
        db.flush()
        for i, item in enumerate(itens):
            item["ordem"] = item.get("ordem") or i
            orcamento.itens.append(models.OrcamentoItem(**item))
    db.commit()
    db.refresh(orcamento)
    return serializar(orcamento)


@router.post("/{orcamento_id}/duplicar", response_model=schemas.OrcamentoOut, status_code=201)
def duplicar(orcamento_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    orig = db.get(models.Orcamento, orcamento_id)
    if not orig:
        raise HTTPException(404, "Orçamento não encontrado")
    novo = models.Orcamento(
        numero=gerar_numero(db),
        cliente_id=orig.cliente_id,
        evento_nome=orig.evento_nome,
        evento_data=orig.evento_data,
        evento_local=orig.evento_local,
        encargos_percentual=orig.encargos_percentual,
        data_entrega=orig.data_entrega,
        especificacoes=orig.especificacoes,
        vencimento=orig.vencimento,
        prazo=orig.prazo,
        validade=orig.validade,
        status="rascunho",
    )
    for item in orig.itens:
        novo.itens.append(
            models.OrcamentoItem(
                ordem=item.ordem,
                item=item.item,
                descritivo=item.descritivo,
                quantidade=item.quantidade,
                diarias=item.diarias,
                valor_unitario=item.valor_unitario,
                encargos_percentual=item.encargos_percentual,
            )
        )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return serializar(novo)


@router.delete("/{orcamento_id}", status_code=204)
def excluir(orcamento_id: int, db: Session = Depends(get_db), _: str = Depends(usuario_atual)):
    orcamento = db.get(models.Orcamento, orcamento_id)
    if not orcamento:
        raise HTTPException(404, "Orçamento não encontrado")
    db.delete(orcamento)
    db.commit()


@router.get("/{orcamento_id}/pdf")
def pdf(
    orcamento_id: int,
    orientacao: str = "landscape",
    db: Session = Depends(get_db),
    _: str = Depends(usuario_atual),
):
    orcamento = db.get(models.Orcamento, orcamento_id)
    if not orcamento:
        raise HTTPException(404, "Orçamento não encontrado")
    cfg = get_config(db)
    buffer = gerar_pdf(orcamento, cfg, orientacao=orientacao)
    # Nome de arquivo ASCII-safe para o header HTTP (ex.: ORÇ-2026-001 -> ORC-2026-001).
    base = orcamento.numero.replace("Ç", "C").replace("ç", "c").replace("/", "-")
    nome_arquivo = (
        unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii") + ".pdf"
    )
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nome_arquivo}"'},
    )
