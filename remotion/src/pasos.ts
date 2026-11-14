// El sistema de pasos. Una diapositiva es una composición; sus pasos son tramos de
// la misma línea de tiempo. Con cortes c[0] = 0 < c[1] < … < c[n] (en cuadros), el
// paso k (1, 2…, como en el guion) va del cuadro c[k-1] al c[k], los dos incluidos:
// el último cuadro de un paso ES el primero del siguiente (mismo número de cuadro,
// mismos píxeles). Cada paso dura lo que dice deck.json (respiro incluido): toda
// animación del paso k empieza y termina dentro de su tramo y deja quietos los
// últimos 0,3 s. Si no, el render falla y dice qué animación pisó el respiro.
import { createContext, useContext } from "react";
import { interpolate, spring, useCurrentFrame, type SpringConfig } from "remotion";
import { duracionesPropias, entradaDe, type Entrada } from "./deck";
import { ANIMACION_MAX_S, CURVA, FPS, MOV, RESORTE, RESPIRO_S } from "./tokens";

/** Segundos a cuadros. */
export const s = (seg: number): number => Math.round(seg * FPS);
/** Cuadros quietos al final de cada paso. */
export const RESPIRO = s(RESPIRO_S);

/** Cortes (en cuadros) a partir de la duración en segundos de cada paso. */
export function cortesDe(duraciones: number[]): number[] {
  return duraciones.reduce((c, d) => [...c, c[c.length - 1] + s(d)], [0]);
}

/**
 * Duraciones (s) de los pasos de una diapositiva: las de deck.json (en el paso 1, sin
 * la transición de entrada). Se pueden ajustar paso por paso: pasosDe("D06", { 2: 3.0 }).
 * Un ajuste se reporta: render.mjs avisa cuando no coincide con deck.json.
 */
export function pasosDe(id: string, ajustes: Record<number, number> = {}): number[] {
  const base = duracionesPropias(id);
  for (const k of Object.keys(ajustes)) {
    const i = Number(k);
    if (!(i >= 1 && i <= base.length)) throw new Error(`pasosDe(${id}): no hay paso ${k}`);
  }
  return base.map((d, i) => ajustes[i + 1] ?? d);
}

export type Rect = { x: number; y: number; ancho: number; alto: number };

export type InfoPasos = {
  id: string;
  /** cortes en cuadros: c[0] = 0, c[n] = último cuadro */
  cortes: number[];
  /** cantidad de pasos */
  n: number;
  entrada: Entrada;
  /** archivo (en public del bundle) con el último cuadro de la diapositiva anterior */
  anterior: string | null;
  /** zonas que el cuadro anterior no muestra: ahí dibujan los elementos fijos */
  huecosAnterior: Rect[];
};

export const PasosContext = createContext<InfoPasos | null>(null);

/** Datos de los pasos de la diapositiva en curso (los pone <Diapositiva>). */
export function usePasos(): InfoPasos {
  const info = useContext(PasosContext);
  if (!info) throw new Error("usePasos(): el componente tiene que estar dentro de una diapositiva registrada (sistema/registrar).");
  return info;
}

function nombreDe(info: InfoPasos, paso: number) {
  return `${info.id}.${paso}`;
}

/** [desde, hasta] en cuadros de una animación del paso, validada contra el respiro. */
export function tramoDe(info: InfoPasos, paso: number, retraso: number, dura: number, quien = "animación", largo = false): [number, number] {
  const { cortes: c, n } = info;
  if (!Number.isInteger(paso) || paso < 1 || paso > n) {
    throw new Error(`${info.id}: ${quien} pide el paso ${paso}, y la diapositiva tiene ${n} (se cuentan desde 1, como en el guion).`);
  }
  if (retraso < 0) throw new Error(`${nombreDe(info, paso)}: ${quien} con retraso negativo (${retraso} s).`);
  if (!(dura > 0)) throw new Error(`${nombreDe(info, paso)}: ${quien} con duración ${dura} s.`);
  if (!largo && dura > ANIMACION_MAX_S + 1e-9) {
    throw new Error(`${nombreDe(info, paso)}: ${quien} dura ${dura} s; el máximo es ${ANIMACION_MAX_S} s (salvo cronómetros: usar useLineal).`);
  }
  const desde = c[paso - 1] + s(retraso);
  const hasta = desde + Math.max(1, s(dura));
  const limite = c[paso] - RESPIRO;
  if (hasta > limite) {
    const fin = (hasta - c[paso - 1]) / FPS;
    const durPaso = (c[paso] - c[paso - 1]) / FPS;
    const n = (v: number) => v.toFixed(2).replace(".", ",");
    throw new Error(
      `${nombreDe(info, paso)}: ${quien} termina a los ${n(fin)} s y el paso dura ${n(durPaso)} s: ` +
        `tiene que terminar antes de los ${n(durPaso - RESPIRO_S)} s (los últimos ${String(RESPIRO_S).replace(".", ",")} s van quietos: el respiro). ` +
        `Acortar la animación o ajustar la duración con pasosDe("${info.id}", { ${paso}: … }).`,
    );
  }
  return [desde, hasta];
}

