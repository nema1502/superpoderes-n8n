// El ascensor en corte: el hueco con tres losas (tres pisos de 10 s), la cabina
// colgada del cable ámbar, el visor que dice a qué piso va y los rótulos de los pisos
// (piso 1 = frase XYZ, piso 2 = prueba, piso 3 = pedido) que se encienden. Es el mapa
// de D08 y el cronómetro de 30 s de D14.1, D19.2, D19.4, A8.2, A8.3 y A9.1.
//
// Hallazgos de la revisión (convenciones §13): paredes y losas de 5 px en hueso al 45 y 50 % (al 25
// y 30 % se perdían desde el fondo); la cabina abierta con luz de verdad (ámbar al 85 % arriba,
// que cae hacia abajo, y la tira en hueso); lo pendiente en gris; palomitas de 56 px con el
// grosor del asta del rótulo, en una columna; el globo «?» pegado a la cabina, encima de la
// pared, con la cola corta.
import { evolvePath } from "@remotion/paths";
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { s, tramoDe, usePasos } from "../pasos";
import { ASCENSOR_CORTE, COLOR, conAlfa, CURVA, FPS, GROSOR, ICONOS, MOV, OPACIDAD, RETICULA, TIPO, VISOR } from "../tokens";
import { Junta, PanelAcero } from "./Acero";
import { Globo } from "./Globo";
import { Icono, type NombreIcono } from "./Icono";
import { useRebote, type Estilo } from "./movimiento";
import { CuentaPrevia } from "./Reloj";
import { medirTexto } from "./Texto";
import { grosorAsta, Palomita } from "./Trazos";
import { useIdSvg, Visor7, VisorCaja, type PropsTriangulo } from "./Visor7";

const RELOJ = RETICULA.reloj;

export type PresetCorte = "mapa" | "crono";

export type GeoCorte = {
  x0: number;
  x1: number;
  xc: number;
  yTecho: number;
  ySuelo: number;
  losas: number[];
  visorY: number;
  rotulosX: number;
  rotuloPx: number;
  iconoPx: number;
  cabinaW: number;
  cabinaH: number;
  /** y del piso de la cabina en el piso k (0 = planta baja … 3), con k continuo. */
  pisoY: (k: number) => number;
  /** y del centro de la cabina en el piso k. */
  centroCabina: (k: number) => number;
  /** y de la mitad del recorrido de la cabina en el tramo k (1, 2, 3): ahí va su rótulo. */
  centroTramo: (k: number) => number;
};

/** Geometría de un preset («mapa»: D08; «crono»: D14 y D19), con ajustes opcionales. */
export function geometriaCorte(preset: PresetCorte = "crono", ajustes: Partial<Omit<GeoCorte, "pisoY" | "centroCabina" | "centroTramo">> = {}): GeoCorte {
  const p = ASCENSOR_CORTE[preset];
  const base = {
    x0: p.x0,
    x1: p.x1,
    xc: (p.x0 + p.x1) / 2,
    yTecho: p.y_techo,
    ySuelo: p.y_suelo,
    losas: [...p.losas],
    visorY: p.visor_y,
    rotulosX: p.rotulos_x,
    rotuloPx: p.rotulo_px,
    iconoPx: p.icono_px,
    cabinaW: ASCENSOR_CORTE.cabina.ancho,
    cabinaH: ASCENSOR_CORTE.cabina.alto,
    ...ajustes,
  };
  if (ajustes.x0 !== undefined || ajustes.x1 !== undefined) base.xc = (base.x0 + base.x1) / 2;
  const niveles = [base.ySuelo, ...base.losas];
  const pisoY = (k: number) => {
    const c = Math.max(0, Math.min(niveles.length - 1, k));
    const i = Math.min(niveles.length - 2, Math.floor(c));
    return niveles[i] + (niveles[i + 1] - niveles[i]) * (c - i);
  };
  const centroCabina = (k: number) => pisoY(k) - base.cabinaH / 2;
  const centroTramo = (k: number) => (centroCabina(k - 1) + centroCabina(k)) / 2;
  return { ...base, pisoY, centroCabina, centroTramo };
}

export type EstadoRotulo = {
  /** 0 → 1: entra (Entrar desde 40 px a la izquierda). */
  visible?: number;
  /** 0 → 1: se enciende en ámbar (el tramo en curso). */
  encendido?: number;
  /** 0 → 1: pasa a hueso con su palomita (el tramo hecho). */
  hecho?: number;
};

