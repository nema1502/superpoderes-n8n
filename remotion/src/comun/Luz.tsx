// Luz: la capa común de luz y movimiento de la charla. Piezas chicas para que lo que se
// nombra se encienda, el dato viaje con luz y el lugar tenga profundidad, sin tocar textos ni tiempos.
//
//   <FondoVivo />                         el PNG del fondo (estrellas y pistas), igual que FondoCircuito
//   <FondoVivo pulsos />                  más dos destellos por las pistas en cada paso
//   <FondoVivo pulsos={[1, 3]} />         solo en esos pasos
//   <FondoVivo luz={k} />                 k de 0 a 1 multiplica el fondo y los pulsos: apagar las luces
//   <FondoVivo variante="estrellas" />    solo las estrellas (D01, que dibuja sus pistas)
//   brillo(color, k, tam)                 boxShadow de tres capas para lo activo (undefined con k 0)
//   filtroBrillo(color, k)                lo mismo para SVG, como filter
//   useDestello(paso, retraso, dura)      0, sube a 1 y vuelve a 0: un fogonazo
//   <Aro ... />                           un aro que crece y se apaga desde el borde de algo que llega
//   <DatoViajero d progreso ... />        el dato ámbar con brillo y estela (el contrato de PuntoDato de D06)
//   <PuntaLuz d progreso />               la chispa en la punta de un trazo que se dibuja
//   <Camara paso ...>...</Camara>         acercamiento suave del contenido (nunca del fondo)
//
// Reglas que respetan todas: el primer y el último cuadro de cada paso no cambian (frontera y
// quietud), nada termina después de lo que se pide, y nada es verde ni turquesa (lima). Cuándo se
// permite cada brillo: docs/convenciones.md.
import { getLength, getPointAtLength } from "@remotion/paths";
import React from "react";
import { Img, staticFile, useCurrentFrame } from "remotion";
import { usePasos, useTramo } from "../pasos";
import { COLOR, conAlfa, CURVA, FPS, RESPIRO_S } from "../tokens";
import { Capa } from "./movimiento";
import { PISTAS_FONDO } from "./pistasFondo.generado";

/** El PNG del fondo (diseno/medios/D01/generar_fondo.py): estrellas y pistas. */
export const FONDO_VIVO = "medios/D01/fondo_circuito.png";
/** Las mismas estrellas, sin pistas (para la portada). */
export const FONDO_ESTRELLAS = "medios/D01/fondo_estrellas.png";

const pantalla: React.CSSProperties = { position: "absolute", left: 0, top: 0, width: 1920, height: 1080 };
const svgPantalla: React.CSSProperties = { position: "absolute", left: 0, top: 0, overflow: "visible" };
const entre01 = (v: number) => Math.max(0, Math.min(1, v));

// ---------------------------------------------------------------------------------------------
// La luz de lo activo
// ---------------------------------------------------------------------------------------------

/**
 * boxShadow de tres capas para un nodo o una tarjeta encendida: 0 0 8px al 80 %, 0 0 24px al 50 % y
 * 0 0 60px al 25 % del color, todo por k (0 a 1) y los radios por tam. Con k 0, undefined (nada).
 * Un nodo con brillo queda a más de 60 px del borde de la zona segura.
 */
export function brillo(color: string, k: number, tam = 1): string | undefined {
  if (!(k > 0)) return undefined;
  const r = (px: number) => `${Math.round(px * tam * 10) / 10}px`;
  return `0 0 ${r(8)} ${conAlfa(color, 0.8 * k)}, 0 0 ${r(24)} ${conAlfa(color, 0.5 * k)}, 0 0 ${r(60)} ${conAlfa(color, 0.25 * k)}`;
}

/** El brillo para SVG (style.filter): drop-shadow de 6 px al 80 % y de 18 px al 40 %, por k. */
export function filtroBrillo(color: string, k: number): string | undefined {
  if (!(k > 0)) return undefined;
  return `drop-shadow(0 0 6px ${conAlfa(color, 0.8 * k)}) drop-shadow(0 0 18px ${conAlfa(color, 0.4 * k)})`;
}

/** Un fogonazo: 0, sube a 1 a la mitad y vuelve a 0 (seno) en `dura` s desde `retraso`. */
export function useDestello(paso: number, retraso: number, dura = 0.45): number {
  return Math.sin(Math.PI * useTramo(paso, retraso, dura, CURVA.lineal));
}

