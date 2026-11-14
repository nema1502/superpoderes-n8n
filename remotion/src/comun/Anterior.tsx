// El último cuadro de la diapositiva anterior, para las entradas «continuo»: la
// diapositiva arranca mostrándolo tal cual (su cuadro 0 es idéntico al último de la
// anterior) y lo transforma ella misma (lo desvanece, lo corre, lo tapa).
//
// Cómo llega: render.mjs copia render/cuadros/<anterior>_<n>.png al bundle de esta
// diapositiva como «anterior.png» (si falta y la anterior es de Remotion, lo renderiza
// antes). En el Studio no hay archivo: se ve un esquema gris.
//
// Los elementos fijos que siguen en esta diapositiva (marca de agua, chip) NO salen del
// PNG: el PNG lleva un hueco ahí y el sistema los dibuja encima, siempre en el mismo píxel.
import React from "react";
import { Img, staticFile, useCurrentFrame } from "remotion";
import { RESPIRO, useTramo, usePasos } from "../pasos";
import { COLOR, conAlfa, CURVA, MOV, TIPO } from "../tokens";
import type { Estilo } from "./movimiento";

export type PropsAnterior = {
  /** Fundido de salida dentro del paso 1 (retraso y duración en s). */
  sale?: { retraso?: number; dura?: number };
  /** O la opacidad a mano (si se anima de otra forma). */
  opacidad?: number;
  /** Transform del cuadro (correrlo, escalarlo…). */
  estilo?: Estilo;
  /** Huecos extra (además de los de la marca y el chip), en px del cuadro. */
  huecos?: { x: number; y: number; ancho: number; alto: number }[];
};

export const Anterior: React.FC<PropsAnterior> = ({ sale, opacidad, estilo, huecos = [] }) => {
  const info = usePasos();
  const frame = useCurrentFrame();
  if (info.entrada.tipo !== "continuo") {
    throw new Error(`${info.id}: <Anterior> es solo para entradas «continuo» (esta entra con «${info.entrada.tipo}»: la transición es otro video).`);
  }
  const fundido = useTramo(1, sale?.retraso ?? 0, sale?.dura ?? MOV.dura.fundido, CURVA.fundido);
  const op = (opacidad ?? (sale ? 1 - fundido : 1)) * (estilo?.opacity !== undefined ? Number(estilo.opacity) : 1);
  const finPaso1 = info.cortes[1];
  if (frame >= finPaso1 - RESPIRO && op > 0.001) {
    throw new Error(`${info.id}.1: el cuadro anterior sigue visible al final del paso 1 (opacidad ${op.toFixed(2)}): tiene que irse antes del respiro.`);
  }
  if (frame > finPaso1 || op <= 0) return null;
  const todos = [...info.huecosAnterior, ...huecos];
  const recorte = todos.length
    ? `path(evenodd, "M0 0 H1920 V1080 H0 Z ${todos.map((h) => `M${h.x} ${h.y} h${h.ancho} v${h.alto} h${-h.ancho} Z`).join(" ")}")`
    : undefined;
  const estiloFinal: React.CSSProperties = { position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "50% 50%", ...estilo, opacity: op };
  if (!info.anterior) {
    return (
      <div style={estiloFinal}>
        <div style={{ position: "absolute", inset: 0, clipPath: recorte, background: `repeating-linear-gradient(135deg, ${conAlfa(COLOR.gris, 0.06)} 0 2px, transparent 2px 28px)` }} />
        <div style={{ position: "absolute", left: 0, right: 0, top: 500, textAlign: "center", fontFamily: TIPO.familia, fontWeight: TIPO.peso, fontSize: 52, color: conAlfa(COLOR.gris, 0.7) }}>
          {`cuadro anterior (${info.entrada.desde ?? "—"}): se agrega al renderizar`}
        </div>
      </div>
    );
  }
  return (
    <div style={estiloFinal}>
      <Img src={staticFile(info.anterior)} style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: recorte }} />
    </div>
  );
};
