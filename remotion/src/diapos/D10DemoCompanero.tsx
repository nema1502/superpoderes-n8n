// D10 Demo 2: El compañero de la madrugada (contenido/guion.md, D10). La segunda demo en vivo:
// un chat con un agente que tiene tres herramientas de SerpApi (mapas, noticias y YouTube) y
// memoria. Lo que sorprende es que elige solo qué herramienta usar.
//
//   D10.1  La tarjeta de la demo: la pastilla Demo 2, el nombre del flujo, la frase y el flujo
//          (Chat, el agente y sus tres herramientas a trazos, en abanico). El dato va del chat al
//          agente y el agente elige una herramienta distinta cada vez: Noticias, YouTube y Mapas.
//          Mapas queda encendida, la respuesta vuelve al chat y abajo sube lo que contestó en el
//          ensayo (workflows/muestras/flujo2-conversacion.json), con el ícono de Mapas.
//   D10.2  La lección: la frase y la respuesta se van, el flujo se aleja y pasa a Foco, y sube
//          Nadie le dijo qué usar. Eligió solo.
//
// El flujo sale de workflows/ESPEC.md (flujo 2), dibujado con el nodo de la charla.
// La tarjeta de demo (de TARJETA hasta FlujoQueSeAleja) es la misma pieza en D09, D10 y D11,
// copiada igual en los tres archivos: si cambia en uno, se copia a los otros dos. Diferencias de
// D10 y D11 (14-nov): NodoDemo acepta brilloComun (el brillo() de tres capas en lugar del halo
// propio, solo en el nodo que queda encendido) y PuntoDato dibuja el DatoViajero de la capa común
// (brillo y estela de 4). Copiar la tarjeta desde D09 encima de este archivo borraría la línea que
// se enciende: los cambios se copian a mano.
// Debajo de todo va el fondo de la charla con dos destellos por las pistas en el paso 1 (FondoVivo).
import { evolvePath } from "@remotion/paths";
import React from "react";
import {
  anchoIcono,
  Aro,
  brillo,
  Camara,
  Capa,
  COLOR,
  conAlfa,
  CURVA,
  DatoViajero,
  filtroBrillo,
  Foco,
  FondoVivo,
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
  useTramo,
  type Estilo,
  type NombreIcono,
  type Resaltado,
} from "../comun";

// Las duraciones de deck.json: 3,7 (con el fundido de 0,4 adentro) y 2,5 s.
export const pasos = pasosDe("D10");

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
  /** El brillo de tres capas de la charla (brillo de comun/Luz) en lugar del halo propio, con el mismo encendido. */
  brilloComun?: boolean;
};