export type Rotulo = {
  /** Texto de deck.json: «1 · Frase XYZ» (D08) o «Frase XYZ» (D14, D19). */
  texto: string;
  estado: EstadoRotulo;
};

const pisoIcono = (k: number) => ICONOS.pisos[k] as NombreIcono;

function rgb(hex: string): number[] {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
}
function mezcla(a: number[], b: number[], k: number) {
  return a.map((v, i) => v + (b[i] - v) * Math.max(0, Math.min(1, k)));
}
const css = (c: number[]) => `rgb(${c.map((v) => Math.round(v)).join(",")})`;

/**
 * Color del rótulo según su estado: gris (pendiente: el único gris de apoyo, el mismo de los
 * «10 s») → ámbar (en curso) → hueso (hecho).
 */
function colorRotulo(e: EstadoRotulo) {
  const c1 = mezcla(rgb(COLOR.gris), rgb(COLOR.ambar), e.encendido ?? 0);
  return mezcla(c1, rgb(COLOR.hueso), e.hecho ?? 0);
}

/** Separación entre el ícono y el texto de un rótulo de piso. */
const sepIcono = (icono: number) => Math.round(icono * 0.36);

/**
 * x del centro de las palomitas de un juego de rótulos de piso: todas en una columna,
 * ASCENSOR_CORTE.palomita_aire (28 px) después del rótulo más largo (cada una al final de su
 * palabra caía en otra x y no se leía como columna). La usa AscensorCorte; para tres RotuloPiso
 * sueltos, pasarla a cada uno como `xPalomita`.
 */
export function columnaPalomitas(textos: string[], x: number, tam = 72, icono = 56): number {
  const ancho = Math.max(...textos.map((t) => medirTexto(t, tam)));
  return x + icono + sepIcono(icono) + ancho + ASCENSOR_CORTE.palomita_aire + ASCENSOR_CORTE.palomita_px / 2;
}

/**
 * Rótulo de un piso: ícono de 56 px (user, shield-halved, hand) y el texto a 72 px. En
 * espera va en gris (con el número en ámbar si lo tiene: los números 1-2-3 en ámbar son los
 * pisos); en curso, en ámbar; hecho, en hueso con una palomita ámbar de 56 px que toma el grosor
 * del asta del rótulo. `xPalomita`: el centro de la palomita (columnaPalomitas); si no, va
 * 28 px después de su propio texto.
 */
export const RotuloPiso: React.FC<{ x: number; y: number; piso: number; rotulo: Rotulo; tam?: number; icono?: number; xPalomita?: number }> = ({
  x,
  y,
  piso,
  rotulo,
  tam = 72,
  icono = 56,
  xPalomita,
}) => {
  const e = rotulo.estado;
  const v = e.visible ?? 1;
  if (v <= 0) return null;
  const color = colorRotulo(e);
  const numero = /^(\d+)(\s*·\s*)(.*)$/.exec(rotulo.texto);
  const colorNumero = css(mezcla(rgb(COLOR.ambar), rgb(COLOR.hueso), e.hecho ?? 0));
  const sep = sepIcono(icono);
  const xTexto = x + icono + sep;
  const optica = TIPO.correccionOpticaEm * tam;
  const lh = Math.round(tam * 1.25);
  const hecho = e.hecho ?? 0;
  const pal = ASCENSOR_CORTE.palomita_px;
  const xPal = xPalomita ?? columnaPalomitas([rotulo.texto], x, tam, icono);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, 1.5 * v), transform: `translateX(${-(1 - v) * MOV.distancia.entrar_lateral}px)` }}>
      <Icono nombre={pisoIcono(piso - 1)} alto={icono} x={x} y={y} ancla="izq" color={css(color)} />
      <div
        style={{
          position: "absolute",
          left: xTexto,
          top: y - lh / 2 - optica,
          height: lh,
          lineHeight: `${lh}px`,
          fontFamily: TIPO.familia,
          fontWeight: TIPO.peso,
          fontSize: tam,
          whiteSpace: "pre",
          color: css(color),
        }}
      >
        {numero ? (
          <>
            <span style={{ color: colorNumero }}>{numero[1]}</span>
            {numero[2]}
            {numero[3]}
          </>
        ) : (
          rotulo.texto
        )}
      </div>
      {hecho > 0 && <Palomita x={xPal} y={y} tam={pal} grosor={grosorAsta(tam)} progreso={Math.min(1, hecho * 1.4)} />}
    </div>
  );
};

