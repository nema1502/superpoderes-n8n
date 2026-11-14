// D01 Portada (guion D01.1). La primera impresión: queda quieta en pantalla mientras entra la gente.
//
// Un solo paso de 4,3 s (respiro incluido: todo quieto desde los 4,0 s). Entra desde tinta (es el
// primer video): el cuadro 0 es tinta lisa. La animación es la llegada: un circuito azul entra desde
// el borde derecho, se enciende y se apaga al 35 % (el guiño al afiche), desemboca en tres nodos (ver,
// pensar y hacer), un dato ámbar los recorre y, a la izquierda, cae el título palabra por palabra.
// Toda la escena se acerca un poco mientras llega (escala 0,965 a 1 con el centro del cuadro quieto).
// Debajo de todo, fuera de esa cámara, las estrellas del fondo de la charla aparecen y se achican de
// 1,08 a 1 al mismo tiempo: dos capas a distinta velocidad (el paralaje). Al terminar son exactamente
// las estrellas del PNG de las demás diapositivas, así el fundido a D02 no las mueve.
//
// Cuadro final (deck D01.1), desde x 160 y alineado a la izquierda:
//   Dale superpoderes en titulo (amarillo lima) a 120 px en y 300 y a tus automatizaciones a 104 px en
//   y 425: los dos renglones son el único título del cuadro.
//   n8n + SerpApi + IA en y 575: los logos oficiales de n8n y de SerpApi a 64 px de alto, tal cual,
//   unidos por signos más en azul de 32 px, y IA en hueso a 72 px. Cada nodo queda con un brillo suave
//   después de que pasa el dato.
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
//   0,00-0,80 aparecen las estrellas; 0,00-3,60 se achican de 1,08 a 1
//   0,00-0,86 las pistas se dibujan desde el borde (0,5 s cada una, desfase 0,06 s), con una chispa
//             en la punta, y bajan al 35 % en 0,9 s; 0,80-1,45 salen dos pistas más de los nodos
//   0,45-1,05 los nodos aparecen cuando su pista llega; 0,85-1,15 se dibujan las conexiones
//   0,55-1,51 el título cae palabra por palabra (desfase 0,12 s)
//   1,30-2,30 el dato ámbar, con brillo y estela, recorre la pista del primer nodo y baja por los
//             tres; cada nodo late y se enciende con un brillo azul
//   2,25-2,75 el dato llega al tercer nodo: un aro azul sale de él y su brillo da un fogonazo
//   1,70-2,20 sube n8n + SerpApi + IA
//   2,30-2,90 aparece el pie; 2,70-3,50 el isotipo se dibuja; 2,95-3,45 entra el nombre
//   3,00-3,50 una franja de luz cruza Dale superpoderes, una vez
//   0,00-3,60 el acercamiento
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
  DatoViajero,
  FondoVivo,
  GROSOR,
  Icono,
  Isotipo,
  MOV,
  pasosDe,
  PuntaLuz,
  Texto,
  textos,
  unir,
  useAparecer,
  useDestello,
  useEntra,
  useEntrar,
  useEntrarPalabras,
  useTramo,
  type Estilo,
  type NombreIcono,
} from "../comun";

export const pasos = pasosDe("D01");

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
const PISTA_ENCENDIDA = 0.85; // mientras se dibujan

// Las pistas: tramos rectos y a 45 grados, cada una con el segundo en que empieza a dibujarse. Las
// siete primeras entran desde el borde derecho: tres desembocan en los nodos (su punto queda a 12 px
// del borde del nodo, como un pin) y cuatro terminan sueltas. Las dos últimas salen de los nodos
// hacia la izquierda cuando los nodos ya están, para que el circuito abrace la columna.
const PISTAS: { pts: Punto[]; t: number }[] = [
  { t: 0.0, pts: [[BORDE_X, 196], [1846, 196], [1742, 300], [1716, 300]] },
  { t: 0.06, pts: [[BORDE_X, 470], [1716, 470]] },
  { t: 0.12, pts: [[BORDE_X, 752], [1854, 752], [1742, 640], [1716, 640]] },
  { t: 0.18, pts: [[BORDE_X, 120], [1782, 120]] },
  { t: 0.24, pts: [[BORDE_X, 385], [1878, 385], [1838, 345], [1790, 345]] },
  { t: 0.3, pts: [[BORDE_X, 560], [1880, 560], [1840, 600], [1790, 600]] },
  { t: 0.36, pts: [[BORDE_X, 852], [1924, 852], [1862, 914], [1600, 914]] },
  { t: 0.8, pts: [[NODO.x, 236], [NODO.x, 196], [1584, 140], [1470, 140]] },
  { t: 0.95, pts: [[NODO.x, 704], [NODO.x, 756], [1576, 820], [1430, 820]] },
];
const T_PISTA = { dura: 0.5, baja: 0.9 };

