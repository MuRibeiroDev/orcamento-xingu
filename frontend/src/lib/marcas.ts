import type { Marca } from "./api";

/** Marcas disponíveis para o modelo de casting (logo exibida na capa do PDF). */
export const MARCAS: { valor: Marca; nome: string; logo: string }[] = [
  { valor: "xingu", nome: "XINGU", logo: "/assets/logo-xingu.png" },
  { valor: "boom", nome: "BOOM", logo: "/assets/logo-boom.png" },
];
