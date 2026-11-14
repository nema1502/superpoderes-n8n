// D04 Anotate al sorteo (guion D04.1). La sala se anota desde el celular en el formulario de n8n
// mientras empieza la charla, y la llama de Tinkazo la invita.
//
// Entra con un fundido de 0,4 s desde D03 (es otro video): el cuadro 0 es tinta con la marca de agua.
// Un solo paso de 3,5 s propios (3,9 en el deck, con el fundido): todo quieto desde los 3,2 s.
//
// Cuadro final (deck D04.1):
//   Desde x 140: Al final hay sorteo. en titulo (amarillo lima) a 104 px en y 200, Escaneá y anotate en
//   hueso a 72 px en y 330, Palabra de la charla: en hueso a 60 px en y 470, llama en ámbar a 104 px
//   en y 580 y Participar es gratis. en gris a 60 px en y 720.
//   A la derecha, la tarjeta hueso de x 1200 a 1800 y de y 120 a 720 con el QR en tinta: los módulos en
//   píxeles enteros, centrados, con el margen claro de 4 módulos o más (las reglas de QR de Tinkazo:
//   oscuro sobre claro, nunca invertido, sin nada encima).
//   Debajo, la dirección escrita en hueso a 49 px: centrada en x 1500 en y 790 si entra en un renglón
//   (706 px). Una dirección de n8n Cloud no entra: va en dos renglones, cortada antes de una barra, en
//   y 800 y 861, centrada en x 1500 o, si así no entra, alineada a la derecha con la tarjeta (x 1800).
//   Siempre por arriba de y 900.
//   La llama de Tinkazo de 300 px de alto (la protagonista del sorteo)
//   parada junto a la esquina de abajo a la izquierda de la tarjeta (su caja de x 896 a 1150, las
//   patas en y 760), mirando al QR. Si la dirección va alineada
//   a la derecha y pasa por debajo de ese lugar, la llama se para 30 px a la izquierda de la dirección,
//   para no quedar parada sobre el texto.
//
// El QR sale de enlaces.formulario_sorteo del deck, pasado a matriz por diseno/medios/D04/
// generar_qr.mjs en diseno/medios/D04/qr.json. Si qr.json no es de la dirección del deck, el render
// falla y dice qué correr.
//
// Sin formulario (mientras el deck diga FORMULARIO_PENDIENTE), la diapositiva se puede presentar igual:
// anuncia el sorteo sin QR. No hay tarjeta, ni dirección, ni Escaneá y anotate (el deck trae cuatro
// textos y no seis). Al final hay sorteo. en y 240, Palabra de la charla: en 440, llama en 550 y
// Participar es gratis. en 700, desde x 140, y la llama grande (560 px) a la derecha, centrada en
// x 1440 con las patas en y 820. Entra caminando desde el borde derecho del cuadro con los mismos
// tiempos y se da vuelta como en la marca. Un QR de prueba (generar_qr.mjs --prueba) solo se ve si el
// deck tiene una dirección.
//
// La llama sale de atrás de la tarjeta: entra por el borde izquierdo de la tarjeta, por abajo,
// caminando hacia la izquierda (cuatro pasos en 1,2 s, mirando hacia donde camina), se para y se da
// vuelta hacia el QR. Al final mira a la derecha, como en la marca, girada 3 grados.
//
// Debajo de todo, el fondo de circuito de la charla (FondoCircuito de D01).
//
// Tiempos (s desde el comienzo del paso):
//   0,05-0,55 el título sube            0,25-0,75 la tarjeta se acerca (escala 0,9 a 1)
//   0,70-1,00 aparece el QR (o el rayado)
//   0,35-1,30 las líneas de la izquierda suben de a una (desfase 0,15 s); llama con un golpe chico
//   1,00-1,40 aparece la dirección
//   1,35-2,55 la llama camina; 2,60-2,85 se da vuelta
import React from "react";
import deckJson from "../../../contenido/deck.json";
import qrJson from "../../../diseno/medios/D04/qr.json";
import {
  COLOR,
  CURVA,
  medirTexto,
  MOV,
  pasosDe,
  RADIO,
  RESORTE,
  Texto,
  textos,
  unir,
  useAparecer,
  useEntra,
  useEntrar,
  useEscalar,
  useTramo,
  type Estilo,
} from "../comun";
import { FondoCircuito } from "./D01Portada";
import { Llama, LLAMA_UNIDADES } from "./D03QuienHabla";

