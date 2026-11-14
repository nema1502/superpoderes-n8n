// La marca nemaxyz: el isotipo es una N
// de UN SOLO TRAZO abierto, que entra por abajo a la izquierda y sale por arriba a la
// derecha. Un color plano, sin relleno, sin rotar, sin degradés ni sombras. El grosor
// sale del tamaño: max(4 px, 4,5 % del alto) (el mismo que marca_nema() de Manim).
// El verde lima es SOLO de la marca: isotipo, marca de agua y firma.
import { evolvePath, getLength } from "@remotion/paths";
import React from "react";
import { useEntra, useTramo } from "../pasos";
import { COLOR, conAlfa, CURVA, GROSOR, MOV, OPACIDAD, RESORTE, RETICULA, TIPO } from "../tokens";
import { medirTexto } from "./Texto";

/** La N de comun/estilo.py (marca_nema), ×100 y con el eje y hacia abajo: 300 × 180. */
export const N_PATH = "M -150 90 L -75 90 L -75 -90 L 75 90 L 75 -90 L 150 -90";
const N_ANCHO = 300;
const N_ALTO = 180;
const N_LARGO = getLength(N_PATH);

/** Grosor del trazo de la N según su alto (px): max(4, 4,5 % del alto). */
export function grosorIsotipo(alto: number): number {
  return Math.max(GROSOR.isotipo_minimo, alto * GROSOR.isotipo_por_alto);
}

/** Ancho del isotipo (línea media, sin el grosor) para un alto dado. */
export function anchoIsotipo(alto: number): number {
  return (alto * N_ANCHO) / N_ALTO;
}

export type PropsIsotipo = {
  /** Alto de la N en px (mínimo 48). */
  alto: number;
  /** Esquina de arriba a la izquierda de la N (su línea media, como el bbox de Manim). */
  x: number;
  y: number;
  /** 0 → 1: se dibuja de un trazo (como Create() en Manim); por encima de 1 se borra desde el comienzo. */
  progreso?: number;
  color?: string;
  /** Opacidad del trazo (nunca relleno). */
  opacidad?: number;
  /** Grosor en px (por defecto, el de la regla de la marca). */
  grosor?: number;
};

/** El isotipo: la N de un solo trazo. */
export const Isotipo: React.FC<PropsIsotipo> = ({ alto, x, y, progreso = 1, color = COLOR.marca, opacidad = 1, grosor }) => {
  const k = alto / N_ALTO;
  const g = (grosor ?? grosorIsotipo(alto)) / k;
  const ev = evolvePath(progreso, N_PATH);
  const m = g; // margen para el grosor y las uniones en punta
  return (
    <svg
      width={(N_ANCHO + 2 * m) * k}
      height={(N_ALTO + 2 * m) * k}
      viewBox={`${-N_ANCHO / 2 - m} ${-N_ALTO / 2 - m} ${N_ANCHO + 2 * m} ${N_ALTO + 2 * m}`}
      style={{ position: "absolute", left: x - m * k, top: y - m * k, overflow: "visible" }}
    >
      {progreso > 0 && (
        <path
          d={N_PATH}
          fill="none"
          stroke={color}
          strokeOpacity={opacidad}
          strokeWidth={g}
          strokeLinejoin="miter"
          strokeMiterlimit={4}
          strokeLinecap="butt"
          strokeDasharray={ev.strokeDasharray}
          strokeDashoffset={ev.strokeDashoffset}
        />
      )}
    </svg>
  );
};

export type PropsLogotipo = {
  /** Alto del isotipo en px. */
  alto: number;
  /** Esquina de arriba a la izquierda del isotipo. */
  x: number;
  y: number;
  /** Tamaño de la palabra (por defecto, igual al alto del isotipo). */
  tamTexto?: number;
  /** La palabra: «nemaxyz» (siempre en minúsculas) o «nemaxyz · Nicolás Mejía». */
  texto?: string;
  colorTexto?: string;
  colorIsotipo?: string;
  /** Separación entre la N y la palabra (por defecto 0,45 × alto, como logotipo_nema()). */
  separacion?: number;
  opacidad?: number;
  progresoIsotipo?: number;
  /** Opacidad de la palabra (aparece después de dibujarse la N). */
  opacidadTexto?: number;
};

/** Ancho total del logotipo (isotipo + separación + palabra). */
export function anchoLogotipo(alto: number, texto = "nemaxyz", tamTexto = alto, separacion = alto * 0.45): number {
  return anchoIsotipo(alto) + separacion + medirTexto(texto, tamTexto);
}

/**
 * Isotipo + palabra. La palabra queda centrada en la altura de la x con el centro de
 * la N (las minúsculas se ven centradas; la «y» cuelga).
 */
