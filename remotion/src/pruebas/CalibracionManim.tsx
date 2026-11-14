// Calibración de Manim contra Remotion: los mismos textos (y un bloque de D07.3) dibujados con
// los componentes de verdad (<Texto>, borde como <Tarjeta>), en un cuadro de 1920×1080.
// La renderiza remotion/calibrar_manim.mjs (la llama manim/calibrar.py, que dibuja lo mismo en
// Manim y compara los dos cuadros). No es una diapositiva.
import React from "react";
import { Lienzo } from "../comun/Lienzo";
import { Texto, type Alineacion } from "../comun/Texto";
import { COLOR, conAlfa } from "../tokens";

export type MuestraCalibracion = {
  texto: string;
  /** px de fuente */
  tam: number;
  /** nombre de un color de los tokens (hueso, ambar, gris…) */
  color: string;
  x: number;
  y: number;
  alinear: Alineacion;
};

export type BloqueCalibracion = { cx: number; cy: number; ancho: number; alto: number; radio: number; grosor: number; relleno: number };

export type PropsCalibracion = { muestras: MuestraCalibracion[]; bloques: BloqueCalibracion[] };

const color = (nombre: string): string => (COLOR as Record<string, string>)[nombre] ?? nombre;

export const CalibracionManim: React.FC<PropsCalibracion> = ({ muestras, bloques }) => (
  <Lienzo>
    {bloques.map((b, i) => (
      <div
        key={`b${i}`}
        style={{
          position: "absolute",
          left: b.cx - b.ancho / 2,
          top: b.cy - b.alto / 2,
          width: b.ancho,
          height: b.alto,
          boxSizing: "border-box",
          borderRadius: b.radio,
          border: `${b.grosor}px solid ${COLOR.ambar}`,
          backgroundColor: conAlfa(COLOR.ambar, b.relleno),
        }}
      />
    ))}
    {muestras.map((m, i) => (
      <Texto key={i} x={m.x} y={m.y} tam={m.tam} color={color(m.color)} alinear={m.alinear}>
        {m.texto}
      </Texto>
    ))}
  </Lienzo>
);
