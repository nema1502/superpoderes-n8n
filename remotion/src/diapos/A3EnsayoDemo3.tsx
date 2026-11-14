// A3 Demo 3 sin internet: el plan B de la demo 3 cuando no hay internet. Muestra lo que salió en el
// ensayo, con el mismo flujo del repositorio.
//
// A3.1 (2,3 s propios: el fundido de 0,4 s desde D11 va aparte). La columna y la tarjeta son las de
// A1 (ColumnaEnsayo y TarjetaEnsayo). Adentro de la tarjeta, el reto de ejemplo en una frase y las
// tres ideas que devolvió el scout, cada una en un recuadro azul con su número en ámbar, como en la
// página del flujo.
//
// Ajuste (revisión): sin la captura de 22 px. Lo esencial de la página, tal cual
// (workflows/muestras/flujo3-incendios.json y su página): la frase del reto, el título de la sección
// de ideas y el nombre de las tres. Lo que ya existe, qué leer y qué ver quedan para la página en vivo.
import React from "react";
import { COLOR, disponerTexto, GROSOR, interlineadoDe, pasosDe, Texto, textos, TIPO } from "../comun";
import { ColumnaEnsayo, ENSAYO, TarjetaEnsayo, useEnsayo } from "./A1EnsayoDemo1";
import { FondoCircuito } from "./D01Portada";

export const pasos = pasosDe("A3");

const SALIDA = {
  reto: "Avisar a comunidades rurales de Santa Cruz sobre riesgo de incendio usando datos satelitales de la NASA.",
  seccion: "Tres ideas para el fin de semana",
  // La tercera no entra en un renglón: se corta a mano en dos parejos (si no, riesgo quedaba solo abajo).
  ideas: ["Alerta SMS con FIRMS y geocercas", "Mapa web de riesgo por proximidad", "Dashboard de tendencia\ny score de riesgo"],
} as const;

/** El recuadro de cada idea: borde azul de 3 px, radio 20, 14 px de aire arriba y abajo y 24 a los lados. */
const IDEA = { padY: 14, padX: 24, radio: 20, aire: 14, maxRenglones: 2 } as const;
const AIRE = { reto: 30, seccion: 16 } as const;

export const A3EnsayoDemo3: React.FC = () => {
  const t = textos("A3", 1); // ["Demo 3 sin internet", "Así salió en el ensayo", "El scout del reto", "Ensayo del 14 de noviembre de 2026"]
  const anim = useEnsayo(2 + SALIDA.ideas.length);
  const tarjeta = ENSAYO.tarjeta;
  const x = tarjeta.x0 + ENSAYO.pad;
  const ancho = tarjeta.x1 - tarjeta.x0 - 2 * ENSAYO.pad;
  const tam = TIPO.escala.rotulo;
  const lh = Math.round(tam * interlineadoDe(tam));

  // Alturas: el reto (hasta 3 renglones), la sección (1) y cada idea (1 o 2 renglones dentro de su recuadro).
  const textoIdea = (i: number) => `${i + 1}. ${SALIDA.ideas[i]}`;
  const anchoIdea = ancho - 2 * IDEA.padX;
  const nReto = disponerTexto(SALIDA.reto, tam, ancho, 3, tam).renglones.length;
  const nIdeas = SALIDA.ideas.map((_, i) => disponerTexto(textoIdea(i), tam, anchoIdea, IDEA.maxRenglones, tam).renglones.length);
  const altoReto = nReto * lh;
  const altosIdea = nIdeas.map((n) => n * lh + 2 * IDEA.padY);
  const total = altoReto + AIRE.reto + lh + AIRE.seccion + altosIdea.reduce((a, b) => a + b, 0) + IDEA.aire * (nIdeas.length - 1);
  const arriba = tarjeta.y0 + ENSAYO.pad;
  const disponible = tarjeta.y1 - tarjeta.y0 - 2 * ENSAYO.pad;
  if (total > disponible) throw new Error(`A3.1: el contenido mide ${total} px y en la tarjeta hay ${disponible}.`);
  const y0 = arriba + (disponible - total) / 2;
  const ySeccion = y0 + altoReto + AIRE.reto + lh / 2;
  const topIdeas = altosIdea.map((_, i) => y0 + altoReto + AIRE.reto + lh + AIRE.seccion + altosIdea.slice(0, i).reduce((a, b) => a + b, 0) + i * IDEA.aire);

  return (
    <>
      <FondoCircuito />
      <ColumnaEnsayo textos={t} anim={anim} />
      <TarjetaEnsayo anim={anim}>
        <Texto x={x} y={y0 + lh / 2} anclaY="primero" tam={tam} ancho={ancho} lineas={3} estilo={anim.renglones[0]}>
          {SALIDA.reto}
        </Texto>
        <Texto x={x} y={ySeccion} tam={tam} color={COLOR.gris} estilo={anim.renglones[1]}>
          {SALIDA.seccion}
        </Texto>
        {SALIDA.ideas.map((_, i) => (
          <div key={i} style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...anim.renglones[2 + i] }}>
            <div
              style={{
                position: "absolute",
                left: x,
                top: topIdeas[i],
                width: ancho,
                height: altosIdea[i],
                boxSizing: "border-box",
                borderRadius: IDEA.radio,
                border: `${GROSOR.borde_fino}px solid ${COLOR.azul}`,
                background: COLOR.noche,
              }}
            />
            <Texto x={x + IDEA.padX} y={topIdeas[i] + IDEA.padY + lh / 2} anclaY="primero" tam={tam} ancho={anchoIdea} lineas={IDEA.maxRenglones} resaltar={`${i + 1}.`}>
              {textoIdea(i)}
            </Texto>
          </div>
        ))}
      </TarjetaEnsayo>
    </>
  );
};
