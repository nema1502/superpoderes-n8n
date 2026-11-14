// Renderiza diapositivas de Remotion paso por paso, cada una desde su entrada aislada
// (src/entradas/<ID>.ts: el error de una no rompe el render de otra).
//
//   node remotion/render.mjs D06 D08 ...          los pasos -> render/pasos/<ID>/<ID>_<k>.mp4
//                                                 y sus cortes -> render/cuadros/<ID>_<k>.png
//   node remotion/render.mjs --still D06 pasos    solo los cortes en PNG (k = 0: el primer
//                                                 cuadro; k = 1…n: el último de cada paso)
//   node remotion/render.mjs --still D06 45       el cuadro 45 -> render/cuadros/D06_c45.png
//
// Opciones: --concurrencia N (≤ 4; 4 por defecto) · --crf N (borrador, sin la receta de
// frontera) · --salida <carpeta> (en vez de render/) · --refrescar-anterior (vuelve a
// sacar el último cuadro de la diapositiva anterior) · --forzar-provisional (renderiza la
// provisional de una diapositiva de Manim; no pisa nada que no sea una provisional).
//
// Videos: h264 High, yuv420p, BT.709, sin audio, QP 16 y cuadro clave en el último cuadro
// (receta de frontera de docs/infra.md §7): el primer cuadro del paso k+1 es idéntico al
// último del paso k. Con la entrada «continuo», el último cuadro de la anterior se toma de
// render/cuadros/<anterior>_<n>.png (si falta o está viejo y es de Remotion, se saca
// primero) y al final se comprueba que el primer cuadro de esta sea idéntico.
//
// Puede correr desde dos procesos a la vez: cada entrada tiene su caché de webpack (con
// candado) y cada proceso su bundle; los archivos se escriben aparte y se renombran.
import { ensureBrowser, openBrowser, renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { diapo, duracionesPropias, entradaDe, leerDeck } from "./lib/deck.mjs";
import { empaquetar } from "./lib/empaquetar.mjs";
import { comparar, leerPng } from "./lib/png.mjs";
import { opcionesTramo } from "./lib/receta.mjs";
import { generarRegistro } from "./lib/registro.mjs";
import { barras, DECK, DIAPOS, PROYECTO, REMOTION, RENDER, SRC, TOKENS } from "./lib/rutas.mjs";

const seg = (ms) => `${(ms / 1000).toFixed(1)} s`;

function leerArgumentos(argv) {
  const a = { ids: [], still: null, concurrencia: 4, crf: null, salida: RENDER, refrescar: false, forzarProvisional: false };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x === "--still") {
      a.still = { id: argv[++i], que: argv[++i] };
      if (!a.still.id || !a.still.que) throw new Error("Uso: --still <ID> <cuadro|pasos>");
    } else if (x === "--concurrencia") a.concurrencia = Math.min(4, Math.max(1, Number(argv[++i])));
    else if (x === "--crf") a.crf = Number(argv[++i]);
    else if (x === "--salida") a.salida = path.resolve(argv[++i]);
    else if (x === "--refrescar-anterior") a.refrescar = true;
    else if (x === "--forzar-provisional") a.forzarProvisional = true;
    else if (x.startsWith("--")) throw new Error(`Opción desconocida: ${x}`);
    else a.ids.push(x.toUpperCase());
  }
  if (!a.still && a.ids.length === 0) throw new Error("Falta qué renderizar: node remotion/render.mjs <ID...>  o  --still <ID> <cuadro|pasos>");
  if (a.still) a.still.id = a.still.id.toUpperCase();
  return a;
}

const args = leerArgumentos(process.argv.slice(2));
// Remotion busca su Chrome en <carpeta con package.json>/node_modules/.remotion: desde la
// raíz del proyecto (que no tiene package.json) bajaría otro. Se trabaja desde remotion/.
process.chdir(REMOTION);
const dirPasos = path.join(args.salida, "pasos");
const dirCuadros = path.join(args.salida, "cuadros");
const avisos = new Set();
const onBrowserLog = (log) => {
  if (log.type === "warning" || log.type === "warn" || log.text.startsWith("AVISO")) {
    if (!avisos.has(log.text)) {
      avisos.add(log.text);
      console.warn(`  ${log.text.startsWith("AVISO") ? "" : "AVISO del navegador: "}${log.text}`);
    }
  } else if (log.type === "error") console.error(`  ERROR del navegador: ${log.text}`);
};

