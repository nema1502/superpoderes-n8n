// D06 Ver, pensar, hacer (contenido/guion.md, D06). La revelación de los dos superpoderes y
// la imagen central de la charla: tres nodos, VER, PENSAR y HACER, unidos por pistas de
// circuito por donde viaja el dato en ámbar.
//
//   D06.1  El flujo de D05 queda chico arriba, en el mismo lugar donde lo deja D05.3. El dato
//          lo recorre una vez, siempre igual, y el flujo pasa a Foco. Sube Un flujo común solo
//          hace. y, de a una, las dos cosas que no puede, cada una con su cruz roja.
//   D06.2  Se apagan las luces y HACER aparece primero, solo y tranquilo, con la cámara cerca y
//          sus engranajes girando un poco al asentarse: es el que ya existía. La cámara se aleja
//          y cada superpoder hace lo suyo al llegar. VER mira: de la lupa sale un haz de luz que
//          barre el cielo una vez, como un faro, y las estrellas que toca se encienden. PENSAR
//          conecta: alrededor del cerebro se dibuja una red de estrellas unidas por líneas finas,
//          que late una vez y se apaga. El haz y la red traen de vuelta la luz del fondo. Recién
//          con los dos llega el título, Dos superpoderes, con un golpe y un barrido de luz. Las
//          pistas se dibujan de puerto a puerto con una chispa en la punta y el dato las recorre
//          con su estela: cada nodo late con brillo ámbar cuando pasa y queda encendido en azul.
//   D06.3  Los logos se van, los tres nodos se achican y suben y entra la idea clave. Cada
//          palabra en ámbar se enciende junto con su nodo: vea con VER, piense con PENSAR y haga
//          con HACER, una tras otra.
//
// Exporta la geometría y las piezas de los tres nodos y de la idea (PODERES, IDEA_PODERES,
// NodoFlujo, PistaLinea, PistaPuertos, PuntoDato, Poderes, PoderesChicos e IdeaPoderes) para
// que D15.1 dibuje el cuadro final de D06.3 igual, píxel por píxel.
//
// Decisiones propias (lo que el guion no fija o no entraba tal cual) van junto a cada constante
// con la palabra Ajuste.
import { getLength, getPointAtLength } from "@remotion/paths";
import React from "react";
import { Img, staticFile } from "remotion";
import {
  anchoIcono,
  BarridoLuz,
  brillo,
  Capa,
  COLOR,
  Cruz,
  conAlfa,
  CURVA,
  DatoViajero,
  Foco,
  FondoVivo,
  GROSOR,
  grosorAsta,
  Icono,
  IDEA_CLAVE,
  medirTexto,
  mezclar,
  pasosDe,
  PuntaLuz,
  Texto,
  textos,
  TIPO,
  unir,
  useAparecer,
  useDesvanecer,
  useDestello,
  useEntrar,
  useGolpe,
  useTramo,
  type Estilo,
  type NombreIcono,
} from "../comun";
import { ICONOS_SVG } from "../comun/iconos.generado";

// Las duraciones de deck.json: 3,3 (con el fundido de 0,4 adentro), 4,5 y 3,1 s.
// Ajuste: D06.2 pasa a 5,4 s para que cada superpoder haga lo suyo al llegar (el haz y la red)
// sin apurar el dato. El deck tiene que decir lo mismo (render.mjs avisa mientras no coincida).
export const pasos = pasosDe("D06", { 2: 5.4 });

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
/** Mezcla de dos colores en hex que devuelve hex (conAlfa pide hex; mezclar devuelve rgb()). */
const mezclaHex = (a: string, b: string, k: number) =>
  "#" + [1, 3, 5].map((i) => Math.round(lerp(parseInt(a.slice(i, i + 2), 16), parseInt(b.slice(i, i + 2), 16), k)).toString(16).padStart(2, "0")).join("");
const entre01 = (v: number) => Math.max(0, Math.min(1, v));

// ---------------------------------------------------------------------------------------
// Piezas: el nodo de flujo, la pista de circuito y el dato que viaja
// ---------------------------------------------------------------------------------------

/** Radio del nodo de flujo de la charla (guion: cuadrado redondeado de radio 32 px). */
export const RADIO_NODO = 32;
/** El dato que viaja: un círculo ámbar de 28 px (guion). */
export const RADIO_DATO = 14;
/** Cuánto crece un nodo cuando el dato pasa por él (el Latido de Manim: 1,06). */
export const LATIDO_NODO = 0.06;

/** Alto de un ícono para que entre en un cuadro de `caja` px de lado (los de Font Awesome no son cuadrados). */
export function altoIconoEn(nombre: NombreIcono, caja: number): number {
  const w = anchoIcono(nombre, caja);
  return w > caja ? (caja * caja) / w : caja;
}

export type PropsNodoFlujo = {
  cx: number;
  cy: number;
  /** Lado del cuadrado. */
  lado: number;
  icono: NombreIcono;
  /** Lado del cuadro donde entra el ícono: 45 % del lado si no se dice. */
  iconoCaja?: number;
  /** Alto del ícono, si se fija (los tres poderes: la mitad del lado, como en D15). Gana sobre iconoCaja. */
  iconoAlto?: number;
  radio?: number;
  /** Grosor del borde (5 px; el flujo de D05 achicado lo lleva a escala). */
  grosor?: number;
  /** 0 = borde azul, 1 = borde ámbar (el dato está pasando por el nodo). */
  encendido?: number;
  /** Entrada (opacidad y transform), con el centro del nodo como origen. */
  estilo?: Estilo;
  /** La luz del nodo activo (brillo() de Luz): una capa o varias. Por defecto, nada. */
  brillo?: LuzNodo | LuzNodo[];
  /** 0 a 1: el borde va hacia el hueso (el fogonazo de cuando llega). Por defecto, 0. */
  destello?: number;
  /** Giro de los engranajes en grados (solo el ícono gears: cada rueda sobre su eje). Por defecto, 0. */
  giro?: number;
};

/**
 * Los dos engranajes del ícono gears, cada uno sobre su propio eje (el centro de su agujero en el
 * SVG de Font Awesome: 160, 176 y 464, 352) y en sentidos contrarios, como dos ruedas que engranan.
 * La chica gira un poco más rápido (radios de 168 y 160). Con giro 0 se dibuja el Icono de siempre.
 */
const ENGRANAJES = { grande: [160, 176], chico: [464, 352], relacion: 168 / 160, corte: "M504.7" } as const;

