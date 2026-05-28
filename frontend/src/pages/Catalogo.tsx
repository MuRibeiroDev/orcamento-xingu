import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { api, CatalogoItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { CurrencyInput } from "@/components/ui/currency-input";
import { NumberInput } from "@/components/ui/number-input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatBRL } from "@/lib/format";

const vazio: Partial<CatalogoItem> = {
  nome: "",
  descritivo: "",
  valor_unitario_padrao: 0,
  quantidade_sugerida: 1,
  diarias_sugeridas: 1,
};

export default function Catalogo() {
  const [itens, setItens] = useState<CatalogoItem[]>([]);
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState<Partial<CatalogoItem>>(vazio);

  function carregar() {
    api.get("/api/catalogo").then((r) => setItens(r.data));
  }
  useEffect(carregar, []);

  function abrirNovo() {
    setForm(vazio);
    setAberto(true);
  }
  function abrirEdicao(it: CatalogoItem) {
    setForm(it);
    setAberto(true);
  }

  async function salvar() {
    if (!form.nome?.trim()) return;
    if (form.id) await api.put(`/api/catalogo/${form.id}`, form);
    else await api.post("/api/catalogo", form);
    setAberto(false);
    carregar();
  }

  async function excluir(it: CatalogoItem) {
    if (!confirm(`Excluir "${it.nome}" do catálogo?`)) return;
    await api.delete(`/api/catalogo/${it.id}`);
    carregar();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Catálogo de itens</h1>
          <p className="text-muted-foreground">
            Itens e serviços reutilizáveis com valor padrão
          </p>
        </div>
        <Button onClick={abrirNovo}>
          <Plus className="h-4 w-4" /> Novo item
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {itens.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Catálogo vazio. Cadastre itens para reutilizá-los nos orçamentos.
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Nome</TH>
                  <TH>Descritivo</TH>
                  <TH className="text-right">Valor unitário</TH>
                  <TH className="text-right">Ações</TH>
                </TR>
              </THead>
              <TBody>
                {itens.map((it) => (
                  <TR key={it.id}>
                    <TD className="font-medium text-primary">{it.nome}</TD>
                    <TD className="max-w-md truncate text-muted-foreground">{it.descritivo || "—"}</TD>
                    <TD className="text-right font-medium">{formatBRL(it.valor_unitario_padrao)}</TD>
                    <TD className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" onClick={() => abrirEdicao(it)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => excluir(it)}>
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
            <DialogTitle>{form.id ? "Editar item" : "Novo item do catálogo"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Nome *</Label>
              <Input
                value={form.nome || ""}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Descritivo</Label>
              <Textarea
                rows={5}
                value={form.descritivo || ""}
                onChange={(e) => setForm({ ...form, descritivo: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Valor unitário</Label>
                <CurrencyInput
                  value={form.valor_unitario_padrao ?? 0}
                  onChange={(v) => setForm({ ...form, valor_unitario_padrao: v })}
                />
              </div>
              <div className="space-y-2">
                <Label>Qtd. sugerida</Label>
                <NumberInput
                  value={form.quantidade_sugerida ?? 1}
                  onChange={(v) => setForm({ ...form, quantidade_sugerida: v })}
                />
              </div>
              <div className="space-y-2">
                <Label>Diárias sugeridas</Label>
                <NumberInput
                  value={form.diarias_sugeridas ?? 1}
                  onChange={(v) => setForm({ ...form, diarias_sugeridas: v })}
                />
              </div>
            </div>
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
