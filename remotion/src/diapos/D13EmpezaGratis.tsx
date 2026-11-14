// D13 Empezá gratis hoy (contenido/guion.md, D13). La diapositiva para sacarle foto: cuatro filas
// numeradas con cómo empezar sin gastar y, a la derecha, el QR grande del repositorio.
//
// D13.1 (3,7 s en el deck = 0,4 s de fundido desde D12, otro video, + 3,3 s propios)
//   0,00-0,74  el título entra palabra por palabra.
//   0,30-1,25  las cuatro filas suben de a una (desfase 0,15 s): primero el círculo con su número
//              (escala desde 0,6) y enseguida el nombre y el detalle.
//   0,75-1,25  el 14 y el 250 entran con un golpe cuando su fila ya está (el dato que se dice).
//   1,05-1,55  la tarjeta del QR sube (escala de 0,9 a 1).
//   1,40-2,45  el QR se arma: primero los tres cuadros de las esquinas, después los módulos en una
//              diagonal, de arriba a la izquierda hacia abajo a la derecha. Quieto desde 2,45.
//
// Cuadro final (guion): "Empezá gratis hoy" en titulo a 104 px en y 160 desde x 160. Cuatro filas
// desde x 260 con el círculo en x 190: el nombre en hueso a 60 px en y 320, 480, 640 y 800 y el
// detalle en gris a 49 px 60 px más abajo (el último, la dirección del repositorio, en hueso). En
// ámbar, solo el 14 y el 250. El QR en una tarjeta hueso a la derecha, sin rótulo propio.
//
// Este archivo exporta TarjetaQR, useArmarQR y QR_REPOSITORIO, que usa también D15 (el mismo QR,
// con otro tamaño de tarjeta). Las decisiones propias van con "Ajuste:".
// Debajo de todo va el fondo de circuito de la charla (FondoCircuito de D01Portada.tsx).
import React from "react";
import { FondoCircuito } from "./D01Portada";
import {
  COLOR,
  conAlfa,
  CURVA,
  GROSOR,
  MOV,
  OPACIDAD,
  pasosDe,
  RADIO,
  TIPO,
  Texto,
  textos,
  useEntrar,
  useEntrarPalabras,
  useEscalar,
  useGolpe,
  useTramo,
  type Estilo,
} from "../comun";
import deckJson from "../../../contenido/deck.json";
import qrJson from "../../../diseno/medios/D13/qr-repositorio.json";

export const pasos = pasosDe("D13");

// ---------------------------------------------------------------------------------------
// El QR del repositorio (D13 y D15)
// ---------------------------------------------------------------------------------------

/**
 * La matriz del QR de enlaces.repositorio (qrcode-generator 2.0.4, corrección M, leída de vuelta con
 * jsqr 1.4.0). Si la dirección del deck cambia y el QR no se volvió a generar, falla el render: un QR
 * que lleva a otro lado no puede salir en pantalla.
 */
export const QR_REPOSITORIO = (() => {
  const url = (deckJson as unknown as { enlaces: { repositorio: string } }).enlaces.repositorio;
  const qr = qrJson as { url: string; modulos: number; filas: string[] };
  if (qr.url !== url) {
    throw new Error(`El QR de diseno/medios/D13/qr-repositorio.json es de "${qr.url}" y el deck dice "${url}": hay que volver a generarlo.`);
  }
  if (qr.filas.length !== qr.modulos || qr.filas.some((f) => f.length !== qr.modulos)) {
    throw new Error("qr-repositorio.json: la matriz no es cuadrada.");
  }
  return { url, n: qr.modulos, filas: qr.filas };
})();

/** Margen blanco mínimo alrededor del QR, en módulos (reglas de QR de la marca de Tinkazo). */
const MARGEN_MODULOS = 4;

/** ¿El módulo (x, y) es parte de uno de los tres cuadros de las esquinas (7×7)? */
function enEsquina(x: number, y: number, n: number): boolean {
  const cerca = (v: number) => v < 7;
  const lejos = (v: number) => v >= n - 7;
  return (cerca(x) && cerca(y)) || (lejos(x) && cerca(y)) || (cerca(x) && lejos(y));
}

export type ArmadoQR = { tarjeta: Estilo; esquinas: number; modulos: number };

