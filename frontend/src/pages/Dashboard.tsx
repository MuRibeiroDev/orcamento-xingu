import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, FileText, Users, Package } from "lucide-react";
import { api, OrcamentoResumo, Cliente, CatalogoItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { StatusBadge } from "@/components/ui/badge";
import { formatBRL, formatData } from "@/lib/format";

export default function Dashboard() {
  const [orcamentos, setOrcamentos] = useState<OrcamentoResumo[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [catalogo, setCatalogo] = useState<CatalogoItem[]>([]);

  useEffect(() => {
    api.get("/api/orcamentos").then((r) => setOrcamentos(r.data));
    api.get("/api/clientes").then((r) => setClientes(r.data));
    api.get("/api/catalogo").then((r) => setCatalogo(r.data));
  }, []);

  const totalAprovado = orcamentos
    .filter((o) => o.status === "aprovado")
    .reduce((s, o) => s + o.previsao_investimento, 0);

  const cards = [
    { label: "Orçamentos", valor: orcamentos.length, icon: FileText },
    { label: "Agências", valor: clientes.length, icon: Users },
    { label: "Itens no catálogo", valor: catalogo.length, icon: Package },
    { label: "Total aprovado", valor: formatBRL(totalAprovado), icon: FileText },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
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

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label}>
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-lg bg-primary/10 p-3 text-primary">
                <c.icon className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xl font-semibold">{c.valor}</div>
                <div className="text-xs text-muted-foreground">{c.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="border-b px-6 py-4 font-medium">Orçamentos recentes</div>
          {orcamentos.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Nenhum orçamento ainda. Crie o primeiro!
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
                  <TH className="text-right">Previsão</TH>
                  <TH>Data</TH>
                </TR>
              </THead>
              <TBody>
                {orcamentos.slice(0, 10).map((o) => (
                  <TR key={o.id} className="cursor-pointer">
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
                    <TD className="text-right font-medium">{formatBRL(o.previsao_investimento)}</TD>
                    <TD className="text-muted-foreground">{formatData(o.created_at)}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
