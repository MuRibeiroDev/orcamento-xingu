import axios from "axios";

// Em produção (Docker/nginx) usa-se string vazia -> chamadas relativas (/api, /static).
// Em dev, o .env define http://localhost:8000. (?? mantém "" quando definido vazio.)
export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

// Injeta o token JWT em toda requisição.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redireciona ao login se o token expirar.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !location.pathname.includes("/login")) {
      localStorage.removeItem("token");
      location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ---------- Tipos ----------
export interface Cliente {
  id: number;
  razao_social: string;
  endereco: string;
  cnpj_cpf: string;
  inscricao_estadual: string;
  telefone: string;
  contato_comercial: string;
  logo_path?: string | null;
  total_orcamentos?: number;
  created_at?: string;
}

export interface CatalogoItem {
  id: number;
  nome: string;
  descritivo: string;
  valor_unitario_padrao: number;
  quantidade_sugerida: number;
  diarias_sugeridas: number;
}

export interface OrcamentoItem {
  id?: number;
  item: string;
  descritivo: string;
  quantidade: number;
  diarias: number;
  valor_unitario: number;
  encargos_percentual: number | null;
  ordem: number;
  total?: number;
  encargos?: number;
  total_final?: number;
}

export interface Orcamento {
  id: number;
  numero: string;
  cliente_id: number;
  cliente: Cliente;
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
  itens: OrcamentoItem[];
  soma_total: number;
  soma_encargos: number;
  previsao_investimento: number;
  created_at: string;
  updated_at: string;
}

export interface OrcamentoResumo {
  id: number;
  numero: string;
  cliente_id: number;
  cliente_razao_social: string;
  cliente_nome: string;
  evento_nome: string;
  evento_data: string;
  status: string;
  previsao_investimento: number;
  created_at: string;
}

export interface Config {
  id: number;
  instagram: string;
  email: string;
  assinatura_nome: string;
  assinatura_cargo: string;
  assinatura_cpf: string;
  assinatura_rg: string;
  encargos_padrao: number;
  logo_path: string;
  contato_logo_path: string;
}