/**
 * Cómo entra el QR: la tarjeta sube con escala de 0,9 a 1 (0,5 s). A los 0,35 s aparecen los tres
 * cuadros de las esquinas (0,3 s) y a los 0,45 s los demás módulos se encienden en una diagonal
 * (0,6 s). Dura 1,05 s desde `retraso`.
 */
export function useArmarQR(paso: number, retraso: number): ArmadoQR {
  return {
    tarjeta: useEscalar(paso, retraso, { desde: MOV.escala.tarjeta_entra }),
    esquinas: useTramo(paso, retraso + 0.35, 0.3, CURVA.sale),
    modulos: useTramo(paso, retraso + 0.45, 0.6, CURVA.lineal),
  };
}

/**
 * La tarjeta hueso con el QR en tinta: oscuro sobre claro, nunca invertido, sin logo encima y con un
 * margen blanco de 4 módulos o más (la tarjeta es ese margen). Los módulos van en píxeles enteros:
 * el módulo es el entero más grande que deja los 4 módulos de margen, y el QR queda centrado.
 * Mientras se arma, cada módulo se enciende con un fundido corto según su diagonal (x + y). Al
 * terminar es un solo trazado con bordes nítidos.
 */
export const TarjetaQR: React.FC<{ x0: number; y0: number; lado: number; armado: ArmadoQR }> = ({ x0, y0, lado, armado }) => {
  const { n, filas } = QR_REPOSITORIO;
  const modulo = Math.floor(lado / (n + 2 * MARGEN_MODULOS));
  const ancho = modulo * n;
  const qx = x0 + Math.floor((lado - ancho) / 2);
  const qy = y0 + Math.floor((lado - ancho) / 2);
  const cx = x0 + lado / 2;
  const cy = y0 + lado / 2;

  // Opacidad de cada módulo: las esquinas, juntas. El resto, por su diagonal, con un fundido de 0,25
  // del recorrido (así la diagonal se ve avanzar sin que ningún módulo aparezca de golpe).
  const ventana = 0.25;
  const opacidadDe = (x: number, y: number): number => {
    if (enEsquina(x, y, n)) return armado.esquinas;
    const orden = (x + y) / (2 * (n - 1));
    const p = (armado.modulos - orden * (1 - ventana)) / ventana;
    return Math.max(0, Math.min(1, p));
  };

  const completo = armado.esquinas >= 1 && armado.modulos >= 1;
  let d = "";
  const sueltos: React.ReactNode[] = [];
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      if (filas[y][x] !== "1") continue;
      const px = qx + x * modulo;
      const py = qy + y * modulo;
      if (completo) {
        d += `M${px} ${py}h${modulo}v${modulo}h${-modulo}z`;
        continue;
      }
      const o = opacidadDe(x, y);
      if (o <= 0) continue;
      if (o >= 1) d += `M${px} ${py}h${modulo}v${modulo}h${-modulo}z`;
      else sueltos.push(<rect key={`${x}-${y}`} x={px} y={py} width={modulo} height={modulo} fill={COLOR.tinta} opacity={o} />);
    }
  }

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${cx}px ${cy}px`, ...armado.tarjeta }}>
      <div
        style={{
          position: "absolute",
          left: x0,
          top: y0,
          width: lado,
          height: lado,
          borderRadius: RADIO.tarjeta,
          backgroundColor: COLOR.hueso,
        }}
      />
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }} shapeRendering="crispEdges">
        {d && <path d={d} fill={COLOR.tinta} />}
        {sueltos}
      </svg>
    </div>
  );
};

// ---------------------------------------------------------------------------------------
// Las filas numeradas
// ---------------------------------------------------------------------------------------

/**
 * Guion D13.1: "cada una con un número en hueso dentro de un círculo de acero2 de 56 px", el círculo
 * en x 190 y el texto desde x 260.
 * Ajuste: el aro en hueso al 40 % (borde de apoyo, como NumeroCirculo de la charla de octubre: el
 * acero2 solo, sobre tinta, se pierde en una sala con luz) en el trazo fino, para que el número a
 * 49 px (el mínimo de un rótulo) respire adentro de 56 px. El círculo va a la altura del nombre.
 */
const FILAS = { xCirculo: 190, xTexto: 260, ys: [320, 480, 640, 800] as const, bajaDetalle: 60, diametro: 56 } as const;

const NumeroEnCirculo: React.FC<{ n: string; x: number; y: number; estilo: Estilo }> = ({ n, x, y, estilo }) => {
  const r = FILAS.diametro;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${x}px ${y}px`, ...estilo }}>
      <div
        style={{
          position: "absolute",
          left: x - r / 2,
          top: y - r / 2,
          width: r,
          height: r,
          boxSizing: "border-box",
          borderRadius: r / 2,
          border: `${GROSOR.borde_fino}px solid ${conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo)}`,
          backgroundColor: COLOR.acero2,
          backgroundClip: "padding-box",
        }}
      />
      <Texto x={x} y={y} tam={TIPO.escala.rotulo} alinear="centro">
        {n}
      </Texto>
    </div>
  );
};

