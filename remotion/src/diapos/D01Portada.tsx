// D01 Portada (guion D01.1). La primera impresión: el encendido.
//
// Un solo paso de 5,0 s (respiro incluido: todo quieto desde los 4,45 s). Entra desde tinta (es el
// primer video): el cuadro 0 es tinta lisa. La animación cuenta algo que se enciende:
//   1. Oscuridad. Solo aparecen las estrellas, muy despacio.
//   2. Un dato ámbar entra desde el borde izquierdo y corre por una pista entre los dos renglones del
//      título. A su paso imprime las letras: cada una nace en hueso encendido y se asienta en el
//      amarillo del título. El segundo renglón lo sigue un poco atrás. La pista se apaga detrás.
//   3. Mientras tanto, a la derecha, los tres nodos y sus pistas se dibujan apagados (al 28 %). El dato
//      sube a la columna y los enciende de arriba abajo, uno por uno: borde a pleno, brillo azul, un
//      aro y un latido.
//   4. Con el tercero, una onda sale de la columna y recorre todas las pistas hacia afuera (una chispa
//      en el frente), las estrellas dan un respiro de luz y todo baja a su brillo final.
//   5. Ya con luz, entran la fila n8n + SerpApi + IA, el evento y la firma, y una franja de luz cruza
//      Dale superpoderes, una vez.
// Toda la escena se acerca un poco mientras llega (escala 0,965 a 1 con el centro del cuadro quieto)
// y las estrellas, fuera de esa cámara, se achican de 1,08 a 1: dos capas a distinta velocidad. Al
// terminar son exactamente las estrellas del PNG de las demás diapositivas, así el fundido a D02 no las
// mueve. El cuadro final es el mismo de la versión anterior, píxel por píxel.
//
// Cuadro final (deck D01.1), desde x 160 y alineado a la izquierda:
//   Dale superpoderes en titulo (amarillo lima) a 120 px en y 300 y a tus automatizaciones a 104 px en
//   y 425: los dos renglones son el único título del cuadro.
//   n8n + SerpApi + IA en y 575: los logos oficiales de n8n y de SerpApi a 64 px de alto, tal cual,
//   unidos por signos más en azul de 32 px, y IA en hueso a 72 px. Cada nodo queda con un brillo suave.
//   Space Talks en gris a 60 px en y 720 y el evento en gris a 49 px en y 790.
//   Firma en y 960: isotipo lima de 48 px y el nombre completo en hueso a 60 px.
//   A la derecha, tres nodos de 128 px en x 1640 (y 300, 470 y 640) con lupa, cerebro y engranajes,
//   unidos por conexiones azules de 5 px, y nueve pistas de circuito de 3 px en azul al 35 %, cada
//   una con su punto de 10 px: siete entran desde el borde derecho y dos salen de los nodos (por eso D01.1 tiene una excepción
//   de zona segura a la derecha en armar/auditoria_reglas.json).
// Sin marca de agua (tokens.json, persistentes.marca_agua_sin). El lima del isotipo está permitido:
// D01.1 está en pasos_de_marca.
//
// Sin logos de NASA Space Apps ni de la UCB: el deck los pide solo si llega el afiche o sus archivos.
//
// Tiempos (s desde el comienzo del paso):
//   0,00-1,80 aparecen las estrellas (muy despacio); 0,00-4,40 se achican de 1,08 a 1
//   0,50-1,80 el dato cruza el título y lo imprime (el segundo renglón, 90 px atrás)
//   0,70-1,50 los nodos, sus conexiones y las pistas aparecen apagados
//   2,05, 2,35 y 2,70 el dato enciende el primer, el segundo y el tercer nodo
//   2,74-3,85 la onda recorre las pistas hacia afuera y bajan a su brillo final; 2,72-3,62 el respiro
//             de luz de las estrellas
//   3,00-3,82 sube n8n + SerpApi + IA; 3,30-3,92 aparece el pie; 3,55-4,25 el isotipo se dibuja;
//   3,75-4,25 entra el nombre
//   3,95-4,45 una franja de luz cruza Dale superpoderes, una vez
//   0,00-4,40 el acercamiento
//
// Exporta NodoFlujo (el nodo de la charla), que usa también D02, y FondoCircuito (las pistas de la
// portada, muy tenues, debajo de todo), que usan D02 a D08 para que la charla parezca un solo lugar.
import React from "react";
import { Img, staticFile } from "remotion";
import {
  anchoIsotipo,
  Aro,
  BarridoLuz,
  brillo,
  Camara,
  Capa,
  COLOR,
  conAlfa,
  CURVA,
  filtroBrillo,
  DatoViajero,
  FondoVivo,
  GROSOR,
  Icono,
  Isotipo,
  pasosDe,
  PuntaLuz,
  Texto,
  textos,
  unir,
  useAparecer,
  useDestello,
  useEntrar,
  useTramo,
  type Estilo,
  type NombreIcono,
} from "../comun";