const Engranajes: React.FC<{ alto: number; x: number; y: number; giro: number }> = ({ alto, x, y, giro }) => {
  const i = ICONOS_SVG.gears;
  const k = i.d.indexOf(ENGRANAJES.corte);
  const w = anchoIcono("gears", alto);
  const [gx, gy] = ENGRANAJES.grande;
  const [cx, cy] = ENGRANAJES.chico;
  const partes = k > 0 ? [i.d.slice(0, k), i.d.slice(k)] : [i.d, ""];
  return (
    <svg width={w} height={alto} viewBox={`0 0 ${i.ancho} ${i.alto}`} style={{ position: "absolute", left: x - w / 2, top: y - alto / 2, overflow: "visible" }}>
      <g transform={`rotate(${giro} ${gx} ${gy})`}>
        <path d={partes[0]} fill={COLOR.hueso} />
      </g>
      {partes[1] && (
        <g transform={`rotate(${-giro * ENGRANAJES.relacion} ${cx} ${cy})`}>
          <path d={partes[1]} fill={COLOR.hueso} />
        </g>
      )}
    </svg>
  );
};

/** Una capa de brillo de un nodo: el color y cuánto (0 no dibuja nada). */
export type LuzNodo = { color: string; k: number };

/** El boxShadow de una o varias capas de brillo, o undefined si ninguna se ve. */
function sombraNodo(luz: LuzNodo | LuzNodo[] | undefined): string | undefined {
  if (!luz) return undefined;
  const capas = (Array.isArray(luz) ? luz : [luz]).map((l) => brillo(l.color, l.k > 0.002 ? l.k : 0)).filter((s): s is string => !!s);
  return capas.length ? capas.join(", ") : undefined;
}

/**
 * El nodo de flujo de la charla: cuadrado redondeado relleno noche, borde azul de 5 px y el
 * ícono en hueso. Mientras el dato pasa, el borde va hacia el ámbar y vuelve.
 */
export const NodoFlujo: React.FC<PropsNodoFlujo> = ({ cx, cy, lado, icono, iconoCaja, iconoAlto, radio = RADIO_NODO, grosor = GROSOR.trazo_normal, encendido = 0, estilo, brillo: luz, destello = 0, giro = 0 }) => {
  // El fogonazo y el latido no se pisan en D06 (el nodo llega antes de que pase el dato): gana el fogonazo.
  const borde =
    destello > 0
      ? mezclar(COLOR.azul, COLOR.hueso, entre01(destello))
      : encendido > 0
        ? mezclar(COLOR.azul, COLOR.ambar, entre01(encendido))
        : COLOR.azul;
  const caja = iconoCaja ?? 0.45 * lado;
  const altoIcono = iconoAlto ?? altoIconoEn(icono, caja);
  return (
    <Capa estilo={estilo} origen={[cx, cy]}>
      <div
        style={{
          position: "absolute",
          left: cx - lado / 2,
          top: cy - lado / 2,
          width: lado,
          height: lado,
          boxSizing: "border-box",
          borderRadius: radio,
          border: `${grosor}px solid ${borde}`,
          background: COLOR.noche,
          boxShadow: sombraNodo(luz),
        }}
      />
      {giro !== 0 && icono === "gears" ? <Engranajes alto={altoIcono} x={cx} y={cy} giro={giro} /> : <Icono nombre={icono} alto={altoIcono} x={cx} y={cy} />}
    </Capa>
  );
};

const svgPantalla: React.CSSProperties = { position: "absolute", left: 0, top: 0, overflow: "visible" };

/** La línea de una pista horizontal, de x0 a x1, que se dibuja con `progreso` (va debajo de los nodos y del dato). */
export const PistaLinea: React.FC<{ x0: number; x1: number; y: number; progreso?: number; opacidad?: number; grosor?: number }> = ({ x0, x1, y, progreso = 1, opacidad = 1, grosor = GROSOR.trazo_normal }) => {
  const p = entre01(progreso);
  if (p <= 0) return null;
  return (
    <svg width={1920} height={1080} style={{ ...svgPantalla, opacity: opacidad }}>
      <line x1={x0} y1={y} x2={lerp(x0, x1, p)} y2={y} stroke={COLOR.azul} strokeWidth={grosor} />
    </svg>
  );
};

/**
 * Los puertos de una pista: un círculo azul en cada punta, montado sobre el borde del nodo,
 * como el pad de una pista de circuito y el puerto de un nodo de n8n. El de la salida nace con
 * la pista y el de la llegada aparece cuando la pista lo alcanza. Van encima de los nodos.
 */
export const PistaPuertos: React.FC<{ x0: number; x1: number; y: number; progreso?: number; radio: number; opacidad?: number }> = ({ x0, x1, y, progreso = 1, radio, opacidad = 1 }) => {
  const p = entre01(progreso);
  if (p <= 0) return null;
  const sale = CURVA.sale(entre01(p / 0.2));
  const llega = CURVA.sale(entre01((p - 0.8) / 0.2));
  return (
    <svg width={1920} height={1080} style={{ ...svgPantalla, opacity: opacidad }}>
      <circle cx={x0} cy={y} r={radio * sale} fill={COLOR.azul} />
      {llega > 0 && <circle cx={x1} cy={y} r={radio * llega} fill={COLOR.azul} />}
    </svg>
  );
};

/** El dato que viaja: un círculo ámbar sobre el camino `d`, en `progreso` (0 a 1). Va debajo de los nodos: entra y sale de ellos. */
export const PuntoDato: React.FC<{ d: string; progreso: number; radio?: number }> = ({ d, progreso, radio = RADIO_DATO }) => {
  if (progreso <= 0 || progreso >= 1) return null;
  const punto = getPointAtLength(d, getLength(d) * progreso);
  if (!punto) return null;
  return (
    <svg width={1920} height={1080} style={svgPantalla}>
      <circle cx={punto.x} cy={punto.y} r={radio} fill={COLOR.ambar} />
    </svg>
  );
};

/** Un latido: 0, sube a 1 a la mitad y vuelve a 0, en `dura` s desde `retraso`. */
function useLatido(paso: number, retraso: number, dura = LATIDO_DURA): number {
  return Math.sin(Math.PI * useTramo(paso, retraso, dura, CURVA.lineal));
}
const LATIDO_DURA = 0.35;

// ---------------------------------------------------------------------------------------
// Los tres poderes (D06.2 y D06.3, y D15.1 con la geometría chica)
// ---------------------------------------------------------------------------------------

