// D11 Demo 3: El scout del reto (contenido/guion.md, D11). La tercera demo en vivo: pegan su reto
// y un agente investiga con tres herramientas y devuelve una página con qué arrancar.
//
//   D11.1  La tarjeta de la demo: la pastilla Demo 3, el nombre del flujo, la frase y el flujo
//          (Tu reto, el agente con sus tres herramientas colgando a trazos, y Página). El dato
//          entra al agente, visita las tres herramientas y sale hacia Página, que queda encendida.
//   D11.2  La lección: la frase se va, el flujo se aleja y pasa a Foco, y sube La IA piensa.
//          n8n le da forma.
//
// El flujo sale de workflows/ESPEC.md (flujo 3), dibujado con el nodo de la charla.
// La tarjeta de demo (de TARJETA hasta FlujoQueSeAleja) es la misma pieza en D09, D10 y D11,
// copiada igual en los tres archivos: si cambia en uno, se copia a los otros dos. Diferencias de
// D10 y D11 (14-nov): NodoDemo acepta brilloComun (el brillo() de tres capas en lugar del halo
// propio, solo en el nodo que queda encendido) y PuntoDato dibuja el DatoViajero de la capa común
// (brillo y estela de 4). Copiar la tarjeta desde D09 encima de este archivo borraría la página que
// se arma: los cambios se copian a mano.
// Debajo de todo va el fondo de la charla con dos destellos por las pistas en el paso 1 (FondoVivo).
import { evolvePath } from "@remotion/paths";
import React from "react";
import {
  anchoIcono,
  brillo,
  Capa,
  COLOR,
  conAlfa,
  CURVA,
  DatoViajero,
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
  RESORTE,
  Texto,
  textos,
  TIPO,
  unir,
  useDesvanecer,
  useEntra,
  useEntrar,
  useEscalar,
  useTramo,
  type Estilo,
  type NombreIcono,
  type Resaltado,
} from "../comun";

// Las duraciones de deck.json: 3,9 (con el fundido de 0,4 adentro) y 2,5 s.
export const pasos = pasosDe("D11");

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
// D11
// =======================================================================================

/** La fila (guion): Tu reto en x 300, el agente en x 800 y Página en x 1650. */
const RETO = { x: 300, icono: "file-contract" as NombreIcono } as const;
const AGENTE = { x: 800, icono: "robot" as NombreIcono } as const;
const PAGINA = { x: 1650, icono: "desktop" as NombreIcono } as const;

/**
 * Las tres herramientas chicas que cuelgan del agente (guion: 90 px, en x 640, 800 y 960, y 820,
 * con su rótulo a 49 px debajo, en y 880), unidas a trazos y en línea recta desde tres puertos del
 * borde de abajo del agente. Con 55 px de alto, una curva como las de n8n quedaba con un gancho
 * en cada punta.
 * Ajuste: en y 820 el borde de abajo de la herramienta (865) tocaba la mayúscula de su rótulo
 * (863): suben a y 805 y quedan 12 px de aire. Y en x 640, 800 y 960, Artículos se montaba sobre
 * Google y YouTube: se abren a x 540, 800 y 1060 (el render falla si dos rótulos se tocan).
 * Con la fila de la tarjeta 20 px más arriba (y 600), suben también a y 785 y los rótulos a
 * y 860: lo último que se lee termina antes de y 900.
 */
const HERRAMIENTAS = {
  xs: [540, 800, 1060],
  y: 785,
  lado: 90,
  iconos: ["magnifying-glass", "building-columns", "film"] as NombreIcono[],
  rotuloY: 860,
  /** Los tres puertos del borde de abajo del agente. */
  puertos: [665, 800, 935],
  aireMinimo: 24,
} as const;

/**
 * Paso 2: el flujo (de y 515 a 885, con los rótulos de abajo) se achica a 0,8 y baja 45 px: queda de
 * y 597 a 893, con los rótulos de las herramientas a 39 px (antes 36,75) y los de la fila a 48.
 * Ajuste: el plan pedía 0,9 (rótulos a 44 px), pero el flujo mediría 333 px y entre la lección (su
 * línea de base, y 551) y y 900 no entra sin pegarse al segundo renglón o dejar los rótulos debajo
 * de y 900.
 */
const ALEJA = { escala: 0.8, dy: 45, cy: 700 } as const;