// El encendido pide 5,0 s (el deck decía 4,3): 4,7 s de animación y 0,3 s quietos.
export const pasos = pasosDe("D01", { 1: 5.0 });

// ---------------------------------------------------------------------------------------------
// El nodo de flujo de la charla (el del deck, el mismo en Remotion y en Manim): cuadrado
// redondeado relleno noche, borde azul de 5 px e ícono en hueso al 45 % del lado. El radio es el
// 16 % del lado (32 px en un nodo de 200).
// ---------------------------------------------------------------------------------------------
export const RADIO_NODO = 0.16;
export const ICONO_NODO = 0.45;

export type PropsNodo = {
  cx: number;
  cy: number;
  lado: number;
  icono?: NombreIcono;
  /** Un ícono dibujado a mano (en coordenadas del cuadro), si no hay uno en manim/comun/iconos. */
  iconoPropio?: React.ReactNode;
  /** Escala alrededor del centro (aparecer, latir). */
  escala?: number;
  opacidad?: number;
  colorBorde?: string;
  relleno?: string;
  grosor?: number;
  radio?: number;
  colorIcono?: string;
  opacidadIcono?: number;
  /** Brillo suave alrededor del nodo (0 a 1): el nodo encendido, por donde pasó el dato. */
  brillo?: number;
};

export const NodoFlujo: React.FC<PropsNodo> = ({
  cx,
  cy,
  lado,
  icono,
  iconoPropio,
  escala = 1,
  opacidad = 1,
  colorBorde = COLOR.azul,
  relleno = COLOR.noche,
  grosor = GROSOR.trazo_normal,
  radio,
  colorIcono = COLOR.hueso,
  opacidadIcono = 1,
  brillo = 0,
}) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      top: 0,
      width: 1920,
      height: 1080,
      opacity: opacidad,
      transform: escala !== 1 ? `scale(${escala})` : undefined,
      transformOrigin: `${cx}px ${cy}px`,
    }}
  >
    <div
      style={{
        position: "absolute",
        left: cx - lado / 2,
        top: cy - lado / 2,
        width: lado,
        height: lado,
        boxSizing: "border-box",
        borderRadius: radio ?? Math.round(RADIO_NODO * lado),
        border: `${grosor}px solid ${colorBorde}`,
        background: relleno,
        boxShadow: brillo > 0 ? `0 0 ${Math.round(lado * 0.3)}px ${Math.round(lado * 0.04)}px ${conAlfa(COLOR.azul, 0.5 * brillo)}` : undefined,
      }}
    />
    {icono && <Icono nombre={icono} alto={Math.round(ICONO_NODO * lado)} x={cx} y={cy} color={colorIcono} opacidad={opacidadIcono} />}
    {iconoPropio}
  </div>
);

/** Latido de un nodo: de 1 a 1,06 y de vuelta a 1 en `dura` s (el de la charla, sin cambiar de color). */
export function useLatido(paso: number, retraso: number, dura = 0.4, escala = 1.06): number {
  const p = useTramo(paso, retraso, dura, CURVA.lineal);
  return 1 + (escala - 1) * Math.sin(Math.PI * p);
}

// ---------------------------------------------------------------------------------------------
// El fondo de circuito: las pistas de la portada al 22 % que entran desde los bordes y se apagan antes
// de salir de la zona segura (diseno/medios/D01/generar_fondo.py). Va primero, debajo de todo. Manim
// pega el mismo PNG en su píxel (fondo_circuito() de manim/escenas/d05_que_es_un_flujo.py).
// ---------------------------------------------------------------------------------------------
export const FONDO_CIRCUITO = "medios/D01/fondo_circuito.png";

export const FondoCircuito: React.FC = () => (
  <Img src={staticFile(FONDO_CIRCUITO)} style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080 }} />
);

// ---------------------------------------------------------------------------------------------
// Polilíneas: el camino de las pistas y del dato.
// ---------------------------------------------------------------------------------------------
export type Punto = [number, number];

export function caminoDe(pts: Punto[]): string {
  return pts.map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
}

export function largoDe(pts: Punto[]): number {
  let l = 0;
  for (let i = 1; i < pts.length; i++) l += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return l;
}

/** El punto a la distancia `d` del comienzo de la polilínea (recortada a sus extremos). */
export function puntoEn(pts: Punto[], d: number): Punto {
  let resto = Math.max(0, d);
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const l = Math.hypot(x1 - x0, y1 - y0);
    if (resto <= l) return [x0 + ((x1 - x0) * resto) / l, y0 + ((y1 - y0) * resto) / l];
    resto -= l;
  }
  return pts[pts.length - 1];
}