/**
 * 0 → 1 con resorte: algo que entra en el paso. Antes del tramo vale 0; después,
 * exactamente 1 (aunque el resorte tenga rebote, al final queda quieto en 1).
 */
export function useEntra(paso: number, retraso = 0, dura: number = MOV.dura.entrar, resorte: Partial<SpringConfig> = RESORTE.entrar): number {
  const info = usePasos();
  const frame = useCurrentFrame();
  const [desde, hasta] = tramoDe(info, paso, retraso, dura, "useEntra");
  if (frame <= desde) return 0;
  if (frame >= hasta) return 1;
  return spring({ frame: frame - desde, fps: FPS, config: resorte, durationInFrames: hasta - desde });
}

/** 0 → 1 con curva (sin rebote): trazos, desplazamientos, fundidos. */
export function useTramo(paso: number, retraso = 0, dura = 0.5, curva: (x: number) => number = CURVA.suave): number {
  const info = usePasos();
  const frame = useCurrentFrame();
  const [desde, hasta] = tramoDe(info, paso, retraso, dura, "useTramo");
  return interpolate(frame, [desde, hasta], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curva });
}

/** 1 → 0: algo que se va en el paso (por defecto, un fundido de 0,3 s). */
export function useSale(paso: number, retraso = 0, dura: number = MOV.dura.desvanecer, curva: (x: number) => number = CURVA.suave): number {
  return 1 - useTramo(paso, retraso, dura, curva);
}

/** 0 → 1 lineal y sin tope de duración: el tiempo de los cronómetros (no se maquilla). */
export function useLineal(paso: number, retraso: number, dura: number): number {
  const info = usePasos();
  const frame = useCurrentFrame();
  const [desde, hasta] = tramoDe(info, paso, retraso, dura, "useLineal", true);
  return interpolate(frame, [desde, hasta], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
}

/** Segundos desde que empezó el paso (negativo antes; sigue contando después). */
export function useSegundos(paso: number): number {
  const info = usePasos();
  const frame = useCurrentFrame();
  if (paso < 1 || paso > info.n) throw new Error(`${info.id}: no hay paso ${paso}`);
  return (frame - info.cortes[paso - 1]) / FPS;
}

/**
 * El paso en curso (1…n) y los segundos desde su comienzo. El cuadro de corte c[k]
 * cuenta como el último del paso k (es el mismo cuadro que el primero del k+1).
 */
export function usePasoActual(): { paso: number; t: number } {
  const info = usePasos();
  const frame = useCurrentFrame();
  let k = 1;
  while (k < info.n && frame > info.cortes[k]) k++;
  return { paso: k, t: (frame - info.cortes[k - 1]) / FPS };
}

/** Duración (s) del paso. */
export function useDuracionPaso(paso: number): number {
  const info = usePasos();
  return (info.cortes[paso] - info.cortes[paso - 1]) / FPS;
}

/**
 * Cuánto hay que restar a un tiempo del guion en el paso 1 cuando la entrada es un
 * video aparte (fundido o puertas): el video propio empieza cuando la transición
 * termina. Ej.: D14.1 dice «las luces a los 1,3 s» → retraso 1,3 − desfase.
 */
export function useDesfaseEntrada(): number {
  const { entrada } = usePasos();
  return entrada.tipo === "fundido" || entrada.tipo === "puertas" ? entrada.duracion_s : 0;
}

/** Para leer la entrada de una diapositiva fuera de un componente. */
export { entradaDe };