// ---------------------------------------------------------------------------------------------
// El fondo con pulsos
// ---------------------------------------------------------------------------------------------

export type PropsFondoVivo = {
  /** true: dos destellos por paso en todos los pasos. Una lista: solo en esos pasos. */
  pulsos?: boolean | number[];
  /** De 0 a 1: multiplica la opacidad del fondo y de los pulsos (apagar las luces). */
  luz?: number;
  /** "circuito" (estrellas y pistas) o "estrellas" (solo estrellas, para D01). */
  variante?: "circuito" | "estrellas";
};

/** Los tiempos de un destello, en s desde el comienzo del paso. */
const PULSO = {
  arranques: [0.15, 0.35],
  viaje: 0.9,
  latido: 0.2,
  fin: 1.45,
  tramos: [
    { largo: 140, alfa: 0.25 },
    { largo: 80, alfa: 0.5 },
    { largo: 30, alfa: 0.9 },
  ],
  trazo: 3,
  punta: 4,
  sombraPunta: 8,
  punto: { desde: 5, hasta: 9, alfa: 0.8 },
};

type Pista = { pts: [number, number][]; d: string; largo: number };
const aPista = (pts: [number, number][]): Pista => {
  const d = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
  let largo = 0;
  for (let i = 1; i < pts.length; i++) largo += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return { pts, d, largo };
};
/** Cuánto de la pista se ve (dentro de la zona segura, con 10 px de margen por la rampa del PNG). */
function largoVisible(pts: [number, number][]): number {
  let n = 0;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const l = Math.hypot(x1 - x0, y1 - y0);
    for (let d = 0; d < l; d += 2) {
      const x = x0 + ((x1 - x0) * d) / l;
      const y = y0 + ((y1 - y0) * d) / l;
      if (x >= 77 && x <= 1843 && y >= 48 && y <= 1032) n += 2;
    }
  }
  return n;
}
// Solo las pistas que se ven al menos 140 px: en las cortas el destello sería un parpadeo.
const VISIBLE_MIN = 140;
const conLargo = PISTAS_FONDO.filter((p) => largoVisible(p.pts) >= VISIBLE_MIN);
const PISTAS_DER = conLargo.filter((p) => p.lado === "der").map((p) => aPista(p.pts));
const PISTAS_OTRAS = conLargo.filter((p) => p.lado !== "der").map((p) => aPista(p.pts));

