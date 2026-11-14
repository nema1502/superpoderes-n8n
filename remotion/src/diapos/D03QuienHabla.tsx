// D03 Quién les habla (guion D03.1). La bio: quién es el orador y por qué habla de n8n. Primera
// aparición de la llama de Tinkazo, que vuelve en D04 y en el sorteo.
//
// Entra con un fundido de 0,4 s desde D02 (es otro video): el cuadro 0 es tinta lisa. Un solo paso de
// 3,3 s propios (3,7 en el deck, con el fundido): todo quieto desde los 3,0 s.
//
// Cuadro final (deck D03.1, más el personaje de Nicolás), desde x 140:
//   Nicolás Emir Mejía Agreda en titulo (amarillo lima) a 88 px en y 200.
//   Isotipo lima de 48 px y nemaxyz en hueso a 49 px en y 290 (la firma de siempre: separación 0,45
//   del alto, como Logotipo).
//   Las cuatro líneas en hueso a 60 px desde x 200, en y 430, 530, 630 y 730, cada una con un
//   cuadradito azul de 16 px que empieza en x 150. Los cuatro cuadraditos van unidos por una pista
//   de circuito de 3 px en azul al 35 % (el mismo guiño al afiche que la portada).
//   Abajo a la derecha, el personaje de Nicolás del pitch de Tinkazo, tal cual, en un nodo de 470 px
//   (x 1320 a 1790, y 500 a 970) con borde azul y un brillo suave. Entra subiendo y enderezándose
//   (0,30 a 1,20 s) y el brillo se enciende de 1,00 a 1,60 s. Debajo de todo, el fondo de circuito.
//   Al final de la primera línea, el símbolo de n8n (n8n-symbol-accent.svg tal cual, 56 px de alto, a
//   30 px del texto). Al final de la tercera, la llama de Tinkazo de 80 px de alto (los nueve
//   rectángulos de contenido/tinkazo.md 4.1, magenta #ff5cb3, girada 3 grados, sin cara).
//   En ámbar solo n8n de la primera línea y Tinkazo.
// Sin marca de agua (tokens.json: D03 no la lleva, el isotipo ya está). D03.1 es paso de marca.
//
// Tiempos (s desde el comienzo del paso):
//   0,10-0,60 el nombre sube            0,45-1,25 el isotipo se dibuja de un trazo
//   0,60-1,10 entra nemaxyz             0,90-1,80 la pista baja y enciende cada cuadradito al pasar
//   1,00-2,10 las cuatro líneas suben de a una (desfase 0,2 s)
//   1,20-1,70 el símbolo de n8n entra con un golpe chico
//   1,65-2,15 la llama aparece con un golpe chico
//
// Exporta Llama (con su caminata), que usa también D04.
import React from "react";
import { Img, staticFile } from "remotion";
import {
  anchoIsotipo,
  COLOR,
  conAlfa,
  CURVA,
  GROSOR,
  Isotipo,
  medirTexto,
  MOV,
  pasosDe,
  RESORTE,
  Texto,
  textos,
  unir,
  useEntra,
  useEntrar,
  useTramo,
  type Estilo,
} from "../comun";
import { FondoCircuito, RADIO_NODO } from "./D01Portada";

export const pasos = pasosDe("D03");

