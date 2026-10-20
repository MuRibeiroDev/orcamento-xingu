"""Geração do PDF de casting (apresentação 16:9) com reportlab, replicando o modelo de casting.

Estrutura: capa (logo da marca à esquerda, "Casting" à direita), páginas com 2 pessoas cada
(grade de até 4 fotos + nome + informações com ícones) e página final com a logo.
"""
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Optional

from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

APP_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(APP_DIR, "static")
FONTS_DIR = os.path.join(APP_DIR, "fonts")
MARCAS_DIR = os.path.join(APP_DIR, "marcas")

# Página 16:9 (pontos).
W, H = 960, 540
METADE = W / 2

# Card de cada pessoa (um por metade da página).
CARD_MX = 30          # margem lateral do card dentro da metade
CARD_MY = 25          # margem superior/inferior
CARD_PAD = 8
FOTOS_W = 268         # largura da área de fotos
FOTO_GAP = 2
FOTO_DPI_FATOR = 3    # pixels por ponto ao redimensionar as fotos (~216 dpi)
FOTO_FOCO_Y = 0.3     # ao cortar na vertical, privilegia o topo (rostos)

FONTE_NOME = "BebasNeue"
FONTE_TITULO = "OutfitBold"
FONTE_INFO = "RobotoCondensed"
TAM_INFO = 13


@dataclass(frozen=True)
class Tema:
    logo: str
    escuro: str        # metade esquerda das páginas de pessoas e da página final
    claro: str         # metade direita
    capa_esq: str      # fundo atrás da logo na capa
    capa_dir: str      # fundo atrás do "Casting"
    capa_texto: str    # cor do "Casting"
    nome: str          # cor do nome da pessoa
    coracao: str
    detalhe: str       # filete vertical ao lado do ano na capa
    ano: str


TEMAS = {
    "xingu": Tema(
        logo="xingu.png", escuro="#6D194B", claro="#E6DED5",
        capa_esq="#6D194B", capa_dir="#E6DED5", capa_texto="#6D194B",
        nome="#4A3B30", coracao="#C8102E", detalhe="#C9A66B", ano="#4A3B30",
    ),
    "boom": Tema(
        logo="boom.png", escuro="#151515", claro="#ECE6DF",
        capa_esq="#F4EFEA", capa_dir="#151515", capa_texto="#F26A1B",
        nome="#151515", coracao="#F26A1B", detalhe="#F26A1B", ano="#ECE6DF",
    ),
}


@dataclass(frozen=True)
class Pessoa:
    nome: str
    idade: str
    manequim: str
    altura: str
    destaque: str
    fotos: tuple  # caminhos relativos a /static, na ordem do card


def _registrar_fontes():
    registradas = pdfmetrics.getRegisteredFontNames()
    for nome, arquivo in (
        (FONTE_NOME, "BebasNeue-Regular.ttf"),
        (FONTE_TITULO, "Outfit-Bold.ttf"),
        (FONTE_INFO, "RobotoCondensed-Regular.ttf"),
    ):
        if nome not in registradas:
            pdfmetrics.registerFont(TTFont(nome, os.path.join(FONTS_DIR, arquivo)))


# ---------- Textos ----------
def _quebrar(texto: str, fonte: str, tamanho: float, largura: float) -> list:
    """Quebra o texto em linhas que caibam na largura (por palavras)."""
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if not atual or pdfmetrics.stringWidth(tentativa, fonte, tamanho) <= largura:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _nome_ajustado(nome: str, largura: float) -> tuple:
    """Nome em maiúsculas quebrado em até 3 linhas, com a maior fonte que couber."""
    texto = nome.upper().strip()
    tamanho = 38.0
    while tamanho > 12:
        linhas = _quebrar(texto, FONTE_NOME, tamanho, largura)
        cabe = all(pdfmetrics.stringWidth(l, FONTE_NOME, tamanho) <= largura for l in linhas)
        if cabe and len(linhas) <= 3:
            return linhas, tamanho
        tamanho -= 1
    return _quebrar(texto, FONTE_NOME, tamanho, largura), tamanho


