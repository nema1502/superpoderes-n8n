import React from "react";
import { COLOR, GROSOR, RADIO } from "../tokens";
import { useAtenuarAmbar, type Estilo } from "./movimiento";

export type Lado = "abajo" | "arriba" | "izq" | "der";

export type Cola = {
  /** Lado del globo del que sale la cola. */
  lado: Lado;
  /** Dónde nace sobre ese lado: 0 = un extremo, 1 = el otro (0,5 = el medio). */
  en?: number;
  /** Punta de la cola, en px relativos al punto donde nace (x a la derecha, y hacia abajo). */
  punta: [number, number];
  /** Ancho de la base de la cola. */
  base?: number;
};

export type PropsGlobo = {
  /** Centro del cuerpo del globo. */
  x: number;
  y: number;
  ancho: number;
  alto: number;
  cola?: Cola | null;
  /** Borde: hueso por defecto; ámbar (respuesta, lo correcto) o rojo (lo incorrecto). */
  color?: string;
  grosor?: number;
  radio?: number;
  relleno?: string;
  /** Opacidad y transform del globo entero; el origen es la punta de la cola (crece desde ahí). */
  estilo?: Estilo;
  /** Lo de adentro, en coordenadas del cuadro. */
  children?: React.ReactNode;
};

/** Punta de la cola en coordenadas del cuadro (el punto desde el que crece el globo). */
export function puntaGlobo(p: Pick<PropsGlobo, "x" | "y" | "ancho" | "alto" | "cola">): [number, number] {
  if (!p.cola) return [p.x, p.y];
  const b = baseCola(p);
  return [b[0] + p.cola.punta[0], b[1] + p.cola.punta[1]];
}

function baseCola(p: Pick<PropsGlobo, "x" | "y" | "ancho" | "alto" | "cola">): [number, number] {
  const c = p.cola!;
  const x0 = p.x - p.ancho / 2;
  const y0 = p.y - p.alto / 2;
  const en = c.en ?? 0.5;
  switch (c.lado) {
    case "abajo":
      return [x0 + en * p.ancho, y0 + p.alto];
    case "arriba":
      return [x0 + en * p.ancho, y0];
    case "izq":
      return [x0, y0 + en * p.alto];
    case "der":
      return [x0 + p.ancho, y0 + en * p.alto];
  }
}

/** Contorno del globo con la cola, como un solo trazo (el borde no se corta). */
export function caminoGlobo(p: Pick<PropsGlobo, "x" | "y" | "ancho" | "alto" | "cola" | "radio">): string {
  const r = Math.min(p.radio ?? RADIO.globo, p.alto / 2, p.ancho / 2);
  const x0 = p.x - p.ancho / 2;
  const y0 = p.y - p.alto / 2;
  const x1 = x0 + p.ancho;
  const y1 = y0 + p.alto;
  const c = p.cola;
  const bw = c ? (c.base ?? Math.min(70, p.ancho * 0.18, p.alto * 0.5)) : 0;
  const [bx, by] = c ? baseCola(p) : [0, 0];
  const [tx, ty] = c ? [bx + c.punta[0], by + c.punta[1]] : [0, 0];
  const lim = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
  const partes: string[] = [`M ${x0 + r} ${y0}`];
  if (c?.lado === "arriba") {
    const cx = lim(bx, x0 + r + bw / 2, x1 - r - bw / 2);
    partes.push(`L ${cx - bw / 2} ${y0} L ${tx} ${ty} L ${cx + bw / 2} ${y0}`);
  }
  partes.push(`L ${x1 - r} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y0 + r}`);
  if (c?.lado === "der") {
    const cy = lim(by, y0 + r + bw / 2, y1 - r - bw / 2);
    partes.push(`L ${x1} ${cy - bw / 2} L ${tx} ${ty} L ${x1} ${cy + bw / 2}`);
  }
  partes.push(`L ${x1} ${y1 - r} A ${r} ${r} 0 0 1 ${x1 - r} ${y1}`);
  if (c?.lado === "abajo") {
    const cx = lim(bx, x0 + r + bw / 2, x1 - r - bw / 2);
    partes.push(`L ${cx + bw / 2} ${y1} L ${tx} ${ty} L ${cx - bw / 2} ${y1}`);
  }
  partes.push(`L ${x0 + r} ${y1} A ${r} ${r} 0 0 1 ${x0} ${y1 - r}`);
  if (c?.lado === "izq") {
    const cy = lim(by, y0 + r + bw / 2, y1 - r - bw / 2);
    partes.push(`L ${x0} ${cy + bw / 2} L ${tx} ${ty} L ${x0} ${cy - bw / 2}`);
  }
  partes.push(`L ${x0} ${y0 + r} A ${r} ${r} 0 0 1 ${x0 + r} ${y0} Z`);
  return partes.join(" ");
}

/**
 * Globo de diálogo: cuerpo redondeado con cola, borde de 5 px y relleno tinta. Sirve
 * para «¿Hay para tipo C?», los dos globos de las preguntas (rojo con cruz, ámbar con
 * palomita), la respuesta del chat, el «?» que sale de la cabina y «¿Quién va a querer?».
 * La cola nunca nace adentro de otra cosa: apunta a quien habla.
 */
export const Globo: React.FC<PropsGlobo> = ({ x, y, ancho, alto, cola = null, color = COLOR.hueso, grosor = GROSOR.borde_globo, radio, relleno = COLOR.tinta, estilo, children }) => {
  const ambar = useAtenuarAmbar();
  const d = caminoGlobo({ x, y, ancho, alto, cola, radio });
  const [px, py] = puntaGlobo({ x, y, ancho, alto, cola });
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${px}px ${py}px`, ...estilo }}>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        <path d={d} fill={relleno} stroke={color} strokeWidth={grosor} strokeLinejoin="round" opacity={color === COLOR.ambar ? ambar : 1} />
      </svg>
      {children}
    </div>
  );
};
