import * as React from "react";
import { Input } from "./input";

interface NumberInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type"> {
  value: number;
  onChange: (value: number) => void;
}

/** Campo somente numérico (quantidades, diárias, percentuais). Não aceita texto. */
export function NumberInput({ value, onChange, ...props }: NumberInputProps) {
  return (
    <Input
      {...props}
      type="number"
      inputMode="decimal"
      value={Number.isFinite(value) ? String(value) : ""}
      onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
    />
  );
}
