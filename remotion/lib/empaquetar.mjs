// Empaquetado de UNA entrada (una diapositiva o el sistema) con su propia caché de webpack
// y su propia carpeta de bundle, para que dos procesos puedan renderizar a la vez sin
// pisarse:
//   - caché: Remotion la guarda en node_modules/.cache/webpack/remotion-production-<versión>/
//     <hash>, con un hash de la configuración que incluye la entrada: cada entrada tiene la
//     suya. Un candado por entrada (una carpeta que se crea de forma atómica en
//     node_modules/.cache/charla/candados/) hace que dos procesos no la escriban a la vez:
//     el segundo espera;
//   - el bundle va a node_modules/.cache/charla/bundles/<entrada>-<pid>-<hora>/ (único por
//     proceso) y se borra al terminar.
import { bundle } from "@remotion/bundler";
import fs from "node:fs";
import path from "node:path";
import { CACHE, PUBLICO, REMOTION } from "./rutas.mjs";

const espera = (ms) => new Promise((r) => setTimeout(r, ms));

function vivo(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (e) {
    return e.code === "EPERM";
  }
}

/** Corre fn con un candado exclusivo (carpeta `dir`). Espera hasta 15 min a otro proceso. */
export async function conCandado(dir, fn, { avisar = true } = {}) {
  fs.mkdirSync(path.dirname(dir), { recursive: true });
  const inicio = Date.now();
  let avisado = false;
  for (;;) {
    try {
      fs.mkdirSync(dir);
      fs.writeFileSync(path.join(dir, "pid"), String(process.pid));
      break;
    } catch (e) {
      if (e.code !== "EEXIST") throw e;
      let pid = NaN;
      let edad = 0;
      try {
        pid = Number(fs.readFileSync(path.join(dir, "pid"), "utf8"));
        edad = Date.now() - fs.statSync(dir).mtimeMs;
      } catch {
        /* recién creado: todavía sin pid */
      }
      if ((Number.isFinite(pid) && !vivo(pid)) || edad > 15 * 60 * 1000) {
        fs.rmSync(dir, { recursive: true, force: true });
        continue;
      }
      if (avisar && !avisado) {
        console.log(`  (esperando a otro proceso que usa ${path.basename(dir)}…)`);
        avisado = true;
      }
      if (Date.now() - inicio > 15 * 60 * 1000) throw new Error(`Candado ${dir} tomado hace más de 15 min`);
      await espera(400);
    }
  }
  try {
    return await fn();
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/**
 * Empaqueta remotion/src/entradas/<nombre>.ts. Devuelve { serveUrl, publico, limpiar }:
 * `publico` es la carpeta public del bundle (ahí se copian anterior.png y los PNG de una
 * transición); `limpiar()` borra el bundle.
 */
export async function empaquetar(nombre, { silencioso = false } = {}) {
  const entryPoint = path.join(REMOTION, "src", "entradas", `${nombre}.ts`);
  if (!fs.existsSync(entryPoint)) throw new Error(`No existe la entrada ${entryPoint} (correr node remotion/generar_registro.mjs)`);
  const outDir = path.join(CACHE, "bundles", `${nombre}-${process.pid}-${Date.now()}`);
  const t0 = Date.now();
  const serveUrl = await conCandado(path.join(CACHE, "candados", `webpack-${nombre}`), () =>
    bundle({
      entryPoint,
      outDir,
      publicDir: fs.existsSync(PUBLICO) ? PUBLICO : null,
      enableCaching: true,
    }),
  );
  const publico = path.join(outDir, "public");
  fs.mkdirSync(publico, { recursive: true });
  if (!silencioso) console.log(`  bundle de ${nombre}: ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  return {
    serveUrl,
    publico,
    limpiar: () => fs.rmSync(outDir, { recursive: true, force: true }),
  };
}
