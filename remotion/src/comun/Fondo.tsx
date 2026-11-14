import React from "react";
import { AbsoluteFill } from "remotion";
import { COLOR } from "../tokens";

/**
 * Fondo tinta plano, a pantalla completa. Es el fondo de toda la charla (y de Manim):
 * sin degradés ni viñetas, para que los bordes midan siempre #070A0F y no haya
 * bandas en el video. <Lienzo> ya lo pone; sirve para tapar algo con fondo dentro
 * de una capa (por ejemplo, detrás de una escena que entra encima de otra).
 */
export const Fondo: React.FC<{ opacidad?: number; color?: string }> = ({ opacidad = 1, color = COLOR.tinta }) => (
  <AbsoluteFill style={{ backgroundColor: color, opacity: opacidad }} />
);
