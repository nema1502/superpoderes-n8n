// La diapositiva provisional: la que se ve mientras una diapositiva no tiene archivo,
// para que el armado funcione de punta a punta desde el primer día. Muestra el id, el
// título, el paso en curso, lo que va a decir la pantalla y una barra que se llena con
// la duración real del paso (la de deck.json), así el ensayo ya tiene los tiempos.
// Si la entrada es continua, arranca en el cuadro de la anterior y lo desvanece, como
// lo hará la diapositiva de verdad (la frontera queda idéntica).
import React from "react";
import { Anterior } from "../comun/Anterior";
import { Capa } from "../comun/movimiento";
import { Texto } from "../comun/Texto";
import { diapoDeck, textos } from "../deck";
import { RESPIRO, useLineal, usePasos, useTramo } from "../pasos";
import { COLOR, conAlfa, CURVA, FPS, MOV, OPACIDAD, RETICULA, TIPO } from "../tokens";

const X = 160;

/** Lo que cambia con cada paso: aparece al empezar el paso y se va al empezar el siguiente. */
const CapaPaso: React.FC<{ k: number; n: number; children: React.ReactNode }> = ({ k, n, children }) => {
  const entra = useTramo(k, 0, 0.25, CURVA.fundido);
  const sale = useTramo(Math.min(k + 1, n), 0, 0.25, CURVA.fundido);
  const op = (k === 1 ? 1 : entra) * (k < n ? 1 - sale : 1);
  return op > 0 ? <Capa estilo={{ opacity: op }}>{children}</Capa> : null;
};

const BarraPaso: React.FC<{ k: number }> = ({ k }) => {
  const info = usePasos();
  const dura = (info.cortes[k] - info.cortes[k - 1] - RESPIRO) / FPS;
  const p = useLineal(k, 0, Math.max(1 / FPS, dura));
  const b = RETICULA.barra_tiempo;
  const w = b.x1 - X;
  return (
    <div style={{ position: "absolute", left: X, top: b.y - b.grosor / 2, width: w, height: b.grosor }}>
      <div style={{ position: "absolute", inset: 0, borderRadius: b.grosor / 2, backgroundColor: conAlfa(COLOR.ambar, OPACIDAD.apagado) }} />
      <div style={{ position: "absolute", left: 0, top: 0, height: b.grosor, width: Math.max(b.grosor, w * p), borderRadius: b.grosor / 2, backgroundColor: conAlfa(COLOR.ambar, 0.6) }} />
    </div>
  );
};

const PuntoPaso: React.FC<{ k: number; n: number }> = ({ k, n }) => {
  const enCurso = useTramo(k, 0, 0.25, CURVA.fundido);
  const hecho = useTramo(Math.min(k + 1, n), 0, 0.25, CURVA.fundido);
  const listo = k < n && hecho > 0.5;
  const x = RETICULA.zona_segura.x1 - (n - k) * 44 - 14;
  const color = listo ? COLOR.hueso : enCurso > 0.5 || k === 1 ? COLOR.ambar : conAlfa(COLOR.ambar, OPACIDAD.apagado * 3);
  return <div style={{ position: "absolute", left: x - 14, top: RETICULA.barra_tiempo.y - 70, width: 28, height: 28, borderRadius: 14, backgroundColor: color }} />;
};

function recortar(t: string, max: number) {
  return t.length <= max ? t : `${t.slice(0, max - 1).trimEnd()}…`;
}

export const Provisional: React.FC<{ id: string }> = ({ id }) => {
  const info = usePasos();
  const d = diapoDeck(id);
  const n = info.n;
  const continuo = info.entrada.tipo === "continuo";
  // Con entrada continua, el cuadro 0 es el de la anterior: lo propio aparece después.
  const aparece = useTramo(1, continuo ? 0.25 : 0, 0.35, CURVA.fundido);
  const op = continuo ? aparece : 1;
  const duraciones = info.cortes.slice(1).map((c, i) => (c - info.cortes[i]) / FPS);
  return (
    <>
      {continuo && <Anterior sale={{ retraso: 0, dura: MOV.dura.fundido }} />}
      <Capa estilo={{ opacity: op }}>
        <Texto x={X} y={180} tam={TIPO.escala.fuente} color={COLOR.gris}>
          {`Provisional · ${d.motor === "manim" ? "Manim" : "Remotion"} · ${d.seccion === "respaldo" ? "respaldo" : "camino principal"}`}
        </Texto>
        <Texto x={X} y={300} tam={TIPO.escala.portada} color={COLOR.ambar}>
          {id}
        </Texto>
        <Texto x={X} y={430} tam={TIPO.escala.frase} lineas={2} ancho={1600} anclaY="primero">
          {d.titulo}
        </Texto>
        {Array.from({ length: n }, (_, i) => i + 1).map((k) => {
          const pantalla = textos(id, k);
          const resumen = pantalla.length ? pantalla.map((t) => `«${t}»`).join(" · ") : "(sin texto en pantalla)";
          return (
            <CapaPaso key={k} k={k} n={n}>
              <Texto x={X} y={600} tam={TIPO.escala.lectura} resaltar={`Paso ${k}`}>
                {`Paso ${k} de ${n} · ${duraciones[k - 1].toFixed(1).replace(".", ",")} s${d.pasos[k - 1].audio ? " · ding" : ""}`}
              </Texto>
              <Texto x={X} y={690} tam={TIPO.escala.fuente} color={COLOR.gris} lineas={5} ancho={1500} anclaY="primero">
                {recortar(resumen, 190)}
              </Texto>
              <BarraPaso k={k} />
            </CapaPaso>
          );
        })}
        {Array.from({ length: n }, (_, i) => (
          <PuntoPaso key={i} k={i + 1} n={n} />
        ))}
      </Capa>
    </>
  );
};
