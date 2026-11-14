// Lo correcto y lo incorrecto llevan SIEMPRE forma, además de color: palomita (ámbar),
// cruz o tachado (rojo). Todo se dibuja como trazo (evolvePath = Create de Manim).
//
// La marca toma el grosor del asta del texto que acompaña (grosorAsta): una palomita de 40 px con
// trazo de 6 px al lado de un rótulo Bold de 72 px (asta de 11 px) se veía como un tilde tímido y
// lo «hecho» se leía casi solo por el color.
import { evolvePath } from "@remotion/paths";
import React from "react";
import { COLOR, GROSOR, TIPO } from "../tokens";
import { useAtenuarAmbar } from "./movimiento";
import { useIdSvg } from "./Visor7";

/** Grosor del asta de Segoe UI Bold a `tam` px (0,15 em: 10,8 px a 72): el trazo de una marca junto a ese texto. */
export const grosorAsta = (tam: number): number => TIPO.astaEm * tam;

type PropsMarca = {
  /** Centro de la marca. */
  x: number;
  y: number;
  /** Lado del cuadrado que ocupa, en px. */
  tam: number;
  /** 0 → 1: se dibuja. */
  progreso?: number;
  color?: string;
  /** Grosor del trazo. Junto a un texto, grosorAsta(tamaño del texto); si no, 0,18 × tam. */
  grosor?: number;
  opacidad?: number;
};

const svgAbs = (x: number, y: number, tam: number, extra = 0): React.CSSProperties => ({
  position: "absolute",
  left: x - tam / 2 - extra,
  top: y - tam / 2 - extra,
  overflow: "visible",
});

/** Palomita dibujada (ámbar): lo correcto, lo hecho. */
export const Palomita: React.FC<PropsMarca> = ({ x, y, tam, progreso = 1, color = COLOR.ambar, grosor, opacidad = 1 }) => {
  const g = grosor ?? Math.max(4, tam * GROSOR.palomita_por_px);
  const d = `M ${0.06 * tam} ${0.55 * tam} L ${0.38 * tam} ${0.86 * tam} L ${0.95 * tam} ${0.16 * tam}`;
  const ev = evolvePath(progreso, d);
  const ambar = useAtenuarAmbar();
  if (progreso <= 0) return null;
  return (
    <svg width={tam} height={tam} style={{ ...svgAbs(x, y, tam), opacity: opacidad * (color === COLOR.ambar ? ambar : 1) }}>
      <path d={d} fill="none" stroke={color} strokeWidth={g} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
    </svg>
  );
};

/** Cruz dibujada (roja): lo incorrecto. Primero un brazo y después el otro. */
export const Cruz: React.FC<PropsMarca> = ({ x, y, tam, progreso = 1, color = COLOR.rojo, grosor, opacidad = 1 }) => {
  const g = grosor ?? Math.max(4, tam * GROSOR.palomita_por_px);
  const m = 0.14 * tam;
  const a = `M ${m} ${m} L ${tam - m} ${tam - m}`;
  const b = `M ${tam - m} ${m} L ${m} ${tam - m}`;
  const e1 = evolvePath(Math.min(1, progreso * 2), a);
  const e2 = evolvePath(Math.max(0, progreso * 2 - 1), b);
  if (progreso <= 0) return null;
  return (
    <svg width={tam} height={tam} style={{ ...svgAbs(x, y, tam), opacity: opacidad }}>
      <path d={a} fill="none" stroke={color} strokeWidth={g} strokeLinecap="round" strokeDasharray={e1.strokeDasharray} strokeDashoffset={e1.strokeDashoffset} />
      {progreso > 0.5 && <path d={b} fill="none" stroke={color} strokeWidth={g} strokeLinecap="round" strokeDasharray={e2.strokeDasharray} strokeDashoffset={e2.strokeDashoffset} />}
    </svg>
  );
};

/**
 * Insignia: la palomita o la cruz dentro de un círculo con relleno tinta y borde del
 * mismo color, para la esquina de un globo o de una tarjeta (D06.3, D20.2).
 */
