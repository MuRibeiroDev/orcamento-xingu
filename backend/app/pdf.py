"""Geração do PDF do orçamento com xhtml2pdf, replicando o modelo da XINGU."""
import base64
import html
import os
from io import BytesIO

from PIL import Image
from reportlab.pdfbase.pdfmetrics import stringWidth
from xhtml2pdf import pisa

from .calc import calcular_orcamento, formatar_brl

PT_POR_CM = 28.3465  # pontos por centímetro
PX_PARA_PT = 0.75    # xhtml2pdf converte 1px ≈ 0,75pt (96 dpi)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _logo_data_uri(logo_path: str) -> str:
    """Lê o logo do diretório static e devolve como data URI base64 (evita problemas de caminho)."""
    caminho = os.path.join(STATIC_DIR, logo_path or "logo.png")
    if not os.path.exists(caminho):
        return ""
    ext = os.path.splitext(caminho)[1].lstrip(".").lower() or "png"
    if ext == "jpg":
        ext = "jpeg"
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


def _logo_dims(logo_path: str, max_w: int, max_h: int) -> tuple:
    """Dimensões (w, h) em px para a logo caber numa caixa, preservando a proporção.

    Assim qualquer logo (quadrada como a XINGU ou larga como a BOOM) fica bem dimensionada.
    """
    caminho = os.path.join(STATIC_DIR, logo_path or "")
    if not os.path.exists(caminho):
        return max_h, max_h
    with Image.open(caminho) as im:
        w, h = im.size
    escala = min(max_w / w, max_h / h)
    return max(1, int(w * escala)), max(1, int(h * escala))


def _fonte_que_cabe(texto, base_px, largura_pt, fonte="Helvetica-Bold", min_px=6.0):
    """Reduz a fonte (px) caso a maior palavra não caiba na largura da coluna.

    Evita que uma palavra única maior que a coluna 'vaze' para a coluna ao lado.
    """
    if not texto:
        return base_px
    maior = max(texto.split() or [texto], key=len)
    largura = stringWidth(maior, fonte, base_px * PX_PARA_PT)
    if largura <= largura_pt:
        return base_px
    return max(min_px, round(base_px * largura_pt / largura, 1))


def _esc(valor) -> str:
    """Escapa texto para HTML, preservando quebras de linha."""
    return html.escape(str(valor or "")).replace("\n", "<br/>")


