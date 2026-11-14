// La hoja de estilo del sistema visual, para evaluarlo: seis páginas de
// 1920×1080 con los componentes a tamaño real (cada página es un cuadro como los de la
// charla) y dos muestras que combinan piezas como lo hará una diapositiva. Los textos de
// ejemplo salen de deck.json. La renderiza remotion/hoja_estilo.mjs a render/revision/.
import React from "react";
import { AbsoluteFill } from "remotion";
import { Anillo } from "../comun/Anillo";
import { Ascensor } from "../comun/Ascensor";
import { AscensorCorte, geometriaCorte } from "../comun/AscensorCorte";
import { ChipPiso } from "../comun/ChipPiso";
import { Globo } from "../comun/Globo";
import { Cable } from "../comun/Hilo";
import { Icono, type NombreIcono } from "../comun/Icono";
import { Lienzo } from "../comun/Lienzo";
import { Firma, FIRMA_COMPLETA, grosorIsotipo, Isotipo, MarcaAgua } from "../comun/Marca";
import { Pastilla } from "../comun/Pastilla";
import { Puertas } from "../comun/Puertas";
import { BarraTiempo, Reloj } from "../comun/Reloj";
import { Tarjeta } from "../comun/Tarjeta";
import { BurbujaRespuesta } from "../comun/Telefono";
import { Texto } from "../comun/Texto";
import { Cruz, grosorAsta, Insignia, lineaTachado, Palomita, Tachado } from "../comun/Trazos";
import { Visor7, VisorCaja } from "../comun/Visor7";
import { textos } from "../deck";
import { ALTO, ANCHO, COLOR, conAlfa, ICONOS, OPACIDAD, TIPO, TOKENS, type NombreColor } from "../tokens";
import { medirTexto } from "../comun/Texto";

const Pagina: React.FC<{ numero: number; titulo: string; children: React.ReactNode; marca?: boolean }> = ({ numero, titulo, children, marca = true }) => (
  <Lienzo>
    {children}
    <Texto x={1853} y={62} tam={TIPO.escala.fuente} color={COLOR.gris} alinear="der">
      {`Sistema visual · ${numero} · ${titulo}`}
    </Texto>
    {marca && <MarcaAgua />}
  </Lienzo>
);

const Rotulo: React.FC<{ x: number; y: number; children: string; alinear?: "izq" | "centro" | "der"; color?: string }> = ({ x, y, children, alinear = "izq", color = COLOR.gris }) => (
  <Texto x={x} y={y} tam={TIPO.escala.fuente} color={color} alinear={alinear}>
    {children}
  </Texto>
);

const Encabezado: React.FC<{ x: number; y: number; children: string }> = ({ x, y, children }) => (
  <Texto x={x} y={y} tam={TIPO.escala.lectura}>
    {children}
  </Texto>
);

const coma = (v: number) => String(v).replace(".", ",");

// ---------- 1 · Paleta y tipografía ----------

const PALETA: NombreColor[] = ["tinta", "hueso", "ambar", "rojo", "gris", "acero", "acero2", "aceroclaro", "vidrio", "pantalla", "marca"];
const NOMBRE: Record<NombreColor, string> = {
  tinta: "tinta",
  hueso: "hueso",
  ambar: "ámbar",
  rojo: "rojo",
  gris: "gris",
  acero: "acero",
  acero2: "acero 2",
  aceroclaro: "acero claro",
  vidrio: "vidrio",
  pantalla: "pantalla",
  marca: "marca (lima)",
  // Los tres tonos del afiche (tokens versión 3) no entran en la columna de la página 1 (once
  // muestras de 74 px llegan a y 970): se ven en D01 y D02, las diapositivas de prueba.
  noche: "noche",
  titulo: "título (amarillo lima)",
  azul: "azul",
};

