// D09 Demo 1: ¿Ya existe tu nombre? (contenido/guion.md, D09). La primera demo en vivo: un flujo
// en línea recta que ve (busca el nombre en Google con SerpApi) y piensa (el modelo da un
// veredicto con pruebas).
//
//   D09.1  La tarjeta de la demo: la pastilla Demo 1, el nombre del flujo, la frase y el flujo
//          (Formulario, Google, Modelo, Veredicto). El dato lo recorre una vez, Veredicto queda
//          encendido y abajo sale lo que devolvió el flujo en el ensayo: Satelitazo, LIBRE y los
//          otros nombres (workflows/muestras/flujo1-satelitazo.json, tal cual).
//   D09.2  La lección: la frase y la salida se van, el flujo se aleja y pasa a Foco, y sube Línea
//          recta: primero ve, después piensa.
//
// El flujo sale de workflows/ESPEC.md (flujo 1), dibujado con el nodo de la charla.
// La tarjeta de demo (de TARJETA hasta FlujoQueSeAleja) es la misma pieza en D09, D10 y D11,
// copiada igual en los tres archivos: si cambia en uno, se copia a los otros dos.
// Debajo de todo va el fondo de circuito de la charla
// (FondoCircuito de D01Portada.tsx), el mismo de D02 a D15.
import { evolvePath, getLength, getPointAtLength } from "@remotion/paths";
import React from "react";
import { FondoCircuito } from "./D01Portada";
import {
  anchoIcono,
  Capa,
  COLOR,
  conAlfa,
  CURVA,
  Foco,
  GROSOR,
  Icono,
  medidasPastilla,
  medirTexto,
  mezclar,
  MOV,
  pasosDe,
  Pastilla,
  RADIO,
  Texto,
  textos,
  TIPO,
  unir,
  useDesvanecer,
  useEntrar,
  useEscalar,
  useGolpe,
  useTramo,
  type Estilo,
  type NombreIcono,
  type Resaltado,
} from "../comun";

// Las duraciones de deck.json: 3,7 (con el fundido de 0,4 adentro) y 2,5 s.
export const pasos = pasosDe("D09");

// =======================================================================================
// Tarjeta de demo: la misma pieza en D09, D10 y D11
// =======================================================================================

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const entre01 = (v: number) => Math.max(0, Math.min(1, v));

/**
 * El diseño de las tres demos (guion): la pastilla arriba a la izquierda, el nombre del flujo en
 * titulo a 104 px en y 270, la frase en hueso a 60 px en y 390, todo desde x 160, y el flujo
 * abajo, con nodos de 170 px y rótulos a 60 px. La lección del paso 2, centrada a 88 px en y 420 y 520.
 * Ajustes: la pastilla va en y 160 y no en 150 (mide 74 px de alto, y en y 150 su borde quedaba
 * dentro de los 20 px de aire que el auditor exige alrededor de la marca de agua). La fila sube de
 * y 620 a 600 y los rótulos de 760 a 740: abajo queda lugar para la salida real del flujo, que
 * ocupa la franja que antes quedaba vacía (nota de dirección 1 y 4).
 */
const TARJETA = {
  x: 160,
  pastillaY: 160,
  tituloY: 270,
  fraseY: 390,
  filaY: 600,
  lado: 170,
  rotuloY: 740,
  leccionYs: [420, 520],
  radio: 32,
  /** El ícono entra en un cuadro del 45 % del lado (guion). */
  iconoCaja: 0.45,
  /** El dato que viaja: un círculo ámbar de 28 px, con un halo suave del doble. */
  radioDato: 14,
  halo: { radio: 30, opacidad: 0.22 },
  /** Las conexiones de herramientas, a trazos de 16 px con huecos de 12, como en el editor de n8n. */
  trazos: "16 12",
  /** Cuánto crece un nodo cuando el dato pasa (el Latido de Manim: 1,06) y cuánto dura. */
  latido: 0.06,
  latidoDura: 0.3,
  /**
   * El brillo del nodo encendido (nota de dirección 3: un brillo suave en el nodo activo). Un halo
   * ámbar alrededor del borde, solo mientras el nodo está encendido. No es un resplandor de fondo.
   */
  brillo: { radio: 36, extension: 2, opacidad: 0.55 },
  /** La salida del flujo: centro en y 848, la franja que el auditor deja para leer (hasta y 900). */
  salidaY: 848,
} as const;

