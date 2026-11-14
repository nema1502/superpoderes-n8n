import React from "react";
import { COLOR, conAlfa, GROSOR, OPACIDAD, TIPO, ZONA } from "../tokens";
import { anchoIcono, Icono, type NombreIcono } from "./Icono";
import { useAtenuarAmbar, type Estilo } from "./movimiento";
import { medirTexto } from "./Texto";
import { Cruz, grosorAsta, Palomita } from "./Trazos";

export type PropsPastilla = {
  /** El texto (de deck.json). */
  children: string;
  /** Centro de la pastilla. */
  x: number;
  y: number;
  /** Tamaño del texto (60 por defecto; 49 en las chicas). */
  tam?: number;
  /**
   * Color del borde: hueso al 40 % por defecto (un elemento de apoyo); ámbar solo si la pastilla
   * ES la respuesta del paso; rojo para lo incorrecto.
   */
  color?: string;
  /** Opacidad del borde: OPACIDAD.borde_apoyo (0,4) si el borde es hueso; 1 si es ámbar o rojo. */
  opacidadBorde?: number;
  grosor?: number;
  /** Relleno: tinta por defecto; con un color (rojo «humo») el texto va en tinta. */
  relleno?: string;
  colorTexto?: string;
  /** Ícono a la izquierda (56 px para texto de 60): user, shield-halved, hand… */
  icono?: NombreIcono;
  colorIcono?: string;
  /** Marca dibujada a la izquierda: palomita (ámbar) o cruz (roja), con su progreso. */
  marca?: { tipo: "palomita" | "cruz"; progreso?: number };
  /** Ancho fijo (si no, el del contenido). */
  ancho?: number;
  estilo?: Estilo;
};

/** Medidas de una pastilla (para alinear varias). */
export function medidasPastilla(texto: string, tam = TIPO.escala.lectura, conIcono = false, icono?: NombreIcono) {
  const alto = Math.round(tam * 1.5);
  const padX = Math.round(tam * 0.62);
  const altoIcono = Math.round(tam * 0.93);
  const sep = Math.round(tam * 0.36);
  const wIcono = conIcono ? (icono ? anchoIcono(icono, altoIcono) : altoIcono) + sep : 0;
  const wTexto = medirTexto(texto, tam);
  return { alto, padX, altoIcono, sep, wIcono, wTexto, ancho: Math.ceil(padX * 2 + wIcono + wTexto) };
}

/**
 * Pastilla: borde de 5 px (hueso al 40 % por defecto, como la Tarjeta de A4; ámbar si es la
 * respuesta del paso), relleno tinta, texto hueso a 60 px y, si hace falta, un ícono (del color
 * del borde, en hueso si el borde es de apoyo) o una marca a la izquierda. Es la de los tres
 * pisos (D02.4), «¿Hay para tipo C?», «15 palabras · ≈ 7 s», «Máximo 75 palabras», «humo».
 * Como mucho dos cosas en ámbar por cuadro (la palabra clave y la marca de lo correcto): una
 * pastilla de apoyo con borde ámbar le compite a la palabra clave.
 */
export const Pastilla: React.FC<PropsPastilla> = ({
  children,
  x,
  y,
  tam = TIPO.escala.lectura,
  color = COLOR.hueso,
  opacidadBorde,
  grosor = GROSOR.borde,
  relleno = COLOR.tinta,
  colorTexto,
  icono,
  colorIcono,
  marca,
  ancho,
  estilo,
}) => {
  const ambar = useAtenuarAmbar();
  const apoyo = color === COLOR.hueso;
  const alfaBorde = (opacidadBorde ?? (apoyo ? OPACIDAD.borde_apoyo : 1)) * (color === COLOR.ambar ? ambar : 1);
  const m = medidasPastilla(children, tam, !!(icono || marca), icono);
  const w = ancho ?? m.ancho;
  if (x - w / 2 < ZONA.x0 - 0.5 || x + w / 2 > ZONA.x1 + 0.5) {
    throw new Error(`Pastilla «${children}»: mide ${Math.round(w)} px y en x = ${x} se sale de la zona segura (${ZONA.x0}-${ZONA.x1}).`);
  }
  const lleno = relleno !== COLOR.tinta;
  const cTexto = colorTexto ?? (lleno ? COLOR.tinta : COLOR.hueso);
  const izq = x - w / 2;
  const contenidoX = izq + (w - (m.wIcono + m.wTexto)) / 2;
  const iconoX = contenidoX + (m.wIcono - m.sep) / 2;
  const optica = TIPO.correccionOpticaEm * tam;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${x}px ${y}px`, ...estilo }}>
      <div
        style={{
          position: "absolute",
          left: izq,
          top: y - m.alto / 2,
          width: w,
          height: m.alto,
          boxSizing: "border-box",
          borderRadius: m.alto / 2,
          border: `${grosor}px solid ${conAlfa(color, alfaBorde)}`,
          backgroundColor: relleno,
        }}
      />
      {icono && <Icono nombre={icono} alto={m.altoIcono} x={iconoX} y={y} color={colorIcono ?? color} />}
      {marca?.tipo === "palomita" && <Palomita x={iconoX} y={y} tam={m.altoIcono * 0.8} grosor={grosorAsta(tam)} progreso={marca.progreso ?? 1} />}
      {marca?.tipo === "cruz" && <Cruz x={iconoX} y={y} tam={m.altoIcono * 0.7} grosor={grosorAsta(tam)} progreso={marca.progreso ?? 1} />}
      <div
        style={{
          position: "absolute",
          left: contenidoX + m.wIcono,
          top: y - m.alto / 2 - optica,
          height: m.alto,
          lineHeight: `${m.alto}px`,
          fontFamily: TIPO.familia,
          fontWeight: TIPO.peso,
          fontSize: tam,
          whiteSpace: "pre",
          color: cTexto,
        }}
      >
        {children}
      </div>
    </div>
  );
};