/**
 * Geometría de los tres nodos. Grande: el cuadro final de D06.2 (guion: 280 px, íconos de 140).
 * Chico: el de D06.3, que vuelve en D15.1 y tiene que verse igual. Son los números de NODOS en
 * D15Cierre.tsx (140 px en x 420, 960 y 1500, radio 35, ícono de 70 y verbos a 49 px en y 412):
 * si cambian allá, cambian acá.
 * Ajuste: el guion pone los logos en y 800. El de n8n pide un espacio libre del alto de su
 * símbolo (64 px, diseno/logos/FUENTES.md): en y 800 quedaba a 43 px de la mayúscula de HACER.
 * En y 820 quedan 63 px, y lo mismo el de SerpApi e IA, que van en la misma fila.
 * Ajuste: los puertos de las pistas (lo que las hace leerse como pistas de circuito en D06.2)
 * se achican hasta desaparecer en D06.3, porque D15.1 dibuja las conexiones sin ellos.
 */
export const PODERES = {
  iconos: ["magnifying-glass", "brain", "gears"] as NombreIcono[],
  grande: { y: 480, xs: [420, 960, 1500], lado: 280, radio: RADIO_NODO, icono: 140, verboY: 700, verboTam: TIPO.escala.frase, puerto: 10 },
  chico: { y: 300, xs: [420, 960, 1500], lado: 140, radio: 35, icono: 70, verboY: 412, verboTam: TIPO.escala.rotulo, puerto: 0 },
  logos: { y: 820, alto: 64 },
} as const;

/** La idea clave en D06.3 y D15.1: centrada a 88 px en y 600, con los tres verbos en ámbar. */
export const IDEA_PODERES = { x: 960, y: 600, tam: TIPO.escala.idea, resaltar: "vea, piense y haga" } as const;

export type PropsPoderes = {
  /** Los tres verbos, tal cual en deck.json: VER, PENSAR, HACER. */
  verbos: string[];
  /** 0 = la geometría grande (D06.2), 1 = la chica (D06.3). En el medio, se interpola (no se escala la imagen). */
  achica?: number;
  /** Entrada de cada nodo (golpe, fundido) con su centro como origen. */
  estilosNodo?: (Estilo | undefined)[];
  /** Entrada de cada verbo. */
  estilosVerbo?: (Estilo | undefined)[];
  /** Progreso de las dos pistas (0 sin dibujar, 1 dibujadas). */
  pistas?: number;
  /** Latido de cada nodo (0 a 1 y vuelta): crece y el borde va al ámbar. */
  latidos?: number[];
  /** Progreso del dato por el camino de VER a HACER (0 o 1: no se ve). */
  dato?: number;
  /** La luz de cada nodo (D06.2 y el comienzo de D06.3). Por defecto, ninguna: D15.1 queda igual. */
  brillos?: (LuzNodo | LuzNodo[] | undefined)[];
  /** El fogonazo del borde de cada nodo (0 a 1). Por defecto, 0. */
  destellos?: number[];
  /** Con un número, el dato viaja con brillo y esa estela (DatoViajero). Sin él, el PuntoDato de siempre. */
  estelaDato?: number;
  /** La chispa en la punta de cada pista mientras se dibuja (PuntaLuz). Por defecto, no. */
  puntaPistas?: boolean;
  /** Giro del ícono de cada nodo en grados (los engranajes de HACER). Por defecto, 0. */
  giros?: number[];
};

/** Centro, lado, ícono y verbo de cada nodo para un `achica` dado. */
export function geometriaPoderes(achica: number) {
  const g = PODERES.grande;
  const c = PODERES.chico;
  const k = entre01(achica);
  return {
    y: lerp(g.y, c.y, k),
    xs: g.xs.map((x, i) => lerp(x, c.xs[i], k)),
    lado: lerp(g.lado, c.lado, k),
    radio: lerp(g.radio, c.radio, k),
    icono: lerp(g.icono, c.icono, k),
    verboY: lerp(g.verboY, c.verboY, k),
    verboTam: lerp(g.verboTam, c.verboTam, k),
    puerto: lerp(g.puerto, c.puerto, k),
  };
}

export const Poderes: React.FC<PropsPoderes> = ({ verbos, achica = 0, estilosNodo = [], estilosVerbo = [], pistas = 1, latidos = [0, 0, 0], dato = 0, brillos = [], destellos = [], estelaDato, puntaPistas = false, giros = [] }) => {
  const g = geometriaPoderes(achica);
  const mitad = g.lado / 2;
  const tramos = [0, 1].map((i) => ({ x0: g.xs[i] + mitad, x1: g.xs[i + 1] - mitad }));
  const camino = `M ${g.xs[0]} ${g.y} L ${g.xs[2]} ${g.y}`;
  return (
    <>
      {tramos.map((t, i) => (
        <PistaLinea key={`l${i}`} x0={t.x0} x1={t.x1} y={g.y} progreso={pistas} />
      ))}
      {estelaDato === undefined ? (
        <PuntoDato d={camino} progreso={dato} />
      ) : (
        <DatoViajero d={camino} progreso={dato} radio={RADIO_DATO} estela={estelaDato} />
      )}
      {g.xs.map((x, i) => (
        <NodoFlujo
          key={`n${i}`}
          cx={x}
          cy={g.y}
          lado={g.lado}
          radio={g.radio}
          icono={PODERES.iconos[i]}
          iconoAlto={g.icono}
          encendido={latidos[i]}
          brillo={brillos[i]}
          destello={destellos[i]}
          giro={giros[i] ?? 0}
          estilo={unir(estilosNodo[i], { transform: `scale(${1 + LATIDO_NODO * (latidos[i] ?? 0)})` })}
        />
      ))}
      {g.puerto > 0.5 &&
        tramos.map((t, i) => <PistaPuertos key={`p${i}`} x0={t.x0} x1={t.x1} y={g.y} progreso={pistas} radio={g.puerto} />)}
      {puntaPistas && tramos.map((t, i) => <PuntaLuz key={`c${i}`} d={`M ${t.x0} ${g.y} L ${t.x1} ${g.y}`} progreso={pistas} />)}
      {g.xs.map((x, i) => (
        <Texto key={`v${i}`} x={x} y={g.verboY} tam={g.verboTam} alinear="centro" estilo={estilosVerbo[i]}>
          {verbos[i]}
        </Texto>
      ))}
    </>
  );
};

/** Los tres nodos chicos, quietos, como en el cuadro final de D06.3 (para D15.1). */
export const PoderesChicos: React.FC<Omit<PropsPoderes, "achica">> = (props) => <Poderes {...props} achica={1} />;