// ---------------------------------------------------------------------------------------------
// La composición.
// ---------------------------------------------------------------------------------------------
const X = 160;
const Y = { titulo1: 300, titulo2: 425, sub: 575, lugar: 720, evento: 790, firma: 960 };
const ISOTIPO = 48;

const NODO = { x: 1640, ys: [300, 470, 640], lado: 128, iconos: ["magnifying-glass", "brain", "gears"] as NombreIcono[] };
const PAD = 10; // diámetro del punto donde termina cada pista
const BORDE_X = 2010; // las pistas arrancan fuera del cuadro (con la escala 0,965 el borde sigue tapado)
const PISTA_FINAL = 0.35; // opacidad con la que quedan las pistas (guion: el guiño al afiche)
const PISTA_ENCENDIDA = 0.95; // cuando pasa la onda
const PISTA_APAGADA = 0.14; // antes de la onda
const NODO_APAGADO = 0.28; // borde e ícono de un nodo antes de que llegue el dato

// Las pistas: tramos rectos y a 45 grados. Las siete primeras entran desde el borde derecho: tres
// desembocan en los nodos (su punto queda a 12 px del borde del nodo, como un pin) y cuatro terminan
// sueltas. Las dos últimas salen de los nodos hacia la izquierda. `desdeColumna`: la onda las recorre
// desde la columna hacia afuera (las siete primeras al revés de como están escritas).
const PISTAS: { pts: Punto[]; desdeColumna: boolean }[] = [
  { desdeColumna: false, pts: [[BORDE_X, 196], [1846, 196], [1742, 300], [1716, 300]] },
  { desdeColumna: false, pts: [[BORDE_X, 470], [1716, 470]] },
  { desdeColumna: false, pts: [[BORDE_X, 752], [1854, 752], [1742, 640], [1716, 640]] },
  { desdeColumna: false, pts: [[BORDE_X, 120], [1782, 120]] },
  { desdeColumna: false, pts: [[BORDE_X, 385], [1878, 385], [1838, 345], [1790, 345]] },
  { desdeColumna: false, pts: [[BORDE_X, 560], [1880, 560], [1840, 600], [1790, 600]] },
  { desdeColumna: false, pts: [[BORDE_X, 852], [1924, 852], [1862, 914], [1600, 914]] },
  { desdeColumna: true, pts: [[NODO.x, 236], [NODO.x, 196], [1584, 140], [1470, 140]] },
  { desdeColumna: true, pts: [[NODO.x, 704], [NODO.x, 756], [1576, 820], [1430, 820]] },
];
// La onda: sale del tercer nodo, llega a cada pista según su distancia y la recorre a velocidad pareja.
const ONDA = { t: 2.74, alcance: 1800, velocidad: 1100, baja: 0.5 };
const ONDA_PISTAS = PISTAS.map(({ pts, desdeColumna }) => {
  const camino: Punto[] = desdeColumna ? pts : [...pts].reverse();
  const largo = largoDe(camino);
  const [ox, oy] = camino[0];
  const retraso = ONDA.t + Math.hypot(ox - NODO.x, oy - NODO.ys[2]) / ONDA.alcance;
  return { camino, largo, retraso, dura: largo / ONDA.velocidad };
});

// El camino del dato: entra por la izquierda entre los dos renglones del título (y 376: debajo de
// las p de superpoderes, que bajan hasta y 368, y arriba de las t del segundo renglón, desde y 384),
// sube en diagonal al primer nodo, lo atraviesa y baja por los otros dos. Los nodos se dibujan
// encima, así que adentro de cada nodo el dato no se ve.
const Y_PISTA_TITULO = 376;
const RUTA: Punto[] = [[-60, Y_PISTA_TITULO], [1460, Y_PISTA_TITULO], [1536, 300], [NODO.x, 300], [NODO.x, 470], [NODO.x, 640]];
const LARGO_RUTA = largoDe(RUTA);
// Distancias a lo largo de la ruta donde el dato toca el borde de cada nodo.
const D_TOCA = [largoDe(RUTA.slice(0, 3)) + (1576 - 1536), largoDe(RUTA.slice(0, 4)) + 170 - 64, largoDe(RUTA.slice(0, 5)) + 170 - 64];
// Cuándo pasa por cada lugar: [s, distancia]. Cruza el título a velocidad pareja (37 px por cuadro)
// y frena al bajar por la columna: uno, dos y tres, el último un poco más esperado.
const T_IGN = [2.05, 2.35, 2.7];
const VIAJE: [number, number][] = [
  [0.5, 0],
  [1.8, 1440],
  [T_IGN[0], D_TOCA[0]],
  [T_IGN[1], D_TOCA[1]],
  [T_IGN[2], D_TOCA[2]],
  [2.8, LARGO_RUTA],
];
// El tramo que ilumina el dato detrás de sí (hasta el primer nodo): la pista que se apaga detrás.
const TRAZO_DATO: Punto[] = RUTA.slice(0, 4);
const COLA_TRAZO = [
  { largo: 520, alfa: 0.16 },
  { largo: 260, alfa: 0.3 },
  { largo: 90, alfa: 0.55 },
];
// La impresión del título: el borde de cada renglón va detrás del dato.
const IMPRESION = { atras1: 20, atras2: 90, caliente: 150, fin1: 1206, fin2: 1276 };

