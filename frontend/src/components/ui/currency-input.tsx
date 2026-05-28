import * as React from "react";
import { Input } from "./input";
import { formatBRL } from "@/lib/format";

interface CurrencyInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange"> {
  value: number;
  onChange: (value: number) => void;
}

/**
 * Campo de valor monetário no padrão brasileiro (R$ 1.234,56).
 * Os dígitos digitados são interpretados como centavos: 350000 -> R$ 3.500,00.
 */
export function CurrencyInput({ value, onChange, ...props }: CurrencyInputProps) {
  function handle(e: React.ChangeEvent<HTMLInputElement>) {
    const digitos = e.target.value.replace(/\D/g, "");
    const numero = digitos ? parseInt(digitos, 10) / 100 : 0;
    onChange(numero);
  }
  return (
    <Input
      {...props}
      inputMode="numeric"
      value={formatBRL(value)}
      onChange={handle}
    />
  );
}