/** La idea clave como en D06.3 (y en D15.1). */
export const IdeaPoderes: React.FC<{ texto: string; estilo?: Estilo; y?: number }> = ({ texto, estilo, y = IDEA_PODERES.y }) => (
  <Texto x={IDEA_PODERES.x} y={y} tam={IDEA_PODERES.tam} alinear="centro" resaltar={IDEA_PODERES.resaltar} estilo={estilo}>
    {texto}
  </Texto>
);

// ---------------------------------------------------------------------------------------
// D06.1: el flujo de D05, chico arriba
// ---------------------------------------------------------------------------------------

/**
 * Ajuste: el guion lo pide de 100 px en y 230. D05.3 deja ese mismo flujo achicado a 0,55 en
 * y 230 (nodos de 110 px con centros en x 580,5, 833,5, 1086,5 y 1339,5): se redibuja igual,
 * con el radio, el borde, las conexiones y el ícono a escala (medido contra el cuadro final de
 * D05: los bordes coinciden al píxel), así el fundido de entrada no lo duplica.
 */
const FLUJO_D05 = {
  y: 230,
  escala: 0.55,
  xs: [270, 730, 1190, 1650].map((x) => 960 + (x - 960) * 0.55),
  iconos: ["mobile-screen-button", "list-check", "wand-magic-sparkles", "table"] as NombreIcono[],
} as const;
const LADO_D05 = 200 * FLUJO_D05.escala;
const GROSOR_D05 = GROSOR.trazo_normal * FLUJO_D05.escala;

/** Las dos líneas de lo que no puede: desde x 520, con su cruz de 50 px en x 450 (guion). */
const NO_PUEDE = { x: 520, ys: [620, 730], cruzX: 450, cruzTam: 50, tam: TIPO.escala.frase } as const;
const TITULO1 = { y: 460 } as const;
const TITULO2 = { y: 170 } as const;

// ---------------------------------------------------------------------------------------
// D06.2: la cámara
// ---------------------------------------------------------------------------------------

/**
 * Ajuste: el guion pide que HACER aparezca primero y tranquilo, y después VER y PENSAR con un
 * golpe. Para que se lea que HACER es lo que ya había y que los otros dos se le suman, la cámara
 * empieza cerca de HACER (a 1,12, con su columna en el centro de la pantalla) y se aleja hasta
 * el cuadro del guion mientras entran los otros dos. Pantalla = (mundo menos foco) por escala
 * más centro. El título no está en la cámara.
 */
const CAMARA = {
  desde: { foco: [1500, 596], centro: [960, 560], escala: 1.12 },
  hasta: { foco: [960, 540], centro: [960, 540], escala: 1 },
} as const;

function transformCamara(k: number): Estilo {
  const e = lerp(CAMARA.desde.escala, CAMARA.hasta.escala, k);
  const fx = lerp(CAMARA.desde.foco[0], CAMARA.hasta.foco[0], k);
  const fy = lerp(CAMARA.desde.foco[1], CAMARA.hasta.foco[1], k);
  const cx = lerp(CAMARA.desde.centro[0], CAMARA.hasta.centro[0], k);
  const cy = lerp(CAMARA.desde.centro[1], CAMARA.hasta.centro[1], k);
  return { transform: `translate(${cx - fx * e}px, ${cy - fy * e}px) scale(${e})`, transformOrigin: "0px 0px" };
}

/** Los logos de lo que da cada poder, tal cual (sin recolorear), con su proporción. */
const LOGO_SERPAPI = { src: "logos/serpapi/logo-with-wordmark-white.svg", proporcion: 1764 / 439 } as const;
const LOGO_N8N = { src: "logos/n8n/n8n-logo-white-accent.svg", proporcion: 480 / 96 } as const;

const Logo: React.FC<{ src: string; proporcion: number; cx: number; cy: number; alto: number; estilo?: Estilo }> = ({ src, proporcion, cx, cy, alto, estilo }) => {
  const ancho = alto * proporcion;
  return <Img src={staticFile(src)} style={{ position: "absolute", left: cx - ancho / 2, top: cy - alto / 2, width: ancho, height: alto, ...estilo }} />;
};

// ---------- Tiempos (s desde el comienzo de cada paso; los últimos 0,3 s, quietos) ----------
// D06.1 (2,9 s propios) 0,15-0,95 el dato recorre el flujo chico (cada nodo late al pasar),
//        1,0-1,3 el flujo pasa a Foco, 0,95 el título, 1,4 y 1,8 las dos líneas, con su cruz
//        0,15 s después (0,3 s).
// D06.2 (5,4 s) 0-0,3 se va lo anterior, 0,3-0,6 se apagan las luces del fondo, 0,4 HACER
//        (fundido 0,4 s) y su columna, 0,4-1,3 sus engranajes giran hasta asentarse, 0,85-1,45
//        la cámara se aleja. 1,4 VER con golpe y fogonazo del borde (con la cámara ya quieta: si
//        el golpe empezaba antes, VER caía cortado en el borde) y 1,5-2,2 su haz barre el cielo.
//        2,1 PENSAR con golpe y fogonazo y 2,15-3,15 su red: se dibuja (0,5 s), late y se
//        apaga. 2,85 el título con golpe y 3,2-3,7 su barrido de luz. 3,1-3,55 las pistas con
//        su chispa, 3,55-4,55 el dato con estela (late VER, PENSAR y HACER al pasar, con brillo
//        ámbar, hasta 4,8, y les queda el brillo azul de lo activo). 0,6 s quietos.
// D06.3 (3,1 s) 0-0,3 se van el título, los logos, IA y el brillo de los nodos, 0,1-0,7 los
//        nodos se achican y suben, 0,7 la idea, 1,15, 1,33 y 1,51 se encienden vea, piense y
//        haga, cada una con el latido de su nodo.
const T1 = { dato: 0.15, datoDura: 0.8, foco: 1.0, titulo: 0.95, lineas: [1.4, 1.8], cruzDesfase: 0.15, cruzDura: 0.3 } as const;
const T2 = {
  hacer: 0.4, giroDura: 0.9, camara: 0.85, camaraDura: 0.6,
  ver: 1.4, haz: 1.5, hazDura: 0.7,
  pensar: 2.1, red: 2.15, redDura: 1.0,
  titulo: 2.85, barridoTitulo: 3.2,
  textosDesfase: 0.15, pistas: 3.1, pistasDura: 0.45, dato: 3.55, datoDura: 1.0,
} as const;
const T3 = { achica: 0.1, achicaDura: 0.6, idea: 0.7, palabras: [1.15, 1.33, 1.51], destelloDura: 0.32 } as const;