export type VisorCorte = { texto: string; anterior?: string; cambio?: number; triangulo?: Omit<PropsTriangulo, "tam"> };

export type PropsAscensorCorte = {
  preset?: PresetCorte;
  geo?: GeoCorte;
  /** 0 → 1: paredes y techo (Trazo). */
  estructura?: number;
  /** 0 → 1 cada una: las losas de abajo hacia arriba (Trazo, 0,15 s cada una en D08.1). */
  losas?: number[];
  /** 0 → 1: el relleno opaco de los tramos (pantalla, como los bloques de 10 s de D07). */
  relleno?: number;
  /**
   * Opacidad del hueco (paredes, techo, polea, losas y cable), aparte de la cabina, el visor y
   * los rótulos: para dejar solo la cabina con su globo (el ascensor chico de D14.2, D19.3 y D19.5).
   */
  opacidadHueco?: number;
  /**
   * Si el corte va dentro de una capa escalada (el ascensor chico: 0,6), esa escala: los grosores
   * se dividen por ella para que ninguna línea baje de su trazo (a 0,6, las losas quedaban en 3 px).
   */
  escalaTrazos?: number;
  /** 0 → 1: el cable baja desde la polea hasta la cabina. */
  cable?: number;
  /** 0 → 1: la cabina aparece (escala 0,9 → 1). */
  cabina?: number;
  /** Piso de la cabina, continuo: 0 = planta baja, 3 = arriba. */
  piso?: number;
  /** 0 = puertas de la cabina cerradas, 1 = abiertas. */
  puertas?: number;
  visor?: VisorCorte | null;
  /** Los tres rótulos (de abajo hacia arriba), o null. */
  rotulos?: Rotulo[] | null;
  /** El globo que sale de la cabina arriba: «?» o «Lo dijeron dos veces.» (estilo = useRebote). */
  globo?: { estilo: Estilo; texto?: string; renglones?: string[]; ancho?: number; alto?: number; tam?: number; lado?: "der" | "izq" } | null;
  opacidad?: number;
};

