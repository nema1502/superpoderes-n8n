// Piezas que Manim tiene que mostrar IDÉNTICAS a Remotion, como cuadros de 1920×1080:
// la marca de agua y los chips de piso 1-3. generar_assets.mjs las renderiza (con fondo
// transparente y sobre tinta) y recorta la zona de cada una a diseno/assets/.
// Van en la misma capa fija que en las diapositivas (sistema/Diapositiva.tsx → CapaFija):
// así salen idénticas al píxel a lo que dibuja cualquier diapositiva.
import React from "react";
import { ChipPiso } from "../comun/ChipPiso";
import { Lienzo } from "../comun/Lienzo";
import { MarcaAgua } from "../comun/Marca";
import { CapaFija } from "./Diapositiva";

export type PropsAsset = { pieza: "marca_agua" | "chip_piso_1" | "chip_piso_2" | "chip_piso_3"; fondo: boolean };

export const Asset: React.FC<PropsAsset> = ({ pieza, fondo }) => (
  <Lienzo fondo={fondo ? undefined : null}>
    <CapaFija>
      {pieza.startsWith("chip_piso_") && <ChipPiso piso={Number(pieza.slice(-1))} />}
      <MarcaAgua opacidad={pieza === "marca_agua" ? 1 : 0} />
    </CapaFija>
  </Lienzo>
);
