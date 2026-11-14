// D02 Les quedan 32 horas (guion D02.1 a D02.3). El gancho: el tiempo del hackathon, las horas que se
// van en repetir pasos y la promesa de que eso lo haga un flujo.
//
// Entra con un fundido de 0,4 s desde D01 (es otro video): el cuadro 0 ya muestra el visor apagado,
// con el 8 fantasma al 8 %, y la marca de agua.
//
// D02.1 (2,7 s propios). El visor de 7 segmentos se acerca (alto 184 a 200 px) mientras enciende
//   32:00:00 de izquierda a derecha (1,2 s), y sube Les quedan 32 horas. (de las 16:00 del sábado al
//   cierre del envío, el domingo a las 23:59). Cuadro final: visor ámbar de 200 px centrado en
//   (960, 430) y la frase en hueso a 88 px en y 720, con 32 horas en ámbar.
// D02.2 (3,7 s). La frase se va, el visor se achica a 90 px y sube a y 150, aparece la grilla de 32
//   horas (8 por 4, cuadrados de 110 px con 16 de aire, de a uno con desfase de 0,02 s), sube la
//   pregunta en hueso a 72 px en y 300 y caen seis pastillas, de a una con un golpe chico. Las horas
//   que tapa cada pastilla pasan a hueso al 30 %: cerca de la mitad. Dónde cae cada pastilla sale de una
//   semilla fija (ubicarPastillas).
// D02.3 (3,5 s). La pregunta se va, las pastillas viajan a una fila en y 560 y se vuelven nodos de
//   120 px (la palabra se apaga al despegar y sube debajo del nodo, a 49 px, cuando llega), se dibujan las conexiones y un dato ámbar recorre la fila:
//   a su paso cada nodo late y queda con un brillo suave, las horas grises vuelven a su color y la
//   grilla baja al 25 %. Sube
//   Eso lo puede hacer un flujo. en hueso a 88 px en y 790, con un flujo en ámbar.
//   El visor chico se queda arriba: el flujo le devuelve las horas al reloj.
//
// Debajo de todo, el fondo de la charla con dos destellos por las pistas en D02.1 y D02.3
// (FondoVivo). D02.2 va sin destellos: ya está cargada.
//
// Íconos de los nodos: magnifying-glass (buscar), copy (copiar), list-check (resumir) y comments
// (avisar) de manim/comun/iconos. Pegar (un portapapeles) y otra vez (una flecha en círculo) no están
// en esa carpeta y se dibujan acá, en hueso y del mismo tamaño.
import React from "react";
import { random } from "remotion";
import {
  COLOR,
  conAlfa,
  CURVA,
  FondoVivo,
  GROSOR,
  Icono,
  medidasPastilla,
  mezclar,
  MOV,
  pasosDe,
  RESORTE,
  Texto,
  textos,
  unir,
  useAparecer,
  useDesvanecer,
  useEntra,
  useEntrar,
  useTramo,
  Visor7,
  type NombreIcono,
} from "../comun";
import { ICONO_NODO, RADIO_NODO, useLatido } from "./D01Portada";

export const pasos = pasosDe("D02");

// ---------------------------------------------------------------------------------------------
// Medidas.
// ---------------------------------------------------------------------------------------------
const VISOR = { x: 960, y: 430, alto: 200, altoLejos: 184, yChico: 150, altoChico: 90 };
const Y_FRASE1 = 720;
const Y_PREGUNTA = 300;
const Y_FRASE3 = 790;

// Una hora por cuadrado: las 32 que quedan a las 16:00 del sábado hasta el cierre del envío de proyectos.
const GRILLA = { cols: 8, filas: 4, lado: 110, aire: 16, y0: 400 };
const PASO_GRILLA = GRILLA.lado + GRILLA.aire;
const ANCHO_GRILLA = GRILLA.cols * GRILLA.lado + (GRILLA.cols - 1) * GRILLA.aire;
const ALTO_GRILLA = GRILLA.filas * GRILLA.lado + (GRILLA.filas - 1) * GRILLA.aire;
const X0_GRILLA = Math.round(960 - ANCHO_GRILLA / 2);
const RADIO_HORA = Math.round(RADIO_NODO * GRILLA.lado);
const BORDE_HORA = GROSOR.trazo_fino;

