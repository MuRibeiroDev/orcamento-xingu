import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { api, Cliente } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const vazio: Partial<Cliente> = {
  razao_social: "",
  endereco: "",
  cnpj_cpf: "",
  inscricao_estadual: "",
  telefone: "",
  contato_comercial: "",
};

export default function Clientes() {
  const navigate = useNavigate();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState<Partial<Cliente>>(vazio);

  function carregar() {
    api.get("/api/clientes").then((r) => setClientes(r.data));
  }
  useEffect(carregar, []);

  function abrirNovo() {
    setForm(vazio);
    setAberto(true);
  }
  function abrirEdicao(c: Cliente, e: React.MouseEvent) {
    e.stopPropagation();
    setForm(c);
    setAberto(true);
  }

  async function salvar() {
    if (!form.razao_social?.trim()) return;
    if (form.id) await api.put(`/api/clientes/${form.id}`, form);
    else await api.post("/api/clientes", form);
    setAberto(false);
    carregar();
  }

  async function excluir(c: Cliente, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Excluir a agência "${c.razao_social}" e todos os seus orçamentos?`)) return;
    await api.delete(`/api/clientes/${c.id}`);
    carregar();
  }

  const campos: [keyof Cliente, string][] = [
    ["razao_social", "Razão social *"],
    ["endereco", "Endereço"],
    ["cnpj_cpf", "CNPJ / CPF"],
    ["inscricao_estadual", "Inscrição estadual"],
    ["telefone", "Telefone"],
    ["contato_comercial", "Contato comercial"],
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agências</h1>
          <p className="text-muted-foreground">Agências que usam o sistema e seus orçamentos</p>
        </div>
        <Button onClick={abrirNovo}>
          <Plus className="h-4 w-4" /> Nova agência
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {clientes.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Nenhuma agência cadastrada.
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Razão social</TH>
                  <TH>CNPJ / CPF</TH>
                  <TH>Contato</TH>
                  <TH className="text-center">Orçamentos</TH>
                  <TH className="text-right">Ações</TH>
                </TR>
              </THead>
              <TBody>
                {clientes.map((c) => (
                  <TR key={c.id} className="cursor-pointer" onClick={() => navigate(`/clientes/${c.id}`)}>
                    <TD className="font-medium">{c.razao_social}</TD>
                    <TD className="text-muted-foreground">{c.cnpj_cpf || "—"}</TD>
                    <TD className="text-muted-foreground">{c.contato_comercial || "—"}</TD>
                    <TD className="text-center">{c.total_orcamentos}</TD>
                    <TD className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" onClick={(e) => abrirEdicao(c, e)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={(e) => excluir(c, e)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={aberto} onOpenChange={setAberto}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{form.id ? "Editar agência" : "Nova agência"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            {campos.map(([k, label]) => (
              <div key={k} className={k === "razao_social" || k === "endereco" ? "sm:col-span-2 space-y-2" : "space-y-2"}>
                <Label>{label}</Label>
                <Input
                  value={(form[k] as string) || ""}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAberto(false)}>
              Cancelar
            </Button>
            <Button onClick={salvar}>Salvar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