// ---------------------------------------------------------------------------------------------
// La llama de Tinkazo: nueve rectángulos en una grilla donde 1 unidad es 1 cuadro (public/marca/
// llama.svg de Tinkazo, contenido/tinkazo.md 4.1). La caja va de x 0 a 22 y de y -2 a 24: 22 por 26
// unidades. Mira a la derecha. Magenta del tema oscuro, #ff5cb3. Sin cara, sin ojos, sin sombrero.
// ---------------------------------------------------------------------------------------------
export const MAGENTA_LLAMA = "#ff5cb3";
const CUERPO = [
  { x: 2, y: 11, w: 16, h: 7 }, // cuerpo
  { x: 15, y: 3, w: 4, h: 10 }, // cuello
  { x: 14, y: 0, w: 8, h: 4 }, // cabeza
  { x: 20, y: -2, w: 2, h: 3 }, // oreja
  { x: 0, y: 9, w: 3, h: 4 }, // cola
];
// Las patas, en dos pares que se alternan al caminar (1 y 3, 2 y 4), como un trote.
const PATAS = [
  { x: 3, par: 0 },
  { x: 8, par: 1 },
  { x: 12.5, par: 0 },
  { x: 16, par: 1 },
];
const PATA = { y: 18, w: 2.5, h: 6 };
export const LLAMA_UNIDADES = { ancho: 22, alto: 26 };

export type PropsLlama = {
  /** Borde izquierdo de la caja (sin girar) y la línea donde apoyan las patas. */
  x: number;
  piso: number;
  /** Alto de la caja en px (de la punta de la oreja a las patas). */
  alto: number;
  /** Pasos dados (continuo): 0 = quieta. Cada paso levanta un par de patas. */
  pasosDados?: number;
  /** Hacia dónde mira: 1 a la derecha (la de la marca), -1 a la izquierda, entre medio está girando. */
  mira?: number;
  /** Giro en grados (la marca la gira unos 3; negativo levanta la cabeza). Se invierte con `mira`. */
  giro?: number;
  opacidad?: number;
  estilo?: Estilo;
  /** Recorte: solo se ve lo que está a la izquierda de esta x (sale de atrás de algo). */
  recorteDerecha?: number;
};

export const Llama: React.FC<PropsLlama> = ({ x, piso, alto, pasosDados = 0, mira = 1, giro = -3, opacidad = 1, estilo, recorteDerecha }) => {
  const u = alto / LLAMA_UNIDADES.alto;
  const ancho = LLAMA_UNIDADES.ancho * u;
  const top = piso - alto;
  // Dentro de cada paso: el par que toca se levanta y avanza; el cuerpo sube un poco a mitad del paso.
  const enMarcha = pasosDados > 0;
  const k = Math.floor(pasosDados);
  const f = pasosDados - k;
  const parArriba = k % 2;
  const alzar = enMarcha ? Math.sin(Math.PI * f) : 0;
  const cuerpoY = enMarcha ? -0.45 * Math.sin(Math.PI * f) : 0;
  const recorte = recorteDerecha !== undefined ? `inset(-40px ${Math.max(0, 1920 - recorteDerecha)}px -40px -40px)` : undefined;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: recorte, opacity: opacidad, ...estilo }}>
      <svg
        width={ancho}
        height={alto}
        viewBox={`0 -2 ${LLAMA_UNIDADES.ancho} ${LLAMA_UNIDADES.alto}`}
        style={{
          position: "absolute",
          left: x,
          top,
          overflow: "visible",
          transform: `rotate(${giro * mira}deg) scaleX(${mira})`,
          transformOrigin: "50% 100%",
        }}
      >
        <g fill={MAGENTA_LLAMA}>
          <g transform={`translate(0 ${cuerpoY})`}>
            {CUERPO.map((r, i) => (
              <rect key={i} x={r.x} y={r.y} width={r.w} height={r.h} />
            ))}
          </g>
          {PATAS.map((p, i) => {
            const arriba = p.par === parArriba ? alzar : 0;
            // La pata levantada se acorta desde abajo y se adelanta; arriba sigue pegada al cuerpo.
            const dx = 0.9 * arriba;
            const corto = 1.6 * arriba;
            return <rect key={`p${i}`} x={p.x + dx} y={PATA.y + cuerpoY} width={PATA.w} height={PATA.h - corto - cuerpoY} />;
          })}
        </g>
      </svg>
    </div>
  );
};

