import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Plus, FileText, CircleDollarSign, TrendingUp, Receipt, Wallet, Check, ChevronLeft, ChevronRight } from "lucide-react";
import { api, OrcamentoResumo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { StatusBadge } from "@/components/ui/badge";
import { formatBRL, formatData } from "@/lib/format";

const POR_PAGINA = 10;

type Periodo = "mes" | "mes_passado" | "ano" | "tudo" | "personalizado";

const PERIODOS: { valor: Periodo; label: string }[] = [
  { valor: "mes", label: "Este mês" },
  { valor: "mes_passado", label: "Mês passado" },
  { valor: "ano", label: "Este ano" },
  { valor: "tudo", label: "Todo o período" },
  { valor: "personalizado", label: "Personalizado" },
];

/** Data local no formato AAAA-MM-DD. */
function iso(d: Date): string {
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

/** Intervalo [de, ate] (AAAA-MM-DD, inclusivo) do período; vazio = sem limite. */
function intervalo(periodo: Periodo, de: string, ate: string): [string, string] {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = hoje.getMonth();
  switch (periodo) {
    case "mes":
      return [iso(new Date(ano, mes, 1)), iso(new Date(ano, mes + 1, 0))];
    case "mes_passado":
      return [iso(new Date(ano, mes - 1, 1)), iso(new Date(ano, mes, 0))];
    case "ano":
      return [`${ano}-01-01`, `${ano}-12-31`];
    case "personalizado":
      return [de, ate];
    default:
      return ["", ""];
  }
}

function dentro(data: string | null, [de, ate]: [string, string]): boolean {
  if (!data) return false;
  const dia = data.slice(0, 10);
  return (!de || dia >= de) && (!ate || dia <= ate);
}

function soma(lista: OrcamentoResumo[], campo: keyof OrcamentoResumo): number {
  return lista.reduce((s, o) => s + (Number(o[campo]) || 0), 0);
}

export default function Dashboard() {
  const [orcamentos, setOrcamentos] = useState<OrcamentoResumo[]>([]);
  const [params, setParams] = useSearchParams();
  const periodo = (params.get("periodo") as Periodo) || "mes";
  const de = params.get("de") ?? "";
  const ate = params.get("ate") ?? "";

  function carregar() {
    api.get("/api/orcamentos").then((r) => setOrcamentos(r.data));
  }
  useEffect(carregar, []);

  function setFiltro(patch: Record<string, string>) {
    const novo = new URLSearchParams(params);
    // Mudar o filtro volta para a primeira página.
    if (!("pagina" in patch)) novo.delete("pagina");
    Object.entries(patch).forEach(([k, v]) => (v ? novo.set(k, v) : novo.delete(k)));
    setParams(novo, { replace: true });
  }

  async function marcarPago(o: OrcamentoResumo) {
    await api.put(`/api/orcamentos/${o.id}`, { pago: true });
    carregar();
  }

  const faixa = intervalo(periodo, de, ate);
  // Orçamentos contam pela data de criação; pagos (faturamento/lucro) pela data do pagamento.
  const criados = orcamentos.filter((o) => dentro(o.created_at, faixa));
  const pagos = orcamentos.filter((o) => o.pago && dentro(o.data_pagamento, faixa));
  const totalPaginas = Math.max(1, Math.ceil(criados.length / POR_PAGINA));
  const pagina = Math.min(Math.max(1, Number(params.get("pagina")) || 1), totalPaginas);
  const inicio = (pagina - 1) * POR_PAGINA;
  const daPagina = criados.slice(inicio, inicio + POR_PAGINA);
  const irPara = (n: number) => setFiltro({ pagina: n > 1 ? String(n) : "" });
  const lucroBruto = soma(pagos, "lucro_bruto");
  const notas = soma(pagos, "valor_nota");

  const cards = [
    {
      label: "Orçamentos criados",
      valor: String(criados.length),
      detalhe: `${criados.filter((o) => o.status === "aprovado").length} aprovados`,
      icon: FileText,
    },
    {
      label: "Pagos · faturamento",
      valor: formatBRL(soma(pagos, "faturamento")),
      detalhe: `${pagos.length} orçamento(s) pago(s)`,
      icon: CircleDollarSign,
    },
    { label: "Lucro bruto", valor: formatBRL(lucroBruto), detalhe: "encargos dos pagos", icon: TrendingUp },
    { label: "Notas fiscais", valor: formatBRL(notas), detalhe: "descontado do recebimento", icon: Receipt },
    {
      label: "Lucro líquido",
      valor: formatBRL(lucroBruto - notas),
      detalhe: `recebido líquido ${formatBRL(soma(pagos, "recebimento_liquido"))}`,
      icon: Wallet,
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Início</h1>
          <p className="text-muted-foreground">Visão geral dos seus orçamentos</p>
        </div>
        <Button asChild>
          <Link to="/orcamentos/novo">
            <Plus className="h-4 w-4" /> Novo orçamento
          </Link>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Select
          className="w-48"
          value={periodo}
          onChange={(e) => setFiltro({ periodo: e.target.value })}
          aria-label="Período"
        >
          {PERIODOS.map((p) => (
            <option key={p.valor} value={p.valor}>
              {p.label}
            </option>
          ))}
        </Select>
        {periodo === "personalizado" && (
          <>
            <Input type="date" className="w-44" value={de} onChange={(e) => setFiltro({ de: e.target.value })} aria-label="De" />
            <span className="text-sm text-muted-foreground">até</span>
            <Input type="date" className="w-44" value={ate} onChange={(e) => setFiltro({ ate: e.target.value })} aria-label="Até" />
          </>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {cards.map((c) => (
          <Card key={c.label}>
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <c.icon className="h-4 w-4 text-primary" />
                {c.label}
              </div>
              <div>
                <div className="text-xl font-semibold">{c.valor}</div>
                <div className="text-xs text-muted-foreground">{c.detalhe}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="border-b px-6 py-4 font-medium">Orçamentos do período ({criados.length})</div>
          {criados.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Nenhum orçamento criado neste período.
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Número</TH>
                  <TH>Agência</TH>
                  <TH>Cliente</TH>
                  <TH>Evento</TH>
                  <TH>Status</TH>
                  <TH className="text-right">Faturamento</TH>
                  <TH className="text-right">Lucro líq.</TH>
                  <TH>Pagamento</TH>
                  <TH>Data</TH>
                </TR>
              </THead>
              <TBody>
                {daPagina.map((o) => (
                  <TR key={o.id}>
                    <TD>
                      <Link to={`/orcamentos/${o.id}`} className="font-medium text-primary">
                        {o.numero}
                      </Link>
                    </TD>
                    <TD>{o.cliente_razao_social}</TD>
                    <TD>{o.cliente_nome || "—"}</TD>
                    <TD className="text-muted-foreground">{o.evento_nome || "—"}</TD>
                    <TD>
                      <StatusBadge status={o.status} />
                    </TD>
                    <TD className="text-right font-medium">{formatBRL(o.faturamento)}</TD>
                    <TD className="text-right">{formatBRL(o.lucro_liquido)}</TD>
                    <TD>
                      {o.pago ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                          <Check className="h-3 w-3" /> Pago {o.data_pagamento && formatData(`${o.data_pagamento}T12:00:00`)}
                        </span>
                      ) : (
                        <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => marcarPago(o)}>
                          Marcar como pago
                        </Button>
                      )}
                    </TD>
                    <TD className="text-muted-foreground">{formatData(o.created_at)}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
          {criados.length > POR_PAGINA && (
            <div className="flex items-center justify-between border-t px-6 py-3 text-sm">
              <span className="text-muted-foreground">
                Mostrando {inicio + 1}–{Math.min(inicio + POR_PAGINA, criados.length)} de {criados.length}
              </span>
              <div className="flex items-center gap-1">
                <Button variant="outline" size="sm" disabled={pagina === 1} onClick={() => irPara(pagina - 1)}>
                  <ChevronLeft className="h-4 w-4" /> Anterior
                </Button>
                {Array.from({ length: totalPaginas }, (_, i) => i + 1)
                  .filter((n) => n === 1 || n === totalPaginas || Math.abs(n - pagina) <= 1)
                  .map((n, i, lista) => (
                    <span key={n} className="flex items-center gap-1">
                      {i > 0 && n - lista[i - 1] > 1 && <span className="px-1 text-muted-foreground">…</span>}
                      <Button
                        variant={n === pagina ? "default" : "ghost"}
                        size="sm"
                        className="w-9 px-0"
                        onClick={() => irPara(n)}
                        aria-current={n === pagina ? "page" : undefined}
                      >
                        {n}
                      </Button>
                    </span>
                  ))}
                <Button variant="outline" size="sm" disabled={pagina === totalPaginas} onClick={() => irPara(pagina + 1)}>
                  Próxima <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
