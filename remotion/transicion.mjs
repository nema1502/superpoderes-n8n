// node remotion/transicion.mjs --de <png> --a <png> --tipo <fundido|puertas> --salida <mp4>
//                              [--duracion <s>] [--marca auto|si|no] [--concurrencia N]
//
// El video de transición entre dos diapositivas (src/sistema/Transicion.tsx), con la
// misma receta que los pasos (QP 16, cuadro clave en el último, BT.709, sin audio): su
// cuadro 0 es idéntico a <de> (el último cuadro de la anterior) y el último, a <a> (el
// primero de la diapositiva). El armado lo pega delante del paso 1 (sin repetir el
// cuadro compartido). «continuo» y «corte» no llevan video de transición.
//   --duracion: por defecto, la de tokens.json (fundido 0,4 s; puertas 1,05 s).
//   --marca auto: si las dos imágenes traen la marca de agua en el mismo píxel, la marca
//     se dibuja encima de todo y queda quieta (por encima de las puertas).
// Al terminar comprueba los dos extremos píxel a píxel contra los PNG (sale con error si no).
import { ensureBrowser, openBrowser, renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { leerTokens } from "./lib/deck.mjs";
import { empaquetar } from "./lib/empaquetar.mjs";
import { comparar, leerPng, recortar, zonaConDibujo } from "./lib/png.mjs";
import { opcionesTramo } from "./lib/receta.mjs";
import { barras, PROYECTO, REMOTION } from "./lib/rutas.mjs";

function leerArgumentos(argv) {
  const a = { de: null, a: null, tipo: null, salida: null, duracion: null, marca: "auto", concurrencia: 4 };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    const v = () => {
      const s = argv[++i];
      if (s === undefined) throw new Error(`Falta el valor de ${x}`);
      return s;
    };
    if (x === "--de") a.de = path.resolve(v());
    else if (x === "--a") a.a = path.resolve(v());
    else if (x === "--tipo") a.tipo = v();
    else if (x === "--salida") a.salida = path.resolve(v());
    else if (x === "--duracion") a.duracion = Number(String(v()).replace(",", "."));
    else if (x === "--marca") a.marca = v();
    else if (x === "--concurrencia") a.concurrencia = Math.min(4, Math.max(1, Number(v())));
    else throw new Error(`Opción desconocida: ${x}`);
  }
  if (!a.de || !a.a || !a.tipo || !a.salida) throw new Error("Uso: node remotion/transicion.mjs --de <png> --a <png> --tipo <fundido|puertas> --salida <mp4> [--duracion s] [--marca auto|si|no]");
  if (a.tipo === "continuo" || a.tipo === "corte") throw new Error(`«${a.tipo}» no lleva video de transición (continuo: la diapositiva arranca en el cuadro anterior; corte: nada).`);
  if (a.tipo !== "fundido" && a.tipo !== "puertas") throw new Error(`Tipo desconocido: ${a.tipo} (fundido o puertas)`);
  if (!["auto", "si", "no"].includes(a.marca)) throw new Error("--marca: auto, si o no");
  return a;
}

const args = leerArgumentos(process.argv.slice(2));
process.chdir(REMOTION);
const tokens = leerTokens();
const fps = tokens.lienzo.fps;
const duracion = args.duracion ?? tokens.transiciones[args.tipo].duracion_s;
const cuadros = Math.max(1, Math.round(duracion * fps));

const imgDe = leerPng(args.de);
const imgA = leerPng(args.a);
for (const [n, img] of [
  ["--de", imgDe],
  ["--a", imgA],
]) {
  if (img.ancho !== tokens.lienzo.ancho || img.alto !== tokens.lienzo.alto) throw new Error(`${n}: la imagen mide ${img.ancho}×${img.alto} (se espera 1920×1080)`);
}
const z = tokens.reticula.marca_agua.zona;
let marca = args.marca === "si";
if (args.marca === "auto") {
  const zDe = recortar(imgDe, z.x, z.y, z.ancho, z.alto);
  const zA = recortar(imgA, z.x, z.y, z.ancho, z.alto);
  marca = zonaConDibujo(imgDe, z) && comparar(zDe, zA).iguales;
}

const t0 = Date.now();
await ensureBrowser();
const navegador = await openBrowser("chrome");
const paquete = await empaquetar("_Sistema", { silencioso: true });
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "transicion-"));
let ok = false;
try {
  fs.copyFileSync(args.de, path.join(paquete.publico, "de.png"));
  fs.copyFileSync(args.a, path.join(paquete.publico, "a.png"));
  const props = (m) => ({ de: "de.png", a: "a.png", tipo: args.tipo, cuadros, marca: m });
  const base = { serveUrl: paquete.serveUrl, puppeteerInstance: navegador, logLevel: "error" };

  // Los dos extremos tienen que salir idénticos a las imágenes; si con la marca encima
  // no da (por ejemplo, una imagen de Manim con la marca pegada de otra forma), sin ella.
  const extremos = async (m) => {
    const composition = await selectComposition({ ...base, id: "Transicion", inputProps: props(m) });
    const p0 = path.join(tmpDir, `0_${m}.png`);
    const pN = path.join(tmpDir, `n_${m}.png`);
    await renderStill({ ...base, composition, inputProps: props(m), frame: 0, output: p0, imageFormat: "png", overwrite: true });
    await renderStill({ ...base, composition, inputProps: props(m), frame: cuadros, output: pN, imageFormat: "png", overwrite: true });
    return { composition, primero: comparar(imgDe, leerPng(p0)), ultimo: comparar(imgA, leerPng(pN)) };
  };
  let r = await extremos(marca);
  if (marca && !(r.primero.iguales && r.ultimo.iguales)) {
    console.warn("  AVISO: con la marca de agua encima los extremos no salen idénticos; va sin ella.");
    marca = false;
    r = await extremos(false);
  }
  if (!r.primero.iguales || !r.ultimo.iguales) {
    throw new Error(`Los extremos no coinciden con las imágenes: primero ${r.primero.distintos} px distintos, último ${r.ultimo.distintos} px.`);
  }

  fs.mkdirSync(path.dirname(args.salida), { recursive: true });
  const tmp = `${args.salida.replace(/\.mp4$/i, "")}.${process.pid}.tmp.mp4`;
  const { opciones, registro } = opcionesTramo(0, cuadros);
  await renderMedia({ ...base, ...opciones, composition: r.composition, inputProps: props(marca), outputLocation: tmp, concurrency: args.concurrencia, overwrite: true });
  if (registro.length === 0) throw new Error("No se aplicó la receta de frontera");
  fs.renameSync(tmp, args.salida);
  ok = true;
  console.log(
    `${barras(path.relative(PROYECTO, args.salida))}: ${args.tipo}, ${cuadros + 1} cuadros (${duracion} s), marca ${marca ? "encima" : "en la imagen"} · ` +
      `primer cuadro = de: IDÉNTICO · último = a: IDÉNTICO · ${((Date.now() - t0) / 1000).toFixed(1)} s`,
  );
} finally {
  paquete.limpiar();
  fs.rmSync(tmpDir, { recursive: true, force: true });
  await navegador.close({ silent: true }).catch(() => {});
}
if (!ok) process.exit(1);
