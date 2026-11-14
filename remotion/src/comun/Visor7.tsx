// Visor de 7 segmentos de verdad, dibujado en SVG (no es una fuente): segmento
// encendido en ámbar con un brillo leve, apagado en ámbar al 8 % (se ve el «8»
// fantasma, como en los visores de los ascensores). Caracteres: 0-9, «P» y «b» (planta
// baja se escribe «Pb»: una B mayúscula en 7 segmentos se leería como un 8), «:», «-»
// y espacio. Todos los números de tiempo de la charla salen de acá.
import React, { useId } from "react";
import { BRILLO, COLOR, conAlfa, OPACIDAD, VISOR } from "../tokens";

const SEGMENTOS: Record<string, string> = {
  "0": "abcdef",
  "1": "bc",
  "2": "abged",
  "3": "abgcd",
  "4": "fgbc",
  "5": "afgcd",
  "6": "afgedc",
  "7": "abc",
  "8": "abcdefg",
  "9": "abcdfg",
  P: "abefg",
  b: "cdefg",
  "-": "g",
  " ": "",
};
const ORDEN = "abcdefg";

const tanInclinacion = Math.tan((VISOR.inclinacion_grados * Math.PI) / 180);

/** Ancho (sin inclinación) de un carácter, en px, para un dígito de alto H. */
function anchoCaracter(c: string, H: number): number {
  return c === ":" ? VISOR.ancho_dos_puntos * H : VISOR.ancho_digito * H;
}

/** Ancho total en px que ocupa un texto en el visor (incluida la inclinación). */
export function anchoVisor(texto: string, alto: number): number {
  const chars = [...texto];
  const w = chars.reduce((s, c) => s + anchoCaracter(c, alto), 0) + Math.max(0, chars.length - 1) * VISOR.separacion_digitos * alto;
  return w + tanInclinacion * alto;
}

type Punto = [number, number];
const pts = (p: Punto[]) => p.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" ");

/** Polígonos de los 7 segmentos de un dígito de alto H (origen arriba a la izquierda). */
function poligonos(H: number): Record<string, string> {
  const W = VISOR.ancho_digito * H;
  const T = VISOR.grosor_segmento * H;
  const G = VISOR.separacion_segmentos * H;
  const h = T / 2;
  const horiz = (x1: number, x2: number, y: number): Punto[] => [
    [x1 + G, y],
    [x1 + G + h, y - h],
    [x2 - G - h, y - h],
    [x2 - G, y],
    [x2 - G - h, y + h],
    [x1 + G + h, y + h],
  ];
  const vert = (x: number, y1: number, y2: number): Punto[] => [
    [x, y1 + G],
    [x + h, y1 + G + h],
    [x + h, y2 - G - h],
    [x, y2 - G],
    [x - h, y2 - G - h],
    [x - h, y1 + G + h],
  ];
  return {
    a: pts(horiz(h, W - h, h)),
    g: pts(horiz(h, W - h, H / 2)),
    d: pts(horiz(h, W - h, H - h)),
    f: pts(vert(h, h, H / 2)),
    e: pts(vert(h, H / 2, H - h)),
    b: pts(vert(W - h, h, H / 2)),
    c: pts(vert(W - h, H / 2, H - h)),
  };
}

type Glifo = { c: string; x: number; w: number };

function disponer(texto: string, H: number): Glifo[] {
  const out: Glifo[] = [];
  let x = 0;
  for (const c of [...texto]) {
    if (!(c in SEGMENTOS) && c !== ":") throw new Error(`Visor7: el carácter «${c}» no existe en 7 segmentos (hay: 0-9, P, b, :, -, espacio).`);
    const w = anchoCaracter(c, H);
    out.push({ c, x, w });
    x += w + VISOR.separacion_digitos * H;
  }
  return out;
}

export type PropsVisorGrupo = {
  /** Lo que muestra: "Pb", "0:30", "10", "3"… */
  texto: string;
  /** Alto del dígito en px. */
  alto: number;
  color?: string;
  /** 0 → 1: los segmentos encendidos se prenden de a uno (portada: «Pb» en 0,4 s). */
  encendido?: number;
  /** true: los segmentos encendidos se ven apagados (para parpadear). */
  parpadeo?: boolean;
  /** Texto anterior y progreso (0 → 1) del cambio rodado: el viejo sale hacia arriba y el nuevo entra desde abajo. */
  anterior?: string;
  cambio?: number;
  /** Brillo de los segmentos encendidos (tokens: brillos.segmento_visor). */
  brillo?: boolean;
  /** Opacidad de los segmentos apagados (0,08). */
  apagado?: number;
};

/**
 * El visor como grupo SVG con origen arriba a la izquierda del primer dígito (para
 * meterlo dentro de otro SVG, como hace <VisorCaja>). Mide anchoVisor(texto, alto) × alto.
 */