/** Alto de un ícono para que entre en un cuadro de `caja` px de lado (los de Font Awesome no son cuadrados). */
function altoIconoEn(nombre: NombreIcono, caja: number): number {
  const w = anchoIcono(nombre, caja);
  return w > caja ? (caja * caja) / w : caja;
}

/** Medidas del nodo ancho del agente: el ícono y su nombre adentro, como el nodo AI Agent del editor de n8n. */
function medidasAgente(texto: string, lado: number = TARJETA.lado) {
  const icono = altoIconoEn("robot", TARJETA.iconoCaja * lado);
  const anchoIc = anchoIcono("robot", icono);
  const tam = TIPO.escala.lectura;
  const aire = 26;
  const pad = 44;
  const ancho = Math.round(2 * pad + anchoIc + aire + medirTexto(texto, tam));
  return { icono, anchoIc, tam, aire, pad, ancho };
}

export type PropsNodoDemo = {
  cx: number;
  cy: number;
  lado: number;
  icono: NombreIcono;
  /** Nodo ancho con el nombre adentro (el agente): el texto del nombre. */
  nombreAdentro?: string;
  /** 0 = borde azul, 1 = borde ámbar y brillo. */
  encendido?: number;
  /** Escala extra (latido, golpe) alrededor del centro. */
  escala?: number;
  estilo?: Estilo;
};

/** El nodo de flujo de la charla: cuadrado redondeado relleno noche, borde azul de 5 px, ícono en hueso. Encendido: borde ámbar y brillo. */
const NodoDemo: React.FC<PropsNodoDemo> = ({ cx, cy, lado, icono, nombreAdentro, encendido = 0, escala = 1, estilo }) => {
  const e = entre01(encendido);
  const borde = e > 0 ? mezclar(COLOR.azul, COLOR.ambar, e) : COLOR.azul;
  const ag = nombreAdentro ? medidasAgente(nombreAdentro, lado) : null;
  const ancho = ag ? ag.ancho : lado;
  const izq = cx - ancho / 2;
  const b = TARJETA.brillo;
  return (
    <Capa estilo={unir(estilo, { transform: `scale(${escala})` })} origen={[cx, cy]}>
      <div
        style={{
          position: "absolute",
          left: izq,
          top: cy - lado / 2,
          width: ancho,
          height: lado,
          boxSizing: "border-box",
          borderRadius: TARJETA.radio,
          border: `${GROSOR.trazo_normal}px solid ${borde}`,
          background: COLOR.noche,
          boxShadow: e > 0 ? `0 0 ${b.radio}px ${b.extension}px ${conAlfa(COLOR.ambar, b.opacidad * e)}` : "none",
        }}
      />
      {ag ? (
        <>
          <Icono nombre={icono} alto={ag.icono} x={izq + ag.pad} y={cy} ancla="izq" />
          <Texto x={izq + ag.pad + ag.anchoIc + ag.aire} y={cy} tam={ag.tam}>
            {nombreAdentro as string}
          </Texto>
        </>
      ) : (
        <Icono nombre={icono} alto={altoIconoEn(icono, TARJETA.iconoCaja * lado)} x={cx} y={cy} />
      )}
    </Capa>
  );
};

const svgPantalla: React.CSSProperties = { position: "absolute", left: 0, top: 0, overflow: "visible" };

/**
 * Una conexión: azul de 5 px que se dibuja con `progreso`. A trazos, la de una herramienta: el
 * dibujo se revela con una máscara, para que los trazos no se corran mientras crece. Con
 * `encendido` va hacia el ámbar mientras el dato la recorre (la herramienta que el agente elige).
 */
