// A4 Después de los 14 días (contenido/guion.md, Respaldo, A4). Para las preguntas: qué pasa cuando
// termina la prueba de n8n Cloud y cómo seguir en la compu propia.
//
// A4.1 (3,1 s en el deck = 0,4 s de fundido desde D15, otro video, + 2,7 s propios)
//   0,00-0,98  el título entra palabra por palabra.
//   0,30-1,10  las tres filas suben de a una (desfase 0,15 s): el ícono se da vuelta y el texto sube.
//   0,80-1,50  "npx n8n@2.47.7" se escribe letra por letra, con un cursor ámbar delante (es un comando).
//   1,35-1,85  el reloj de arena, que entró dado vuelta, gira media vuelta y queda derecho.
//   Quieto desde 1,95 (el respiro empieza a los 2,4).
//
// Cuadro final (guion): "Después de los 14 días" en titulo a 104 px en y 170 desde x 160. Tres filas
// con la línea principal en hueso y su detalle en gris debajo, cada una con su ícono en hueso a la
// izquierda (desktop, globe y hourglass-half). "npx n8n@2.47.7" en ámbar (la versión probada: desde
// n8n 3 el comando sin versión deja de servir). Marca de agua.
// Pulido: el guion pedía 72 y 49 px, y la diapositiva usaba media pantalla. Ahora la línea principal
// va a 88 px en y 340, 560 y 780, el detalle a 60 px 82 px más abajo y los íconos a 72 px: llena el
// ancho y el alto, y el detalle se lee desde el fondo. Debajo de todo, el fondo de circuito de la charla.
import React from "react";
import { FondoCircuito } from "./D01Portada";
import {
  COLOR,
  CURVA,
  grosorAsta,
  Icono,
  medirTexto,
  MOV,
  pasosDe,
  TIPO,
  Texto,
  textos,
  unir,
  useAparecer,
  useDesvanecer,
  useEntrar,
  useEntrarPalabras,
  useSegundos,
  useTramo,
  useVoltear,
  type NombreIcono,
} from "../comun";

export const pasos = pasosDe("A4");

/**
 * Las filas. Guion: "Tres filas desde x 260 … cada una con su ícono en hueso de 56 px a la
 * izquierda". Ajuste: los íconos centrados en x 190, en una columna (como los números de D13), a la
 * altura de la línea principal.
 */
const FILAS = { xIcono: 200, xTexto: 300, ys: [340, 560, 780] as const, bajaDetalle: 82, icono: 72 } as const;
const ICONOS: NombreIcono[] = ["desktop", "globe", "hourglass-half"];

/** El comando que se escribe letra por letra (tiene que estar tal cual en la primera fila). */
const COMANDO = "npx n8n@2.47.7";

const T = {
  titulo: 0,
  filas: 0.3,
  desfase: MOV.desfase.renglones,
  textoDespues: 0.05,
  escribe: 0.8,
  porLetra: 0.05,
  reloj: { retraso: 1.35, dura: 0.5 },
} as const;

/**
 * "npx n8n" se escribe: una franja de tinta tapa lo que falta escribir y el cursor va delante de la
 * última letra. El fondo es tinta pareja, así que la franja no se ve. Al terminar, el cursor se apaga.
 * Ajuste: el cursor es un guion bajo ámbar (medio em de ancho, el grosor del asta, sobre la línea de
 * base), como el de una terminal. Una barra vertical del alto de la mayúscula se leía como una "l" más
 * del comando ("npx n8nl").
 */
const Escritura: React.FC<{ linea: string; x: number; y: number; tam: number; letras: number; cursor: number }> = ({ linea, x, y, tam, letras, cursor }) => {
  const i = linea.indexOf(COMANDO);
  if (i < 0) throw new Error(`A4: "${COMANDO}" no está en "${linea}".`);
  const antes = linea.slice(0, i);
  const xEscrito = x + medirTexto(antes + COMANDO.slice(0, letras), tam);
  const xFin = x + medirTexto(antes + COMANDO, tam);
  // La franja cubre del techo de las mayúsculas al fondo de la "p", sin tocar el detalle de abajo.
  const alto = Math.round(tam * 1.15);
  const ancho = Math.round(0.5 * tam);
  const grosor = Math.max(4, Math.round(grosorAsta(tam)));
  // Línea de base de Segoe UI Bold desde la y de <Texto>: 0,35 em (medido en la charla de octubre).
  const base = Math.round(y + 0.35 * tam);
  return (
    <>
      {letras < COMANDO.length && (
        <div style={{ position: "absolute", left: xEscrito, top: y - alto / 2, width: xFin - xEscrito + 8, height: alto, backgroundColor: COLOR.tinta }} />
      )}
      {cursor > 0 && (
        <div
          style={{
            position: "absolute",
            left: Math.round(xEscrito + (letras > 0 ? 4 : 0)),
            top: base + 3,
            width: ancho,
            height: grosor,
            backgroundColor: COLOR.ambar,
            opacity: cursor,
          }}
        />
      )}
    </>
  );
};

export const A4DespuesDeLaPrueba: React.FC = () => {
  const t = textos("A4", 1);
  const [titulo] = t;
  const lineas = [t[1], t[3], t[5]];
  const detalles = [t[2], t[4], t[6]];

  const palabrasTitulo = useEntrarPalabras(titulo, 1, T.titulo);
  const iconos = [0, 1, 2].map((i) => useVoltear(1, T.filas + i * T.desfase));
  const filas = [0, 1, 2].map((i) => useEntrar(1, T.filas + i * T.desfase + T.textoDespues));

  // La escritura: letras enteras, de a una, cada 0,05 s desde T.escribe.
  const seg = useSegundos(1);
  const letras = Math.max(0, Math.min(COMANDO.length, Math.floor((seg - T.escribe) / T.porLetra) + 1));
  const finEscritura = T.escribe + COMANDO.length * T.porLetra;
  const cursor = Number(useAparecer(1, T.escribe - 0.15, 0.15).opacity) * Number(useDesvanecer(1, finEscritura + 0.15, 0.3).opacity);

  // El reloj de arena entra dado vuelta y gira media vuelta hasta quedar derecho.
  const vuelta = useTramo(1, T.reloj.retraso, T.reloj.dura, CURVA.suave);

  return (
    <>
      <FondoCircuito />
      <Texto x={160} y={170} tam="grande" color={COLOR.titulo} estiloPalabras={palabrasTitulo}>
        {titulo}
      </Texto>

      {FILAS.ys.map((y, i) => (
        <React.Fragment key={i}>
          <Icono
            nombre={ICONOS[i]}
            alto={FILAS.icono}
            x={FILAS.xIcono}
            y={y}
            color={COLOR.hueso}
            estilo={i === 2 ? unir(iconos[i], { transform: `rotate(${180 * (1 - vuelta)}deg)` }) : iconos[i]}
          />
          <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...filas[i] }}>
            <Texto x={FILAS.xTexto} y={y} tam="idea" resaltar={i === 0 ? COMANDO : undefined}>
              {lineas[i]}
            </Texto>
            {i === 0 && <Escritura linea={lineas[0]} x={FILAS.xTexto} y={y} tam={TIPO.escala.idea} letras={letras} cursor={cursor} />}
            <Texto x={FILAS.xTexto} y={y + FILAS.bajaDetalle} tam="lectura" color={COLOR.gris}>
              {detalles[i]}
            </Texto>
          </div>
        </React.Fragment>
      ))}
    </>
  );
};