/**
 * La luz de D06.2. Las luces del fondo bajan a 0,22 mientras HACER está solo y vuelven en dos
 * escalones, cada uno con un superpoder: el haz de VER las sube a 0,6 y la red de PENSAR, al
 * latir, a 1. Cada latido empieza 0,1 s antes de que el dato llegue al centro del nodo.
 * Ajuste: los engranajes de HACER arrancan 40 grados atrás y vuelven a 0 al asentarse, así el
 * cuadro final dibuja el ícono de siempre.
 */
const LUZ2 = {
  apaga: 0.3, apagaDura: 0.3, baja: 0.78, conHaz: 0.38, conRed: 0.4,
  destelloDura: 0.1, latidoAdelanto: 0.1, azulActivo: 0.45, estela: 6, giro: -40,
} as const;

// ---------------------------------------------------------------------------------------
// VER mira: el haz
// ---------------------------------------------------------------------------------------

/**
 * Las estrellas del fondo, las mismas de diseno/medios/D01/generar_fondo.py (semilla fija): x, y,
 * su opacidad en el PNG y si es de las brillantes. El haz enciende las que toca.
 */
const ESTRELLAS: [number, number, number, number][] = [
  [1400, 102, 0.80, 1], [894, 933, 0.80, 1], [1261, 69, 0.80, 1], [76, 186, 0.80, 1], [1186, 66, 0.80, 1], [1845, 961, 0.80, 1], [1460, 1032, 0.80, 1], [1515, 57, 0.80, 1],
  [1548, 148, 0.80, 1], [503, 920, 0.80, 1], [1112, 62, 0.43, 0], [941, 87, 0.34, 0], [1805, 217, 0.43, 0], [112, 507, 0.46, 0], [397, 88, 0.30, 0], [1163, 914, 0.44, 0],
  [836, 65, 0.30, 0], [1723, 273, 0.40, 0], [1786, 168, 0.42, 0], [436, 74, 0.48, 0], [1265, 1029, 0.46, 0], [518, 64, 0.43, 0], [77, 228, 0.48, 0], [692, 921, 0.55, 0],
  [741, 70, 0.55, 0], [1724, 57, 0.44, 0], [689, 1036, 0.35, 0], [115, 625, 0.46, 0], [420, 81, 0.27, 0], [1671, 150, 0.47, 0], [1637, 173, 0.36, 0], [1411, 1026, 0.49, 0],
  [1234, 103, 0.60, 0], [1776, 52, 0.31, 0], [1491, 166, 0.36, 0], [612, 115, 0.40, 0], [1736, 160, 0.36, 0], [820, 915, 0.32, 0], [385, 62, 0.45, 0], [113, 884, 0.36, 0],
  [542, 106, 0.39, 0], [951, 57, 0.55, 0], [448, 1033, 0.31, 0], [1648, 74, 0.60, 0], [1282, 103, 0.29, 0], [1763, 69, 0.35, 0], [991, 1036, 0.31, 0], [125, 1017, 0.29, 0],
  [630, 66, 0.26, 0], [1726, 174, 0.58, 0], [1316, 91, 0.51, 0], [759, 54, 0.44, 0], [1450, 44, 0.41, 0], [1799, 49, 0.44, 0], [1757, 273, 0.46, 0], [435, 89, 0.29, 0],
  [1619, 164, 0.26, 0], [684, 112, 0.32, 0], [471, 1022, 0.47, 0], [98, 254, 0.60, 0], [1668, 1029, 0.44, 0], [1062, 68, 0.35, 0], [1417, 51, 0.31, 0], [1434, 65, 0.45, 0],
  [1356, 69, 0.27, 0], [1800, 272, 0.52, 0], [1295, 1028, 0.57, 0], [1793, 68, 0.46, 0], [1073, 50, 0.30, 0], [989, 89, 0.36, 0], [1779, 97, 0.29, 0], [1578, 65, 0.60, 0],
  [1306, 104, 0.52, 0], [82, 246, 0.40, 0], [1122, 913, 0.42, 0], [772, 915, 0.26, 0], [1700, 1033, 0.57, 0], [1791, 202, 0.34, 0], [884, 44, 0.36, 0], [1044, 45, 0.34, 0],
  [1579, 82, 0.27, 0], [1398, 57, 0.50, 0], [1639, 49, 0.33, 0], [1460, 147, 0.52, 0], [1167, 1030, 0.53, 0], [872, 101, 0.33, 0], [944, 914, 0.33, 0], [922, 45, 0.35, 0],
  [1752, 158, 0.55, 0], [1719, 1019, 0.27, 0], [395, 50, 0.35, 0], [1812, 1018, 0.32, 0], [1361, 47, 0.41, 0], [966, 1022, 0.46, 0], [404, 76, 0.26, 0], [156, 939, 0.47, 0],
  [101, 585, 0.57, 0], [241, 1029, 0.28, 0], [724, 59, 0.50, 0], [1699, 265, 0.36, 0], [488, 91, 0.32, 0], [1809, 74, 0.55, 0], [851, 925, 0.51, 0], [531, 46, 0.41, 0],
  [421, 1023, 0.30, 0], [117, 950, 0.28, 0], [816, 90, 0.45, 0], [903, 53, 0.47, 0], [1016, 46, 0.47, 0], [1137, 1030, 0.58, 0], [391, 108, 0.44, 0], [135, 978, 0.48, 0],
  [1737, 1031, 0.54, 0], [1660, 87, 0.49, 0], [1776, 1020, 0.35, 0], [1726, 240, 0.59, 0], [807, 80, 0.27, 0], [1017, 968, 0.54, 0], [1439, 153, 0.57, 0], [1843, 90, 0.45, 0],
  [1593, 165, 0.41, 0], [88, 976, 0.56, 0], [795, 1030, 0.44, 0], [1785, 1032, 0.50, 0], [1249, 913, 0.50, 0], [1106, 923, 0.56, 0], [772, 1032, 0.26, 0], [97, 511, 0.33, 0],
  [1484, 183, 0.24, 0], [1468, 187, 0.25, 0], [1503, 187, 0.24, 0], [1582, 238, 0.29, 0],
];

