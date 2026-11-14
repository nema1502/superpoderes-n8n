// Texto y Titulo: el único camino para escribir en pantalla. Miden con
// @remotion/layout-utils (la fuente real, Segoe UI Bold) y NUNCA desbordan la zona
// segura: si un renglón no entra, primero lo parten (si se permiten varios renglones)
// y después lo achican hasta el mínimo legible; si ni así entra, el render falla con
// el texto culpable. El texto no se cambia: se ajusta el diseño o se reporta.
import { measureText } from "@remotion/layout-utils";
import React, { createContext, useContext } from "react";
import { useTramo } from "../pasos";
import { COLOR, conAlfa, CURVA, MOV, OPACIDAD, TIPO, ZONA, type NombreTamano } from "../tokens";
import { useAtenuarAmbar, type Estilo } from "./movimiento";

export type Alineacion = "izq" | "centro" | "der";
/** Partes del texto en otro color: "tipo C" (ámbar), ["X", "Y"] o { "ganas de irse": COLOR.rojo }. */
export type Resaltado = string | string[] | Record<string, string>;

/** px de un tamaño de la escala (o el número tal cual). */
export function px(tam: number | NombreTamano): number {
  return typeof tam === "number" ? tam : TIPO.escala[tam];
}

/** Ancho en px de un renglón en Segoe UI Bold. */
export function medirTexto(texto: string, tam: number | NombreTamano, numeros = false): number {
  return measureText({
    text: texto,
    fontFamily: TIPO.familia,
    fontSize: px(tam),
    fontWeight: TIPO.peso,
    fontVariantNumeric: numeros ? "tabular-nums" : undefined,
  }).width;
}

/** Interlineado por defecto según el tamaño: títulos 1,1; ideas y frases 1,25; lectura 1,3. */
export function interlineadoDe(tam: number): number {
  if (tam >= TIPO.escala.grande) return TIPO.interlineado.titulo;
  if (tam >= TIPO.escala.idea_arriba) return TIPO.interlineado.idea;
  return TIPO.interlineado.lectura;
}

/** Ancho disponible dentro de la zona segura para un texto anclado en x. */
export function anchoDisponible(x: number, alinear: Alineacion): number {
  if (alinear === "izq") return ZONA.x1 - x;
  if (alinear === "der") return x - ZONA.x0;
  return 2 * Math.min(x - ZONA.x0, ZONA.x1 - x);
}

type Renglon = { texto: string; inicio: number; ancho: number };

function partir(texto: string, tam: number, maxAncho: number, numeros: boolean): Renglon[] {
  const renglones: Renglon[] = [];
  let base = 0;
  for (const parrafo of texto.split("\n")) {
    const palabras = [...parrafo.matchAll(/\S+/g)];
    let actual: { desde: number; hasta: number } | null = null;
    for (const m of palabras) {
      const ini = base + (m.index ?? 0);
      const fin = ini + m[0].length;
      if (!actual) {
        actual = { desde: ini, hasta: fin };
        continue;
      }
      const candidato = texto.slice(actual.desde, fin);
      if (medirTexto(candidato, tam, numeros) <= maxAncho) actual.hasta = fin;
      else {
        renglones.push({ texto: texto.slice(actual.desde, actual.hasta), inicio: actual.desde, ancho: 0 });
        actual = { desde: ini, hasta: fin };
      }
    }
    if (actual) renglones.push({ texto: texto.slice(actual.desde, actual.hasta), inicio: actual.desde, ancho: 0 });
    else renglones.push({ texto: "", inicio: base, ancho: 0 });
    base += parrafo.length + 1;
  }
  for (const r of renglones) r.ancho = medirTexto(r.texto, tam, numeros);
  return renglones;
}

type Diseno = { tam: number; renglones: Renglon[]; achicado: boolean };

/** Elige tamaño y renglones para que el texto entre en maxAncho y maxLineas. */
export function disponerTexto(texto: string, tam: number, maxAncho: number, maxLineas: number, minimo: number, numeros = false): Diseno {
  for (let t = tam; t >= minimo; t -= t > 80 ? 2 : 1) {
    const renglones = partir(texto, t, maxAncho, numeros);
    if (renglones.length <= maxLineas && renglones.every((r) => r.ancho <= maxAncho + 0.5)) {
      return { tam: t, renglones, achicado: t < tam };
    }
  }
  const medida = Math.round(medirTexto(texto, tam, numeros));
  throw new Error(
    `El texto «${texto}» no entra: a ${tam} px mide ${medida} px y el lugar es de ${Math.round(maxAncho)} px` +
      ` en ${maxLineas} renglón(es), sin bajar de ${minimo} px. No cambiar el texto: ajustar el diseño (posición, ancho o renglones) o reportarlo.`,
  );
}

type Tramo = { desde: number; hasta: number; color: string };