/** El nodo de flujo de la charla: cuadrado redondeado relleno noche, borde azul de 5 px, ícono en hueso. Encendido: borde ámbar y brillo. */
const NodoDemo: React.FC<PropsNodoDemo> = ({ cx, cy, lado, icono, nombreAdentro, encendido = 0, escala = 1, estilo, brilloComun = false }) => {
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
          boxShadow: brilloComun ? brillo(COLOR.ambar, e) ?? "none" : e > 0 ? `0 0 ${b.radio}px ${b.extension}px ${conAlfa(COLOR.ambar, b.opacidad * e)}` : "none",
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

/**
 * El dato que viaja: el DatoViajero de la charla (comun/Luz: círculo ámbar con brillo y una estela
 * de 4), sobre el camino `d`, en `progreso` (0 a 1). Con 0 o 1 no se ve. Va debajo de los nodos:
 * entra y sale de ellos.
 */
const PuntoDato: React.FC<{ d: string; progreso: number }> = ({ d, progreso }) => (
  <DatoViajero d={d} progreso={progreso} radio={TARJETA.radioDato} estela={4} color={COLOR.ambar} brillo={1} />
);

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
// D10
// =======================================================================================

/** El chat en x 360 y el agente en x 860, en la fila (guion). */
const CHAT = { x: 360, icono: "comments" as NombreIcono } as const;
const AGENTE = { x: 860, icono: "robot" as NombreIcono } as const;

/**
 * Las tres herramientas en columna (guion: nodos de 120 px en x 1380, y 500, 640 y 780, con su
 * rótulo a 60 px a la derecha, 28 px de aire), unidas al agente a trazos y en abanico.
 * Ajustes: salen de tres puertos del borde derecho del agente (40 px uno del otro): desde un solo
 * punto, los tres trazos se amontonaban en un nudo justo al salir. La columna sube a y 450, 590 y
 * 730 y se corre a x 1440: abajo a la izquierda entra la respuesta del agente sin tocar YouTube.
 */
const HERRAMIENTAS = {
  x: 1440,
  ys: [450, 590, 730],
  lado: 120,
  iconos: ["map-location-dot", "globe", "film"] as NombreIcono[],
  aireRotulo: 28,
  puertos: [-40, 0, 40],
  /** Cuánto se separa la curva de cada punta, en horizontal (tangentes horizontales, como en n8n). */
  curva: 120,
} as const;

/**
 * La respuesta real del ensayo (workflows/muestras/flujo2-conversacion.json, primera pregunta: un
 * café cerca del centro). El agente usó Mapas. Va el comienzo de su primer renglón, tal cual, con
 * el ícono de Mapas en ámbar: la herramienta que eligió.
 */
const RESPUESTA = { texto: "Podemos ir a Santuario Caffé Art", icono: "map-location-dot" as NombreIcono, alto: 104, pad: 44, aire: 24, iconoAlto: 56 } as const;

/** El orden en que el agente elige: Noticias, YouTube y al final Mapas, que es la que responde abajo. */
const ORDEN = [1, 2, 0] as const;

/**
 * Paso 2: el flujo (de y 390 a 790) se achica a 0,75 y baja 160 px: queda de y 600 a 900, con los
 * rótulos a 45 px (con 0,7 quedaban en 42, por debajo de los 44 que se leen desde el fondo). Mapas
 * queda a la derecha de la lección (x 1275 a 1365): no la pisa.
 */
const ALEJA = { escala: 0.75, dy: 160, cy: 590 } as const;

// ---------- Tiempos (s desde el comienzo de cada paso, los últimos 0,3 s quietos) ----------
// D10.1 (3,3 s propios) 0, 0,15 y 0,3 la pastilla, el título y la frase. 0,45 el chat y 0,6
//        el agente. 0,75 a 1,05 la conexión. 0,95 a 1,9 las tres herramientas salen del agente
//        en abanico, de a una. 1,35 a 1,6 el dato va del chat al agente, y desde 1,6 elige una
//        herramienta distinta cada vez: Noticias, YouTube y Mapas (cada viaje 0,26 s y cada
//        herramienta late al recibirlo). Cuando el dato llega a Mapas (2,38), la línea se
//        enciende: de 2,38 a 2,63 la conexión a Mapas pasa a una línea sólida ámbar de 6 px con
//        brillo, Noticias y YouTube bajan a 0,4 con sus líneas, Mapas queda con el brillo de
//        tres capas y un aro ámbar sale de su borde (2,38 a 2,78). 2,42 a 2,62 la respuesta
//        vuelve al chat, que late hasta 2,8, y de 2,45 a 2,8 sube abajo. Quieto desde 2,8.
// D10.2 (2,5 s) 0 a 0,3 se van la frase y la respuesta, 0 a 0,5 el flujo se aleja y pasa a Foco,
//        0,3 y 0,45 los dos renglones de la lección. La línea de Mapas, su brillo y las otras
//        dos herramientas a 0,4 siguen como quedaron.
const T1 = {
  chat: 0.45,
  agente: 0.6,
  rotulo: 0.05,
  conexion: 0.75,
  conexionDura: 0.3,
  herramientas: 0.95,
  desfaseHerramienta: 0.15,
  nodoHerramienta: 0.15,
  datoAlAgente: 1.35,
  datoAlAgenteDura: 0.25,
  elige: [1.6, 1.86, 2.12],
  eligeDura: 0.26,
  latido: 0.25,
  /** Cuando el dato llega a Mapas (2,12 + 0,26): la línea se enciende y lo demás baja. */
  enciende: 2.38,
  enciendeDura: 0.25,
  aroDura: 0.4,
  vuelta: 2.42,
  vueltaDura: 0.2,
  latidoChat: 0.18,
  respuesta: 2.45,
  respuestaDura: 0.35,
} as const;

/**
 * La cámara del paso 1: el flujo y la respuesta, de 0,96 a 1 en 2,8 s alrededor del centro del flujo.
 * Termina con lo demás, sin transform. La cabecera queda afuera: con el título amarillo a medio
 * aparecer y escalado, el auditor de lima marcaba 11 px en el cuadro 15.
 */
const CAMARA = { desde: 0.96, dura: 2.8, origen: [960, 640] as [number, number] } as const;

/** La línea elegida: sólida, ámbar, de 6 px, con el brillo de la charla. Las otras herramientas, a 0,4. El aro crece 80 px por lado. */
const ELEGIDA = { grosor: 6, otras: 0.4, aroCrece: 160, aroGrosor: 5 } as const;

export const D10DemoCompanero: React.FC = () => {
  const t1 = textos("D10", 1); // ["Demo 2", "El compañero de la madrugada", "Preguntale como a un amigo.", "Chat", "Agente", "Mapas", "Noticias", "YouTube"]
  const t2 = textos("D10", 2); // ["Nadie le dijo qué usar.", "Eligió solo."]
  const rotulosHerramientas = t1.slice(5, 8);

  const cabecera = useCabecera();
  const chat = useEscalar(1, T1.chat, { desde: 0.85 });
  const agente = useEscalar(1, T1.agente, { desde: 0.85 });
  const rotuloChat = useEntrar(1, T1.chat + T1.rotulo, { distancia: 30 });
  const conexion = useTramo(1, T1.conexion, T1.conexionDura, CURVA.suave);
  const conexiones = [0, 1, 2].map((i) => useTramo(1, T1.herramientas + i * T1.desfaseHerramienta, T1.conexionDura, CURVA.suave));
  const herramientas = [0, 1, 2].map((i) => useEscalar(1, T1.herramientas + i * T1.desfaseHerramienta + T1.nodoHerramienta, { desde: 0.85 }));
  const rotulosEntran = [0, 1, 2].map((i) => useEntrar(1, T1.herramientas + i * T1.desfaseHerramienta + T1.nodoHerramienta + T1.rotulo, { desde: "izq" }));
  const datoAlAgente = useTramo(1, T1.datoAlAgente, T1.datoAlAgenteDura, CURVA.lineal);
  const latidoAgente = useLatido(1, T1.datoAlAgente + T1.datoAlAgenteDura, T1.latido);
  // elige[i] y latidos[i] son de la herramienta i (0 Mapas, 1 Noticias, 2 YouTube), en el ORDEN de los viajes.
  const vez = [0, 1, 2].map((i) => (ORDEN as readonly number[]).indexOf(i));
  const elige = [0, 1, 2].map((i) => useTramo(1, T1.elige[vez[i]], T1.eligeDura, CURVA.suave));
  const latidos = [0, 1, 2].map((i) => useLatido(1, T1.elige[vez[i]] + T1.eligeDura, T1.latido));
  const queda = useTramo(1, T1.enciende, T1.enciendeDura, CURVA.sale);
  const lineaElegida = useTramo(1, T1.enciende, T1.enciendeDura, CURVA.sale);
  const bajan = useTramo(1, T1.enciende, T1.enciendeDura, CURVA.suave);
  const opOtras = 1 - (1 - ELEGIDA.otras) * bajan;
  const vuelta = useTramo(1, T1.vuelta, T1.vueltaDura, CURVA.lineal);
  const latidoChat = useLatido(1, T1.vuelta + T1.vueltaDura, T1.latidoChat);
  const respuesta = useSalida(T1.respuesta, T1.respuestaDura);
  const leccion = useLeccion();

  const y = TARJETA.filaY;
  const ag = medidasAgente(t1[4]);
  const agIzq = AGENTE.x - ag.ancho / 2;
  const agDer = AGENTE.x + ag.ancho / 2;
  const h = HERRAMIENTAS;
  const hIzq = h.x - h.lado / 2;
  const curva = (i: number) => {
    const yp = y + h.puertos[i];
    const yh = h.ys[i];
    return `M ${agDer} ${yp} C ${agDer + h.curva} ${yp} ${hIzq - h.curva} ${yh} ${hIzq} ${yh}`;
  };
  // El dato sale de adentro del agente (cerca de su borde, para que el viaje se vea) y entra en la herramienta.
  const viaje = (i: number) => `M ${agDer - 20} ${y + h.puertos[i]} L ${agDer} ${y + h.puertos[i]} ${curva(i).slice(curva(i).indexOf("C"))} L ${h.x} ${h.ys[i]}`;
  // Mapas (la última) queda encendida: su conexión no vuelve al azul.
  const ultima = ORDEN[2];
  const encendidoConexion = (i: number) => (i === ultima ? Math.sin(Math.PI * Math.min(elige[i], 0.5)) : Math.sin(Math.PI * elige[i]));

  // La respuesta, abajo a la izquierda, alineada con la cabecera.
  const r = RESPUESTA;
  const tamR = TIPO.escala.lectura;
  const wIcono = anchoIcono(r.icono, r.iconoAlto);
  const anchoR = 2 * r.pad + wIcono + r.aire + medirTexto(r.texto, tamR);
  const rx0 = TARJETA.x;
  const ry = TARJETA.salidaY;
  const youtubeAbajo = h.ys[2] + h.lado / 2;
  if (rx0 + anchoR > hIzq - 40 && ry - r.alto / 2 < youtubeAbajo + 12) {
    throw new Error(`D10.1: la respuesta (hasta x ${Math.round(rx0 + anchoR)}) toca la columna de herramientas.`);
  }

  return (
    <>
      <FondoVivo pulsos={[1]} />
      <Cabecera demo={t1[0]} titulo={t1[1]} frase={t1[2]} anim={cabecera} />

      {/* La cámara se acerca al flujo y a la respuesta durante el paso 1. La cabecera y el fondo quedan quietos. */}
      <Camara paso={1} desde={CAMARA.desde} dura={CAMARA.dura} origen={CAMARA.origen}>

      <FlujoQueSeAleja aleja={leccion.aleja} {...ALEJA}>
        <ConexionDemo id="d10-chat" d={`M ${CHAT.x + TARJETA.lado / 2} ${y} L ${agIzq} ${y}`} progreso={conexion} />
        {h.ys.map((_, i) => (
          <Capa key={`c${i}`} estilo={i === ultima ? undefined : { opacity: opOtras }}>
            <ConexionDemo id={`d10-h${i}`} d={curva(i)} progreso={conexiones[i]} trazos encendido={encendidoConexion(i)} />
          </Capa>
        ))}
        {/* La línea que se enciende: del agente a Mapas, sólida, ámbar y con brillo, encima de los trazos. */}
        {lineaElegida > 0 && (
          <svg width={1920} height={1080} style={{ ...svgPantalla, filter: filtroBrillo(COLOR.ambar, 1) }}>
            <path
              d={curva(ultima)}
              fill="none"
              stroke={COLOR.ambar}
              strokeWidth={ELEGIDA.grosor}
              strokeDasharray={evolvePath(lineaElegida, curva(ultima)).strokeDasharray}
              strokeDashoffset={evolvePath(lineaElegida, curva(ultima)).strokeDashoffset}
            />
          </svg>
        )}
        <PuntoDato d={`M ${CHAT.x} ${y} L ${AGENTE.x} ${y}`} progreso={datoAlAgente} />
        {h.ys.map((_, i) => (
          <PuntoDato key={`p${i}`} d={viaje(i)} progreso={elige[i]} />
        ))}
        <PuntoDato d={`M ${AGENTE.x} ${y} L ${CHAT.x} ${y}`} progreso={vuelta} />

        <NodoDemo cx={CHAT.x} cy={y} lado={TARJETA.lado} icono={CHAT.icono} encendido={latidoChat} escala={1 + TARJETA.latido * latidoChat} estilo={chat} />
        <Texto x={CHAT.x} y={TARJETA.rotuloY} tam="lectura" alinear="centro" estilo={rotuloChat}>
          {t1[3]}
        </Texto>
        <NodoDemo cx={AGENTE.x} cy={y} lado={TARJETA.lado} icono={AGENTE.icono} nombreAdentro={t1[4]} encendido={latidoAgente} escala={1 + TARJETA.latido * latidoAgente} estilo={agente} />
        {h.ys.map((yh, i) => (
          <Capa key={`h${i}`} estilo={i === ultima ? undefined : { opacity: opOtras }}>
            <NodoDemo
              cx={h.x}
              cy={yh}
              lado={h.lado}
              icono={h.iconos[i]}
              encendido={i === ultima ? Math.max(latidos[i], queda) : latidos[i]}
              escala={1 + TARJETA.latido * latidos[i]}
              estilo={herramientas[i]}
              brilloComun={i === ultima}
            />
            <Texto x={h.x + h.lado / 2 + h.aireRotulo} y={yh} tam="lectura" estilo={rotulosEntran[i]}>
              {rotulosHerramientas[i]}
            </Texto>
          </Capa>
        ))}
        <Aro
          paso={1}
          retraso={T1.enciende}
          cx={h.x}
          cy={h.ys[ultima]}
          desde={h.lado}
          hasta={h.lado + ELEGIDA.aroCrece}
          radioEsquina={TARJETA.radio / h.lado}
          color={COLOR.ambar}
          grosor={ELEGIDA.aroGrosor}
          dura={T1.aroDura}
        />
      </FlujoQueSeAleja>

      {/* Lo que respondió el agente en el ensayo, con el ícono de la herramienta que eligió. */}
      <Capa estilo={respuesta}>
        <MarcoSalida x0={rx0} x1={rx0 + anchoR} y={ry} alto={r.alto} />
        <Icono nombre={r.icono} alto={r.iconoAlto} x={rx0 + r.pad} y={ry} ancla="izq" color={COLOR.ambar} />
        <Texto x={rx0 + r.pad + wIcono + r.aire} y={ry} tam={tamR}>
          {r.texto}
        </Texto>
      </Capa>
      </Camara>

      <Leccion lineas={t2} resaltar={[undefined, "Eligió solo"]} anim={leccion} />
    </>
  );
};
