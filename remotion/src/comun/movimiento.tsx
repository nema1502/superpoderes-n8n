// El vocabulario de movimiento (guion: «Vocabulario de movimiento»), uno solo para
// toda la charla. Cada pieza es un hook que devuelve un estilo CSS (opacidad y
// transform) para aplicar a un <Texto estilo={…}> o a una <Capa>, y un componente
// del mismo nombre que envuelve a sus hijos en una capa a pantalla completa.
// Los hijos se posicionan en coordenadas del cuadro (1920×1080), como siempre.
import React, { createContext, useContext } from "react";
import { AbsoluteFill } from "remotion";
import { useEntra, useTramo } from "../pasos";
import { CURVA, MOV, OPACIDAD, RESORTE } from "../tokens";

export type Estilo = React.CSSProperties;
export type Origen = [number, number];

/** Une estilos: multiplica las opacidades y encadena los transform (en orden). */
export function unir(...estilos: (Estilo | undefined | null | false)[]): Estilo {
  let opacidad = 1;
  const transformes: string[] = [];
  const resto: Estilo = {};
  for (const e of estilos) {
    if (!e) continue;
    const { opacity, transform, ...otros } = e;
    if (opacity !== undefined) opacidad *= Number(opacity);
    if (transform) transformes.push(String(transform));
    Object.assign(resto, otros);
  }
  return { ...resto, opacity: opacidad, transform: transformes.length ? transformes.join(" ") : undefined };
}

export type Direccion = "abajo" | "arriba" | "izq" | "der";

/**
 * Entrar: resorte damping 15 / mass 0,7; opacidad min(1, 1,5·p); sube (1−p)·60 px.
 * `desde`: de dónde viene ("abajo" sube, "izq" entra 40 px desde la izquierda…).
 * Desfase entre hermanos: 0,12-0,2 s (MOV.desfase.renglones = 0,15).
 */
export function useEntrar(paso: number, retraso = 0, op: { dura?: number; desde?: Direccion; distancia?: number } = {}): Estilo {
  const p = useEntra(paso, retraso, op.dura ?? MOV.dura.entrar, RESORTE.entrar);
  const desde = op.desde ?? "abajo";
  const lateral = desde === "izq" || desde === "der";
  const d = (1 - p) * (op.distancia ?? (lateral ? MOV.distancia.entrar_lateral : MOV.distancia.entrar));
  const dx = desde === "izq" ? -d : desde === "der" ? d : 0;
  const dy = desde === "abajo" ? d : desde === "arriba" ? -d : 0;
  return { opacity: Math.min(1, 1.5 * p), transform: `translate(${dx}px, ${dy}px)` };
}

/**
 * Entrar palabra por palabra (el título de la portada): un estilo por palabra de
 * `texto`, para <Texto estiloPalabras={…}>. Desfase 0,12 s entre palabras.
 */
export function useEntrarPalabras(
  texto: string,
  paso: number,
  retraso = 0,
  op: { desfase?: number; dura?: number; desde?: Direccion; distancia?: number } = {},
): Estilo[] {
  const n = (texto.match(/\S+/g) ?? []).length;
  const estilos: Estilo[] = [];
  for (let i = 0; i < n; i++) {
    // n es fijo para un mismo texto: el orden de los hooks no cambia entre cuadros.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    estilos.push(useEntrar(paso, retraso + i * (op.desfase ?? MOV.desfase.palabras), op));
  }
  return estilos;
}

/**
 * Golpe: escala 1,25 → 1 (chico: 1,1 → 1), sin giro y SIN rebote: resorte damping 14 /
 * mass 0,8, recortado en 1. Para «Su turno:», «Evalúenme:», la fila correcta de un par.
 */
export function useGolpe(paso: number, retraso = 0, op: { chico?: boolean; dura?: number } = {}): Estilo {
  const p = Math.min(1, useEntra(paso, retraso, op.dura ?? MOV.dura.golpe, RESORTE.golpe));
  const desde = op.chico ? MOV.escala.golpe_chico : MOV.escala.golpe;
  return { opacity: Math.min(1, 2.5 * p), transform: `scale(${desde - (desde - 1) * p})` };
}

/**
 * Rebote: escala 0,4 → 1 con resorte damping 9 / mass 0,9 / stiffness 120: se pasa a 1,13 y
 * vuelve; opacidad min(1, 4·p). SOLO para el globo «?» que sale de la cabina, con el origen en la
 * punta de su cola (Globo lo pone ahí): la pregunta SALE de la cabina. (De 2 → 1, el primer cuadro
 * visible ya estaba casi opaco a 1,75 veces su tamaño y se salía del margen: un golpe de
 * historieta que caía sobre la sala.)
 */
export function useRebote(paso: number, retraso = 0, dura: number = MOV.dura.rebote): Estilo {
  const p = useEntra(paso, retraso, dura, RESORTE.rebote);
  const desde = MOV.escala.rebote;
  return { opacity: Math.min(1, 4 * p), transform: `scale(${desde + (1 - desde) * p})` };
}

/** Voltear: rotateY de 90° a 0° con perspectiva de 1200 px, resorte sin rebote. Tarjetas e íconos. */
export function useVoltear(paso: number, retraso = 0, dura: number = MOV.dura.voltear): Estilo {
  const p = useEntra(paso, retraso, dura, RESORTE.suave);
  return { opacity: p > 0.02 ? 1 : 0, transform: `perspective(${MOV.perspectiva}px) rotateY(${(1 - p) * 90}deg)` };
}