function tramosResaltados(texto: string, resaltar: Resaltado | undefined, colorBase: string): Tramo[] {
  if (!resaltar) return [];
  const mapa: Record<string, string> =
    typeof resaltar === "string" ? { [resaltar]: COLOR.ambar } : Array.isArray(resaltar) ? Object.fromEntries(resaltar.map((r) => [r, COLOR.ambar])) : resaltar;
  const tramos: Tramo[] = [];
  for (const [parte, color] of Object.entries(mapa)) {
    let i = texto.indexOf(parte);
    if (i < 0) throw new Error(`Texto: «${parte}» no aparece en «${texto}» (el resaltado tiene que coincidir letra por letra).`);
    while (i >= 0) {
      if (color !== colorBase) tramos.push({ desde: i, hasta: i + parte.length, color });
      i = texto.indexOf(parte, i + parte.length);
    }
  }
  return tramos.sort((a, b) => a.desde - b.desde);
}

// ---------- Barrido de luz ----------

const BarridoContext = createContext<number | null>(null);

/**
 * Barrido de luz: una franja diagonal de 120 px, hueso al 18 %, inclinada 20°, que cruza
 * el texto de izquierda a derecha en 0,5 s, recortada por la forma de las letras, una
 * sola vez. Envuelve a los <Texto> que cruza. Solo la idea clave (D06.2, D20.1).
 * Sobre texto hueso casi no se ve: va sobre la línea ámbar.
 */
export const BarridoLuz: React.FC<{ paso: number; retraso?: number; dura?: number; children: React.ReactNode }> = ({ paso, retraso = 0, dura = MOV.dura.barrido, children }) => {
  const p = useTramo(paso, retraso, dura, CURVA.lineal);
  return <BarridoContext.Provider value={p}>{children}</BarridoContext.Provider>;
};

// ---------- Texto ----------

export type PropsTexto = {
  /** El texto exacto (de deck.json). Un "\n" fuerza un renglón nuevo. */
  children: string;
  /** Ancla horizontal (según `alinear`) y vertical (centro del renglón o del bloque). */
  x: number;
  y: number;
  /** px o nombre de la escala (TIPO.escala): "lectura" = 60, "frase" = 72… */
  tam?: number | NombreTamano;
  color?: string;
  alinear?: Alineacion;
  /** Ancho máximo; por defecto, lo que deja la zona segura desde x. */
  ancho?: number;
  /** Renglones permitidos (1 por defecto). */
  lineas?: number;
  interlineado?: number;
  /** Tamaño mínimo al achicar: 60 para lectura, 49 para rótulos. */
  minimo?: number;
  resaltar?: Resaltado;
  /** Opacidad y transform del bloque (useEntrar, useGolpe…); el origen es el centro del bloque. */
  estilo?: Estilo;
  /** Un estilo por palabra (para entrar palabra por palabra: useEntrarPalabras). */
  estiloPalabras?: Estilo[];
  /** Números de ancho fijo (contadores). */
  numeros?: boolean;
  /** "centro" (por defecto): y es el centro del bloque; "primero": y es el centro del primer renglón. */
  anclaY?: "centro" | "primero";
};

