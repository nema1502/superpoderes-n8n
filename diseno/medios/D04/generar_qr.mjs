// El QR de D04 (Anotate al sorteo): lo arma desde contenido/deck.json y lo comprueba en el cuadro.
//
//   node diseno/medios/D04/generar_qr.mjs                       el QR de enlaces.formulario_sorteo del deck
//   node diseno/medios/D04/generar_qr.mjs --prueba <dirección>  un QR de prueba (para mirar el armado
//                                                                antes de tener la dirección real)
//   node diseno/medios/D04/generar_qr.mjs --comprobar <png>     lee el QR del cuadro con jsqr y lo
//                                                                compara con qr.json (sale con 1 si no da)
//
// Deja la matriz en diseno/medios/D04/qr.json, que la diapositiva (remotion/src/diapos/
// D04AnotateAlSorteo.tsx) importa al empaquetarse. Mientras el deck diga FORMULARIO_PENDIENTE no hay
// matriz y la diapositiva anuncia el sorteo sin QR (sin tarjeta). Si la dirección del deck
// cambia, hay que correr este guion de nuevo antes de renderizar D04: si qr.json no coincide con el
// deck, el render falla y lo dice.
//
// Usa qrcode-generator (2.0.4, nivel de corrección M) y jsqr (1.4.0), de npm. No están entre las
// dependencias de remotion/: se buscan en las carpetas node_modules que diga la variable QR_MODULOS
// (varias, separadas como en PATH), y si no, en remotion/node_modules y en node_modules de la raíz.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "../../..");
const SALIDA = path.join(AQUI, "qr.json");
const DECK = path.join(RAIZ, "contenido/deck.json");
const PENDIENTE = "FORMULARIO_PENDIENTE";
const NIVEL = "M";
// La tarjeta del QR en el cuadro (deck D04.1): x 1200-1800, y 120-720.
const TARJETA = { x0: 1200, y0: 120, x1: 1800, y1: 720 };

function cargar(nombre) {
  const propios = (process.env.QR_MODULOS ?? "").split(path.delimiter).filter(Boolean);
  const lugares = [...propios, path.join(RAIZ, "remotion/node_modules"), path.join(RAIZ, "node_modules")];
  for (const l of lugares) {
    try {
      // Desde un archivo al lado de la carpeta node_modules, como lo buscaría un guion de ese proyecto.
      return createRequire(path.join(path.dirname(path.resolve(l)), "_.js"))(nombre);
    } catch {
      // probar el siguiente lugar
    }
  }
  throw new Error(`No encuentro ${nombre}. Instalalo o poné en QR_MODULOS la carpeta node_modules que lo tiene.`);
}

function direccionDelDeck() {
  const deck = JSON.parse(fs.readFileSync(DECK, "utf8"));
  const d = deck.enlaces?.formulario_sorteo;
  if (typeof d !== "string" || !d) throw new Error("contenido/deck.json no trae enlaces.formulario_sorteo");
  return d;
}

function generar(texto, prueba) {
  const pendiente = texto.includes(PENDIENTE);
  const datos = {
    _que_es: "Matriz del QR de D04, generada por diseno/medios/D04/generar_qr.mjs desde enlaces.formulario_sorteo del deck. No se edita a mano.",
    texto,
    pendiente,
    prueba,
    nivel: NIVEL,
    modulos: 0,
    filas: [],
  };
  if (!pendiente) {
    const qrcode = cargar("qrcode-generator");
    const qr = qrcode(0, NIVEL);
    qr.addData(texto, "Byte");
    qr.make();
    const n = qr.getModuleCount();
    datos.modulos = n;
    for (let r = 0; r < n; r++) {
      let fila = "";
      for (let c = 0; c < n; c++) fila += qr.isDark(r, c) ? "1" : "0";
      datos.filas.push(fila);
    }
  }
  fs.writeFileSync(SALIDA, JSON.stringify(datos, null, 1) + "\n");
  const que = pendiente ? "pendiente: D04 va sin QR" : `${datos.modulos} por ${datos.modulos} módulos, nivel ${NIVEL}`;
  console.log(`qr.json: ${prueba ? "PRUEBA " : ""}"${texto}" (${que})`);
}

async function comprobar(png) {
  const { leerPng } = await import(new URL("../../../remotion/lib/png.mjs", import.meta.url));
  const jsQR = cargar("jsqr");
  const qr = JSON.parse(fs.readFileSync(SALIDA, "utf8"));
  const img = leerPng(png);
  // Se lee la tarjeta con un margen de 20 px, como la vería un celular que apunta al QR.
  const m = 20;
  const x0 = TARJETA.x0 - m;
  const y0 = TARJETA.y0 - m;
  const w = TARJETA.x1 - TARJETA.x0 + 2 * m;
  const h = TARJETA.y1 - TARJETA.y0 + 2 * m;
  const rgba = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const o = ((y0 + y) * img.ancho + (x0 + x)) * 4;
      const d = (y * w + x) * 4;
      rgba[d] = img.datos[o];
      rgba[d + 1] = img.datos[o + 1];
      rgba[d + 2] = img.datos[o + 2];
      rgba[d + 3] = 255;
    }
  }
  const leido = jsQR(rgba, w, h, { inversionAttempts: "attemptBoth" });
  if (qr.pendiente) {
    if (leido) {
      console.log(`MAL: el cuadro ${png} tiene un QR legible ("${leido.data}") y el deck dice ${PENDIENTE}.`);
      process.exit(1);
    }
    console.log(`BIEN: ${png} no tiene QR legible (el deck dice ${PENDIENTE}: D04 va sin QR).`);
    return;
  }
  if (!leido) {
    console.log(`MAL: jsqr no encuentra un QR en la tarjeta de ${png}.`);
    process.exit(1);
  }
  if (leido.data !== qr.texto) {
    console.log(`MAL: el QR de ${png} dice "${leido.data}" y tenía que decir "${qr.texto}".`);
    process.exit(1);
  }
  console.log(`BIEN: el QR de ${png} se lee con jsqr y dice "${leido.data}" (versión ${leido.version}).`);
}

const args = process.argv.slice(2);
if (args[0] === "--comprobar") {
  if (!args[1]) throw new Error("Uso: --comprobar <png>");
  await comprobar(path.resolve(args[1]));
} else if (args[0] === "--prueba") {
  if (!args[1]) throw new Error("Uso: --prueba <dirección>");
  generar(args[1], true);
} else {
  generar(direccionDelDeck(), false);
}