// La escala con nombre: siete tamaños (rótulo = fuente = 49) más la idea arriba (64, del guion).
const ESCALA: { px: number; texto: string; color?: string }[] = [
  { px: TIPO.escala.portada, texto: "Portada" },
  { px: TIPO.escala.titulo, texto: "Título" },
  { px: TIPO.escala.grande, texto: "Paso clave" },
  { px: TIPO.escala.idea, texto: "Idea clave", color: COLOR.ambar },
  { px: TIPO.escala.frase, texto: "Frase principal" },
  { px: TIPO.escala.idea_arriba, texto: "Idea arriba" },
  { px: TIPO.escala.lectura, texto: "Lectura (mínimo)" },
  { px: TIPO.escala.fuente, texto: "Rótulo y fuente (mínimo)", color: COLOR.gris },
];

export const Pagina1: React.FC = () => (
  <Pagina numero={1} titulo="Paleta y tipografía">
    <Encabezado x={67} y={150}>
      Paleta · contraste sobre tinta
    </Encabezado>
    {PALETA.map((c, i) => {
      const y = 230 + i * 74;
      const t = TOKENS.color[c];
      const oscuro = ["tinta", "acero", "acero2", "vidrio", "pantalla"].includes(c);
      return (
        <React.Fragment key={c}>
          <div
            style={{
              position: "absolute",
              left: 67,
              top: y - 30,
              width: 60,
              height: 60,
              borderRadius: 12,
              backgroundColor: t.hex,
              boxSizing: "border-box",
              border: oscuro ? `2px solid ${COLOR.acero2}` : undefined,
            }}
          />
          <Texto x={150} y={y} tam={TIPO.escala.rotulo} color={c === "marca" ? COLOR.hueso : COLOR.hueso}>
            {NOMBRE[c]}
          </Texto>
          <Rotulo x={480} y={y}>
            {t.hex}
          </Rotulo>
          <Texto x={880} y={y} tam={TIPO.escala.rotulo} color={t.contraste >= 4.5 ? COLOR.hueso : COLOR.gris} alinear="der">
            {c === "tinta" ? "fondo" : `${coma(Math.round(t.contraste * 10) / 10)}:1`}
          </Texto>
        </React.Fragment>
      );
    })}
    <Encabezado x={1000} y={150}>
      Escala en px (Segoe UI Bold)
    </Encabezado>
    {ESCALA.map((e, i) => {
      const ys = [262, 392, 507, 607, 693, 768, 838, 901];
      return (
        <React.Fragment key={e.px}>
          <Rotulo x={1110} y={ys[i]} alinear="der">
            {String(e.px)}
          </Rotulo>
          <Texto x={1150} y={ys[i]} tam={e.px} color={e.color ?? COLOR.hueso}>
            {e.texto}
          </Texto>
        </React.Fragment>
      );
    })}
  </Pagina>
);

// ---------- 2 · Visor de 7 segmentos, chips y reloj ----------

export const Pagina2: React.FC = () => (
  <Pagina numero={2} titulo="Visor de 7 segmentos, chip y reloj">
    <Encabezado x={67} y={150}>
      7 segmentos en SVG (no es una fuente)
    </Encabezado>
    <Visor7 texto="0123456789" alto={96} x={80} y={275} ancla="izq" />
    <Visor7 texto="Pb" alto={96} x={80} y={420} ancla="izq" />
    <Visor7 texto="0:30" alto={96} x={300} y={420} ancla="izq" />
    <Visor7 texto="1:00" alto={96} x={610} y={420} ancla="izq" />
    <Rotulo x={67} y={515}>
      «Pb» = planta baja (una B se leería como un 8)
    </Rotulo>
    {[0.3, 0.6, 1].map((e, i) => (
      <VisorCaja key={i} cx={150 + i * 190} cy={630} ancho={160} alto={80} digito={56} triangulo={{ tam: 24, encendido: 0 }} texto="Pb" encendido={e} />
    ))}
    <VisorCaja cx={720} cy={630} ancho={160} alto={80} digito={56} triangulo={{ tam: 24, encendido: 1, brillo: 0.8 }} texto="Pb" />
    <Rotulo x={67} y={718}>
      se enciende segmento por segmento · ▲ listo para subir
    </Rotulo>
    {[1, 2, 3].map((p, i) => (
      <ChipPiso key={p} piso={p} cx={133 + i * 170} cy={835} />
    ))}
    <ChipPiso piso={3} anterior={2} cambio={0.45} brillo={0.6} cx={643} cy={835} />
    <Rotulo x={67} y={935}>
      chip de piso 132×84 · el dígito rueda al cambiar
    </Rotulo>
    <Reloj texto="30" luces={[1, 1, 0.55]} />
    <Rotulo x={1500} y={775} alinear="centro">
      reloj grande, siempre aquí
    </Rotulo>
    <Rotulo x={1500} y={840} alinear="centro">
      220 px · centro (1500, 520)
    </Rotulo>
    <Reloj texto="0:45" cx={1690} cy={190} alto={100} />
    <BarraTiempo queda={0.38} />
    <Rotulo x={1853} y={975} alinear="der">
      barra de 8 px en y 1020
    </Rotulo>
  </Pagina>
);

