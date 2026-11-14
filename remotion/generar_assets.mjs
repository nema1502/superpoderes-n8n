// node remotion/generar_assets.mjs
//
// Renderiza desde Remotion las piezas que Manim tiene que mostrar IDÉNTICAS (marca de
// agua y chips de piso 1-3) y las deja en diseno/assets/:
//   <pieza>.png        recorte de su zona reservada, con fondo transparente
//   <pieza>_tinta.png  el mismo recorte sobre tinta (opaco): pegado en su píxel da
//                      exactamente lo que dibuja Remotion (la zona es reservada)
//   <pieza>_1080.png   cuadro entero de 1920×1080 transparente (para superponer sin mover)
//   assets.json        dónde va cada recorte (x, y, ancho, alto) y de qué tokens sale
// Se corre de nuevo cada vez que cambian los tokens o los componentes de la marca o el chip.
import { ensureBrowser, openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { leerTokens } from "./lib/deck.mjs";
import { empaquetar } from "./lib/empaquetar.mjs";
import { escribirPng, leerPng, recortar } from "./lib/png.mjs";
import { generarRegistro } from "./lib/registro.mjs";
import { ASSETS, barras, PROYECTO, REMOTION } from "./lib/rutas.mjs";

process.chdir(REMOTION);
generarRegistro({ silencioso: true });
const tokens = leerTokens();
const zonas = {
  marca_agua: tokens.reticula.marca_agua.zona,
  chip_piso_1: tokens.reticula.chip_piso.zona,
  chip_piso_2: tokens.reticula.chip_piso.zona,
  chip_piso_3: tokens.reticula.chip_piso.zona,
};

fs.mkdirSync(ASSETS, { recursive: true });
await ensureBrowser();
const navegador = await openBrowser("chrome");
const paquete = await empaquetar("_Sistema", { silencioso: true });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "assets-"));
const manifiesto = {
  _doc: "Piezas de Remotion para Manim, en el mismo píxel (x, y = esquina de arriba a la izquierda del recorte en el cuadro de 1920×1080). Las genera remotion/generar_assets.mjs; no se editan a mano.",
  generado: new Date().toISOString().slice(0, 10),
  piezas: {},
};
try {
  for (const [pieza, z] of Object.entries(zonas)) {
    const archivos = {};
    for (const fondo of [false, true]) {
      const inputProps = { pieza, fondo };
      const composition = await selectComposition({ serveUrl: paquete.serveUrl, id: "Asset", inputProps, puppeteerInstance: navegador, logLevel: "error" });
      const cuadro = path.join(tmp, `${pieza}_${fondo}.png`);
      await renderStill({ serveUrl: paquete.serveUrl, composition, inputProps, frame: 0, output: cuadro, imageFormat: "png", overwrite: true, puppeteerInstance: navegador, logLevel: "error" });
      const img = leerPng(cuadro);
      const r = recortar(img, z.x, z.y, z.ancho, z.alto);
      if (fondo) {
        escribirPng(path.join(ASSETS, `${pieza}_tinta.png`), r, { rgb: true });
        archivos.tinta = `${pieza}_tinta.png`;
      } else {
        escribirPng(path.join(ASSETS, `${pieza}.png`), r);
        escribirPng(path.join(ASSETS, `${pieza}_1080.png`), img);
        archivos.transparente = `${pieza}.png`;
        archivos.cuadro = `${pieza}_1080.png`;
        // Nada de la pieza puede quedar fuera de su zona reservada.
        for (let i = 0; i < img.ancho * img.alto; i++) {
          const x = i % img.ancho;
          const y = Math.floor(i / img.ancho);
          const dentro = x >= z.x && x < z.x + z.ancho && y >= z.y && y < z.y + z.alto;
          if (!dentro && img.datos[i * 4 + 3] !== 0) throw new Error(`${pieza}: hay dibujo fuera de su zona (${x}, ${y})`);
        }
      }
    }
    manifiesto.piezas[pieza] = { x: z.x, y: z.y, ancho: z.ancho, alto: z.alto, archivos };
    console.log(`  ${pieza}: zona ${z.x},${z.y} ${z.ancho}×${z.alto}`);
  }
  fs.writeFileSync(path.join(ASSETS, "assets.json"), `${JSON.stringify(manifiesto, null, 2)}\n`);
  console.log(`Listo: ${barras(path.relative(PROYECTO, ASSETS))}/`);
} finally {
  paquete.limpiar();
  fs.rmSync(tmp, { recursive: true, force: true });
  await navegador.close({ silent: true }).catch(() => {});
}