export const pasos = pasosDe("D04");

type DatosQr = { texto: string; pendiente: boolean; prueba: boolean; nivel: string; modulos: number; filas: string[] };
const QR = qrJson as unknown as DatosQr;
const DIRECCION_DECK = (deckJson as unknown as { enlaces: { formulario_sorteo: string } }).enlaces.formulario_sorteo;
const CON_FORMULARIO = !DIRECCION_DECK.includes("FORMULARIO_PENDIENTE");

// Si qr.json no es de la dirección del deck, no se renderiza (salvo un QR de prueba, que no va a git).
if (!QR.prueba && QR.texto !== DIRECCION_DECK) {
  throw new Error(
    `D04: diseno/medios/D04/qr.json es de "${QR.texto}" y el deck dice "${DIRECCION_DECK}". ` +
      "Correr node diseno/medios/D04/generar_qr.mjs y volver a renderizar D04.",
  );
}

// ---------------------------------------------------------------------------------------------
// Medidas.
// ---------------------------------------------------------------------------------------------
const X = 140;
const Y = { titulo: 200, escanea: 330, palabraDe: 470, palabra: 580, gratis: 720 };
const TARJETA = { x0: 1200, y0: 120, x1: 1800, y1: 720 };
const LADO_TARJETA = TARJETA.x1 - TARJETA.x0;
const CX_TARJETA = (TARJETA.x0 + TARJETA.x1) / 2;
const CY_TARJETA = (TARJETA.y0 + TARJETA.y1) / 2;
const MARGEN_QR = 4; // módulos de margen claro, como mínimo
// La llama es la protagonista del sorteo: 300 px de alto (era 150), entre el texto y la tarjeta.
const LLAMA = { alto: 300, piso: 760, derecha: 1150 };
const ANCHO_LLAMA = (LLAMA.alto * LLAMA_UNIDADES.ancho) / LLAMA_UNIDADES.alto;
const X_LLAMA_SALE = TARJETA.x0 + 16; // escondida detrás de la tarjeta

// Sin formulario: sin tarjeta, los cuatro textos más repartidos y la llama grande a la derecha.
const Y_SIN = { titulo: 240, palabraDe: 440, palabra: 550, gratis: 700 };
const LLAMA_SIN = { alto: 560, piso: 820, cx: 1440 };
const X_LLAMA_SIN = Math.round(LLAMA_SIN.cx - (LLAMA_SIN.alto * LLAMA_UNIDADES.ancho) / LLAMA_UNIDADES.alto / 2);
const X_LLAMA_SIN_SALE = 1960; // afuera del cuadro, a la derecha

// ---------------------------------------------------------------------------------------------
// La dirección escrita: en un renglón si entra, si no en dos, cortada antes de una barra.
// ---------------------------------------------------------------------------------------------
const TAM_DIRECCION = 49;
const ANCHO_CENTRADO = 2 * (1853 - CX_TARJETA); // centrada en x 1500 sin salir de la zona segura
const ANCHO_DERECHA = TARJETA.x1 - 960; // alineada con la tarjeta, sin pasar x 960

type Direccion = { renglones: string[]; x: number; alinear: "centro" | "der"; y: number; ancho: number };

export function disponerDireccion(texto: string): Direccion {
  const entero = medirTexto(texto, TAM_DIRECCION);
  if (entero <= ANCHO_CENTRADO) return { renglones: [texto], x: CX_TARJETA, alinear: "centro", y: 790, ancho: entero };
  // Cortes posibles: antes de cada barra que no sea la de https://.
  const inicio = texto.indexOf("://") >= 0 ? texto.indexOf("://") + 3 : 0;
  let mejor: string[] | null = null;
  let anchoMejor = Infinity;
  for (let i = inicio; i < texto.length; i++) {
    if (texto[i] !== "/") continue;
    const partes = [texto.slice(0, i), texto.slice(i)];
    const w = Math.max(...partes.map((p) => medirTexto(p, TAM_DIRECCION)));
    if (w < anchoMejor) {
      anchoMejor = w;
      mejor = partes;
    }
  }
  if (mejor && anchoMejor <= ANCHO_CENTRADO) return { renglones: mejor, x: CX_TARJETA, alinear: "centro", y: 800, ancho: anchoMejor };
  if (mejor && anchoMejor <= ANCHO_DERECHA) return { renglones: mejor, x: TARJETA.x1, alinear: "der", y: 800, ancho: anchoMejor };
  throw new Error(
    `D04: la dirección "${texto}" no entra debajo de la tarjeta a ${TAM_DIRECCION} px ni en dos renglones ` +
      `(el renglón más largo mide ${Math.round(anchoMejor)} px y caben ${Math.round(ANCHO_DERECHA)}). Hay que acortarla.`,
  );
}