// ---------- 3 · Ascensor de frente y en corte ----------

// En la hoja, el corte va más bajo y más corto que en la charla, para dejar lugar al título.
const geoHoja = geometriaCorte("crono", { x0: 930, x1: 1330, rotulosX: 1380, yTecho: 200, ySuelo: 965, losas: [775, 565, 355], visorY: 154 });

export const Pagina3: React.FC = () => {
  const r = textos("D14", 1);
  return (
    <Pagina numero={3} titulo="Ascensor de frente y en corte">
      <Ascensor />
      <Rotulo x={450} y={1010} alinear="centro">
        de frente: portada y D04
      </Rotulo>
      <AscensorCorte
        geo={geoHoja}
        piso={1.55}
        puertas={0}
        visor={{ texto: "2", triangulo: { encendido: 1 } }}
        rotulos={[
          { texto: r[0], estado: { encendido: 1, hecho: 1 } },
          { texto: r[1], estado: { encendido: 1 } },
          { texto: r[2], estado: {} },
        ]}
      />
    </Pagina>
  );
};

// ---------- 4 · Puertas de capítulo ----------

export const Pagina4: React.FC = () => {
  const t = textos("D20", 1);
  return (
    <Pagina numero={4} titulo="Puertas de capítulo, a mitad de camino">
      <Texto x={960} y={470} tam="idea" alinear="centro">
        {t[0]}
      </Texto>
      <Texto x={960} y={580} tam="idea" alinear="centro" color={COLOR.ambar}>
        {t[1]}
      </Texto>
      <Texto x={960} y={780} tam="lectura" alinear="centro">
        {t[2]}
      </Texto>
      <Puertas cierre={0.64} />
    </Pagina>
  );
};

// ---------- 5 · La marca ----------

export const Pagina5: React.FC = () => (
  <Pagina numero={5} titulo="La marca: nemaxyz">
    <Encabezado x={67} y={170}>
      La N de un solo trazo (marca_nema)
    </Encabezado>
    {[48, 96, 200].map((alto, i) => {
      const x = [90, 330, 640][i];
      const y = 400 - alto / 2;
      return (
        <React.Fragment key={alto}>
          <Isotipo alto={alto} x={x} y={y} />
          <Rotulo x={x} y={560}>
            {`${alto} px`}
          </Rotulo>
          <Rotulo x={x} y={620}>
            {`trazo ${coma(Math.round(grosorIsotipo(alto) * 10) / 10)}`}
          </Rotulo>
        </React.Fragment>
      );
    })}
    <Rotulo x={67} y={760} color={COLOR.hueso}>
      lima: solo isotipo, marca de agua y firma
    </Rotulo>
    <Rotulo x={67} y={830}>
      un trazo abierto, sin relleno, sin rotar
    </Rotulo>
    <Rotulo x={67} y={900}>
      grosor: máx(4 px, 4,5 % del alto)
    </Rotulo>
    <Rotulo x={67} y={970}>
      arriba a la izquierda: la marca de agua real
    </Rotulo>
    <Firma estado={{ hilo: 0.78, lima: 0, nema: 0, xyz: [0, 0, 0], xyzHueso: 0, arroba: 0 }} cx={1500} cy={330} cola={[-230, 150]} />
    <Rotulo x={1500} y={480} alinear="centro">
      D20.3: el cable dibuja la N…
    </Rotulo>
    <Firma estado={FIRMA_COMPLETA} cx={1460} cy={720} arrobaY={840} />
    <Rotulo x={1460} y={950} alinear="centro">
      …y la N pasa a lima: la firma
    </Rotulo>
  </Pagina>
);