/** El ascensor en corte (ver arriba). Todo se dibuja en coordenadas del cuadro. */
export const AscensorCorte: React.FC<PropsAscensorCorte> = ({
  preset = "crono",
  geo: geoDada,
  estructura = 1,
  losas = [1, 1, 1],
  relleno = 0,
  opacidadHueco = 1,
  escalaTrazos = 1,
  cable = 1,
  cabina = 1,
  piso = 0,
  puertas = 0,
  visor = { texto: "Pb", triangulo: { encendido: 0 } },
  rotulos = null,
  globo = null,
  opacidad = 1,
}) => {
  const idBase = useIdSvg("ac");
  const g = geoDada ?? geometriaCorte(preset);
  const k = 1 / Math.max(0.1, escalaTrazos); // los grosores, compensados por la escala de la capa
  const linea = conAlfa(COLOR.hueso, OPACIDAD.losa);
  const pared = conAlfa(COLOR.hueso, OPACIDAD.pared);
  const vuelo = 36;
  const poleaY = g.yTecho + 20;
  const cabY = g.pisoY(piso) - g.cabinaH;
  const cabX = g.xc - g.cabinaW / 2;
  const cuelgaY = cabY - 10;
  const camEstructura = `M ${g.x0} ${g.ySuelo} L ${g.x0} ${g.yTecho} L ${g.x1} ${g.yTecho} L ${g.x1} ${g.ySuelo}`;
  const evE = evolvePath(estructura, camEstructura);
  const camCable = `M ${g.xc} ${poleaY} L ${g.xc} ${cuelgaY}`;
  const evC = evolvePath(cable, camCable);
  const margen = 12;
  const hx0 = cabX + margen;
  const hx1 = cabX + g.cabinaW - margen;
  const hy0 = cabY + margen + 8;
  const hy1 = cabY + g.cabinaH;
  const hoja = (hx1 - hx0) / 2;
  const a = Math.max(0, Math.min(1, puertas));
  const clip = `${idBase}-cab`;
  const niveles = [g.ySuelo, ...g.losas];
  const caja = VISOR.caja_corte;
  const luz = OPACIDAD.luz_cabina;
  const juntaCabina = 3 * k;
  const hueco = Math.max(0, Math.min(1, opacidadHueco));
  const xPalomita = rotulos ? columnaPalomitas(rotulos.map((r) => r.texto), g.rotulosX, g.rotuloPx, g.iconoPx) : 0;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: opacidad }}>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        <defs>
          <clipPath id={clip}>
            <rect x={hx0} y={hy0} width={hx1 - hx0} height={hy1 - hy0} />
          </clipPath>
        </defs>
        {hueco > 0 && (
          <g opacity={hueco}>
            {relleno > 0 &&
              [1, 2, 3].map((n) => (
                <rect key={n} x={g.x0} y={niveles[n]} width={g.x1 - g.x0} height={niveles[n - 1] - niveles[n]} fill={conAlfa(COLOR.pantalla, relleno)} />
              ))}
            {estructura > 0 && (
              <path d={camEstructura} fill="none" stroke={pared} strokeWidth={GROSOR.pared_hueco * k} strokeLinejoin="miter" strokeDasharray={evE.strokeDasharray} strokeDashoffset={evE.strokeDashoffset} />
            )}
            {estructura > 0 && <line x1={g.x0 - vuelo} x2={g.x0 - vuelo + (g.x1 - g.x0 + 2 * vuelo) * estructura} y1={g.ySuelo} y2={g.ySuelo} stroke={linea} strokeWidth={GROSOR.losa * k} />}
            {g.losas.map((y, i) => {
              const p = Math.max(0, Math.min(1, losas[i] ?? 1));
              return p > 0 ? <line key={i} x1={g.x0 - vuelo} x2={g.x0 - vuelo + (g.x1 - g.x0 + 2 * vuelo) * p} y1={y} y2={y} stroke={linea} strokeWidth={GROSOR.losa * k} /> : null;
            })}
            {estructura > 0 && (
              <g opacity={Math.min(1, estructura * 2)}>
                <circle cx={g.xc} cy={poleaY} r={15} fill="none" stroke={linea} strokeWidth={GROSOR.trazo_fino * k} />
                <circle cx={g.xc} cy={poleaY} r={4} fill={linea} />
              </g>
            )}
            {cable > 0 && <path d={camCable} stroke={COLOR.ambar} strokeWidth={GROSOR.cable_cabina * k} strokeDasharray={evC.strokeDasharray} strokeDashoffset={evC.strokeDashoffset} />}
          </g>
        )}
        {cabina > 0 && (
          <g opacity={Math.min(1, 1.5 * cabina)} transform={`translate(${g.xc} ${cabY + g.cabinaH / 2}) scale(${0.9 + 0.1 * Math.min(1, cabina)}) translate(${-g.xc} ${-(cabY + g.cabinaH / 2)})`}>
            <path d={`M ${g.xc - 22} ${cabY} L ${g.xc - 12} ${cuelgaY} L ${g.xc + 12} ${cuelgaY} L ${g.xc + 22} ${cabY} Z`} fill={linea} />
            <rect x={cabX} y={cabY} width={g.cabinaW} height={g.cabinaH} rx={10} fill={COLOR.acero} stroke={conAlfa(COLOR.hueso, OPACIDAD.borde_apoyo)} strokeWidth={GROSOR.trazo_fino * k} />
            {a > 0 && (
              <g opacity={a}>
                {/* La cabina iluminada: ámbar al 85 % arriba que cae hacia abajo, y la tira de luz en hueso. */}
                <defs>
                  <linearGradient id={`${idBase}-luz`} x1={0} x2={0} y1={0} y2={1}>
                    <stop offset="0" stopColor={COLOR.ambar} stopOpacity={luz.arriba} />
                    <stop offset={luz.medio_en} stopColor={COLOR.ambar} stopOpacity={luz.medio} />
                    <stop offset="1" stopColor={COLOR.ambar} stopOpacity={luz.abajo} />
                  </linearGradient>
                </defs>
                <rect x={hx0} y={hy0} width={hx1 - hx0} height={hy1 - hy0} fill={COLOR.vidrio} />
                <rect x={hx0} y={hy0} width={hx1 - hx0} height={hy1 - hy0} fill={`url(#${idBase}-luz)`} />
                <rect x={hx0 + 14} y={hy0 + 2} width={hx1 - hx0 - 28} height={4 * k} rx={2 * k} fill={COLOR.hueso} opacity={luz.tira} />
              </g>
            )}
            <g clipPath={`url(#${clip})`}>
              <PanelAcero x={hx0 - hoja * a} y={hy0} ancho={hoja} alto={hy1 - hy0} junta="der" idBase={`${idBase}c`} nucleo={juntaCabina} />
              <PanelAcero x={hx0 + hoja + hoja * a} y={hy0} ancho={hoja} alto={hy1 - hy0} junta="izq" idBase={`${idBase}c`} nucleo={juntaCabina} />
              <Junta x={g.xc} y0={hy0} y1={hy1} ancho={juntaCabina} opacidad={OPACIDAD.junta_reposo * Math.max(0, 1 - a * 6)} idBase={`${idBase}c`} brillo={false} />
            </g>
          </g>
        )}
      </svg>
      {visor && (
        <VisorCaja
          cx={g.xc}
          cy={g.visorY}
          ancho={caja.ancho}
          alto={caja.alto}
          digito={caja.digito}
          triangulo={{ tam: caja.triangulo, ...(visor.triangulo ?? { encendido: 0 }) }}
          texto={visor.texto}
          anterior={visor.anterior}
          cambio={visor.cambio}
          opacidad={Math.min(1, estructura * 2) * hueco}
        />
      )}
      {rotulos &&
        rotulos.map((r, i) => (
          <RotuloPiso key={i} x={g.rotulosX} y={g.centroTramo(i + 1)} piso={i + 1} rotulo={r} tam={g.rotuloPx} icono={g.iconoPx} xPalomita={xPalomita} />
        ))}
      {globo && <GloboCabina g={g} {...globo} />}
    </div>
  );
};

