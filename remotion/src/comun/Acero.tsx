// Acero cepillado de puertas, paneles y cabina: la hoja va de acero2 (del lado de la pared) a
// aceroclaro (#4A586F, hacia la junta), con un brillo metálico suave al 45 % del ancho y el canto
// claro del lado de la junta, separado de la luz por un filete oscuro. Lo usan las Puertas de
// capítulo, los Paneles de D06.2, el Ascensor de frente y la cabina del corte: el acero es uno solo.
//
// Hallazgos de la revisión (convenciones §13): sin la segunda costura al 30 % del ancho ni la banda
// marcada al 62 % (parecían un ropero o una cortina); con aceroclaro (2,75:1) y el canto al 50 %
// las hojas se leen como objetos desde el fondo de la sala. Las hojas de menos de 200 px de alto
// van planas (acero2, canto y junta): con 105 px de alto, cualquier franja las volvía una barra
// borrosa.
import React from "react";
import { BRILLO, COLOR, conAlfa, GROSOR, OPACIDAD } from "../tokens";

/** Alto desde el que una hoja lleva degradé y brillo; las más bajas van planas. */
export const ALTO_HOJA_PLANA = 200;

/**
 * Una hoja de acero como grupo SVG. `junta` es el lado que da a la otra hoja (el más claro,
 * con su canto). `nucleo`: el ancho de la luz de la junta que tapa ese borde (GROSOR.junta por
 * defecto; 3 en la cabina): el filete oscuro empieza donde termina.
 */
export const PanelAcero: React.FC<{ x: number; y: number; ancho: number; alto: number; junta: "izq" | "der"; idBase: string; nucleo?: number }> = ({
  x,
  y,
  ancho,
  alto,
  junta,
  idBase,
  nucleo = GROSOR.junta,
}) => {
  const id = `${idBase}-${junta}`;
  const plana = alto < ALTO_HOJA_PLANA;
  const desdeJunta = (f: number) => (junta === "der" ? x + ancho * (1 - f) : x + ancho * f);
  // Canto claro (4 px; menos en una hoja muy angosta) y, entre el canto y la luz, un filete de sombra.
  const canto = Math.min(GROSOR.canto_puerta, Math.max(2, ancho * 0.03));
  const filete = Math.min(2, Math.max(1, ancho * 0.015));
  const sombra = nucleo / 2 + filete;
  const xSombra = junta === "der" ? x + ancho - sombra : x;
  const xCanto = junta === "der" ? x + ancho - sombra - canto : x + sombra;
  const banda = ancho * 0.26;
  const xBanda = desdeJunta(0.45) - banda / 2;
  return (
    <g>
      {plana ? (
        <rect x={x} y={y} width={ancho} height={alto} fill={COLOR.acero2} />
      ) : (
        <>
          <defs>
            <linearGradient id={id} x1={junta === "der" ? 0 : 1} x2={junta === "der" ? 1 : 0} y1={0} y2={0}>
              <stop offset="0" stopColor={COLOR.acero2} />
              <stop offset="1" stopColor={COLOR.aceroclaro} />
            </linearGradient>
            <linearGradient id={`${id}-b`} x1={0} x2={1} y1={0} y2={0}>
              <stop offset="0" stopColor={COLOR.hueso} stopOpacity={0} />
              <stop offset="0.5" stopColor={COLOR.hueso} stopOpacity={OPACIDAD.banda_puerta} />
              <stop offset="1" stopColor={COLOR.hueso} stopOpacity={0} />
            </linearGradient>
            <linearGradient id={`${id}-v`} x1={0} x2={0} y1={0} y2={1}>
              <stop offset="0" stopColor={COLOR.hueso} stopOpacity={0.05} />
              <stop offset="0.5" stopColor={COLOR.hueso} stopOpacity={0} />
              <stop offset="1" stopColor={COLOR.tinta} stopOpacity={0.18} />
            </linearGradient>
          </defs>
          <rect x={x} y={y} width={ancho} height={alto} fill={`url(#${id})`} />
          <rect x={x} y={y} width={ancho} height={alto} fill={`url(#${id}-v)`} />
          <rect x={xBanda} y={y} width={banda} height={alto} fill={`url(#${id}-b)`} />
        </>
      )}
      {/* canto de la hoja (el filo claro) y la sombra pegada a la junta */}
      <rect x={xCanto} y={y} width={canto} height={alto} fill={conAlfa(COLOR.hueso, OPACIDAD.canto_puerta)} />
      <rect x={xSombra} y={y} width={sombra} height={alto} fill={conAlfa(COLOR.tinta, 0.6)} />
    </g>
  );
};

/**
 * La línea de luz ámbar de la junta, con su brillo (el único resplandor permitido además del
 * visor). El núcleo va siempre en ámbar pleno: `opacidad` es el NIVEL de la luz. Hasta
 * OPACIDAD.junta_reposo (0,4) el nivel solo enciende o apaga el núcleo (para los fundidos); de
 * ahí para arriba crece solo el brillo: reposo 0,4, lista 0,7, capítulo 1. (Con la opacidad en
 * todo el grupo, el núcleo en reposo salía (115, 88, 50): una veta de óxido, no una luz.)
 */
export const Junta: React.FC<{ x: number; y0: number; y1: number; ancho?: number; opacidad: number; idBase: string; brillo?: boolean }> = ({
  x,
  y0,
  y1,
  ancho = GROSOR.junta,
  opacidad,
  idBase,
  brillo = true,
}) => {
  if (opacidad <= 0) return null;
  const id = `${idBase}-j`;
  const nucleo = Math.min(1, opacidad / OPACIDAD.junta_reposo);
  return (
    <g>
      {brillo && (
        <>
          <defs>
            <filter id={id} x="-400%" y="-10%" width="900%" height="120%">
              <feGaussianBlur stdDeviation={BRILLO.junta.radio_px / 2} />
            </filter>
          </defs>
          <rect x={x - ancho} y={y0} width={ancho * 2} height={y1 - y0} fill={COLOR.ambar} filter={`url(#${id})`} opacity={BRILLO.junta.opacidad * Math.min(1, opacidad)} />
        </>
      )}
      <rect x={x - ancho / 2} y={y0} width={ancho} height={y1 - y0} fill={COLOR.ambar} opacity={nucleo} />
    </g>
  );
};

/** Sombra que la hoja proyecta sobre lo que tapa (solo las puertas de capítulo). */
export const SombraHoja: React.FC<{ x: number; y: number; alto: number; hacia: "izq" | "der"; idBase: string; ancho?: number }> = ({ x, y, alto, hacia, idBase, ancho = 48 }) => {
  const id = `${idBase}-s${hacia}`;
  return (
    <g>
      <defs>
        <linearGradient id={id} x1={hacia === "der" ? 0 : 1} x2={hacia === "der" ? 1 : 0} y1={0} y2={0}>
          <stop offset="0" stopColor={COLOR.tinta} stopOpacity={0.55} />
          <stop offset="1" stopColor={COLOR.tinta} stopOpacity={0} />
        </linearGradient>
      </defs>
      <rect x={hacia === "der" ? x : x - ancho} y={y} width={ancho} height={alto} fill={`url(#${id})`} />
    </g>
  );
};