// ---------- 6 · Piezas ----------

export const Pagina6: React.FC = () => {
  const p = textos("D02", 4);
  const r = textos("D06", 1);
  const v = textos("D13", 2);
  const t = textos("D12", 2);
  const iconos = ICONOS.pisos as ("user" | "shield-halved" | "hand")[];
  const yTachado = 690;
  const wTachado = medirTexto(v[3], 60);
  return (
    <Pagina numero={6} titulo="Piezas">
      {[p[1], p[2], p[3]].map((texto, i) => (
        <Pastilla key={i} x={520} y={230 + i * 118} icono={iconos[i]}>
          {texto}
        </Pastilla>
      ))}
      <Texto x={120} y={600} tam={TIPO.escala.fuente} color={COLOR.rojo}>
        {v[2]}
      </Texto>
      <Cruz x={120 + medirTexto(v[2], TIPO.escala.fuente) + 34} y={600} tam={40} grosor={grosorAsta(TIPO.escala.fuente)} />
      {/* El texto tachado en hueso al 55 % (no en gris: el rojo tiene su misma luz) y el tachado con filete. */}
      <Texto x={120} y={yTachado} tam="lectura" color={conAlfa(COLOR.hueso, OPACIDAD.tachado_texto)}>
        {v[3]}
      </Texto>
      <Tachado x0={120} x1={120 + wTachado} y={lineaTachado(yTachado, 60)} />
      <Texto x={120} y={800} tam={TIPO.escala.fuente} color={COLOR.ambar}>
        {v[4]}
      </Texto>
      <Palomita x={120 + medirTexto(v[4], TIPO.escala.fuente) + 34} y={800} tam={40} grosor={grosorAsta(TIPO.escala.fuente)} />
      <Texto x={120} y={880} tam="lectura">
        {v[5]}
      </Texto>
      <BurbujaRespuesta x={1530} y={330} renglones={r.slice(1, 3)} punta={[1190, 380]} color={COLOR.ambar} />
      <Rotulo x={1530} y={490} alinear="centro">
        si es la respuesta: ámbar
      </Rotulo>
      <Tarjeta x={1530} y={790} ancho={480} alto={260}>
        <Icono nombre="chart-simple" alto={72} x={1530} y={740} color={COLOR.ambar} />
        <Texto x={1530} y={845} tam="lectura" alinear="centro">
          {t[3]}
        </Texto>
      </Tarjeta>
    </Pagina>
  );
};

// ---------- 7 · Íconos, anillo y cable ----------

const ICONOS_GUION: NombreIcono[] = [
  "bus",
  "handshake",
  "gavel",
  "briefcase",
  "chart-simple",
  "circle-check",
  "store",
  "fire",
  "list-check",
  "pen",
  "microphone",
  "comments",
  "calendar-check",
  "user-tie",
  "envelope",
  "triangle-exclamation",
];

