// contenido/deck.json visto desde Remotion: textos, pasos, duraciones, entrada y las
// reglas de los elementos fijos (marca de agua y chip de piso). La misma lógica, en
// Node, vive en remotion/lib/deck.mjs: si se cambia una, se cambia la otra.
import deckJson from "../../contenido/deck.json";
import { PERSISTENTES } from "./tokens";

export type TipoEntrada = "continuo" | "fundido" | "puertas" | "corte";
export type Entrada = { tipo: TipoEntrada; duracion_s: number; desde: string | null };

export type PasoDeck = {
  texto_pantalla: string[];
  visual: string;
  notas: string;
  fuente: string | null;
  recortable: string | null;
  segundos_habla: number;
  duracion_animacion_s: number;
  audio: string | null;
};

export type DiapoDeck = {
  id: string;
  nombre: string;
  titulo: string;
  seccion: string;
  motor: "remotion" | "manim";
  piso: number | null;
  objetivo: string;
  entrada?: { tipo: TipoEntrada; duracion_s: number; desde?: string | null };
  pasos: PasoDeck[];
};

const DECK = deckJson as unknown as { titulo: string; idea_clave: string; diapositivas: DiapoDeck[] };

export const IDEA_CLAVE: string = DECK.idea_clave;
export const IDS: string[] = DECK.diapositivas.map((d) => d.id);

/** La diapositiva de deck.json, o error con la lista de ids. */
export function diapoDeck(id: string): DiapoDeck {
  const d = DECK.diapositivas.find((x) => x.id === id);
  if (!d) throw new Error(`«${id}» no está en deck.json (hay: ${IDS.join(" ")})`);
  return d;
}

/** Cómo entra la diapositiva (deck.json → entrada), con «desde» resuelto. */
export function entradaDe(id: string): Entrada {
  const i = IDS.indexOf(id);
  const d = diapoDeck(id);
  const e = d.entrada ?? { tipo: i === 0 ? "corte" : "continuo", duracion_s: 0 };
  const desde = e.desde !== undefined ? e.desde : i <= 0 ? null : IDS[i - 1];
  return { tipo: e.tipo, duracion_s: e.duracion_s ?? 0, desde: desde ?? null };
}

/**
 * Los textos en pantalla del paso (1, 2…), tal cual están en deck.json. Se usan así,
 * sin retocarlos: si uno no entra, se ajusta el diseño o se reporta.
 */
export function textos(id: string, paso: number): string[] {
  const d = diapoDeck(id);
  const p = d.pasos[paso - 1];
  if (!p) throw new Error(`${id} tiene ${d.pasos.length} pasos: no hay paso ${paso}`);
  return p.texto_pantalla;
}

/** ¿Lleva marca de agua el paso k de la diapositiva? (tokens.json → persistentes). */
export function marcaEn(id: string, k: number): boolean {
  const sin = PERSISTENTES.marca_agua_sin as string[];
  return !(sin.includes(id) || sin.includes(`${id}.${k}`));
}

/** Dígito del chip de piso de la diapositiva (deck.json → piso), o null. */
export function chipEn(id: string): number | null {
  return diapoDeck(id).piso;
}

export type EstadoFijo = { marca: boolean; chip: number | null };

/** Marca de agua y chip en el paso k. */
export function estadoFijo(id: string, k: number): EstadoFijo {
  return { marca: marcaEn(id, k), chip: chipEn(id) };
}

/**
 * Estado de los elementos fijos justo antes del paso 1: el del último paso de la
 * diapositiva de la que se entra si la entrada es continua; si no, el del paso 1
 * (la transición se encarga del cambio).
 */
export function estadoPrevio(id: string): EstadoFijo {
  const e = entradaDe(id);
  if (e.tipo === "continuo" && e.desde) {
    const d = diapoDeck(e.desde);
    return estadoFijo(e.desde, d.pasos.length);
  }
  return estadoFijo(id, 1);
}

/** El paso cuyo último cuadro es el primero de esta diapositiva (para la entrada continua). */
export function pasoAnterior(id: string): { id: string; paso: number } | null {
  const e = entradaDe(id);
  if (!e.desde) return null;
  return { id: e.desde, paso: diapoDeck(e.desde).pasos.length };
}

/**
 * Duraciones (s) del video propio de cada paso: las de deck.json; en el paso 1 se
 * descuenta la transición (fundido o puertas), que es otro video que arma el armado.
 */
export function duracionesPropias(id: string): number[] {
  const d = diapoDeck(id);
  const e = entradaDe(id);
  const descontar = e.tipo === "fundido" || e.tipo === "puertas" ? e.duracion_s : 0;
  return d.pasos.map((p, k) => {
    const dur = k === 0 ? p.duracion_animacion_s - descontar : p.duracion_animacion_s;
    if (!(dur > 0)) throw new Error(`${id}.${k + 1}: dura ${p.duracion_animacion_s} s y la entrada ${descontar} s`);
    return Math.round(dur * 1000) / 1000;
  });
}
