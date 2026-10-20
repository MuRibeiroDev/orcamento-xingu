"""Testes do controle interno: lucro x faturamento, nota fiscal e pagamento."""
from datetime import date
from io import BytesIO

from pypdf import PdfReader

from app.calc import calcular_financeiro


def _novo_orcamento(cliente, **extra):
    agencia = cliente.post("/api/clientes", json={"razao_social": "Agência Teste"}).json()
    dados = {
        "cliente_id": agencia["id"],
        "encargos_percentual": 15,
        "itens": [{"item": "Promotora", "quantidade": 2, "diarias": 5, "valor_unitario": 100}],
        **extra,
    }
    return cliente.post("/api/orcamentos", json=dados).json()


def test_calculo_separa_custo_lucro_e_nota():
    r = calcular_financeiro(custo=1000, lucro_bruto=150, nota_percentual=6)

    assert r["faturamento"] == 1150
    assert r["valor_nota"] == 69
    assert r["recebimento_liquido"] == 1081
    assert r["lucro_liquido"] == 81


def test_sem_nota_lucro_liquido_igual_ao_bruto():
    r = calcular_financeiro(custo=1000, lucro_bruto=150, nota_percentual=0)

    assert r["valor_nota"] == 0
    assert r["lucro_liquido"] == 150


def test_orcamento_retorna_valores_financeiros(cliente):
    o = _novo_orcamento(cliente, nota_percentual=6)

    assert o["custo"] == 1000
    assert o["lucro_bruto"] == 150
    assert o["faturamento"] == 1150
    assert o["valor_nota"] == 69
    assert o["lucro_liquido"] == 81
    assert o["recebimento_liquido"] == 1081


def test_marcar_como_pago_sem_data_usa_hoje(cliente):
    o = _novo_orcamento(cliente)

    o = cliente.put(f"/api/orcamentos/{o['id']}", json={"pago": True}).json()

    assert o["pago"] is True
    assert o["data_pagamento"] == date.today().isoformat()


def test_marcar_como_pago_com_data_informada(cliente):
    o = _novo_orcamento(cliente)

    o = cliente.put(f"/api/orcamentos/{o['id']}", json={"pago": True, "data_pagamento": "2026-09-15"}).json()

    assert o["data_pagamento"] == "2026-09-15"


def test_desmarcar_pago_limpa_data(cliente):
    o = _novo_orcamento(cliente, pago=True, data_pagamento="2026-09-15")

    o = cliente.put(f"/api/orcamentos/{o['id']}", json={"pago": False}).json()

    assert o["pago"] is False
    assert o["data_pagamento"] is None


def test_listagem_traz_pagamento_e_lucro(cliente):
    o = _novo_orcamento(cliente, nota_percentual=6, pago=True, data_pagamento="2026-09-15")

    item = next(x for x in cliente.get("/api/orcamentos").json() if x["id"] == o["id"])

    assert item["pago"] is True
    assert item["data_pagamento"] == "2026-09-15"
    assert item["faturamento"] == 1150
    assert item["lucro_liquido"] == 81


def test_nota_invalida_retorna_422(cliente):
    o = _novo_orcamento(cliente)

    r = cliente.put(f"/api/orcamentos/{o['id']}", json={"nota_percentual": 150})

    assert r.status_code == 422


def test_pdf_do_orcamento_nao_mostra_controle_interno(cliente):
    o = _novo_orcamento(cliente, nota_percentual=6, pago=True)

    r = cliente.get(f"/api/orcamentos/{o['id']}/pdf")

    texto = " ".join(p.extract_text() for p in PdfReader(BytesIO(r.content)).pages).lower()
    assert "lucro" not in texto
    assert "nota" not in texto
    assert "pago" not in texto


def test_item_sem_custo_conta_valor_inteiro_como_lucro(cliente):
    agencia = cliente.post("/api/clientes", json={"razao_social": "Agência Sem Custo"}).json()
    o = cliente.post("/api/orcamentos", json={
        "cliente_id": agencia["id"],
        "encargos_percentual": 15,
        "nota_percentual": 6,
        "itens": [
            {"item": "Aluguel estande", "quantidade": 1, "diarias": 1, "valor_unitario": 1000},
            {"item": "Mão de obra", "quantidade": 1, "diarias": 1, "valor_unitario": 1000, "sem_custo": True},
        ],
    }).json()

    assert o["faturamento"] == 2300
    assert o["custo"] == 1000            # só o aluguel
    assert o["lucro_bruto"] == 1300      # 150 + 150 de encargos + 1000 da mão de obra
    assert o["valor_nota"] == 138
    assert o["lucro_liquido"] == 1162
    assert [i["sem_custo"] for i in o["itens"]] == [False, True]


def test_catalogo_guarda_padrao_sem_custo(cliente):
    item = cliente.post("/api/catalogo", json={"nome": "Mão de obra", "sem_custo": True}).json()

    assert item["sem_custo"] is True


def test_duplicar_mantem_sem_custo(cliente):
    agencia = cliente.post("/api/clientes", json={"razao_social": "Agência Dup"}).json()
    o = cliente.post("/api/orcamentos", json={
        "cliente_id": agencia["id"],
        "itens": [{"item": "Mão de obra", "quantidade": 1, "diarias": 1, "valor_unitario": 100, "sem_custo": True}],
    }).json()

    copia = cliente.post(f"/api/orcamentos/{o['id']}/duplicar").json()

    assert copia["itens"][0]["sem_custo"] is True