function escribirAtomico(destino, generar) {
  fs.mkdirSync(path.dirname(destino), { recursive: true });
  const ext = path.extname(destino);
  const tmp = `${destino.slice(0, -ext.length)}.${process.pid}.tmp${ext}`;
  return generar(tmp).then(
    () => fs.renameSync(tmp, destino),
    (e) => {
      fs.rmSync(tmp, { force: true });
      throw e;
    },
  );
}

/** Fecha de modificación más nueva entre los fuentes que cambian una diapositiva de Remotion. */
function fuentesMasNuevas(id) {
  const archivos = [TOKENS, DECK];
  const archivoDiapo = fs.readdirSync(DIAPOS).find((f) => new RegExp(`^${id}[A-Z][A-Za-z0-9]*\\.tsx$`).test(f));
  if (archivoDiapo) archivos.push(path.join(DIAPOS, archivoDiapo));
  for (const dir of ["comun", "sistema"]) for (const f of fs.readdirSync(path.join(SRC, dir))) archivos.push(path.join(SRC, dir, f));
  archivos.push(path.join(SRC, "pasos.ts"), path.join(SRC, "deck.ts"), path.join(SRC, "tokens.ts"));
  return Math.max(...archivos.filter((f) => fs.existsSync(f)).map((f) => fs.statSync(f).mtimeMs));
}

let navegador = null;
const deck = leerDeck();

/** Renderiza cortes (y videos si `videos`) de una diapositiva. Devuelve un resumen. */
async function renderDiapo(id, { videos = true, cortes = "todos", cuadroSuelto = null } = {}) {
  const d = diapo(deck, id);
  if (d.motor !== "remotion" && !args.forzarProvisional) {
    throw new Error(`${id} es de Manim: se renderiza con .venv/Scripts/python.exe manim/render_diapo.py ${id} (o --forzar-provisional para su provisional).`);
  }
  const t0 = performance.now();
  const anterior = await prepararAnterior(id);
  const paquete = await empaquetar(id);
  try {
    if (anterior.ruta) fs.copyFileSync(anterior.ruta, path.join(paquete.publico, "anterior.png"));
    const inputProps = anterior.ruta ? { anterior: "anterior.png" } : {};
    const base = { serveUrl: paquete.serveUrl, inputProps, puppeteerInstance: navegador, onBrowserLog, logLevel: "error" };
    const comp = await selectComposition({ ...base, id });
    const c = comp.props.cortes;
    const n = c.length - 1;
    const esperado = duracionesPropias(deck, id);
    comp.props.pasos.forEach((dur, k) => {
      if (Math.abs(dur - esperado[k]) > 0.0005) console.warn(`  AVISO: ${id}.${k + 1} dura ${dur} s en el archivo y ${esperado[k]} s según deck.json (reportarlo para que el deck y el mapa de tiempos coincidan).`);
    });
    const resumen = { id, n, cuadros: c[n] + 1, frontera: null };

    if (cuadroSuelto !== null) {
      if (cuadroSuelto < 0 || cuadroSuelto > c[n]) throw new Error(`${id} tiene cuadros 0-${c[n]}`);
      const destino = path.join(dirCuadros, `${id}_c${cuadroSuelto}.png`);
      await escribirAtomico(destino, (tmp) => renderStill({ ...base, composition: comp, frame: cuadroSuelto, output: tmp, imageFormat: "png", overwrite: true }));
      console.log(`  ${barras(path.relative(PROYECTO, destino))}`);
      return resumen;
    }

    if (videos) {
      fs.mkdirSync(path.join(dirPasos, id), { recursive: true });
      for (let k = 1; k <= n; k++) {
        const destino = path.join(dirPasos, id, `${id}_${k}.mp4`);
        const { opciones, registro } = opcionesTramo(c[k - 1], c[k], args.crf);
        await escribirAtomico(destino, (tmp) =>
          renderMedia({ ...base, ...opciones, composition: comp, outputLocation: tmp, concurrency: args.concurrencia, overwrite: true }),
        );
        if (args.crf === null && registro.length === 0) throw new Error(`${id}_${k}: no se aplicó la receta de frontera (¿cambió Remotion sus argumentos de ffmpeg?)`);
        process.stdout.write(`  ${id}_${k}.mp4: ${c[k] - c[k - 1] + 1} cuadros\n`);
      }
      // Pasos que sobran de un render anterior con más pasos.
      for (const f of fs.readdirSync(path.join(dirPasos, id))) {
        const m = new RegExp(`^${id}_(\\d+)\\.mp4$`).exec(f);
        if (m && Number(m[1]) > n) fs.rmSync(path.join(dirPasos, id, f));
      }
    }

    if (cortes) {
      const lista = cortes === "ultimo" ? [n] : [...Array(n + 1).keys()];
      for (const k of lista) {
        const destino = path.join(dirCuadros, `${id}_${k}.png`);
        await escribirAtomico(destino, (tmp) => renderStill({ ...base, composition: comp, frame: c[k], output: tmp, imageFormat: "png", overwrite: true }));
      }
    }

    // La frontera con la diapositiva anterior (entrada continua): primer cuadro idéntico.
    if (anterior.ruta && cortes && cortes !== "ultimo") {
      const r = comparar(leerPng(anterior.ruta), leerPng(path.join(dirCuadros, `${id}_0.png`)));
      resumen.frontera = r.iguales ? `frontera con ${anterior.desde}: IDÉNTICA` : `frontera con ${anterior.desde}: DISTINTA (${r.distintos} px, máx. ${r.maximo}, caja ${r.caja?.join(",")})`;
    } else if (anterior.provisional) resumen.frontera = `frontera con ${anterior.desde}: SIN CUADRO (provisional)`;
    resumen.ms = performance.now() - t0;
    return resumen;
  } finally {
    paquete.limpiar();
  }
}