export const Visor7Grupo: React.FC<PropsVisorGrupo & { idBase: string }> = ({
  texto,
  alto: H,
  color = COLOR.ambar,
  encendido = 1,
  parpadeo = false,
  anterior,
  cambio = 1,
  brillo = true,
  apagado = OPACIDAD.apagado,
  idBase,
}) => {
  const P = poligonos(H);
  const glifos = disponer(texto, H);
  const previos = anterior !== undefined ? disponer(anterior.padStart(texto.length, " ").slice(-texto.length), H) : null;
  const sh = tanInclinacion * H;
  const T = VISOR.grosor_segmento * H;

  // Segmentos encendidos, en orden, para el encendido de a uno.
  const encendidos: { g: number; s: string }[] = [];
  glifos.forEach((gl, i) => {
    if (gl.c === ":") encendidos.push({ g: i, s: "p1" }, { g: i, s: "p2" });
    else for (const s of ORDEN) if (SEGMENTOS[gl.c].includes(s)) encendidos.push({ g: i, s });
  });
  const cuantos = Math.floor(Math.max(0, Math.min(1, encendido)) * encendidos.length + 1e-6);
  const prendido = new Set(encendidos.slice(0, cuantos).map((e) => `${e.g}:${e.s}`));

  const dibujar = (gl: Glifo, i: number, cuales: (s: string) => boolean, relleno: string, dy = 0, clave = "") => {
    if (gl.c === ":") {
      const cx = gl.x + gl.w / 2;
      return (
        <g key={`${clave}${i}`} transform={`translate(0 ${dy})`}>
          {["p1", "p2"].filter(cuales).map((p) => (
            <rect key={p} x={cx - T / 2} y={(p === "p1" ? 0.3 : 0.7) * H - T / 2} width={T} height={T} fill={relleno} />
          ))}
        </g>
      );
    }
    return (
      <g key={`${clave}${i}`} transform={`translate(${gl.x} ${dy})`}>
        {[...ORDEN].filter(cuales).map((s) => (
          <polygon key={s} points={P[s]} fill={relleno} />
        ))}
      </g>
    );
  };

  const fantasmas = glifos.map((gl, i) => dibujar(gl, i, () => true, conAlfa(color, apagado), 0, "f"));
  const salto = H * 1.18;
  const k = Math.max(0, Math.min(1, cambio));
  const luces: React.ReactNode[] = [];
  if (!parpadeo) {
    glifos.forEach((gl, i) => {
      const nuevo = (s: string) => (gl.c === ":" ? true : SEGMENTOS[gl.c].includes(s)) && prendido.has(`${i}:${s}`);
      const viejo = previos ? previos[i] : null;
      if (viejo && viejo.c !== gl.c && k <= 0) {
        // Antes de empezar el cambio, el viejo se dibuja igual que un visor quieto (mismos
        // píxeles que el último cuadro del paso anterior: sin recorte ni desplazamiento).
        luces.push(dibujar(viejo, i, (s) => (viejo.c === ":" ? true : SEGMENTOS[viejo.c].includes(s)), color, 0, "l"));
      } else if (viejo && viejo.c !== gl.c && k < 1) {
        const clip = `${idBase}-c${i}`;
        luces.push(
          <g key={`r${i}`} clipPath={`url(#${clip})`}>
            <defs>
              <clipPath id={clip}>
                <rect x={gl.x - T} y={-T * 0.4} width={gl.w + 2 * T} height={H + T * 0.8} />
              </clipPath>
            </defs>
            {k > 0 && dibujar(gl, i, nuevo, color, (1 - k) * salto, "n")}
            {dibujar(viejo, i, (s) => (viejo.c === ":" ? true : SEGMENTOS[viejo.c].includes(s)), color, -k * salto, "v")}
          </g>,
        );
      } else luces.push(dibujar(gl, i, nuevo, color, 0, "l"));
    });
  }
  const filtro = `${idBase}-b`;
  const radio = BRILLO.segmento_visor.radio_por_alto * H;
  return (
    <g transform={`translate(${sh} 0) skewX(${-VISOR.inclinacion_grados})`}>
      {brillo && (
        <defs>
          <filter id={filtro} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={radio / 2} />
          </filter>
        </defs>
      )}
      {fantasmas}
      {brillo && luces.length > 0 && (
        <g filter={`url(#${filtro})`} opacity={BRILLO.segmento_visor.opacidad}>
          {luces}
        </g>
      )}
      {luces}
    </g>
  );
};

