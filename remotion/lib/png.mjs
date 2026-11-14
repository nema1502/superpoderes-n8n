// PNG mínimo, sin dependencias: leer (8 bits, gris/RGB/RGBA, sin entrelazado: lo que
// sacan Remotion, ffmpeg y Pillow) y escribir RGBA o RGB. Sirve para comparar fronteras
// píxel a píxel, recortar los PNG para Manim y detectar la marca de agua.
import fs from "node:fs";
import zlib from "node:zlib";

const FIRMA = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

/** Lee un PNG y lo devuelve como RGBA: { ancho, alto, datos: Uint8Array (ancho*alto*4) }. */
export function leerPng(ruta) {
  const b = fs.readFileSync(ruta);
  if (!b.subarray(0, 8).equals(FIRMA)) throw new Error(`${ruta}: no es un PNG`);
  let p = 8;
  let ancho = 0;
  let alto = 0;
  let profundidad = 0;
  let tipo = 0;
  let entrelazado = 0;
  const idat = [];
  while (p < b.length) {
    const largo = b.readUInt32BE(p);
    const nombre = b.toString("latin1", p + 4, p + 8);
    const datos = b.subarray(p + 8, p + 8 + largo);
    if (nombre === "IHDR") {
      ancho = datos.readUInt32BE(0);
      alto = datos.readUInt32BE(4);
      profundidad = datos[8];
      tipo = datos[9];
      entrelazado = datos[12];
    } else if (nombre === "IDAT") idat.push(datos);
    else if (nombre === "IEND") break;
    p += 12 + largo;
  }
  if (profundidad !== 8 || entrelazado !== 0 || ![0, 2, 4, 6].includes(tipo)) {
    throw new Error(`${ruta}: PNG no soportado (profundidad ${profundidad}, tipo ${tipo}, entrelazado ${entrelazado})`);
  }
  const canales = { 0: 1, 2: 3, 4: 2, 6: 4 }[tipo];
  const crudo = zlib.inflateSync(Buffer.concat(idat));
  const fila = ancho * canales;
  const plano = new Uint8Array(alto * fila);
  for (let y = 0; y < alto; y++) {
    const filtro = crudo[y * (fila + 1)];
    const ent = crudo.subarray(y * (fila + 1) + 1, (y + 1) * (fila + 1));
    const sal = plano.subarray(y * fila, (y + 1) * fila);
    const ant = y > 0 ? plano.subarray((y - 1) * fila, y * fila) : null;
    for (let x = 0; x < fila; x++) {
      const a = x >= canales ? sal[x - canales] : 0;
      const u = ant ? ant[x] : 0;
      const c = ant && x >= canales ? ant[x - canales] : 0;
      let v = ent[x];
      if (filtro === 1) v += a;
      else if (filtro === 2) v += u;
      else if (filtro === 3) v += (a + u) >> 1;
      else if (filtro === 4) {
        const q = a + u - c;
        const pa = Math.abs(q - a);
        const pb = Math.abs(q - u);
        const pc = Math.abs(q - c);
        v += pa <= pb && pa <= pc ? a : pb <= pc ? u : c;
      }
      sal[x] = v & 255;
    }
  }
  const datos = new Uint8Array(ancho * alto * 4);
  for (let i = 0, j = 0; i < ancho * alto; i++, j += canales) {
    const o = i * 4;
    if (canales === 1 || canales === 2) {
      datos[o] = datos[o + 1] = datos[o + 2] = plano[j];
      datos[o + 3] = canales === 2 ? plano[j + 1] : 255;
    } else {
      datos[o] = plano[j];
      datos[o + 1] = plano[j + 1];
      datos[o + 2] = plano[j + 2];
      datos[o + 3] = canales === 4 ? plano[j + 3] : 255;
    }
  }
  return { ancho, alto, datos };
}

