import React from "react";
import { useTramo } from "../pasos";
import { CURVA, MOV } from "../tokens";
import { Texto, type PropsTexto } from "./Texto";

/** 125 → "2:05". */
export function formatoReloj(segundos: number): string {
  const s = Math.max(0, Math.round(segundos));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**
 * Contador: un número que corre de `desde` a `hasta` con Easing.out(cubic), 0,6-1,2 s
 * (el «40», el 4:12 → 0:30, los conteos de caracteres). Devuelve el valor (sin redondear).
 */
export function useContador(paso: number, retraso: number, desde: number, hasta: number, dura: number = MOV.dura.contador): number {
  const p = useTramo(paso, retraso, dura, CURVA.sale);
  return desde + (hasta - desde) * p;
}

/** Contador como texto (números de ancho fijo): <Contador paso={2} desde={0} hasta={40} x y tam />. */
export const Contador: React.FC<
  Omit<PropsTexto, "children"> & { paso: number; retraso?: number; desde: number; hasta: number; dura?: number; formato?: (v: number) => string }
> = ({ paso, retraso = 0, desde, hasta, dura, formato = (v) => String(Math.round(v)), ...texto }) => {
  const v = useContador(paso, retraso, desde, hasta, dura);
  return (
    <Texto numeros {...texto}>
      {formato(v)}
    </Texto>
  );
};