// Las conexiones entre nodos: [desde, hasta] a lo largo de la ruta (de borde a borde).
const D_CONEXION: [number, number][] = [
  [largoDe(RUTA.slice(0, 4)) + 64, D_TOCA[1]],
  [largoDe(RUTA.slice(0, 5)) + 64, D_TOCA[2]],
];

// El renglón n8n + SerpApi + IA con los logos oficiales tal cual (diseno/logos/FUENTES.md): el de n8n a
// la izquierda y unido al de SerpApi con un signo más que mide la mitad del alto del símbolo de n8n,
// como piden las reglas de marca de n8n. Los dos logos a 64 px de alto, IA en hueso a 72 px.
const LOGOS = {
  alto: 64,
  n8n: { src: "logos/n8n/n8n-logo-white-accent.svg", proporcion: 480 / 96 },
  serpapi: { src: "logos/serpapi/logo-with-wordmark-white.svg", proporcion: 1764 / 439 },
  mas: { lado: 32, grosor: 6 },
  aire: 36,
};

const Mas: React.FC<{ cx: number; cy: number; estilo: Estilo }> = ({ cx, cy, estilo }) => {
  const { lado, grosor } = LOGOS.mas;
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, ...estilo }}>
      <rect x={cx - lado / 2} y={cy - grosor / 2} width={lado} height={grosor} fill={COLOR.azul} />
      <rect x={cx - grosor / 2} y={cy - lado / 2} width={grosor} height={lado} fill={COLOR.azul} />
    </svg>
  );
};

/** n8n + SerpApi + IA: los dos logos, los dos signos más y la palabra IA (el último pedazo del texto). */
const FilaLogos: React.FC<{ texto: string; estilos: Estilo[] }> = ({ texto, estilos }) => {
  const ia = texto.split("+").pop()!.trim();
  const y = Y.sub;
  const h = LOGOS.alto;
  const wN8n = h * LOGOS.n8n.proporcion;
  const wSerp = h * LOGOS.serpapi.proporcion;
  const xMas1 = X + wN8n + LOGOS.aire + LOGOS.mas.lado / 2;
  const xSerp = xMas1 + LOGOS.mas.lado / 2 + LOGOS.aire;
  const xMas2 = xSerp + wSerp + LOGOS.aire + LOGOS.mas.lado / 2;
  const xIa = xMas2 + LOGOS.mas.lado / 2 + LOGOS.aire;
  const logo = (src: string, x: number, w: number, estilo: Estilo) => (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...estilo }}>
      <Img src={staticFile(src)} style={{ position: "absolute", left: x, top: y - h / 2, width: w, height: h }} />
    </div>
  );
  return (
    <>
      {logo(LOGOS.n8n.src, X, wN8n, estilos[0])}
      <Mas cx={xMas1} cy={y} estilo={estilos[1]} />
      {logo(LOGOS.serpapi.src, xSerp, wSerp, estilos[2])}
      <Mas cx={xMas2} cy={y} estilo={estilos[3]} />
      <Texto x={xIa} y={y} tam="frase" estilo={estilos[4]}>
        {ia}
      </Texto>
    </>
  );
};

/** Lo que se ve de un renglón a medida que se imprime: hasta `borde` (px) y con un borde suave. */
const Revelado: React.FC<{ mascara?: string; children: React.ReactNode }> = ({ mascara, children }) =>
  mascara === undefined ? (
    <>{children}</>
  ) : (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, WebkitMaskImage: mascara, maskImage: mascara }}>{children}</div>
  );

const mascaraAsentada = (borde: number) => `linear-gradient(90deg, #000 ${borde - 40}px, transparent ${borde - 10}px)`;
const mascaraCaliente = (borde: number) =>
  `linear-gradient(90deg, transparent ${borde - IMPRESION.caliente}px, #000 ${borde - 45}px, #000 ${borde - 28}px, transparent ${borde}px)`;