/** Hash fijo (FNV-1a) de un texto: elige las pistas de cada paso siempre igual. */
function hash(texto: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < texto.length; i++) {
    h ^= texto.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

/** Un destello en su pista, a t s de su arranque. Nada antes de arrancar ni después del latido. */
const Destello: React.FC<{ pista: Pista; t: number; luz: number }> = ({ pista, t, luz }) => {
  if (t <= 0 || t >= PULSO.viaje + PULSO.latido) return null;
  const { d, largo } = pista;
  const viajando = t < PULSO.viaje;
  const p = viajando ? CURVA.sale(t / PULSO.viaje) : 1;
  const q = viajando ? 0 : (t - PULSO.viaje) / PULSO.latido; // 0 a 1 durante el latido
  // Al llegar, la cola entra en el punto y se apaga mientras late.
  const cabeza = p * largo + q * PULSO.tramos[0].largo;
  const apaga = 1 - q;
  const azul = COLOR.azul;
  const [px, py] = pista.pts[pista.pts.length - 1];
  const punta = viajando ? getPointAtLength(d, cabeza) : null;
  return (
    <g>
      {PULSO.tramos.map(({ largo: l, alfa }) => {
        const a = Math.max(0, cabeza - l);
        const b = Math.min(largo, cabeza);
        if (b - a <= 0.5) return null;
        return (
          <path
            key={l}
            d={d}
            fill="none"
            stroke={conAlfa(azul, alfa * apaga * luz)}
            strokeWidth={PULSO.trazo}
            strokeLinejoin="miter"
            strokeLinecap="butt"
            strokeDasharray={`${b - a} ${largo * 3}`}
            strokeDashoffset={-a}
          />
        );
      })}
      {punta && (
        <circle
          cx={punta.x}
          cy={punta.y}
          r={PULSO.punta}
          fill={conAlfa(COLOR.hueso, luz)}
          style={{ filter: `drop-shadow(0 0 ${PULSO.sombraPunta}px ${conAlfa(azul, luz)})` }}
        />
      )}
      {!viajando && (
        <circle
          cx={px}
          cy={py}
          r={PULSO.punto.desde + (PULSO.punto.hasta - PULSO.punto.desde) * Math.sin(Math.PI * q)}
          fill={conAlfa(COLOR.hueso, PULSO.punto.alfa * Math.sin(Math.PI * q) * luz)}
        />
      )}
    </g>
  );
};

/**
 * El fondo de la charla. Va primero, debajo de todo, y nunca dentro de una Camara. Con `pulsos`, en
 * cada paso pedido dos destellos recorren dos pistas (una de la derecha y una de la izquierda o de
 * arriba, elegidas con el id de la diapositiva y el número de paso), del borde al punto en 0,9 s,
 * a 0,15 y 0,35 s del comienzo; el punto late al llegar y todo termina a los 1,45 s. Un paso más
 * corto que 1,45 s más el respiro no lleva pulsos (no falla). El primer y el último cuadro de cada
 * paso son exactamente el PNG.
 */
export const FondoVivo: React.FC<PropsFondoVivo> = ({ pulsos = false, luz = 1, variante = "circuito" }) => {
  const info = usePasos();
  const frame = useCurrentFrame();
  const k = entre01(luz);
  const src = variante === "estrellas" ? FONDO_ESTRELLAS : FONDO_VIVO;

  let capaPulsos: React.ReactNode = null;
  if (pulsos && variante === "circuito" && k > 0) {
    // El paso en curso (el cuadro de corte es el último del paso anterior y no lleva nada).
    let paso = 1;
    while (paso < info.n && frame > info.cortes[paso]) paso++;
    const pedido = pulsos === true || (Array.isArray(pulsos) && pulsos.includes(paso));
    const inicio = info.cortes[paso - 1];
    const durPaso = (info.cortes[paso] - inicio) / FPS;
    const t = (frame - inicio) / FPS;
    if (pedido && durPaso >= PULSO.fin + RESPIRO_S && t > 0 && t < PULSO.fin) {
      const der = PISTAS_DER[hash(`${info.id}:${paso}:der`) % PISTAS_DER.length];
      const otra = PISTAS_OTRAS[hash(`${info.id}:${paso}:otra`) % PISTAS_OTRAS.length];
      capaPulsos = (
        <svg width={1920} height={1080} style={svgPantalla}>
          <defs>
            <clipPath id="fondo-zona-segura">
              <rect x={67} y={38} width={1853 - 67} height={1042 - 38} />
            </clipPath>
          </defs>
          <g clipPath="url(#fondo-zona-segura)">
            <Destello pista={der} t={t - PULSO.arranques[0]} luz={k} />
            <Destello pista={otra} t={t - PULSO.arranques[1]} luz={k} />
          </g>
        </svg>
      );
    }
  }

  return (
    <>
      <Img src={staticFile(src)} style={{ ...pantalla, opacity: k < 1 ? k : undefined }} />
      {capaPulsos}
    </>
  );
};

// ---------------------------------------------------------------------------------------------
// Aro
// ---------------------------------------------------------------------------------------------

export type PropsAro = {
  paso: number;
  retraso: number;
  cx: number;
  cy: number;
  /** Lado del aro al empezar y al terminar (px). */
  desde: number;
  hasta: number;
  /** Radio de las esquinas como fracción del lado: 0,5 es un círculo. */
  radioEsquina?: number;
  color?: string;
  grosor?: number;
  dura?: number;
};

/**
 * Un aro que sale del borde de lo que llega y se apaga: el lado va de `desde` a `hasta` y la opacidad
 * de 0,9 a 0, con CURVA.sale, en `dura` s. Fuera del tramo no dibuja nada (frontera y quietud intactas).
 */
export const Aro: React.FC<PropsAro> = ({ paso, retraso, cx, cy, desde, hasta, radioEsquina = 0.5, color = COLOR.azul, grosor = 5, dura = 0.5 }) => {
  const t = useTramo(paso, retraso, dura, CURVA.lineal);
  if (t <= 0 || t >= 1) return null;
  const p = CURVA.sale(t);
  const lado = desde + (hasta - desde) * p;
  return (
    <div
      style={{
        position: "absolute",
        left: cx - lado / 2,
        top: cy - lado / 2,
        width: lado,
        height: lado,
        boxSizing: "border-box",
        border: `${grosor}px solid ${color}`,
        borderRadius: radioEsquina * lado,
        opacity: 0.9 * (1 - p),
      }}
    />
  );
};

// ---------------------------------------------------------------------------------------------
// El dato y la punta
// ---------------------------------------------------------------------------------------------

export type PropsDatoViajero = {
  /** Camino SVG (en px del cuadro). */
  d: string;
  /** 0 a 1. Con 0 o 1 no se ve (el contrato de PuntoDato de D06). */
  progreso: number;
  radio?: number;
  /** Cuántos círculos de estela, cada 18 px hacia atrás (opacidad 0,5^i, radio 0,85^i). */
  estela?: number;
  color?: string;
  /** Brillo del dato (0 a 1, filtroBrillo). */
  brillo?: number;
};

const PASO_ESTELA = 18;

/** El dato que viaja, con brillo y estela. Va debajo de los nodos: entra y sale de ellos. */
export const DatoViajero: React.FC<PropsDatoViajero> = ({ d, progreso, radio = 14, estela = 5, color = COLOR.ambar, brillo: b = 1 }) => {
  if (progreso <= 0 || progreso >= 1) return null;
  const largo = getLength(d);
  const pos = largo * progreso;
  const punto = getPointAtLength(d, pos);
  if (!punto) return null;
  const cola: React.ReactNode[] = [];
  for (let i = estela; i >= 1; i--) {
    const di = pos - PASO_ESTELA * i;
    if (di < 0) continue;
    const q = getPointAtLength(d, di);
    if (!q) continue;
    cola.push(<circle key={i} cx={q.x} cy={q.y} r={radio * Math.pow(0.85, i)} fill={color} opacity={Math.pow(0.5, i)} />);
  }
  return (
    <svg width={1920} height={1080} style={{ ...svgPantalla, filter: filtroBrillo(color, b) }}>
      {cola}
      <circle cx={punto.x} cy={punto.y} r={radio} fill={color} />
    </svg>
  );
};

/**
 * La chispa en la punta de un trazo que se dibuja: un punto hueso con sombra azul de 10 px. Solo se ve
 * con 0 < progreso < 1, así el trazo terminado queda igual que sin ella.
 */
export const PuntaLuz: React.FC<{ d: string; progreso: number; radio?: number; color?: string }> = ({ d, progreso, radio = 6, color = COLOR.azul }) => {
  if (progreso <= 0 || progreso >= 1) return null;
  const punto = getPointAtLength(d, getLength(d) * progreso);
  if (!punto) return null;
  return (
    <svg width={1920} height={1080} style={svgPantalla}>
      <circle cx={punto.x} cy={punto.y} r={radio} fill={COLOR.hueso} style={{ filter: `drop-shadow(0 0 10px ${color})` }} />
    </svg>
  );
};

// ---------------------------------------------------------------------------------------------
// La cámara
// ---------------------------------------------------------------------------------------------

export type PropsCamara = {
  paso?: number;
  retraso?: number;
  /** Escala con la que arranca (llega a 1). */
  desde?: number;
  dura?: number;
  origen?: [number, number];
  children: React.ReactNode;
};

/**
 * Acercamiento del contenido: escala de `desde` a 1 con CURVA.sale. Envuelve solo el contenido, nunca
 * el fondo (con el fondo quieto, la cámara es el paralaje). Solo en el paso 1, o envolviendo solo lo
 * que entra en ese paso: si envuelve algo que ya estaba, el paso arranca en otra escala y se rompe la
 * frontera. Al terminar no deja transform: el cuadro final es idéntico al de sin cámara.
 */
export const Camara: React.FC<PropsCamara> = ({ paso = 1, retraso = 0, desde = 0.97, dura = 1.4, origen = [960, 540], children }) => {
  const p = useTramo(paso, retraso, dura, CURVA.sale);
  const escala = desde + (1 - desde) * p;
  return (
    <Capa estilo={escala !== 1 ? { transform: `scale(${escala})` } : undefined} origen={origen}>
      {children}
    </Capa>
  );
};
