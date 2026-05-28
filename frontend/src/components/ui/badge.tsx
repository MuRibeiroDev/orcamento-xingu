import { cn } from "@/lib/utils";

const estilos: Record<string, string> = {
  rascunho: "bg-secondary text-secondary-foreground",
  enviado: "bg-blue-100 text-blue-700",
  aprovado: "bg-green-100 text-green-700",
};

export function StatusBadge({ status }: { status: string }) {
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        estilos[status] || estilos.rascunho
      )}
    >
      {label}
    </span>
  );
}
