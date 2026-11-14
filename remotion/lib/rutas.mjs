// Rutas del proyecto, para todos los scripts de Node de remotion/.
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REMOTION = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const PROYECTO = path.resolve(REMOTION, "..");
export const SRC = path.join(REMOTION, "src");
export const DIAPOS = path.join(SRC, "diapos");
export const ENTRADAS = path.join(SRC, "entradas");
// La carpeta pública de los bundles es diseno/: así una diapositiva usa los logos y las piezas
// con staticFile("logos/tinkazo/llama.svg") o staticFile("assets/marca_agua.png"), sin copiarlos.
// (El Studio lee lo mismo: remotion.config.ts → Config.setPublicDir("../diseno").)
export const PUBLICO = path.join(PROYECTO, "diseno");
export const DECK = path.join(PROYECTO, "contenido", "deck.json");
export const TOKENS = path.join(PROYECTO, "diseno", "tokens.json");
export const ICONOS = path.join(PROYECTO, "manim", "comun", "iconos");
export const ASSETS = path.join(PROYECTO, "diseno", "assets");
export const RENDER = path.join(PROYECTO, "render");
export const PASOS = path.join(RENDER, "pasos");
export const CUADROS = path.join(RENDER, "cuadros");
export const REVISION = path.join(RENDER, "revision");
export const TRANSICIONES = path.join(RENDER, "transiciones");
// Cachés y bundles de webpack: dentro de node_modules (ignorado por git), uno por entrada.
// node_modules es una carpeta propia con enlaces a las dependencias de otra copia, salvo .cache,
// que es de esta: la caché y los bundles de esta charla no se mezclan con los de otra.
export const CACHE = path.join(REMOTION, "node_modules", ".cache", "charla");

/** Ruta con barras normales, para mostrar y para escribir en código generado. */
export const barras = (p) => p.split(path.sep).join("/");

// Cuando un render falla, Remotion cierra la pestaña y su cierre rechaza otra promesa
// («Target closed») que taparía el error de verdad: ese rechazo se ignora acá.
process.on("unhandledRejection", (e) => {
  if (/Target closed|Session closed/i.test(String(e?.message ?? e))) return;
  console.error(e);
  process.exitCode = 1;
});