/**
 * El haz de VER. Sale del centro de la lupa (queda detrás del nodo) y barre el cielo una vez, de
 * izquierda a derecha por arriba, como un faro. Ángulos en grados de pantalla (0 a la derecha, 90
 * abajo). El título todavía no está, así que el haz no cruza ningún texto: termina apuntando por
 * encima de HACER, lejos de su rótulo.
 * Ajuste: 44 grados de cuña con los bordes suaves (el guion pide unos 40), luz azul clara al 30 %
 * cerca del nodo que se pierde hacia el borde de la pantalla.
 */
const HAZ = {
  origen: [420, 480] as const,
  desde: -168, hasta: -28,
  ancho: 44,
  alfa: 0.3,
  color: mezclaHex(COLOR.azul, COLOR.hueso, 0.5),
  /** Lo que tarda en encenderse y en apagarse, como fracción del barrido. */
  sube: 0.16, baja: 0.3,
} as const;

/** Cuánto ilumina el haz a `delta` grados de su centro: 1 en el centro, 0 en el borde de la cuña. */
function perfilHaz(delta: number): number {
  const d = Math.abs(delta) / (HAZ.ancho / 2);
  return d >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * d);
}

const HazVer: React.FC<{ p: number }> = ({ p }) => {
  if (p <= 0 || p >= 1) return null;
  const env = CURVA.suave(entre01(p / HAZ.sube)) * CURVA.suave(entre01((1 - p) / HAZ.baja));
  if (env <= 0.001) return null;
  const centro = lerp(HAZ.desde, HAZ.hasta, CURVA.suave(p));
  const [ox, oy] = HAZ.origen;
  // conic-gradient mide desde arriba y en sentido horario: grados de pantalla más 90.
  const desde = centro + 90 - HAZ.ancho / 2;
  const pasos = 8;
  const paradas = Array.from({ length: pasos + 1 }, (_, i) => {
    const a = (HAZ.ancho * i) / pasos;
    return `${conAlfa(HAZ.color, HAZ.alfa * env * perfilHaz(a - HAZ.ancho / 2))} ${a.toFixed(2)}deg`;
  });
  const cono = `conic-gradient(from ${desde.toFixed(2)}deg at ${ox}px ${oy}px, ${paradas.join(", ")}, transparent ${HAZ.ancho}deg)`;
  const lejos = `radial-gradient(circle at ${ox}px ${oy}px, #000 0px, #000 160px, rgba(0,0,0,0.6) 650px, rgba(0,0,0,0.18) 1250px, rgba(0,0,0,0) 1700px)`;

  const encendidas: React.ReactNode[] = [];
  ESTRELLAS.forEach(([x, y, , grande], i) => {
    const dx = x - ox;
    const dy = y - oy;
    const r = Math.hypot(dx, dy);
    if (r < 160) return;
    let delta = (Math.atan2(dy, dx) * 180) / Math.PI - centro;
    delta = ((((delta + 180) % 360) + 360) % 360) - 180;
    const k = env * perfilHaz(delta) * (1 - 0.35 * entre01((r - 300) / 1200));
    if (k < 0.03) return;
    const nucleo = (grande ? 5.5 : 4) * (0.75 + 0.25 * k);
    encendidas.push(
      <g key={i}>
        <circle cx={x} cy={y} r={nucleo * 3.2} fill={conAlfa(HAZ.color, 0.28 * k)} />
        <circle cx={x} cy={y} r={nucleo} fill={conAlfa(COLOR.hueso, Math.min(1, 1.15 * k))} />
      </g>,
    );
  });

  return (
    <>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, backgroundImage: cono, WebkitMaskImage: lejos, maskImage: lejos }} />
      <svg width={1920} height={1080} style={{ ...svgPantalla, filter: `drop-shadow(0 0 6px ${conAlfa(COLOR.hueso, 0.7)})` }}>
        {encendidas}
      </svg>
    </>
  );
};

// ---------------------------------------------------------------------------------------
// PENSAR conecta: la red
// ---------------------------------------------------------------------------------------

/**
 * La red de PENSAR: once estrellas puestas a mano alrededor del cerebro y doce líneas finas que
 * las unen, como una constelación o una red de neuronas. Se dibuja desde arriba del nodo hacia los
 * dos lados y baja, late una vez y se apaga. Las estrellas quedan fuera del nodo (x 820 a 1100, y
 * 340 a 620), lejos de los otros dos, por debajo de donde va a caer el título (y 290 o más) y al
 * costado del rótulo PENSAR (x 822 a 1098 desde y 670).
 */
const RED = {
  puntos: {
    c: [960, 292], b: [812, 318], d: [1112, 312], a: [700, 384], e: [1226, 380],
    f: [664, 486], g: [1262, 492], h: [712, 588], k: [1218, 594], i: [800, 646], j: [1128, 650],
  } as Record<string, [number, number]>,
  // De dónde a dónde y cuándo empieza (s desde que arranca la red): se abre desde arriba hacia los dos lados.
  lineas: [
    ["c", "b", 0.0], ["c", "d", 0.0], ["b", "a", 0.07], ["d", "e", 0.07], ["b", "f", 0.12], ["d", "g", 0.12],
    ["a", "f", 0.17], ["e", "g", 0.17], ["f", "h", 0.23], ["g", "k", 0.23], ["h", "i", 0.3], ["k", "j", 0.3],
  ] as [string, string, number][],
  trazo: 0.19,
  late: 0.5, lateDura: 0.22,
  apaga: 0.7, apagaDura: 0.3,
  grosor: 4, radio: 6.5,
  color: mezclaHex(COLOR.azul, COLOR.hueso, 0.35),
} as const;

const RedPensar: React.FC<{ t: number }> = ({ t }) => {
  if (t <= 0 || t >= RED.apaga + RED.apagaDura) return null;
  const late = Math.sin(Math.PI * entre01((t - RED.late) / RED.lateDura));
  const queda = 1 - CURVA.suave(entre01((t - RED.apaga) / RED.apagaDura));
  const alfa = (0.8 + 0.2 * late) * queda;
  // Cuándo se enciende cada estrella: cuando llega la primera línea (la de arriba, al empezar).
  const llega: Record<string, number> = { c: 0 };
  RED.lineas.forEach(([, hasta, t0]) => {
    const fin = t0 + RED.trazo;
    llega[hasta] = Math.min(llega[hasta] ?? Infinity, fin);
  });
  return (
    <svg width={1920} height={1080} style={{ ...svgPantalla, filter: `drop-shadow(0 0 ${5 + 6 * late}px ${conAlfa(COLOR.azul, 0.9)})` }}>
      {RED.lineas.map(([de, hasta, t0], i) => {
        const p = CURVA.sale(entre01((t - t0) / RED.trazo));
        if (p <= 0) return null;
        const [x0, y0] = RED.puntos[de];
        const [x1, y1] = RED.puntos[hasta];
        const x = lerp(x0, x1, p);
        const y = lerp(y0, y1, p);
        return (
          <g key={i}>
            <line x1={x0} y1={y0} x2={x} y2={y} stroke={RED.color} strokeWidth={RED.grosor + late} strokeLinecap="round" opacity={alfa} />
            {p < 1 && <circle cx={x} cy={y} r={4.5} fill={COLOR.hueso} opacity={queda} />}
          </g>
        );
      })}
      {Object.entries(RED.puntos).map(([n, [x, y]]) => {
        const aparece = CURVA.sale(entre01((t - (llega[n] ?? 0)) / 0.12));
        if (aparece <= 0) return null;
        return <circle key={n} cx={x} cy={y} r={(RED.radio + 2.5 * late) * (0.5 + 0.5 * aparece)} fill={COLOR.hueso} opacity={aparece * queda} />;
      })}
    </svg>
  );
};

