// Prueba de infraestructura 2: lo que falta probar de los paquetes de Remotion.
// - @remotion/transitions: una escena pasa a la otra con un deslizamiento.
// - @remotion/motion-blur: el número entra con estela.
// - @remotion/shapes: el anillo de un cronómetro que se llena.
// - @remotion/noise: puntitos de fondo que flotan y se aquietan al final.
import { Trail } from "@remotion/motion-blur";
import { noise2D } from "@remotion/noise";
import { Circle } from "@remotion/shapes";
import { springTiming, TransitionSeries } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Lienzo } from "../Lienzo";
import { ACENTO, FUENTE, GRIS, HUESO } from "../tokens";

const Numero: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 24 });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: FUENTE,
          fontWeight: 700,
          fontSize: 300,
          lineHeight: 1,
          color: HUESO,
          transform: `translateX(${(1 - entra) * -600}px)`,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        60
      </div>
    </AbsoluteFill>
  );
};

const EscenaA: React.FC = () => (
  <Lienzo>
    <Trail layers={6} lagInFrames={0.6} trailOpacity={0.6}>
      <Numero />
    </Trail>
    <div
      style={{
        position: "absolute",
        bottom: 250,
        width: "100%",
        textAlign: "center",
        fontFamily: FUENTE,
        fontWeight: 700,
        fontSize: 48,
        color: GRIS,
      }}
    >
      segundos para contarlo
    </div>
  </Lienzo>
);

// 60 -> "1:00", 7 -> "0:07"
const reloj = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

const PUNTOS = Array.from({ length: 36 }, (_, i) => ({ x: 120 + ((i * 523) % 1680), y: 90 + ((i * 331) % 900) }));

const EscenaB: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const lleno = interpolate(frame, [5, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Los puntitos flotan y se quedan quietos en los últimos cuadros.
  const calma = interpolate(frame, [durationInFrames - 20, durationInFrames - 5], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const radio = 230;
  const largo = 2 * Math.PI * radio;
  return (
    <Lienzo>
      {PUNTOS.map((p, i) => {
        const dx = noise2D("x", i, frame / 60) * 18 * calma;
        const dy = noise2D("y", i, frame / 60) * 18 * calma;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x + dx,
              top: p.y + dy,
              width: 6,
              height: 6,
              borderRadius: 3,
              background: GRIS,
              opacity: 0.25,
            }}
          />
        );
      })}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ position: "relative", width: radio * 2 + 40, height: radio * 2 + 40 }}>
          <Circle
            radius={radio}
            fill="none"
            stroke={GRIS}
            strokeWidth={14}
            style={{ position: "absolute", left: 20, top: 20, opacity: 0.25 }}
          />
          <Circle
            radius={radio}
            fill="none"
            stroke={ACENTO}
            strokeWidth={14}
            strokeLinecap="round"
            strokeDasharray={largo}
            strokeDashoffset={largo * (1 - lleno)}
            style={{ position: "absolute", left: 20, top: 20, transform: "rotate(-90deg)" }}
          />
          <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
            <div style={{ fontFamily: FUENTE, fontWeight: 700, fontSize: 120, color: HUESO, fontVariantNumeric: "tabular-nums" }}>
              {reloj(Math.round(lleno * 60))}
            </div>
          </AbsoluteFill>
        </div>
      </AbsoluteFill>
    </Lienzo>
  );
};

export const PruebaDos: React.FC = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={45}>
      <EscenaA />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={springTiming({ config: { damping: 200 }, durationInFrames: 15 })} />
    <TransitionSeries.Sequence durationInFrames={60}>
      <EscenaB />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);