// ---------------------------------------------------------------------------------------------
// El QR (o el rayado de pendiente), en píxeles enteros.
// ---------------------------------------------------------------------------------------------
const CodigoQr: React.FC<{ opacidad: number }> = ({ opacidad }) => {
  const n = QR.modulos;
  const px = Math.floor(LADO_TARJETA / (n + 2 * MARGEN_QR));
  const lado = n * px;
  const x0 = Math.round(CX_TARJETA - lado / 2);
  const y0 = Math.round(CY_TARJETA - lado / 2);
  // Un rectángulo por tramo de módulos oscuros seguidos en cada fila.
  const tramos: React.ReactNode[] = [];
  QR.filas.forEach((fila, r) => {
    let c = 0;
    while (c < n) {
      if (fila[c] !== "1") {
        c++;
        continue;
      }
      let f = c;
      while (f < n && fila[f] === "1") f++;
      tramos.push(<rect key={`${r}-${c}`} x={x0 + c * px} y={y0 + r * px} width={(f - c) * px} height={px} />);
      c = f;
    }
  });
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, opacity: opacidad }} shapeRendering="crispEdges">
      <g fill={COLOR.tinta}>{tramos}</g>
    </svg>
  );
};

// ---------------------------------------------------------------------------------------------
// La diapositiva.
// ---------------------------------------------------------------------------------------------
const T = { titulo: 0.05, tarjeta: 0.25, qr: 0.7, lineas: 0.35, desfase: 0.15, direccion: 1.0, camina: 1.35, duraCamina: 1.2, vuelta: 2.6 };

