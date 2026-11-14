// D14 El sorteo con Tinkazo: el cierre en vivo. La llama de Tinkazo es la protagonista.
//
// D14.1 (4,1 s propios: el fundido de 0,4 s desde D13 va aparte). El logo baja arriba, la llama
//   entra caminando desde la izquierda hasta el centro, frena y se inclina 3 grados hacia la sala.
//   Después sube el título palabra por palabra y el lema.
// D14.2 (3,3 s). La llama da media vuelta, camina hacia la izquierda mientras se achica a 0,6,
//   vuelve a mirar a la derecha y se inclina. Entran las tres razones, cada una con su número.
// D14.3 (3,5 s). La llama cruza la fila hacia la derecha y detrás de ella van apareciendo los
//   tres nodos de n8n. Al llegar, el cuadrado crema de Tinkazo crece a su alrededor (su único
//   cuadro con el estilo de la marca: borde y sombra dura de tinta) y la llama toma el magenta
//   de fondo claro. Se dibujan las conexiones, la lista (una pastilla ámbar) recorre la fila y
//   entra al cuadrado, que late, mientras la cámara se acerca un poco.
//
// La llama se dibuja con los nueve rectángulos de la marca (contenido/tinkazo.md, 4.1: los mismos
// de diseno/logos/tinkazo/llama-oscuro.svg). En reposo es idéntica al archivo: las patas solo
// giran sobre la cadera mientras camina. Sin cara, sin ojos, sin sombrero. El magenta va solo en
// la llama y en el logo. Los colores de la marca de Tinkazo no son tokens de la charla: están acá,
// con su fuente (diseno/logos/tinkazo/LEEME.md).
//
// Todo lo que se lee queda arriba de y 900 (por eso el título y el lema suben respecto del deck).
//
// Pulido (nota de dirección 6: la llama protagonista en el sorteo, y 1: nada de media pantalla vacía):
// en D14.2 la llama queda a 0,8 (240 px) y no a 0,6, y la llama y las razones se centran en y 560
// (antes el tercio de abajo quedaba vacío). En D14.3 los nodos son de 170 px como en las demos, la
// fila baja a y 580 y el cuadrado de Tinkazo crece a 260 px con la llama a 0,55 adentro. Debajo de
// todo, el fondo de circuito de la charla (FondoCircuito de D01Portada.tsx), fuera de la cámara.
import React from "react";
import { FondoCircuito } from "./D01Portada";
import { Easing, Img, interpolateColors, staticFile } from "remotion";
import {
  COLOR,
  conAlfa,
  CURVA,
  GROSOR,
  Hilo,
  Icono,
  OPACIDAD,
  pasosDe,
  Texto,
  textos,
  unir,
  useEntra,
  useEntrar,
  useEntrarPalabras,
  useGolpe,
  useSale,
  useTramo,
  type Estilo,
} from "../comun";

export const pasos = pasosDe("D14");

// ---------- La marca de Tinkazo (diseno/logos/tinkazo/LEEME.md y contenido/tinkazo.md, 4.2) ----------
const MAGENTA_OSCURO = "#ff5cb3"; // la llama sobre fondo oscuro (llama-oscuro.svg)
const MAGENTA_CLARO = "#e93d9c"; // la llama sobre fondo claro (llama.svg)
const PAPEL = "#fff6e9"; // el papel del tema claro
const TINTA_MARCA = "#191919"; // bordes y sombras duras de la marca

// Logo horizontal oscuro: viewBox 715,398 x 148,96, a 100 px de alto (tal cual, sin deformar).
const LOGO_ALTO = 100;
const LOGO_ANCHO = (LOGO_ALTO * 715.398) / 148.96;
const LOGO_Y = 170;

