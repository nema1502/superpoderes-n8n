// La raíz del Studio (pnpm studio): TODAS las diapositivas de deck.json (las que no
// tienen archivo, provisionales), el sistema visual (hoja de estilo, muestras, PNG para
// Manim), la transición y las pruebas de infraestructura. Para renderizar, render.mjs
// usa las entradas aisladas de src/entradas/ (una diapositiva por bundle), no esta.
import React from "react";
import { Folder } from "remotion";
import { DIAPOS } from "./diapos";
import { Prueba } from "./pruebas/Prueba";
import { PruebaDos } from "./pruebas/PruebaDos";
import { ComposicionesSistema } from "./sistema/Sistema";
import { ComposicionesEjemplo } from "./sistema/Ejemplos";
import { ComposicionTransicion } from "./sistema/Transicion";
import { ComposicionDiapo } from "./sistema/registrar";
import { ALTO, ANCHO, FPS } from "./tokens";
import { Composition } from "remotion";

export const Root: React.FC = () => (
  <>
    <Folder name="diapositivas">
      {DIAPOS.map((def) => (
        <ComposicionDiapo key={def.id} def={def} />
      ))}
    </Folder>
    <Folder name="sistema">
      <ComposicionesSistema />
      <ComposicionTransicion />
      <ComposicionesEjemplo />
    </Folder>
    <Folder name="pruebas">
      <Composition id="Prueba" component={Prueba} defaultProps={{ titulo: "Dale superpoderes a tus automatizaciones" }} durationInFrames={90} fps={FPS} width={ANCHO} height={ALTO} />
      <Composition id="PruebaDos" component={PruebaDos} durationInFrames={90} fps={FPS} width={ANCHO} height={ALTO} />
    </Folder>
  </>
);
