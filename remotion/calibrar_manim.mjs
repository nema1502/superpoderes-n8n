// node remotion/calibrar_manim.mjs <muestras.json> <salida.png>
//
// Dibuja con Remotion (los componentes de verdad: <Texto>, el borde de <Tarjeta>) las muestras de
// la calibración de Manim y deja el cuadro en PNG. Lo llama manim/calibrar.py, que dibuja lo mismo
// en Manim y compara. El JSON trae { muestras: [{ texto, tam, color, x, y, alinear }], bloques: [...] }.
import { bundle } from "@remotion/bundler";
import { ensureBrowser, openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
import { conCandado } from "./lib/empaquetar.mjs";
import { CACHE, REMOTION } from "./lib/rutas.mjs";

const [entrada, salida] = process.argv.slice(2).map((p) => path.resolve(p));
if (!entrada || !salida) {
  console.error("Uso: node remotion/calibrar_manim.mjs <muestras.json> <salida.png>");
  process.exit(2);
}
const props = JSON.parse(fs.readFileSync(entrada, "utf8"));
process.chdir(REMOTION);
const entryPoint = path.join(REMOTION, "src", "pruebas", "raiz_calibracion.tsx");
const outDir = path.join(CACHE, "bundles", `calibracion-${process.pid}-${Date.now()}`);
const serveUrl = await conCandado(path.join(CACHE, "candados", "webpack-calibracion"), () => bundle({ entryPoint, outDir, enableCaching: true }));
await ensureBrowser();
const navegador = await openBrowser("chrome");
try {
  const composition = await selectComposition({ serveUrl, id: "CalibracionManim", inputProps: props, puppeteerInstance: navegador, logLevel: "error" });
  fs.mkdirSync(path.dirname(salida), { recursive: true });
  await renderStill({ serveUrl, composition, inputProps: props, frame: 0, output: salida, imageFormat: "png", overwrite: true, puppeteerInstance: navegador, logLevel: "error" });
  console.log(`Remotion: ${salida}`);
} finally {
  fs.rmSync(outDir, { recursive: true, force: true });
  await navegador.close({ silent: true }).catch(() => {});
}