// ---------------------------------------------------------------------------------------
// D06.3: cada palabra se enciende con su nodo
// ---------------------------------------------------------------------------------------

/** Las tres palabras en ámbar de la idea, en el orden de los nodos. */
const PALABRAS = ["vea", "piense", "haga"] as const;
/** El color de la palabra encendida (ámbar hacia el hueso, tono 35°) y su resplandor ámbar. */
const ENCENDIDA = {
  color: mezclar(COLOR.ambar, COLOR.hueso, 0.5),
  sombra: `0 0 14px ${conAlfa(COLOR.ambar, 0.95)}, 0 0 36px ${conAlfa(COLOR.ambar, 0.55)}`,
  borde: 22,
} as const;

/**
 * Una copia exacta de la idea encima de la de siempre, con la parte en ámbar pasada a ENCENDIDA y
 * una máscara que deja ver solo una palabra (los bordes de la máscara, suaves). Como es el mismo
 * Texto con los mismos cortes, las letras caen justo encima. Con fuerza 0 no dibuja nada.
 */
const PalabraEncendida: React.FC<{ texto: string; palabra: string; fuerza: number; estilo?: Estilo }> = ({ texto, palabra, fuerza, estilo }) => {
  if (fuerza <= 0.002) return null;
  const tam = IDEA_PODERES.tam;
  const izquierda = IDEA_PODERES.x - medirTexto(texto, tam) / 2;
  const i = texto.indexOf(palabra);
  const x0 = izquierda + medirTexto(texto.slice(0, i), tam);
  const x1 = izquierda + medirTexto(texto.slice(0, i + palabra.length), tam);
  const b = ENCENDIDA.borde;
  const mascara = `linear-gradient(90deg, transparent ${x0 - b}px, #000 ${x0}px, #000 ${x1}px, transparent ${x1 + b}px)`;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, WebkitMaskImage: mascara, maskImage: mascara }}>
      <Texto
        x={IDEA_PODERES.x}
        y={IDEA_PODERES.y}
        tam={tam}
        alinear="centro"
        resaltar={{ [IDEA_PODERES.resaltar]: ENCENDIDA.color }}
        estilo={unir(estilo, { opacity: fuerza, textShadow: ENCENDIDA.sombra })}
      >
        {texto}
      </Texto>
    </div>
  );
};