/**
 * La página que arma el flujo, dibujada sin texto sobre la línea vacía del agente a Página: centrada
 * en x 1280 (la mitad entre el borde del agente y el de Página) y en la fila. Un marco, una barra
 * ámbar arriba, tres tarjetas en noche con borde azul de 3 px y cuatro renglones grises. Se arma
 * bloque por bloque cuando el dato pasa por encima (desfase 0,08 s, cada bloque de 0,9 a 1 en 0,25 s).
 * Ajuste: 420 por 250 y no 280. Con 280 su borde de abajo (y 740) tocaba la esquina de arriba de la
 * herramienta YouTube (x 1015 a 1105, desde y 740). Con 250 queda de y 475 a 725: 15 px sobre las
 * herramientas y 40 debajo de la frase (y 390, 60 px).
 */
const DIBUJO = {
  cx: 1280,
  cy: 600,
  ancho: 420,
  alto: 250,
  radio: 18,
  pad: 20,
  borde: 3,
  barra: { alto: 26, radio: 8 },
  tarjetas: { arriba: 14, alto: 80, aire: 14, radio: 12, borde: 3 },
  renglones: { arriba: 16, alto: 12, paso: 20, radio: 6, anchos: [1, 0.86, 0.94, 0.58] },
  desfase: 0.08,
  dura: 0.25,
  desde: 0.9,
} as const;

/** Un bloque del dibujo: un rectángulo que crece de 0,9 a 1 alrededor de su centro. */
type Bloque = { x: number; y: number; w: number; h: number; radio: number; fondo: string; borde?: string };

function bloquesDibujo(): Bloque[][] {
  const D = DIBUJO;
  const x0 = D.cx - D.ancho / 2;
  const y0 = D.cy - D.alto / 2;
  const xi = x0 + D.pad;
  const wi = D.ancho - 2 * D.pad;
  const yBarra = y0 + D.pad;
  const yTarjetas = yBarra + D.barra.alto + D.tarjetas.arriba;
  const wTarjeta = (wi - 2 * D.tarjetas.aire) / 3;
  const yRenglones = yTarjetas + D.tarjetas.alto + D.renglones.arriba;
  const renglon = (i: number): Bloque => ({ x: xi, y: yRenglones + i * D.renglones.paso, w: wi * D.renglones.anchos[i], h: D.renglones.alto, radio: D.renglones.radio, fondo: COLOR.gris });
  return [
    [{ x: x0, y: y0, w: D.ancho, h: D.alto, radio: D.radio, fondo: COLOR.tinta, borde: conAlfa(COLOR.hueso, 0.5) }],
    [{ x: xi, y: yBarra, w: wi, h: D.barra.alto, radio: D.barra.radio, fondo: COLOR.ambar }],
    ...[0, 1, 2].map((i) => [{ x: xi + i * (wTarjeta + D.tarjetas.aire), y: yTarjetas, w: wTarjeta, h: D.tarjetas.alto, radio: D.tarjetas.radio, fondo: COLOR.noche, borde: COLOR.azul }]),
    [renglon(0), renglon(1)],
    [renglon(2), renglon(3)],
  ];
}

const BLOQUES = bloquesDibujo();

const DibujoPagina: React.FC<{ estilos: Estilo[]; sale: Estilo }> = ({ estilos, sale }) => (
  <Capa estilo={sale}>
    {BLOQUES.map((grupo, g) => (
      <React.Fragment key={g}>
        {grupo.map((b, i) => (
          <Capa key={i} estilo={estilos[g]} origen={[b.x + b.w / 2, b.y + b.h / 2]}>
            <div
              style={{
                position: "absolute",
                left: b.x,
                top: b.y,
                width: b.w,
                height: b.h,
                boxSizing: "border-box",
                borderRadius: b.radio,
                background: b.fondo,
                border: b.borde ? `${b.fondo === COLOR.tinta ? DIBUJO.borde : DIBUJO.tarjetas.borde}px solid ${b.borde}` : undefined,
              }}
            />
          </Capa>
        ))}
      </React.Fragment>
    ))}
  </Capa>
);