/** El último cuadro de la diapositiva de la que se entra (si la entrada es continua). */
async function prepararAnterior(id) {
  const e = entradaDe(deck, id);
  if (e.tipo !== "continuo" || !e.desde) return { ruta: null };
  const prev = diapo(deck, e.desde);
  const n = prev.pasos.length;
  const ruta = path.join(dirCuadros, `${e.desde}_${n}.png`);
  const desde = `${e.desde}.${n}`;
  if (prev.motor === "remotion") {
    const viejo = fs.existsSync(ruta) && fs.statSync(ruta).mtimeMs < fuentesMasNuevas(e.desde);
    if (!fs.existsSync(ruta) || viejo || args.refrescar) {
      console.log(`  ${id} entra desde ${desde}: saco su último cuadro${viejo ? " (el que había estaba viejo)" : ""}`);
      await renderDiapo(e.desde, { videos: false, cortes: "ultimo" });
    }
    return { ruta, desde };
  }
  if (fs.existsSync(ruta)) return { ruta, desde };
  console.warn(`  AVISO: falta ${barras(path.relative(PROYECTO, ruta))} (${e.desde} es de Manim): ${id} arranca desde un esquema provisional y su frontera no va a empalmar.`);
  return { ruta: null, desde, provisional: true };
}

async function main() {
  const t0 = performance.now();
  const reg = generarRegistro({ silencioso: true });
  console.log(`Registro al día (${reg.diapositivas.length} diapositivas, ${reg.conArchivo.size} con archivo).`);
  await ensureBrowser();
  navegador = await openBrowser("chrome");
  const errores = [];
  try {
    if (args.still) {
      const { id, que } = args.still;
      console.log(`${id}: cuadros (${que})`);
      if (que === "pasos") {
        const r = await renderDiapo(id, { videos: false, cortes: "todos" });
        console.log(`  ${barras(path.relative(PROYECTO, dirCuadros))}/${id}_0..${r.n}.png${r.frontera ? ` · ${r.frontera}` : ""}`);
      } else if (/^\d+$/.test(que)) await renderDiapo(id, { videos: false, cortes: false, cuadroSuelto: Number(que) });
      else throw new Error(`--still ${id} ${que}: se espera un número de cuadro o «pasos»`);
    } else {
      for (const id of args.ids) {
        console.log(`${id}:`);
        try {
          const r = await renderDiapo(id);
          console.log(`  ${id}: ${r.n} pasos, ${r.cuadros} cuadros en ${seg(r.ms)} -> ${barras(path.relative(PROYECTO, path.join(dirPasos, id)))}/${r.frontera ? ` · ${r.frontera}` : ""}`);
        } catch (e) {
          console.error(`  ${id}: ERROR\n${String(e.stack || e.message || e)
            .split("\n")
            .slice(0, 12)
            .map((l) => `    ${l}`)
            .join("\n")}`);
          errores.push(id);
        }
      }
    }
  } finally {
    await navegador.close({ silent: true });
  }
  console.log(`Listo en ${seg(performance.now() - t0)}${errores.length ? ` · con errores: ${errores.join(" ")}` : ""}.`);
  if (errores.length) process.exit(1);
}

main().catch((e) => {
  console.error(`ERROR: ${e.message || e}`);
  process.exit(1);
});
