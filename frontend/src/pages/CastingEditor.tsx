import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowDown, ArrowUp, FileDown, ImageOff, Plus, Save, Search, Trash2, X } from "lucide-react";
import { api, fotoUrl, Marca, Modelo } from "@/lib/api";
import { MARCAS } from "@/lib/marcas";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function Miniatura({ modelo }: { modelo: Modelo }) {
  const foto = modelo.fotos[0];
  return foto ? (
    <img src={fotoUrl(foto.arquivo)} alt="" className="h-12 w-9 shrink-0 rounded object-cover" />
  ) : (
    <div className="flex h-12 w-9 shrink-0 items-center justify-center rounded bg-muted text-muted-foreground">
      <ImageOff className="h-4 w-4" />
    </div>
  );
}

function resumo(m: Modelo): string {
  return [m.altura, m.manequim && `Manequim ${m.manequim}`, m.destaque].filter(Boolean).join(" · ");
}

export default function CastingEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const editando = Boolean(id);

  const [titulo, setTitulo] = useState("");
  const [marca, setMarca] = useState<Marca>("xingu");
  const [selecionadas, setSelecionadas] = useState<Modelo[]>([]);
  const [todas, setTodas] = useState<Modelo[]>([]);
  const [busca, setBusca] = useState("");
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    api.get("/api/modelos").then((r) => setTodas(r.data));
    if (!id) return;
    api.get(`/api/castings/${id}`).then(({ data }) => {
      setTitulo(data.titulo);
      setMarca(data.marca);
      setSelecionadas(data.modelos);
    });
  }, [id]);

  async function salvar(): Promise<number | null> {
    if (!titulo.trim()) {
      alert("Informe o título do casting.");
      return null;
    }
    setSalvando(true);
    try {
      const dados = { titulo, marca, modelo_ids: selecionadas.map((m) => m.id) };
      if (editando) {
        await api.put(`/api/castings/${id}`, dados);
        return Number(id);
      }
      const { data } = await api.post("/api/castings", dados);
      navigate(`/castings/${data.id}`, { replace: true });
      return data.id;
    } catch {
      alert("Não foi possível salvar o casting.");
      return null;
    } finally {
      setSalvando(false);
    }
  }

  async function gerarPdf() {
    if (selecionadas.length === 0) {
      alert("Adicione pelo menos uma modelo ao casting.");
      return;
    }
    const cid = await salvar();
    if (!cid) return;
    const resp = await api.get(`/api/castings/${cid}/pdf`, { responseType: "blob" });
    window.open(URL.createObjectURL(resp.data), "_blank");
  }

  async function excluir() {
    if (!confirm("Excluir este casting?")) return;
    await api.delete(`/api/castings/${id}`);
    navigate("/castings");
  }

  function adicionar(m: Modelo) {
    setSelecionadas((atual) => [...atual, m]);
  }
  function remover(modeloId: number) {
    setSelecionadas((atual) => atual.filter((m) => m.id !== modeloId));
  }
  function mover(indice: number, direcao: -1 | 1) {
    setSelecionadas((atual) => {
      const destino = indice + direcao;
      if (destino < 0 || destino >= atual.length) return atual;
      const nova = [...atual];
      [nova[indice], nova[destino]] = [nova[destino], nova[indice]];
      return nova;
    });
  }

  const idsSelecionados = new Set(selecionadas.map((m) => m.id));
  const termo = busca.trim().toLowerCase();
  const disponiveis = todas.filter(
    (m) => !idsSelecionados.has(m.id) && `${m.nome} ${m.destaque}`.toLowerCase().includes(termo)
  );
  const paginas = Math.ceil(selecionadas.length / 2) + 2;

  return (
    <div className="space-y-6">
      <Link to="/castings" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Voltar para castings
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{editando ? "Editar casting" : "Novo casting"}</h1>
          <p className="text-muted-foreground">Escolha a marca, selecione as modelos e gere o PDF</p>
        </div>
        <div className="flex gap-2">
          {editando && (
            <Button variant="ghost" onClick={excluir}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          )}
          <Button variant="outline" onClick={salvar} disabled={salvando}>
            <Save className="h-4 w-4" /> Salvar
          </Button>
          <Button onClick={gerarPdf} disabled={salvando}>
            <FileDown className="h-4 w-4" /> Gerar PDF
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-6 p-6 md:grid-cols-[1fr_auto]">
          <div className="space-y-2">
            <Label>Título (evento / cliente)</Label>
            <Input placeholder="ex: SIC - CRESOL" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Modelo da capa</Label>
            <div className="flex gap-2">
              {MARCAS.map((m) => (
                <button
                  key={m.valor}
                  type="button"
                  onClick={() => setMarca(m.valor)}
                  aria-pressed={marca === m.valor}
                  className={cn(
                    "flex h-10 w-28 items-center justify-center rounded-md border px-3 transition-colors",
                    marca === m.valor ? "border-primary ring-2 ring-primary" : "hover:bg-accent"
                  )}
                >
                  <img src={m.logo} alt={m.nome} className="max-h-7 max-w-full object-contain" />
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <span className="font-medium">No casting ({selecionadas.length})</span>
              <span className="text-xs text-muted-foreground">
                {paginas} páginas · 2 pessoas por página
              </span>
            </div>
            {selecionadas.length === 0 ? (
              <div className="p-10 text-center text-sm text-muted-foreground">
                Adicione modelos da lista ao lado.
              </div>
            ) : (
              <ol className="divide-y">
                {selecionadas.map((m, i) => (
                  <li key={m.id} className="flex items-center gap-3 px-4 py-2">
                    <span className="w-5 text-right text-xs text-muted-foreground">{i + 1}</span>
                    <Miniatura modelo={m} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium uppercase">{m.nome}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {m.fotos.length} foto(s){resumo(m) && ` · ${resumo(m)}`}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="h-8 w-8" disabled={i === 0} onClick={() => mover(i, -1)} title="Subir">
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      disabled={i === selecionadas.length - 1}
                      onClick={() => mover(i, 1)}
                      title="Descer"
                    >
                      <ArrowDown className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => remover(m.id)} title="Remover">
                      <X className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            <div className="space-y-3 border-b px-6 py-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Modelos cadastradas</span>
                <Link to="/modelos" className="text-xs text-primary hover:underline">
                  Gerenciar modelos
                </Link>
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input className="pl-9" placeholder="Buscar" value={busca} onChange={(e) => setBusca(e.target.value)} />
              </div>
            </div>
            {disponiveis.length === 0 ? (
              <div className="p-10 text-center text-sm text-muted-foreground">
                {todas.length === 0 ? "Nenhuma modelo cadastrada ainda." : "Nenhuma modelo disponível."}
              </div>
            ) : (
              <ul className="max-h-[480px] divide-y overflow-y-auto">
                {disponiveis.map((m) => (
                  <li key={m.id}>
                    <button
                      type="button"
                      onClick={() => adicionar(m)}
                      className="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-accent"
                    >
                      <Miniatura modelo={m} />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium uppercase">{m.nome}</div>
                        <div className="truncate text-xs text-muted-foreground">{resumo(m) || "—"}</div>
                      </div>
                      <Plus className="h-4 w-4 text-muted-foreground" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
