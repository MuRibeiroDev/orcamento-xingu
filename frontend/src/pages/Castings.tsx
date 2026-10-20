import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";
import { api, CastingResumo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { formatData } from "@/lib/format";
import { MARCAS } from "@/lib/marcas";

export default function Castings() {
  const navigate = useNavigate();
  const [castings, setCastings] = useState<CastingResumo[]>([]);

  function carregar() {
    api.get("/api/castings").then((r) => setCastings(r.data));
  }
  useEffect(carregar, []);

  async function excluir(c: CastingResumo, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Excluir o casting "${c.titulo}"?`)) return;
    await api.delete(`/api/castings/${c.id}`);
    carregar();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Castings</h1>
          <p className="text-muted-foreground">Apresentações em PDF com as modelos selecionadas</p>
        </div>
        <Button asChild>
          <Link to="/castings/novo">
            <Plus className="h-4 w-4" /> Novo casting
          </Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {castings.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Nenhum casting criado ainda.
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Título</TH>
                  <TH>Modelo</TH>
                  <TH className="text-center">Pessoas</TH>
                  <TH>Atualizado</TH>
                  <TH className="text-right">Ações</TH>
                </TR>
              </THead>
              <TBody>
                {castings.map((c) => {
                  const marca = MARCAS.find((m) => m.valor === c.marca);
                  return (
                    <TR key={c.id} className="cursor-pointer" onClick={() => navigate(`/castings/${c.id}`)}>
                      <TD className="font-medium">{c.titulo}</TD>
                      <TD>
                        <img src={marca?.logo} alt={marca?.nome} className="h-7 w-16 object-contain object-left" />
                      </TD>
                      <TD className="text-center">{c.total_modelos}</TD>
                      <TD className="text-muted-foreground">{formatData(c.updated_at)}</TD>
                      <TD className="text-right">
                        <Button variant="ghost" size="icon" onClick={(e) => excluir(c, e)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