export const Logotipo: React.FC<PropsLogotipo> = ({
  alto,
  x,
  y,
  tamTexto,
  texto = "nemaxyz",
  colorTexto = COLOR.hueso,
  colorIsotipo = COLOR.marca,
  separacion,
  opacidad = 1,
  progresoIsotipo = 1,
  opacidadTexto = 1,
}) => {
  const tam = tamTexto ?? alto;
  const sep = separacion ?? alto * 0.45;
  const xTexto = x + anchoIsotipo(alto) + sep;
  // Con line-height = tam, el centro de la altura de la x queda 0,164 em debajo del
  // centro de la caja (Segoe UI: ascendente 1,079 em, descendente 0,251 em, x = 0,5 em).
  const centroX = 0.164 * tam;
  const top = y + alto / 2 - tam / 2 - centroX;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: opacidad }}>
      <Isotipo alto={alto} x={x} y={y} color={colorIsotipo} progreso={progresoIsotipo} />
      <div
        style={{
          position: "absolute",
          left: xTexto,
          top,
          height: tam,
          lineHeight: `${tam}px`,
          fontFamily: TIPO.familia,
          fontWeight: TIPO.peso,
          fontSize: tam,
          whiteSpace: "pre",
          color: colorTexto,
          opacity: opacidadTexto,
        }}
      >
        {texto}
      </div>
    </div>
  );
};

const MA = RETICULA.marca_agua;

/**
 * Marca de agua: isotipo lima de 48 px + «nemaxyz» en hueso a 34 px, al 72 %, arriba a la
 * izquierda (x 67-300, y 38-86). En todos los pasos menos D01, D02.1, D02.2, D03 y D20.3
 * (tokens.json → persistentes). La pone el sistema; nada más se dibuja en su zona.
 */
export const MarcaAgua: React.FC<{ opacidad?: number }> = ({ opacidad = 1 }) =>
  opacidad <= 0 ? null : (
    <Logotipo alto={MA.alto_isotipo} x={MA.x} y={MA.y} tamTexto={MA.texto_px} separacion={MA.separacion} opacidad={OPACIDAD.marca_agua * opacidad} />
  );

// ---------- Firma (D20.3) ----------

export type EstadoFirma = {
  /** 0 → 1: el hilo entra desde abajo a la izquierda y dibuja la N (en ámbar, grosor del cable). */
  hilo: number;
  /** 0 → 1: la N pasa entera a lima y al grosor de la marca; la cola se recoge. */
  lima: number;
  /** 0 → 1: aparece «nema». */
  nema: number;
  /** 0 → 1 cada una: «x», «y», «z» bajan 40 px a su lugar (resorte, sin rebote). */
  xyz: [number, number, number];
  /** 0 → 1: x, y, z pasan de ámbar a hueso. */
  xyzHueso: number;
  /** 0 → 1: aparece «@nemaxyz» en lima. */
  arroba: number;
};

export const FIRMA_COMPLETA: EstadoFirma = { hilo: 1, lima: 1, nema: 1, xyz: [1, 1, 1], xyzHueso: 1, arroba: 1 };

/**
 * Tiempos de la firma de D20.3 (≤ 4 s): hilo 1,0 s; lima 0,3 s; «nema» 0,3 s; x, y, z
 * con desfase 0,1 s; a hueso 0,3 s; «@nemaxyz» 0,3 s. `retraso` = cuándo arranca el hilo.
 */
export function useFirma(paso: number, retraso = 0): EstadoFirma {
  const hilo = useTramo(paso, retraso, 1.0, CURVA.suave);
  const lima = useTramo(paso, retraso + 1.0, 0.3, CURVA.suave);
  const nema = useTramo(paso, retraso + 1.25, 0.3, CURVA.fundido);
  const x = useEntra(paso, retraso + 1.45, 0.5, RESORTE.entrar);
  const yy = useEntra(paso, retraso + 1.55, 0.5, RESORTE.entrar);
  const z = useEntra(paso, retraso + 1.65, 0.5, RESORTE.entrar);
  const xyzHueso = useTramo(paso, retraso + 2.15, 0.3, CURVA.suave);
  const arroba = useTramo(paso, retraso + 2.35, 0.3, CURVA.fundido);
  return { hilo, lima, nema, xyz: [Math.min(1, x), Math.min(1, yy), Math.min(1, z)], xyzHueso, arroba };
}

function mezclaHex(a: string, b: string, k: number): string {
  const ca = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const cb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `rgb(${ca.map((v, i) => Math.round(v + (cb[i] - v) * k)).join(",")})`;
}

/**
 * La firma del cierre: el cable de la cabina (un hilo ámbar) entra desde abajo a la
 * izquierda, dibuja la N, la N pasa de una vez a lima y aparece «nema» + x, y, z (las
 * incógnitas, que bajan a su lugar) y «@nemaxyz». Cuadro final: isotipo de 96 px +
 * «nemaxyz» a 96 px centrados juntos en `cy`, «@nemaxyz» a 60 px en lima 120 px abajo.
 */