// ---------------------------------------------------------------------------------------------
// La diapositiva.
// ---------------------------------------------------------------------------------------------
const X = 140;
const Y_NOMBRE = 200;
const Y_FIRMA = 290;
const ISOTIPO = 48;
const LINEAS_Y = [430, 530, 630, 730];
const X_LINEA = 200;
const CUADRITO = { x: 150, lado: 16 };
// El personaje de Nicolás (el del pitch de Tinkazo, tal cual: diseno/medios/D03/nicolas_personaje.png)
// en un nodo grande abajo a la derecha: borde azul de 5 px, radio del 16 % del lado y un brillo suave.
// Va debajo de la primera línea (la más larga) y a la derecha de la cuarta.
const RETRATO = { x0: 1320, y0: 500, lado: 470, src: "medios/D03/nicolas_personaje.png" };
const SIMBOLO_N8N = { alto: 56, ancho: (56 * 240) / 96, separacion: 30 };
const LLAMA = { alto: 80, separacion: 30 };

const T = { nombre: 0.1, isotipo: 0.45, firma: 0.6, pista: 0.9, duraPista: 0.9, lineas: 1.0, desfase: 0.2, retrato: 0.3, duraRetrato: 0.9, brillo: 1.0 };

export const D03QuienHabla: React.FC = () => {
  // ["Nicolás Emir Mejía Agreda", "nemaxyz", "Embajador de la comunidad de n8n en Bolivia",
  //  "n8n In the Loop, Berlín 2026", "Fundador de Tinkazo", "19 eventos de tecnología organizados"]
  const [nombre, firma, ...lineas] = textos("D03", 1);

  const estNombre = useEntrar(1, T.nombre, { dura: 0.5 });
  const isotipo = useTramo(1, T.isotipo, 0.8, CURVA.suave);
  const estFirma = useEntrar(1, T.firma, { dura: 0.5, desde: "izq" });
  const xFirma = X + anchoIsotipo(ISOTIPO) + Math.round(0.45 * ISOTIPO);

  // La pista baja por los cuadraditos y cada uno se enciende cuando la pista llega.
  const cx = CUADRITO.x + CUADRITO.lado / 2;
  const pista = useTramo(1, T.pista, T.duraPista, CURVA.suave);
  const yPista = LINEAS_Y[0] + (LINEAS_Y[3] - LINEAS_Y[0]) * pista;
  const cuadritos = LINEAS_Y.map((_, i) => useEntra(1, T.pista + (i / 3) * T.duraPista * 0.85, 0.35, RESORTE.golpe));
  const estLineas = LINEAS_Y.map((_, i) => useEntrar(1, T.lineas + i * T.desfase, { dura: 0.5 }));

  // El símbolo de n8n y la llama, al final de su renglón, con un golpe chico.
  const golpe = (retraso: number): Estilo => {
    const p = Math.min(1, useEntra(1, retraso, 0.5, RESORTE.golpe));
    const desde = MOV.escala.golpe_chico;
    return { opacity: Math.min(1, 2.5 * p), transform: `scale(${desde - (desde - 1) * p})` };
  };
  const estN8n = golpe(T.lineas + 0.2);
  const estLlama = golpe(T.lineas + 2 * T.desfase + 0.25);

  const xN8n = X_LINEA + medirTexto(lineas[0], "lectura") + SIMBOLO_N8N.separacion;
  const xLlama = X_LINEA + medirTexto(lineas[2], "lectura") + LLAMA.separacion;
  const pisoLlama = LINEAS_Y[2] + LLAMA.alto / 2;

  // El retrato sube desde abajo, enderezándose, con un resorte, y después se enciende su brillo.
  const pRetrato = useEntra(1, T.retrato, T.duraRetrato, RESORTE.entrar);
  const opRetrato = Math.min(1, 2.2 * useTramo(1, T.retrato, T.duraRetrato, CURVA.sale));
  const brilloRetrato = useTramo(1, T.brillo, 0.6, CURVA.suave);

  return (
    <>
      <FondoCircuito />

      {/* El retrato, en un nodo grande. */}
      <div
        style={{
          position: "absolute",
          left: RETRATO.x0,
          top: RETRATO.y0,
          width: RETRATO.lado,
          height: RETRATO.lado,
          opacity: opRetrato,
          transform: `translateY(${(1 - pRetrato) * 90}px) rotate(${(1 - pRetrato) * 5}deg) scale(${0.92 + 0.08 * pRetrato})`,
          transformOrigin: `${RETRATO.lado / 2}px ${RETRATO.lado}px`,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: Math.round(RADIO_NODO * RETRATO.lado),
            overflow: "hidden",
            boxShadow: `0 0 ${Math.round(RETRATO.lado * 0.12)}px ${Math.round(RETRATO.lado * 0.015)}px ${conAlfa(COLOR.azul, 0.45 * brilloRetrato)}`,
          }}
        >
          <Img src={staticFile(RETRATO.src)} style={{ position: "absolute", left: 0, top: 0, width: RETRATO.lado, height: RETRATO.lado }} />
        </div>
        <div
          style={{
            position: "absolute",
            inset: 0,
            boxSizing: "border-box",
            borderRadius: Math.round(RADIO_NODO * RETRATO.lado),
            border: `${GROSOR.borde}px solid ${COLOR.azul}`,
          }}
        />
      </div>
      <Texto x={X} y={Y_NOMBRE} tam="idea" color={COLOR.titulo} estilo={estNombre}>
        {nombre}
      </Texto>
      <Isotipo alto={ISOTIPO} x={X} y={Y_FIRMA - ISOTIPO / 2} progreso={isotipo} />
      <Texto x={xFirma} y={Y_FIRMA} tam="rotulo" estilo={estFirma}>
        {firma}
      </Texto>

      {/* La pista que une los cuadraditos y los cuadraditos. */}
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        {pista > 0 && <line x1={cx} y1={LINEAS_Y[0]} x2={cx} y2={yPista} stroke={conAlfa(COLOR.azul, 0.35)} strokeWidth={GROSOR.trazo_fino} />}
        {LINEAS_Y.map((y, i) => {
          const e = cuadritos[i];
          if (e <= 0) return null;
          const l = CUADRITO.lado * Math.min(1.25, e);
          return <rect key={y} x={cx - l / 2} y={y - l / 2} width={l} height={l} rx={3} fill={COLOR.azul} opacity={Math.min(1, 2 * e)} />;
        })}
      </svg>

      <Texto x={X_LINEA} y={LINEAS_Y[0]} resaltar="n8n" estilo={estLineas[0]}>
        {lineas[0]}
      </Texto>
      <Texto x={X_LINEA} y={LINEAS_Y[1]} estilo={estLineas[1]}>
        {lineas[1]}
      </Texto>
      <Texto x={X_LINEA} y={LINEAS_Y[2]} resaltar="Tinkazo" estilo={estLineas[2]}>
        {lineas[2]}
      </Texto>
      <Texto x={X_LINEA} y={LINEAS_Y[3]} estilo={estLineas[3]}>
        {lineas[3]}
      </Texto>

      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${xN8n + SIMBOLO_N8N.ancho / 2}px ${LINEAS_Y[0]}px`, ...estN8n }}>
        <Img
          src={staticFile("logos/n8n/n8n-symbol-accent.svg")}
          style={{ position: "absolute", left: xN8n, top: LINEAS_Y[0] - SIMBOLO_N8N.alto / 2, width: SIMBOLO_N8N.ancho, height: SIMBOLO_N8N.alto }}
        />
      </div>

      <Llama
        x={xLlama}
        piso={pisoLlama}
        alto={LLAMA.alto}
        estilo={unir(estLlama, { transformOrigin: `${xLlama + (LLAMA.alto * LLAMA_UNIDADES.ancho) / LLAMA_UNIDADES.alto / 2}px ${pisoLlama}px` })}
      />
    </>
  );
};