// ---------- Tiempos (s desde el comienzo de cada paso, los últimos 0,3 s quietos) ----------
// D11.1 (3,5 s propios) 0, 0,15 y 0,3 la pastilla, el título y la frase. 0,45, 0,6 y 0,75 Tu
//        reto, el agente y Página. 0,8 a 1,3 las conexiones de la fila. 1,0 a 1,95 las tres
//        herramientas, de a una. 1,18 a 1,4 el dato entra al agente, de 1,4 a 2,12 visita las
//        tres herramientas (va y vuelve, y cada una late cuando el dato llega), de 2,12 a 2,42
//        sale hacia Página. Cuando entra en la línea vacía (2,22) la página se arma encima, bloque
//        por bloque, hasta 2,95. Página se enciende con un golpe chico y el brillo de la charla
//        (2,42 a 2,77). Quieto desde 2,95.
// D11.2 (2,5 s) 0 a 0,5 el flujo se aleja y pasa a Foco, 0 a 0,3 se van la frase y el dibujo de
//        la página, 0,3 y 0,45 los dos renglones de la lección.
const T1 = {
  reto: 0.45,
  agente: 0.6,
  pagina: 0.75,
  rotulo: 0.05,
  conexiones: [0.8, 0.95],
  conexionDura: 0.35,
  herramientas: 1.0,
  desfaseHerramienta: 0.12,
  conexionHerramientaDura: 0.25,
  nodoHerramienta: 0.1,
  datoAlAgente: 1.18,
  datoAlAgenteDura: 0.22,
  visitas: [1.4, 1.64, 1.88],
  visitaDura: 0.24,
  latido: 0.25,
  aPagina: 2.12,
  aPaginaDura: 0.3,
  /** Cuando el dato entra en la línea vacía (x 1070): empieza a armarse la página. */
  arma: 2.22,
  golpe: 0.35,
  enciende: 0.15,
} as const;

