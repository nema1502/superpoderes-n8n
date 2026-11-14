// El teléfono genérico de D05-D06 (sin logo ni verde de WhatsApp): contorno de 4 px en hueso
// al 40 % (con 6 px de hueso pleno era lo más brillante del cuadro y el único objeto dibujado
// con línea blanca gruesa), 520×940, esquinas de 64 px, pantalla #0E141D, una barra de chat sin
// nombre (círculo gris y una línea). Adentro va la burbuja de voz; la respuesta nace AFUERA,
// del borde derecho (BurbujaRespuesta), nunca adentro.
import React from "react";
import { random } from "remotion";
import { COLOR, conAlfa, GROSOR, OPACIDAD, RADIO, TELEFONO, TIPO } from "../tokens";
import { Globo } from "./Globo";
import type { Estilo } from "./movimiento";
import { medirTexto } from "./Texto";

const W = TELEFONO.ancho;
const H = TELEFONO.alto;

export type PropsTelefono = {
  /** Centro del teléfono en el cuadro. */
  cx: number;
  cy: number;
  /** Escala alrededor del centro (D05.2: 0,7). */
  escala?: number;
  opacidad?: number;
  estilo?: Estilo;
  /** Lo de la pantalla, en coordenadas del teléfono (0-520 × 0-940). */
  children?: React.ReactNode;
};

/** Medidas útiles dentro del teléfono (coordenadas locales). */
export const PANTALLA = { x0: 18, y0: 18, x1: W - 18, y1: H - 18, barraY: 120, contenidoY0: 176 } as const;

/** Del sistema local del teléfono al cuadro (para alinear algo de afuera con algo de adentro). */
export function aCuadro(t: Pick<PropsTelefono, "cx" | "cy" | "escala">, x: number, y: number): [number, number] {
  const k = t.escala ?? 1;
  return [t.cx + (x - W / 2) * k, t.cy + (y - H / 2) * k];
}

export const Telefono: React.FC<PropsTelefono> = ({ cx, cy, escala = 1, opacidad = 1, estilo, children }) => {
  const g = GROSOR.contorno_telefono;
  return (
    <div
      style={{
        position: "absolute",
        left: cx - W / 2,
        top: cy - H / 2,
        width: W,
        height: H,
        transformOrigin: "50% 50%",
        ...estilo,
        transform: `${estilo?.transform ?? ""} scale(${escala})`,
        opacity: opacidad * (estilo?.opacity !== undefined ? Number(estilo.opacity) : 1),
      }}
    >
      <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        <rect x={g / 2} y={g / 2} width={W - g} height={H - g} rx={RADIO.telefono} fill={COLOR.tinta} stroke={conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo)} strokeWidth={g} />
        <rect x={PANTALLA.x0} y={PANTALLA.y0} width={PANTALLA.x1 - PANTALLA.x0} height={PANTALLA.y1 - PANTALLA.y0} rx={RADIO.telefono - 14} fill={COLOR.pantalla} />
        <rect x={W / 2 - 56} y={34} width={112} height={18} rx={9} fill={COLOR.tinta} />
        {/* barra de chat sin nombre: un círculo gris y una línea */}
        <circle cx={78} cy={PANTALLA.barraY} r={28} fill={conAlfa(COLOR.gris, 0.55)} />
        <rect x={124} y={PANTALLA.barraY - 9} width={170} height={18} rx={9} fill={conAlfa(COLOR.gris, 0.45)} />
        <line x1={PANTALLA.x0} x2={PANTALLA.x1} y1={PANTALLA.barraY + 46} y2={PANTALLA.barraY + 46} stroke={COLOR.acero2} strokeWidth={2} />
      </svg>
      {children}
    </div>
  );
};

const ALTO_BURBUJA = 104;

/** Ancho de la burbuja de voz para una cantidad de barras (puede ser fraccionaria al encogerse). */
export function anchoBurbujaVoz(barras: number, duracion: string): number {
  const onda = barras * 6 + Math.max(0, barras - 1) * 5;
  return 26 + 44 + 20 + onda + 22 + medirTexto(duracion, TIPO.escala.lectura, true) + 30;
}

/**
 * Burbuja de voz (mensaje enviado, a la derecha de la pantalla): «▶» de 44 px, la onda
 * (20 barras de 6 px con 5 px de aire, hueso al 70 %) y la duración a 60 px. `barras`
 * puede bajar de 20 a 6 (se encoge a lo ancho); `onda` dibuja las barras de izquierda a
 * derecha (0 → 1). Coordenadas del teléfono: `derecha` es el borde derecho, `y` el centro.
 */
