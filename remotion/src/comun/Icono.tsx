import React from "react";
import { COLOR } from "../tokens";
import { ICONOS_SVG, type NombreIcono } from "./iconos.generado";
import { useAtenuarAmbar, type Estilo } from "./movimiento";

export type { NombreIcono };

/** Ancho en px de un ícono dibujado con un alto dado (los de Font Awesome no son cuadrados). */
export function anchoIcono(nombre: NombreIcono, alto: number): number {
  const i = ICONOS_SVG[nombre];
  return (alto * i.ancho) / i.alto;
}

export type PropsIcono = {
  nombre: NombreIcono;
  /** Alto en px (56 en los pisos, 64 en filas, 96 en tarjetas…). */
  alto: number;
  x: number;
  y: number;
  /** x es el centro (por defecto), el borde izquierdo o el derecho; y es siempre el centro. */
  ancla?: "centro" | "izq" | "der";
  color?: string;
  opacidad?: number;
  estilo?: Estilo;
};

/**
 * Ícono de manim/comun/iconos (Font Awesome Free solid, el mismo SVG que usa Manim),
 * monocromo. Los tres de los pisos son un sistema: user = para quién, shield-halved =
 * prueba, hand = pedido (ICONOS.pisos).
 */
export const Icono: React.FC<PropsIcono> = ({ nombre, alto, x, y, ancla = "centro", color = COLOR.hueso, opacidad = 1, estilo }) => {
  const i = ICONOS_SVG[nombre];
  if (!i) throw new Error(`Icono: «${nombre}» no está en manim/comun/iconos (correr node remotion/generar_registro.mjs después de agregarlo).`);
  const ambar = useAtenuarAmbar();
  const w = anchoIcono(nombre, alto);
  const izquierda = ancla === "centro" ? x - w / 2 : ancla === "izq" ? x : x - w;
  return (
    <svg
      width={w}
      height={alto}
      viewBox={`0 0 ${i.ancho} ${i.alto}`}
      style={{
        position: "absolute",
        left: izquierda,
        top: y - alto / 2,
        overflow: "visible",
        transformOrigin: "50% 50%",
        ...estilo,
        opacity: opacidad * (color === COLOR.ambar ? ambar : 1) * (estilo?.opacity !== undefined ? Number(estilo.opacity) : 1),
      }}
    >
      <path d={i.d} fill={color} />
    </svg>
  );
};