export const D11DemoScout: React.FC = () => {
  const t1 = textos("D11", 1); // ["Demo 3", "El scout del reto", "Pegá tu reto. Te devuelve con qué arrancar.", "Tu reto", "Agente", "Google", "Artículos", "YouTube", "Página"]
  const t2 = textos("D11", 2); // ["La IA piensa.", "n8n le da forma."]
  const rotulosHerramientas = t1.slice(5, 8);
  const h = HERRAMIENTAS;

  // Los rótulos de las herramientas no se tocan entre sí.
  const tamRotulo = TIPO.escala.rotulo;
  for (let i = 0; i < 2; i++) {
    const derecha = h.xs[i] + medirTexto(rotulosHerramientas[i], tamRotulo) / 2;
    const izquierda = h.xs[i + 1] - medirTexto(rotulosHerramientas[i + 1], tamRotulo) / 2;
    if (izquierda - derecha < h.aireMinimo) {
      throw new Error(`D11.1: los rótulos ${rotulosHerramientas[i]} y ${rotulosHerramientas[i + 1]} quedan a ${Math.round(izquierda - derecha)} px (mínimo ${h.aireMinimo}).`);
    }
  }

  const cabecera = useCabecera();
  const nodos = [T1.reto, T1.agente, T1.pagina].map((t) => useEscalar(1, t, { desde: 0.85 }));
  const rotulosFila = [T1.reto, T1.pagina].map((t) => useEntrar(1, t + T1.rotulo, { distancia: 30 }));
  const conexiones = [0, 1].map((i) => useTramo(1, T1.conexiones[i], T1.conexionDura, CURVA.suave));
  const conexionesH = [0, 1, 2].map((i) => useTramo(1, T1.herramientas + i * T1.desfaseHerramienta, T1.conexionHerramientaDura, CURVA.suave));
  const herramientas = [0, 1, 2].map((i) => useEscalar(1, T1.herramientas + i * T1.desfaseHerramienta + T1.nodoHerramienta, { desde: 0.85 }));
  const rotulosH = [0, 1, 2].map((i) => useEntrar(1, T1.herramientas + i * T1.desfaseHerramienta + T1.nodoHerramienta + T1.rotulo, { distancia: 30 }));
  const datoAlAgente = useTramo(1, T1.datoAlAgente, T1.datoAlAgenteDura, CURVA.lineal);
  const latidoAgente = useLatido(1, T1.datoAlAgente + T1.datoAlAgenteDura, T1.latido);
  const visitas = [0, 1, 2].map((i) => useTramo(1, T1.visitas[i], T1.visitaDura, CURVA.lineal));
  const latidos = [0, 1, 2].map((i) => useLatido(1, T1.visitas[i] + T1.visitaDura / 2, T1.latido));
  const aPagina = useTramo(1, T1.aPagina, T1.aPaginaDura, CURVA.lineal);
  const golpe = useEntra(1, T1.aPagina + T1.aPaginaDura, T1.golpe, RESORTE.golpe);
  const enciende = useTramo(1, T1.aPagina + T1.aPaginaDura, T1.enciende, CURVA.sale);
  const estilosDibujo = BLOQUES.map((_, g) => useEscalar(1, T1.arma + g * DIBUJO.desfase, { desde: DIBUJO.desde, dura: DIBUJO.dura }));
  const saleDibujo = useDesvanecer(2, 0, 0.3);
  const leccion = useLeccion();

  const y = TARJETA.filaY;
  const mitad = TARJETA.lado / 2;
  const ag = medidasAgente(t1[4]);
  const agIzq = AGENTE.x - ag.ancho / 2;
  const agDer = AGENTE.x + ag.ancho / 2;
  const agAbajo = y + TARJETA.lado / 2;
  const hArriba = h.y - h.lado / 2;
  const colgante = (i: number) => `M ${h.puertos[i]} ${agAbajo} L ${h.xs[i]} ${hArriba}`;
  // El dato baja desde adentro del agente hasta el centro de la herramienta y vuelve.
  const visita = (i: number) => `M ${h.puertos[i]} ${agAbajo - 30} L ${h.puertos[i]} ${agAbajo} L ${h.xs[i]} ${hArriba} L ${h.xs[i]} ${h.y}`;
  const idaYVuelta = (u: number) => (u <= 0 || u >= 1 ? 0 : 1 - Math.abs(2 * u - 1));
  // Página: golpe chico (1,1 a 1) cuando llega el dato, y queda encendida.
  const escalaPagina = golpe > 0 ? 1 + (MOV.escala.golpe_chico - 1) * (1 - golpe) : 1;

  return (
    <>
      <FondoVivo pulsos={[1]} />
      <Cabecera demo={t1[0]} titulo={t1[1]} frase={t1[2]} anim={cabecera} />

      <FlujoQueSeAleja aleja={leccion.aleja} {...ALEJA}>
        <ConexionDemo id="d11-reto" d={`M ${RETO.x + mitad} ${y} L ${agIzq} ${y}`} progreso={conexiones[0]} />
        <ConexionDemo id="d11-pagina" d={`M ${agDer} ${y} L ${PAGINA.x - mitad} ${y}`} progreso={conexiones[1]} />
        {h.xs.map((_, i) => (
          <ConexionDemo key={`c${i}`} id={`d11-h${i}`} d={colgante(i)} progreso={conexionesH[i]} trazos encendido={Math.sin(Math.PI * visitas[i])} />
        ))}
        <DibujoPagina estilos={estilosDibujo} sale={saleDibujo} />
        <PuntoDato d={`M ${RETO.x} ${y} L ${AGENTE.x} ${y}`} progreso={datoAlAgente} />
        {h.xs.map((_, i) => (
          <PuntoDato key={`v${i}`} d={visita(i)} progreso={idaYVuelta(visitas[i])} />
        ))}
        <PuntoDato d={`M ${AGENTE.x} ${y} L ${PAGINA.x} ${y}`} progreso={aPagina} />

        <NodoDemo cx={RETO.x} cy={y} lado={TARJETA.lado} icono={RETO.icono} estilo={nodos[0]} />
        <NodoDemo cx={AGENTE.x} cy={y} lado={TARJETA.lado} icono={AGENTE.icono} nombreAdentro={t1[4]} encendido={latidoAgente} escala={1 + TARJETA.latido * latidoAgente} estilo={nodos[1]} />
        <NodoDemo cx={PAGINA.x} cy={y} lado={TARJETA.lado} icono={PAGINA.icono} encendido={enciende} escala={escalaPagina} estilo={nodos[2]} brilloComun />
        <Texto x={RETO.x} y={TARJETA.rotuloY} tam="lectura" alinear="centro" estilo={rotulosFila[0]}>
          {t1[3]}
        </Texto>
        <Texto x={PAGINA.x} y={TARJETA.rotuloY} tam="lectura" alinear="centro" estilo={rotulosFila[1]}>
          {t1[8]}
        </Texto>
        {h.xs.map((x, i) => (
          <React.Fragment key={`h${i}`}>
            <NodoDemo cx={x} cy={h.y} lado={h.lado} icono={h.iconos[i]} encendido={latidos[i]} escala={1 + TARJETA.latido * latidos[i]} estilo={herramientas[i]} />
            <Texto x={x} y={h.rotuloY} tam={tamRotulo} alinear="centro" estilo={rotulosH[i]}>
              {rotulosHerramientas[i]}
            </Texto>
          </React.Fragment>
        ))}
      </FlujoQueSeAleja>

      <Leccion lineas={t2} resaltar={[undefined, "le da forma"]} anim={leccion} />
    </>
  );
};
