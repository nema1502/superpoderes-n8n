// D15 Cierre (contenido/guion.md, D15). La idea clave por última vez, con las mismas palabras y el
// mismo dibujo que en D06.3, y dónde encontrar todo: el QR del repositorio, el LinkedIn y la firma.
// Es la última imagen de la charla: queda quieta durante las preguntas.
//
// D15.1 (3,7 s en el deck = 0,4 s de fundido desde D14, otro video, + 3,3 s propios)
//   0,00-0,74  vuelven los tres nodos de D06.3 (VER, PENSAR, HACER), de a uno, con su verbo.
//   0,40-0,85  las pistas se dibujan de puerto a puerto.
//   0,90-1,90  el dato ámbar recorre el flujo: sale de VER, pasa por PENSAR y entra en HACER, y cada
//              nodo late cuando el dato está adentro.
//   0,95-2,25  la idea se arma al ritmo del dato: "Que el flujo vea," cuando sale de VER, "piense"
//              cuando pasa por PENSAR y "y haga." cuando entra en HACER.
//   2,25-2,75  sube "Y ustedes, a construir lo que importa.". Quieto desde 2,75.
// D15.2 (3,9 s)
//   0,00-0,30  se van los nodos y la segunda frase.
//   0,05-0,60  la idea sube a y 150 y pasa a 64 px (texto nativo en cada cuadro, no una imagen escalada).
//   0,45-1,50  la tarjeta del QR sube y el QR se arma (el mismo de D13).
//   0,55-1,35  el repositorio, el LinkedIn y "Gracias" suben de a uno.
//   0,90-3,55  la firma: el hilo ámbar dibuja la N, la N pasa a lima, aparece nemaxyz y @nemaxyz.
//
// Los nodos, las pistas, el dato y la idea son las piezas de D06DosSuperpoderes.tsx con su geometría
// chica (PoderesChicos e IDEA_PODERES): el cuadro final de D15.1 es el de D06.3 con la segunda frase
// debajo. Si cambia D06.3, D15.1 cambia con ella.
//
// Cuadro final de D15.2 (guion): la idea arriba a 64 px, el QR a la izquierda (420 por 420, x 160 a
// 580, y 270 a 690), el repositorio y el LinkedIn en hueso a 60 px en y 360 y 460, "Gracias" en
// titulo a 104 px en y 620, y la firma centrada en x 1260 (N de 96 px y nemaxyz a 96 px en y 830,
// @nemaxyz en lima a 60 px en y 950). Sin marca de agua (tokens.json). El lima de la firma está
// permitido en D15.2 (armar/auditoria_reglas.json, pasos_de_marca).
//
// El renglón del LinkedIn sale del deck tal cual: mientras el deck no tenga el LinkedIn, dice tinkazo.app.
// armar/poner_datos.py lo pone y vuelve a renderizar esta diapositiva. Las decisiones propias van con "Ajuste:".
//
// Pulido: debajo de todo, el fondo de circuito de la charla (FondoCircuito de D01Portada.tsx), el mismo
// de D06.3, así D15.1 sigue siendo D06.3. En D15.2 vuelve chico el personaje de Nicolás que se vio en
// D03 (nota de dirección 2), en el mismo nodo de borde azul, debajo del QR: llena la esquina de abajo a
// la izquierda, que quedaba vacía, y la charla cierra con su cara al lado de Gracias.
import React from "react";
import { Img, staticFile } from "remotion";
import { FondoCircuito } from "./D01Portada";
import {
  Capa,
  COLOR,
  conAlfa,
  CURVA,
  Firma,
  GROSOR,
  IDEA_CLAVE,
  medirTexto,
  TIPO,
  Texto,
  textos,
  pasosDe,
  useDesvanecer,
  useEntra,
  useEntrar,
  useEscalar,
  useFirma,
  useTramo,
  ZONA,
  type Estilo,
} from "../comun";
import { TarjetaQR, useArmarQR } from "./D13EmpezaGratis";
import { IDEA_PODERES, PoderesChicos } from "./D06DosSuperpoderes";

export const pasos = pasosDe("D15");

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

/** Un latido de D06 (0, sube a 1 a la mitad y vuelve a 0): el nodo crece 1,06 y su borde va al ámbar. */
function useLatido(paso: number, retraso: number, dura = 0.35): number {
  return Math.sin(Math.PI * useTramo(paso, retraso, dura, CURVA.lineal));
}

/**
 * Cuándo está el dato adentro de cada nodo. Va de VER a HACER por el centro de la fila con la curva
 * suave: sale del centro de VER, cruza PENSAR a la mitad del recorrido y llega al centro de HACER.
 * El latido de cada nodo queda centrado en ese momento.
 */
const T1 = {
  nodos: 0,
  desfaseNodo: 0.12,
  verbo: 0.15,
  pistas: { retraso: 0.4, dura: 0.45 },
  dato: { retraso: 0.9, dura: 1.0 },
  latidos: [0.9, 1.225, 1.6] as const,
  // La idea, en tres golpes: cuando el dato sale de VER, cuando está en PENSAR y cuando entra en HACER.
  idea: [0.95, 1.3, 1.75] as const,
  segunda: 2.25,
} as const;