/**
 * El globo que sale de la cabina en el piso 3: a la izquierda del hueco (el mapa de D08) o a la
 * derecha (el cronómetro: el lado izquierdo es angosto). Pegado a la cabina: ASCENSOR_CORTE.globo
 * .aire (30 px) entre los dos, dibujado ENCIMA de la pared del hueco (su relleno tinta la tapa) y
 * con la cola corta (≤ cola_max, 50 px), así la pregunta sale de la cabina y no es un puntero que
 * cruza la pared. En el cronómetro sube 16 + sube_crono px para dejar aire sobre «Pedido». Crece
 * desde la punta de la cola (useRebote: 0,4 → 1).
 */
const GloboCabina: React.FC<{ g: GeoCorte; estilo: Estilo; texto?: string; renglones?: string[]; ancho?: number; alto?: number; tam?: number; lado?: "der" | "izq" }> = ({
  g,
  estilo,
  texto = "?",
  renglones,
  ancho,
  alto,
  tam,
  lado,
}) => {
  const GC = ASCENSOR_CORTE.globo;
  const izq = ladoGlobo(g, lado) === "izq";
  const lineas = renglones ?? [texto];
  const corto = lineas.length === 1 && texto.length <= 2;
  const t = tam ?? (corto ? TIPO.escala.grande : TIPO.escala.lectura);
  const w = ancho ?? (corto ? (izq ? 260 : 220) : Math.max(...lineas.map((l) => medirTexto(l, t))) + 80);
  const h = alto ?? (lineas.length === 1 ? (izq ? 130 : 120) : Math.round(lineas.length * t * 1.25 + 56));
  const cabY = g.pisoY(3) - g.cabinaH;
  const { cx, cy } = cajaGloboCabina(g, { lado: izq ? "izq" : "der", ancho: w, alto: h });
  const bordeCabina = izq ? g.xc - g.cabinaW / 2 : g.xc + g.cabinaW / 2;
  const nace = izq ? cx + w / 2 : cx - w / 2;
  const enY = 0.66;
  const yNace = cy - h / 2 + enY * h;
  // La punta: a 6 px de la cabina, un poco más abajo que donde nace y dentro de la puerta abierta.
  const dx = bordeCabina - nace + (izq ? -6 : 6);
  const caida = Math.min(12, Math.sqrt(Math.max(0, GC.cola_max ** 2 - dx ** 2)));
  const yPunta = Math.max(cabY + 24, Math.min(cabY + g.cabinaH - 24, yNace + caida));
  const lh = Math.round(t * 1.25);
  const optica = TIPO.correccionOpticaEm * t;
  return (
    <Globo x={cx} y={cy} ancho={w} alto={h} color={COLOR.ambar} cola={{ lado: izq ? "der" : "izq", en: enY, punta: [dx, yPunta - yNace], base: 46 }} estilo={estilo}>
      {lineas.map((l, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: cx - w / 2,
            width: w,
            top: cy - (lineas.length * lh) / 2 + i * lh - optica,
            height: lh,
            lineHeight: `${lh}px`,
            textAlign: "center",
            fontFamily: TIPO.familia,
            fontWeight: TIPO.peso,
            fontSize: t,
            color: COLOR.ambar,
            whiteSpace: "pre",
          }}
        >
          {l}
        </div>
      ))}
    </Globo>
  );
};

