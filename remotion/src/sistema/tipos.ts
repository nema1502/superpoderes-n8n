import type React from "react";

/** Ajustes de los elementos fijos que pone el sistema (marca de agua y chip de piso). */
export type AjustePersistente = false | { retraso?: number; dura?: number };

export type OpcionesDiapo = {
  /**
   * El sistema dibuja la marca de agua y el chip de piso según tokens.json y deck.json,
   * y anima sus cambios al empezar cada paso (0,3 s). Con false, los dibuja la diapositiva.
   */
  persistentes?: false | { marca?: AjustePersistente; chip?: AjustePersistente };
};

/** Lo que exporta cada archivo de remotion/src/diapos/<ID><Nombre>.tsx. */
export type ModuloDiapo = {
  componente: React.FC;
  /** Duración en s del video propio de cada paso (pasosDe(id) = la de deck.json). */
  pasos: number[];
  opciones?: OpcionesDiapo;
};

/** Una entrada del registro: modulo = null es una provisional. */
export type DefDiapo = { id: string; modulo: ModuloDiapo | null };

/** Props de la composición de una diapositiva (las lee render.mjs). */
export type PropsComposicion = {
  cortes: number[];
  pasos: number[];
  /** Archivo en public del bundle con el último cuadro de la diapositiva anterior. */
  anterior: string | null;
};
