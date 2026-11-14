import React from "react";
import { RETICULA, VISOR } from "../tokens";
import { VisorCaja } from "./Visor7";

const CHIP = RETICULA.chip_piso;

export type PropsChipPiso = {
  /** El piso: 1, 2 o 3 (o «Pb»). */
  piso: number | string;
  /** Cambio de piso: el dígito viejo sale hacia arriba y el nuevo entra desde abajo (0,35 s). */
  anterior?: number | string;
  cambio?: number;
  /** El ▲ brilla una vez al cambiar de piso (0 → 1 → 0). */
  brillo?: number;
  opacidad?: number;
  /** Escala alrededor del centro (aparece con 0,9 → 1). */
  escala?: number;
  /** Otra posición (centro) y otro ancho: en D15.3 el chip va chico al lado de cada bloque. */
  cx?: number;
  cy?: number;
  ancho?: number;
};

/**
 * Chip de piso: caja de vidrio de 132×84 con borde de acero de 2 px, ▲ ámbar de 24 px y
 * el dígito en 7 segmentos de 56 px, arriba a la derecha (x 1721-1853, y 38-122) en
 * D09-D13. Lo pone solo el sistema (sistema/Diapositiva.tsx) según el piso de deck.json;
 * Manim pega el PNG de diseno/assets/ en el mismo píxel.
 */
export const ChipPiso: React.FC<PropsChipPiso> = ({ piso, anterior, cambio = 1, brillo = 0, opacidad = 1, escala = 1, cx, cy, ancho }) => {
  const k = (ancho ?? CHIP.ancho) / CHIP.ancho;
  return (
    <VisorCaja
      cx={cx ?? CHIP.x + CHIP.ancho / 2}
      cy={cy ?? CHIP.y + CHIP.alto / 2}
      ancho={CHIP.ancho * k}
      alto={CHIP.alto * k}
      digito={CHIP.digito * k}
      triangulo={{ tam: CHIP.triangulo * k, encendido: 1, brillo }}
      texto={String(piso)}
      anterior={anterior !== undefined ? String(anterior) : undefined}
      cambio={cambio}
      opacidad={opacidad}
      escala={escala}
    />
  );
};

/** Medidas del chip (para quien necesite alinear algo con él). */
export const MEDIDAS_CHIP = { ...CHIP, visor: VISOR };