// ---------- La llama: nueve rectángulos en una grilla de 22 x 26 unidades ----------
// x, y, ancho, alto (de -2 a 24 en y: la oreja sube a -2). Sin las patas.
const CUERPO: [number, number, number, number][] = [
  [2, 11, 16, 7], // cuerpo
  [15, 3, 4, 10], // cuello
  [14, 0, 8, 4], // cabeza
  [20, -2, 2, 3], // oreja
  [0, 9, 3, 4], // cola
];
const PATAS_X = [3, 8, 12.5, 16]; // ancho 2,5 y alto 6, desde y 18
const ALTO_UNIDADES = 26;
const PX_POR_UNIDAD = 300 / ALTO_UNIDADES; // a escala 1 la llama mide 300 px de alto
const ANGULO_PATA = 22; // grados que gira cada pata sobre la cadera en la mitad del paso
const REBOTE_PX = 6; // el rebote por paso, a escala 1
const PASO_PX = 130; // lo que avanza en cada paso, a escala 1
const INCLINACION = -3; // grados: la cabeza sube, como la marca la gira

type PoseLlama = {
  /** Centro de la llama en x (el medio de la grilla). */
  cx: number;
  /** y del piso: donde apoyan las patas. */
  base: number;
  escala: number;
  /** Fase de la marcha en radianes: en múltiplos de pi las patas quedan derechas. */
  fase: number;
  /** Giro en grados alrededor del medio de las patas (negativo: la cabeza sube). */
  giro: number;
  /** 1 mira a la derecha, -1 a la izquierda (lo de en medio es la media vuelta). */
  mira: number;
  color: string;
};

const Llama: React.FC<PoseLlama> = ({ cx, base, escala, fase, giro, mira, color }) => {
  const u = PX_POR_UNIDAD * escala;
  const a = ANGULO_PATA * Math.sin(fase);
  const rebote = -REBOTE_PX * escala * Math.abs(Math.sin(fase));
  const g = giro * (mira < 0 ? -1 : 1);
  const caminando = Math.abs(a) > 1e-6;
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
      <g transform={`translate(${cx} ${base + rebote}) rotate(${g}) scale(${mira * u} ${u}) translate(-11 -24)`} fill={color}>
        {CUERPO.map(([x, y, w, h], i) => (
          <rect key={i} x={x} y={y} width={w} height={h} />
        ))}
        {PATAS_X.map((x, i) => {
          // De a pares: la 1 con la 3 y la 2 con la 4. Cada pata gira sobre su cadera. Mientras
          // camina, una cadera quieta (mismo color, dentro del ancho del cuerpo) tapa la muesca que
          // deja el giro debajo del cuerpo. En reposo queda escondida detrás de la pata.
          const ang = i % 2 === 0 ? a : -a;
          return (
            <React.Fragment key={`p${i}`}>
              <rect x={x} y={18} width={2.5} height={6} transform={`rotate(${ang} ${x + 1.25} 18)`} />
              {caminando && <rect x={x} y={17.5} width={Math.min(2.5, 18 - x)} height={1.1} />}
            </React.Fragment>
          );
        })}
      </g>
    </svg>
  );
};

/** Caminata de x0 a x1 con un número entero de pasos (al llegar, las patas quedan derechas). */
function caminata(p: number, x0: number, x1: number, e0: number, e1: number, pasoPx = PASO_PX) {
  const distancia = Math.abs(x1 - x0);
  const pasosEnteros = Math.max(1, Math.round(distancia / (pasoPx * ((e0 + e1) / 2))));
  return {
    cx: x0 + (x1 - x0) * p,
    escala: e0 + (e1 - e0) * p,
    // Al llegar (p = 1) la fase es un múltiplo de pi y las patas quedan derechas. Se devuelve 0 exacto,
    // como al arrancar el paso siguiente (con pi * n el seno da 1e-15 y no 0).
    fase: p >= 1 ? 0 : Math.PI * pasosEnteros * p,
  };
}

// La marcha de D14.1: casi pareja al entrar y frenando al final.
const ENTRA_CAMINANDO = Easing.bezier(0.3, 0.4, 0.55, 1);