// Cuando el dato llega a cada nodo: un aro azul que sale de su borde. El del tercero es el más grande.
const AROS = [
  { hasta: 300, grosor: 4, dura: 0.5 },
  { hasta: 300, grosor: 4, dura: 0.5 },
  { hasta: 660, grosor: 5, dura: 0.75 },
];
// Una franja de luz cruza Dale superpoderes, una sola vez, cuando ya llegó todo lo demás.
const T_BARRIDO = { retraso: 3.95, dura: 0.5 };
// La cámara del contenido y las estrellas, que se achican mientras el contenido crece.
const CAMARA = { desde: 0.965, dura: 4.4 };
const ESTRELLAS = { aparece: 1.8, desde: 1.08 };
// El respiro de luz de las estrellas con la onda: las estrellas suben y la tinta del fondo queda igual.
const RESPIRO = { t: 2.72, dura: 0.9, sube: 1.7 };
// Las estrellas del PNG que en la portada quedan a menos de 26 px de una letra o del isotipo (medido en
// el cuadro final): se tapan con tinta solo acá. La que queda a media altura después de Agreda se leía
// como un punto, y las de arriba del nombre, como motas sobre las letras. [x, y, radio]
const ESTRELLAS_TAPADAS: [number, number, number][] = [
  [1017, 968, 8],
  [894, 933, 11],
  [503, 920, 11],
  [692, 921, 8],
  [820, 915, 8],
  [851, 925, 8],
  [156, 939, 8],
  [135, 978, 8],
];
// La tinta del fondo (#070A0F) en 0 a 1, para que el respiro no la aclare.
const TINTA_RGB = [7 / 255, 10 / 255, 15 / 255];

/** La distancia recorrida por el dato a los t s (lineal entre los puntos de VIAJE). */
function distanciaDato(t: number): number {
  if (t <= VIAJE[0][0]) return -1;
  for (let i = 1; i < VIAJE.length; i++) {
    const [t0, d0] = VIAJE[i - 1];
    const [t1, d1] = VIAJE[i];
    if (t <= t1) return d0 + ((d1 - d0) * (t - t0)) / (t1 - t0);
  }
  return LARGO_RUTA + 1;
}

const entre01 = (v: number) => Math.max(0, Math.min(1, v));
/** Un destello que ya terminó vale sin(pi), casi cero: se toma como cero para no dejar nada en el cuadro final. */
const casiCero = (v: number) => (v < 0.001 ? 0 : v);
// Hasta dónde corre el reloj del paso (el último tramo termina antes).
const RELOJ = 4.6;