export const Pagina7: React.FC = () => {
  const pisos = ICONOS.pisos as NombreIcono[];
  const nombres = ["para quién", "prueba", "pedido"];
  return (
    <Pagina numero={7} titulo="Íconos, anillo y cable">
      <Encabezado x={67} y={170}>
        Los íconos de los pisos (un sistema)
      </Encabezado>
      {pisos.map((n, i) => (
        <React.Fragment key={n}>
          <Icono nombre={n} alto={96} x={220 + i * 330} y={300} color={COLOR.ambar} />
          <Rotulo x={220 + i * 330} y={400} alinear="centro">
            {nombres[i]}
          </Rotulo>
        </React.Fragment>
      ))}
      {ICONOS_GUION.map((n, i) => (
        <Icono key={n} nombre={n} alto={72} x={130 + (i % 8) * 140} y={560 + Math.floor(i / 8) * 150} />
      ))}
      <Rotulo x={67} y={880}>
        Font Awesome Free 6.7.2 (solid) · CC BY 4.0
      </Rotulo>
      <Rotulo x={67} y={950}>
        los mismos SVG que usa Manim (manim/comun/iconos)
      </Rotulo>
      <Anillo cx={1560} cy={330} diametro={330} grosor={14} progreso={2 / 3} />
      <Visor7 texto="40" alto={130} x={1560} y={330} />
      <Texto x={1560} y={550} tam="frase" alinear="centro">
        segundos
      </Texto>
      <Cable x0={1260} y0={900} largo={480} grados={25} barrido={0.55} />
    </Pagina>
  );
};

export const PAGINAS: React.FC[] = [Pagina1, Pagina2, Pagina3, Pagina4, Pagina5, Pagina6, Pagina7];

// ---------- Muestras ----------

/** Muestra 1: el cuadro final de D14.1 (el ascensor de 30 s llegó: «0», ding, «?»). */
export const Muestra1: React.FC = () => {
  const r = textos("D14", 1);
  return (
    <Lienzo>
      <AscensorCorte
        preset="crono"
        piso={3}
        puertas={1}
        visor={{ texto: "3", triangulo: { encendido: 1 } }}
        rotulos={r.slice(0, 3).map((texto) => ({ texto, estado: { encendido: 1, hecho: 1 } }))}
        globo={{ estilo: { opacity: 1, transform: "scale(1)" } }}
      />
      <Reloj texto="0" luces={[1, 1, 1]} />
      <MarcaAgua />
    </Lienzo>
  );
};

/** Muestra 2: el cuadro final de D06.3 (las dos preguntas, con forma además de color). */
export const Muestra2: React.FC = () => {
  const t = textos("D06", 3);
  return (
    <Lienzo>
      <Texto x={960} y={150} tam="idea_arriba" alinear="centro">
        {t[0]}
      </Texto>
      <Texto x={960} y={230} tam="idea_arriba" alinear="centro" color={COLOR.ambar}>
        {t[1]}
      </Texto>
      <Globo x={560} y={500} ancho={760} alto={190} color={COLOR.rojo} cola={{ lado: "abajo", en: 0.16, punta: [-40, 52] }}>
        <Texto x={560} y={500} tam="frase" alinear="centro">
          {t[2]}
        </Texto>
      </Globo>
      <Insignia tipo="cruz" x={928} y={414} />
      <Texto x={560} y={700} tam="lectura" alinear="centro" color={COLOR.rojo}>
        {t[3]}
      </Texto>
      <Globo x={1360} y={500} ancho={760} alto={190} color={COLOR.ambar} cola={{ lado: "abajo", en: 0.84, punta: [40, 52] }}>
        <Texto x={1360} y={500} tam="frase" alinear="centro">
          {t[4]}
        </Texto>
      </Globo>
      <Insignia tipo="palomita" x={1728} y={414} />
      <Texto x={1360} y={700} tam="lectura" alinear="centro" color={COLOR.ambar}>
        {t[5]}
      </Texto>
      <Pastilla x={1360} y={820} tam={TIPO.escala.rotulo} icono="hand">
        {t[6]}
      </Pastilla>
      <MarcaAgua />
    </Lienzo>
  );
};

export const MUESTRAS: React.FC[] = [Muestra1, Muestra2];

/** La hoja completa: las siete páginas y las dos muestras en una grilla de 3 × 3 (5760×3240). */
export const HojaEstilo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLOR.acero }}>
    {[...PAGINAS, ...MUESTRAS].map((P, i) => (
      <div key={i} style={{ position: "absolute", left: (i % 3) * ANCHO, top: Math.floor(i / 3) * ALTO, width: ANCHO, height: ALTO, overflow: "hidden", outline: `2px solid ${COLOR.acero2}` }}>
        <P />
      </div>
    ))}
  </AbsoluteFill>
);