// ---------- Nodos del flujo (el estilo de la charla: deck, D11) ----------
const NODO = 170;
const NODO_RADIO = 32;
const NODOS_X = [300, 680, 1060];
const FILA_Y = 580;
const ROTULO_Y = 775;
const CUADRO_X = 1540; // el cuadrado de Tinkazo, cuarto lugar de la fila
const CUADRO = 260;

// wand-magic-sparkles, Font Awesome Free 6.7.2 solid (CC BY 4.0), el mismo SVG que usó la charla de
// octubre. No está en manim/comun/iconos: va acá para no tocar los íconos comunes.
const VARITA = {
  ancho: 576,
  alto: 512,
  d: "M234.7 42.7L197 56.8c-3 1.1-5 4-5 7.2s2 6.1 5 7.2l37.7 14.1L248.8 123c1.1 3 4 5 7.2 5s6.1-2 7.2-5l14.1-37.7L315 71.2c3-1.1 5-4 5-7.2s-2-6.1-5-7.2L277.3 42.7 263.2 5c-1.1-3-4-5-7.2-5s-6.1 2-7.2 5L234.7 42.7zM46.1 395.4c-18.7 18.7-18.7 49.1 0 67.9l34.6 34.6c18.7 18.7 49.1 18.7 67.9 0L529.9 116.5c18.7-18.7 18.7-49.1 0-67.9L495.3 14.1c-18.7-18.7-49.1-18.7-67.9 0L46.1 395.4zM484.6 82.6l-105 105-23.3-23.3 105-105 23.3 23.3zM7.5 117.2C3 118.9 0 123.2 0 128s3 9.1 7.5 10.8L64 160l21.2 56.5c1.7 4.5 6 7.5 10.8 7.5s9.1-3 10.8-7.5L128 160l56.5-21.2c4.5-1.7 7.5-6 7.5-10.8s-3-9.1-7.5-10.8L128 96 106.8 39.5C105.1 35 100.8 32 96 32s-9.1 3-10.8 7.5L64 96 7.5 117.2zm352 256c-4.5 1.7-7.5 6-7.5 10.8s3 9.1 7.5 10.8L416 416l21.2 56.5c1.7 4.5 6 7.5 10.8 7.5s9.1-3 10.8-7.5L480 416l56.5-21.2c4.5-1.7 7.5-6 7.5-10.8s-3-9.1-7.5-10.8L480 352l-21.2-56.5c-1.7-4.5-6-7.5-10.8-7.5s-9.1 3-10.8 7.5L416 352l-56.5 21.2z",
};

const Nodo: React.FC<{ cx: number; cy: number; entra: number; children: React.ReactNode }> = ({ cx, cy, entra, children }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      top: 0,
      width: 1920,
      height: 1080,
      transformOrigin: `${cx}px ${cy}px`,
      transform: `scale(${0.6 + 0.4 * entra})`,
      opacity: Math.min(1, 2 * entra),
    }}
  >
    <div
      style={{
        position: "absolute",
        left: cx - NODO / 2,
        top: cy - NODO / 2,
        width: NODO,
        height: NODO,
        boxSizing: "border-box",
        borderRadius: NODO_RADIO,
        border: `${GROSOR.trazo_normal}px solid ${COLOR.azul}`,
        background: COLOR.noche,
      }}
    />
    {children}
  </div>
);

const ICONO_NODO = Math.round(NODO * 0.45);

/** La varita, del mismo alto que los demás íconos del nodo. */
const Varita: React.FC<{ x: number; y: number }> = ({ x, y }) => {
  const w = (ICONO_NODO * VARITA.ancho) / VARITA.alto;
  return (
    <svg width={w} height={ICONO_NODO} viewBox={`0 0 ${VARITA.ancho} ${VARITA.alto}`} style={{ position: "absolute", left: x - w / 2, top: y - ICONO_NODO / 2 }}>
      <path d={VARITA.d} fill={COLOR.hueso} />
    </svg>
  );
};