/** Texto en Segoe UI Bold, medido, dentro de la zona segura. */
export const Texto: React.FC<PropsTexto> = ({
  children,
  x,
  y,
  tam = "lectura",
  color = COLOR.hueso,
  alinear = "izq",
  ancho,
  lineas = 1,
  interlineado,
  minimo,
  resaltar,
  estilo,
  estiloPalabras,
  numeros = false,
  anclaY = "centro",
}) => {
  const texto = children;
  const pedido = px(tam);
  const min = minimo ?? (pedido >= TIPO.minimo.lectura ? TIPO.minimo.lectura : TIPO.minimo.rotulo);
  if (pedido < TIPO.minimo.rotulo && (minimo === undefined || minimo > pedido)) {
    throw new Error(`Texto «${texto}» a ${pedido} px: el mínimo es ${TIPO.minimo.rotulo} px (rótulos) y ${TIPO.minimo.lectura} px (lectura).`);
  }
  const maxAncho = Math.min(ancho ?? Infinity, anchoDisponible(x, alinear));
  if (maxAncho <= 0) throw new Error(`Texto «${texto}»: x = ${x} queda fuera de la zona segura (${ZONA.x0}-${ZONA.x1}).`);
  const d = disponerTexto(texto, pedido, maxAncho, lineas, Math.min(min, pedido), numeros);
  if (d.achicado) console.warn(`AVISO: «${texto}» se achicó de ${pedido} a ${d.tam} px para entrar en ${Math.round(maxAncho)} px.`);
  const lh = Math.round(d.tam * (interlineado ?? interlineadoDe(d.tam)));
  const anchoBloque = Math.max(...d.renglones.map((r) => r.ancho));
  const altoBloque = lh * d.renglones.length;
  const izquierda = alinear === "izq" ? x : alinear === "centro" ? x - anchoBloque / 2 : x - anchoBloque;
  const optica = TIPO.correccionOpticaEm * d.tam;
  const arriba = (anclaY === "primero" ? y - lh / 2 : y - altoBloque / 2) - optica;

  const factorAmbar = useAtenuarAmbar();
  const barrido = useContext(BarridoContext);
  const tramos = tramosResaltados(texto, resaltar, color);
  const opacidadDe = (c: string) => (c.toLowerCase() === COLOR.ambar.toLowerCase() ? factorAmbar : 1);

  // Palabras (para estiloPalabras): índice de palabra por posición de carácter.
  const indicePalabra: number[] = new Array(texto.length).fill(-1);
  [...texto.matchAll(/\S+/g)].forEach((m, i) => {
    for (let k = m.index ?? 0; k < (m.index ?? 0) + m[0].length; k++) indicePalabra[k] = i;
  });

  const pedazos = (r: Renglon, fantasma: boolean) => {
    // Cortes por color y por palabra dentro del renglón.
    const out: React.ReactNode[] = [];
    let i = r.inicio;
    const fin = r.inicio + r.texto.length;
    let clave = 0;
    while (i < fin) {
      const t = tramos.find((q) => q.desde <= i && i < q.hasta);
      const colorAqui = t ? t.color : color;
      const pal = indicePalabra[i];
      let j = i + 1;
      while (j < fin) {
        const tj = tramos.find((q) => q.desde <= j && j < q.hasta);
        if ((tj ? tj.color : color) !== colorAqui || indicePalabra[j] !== pal) break;
        j++;
      }
      const trozo = texto.slice(i, j);
      const estiloPalabra = estiloPalabras && pal >= 0 ? estiloPalabras[pal] : undefined;
      const st: React.CSSProperties = fantasma
        ? {}
        : {
            color: colorAqui,
            opacity: (colorAqui !== color ? opacidadDe(colorAqui) : 1) * (estiloPalabra?.opacity !== undefined ? Number(estiloPalabra.opacity) : 1),
          };
      if (estiloPalabra && pal >= 0) {
        out.push(
          <span key={clave++} style={{ ...st, display: "inline-block", transform: estiloPalabra.transform }}>
            {trozo}
          </span>,
        );
      } else {
        out.push(
          <span key={clave++} style={st}>
            {trozo}
          </span>,
        );
      }
      i = j;
    }
    return out;
  };

  const comun: React.CSSProperties = {
    fontFamily: TIPO.familia,
    fontWeight: TIPO.peso,
    fontSize: d.tam,
    lineHeight: `${lh}px`,
    whiteSpace: "pre",
    textAlign: alinear === "izq" ? "left" : alinear === "centro" ? "center" : "right",
    fontVariantNumeric: numeros ? "tabular-nums" : undefined,
  };

  // Franja del barrido, en coordenadas del bloque.
  const franja = MOV.barrido.ancho_px;
  const mostrarBarrido = barrido !== null && barrido > 0 && barrido < 1;
  const centroFranja = -franja + (barrido ?? 0) * (anchoBloque + 2 * franja);
  const luz = conAlfa(COLOR.hueso, OPACIDAD.barrido);

  const opacidadBloque = (color.toLowerCase() === COLOR.ambar.toLowerCase() ? factorAmbar : 1) * (estilo?.opacity !== undefined ? Number(estilo.opacity) : 1);

  return (
    <div
      style={{
        position: "absolute",
        left: izquierda,
        top: arriba,
        width: anchoBloque,
        height: altoBloque,
        color,
        transformOrigin: "50% 50%",
        ...estilo,
        opacity: opacidadBloque,
      }}
    >
      {d.renglones.map((r, i) => (
        <div key={i} style={{ ...comun, position: "absolute", left: 0, top: i * lh, width: anchoBloque, height: lh }}>
          {pedazos(r, false)}
        </div>
      ))}
      {mostrarBarrido &&
        d.renglones.map((r, i) => {
          const desplazamiento = alinear === "izq" ? 0 : alinear === "centro" ? (anchoBloque - r.ancho) / 2 : anchoBloque - r.ancho;
          const c = centroFranja - desplazamiento;
          return (
            <div
              key={`b${i}`}
              style={{
                ...comun,
                position: "absolute",
                left: desplazamiento,
                top: i * lh,
                width: r.ancho,
                height: lh,
                textAlign: "left",
                color: "transparent",
                backgroundImage: `linear-gradient(${90 + MOV.barrido.inclinacion_grados}deg, transparent ${c - franja / 2}px, ${luz} ${c - franja / 2}px, ${luz} ${c + franja / 2}px, transparent ${c + franja / 2}px)`,
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
              }}
            >
              {r.texto}
            </div>
          );
        })}
    </div>
  );
};

/** Título: Texto con tamaño de título (96 px) y que no baja de 72 px al achicarse. */
export const Titulo: React.FC<PropsTexto> = ({ tam = "grande", minimo = TIPO.escala.frase, ...resto }) => <Texto tam={tam} minimo={minimo} {...resto} />;