/** De qué lado del hueco sale el globo: a la izquierda en el mapa (D08), a la derecha en el cronómetro. */
const ladoGlobo = (g: GeoCorte, lado?: "der" | "izq") => lado ?? (g.x0 > 400 ? "izq" : "der");

/**
 * La caja que ocupa el globo de la cabina (el «?» de 260×130 en el mapa y 220×120 en el
 * cronómetro, o el tamaño dado): para ubicar algo debajo, como «ganas de preguntar» en D08.2.
 */
export function cajaGloboCabina(g: GeoCorte, op: { lado?: "der" | "izq"; ancho?: number; alto?: number } = {}): { x0: number; y0: number; x1: number; y1: number; cx: number; cy: number } {
  const GC = ASCENSOR_CORTE.globo;
  const izq = ladoGlobo(g, op.lado) === "izq";
  const w = op.ancho ?? (izq ? 260 : 220);
  const h = op.alto ?? (izq ? 130 : 120);
  const cy = g.centroCabina(3) - (izq ? 0 : 16 + GC.sube_crono);
  const bordeCabina = izq ? g.xc - g.cabinaW / 2 : g.xc + g.cabinaW / 2;
  const cx = izq ? bordeCabina - GC.aire - w / 2 : bordeCabina + GC.aire + w / 2;
  return { x0: cx - w / 2, y0: cy - h / 2, x1: cx + w / 2, y1: cy + h / 2, cx, cy };
}

// ---------- El viaje de 30 s ----------

export type EstadoViaje = {
  luces: number[];
  puertas: number;
  piso: number;
  visor: VisorCorte;
  estados: EstadoRotulo[];
  cuenta: { texto: string; latido: number };
  /** Segundo del paso en que empieza a salir el globo: useRebote(paso, viaje.globoS). */
  globoS: number;
  /** Segundo del paso en que llega la cabina y suena el ding (el campo audio del deck). */
  dingS: number;
  /** Segundo en que la cabina empieza a subir (se cierran las puertas 0,5 s antes). */
  subeS: number;
};

/**
 * El cronómetro de 30 s del ascensor, como función del tiempo del paso. `luz1` = segundo
 * del paso en que se enciende la primera luz (las otras, 1 s después cada una); 0,5 s
 * después de la tercera se cierran las puertas de la cabina (0,5 s) y desde ahí sube 30 s
 * lineales: el visor y el rótulo cambian al EMPEZAR cada tramo; el tramo hecho pasa a
 * hueso con palomita; la cuenta baja de 30 a 0 y late los últimos 5 s. Al llegar: ding,
 * las puertas se abren (0,6 s) y sale el globo. D19.2: luz1 = 0,6. D14.1: 1,3 − 1,05 (la
 * transición de puertas es otro video). Falla si no termina antes del respiro.
 */