/** La lista que viaja: una pastilla ámbar con tres renglones dibujados (los nombres). */
const ListaViaja: React.FC<{ x: number; y: number; escala: number; opacidad: number }> = ({ x, y, escala, opacidad }) => (
  <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: opacidad }}>
    <g transform={`translate(${x} ${y}) scale(${escala})`}>
      <rect x={-56} y={-38} width={112} height={76} rx={22} fill={COLOR.ambar} />
      <line x1={-30} y1={-17} x2={30} y2={-17} stroke={COLOR.tinta} strokeWidth={7} strokeLinecap="round" />
      <line x1={-30} y1={0} x2={30} y2={0} stroke={COLOR.tinta} strokeWidth={7} strokeLinecap="round" />
      <line x1={-30} y1={17} x2={12} y2={17} stroke={COLOR.tinta} strokeWidth={7} strokeLinecap="round" />
    </g>
  </svg>
);

/** El número de una razón: hueso en un círculo de acero2 con aro en hueso al 40 % (como D14 de octubre). */
const NumeroCirculo: React.FC<{ n: string; cx: number; cy: number; estilo?: Estilo }> = ({ n, cx, cy, estilo }) => {
  const d = 72;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${cx}px ${cy}px`, ...estilo }}>
      <div
        style={{
          position: "absolute",
          left: cx - d / 2,
          top: cy - d / 2,
          width: d,
          height: d,
          boxSizing: "border-box",
          borderRadius: "50%",
          background: COLOR.acero2,
          border: `${GROSOR.borde_fino}px solid ${conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo)}`,
        }}
      />
      <Texto x={cx} y={cy} tam="rotulo" alinear="centro">
        {n}
      </Texto>
    </div>
  );
};

/** Primer momento (en s del paso) en que la caminata pasa por x (la curva es monótona). */
function cuandoPasa(curva: (t: number) => number, x0: number, x1: number, x: number, retraso: number, dura: number): number {
  const objetivo = (x - x0) / (x1 - x0);
  for (let i = 0; i <= 400; i++) {
    const t = i / 400;
    if (curva(t) >= objetivo) return retraso + t * dura;
  }
  return retraso + dura;
}

// ---------- Posiciones de la llama en cada paso ----------
// D14.1: entra desde fuera del cuadro y queda con su centro en (960, 490): base en 640.
const L1 = { x0: -150, x1: 960, base: 640 };
const baseCentrada = (cy: number, escala: number) => cy + (ALTO_UNIDADES / 2) * PX_POR_UNIDAD * escala;
// D14.2: a la izquierda, a 0,8 (240 px), con su centro en (300, 560), a la altura de la razón del medio.
const L2 = { x1: 300, escala: 0.8, base: baseCentrada(560, 0.8) };
// D14.3: cruza la fila (centro en y 580, va de 0,8 a 0,6 mientras camina) y queda dentro del cuadrado a 0,55.
const L3 = { x1: CUADRO_X, escalaFila: 0.6, baseFila: baseCentrada(FILA_Y, 0.6), escalaCuadro: 0.55 };
/** Las tres razones de D14.2, centradas con la llama: y 410, 560 y 710. */
const RAZONES = { y0: 410, paso: 150, xCirculo: 560, xTexto: 640 } as const;

// ---------- Tiempos (s desde que empieza cada paso) ----------
const T1 = { logo: 0.1, camina: [0.35, 2.0], inclina: [2.4, 0.35], titulo: 2.55, lema: 3.0 } as const;
const T2 = { sale: 0.0, endereza: 0.0, vuelta1: [0.05, 0.25], camina: [0.25, 1.2], vuelta2: [1.45, 0.25], inclina: [1.7, 0.35], razones: 0.9, desfase: 0.3 } as const;
const T3 = {
  sale: 0.0,
  endereza: 0.0,
  camina: [0.1, 1.35],
  titulo: 0.3,
  cuadro: [1.35, 0.45],
  achica: [1.4, 0.4],
  inclina: [1.8, 0.3],
  conexiones: 1.55,
  conexion: 0.25,
  conexionDesfase: 0.2,
  rotuloTinkazo: 1.75,
  lista: [2.15, 0.65],
  listaEntra: [2.7, 0.15],
  late: [2.82, 0.35],
  camara: [2.1, 1.0],
} as const;

export const D14ElSorteo: React.FC = () => {
  const [titulo1, lema] = textos("D14", 1);
  const t2 = textos("D14", 2); // 1, frase, 2, frase, 3, frase
  const [titulo3, formulario, limpiar, guardar, web] = textos("D14", 3);

  // ---------- Paso 1 ----------
  const logoEntra = useEntrar(1, T1.logo, { desde: "arriba", distancia: 40 });
  const camina1 = useTramo(1, T1.camina[0], T1.camina[1], ENTRA_CAMINANDO);
  const inclina1 = useTramo(1, T1.inclina[0], T1.inclina[1], CURVA.suave);
  const palabras1 = useEntrarPalabras(titulo1, 1, T1.titulo);
  const lemaEntra = useEntrar(1, T1.lema);

  // ---------- Paso 2 ----------
  const saleTitulo = useSale(2, T2.sale, 0.3, CURVA.fundido);
  const endereza2 = useTramo(2, T2.endereza, 0.2, CURVA.suave);
  const vuelta1 = useTramo(2, T2.vuelta1[0], T2.vuelta1[1], CURVA.suave);
  const camina2 = useTramo(2, T2.camina[0], T2.camina[1], CURVA.suave);
  const vuelta2 = useTramo(2, T2.vuelta2[0], T2.vuelta2[1], CURVA.suave);
  const inclina2 = useTramo(2, T2.inclina[0], T2.inclina[1], CURVA.suave);
  const numeros = [0, 1, 2].map((i) => useGolpe(2, T2.razones + i * T2.desfase, { chico: true }));
  const frases = [0, 1, 2].map((i) => useEntrar(2, T2.razones + 0.05 + i * T2.desfase, { desde: "izq" }));

  // ---------- Paso 3 ----------
  const saleRazones = useSale(3, T3.sale, 0.3, CURVA.fundido);
  const saleLogo = useSale(3, T3.sale, 0.3, CURVA.fundido);
  const endereza3 = useTramo(3, T3.endereza, 0.15, CURVA.suave);
  const camina3 = useTramo(3, T3.camina[0], T3.camina[1], CURVA.suave);
  const palabras3 = useEntrarPalabras(titulo3, 3, T3.titulo);
  const cuadro = useEntra(3, T3.cuadro[0], T3.cuadro[1]);
  const achica = useTramo(3, T3.achica[0], T3.achica[1], CURVA.suave);
  const inclina3 = useTramo(3, T3.inclina[0], T3.inclina[1], CURVA.suave);
  // Cada nodo aparece cuando la llama ya lo pasó (su cola, unos 90 px más allá del centro).
  const entraNodo = NODOS_X.map((x) => cuandoPasa(CURVA.suave, L2.x1, L3.x1, x + 90, T3.camina[0], T3.camina[1]));
  const nodos = entraNodo.map((t) => useEntra(3, t, 0.4));
  const rotulos = entraNodo.map((t) => useEntrar(3, t + 0.08));
  const conexiones = [0, 1, 2].map((i) => useTramo(3, T3.conexiones + i * T3.conexionDesfase, T3.conexion, CURVA.suave));
  const rotuloWeb = useEntrar(3, T3.rotuloTinkazo);
  const listaAparece = useEntra(3, T3.lista[0] - 0.05, 0.25);
  const listaViaja = useTramo(3, T3.lista[0], T3.lista[1], CURVA.suave);
  const listaEntra = useTramo(3, T3.listaEntra[0], T3.listaEntra[1], CURVA.suave);
  const late = useTramo(3, T3.late[0], T3.late[1], CURVA.lineal);
  const camara = useTramo(3, T3.camara[0], T3.camara[1], CURVA.suave);

  // ---------- La llama: una sola, que va de paso en paso ----------
  let pose: PoseLlama;
  if (camina3 > 0 || saleRazones < 1) {
    // Paso 3: cruza la fila y entra al cuadrado.
    // Con 1.240 px por delante, trota con pasos más largos (unos 7 pasos en 1,35 s). Mientras camina
    // pasa de 0,8 (donde la dejó D14.2) a 0,6, y al llegar se achica a 0,55 dentro del cuadrado.
    const c = caminata(camina3, L2.x1, L3.x1, L2.escala, L3.escalaFila, 250);
    const escalaFila = L2.escala + (L3.escalaFila - L2.escala) * camina3;
    const escala = escalaFila + (L3.escalaCuadro - escalaFila) * achica;
    const baseFila = L2.base + (L3.baseFila - L2.base) * camina3;
    const base = baseFila + (baseCentrada(FILA_Y, escala) - baseCentrada(FILA_Y, escalaFila));
    pose = {
      cx: c.cx,
      base,
      escala,
      fase: c.fase,
      giro: INCLINACION * (1 - endereza3) + INCLINACION * inclina3,
      mira: 1,
      color: interpolateColors(achica, [0, 1], [MAGENTA_OSCURO, MAGENTA_CLARO]),
    };
  } else if (vuelta1 > 0 || saleTitulo < 1) {
    // Paso 2: media vuelta, camina a la izquierda achicándose, media vuelta y se inclina.
    const c = caminata(camina2, L1.x1, L2.x1, 1, L2.escala);
    pose = {
      cx: c.cx,
      base: L1.base + (L2.base - L1.base) * camina2,
      escala: c.escala,
      fase: c.fase,
      giro: INCLINACION * (1 - endereza2) + INCLINACION * inclina2,
      mira: vuelta2 > 0 ? -Math.cos(Math.PI * vuelta2) : Math.cos(Math.PI * vuelta1),
      color: MAGENTA_OSCURO,
    };
  } else {
    // Paso 1: entra caminando, frena y se inclina hacia la sala.
    const c = caminata(camina1, L1.x0, L1.x1, 1, 1);
    pose = { cx: c.cx, base: L1.base, escala: 1, fase: c.fase, giro: INCLINACION * inclina1, mira: 1, color: MAGENTA_OSCURO };
  }

  // ---------- La lista que viaja por la fila ----------
  const listaX = NODOS_X[0] + (CUADRO_X - NODOS_X[0]) * listaViaja;
  const listaEscala = (0.5 + 0.5 * listaAparece) * (1 - 0.6 * listaEntra);
  const listaOpacidad = Math.min(1, 3 * listaAparece) * (1 - listaEntra);

  // ---------- El cuadrado de Tinkazo ----------
  const latido = 1 + 0.06 * Math.sin(Math.PI * late);
  const escalaCuadro = (0.4 + 0.6 * cuadro) * latido;

  const zoom = 1 + 0.035 * camara;
  const bordeIzqCuadro = CUADRO_X - CUADRO / 2;
  const tramos: [number, number][] = [
    [NODOS_X[0] + NODO / 2, NODOS_X[1] - NODO / 2],
    [NODOS_X[1] + NODO / 2, NODOS_X[2] - NODO / 2],
    [NODOS_X[2] + NODO / 2, bordeIzqCuadro],
  ];
  const rotulosFila = [formulario, limpiar, guardar];
  const iconos = ["mobile-screen-button", null, "table"] as const;

  return (
    <>
    <FondoCircuito />
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${CUADRO_X - 130}px ${FILA_Y}px`, transform: `scale(${zoom})` }}>
      {/* El logo de Tinkazo, tal cual, arriba (pasos 1 y 2). */}
      <div style={{ position: "absolute", inset: 0, ...unir(logoEntra, { opacity: saleLogo }) }}>
        <Img
          src={staticFile("logos/tinkazo/logo-horizontal-oscuro.svg")}
          style={{ position: "absolute", left: 960 - LOGO_ANCHO / 2, top: LOGO_Y - LOGO_ALTO / 2, width: LOGO_ANCHO, height: LOGO_ALTO }}
        />
      </div>

      {/* Paso 1: el título y el lema. */}
      <div style={{ position: "absolute", inset: 0, opacity: saleTitulo }}>
        <Texto x={960} y={760} tam="grande" color={COLOR.titulo} alinear="centro" estiloPalabras={palabras1}>
          {titulo1}
        </Texto>
        <Texto x={960} y={860} tam="lectura" alinear="centro" estilo={lemaEntra}>
          {lema}
        </Texto>
      </div>

      {/* Paso 2: las tres razones. */}
      <div style={{ position: "absolute", inset: 0, opacity: saleRazones }}>
        {[0, 1, 2].map((i) => (
          <React.Fragment key={i}>
            <NumeroCirculo n={t2[2 * i]} cx={RAZONES.xCirculo} cy={RAZONES.y0 + RAZONES.paso * i} estilo={numeros[i]} />
            <Texto x={RAZONES.xTexto} y={RAZONES.y0 + RAZONES.paso * i} tam="lectura" resaltar={i === 2 ? "Cualquiera lo comprueba" : undefined} estilo={frases[i]}>
              {t2[2 * i + 1]}
            </Texto>
          </React.Fragment>
        ))}
      </div>

      {/* Paso 3: la lista la armó n8n y se la pasa a Tinkazo. */}
      <Texto x={960} y={280} tam="idea" color={COLOR.titulo} alinear="centro" estiloPalabras={palabras3}>
        {titulo3}
      </Texto>
      {tramos.map(([a, b], i) => (
        <Hilo key={i} d={`M ${a} ${FILA_Y} L ${b} ${FILA_Y}`} progreso={conexiones[i]} color={COLOR.azul} grosor={GROSOR.trazo_normal} />
      ))}
      {NODOS_X.map((x, i) => (
        <Nodo key={x} cx={x} cy={FILA_Y} entra={nodos[i]}>
          {iconos[i] ? <Icono nombre={iconos[i]!} alto={ICONO_NODO} x={x} y={FILA_Y} /> : <Varita x={x} y={FILA_Y} />}
        </Nodo>
      ))}
      {NODOS_X.map((x, i) => (
        <Texto key={`r${x}`} x={x} y={ROTULO_Y} tam="lectura" alinear="centro" estilo={rotulos[i]}>
          {rotulosFila[i]}
        </Texto>
      ))}
      {listaAparece > 0 && listaEntra < 1 && <ListaViaja x={listaX} y={FILA_Y} escala={listaEscala} opacidad={listaOpacidad} />}

      {cuadro > 0 && (
        <div
          style={{
            position: "absolute",
            left: CUADRO_X - CUADRO / 2,
            top: FILA_Y - CUADRO / 2,
            width: CUADRO,
            height: CUADRO,
            boxSizing: "border-box",
            background: PAPEL,
            border: `3px solid ${TINTA_MARCA}`,
            boxShadow: `8px 8px 0 ${TINTA_MARCA}`,
            transformOrigin: "50% 50%",
            transform: `scale(${escalaCuadro})`,
            opacity: Math.min(1, 3 * cuadro),
          }}
        />
      )}
      <Texto x={CUADRO_X} y={ROTULO_Y} tam="lectura" alinear="centro" estilo={rotuloWeb}>
        {web}
      </Texto>

      {/* La llama, encima de todo. */}
      <div style={{ position: "absolute", inset: 0, transformOrigin: `${CUADRO_X}px ${FILA_Y}px`, transform: `scale(${cuadro > 0 ? latido : 1})` }}>
        <Llama {...pose} />
      </div>
    </div>
    </>
  );
};
