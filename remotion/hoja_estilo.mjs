// node remotion/hoja_estilo.mjs [páginas…]
//
// Renderiza la hoja de estilo del sistema visual (src/sistema/HojaEstilo.tsx):
//   render/revision/sistema.png              las siete páginas y las dos muestras en una grilla de 3 × 3 (5760×3240)
//   render/revision/sistema_<n>.png          cada página a 1920×1080 (para mirarla a tamaño real)
//   render/revision/sistema_muestra_<n>.png  las muestras que combinan piezas
// Con números (node remotion/hoja_estilo.mjs 2 5) saca solo esas páginas.
import { ensureBrowser, openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
import { empaquetar } from "./lib/empaquetar.mjs";
import { generarRegistro } from "./lib/registro.mjs";
import { barras, PROYECTO, REMOTION, REVISION } from "./lib/rutas.mjs";

const solo = process.argv.slice(2).map(Number).filter((n) => n > 0);
process.chdir(REMOTION);
generarRegistro({ silencioso: true });
fs.mkdirSync(REVISION, { recursive: true });
await ensureBrowser();
const navegador = await openBrowser("chrome");
const paquete = await empaquetar("_Sistema");
const onBrowserLog = (l) => {
  if (l.text.startsWith("AVISO")) console.warn(`  ${l.text}`);
};
let fallas = 0;
try {
  const trabajos = [];
  for (let i = 1; i <= 7; i++) if (!solo.length || solo.includes(i)) trabajos.push([`HojaEstilo${i}`, `sistema_${i}.png`]);
  if (!solo.length) trabajos.push(["Muestra1", "sistema_muestra_1.png"], ["Muestra2", "sistema_muestra_2.png"], ["HojaEstilo", "sistema.png"]);
  for (const [id, archivo] of trabajos) {
    const destino = path.join(REVISION, archivo);
    try {
      const composition = await selectComposition({ serveUrl: paquete.serveUrl, id, inputProps: {}, puppeteerInstance: navegador, onBrowserLog, logLevel: "error" });
      await renderStill({ serveUrl: paquete.serveUrl, composition, frame: 0, output: destino, imageFormat: "png", overwrite: true, puppeteerInstance: navegador, onBrowserLog, logLevel: "error" });
      console.log(`  ${barras(path.relative(PROYECTO, destino))}`);
    } catch (e) {
      fallas++;
      console.error(`  ${id}: ERROR ${String(e.message ?? e).split("\n")[0]}`);
    }
  }
} finally {
  paquete.limpiar();
  await navegador.close({ silent: true }).catch(() => {});
}
if (fallas) process.exit(1);