export const D01Portada: React.FC = () => {
  // ["Dale superpoderes", "a tus automatizaciones", "n8n + SerpApi + IA", "Space Talks",
  //  "Hackathon NASA Space Apps 2026, Santa Cruz", "Nicolás Emir Mejía Agreda"]
  const [titulo1, titulo2, sub, lugar, evento, nombre] = textos("D01", 1);

  // El reloj del paso en segundos (de 0 a 4,6 s, después queda en 4,6).
  const t = RELOJ * useTramo(1, 0, RELOJ, CURVA.lineal);

  // Las estrellas: aparecen muy despacio desde tinta y se achican de 1,08 a 1 mientras el contenido se acerca.
  const opEstrellas = useTramo(1, 0, ESTRELLAS.aparece, CURVA.fundido);
  const escEstrellas = ESTRELLAS.desde - (ESTRELLAS.desde - 1) * useTramo(1, 0, CAMARA.dura, CURVA.sale);
  const respiro = casiCero(useDestello(1, RESPIRO.t, RESPIRO.dura));
  const pendiente = 1 + RESPIRO.sube * respiro;

  // Lo apagado (nodos, conexiones y pistas) aparece mientras se imprime el título.
  const apagado = useTramo(1, 0.7, 0.8, CURVA.fundido);

  // El dato.
  const dDato = distanciaDato(t);
  const progresoDato = dDato <= 0 ? 0 : dDato >= LARGO_RUTA ? 1 : dDato / LARGO_RUTA;
  const xDato = dDato <= 0 ? -1000 : puntoEn(RUTA, dDato)[0];
  // La pista del dato se apaga entera cuando el dato ya está en la columna.
  const trazoVivo = 1 - useTramo(1, 2.0, 0.6, CURVA.fundido);

  // La impresión del título: el borde de cada renglón y si ya terminó.
  const borde1 = xDato - IMPRESION.atras1;
  const borde2 = xDato - IMPRESION.atras2;
  const listo1 = borde1 - IMPRESION.caliente > IMPRESION.fin1 + 10;
  const listo2 = borde2 - IMPRESION.caliente > IMPRESION.fin2 + 10;

  // Los nodos: cada uno se enciende de golpe cuando el dato toca su borde.
  const encendidos = T_IGN.map((ti) => useTramo(1, ti, 0.12, CURVA.sale));
  const latidos = T_IGN.map((ti, i) => useLatido(1, ti - 0.02, i === 2 ? 0.45 : 0.35, i === 2 ? 1.14 : 1.1));
  const fogonazos = T_IGN.map((ti, i) => casiCero(useDestello(1, ti, i === 2 ? 0.7 : 0.5)));
  // Con la onda, los dos primeros acompañan con un fogonazo más chico.
  const ecos = [casiCero(useDestello(1, ONDA.t + 0.02, 0.5)), casiCero(useDestello(1, ONDA.t + 0.06, 0.5))];

  // Las conexiones: se encienden detrás del dato.
  const conexiones = D_CONEXION.map(([d0, d1]) => entre01((dDato - d0) / (d1 - d0)));

  // La onda por las pistas: la cabeza avanza y lo encendido baja a su opacidad final.
  const cabezas = ONDA_PISTAS.map((o) => useTramo(1, o.retraso, o.dura, CURVA.sale));
  const bajadas = ONDA_PISTAS.map((o) => useTramo(1, o.retraso + 0.6 * o.dura, ONDA.baja, CURVA.fundido));
  const brilloOnda = 1 - useTramo(1, ONDA.t + 0.45, 0.6, CURVA.fundido);

  // El texto que acompaña, ya con luz.
  const estFila = [0, 1, 2, 3, 4].map((i) => useEntrar(1, 3.0 + i * 0.08, { dura: 0.5 }));
  const estLugar = unir(useAparecer(1, 3.3, 0.4), useEntrar(1, 3.3, { dura: 0.5, distancia: 24 }));
  const estEvento = unir(useAparecer(1, 3.42, 0.4), useEntrar(1, 3.42, { dura: 0.5, distancia: 24 }));
  const isotipo = useTramo(1, 3.55, 0.7, CURVA.suave);
  const estNombre = useEntrar(1, 3.75, { dura: 0.5, desde: "izq" });
  const xNombre = X + anchoIsotipo(ISOTIPO) + Math.round(0.45 * ISOTIPO);

  // Cada palabra del título queda como la dejaba la entrada palabra por palabra de antes: así el cuadro
  // final es el mismo.
  const quieto = (texto: string): Estilo[] => (texto.match(/\S+/g) ?? []).map(() => ({ opacity: 1, transform: "translate(0px, 0px)" }));
  const palabras1 = quieto(titulo1);
  const palabras2 = quieto(titulo2);
  const caliente: Estilo = { textShadow: `0 0 18px ${conAlfa(COLOR.ambar, 0.85)}, 0 0 4px ${conAlfa(COLOR.hueso, 0.9)}` };

  const azul = (alfa: number) => conAlfa(COLOR.azul, alfa);
  const filtroRespiro = respiro > 0 ? "url(#d01-respiro)" : undefined;
  // La onda está viva mientras alguna pista no llegó a su estado final.
  const ondaViva = cabezas.some((c, i) => c > 0 && !(c >= 1 && bajadas[i] >= 1));

  return (
    <>
      {respiro > 0 && (
        <svg width={0} height={0} style={{ position: "absolute" }}>
          <filter id="d01-respiro" colorInterpolationFilters="sRGB">
            <feComponentTransfer>
              <feFuncR type="linear" slope={pendiente} intercept={-(pendiente - 1) * TINTA_RGB[0]} />
              <feFuncG type="linear" slope={pendiente} intercept={-(pendiente - 1) * TINTA_RGB[1]} />
              <feFuncB type="linear" slope={pendiente} intercept={-(pendiente - 1) * TINTA_RGB[2]} />
            </feComponentTransfer>
          </filter>
        </svg>
      )}
      {/* Las estrellas, debajo de todo y fuera de la cámara: se achican mientras el contenido crece. */}
      <Capa
        estilo={{ opacity: opEstrellas, transform: escEstrellas !== 1 ? `scale(${escEstrellas})` : undefined, filter: filtroRespiro }}
        origen={[960, 540]}
      >
        <FondoVivo variante="estrellas" />
        <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
          {ESTRELLAS_TAPADAS.map(([x, y, r]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r={r} fill={COLOR.tinta} />
          ))}
        </svg>
      </Capa>
      <Camara paso={1} desde={CAMARA.desde} dura={CAMARA.dura} origen={[960, 540]}>
        {/* Las pistas de circuito, con su punto al final: apagadas, encendidas por la onda y en su brillo final. */}
        <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
          {PISTAS.map(({ pts }, i) => {
            const o = ONDA_PISTAS[i];
            const largo = largoDe(pts);
            const [px, py] = pts[pts.length - 1];
            const cabeza = cabezas[i];
            const alfaEncendida = PISTA_ENCENDIDA + (PISTA_FINAL - PISTA_ENCENDIDA) * bajadas[i];
            if (cabeza >= 1 && bajadas[i] >= 1) {
              // El cuadro final: la pista tal cual quedaba antes.
              return (
                <g key={i}>
                  <path
                    d={caminoDe(pts)}
                    fill="none"
                    stroke={azul(PISTA_FINAL)}
                    strokeWidth={GROSOR.trazo_fino}
                    strokeLinejoin="miter"
                    strokeLinecap="butt"
                    strokeDasharray={largo}
                    strokeDashoffset={0}
                  />
                  <circle cx={px} cy={py} r={PAD / 2} fill={azul(PISTA_FINAL)} />
                </g>
              );
            }
            if (apagado <= 0) return null;
            const hecho = cabeza * o.largo;
            const alfaApagada = PISTA_APAGADA * apagado;
            // El punto: del lado de la columna se enciende cuando arranca la onda, del otro cuando llega.
            const puntoEncendido = o.camino[0][0] === px && o.camino[0][1] === py ? cabeza > 0 : cabeza >= 1;
            return (
              <g key={i}>
                {hecho < o.largo && (
                  <path
                    d={caminoDe(o.camino)}
                    fill="none"
                    stroke={azul(alfaApagada)}
                    strokeWidth={GROSOR.trazo_fino}
                    strokeLinejoin="miter"
                    strokeLinecap="butt"
                    strokeDasharray={`0 ${hecho} ${o.largo - hecho} ${o.largo * 3}`}
                  />
                )}
                <circle cx={px} cy={py} r={PAD / 2} fill={azul(puntoEncendido ? alfaEncendida : alfaApagada)} />
              </g>
            );
          })}
          {/* Las conexiones entre nodos: apagadas y encendidas por el dato; al final, azul pleno de 5 px. */}
          {[0, 1].map((i) => {
            const y0 = NODO.ys[i] + NODO.lado / 2;
            const y1 = NODO.ys[i + 1] - NODO.lado / 2;
            const k = conexiones[i];
            if (k >= 1) return <line key={`c${i}`} x1={NODO.x} y1={y0} x2={NODO.x} y2={y1} stroke={COLOR.azul} strokeWidth={GROSOR.trazo_normal} />;
            if (apagado <= 0) return null;
            return (
              <g key={`c${i}`}>
                <line x1={NODO.x} y1={y0 + (y1 - y0) * k} x2={NODO.x} y2={y1} stroke={azul(NODO_APAGADO * apagado)} strokeWidth={GROSOR.trazo_normal} />
                {k > 0 && <line x1={NODO.x} y1={y0} x2={NODO.x} y2={y0 + (y1 - y0) * k} stroke={COLOR.azul} strokeWidth={GROSOR.trazo_normal} />}
              </g>
            );
          })}
          {/* La pista por la que corre el dato: se ve solo detrás de él y se apaga. */}
          {dDato > 0 &&
            trazoVivo > 0 &&
            COLA_TRAZO.map(({ largo: l, alfa }) => {
              const largoTrazo = largoDe(TRAZO_DATO);
              const b = Math.min(dDato, largoTrazo);
              const a = Math.max(0, dDato - l);
              if (b - a <= 0.5) return null;
              return (
                <path
                  key={l}
                  d={caminoDe(TRAZO_DATO)}
                  fill="none"
                  stroke={azul(alfa * trazoVivo)}
                  strokeWidth={GROSOR.trazo_fino}
                  strokeLinejoin="miter"
                  strokeLinecap="butt"
                  strokeDasharray={`0 ${a} ${b - a} ${largoTrazo * 3}`}
                />
              );
            })}
        </svg>
        {/* Lo que la onda ya encendió, con brillo mientras pasa. */}
        {ondaViva && (
          <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", filter: filtroBrillo(COLOR.azul, brilloOnda) }}>
            {ONDA_PISTAS.map((o, i) => {
              if (cabezas[i] >= 1 && bajadas[i] >= 1) return null;
              const hecho = cabezas[i] * o.largo;
              if (hecho <= 0) return null;
              return (
                <path
                  key={i}
                  d={caminoDe(o.camino)}
                  fill="none"
                  stroke={azul(PISTA_ENCENDIDA + (PISTA_FINAL - PISTA_ENCENDIDA) * bajadas[i])}
                  strokeWidth={GROSOR.trazo_fino}
                  strokeLinejoin="miter"
                  strokeLinecap="butt"
                  strokeDasharray={`${hecho} ${o.largo * 3}`}
                />
              );
            })}
          </svg>
        )}
        {/* La chispa en el frente de la onda, en cada pista. */}
        {ONDA_PISTAS.map((o, i) => (
          <PuntaLuz key={`p${i}`} d={caminoDe(o.camino)} progreso={cabezas[i]} radio={8} />
        ))}
        {/* El dato ámbar con brillo y estela (debajo de los nodos: adentro de un nodo no se ve). */}
        <DatoViajero d={caminoDe(RUTA)} progreso={progresoDato} radio={11} estela={4} />

        {NODO.ys.map((y, i) => {
          const enc = encendidos[i];
          const op = apagado;
          if (op <= 0) return null;
          const esc = latidos[i];
          const alfaBorde = NODO_APAGADO + (1 - NODO_APAGADO) * enc;
          const k = 0.45 * enc;
          const golpe = Math.max(fogonazos[i], i < 2 ? 0.7 * ecos[i] : 0);
          return (
            <React.Fragment key={y}>
              {/* El brillo azul del nodo encendido, en un div con la misma forma, debajo del nodo. */}
              <div
                style={{
                  position: "absolute",
                  left: NODO.x - NODO.lado / 2,
                  top: y - NODO.lado / 2,
                  width: NODO.lado,
                  height: NODO.lado,
                  borderRadius: Math.round(RADIO_NODO * NODO.lado),
                  boxShadow: brillo(COLOR.azul, k * op),
                  transform: esc !== 1 ? `scale(${esc})` : undefined,
                }}
              />
              {golpe > 0 && (
                <div
                  style={{
                    position: "absolute",
                    left: NODO.x - NODO.lado / 2,
                    top: y - NODO.lado / 2,
                    width: NODO.lado,
                    height: NODO.lado,
                    borderRadius: Math.round(RADIO_NODO * NODO.lado),
                    boxShadow: brillo(COLOR.azul, golpe, i === 2 ? 2.2 : 1.6),
                    transform: esc !== 1 ? `scale(${esc})` : undefined,
                  }}
                />
              )}
              <NodoFlujo
                cx={NODO.x}
                cy={y}
                lado={NODO.lado}
                icono={NODO.iconos[i]}
                escala={esc}
                opacidad={op}
                colorBorde={alfaBorde >= 1 ? COLOR.azul : azul(alfaBorde)}
                opacidadIcono={alfaBorde >= 1 ? 1 : alfaBorde}
              />
            </React.Fragment>
          );
        })}
        {NODO.ys.map((y, i) => (
          <Aro
            key={`a${i}`}
            paso={1}
            retraso={T_IGN[i]}
            cx={NODO.x}
            cy={y}
            desde={NODO.lado}
            hasta={AROS[i].hasta}
            radioEsquina={0.5}
            color={COLOR.azul}
            grosor={AROS[i].grosor}
            dura={AROS[i].dura}
          />
        ))}

        {/* El título: asentado en amarillo detrás del borde, y caliente en hueso justo detrás del dato. */}
        <Revelado mascara={listo1 ? undefined : mascaraAsentada(borde1)}>
          <BarridoLuz paso={1} retraso={T_BARRIDO.retraso} dura={T_BARRIDO.dura}>
            <Texto x={X} y={Y.titulo1} tam="titulo" color={COLOR.titulo} estiloPalabras={palabras1}>
              {titulo1}
            </Texto>
          </BarridoLuz>
        </Revelado>
        {!listo1 && (
          <Revelado mascara={mascaraCaliente(borde1)}>
            <Texto x={X} y={Y.titulo1} tam="titulo" color={COLOR.hueso} estiloPalabras={palabras1} estilo={caliente}>
              {titulo1}
            </Texto>
          </Revelado>
        )}
        <Revelado mascara={listo2 ? undefined : mascaraAsentada(borde2)}>
          <Texto x={X} y={Y.titulo2} tam="grande" color={COLOR.titulo} estiloPalabras={palabras2}>
            {titulo2}
          </Texto>
        </Revelado>
        {!listo2 && (
          <Revelado mascara={mascaraCaliente(borde2)}>
            <Texto x={X} y={Y.titulo2} tam="grande" color={COLOR.hueso} estiloPalabras={palabras2} estilo={caliente}>
              {titulo2}
            </Texto>
          </Revelado>
        )}
        <FilaLogos texto={sub} estilos={estFila} />
        <Texto x={X} y={Y.lugar} tam="lectura" color={COLOR.gris} estilo={estLugar}>
          {lugar}
        </Texto>
        <Texto x={X} y={Y.evento} tam="rotulo" color={COLOR.gris} estilo={estEvento}>
          {evento}
        </Texto>
        <Isotipo alto={ISOTIPO} x={X} y={Y.firma - ISOTIPO / 2} progreso={isotipo} />
        <Texto x={xNombre} y={Y.firma} tam="lectura" estilo={estNombre}>
          {nombre}
        </Texto>
      </Camara>
    </>
  );
};