// El camino del dato: entra por la pista del primer nodo, lo atraviesa y baja por los otros dos. Los
// nodos se dibujan encima, así que adentro de cada nodo el dato no se ve.
const RUTA: Punto[] = [[1960, 196], [1846, 196], [1742, 300], [NODO.x, 300], [NODO.x, 470], [NODO.x, 640]];

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
const T_DATO = { retraso: 1.3, dura: 1.0 };
const ESTELA_DATO = 5; // círculos de estela detrás del dato
// Cuando el dato llega al tercer nodo: un aro azul de 4 px que sale de su borde (círculo de 128 a
// 520 px de lado) y un fogonazo en su brillo.
const T_ARO = { retraso: 2.25, dura: 0.5, hasta: 520, grosor: 4, fogonazo: 0.3 };
// Una franja de luz cruza Dale superpoderes, una sola vez, cuando ya llegó todo lo demás.
const T_BARRIDO = { retraso: 3.0, dura: 0.5 };
// La cámara del contenido y las estrellas, que se achican mientras el contenido crece.
const CAMARA = { desde: 0.965, dura: 3.6 };
const ESTRELLAS = { aparece: 0.8, desde: 1.08 };
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

export const D01Portada: React.FC = () => {
  // ["Dale superpoderes", "a tus automatizaciones", "n8n + SerpApi + IA", "Space Talks",
  //  "Hackathon NASA Space Apps 2026, Santa Cruz", "Nicolás Emir Mejía Agreda"]
  const [titulo1, titulo2, sub, lugar, evento, nombre] = textos("D01", 1);

  // Las estrellas: aparecen desde tinta y se achican de 1,08 a 1 mientras el contenido se acerca.
  const opEstrellas = useTramo(1, 0, ESTRELLAS.aparece, CURVA.fundido);
  const escEstrellas = ESTRELLAS.desde - (ESTRELLAS.desde - 1) * useTramo(1, 0, CAMARA.dura, CURVA.sale);

  // Las pistas: se dibujan encendidas y bajan al 35 %.
  const dibujo = PISTAS.map((q) => useTramo(1, q.t, T_PISTA.dura, CURVA.sale));
  const baja = PISTAS.map((q) => useTramo(1, q.t + T_PISTA.dura - 0.05, T_PISTA.baja, CURVA.fundido));
  const puntos = PISTAS.map((q) => useEntra(1, q.t + T_PISTA.dura - 0.08, 0.3));

  // Los nodos aparecen cuando su pista llega (de 0,6 a 1 con fundido), y las conexiones entre ellos.
  const nodos = NODO.ys.map((_, i) => useEntra(1, 0.45 + i * 0.15, 0.45));
  const conexiones = [useTramo(1, 0.85, 0.3, CURVA.suave), useTramo(1, 0.95, 0.3, CURVA.suave)];

  // El dato: velocidad pareja con la curva suave, y cada nodo late cuando el dato llega a su centro.
  // Con progreso 0 o 1 el dato no se ve (al final queda debajo del tercer nodo).
  const ruta = largoDe(RUTA);
  const avance = useTramo(1, T_DATO.retraso, T_DATO.dura, CURVA.suave);
  // Cuándo pasa por el centro de cada nodo (invirtiendo la curva suave por bisección).
  const llegada = (d: number) => {
    let a = 0;
    let b = 1;
    for (let k = 0; k < 30; k++) {
      const m = (a + b) / 2;
      if (CURVA.suave(m) * ruta < d) a = m;
      else b = m;
    }
    return T_DATO.retraso + a * T_DATO.dura;
  };
  const dCentro = [largoDe(RUTA.slice(0, 4)), largoDe(RUTA.slice(0, 5)), ruta];
  const latidos = [useLatido(1, llegada(dCentro[0]) - 0.1), useLatido(1, llegada(dCentro[1]) - 0.1), useLatido(1, llegada(dCentro[2]) - 0.12)];
  // Cada nodo se enciende cuando el dato lo atraviesa y queda con un brillo suave.
  const llegadas = [llegada(dCentro[0]) - 0.1, llegada(dCentro[1]) - 0.1, llegada(dCentro[2]) - 0.12];
  const encendidos = llegadas.map((t) => useTramo(1, t, 0.4, CURVA.sale));
  const brillos = latidos.map((l, i) => Math.max(Math.min(1, (l - 1) / 0.06), 0.45 * encendidos[i]));
  // El dato llega al tercer nodo: fogonazo en su brillo (el aro va en el JSX).
  const fogonazo = useDestello(1, T_ARO.retraso, T_ARO.fogonazo);

  // El texto.
  const desfase = MOV.desfase.palabras;
  const palabras1 = useEntrarPalabras(titulo1, 1, 0.55, { desfase, dura: 0.5, desde: "arriba", distancia: MOV.distancia.xyz });
  const n1 = (titulo1.match(/\S+/g) ?? []).length;
  const palabras2 = useEntrarPalabras(titulo2, 1, 0.55 + n1 * desfase, { desfase, dura: 0.5, desde: "arriba", distancia: MOV.distancia.xyz });
  const estFila = [0, 1, 2, 3, 4].map((i) => useEntrar(1, 1.7 + i * 0.08, { dura: 0.5 }));
  const estLugar = unir(useAparecer(1, 2.3, 0.4), useEntrar(1, 2.3, { dura: 0.5, distancia: 24 }));
  const estEvento = unir(useAparecer(1, 2.45, 0.4), useEntrar(1, 2.45, { dura: 0.5, distancia: 24 }));
  const isotipo = useTramo(1, 2.7, 0.8, CURVA.suave);
  const estNombre = useEntrar(1, 2.95, { dura: 0.5, desde: "izq" });
  const xNombre = X + anchoIsotipo(ISOTIPO) + Math.round(0.45 * ISOTIPO);

  const azul = (alfa: number) => conAlfa(COLOR.azul, alfa);

  return (
    <>
      {/* Las estrellas, debajo de todo y fuera de la cámara: se achican mientras el contenido crece. */}
      <Capa estilo={{ opacity: opEstrellas, transform: escEstrellas !== 1 ? `scale(${escEstrellas})` : undefined }} origen={[960, 540]}>
        <FondoVivo variante="estrellas" />
        <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
          {ESTRELLAS_TAPADAS.map(([x, y, r]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r={r} fill={COLOR.tinta} />
          ))}
        </svg>
      </Capa>
      <Camara paso={1} desde={CAMARA.desde} dura={CAMARA.dura} origen={[960, 540]}>
      {/* Las pistas de circuito, con su punto al final. */}
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        {PISTAS.map(({ pts }, i) => {
          const largo = largoDe(pts);
          const alfa = PISTA_ENCENDIDA + (PISTA_FINAL - PISTA_ENCENDIDA) * baja[i];
          const [px, py] = pts[pts.length - 1];
          return (
            <g key={i}>
              {dibujo[i] > 0 && (
                <path
                  d={caminoDe(pts)}
                  fill="none"
                  stroke={azul(alfa)}
                  strokeWidth={GROSOR.trazo_fino}
                  strokeLinejoin="miter"
                  strokeLinecap="butt"
                  strokeDasharray={largo}
                  strokeDashoffset={largo * (1 - dibujo[i])}
                />
              )}
              {puntos[i] > 0 && <circle cx={px} cy={py} r={(PAD / 2) * puntos[i]} fill={azul(alfa)} />}
            </g>
          );
        })}
        {/* Las conexiones entre nodos: azul pleno de 5 px, de borde a borde. */}
        {[0, 1].map((i) => {
          const y0 = NODO.ys[i] + NODO.lado / 2;
          const y1 = NODO.ys[i + 1] - NODO.lado / 2;
          return conexiones[i] > 0 ? (
            <line key={`c${i}`} x1={NODO.x} y1={y0} x2={NODO.x} y2={y0 + (y1 - y0) * conexiones[i]} stroke={COLOR.azul} strokeWidth={GROSOR.trazo_normal} />
          ) : null;
        })}
      </svg>
      {/* La chispa en la punta de cada pista mientras se dibuja. */}
      {PISTAS.map(({ pts }, i) => (
        <PuntaLuz key={`p${i}`} d={caminoDe(pts)} progreso={dibujo[i]} />
      ))}
      {/* El dato ámbar con brillo y estela (debajo de los nodos: adentro de un nodo no se ve). */}
      <DatoViajero d={caminoDe(RUTA)} progreso={avance} estela={ESTELA_DATO} />

      {NODO.ys.map((y, i) => {
        const esc = (0.6 + 0.4 * nodos[i]) * latidos[i];
        const op = Math.min(1, 1.6 * nodos[i]);
        const k = Math.max(brillos[i], i === 2 ? fogonazo : 0);
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
            <NodoFlujo cx={NODO.x} cy={y} lado={NODO.lado} icono={NODO.iconos[i]} escala={esc} opacidad={op} />
          </React.Fragment>
        );
      })}
      <Aro
        paso={1}
        retraso={T_ARO.retraso}
        cx={NODO.x}
        cy={NODO.ys[2]}
        desde={NODO.lado}
        hasta={T_ARO.hasta}
        radioEsquina={0.5}
        color={COLOR.azul}
        grosor={T_ARO.grosor}
        dura={T_ARO.dura}
      />

      <BarridoLuz paso={1} retraso={T_BARRIDO.retraso} dura={T_BARRIDO.dura}>
        <Texto x={X} y={Y.titulo1} tam="titulo" color={COLOR.titulo} estiloPalabras={palabras1}>
          {titulo1}
        </Texto>
      </BarridoLuz>
      <Texto x={X} y={Y.titulo2} tam="grande" color={COLOR.titulo} estiloPalabras={palabras2}>
        {titulo2}
      </Texto>
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
