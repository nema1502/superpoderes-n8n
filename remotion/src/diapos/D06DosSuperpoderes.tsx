// D06 Ver, pensar, hacer (contenido/guion.md, D06). La revelación de los dos superpoderes y
// la imagen central de la charla: tres nodos, VER, PENSAR y HACER, unidos por pistas de
// circuito por donde viaja el dato en ámbar.
//
//   D06.1  El flujo de D05 queda chico arriba, en el mismo lugar donde lo deja D05.3. El dato
//          lo recorre una vez, siempre igual, y el flujo pasa a Foco. Sube Un flujo común solo
//          hace. y, de a una, las dos cosas que no puede, cada una con su cruz roja.
//   D06.2  Dos superpoderes. Se apagan las luces y HACER aparece primero, solo y tranquilo, con
//          la cámara cerca: es el que ya existía. La cámara se aleja y entran VER y PENSAR con un
//          golpe, un aro y un fogonazo del borde, y con ellos vuelve la luz. Las pistas se dibujan
//          de puerto a puerto con una chispa en la punta y el dato las recorre con su estela:
//          cada nodo late con brillo ámbar cuando pasa y queda encendido en azul.
//   D06.3  Los logos se van, los tres nodos se achican y suben, y entra la idea clave con su
//          barrido de luz.
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
  Aro,
  BarridoLuz,
  brillo,
  Capa,
  COLOR,
  Cruz,
  CURVA,
  DatoViajero,
  Foco,
  FondoVivo,
  GROSOR,
  grosorAsta,
  Icono,
  IDEA_CLAVE,
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

