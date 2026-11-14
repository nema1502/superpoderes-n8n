import React from "react";
import { COLOR, conAlfa, OPACIDAD } from "../tokens";

export type PropsAnillo = {
  cx: number;
  cy: number;
  /** Diámetro exterior en px (480 en D02.3). */
  diametro: number;
  /** Grosor del anillo (18 en D02.3). */
  grosor: number;
  /** 0 → 1: cuánto está lleno, desde las 12 en sentido horario. */
  progreso: number;
  color?: string;
  /** Opacidad de la pista vacía (ámbar al 8 %, como los segmentos apagados). */
  pista?: number;
  opacidad?: number;
};

/** Anillo que se llena (el de los 40 segundos del vendedor). */
export const Anillo: React.FC<PropsAnillo> = ({ cx, cy, diametro, grosor, progreso, color = COLOR.ambar, pista = OPACIDAD.apagado, opacidad = 1 }) => {
  const r = diametro / 2 - grosor / 2;
  const largo = 2 * Math.PI * r;
  const p = Math.max(0, Math.min(1, progreso));
  return (
    <svg width={diametro} height={diametro} style={{ position: "absolute", left: cx - diametro / 2, top: cy - diametro / 2, overflow: "visible", opacity: opacidad }}>
      <circle cx={diametro / 2} cy={diametro / 2} r={r} fill="none" stroke={conAlfa(color, pista)} strokeWidth={grosor} />
      {p > 0 && (
        <circle
          cx={diametro / 2}
          cy={diametro / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={grosor}
          strokeLinecap="round"
          strokeDasharray={`${largo * p} ${largo}`}
          transform={`rotate(-90 ${diametro / 2} ${diametro / 2})`}
        />
      )}
    </svg>
  );
};
