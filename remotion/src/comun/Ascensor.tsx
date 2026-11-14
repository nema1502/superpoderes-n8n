import { evolvePath } from "@remotion/paths";
import React from "react";
import { ASCENSOR_FRENTE, COLOR, conAlfa, GROSOR, OPACIDAD, VISOR } from "../tokens";
import { Junta, PanelAcero } from "./Acero";
import { useIdSvg, VisorCaja, type PropsTriangulo } from "./Visor7";

const M = ASCENSOR_FRENTE.marco;
const V = ASCENSOR_FRENTE.visor;
const CAJA = VISOR.caja_ascensor;

export type VisorAscensor = {
  texto: string;
  encendido?: number;
  anterior?: string;
  cambio?: number;
  triangulo?: Omit<PropsTriangulo, "tam">;
};

export type PropsAscensor = {
  /** El hueco de la puerta (el marco). Por defecto, el de la portada: x 170-730, y 230-950. */
  marco?: { x0: number; y0: number; x1: number; y1: number };
  /** 0 = puertas cerradas, 1 = abiertas del todo (entran en la pared). */
  apertura?: number;
  /**
   * Nivel de la luz de la junta: 0,4 en reposo, 0,7 «listo para subir». El núcleo va en ámbar
   * pleno desde 0,4; por debajo, el nivel lo enciende (D01: junta_reposo × encendido).
   */
  junta?: number;
  /** 0 → 1: el marco se dibuja (Trazo). */
  trazoMarco?: number;
  /** El visor de arriba (null: sin visor). */
  visor?: VisorAscensor | null;
  opacidad?: number;
  /** Lo que se ve detrás de las puertas al abrirse, en coordenadas del cuadro (se recorta al hueco). */
  detras?: React.ReactNode;
};

/**
 * Ascensor de frente: marco en hueso al 50 % (OPACIDAD.marco), dos puertas de acero (de acero2 a
 * aceroclaro hacia la junta, con su canto claro) y la junta con su luz ámbar; arriba, el visor de
 * vidrio con «Pb» en 7 segmentos de 56 px y el ▲. Todo escala con el ancho del marco (560 px =
 * escala 1): en D04 va a 0,75 (marco x 140-560, y 290-830).
 */
export const Ascensor: React.FC<PropsAscensor> = ({
  marco = M,
  apertura = 0,
  junta = OPACIDAD.junta_reposo,
  trazoMarco = 1,
  visor = { texto: "Pb", triangulo: { encendido: 0 } },
  opacidad = 1,
  detras,
}) => {
  const idBase = useIdSvg("as");
  const k = (marco.x1 - marco.x0) / (M.x1 - M.x0);
  const fw = GROSOR.marco_ascensor * k;
  const xm = (marco.x0 + marco.x1) / 2;
  const hx0 = marco.x0 + fw / 2;
  const hx1 = marco.x1 - fw / 2;
  const hy0 = marco.y0 + fw / 2;
  const hy1 = marco.y1;
  const hoja = xm - hx0;
  const a = Math.max(0, Math.min(1, apertura));
  const camino = `M ${marco.x0} ${marco.y1} L ${marco.x0} ${marco.y0} L ${marco.x1} ${marco.y0} L ${marco.x1} ${marco.y1}`;
  const ev = evolvePath(trazoMarco, camino);
  const sill = 34 * k;
  const clip = `${idBase}-h`;
  const visorCy = marco.y0 - (M.y0 - (V.y0 + V.y1) / 2) * k;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: opacidad }}>
      {detras && a > 0 && (
        <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(${hy0}px ${1920 - hx1}px ${1080 - hy1}px ${hx0}px)` }}>{detras}</div>
      )}
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        <defs>
          <clipPath id={clip}>
            <rect x={hx0} y={hy0} width={hx1 - hx0} height={hy1 - hy0} />
          </clipPath>
        </defs>
        {a < 1 && (
          <g clipPath={`url(#${clip})`}>
            <PanelAcero x={hx0 - hoja * a} y={hy0} ancho={hoja} alto={hy1 - hy0} junta="der" idBase={idBase} nucleo={GROSOR.junta * k} />
            <PanelAcero x={xm + hoja * a} y={hy0} ancho={hoja} alto={hy1 - hy0} junta="izq" idBase={idBase} nucleo={GROSOR.junta * k} />
            <Junta x={xm} y0={hy0} y1={hy1} ancho={GROSOR.junta * k} opacidad={junta * Math.max(0, 1 - a * 8)} idBase={idBase} />
          </g>
        )}
        {trazoMarco > 0 && (
          <path
            d={camino}
            fill="none"
            stroke={conAlfa(COLOR.hueso, OPACIDAD.marco)}
            strokeWidth={fw}
            strokeLinejoin="miter"
            strokeDasharray={ev.strokeDasharray}
            strokeDashoffset={ev.strokeDashoffset}
          />
        )}
        {trazoMarco > 0 && (
          <line
            x1={marco.x0 - sill}
            x2={marco.x0 - sill + (marco.x1 - marco.x0 + 2 * sill) * Math.min(1, trazoMarco)}
            y1={marco.y1 + fw * 0.3}
            y2={marco.y1 + fw * 0.3}
            stroke={conAlfa(COLOR.hueso, OPACIDAD.marco)}
            strokeWidth={fw * 0.6}
          />
        )}
      </svg>
      {visor && (
        <VisorCaja
          cx={xm}
          cy={visorCy}
          ancho={CAJA.ancho * k}
          alto={CAJA.alto * k}
          digito={CAJA.digito * k}
          triangulo={{ tam: CAJA.triangulo * k, ...(visor.triangulo ?? { encendido: 0 }) }}
          texto={visor.texto}
          encendido={visor.encendido}
          anterior={visor.anterior}
          cambio={visor.cambio}
        />
      )}
    </div>
  );
};
