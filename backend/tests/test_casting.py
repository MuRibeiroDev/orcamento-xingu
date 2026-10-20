"""Testes de integração do casting: modelos, fotos, castings e PDF."""
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader

from app import casting_pdf
from app.routers import modelos as rota_modelos


@pytest.fixture(autouse=True)
def static_temporario(monkeypatch, tmp_path):
    monkeypatch.setattr(rota_modelos, "STATIC_DIR", str(tmp_path))
    monkeypatch.setattr(casting_pdf, "STATIC_DIR", str(tmp_path))
    return tmp_path


def _imagem(cor="red", tamanho=(600, 900), formato="PNG") -> bytes:
    buf = BytesIO()
    Image.new("RGB", tamanho, cor).save(buf, formato)
    return buf.getvalue()


def _nova_modelo(cliente, nome="Luiza Batista", fotos=0):
    m = cliente.post("/api/modelos", json={
        "nome": nome, "idade": "20", "manequim": "38/40", "altura": "1,67",
        "destaque": "Belo Horizonte - MG",
    }).json()
    for _ in range(fotos):
        m = cliente.post(f"/api/modelos/{m['id']}/fotos", files={"file": ("f.png", _imagem())}).json()
    return m


def test_upload_converte_foto_para_jpeg(cliente, static_temporario):
    m = _nova_modelo(cliente, fotos=1)

    assert len(m["fotos"]) == 1
    arquivo = m["fotos"][0]["arquivo"]
    assert arquivo.startswith("modelos/") and arquivo.endswith(".jpg")
    assert (static_temporario / arquivo).exists()


def test_upload_rejeita_arquivo_que_nao_e_imagem(cliente):
    m = _nova_modelo(cliente)

    r = cliente.post(f"/api/modelos/{m['id']}/fotos", files={"file": ("x.png", b"nao e imagem")})

    assert r.status_code == 400


def test_limite_de_4_fotos_por_modelo(cliente):
    m = _nova_modelo(cliente, fotos=4)

    r = cliente.post(f"/api/modelos/{m['id']}/fotos", files={"file": ("f.png", _imagem())})

    assert r.status_code == 400


def test_reordenar_e_remover_foto(cliente, static_temporario):
    m = _nova_modelo(cliente, fotos=3)
    ids = [f["id"] for f in m["fotos"]]

    m = cliente.put(f"/api/modelos/{m['id']}/fotos/ordem", json=list(reversed(ids))).json()
    assert [f["id"] for f in m["fotos"]] == list(reversed(ids))

    arquivo = m["fotos"][0]["arquivo"]
    m = cliente.delete(f"/api/modelos/{m['id']}/fotos/{m['fotos'][0]['id']}").json()
    assert len(m["fotos"]) == 2
    assert not (static_temporario / arquivo).exists()


def test_casting_rejeita_marca_invalida(cliente):
    r = cliente.post("/api/castings", json={"titulo": "X", "marca": "outra", "modelo_ids": []})

    assert r.status_code == 422


@pytest.mark.parametrize("marca", ["xingu", "boom"])
def test_pdf_tem_capa_paginas_de_2_pessoas_e_final(cliente, marca):
    ids = [_nova_modelo(cliente, nome=f"Pessoa {i}", fotos=i % 5)["id"] for i in range(5)]
    casting = cliente.post("/api/castings", json={
        "titulo": "SIC - CRESOL", "marca": marca, "modelo_ids": ids,
    }).json()

    r = cliente.get(f"/api/castings/{casting['id']}/pdf")

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert 'filename="Casting_SIC-CRESOL.pdf"' in r.headers["content-disposition"]
    # capa + 3 páginas (5 pessoas, 2 por página) + página final
    assert len(PdfReader(BytesIO(r.content)).pages) == 5


def test_casting_mantem_ordem_e_ignora_repetidas(cliente):
    a, b = _nova_modelo(cliente, "A")["id"], _nova_modelo(cliente, "B")["id"]

    c = cliente.post("/api/castings", json={"titulo": "T", "modelo_ids": [b, a, b]}).json()

    assert [m["id"] for m in c["modelos"]] == [b, a]


def test_excluir_modelo_remove_do_casting(cliente):
    a, b = _nova_modelo(cliente, "A")["id"], _nova_modelo(cliente, "B")["id"]
    c = cliente.post("/api/castings", json={"titulo": "T", "modelo_ids": [a, b]}).json()

    cliente.delete(f"/api/modelos/{a}")

    c = cliente.get(f"/api/castings/{c['id']}").json()
    assert [m["id"] for m in c["modelos"]] == [b]


def test_casting_com_modelo_inexistente_retorna_400(cliente):
    r = cliente.post("/api/castings", json={"titulo": "T", "modelo_ids": [99999]})

    assert r.status_code == 400
