// Prueba de infraestructura 1: un título en Segoe UI Bold que entra con spring y
// un trazo SVG que se dibuja. Termina quieto: el último cuadro es el que queda
// en pantalla mientras el orador habla.
import { evolvePath } from "@remotion/paths";
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Lienzo } from "../Lienzo";
import { ACENTO, FUENTE, GRIS, HUESO } from "../tokens";

// Un subrayado con onda, debajo del título.
const TRAZO = "M 430 640 C 700 590, 900 700, 1160 640 S 1440 600, 1490 630";

export type PropsPrueba = { titulo: string };

export const Prueba: React.FC<PropsPrueba> = ({ titulo }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // El spring se estira a 40 cuadros: a partir de ahí el título está quieto.
  const entra = spring({ frame, fps, config: { damping: 14, stiffness: 120, mass: 0.8 }, durationInFrames: 40 });
  const dibujo = interpolate(frame, [18, 58], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const { strokeDasharray, strokeDashoffset } = evolvePath(dibujo, TRAZO);
  const rotulo = interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <Lienzo>
      <div
        style={{
          position: "absolute",
          top: 200,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: FUENTE,
          fontWeight: 700,
          fontSize: 28,
          letterSpacing: 6,
          color: GRIS,
          opacity: rotulo,
        }}
      >
        PRUEBA DE INFRAESTRUCTURA · REMOTION
      </div>
      <div
        style={{
          position: "absolute",
          top: 410,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: FUENTE,
          fontWeight: 700,
          fontSize: 120,
          lineHeight: 1,
          color: HUESO,
          whiteSpace: "nowrap",
          opacity: Math.min(1, entra * 1.5),
          transform: `translateY(${(1 - entra) * 70}px) scale(${0.94 + 0.06 * entra})`,
        }}
      >
        {titulo}
      </div>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        <path
          d={TRAZO}
          fill="none"
          stroke={ACENTO}
          strokeWidth={12}
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          top: 790,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: FUENTE,
          fontWeight: 700,
          fontSize: 44,
          color: HUESO,
          opacity: rotulo,
        }}
      >
        ¿Qué contarían en 60 segundos? ñ á é í ó ú ü
      </div>
    </Lienzo>
  );
};