const ConexionDemo: React.FC<{ id: string; d: string; progreso: number; trazos?: boolean; encendido?: number }> = ({ id, d, progreso, trazos = false, encendido = 0 }) => {
  const p = entre01(progreso);
  if (p <= 0) return null;
  const ev = evolvePath(p, d);
  const color = encendido > 0 ? mezclar(COLOR.azul, COLOR.ambar, entre01(encendido)) : COLOR.azul;
  if (!trazos) {
    return (
      <svg width={1920} height={1080} style={svgPantalla}>
        <path d={d} fill="none" stroke={color} strokeWidth={GROSOR.trazo_normal} strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
      </svg>
    );
  }
  const mascara = `mascara-${id}`;
  return (
    <svg width={1920} height={1080} style={svgPantalla}>
      <defs>
        <mask id={mascara} maskUnits="userSpaceOnUse" x={0} y={0} width={1920} height={1080}>
          <path d={d} fill="none" stroke="#ffffff" strokeWidth={4 * GROSOR.trazo_normal} strokeDasharray={ev.strokeDasharray} strokeDashoffset={ev.strokeDashoffset} />
        </mask>
      </defs>
      <path d={d} fill="none" stroke={color} strokeWidth={GROSOR.trazo_normal} strokeDasharray={TARJETA.trazos} mask={`url(#${mascara})`} />
    </svg>
  );
};

/** El dato que viaja: un círculo ámbar con su halo sobre el camino `d`, en `progreso` (0 a 1). Va debajo de los nodos: entra y sale de ellos. */
const PuntoDato: React.FC<{ d: string; progreso: number }> = ({ d, progreso }) => {
  if (progreso <= 0 || progreso >= 1) return null;
  const punto = getPointAtLength(d, getLength(d) * progreso);
  if (!punto) return null;
  return (
    <svg width={1920} height={1080} style={svgPantalla}>
      <circle cx={punto.x} cy={punto.y} r={TARJETA.halo.radio} fill={conAlfa(COLOR.ambar, TARJETA.halo.opacidad)} />
      <circle cx={punto.x} cy={punto.y} r={TARJETA.radioDato} fill={COLOR.ambar} />
    </svg>
  );
};

/** Un latido: 0, sube a 1 a la mitad y vuelve a 0, en `dura` s desde `retraso`. */
function useLatido(paso: number, retraso: number, dura: number = TARJETA.latidoDura): number {
  return Math.sin(Math.PI * useTramo(paso, retraso, dura, CURVA.lineal));
}

/** La cabecera del paso 1: pastilla, título y frase, de a uno (desfase de renglón). La frase se va al empezar el paso 2. */
function useCabecera() {
  const d = MOV.desfase.renglones;
  return {
    pastilla: useEntrar(1, 0),
    titulo: useEntrar(1, d),
    frase: unir(useEntrar(1, 2 * d), useDesvanecer(2, 0, 0.3)),
  };
}

const Cabecera: React.FC<{ demo: string; titulo: string; frase: string; anim: ReturnType<typeof useCabecera> }> = ({ demo, titulo, frase, anim }) => {
  const ancho = medidasPastilla(demo, TIPO.escala.rotulo).ancho;
  return (
    <>
      <Pastilla x={TARJETA.x + ancho / 2} y={TARJETA.pastillaY} tam={TIPO.escala.rotulo} estilo={anim.pastilla}>
        {demo}
      </Pastilla>
      <Texto x={TARJETA.x} y={TARJETA.tituloY} tam="grande" color={COLOR.titulo} estilo={anim.titulo}>
        {titulo}
      </Texto>
      <Texto x={TARJETA.x} y={TARJETA.fraseY} tam="lectura" estilo={anim.frase}>
        {frase}
      </Texto>
    </>
  );
};

/** La salida real del flujo: entra al final del paso 1 (sube 30 px con fundido) y se va con la frase al empezar el paso 2. */
export function useSalida(retraso: number, dura = 0.4): Estilo {
  return unir(useEntrar(1, retraso, { dura, distancia: 30 }), useDesvanecer(2, 0, 0.3));
}

/** El marco de la salida: relleno noche y borde azul fino, como un nodo, para que se lea como lo que devolvió el flujo. */
export const MarcoSalida: React.FC<{ x0: number; x1: number; y: number; alto: number }> = ({ x0, x1, y, alto }) => (
  <div
    style={{
      position: "absolute",
      left: x0,
      top: y - alto / 2,
      width: x1 - x0,
      height: alto,
      boxSizing: "border-box",
      borderRadius: RADIO.tarjeta,
      border: `${GROSOR.borde_fino}px solid ${COLOR.azul}`,
      background: COLOR.noche,
    }}
  />
);

/** El paso 2: el flujo se aleja (0,5 s) y pasa a Foco (0,3 s), y la lección sube en dos renglones. */
function useLeccion() {
  const d = MOV.desfase.renglones;
  return {
    aleja: useTramo(2, 0, 0.5, CURVA.suave),
    lineas: [useEntrar(2, 0.3), useEntrar(2, 0.3 + d)],
  };
}