export const Insignia: React.FC<{ tipo: "palomita" | "cruz"; x: number; y: number; diametro?: number; progreso?: number; opacidad?: number }> = ({
  tipo,
  x,
  y,
  diametro = 84,
  progreso = 1,
  opacidad = 1,
}) => {
  const color = tipo === "palomita" ? COLOR.ambar : COLOR.rojo;
  const ambar = useAtenuarAmbar();
  if (progreso <= 0) return null;
  const aro = Math.min(1, progreso * 3);
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: x - diametro / 2,
          top: y - diametro / 2,
          width: diametro,
          height: diametro,
          boxSizing: "border-box",
          borderRadius: diametro / 2,
          border: `${GROSOR.borde}px solid ${color}`,
          backgroundColor: COLOR.tinta,
          opacity: aro * opacidad * (tipo === "palomita" ? ambar : 1),
          transform: `scale(${0.85 + 0.15 * aro})`,
        }}
      />
      {tipo === "palomita" ? (
        <Palomita x={x} y={y + diametro * 0.02} tam={diametro * 0.52} progreso={Math.max(0, progreso * 1.5 - 0.5)} opacidad={opacidad} grosor={Math.max(5, diametro * 0.085)} />
      ) : (
        <Cruz x={x} y={y} tam={diametro * 0.5} progreso={Math.max(0, progreso * 1.5 - 0.5)} opacidad={opacidad} grosor={Math.max(5, diametro * 0.085)} />
      )}
    </>
  );
};

type PropsLinea = {
  /** Desde x0 hasta x1, a la altura y (ver lineaTachado / lineaSubrayado). */
  x0: number;
  x1: number;
  y: number;
  progreso?: number;
  color?: string;
  grosor?: number;
  opacidad?: number;
  /** Trazos (px) para una línea a trazos: [largo, hueco]. Se revela de izquierda a derecha. */
  trazos?: [number, number];
  /** Filete de tinta a cada lado de la línea, en px (el tachado: corta las letras). */
  filete?: number;
};

const Linea: React.FC<PropsLinea & { cap: "round" | "butt" }> = ({ x0, x1, y, progreso = 1, color = COLOR.rojo, grosor = GROSOR.tachado, opacidad = 1, trazos, filete = 0, cap }) => {
  const id = useIdSvg("linea");
  if (progreso <= 0) return null;
  const d = `M ${x0} ${y} L ${x1} ${y}`;
  const ev = evolvePath(Math.min(1, progreso), d);
  const pad = grosor;
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: opacidad }}>
      {trazos ? (
        <g>
          <defs>
            <clipPath id={id}>
              <rect x={x0 - pad} y={y - pad} width={(x1 - x0) * Math.min(1, progreso) + pad} height={2 * pad} />
            </clipPath>
          </defs>
          <path d={d} stroke={color} strokeWidth={grosor} strokeDasharray={`${trazos[0]} ${trazos[1]}`} strokeLinecap="butt" clipPath={`url(#${id})`} />
        </g>
      ) : (
        <>
          {filete > 0 && (
            <path d={d} stroke={COLOR.tinta} strokeWidth={grosor + 2 * filete} strokeLinecap={cap} strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
          )}
          <path d={d} stroke={color} strokeWidth={grosor} strokeLinecap={cap} strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
        </>
      )}
    </svg>
  );
};

/**
 * Tachado (rojo, 7 px: el trazo fuerte) de izquierda a derecha, con un filete de tinta de 3 px a
 * cada lado que corta las letras: el humo, la promesa, lo vago. El rojo tiene la misma luz que el
 * gris (1,0:1): sin el filete, sobre texto gris se separaba solo por el tono. El texto tachado va en
 * hueso al 55 % (OPACIDAD.tachado_texto), no en gris.
 */
export const Tachado: React.FC<PropsLinea> = (p) => <Linea cap="round" color={COLOR.rojo} grosor={GROSOR.tachado} filete={GROSOR.tachado_filete} {...p} />;

/** Subrayado (ámbar, 5 px: el trazo normal): X, Y y Z resueltas, la prueba, el pedido. */
export const Subrayado: React.FC<PropsLinea> = (p) => {
  const ambar = useAtenuarAmbar();
  const color = p.color ?? COLOR.ambar;
  return <Linea cap="round" grosor={GROSOR.subrayado} {...p} color={color} opacidad={(p.opacidad ?? 1) * (color === COLOR.ambar ? ambar : 1)} />;
};

/** y del tachado para un <Texto> anclado en y con tamaño tam (cruza las minúsculas por el medio). */
export const lineaTachado = (y: number, tam: number): number => y + 0.06 * tam;
/** y del subrayado para un <Texto> anclado en y con tamaño tam (un poco debajo de la línea de base). */
export const lineaSubrayado = (y: number, tam: number): number => y + (TIPO.mayusculaEm / 2 + 0.13) * tam;
