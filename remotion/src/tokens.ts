// Tokens de diseño de la charla, leídos de diseno/tokens.json (la fuente única que
// también leen Manim y la hoja de LaTeX). Acá no se escribe ningún valor: solo se
// le da forma y tipo a lo que dice el JSON. Para cambiar un color, un tamaño o un
// tiempo, se cambia el JSON (y se vuelve a renderizar lo que lo use).
import { Easing, type SpringConfig } from "remotion";
import t from "../../diseno/tokens.json";

export const TOKENS = t;

export const ANCHO = t.lienzo.ancho;
export const ALTO = t.lienzo.alto;
export const FPS = t.lienzo.fps;

// ---------- Color ----------
export type NombreColor = keyof typeof t.color;
const colores = {} as Record<NombreColor, string>;
for (const k of Object.keys(t.color) as NombreColor[]) colores[k] = t.color[k].hex;
/** Hex de cada color por nombre: COLOR.ambar, COLOR.hueso… */
export const COLOR: Readonly<Record<NombreColor, string>> = colores;

/** Opacidades con nombre (apagado 0,08, foco 0,6, borde de apoyo 0,4, marco y losa 0,5, luz de la cabina…). */
export const OPACIDAD = t.opacidad;

function hexARgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

/** Color con transparencia: conAlfa(COLOR.hueso, 0.55) → "rgba(245,247,255,0.55)". */
export function conAlfa(hex: string, alfa: number): string {
  const [r, g, b] = hexARgb(hex);
  return `rgba(${r},${g},${b},${Math.max(0, Math.min(1, alfa))})`;
}

/** Mezcla opaca de dos colores (t = 0 → a, t = 1 → b). */
export function mezclar(a: string, b: string, k: number): string {
  const x = hexARgb(a);
  const y = hexARgb(b);
  const c = x.map((v, i) => Math.round(v + (y[i] - v) * Math.max(0, Math.min(1, k))));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// ---------- Tipografía ----------
export const TIPO = {
  familia: t.tipografia.familia,
  peso: t.tipografia.peso,
  escala: t.tipografia.escala_px,
  minimo: t.tipografia.minimo_px,
  interlineado: t.tipografia.interlineado,
  mayusculaEm: t.tipografia.mayuscula_em,
  alturaXEm: t.tipografia.altura_x_em,
  correccionOpticaEm: t.tipografia.correccion_optica_em,
  /** Grosor del asta de Segoe UI Bold, en em (la palomita y la cruz que acompañan un texto lo toman). */
  astaEm: t.tipografia.asta_em,
  /** Tamaños héroe (fuera de la escala, con su motivo): elevator_pitch 128, ecuacion 105, firma 96. */
  heroe: t.tipografia.heroe_px,
} as const;
export type NombreTamano = keyof typeof t.tipografia.escala_px;

// ---------- Retícula, radios, grosores, brillos ----------
export const RETICULA = t.reticula;
export const ZONA = t.reticula.zona_segura;
/** Por debajo de esta y, solo fuentes, firma y decoración (la última fila no ve el borde de abajo). */
export const FRANJA_INFERIOR_Y = t.reticula.franja_inferior.y;
export const RADIO = t.radio;
export const GROSOR = t.grosor;
export const BRILLO = t.brillos;
export const VISOR = t.visor;
export const ASCENSOR_FRENTE = t.ascensor_frente;
export const ASCENSOR_CORTE = t.ascensor_corte;
export const TELEFONO = t.telefono;
export const ICONOS = t.iconos;
export const PERSISTENTES = t.persistentes;
export const TRANSICIONES = t.transiciones;

// ---------- Movimiento ----------
export type NombreResorte = keyof typeof t.movimiento.resortes;
/** Configuraciones de resorte del vocabulario (Entrar, Golpe, Rebote…). */
export const RESORTE = t.movimiento.resortes as Record<NombreResorte, Partial<SpringConfig>>;

const CURVAS_REMOTION: Record<string, (x: number) => number> = {
  "inOut(cubic)": Easing.inOut(Easing.cubic),
  "out(cubic)": Easing.out(Easing.cubic),
  "in(cubic)": Easing.in(Easing.cubic),
  linear: Easing.linear,
  "inOut(sin)": Easing.inOut(Easing.sin),
};
export type NombreCurva = keyof typeof t.movimiento.curvas & string;
const curvas = {} as Record<Exclude<NombreCurva, "_doc">, (x: number) => number>;
for (const [k, v] of Object.entries(t.movimiento.curvas)) {
  if (k === "_doc" || typeof v === "string") continue;
  const f = CURVAS_REMOTION[v.remotion];
  if (!f) throw new Error(`tokens.json: curva «${v.remotion}» desconocida`);
  (curvas as Record<string, (x: number) => number>)[k] = f;
}
/** Curvas con nombre: CURVA.suave (inOut cúbica), CURVA.sale (out cúbica), CURVA.lineal… */
export const CURVA = curvas;

export const MOV = {
  dura: t.movimiento.duracion_s,
  desfase: t.movimiento.desfase_s,
  distancia: t.movimiento.distancia_px,
  escala: t.movimiento.escala,
  perspectiva: t.movimiento.perspectiva_voltear_px,
  barrido: t.movimiento.barrido,
  latidoUltimos: t.movimiento.latido_ultimos_s,
  cuentaPrevia: t.movimiento.cuenta_previa,
  viaje: t.movimiento.viaje,
} as const;

/** Segundos de quietud al final de cada paso (respiro incluido en la duración del deck). */
export const RESPIRO_S = t.pasos.respiro_s;
export const ANIMACION_MAX_S = t.pasos.animacion_max_s;

// ---------- Nombres de antes (las pruebas de infraestructura los usan) ----------
export const FONDO = COLOR.tinta;
export const HUESO = COLOR.hueso;
export const GRIS = COLOR.gris;
export const MARCA = COLOR.marca;
export const ACENTO = COLOR.ambar;
export const FUENTE = TIPO.familia;