def _infos(p: Pessoa) -> list:
    """Linhas (ícone, texto) do card; campos vazios não aparecem."""
    idade = p.idade.strip()
    if idade.isdigit():
        idade = f"{idade} anos"
    manequim = p.manequim.strip()
    if manequim and not manequim.lower().startswith("manequim"):
        manequim = f"Manequim {manequim}"
    itens = [
        ("pessoa", idade),
        ("regua", manequim),
        ("vestido", p.altura.strip()),
        ("coracao", p.destaque.strip()),
    ]
    return [(icone, texto) for icone, texto in itens if texto]


# ---------- Ícones (vetoriais) ----------
def _icone(c: canvas.Canvas, tipo: str, cx: float, cy: float, tema: Tema):
    """Desenha o ícone centrado em (cx, cy), ~16pt de altura."""
    c.saveState()
    c.setLineWidth(1.2)
    c.setStrokeColor(HexColor("#111111"))
    c.setLineJoin(1)
    c.setLineCap(1)
    if tipo == "pessoa":
        c.circle(cx, cy + 3.5, 3.6, stroke=1, fill=0)
        p = c.beginPath()
        p.moveTo(cx - 7, cy - 8)
        p.curveTo(cx - 7, cy - 0.5, cx + 7, cy - 0.5, cx + 7, cy - 8)
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    elif tipo == "regua":
        c.rect(cx - 3, cy - 8.5, 6.5, 17, stroke=1, fill=0)
        for i in range(1, 7):
            y = cy - 8.5 + i * 17 / 7
            c.line(cx - 3, y, cx - 3 + (3.5 if i % 2 else 2), y)
    elif tipo == "vestido":
        p = c.beginPath()
        p.moveTo(cx - 2, cy + 8.5)
        p.lineTo(cx - 2.6, cy + 4)
        p.curveTo(cx - 3.6, cy + 2.5, cx - 2.6, cy + 1, cx - 2.2, cy)
        p.lineTo(cx - 6, cy - 8.5)
        p.curveTo(cx - 2, cy - 9.5, cx + 2, cy - 9.5, cx + 6, cy - 8.5)
        p.lineTo(cx + 2.2, cy)
        p.curveTo(cx + 2.6, cy + 1, cx + 3.6, cy + 2.5, cx + 2.6, cy + 4)
        p.lineTo(cx + 2, cy + 8.5)
        p.curveTo(cx + 1, cy + 6.5, cx - 1, cy + 6.5, cx - 2, cy + 8.5)
        c.drawPath(p, stroke=1, fill=0)
    elif tipo == "coracao":
        c.setFillColor(HexColor(tema.coracao))
        p = c.beginPath()
        p.moveTo(cx, cy - 7.5)
        p.curveTo(cx - 10, cy - 0.5, cx - 6, cy + 9.5, cx, cy + 4.5)
        p.curveTo(cx + 6, cy + 9.5, cx + 10, cy - 0.5, cx, cy - 7.5)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


# ---------- Fotos ----------
def _foto_recortada(arquivo: str, w_pt: float, h_pt: float) -> Optional[ImageReader]:
    """Recorta a foto para preencher a célula (como object-fit: cover) e reduz o tamanho."""
    caminho = os.path.realpath(os.path.join(STATIC_DIR, arquivo))
    if not caminho.startswith(os.path.realpath(STATIC_DIR) + os.sep) or not os.path.exists(caminho):
        return None
    with Image.open(caminho) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        iw, ih = im.size
        alvo = w_pt / h_pt
        if iw / ih > alvo:  # foto mais larga: corta as laterais (centralizado)
            nw = int(ih * alvo)
            x0 = (iw - nw) // 2
            im = im.crop((x0, 0, x0 + nw, ih))
        else:  # foto mais alta: corta em cima/embaixo privilegiando o topo
            nh = int(iw / alvo)
            y0 = int((ih - nh) * FOTO_FOCO_Y)
            im = im.crop((0, y0, iw, y0 + nh))
        tw, th = int(w_pt * FOTO_DPI_FATOR), int(h_pt * FOTO_DPI_FATOR)
        if im.width > tw:
            im = im.resize((tw, th), Image.LANCZOS)
        buf = BytesIO()
        im.save(buf, "JPEG", quality=82)
    buf.seek(0)
    return ImageReader(buf)