// Mezclas opacas en hex (mezclar() de tokens devuelve rgb() y no se puede volver a mezclar).
function aHex(c: string): string {
  const m = c.match(/\d+/g);
  if (!m) return c;
  return "#" + m.slice(0, 3).map((v) => Number(v).toString(16).padStart(2, "0")).join("");
}
const mezcla = (a: string, b: string, k: number): string => aHex(mezclar(a, b, k));

// Colores de una hora: encendida (noche con borde azul al 70 %) y perdida (hueso al 30 % sobre tinta).
// Con borde azul al 40 % y gris al 30 %, desde el fondo de la sala las horas perdidas no se
// distinguían de las otras (hoja_contactos.py D02 --sala): ahora las perdidas son claras y las que
// quedan, azules.
const HORA_RELLENO = COLOR.noche;
const HORA_BORDE = mezcla(COLOR.tinta, COLOR.azul, 0.7);
const HORA_GRIS = mezcla(COLOR.tinta, COLOR.hueso, 0.3);
const BORDE_PASTILLA = mezcla(COLOR.tinta, COLOR.hueso, 0.4);

const PASTILLA = { tam: 60, alto: 90 };
const FILA = { y: 560, lado: 120, paso: 260, yPalabra: 664, tamPalabra: 49 };
const xNodo = (i: number) => 960 + (i - 2.5) * FILA.paso;

const ICONOS: (NombreIcono | "portapapeles" | "otra-vez")[] = ["magnifying-glass", "copy", "portapapeles", "list-check", "comments", "otra-vez"];

// ---------------------------------------------------------------------------------------------
// Dónde caen las pastillas: semilla fija, sin encimarse, cerca de la mitad de las horas tapadas y repartidas.
// ---------------------------------------------------------------------------------------------
type Caida = { cx: number; cy: number; w: number; horas: number[] };

function horaRect(k: number) {
  const c = k % GRILLA.cols;
  const r = Math.floor(k / GRILLA.cols);
  const x = X0_GRILLA + c * PASO_GRILLA;
  const y = GRILLA.y0 + r * PASO_GRILLA;
  return { x, y, x1: x + GRILLA.lado, y1: y + GRILLA.lado, cx: x + GRILLA.lado / 2 };
}

let CACHE_CAIDAS: Caida[] | null = null;

/** La ubicación de las seis pastillas: la primera semilla D02-k que cumple las condiciones. */
export function ubicarPastillas(palabras: string[]): Caida[] {
  if (CACHE_CAIDAS) return CACHE_CAIDAS;
  const anchos = palabras.map((p) => medidasPastilla(p, PASTILLA.tam).ancho);
  const filasY = [0, 1, 2, 3].map((r) => GRILLA.y0 + r * PASO_GRILLA + GRILLA.lado / 2);
  const huecosY = [0, 1, 2].map((r) => GRILLA.y0 + r * PASO_GRILLA + GRILLA.lado + GRILLA.aire / 2);
  const ranuras = [...filasY, ...huecosY];
  for (let k = 1; k < 500; k++) {
    const caidas: Caida[] = [];
    let ok = true;
    for (let i = 0; i < palabras.length && ok; i++) {
      const w = anchos[i];
      let puesta = false;
      for (let intento = 0; intento < 40 && !puesta; intento++) {
        const r = random(`D02-${k}-${i}-${intento}-ranura`);
        const cy = ranuras[Math.floor(r * ranuras.length)];
        const libre = ANCHO_GRILLA - w - 20;
        const cx = X0_GRILLA + 10 + w / 2 + random(`D02-${k}-${i}-${intento}-x`) * libre;
        const choca = caidas.some((o) => Math.abs(o.cx - cx) < (o.w + w) / 2 + 30 && Math.abs(o.cy - cy) < PASTILLA.alto + 24);
        if (!choca) {
          caidas.push({ cx: Math.round(cx), cy, w, horas: [] });
          puesta = true;
        }
      }
      if (!puesta) ok = false;
    }
    if (!ok) continue;
    // Las horas que tapa cada pastilla: las que quedan cubiertas en un cuarto de su superficie o más.
    const tomadas = new Set<number>();
    for (const p of caidas) {
      const x0 = p.cx - p.w / 2;
      const x1 = p.cx + p.w / 2;
      const y0 = p.cy - PASTILLA.alto / 2;
      const y1 = p.cy + PASTILLA.alto / 2;
      for (let h = 0; h < GRILLA.cols * GRILLA.filas; h++) {
        const q = horaRect(h);
        const sx = Math.max(0, Math.min(x1, q.x1) - Math.max(x0, q.x));
        const sy = Math.max(0, Math.min(y1, q.y1) - Math.max(y0, q.y));
        if (sx * sy >= 0.25 * GRILLA.lado * GRILLA.lado && !tomadas.has(h)) {
          tomadas.add(h);
          p.horas.push(h);
        }
      }
    }
    const filasTocadas = new Set([...tomadas].map((h) => Math.floor(h / GRILLA.cols)));
    const izquierda = caidas.filter((p) => p.cx < 960).length;
    const cadaUna = caidas.every((p) => p.horas.length >= 2);
    if (tomadas.size >= 13 && tomadas.size <= 17 && filasTocadas.size === 4 && izquierda >= 2 && izquierda <= 4 && cadaUna) {
      CACHE_CAIDAS = caidas;
      return caidas;
    }
  }
  throw new Error("D02: ninguna semilla dio una ubicación de las pastillas que cumpla las condiciones.");
}