def montar_html(orcamento, cfg, orientacao: str = "landscape") -> str:
    orientacao = "portrait" if orientacao == "portrait" else "landscape"
    retrato = orientacao == "portrait"
    calculo = calcular_orcamento(orcamento)
    por_id = {l["id"]: l for l in calculo["linhas"]}
    cliente = orcamento.cliente

    # Tamanhos adaptados à orientação (a vertical é mais estreita, então tudo um pouco menor).
    s = {
        "fs_tab": 8 if retrato else 10,
        "fs_num": 11 if retrato else 12,  # dados das colunas numéricas/de valor
        "fs_th": 7 if retrato else 9,
        "fs_prev": 11 if retrato else 12,
        "fs_cab": 9.5 if retrato else 12,
        "fs_titulo": 11 if retrato else 13,
        "fs_cond": 9 if retrato else 11,
        "fs_assin": 10 if retrato else 11.5,
        "contato_h": 60 if retrato else 76,
        "logo_max_w": 200 if retrato else 300,
        "logo_max_h": 95 if retrato else 135,
    }

    # Logo da agência (esquerda). Se a agência não tiver logo própria, usa a logo padrão.
    logo_arquivo = getattr(cliente, "logo_path", None) or cfg.logo_path
    logo_principal = _logo_data_uri(logo_arquivo)
    logo_w, logo_h = _logo_dims(logo_arquivo, max_w=s["logo_max_w"], max_h=s["logo_max_h"])

    # Imagem de contato @agenciaxingu (direita).
    contato_logo = _logo_data_uri(getattr(cfg, "contato_logo_path", "") or "contato.png")
    if contato_logo:
        bloco_contato = f'<img class="contato-logo" src="{contato_logo}"/>'
    else:
        bloco_contato = (
            f'<div class="insta">{_esc(cfg.instagram)}</div><div>{_esc(cfg.email)}</div>'
        )

    # Largura útil da coluna ITEM (em pt), para reduzir a fonte de itens com palavra longa.
    largura_pagina_cm = 21.0 if retrato else 29.7
    util_pt = (largura_pagina_cm - 2 * 1.2) * PT_POR_CM
    largura_item_pt = util_pt * 0.09 - 11  # 9% da largura menos padding/borda da célula

    # Linhas da tabela principal.
    linhas_html = ""
    for item in orcamento.itens:
        c = por_id.get(item.id, {})
        fs_item = _fonte_que_cabe(item.item, s["fs_tab"], largura_item_pt)
        linhas_html += f"""
        <tr>
          <td class="c-item" style="font-size:{fs_item}px">{_esc(item.item)}</td>
          <td class="c-desc">{_esc(item.descritivo)}</td>
          <td class="c-num">{_esc(_fmt_qtd(item.quantidade))}</td>
          <td class="c-num">{_esc(_fmt_qtd(item.diarias))}</td>
          <td class="c-val">R$ {formatar_brl(item.valor_unitario)}</td>
          <td class="c-val">R$ {formatar_brl(c.get('total', 0))}</td>
          <td class="c-val">R$ {formatar_brl(c.get('encargos', 0))}</td>
          <td class="c-val total">R$ {formatar_brl(c.get('total_final', 0))}</td>
        </tr>"""

    validade_html = (
        f'<p class="validade">{_esc(orcamento.validade)}</p>' if orcamento.validade else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  @page {{ size: a4 {orientacao}; margin: 1.2cm; }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 8px; color: #1a1a1a; }}
  .topo {{ width: 100%; margin-bottom: 20px; }}
  .topo td {{ vertical-align: middle; padding: 8px 0 14px; }}
  .logo {{ height: 115px; }}
  .logo-xingu {{ height: 145px; }}
  .contato {{ text-align: right; font-size: 10px; color: #444; padding-right: 6px; }}
  .contato-logo {{ height: {s["contato_h"]}px; }}
  .contato .insta {{ font-weight: bold; font-size: 11px; color: #b8312f; }}
  .numero {{ text-align: right; font-size: 13px; font-weight: bold; margin: 6px 0; color: #b8312f; }}
  .cab {{ margin-top: 14px; font-size: {s["fs_cab"]}px; line-height: 1.6; }}
  .cab b {{ color: #000; }}
  .cab .v {{ color: #b8312f; }}
  .titulo {{ background: #d9d9d9; text-align: center; font-weight: bold; font-size: {s["fs_titulo"]}px;
            padding: 6px; margin-top: 10px; border: 1px solid #888; }}
  table.itens {{ width: 100%; border-collapse: collapse; margin-top: 0; table-layout: fixed; }}
  table.itens th {{ background: #404040; color: #fff; font-size: {s["fs_th"]}px; padding: 6px 3px;
                    border: 1px solid #888; vertical-align: middle; word-wrap: break-word;
                    text-align: center; }}
  table.itens td {{ border: 1px solid #999; padding: 6px 5px; font-size: {s["fs_tab"]}px;
                    vertical-align: top; word-wrap: break-word; }}
  /* Larguras das colunas (TH e TD). Títulos sempre centralizados; dados alinhados por tipo. */
  .c-item {{ width: 9%; }}
  .c-desc {{ width: 30%; }}
  .c-num {{ width: 7.5%; }}
  .c-val {{ width: 11.5%; }}
  td.c-item {{ text-align: left; font-weight: bold; color: #b8312f; }}
  td.c-desc {{ text-align: left; }}
  td.c-num {{ text-align: center; font-size: {s["fs_num"]}px; }}
  td.c-val {{ text-align: right; white-space: nowrap; font-size: {s["fs_num"]}px; }}
  td.total {{ font-weight: bold; }}
  .previsao td {{ background: #f0f0f0; font-weight: bold; font-size: {s["fs_prev"]}px; }}
  .previsao .lbl {{ text-align: right; }}
  table.cond {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
  table.cond th {{ background: #d9d9d9; border: 1px solid #888; padding: 6px; font-size: {s["fs_cond"]}px; }}
  table.cond td {{ border: 1px solid #999; padding: 18px 6px; font-size: {s["fs_cond"]}px; }}
  .assin {{ margin-top: 22px; font-size: {s["fs_assin"]}px; line-height: 1.8; }}
  .assin .linha {{ margin-top: 18px; }}
  .validade {{ margin-top: 10px; font-size: 8.5px; font-style: italic; color: #555; }}
</style>
</head>
<body>
  <table class="topo">
    <tr>
      <td>{f'<img src="{logo_principal}" width="{logo_w}" height="{logo_h}"/>' if logo_principal else ''}</td>
      <td class="contato">{bloco_contato}</td>
    </tr>
  </table>

  <div class="cab">
    <b>RAZÃO SOCIAL:</b> <span class="v">{_esc(cliente.razao_social)}</span><br/>
    <b>ENDEREÇO:</b> <span class="v">{_esc(cliente.endereco)}</span><br/>
    <b>CNPJ/CPF:</b> <span class="v">{_esc(cliente.cnpj_cpf)}</span>
        &nbsp;&nbsp; <b>INSC. ESTADUAL:</b> <span class="v">{_esc(cliente.inscricao_estadual)}</span><br/>
    <b>TELEFONE:</b> <span class="v">{_esc(cliente.telefone)}</span>
        &nbsp;&nbsp; <b>CONTATO COMERCIAL:</b> <span class="v">{_esc(cliente.contato_comercial)}</span><br/>
    <b>DATA DO EVENTO:</b> <span class="v">{_esc(orcamento.evento_data)}</span><br/>
    <b>LOCAL:</b> <span class="v">{_esc(orcamento.evento_local)}</span><br/>
    <b>EVENTO:</b> <span class="v">{_esc(orcamento.evento_nome)}</span>
  </div>

  <div class="titulo">PREVISÃO DE INVESTIMENTO</div>
  <table class="itens">
    <thead>
      <tr>
        <th class="c-item">ITEM</th><th class="c-desc">DESCRITIVO</th>
        <th class="c-num">QUANTIDADE</th><th class="c-num">DIÁRIAS</th>
        <th class="c-val">VL. UNITÁRIO</th><th class="c-val">TOTAL</th>
        <th class="c-val">ENCARGOS</th><th class="c-val">TOTAL</th>
      </tr>
    </thead>
    <tbody>
      {linhas_html}
      <tr class="previsao">
        <td colspan="7" class="lbl">Total:</td>
        <td class="c-val">R$ {formatar_brl(calculo['previsao_investimento'])}</td>
      </tr>
    </tbody>
  </table>

  {validade_html}

  <table class="cond">
    <thead>
      <tr>
        <th style="width:25%">DATA DA ENTREGA</th>
        <th style="width:30%">ESPECIFICAÇÕES</th>
        <th style="width:22%">VENCIMENTO</th>
        <th style="width:23%">PRAZO</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="width:25%">{_esc(orcamento.data_entrega) or "&nbsp;"}</td>
        <td style="width:30%">{_esc(orcamento.especificacoes) or "&nbsp;"}</td>
        <td style="width:22%">{_esc(orcamento.vencimento) or "&nbsp;"}</td>
        <td style="width:23%">{_esc(orcamento.prazo) or "&nbsp;"}</td>
      </tr>
    </tbody>
  </table>

  <div class="assin">
    <b>NOME:</b> {_esc(cfg.assinatura_nome)}<br/>
    <b>Cargo:</b> {_esc(cfg.assinatura_cargo)}<br/>
    <b>CPF:</b> {_esc(cfg.assinatura_cpf)} &nbsp;&nbsp; <b>RG:</b> {_esc(cfg.assinatura_rg)}<br/>
    <div class="linha"><b>ASSINATURA:</b> _______________________________________________________</div>
  </div>
</body>
</html>"""


def _fmt_qtd(valor) -> str:
    """Mostra quantidades inteiras sem casas decimais (2 em vez de 2.0)."""
    v = valor or 0
    return str(int(v)) if float(v).is_integer() else str(v)


def gerar_pdf(orcamento, cfg, orientacao: str = "landscape") -> BytesIO:
    """Renderiza o orçamento em PDF e devolve um buffer pronto para download."""
    html_str = montar_html(orcamento, cfg, orientacao=orientacao)
    buffer = BytesIO()
    pisa.CreatePDF(src=html_str, dest=buffer, encoding="utf-8")
    buffer.seek(0)
    return buffer