export const D06DosSuperpoderes: React.FC = () => {
  const t1 = textos("D06", 1); // ["Un flujo común solo hace.", "No ve lo que pasa en internet.", "No piensa."]
  const t2 = textos("D06", 2); // ["Dos superpoderes", "VER", "PENSAR", "HACER", "IA"]
  const t3 = textos("D06", 3); // ["Que el flujo vea, piense y haga."]
  if (t3[0] !== IDEA_CLAVE) throw new Error(`D06.3: la idea (${t3[0]}) tiene que ser la idea clave del deck (${IDEA_CLAVE}).`);
  const verbos = [t2[1], t2[2], t2[3]];

  // ---- Paso 1 ----
  const datoD05 = useTramo(1, T1.dato, T1.datoDura, CURVA.lineal);
  const latidosD05 = [0, 1, 2, 3].map((i) => useLatido(1, T1.dato + (T1.datoDura * i) / 3)); // largo fijo: el orden de los hooks no cambia
  const titulo1 = useEntrar(1, T1.titulo);
  const lineas = [useEntrar(1, T1.lineas[0], { desde: "izq" }), useEntrar(1, T1.lineas[1], { desde: "izq" })];
  const cruces = [useTramo(1, T1.lineas[0] + T1.cruzDesfase, T1.cruzDura), useTramo(1, T1.lineas[1] + T1.cruzDesfase, T1.cruzDura)];
  const sale1 = useDesvanecer(2, 0, 0.3);

  // ---- Paso 2 ----
  const titulo2 = unir(useGolpe(2, T2.titulo), useDesvanecer(3, 0, 0.3));
  const hacer = useAparecer(2, T2.hacer, 0.4);
  const hacerAsienta = useTramo(2, T2.hacer, 0.6, CURVA.sale);
  const hacerTextos = useAparecer(2, T2.hacer + T2.textosDesfase, 0.4);
  const giroHacer = LUZ2.giro * (1 - useTramo(2, T2.hacer, T2.giroDura, CURVA.sale));
  const camara = useTramo(2, T2.camara, T2.camaraDura, CURVA.suave);
  const golpeVer = useGolpe(2, T2.ver);
  const golpePensar = useGolpe(2, T2.pensar);
  const textosVer = useEntrar(2, T2.ver + T2.textosDesfase);
  const textosPensar = useEntrar(2, T2.pensar + T2.textosDesfase);
  const haz = useTramo(2, T2.haz, T2.hazDura, CURVA.lineal);
  const red = useTramo(2, T2.red, T2.redDura, CURVA.lineal) * T2.redDura;
  const pistas = useTramo(2, T2.pistas, T2.pistasDura, CURVA.suave);
  const dato = useTramo(2, T2.dato, T2.datoDura, CURVA.lineal);
  const inicioLatidos = [0, 1, 2].map((i) => T2.dato - LUZ2.latidoAdelanto + (T2.datoDura * i) / 2);
  const latidos2 = inicioLatidos.map((t) => useLatido(2, t));
  const salenLogos = useDesvanecer(3, 0, 0.3);

  // ---- La luz de D06.2 ----
  const apaga = useTramo(2, LUZ2.apaga, LUZ2.apagaDura);
  const conHaz = useTramo(2, T2.haz + 0.1, T2.hazDura - 0.1);
  const conRed = useTramo(2, T2.red + RED.late - 0.1, 0.45);
  const luz = 1 - LUZ2.baja * apaga + LUZ2.conHaz * conHaz + LUZ2.conRed * conRed; // 1 en D06.1 y en D06.3
  const destellos = [useDestello(2, T2.ver, LUZ2.destelloDura), useDestello(2, T2.pensar, LUZ2.destelloDura), 0];
  // VER y PENSAR se quedan con el brillo azul de lo activo desde que hacen lo suyo (más fuerte
  // mientras el haz barre y mientras la red late). HACER lo recibe cuando el dato pasa por él.
  // Todo se apaga con los logos en D06.3.
  const enciendeVer = useTramo(2, T2.haz, 0.25, CURVA.suave);
  const enciendePensar = useTramo(2, T2.red, 0.25, CURVA.suave);
  const quedaHacer = useTramo(2, inicioLatidos[2] + LATIDO_DURA / 2, LATIDO_DURA / 2, CURVA.suave);
  const envHaz = haz > 0 && haz < 1 ? Math.sin(Math.PI * haz) : 0;
  const lateRed = Math.sin(Math.PI * entre01((red - RED.late) / RED.lateDura));
  const apagaAzul = useTramo(3, 0, 0.3, CURVA.fundido);
  const azules = [
    LUZ2.azulActivo * enciendeVer + 0.45 * envHaz,
    LUZ2.azulActivo * enciendePensar + 0.4 * lateRed,
    LUZ2.azulActivo * quedaHacer,
  ];

  // ---- Paso 3 ----
  const achica = useTramo(3, T3.achica, T3.achicaDura, CURVA.suave);
  const idea = useEntrar(3, T3.idea);
  const latidos3 = T3.palabras.map((t) => useLatido(3, t));
  const encendidas = T3.palabras.map((t) => useDestello(3, t, T3.destelloDura));

  const latidos = [0, 1, 2].map((i) => latidos2[i] + latidos3[i]);
  const brillos: LuzNodo[][] = [0, 1, 2].map((i) => [
    { color: COLOR.ambar, k: latidos[i] },
    { color: COLOR.azul, k: azules[i] * (1 - apagaAzul) },
  ]);
  const estilosNodo = [golpeVer, golpePensar, unir(hacer, { transform: `scale(${0.96 + 0.04 * hacerAsienta})` })];
  const estilosVerbo = [textosVer, textosPensar, hacerTextos];
  const logos = PODERES.logos;
  const xs = PODERES.grande.xs;

  return (
    <>
      {/* Debajo de todo, quieto aunque la cámara se mueva: el fondo de la charla, que se apaga en D06.2. */}
      <FondoVivo pulsos={[1]} luz={luz} />

      {/* D06.1 */}
      <Capa estilo={sale1}>
        <Foco paso={1} retraso={T1.foco}>
          {FLUJO_D05.xs.slice(0, -1).map((x, i) => (
            <PistaLinea key={`l${i}`} x0={x + LADO_D05 / 2} x1={FLUJO_D05.xs[i + 1] - LADO_D05 / 2} y={FLUJO_D05.y} grosor={GROSOR_D05} />
          ))}
          <PuntoDato d={`M ${FLUJO_D05.xs[0]} ${FLUJO_D05.y} L ${FLUJO_D05.xs[3]} ${FLUJO_D05.y}`} progreso={datoD05} />
          {FLUJO_D05.xs.map((x, i) => (
            <NodoFlujo
              key={`n${i}`}
              cx={x}
              cy={FLUJO_D05.y}
              lado={LADO_D05}
              radio={RADIO_NODO * FLUJO_D05.escala}
              grosor={GROSOR_D05}
              icono={FLUJO_D05.iconos[i]}
              encendido={latidosD05[i]}
              estilo={{ transform: `scale(${1 + LATIDO_NODO * latidosD05[i]})` }}
            />
          ))}
        </Foco>
        <Texto x={960} y={TITULO1.y} tam="idea" color={COLOR.titulo} alinear="centro" estilo={titulo1}>
          {t1[0]}
        </Texto>
        {[0, 1].map((i) => (
          <React.Fragment key={`np${i}`}>
            <Cruz x={NO_PUEDE.cruzX} y={NO_PUEDE.ys[i]} tam={NO_PUEDE.cruzTam} grosor={grosorAsta(NO_PUEDE.tam)} progreso={cruces[i]} />
            <Texto x={NO_PUEDE.x} y={NO_PUEDE.ys[i]} tam={NO_PUEDE.tam} estilo={lineas[i]}>
              {t1[i + 1]}
            </Texto>
          </React.Fragment>
        ))}
      </Capa>

      {/* D06.2: lo que hace cada superpoder, sobre el fondo y debajo de los nodos (la cámara ya está quieta). */}
      <HazVer p={haz} />
      <RedPensar t={red} />

      {/* D06.2 y D06.3 */}
      <BarridoLuz paso={2} retraso={T2.barridoTitulo}>
        <Texto x={960} y={TITULO2.y} tam="grande" color={COLOR.titulo} alinear="centro" estilo={titulo2}>
          {t2[0]}
        </Texto>
      </BarridoLuz>
      <Capa estilo={transformCamara(camara)}>
        <Poderes
          verbos={verbos}
          achica={achica}
          estilosNodo={estilosNodo}
          estilosVerbo={estilosVerbo}
          pistas={pistas}
          latidos={latidos}
          dato={dato}
          brillos={brillos}
          destellos={destellos}
          estelaDato={LUZ2.estela}
          puntaPistas
          giros={[0, 0, giroHacer]}
        />
        <Logo {...LOGO_SERPAPI} cx={xs[0]} cy={logos.y} alto={logos.alto} estilo={unir(textosVer, salenLogos)} />
        <Texto x={xs[1]} y={logos.y} tam="frase" alinear="centro" estilo={unir(textosPensar, salenLogos)}>
          {t2[4]}
        </Texto>
        <Logo {...LOGO_N8N} cx={xs[2]} cy={logos.y} alto={logos.alto} estilo={unir(hacerTextos, salenLogos)} />
      </Capa>

      <IdeaPoderes texto={t3[0]} estilo={idea} />
      {PALABRAS.map((p, i) => (
        <PalabraEncendida key={p} texto={t3[0]} palabra={p} fuerza={encendidas[i]} estilo={idea} />
      ))}
    </>
  );
};