// ---------------------------------------------------------------------------------------------
// Íconos dibujados acá (en hueso, del alto de los íconos de nodo).
// ---------------------------------------------------------------------------------------------
const Portapapeles: React.FC<{ cx: number; cy: number; alto: number; opacidad: number }> = ({ cx, cy, alto, opacidad }) => {
  // Tablero lleno, hoja recortada en el color del nodo y la pinza arriba.
  const w = alto * 0.8;
  const h = alto;
  return (
    <svg width={w} height={h} viewBox="0 0 80 100" style={{ position: "absolute", left: cx - w / 2, top: cy - h / 2, opacity: opacidad }}>
      <rect x={0} y={8} width={80} height={92} rx={10} fill={COLOR.hueso} />
      <rect x={13} y={26} width={54} height={60} rx={4} fill={COLOR.noche} />
      <rect x={22} y={0} width={36} height={20} rx={6} fill={COLOR.hueso} />
      <rect x={30} y={6} width={20} height={6} rx={3} fill={COLOR.noche} />
      <rect x={22} y={40} width={36} height={7} rx={3.5} fill={COLOR.hueso} />
      <rect x={22} y={56} width={26} height={7} rx={3.5} fill={COLOR.hueso} />
    </svg>
  );
};

const OtraVez: React.FC<{ cx: number; cy: number; alto: number; opacidad: number }> = ({ cx, cy, alto, opacidad }) => {
  // Una flecha en círculo: el arco va de los 300 a los 590 grados (sentido horario) y deja un hueco
  // arriba; la punta, al final del arco, apunta hacia el hueco.
  const r = 34;
  const g = (a: number) => (a * Math.PI) / 180;
  const p = (a: number): [number, number] => [50 + r * Math.cos(g(a)), 50 + r * Math.sin(g(a))];
  const [x0, y0] = p(300);
  const [x1, y1] = p(230);
  const t: [number, number] = [-Math.sin(g(230)), Math.cos(g(230))];
  const n: [number, number] = [Math.cos(g(230)), Math.sin(g(230))];
  const q = (k: number, m: number) => `${(x1 + t[0] * k + n[0] * m).toFixed(2)},${(y1 + t[1] * k + n[1] * m).toFixed(2)}`;
  return (
    <svg width={alto} height={alto} viewBox="0 0 100 100" style={{ position: "absolute", left: cx - alto / 2, top: cy - alto / 2, opacity: opacidad, overflow: "visible" }}>
      <path d={`M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 1 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`} fill="none" stroke={COLOR.hueso} strokeWidth={13} strokeLinecap="butt" />
      <polygon points={`${q(22, 0)} ${q(-4, -19)} ${q(-4, 19)}`} fill={COLOR.hueso} />
    </svg>
  );
};

