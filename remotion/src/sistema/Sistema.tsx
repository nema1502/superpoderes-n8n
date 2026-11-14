// Composiciones del sistema visual (no son diapositivas): la hoja de estilo para revisar,
// las muestras y los PNG que usa Manim. Las renderizan remotion/hoja_estilo.mjs y
// remotion/generar_assets.mjs con la entrada src/entradas/_Sistema.ts.
import React from "react";
import { Still } from "remotion";
import { ALTO, ANCHO } from "../tokens";
import { Asset, type PropsAsset } from "./Assets";
import { HojaEstilo, MUESTRAS, PAGINAS } from "./HojaEstilo";

export const ComposicionesSistema: React.FC = () => (
  <>
    <Still id="HojaEstilo" component={HojaEstilo} width={ANCHO * 3} height={ALTO * 3} />
    {PAGINAS.map((P, i) => (
      <Still key={i} id={`HojaEstilo${i + 1}`} component={P} width={ANCHO} height={ALTO} />
    ))}
    {MUESTRAS.map((M, i) => (
      <Still key={`m${i}`} id={`Muestra${i + 1}`} component={M} width={ANCHO} height={ALTO} />
    ))}
    <Still id="Asset" component={Asset} width={ANCHO} height={ALTO} defaultProps={{ pieza: "marca_agua", fondo: false } satisfies PropsAsset} />
  </>
);
