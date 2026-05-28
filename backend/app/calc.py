"""Funções de cálculo dos orçamentos. Fonte única da verdade para a matemática."""


def encargos_da_linha(item, encargos_orcamento: float) -> float:
    """Percentual de encargos efetivo da linha (override da linha ou o do orçamento)."""
    if item.encargos_percentual is not None:
        return item.encargos_percentual
    return encargos_orcamento


def calcular_linha(item, encargos_orcamento: float) -> dict:
    """Calcula os valores de uma linha de item.

    total       = quantidade * diárias * valor unitário
    encargos    = total * (percentual / 100)
    total_final = total + encargos
    """
    quantidade = item.quantidade or 0
    diarias = item.diarias or 0
    valor_unitario = item.valor_unitario or 0
    perc = encargos_da_linha(item, encargos_orcamento)

    total = quantidade * diarias * valor_unitario
    encargos = total * (perc / 100.0)
    total_final = total + encargos
    return {
        "total": round(total, 2),
        "encargos_percentual_efetivo": perc,
        "encargos": round(encargos, 2),
        "total_final": round(total_final, 2),
    }


def calcular_orcamento(orcamento) -> dict:
    """Calcula todas as linhas e a previsão de investimento (soma dos totais finais)."""
    linhas = []
    soma_total = 0.0
    soma_encargos = 0.0
    soma_final = 0.0
    for item in orcamento.itens:
        c = calcular_linha(item, orcamento.encargos_percentual)
        linhas.append({"id": item.id, **c})
        soma_total += c["total"]
        soma_encargos += c["encargos"]
        soma_final += c["total_final"]
    return {
        "linhas": linhas,
        "soma_total": round(soma_total, 2),
        "soma_encargos": round(soma_encargos, 2),
        "previsao_investimento": round(soma_final, 2),
    }


def formatar_brl(valor: float) -> str:
    """Formata um número no padrão monetário brasileiro: 1.234,56."""
    s = f"{(valor or 0):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