export const BurbujaVoz: React.FC<{ duracion: string; barras?: number; onda?: number; derecha?: number; y?: number; estilo?: Estilo }> = ({
  duracion,
  barras = 20,
  onda = 1,
  derecha = PANTALLA.x1 - 18,
  y = PANTALLA.contenidoY0 + 90,
  estilo,
}) => {
  const ancho = anchoBurbujaVoz(barras, duracion);
  const x0 = derecha - ancho;
  const n = Math.ceil(barras);
  const alturaMax = 56;
  const optica = TIPO.correccionOpticaEm * TIPO.escala.lectura;
  const xOnda = x0 + 26 + 44 + 20;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transformOrigin: `${derecha}px ${y}px`, ...estilo }}>
      <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        <rect x={x0} y={y - ALTO_BURBUJA / 2} width={ancho} height={ALTO_BURBUJA} rx={RADIO.burbuja} fill={COLOR.acero2} />
        <path d={`M ${derecha - 4} ${y + ALTO_BURBUJA / 2 - 22} L ${derecha + 14} ${y + ALTO_BURBUJA / 2 + 2} L ${derecha - 30} ${y + ALTO_BURBUJA / 2}`} fill={COLOR.acero2} />
        <path d={`M ${x0 + 30} ${y - 20} L ${x0 + 30} ${y + 20} L ${x0 + 30 + 36} ${y} Z`} fill={COLOR.hueso} stroke={COLOR.hueso} strokeWidth={5} strokeLinejoin="round" />
        {Array.from({ length: n }, (_, i) => {
          const visible = Math.max(0, Math.min(1, barras - i));
          const dibujada = Math.max(0, Math.min(1, onda * n - i));
          const h = (0.3 + 0.7 * random(`onda-${i}`)) * alturaMax * dibujada;
          return h > 0 && visible > 0 ? (
            <rect key={i} x={xOnda + i * 11} y={y - h / 2} width={6} height={h} rx={3} fill={conAlfa(COLOR.hueso, OPACIDAD.onda_voz * visible)} />
          ) : null;
        })}
      </svg>
      <div
        style={{
          position: "absolute",
          left: derecha - 30 - medirTexto(duracion, TIPO.escala.lectura, true),
          top: y - ALTO_BURBUJA / 2 - optica,
          height: ALTO_BURBUJA,
          lineHeight: `${ALTO_BURBUJA}px`,
          fontFamily: TIPO.familia,
          fontWeight: TIPO.peso,
          fontSize: TIPO.escala.lectura,
          fontVariantNumeric: "tabular-nums",
          color: COLOR.hueso,
          whiteSpace: "pre",
        }}
      >
        {duracion}
      </div>
    </div>
  );
};

/**
 * «Escribiendo»: tres puntos que laten en una burbuja recibida (a la izquierda).
 * `fase` 0 → 1 en los 0,6 s del guion; se apagan al final.
 */
export const Escribiendo: React.FC<{ fase: number; x?: number; y?: number }> = ({ fase, x = PANTALLA.x0 + 26, y = PANTALLA.contenidoY0 + 230 }) => {
  if (fase <= 0 || fase >= 1) return null;
  const apagar = fase > 0.8 ? (1 - fase) / 0.2 : Math.min(1, fase / 0.15);
  return (
    <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: apagar }}>
      <rect x={x} y={y - 34} width={124} height={68} rx={RADIO.burbuja} fill={COLOR.acero} />
      {[0, 1, 2].map((i) => {
        const ola = 0.5 + 0.5 * Math.sin(2 * Math.PI * (fase * 2 - i * 0.18));
        return <circle key={i} cx={x + 32 + i * 30} cy={y - ola * 6} r={9} fill={conAlfa(COLOR.hueso, 0.35 + 0.5 * ola)} />;
      })}
    </svg>
  );
};

/**
 * Burbuja de respuesta: nace del borde derecho del teléfono (la cola apunta ahí), borde de 5 px
 * (el trazo normal), dos renglones a 60 px (640×200 en D06.1). En coordenadas del cuadro. El borde
 * va en hueso al 40 % (apoyo) salvo que la burbuja SEA la respuesta del paso: entonces
 * `color={COLOR.ambar}` (D06.1). En el paso siguiente, si ya no es lo nuevo, va adentro de un Foco.
 */
export const BurbujaRespuesta: React.FC<{ x: number; y: number; renglones: string[]; punta?: [number, number] | null; ancho?: number; alto?: number; color?: string; estilo?: Estilo }> = ({
  x,
  y,
  renglones,
  punta = null,
  ancho = 640,
  alto = 200,
  color = COLOR.hueso,
  estilo,
}) => {
  const tam = TIPO.escala.lectura;
  const lh = Math.round(tam * 1.3);
  const optica = TIPO.correccionOpticaEm * tam;
  const x0 = x - ancho / 2;
  const cola = punta ? { lado: "izq" as const, en: Math.max(0.2, Math.min(0.8, (punta[1] - (y - alto / 2)) / alto)), punta: [punta[0] - x0, 0] as [number, number], base: 44 } : null;
  return (
    <Globo x={x} y={y} ancho={ancho} alto={alto} color={color === COLOR.hueso ? conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo) : color} grosor={GROSOR.borde_respuesta} cola={cola} estilo={estilo}>
      {renglones.map((r, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x0,
            width: ancho,
            top: y - (renglones.length * lh) / 2 + i * lh - optica,
            height: lh,
            lineHeight: `${lh}px`,
            textAlign: "center",
            fontFamily: TIPO.familia,
            fontWeight: TIPO.peso,
            fontSize: tam,
            color: COLOR.hueso,
            whiteSpace: "pre",
          }}
        >
          {r}
        </div>
      ))}
    </Globo>
  );
};
