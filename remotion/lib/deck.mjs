// Lectura de contenido/deck.json y de las reglas de diseno/tokens.json desde Node.
// La misma lógica (en TypeScript) vive en remotion/src/deck.ts: si se cambia una,
// se cambia la otra.
import fs from "node:fs";
import { DECK, TOKENS } from "./rutas.mjs";

export function leerDeck() {
  return JSON.parse(fs.readFileSync(DECK, "utf8"));
}

export function leerTokens() {
  return JSON.parse(fs.readFileSync(TOKENS, "utf8"));
}

export const FPS = leerTokens().lienzo.fps;
export const s = (seg) => Math.round(seg * FPS);

/** Diapositiva por id, o error con la lista de ids válidos. */
export function diapo(deck, id) {
  const d = deck.diapositivas.find((x) => x.id === id);
  if (!d) throw new Error(`«${id}» no está en deck.json (hay: ${deck.diapositivas.map((x) => x.id).join(" ")})`);
  return d;
}

/** La entrada de una diapositiva, con valores por defecto si deck.json todavía no la tiene. */
export function entradaDe(deck, id) {
  const lista = deck.diapositivas;
  const i = lista.findIndex((x) => x.id === id);
  if (i < 0) diapo(deck, id);
  const d = lista[i];
  const e = d.entrada ?? { tipo: i === 0 ? "corte" : "continuo", duracion_s: 0 };
  const desde = e.desde !== undefined ? e.desde : i === 0 ? null : lista[i - 1].id;
  return { tipo: e.tipo, duracion_s: e.duracion_s ?? 0, desde };
}

/** ¿Lleva marca de agua el paso k (1, 2…) de la diapositiva id? */
export function marcaEn(tokens, id, k) {
  const sin = tokens.persistentes.marca_agua_sin;
  return !(sin.includes(id) || sin.includes(`${id}.${k}`));
}

/** Duraciones (s) del video propio de cada paso: la del deck, menos la transición en el paso 1. */
export function duracionesPropias(deck, id) {
  const d = diapo(deck, id);
  const e = entradaDe(deck, id);
  const descontar = e.tipo === "fundido" || e.tipo === "puertas" ? e.duracion_s : 0;
  return d.pasos.map((p, k) => {
    const dur = k === 0 ? p.duracion_animacion_s - descontar : p.duracion_animacion_s;
    if (!(dur > 0)) throw new Error(`${id}.${k + 1}: dura ${p.duracion_animacion_s} s y la entrada (${e.tipo}) ${descontar} s: no queda video propio`);
    return Math.round(dur * 1000) / 1000;
  });
}