// Las duraciones de deck.json: 3,3 (con el fundido de 0,4 adentro), 4,5 y 3,1 s.
export const pasos = pasosDe("D06");

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
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
export const NodoFlujo: React.FC<PropsNodoFlujo> = ({ cx, cy, lado, icono, iconoCaja, iconoAlto, radio = RADIO_NODO, grosor = GROSOR.trazo_normal, encendido = 0, estilo, brillo: luz, destello = 0 }) => {
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
      <Icono nombre={icono} alto={altoIcono} x={cx} y={cy} />
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

export const Poderes: React.FC<PropsPoderes> = ({ verbos, achica = 0, estilosNodo = [], estilosVerbo = [], pistas = 1, latidos = [0, 0, 0], dato = 0, brillos = [], destellos = [], estelaDato, puntaPistas = false }) => {
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
// D06.2 (4,5 s) 0-0,3 se va lo anterior, 0,3-0,6 se apagan las luces del fondo, 0,15 el
//        título, 0,4 HACER (fundido 0,4 s) y su columna, 0,85-1,45 la cámara se aleja, 1,35 VER
//        y 1,65 PENSAR con golpe, aro y fogonazo del borde (con la cámara ya quieta: si el golpe
//        empezaba antes, VER caía cortado en el borde), 1,3-2,1 vuelven las luces, 2,1-2,6 las
//        pistas con su chispa, 2,65-3,75 el dato con estela (late VER, PENSAR y HACER al pasar,
//        con brillo ámbar, hasta 4,0, y les queda el brillo azul de lo activo).
// D06.3 (3,1 s) 0-0,3 se van el título, los logos, IA y el brillo de los nodos, 0,1-0,7 los
//        nodos se achican y suben, 0,7 la idea, 1,3-1,8 el barrido de luz.
const T1 = { dato: 0.15, datoDura: 0.8, foco: 1.0, titulo: 0.95, lineas: [1.4, 1.8], cruzDesfase: 0.15, cruzDura: 0.3 } as const;
const T2 = { titulo: 0.15, hacer: 0.4, camara: 0.85, camaraDura: 0.6, ver: 1.35, pensar: 1.65, textosDesfase: 0.15, pistas: 2.1, pistasDura: 0.5, dato: 2.65, datoDura: 1.1 } as const;
const T3 = { achica: 0.1, achicaDura: 0.6, idea: 0.7, barrido: 1.3 } as const;

/**
 * La luz de D06.2. Las luces del fondo bajan a 0,35 mientras HACER está solo y vuelven cuando
 * llegan VER y PENSAR: los superpoderes traen la luz. Cada latido empieza 0,1 s antes de que el
 * dato llegue al centro del nodo, así el último termina a los 4,0 s y quedan 0,5 s quietos.
 */
const LUZ2 = {
  apaga: 0.3, apagaDura: 0.3, vuelve: 1.3, vuelveDura: 0.8, baja: 0.65,
  aro: { desde: 280, hasta: 420, radioEsquina: 0.114, grosor: 5, dura: 0.5 },
  destelloDura: 0.1, latidoAdelanto: 0.1, azulActivo: 0.45, estela: 6,
} as const;

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
  const titulo2 = unir(useEntrar(2, T2.titulo), useDesvanecer(3, 0, 0.3));
  const hacer = useAparecer(2, T2.hacer, 0.4);
  const hacerAsienta = useTramo(2, T2.hacer, 0.6, CURVA.sale);
  const hacerTextos = useAparecer(2, T2.hacer + T2.textosDesfase, 0.4);
  const camara = useTramo(2, T2.camara, T2.camaraDura, CURVA.suave);
  const golpeVer = useGolpe(2, T2.ver);
  const golpePensar = useGolpe(2, T2.pensar);
  const textosVer = useEntrar(2, T2.ver + T2.textosDesfase);
  const textosPensar = useEntrar(2, T2.pensar + T2.textosDesfase);
  const pistas = useTramo(2, T2.pistas, T2.pistasDura, CURVA.suave);
  const dato = useTramo(2, T2.dato, T2.datoDura, CURVA.lineal);
  const inicioLatidos = [0, 1, 2].map((i) => T2.dato - LUZ2.latidoAdelanto + (T2.datoDura * i) / 2);
  const latidos = inicioLatidos.map((t) => useLatido(2, t));
  const salenLogos = useDesvanecer(3, 0, 0.3);

  // ---- La luz de D06.2 ----
  const apaga = useTramo(2, LUZ2.apaga, LUZ2.apagaDura);
  const vuelve = useTramo(2, LUZ2.vuelve, LUZ2.vuelveDura);
  const luz = 1 - LUZ2.baja * apaga + LUZ2.baja * vuelve; // 1 en D06.1 y en D06.3
  const destellos = [useDestello(2, T2.ver, LUZ2.destelloDura), useDestello(2, T2.pensar, LUZ2.destelloDura), 0];
  // Del pico del latido al final, a cada nodo le queda el brillo azul de lo activo, que se apaga con los logos en D06.3.
  const quedaAzul = inicioLatidos.map((t) => useTramo(2, t + LATIDO_DURA / 2, LATIDO_DURA / 2, CURVA.suave));
  const apagaAzul = useTramo(3, 0, 0.3, CURVA.fundido);
  const brillos: LuzNodo[][] = [0, 1, 2].map((i) => [
    { color: COLOR.ambar, k: latidos[i] },
    { color: COLOR.azul, k: LUZ2.azulActivo * quedaAzul[i] * (1 - apagaAzul) },
  ]);

  // ---- Paso 3 ----
  const achica = useTramo(3, T3.achica, T3.achicaDura, CURVA.suave);
  const idea = useEntrar(3, T3.idea);

  const estilosNodo = [golpeVer, golpePensar, unir(hacer, { transform: `scale(${0.96 + 0.04 * hacerAsienta})` })];
  const estilosVerbo = [textosVer, textosPensar, hacerTextos];
  const logos = PODERES.logos;
  const xs = PODERES.grande.xs;
  const g2 = PODERES.grande;
  const aro = LUZ2.aro;

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

      {/* D06.2 y D06.3 */}
      <Texto x={960} y={TITULO2.y} tam="grande" color={COLOR.titulo} alinear="centro" estilo={titulo2}>
        {t2[0]}
      </Texto>
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
        />
        {[T2.ver, T2.pensar].map((t, i) => (
          <Aro key={`aro${i}`} paso={2} retraso={t} cx={xs[i]} cy={g2.y} desde={aro.desde} hasta={aro.hasta} radioEsquina={aro.radioEsquina} color={COLOR.azul} grosor={aro.grosor} dura={aro.dura} />
        ))}
        <Logo {...LOGO_SERPAPI} cx={xs[0]} cy={logos.y} alto={logos.alto} estilo={unir(textosVer, salenLogos)} />
        <Texto x={xs[1]} y={logos.y} tam="frase" alinear="centro" estilo={unir(textosPensar, salenLogos)}>
          {t2[4]}
        </Texto>
        <Logo {...LOGO_N8N} cx={xs[2]} cy={logos.y} alto={logos.alto} estilo={unir(hacerTextos, salenLogos)} />
      </Capa>

      <BarridoLuz paso={3} retraso={T3.barrido}>
        <IdeaPoderes texto={t3[0]} estilo={idea} />
      </BarridoLuz>
    </>
  );
};