const Leccion: React.FC<{ lineas: string[]; resaltar: (Resaltado | undefined)[]; anim: ReturnType<typeof useLeccion> }> = ({ lineas, resaltar, anim }) => (
  <>
    {lineas.map((l, i) => (
      <Texto key={i} x={960} y={TARJETA.leccionYs[i]} tam="idea" alinear="centro" resaltar={resaltar[i]} estilo={anim.lineas[i]}>
        {l}
      </Texto>
    ))}
  </>
);

/**
 * Ajuste: el guion pone la lección en y 420 y 520 y deja el flujo en su lugar, y el segundo
 * renglón pisaba los nodos. En el paso 2 el flujo se achica alrededor de su centro y baja hasta
 * quedar entero por debajo de y 605, y pasa a Foco: queda de fondo, como recuerdo.
 */
const FlujoQueSeAleja: React.FC<{ aleja: number; escala: number; dy: number; cy: number; children: React.ReactNode }> = ({ aleja, escala, dy, cy, children }) => (
  <Foco paso={2}>
    <Capa estilo={{ transform: `translate(0px, ${dy * aleja}px) scale(${lerp(1, escala, aleja)})` }} origen={[960, cy]}>
      {children}
    </Capa>
  </Foco>
);

// =======================================================================================
// D09
// =======================================================================================

/**
 * Los cuatro nodos (guion: x 360, 800, 1240 y 1680), con sus íconos.
 * Ajuste: la fila se corre a x 340, 770, 1200 y 1630. En 1680 el rótulo Veredicto terminaba a 11 px
 * de la pista vertical del fondo de circuito (x 1825).
 */
const NODOS = {
  xs: [340, 770, 1200, 1630],
  iconos: ["mobile-screen-button", "magnifying-glass", "brain", "circle-check"] as NombreIcono[],
} as const;

/**
 * La salida real del ensayo (workflows/muestras/flujo1-satelitazo.json): el nombre que se probó, el
 * veredicto y los otros nombres, tal como los mostró la página del flujo. LIBRE es lo correcto: va
 * en una pastilla ámbar con su palomita.
 */
const SALIDA = {
  nombre: "Satelitazo",
  veredicto: "LIBRE",
  otros: "PasaSat / SatAviso / OrbitaYa",
  /** Aire entre las tres piezas y a los costados del marco. */
  aire: 44,
  pad: 44,
  alto: 104,
} as const;

/** Paso 2: el flujo (de y 515 a 770, con los rótulos) se achica a 0,9 y baja 95 px: queda de y 622 a 851. */
const ALEJA = { escala: 0.9, dy: 95, cy: 640 } as const;

// ---------- Tiempos (s desde el comienzo de cada paso; los últimos 0,3 s, quietos) ----------
// D09.1 (3,3 s propios) 0, 0,15 y 0,3 la pastilla, el título y la frase. 0,45 a 0,9 los cuatro
//        nodos, de a uno, con su rótulo. 0,95 a 1,45 las conexiones. 1,4 a 2,2 el dato recorre
//        el flujo y cada nodo late al pasar. Veredicto queda encendido. 2,3 a 2,7 sube la salida
//        y la pastilla LIBRE da un golpe chico (2,45 a 2,95).
// D09.2 (2,5 s) 0 a 0,3 se van la frase y la salida, 0 a 0,5 el flujo se aleja y pasa a Foco,
//        0,3 y 0,45 los dos renglones de la lección.
const T1 = { nodos: 0.45, desfaseNodo: 0.15, rotulo: 0.05, conexiones: 0.95, desfaseConexion: 0.1, conexionDura: 0.3, dato: 1.4, datoDura: 0.8, salida: 2.3, golpe: 2.45 } as const;