export const D04AnotateAlSorteo: React.FC = () => {
  // Con formulario: ["Al final hay sorteo.", "Escaneá y anotate", "Palabra de la charla:", "llama",
  //  "Participar es gratis.", la dirección sin https://]. Sin formulario: ["Al final hay sorteo.",
  //  "Palabra de la charla:", "llama", "Participar es gratis."].
  const t = textos("D04", 1);
  if (t.length !== (CON_FORMULARIO ? 6 : 4)) {
    throw new Error(`D04: el deck trae ${t.length} textos y ${CON_FORMULARIO ? "con" : "sin"} formulario son ${CON_FORMULARIO ? 6 : 4}. Correr contenido/generar_deck.py.`);
  }
  const [titulo, escanea, palabraDe, palabra, gratis, direccionDeck] = CON_FORMULARIO ? t : [t[0], "", t[1], t[2], t[3], ""];
  // Con un QR de prueba, la dirección escrita es la de la prueba (así se mira cómo queda).
  const direccion = CON_FORMULARIO ? disponerDireccion(QR.prueba ? QR.texto : direccionDeck) : null;
  // Sin la línea de Escaneá y anotate, las demás suben un lugar en la cascada.
  const k0 = CON_FORMULARIO ? 1 : 0;

  const estTitulo = useEntrar(1, T.titulo, { dura: 0.5 });
  const estTarjeta = useEscalar(1, T.tarjeta, { desde: MOV.escala.tarjeta_entra, dura: 0.5 });
  const opQr = useAparecer(1, T.qr, 0.3).opacity as number;
  const estEscanea = useEntrar(1, T.lineas, { dura: 0.5 });
  const estPalabraDe = useEntrar(1, T.lineas + k0 * T.desfase, { dura: 0.5 });
  const pPalabra = Math.min(1, useEntra(1, T.lineas + (k0 + 1) * T.desfase, 0.5, RESORTE.golpe));
  const estPalabra: Estilo = { opacity: Math.min(1, 2.5 * pPalabra), transform: `scale(${MOV.escala.golpe_chico - (MOV.escala.golpe_chico - 1) * pPalabra})` };
  const estGratis = useEntrar(1, T.lineas + (k0 + 2) * T.desfase, { dura: 0.5 });
  const estDireccion = unir(useAparecer(1, T.direccion, 0.4), useEntrar(1, T.direccion, { dura: 0.5, distancia: 20 }));

  // La llama: cuatro pasos hacia la izquierda, a velocidad pareja con arranque y frenada suaves. Se para
  // junto a la esquina de la tarjeta (su borde derecho en x 1150), salvo que la dirección vaya en dos
  // renglones alineados a la derecha y pase por debajo de ella: ahí se para 30 px antes de la dirección.
  const derechaLlama = direccion && direccion.alinear === "der" ? Math.min(LLAMA.derecha, Math.round(direccion.x - direccion.ancho - 30)) : LLAMA.derecha;
  const X_LLAMA = Math.round(derechaLlama - ANCHO_LLAMA);
  const camino = useTramo(1, T.camina, T.duraCamina, CURVA.suave);
  const pasosDados = useTramo(1, T.camina, T.duraCamina, CURVA.lineal) * 4;
  const xLlama = X_LLAMA_SALE + (X_LLAMA - X_LLAMA_SALE) * camino;
  const vuelta = useTramo(1, T.vuelta, 0.25, CURVA.suave);
  const mira = -1 + 2 * vuelta;
  const enMarcha = pasosDados > 0 && pasosDados < 4;

  if (!direccion) {
    // Sin formulario: el sorteo se anuncia sin QR, con la llama grande que entra desde el borde derecho.
    const xLlamaSin = X_LLAMA_SIN_SALE + (X_LLAMA_SIN - X_LLAMA_SIN_SALE) * camino;
    return (
      <>
        <FondoCircuito />

        <Texto x={X} y={Y_SIN.titulo} tam="grande" color={COLOR.titulo} estilo={estTitulo}>
          {titulo}
        </Texto>
        <Texto x={X} y={Y_SIN.palabraDe} tam="lectura" estilo={estPalabraDe}>
          {palabraDe}
        </Texto>
        <Texto x={X} y={Y_SIN.palabra} tam="grande" color={COLOR.ambar} estilo={{ ...estPalabra, transformOrigin: "0% 50%" }}>
          {palabra}
        </Texto>
        <Texto x={X} y={Y_SIN.gratis} tam="lectura" color={COLOR.gris} estilo={estGratis}>
          {gratis}
        </Texto>

        {pasosDados > 0 && (
          <Llama x={xLlamaSin} piso={LLAMA_SIN.piso} alto={LLAMA_SIN.alto} pasosDados={enMarcha ? pasosDados : 0} mira={mira} />
        )}
      </>
    );
  }

  return (
    <>
      <FondoCircuito />

      <Texto x={X} y={Y.titulo} tam="grande" color={COLOR.titulo} estilo={estTitulo}>
        {titulo}
      </Texto>
      <Texto x={X} y={Y.escanea} tam="frase" estilo={estEscanea}>
        {escanea}
      </Texto>
      <Texto x={X} y={Y.palabraDe} tam="lectura" estilo={estPalabraDe}>
        {palabraDe}
      </Texto>
      <Texto x={X} y={Y.palabra} tam="grande" color={COLOR.ambar} estilo={{ ...estPalabra, transformOrigin: "0% 50%" }}>
        {palabra}
      </Texto>
      <Texto x={X} y={Y.gratis} tam="lectura" color={COLOR.gris} estilo={estGratis}>
        {gratis}
      </Texto>

      {/* La llama camina detrás de la tarjeta y sale por su borde izquierdo. */}
      {pasosDados > 0 && (
        <Llama
          x={xLlama}
          piso={LLAMA.piso}
          alto={LLAMA.alto}
          pasosDados={enMarcha ? pasosDados : 0}
          mira={mira}
          recorteDerecha={TARJETA.x0}
        />
      )}

      {/* La tarjeta con el QR. */}
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${CX_TARJETA}px ${CY_TARJETA}px`, ...estTarjeta }}>
        <div
          style={{
            position: "absolute",
            left: TARJETA.x0,
            top: TARJETA.y0,
            width: LADO_TARJETA,
            height: TARJETA.y1 - TARJETA.y0,
            borderRadius: RADIO.tarjeta,
            background: COLOR.hueso,
          }}
        />
        <CodigoQr opacidad={opQr} />
      </div>

      {direccion.renglones.map((r, i) => (
        <Texto key={i} x={direccion.x} y={direccion.y + i * Math.round(TAM_DIRECCION * 1.25)} tam={TAM_DIRECCION} alinear={direccion.alinear} estilo={estDireccion}>
          {r}
        </Texto>
      ))}
    </>
  );
};
