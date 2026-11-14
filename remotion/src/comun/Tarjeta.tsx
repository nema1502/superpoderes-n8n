import React from "react";
import { COLOR, conAlfa, GROSOR, RADIO } from "../tokens";
import { useAtenuarAmbar, type Estilo } from "./movimiento";

export type PropsTarjeta = {
  /** Centro de la tarjeta. */
  x: number;
  y: number;
  ancho: number;
  alto: number;
  /** Borde: ámbar (D12.2) o hueso al 50 % (D17.1). */
  color?: string;
  opacidadBorde?: number;
  grosor?: number;
  radio?: number;
  /** Relleno: tinta, o pantalla (#0E141D) para destacar sin borde fuerte (A4). */
  relleno?: string;
  /** Opacidad y transform (useVoltear, useEntrar); el origen es el centro de la tarjeta. */
  estilo?: Estilo;
  /** Lo de adentro, en coordenadas del cuadro (íconos y rótulos). */
  children?: React.ReactNode;
};

/**
 * Tarjeta: rectángulo redondeado (radio 28) con borde de 5 px. Va con Voltear (rotateY
 * de 90° a 0°, perspectiva de 1200 px): las tres de la prueba, las dos de la votación.
 */
export const Tarjeta: React.FC<PropsTarjeta> = ({
  x,
  y,
  ancho,
  alto,
  color = COLOR.ambar,
  opacidadBorde = 1,
  grosor = GROSOR.borde,
  radio = RADIO.tarjeta,
  relleno = COLOR.tinta,
  estilo,
  children,
}) => {
  const ambar = useAtenuarAmbar();
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${x}px ${y}px`, ...estilo }}>
      <div
        style={{
          position: "absolute",
          left: x - ancho / 2,
          top: y - alto / 2,
          width: ancho,
          height: alto,
          boxSizing: "border-box",
          borderRadius: radio,
          border: `${grosor}px solid ${conAlfa(color, opacidadBorde * (color === COLOR.ambar ? ambar : 1))}`,
          backgroundColor: relleno,
        }}
      />
      {children}
    </div>
  );
};
