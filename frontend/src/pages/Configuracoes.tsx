import { useEffect, useRef, useState } from "react";
import { Upload, Check } from "lucide-react";
import { api, API_URL, Config } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NumberInput } from "@/components/ui/number-input";
import { Label } from "@/components/ui/label";

export default function Configuracoes() {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [salvo, setSalvo] = useState(false);
  const [logoVersao, setLogoVersao] = useState(Date.now());
  const fileRef = useRef<HTMLInputElement>(null);
  const contatoRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get("/api/config").then((r) => setCfg(r.data));
  }, []);

  if (!cfg) return <div className="text-muted-foreground">Carregando...</div>;

  async function salvar() {
    await api.put("/api/config", cfg);
    setSalvo(true);
    setTimeout(() => setSalvo(false), 2000);
  }

  async function enviarLogo(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await api.post("/api/config/logo", fd);
    setCfg(data);
    setLogoVersao(Date.now());
  }

  async function enviarContatoLogo(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await api.post("/api/config/contato-logo", fd);
    setCfg(data);
    setLogoVersao(Date.now());
  }

  const campos: [keyof Config, string][] = [
    ["instagram", "Instagram"],
    ["email", "E-mail"],
    ["assinatura_nome", "Nome (assinatura)"],
    ["assinatura_cargo", "Cargo"],
    ["assinatura_cpf", "CPF"],
    ["assinatura_rg", "RG"],
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Configurações</h1>
        <p className="text-muted-foreground">Dados fixos da empresa que aparecem no PDF</p>
      </div>

      <Card>
        <CardContent className="flex items-center gap-6 p-6">
          <img
            src={`${API_URL}/static/${cfg.logo_path}?v=${logoVersao}`}
            alt="Logo"
            className="h-24 w-24 rounded-lg border object-contain p-2"
          />
          <div>
            <div className="font-medium">Logo XINGU</div>
            <p className="mb-3 text-sm text-muted-foreground">
              Canto superior esquerdo do PDF (e topo do sistema).
            </p>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={enviarLogo} />
            <Button variant="outline" onClick={() => fileRef.current?.click()}>
              <Upload className="h-4 w-4" /> Trocar logo
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-6 p-6">
          <img
            src={`${API_URL}/static/${cfg.contato_logo_path}?v=${logoVersao}`}
            alt="Contato"
            className="h-24 w-40 rounded-lg border object-contain p-2"
          />
          <div>
            <div className="font-medium">Contato (@agenciaxingu)</div>
            <p className="mb-3 text-sm text-muted-foreground">
              Imagem do canto superior direito do PDF.
            </p>
            <input
              ref={contatoRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={enviarContatoLogo}
            />
            <Button variant="outline" onClick={() => contatoRef.current?.click()}>
              <Upload className="h-4 w-4" /> Trocar imagem de contato
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="grid gap-4 p-6 md:grid-cols-2">
          {campos.map(([k, label]) => (
            <div key={k} className="space-y-2">
              <Label>{label}</Label>
              <Input
                value={(cfg[k] as string) || ""}
                onChange={(e) => setCfg({ ...cfg, [k]: e.target.value })}
              />
            </div>
          ))}
          <div className="space-y-2">
            <Label>Encargos padrão (%)</Label>
            <NumberInput
              value={cfg.encargos_padrao}
              onChange={(v) => setCfg({ ...cfg, encargos_padrao: v })}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={salvar}>
          {salvo ? (
            <>
              <Check className="h-4 w-4" /> Salvo!
            </>
          ) : (
            "Salvar configurações"
          )}
        </Button>
      </div>
    </div>
  );
}
