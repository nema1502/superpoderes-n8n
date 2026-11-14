// El reloj grande: SIEMPRE en el mismo lugar (220 px de alto, centrado en (1500, 520));
// lo que lo acompaña (las tres luces, «Tiempo.», la ronda) va debajo. Los números
// son el visor de 7 segmentos. El tiempo corre lineal: no se maquilla.
import { useCurrentFrame } from "remotion";
import React from "react";
import { s, tramoDe, usePasos } from "../pasos";
import { BRILLO, COLOR, conAlfa, FPS, MOV, OPACIDAD, RETICULA, TIPO } from "../tokens";
import { formatoReloj } from "./Contador";
import { Texto } from "./Texto";
import { useIdSvg, Visor7 } from "./Visor7";

const R = RETICULA.reloj;
const B = RETICULA.barra_tiempo;
const CP = MOV.cuentaPrevia;

export type EstadoCuenta = {
  /** Lo que muestra el visor: "1:00", "0:59"… o "30", "0". */
  texto: string;
  /** Segundos que faltan (sin redondear). */
  falta: number;
  /** Escala del latido de los últimos segundos (1 → 1,03), apagado antes del final. */
  latido: number;
  /** true en los dos parpadeos del cero. */
  parpadeo: boolean;
  /** 0 → 1: entra «Tiempo.» después de los parpadeos. */
  tiempo: number;
  /** Lo que queda de la barra (1 → 0). */
  barra: number;
  terminado: boolean;
};

/**
 * Cuenta regresiva del paso: arranca en `inicio` (s desde el comienzo del paso), baja de
 * a un segundo desde `desde` hasta 0 (lineal), late los últimos `latido` segundos, en 0
 * parpadea dos veces (0,4 s) y después entra «Tiempo.» (0,4 s). Todo eso tiene que
 * terminar antes del respiro del paso: si no, el render falla.
 */
export function useCuentaRegresiva(op: {
  paso: number;
  inicio: number;
  desde: number;
  formato?: "s" | "m:ss";
  latido?: number;
  /** Con «Tiempo.» al final (los relojes de escribir) o sin (la cuenta de 30 del ascensor). */
  conTiempo?: boolean;
  /** Parpadeo en el cero (sí por defecto). */
  conParpadeo?: boolean;
}): EstadoCuenta {
  const info = usePasos();
  const frame = useCurrentFrame();
  const { paso, inicio, desde, formato = desde >= 60 ? "m:ss" : "s", latido = desde >= 60 ? MOV.latidoUltimos.reloj_largo : MOV.latidoUltimos.cuenta_30, conTiempo = true, conParpadeo = true } = op;
  const cola = (conParpadeo ? MOV.dura.parpadeo : 0) + (conTiempo ? MOV.dura.tiempo_texto : 0);
  tramoDe(info, paso, inicio, desde + cola, "la cuenta regresiva", true);
  const t0 = info.cortes[paso - 1] + s(inicio);
  const transcurrido = (frame - t0) / FPS;
  const falta = Math.max(0, Math.min(desde, desde - transcurrido));
  const mostrado = frame <= t0 ? desde : Math.ceil(falta - 1e-9);
  const texto = formato === "m:ss" ? formatoReloj(mostrado) : String(mostrado);
  const enLatido = falta > 0 && falta <= latido;
  const pulso = enLatido ? 0.5 - 0.5 * Math.cos(2 * Math.PI * (falta % 1)) : 0;
  const despues = transcurrido - desde; // segundos desde que llegó a 0
  let parpadeo = false;
  if (conParpadeo && despues >= 0 && despues < MOV.dura.parpadeo) {
    const fase = Math.floor((despues / MOV.dura.parpadeo) * 4);
    parpadeo = fase === 0 || fase === 2;
  }
  const tTiempo = despues - (conParpadeo ? MOV.dura.parpadeo : 0);
  const tiempo = conTiempo ? Math.max(0, Math.min(1, tTiempo / MOV.dura.tiempo_texto)) : 0;
  return {
    texto,
    falta,
    latido: 1 + (MOV.escala.latido - 1) * pulso,
    parpadeo,
    tiempo,
    barra: desde > 0 ? falta / desde : 0,
    terminado: despues >= 0,
  };
}

// ---------- Piezas ----------

