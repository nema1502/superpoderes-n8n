// Entrada propia de la calibración de Manim (remotion/calibrar_manim.mjs): solo esta composición.
import React from "react";
import { registerRoot, Still } from "remotion";
import { ALTO, ANCHO } from "../tokens";
import { CalibracionManim, type PropsCalibracion } from "./CalibracionManim";

const Raiz: React.FC = () => (
  <Still id="CalibracionManim" component={CalibracionManim} width={ANCHO} height={ALTO} defaultProps={{ muestras: [], bloques: [] } satisfies PropsCalibracion} />
);

registerRoot(Raiz);
