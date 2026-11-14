import { evolvePath, getLength } from "@remotion/paths";
import React from "react";
import { COLOR, conAlfa, GROSOR, MOV } from "../tokens";

/**
 * Hilo: un trazo cualquiera que se dibuja de un tirón (evolvePath). Por defecto, el cable
 * de la cabina: ámbar de 4 px. Por encima de 1 se borra desde el comienzo (la cola de la
 * firma se recoge así).
 */
export const Hilo: React.FC<{ d: string; progreso?: number; color?: string; grosor?: number; opacidad?: number; extremos?: "butt" | "round" }> = ({
  d,
  progreso = 1,
  color = COLOR.ambar,
  grosor = GROSOR.cable_cabina,
  opacidad = 1,
  extremos = "butt",
}) => {
  if (progreso <= 0 || progreso >= 2) return null;
  const ev = evolvePath(progreso, d);
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: opacidad }}>
      <path d={d} fill="none" stroke={color} strokeWidth={grosor} strokeLinecap={extremos} strokeLinejoin="round" strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
    </svg>
  );
};

/** Punto y dirección (radianes, 0 = derecha, negativo = hacia arriba) del final de un arco de largo L doblado `grados`. */
export function finDelArco(x0: number, y0: number, largo: number, grados: number): { x: number; y: number; angulo: number } {
  const t = (grados * Math.PI) / 180;
  if (Math.abs(t) < 1e-4) return { x: x0 + largo, y: y0, angulo: 0 };
  const r = largo / t;
  return { x: x0 + r * Math.sin(t), y: y0 - r + r * Math.cos(t), angulo: -t };
}

/** El arco de largo constante como camino SVG (curva hacia arriba para ángulos positivos). */
export function caminoArco(x0: number, y0: number, largo: number, grados: number): string {
  const t = (grados * Math.PI) / 180;
  if (Math.abs(t) < 1e-4) return `M ${x0} ${y0} L ${x0 + largo} ${y0}`;
  const r = largo / t;
  const f = finDelArco(x0, y0, largo, grados);
  return `M ${x0} ${y0} A ${Math.abs(r)} ${Math.abs(r)} 0 ${Math.abs(t) > Math.PI ? 1 : 0} ${t > 0 ? 0 : 1} ${f.x} ${f.y}`;
}

/**
 * Cable cargador (D12.1): trazo hueso de 14 px que se dobla como un arco de LARGO
 * CONSTANTE (L = 600 px; radio = L ÷ ángulo). La ficha USB-A queda fija a la izquierda y
 * la USB-C sigue la tangente del extremo. `barrido` 0 → 1: una luz recorre el cable una vez.
 */
export const Cable: React.FC<{
  x0: number;
  y0: number;
  largo?: number;
  /** Ángulo de doblez en grados (0 = recto, 180 = media vuelta hacia arriba). */
  grados: number;
  grosor?: number;
  color?: string;
  barrido?: number;
  colorBarrido?: string;
  opacidad?: number;
}> = ({ x0, y0, largo = 600, grados, grosor = 14, color = COLOR.hueso, barrido = 0, colorBarrido = conAlfa(COLOR.ambar, 0.9), opacidad = 1 }) => {
  const d = caminoArco(x0, y0, largo, grados);
  const fin = finDelArco(x0, y0, largo, grados);
  const L = getLength(d);
  const banda = MOV.barrido.ancho_px;
  const mostrarBarrido = barrido > 0 && barrido < 1;
  const desplaz = -(-banda + barrido * (L + banda));
  const ang = (fin.angulo * 180) / Math.PI;
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: opacidad }}>
      {/* ficha USB-A fija */}
      <g transform={`translate(${x0} ${y0})`}>
        <rect x={-74} y={-21} width={58} height={42} rx={9} fill={COLOR.acero2} stroke={color} strokeWidth={4} />
        <rect x={-104} y={-14} width={32} height={28} rx={3} fill="none" stroke={color} strokeWidth={4} />
        <rect x={-18} y={-grosor / 2 - 2} width={20} height={grosor + 4} rx={4} fill={color} />
      </g>
      <path d={d} fill="none" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
      {mostrarBarrido && <path d={d} fill="none" stroke={colorBarrido} strokeWidth={grosor * 0.55} strokeLinecap="round" strokeDasharray={`${banda} ${L + banda}`} strokeDashoffset={desplaz} />}
      {/* ficha USB-C en la punta, siguiendo la tangente */}
      <g transform={`translate(${fin.x} ${fin.y}) rotate(${ang})`}>
        <rect x={-2} y={-grosor / 2 - 2} width={22} height={grosor + 4} rx={4} fill={color} />
        <rect x={16} y={-19} width={60} height={38} rx={9} fill={COLOR.acero2} stroke={color} strokeWidth={4} />
        <rect x={74} y={-10} width={26} height={20} rx={8} fill="none" stroke={color} strokeWidth={4} />
      </g>
    </svg>
  );
};