/** Id único y válido para url(#…) en un SVG. */
export function useIdSvg(prefijo: string): string {
  return `${prefijo}${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
}

export type PropsVisor7 = PropsVisorGrupo & {
  x: number;
  y: number;
  /** Dónde está x: el centro del texto (por defecto), su borde izquierdo o el derecho. y es el centro vertical. */
  ancla?: "centro" | "izq" | "der";
  /** Escala extra (latido: 1 → 1,03), alrededor del centro. */
  latido?: number;
  opacidad?: number;
};

/** Visor de 7 segmentos suelto, posicionado en el cuadro (el reloj grande, el «40»). */
export const Visor7: React.FC<PropsVisor7> = ({ x, y, ancla = "centro", latido = 1, opacidad = 1, ...grupo }) => {
  const idBase = useIdSvg("v7");
  const H = grupo.alto;
  const w = anchoVisor(grupo.texto, H);
  const pad = H * 0.25;
  const izquierda = ancla === "centro" ? x - w / 2 : ancla === "izq" ? x : x - w;
  return (
    <svg
      width={w + 2 * pad}
      height={H + 2 * pad}
      style={{
        position: "absolute",
        left: izquierda - pad,
        top: y - H / 2 - pad,
        overflow: "visible",
        opacity: opacidad,
        transform: latido !== 1 ? `scale(${latido})` : undefined,
        transformOrigin: "50% 50%",
      }}
    >
      <g transform={`translate(${pad} ${pad})`}>
        <Visor7Grupo {...grupo} idBase={idBase} />
      </g>
    </svg>
  );
};

// ---------- ▲ ----------

export type PropsTriangulo = {
  /** Ancho del triángulo en px (alto = 0,86 × ancho). */
  tam: number;
  /** 0 = apagado (ámbar al 8 %), 1 = encendido. */
  encendido?: number;
  /** 0 → 1 → 0: el brillo de una vez (el ▲ «brilla una vez» al cambiar de piso). */
  brillo?: number;
  color?: string;
};

/** ▲ como grupo SVG, con el vértice arriba y origen arriba a la izquierda. */
export const TrianguloGrupo: React.FC<PropsTriangulo & { idBase: string }> = ({ tam, encendido = 1, brillo = 0, color = COLOR.ambar, idBase }) => {
  const h = tam * 0.86;
  const r = tam * 0.06;
  const puntos = `${tam / 2},${r} ${tam - r},${h - r} ${r},${h - r}`;
  const alfa = OPACIDAD.apagado + (1 - OPACIDAD.apagado) * Math.max(0, Math.min(1, encendido));
  const filtro = `${idBase}-t`;
  // Un brillo de 1e-16 (sin(π)) igual activaría el filtro y cambiaría los píxeles del ▲ quieto.
  const b = brillo > 0.002 ? Math.min(1, brillo) : 0;
  return (
    <g>
      {b > 0 && (
        <>
          <defs>
            <filter id={filtro} x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation={BRILLO.triangulo_una_vez.radio_px / 2} />
            </filter>
          </defs>
          <polygon points={puntos} fill={color} stroke={color} strokeWidth={r * 2} strokeLinejoin="round" filter={`url(#${filtro})`} opacity={b * BRILLO.triangulo_una_vez.opacidad} />
        </>
      )}
      <polygon points={puntos} fill={conAlfa(color, alfa)} stroke={conAlfa(color, alfa)} strokeWidth={r * 2} strokeLinejoin="round" />
    </g>
  );
};

// ---------- Caja de visor ----------

export type PropsVisorCaja = Omit<PropsVisorGrupo, "alto"> & {
  /** Centro de la caja. */
  cx: number;
  cy: number;
  ancho: number;
  alto: number;
  /** Alto del dígito en px. */
  digito: number;
  /** ▲ a la izquierda (null: sin triángulo). */
  triangulo?: PropsTriangulo | null;
  opacidad?: number;
  escala?: number;
};

/**
 * Caja de vidrio (#05070A, borde de acero de 2 px) con ▲ y el visor adentro. El
 * cambio rodado se recorta con la caja. Es el visor del ascensor y el chip de piso.
 */
export const VisorCaja: React.FC<PropsVisorCaja> = ({ cx, cy, ancho, alto, digito, triangulo = null, opacidad = 1, escala = 1, ...visor }) => {
  const idBase = useIdSvg("vc");
  const wTexto = anchoVisor(visor.texto, digito);
  const sep = triangulo ? triangulo.tam * 0.55 : 0;
  const wContenido = (triangulo ? triangulo.tam + sep : 0) + wTexto;
  const x0 = (ancho - wContenido) / 2;
  const borde = 2;
  const clip = `${idBase}-k`;
  return (
    <svg
      width={ancho}
      height={alto}
      style={{
        position: "absolute",
        left: cx - ancho / 2,
        top: cy - alto / 2,
        overflow: "visible",
        opacity: opacidad,
        transform: escala !== 1 ? `scale(${escala})` : undefined,
        transformOrigin: "50% 50%",
      }}
    >
      <defs>
        <clipPath id={clip}>
          <rect x={borde} y={borde} width={ancho - 2 * borde} height={alto - 2 * borde} rx={8} />
        </clipPath>
      </defs>
      <rect x={borde / 2} y={borde / 2} width={ancho - borde} height={alto - borde} rx={10} fill={COLOR.vidrio} stroke={COLOR.acero2} strokeWidth={borde} />
      <g clipPath={`url(#${clip})`}>
        {triangulo && (
          <g transform={`translate(${x0} ${(alto - triangulo.tam * 0.86) / 2})`}>
            <TrianguloGrupo {...triangulo} idBase={idBase} />
          </g>
        )}
        <g transform={`translate(${x0 + (triangulo ? triangulo.tam + sep : 0)} ${(alto - digito) / 2})`}>
          <Visor7Grupo {...visor} alto={digito} idBase={idBase} />
        </g>
      </g>
    </svg>
  );
};