/** Cuenta previa: tres luces de 28 px en fila (apagadas en ámbar al 8 %) que se encienden de a una. */
export const CuentaPrevia: React.FC<{ luces: number[]; cx?: number; y?: number; opacidad?: number }> = ({ luces, cx = R.cx, y = R.luces_y, opacidad = 1 }) => {
  const id = useIdSvg("cp");
  const d = CP.diametro;
  const w = luces.length * d + (luces.length - 1) * CP.separacion;
  const pad = d;
  return (
    <svg width={w + 2 * pad} height={d + 2 * pad} style={{ position: "absolute", left: cx - w / 2 - pad, top: y - d / 2 - pad, overflow: "visible", opacity: opacidad }}>
      <defs>
        <filter id={id} x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation={(BRILLO.luz_cuenta.radio_por_diametro * d) / 2} />
        </filter>
      </defs>
      {luces.map((v, i) => {
        const cx0 = pad + d / 2 + i * (d + CP.separacion);
        const k = Math.max(0, Math.min(1, v));
        return (
          <g key={i}>
            <circle cx={cx0} cy={pad + d / 2} r={d / 2} fill={conAlfa(COLOR.ambar, OPACIDAD.apagado)} />
            {k > 0 && <circle cx={cx0} cy={pad + d / 2} r={d / 2} fill={COLOR.ambar} filter={`url(#${id})`} opacity={k * BRILLO.luz_cuenta.opacidad} />}
            {k > 0 && <circle cx={cx0} cy={pad + d / 2} r={d / 2} fill={conAlfa(COLOR.ambar, k)} />}
          </g>
        );
      })}
    </svg>
  );
};

/** La barra de 8 px en y 1020 que se acorta de derecha a izquierda (con su pista al 8 %). */
export const BarraTiempo: React.FC<{ queda: number; opacidad?: number }> = ({ queda, opacidad = 1 }) => {
  const w = B.x1 - B.x0;
  const q = Math.max(0, Math.min(1, queda));
  return (
    <div style={{ position: "absolute", left: B.x0, top: B.y - B.grosor / 2, width: w, height: B.grosor, opacity: opacidad }}>
      <div style={{ position: "absolute", inset: 0, borderRadius: B.grosor / 2, backgroundColor: conAlfa(COLOR.ambar, OPACIDAD.apagado) }} />
      {q > 0 && <div style={{ position: "absolute", left: 0, top: 0, height: B.grosor, width: Math.max(B.grosor, w * q), borderRadius: B.grosor / 2, backgroundColor: COLOR.ambar }} />}
    </div>
  );
};

export type PropsReloj = {
  /** Lo que muestra el visor ("1:00", "30", "0"). */
  texto: string;
  latido?: number;
  parpadeo?: boolean;
  /** 0 → 1: segmentos que se encienden de a uno (D11.1: «1:00» en 0,4 s). */
  encendido?: number;
  /** Cambio rodado del dígito (anterior + progreso). */
  anterior?: string;
  cambio?: number;
  /** Las tres luces de la cuenta previa debajo del visor (0 → 1 cada una); null: sin luces. */
  luces?: number[] | null;
  /** 0 → 1: «Tiempo.» debajo (72 px en y 760). */
  tiempo?: number;
  /** Lo que queda de la barra de abajo; null: sin barra. */
  barra?: number | null;
  /** Otro lugar o tamaño (el reloj chico de D19.3: alto 100 en (1690, 170)). */
  cx?: number;
  cy?: number;
  alto?: number;
  opacidad?: number;
  /** El texto de la palabra final, tal cual está en deck.json. */
  textoTiempo?: string;
};

/** El reloj grande (o el chico) con lo que va debajo. Con useCuentaRegresiva se mueve solo. */
export const Reloj: React.FC<PropsReloj> = ({
  texto,
  latido = 1,
  parpadeo = false,
  encendido = 1,
  anterior,
  cambio,
  luces = null,
  tiempo = 0,
  barra = null,
  cx = R.cx,
  cy = R.cy,
  alto = R.alto,
  opacidad = 1,
  textoTiempo = "Tiempo.",
}) => (
  <>
    <Visor7 texto={texto} alto={alto} x={cx} y={cy} latido={latido} parpadeo={parpadeo} encendido={encendido} anterior={anterior} cambio={cambio} opacidad={opacidad} />
    {luces && <CuentaPrevia luces={luces} cx={cx} opacidad={opacidad} />}
    {tiempo > 0 && (
      <Texto x={cx} y={R.tiempo_y} tam={TIPO.escala.frase} alinear="centro" estilo={{ opacity: tiempo * opacidad, transform: `translateY(${(1 - tiempo) * 30}px)` }}>
        {textoTiempo}
      </Texto>
    )}
    {barra !== null && <BarraTiempo queda={barra} opacidad={opacidad} />}
  </>
);
