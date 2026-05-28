/** Formata número como moeda brasileira: R$ 1.234,56 */
export function formatBRL(valor: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(valor || 0);
}

/** Formata número simples no padrão pt-BR (sem símbolo de moeda). */
export function formatNum(valor: number): string {
  const v = valor || 0;
  return Number.isInteger(v) ? String(v) : v.toLocaleString("pt-BR");
}

/** Converte string digitada (com vírgula ou ponto) em número. */
export function parseNum(texto: string): number {
  if (!texto) return 0;
  const limpo = texto.replace(/\./g, "").replace(",", ".");
  const n = parseFloat(limpo);
  return isNaN(n) ? 0 : n;
}

export function formatData(iso: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("pt-BR");
  } catch {
    return iso;
  }
}
