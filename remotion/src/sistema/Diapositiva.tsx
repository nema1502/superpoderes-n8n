// El envoltorio de toda diapositiva (lo pone el registro, no se usa a mano): el Lienzo,
// los datos de los pasos para los hooks (usePasos, useEntra…) y los elementos fijos que
// dibuja el sistema por encima de todo, siempre en el mismo píxel:
//   - la marca de agua, en los pasos que la llevan (tokens.json → persistentes);
//   - el chip de piso, en las diapositivas con piso (deck.json → piso).
// Cuando cambian entre un paso y el siguiente (o desde la diapositiva anterior, si la
// entrada es continua), el cambio se anima al empezar el paso: fundido de 0,3 s; el chip
// aparece con escala 0,9 → 1 o rueda el dígito (0,35 s) con el ▲ que brilla una vez.
import React, { useMemo } from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { ChipPiso } from "../comun/ChipPiso";
import { Lienzo } from "../comun/Lienzo";
import { MarcaAgua } from "../comun/Marca";
import { chipEn, entradaDe, estadoPrevio, marcaEn } from "../deck";
import { cortesDe, PasosContext, s, tramoDe, usePasos, type InfoPasos, type Rect } from "../pasos";
import { CURVA, MOV, PERSISTENTES, RETICULA } from "../tokens";
import type { AjustePersistente, OpcionesDiapo } from "./tipos";

const zona = (z: { x: number; y: number; ancho: number; alto: number }): Rect => ({ x: z.x, y: z.y, ancho: z.ancho, alto: z.alto });

export const Diapositiva: React.FC<{ id: string; pasos: number[]; anterior: string | null; opciones?: OpcionesDiapo; children: React.ReactNode }> = ({
  id,
  pasos,
  anterior,
  opciones,
  children,
}) => {
  const info = useMemo<InfoPasos>(() => {
    const cortes = cortesDe(pasos);
    const entrada = entradaDe(id);
    const previo = estadoPrevio(id);
    const p = opciones?.persistentes;
    const conMarca = p !== false && p?.marca !== false;
    const conChip = p !== false && p?.chip !== false;
    // Hueco en el cuadro anterior donde la anterior trae un elemento fijo: desde el cuadro 0
    // lo dibuja el sistema en el mismo píxel (quieto, rodando o desvaneciéndose), así nunca
    // hay dos copias superpuestas.
    const huecos: Rect[] = [];
    if (entrada.tipo === "continuo") {
      if (conMarca && previo.marca) huecos.push(zona(RETICULA.marca_agua.zona));
      if (conChip && previo.chip !== null) huecos.push(zona(RETICULA.chip_piso.zona));
    }
    return { id, cortes, n: pasos.length, entrada, anterior, huecosAnterior: huecos };
  }, [id, pasos, anterior, opciones]);
  const p = opciones?.persistentes;
  return (
    <PasosContext.Provider value={info}>
      <Lienzo>
        {children}
        {p !== false && <Persistentes marca={p?.marca} chip={p?.chip} />}
      </Lienzo>
    </PasosContext.Provider>
  );
};

const Persistentes: React.FC<{ marca?: AjustePersistente; chip?: AjustePersistente }> = ({ marca, chip }) => {
  const info = usePasos();
  const frame = useCurrentFrame();
  const { id, cortes: c, n } = info;
  const previo = estadoPrevio(id);

  // ---- marca de agua ----
  let opMarca = 0;
  if (marca !== false) {
    const retraso = marca?.retraso ?? 0;
    let antes = previo.marca;
    opMarca = antes ? 1 : 0;
    for (let k = 1; k <= n; k++) {
      const ahora = marcaEn(id, k);
      if (frame >= c[k - 1]) {
        if (ahora !== antes) {
          const dura = marca?.dura ?? (ahora ? PERSISTENTES.entra_s : PERSISTENTES.sale_s);
          const [a, b] = tramoDe(info, k, retraso, dura, "la marca de agua");
          opMarca = interpolate(frame, [a, b], [antes ? 1 : 0, ahora ? 1 : 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.fundido });
        } else opMarca = ahora ? 1 : 0;
      }
      antes = ahora;
    }
  }

  // ---- chip de piso (el piso es de toda la diapositiva: solo cambia en el paso 1) ----
  let chip_: React.ReactNode = null;
  if (chip !== false) {
    const v = chipEn(id);
    const v0 = previo.chip;
    const retraso = chip?.retraso ?? 0;
    if (v !== null || v0 !== null) {
      if (v === v0) chip_ = <ChipPiso piso={v!} />;
      else if (v0 === null) {
        const [a, b] = tramoDe(info, 1, retraso, chip?.dura ?? PERSISTENTES.entra_s, "el chip de piso");
        const p = interpolate(frame, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.sale });
        chip_ = p > 0 ? <ChipPiso piso={v!} opacidad={p} escala={MOV.escala.tarjeta_entra + (1 - MOV.escala.tarjeta_entra) * p} /> : null;
      } else if (v === null) {
        const [a, b] = tramoDe(info, 1, retraso, chip?.dura ?? PERSISTENTES.sale_s, "el chip de piso");
        const p = interpolate(frame, [a, b], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.fundido });
        chip_ = p > 0 ? <ChipPiso piso={v0} opacidad={p} /> : null;
      } else {
        const dura = chip?.dura ?? MOV.dura.visor_cambio;
        const [a, b] = tramoDe(info, 1, retraso, Math.max(dura, 0.5), "el chip de piso");
        const cambio = interpolate(frame, [a, a + s(dura)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA.suave });
        const fase = interpolate(frame, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const brillo = fase <= 0 || fase >= 1 ? 0 : Math.sin(Math.PI * fase);
        chip_ = <ChipPiso piso={v} anterior={v0} cambio={cambio} brillo={brillo} />;
      }
    }
  }
  return <CapaFija>{chip_}<MarcaAgua opacidad={opMarca} /></CapaFija>;
};

/**
 * Capa compuesta propia para los elementos fijos: así Chrome los rasteriza igual haya lo
 * que haya debajo (sin ella, las esquinas del chip variaban ±1 según el contenido) y el
 * PNG para Manim (sistema/Assets.tsx) sale idéntico al de cualquier diapositiva.
 */
export const CapaFija: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, willChange: "transform" }}>{children}</div>
);