/** Escalar desde `desde` (0,9) hasta 1, con fundido: la cabina, el avatar, un globo. */
export function useEscalar(paso: number, retraso = 0, op: { desde?: number; dura?: number; resorte?: keyof typeof RESORTE } = {}): Estilo {
  const p = useEntra(paso, retraso, op.dura ?? MOV.dura.entrar, RESORTE[op.resorte ?? "entrar"]);
  const desde = op.desde ?? MOV.escala.tarjeta_entra;
  return { opacity: Math.min(1, 1.5 * p), transform: `scale(${desde + (1 - desde) * p})` };
}

/** Aparece con un fundido (sin moverse). */
export function useAparecer(paso: number, retraso = 0, dura: number = MOV.dura.desvanecer): Estilo {
  return { opacity: useTramo(paso, retraso, dura, CURVA.fundido) };
}

/** Se va con un fundido (0,3 s por defecto). */
export function useDesvanecer(paso: number, retraso = 0, dura: number = MOV.dura.desvanecer): Estilo {
  return { opacity: 1 - useTramo(paso, retraso, dura, CURVA.fundido) };
}

// ---------- Capas ----------

/** Capa a pantalla completa con un estilo; `origen` es el punto fijo de escalas y giros. */
export const Capa: React.FC<{ estilo?: Estilo; origen?: Origen; children: React.ReactNode }> = ({ estilo, origen, children }) => (
  <AbsoluteFill style={{ ...estilo, transformOrigin: origen ? `${origen[0]}px ${origen[1]}px` : estilo?.transformOrigin }}>{children}</AbsoluteFill>
);

type PropsPieza = { paso: number; retraso?: number; children: React.ReactNode };

/** <Entrar paso={1} retraso={0.2}>…</Entrar>: sus hijos entran juntos (ver useEntrar). */
export const Entrar: React.FC<PropsPieza & { dura?: number; desde?: Direccion; distancia?: number }> = ({ paso, retraso = 0, dura, desde, distancia, children }) => (
  <Capa estilo={useEntrar(paso, retraso, { dura, desde, distancia })}>{children}</Capa>
);

/** <Golpe paso={1} origen={[x, y]}>…</Golpe>: escala 1,25 → 1 alrededor de `origen`. */
export const Golpe: React.FC<PropsPieza & { origen: Origen; chico?: boolean }> = ({ paso, retraso = 0, origen, chico, children }) => (
  <Capa estilo={useGolpe(paso, retraso, { chico })} origen={origen}>
    {children}
  </Capa>
);

/** <Rebote paso={2} origen={[x, y]}>: solo el globo «?»; `origen` = la punta de su cola (puntaGlobo). */
export const Rebote: React.FC<PropsPieza & { origen: Origen }> = ({ paso, retraso = 0, origen, children }) => (
  <Capa estilo={useRebote(paso, retraso)} origen={origen}>
    {children}
  </Capa>
);

/** <Voltear paso={1} origen={[x, y]}>: tarjetas que se dan vuelta. */
export const Voltear: React.FC<PropsPieza & { origen: Origen }> = ({ paso, retraso = 0, origen, children }) => (
  <Capa estilo={useVoltear(paso, retraso)} origen={origen}>
    {children}
  </Capa>
);

/** <Aparecer> / <Desvanecer>: fundidos. */
export const Aparecer: React.FC<PropsPieza & { dura?: number }> = ({ paso, retraso = 0, dura, children }) => (
  <Capa estilo={useAparecer(paso, retraso, dura)}>{children}</Capa>
);
export const Desvanecer: React.FC<PropsPieza & { dura?: number }> = ({ paso, retraso = 0, dura, children }) => (
  <Capa estilo={useDesvanecer(paso, retraso, dura)}>{children}</Capa>
);

// ---------- Foco ----------

const FocoContext = createContext(0);

/**
 * Foco: al entrar lo nuevo, lo ya explicado baja en 0,3 s a hueso al 60 % y su ámbar a
 * ámbar al 60 % (OPACIDAD.foco_hueso y foco_ambar: más abajo, desde el fondo de una sala
 * con luz quedaba ilegible). Se envuelve lo viejo: <Foco paso={3}>…lo de antes…</Foco>.
 * La idea clave, el chip y la marca de agua nunca van adentro.
 */
export const Foco: React.FC<PropsPieza & { dura?: number }> = ({ paso, retraso = 0, dura = MOV.dura.foco, children }) => {
  const f = useTramo(paso, retraso, dura, CURVA.suave);
  const exterior = useContext(FocoContext);
  const total = Math.max(f, exterior);
  return (
    <FocoContext.Provider value={total}>
      <AbsoluteFill style={{ opacity: 1 - f * (1 - OPACIDAD.foco_hueso) }}>{children}</AbsoluteFill>
    </FocoContext.Provider>
  );
};

/** Factor extra para lo ámbar dentro de un Foco (para que quede en foco_ambar y no en foco_hueso; hoy los dos son 0,6). */
export function useAtenuarAmbar(): number {
  const f = useContext(FocoContext);
  return 1 - f * (1 - OPACIDAD.foco_ambar / OPACIDAD.foco_hueso);
}

/** ¿Hay un Foco activo arriba? (0 = no, 1 = atenuado del todo). */
export function useFocoActual(): number {
  return useContext(FocoContext);
}
