import { useEffect, useRef, useState } from "react";
import { Plus, Pencil, Trash2, Upload, ChevronLeft, ChevronRight, X, ImageOff, Search } from "lucide-react";
import { api, fotoUrl, Modelo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const MAX_FOTOS = 4;

const vazio: Partial<Modelo> = {
  nome: "",
  idade: "",
  manequim: "",
  altura: "",
  destaque: "",
  fotos: [],
};

const campos: [keyof Modelo, string, string][] = [
  ["idade", "Idade", "ex: 20"],
  ["manequim", "Manequim", "ex: 38/40"],
  ["altura", "Altura", "ex: 1,68"],
  ["destaque", "Cidade / destaque", "ex: Belo Horizonte - MG, Bilíngue"],
];

function mensagemErro(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : "Não foi possível concluir a operação.";
}

export default function Modelos() {
  const [modelos, setModelos] = useState<Modelo[]>([]);
  const [busca, setBusca] = useState("");
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState<Partial<Modelo>>(vazio);
  const [enviando, setEnviando] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function carregar() {
    api.get("/api/modelos").then((r) => setModelos(r.data));
  }
  useEffect(carregar, []);

  function abrirNova() {
    setForm(vazio);
    setAberto(true);
  }
  function abrirEdicao(m: Modelo) {
    setForm(m);
    setAberto(true);
  }

  async function salvar() {
    if (!form.nome?.trim()) return;
    const dados = {
      nome: form.nome,
      idade: form.idade,
      manequim: form.manequim,
      altura: form.altura,
      destaque: form.destaque,
    };
    try {
      if (form.id) {
        await api.put(`/api/modelos/${form.id}`, dados);
        setAberto(false);
      } else {
        // Mantém o diálogo aberto para já enviar as fotos da nova modelo.
        const { data } = await api.post("/api/modelos", dados);
        setForm(data);
      }
      carregar();
    } catch (e) {
      alert(mensagemErro(e));
    }
  }

  async function enviarFotos(e: React.ChangeEvent<HTMLInputElement>) {
    const arquivos = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (!form.id || arquivos.length === 0) return;
    const livres = MAX_FOTOS - (form.fotos?.length ?? 0);
    setEnviando(true);
    try {
      for (const arquivo of arquivos.slice(0, livres)) {
        const fd = new FormData();
        fd.append("file", arquivo);
        const { data } = await api.post(`/api/modelos/${form.id}/fotos`, fd);
        setForm(data);
      }
      if (arquivos.length > livres) alert(`Cada modelo pode ter até ${MAX_FOTOS} fotos.`);
      carregar();
    } catch (err) {
      alert(mensagemErro(err));
    } finally {
      setEnviando(false);
    }
  }

  async function removerFoto(fotoId: number) {
    const { data } = await api.delete(`/api/modelos/${form.id}/fotos/${fotoId}`);
    setForm(data);
    carregar();
  }

  async function moverFoto(indice: number, direcao: -1 | 1) {
    const ids = (form.fotos ?? []).map((f) => f.id);
    const destino = indice + direcao;
    if (destino < 0 || destino >= ids.length) return;
    const novos = [...ids];
    [novos[indice], novos[destino]] = [novos[destino], novos[indice]];
    const { data } = await api.put(`/api/modelos/${form.id}/fotos/ordem`, novos);
    setForm(data);
    carregar();
  }

  async function excluir(m: Modelo) {
    if (!confirm(`Excluir "${m.nome}"? Ela também sairá dos castings em que aparece.`)) return;
    await api.delete(`/api/modelos/${m.id}`);
    carregar();
  }

  const termo = busca.trim().toLowerCase();
  const filtradas = termo
    ? modelos.filter((m) => `${m.nome} ${m.destaque}`.toLowerCase().includes(termo))
    : modelos;
  const fotos = form.fotos ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Modelos</h1>
          <p className="text-muted-foreground">Banco de pessoas com fotos e medidas para os castings</p>
        </div>
        <Button onClick={abrirNova}>
          <Plus className="h-4 w-4" /> Nova modelo
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Buscar por nome ou cidade"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>

      {filtradas.length === 0 ? (
        <Card>
          <CardContent className="p-10 text-center text-sm text-muted-foreground">
            {modelos.length === 0 ? "Nenhuma modelo cadastrada." : "Nenhuma modelo encontrada."}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {filtradas.map((m) => (
            <Card key={m.id} className="overflow-hidden">
              <button className="block w-full text-left" onClick={() => abrirEdicao(m)}>
                <div className="grid aspect-[3/4] grid-cols-2 gap-0.5 bg-muted">
                  {m.fotos.length === 0 ? (
                    <div className="col-span-2 flex items-center justify-center text-muted-foreground">
                      <ImageOff className="h-8 w-8" />
                    </div>
                  ) : (
                    m.fotos.slice(0, MAX_FOTOS).map((f, i) => (
                      <img
                        key={f.id}
                        src={fotoUrl(f.arquivo)}
                        alt=""
                        className={
                          "h-full w-full object-cover " +
                          (m.fotos.length === 1 || (m.fotos.length === 3 && i === 0) ? "row-span-2 " : "") +
                          (m.fotos.length === 1 ? "col-span-2" : "")
                        }
                      />
                    ))
                  )}
                </div>
              </button>
              <CardContent className="space-y-1 p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold uppercase leading-tight">{m.nome}</div>
                  <div className="flex shrink-0">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => abrirEdicao(m)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => excluir(m)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {[m.idade && `${m.idade}${/^\d+$/.test(m.idade) ? " anos" : ""}`, m.altura, m.manequim && `Manequim ${m.manequim}`, m.destaque]
                    .filter(Boolean)
                    .join(" · ") || "—"}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={aberto} onOpenChange={setAberto}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{form.id ? "Editar modelo" : "Nova modelo"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label>Nome *</Label>
              <Input value={form.nome || ""} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            </div>
            {campos.map(([k, label, placeholder]) => (
              <div key={k} className="space-y-2">
                <Label>{label}</Label>
                <Input
                  placeholder={placeholder}
                  value={(form[k] as string) || ""}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <Label>Fotos ({fotos.length}/{MAX_FOTOS})</Label>
            {!form.id ? (
              <p className="text-sm text-muted-foreground">Salve a modelo para enviar as fotos.</p>
            ) : (
              <>
                <p className="text-xs text-muted-foreground">
                  A ordem define a posição no PDF: 1ª superior esquerda, 2ª superior direita, 3ª inferior
                  esquerda, 4ª inferior direita.
                </p>
                <div className="grid grid-cols-4 gap-2">
                  {fotos.map((f, i) => (
                    <div key={f.id} className="group relative aspect-[3/4] overflow-hidden rounded-md border">
                      <img src={fotoUrl(f.arquivo)} alt="" className="h-full w-full object-cover" />
                      <span className="absolute left-1 top-1 rounded bg-black/60 px-1.5 text-xs text-white">
                        {i + 1}
                      </span>
                      <button
                        title="Remover"
                        onClick={() => removerFoto(f.id)}
                        className="absolute right-1 top-1 rounded bg-black/60 p-0.5 text-white hover:bg-destructive"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                      <div className="absolute inset-x-1 bottom-1 flex justify-between">
                        <button
                          title="Mover para trás"
                          disabled={i === 0}
                          onClick={() => moverFoto(i, -1)}
                          className="rounded bg-black/60 p-0.5 text-white disabled:opacity-0"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button
                          title="Mover para frente"
                          disabled={i === fotos.length - 1}
                          onClick={() => moverFoto(i, 1)}
                          className="rounded bg-black/60 p-0.5 text-white disabled:opacity-0"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                  {fotos.length < MAX_FOTOS && (
                    <button
                      onClick={() => fileRef.current?.click()}
                      disabled={enviando}
                      className="flex aspect-[3/4] flex-col items-center justify-center gap-1 rounded-md border border-dashed text-sm text-muted-foreground hover:bg-accent disabled:opacity-50"
                    >
                      <Upload className="h-5 w-5" />
                      {enviando ? "Enviando..." : "Adicionar"}
                    </button>
                  )}
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={enviarFotos}
                />
              </>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setAberto(false)}>
              {form.id ? "Fechar" : "Cancelar"}
            </Button>
            <Button onClick={salvar}>{form.id ? "Salvar" : "Salvar e adicionar fotos"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
