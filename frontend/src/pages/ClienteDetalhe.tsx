import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus, Upload, ImageOff, Pencil } from "lucide-react";
import { api, API_URL, Cliente, OrcamentoResumo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { StatusBadge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatBRL, formatData } from "@/lib/format";

export default function ClienteDetalhe() {
  const { id } = useParams();
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [orcamentos, setOrcamentos] = useState<OrcamentoResumo[]>([]);
  const [logoVersao, setLogoVersao] = useState(Date.now());
  const [editAberto, setEditAberto] = useState(false);
  const [form, setForm] = useState<Partial<Cliente>>({});
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get(`/api/clientes/${id}`).then((r) => setCliente(r.data));
    api.get(`/api/orcamentos?cliente_id=${id}`).then((r) => setOrcamentos(r.data));
  }, [id]);

  function abrirEdicao() {
    if (cliente) setForm(cliente);
    setEditAberto(true);
  }

  async function salvarEdicao() {
    if (!form.razao_social?.trim()) return;
    const { data } = await api.put(`/api/clientes/${id}`, form);
    setCliente(data);
    setEditAberto(false);
  }

  async function enviarLogo(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await api.post(`/api/clientes/${id}/logo`, fd);
    setCliente(data);
    setLogoVersao(Date.now());
  }

  async function removerLogo() {
    const { data } = await api.delete(`/api/clientes/${id}/logo`);
    setCliente(data);
  }

  if (!cliente) return <div className="text-muted-foreground">Carregando...</div>;

  const info: [string, string][] = [
    ["Endereço", cliente.endereco],
    ["CNPJ / CPF", cliente.cnpj_cpf],
    ["Inscrição estadual", cliente.inscricao_estadual],
    ["Telefone", cliente.telefone],
    ["Contato comercial", cliente.contato_comercial],
  ];

  return (
    <div className="space-y-6">
      <Link to="/clientes" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Voltar para agências
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{cliente.razao_social}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={abrirEdicao}>
            <Pencil className="h-4 w-4" /> Editar
          </Button>
          <Button asChild>
            <Link to={`/orcamentos/novo?cliente=${cliente.id}`}>
              <Plus className="h-4 w-4" /> Novo orçamento
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          {info.map(([label, valor]) => (
            <div key={label}>
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
              <div className="font-medium">{valor || "—"}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-6 p-6">
          {cliente.logo_path ? (
            <img
              src={`${API_URL}/static/${cliente.logo_path}?v=${logoVersao}`}
              alt="Logo da agência"
              className="h-20 w-32 rounded-lg border object-contain p-2"
            />
          ) : (
            <div className="flex h-20 w-32 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
              <ImageOff className="h-6 w-6" />
            </div>
          )}
          <div>
            <div className="font-medium">Logo da agência</div>
            <p className="mb-3 text-sm text-muted-foreground">
              Aparece no cabeçalho do PDF dos orçamentos desta agência.
            </p>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={enviarLogo} />
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => fileRef.current?.click()}>
                <Upload className="h-4 w-4" /> {cliente.logo_path ? "Trocar" : "Enviar"} logo
              </Button>
              {cliente.logo_path && (
                <Button variant="ghost" onClick={removerLogo}>
                  Remover
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="border-b px-6 py-4 font-medium">
            Orçamentos desta agência ({orcamentos.length})
          </div>
          {orcamentos.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Nenhum orçamento para esta agência.
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Número</TH>
                  <TH>Cliente</TH>
                  <TH>Evento</TH>
                  <TH>Status</TH>
                  <TH className="text-right">Previsão</TH>
                  <TH>Data</TH>
                </TR>
              </THead>
              <TBody>
                {orcamentos.map((o) => (
                  <TR key={o.id}>
                    <TD>
                      <Link to={`/orcamentos/${o.id}`} className="font-medium text-primary">
                        {o.numero}
                      </Link>
                    </TD>
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

      <Dialog open={editAberto} onOpenChange={setEditAberto}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar agência</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            {(
              [
                ["razao_social", "Razão social *"],
                ["endereco", "Endereço"],
                ["cnpj_cpf", "CNPJ / CPF"],
                ["inscricao_estadual", "Inscrição estadual"],
                ["telefone", "Telefone"],
                ["contato_comercial", "Contato comercial"],
              ] as [keyof Cliente, string][]
            ).map(([k, label]) => (
              <div
                key={k}
                className={
                  k === "razao_social" || k === "endereco"
                    ? "sm:col-span-2 space-y-2"
                    : "space-y-2"
                }
              >
                <Label>{label}</Label>
                <Input
                  value={(form[k] as string) || ""}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditAberto(false)}>
              Cancelar
            </Button>
            <Button onClick={salvarEdicao}>Salvar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