export const D09DemoNombre: React.FC = () => {
  const t1 = textos("D09", 1); // ["Demo 1", "¿Ya existe tu nombre?", "Decí el nombre de tu proyecto.", "Formulario", "Google", "Modelo", "Veredicto"]
  const t2 = textos("D09", 2); // ["Línea recta:", "primero ve, después piensa."]
  const rotulos = t1.slice(3, 7);

  const cabecera = useCabecera();
  const nodos = [0, 1, 2, 3].map((i) => useEscalar(1, T1.nodos + i * T1.desfaseNodo, { desde: 0.85 }));
  const rotulosEntran = [0, 1, 2, 3].map((i) => useEntrar(1, T1.nodos + i * T1.desfaseNodo + T1.rotulo, { distancia: 30 }));
  const conexiones = [0, 1, 2].map((i) => useTramo(1, T1.conexiones + i * T1.desfaseConexion, T1.conexionDura, CURVA.suave));
  const dato = useTramo(1, T1.dato, T1.datoDura, CURVA.lineal);
  // Cada nodo late cuando el dato pasa por su centro. Veredicto, además, queda encendido.
  const latidos = [0, 1, 2, 3].map((i) => useLatido(1, T1.dato + (T1.datoDura * i) / 3 - TARJETA.latidoDura / 2));
  const queda = useTramo(1, T1.dato + T1.datoDura - 0.1, 0.25, CURVA.sale);
  const salida = useSalida(T1.salida);
  const golpe = useGolpe(1, T1.golpe, { chico: true });
  const leccion = useLeccion();

  // La fila de la salida, centrada bajo el flujo.
  const s = SALIDA;
  const tamNombre = TIPO.escala.lectura;
  const tamOtros = TIPO.escala.rotulo;
  const wNombre = medirTexto(s.nombre, tamNombre);
  const pVeredicto = medidasPastilla(s.veredicto, tamNombre, true);
  const wOtros = medirTexto(s.otros, tamOtros);
  const anchoSalida = 2 * s.pad + wNombre + s.aire + pVeredicto.ancho + s.aire + wOtros;
  const centroFlujo = (NODOS.xs[0] + NODOS.xs[3]) / 2;
  const x0 = centroFlujo - anchoSalida / 2;
  const xNombre = x0 + s.pad;
  const xVeredicto = xNombre + wNombre + s.aire + pVeredicto.ancho / 2;
  const xOtros = xNombre + wNombre + s.aire + pVeredicto.ancho + s.aire;
  const ys = TARJETA.salidaY;

  const y = TARJETA.filaY;
  const mitad = TARJETA.lado / 2;
  return (
    <>
      <FondoCircuito />
      <Cabecera demo={t1[0]} titulo={t1[1]} frase={t1[2]} anim={cabecera} />

      <FlujoQueSeAleja aleja={leccion.aleja} {...ALEJA}>
        {[0, 1, 2].map((i) => (
          <ConexionDemo key={`c${i}`} id={`d09-${i}`} d={`M ${NODOS.xs[i] + mitad} ${y} L ${NODOS.xs[i + 1] - mitad} ${y}`} progreso={conexiones[i]} />
        ))}
        <PuntoDato d={`M ${NODOS.xs[0]} ${y} L ${NODOS.xs[3]} ${y}`} progreso={dato} />
        {NODOS.xs.map((x, i) => (
          <React.Fragment key={`n${i}`}>
            <NodoDemo cx={x} cy={y} lado={TARJETA.lado} icono={NODOS.iconos[i]} encendido={i === 3 ? Math.max(latidos[i], queda) : latidos[i]} escala={1 + TARJETA.latido * latidos[i]} estilo={nodos[i]} />
            <Texto x={x} y={TARJETA.rotuloY} tam="lectura" alinear="centro" estilo={rotulosEntran[i]}>
              {rotulos[i]}
            </Texto>
          </React.Fragment>
        ))}
      </FlujoQueSeAleja>

      {/* Lo que devolvió el flujo en el ensayo. */}
      <Capa estilo={salida}>
        <MarcoSalida x0={x0} x1={x0 + anchoSalida} y={ys} alto={s.alto} />
        <Texto x={xNombre} y={ys} tam={tamNombre}>
          {s.nombre}
        </Texto>
        <Pastilla x={xVeredicto} y={ys} tam={tamNombre} color={COLOR.ambar} colorTexto={COLOR.ambar} marca={{ tipo: "palomita" }} estilo={golpe}>
          {s.veredicto}
        </Pastilla>
        <Texto x={xOtros} y={ys} tam={tamOtros} color={COLOR.gris}>
          {s.otros}
        </Texto>
      </Capa>

      <Leccion lineas={t2} resaltar={[undefined, ["primero ve", "después piensa"]]} anim={leccion} />
    </>
  );
};
