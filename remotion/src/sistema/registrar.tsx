// Registro de una diapositiva como composición de Remotion. Lo usan las entradas aisladas
// (src/entradas/<ID>.ts: una sola diapositiva) y el Studio (src/Root.tsx: todas).
// La composición se llama como la diapositiva («D06»), mide c[n] + 1 cuadros y lleva sus
// cortes en las props (render.mjs los lee para cortar los pasos).
import React from "react";
import { Composition } from "remotion";
import { diapoDeck } from "../deck";
import { cortesDe, pasosDe } from "../pasos";
import { ALTO, ANCHO, FPS } from "../tokens";
import { Diapositiva } from "./Diapositiva";
import { Provisional } from "./Provisional";
import type { DefDiapo, PropsComposicion } from "./tipos";

const componentes = new Map<string, React.FC<PropsComposicion>>();

function componenteDe(def: DefDiapo, clave: string): React.FC<PropsComposicion> {
  const ya = componentes.get(clave);
  if (ya) return ya;
  const Contenido = def.modulo ? def.modulo.componente : () => <Provisional id={def.id} />;
  const C: React.FC<PropsComposicion> = ({ pasos, anterior }) => (
    <Diapositiva id={def.id} pasos={pasos} anterior={anterior} opciones={def.modulo?.opciones}>
      <Contenido />
    </Diapositiva>
  );
  C.displayName = clave;
  componentes.set(clave, C);
  return C;
}

/** Duraciones de los pasos de una diapositiva registrada (las del módulo o las del deck). */
export function pasosDeDef(def: DefDiapo): number[] {
  const pasos = def.modulo ? def.modulo.pasos : pasosDe(def.id);
  const esperados = diapoDeck(def.id).pasos.length;
  if (pasos.length !== esperados) {
    throw new Error(`${def.id}: el archivo declara ${pasos.length} pasos y deck.json tiene ${esperados} (cada paso es una diapositiva del .pptx).`);
  }
  return pasos;
}

/** La composición de una diapositiva (`idComposicion`: otro nombre, para ejemplos y pruebas). */
export const ComposicionDiapo: React.FC<{ def: DefDiapo; idComposicion?: string }> = ({ def, idComposicion }) => {
  const pasos = pasosDeDef(def);
  const cortes = cortesDe(pasos);
  const id = idComposicion ?? def.id;
  return (
    <Composition
      id={id}
      component={componenteDe(def, id)}
      durationInFrames={cortes[cortes.length - 1] + 1}
      fps={FPS}
      width={ANCHO}
      height={ALTO}
      defaultProps={{ cortes, pasos, anterior: null } satisfies PropsComposicion}
    />
  );
};

/** La raíz de una entrada aislada: registerRoot(raizDe({ id, modulo })). */
export function raizDe(def: DefDiapo): React.FC {
  const Raiz: React.FC = () => <ComposicionDiapo def={def} />;
  return Raiz;
}