/** Palabras de la idea que entran en cada golpe: "Que el flujo vea,", "piense" e "y haga." */
const GRUPOS_IDEA = [4, 1, 2] as const;

/**
 * La idea: en D15.1, la de D06.3 (IDEA_PODERES: 88 px centrada en y 600, "vea, piense y haga" en
 * ámbar), y la segunda frase en hueso a 60 px en y 720. En D15.2 sube a y 150 a 64 px (idea_arriba).
 */
const IDEA = { arriba: { y: 150, tam: TIPO.escala.idea_arriba }, ySegunda: 720 } as const;

/**
 * Guion D15.2: el QR de 420 por 420 de x 160 a 580 y de y 270 a 690, el repositorio y el LinkedIn
 * desde x 680 y la firma centrada en x 1260.
 * Ajuste: la dirección del repositorio a 60 px mide unos 1185 px y desde x 680 se pasaba del borde
 * de la zona segura (x 1853). El bloque entero (el QR, 80 px de aire y la columna, que mide lo que
 * mida su renglón más largo) va centrado en el cuadro: con la dirección de hoy el QR queda de x 118
 * a 538 con sus 420 px (módulos de 10 px, 4,5 de margen) y la columna de x 618 a 1802, con el
 * mismo aire a cada lado del cuadro. La firma va centrada en la columna (x 1210), como pide el
 * guion respecto de la columna que él dibujaba.
 * Si el LinkedIn que llegue fuera más largo que la dirección, el QR se achica hasta 360 px como
 * mucho. Más allá, el LinkedIn se achica (hasta 49 px) en vez de romper el render.
 */
// Pulido: el QR de 410 y 64 px de aire (eran 420 y 80). Con la dirección de hoy la columna termina en
// x 1789 y no en 1802: la pista vertical del fondo de circuito (x 1825) ya no queda pegada a la n final.
const QR = { y0: 270, lado: 410, ladoMinimo: 360, aire: 64 } as const;
const COLUMNA = { yRepo: 360, yLinkedin: 460, yGracias: 620 } as const;
const FIRMA = { cy: 830, alto: 96, arrobaY: 950 } as const;

/**
 * El personaje de Nicolás (diseno/medios/D03/nicolas_personaje.png, tal cual, el de D03): un nodo de
 * 230 px con borde azul de 5 px, radio del 16 % del lado y el brillo azul suave de D03, centrado debajo
 * del QR, con 50 px de aire.
 */
const RETRATO = { lado: 230, aire: 50, radio: 0.16, src: "medios/D03/nicolas_personaje.png" } as const;

// La tarjeta del QR espera a que la idea termine de pasar por encima de su lugar (a los 0,45 s la idea
// ya está arriba de y 230 y la tarjeta empieza en y 291 por la escala de 0,9).
const T2 = { sale: 0, subir: { retraso: 0.05, dura: 0.55 }, qr: 0.45, repo: 0.55, linkedin: 0.7, gracias: 0.85, firma: 0.9, retrato: 1.1, retratoDura: 0.8 } as const;