/** Un estilo por palabra de `texto`: el golpe para la palabra `clave` y nada para las demás. */
function estilosConGolpe(texto: string, clave: string, golpe: Estilo): Estilo[] {
  const palabras: string[] = texto.match(/\S+/g) ?? [];
  if (!palabras.includes(clave)) throw new Error(`D13: "${clave}" no es una palabra de "${texto}".`);
  return palabras.map((p) => (p === clave ? golpe : {}));
}

/**
 * El QR. Guion: tarjeta de 480 por 480 px de x 1320 a 1800 y de y 300 a 780.
 * Ajuste: de 520 px (x 1270 a 1790, y 290 a 810) para que el QR sea lo más grande que deja la
 * columna de las filas (su renglón más largo termina antes de x 1240): módulos de 12 px en vez de 11.
 * Va 30 px más a la izquierda que antes: en x 1820 su borde quedaba pegado a la pista vertical del
 * fondo de circuito (x 1825).
 */
const QR = { x0: 1270, y0: 290, lado: 520 } as const;

// Tiempos (s desde el comienzo del video propio del paso, con los últimos 0,3 s quietos).
const T = {
  titulo: 0,
  filas: 0.3,
  desfase: MOV.desfase.renglones,
  numeroDespues: 0.05,
  golpes: [0.75, 0.9] as const,
  qr: 1.05,
} as const;

export const D13EmpezaGratis: React.FC = () => {
  const t = textos("D13", 1);
  const [titulo] = t;
  const nombres = [t[1], t[3], t[5], t[7]];
  const detalles = [t[2], t[4], t[6], t[8]];

  const palabrasTitulo = useEntrarPalabras(titulo, 1, T.titulo);
  const circulos = [0, 1, 2, 3].map((i) => useEscalar(1, T.filas + i * T.desfase, { desde: 0.6 }));
  const filas = [0, 1, 2, 3].map((i) => useEntrar(1, T.filas + i * T.desfase + T.numeroDespues));
  const golpe14 = useGolpe(1, T.golpes[0]);
  const golpe250 = useGolpe(1, T.golpes[1]);
  const armado = useArmarQR(1, T.qr);

  const palabras: (Estilo[] | undefined)[] = [estilosConGolpe(nombres[0], "14", golpe14), estilosConGolpe(nombres[1], "250", golpe250), undefined, undefined];
  const resaltados: (string | undefined)[] = ["14", "250", undefined, undefined];

  return (
    <>
      <FondoCircuito />
      <Texto x={160} y={160} tam="grande" color={COLOR.titulo} estiloPalabras={palabrasTitulo}>
        {titulo}
      </Texto>

      {FILAS.ys.map((y, i) => (
        <React.Fragment key={i}>
          <NumeroEnCirculo n={String(i + 1)} x={FILAS.xCirculo} y={y} estilo={circulos[i]} />
          <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...filas[i] }}>
            <Texto x={FILAS.xTexto} y={y} tam="lectura" resaltar={resaltados[i]} estiloPalabras={palabras[i]}>
              {nombres[i]}
            </Texto>
            <Texto x={FILAS.xTexto} y={y + FILAS.bajaDetalle} tam="rotulo" color={i === 3 ? COLOR.hueso : COLOR.gris}>
              {detalles[i]}
            </Texto>
          </div>
        </React.Fragment>
      ))}

      <TarjetaQR x0={QR.x0} y0={QR.y0} lado={QR.lado} armado={armado} />
    </>
  );
};