def _celulas(n: int) -> list:
    """Posições relativas (x, y, w, h) das fotos na área, origem no canto inferior esquerdo."""
    if n <= 1:
        return [(0, 0, 1, 1)]
    if n == 2:
        return [(0, 0, 0.5, 1), (0.5, 0, 0.5, 1)]
    if n == 3:
        return [(0, 0, 0.5, 1), (0.5, 0.5, 0.5, 0.5), (0.5, 0, 0.5, 0.5)]
    return [(0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5), (0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5)]


def _desenhar_fotos(c: canvas.Canvas, fotos: tuple, x: float, y: float, w: float, h: float):
    fotos = fotos[:4]
    if not fotos:
        c.setFillColor(HexColor("#E5E5E5"))
        c.rect(x, y, w, h, stroke=0, fill=1)
        return
    g = FOTO_GAP / 2
    for arquivo, (rx, ry, rw, rh) in zip(fotos, _celulas(len(fotos))):
        # Meio espaçamento em cada lado interno da célula.
        cx = x + rx * w + (g if rx > 0 else 0)
        cy = y + ry * h + (g if ry > 0 else 0)
        cw = rw * w - (g if rx > 0 else 0) - (g if rx + rw < 1 else 0)
        ch = rh * h - (g if ry > 0 else 0) - (g if ry + rh < 1 else 0)
        img = _foto_recortada(arquivo, cw, ch)
        if img is None:
            c.setFillColor(HexColor("#E5E5E5"))
            c.rect(cx, cy, cw, ch, stroke=0, fill=1)
        else:
            c.drawImage(img, cx, cy, cw, ch)


# ---------- Páginas ----------
def _fundo_dividido(c: canvas.Canvas, esq: str, dir_: str):
    c.setFillColor(HexColor(esq))
    c.rect(0, 0, METADE, H, stroke=0, fill=1)
    c.setFillColor(HexColor(dir_))
    c.rect(METADE, 0, W - METADE, H, stroke=0, fill=1)


def _logo(c: canvas.Canvas, tema: Tema, cx: float, cy: float, max_w: float, max_h: float):
    caminho = os.path.join(MARCAS_DIR, tema.logo)
    img = ImageReader(caminho)
    iw, ih = img.getSize()
    escala = min(max_w / iw, max_h / ih)
    w, h = iw * escala, ih * escala
    c.drawImage(img, cx - w / 2, cy - h / 2, w, h, mask="auto")


def _capa(c: canvas.Canvas, tema: Tema, ano: int):
    _fundo_dividido(c, tema.capa_esq, tema.capa_dir)
    _logo(c, tema, METADE / 2, H / 2, 300, 190)
    c.setFillColor(HexColor(tema.capa_texto))
    c.setFont(FONTE_TITULO, 40)
    c.drawCentredString(METADE + (W - METADE) / 2, H / 2 - 14, "Casting")
    # Filete + ano na vertical, no canto inferior direito (como no modelo).
    c.setStrokeColor(HexColor(tema.detalhe))
    c.setLineWidth(0.8)
    c.line(W - 14, 40, W - 14, 125)
    c.saveState()
    c.setFillColor(HexColor(tema.ano))
    c.setFont(FONTE_INFO, 7)
    c.translate(W - 11.5, 34)
    c.rotate(-90)
    c.drawString(0, 0, str(ano))
    c.restoreState()


