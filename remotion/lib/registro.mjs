// Genera el código que une deck.json con las diapositivas que existen:
//   src/diapos/index.ts        registro de TODAS las diapositivas de deck.json
//   src/entradas/<ID>.ts       una entrada aislada por diapositiva (registerRoot de esa sola)
//   src/comun/iconos.generado.ts   los íconos de manim/comun/iconos como datos de SVG
// Las diapositivas sin archivo se registran como provisionales (sistema/Provisional.tsx).
// Escribe solo si el contenido cambió, y de forma atómica (archivo temporal + rename):
// dos procesos pueden correrlo a la vez sin dejar un archivo a medias.
import fs from "node:fs";
import path from "node:path";
import { leerDeck } from "./deck.mjs";
import { DIAPOS, ENTRADAS, ICONOS, SRC, barras } from "./rutas.mjs";

const CABECERA = "// GENERADO por remotion/generar_registro.mjs: no editar a mano (se rehace en cada render).";
const PATRON_ARCHIVO = /^((?:D\d{2})|(?:A\d{1,2}))([A-Z][A-Za-z0-9]*)\.tsx$/;

function escribirSiCambia(ruta, contenido) {
  const antes = fs.existsSync(ruta) ? fs.readFileSync(ruta, "utf8") : null;
  if (antes === contenido) return false;
  fs.mkdirSync(path.dirname(ruta), { recursive: true });
  const tmp = `${ruta}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, contenido, "utf8");
  fs.renameSync(tmp, ruta);
  return true;
}

/** Archivos de diapositiva que existen: id -> { archivo, nombre, componente, opciones } */
export function diapositivasConArchivo(deck) {
  const ids = new Set(deck.diapositivas.map((d) => d.id));
  const halladas = new Map();
  const problemas = [];
  for (const archivo of fs.readdirSync(DIAPOS)) {
    if (!archivo.endsWith(".tsx")) continue;
    const m = PATRON_ARCHIVO.exec(archivo);
    if (!m) {
      problemas.push(`src/diapos/${archivo}: el nombre tiene que ser <ID><Nombre>.tsx (por ejemplo D06IdeaClave.tsx)`);
      continue;
    }
    const [, id, nombre] = m;
    if (!ids.has(id)) {
      problemas.push(`src/diapos/${archivo}: ${id} no está en deck.json`);
      continue;
    }
    if (halladas.has(id)) {
      problemas.push(`src/diapos/${archivo}: ${id} ya tiene archivo (${halladas.get(id).archivo})`);
      continue;
    }
    const texto = fs.readFileSync(path.join(DIAPOS, archivo), "utf8");
    const componente = `${id}${nombre}`;
    const exporta = (n) => new RegExp(`export\\s+(?:const|function)\\s+${n}\\b`).test(texto);
    if (!exporta(componente)) problemas.push(`src/diapos/${archivo}: falta «export const ${componente}» (el componente)`);
    if (!exporta("pasos")) problemas.push(`src/diapos/${archivo}: falta «export const pasos» (duraciones de cada paso)`);
    const d = deck.diapositivas.find((x) => x.id === id);
    if (d.nombre && d.nombre !== nombre) {
      console.warn(`AVISO: src/diapos/${archivo}: en deck.json la escena se llama ${d.nombre}`);
    }
    halladas.set(id, { archivo, nombre, componente, opciones: exporta("opciones") });
  }
  if (problemas.length) throw new Error(`Registro de diapositivas:\n  ${problemas.join("\n  ")}`);
  return halladas;
}

function modulo(id, h, alias) {
  if (!h) return "null";
  const op = h.opciones ? `, opciones: ${alias}.opciones` : "";
  return `{ componente: ${alias}.${h.componente}, pasos: ${alias}.pasos${op} }`;
}

function generarIndice(deck, halladas) {
  const imports = [];
  const filas = [];
  for (const d of deck.diapositivas) {
    const h = halladas.get(d.id);
    if (h) imports.push(`import * as ${d.id} from "./${h.archivo.replace(/\.tsx$/, "")}";`);
    filas.push(`  { id: "${d.id}", modulo: ${modulo(d.id, h, d.id)} },`);
  }
  return [
    CABECERA,
    "// Todas las diapositivas de contenido/deck.json, en el orden del .pptx.",
    "// modulo = null: todavía no tiene archivo y se muestra la provisional (sistema/Provisional.tsx).",
    'import type { DefDiapo } from "../sistema/tipos";',
    ...imports,
    "",
    "export const DIAPOS: DefDiapo[] = [",
    ...filas,
    "];",
    "",
  ].join("\n");
}

function generarEntrada(id, h) {
  const imp = h ? `import * as m from "../diapos/${h.archivo.replace(/\.tsx$/, "")}";\n` : "";
  return [
    CABECERA,
    `// Entrada aislada de ${id}: compila solo esta diapositiva (y lo común).`,
    'import { registerRoot } from "remotion";',
    'import { raizDe } from "../sistema/registrar";',
    `${imp}registerRoot(raizDe({ id: "${id}", modulo: ${modulo(id, h, "m")} }));`,
    "",
  ].join("\n");
}

