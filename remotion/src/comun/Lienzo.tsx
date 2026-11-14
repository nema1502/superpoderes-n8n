import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { COLOR } from "../tokens";

/**
 * El lienzo de toda diapositiva: el fondo tinta y, encima, una capa propia y
 * transparente para el contenido. **Todo lo que se dibuja va adentro.**
 *
 * Esa capa hace dos cosas:
 * 1. Deja el texto limpio. Sin ella, el Chrome de Remotion en Windows dibuja el texto
 *    quieto con ClearType (antialias subpíxel): bordes azules y naranjas en cada letra,
 *    que en un video 4:2:0 y en un proyector se ven como halos. Con `willChange:
 *    transform` el texto va en escala de grises (docs/infra.md §6: 2872 píxeles con
 *    franja sin la capa, 0 con ella).
 * 2. Hace que cada cuadro se dibuje desde cero (`key` = número de cuadro). Chrome
 *    reutiliza en cada pestaña lo que ya rasterizó y solo vuelve a pintar lo que cambió:
 *    el mismo cuadro salía con bordes distintos (hasta 58 niveles) según qué cuadros había
 *    dibujado antes la pestaña, y el último cuadro de un paso no coincidía con el primero
 *    del siguiente. Con una capa nueva por cuadro, el cuadro N es siempre el mismo.
 *
 * `fondo = null` deja el fondo transparente (los PNG para Manim, diseno/assets/).
 */
export const Lienzo: React.FC<{ fondo?: string | null; children: React.ReactNode }> = ({ fondo = COLOR.tinta, children }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: fondo ?? "transparent" }}>
      <AbsoluteFill key={frame} style={{ willChange: "transform" }}>
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