export const D15Cierre: React.FC = () => {
  const t1 = textos("D15", 1); // [idea, segunda frase]
  const t2 = textos("D15", 2); // [idea, repositorio, LinkedIn, Gracias, nemaxyz, @nemaxyz]
  const verbos = textos("D06", 2).slice(1, 4); // VER, PENSAR, HACER, tal cual D06.2

  // La idea es la misma de D06.3 y de idea_clave: con las mismas palabras, o no se renderiza.
  const idea = t1[0];
  if (t2[0] !== idea || textos("D06", 3)[0] !== idea || idea !== IDEA_CLAVE) {
    throw new Error("D15: la idea tiene que ser la misma en D15.1, D15.2, D06.3 e idea_clave (deck.json).");
  }
  if (t2[4] !== "nemaxyz") throw new Error(`D15.2: deck.json dice "${t2[4]}" y la firma dibuja "nemaxyz".`);

  // ---- Paso 1 ----
  const estilosNodo = [0, 1, 2].map((i) => useEscalar(1, T1.nodos + i * T1.desfaseNodo, { desde: 0.85 }));
  const estilosVerbo = [0, 1, 2].map((i) => useEntrar(1, T1.nodos + i * T1.desfaseNodo + T1.verbo, { distancia: 30 }));
  const pistas = useTramo(1, T1.pistas.retraso, T1.pistas.dura, CURVA.suave);
  const dato = useTramo(1, T1.dato.retraso, T1.dato.dura, CURVA.suave);
  const latidos = [useLatido(1, T1.latidos[0]), useLatido(1, T1.latidos[1]), useLatido(1, T1.latidos[2])];
  const golpes = [useEntrar(1, T1.idea[0]), useEntrar(1, T1.idea[1]), useEntrar(1, T1.idea[2])];
  const estilosIdea: Estilo[] = GRUPOS_IDEA.flatMap((n, g) => Array.from({ length: n }, () => golpes[g]));
  const nPalabras = (idea.match(/\S+/g) ?? []).length;
  if (estilosIdea.length !== nPalabras) throw new Error(`D15.1: la idea tiene ${nPalabras} palabras y los grupos suman ${estilosIdea.length}.`);
  const segunda = useEntrar(1, T1.segunda);

  // ---- Paso 2 ----
  const sale = useDesvanecer(2, T2.sale);
  const subir = useTramo(2, T2.subir.retraso, T2.subir.dura, CURVA.suave);
  const armado = useArmarQR(2, T2.qr);
  const repo = useEntrar(2, T2.repo);
  const linkedin = useEntrar(2, T2.linkedin);
  const gracias = useEntrar(2, T2.gracias);
  const firma = useFirma(2, T2.firma);
  // El retrato sube desde abajo, enderezándose, con el resorte de entrar (como en D03).
  const pRetrato = useEntra(2, T2.retrato, T2.retratoDura);
  const opRetrato = Math.min(1, 2.2 * useTramo(2, T2.retrato, 0.5, CURVA.sale));

  // La columna de la derecha y el QR (ver el Ajuste de QR).
  const lectura = TIPO.escala.lectura;
  const anchoColumna = Math.max(medirTexto(t2[1], lectura), medirTexto(t2[2], lectura));
  const zona = ZONA.x1 - ZONA.x0;
  const ladoQR = Math.max(QR.ladoMinimo, Math.min(QR.lado, Math.floor(zona - QR.aire - anchoColumna)));
  const x0QR = Math.max(ZONA.x0, Math.round((1920 - (ladoQR + QR.aire + anchoColumna)) / 2));
  const xColumna = x0QR + ladoQR + QR.aire;
  const cxFirma = Math.round(xColumna + Math.min(anchoColumna, ZONA.x1 - xColumna) / 2);

  const retratoX0 = Math.round(x0QR + (ladoQR - RETRATO.lado) / 2);
  const retratoY0 = QR.y0 + ladoQR + RETRATO.aire;
  const radioRetrato = Math.round(RETRATO.radio * RETRATO.lado);

  const tamIdea = lerp(IDEA_PODERES.tam, IDEA.arriba.tam, subir);
  const yIdea = lerp(IDEA_PODERES.y, IDEA.arriba.y, subir);

  return (
    <>
      <FondoCircuito />
      <Capa estilo={sale}>
        <PoderesChicos verbos={verbos} estilosNodo={estilosNodo} estilosVerbo={estilosVerbo} pistas={pistas} latidos={latidos} dato={dato} />
        <Texto x={IDEA_PODERES.x} y={IDEA.ySegunda} tam="lectura" alinear="centro" estilo={segunda}>
          {t1[1]}
        </Texto>
      </Capa>

      <Texto x={IDEA_PODERES.x} y={yIdea} tam={tamIdea} alinear="centro" resaltar={IDEA_PODERES.resaltar} estiloPalabras={estilosIdea}>
        {idea}
      </Texto>

      {/* D15.2 */}
      <TarjetaQR x0={x0QR} y0={QR.y0} lado={ladoQR} armado={armado} />
      <Texto x={xColumna} y={COLUMNA.yRepo} tam="lectura" estilo={repo}>
        {t2[1]}
      </Texto>
      <Texto x={xColumna} y={COLUMNA.yLinkedin} tam="lectura" minimo={TIPO.escala.rotulo} estilo={linkedin}>
        {t2[2]}
      </Texto>
      <Texto x={xColumna} y={COLUMNA.yGracias} tam="grande" color={COLOR.titulo} estilo={gracias}>
        {t2[3]}
      </Texto>
      <Firma estado={firma} cx={cxFirma} cy={FIRMA.cy} alto={FIRMA.alto} arroba={t2[5]} arrobaY={FIRMA.arrobaY} />
      {pRetrato > 0 && (
        <div
          style={{
            position: "absolute",
            left: retratoX0,
            top: retratoY0,
            width: RETRATO.lado,
            height: RETRATO.lado,
            opacity: opRetrato,
            transform: `translateY(${(1 - pRetrato) * 60}px) rotate(${(1 - pRetrato) * 5}deg) scale(${0.92 + 0.08 * pRetrato})`,
            transformOrigin: `${RETRATO.lado / 2}px ${RETRATO.lado}px`,
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: radioRetrato,
              overflow: "hidden",
              boxShadow: `0 0 ${Math.round(RETRATO.lado * 0.12)}px ${Math.round(RETRATO.lado * 0.015)}px ${conAlfa(COLOR.azul, 0.45 * opRetrato)}`,
            }}
          >
            <Img src={staticFile(RETRATO.src)} style={{ position: "absolute", left: 0, top: 0, width: RETRATO.lado, height: RETRATO.lado }} />
          </div>
          <div style={{ position: "absolute", inset: 0, boxSizing: "border-box", borderRadius: radioRetrato, border: `${GROSOR.borde}px solid ${COLOR.azul}` }} />
        </div>
      )}
    </>
  );
};
