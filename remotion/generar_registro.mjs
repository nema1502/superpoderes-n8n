// node remotion/generar_registro.mjs
//
// Rehace el código generado a partir de contenido/deck.json y de los archivos que hay:
//   remotion/src/diapos/index.ts       TODAS las diapositivas de deck.json (las que no
//                                      tienen archivo, como provisionales)
//   remotion/src/entradas/<ID>.ts      una entrada aislada por diapositiva
//   remotion/src/comun/iconos.generado.ts  los íconos de manim/comun/iconos
// render.mjs lo corre solo antes de cada render; a mano sirve después de crear una
// diapositiva nueva, para que el Studio y tsc la vean.
import { generarRegistro } from "./lib/registro.mjs";

try {
  generarRegistro();
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
