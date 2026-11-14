// La transición entre dos diapositivas, como video aparte (la arma remotion/transicion.mjs
// y el armado la pega delante del paso 1): el cuadro 0 es <de> (el último cuadro de la
// diapositiva anterior) y el último es <a> (el primero de esta), idénticos a los PNG.
//   fundido: <a> aparece sobre <de> (0,4 s).
//   puertas: las puertas de capítulo se juntan sobre <de> (0,45 s), quedan cerradas (0,1 s)
//            y se abren sobre <a> (0,5 s). Solo D14, D18 y D20.
// Si las dos imágenes traen la marca de agua (marca = true), sale del PNG y la dibuja el
// sistema por encima de todo: queda quieta y por encima de las puertas.
import React from "react";
import { AbsoluteFill, Composition, Img, staticFile, useCurrentFrame } from "remotion";
import { Lienzo } from "../comun/Lienzo";
import { MarcaAgua } from "../comun/Marca";
import { CapaFija } from "./Diapositiva";
import { cierrePuertas, Puertas } from "../comun/Puertas";
import { ALTO, ANCHO, COLOR, conAlfa, CURVA, FPS, RETICULA, TIPO, TRANSICIONES } from "../tokens";

export type PropsTransicion = {
  /** Archivos en public del bundle (los copia transicion.mjs). Vacíos: esquema para el Studio. */
  de: string;
  a: string;
  tipo: "fundido" | "puertas";
  /** Cuadros de movimiento (el video tiene cuadros + 1). */
  cuadros: number;
  /** Dibujar la marca de agua encima (las dos imágenes la traen en el mismo píxel). */
  marca: boolean;
};

const Z = RETICULA.marca_agua.zona;
const RECORTE = `path(evenodd, "M0 0 H${ANCHO} V${ALTO} H0 Z M${Z.x} ${Z.y} h${Z.ancho} v${Z.alto} h${-Z.ancho} Z")`;

const Imagen: React.FC<{ src: string; marca: boolean; opacidad?: number; nombre: string }> = ({ src, marca, opacidad = 1, nombre }) => {
  if (opacidad <= 0) return null;
  if (!src) {
    return (
      <AbsoluteFill style={{ opacity: opacidad, backgroundColor: COLOR.tinta }}>
        <div style={{ position: "absolute", inset: 0, background: `repeating-linear-gradient(135deg, ${conAlfa(COLOR.gris, 0.08)} 0 2px, transparent 2px 30px)` }} />
        <div style={{ position: "absolute", left: 0, right: 0, top: 470, textAlign: "center", fontFamily: TIPO.familia, fontWeight: TIPO.peso, fontSize: 120, color: conAlfa(COLOR.gris, 0.6) }}>
          {nombre}
        </div>
      </AbsoluteFill>
    );
  }
  return <Img src={staticFile(src)} style={{ position: "absolute", left: 0, top: 0, width: ANCHO, height: ALTO, opacity: opacidad, clipPath: marca ? RECORTE : undefined }} />;
};

export const Transicion: React.FC<PropsTransicion> = ({ de, a, tipo, cuadros, marca }) => {
  const f = useCurrentFrame();
  let contenido: React.ReactNode;
  if (tipo === "fundido") {
    const p = f >= cuadros ? 1 : CURVA.fundido(Math.max(0, f / cuadros));
    contenido = (
      <>
        {p < 1 && <Imagen src={de} marca={marca} nombre="de" />}
        <Imagen src={a} marca={marca} opacidad={p} nombre="a" />
      </>
    );
  } else {
    const { cierre, abriendo } = cierrePuertas(f, cuadros);
    contenido = (
      <>
        <Imagen src={abriendo ? a : de} marca={marca} nombre={abriendo ? "a" : "de"} />
        <Puertas cierre={f >= cuadros ? 0 : cierre} />
      </>
    );
  }
  return (
    <Lienzo>
      {contenido}
      {marca && (
        <CapaFija>
          <MarcaAgua />
        </CapaFija>
      )}
    </Lienzo>
  );
};

export const PROPS_TRANSICION: PropsTransicion = {
  de: "",
  a: "",
  tipo: "puertas",
  cuadros: Math.round(TRANSICIONES.puertas.duracion_s * FPS),
  marca: true,
};

/** La composición «Transicion»: dura cuadros + 1 (las props mandan). */
export const ComposicionTransicion: React.FC = () => (
  <Composition
    id="Transicion"
    component={Transicion}
    durationInFrames={PROPS_TRANSICION.cuadros + 1}
    fps={FPS}
    width={ANCHO}
    height={ALTO}
    defaultProps={PROPS_TRANSICION}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, props.cuadros) + 1 })}
  />
);