function trozo(nombre, datos) {
  const largo = Buffer.alloc(4);
  largo.writeUInt32BE(datos.length);
  const cuerpo = Buffer.concat([Buffer.from(nombre, "latin1"), datos]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(zlib.crc32(cuerpo) >>> 0);
  return Buffer.concat([largo, cuerpo, crc]);
}

/** Escribe una imagen RGBA ({ ancho, alto, datos }); con rgb = true descarta el alfa. */
export function escribirPng(ruta, img, { rgb = false } = {}) {
  const canales = rgb ? 3 : 4;
  const fila = img.ancho * canales;
  const crudo = Buffer.alloc(img.alto * (fila + 1));
  for (let y = 0; y < img.alto; y++) {
    crudo[y * (fila + 1)] = 0;
    for (let x = 0; x < img.ancho; x++) {
      const o = (y * img.ancho + x) * 4;
      const d = y * (fila + 1) + 1 + x * canales;
      crudo[d] = img.datos[o];
      crudo[d + 1] = img.datos[o + 1];
      crudo[d + 2] = img.datos[o + 2];
      if (!rgb) crudo[d + 3] = img.datos[o + 3];
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(img.ancho, 0);
  ihdr.writeUInt32BE(img.alto, 4);
  ihdr[8] = 8;
  ihdr[9] = rgb ? 2 : 6;
  ihdr[10] = ihdr[11] = ihdr[12] = 0;
  const salida = Buffer.concat([FIRMA, trozo("IHDR", ihdr), trozo("IDAT", zlib.deflateSync(crudo, { level: 9 })), trozo("IEND", Buffer.alloc(0))]);
  const tmp = `${ruta}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, salida);
  fs.renameSync(tmp, ruta);
}

/** Recorte de una imagen RGBA. */
export function recortar(img, x, y, ancho, alto) {
  const datos = new Uint8Array(ancho * alto * 4);
  for (let f = 0; f < alto; f++) {
    const o = ((y + f) * img.ancho + x) * 4;
    datos.set(img.datos.subarray(o, o + ancho * 4), f * ancho * 4);
  }
  return { ancho, alto, datos };
}

/** Compara dos imágenes RGBA (solo RGB): { iguales, distintos, maximo, caja }. */
export function comparar(a, b) {
  if (a.ancho !== b.ancho || a.alto !== b.alto) return { iguales: false, distintos: Infinity, maximo: 255, caja: null, motivo: `tamaños ${a.ancho}×${a.alto} y ${b.ancho}×${b.alto}` };
  let distintos = 0;
  let maximo = 0;
  let x0 = Infinity;
  let y0 = Infinity;
  let x1 = -1;
  let y1 = -1;
  for (let i = 0; i < a.ancho * a.alto; i++) {
    const o = i * 4;
    const d = Math.max(Math.abs(a.datos[o] - b.datos[o]), Math.abs(a.datos[o + 1] - b.datos[o + 1]), Math.abs(a.datos[o + 2] - b.datos[o + 2]));
    if (d > 0) {
      distintos++;
      if (d > maximo) maximo = d;
      const x = i % a.ancho;
      const y = Math.floor(i / a.ancho);
      x0 = Math.min(x0, x);
      y0 = Math.min(y0, y);
      x1 = Math.max(x1, x);
      y1 = Math.max(y1, y);
    }
  }
  return { iguales: distintos === 0, distintos, maximo, caja: distintos ? [x0, y0, x1, y1] : null };
}

/** ¿La zona tiene algo distinto del color de fondo? (para saber si un cuadro trae la marca de agua). */
export function zonaConDibujo(img, z, fondo = [7, 10, 15], tolerancia = 6) {
  for (let y = z.y; y < z.y + z.alto; y++) {
    for (let x = z.x; x < z.x + z.ancho; x++) {
      const o = (y * img.ancho + x) * 4;
      if (Math.abs(img.datos[o] - fondo[0]) > tolerancia || Math.abs(img.datos[o + 1] - fondo[1]) > tolerancia || Math.abs(img.datos[o + 2] - fondo[2]) > tolerancia) return true;
    }
  }
  return false;
}