function generarIconos() {
  const nombres = fs.readdirSync(ICONOS).filter((f) => f.endsWith(".svg")).sort();
  const filas = [];
  for (const f of nombres) {
    const svg = fs.readFileSync(path.join(ICONOS, f), "utf8");
    const vb = /viewBox="0 0 ([\d.]+) ([\d.]+)"/.exec(svg);
    const caminos = [...svg.matchAll(/<path[^>]*\sd="([^"]+)"/g)].map((x) => x[1]);
    if (!vb || caminos.length !== 1) throw new Error(`Ícono ${f}: se espera un viewBox 0 0 W H y un solo <path>`);
    filas.push(`  "${f.replace(/\.svg$/, "")}": { ancho: ${vb[1]}, alto: ${vb[2]}, d: ${JSON.stringify(caminos[0])} },`);
  }
  return [
    CABECERA,
    "// Íconos de manim/comun/iconos/*.svg como datos (Font Awesome Free 6.7.2, solid, CC BY 4.0:",
    "// «Íconos: Font Awesome»). Para agregar uno: copiar el .svg a esa carpeta y volver a generar.",
    "export const ICONOS_SVG = {",
    ...filas,
    "} as const;",
    "",
    "export type NombreIcono = keyof typeof ICONOS_SVG;",
    "",
  ].join("\n");
}

/** Genera todo. Devuelve { diapositivas, conArchivo, cambiados }. */
export function generarRegistro({ silencioso = false } = {}) {
  const deck = leerDeck();
  fs.mkdirSync(DIAPOS, { recursive: true });
  fs.mkdirSync(ENTRADAS, { recursive: true });
  const halladas = diapositivasConArchivo(deck);
  const cambiados = [];
  const anotar = (ruta, contenido) => {
    if (escribirSiCambia(ruta, contenido)) cambiados.push(barras(path.relative(SRC, ruta)));
  };
  anotar(path.join(DIAPOS, "index.ts"), generarIndice(deck, halladas));
  const ids = new Set();
  for (const d of deck.diapositivas) {
    ids.add(d.id);
    anotar(path.join(ENTRADAS, `${d.id}.ts`), generarEntrada(d.id, halladas.get(d.id)));
  }
  // Entradas generadas de diapositivas que ya no están en deck.json: se borran.
  for (const f of fs.readdirSync(ENTRADAS)) {
    const id = f.replace(/\.ts$/, "");
    const ruta = path.join(ENTRADAS, f);
    if (!ids.has(id) && fs.readFileSync(ruta, "utf8").startsWith(CABECERA)) {
      fs.rmSync(ruta);
      cambiados.push(`(borrada) entradas/${f}`);
    }
  }
  anotar(path.join(SRC, "comun", "iconos.generado.ts"), generarIconos());
  if (!silencioso) {
    const con = [...halladas.keys()];
    console.log(`Registro: ${deck.diapositivas.length} diapositivas, ${con.length} con archivo${con.length ? ` (${con.join(" ")})` : ""}, el resto provisionales.`);
    if (cambiados.length) console.log(`  actualizados: ${cambiados.join(", ")}`);
  }
  return { diapositivas: deck.diapositivas.map((d) => d.id), conArchivo: halladas, cambiados };
}
