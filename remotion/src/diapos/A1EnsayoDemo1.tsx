// A1 Demo 1 sin internet: el plan B de la demo 1 cuando no hay internet. Muestra lo que salió en el
// ensayo, con el mismo flujo del repositorio.
//
// A1.1 (2,3 s propios: el fundido de 0,4 s desde D09 va aparte). Entran la pastilla y el
// título (desfase 0,15 s), después el nombre de la demo, la tarjeta sube a su lugar mientras se
// acerca (escala de 0,95 a 1) y su contenido entra de a un renglón. Al final aparece la fuente.
//
// Cuadro final en dos columnas. A la izquierda, desde x 160 y hasta x 700: la pastilla (borde hueso
// al 40 %, 49 px) en y 170, el título en el amarillo de los títulos a 88 px en dos renglones desde
// y 300, el nombre de la demo en gris a 60 px en y 560 (hasta dos renglones) y la fuente en gris a
// 49 px al pie de la columna, en dos renglones que terminan a la altura del pie de la tarjeta. A la
// derecha, la tarjeta del ensayo con borde hueso al 40 %, de x 760 a 1840 y de y 120 a 900.
// La fuente iba en y 990: ahí pasa una pista del fondo de circuito de la charla, y en la columna
// queda alineada con la tarjeta.
//
// Ajuste (revisión): la tarjeta ya no lleva la captura de la página, que dejaba la letra entre 22 y
// 28 px. Lleva lo esencial de la salida real, escrito con el sistema de la charla, a 49 px o más:
// el nombre, el veredicto, el porqué y los otros nombres (workflows/muestras/flujo1-satelitazo.json,
// tal cual). La tarjeta se estira hasta y 900 y x 1840 para que entre a ese tamaño.
//
// Este archivo exporta la columna y la tarjeta (ColumnaEnsayo, TarjetaEnsayo, ENSAYO, useEnsayo),
// que usan también A2 y A3. Debajo de todo, el fondo de circuito de la charla (FondoCircuito).
import React from "react";
import {
  COLOR,
  conAlfa,
  GROSOR,
  medidasPastilla,
  OPACIDAD,
  Pastilla,
  pasosDe,
  RADIO,
  Texto,
  textos,
  TIPO,
  unir,
  useAparecer,
  useEntra,
  useEntrar,
  type Estilo,
} from "../comun";
import { FondoCircuito } from "./D01Portada";

export const pasos = pasosDe("A1");

// =======================================================================================
// La columna y la tarjeta del ensayo: las mismas en A1, A2 y A3
// =======================================================================================

export const ENSAYO = {
  columna: { x: 160, ancho: 540 },
  pastillaY: 170,
  tituloY: 300, // centro del primer renglón
  demoY: 560,
  /** Centro del primer renglón de la fuente (dos renglones de 64 px: el segundo termina en y 898). */
  fuenteY: 802,
  tarjeta: { x0: 760, y0: 120, x1: 1840, y1: 900 },
  /** Aire adentro de la tarjeta: el contenido va de x 812 a 1788 y de y 172 a 848. */
  pad: 52,
} as const;

/** Tiempos en s desde que empieza el paso. Dura 2,3 s y todo termina antes de los 2,0 s. */
const T = { pastilla: 0.1, titulo: 0.25, demo: 0.5, tarjeta: 0.3, tarjetaDura: 0.8, contenido: 0.55, desfase: 0.12, fuente: 1.2 } as const;

export function useEnsayo(renglones: number) {
  const sube = useEntra(1, T.tarjeta, T.tarjetaDura);
  return {
    pastilla: useEntrar(1, T.pastilla),
    titulo: useEntrar(1, T.titulo),
    demo: useEntrar(1, T.demo),
    fuente: useAparecer(1, T.fuente),
    // La tarjeta sube 40 px y se acerca de 0,95 a 1 con el resorte de entrar.
    tarjeta: { opacity: Math.min(1, 1.6 * sube), transform: `translateY(${(1 - sube) * 40}px) scale(${0.95 + 0.05 * sube})` } as Estilo,
    // Cada renglón del contenido entra con un desfase chico (el último a los 0,55 + 0,12 n s, más 0,5 de entrada).
    renglones: Array.from({ length: renglones }, (_, i) => useEntrar(1, T.contenido + i * T.desfase, { distancia: 24 })),
  };
}