def _card(c: canvas.Canvas, p: Pessoa, x0: float, tema: Tema):
    x, y = x0 + CARD_MX, CARD_MY
    w, h = METADE - 2 * CARD_MX, H - 2 * CARD_MY
    topo = y + h
    c.setFillColor(white)
    c.rect(x, y, w, h, stroke=0, fill=1)

    # Filete no topo do card.
    c.setStrokeColor(HexColor("#333333"))
    c.setLineWidth(0.8)
    c.line(x + CARD_PAD, topo - 9, x + w - CARD_PAD, topo - 9)

    # Fotos.
    fx, fy = x + CARD_PAD, y + CARD_PAD
    fh = h - CARD_PAD - 15
    _desenhar_fotos(c, p.fotos, fx, fy, FOTOS_W, fh)

    # Coluna de informações.
    ix = fx + FOTOS_W + 12
    iw = x + w - CARD_PAD - ix
    linhas_nome, tam_nome = _nome_ajustado(p.nome, iw)
    entre_linhas_nome = tam_nome * 0.95
    infos = [(icone, _quebrar(texto, FONTE_INFO, TAM_INFO, iw - 26)[:3]) for icone, texto in _infos(p)]
    altura_infos = sum(42 + 15 * (len(l) - 1) for _, l in infos)
    altura_bloco = len(linhas_nome) * entre_linhas_nome + 14 + altura_infos

    # Bloco centralizado verticalmente (um pouco acima do centro, como no modelo).
    cursor = y + h / 2 + altura_bloco / 2 + 10
    c.setFillColor(HexColor(tema.nome))
    c.setFont(FONTE_NOME, tam_nome)
    for linha in linhas_nome:
        cursor -= entre_linhas_nome
        c.drawString(ix, cursor + tam_nome * 0.12, linha)
    cursor -= 6
    c.setStrokeColor(HexColor("#555555"))
    c.setLineWidth(1)
    c.line(ix, cursor, x + w - CARD_PAD, cursor)
    cursor -= 10

    c.setFillColor(HexColor("#1A1A1A"))
    c.setFont(FONTE_INFO, TAM_INFO)
    for icone, linhas in infos:
        cursor -= 20
        _icone(c, icone, ix + 8, cursor, tema)
        ty = cursor - 4.5 + (len(linhas) - 1) * 7.5
        for linha in linhas:
            c.drawString(ix + 26, ty, linha)
            ty -= 15
        cursor -= 15 * (len(linhas) - 1) + 22


def _pagina_pessoas(c: canvas.Canvas, par: list, tema: Tema):
    _fundo_dividido(c, tema.escuro, tema.claro)
    for i, pessoa in enumerate(par):
        _card(c, pessoa, i * METADE, tema)


def _nome_evento(c: canvas.Canvas, titulo: str, tema: Tema):
    """Nome do evento centralizado na metade esquerda, reduzindo a fonte até caber em 3 linhas."""
    largura = METADE - 2 * 60
    tamanho = 40.0
    linhas = _quebrar(titulo, FONTE_TITULO, tamanho, largura)
    while tamanho > 14 and (
        len(linhas) > 3
        or max(pdfmetrics.stringWidth(l, FONTE_TITULO, tamanho) for l in linhas) > largura
    ):
        tamanho -= 1
        linhas = _quebrar(titulo, FONTE_TITULO, tamanho, largura)
    entre_linhas = tamanho * 1.15
    # Primeira linha posicionada para o bloco ficar centralizado na vertical.
    y = H / 2 + (len(linhas) - 1) * entre_linhas / 2 - tamanho * 0.35
    c.setFillColor(HexColor(tema.claro))
    c.setFont(FONTE_TITULO, tamanho)
    for linha in linhas:
        c.drawCentredString(METADE / 2, y, linha)
        y -= entre_linhas


def _pagina_final(c: canvas.Canvas, titulo: str, tema: Tema):
    _fundo_dividido(c, tema.escuro, tema.claro)
    if titulo.strip():
        _nome_evento(c, titulo.strip(), tema)
    _logo(c, tema, METADE + (W - METADE) / 2, H / 2, 260, 170)


def gerar_casting_pdf(titulo: str, marca: str, pessoas: list, ano: Optional[int] = None) -> BytesIO:
    """Renderiza o casting e devolve um buffer com o PDF."""
    _registrar_fontes()
    tema = TEMAS.get(marca, TEMAS["xingu"])
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(W, H))
    c.setTitle(f"Casting - {titulo}")

    _capa(c, tema, ano or datetime.now().year)
    c.showPage()
    for i in range(0, len(pessoas), 2):
        _pagina_pessoas(c, pessoas[i:i + 2], tema)
        c.showPage()
    _pagina_final(c, titulo, tema)
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
