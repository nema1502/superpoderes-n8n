// D12 Ideas para tu reto: cuatro formas de usar n8n en un proyecto del hackathon, con los mismos
// bloques de las demos.
//
// D12.1 (3,3 s propios: el fundido de 0,4 s desde D11 va aparte). Entra el título palabra por
// palabra, las cuatro tarjetas se dan vuelta de a una (arriba y después abajo), el ícono de cada
// una da un golpe chico y la receta entra bloque por bloque, como se arma un flujo.
//
// Cuadro final: el título en el amarillo de los títulos a 104 px en y 180, alineado con el contenido
// de las tarjetas (x 122). Cuatro tarjetas de 864 por 264 px (relleno pantalla, borde hueso al 40 %,
// radio 28) en dos filas: x 80 y 976, y 300 y 600. Adentro, a 42 px del borde, el ícono en hueso de
// 60 px y el nombre en hueso a 60 px en el primer renglón, y la receta en gris a 60 px debajo (en el
// deck iba a 49: a 60 se lee desde el fondo, y por eso las tarjetas son más anchas que las del deck).
// Ningún texto en ámbar: solo el ícono de la primera tarjeta.
// Pulido: las tarjetas crecen hasta y 864 (antes terminaban en 840 y abajo quedaba un tercio vacío) y
// el fondo de circuito de la charla va debajo de todo.
import React from "react";
import { FondoCircuito } from "./D01Portada";
import {
  anchoIcono,
  COLOR,
  Icono,
  OPACIDAD,
  pasosDe,
  Tarjeta,
  Texto,
  textos,
  unir,
  useEntrarPalabras,
  useGolpe,
  useVoltear,
  type NombreIcono,
} from "../comun";

export const pasos = pasosDe("D12");

const TITULO = { x: 122, y: 180 };
const ANCHO = 864;
const ALTO = 264;
const PAD = 42;
const COLUMNAS = [80, 976]; // borde izquierdo de cada columna
const FILAS = [300, 600]; // borde de arriba de cada fila
const ICONO = 60;
const COLUMNA_ICONO = 75; // el ancho del ícono más ancho (gears y comments, a 60 px)
const SEP_ICONO = 20;
const RENGLON_1 = PAD + 46; // centro del nombre, desde el borde de arriba
const RENGLON_2 = RENGLON_1 + 100; // centro de la receta

const ICONOS: NombreIcono[] = ["gears", "comments", "clock", "table"];

// Tiempos en s desde que empieza el paso. Dura 3,3 s y todo termina antes de los 3,0 s.
const T = { titulo: 0.1, tarjeta: 0.45, desfase: 0.15, icono: 0.3, receta: 0.35, recetaDesfase: 0.08 } as const;

const TarjetaIdea: React.FC<{ i: number; nombre: string; receta: string }> = ({ i, nombre, receta }) => {
  const x0 = COLUMNAS[i % 2];
  const y0 = FILAS[Math.floor(i / 2)];
  const inicio = T.tarjeta + i * T.desfase;
  const voltea = useVoltear(1, inicio);
  const golpe = useGolpe(1, inicio + T.icono, { chico: true });
  // Cada bloque de la receta sube un poco en su lugar (de costado se salía del borde de la tarjeta).
  const bloques = useEntrarPalabras(receta, 1, inicio + T.receta, { desfase: T.recetaDesfase, distancia: 24 });
  const xIcono = x0 + PAD + COLUMNA_ICONO / 2;
  const yNombre = y0 + RENGLON_1;
  const ancho = anchoIcono(ICONOS[i], ICONO);
  return (
    <Tarjeta x={x0 + ANCHO / 2} y={y0 + ALTO / 2} ancho={ANCHO} alto={ALTO} color={COLOR.hueso} opacidadBorde={OPACIDAD.borde_apoyo} relleno={COLOR.pantalla} estilo={voltea}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${xIcono}px ${yNombre}px`, ...unir(golpe) }}>
        <Icono nombre={ICONOS[i]} alto={ICONO} x={xIcono} y={yNombre} color={i === 0 ? COLOR.ambar : COLOR.hueso} />
      </div>
      <Texto x={x0 + PAD + Math.max(COLUMNA_ICONO, ancho) + SEP_ICONO} y={yNombre} tam="lectura">
        {nombre}
      </Texto>
      <Texto x={x0 + PAD} y={y0 + RENGLON_2} tam="lectura" color={COLOR.gris} estiloPalabras={bloques}>
        {receta}
      </Texto>
    </Tarjeta>
  );
};

export const D12IdeasParaTuReto: React.FC = () => {
  // ["¿Y en tu reto?", nombre 1, receta 1, … nombre 4, receta 4], tal cual
  const t = textos("D12", 1);
  const titulo = useEntrarPalabras(t[0], 1, T.titulo);
  return (
    <>
      <FondoCircuito />
      <Texto x={TITULO.x} y={TITULO.y} tam="grande" color={COLOR.titulo} estiloPalabras={titulo}>
        {t[0]}
      </Texto>
      {[0, 1, 2, 3].map((i) => (
        <TarjetaIdea key={i} i={i} nombre={t[1 + 2 * i]} receta={t[2 + 2 * i]} />
      ))}
    </>
  );
};
