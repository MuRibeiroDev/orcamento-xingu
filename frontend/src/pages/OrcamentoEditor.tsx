import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, FileDown, Copy, Save } from "lucide-react";
import { api, API_URL, Cliente, CatalogoItem, OrcamentoItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CurrencyInput } from "@/components/ui/currency-input";
import { NumberInput } from "@/components/ui/number-input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formatBRL } from "@/lib/format";

interface Estado {
  cliente_id: number | null;
  cliente_nome: string;
  evento_nome: string;
  evento_data: string;
  evento_local: string;
  encargos_percentual: number;
  data_entrega: string;
  especificacoes: string;
  vencimento: string;
  prazo: string;
  validade: string;
  status: string;
  nota_percentual: number;
  pago: boolean;
  data_pagamento: string | null;
  itens: OrcamentoItem[];
}

const inicial: Estado = {
  cliente_id: null,
  cliente_nome: "",
  evento_nome: "",
  evento_data: "",
  evento_local: "",
  encargos_percentual: 15,
  data_entrega: "",
  especificacoes: "",
  vencimento: "",
  prazo: "",
  validade: "",
  status: "rascunho",
  nota_percentual: 0,
  pago: false,
  data_pagamento: null,
  itens: [],
};

/** Data de hoje no formato do input date (AAAA-MM-DD), no fuso local. */
function hojeISO(): string {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function calcLinha(it: OrcamentoItem, encOrc: number) {
  const perc = it.encargos_percentual ?? encOrc;
  const total = (it.quantidade || 0) * (it.diarias || 0) * (it.valor_unitario || 0);
  const encargos = total * (perc / 100);
  return { total, encargos, total_final: total + encargos };
}

export default function OrcamentoEditor() {
  const { id } = useParams();
  const editando = Boolean(id);
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [catalogo, setCatalogo] = useState<CatalogoItem[]>([]);
  const [numero, setNumero] = useState("");
  const [estado, setEstado] = useState<Estado>(inicial);
  const [salvando, setSalvando] = useState(false);
  const [orientacao, setOrientacao] = useState("landscape");

  const agenciaSelecionada = clientes.find((c) => c.id === estado.cliente_id);
  const agenciaTemLogo = Boolean(agenciaSelecionada?.logo_path);

  useEffect(() => {
    api.get("/api/clientes").then((r) => setClientes(r.data));
    api.get("/api/catalogo").then((r) => setCatalogo(r.data));
    api.get("/api/config").then((r) =>
      setEstado((s) =>
        editando
          ? s
          : { ...s, encargos_percentual: r.data.encargos_padrao, nota_percentual: r.data.nota_padrao ?? 0 }
      )
    );
    if (editando) {
      api.get(`/api/orcamentos/${id}`).then((r) => {
        const o = r.data;
        setNumero(o.numero);
        setEstado({
          cliente_id: o.cliente_id,
          cliente_nome: o.cliente_nome,
          evento_nome: o.evento_nome,
          evento_data: o.evento_data,
          evento_local: o.evento_local,
          encargos_percentual: o.encargos_percentual,
          data_entrega: o.data_entrega,
          especificacoes: o.especificacoes,
          vencimento: o.vencimento,
          prazo: o.prazo,
          validade: o.validade,
          status: o.status,
          nota_percentual: o.nota_percentual ?? 0,
          pago: Boolean(o.pago),
          data_pagamento: o.data_pagamento,
          itens: o.itens,
        });
      });
    } else {
      const cli = params.get("cliente");
      if (cli) setEstado((s) => ({ ...s, cliente_id: Number(cli) }));
    }
  }, [id]);

  const calculo = useMemo(() => {
    let total = 0,
      encargos = 0,
      final = 0,
      custo = 0;
    const linhas = estado.itens.map((it) => {
      const c = calcLinha(it, estado.encargos_percentual);
      total += c.total;
      encargos += c.encargos;
      final += c.total_final;
      // Linhas sem custo (ex.: mão de obra) contam inteiras como lucro.
      if (!it.sem_custo) custo += c.total;
      return c;
    });
    const lucroBruto = final - custo;
    const nota = final * ((estado.nota_percentual || 0) / 100);
    return {
      linhas,
      total,
      encargos,
      previsao: final,
      custo,
      lucroBruto,
      nota,
      recebimentoLiquido: final - nota,
      lucroLiquido: lucroBruto - nota,
    };
  }, [estado.itens, estado.encargos_percentual, estado.nota_percentual]);

  function set<K extends keyof Estado>(k: K, v: Estado[K]) {
    setEstado((s) => ({ ...s, [k]: v }));
  }

  function marcarPago(pago: boolean) {
    setEstado((s) => ({ ...s, pago, data_pagamento: pago ? s.data_pagamento || hojeISO() : null }));
  }

  function setItem(idx: number, patch: Partial<OrcamentoItem>) {
    setEstado((s) => {
      const itens = [...s.itens];
      itens[idx] = { ...itens[idx], ...patch };
      return { ...s, itens };
    });
  }

  function novaLinha() {
    set("itens", [
      ...estado.itens,
      {
        item: "",
        descritivo: "",
        quantidade: 1,
        diarias: 1,
        valor_unitario: 0,
        encargos_percentual: null,
        ordem: estado.itens.length,
        sem_custo: false,
      },
    ]);
  }

  function adicionarDoCatalogo(catId: string) {
    const c = catalogo.find((x) => x.id === Number(catId));
    if (!c) return;
    set("itens", [
      ...estado.itens,
      {
        item: c.nome,
        descritivo: c.descritivo,
        quantidade: c.quantidade_sugerida,
        diarias: c.diarias_sugeridas,
        valor_unitario: c.valor_unitario_padrao,
        encargos_percentual: null,
        ordem: estado.itens.length,
        sem_custo: Boolean(c.sem_custo),
      },
    ]);
  }

  function removerLinha(idx: number) {
    set(
      "itens",
      estado.itens.filter((_, i) => i !== idx)
    );
  }

  async function salvar(): Promise<number | null> {
    if (!estado.cliente_id) {
      alert("Selecione uma agência.");
      return null;
    }
    setSalvando(true);
    try {
      const payload = { ...estado };
      if (editando) {
        await api.put(`/api/orcamentos/${id}`, payload);
        return Number(id);
      } else {
        const { data } = await api.post("/api/orcamentos", payload);
        navigate(`/orcamentos/${data.id}`, { replace: true });
        return data.id;
      }
    } finally {
      setSalvando(false);
    }
  }

  async function gerarPdf() {
    const oid = await salvar();
    if (!oid) return;
    const resp = await api.get(`/api/orcamentos/${oid}/pdf?orientacao=${orientacao}`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(resp.data);
    window.open(url, "_blank");
  }

  async function duplicar() {
    if (!editando) return;
    const { data } = await api.post(`/api/orcamentos/${id}/duplicar`);
    navigate(`/orcamentos/${data.id}`);
  }

  async function excluir() {
    if (!editando) return;
    if (!confirm("Excluir este orçamento?")) return;
    await api.delete(`/api/orcamentos/${id}`);
    navigate("/");
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Voltar
      </button>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">
            {editando ? numero : "Novo orçamento"}
          </h1>
          <p className="text-muted-foreground">Preencha os dados e gere o PDF</p>
        </div>
        <div className="flex gap-2">
          {editando && (
            <>
              <Button variant="outline" onClick={duplicar}>
                <Copy className="h-4 w-4" /> Duplicar
              </Button>
              <Button variant="outline" onClick={excluir}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </>
          )}
          <Button variant="outline" onClick={salvar} disabled={salvando}>
            <Save className="h-4 w-4" /> Salvar
          </Button>
          <Select
            className="w-32"
            value={orientacao}
            onChange={(e) => setOrientacao(e.target.value)}
            title="Orientação do PDF"
          >
            <option value="landscape">Horizontal</option>
            <option value="portrait">Vertical</option>
          </Select>
          <Button onClick={gerarPdf}>
            <FileDown className="h-4 w-4" /> Gerar PDF
          </Button>
        </div>
      </div>

      {/* Dados do cliente e evento */}
      <Card>
        <CardContent className="grid gap-4 p-6 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Agência *</Label>
            <Select
              value={estado.cliente_id ?? ""}
              onChange={(e) => set("cliente_id", e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Selecione...</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.razao_social}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Cliente</Label>
            <Input
              placeholder="Nome do cliente final"
              value={estado.cliente_nome}
              onChange={(e) => set("cliente_nome", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Status</Label>
            <Select value={estado.status} onChange={(e) => set("status", e.target.value)}>
              <option value="rascunho">Rascunho</option>
              <option value="enviado">Enviado</option>
              <option value="aprovado">Aprovado</option>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Nome do evento</Label>
            <Input value={estado.evento_nome} onChange={(e) => set("evento_nome", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Local</Label>
            <Input value={estado.evento_local} onChange={(e) => set("evento_local", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Data do evento</Label>
            <Input
              placeholder="ex: 26 a 30 de maio de 2026 - 10h às 18h"
              value={estado.evento_data}
              onChange={(e) => set("evento_data", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Validade da proposta</Label>
            <Input
              placeholder="ex: Proposta válida por 15 dias"
              value={estado.validade}
              onChange={(e) => set("validade", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Encargos padrão deste orçamento (%)</Label>
            <NumberInput
              value={estado.encargos_percentual}
              onChange={(v) => set("encargos_percentual", v)}
            />
          </div>
          <div className="space-y-1 md:col-span-2">
            <Label>Logo do cabeçalho do PDF</Label>
            <p className="text-sm text-muted-foreground">
              {agenciaTemLogo
                ? `Será usada a logo da agência ${agenciaSelecionada?.razao_social}.`
                : "Esta agência não tem logo cadastrada — será usada a logo padrão (XINGU). Para usar a logo dela, cadastre em Agências → abrir agência → Enviar logo."}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Itens */}
      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">Itens do orçamento</h2>
            <div className="flex gap-2">
              <Select className="w-56" value="" onChange={(e) => adicionarDoCatalogo(e.target.value)}>
                <option value="">+ Adicionar do catálogo</option>
                {catalogo.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome} — {formatBRL(c.valor_unitario_padrao)}
                  </option>
                ))}
              </Select>
              <Button variant="outline" onClick={novaLinha}>
                <Plus className="h-4 w-4" /> Linha em branco
              </Button>
            </div>
          </div>

          {estado.itens.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              Nenhum item. Adicione do catálogo ou crie uma linha em branco.
            </div>
          ) : (
            <div className="space-y-3">
              {estado.itens.map((it, idx) => {
                const c = calculo.linhas[idx];
                return (
                  <div key={idx} className="rounded-lg border p-4">
                    <div className="grid gap-3 md:grid-cols-12">
                      <div className="space-y-1 md:col-span-3">
                        <Label className="text-xs">Item</Label>
                        <Input
                          value={it.item}
                          onChange={(e) => setItem(idx, { item: e.target.value })}
                        />
                      </div>
                      <div className="space-y-1 md:col-span-9">
                        <Label className="text-xs">Descritivo</Label>
                        <Textarea
                          rows={2}
                          value={it.descritivo}
                          onChange={(e) => setItem(idx, { descritivo: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 items-end gap-3 md:grid-cols-12">
                      <div className="space-y-1 md:col-span-2">
                        <Label className="text-xs">Qtd.</Label>
                        <NumberInput
                          value={it.quantidade}
                          onChange={(v) => setItem(idx, { quantidade: v })}
                        />
                      </div>
                      <div className="space-y-1 md:col-span-2">
                        <Label className="text-xs">Diárias</Label>
                        <NumberInput
                          value={it.diarias}
                          onChange={(v) => setItem(idx, { diarias: v })}
                        />
                      </div>
                      <div className="space-y-1 md:col-span-2">
                        <Label className="text-xs">Vl. unitário</Label>
                        <CurrencyInput
                          value={it.valor_unitario}
                          onChange={(v) => setItem(idx, { valor_unitario: v })}
                        />
                      </div>
                      <div className="space-y-1 md:col-span-2">
                        <Label className="text-xs">Encargos %</Label>
                        <Input
                          type="number"
                          inputMode="decimal"
                          placeholder={String(estado.encargos_percentual)}
                          value={it.encargos_percentual ?? ""}
                          onChange={(e) =>
                            setItem(idx, {
                              encargos_percentual:
                                e.target.value.trim() === "" ? null : Number(e.target.value),
                            })
                          }
                        />
                      </div>
                      <div className="md:col-span-3">
                        <div className="text-xs text-muted-foreground">Total + encargos</div>
                        <div className="font-semibold">{formatBRL(c?.total_final || 0)}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatBRL(c?.total || 0)} + {formatBRL(c?.encargos || 0)}
                        </div>
                        <label
                          className="mt-1 flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground"
                          title="Uso interno: o valor inteiro da linha conta como lucro (não aparece no PDF)"
                        >
                          <input
                            type="checkbox"
                            className="h-3.5 w-3.5 accent-primary"
                            checked={Boolean(it.sem_custo)}
                            onChange={(e) => setItem(idx, { sem_custo: e.target.checked })}
                          />
                          Sem custo (mão de obra)
                        </label>
                      </div>
                      <div className="flex justify-end md:col-span-1">
                        <Button variant="ghost" size="icon" onClick={() => removerLinha(idx)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Totais */}
          <div className="flex justify-end border-t pt-4">
            <div className="w-full max-w-xs space-y-1 text-sm">
              <div className="flex justify-between text-muted-foreground">
                <span>Subtotal</span>
                <span>{formatBRL(calculo.total)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>Encargos</span>
                <span>{formatBRL(calculo.encargos)}</span>
              </div>
              <div className="flex justify-between border-t pt-1 text-base font-semibold">
                <span>Previsão de investimento</span>
                <span className="text-primary">{formatBRL(calculo.previsao)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Controle interno (não vai para o PDF) */}
      <Card className="border-dashed">
        <CardContent className="space-y-4 p-6">
          <div>
            <h2 className="font-semibold">Controle interno</h2>
            <p className="text-sm text-muted-foreground">Uso exclusivo do sistema — não aparece no PDF do orçamento.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Nota fiscal (%)</Label>
                <NumberInput
                  value={estado.nota_percentual}
                  onChange={(v) => set("nota_percentual", v)}
                />
              </div>
              <div className="space-y-2">
                <label className="flex cursor-pointer items-center gap-2 text-sm font-medium">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-primary"
                    checked={estado.pago}
                    onChange={(e) => marcarPago(e.target.checked)}
                  />
                  Pago
                </label>
                {estado.pago && (
                  <div className="space-y-2">
                    <Label>Data do pagamento</Label>
                    <Input
                      type="date"
                      value={estado.data_pagamento ?? ""}
                      onChange={(e) => set("data_pagamento", e.target.value || null)}
                    />
                  </div>
                )}
              </div>
            </div>
            <div className="space-y-1 rounded-lg bg-muted/50 p-4 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Faturamento</span>
                <span className="font-medium">{formatBRL(calculo.previsao)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Custo (itens com custo)</span>
                <span>{formatBRL(calculo.custo)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Lucro bruto (encargos + sem custo)</span>
                <span>{formatBRL(calculo.lucroBruto)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Nota ({estado.nota_percentual || 0}%)</span>
                <span className="text-destructive">− {formatBRL(calculo.nota)}</span>
              </div>
              <div className="flex justify-between border-t pt-1">
                <span className="text-muted-foreground">Recebimento líquido</span>
                <span className="font-medium">{formatBRL(calculo.recebimentoLiquido)}</span>
              </div>
              <div className="flex justify-between text-base font-semibold">
                <span>Lucro líquido</span>
                <span className={calculo.lucroLiquido < 0 ? "text-destructive" : "text-green-700"}>
                  {formatBRL(calculo.lucroLiquido)}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Condições */}
      <Card>
        <CardContent className="grid gap-4 p-6 md:grid-cols-2">
          <h2 className="font-semibold md:col-span-2">Condições</h2>
          <div className="space-y-2">
            <Label>Data da entrega</Label>
            <Input value={estado.data_entrega} onChange={(e) => set("data_entrega", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Vencimento</Label>
            <Input value={estado.vencimento} onChange={(e) => set("vencimento", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Prazo</Label>
            <Input value={estado.prazo} onChange={(e) => set("prazo", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Especificações</Label>
            <Input
              value={estado.especificacoes}
              onChange={(e) => set("especificacoes", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
