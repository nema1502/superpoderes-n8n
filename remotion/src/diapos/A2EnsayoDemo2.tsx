// A2 Demo 2 sin internet: el plan B de la demo 2 cuando no hay internet. Muestra lo que salió en el
// ensayo, con el mismo flujo del repositorio.
//
// A2.1 (2,3 s propios: el fundido de 0,4 s desde D10 va aparte). La columna y la tarjeta son las de
// A1 (ColumnaEnsayo y TarjetaEnsayo). Adentro de la tarjeta, las cuatro preguntas del ensayo, cada
// una con la herramienta que eligió el agente a la izquierda, en ámbar: Mapas, Noticias, Videos y
// Memoria (la cuarta la contestó sin buscar). Es lo que se quiere mostrar: nadie le dijo qué usar.
//
// Ajuste (revisión): sin la captura de 22 px y sin las respuestas. La respuesta a la pregunta de la
// NASA repetía como de hoy titulares viejos de Google News: no se muestra. Quedan la herramienta y la
// pregunta, tal cual (workflows/muestras/flujo2-conversacion.json), a 49 px. La herramienta se llama
// Videos, como en el registro de n8n.
import React from "react";
import { anchoIcono, COLOR, disponerTexto, Icono, interlineadoDe, pasosDe, Texto, textos, TIPO, type NombreIcono } from "../comun";
import { ColumnaEnsayo, ENSAYO, TarjetaEnsayo, useEnsayo } from "./A1EnsayoDemo1";
import { FondoCircuito } from "./D01Portada";

export const pasos = pasosDe("A2");

/** Las cuatro preguntas del ensayo, en orden, con la herramienta que usó el agente para cada una. */
const FILAS: { herramienta: string; icono: NombreIcono; pregunta: string }[] = [
  { herramienta: "Mapas", icono: "map-location-dot", pregunta: "Somos cuatro y necesitamos un café abierto cerca del centro. ¿Dónde vamos?" },
  { herramienta: "Noticias", icono: "globe", pregunta: "¿Qué pasó hoy con la NASA? Contámelo en dos frases." },
  { herramienta: "Videos", icono: "film", pregunta: "Pasame un video corto en español para aprender n8n." },
  { herramienta: "Memoria", icono: "memory", pregunta: "De esos cafés, ¿cuál tiene mejor puntaje?" },
];

/** La columna de la herramienta: ícono de 46 px, 16 px de aire y el nombre. La pregunta empieza 300 px más a la derecha. */
const COL = { icono: 46, aireIcono: 16, pregunta: 300, aireFilas: 30, maxRenglones: 3 } as const;

export const A2EnsayoDemo2: React.FC = () => {
  const t = textos("A2", 1); // ["Demo 2 sin internet", "Así salió en el ensayo", "El compañero de la madrugada", "Ensayo del 14 de noviembre de 2026"]
  const anim = useEnsayo(FILAS.length);
  const tarjeta = ENSAYO.tarjeta;
  const x = tarjeta.x0 + ENSAYO.pad;
  const xPregunta = x + COL.pregunta;
  const ancho = tarjeta.x1 - ENSAYO.pad - xPregunta;
  const tam = TIPO.escala.rotulo;
  const lh = Math.round(tam * interlineadoDe(tam));

  // Cada fila mide lo que miden sus renglones. El bloque va centrado en el alto de la tarjeta.
  const renglones = FILAS.map((f) => disponerTexto(f.pregunta, tam, ancho, COL.maxRenglones, tam).renglones.length);
  const altos = renglones.map((n) => n * lh);
  const total = altos.reduce((a, b) => a + b, 0) + COL.aireFilas * (FILAS.length - 1);
  const arriba = tarjeta.y0 + ENSAYO.pad;
  const disponible = tarjeta.y1 - tarjeta.y0 - 2 * ENSAYO.pad;
  if (total > disponible) throw new Error(`A2.1: las cuatro filas miden ${total} px y en la tarjeta hay ${disponible}.`);
  const y0 = arriba + (disponible - total) / 2;
  const tops = altos.map((_, i) => y0 + altos.slice(0, i).reduce((a, b) => a + b, 0) + i * COL.aireFilas);

  return (
    <>
      <FondoCircuito />
      <ColumnaEnsayo textos={t} anim={anim} />
      <TarjetaEnsayo anim={anim}>
        {FILAS.map((f, i) => {
          const y = tops[i] + lh / 2;
          return (
            <div key={f.herramienta} style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...anim.renglones[i] }}>
              <Icono nombre={f.icono} alto={COL.icono} x={x} y={y} ancla="izq" color={COLOR.ambar} />
              <Texto x={x + anchoIcono(f.icono, COL.icono) + COL.aireIcono} y={y} tam={tam} color={COLOR.ambar}>
                {f.herramienta}
              </Texto>
              <Texto x={xPregunta} y={y} anclaY="primero" tam={tam} ancho={ancho} lineas={COL.maxRenglones}>
                {f.pregunta}
              </Texto>
            </div>
          );
        })}
      </TarjetaEnsayo>
    </>
  );
};