export const ColumnaEnsayo: React.FC<{ textos: string[]; anim: ReturnType<typeof useEnsayo> }> = ({ textos: t, anim }) => {
  const [pastilla, titulo, demo, fuente] = t;
  const c = ENSAYO.columna;
  const anchoPastilla = medidasPastilla(pastilla, TIPO.escala.rotulo).ancho;
  return (
    <>
      <Pastilla x={c.x + anchoPastilla / 2} y={ENSAYO.pastillaY} tam={TIPO.escala.rotulo} estilo={anim.pastilla}>
        {pastilla}
      </Pastilla>
      <Texto x={c.x} y={ENSAYO.tituloY} anclaY="primero" tam="idea" color={COLOR.titulo} ancho={c.ancho} lineas={2} estilo={anim.titulo}>
        {titulo}
      </Texto>
      <Texto x={c.x} y={ENSAYO.demoY} anclaY="primero" tam="lectura" color={COLOR.gris} ancho={c.ancho} lineas={2} estilo={anim.demo}>
        {demo}
      </Texto>
      <Texto x={c.x} y={ENSAYO.fuenteY} anclaY="primero" tam="fuente" color={COLOR.gris} ancho={c.ancho} lineas={2} estilo={anim.fuente}>
        {fuente}
      </Texto>
    </>
  );
};

/** La tarjeta: relleno pantalla, borde hueso al 40 %, radio 28. Lo de adentro va en coordenadas del cuadro. */
export const TarjetaEnsayo: React.FC<{ anim: ReturnType<typeof useEnsayo>; children: React.ReactNode }> = ({ anim, children }) => {
  const t = ENSAYO.tarjeta;
  const cx = (t.x0 + t.x1) / 2;
  const cy = (t.y0 + t.y1) / 2;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${cx}px ${cy}px`, ...unir(anim.tarjeta) }}>
      <div
        style={{
          position: "absolute",
          left: t.x0,
          top: t.y0,
          width: t.x1 - t.x0,
          height: t.y1 - t.y0,
          boxSizing: "border-box",
          borderRadius: RADIO.tarjeta,
          border: `${GROSOR.borde}px solid ${conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo)}`,
          backgroundColor: COLOR.pantalla,
        }}
      />
      {children}
    </div>
  );
};

// =======================================================================================
// A1
// =======================================================================================

/** Lo esencial de la página del flujo 1 en el ensayo (workflows/muestras/flujo1-satelitazo.json). */
const SALIDA = {
  nombre: "Satelitazo",
  veredicto: "LIBRE",
  porque: "No apareció ningún resultado con el nombre \"Satelitazo\"",
  otrosRotulo: "Otros nombres",
  otros: "PasaSat / SatAviso / OrbitaYa",
} as const;

/** Centros de cada renglón dentro de la tarjeta (el porqué ocupa dos renglones desde y 520). */
const Y = { nombre: 240, veredicto: 382, porque: 520, otrosRotulo: 690, otros: 768 } as const;

export const A1EnsayoDemo1: React.FC = () => {
  const t = textos("A1", 1); // ["Demo 1 sin internet", "Así salió en el ensayo", "¿Ya existe tu nombre?", "Ensayo del 14 de noviembre de 2026"]
  const anim = useEnsayo(5);
  const x = ENSAYO.tarjeta.x0 + ENSAYO.pad;
  const ancho = ENSAYO.tarjeta.x1 - ENSAYO.tarjeta.x0 - 2 * ENSAYO.pad;
  const tamVeredicto = TIPO.escala.frase;
  const pVeredicto = medidasPastilla(SALIDA.veredicto, tamVeredicto, true);

  return (
    <>
      <FondoCircuito />
      <ColumnaEnsayo textos={t} anim={anim} />
      <TarjetaEnsayo anim={anim}>
        <Texto x={x} y={Y.nombre} tam="idea" estilo={anim.renglones[0]}>
          {SALIDA.nombre}
        </Texto>
        <Pastilla x={x + pVeredicto.ancho / 2} y={Y.veredicto} tam={tamVeredicto} color={COLOR.ambar} colorTexto={COLOR.ambar} marca={{ tipo: "palomita" }} estilo={anim.renglones[1]}>
          {SALIDA.veredicto}
        </Pastilla>
        <Texto x={x} y={Y.porque} anclaY="primero" tam="rotulo" ancho={ancho} lineas={2} estilo={anim.renglones[2]}>
          {SALIDA.porque}
        </Texto>
        <Texto x={x} y={Y.otrosRotulo} tam="rotulo" color={COLOR.gris} estilo={anim.renglones[3]}>
          {SALIDA.otrosRotulo}
        </Texto>
        <Texto x={x} y={Y.otros} tam="lectura" estilo={anim.renglones[4]}>
          {SALIDA.otros}
        </Texto>
      </TarjetaEnsayo>
    </>
  );
};
