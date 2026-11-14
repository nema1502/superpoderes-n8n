import React from "react";
import { interpolate } from "remotion";
import { ALTO, ANCHO, CURVA, FPS, MOV, OPACIDAD, TRANSICIONES } from "../tokens";
import { Junta, PanelAcero, SombraHoja } from "./Acero";
import { useIdSvg } from "./Visor7";

const P = TRANSICIONES.puertas;

/** Cuadros de cada etapa de las puertas de capítulo: se juntan, quedan cerradas, se abren. */
export const CUADROS_PUERTAS = {
  cierran: Math.round(P.cierran_s * FPS),
  cerradas: Math.round(P.cerradas_s * FPS),
  abren: Math.round(P.abren_s * FPS),
};

/**
 * Cuánto están cerradas las puertas de capítulo en el cuadro f de la transición
 * (0 = abiertas, 1 = cerradas): se juntan en 0,45 s (inOut cúbica), quedan 0,1 s y se
 * abren en 0,5 s (out cúbica). `estirar` reparte otra duración total en la misma proporción.
 */
export function cierrePuertas(f: number, total?: number): { cierre: number; abriendo: boolean } {
  const { cierran, cerradas, abren } = CUADROS_PUERTAS;
  const base = cierran + cerradas + abren;
  const k = total ? total / base : 1;
  const a = cierran * k;
  const b = (cierran + cerradas) * k;
  const c = base * k;
  if (f <= a) return { cierre: interpolate(f, [0, a], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.suave }), abriendo: false };
  if (f <= b) return { cierre: 1, abriendo: false };
  return { cierre: 1 - interpolate(f, [b, c], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.sale }), abriendo: true };
}

/**
 * Puertas de capítulo: dos paneles de acero de 960×1080 que entran desde los costados y
 * se juntan, con la línea de luz ámbar de la junta (GROSOR.junta, 6 px, núcleo pleno). Solo en
 * D14.1, D18.1 y D20.1 (las arma la transición «puertas»; ver remotion/transicion.mjs). La
 * marca de agua queda por encima.
 */
export const Puertas: React.FC<{ cierre: number }> = ({ cierre }) => {
  const idBase = useIdSvg("pu");
  const c = Math.max(0, Math.min(1, cierre));
  if (c <= 0) return null;
  const mitad = ANCHO / 2;
  const hueco = 2 * mitad * (1 - c);
  const luz = Math.max(0, 1 - hueco / 60) * OPACIDAD.junta_capitulo;
  const bordeIzq = mitad * c;
  const bordeDer = ANCHO - mitad * c;
  return (
    <svg width={ANCHO} height={ALTO} style={{ position: "absolute", left: 0, top: 0 }}>
      {hueco > 2 && (
        <>
          <SombraHoja x={bordeIzq} y={0} alto={ALTO} hacia="der" idBase={idBase} ancho={Math.min(48, hueco / 2)} />
          <SombraHoja x={bordeDer} y={0} alto={ALTO} hacia="izq" idBase={idBase} ancho={Math.min(48, hueco / 2)} />
        </>
      )}
      <PanelAcero x={-mitad * (1 - c)} y={0} ancho={mitad} alto={ALTO} junta="der" idBase={idBase} />
      <PanelAcero x={mitad + mitad * (1 - c)} y={0} ancho={mitad} alto={ALTO} junta="izq" idBase={idBase} />
      <Junta x={mitad} y0={0} y1={ALTO} opacidad={luz} idBase={idBase} />
    </svg>
  );
};

/**
 * Paneles (D06.2): dos paneles chicos de acero, del alto de un renglón, tapan un texto
 * y se separan como puertas (0,5 s), desvaneciéndose en sus últimos 0,15 s. `progreso`
 * 0 = cerrados, 1 = abiertos y ya invisibles. Se dibujan ENCIMA del texto que tapan. Son hojas
 * bajas: acero2 plano con su canto y la junta, sin banda (PanelAcero).
 */
export const Paneles: React.FC<{ x: number; y: number; ancho: number; alto: number; progreso: number }> = ({ x, y, ancho, alto, progreso }) => {
  const idBase = useIdSvg("pa");
  const p = Math.max(0, Math.min(1, progreso));
  if (p >= 1) return null;
  const dur = MOV.dura.paneles;
  const fundido = MOV.dura.paneles_fundido_final / dur;
  const opacidad = p < 1 - fundido ? 1 : (1 - p) / fundido;
  const mitad = ancho / 2;
  const abierto = CURVA.suave(p);
  const clip = `${idBase}-r`;
  const x0 = x - ancho / 2;
  const y0 = y - alto / 2;
  return (
    <svg width={ANCHO} height={ALTO} style={{ position: "absolute", left: 0, top: 0, opacity: opacidad }}>
      <defs>
        <clipPath id={clip}>
          <rect x={x0} y={y0} width={ancho} height={alto} rx={6} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${clip})`}>
        <PanelAcero x={x0 - mitad * abierto} y={y0} ancho={mitad} alto={alto} junta="der" idBase={idBase} />
        <PanelAcero x={x0 + mitad + mitad * abierto} y={y0} ancho={mitad} alto={alto} junta="izq" idBase={idBase} />
        <Junta x={x} y0={y0} y1={y0 + alto} opacidad={Math.max(0, 1 - abierto * 6)} idBase={idBase} />
      </g>
    </svg>
  );
};