// ---------------------------------------------------------------------------------------------
// Una pastilla que se vuelve nodo: la caja pasa de pastilla a nodo mientras viaja a la fila. Su palabra
// se apaga al despegar (las pastillas se cruzan en el viaje y las palabras se encimarían) y vuelve a
// subir debajo del nodo, a 49 px, cuando el nodo llegó.
// ---------------------------------------------------------------------------------------------
const PastillaNodo: React.FC<{
  palabra: string;
  desde: { cx: number; cy: number; w: number };
  hasta: { cx: number; cy: number };
  p: number; // 0 pastilla, 1 nodo (con resorte)
  estilo: React.CSSProperties; // la caída (paso 2)
  icono: (typeof ICONOS)[number];
  opIcono: number;
  latido: number;
  brillo: number; // el brillo suave del nodo encendido (0 a 1)
  salePalabra: number; // de 1 a 0 al despegar
  estPalabraNodo: React.CSSProperties; // la palabra debajo del nodo
}> = ({ palabra, desde, hasta, p, estilo, icono, opIcono, latido, brillo, salePalabra, estPalabraNodo }) => {
  const k = Math.max(0, Math.min(1, p));
  const cx = desde.cx + (hasta.cx - desde.cx) * p;
  const cy = desde.cy + (hasta.cy - desde.cy) * p;
  const w = desde.w + (FILA.lado - desde.w) * k;
  const h = PASTILLA.alto + (FILA.lado - PASTILLA.alto) * k;
  const radio = PASTILLA.alto / 2 + (Math.round(RADIO_NODO * FILA.lado) - PASTILLA.alto / 2) * k;
  const borde = mezcla(BORDE_PASTILLA, COLOR.azul, k);
  const relleno = mezcla(COLOR.tinta, COLOR.noche, k);
  const lado = Math.round(ICONO_NODO * FILA.lado);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${desde.cx}px ${desde.cy}px`, ...estilo }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: latido !== 1 ? `scale(${latido})` : undefined, transformOrigin: `${cx}px ${cy}px` }}>
        <div
          style={{
            position: "absolute",
            left: cx - w / 2,
            top: cy - h / 2,
            width: w,
            height: h,
            boxSizing: "border-box",
            borderRadius: radio,
            border: `${GROSOR.borde}px solid ${borde}`,
            background: relleno,
            boxShadow: brillo > 0 ? `0 0 ${Math.round(FILA.lado * 0.3)}px ${Math.round(FILA.lado * 0.04)}px ${conAlfa(COLOR.azul, 0.5 * brillo)}` : undefined,
          }}
        />
        {opIcono > 0 &&
          (icono === "portapapeles" ? (
            <Portapapeles cx={cx} cy={cy} alto={lado} opacidad={opIcono} />
          ) : icono === "otra-vez" ? (
            <OtraVez cx={cx} cy={cy} alto={lado} opacidad={opIcono} />
          ) : (
            <NodoIcono nombre={icono} cx={cx} cy={cy} alto={lado} opacidad={opIcono} />
          ))}
      </div>
      {salePalabra > 0 && (
        <Texto x={cx} y={cy} tam={PASTILLA.tam} alinear="centro" estilo={{ opacity: salePalabra }}>
          {palabra}
        </Texto>
      )}
      <Texto x={hasta.cx} y={FILA.yPalabra} tam={FILA.tamPalabra} alinear="centro" estilo={estPalabraNodo}>
        {palabra}
      </Texto>
    </div>
  );
};

const NodoIcono: React.FC<{ nombre: NombreIcono; cx: number; cy: number; alto: number; opacidad: number }> = ({ nombre, cx, cy, alto, opacidad }) => (
  <Icono nombre={nombre} alto={alto} x={cx} y={cy} opacidad={opacidad} />
);

// ---------------------------------------------------------------------------------------------
// La diapositiva.
// ---------------------------------------------------------------------------------------------
const T2 = { visor: 0.0, pregunta: 0.3, horas: 0.45, desfaseHoras: 0.02, pastillas: 1.75, desfasePastillas: 0.15, gris: 0.25 };
const T3 = { pregunta: 0.0, viaje: 0.05, desfaseViaje: 0.04, iconos: 0.55, palabras: 0.55, conexiones: 0.7, dato: 1.15, duraDato: 1.0, frase: 2.2 };

export const D02CuarentaYOchoHoras: React.FC = () => {
  const [reloj, frase1] = textos("D02", 1); // ["32:00:00", "Les quedan 32 horas."]
  const [pregunta, ...palabras] = textos("D02", 2); // la pregunta y las seis pastillas
  const [frase3] = textos("D02", 3);
  const caidas = ubicarPastillas(palabras);

  // ---- Paso 1: el visor se acerca y enciende; sube la frase.
  const acerca = useTramo(1, 0, 1.5, CURVA.sale);
  const encendido = useTramo(1, 0.15, 1.2, CURVA.lineal);
  const estFrase1 = unir(useEntrar(1, 1.5, { dura: 0.5 }), useDesvanecer(2, 0, 0.3));

  // ---- Paso 2: el visor se achica y sube, la grilla, la pregunta y las pastillas.
  const achica = useTramo(2, T2.visor, 0.5, CURVA.suave);
  const altoVisor = VISOR.altoLejos + (VISOR.alto - VISOR.altoLejos) * acerca + (VISOR.altoChico - VISOR.alto) * achica;
  const yVisor = VISOR.y + (VISOR.yChico - VISOR.y) * achica;
  const estPregunta = unir(useEntrar(2, T2.pregunta, { dura: 0.5 }), useDesvanecer(3, T3.pregunta, 0.3));
  const horas = Array.from({ length: GRILLA.cols * GRILLA.filas }, (_, h) => useEntra(2, T2.horas + h * T2.desfaseHoras, 0.25));
  const caen = caidas.map((_, i) => {
    const t = T2.pastillas + i * T2.desfasePastillas;
    return unir(useEntrar(2, t, { dura: 0.4, desde: "arriba", distancia: 60 }), {
      transform: `scale(${MOV.escala.golpe_chico - (MOV.escala.golpe_chico - 1) * Math.min(1, useEntra(2, t + 0.1, 0.5, RESORTE.golpe))})`,
    });
  });
  // Cuándo se apaga cada hora (la de la pastilla que la tapa) y cuándo vuelve (paso 3, al pasar el dato).
  const apagaDe = new Map<number, number>();
  caidas.forEach((p, i) => p.horas.forEach((h) => apagaDe.set(h, T2.pastillas + i * T2.desfasePastillas + T2.gris)));
  const apagado = Array.from({ length: GRILLA.cols * GRILLA.filas }, (_, h) => (apagaDe.has(h) ? useTramo(2, apagaDe.get(h)!, 0.3, CURVA.fundido) : 0));

  // ---- Paso 3: las pastillas viajan a la fila y se vuelven nodos; el dato recorre la fila.
  const viaje = caidas.map((_, i) => useEntra(3, T3.viaje + i * T3.desfaseViaje, 0.6, RESORTE.entrar));
  const opIconos = caidas.map((_, i) => useAparecer(3, T3.iconos + i * T3.desfaseViaje, 0.3).opacity as number);
  const salePalabras = caidas.map((_, i) => 1 - useTramo(3, T3.viaje + i * T3.desfaseViaje, 0.15, CURVA.fundido));
  const palabrasNodo = caidas.map((_, i) => useEntrar(3, T3.palabras + i * T3.desfaseViaje, { dura: 0.4, distancia: 24 }));
  const conexiones = [0, 1, 2, 3, 4].map((i) => useTramo(3, T3.conexiones + i * 0.06, 0.3, CURVA.suave));
  const avance = useTramo(3, T3.dato, T3.duraDato, CURVA.suave);
  const xIni = xNodo(0);
  const xFin = xNodo(5);
  const xDato = xIni + (xFin - xIni) * avance;
  const opDato = Math.min(useAparecer(3, T3.dato, 0.1).opacity as number, 1 - useTramo(3, T3.dato + T3.duraDato - 0.08, 0.12, CURVA.lineal));
  // Instante en que el dato pasa por x (invirtiendo la curva suave).
  const cuandoPasa = (x: number) => {
    const d = Math.max(0, Math.min(1, (x - xIni) / (xFin - xIni)));
    let a = 0;
    let b = 1;
    for (let k = 0; k < 30; k++) {
      const m = (a + b) / 2;
      if (CURVA.suave(m) < d) a = m;
      else b = m;
    }
    return T3.dato + a * T3.duraDato;
  };
  const latidos = caidas.map((_, i) => useLatido(3, Math.max(0, cuandoPasa(xNodo(i)) - 0.12)));
  // Cada nodo se enciende cuando el dato lo atraviesa y queda con un brillo suave.
  const encendidos = caidas.map((_, i) => useTramo(3, Math.max(0, cuandoPasa(xNodo(i)) - 0.12), 0.4, CURVA.sale));
  const brillos = latidos.map((l, i) => Math.max(Math.min(1, (l - 1) / 0.06), 0.45 * encendidos[i]));
  const vuelve = Array.from({ length: GRILLA.cols * GRILLA.filas }, (_, h) =>
    apagaDe.has(h) ? useTramo(3, Math.max(T3.dato, cuandoPasa(horaRect(h).cx) - 0.1), 0.3, CURVA.fundido) : 0,
  );
  const tenue = useTramo(3, T3.dato, T3.duraDato, CURVA.suave);
  const estFrase3 = useEntrar(3, T3.frase, { dura: 0.5 });

  const opGrilla = 1 - (1 - 0.25) * tenue;

  return (
    <>
      <FondoVivo pulsos={[1, 3]} />

      {/* La grilla de las 32 horas. */}
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: opGrilla }}>
        {horas.map((e, h) => {
          if (e <= 0) return null;
          const q = horaRect(h);
          const gris = apagado[h] * (1 - vuelve[h]);
          return (
            <div
              key={h}
              style={{
                position: "absolute",
                left: q.x,
                top: q.y,
                width: GRILLA.lado,
                height: GRILLA.lado,
                boxSizing: "border-box",
                borderRadius: RADIO_HORA,
                border: `${BORDE_HORA}px solid ${mezcla(HORA_BORDE, HORA_GRIS, gris)}`,
                background: mezcla(HORA_RELLENO, HORA_GRIS, gris),
                opacity: Math.min(1, 1.6 * e),
                transform: `scale(${0.7 + 0.3 * e})`,
              }}
            />
          );
        })}
      </div>

      {/* Las conexiones y el dato (debajo de los nodos). */}
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        {conexiones.map((c, i) => {
          if (c <= 0) return null;
          const x0 = xNodo(i) + FILA.lado / 2;
          const x1 = xNodo(i + 1) - FILA.lado / 2;
          return <line key={i} x1={x0} y1={FILA.y} x2={x0 + (x1 - x0) * c} y2={FILA.y} stroke={COLOR.azul} strokeWidth={GROSOR.trazo_normal} />;
        })}
        {avance > 0 && opDato > 0 && <circle cx={xDato} cy={FILA.y} r={14} fill={COLOR.ambar} opacity={opDato} />}
      </svg>

      {/* Las pastillas (paso 2), que se vuelven nodos (paso 3). */}
      {caidas.map((p, i) => (
        <PastillaNodo
          key={i}
          palabra={palabras[i]}
          desde={p}
          hasta={{ cx: xNodo(i), cy: FILA.y }}
          p={viaje[i]}
          estilo={caen[i]}
          icono={ICONOS[i]}
          opIcono={opIconos[i]}
          latido={latidos[i]}
          brillo={brillos[i]}
          salePalabra={salePalabras[i]}
          estPalabraNodo={palabrasNodo[i]}
        />
      ))}

      {/* El visor: se acerca y enciende (1), se achica y sube (2), se queda (3). */}
      <Visor7 texto={reloj} alto={altoVisor} x={VISOR.x} y={yVisor} encendido={encendido} />

      <Texto x={960} y={Y_FRASE1} tam="idea" alinear="centro" resaltar="32 horas" estilo={estFrase1}>
        {frase1}
      </Texto>
      <Texto x={960} y={Y_PREGUNTA} tam="frase" alinear="centro" estilo={estPregunta}>
        {pregunta}
      </Texto>
      <Texto x={960} y={Y_FRASE3} tam="idea" alinear="centro" resaltar="un flujo" estilo={estFrase3}>
        {frase3}
      </Texto>
    </>
  );
};

// La grilla, para quien la necesite medir: x de X0_GRILLA a X0_GRILLA + ANCHO_GRILLA, y de 415 a 415 + ALTO_GRILLA.
export const MEDIDAS_GRILLA = { x0: X0_GRILLA, y0: GRILLA.y0, ancho: ANCHO_GRILLA, alto: ALTO_GRILLA };
