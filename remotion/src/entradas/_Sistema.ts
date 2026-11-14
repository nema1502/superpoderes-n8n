// Entrada del sistema visual (no es una diapositiva): hoja de estilo, muestras, PNG para
// Manim y la transición. La usan hoja_estilo.mjs, generar_assets.mjs y transicion.mjs.
// (Escrita a mano: generar_registro.mjs no la toca porque no empieza con su cabecera.)
import React from "react";
import { registerRoot } from "remotion";
import { ComposicionesSistema } from "../sistema/Sistema";
import { ComposicionesEjemplo } from "../sistema/Ejemplos";
import { ComposicionTransicion } from "../sistema/Transicion";

const Raiz: React.FC = () => React.createElement(React.Fragment, null, React.createElement(ComposicionesSistema), React.createElement(ComposicionTransicion), React.createElement(ComposicionesEjemplo));

registerRoot(Raiz);