export function useViajeCrono(paso: number, luz1: number): EstadoViaje {
  const info = usePasos();
  const frame = useCurrentFrame();
  const v = MOV.viaje;
  const cp = MOV.cuentaPrevia;
  const cierre = luz1 + (cp.luces - 1) * cp.entre_luces_s + cp.cierre_tras_luz_s;
  const sube = cierre + cp.cierre_s;
  const llega = sube + v.segundos;
  const globo = llega + v.globo_tras_s;
  tramoDe(info, paso, luz1, globo + MOV.dura.rebote - luz1, "el viaje de 30 s", true);
  const t0 = info.cortes[paso - 1];
  const t = (frame - t0) / FPS;
  const f = (seg: number) => t0 + s(seg);
  const entre = (a: number, b: number, curva = CURVA.suave) => interpolate(frame, [f(a), Math.max(f(a) + 1, f(b))], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curva });
  const luces = [0, 1, 2].map((i) => entre(luz1 + i * cp.entre_luces_s, luz1 + i * cp.entre_luces_s + 0.12, CURVA.lineal));
  const puertas = 1 - entre(cierre, sube) + entre(llega, llega + v.abre_s, CURVA.sale);
  const piso = interpolate(frame, [f(sube), f(llega)], [0, v.pisos], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Visor: va al piso siguiente al EMPEZAR cada tramo.
  const tramo = t < sube ? 0 : Math.min(v.pisos, Math.floor((t - sube) / (v.segundos / v.pisos)) + 1);
  const inicioTramo = sube + (Math.max(1, tramo) - 1) * (v.segundos / v.pisos);
  const cambio = tramo === 0 ? 1 : entre(inicioTramo, inicioTramo + MOV.dura.visor_cambio);
  const visor: VisorCorte = {
    texto: tramo === 0 ? "Pb" : String(tramo),
    anterior: tramo <= 1 ? "Pb" : String(tramo - 1),
    cambio,
    triangulo: { encendido: entre(sube, sube + 0.2), brillo: tramo >= 1 ? Math.sin(Math.PI * Math.min(1, Math.max(0, (t - inicioTramo) / 0.5))) : 0 },
  };
  if (tramo === 1 && t - sube < 0.001) visor.anterior = "Pb";
  const estados = [1, 2, 3].map((k) => {
    const empieza = sube + (k - 1) * (v.segundos / v.pisos);
    const termina = empieza + v.segundos / v.pisos;
    return { visible: 1, encendido: entre(empieza, empieza + 0.2), hecho: entre(termina, termina + 0.3) };
  });
  const falta = Math.max(0, Math.min(v.segundos, v.segundos - (t - sube)));
  const mostrado = t <= sube ? v.segundos : Math.ceil(falta - 1e-9);
  const pulso = falta > 0 && falta <= MOV.latidoUltimos.cuenta_30 ? 0.5 - 0.5 * Math.cos(2 * Math.PI * (falta % 1)) : 0;
  return {
    luces,
    puertas: Math.max(0, Math.min(1, puertas)),
    piso,
    visor,
    estados,
    cuenta: { texto: String(mostrado), latido: 1 + (MOV.escala.latido - 1) * pulso },
    globoS: globo,
    dingS: llega,
    subeS: sube,
  };
}

/**
 * El ascensor de 30 s completo, como en D14.1 y D19.2: el corte a la izquierda (preset
 * «crono») con sus rótulos, la cuenta en el lugar fijo del reloj grande con las tres
 * luces debajo, el ding (en el audio del deck) y el globo. `rotulos`: los tres textos de
 * deck.json («Frase XYZ», «Prueba», «Pedido»).
 */
export const AscensorCrono: React.FC<{
  paso: number;
  luz1: number;
  rotulos: string[];
  /** Lo que dice el globo al llegar (por defecto «?»); renglones para dos líneas (A8.3). */
  globo?: { texto?: string; renglones?: string[] };
  opacidad?: number;
}> = ({ paso, luz1, rotulos, globo, opacidad = 1 }) => {
  const viaje = useViajeCrono(paso, luz1);
  const rebote = useReboteGlobo(paso, viaje.globoS);
  return (
    <>
      <AscensorCorte
        preset="crono"
        piso={viaje.piso}
        puertas={viaje.puertas}
        visor={viaje.visor}
        rotulos={rotulos.map((texto, i) => ({ texto, estado: viaje.estados[i] }))}
        globo={{ estilo: rebote, ...globo }}
        opacidad={opacidad}
      />
      <Visor7 texto={viaje.cuenta.texto} alto={RELOJ.alto} x={RELOJ.cx} y={RELOJ.cy} latido={viaje.cuenta.latido} opacidad={opacidad} />
      <CuentaPrevia luces={viaje.luces} opacidad={opacidad} />
    </>
  );
};

function useReboteGlobo(paso: number, desde: number): Estilo {
  return useRebote(paso, desde);
}