export const Firma: React.FC<{
  estado: EstadoFirma;
  cx?: number;
  cy?: number;
  alto?: number;
  arroba?: string | null;
  arrobaY?: number;
  /** De dónde sale el hilo, relativo al comienzo de la N (por defecto, fuera de cuadro abajo a la izquierda). */
  cola?: [number, number];
}> = ({ estado, cx = 960, cy = 640, alto = 96, arroba = "@nemaxyz", arrobaY, cola: desdeCola }) => {
  const tam = alto;
  const sep = alto * 0.45;
  const wTotal = anchoLogotipo(alto, "nemaxyz", tam, sep);
  const x0 = cx - wTotal / 2;
  const y0 = cy - alto / 2;
  const k = alto / N_ALTO;
  // Cola: de abajo a la izquierda (fuera de cuadro) al comienzo de la N, llegando en horizontal.
  const nx = x0;
  const ny = y0 + alto;
  const [cdx, cdy] = desdeCola ?? [-520, 1130 - ny];
  const cola = `M ${nx + cdx} ${ny + cdy} C ${nx + cdx * 0.9} ${ny + Math.min(40, cdy * 0.15)}, ${nx + cdx * 0.5} ${ny}, ${nx} ${ny}`;
  const largoCola = getLength(cola);
  const largoN = N_LARGO * k;
  const dibujado = Math.max(0, Math.min(1, estado.hilo)) * (largoCola + largoN);
  const pCola = Math.min(1, dibujado / largoCola) + Math.max(0, Math.min(1, estado.lima));
  const pN = Math.max(0, Math.min(1, (dibujado - largoCola) / largoN));
  const grosorCable = GROSOR.cable_cabina;
  const grosor = grosorCable + (grosorIsotipo(alto) - grosorCable) * estado.lima;
  const colorN = estado.lima <= 0 ? COLOR.ambar : estado.lima >= 1 ? COLOR.marca : mezclaHex(COLOR.ambar, COLOR.marca, estado.lima);
  const evCola = evolvePath(Math.min(2, pCola), cola);
  const xTexto = x0 + anchoIsotipo(alto) + sep;
  const centroX = 0.164 * tam;
  const top = cy - tam / 2 - centroX;
  const anchoNema = medirTexto("nema", tam);
  const anchoX = medirTexto("nemax", tam) - anchoNema;
  const anchoY = medirTexto("nemaxy", tam) - anchoNema - anchoX;
  const colorXyz = estado.xyzHueso <= 0 ? COLOR.ambar : estado.xyzHueso >= 1 ? COLOR.hueso : mezclaHex(COLOR.ambar, COLOR.hueso, estado.xyzHueso);
  const letra: React.CSSProperties = {
    position: "absolute",
    top,
    height: tam,
    lineHeight: `${tam}px`,
    fontFamily: TIPO.familia,
    fontWeight: TIPO.peso,
    fontSize: tam,
    whiteSpace: "pre",
  };
  const completa = estado.xyz.every((v) => v >= 1) && estado.xyzHueso >= 1 && estado.nema >= 1;
  const caida = MOV.distancia.xyz;
  return (
    <>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        {pCola > 0 && pCola < 2 && (
          <path d={cola} fill="none" stroke={COLOR.ambar} strokeWidth={grosorCable} strokeLinecap="butt" strokeDasharray={evCola.strokeDasharray} strokeDashoffset={evCola.strokeDashoffset} />
        )}
      </svg>
      {pN > 0 && <Isotipo alto={alto} x={x0} y={y0} progreso={pN} color={colorN} grosor={grosor} />}
      {completa ? (
        <div style={{ ...letra, left: xTexto, color: COLOR.hueso }}>nemaxyz</div>
      ) : (
        <>
          {estado.nema > 0 && <div style={{ ...letra, left: xTexto, color: COLOR.hueso, opacity: estado.nema }}>nema</div>}
          {(["x", "y", "z"] as const).map((l, i) => {
            const p = estado.xyz[i];
            if (p <= 0) return null;
            const dx = anchoNema + (i > 0 ? anchoX : 0) + (i > 1 ? anchoY : 0);
            return (
              <div key={l} style={{ ...letra, left: xTexto + dx, color: colorXyz, opacity: Math.min(1, 1.5 * p), transform: `translateY(${-(1 - p) * caida}px)` }}>
                {l}
              </div>
            );
          })}
        </>
      )}
      {arroba && estado.arroba > 0 && (
        <div
          style={{
            position: "absolute",
            left: cx - 960,
            width: 1920,
            top: (arrobaY ?? cy + 120) - TIPO.escala.lectura / 2 - TIPO.correccionOpticaEm * TIPO.escala.lectura,
            height: TIPO.escala.lectura,
            lineHeight: `${TIPO.escala.lectura}px`,
            textAlign: "center",
            fontFamily: TIPO.familia,
            fontWeight: TIPO.peso,
            fontSize: TIPO.escala.lectura,
            color: conAlfa(COLOR.marca, estado.arroba),
          }}
        >
          {arroba}
        </div>
      )}
    </>
  );
};
