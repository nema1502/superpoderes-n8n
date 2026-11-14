# Convenciones del sistema visual (Remotion)

> **Manual heredado del armado de la charla de octubre.** Lo que cuenta de su contenido (D01 a D20, el ascensor, los pisos, el reloj) es de esa charla y queda como ejemplo de cómo se resolvió. Sus comandos se escribieron para aquella carpeta: acá se corren desde la raíz de este repositorio y con el Python del entorno de la charla, no con `.venv/Scripts/python.exe`. Lo vigente para esta charla, con los comandos exactos, los tiempos medidos y las reglas para trabajar varios a la vez, está en `docs/ESTADO.md`.

El manual para quien construya las diapositivas de «Cómo hacer tu elevator pitch». Todo lo de acá se
probó el 23 de octubre de 2026 (`node remotion/probar_sistema.mjs` da «Todo bien»). Lo visual se ve en
`render/revision/sistema.png` (la hoja completa) y en `sistema_1.png` … `sistema_7.png` a tamaño real.
Los hallazgos de sistema de la revisión visual (tokens versión 2) están aplicados: qué cambió, qué no y qué
queda para cada diapositiva, en la sección 13.

**Las cinco reglas que no se negocian**

1. Los textos en pantalla salen de `contenido/deck.json` tal cual (`textos(id, paso)`). Si uno no entra,
   se ajusta el diseño o se reporta: el texto no se cambia.
2. Todo movimiento del paso k empieza y termina dentro del paso k y deja quietos sus últimos 0,3 s. Los
   hooks lo controlan: si una animación pisa el respiro, el render falla y dice cuál.
3. Lo correcto y lo incorrecto llevan siempre forma (palomita, cruz o tachado), además del color.
4. El verde lima es solo de la marca (isotipo, marca de agua, firma). La marca de agua y el chip de piso
   los pone el sistema: no se dibujan a mano ni se tapa su zona.
5. Mirar cada PNG que se renderiza, a tamaño real, antes de darlo por bueno.

## 0. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Tokens (colores, tipografía, retícula, movimiento, reglas de pasos) | `diseno/tokens.json` → `remotion/src/tokens.ts` |
| Componentes comunes | `remotion/src/comun/` (todo se importa de `../comun`) |
| Sistema de pasos | `remotion/src/pasos.ts` |
| Lectura de deck.json (textos, entradas, marca, chip) | `remotion/src/deck.ts` (y `remotion/lib/deck.mjs` en Node) |
| Una diapositiva | `remotion/src/diapos/<ID><Nombre>.tsx` (por ejemplo `D06IdeaClave.tsx`) |
| Registro de todas (generado) | `remotion/src/diapos/index.ts` |
| Entrada aislada por diapositiva (generada) | `remotion/src/entradas/<ID>.ts` |
| Envoltorio de cada diapositiva, provisional, transición, hoja de estilo | `remotion/src/sistema/` |
| Ejemplo comentado y caso roto | `remotion/src/ejemplos/` |
| PNG para Manim | `diseno/assets/` (+ `assets.json`) |
| Las diapositivas de Manim (D07, D09, D10): base, escenas y render | `manim/comun/charla.py`, `manim/escenas/`, `manim/render_diapo.py` (sección 11) |
| Salidas | `render/pasos/<ID>/<ID>_<k>.mp4`, `render/cuadros/<ID>_<k>.png`, `render/revision/` |

`index.ts` y `entradas/<ID>.ts` los escribe `remotion/generar_registro.mjs` (lo corre solo cada render).
No se versionan: en un clon nuevo, `node remotion/generar_registro.mjs` antes de `tsc` o del Studio.

## 1. Crear una diapositiva

1. Crear `remotion/src/diapos/<ID><Nombre>.tsx`. `<Nombre>` es el `nombre` de deck.json (por ejemplo
   `D12PisoDosPrueba.tsx`). El archivo exporta **`pasos`** y **el componente con el mismo nombre que el
   archivo**. Opcional: `opciones` (sección 4).
2. `node remotion/generar_registro.mjs`: desde ahí el Studio y `tsc` la ven, y la provisional desaparece.
3. Mirarla en el Studio (`cd remotion` y `pnpm studio`) y renderizarla (sección 8).

Plantilla mínima (D12 paso 1, con su entrada continua desde D11):

```tsx
// remotion/src/diapos/D12PisoDosPrueba.tsx
import React from "react";
import { Anterior, COLOR, pasosDe, Texto, textos, useEntrar } from "../comun";

// Duración de cada paso: la de deck.json (3,0 · 2,5 · 2,8 s), respiro de 0,3 s incluido.
// Se puede ajustar un paso, pero el ajuste se reporta: pasosDe("D12", { 2: 2.8 }).
export const pasos = pasosDe("D12");

export const D12PisoDosPrueba: React.FC = () => {
  const t = textos("D12", 1); // ["2", "Prueba", "= por qué creerles"], tal cual
  // Hooks: (paso, retraso en s, opciones). Paso 1, a los 0,6 s y a los 0,75 s.
  const titulo = useEntrar(1, 0.6);
  const definicion = useEntrar(1, 0.75);
  return (
    <>
      {/* Entrada continua: arranca en el último cuadro de D11 y lo desvanece (0,4 s). */}
      <Anterior sale={{ dura: 0.4 }} />
      <Texto x={860} y={430} tam="grande" estilo={titulo}>
        {t[1]}
      </Texto>
      <Texto x={860} y={550} tam="idea" color={COLOR.ambar} estilo={definicion}>
        {t[2]}
      </Texto>
      {/* El chip (1 → 2, el dígito rueda) y la marca de agua los pone el sistema. */}
    </>
  );
};
```

El ejemplo completo y comentado (entrada continua, teléfono, contador, paneles, barrido, Foco, Golpe,
globos con insignia) es `remotion/src/ejemplos/EjemploD06.tsx`. Los cronómetros:
`remotion/src/ejemplos/EjemploRelojes.tsx`.

Cosas que la plantilla da por hechas:

- Todo se posiciona en **coordenadas del cuadro** (1920×1080, origen arriba a la izquierda), como el
  «Cuadro final» del guion. No hay que poner `<Lienzo>`: lo pone el envoltorio.
- El componente no recibe props: los pasos, la entrada y el cuadro anterior están en el contexto
  (`usePasos()`), y los hooks los leen solos.
- Cada cuadro es función pura del número de cuadro: nada de `useState`, `Math.random()` (usar
  `random("semilla")` de Remotion) ni relojes.

## 2. Los pasos

Una diapositiva es una composición de Remotion; sus pasos son tramos de la misma línea de tiempo. Con
cortes c₀ = 0 < c₁ < … < cₙ (en cuadros), **el paso k (1…n, como en el guion) va del cuadro c₍ₖ₋₁₎ al
cₖ, los dos incluidos**: el último cuadro de un paso es el mismo cuadro que el primero del siguiente, y
la receta de codificación los deja idénticos al bit (medido: máx. 0 en el video decodificado).

- `pasosDe(id)` da la duración del **video propio** de cada paso: `duracion_animacion_s` de deck.json,
  con el respiro de 0,3 s adentro. Si la entrada es `fundido` o `puertas`, al paso 1 se le resta la
  transición (es otro video, que el armado pega delante): D14.1 dura 35,6 s en el deck y 34,55 s propios.
- Los tiempos del guion en el paso 1 de esas diapositivas se corren: `useDesfaseEntrada()` da lo que hay
  que restar (D14.1: «las luces a los 1,3 s» → `1.3 - desfase` = 0,25 s).
- `pasosDe(id, { 2: 3.0 })` ajusta un paso; `render.mjs` avisa cuando no coincide con deck.json (hay que
  reportarlo: el mapa de tiempos y el audio salen del deck). La cantidad de pasos tiene que ser la del
  deck, o el registro falla.

**Hooks** (todos validan contra el respiro; `retraso` y `dura` en segundos desde que empieza el paso):

| Hook | Devuelve | Para |
|---|---|---|
| `useEntra(paso, retraso, dura = 0,5, resorte = RESORTE.entrar)` | 0 → 1 con resorte, exactamente 1 al final | entradas |
| `useTramo(paso, retraso, dura = 0,5, curva = CURVA.suave)` | 0 → 1 con curva | trazos, desplazamientos, fundidos |
| `useSale(paso, retraso, dura = 0,3, curva)` | 1 → 0 | lo que se va |
| `useLineal(paso, retraso, dura)` | 0 → 1 lineal, sin tope de 6 s | el tiempo de los cronómetros |
| `useSegundos(paso)` | segundos desde que empezó el paso | lógica propia |
| `usePasoActual()` | `{ paso, t }` | saber en qué paso se está |
| `useDuracionPaso(paso)` | duración del paso en s | |
| `useDesfaseEntrada()` | lo que dura la transición de entrada (fundido o puertas) | |

- Lo que aparece en el paso k sigue en los pasos siguientes; para sacarlo, multiplicarlo por
  `useSale(k2, …)` o `unir(estilo, useDesvanecer(k2))`.
- Ninguna animación dura más de 6 s (salvo cronómetros: `useLineal`, `useCuentaRegresiva`,
  `useViajeCrono`). Todo movimiento ambiente (latidos, ondas) se apaga antes del respiro.
- Si una animación pisa el respiro, el render falla así: `A7.1: useEntra termina a los 1,50 s y el paso
  dura 1,40 s: tiene que terminar antes de los 1,10 s (los últimos 0,3 s van quietos: el respiro)`.

## 3. Cómo entra cada diapositiva

Cada diapositiva de deck.json tiene un campo estructural (el único que agregó el sistema):

```json
"entrada": { "tipo": "continuo" | "fundido" | "puertas" | "corte", "duracion_s": 0.4, "desde": "D20" }
```

| Entrada | Diapositivas | Qué es |
|---|---|---|
| `corte` | D01 | primer video: arranca en su propio cuadro 0 |
| `continuo` | D02-D13, D19, A8 (desde D19), A9 (desde A8) | la diapositiva arranca en el último cuadro de `desde` y lo transforma ella misma |
| `fundido` 0,4 s | D15, D17, A1-A7, A10 (estos desde D20) | video de transición aparte: `desde` se funde en el cuadro 0 de esta |
| `puertas` 1,05 s | D14, D18, D20 | video de transición aparte: las puertas de capítulo se juntan sobre `desde` (0,45 s), quedan 0,1 s y se abren sobre esta (0,5 s) |

**Continuo, en Remotion.** `render.mjs` copia `render/cuadros/<desde>_<n>.png` (el último cuadro de la
anterior) al bundle y la diapositiva lo muestra con `<Anterior>`:

- `<Anterior sale={{ retraso, dura }} />` lo desvanece en el paso 1; `opacidad` y `estilo` permiten
  moverlo a mano (D05: «barrido hacia la izquierda» → `estilo={{ transform: \`translateX(${-x}px)\` }}`).
- Lleva **huecos** en las zonas de la marca de agua y del chip cuando la anterior los trae: ahí los
  dibuja el sistema desde el cuadro 0 (en el mismo píxel, quietos, rodando o desvaneciéndose), así nunca
  hay dos copias superpuestas ni se mueven con el cuadro.
- Para redibujar algo del cuadro anterior encima en el mismo píxel (D02 con el ascensor de D01, D08 con
  los bloques de D07), se agrega su rectángulo a `huecos` y se dibuja con el mismo componente y props.
- Tiene que haberse ido al terminar el paso 1, o el render falla.
- Si el PNG de la anterior falta o está viejo y la anterior es de Remotion, `render.mjs` lo saca primero.
  Si es de Manim y falta, avisa y la diapositiva arranca desde un esquema gris (la frontera no empalma).
- Al final `render.mjs` compara el cuadro 0 con ese PNG y dice `frontera con D12.3: IDÉNTICA` (o cuántos
  píxeles difieren).

**Continuo, en Manim.** Ver la sección 11: el primer paso arranca con el PNG del último cuadro de la
anterior a pantalla completa (o reconstruye el estado con el mismo código, D10) y Manim deja también su
último cuadro de cada paso en `render/cuadros/<ID>_<k>.png`, sin pérdida, para la diapositiva siguiente.

**Fundido y puertas.** El video lo hace `remotion/transicion.mjs` (sección 8) entre `<desde>_<n>.png` y
`<ID>_0.png`; su cuadro 0 es idéntico al primero y el último al segundo. El armado lo pega delante del
paso 1 sin repetir el cuadro compartido. El cuadro 0 de la diapositiva es lo que «descubren» las puertas:
D14.1 ya tiene el ascensor en corte en su lugar; D18.1, solo la marca de agua (el título entra después).
El `audio` del deck (`ding:34.3`) cuenta desde el comienzo del video final, transición incluida.

## 4. Marca de agua y chip de piso (los pone el sistema)

- **Marca de agua**: isotipo lima de 48 px + «nemaxyz» hueso a 34 px, al 72 %, en x 67-300, y 38-86, en
  todos los pasos menos D01, D02.1, D02.2, D03 y D20.3 (`tokens.json → persistentes.marca_agua_sin`).
- **Chip de piso**: caja de vidrio de 132×84 con ▲ y el dígito en 7 segmentos de 56 px, en x 1721-1853,
  y 38-122, en las diapositivas con `piso` en deck.json (D09-D13).
- Cuando cambian (de un paso al siguiente, o desde la anterior con entrada continua) el sistema anima el
  cambio al empezar el paso: fundido de 0,3 s; el chip aparece con escala 0,9 → 1, o rueda el dígito
  (0,35 s) y el ▲ brilla una vez (D12, D13).
- Sus zonas son **reservadas** (`reticula.marca_agua.zona` y `reticula.chip_piso.zona`): nada más se
  dibuja ahí. Van en su propia capa compuesta (`CapaFija`), por eso salen idénticas al píxel en todas las
  diapositivas y en los PNG para Manim.
- Para otro tiempo de entrada o para dibujarlos a mano: `export const opciones: OpcionesDiapo =
  { persistentes: { marca: { retraso: 0.4, dura: 0.3 } } }` (o `marca: false`, `chip: false`, o
  `persistentes: false`). `OpcionesDiapo` está en `../sistema/tipos`.

## 5. Tokens

Todos salen de `diseno/tokens.json` (la misma fuente lee Manim y LaTeX). En TypeScript:
`import { COLOR, OPACIDAD, TIPO, RETICULA, MOV, CURVA, RESORTE, conAlfa } from "../comun"`.

**Color** (contraste WCAG sobre tinta):

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `tinta` | #070A0F | fondo de todo; texto sobre relleno ámbar o rojo | — |
| `hueso` | #F5F7FF | texto principal | 18,5:1 |
| `ambar` | #FFB547 | acento: la palabra clave de cada paso, X/Y/Z, lo correcto (con palomita), visores, relojes, cable, la luz | 11,3:1 |
| `rojo` | #FF7A7A | alerta: humo, tachados, «reescribir», cruces (con forma). Era #FF5C5C (6,5:1): con protanopía y con luz en la sala era el texto más débil | 7,9:1 |
| `gris` | #9AA3B8 | **el único gris de apoyo**: fuentes, rótulos de apoyo y lo pendiente; nunca la idea | 7,8:1 |
| `acero`, `acero2` | #1A2230, #2A3446 | cabina; hojas de acero (lado de la pared), hojas bajas, bordes de visor, burbujas | hueso encima 14,9 y 11,7:1 |
| `aceroclaro` | #4A586F | el lado claro de las hojas de acero, hacia la junta: las puertas se leen como objetos desde el fondo | 2,75:1 (hueso encima 6,7:1) |
| `vidrio` | #05070A | fondo de los visores de 7 segmentos | — |
| `pantalla` | #0E141D | pantalla del teléfono, relleno de tarjetas y de los bloques de 10 s (opaco, con borde ámbar) | — |
| `marca` | #B8FF3C | **solo** isotipo, marca de agua y firma | — |

`OPACIDAD`: apagado 0,08 (segmentos, luces, ▲ apagados) · foco 0,6 (hueso y ámbar) · tachado_texto 0,55
(el texto tachado) · borde_apoyo 0,4 (bordes en hueso de lo que acompaña: pastillas, burbujas, teléfono,
cabina) · marco 0,5 · losa 0,5 · pared 0,45 · banda_puerta 0,034 y canto_puerta 0,5 (el acero) · junta
0,4 / 0,7 / 1 (el NIVEL de la luz: ver Puertas) · luz_cabina (arriba 0,85, al 40 % del alto 0,35, abajo
0,08, tira en hueso 0,9) · barrido 0,18 · marca de agua 0,72. Con color:
`conAlfa(COLOR.hueso, OPACIDAD.foco_hueso)`. Ya no existen `pendiente` (lo pendiente va en `gris`),
`relleno_bloque` (los bloques van rellenos de `pantalla`) ni `brillo_puerta`.

**Tipografía**: Segoe UI Bold (`TIPO.familia`, peso 700) en todo. Escala en px (`tam` acepta el nombre o
el número), **siete tamaños**: `portada` 140 · `titulo` 120 · `grande` 104 · `idea` 88 · `frase` 72 ·
**`lectura` 60 (mínimo de lo que se lee)** · **`fuente` = `rotulo` 49 (mínimo absoluto)**; además
`idea_arriba` 64, que pide el guion para la idea cuando sube (D06.3, D20.2-3). Diferencias de 3-4 px no se
leen como jerarquía: un tamaño del guion que no está en la escala va al más cercano (96 → 104 o 88, 84 → 88,
68 → 72, 52 → 49). Fuera de la escala, solo los **héroe** de `TIPO.heroe`, cada uno con su motivo:
«elevator pitch» 128 (D01: mide lo que «Cómo hacer tu» a 120), las ecuaciones de D07 105 y la firma de
D20.3 96 (guion). Interlineado: 1,1 (títulos) · 1,25 (ideas y frases) · 1,3 (lectura). Los números de
tiempo no son texto: van en 7 segmentos (`Visor7`). `TIPO.astaEm` = 0,15: el asta de Segoe UI Bold (10,8 px
a 72), el grosor de una marca junto a un texto (`grosorAsta(tam)`).

**Retícula** (`RETICULA`): márgenes 67 px a los lados y 38 px arriba y abajo (zona segura x 67-1853,
y 38-1042) · marca de agua x 67-300, y 38-86 · chip x 1721-1853, y 38-122 · **reloj grande siempre en
(1500, 520) a 220 px**, luces en y 670, «Tiempo.» en y 760 · reloj chico (1690, 170) a 100 px · barra de
tiempo de 8 px en y 1020 · columna izquierda de los relojes x 120-1190 · **franja inferior: por debajo de
y 900 solo fuentes, firma y decoración** (`FRANJA_INFERIOR_Y`: en una sala plana, las cabezas de adelante le
tapan a la última fila el 10-15 % de abajo).

**Trazos** (`GROSOR`): tres, que se distinguen a simple vista: **fino 3** (corchetes, filetes, la cabina,
detalles chicos) · **normal 5** (globos, pastillas, bloques, recuadros, tarjetas, subrayado, paredes y losas
del hueco, la burbuja de respuesta) · **fuerte 7** (flechas, tachado). Fuera de los tres, con su motivo:
marco del ascensor de frente 10 (es la pared) · junta 6 (es una luz) · canto de las hojas de acero 4 (el
filo de una superficie) · contorno del teléfono 4 al 40 % · borde de visores y chip 2 · cable 4 (el trazo
de la N que dibuja al final) · las marcas (palomita y cruz: el asta del texto que acompañan).

**Movimiento** (`MOV`, `RESORTE`, `CURVA`): resortes `entrar` (damping 15, mass 0,7), `golpe` (14, 0,8),
`rebote` (9, 0,9, stiffness 120: solo el «?»), `suave` (200), `burbuja` (14), `mano` (11), `balanza` (12).
Curvas `suave` (inOut cúbica), `sale` (out cúbica), `entra`, `lineal`, `fundido` (inOut seno).
Duraciones: entrar 0,5 · golpe 0,5 · rebote 0,42 · voltear 0,5 · foco 0,3 · barrido 0,5 · cambio de visor
0,35 · contador 0,6-1,2 · fundido 0,4 · desvanecer 0,3 · parpadeo 0,4 · «Tiempo.» 0,4 · paneles 0,5.
Desfases: palabras 0,12 · renglones 0,15 · elementos 0,2. Distancias: entrar 60 px (40 de costado),
x/y/z 40 px. Escalas de partida: golpe 1,25 · golpe chico 1,1 · **rebote 0,4** (se pasa a 1,13 y
vuelve) · latido 1,03 · entrada de tarjeta 0,9.

**Brillos permitidos** (y ningún otro): segmento encendido del visor, luces de la cuenta previa, junta de
las puertas, el ▲ que brilla una vez, y la luz de la cabina abierta (un degradé, no un resplandor). Nada de
estrellas, destellos, confeti ni resplandores de fondo.
Excepción de esta charla (14 de noviembre): las estrellas del fondo, los destellos que recorren las pistas, el brillo del nodo activo (`brillo()` y `filtroBrillo()` de `remotion/src/comun/Luz.tsx`) y, solo en D14.1, una lluvia de cuadrados de la marca sin magenta. Cómo se usan: la cabecera de `remotion/src/comun/Luz.tsx`.

## 6. Componentes

Todos se importan de `../comun`, se dibujan en coordenadas del cuadro y aceptan, cuando tiene sentido,
`estilo` (opacidad y transform de los hooks de movimiento) u `opacidad`.

### Texto

- **`<Texto x y tam color alinear ancho lineas interlineado minimo resaltar estilo estiloPalabras numeros anclaY>`**
  `children` es el texto exacto. `x` según `alinear` (`"izq"` por defecto, `"centro"`, `"der"`); `y` es
  el centro óptico del renglón (o del bloque, o del primer renglón con `anclaY="primero"`). Mide con la
  fuente real y **nunca desborda la zona segura**: si no entra, parte en renglones (hasta `lineas`) y
  achica hasta `minimo` (60 en lectura, 49 en rótulos), con un AVISO; si ni así entra, el render falla
  con el texto culpable. `resaltar="tipo C"`, `resaltar={["X", "Y", "Z"]}` (ámbar) o
  `resaltar={{ "ganas de irse": COLOR.rojo }}` pinta partes (tienen que existir letra por letra).
  `numeros` = cifras de ancho fijo.
  ```tsx
  <Texto x={960} y={470} tam="idea" alinear="centro">{t[2]}</Texto>
  <Texto x={160} y={570} tam="lectura" color={COLOR.gris} lineas={2} ancho={1600}>{t[3]}</Texto>
  ```
- **`<Titulo>`**: Texto de 96 px que no baja de 72.
- **`medirTexto(texto, tam)`** da el ancho en px (para poner un ícono o una palomita al lado).
- **`<BarridoLuz paso retraso dura>`** envuelve a los `<Texto>` que cruza: franja de 120 px, hueso al
  18 %, inclinada 20°, recortada por las letras, una vez (0,5 s). Solo la idea clave, sobre la línea ámbar.

### Movimiento

Hooks que devuelven un estilo (`{ opacity, transform }`) para `estilo={…}`, y componentes del mismo
nombre que envuelven a sus hijos en una capa a pantalla completa:

| Hook / componente | Qué hace |
|---|---|
| `useEntrar(paso, retraso, { dura, desde, distancia })` / `<Entrar>` | sube 60 px (o entra 40 px de costado) con resorte damping 15, opacidad min(1, 1,5·p) |
| `useEntrarPalabras(texto, paso, retraso, { desfase })` | un estilo por palabra para `<Texto estiloPalabras>` (el título de la portada) |
| `useGolpe(paso, retraso, { chico })` / `<Golpe origen={[x, y]}>` | escala 1,25 → 1 (chico 1,1 → 1), sin giro y sin rebote |
| `useRebote(paso, retraso)` / `<Rebote origen>` | escala 0,4 → 1 con el resorte de rebote (se pasa a 1,13 en el cuarto cuadro y vuelve; la revisión estimaba 1,08), opacidad min(1, 4·p), con el origen en la punta de la cola del globo (`Globo` lo pone ahí; con `<Rebote>`, `origen={puntaGlobo(…)}`): SOLO el globo «?», que SALE de la cabina. De 2 → 1, el primer cuadro visible ya estaba casi opaco a 1,75 veces su tamaño y se salía del margen. |
| `useVoltear(paso, retraso)` / `<Voltear origen>` | rotateY 90° → 0°, perspectiva 1200 px: tarjetas e íconos |
| `useEscalar(paso, retraso, { desde: 0.9 })` | escala desde 0,9 con fundido: cabina, avatar, burbuja |
| `useAparecer` / `useDesvanecer` / `<Aparecer>` / `<Desvanecer>` | fundidos |
| `unir(a, b, …)` | junta estilos: multiplica opacidades, encadena transform |
| `<Capa estilo origen>` | capa a pantalla completa con un estilo (para animar un grupo) |
| `<Foco paso retraso>` | lo de adentro baja en 0,3 s a hueso al 60 % y su ámbar al 60 % (los componentes del sistema lo hacen solos). Más abajo quedaba ilegible desde el fondo de una sala con luz; si falta jerarquía, que lo nuevo crezca o lo viejo se achique a 0,9, no apagarlo más |

```tsx
const golpe = useGolpe(1, 0.2);
<Texto x={120} y={280} tam="grande" color={COLOR.ambar} estilo={golpe}>{t[1]}</Texto>
<Foco paso={3}>{/* lo ya explicado */}</Foco>
```

### Contador

`useContador(paso, retraso, desde, hasta, dura = 0,8)` da el valor (Easing.out cúbica);
`formatoReloj(252)` → «4:12»; `<Contador paso desde hasta x y tam formato>` lo escribe con cifras de
ancho fijo. Para 7 segmentos: `<Visor7 texto={String(Math.round(v))} …>`.

### Visor de 7 segmentos

- **`<Visor7 texto alto x y ancla latido opacidad encendido parpadeo anterior cambio brillo>`**: dígitos
  de verdad en SVG. Caracteres `0-9 P b : -` y espacio («Pb» = planta baja). Segmento encendido en
  ámbar con brillo leve; apagado en ámbar al 8 % (el «8» fantasma). `encendido` 0 → 1 los prende de a
  uno («Pb» en 0,4 s); `parpadeo` los apaga; `anterior` + `cambio` (0 → 1, 0,35 s) hace rodar el dígito.
  `anchoVisor(texto, alto)` da su ancho.
- **`<VisorCaja cx cy ancho alto digito triangulo={{ tam, encendido, brillo }} texto …>`**: la caja de
  vidrio con borde de acero, ▲ y visor; el cambio rodado se recorta con la caja.
- **`<ChipPiso piso anterior cambio brillo opacidad escala cx cy ancho>`**: el chip (lo pone el sistema;
  en D15.3 va chico al lado de cada bloque: `cx`, `cy`, `ancho={80}`).

### Reloj

- **`useCuentaRegresiva({ paso, inicio, desde, formato, latido, conTiempo, conParpadeo })`**: arranca en
  `inicio` (s del paso), baja de a un segundo (lineal) desde `desde`, late los últimos 10 s (5 en la de
  30), en 0 parpadea dos veces (0,4 s) y entra «Tiempo.» (0,4 s). Devuelve `{ texto, latido, parpadeo,
  tiempo, barra, falta, terminado }`. Falla si no termina antes del respiro.
- **`<Reloj texto latido parpadeo encendido luces tiempo barra cx cy alto textoTiempo>`**: el reloj grande
  en su lugar fijo, con `luces` (las tres de la cuenta previa) y `tiempo` («Tiempo.» en y 760) debajo y la
  `barra` abajo. El reloj chico de D19.3: `cx={1690} cy={170} alto={100}`.
  ```tsx
  const cuenta = useCuentaRegresiva({ paso: 2, inicio: 0.3, desde: 60 }); // D11.2
  <Reloj texto={cuenta.texto} latido={cuenta.latido} parpadeo={cuenta.parpadeo} tiempo={cuenta.tiempo} barra={cuenta.barra} />
  ```
- `<CuentaPrevia luces={[1, 1, 0]} />` y `<BarraTiempo queda={0.4} />` sueltos.

### Ascensor de frente

**`<Ascensor marco apertura junta trazoMarco visor opacidad detras>`**: marco de 10 px en hueso al 50 %,
dos puertas de acero cepillado (de acero2 a aceroclaro hacia la junta, con su canto) con la junta de luz
ámbar (nivel 0,4 en reposo, 0,7 «listo»: el núcleo va pleno; el nivel solo cambia el brillo), visor de
vidrio con «Pb» y ▲ arriba. Todo escala con el ancho del marco (560 px = 1): D01 usa el de los tokens
(x 170-730, y 230-950), D04 `marco={{ x0: 140, y0: 290, x1: 560, y1: 830 }}`. `apertura` 0 → 1 abre las
puertas (entran en la pared) y deja ver `detras` (D02: el micro); `trazoMarco` 0 → 1 dibuja el marco;
`visor={{ texto: "Pb", encendido, triangulo: { encendido, brillo } }}`. Para encender la junta con un
fundido: `junta={OPACIDAD.junta_reposo * encendido}` (D01).

### Ascensor en corte y el viaje de 30 s

- **`geometriaCorte("mapa" | "crono", ajustes)`**: «mapa» = D08 (hueco x 420-780, y 150-1000, losas
  790/560/330, rótulos desde x 860); «crono» = D14 y D19 (x 300-700, y 120-1010, losas 800/570/340,
  rótulos desde x 760). Da `pisoY(k)`, `centroCabina(k)` y `centroTramo(k)` (donde va cada rótulo).
  **El mapa y el cronómetro ubican los rótulos con la misma regla**, `centroTramo(k)`: el medio del
  recorrido de la cabina en su tramo (el mapa tiene que verse igual que su uso). Los «10 s» del mapa pueden
  ir en el centro de la banda, porque miden el tramo.
- **`<AscensorCorte preset geo estructura losas relleno opacidadHueco escalaTrazos cable cabina piso puertas
  visor rotulos globo>`**: paredes y techo de 5 px en hueso al 45 %, losas de 5 px al 50 % (al 25 y 30 %,
  desde el fondo de la sala, los «tres pisos» desaparecían); `estructura` y `losas` (0 → 1) se dibujan como
  trazos; `relleno` = el relleno opaco (`pantalla`) de los tramos, como los bloques de D07; `cable` baja
  desde la polea; `cabina` aparece; `piso` continuo 0-3; `puertas` 0 → 1 (al abrirse se ve la cabina
  **iluminada**: ámbar al 85 % arriba que cae al 8 % abajo, con la tira de luz en hueso, `OPACIDAD.luz_cabina`);
  `rotulos` = los tres textos de deck.json con su estado `{ visible, encendido, hecho }` (gris → ámbar →
  hueso con palomita). `globo={{ estilo: useRebote(…), texto: "?" }}` sale de la cabina en el piso 3 (a la
  izquierda en el mapa, a la derecha en el cronómetro): a 30 px de la cabina, **encima** de la pared del
  hueco (su relleno tinta la tapa), con la cola de 50 px o menos y el «?» a 104 px; en el cronómetro sube
  30 px más para dejar 70 px de aire sobre «Pedido» (`ASCENSOR_CORTE.globo`). `cajaGloboCabina(g)` da su caja, para
  poner algo debajo. `opacidadHueco` apaga el hueco (paredes, techo, polea, losas, cable y visor) y deja la
  cabina, los rótulos y el globo; `escalaTrazos` (0,6 en el ascensor chico) divide los grosores por la
  escala de la capa, para que ninguna línea baje de su trazo.
- **Palomitas en columna**: las de los tramos hechos miden 56 px, toman el grosor del asta del rótulo
  (10,8 px a 72) y van todas en la misma x, 28 px después del rótulo más largo (`columnaPalomitas(textos,
  x, tam, icono)`). AscensorCorte lo hace solo; tres `<RotuloPiso>` sueltos (AscensorConCuenta de D14)
  reciben `xPalomita={columnaPalomitas(…)}`.
- **`useViajeCrono(paso, luz1)`**: el cronómetro entero: luces a `luz1`, +1 s, +2 s; las puertas de la
  cabina se cierran 0,5 s después de la tercera; sube 30 s lineales; visor y rótulo cambian al EMPEZAR
  cada tramo; la cuenta baja de 30 a 0 y late los últimos 5 s; al llegar, ding (`dingS`), puertas abiertas
  (0,6 s) y globo (`globoS`). D19.2: `luz1 = 0.6` (ding a los 33,6 s); D14.1: `1.3 - useDesfaseEntrada()`.
- **`<AscensorCrono paso luz1 rotulos globo>`**: todo junto (corte, cuenta grande y luces), para D14.1,
  D19.2, A8.2 y A9.1. D19.4 y A8.3 bajan la cabina antes: se arman con `AscensorCorte` + `useViajeCrono`.

### Puertas y paneles

- **`<Puertas cierre>`** (0 abiertas, 1 cerradas): dos hojas de 960×1080 de acero cepillado, sombra
  sobre lo que tapan y la línea de luz ámbar de 6 px al juntarse. `cierrePuertas(f, total)` da el cierre
  del cuadro f (0,45 s inOut, 0,1 s, 0,5 s out). Las usa la transición «puertas»; la marca de agua queda
  encima.
- **`<Paneles x y ancho alto progreso>`** (D06.2): dos paneles chicos del alto de un renglón que tapan
  un texto y se abren (0,5 s), desvaneciéndose en sus últimos 0,15 s. Se dibujan encima del texto. Son
  hojas bajas: acero2 plano, canto y junta.
- **`PanelAcero`** (lo usan todas): la hoja va de acero2 (lado de la pared) a aceroclaro (#4A586F, hacia la
  junta), con una banda de brillo suave (hueso al 3,4 %) al 45 % del ancho; del lado de la junta, el canto
  claro (4 px en hueso al 50 %) y un filete de sombra hasta la luz. Sin segunda costura ni banda marcada
  (la hoja parecía un ropero o una cortina). **Las hojas de menos de 200 px de alto van planas** (acero2,
  canto y junta, sin banda: con 105 px de alto, cualquier franja las volvía una barra borrosa).
- **`Junta`**: el núcleo (6 px, `GROSOR.junta`) va **siempre en ámbar pleno**; `opacidad` es el nivel de
  la luz: hasta `junta_reposo` (0,4) solo enciende o apaga el núcleo (fundidos), y de ahí para arriba crece
  el brillo (`brillos.junta` × nivel): reposo 0,4, lista 0,7, capítulo 1. Con la opacidad en todo el grupo,
  el núcleo en reposo salía (115, 88, 50): una veta de óxido, no una luz.

### Trazos

`<Palomita x y tam grosor progreso>` (ámbar) · `<Cruz x y tam grosor progreso>` (roja) · `<Insignia
tipo="palomita" | "cruz" x y diametro progreso>` (la marca en un círculo, para la esquina de un globo o
tarjeta) · `<Tachado x0 x1 y progreso>` (rojo, 7 px, con un filete de tinta de 3 px a cada lado que corta
las letras) · `<Subrayado x0 x1 y progreso trazos>` (ámbar, 5 px; `trazos` para línea a trazos) ·
`lineaTachado(y, tam)` y `lineaSubrayado(y, tam)` dan la `y` para un `<Texto>`.

- **La marca toma el grosor del asta del texto que acompaña**: `grosor={grosorAsta(tam del texto)}` (0,15
  em: 10,8 px a 72, 7,4 px a 49), y un tamaño parecido al de la mayúscula o mayor (las de los pisos: 56 px
  junto a rótulos de 72). Suelta, sin texto, el grosor es 0,18 × tam.
- **El texto tachado va en hueso al 55 %** (`OPACIDAD.tachado_texto`), no en gris: el rojo tiene la misma
  luz que el gris (1,0:1) y el tachado se separaba de las letras solo por el tono; con el filete y el texto
  más oscuro se separa por luz (sistema_6, también con protanopía y en `--sala`).

```tsx
<Texto x={160} y={570} tam="lectura" color={conAlfa(COLOR.hueso, OPACIDAD.tachado_texto)}>{t[4]}</Texto>
<Tachado x0={160} x1={160 + medirTexto(t[4], 60)} y={lineaTachado(570, 60)} progreso={useTramo(3, 0.6, 0.4)} />
<Cruz x={x} y={y} tam={44} grosor={grosorAsta(60)} />
```

### Pastilla, globo, tarjeta, anillo

- **`<Pastilla x y tam color opacidadBorde grosor relleno colorTexto icono marca ancho estilo>`**: borde
  de 5 px **en hueso al 40 % por defecto** (es un elemento de apoyo, como la Tarjeta de A4), relleno tinta,
  texto hueso a 60 px; `icono` a la izquierda (56 px, en hueso si el borde es de apoyo); `marca={{ tipo:
  "cruz", progreso }}`; `color={COLOR.ambar}` solo si la pastilla ES la respuesta del paso;
  `relleno={COLOR.rojo}` para «humo» (texto en tinta). `medidasPastilla(texto, tam)` da sus medidas.
  **Con ícono de piso, solo para las tres partes del pitch** (D02.4, la hoja). Una pregunta que alguien
  dice va en un `Globo`, con su cola: en D06.3, «¿Hay para tipo C?» en una pastilla con la mano se leía
  como una parte del pitch y no como una pregunta, al lado de otras dos preguntas que eran globos.
- **`<Globo x y ancho alto cola color grosor radio relleno estilo>`**: cuerpo redondeado con cola (un solo
  trazo); `cola={{ lado: "abajo", en: 0.16, punta: [-40, 52] }}` (la punta relativa a donde nace). Crece
  desde la punta (el origen del `estilo`). Los hijos (los `<Texto>`) en coordenadas del cuadro.
- **`<Tarjeta x y ancho alto color opacidadBorde grosor radio relleno estilo>`**: radio 28, borde 5 px;
  va con `useVoltear`. A4: `color={COLOR.hueso} opacidadBorde={0.4} relleno={COLOR.pantalla}`.
- **`<Anillo cx cy diametro grosor progreso>`**: se llena desde las 12 en sentido horario, con pista al 8 %.

### Teléfono

`<Telefono cx cy escala estilo>` (520×940, contorno de 4 px en hueso al 40 %, pantalla #0E141D, barra de
chat sin nombre: con 6 px de hueso pleno era lo más brillante del cuadro y el único objeto con línea blanca
gruesa); adentro, en coordenadas del teléfono: `<BurbujaVoz duracion barras onda>` (▶, la onda de 20
barras que puede bajar a 6, la duración a 60 px) y `<Escribiendo fase>`. Afuera, en el cuadro:
`<BurbujaRespuesta x y renglones punta color>` (borde de 5 px, en hueso al 40 % por defecto y
`color={COLOR.ambar}` cuando ES la respuesta del paso, como en D06.1; la cola apunta a `punta`: usar
`aCuadro(tel, 520, y)` para el borde derecho del teléfono). En el paso siguiente, si ya no es lo nuevo, va
adentro de un `<Foco>`. Sin logo ni verde de WhatsApp. El teléfono no tiene que ser el centro de la
composición: si su pantalla queda vacía, más chico (0,85) o bajado hasta salir por el borde de abajo
(D06.1 lo baja a cy 700; lo que sale de la zona segura lo permite una excepción de `zona_segura` en
`armar/auditoria_reglas.json`). `BurbujaVoz` se escala con `estilo={{ transform: \`scale(k)\` }}`
alrededor de su borde derecho (`derecha`): con 20 barras y «4:12» mide 477 px y la pantalla 484, así que a
escala 1 ya se sale 11 px por la izquierda (D06.1 la empieza a 0,93 con `derecha` 480 y la lleva a 1,3
mientras se encoge).

### Marca nemaxyz

- **`<Isotipo alto x y progreso color opacidad>`**: la N de un solo trazo de `marca_nema()` (×100, eje y
  hacia abajo: `N_PATH`), sin relleno, uniones en punta, grosor `max(4 px, 4,5 % del alto)`, alto mínimo
  48. `progreso` 0 → 1 la dibuja (Create); por encima de 1 la borra desde el comienzo. `x, y` = esquina
  de su línea media.
- **`<Logotipo alto x y tamTexto texto colorTexto>`**: N + «nemaxyz» (siempre en minúsculas), separación
  0,45 × alto, la palabra centrada en su altura de x con la N. Portada: `texto="nemaxyz · Nicolás Mejía"`.
- **`<MarcaAgua>`**: la pone el sistema.
- **`<Firma estado cx cy alto arroba>`** + **`useFirma(paso, retraso)`** (D20.3): el hilo ámbar entra
  desde abajo a la izquierda, dibuja la N, la N pasa de una vez a lima, aparece «nema», bajan x, y, z
  (ámbar → hueso) y aparece «@nemaxyz» en lima. Cuadro final: N de 96 px + «nemaxyz» a 96 px centrados
  en `cy`, «@nemaxyz» a 60 px 120 px abajo (`arroba={null}` si Nicolás no lo confirma).

### Hilo, cable e íconos

- **`<Hilo d progreso color grosor>`**: un trazo que se dibuja (por defecto el cable de la cabina: ámbar
  de 4 px).
- **`<Cable x0 y0 largo grados barrido>`** (D12.1): el cable cargador como arco de LARGO CONSTANTE (L =
  600 px; radio = L ÷ ángulo), ficha USB-A fija y USB-C siguiendo la tangente; `barrido` 0 → 1, una luz
  lo recorre. `caminoArco` y `finDelArco` para animarlo a mano.
- **`<Icono nombre alto x y ancla color estilo>`**: los SVG de `manim/comun/iconos` (Font Awesome Free
  6.7.2 solid, los mismos que Manim). Los de los pisos son un sistema **reservado**: `user` = para quién,
  `shield-halved` = prueba, `hand` = pedido (`ICONOS.pisos`), y como ícono (en una pastilla, un rótulo,
  una lista o una fila) no se usan para nada más; para otra cosa, otro ícono (`comments`…) o ninguno.
  Revisión: en D06.3 la mano de «¿Hay para tipo C?» le daba a `hand` dos sentidos en la misma charla. La
  mano que se levanta en la escena del micro (D02.2) es parte de la escena: es la sala respondiendo al
  pedido del vendedor («levanten la mano»). Para uno nuevo: copiar el .svg a esa carpeta, `node
  remotion/generar_registro.mjs` y mirarlo en `sistema_7.png` (o en una hoja propia).

### Anterior

Ver la sección 3. `<Anterior sale={{ retraso, dura }} opacidad estilo huecos />`.

## 7. Reglas

- **Textos**: de `textos(id, paso)`, sin retocar. Sin emojis. «nemaxyz» siempre en minúsculas.
- **Tamaños**: lo que se lee, 60 px o más; rótulos y fuentes, 49 px o más (el sistema no deja bajar de
  49). Solo los siete de la escala (más `idea_arriba` y los héroe con su motivo). Una idea por paso y como
  mucho 2 renglones por idea (salvo los pitches de ejemplo de D15).
- **Trazos**: fino 3, normal 5, fuerte 7 (y las excepciones de la sección 5). Lado a lado, una pastilla de
  3 px junto a globos de 5 px parece un descuido.
- **Zona segura**: x 67-1853, y 38-1042. `Texto` y `Pastilla` no la dejan pasar; lo demás se cuida a mano.
- **Franja inferior**: por debajo de y 900, solo fuentes, firma y decoración; nada que haya que leer para
  entender el paso (desde la última fila de una sala plana, las cabezas tapan ese 10-15 %).
- **Lima**: solo isotipo, marca de agua y firma. Nunca para un dato, un título ni «lo correcto».
- **Correcto e incorrecto**: siempre con forma (palomita ámbar, cruz o tachado rojo), no solo con color, y
  **la forma pegada a la palabra** que califica (una cruz en la esquina del globo no alcanza para
  «reescribir»). La marca toma el grosor del asta del texto que acompaña (`grosorAsta`). El rojo de «ganas
  de irse» (D05.2) es tensión, no error: va sin cruz. El texto tachado, en hueso al 55 %.
- **Ámbar: como mucho dos cosas en ámbar por cuadro**: la palabra clave del paso y la marca de lo correcto
  (un globo con su palomita y su rótulo cuentan como una). Bordes y rótulos de apoyo van en hueso al 40 %
  (`OPACIDAD.borde_apoyo`): pastillas, burbujas que no son la respuesta del paso, aros numerados, teléfono.
  Texto sobre un relleno ámbar, en tinta.
- **Luz**: en nada que tenga que leerse como luz (la junta, la cabina abierta, los segmentos encendidos) el
  ámbar **no baja del 60 %** donde está la fuente (la junta entera, la parte de arriba de la cabina; el
  degradé que cae desde ahí sí baja): más bajo sale marrón, una veta de óxido o una caja color café. Para
  atenuar una luz se baja su brillo, no su color. Los bloques y tramos no son luz: relleno opaco `pantalla`
  con borde ámbar.
- **Números 1-2-3 en ámbar: solo los pisos** (visor, chip, rótulos de D08, insignias de D15.3, D18.2). Las
  demás listas numeradas (D14.2, D18.1, D19.3, D19.5) llevan el número en hueso (en un círculo de acero2 o
  con aro en hueso al 40 %): un número ámbar en esta charla quiere decir «piso». Y ninguna frase de una
  lista a la altura de una losa: se leería «frase 1 = piso 1».
- **Un solo gris de apoyo**: `gris` (#9AA3B8) para fuentes, rótulos de apoyo y lo pendiente. Nada de hueso
  al 60 % haciendo de gris al lado del gris (dos grises de matiz distinto parecen un error de color).
- **Lo pendiente, solo en un viaje**: el estado pendiente (en gris) es para lo que espera su turno durante un
  viaje o un cronómetro (los tramos que faltan en D08.2, D14.1 y D19), nunca para el contenido que el paso
  presenta. En el mapa de D08.1 los rótulos van en hueso pleno con el número en ámbar (el orador los explica
  21 s) y pasan a gris recién al arrancar el viaje de D08.2 (revisión: en gris se leían como apoyo, del mismo
  gris que los «10 s» y las fuentes).
- **Mapa y cronómetro**: los rótulos de los pisos con la misma regla (`centroTramo`); ver Ascensor en corte.
- **Marca de agua y chip**: los pone el sistema; nada se dibuja en sus zonas.
- **Reloj grande**: siempre en (1500, 520) a 220 px; lo que lo acompaña, debajo.
- **Foco**: en los pasos acumulativos (D04.1, D09.3, D12.2-D12.3, D13.2-D13.3, A10), lo ya explicado
  va adentro de `<Foco paso={k}>` (baja al 60 %), y también **lo que vuelve como recuerdo** cuando entra
  lo nuevo del paso (la respuesta de D06.1 cuando entra la idea en D06.2; los globos de D20.2, si quedan
  en el mismo paso que la tarea); la idea clave, el chip y la marca de agua nunca.
- **Rebote** solo para el «?» (0,4 → 1 desde la punta de su cola). **Golpe** sin giro ni rebote. Sin confeti.
  Excepción de esta charla (14 de noviembre): las estrellas del fondo, los destellos que recorren las pistas, el brillo del nodo activo (`brillo()` y `filtroBrillo()` de `remotion/src/comun/Luz.tsx`) y, solo en D14.1, una lluvia de cuadrados de la marca sin magenta. Cómo se usan: la cabecera de `remotion/src/comun/Luz.tsx`.
- **Cada animación** ≤ 6 s (salvo cronómetros); cada paso termina con 0,3 s quietos; nada ambiente al
  corte.
- **Determinismo**: nada de `Math.random()` ni estado; `random("semilla")` de Remotion.
- **Tope de texto nuevo**: unas 10 palabras por paso (`docs/reglas_contenido.md` 7.2).

## 8. Renderizar

Desde la raíz del proyecto (los scripts trabajan desde `remotion/` solos):

| Comando | Qué hace |
|---|---|
| `node remotion/render.mjs D06 D08` | cada paso a `render/pasos/<ID>/<ID>_<k>.mp4` (h264 High, yuv420p, BT.709, sin audio, QP 16 y cuadro clave en el último cuadro) y los cortes a `render/cuadros/<ID>_<k>.png` (k = 0 primer cuadro, 1…n el último de cada paso); dice la frontera con la anterior |
| `node remotion/render.mjs --still D06 pasos` | solo los cortes en PNG |
| `node remotion/render.mjs --still D06 45` | el cuadro 45 → `render/cuadros/D06_c45.png` |
| opciones | `--concurrencia N` (≤ 4) · `--crf 18` (borrador sin receta) · `--salida <carpeta>` · `--refrescar-anterior` · `--forzar-provisional` (la provisional de una de Manim) |
| `node remotion/transicion.mjs --de render/cuadros/D13_3.png --a render/cuadros/D14_0.png --tipo puertas --salida render/transiciones/D14.mp4` | la transición (fundido o puertas), con la receta; comprueba que los extremos sean idénticos a los PNG (`--duracion`, `--marca auto/si/no`) |
| `node remotion/generar_assets.mjs` | los PNG para Manim en `diseno/assets/` |
| `node remotion/hoja_estilo.mjs [páginas]` | la hoja de estilo en `render/revision/sistema*.png` |
| `node remotion/probar_sistema.mjs` | la prueba de punta a punta (ejemplo, fronteras, caso roto, cronómetros) |
| `node remotion/generar_registro.mjs` | rehace el registro y las entradas |
| `cd remotion && pnpm studio` · `pnpm tipos` | el Studio con todo · `tsc --noEmit` |

- Cada diapositiva se empaqueta sola (`src/entradas/<ID>.ts`): un error en una no rompe otra. Dos procesos
  pueden renderizar a la vez: cada entrada tiene su caché de webpack (Remotion la nombra con un hash
  que incluye la entrada) y un candado; cada proceso, su bundle; los archivos se escriben aparte y se
  renombran al final.
- Los avisos (`AVISO: …`) del navegador salen una vez cada uno: un texto que se achicó, una duración que
  no coincide con el deck, una frontera sin cuadro anterior.
- Tiempos medidos: bundle 1,5-10 s (con caché, menos); render ≈ 25 cuadros/s (D14 entero, 1110 cuadros,
  en 45 s).

## 9. Mirar

- Los cortes: `render/cuadros/<ID>_<k>.png`, a tamaño real, uno por uno (Read de cada PNG).
- El movimiento: una hoja de contactos por paso:
  `ffmpeg -i render/pasos/D06/D06_2.mp4 -vf "select='not(mod(n\,6))',scale=480:-1,tile=4x3" -frames:v 1 -update 1 hoja.png`.
- Las fronteras: `render.mjs` compara el cuadro 0 con la anterior; entre pasos,
  `.venv/Scripts/python.exe armar/comparar_cuadros.py <paso k>.mp4 <paso k+1>.mp4` (tiene que dar
  IDÉNTICOS).
- La fuente y las franjas de ClearType: `armar/verificar_fuente.py <png> "<texto>" <px> <y0> <y1>`
  (franjas: 0).
- **La sala**: `armar/hoja_contactos.py <ID…> --proyector` (un buen proyector en una sala oscura: 18:1) y
  **`--sala`** (la que hay que aprobar: proyector de aula con la luz encendida, 7:1, desenfoque σ = 1 px a
  960×540 y los colores saturados al 60 % del blanco). En `--sala` se ve lo que se pierde desde el fondo:
  líneas finas o al 25 %, el acero contra la tinta, el ámbar atenuado (que queda más apagado que el hueso:
  la palabra clave no puede depender solo de su color). Todas las hojas se miran también con `--sala`.
- **El proyector de verdad** (para la guía para presentar): probar D01 y D08.1 en el proyector del lugar
  (el acero de las puertas, la junta, las losas y los «10 s» en gris tienen que verse); proyector en modo
  presentación o sRGB, con el realce de blanco (BrilliantColor o parecido) apagado; que ninguna luz de la
  sala dé sobre la pantalla; si la última fila queda a más de unas 8 alturas de pantalla, sentar al público
  adelante.
- En el Studio, el cuadro anterior de una entrada continua se ve como un esquema gris (el PNG llega al
  renderizar).

## 10. Qué no hacer

- Escribir un texto a mano en vez de `textos(id, paso)`, o cambiarlo para que entre.
- Dibujar la marca de agua o el chip, o poner algo en sus zonas.
- Animar con `useState`, `Math.random()`, `setTimeout` o CSS `transition`/`animation`.
- Usar `interpolate` sin `extrapolateLeft/Right: "clamp"` (los hooks ya lo hacen).
- Sacar algo con `return null` de golpe en medio de un paso: se va con un fundido.
- Usar el lima, otro color fuera de los tokens u opacidades sueltas.
- Atenuar una luz bajando su ámbar (sale marrón), usar hueso al 60 % como gris, o dar borde ámbar a algo
  que acompaña (una pastilla, una burbuja que no es la respuesta, un número que no es un piso).
- Agregar brillos, destellos, sombras de texto, degradés de fondo o confeti.
  Excepción de esta charla (14 de noviembre): las estrellas del fondo, los destellos que recorren las pistas, el brillo del nodo activo (`brillo()` y `filtroBrillo()` de `remotion/src/comun/Luz.tsx`) y, solo en D14.1, una lluvia de cuadrados de la marca sin magenta. Cómo se usan: la cabecera de `remotion/src/comun/Luz.tsx`.
- Renderizar desde la raíz con `npx remotion …` (bajaría otro Chrome): usar los scripts.
- Tocar `index.ts` o `entradas/` a mano (se regeneran), o deck.json (es de quien escribe el guion).

## 11. Manim (D07, D09 y D10)

Las tres diapositivas de Manim usan una sola base, `manim/comun/charla.py`, que lee los mismos tokens y
el mismo deck que Remotion y dibuja y mueve con los mismos números. Probado el 23 de octubre de 2026 con
D07, la piloto: auditor de Manim APROBADO, frontera con D06.3 IDÉNTICA, fronteras entre pasos IDÉNTICAS,
`armar/auditar_cuadros.py D07` APROBADO, y en la calibración el texto de Manim y el de Remotion no se
distinguen ni ampliados ×4 (11.3).

### 11.1 Dónde está cada cosa

| Qué | Dónde |
|---|---|
| La base: tokens, `Texto`, formas, movimiento, pasos, marca de agua, chip, entrada continua | `manim/comun/charla.py` |
| Una diapositiva | `manim/escenas/<id>_<nombre>.py` con la clase `<ID><Nombre>` (`d07_cuanto_cabe.py` → `D07CuantoCabe`) |
| Renderizar | `.venv/Scripts/python.exe manim/render_diapo.py <ID…>` |
| Calibración contra Remotion | `manim/calibrar.py` (con `remotion/calibrar_manim.mjs` y `remotion/src/pruebas/CalibracionManim.tsx`) |
| Auditor de geometría (ahora ve los textos TeX: 11.9) | `manim/auditor/auditar.py` |
| Medios de Manim: caché de TeX, secciones sin pérdida | `render/manim/` |
| Salidas | `render/pasos/<ID>/<ID>_<k>.mp4` y `render/cuadros/<ID>_<k>.png`, igual que Remotion |

### 11.2 Plantilla mínima

```python
# manim/escenas/d09_piso_uno_frase.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))
from charla import AMBAR, GRIS, Aparecer, DiapoCharla, EntrarPartes, Texto, textos  # y lo que haga falta


class D09PisoUnoFrase(DiapoCharla):
    ID = "D09"

    def construct(self):
        t = textos("D09", 1)                          # tal cual deck.json
        self.paso(1)                                  # abre la sección del paso 1
        self.anterior()                               # el último cuadro de D08, a pantalla completa
        frase = Texto(t[1], 960, 430, tam=90, alinear="centro",
                      partes=["Ayudamos a ", "X", " a ", "Y", " haciendo ", "Z", "."], resaltar=["X", "Y", "Z"])
        fuente = Texto(t[2], 960, 1000, tam="fuente", color=GRIS, alinear="centro")
        self.tocar(                                   # un segmento: cada tramo en sus cuadros
            self.salir_anterior(0, 0.4),              # D08 se funde a tinta (como <Anterior sale>)
            EntrarPartes(frase, 0.3),                 # parte por parte, desfase 0,12 s
            Aparecer(fuente, 1.0, 0.3),
        )                                             # el chip «1» aparece solo (deck.json → piso)
        self.paso(2)                                  # cierra el 1 (quieto hasta su duración) y abre el 2
        ...
```

Lo que da por hecho:

- Todo se escribe en **px del cuadro** (1920×1080, origen arriba a la izquierda), como el «Cuadro final» del
  guion: `punto(x, y)` lo pasa a Manim; `u(px)`, `trazo(px)` (el `stroke_width` de un trazo de px píxeles),
  `caja_px(m)` (la caja de tinta en px). Importar `charla` deja 1 u = 135 px exactos en los dos ejes
  (cuadro de 14,222… × 8 u); `estilo.configurar_horizontal()` usa 14,222 y deja 135,002 px en x: no se usa.
- Los tokens con nombre: `HUESO`, `AMBAR`, `GRIS`, `ROJO`, `TINTA`…, `OPACIDAD`, `ESCALA` (px por nombre),
  `GROSOR`, `RADIO`, `RETICULA`, `DURA`, `DESFASE`, `CURVA`. Nada de colores ni números sueltos.
- Los textos salen de `textos(id, paso)`. A mano, solo los estados intermedios que el guion describe en la
  animación (D07.2: «palabras = 60 a 75»).
- Importar `charla` también configura Manim: 1080p30, fondo tinta, secciones guardadas, pedazos sin pérdida
  (`sin_perdida.activar()`) y sin caché de animaciones (la de Manim no mira los píxeles de las imágenes).

### 11.3 Texto (y la calibración)

**`Texto(cadena, x, y, tam, color, alinear, partes, resaltar, ancho, minimo)`** es `<Texto>` de Remotion en
Manim: un renglón, `x` según `alinear` (`"izq"` por defecto, `"centro"`, `"der"`), `y` = centro óptico, `tam`
en px o por nombre de la escala. Nunca sale de la zona segura: achica hasta el mínimo (60 en lectura, 49 en
rótulos) con un AVISO o falla con el texto culpable. El texto no se cambia.

- Se compone con **XeLaTeX y el mismo `segoeuib.ttf`** que usa Chrome: el mismo kerning, el mismo espacio,
  sin ligaduras de TeX (`Ligatures=TeXOff`), sin espacio extra después del punto (`\frenchspacing`) y cada
  parte en una caja horizontal (sin cortes ni guiones). **No se usa `Text` ni `estilo.texto()`** (Pango): deja
  huecos después de la T y espacia distinto (`docs/infra.md` §4).
- **Dónde queda**: dos reglas de 1 em sin ancho (`\rlap`, `\llap`) marcan el comienzo del renglón, la línea
  base y el final del avance; el texto se escala a 1 em = `tam` px y se ubica por ahí, como Chrome, y no por
  la caja de tinta, que cambia con las letras. La línea base es la de Chrome (`linea_base(y, tam)`): el
  renglón es una caja de `lh = round(tam × interlineado)` con el borde de arriba en `y − lh/2 − 0,07·tam`;
  Blink redondea el ascenso (2210/2048 em) y el descenso (514/2048 em) a px, pone arriba la mitad del
  interlineado que sobra (redondeada hacia abajo) y dibuja con la línea base en un píxel entero.
- **Peso**: el antialias de Chrome engorda un poco el texto (Manim sin ayuda tenía 1,5 a 6 % menos tinta).
  Cada glifo lleva un trazo de su mismo color: 0,4 px en hueso, 0,3 px en ámbar y gris (`REFUERZO_PX`).
- `partes=[...]`: cortes del texto, con sus espacios, para transformarlo por partes; la clave de una parte
  es su texto sin espacios en los bordes. Quedan `t.parte("ritmo")`, `t.centro_parte_px("ritmo")`,
  `t.izquierda`, `t.derecha`, `t.base` (px), `t.avance` y `t.tam`.
- `resaltar="60 a 75"`, `["X", "Y", "Z"]` (ámbar) o `{"reescribir": ROJO}`: tiene que coincidir letra por letra.
- Comprueba que cada parte dé tantos glifos como letras (si no, es una ligadura o un carácter que la fuente
  no tiene). Andan `≈ × · « » ¿ ¡ …` y las tildes; los caracteres especiales de TeX se escapan solos.
- Un renglón por `Texto`. Para dos renglones, dos `Texto` en su `y` (como dice el guion: «en y 870 y 950»);
  `linea_base(y, tam, renglon, renglones)` da la de cada renglón de un bloque, si hiciera falta.
- La primera vez cada cadena tarda 0,7-2,6 s (XeLaTeX); después sale de la caché (`render/manim/Tex/`).

**Calibración** (`manim/calibrar.py`, 23-oct-2026). Once muestras de 49 a 105 px, en hueso, ámbar y gris,
alineadas a la izquierda, al centro y a la derecha (entre ellas «Ayudamos a X a Y» a 60 y 96 px en hueso y
en ámbar), dibujadas con `<Texto>` de verdad en Remotion y con `Texto` en Manim, comparadas a resolución
nativa:

| Medida | Manim antes de ajustar (TeX, línea base continua y + 0,344·tam, sin trazo) | Manim ahora |
|---|---|---|
| Ancho de la tinta | igual al px en las once (496/496, 794/794, 1409/1409, 1400/1399…) | igual |
| Corrimiento horizontal | −0,2 a 0 px | −0,2 a +0,1 px |
| Corrimiento vertical | −0,44 a +0,90 px | **−0,18 a +0,22 px** (la línea base de Chrome) |
| Tinta, Manim contra Remotion | −1,5 a −5,9 % | **−0,9 a +1,5 %** (el trazo por color) |
| IoU de la tinta | 0,87-0,98 | 0,93-0,98 |
| Color de lo lleno | el mismo: (245, 247, 255), (255, 181, 71), (154, 163, 184) | el mismo |
| Diferencia media por píxel en la franja del texto | 0,9-4,5 niveles | 0,8-2,6 (solo en los bordes) |

Los recortes lado a lado quedan en `render/revision/calibracion/` (arriba Remotion, en el medio Manim, abajo
la diferencia ×4): ampliados ×4 no se distinguen. Un bloque como los de D07.3 (540×200 en la calibración; los
de D07.3 miden hoy 560×200), borde de 5 px hacia adentro y radio 24, tiene la misma geometría; con el relleno
ámbar al 12 % de la calibración, el relleno quedaba en
(36, 30, 21) en Manim y (37, 30, 22) en Chrome y el antialias de las esquinas difería hasta 42 niveles:
**entre motores no hay redibujo idéntico al píxel**. (Desde los tokens v2 el bloque va relleno de
`pantalla` opaco, que los dos motores dan igual: (13, 18, 29) en el video de los dos lados del corte
D07.3 → D08.1; la calibración sigue midiendo el 12 % como caso difícil.) Para volver a medir:
`.venv/Scripts/python.exe manim/calibrar.py` (15 s; `--sin-remotion` reusa el cuadro de Remotion;
`CALIBRAR_REFUERZO=0.3` y `CALIBRAR_BASE=continua` prueban otros ajustes sin tocar la base).

### 11.4 Pasos y tiempo

- `self.paso(k)` cierra el paso anterior (quieto hasta lo que dura en deck.json) y abre su sección
  (`paso_k`). Al final la base agrega una sección `fin` de un cuadro: el video del paso k son los cuadros de
  su sección más el primero de la siguiente (los dos extremos, s(d) + 1 cuadros, como en Remotion).
- `self.tocar(t1, t2, …)` toca un **segmento**: cada tramo con su `retraso` y su `dura` en s desde el
  comienzo del segmento, en cuadros enteros como `tramoDe` (s(x) = round(30·x)); el cuadro i del segmento le
  da a cada tramo α = (i − inicio)/duración. El segmento siguiente empieza cuando termina el último tramo.
  `self.esperar(s)` deja quieto.
- Falla con nombre y apellido si una animación pisa el respiro («D07.2: una animación termina a los 2,80 s y
  el paso dura 3,00 s: tiene que terminar antes de los 2,70 s…»), si dura más de 6 s, si el paso usa más
  cuadros que los de deck.json o si el cuadro anterior sigue en escena al terminar el paso 1.
- **Un objeto, un tramo por segmento** (si no, falla): Manim fija el punto de partida de cada animación al
  empezar el segmento, así que lo que depende de otra animación (una copia que baja y después se
  transforma) va en el `tocar()` siguiente.
- Cuadros exactos: un `play` de T s da `ceil(30·T)` cuadros y una espera quieta `int(30·T)`; la base pide
  (n − 0,5)/30 y (n + 0,5)/30 para que salgan n (sin eso se perdía un cuadro en cada espera).

### 11.5 El vocabulario de movimiento, en Manim

Los mismos nombres y números que en Remotion. Todas devuelven un `Tramo` para `tocar()`:

| Pieza | Qué hace | Es |
|---|---|---|
| `Entrar(m, retraso, dura=0,5, desde="abajo")` | el resorte de `spring()` de Remotion portado operación por operación (damping 15, mass 0,7, estirado a los cuadros del tramo; difiere del de Node en 3·10⁻¹⁶), opacidad min(1, 1,5·p), sube (1 − p)·60 px (40 de costado) | `useEntrar` |
| `EntrarPartes(texto, retraso, desfase=0,12)` | Entrar parte por parte; al final queda el `Texto` entero en escena | `useEntrarPalabras` |
| `Aparecer` / `Desvanecer(m, retraso, dura=0,3)` | fundido inOut seno; `Desvanecer` además lo saca de la escena | `useAparecer` / `useDesvanecer` |
| `AparecerImagen` / `DesvanecerImagen` | lo mismo para un PNG, multiplicando su alfa (`ImageMobject.set_opacity` lo pisa entero) | — |
| `Trazo(m, retraso, dura=0,4, curva="suave")` | `Create` con la curva inOut cúbica | `evolvePath` |
| `Desplazar(m, dx, dy, retraso, dura, curva, aparece)` | mueve en px; con `aparece` se enciende al salir (una copia que sale de su original sin dibujarse dos veces) | `useTramo` + `translate` |
| `Mover(m, destino, …)` | `Transform` con curva | — |
| `TransformarPorPartes(origen, destino, retraso, dura, separar)` | de un `Texto` a otro: las partes con la misma clave viajan; las demás cambian como un dígito de visor (la vieja sube y se apaga, la nueva sube y se enciende, casi sin superponerse); las de `separar`, que se cruzarían con otra palabra, cambian en su lugar | `TransformMatchingTex`, sin letras encimadas |
| `Latido(m, retraso, dura=0,4, escala=1,06)` | un solo latido 1 → 1,06 → 1 | el `Indicate` del guion, sin el #FFFF00 ni el 1,2 de Manim |
| `CrecerDesdeIzquierda(rect, ancho, alto, radio, grosor, …)` | el rectángulo crece a lo ancho desde su borde izquierdo con el radio y el borde fijos | `GrowFromEdge` sin aplastar las esquinas |
| `Foco(m, retraso, dura=0,3)` | lo ya explicado baja a hueso al 60 % y su ámbar al 60 % (los tokens) | `<Foco>` |

Curvas: `CURVA["suave"]` (inOut cúbica), `"sale"` (out cúbica), `"entra"`, `"lineal"` y `"fundido"` (inOut
seno), las mismas funciones que `Easing` de Remotion. `Write` no se usa para texto.

Formas en px: `rect_borde(cx, cy, ancho, alto, radio, grosor, color, relleno=…, opacidad_relleno=…)`
(borde hacia adentro, como `boxSizing: border-box`; los bloques: `relleno=PANTALLA, opacidad_relleno=1`),
`linea`, `corchete` (⌴ bajo una palabra, para su rótulo), `subrayado` (ámbar de 5 px; `trazos=(largo,
hueco)` para el de trazos), `tachado` (rojo de 7 px con el filete de tinta de 3 px a cada lado, como
Remotion; el texto tachado en hueso al 55 %) y `linea_subrayado(y, tam)` / `linea_tachado(y, tam)` (las
mismas fórmulas que Remotion).

### 11.6 Marca de agua y chip

Los pone `DiapoCharla` según `tokens.json → persistentes` y `deck.json → piso`, con los PNG de
`diseno/assets/` en su píxel exacto y encima de todo (z 1000). `imagen_en` corre las esquinas 0,001 px:
la cámara de Manim trunca las esquinas a píxeles y redimensiona, y sin eso el PNG podía salir 1 px más chico
y borroso.

- Quietos: el recorte opaco (`<pieza>_tinta.png`), idéntico al píxel a Remotion.
- Cuando aparecen (D09.1, el chip «1»): el PNG transparente con fundido de 0,3 s (y escala 0,9 → 1 alrededor
  del centro del chip, out cúbica); al terminar, el recorte opaco toma su lugar. Cuando se van: el recorte
  opaco se funde. Como en Remotion, el cambio va desde el cuadro 0 del paso.
- El dígito que rueda (el chip que cambia de piso) está solo en Remotion: si una de Manim lo pidiera, falla.
- Nada se dibuja en sus zonas: el auditor de Manim mide los 20 px (0,15 u) alrededor de la marca y
  `armar/auditar_cuadros.py`, las dos zonas.

### 11.7 Entrada continua

- **Desde una de Remotion** (D07 desde D06, D09 desde D08): `self.anterior()`, al comienzo del paso 1, pone
  `render/cuadros/<anterior>_<n>.png` a pantalla completa, debajo de todo y sin remuestrear (el cuadro 0 de
  D07 es idéntico al bit a D06.3); la marca y el chip quedan encima en su píxel (es el «hueco» de
  `<Anterior>`). `self.salir_anterior(retraso, dura=0,4)` lo funde a tinta como `<Anterior sale>`; tiene que
  irse antes del respiro del paso 1. `render_diapo.py` saca ese PNG si falta o está viejo, con la misma regla
  que `render.mjs`.
- **Desde una de Manim** (D10 desde D09): se reconstruye el estado con el mismo código. El módulo de D09
  expone una función `estado_final()` que arma los objetos de su último cuadro (los mismos `Texto`, cajas y
  opacidades de Foco, sin animar), y D10 la usa:

  ```python
  from d09_piso_uno_frase import estado_final as estado_d09

  class D10ResolverVendedor(DiapoCharla):
      ID = "D10"

      def estado_anterior(self):        # la llama self.anterior()
          return estado_d09()
  ```

  La marca y el chip no van ahí (los pone la base). `render_diapo.py` compara el cuadro 0 con `D09_3.png`:
  tiene que dar IDÉNTICA.
- **Hacia una de Remotion** (D08 desde D07, D11 desde D10): `render_diapo.py` deja los cortes sin pérdida en
  `render/cuadros/<ID>_<k>.png` (k = 0: el primer cuadro; 1…n: el último de cada paso). `render.mjs` no sabe
  si un PNG de Manim está viejo: **si cambia una de Manim, hay que volver a renderizar la de Remotion que la
  sigue**. D07.3 deja: «60 a 75 palabras ≈ 3 frases» a 72 px centrado en y 250 («3 frases» en ámbar); los
  tres bloques de 560×200 (borde ámbar de 5 px hacia adentro, radio 24, relleno opaco `pantalla`) centrados
  en x 354, 960 y 1566 (46 px entre uno y otro), y 560, con «20 a 25 palabras» a 60 px en hueso centrado en
  cada uno; «10 s» a 60 px en gris centrado en y 720 (D08.1 los sigue llevando en gris). Esas medidas están
  dos veces, `BLOQUE` y `Y_DIEZ` en `d07_cuanto_cabe.py` y la constante `D07` de `D08TresPisos.tsx`: si cambia
  una, cambia la otra. Como Cairo y Chrome no dibujan igual las esquinas (11.3), D08 aparece sus bloques
  sobre el PNG con un cruce corto en vez de contar con un redibujo idéntico (medido: el texto redibujado
  queda a 0,1 px del de Manim y los bordes caen en los mismos píxeles).

### 11.8 Renderizar y mirar

```bash
.venv/Scripts/python.exe manim/render_diapo.py D07              # auditor, render, pasos, cortes y fronteras
.venv/Scripts/python.exe armar/auditar_cuadros.py D07           # el auditor de los videos
.venv/Scripts/python.exe armar/hoja_contactos.py D07 --medios   # la hoja para mirar (y mirar cada PNG)
```

`render_diapo.py <ID…>`: (1) busca `manim/escenas/<id>_*.py` con la clase `<ID><Nombre>`; (2) si entra
continua desde una de Remotion, se asegura de que el PNG de la anterior exista y esté al día; (3) corre el
auditor en seco y, si no da APROBADO, no renderiza; (4) renderiza con secciones y pedazos `libx264rgb` sin
pérdida en `render/manim/`; (5) comprueba los cuadros de cada sección contra deck.json y arma cada paso (su
sección más el primer cuadro de la siguiente) con la receta de frontera (`armar/codificar_paso.py`); (6)
deja los cortes sin pérdida en `render/cuadros/`; (7) compara la frontera con la anterior (PNG contra PNG) y
la de cada paso con el siguiente (videos decodificados). Opciones: `--sin-auditor` (para probar, nunca para
entregar), `--sin-refrescar`, `--refrescar-anterior`. D07 (289 cuadros) tarda unos 33 s: auditor 12 s, Manim
14 s, armado 6 s (la primera vez, más, por XeLaTeX).

```
D07: manim/escenas/d07_cuanto_cabe.py :: D07CuantoCabe
  -> APROBADO: 0 errores, 0 avisos. Reporte: auditoria\reporte_D07CuantoCabe.md
  D07_1.mp4: 109 cuadros
  D07_2.mp4: 91 cuadros
  D07_3.mp4: 91 cuadros
  frontera con D06.3: IDÉNTICA
  frontera D07.1 → D07.2: IDÉNTICOS
  frontera D07.2 → D07.3: IDÉNTICOS
```

### 11.9 El auditor ve los textos TeX

`manim/auditor/auditar.py` solo reconocía `Text` (Pango): un MathTex no se juzgaba (trampa 39 de
`docs/referencia_manim.md`). Desde el 23-oct-2026 todo objeto con `es_texto` (lo pone `Texto`) se juzga
como texto: tamaño (`tamano_efectivo` = px ÷ 1,873), contraste contra lo que tiene detrás, solapes, figuras
que lo tapan, líneas que lo cruzan y distancia a la marca de agua; sus partes y glifos no cuentan como
figuras opacas. Probado con un caso roto a propósito (dos textos encimados y uno pegado a la marca):
RECHAZADO, con los dos errores.

### 11.10 Trampas de Manim que ya resuelve la base

| Problema | Arreglo |
|---|---|
| `Scene.remove(grupo)` no saca la familia: al transformar por partes quedaban las partes viejas encima de las nuevas, como fantasmas | `TransformarPorPartes` las saca una por una |
| Animar las partes de un `Texto` lo deja desarmado en la escena (y el auditor no lo veía como texto) | `EntrarPartes` vuelve a poner el `Texto` entero al final |
| MathTex 0.19 corta las partes compilando cada una aparte: una parte larga se partía en dos renglones y TeX le agregaba un guion (un glifo de más) | cada parte va en una caja horizontal (`renglon`) y se cuentan los glifos |
| Una espera quieta da `int(30·T)` cuadros y un `play` `ceil(30·T)` | `(n ± 0,5)/30` según el caso |
| La cámara trunca las esquinas de las imágenes y las redimensiona | `imagen_en` (cuadro 0 de D07 = D06.3 al bit) |
| `ImageMobject.set_opacity` pone el alfa entero en un solo valor (se pierde la transparencia del PNG) | fundidos que multiplican el alfa |
| `TransformMatchingTex` encima la palabra vieja y la nueva a mitad de camino («palabras =g30d×») | el cambio como dígito de visor (`TransformarPorPartes`) |
| `configurar_horizontal()` deja 1 u = 135,002 px en x | `charla.configurar()` con 1920/135 |

### 11.11 Decisiones de D07 (la piloto)

- Ecuaciones a 105 px (el `tamano` 56 del guion) y alineadas a la izquierda en el mismo x: la segunda línea
  entra igual a la primera, en su columna, y solo cambia lo que se reemplaza («palabras =» queda quieto). El x
  centra el conjunto: la ecuación (1425 px) y el rótulo de «ritmo» (800 px), que centrado bajo la palabra se
  salía del cuadro; queda de x 115 a 1805.
- «Una línea corta gris» es un **corchete** (⌴) del ancho de la palabra: el palito vertical de 20 px que
  pedía el guion se veía como una raya suelta. Lo llevan los dos rótulos, 24 px debajo del corchete: en
  y 401 y 676 (el guion decía 400 y 660; el paréntesis baja más que «ritmo»).
- Revisión (última fila): los dos rótulos van a 60 px (lectura), no a 49: definen el ritmo, que es lo que se
  explica. Los corchetes van en el trazo normal (5 px) y no en el fino: a 3 px, en gris y con antialias,
  desaparecían en una sala con luz; con las coordenadas en el medio del píxel son 5 filas y 5 columnas de
  gris pleno (medido en `D07_1.png`). En `--sala` se leen los dos.
- Revisión (dirección de arte): la segunda línea ya no es una copia que baja de la primera. Con la curva suave
  la copia estaba casi entera a 8 px de la original entre los 2,2 y los 2,4 s («palabras» doble, el «=» como
  un «≡»); con salida cúbica dejaba de encimarse con la original pero atravesaba el rótulo de «ritmo», que a
  60 px queda en el camino. Entra con Entrar desde abajo en su lugar (0,5 s, la otra opción de la revisión) y
  después cambia en tres tiempos, sin cruces: «segundos» y «ritmo» suben y se apagan (0,2 s), el «×» se
  acomoda en el hueco que dejan (0,3 s, curva suave) y recién entonces suben «30» y «(2 a 2,5)» (0,3 s), con
  su corchete y su rótulo. Con `TransformarPorPartes` lo viejo y lo nuevo se cruzaban y el «×» viajaba por
  encima de todo. El cambio usa `_Cambio` de la base con `solape=1.0` (cada palabra en su propio tramo).
- D07.2: «30 × (2 a 2,5)» se resuelve en «60 a 75» (0,6 s; su rótulo se va con él); se va la primera línea y
  el resultado se reordena centrado (0,7 s; «palabras» cambia en su lugar para no cruzarse con «60 a 75»); el
  recuadro (5 px, el trazo normal; el guion decía 6, que no es uno de los tres trazos; radio 28) se dibuja en
  0,6 s y late una vez mientras entra la regla.
- D07.3: «60 a 75 palabras ≈ 3 frases» no entra de la nada: el resultado de D07.2 sube y se transforma en
  ella («60 a 75» y «palabras» viajan; «30 s» y «≈» cambian en su lugar), así se ve que es la misma cuenta;
  «3 frases» en ámbar, lo único en ámbar además de los bordes. Los bloques crecen desde su borde izquierdo
  (0,5 s, out cúbica, desfase 0,2 s). Revisión (dirección de arte): bloques de 560 px separados 46 px (con 540,
  «20 a 25 palabras» quedaba a 40 px de los costados y a 68 de arriba y abajo) y los «10 s» en gris (en
  ámbar competían con «3 frases» y en D08.1 cambiaban a gris); D08.1 los redibuja igual (11.7).
- Las duraciones son las de deck.json (3,6, 3,0 y 3,0 s) y todo termina antes del respiro (la última
  animación de cada paso termina a los 3,27, 2,40 y 2,20 s).

## 12. Decisiones de diseño del sistema (y por qué)

- **Un solo acero, un solo ámbar.** Puertas, cabina y paneles comparten `PanelAcero` (degradé de acero2 a
  aceroclaro hacia la junta, una banda de brillo suave al 45 % del ancho, el canto claro y el filete de
  sombra junto a la luz; las hojas bajas, planas): las primeras versiones con tres líneas por hoja parecían
  una persiana, y la de una costura fina al 30 % y una banda al 62 %, un ropero. La única luz es ámbar y
  está en la junta, con el núcleo siempre pleno.
- **7 segmentos de verdad, inclinados 6°**, con el «8» fantasma al 8 % y un brillo leve en lo encendido:
  se leen como un visor de ascensor y no como una tipografía; «Pb» en vez de «PB».
- **Elementos fijos en una capa propia**: sin ella, Chrome rasterizaba las esquinas del chip ±1 distinto
  según el contenido de cada diapositiva; con ella, el chip y la marca son idénticos al píxel en todas y en
  los PNG de Manim.
- **Cada cuadro desde cero** (`Lienzo` con `key` = cuadro): Chrome reutiliza lo ya rasterizado en cada
  pestaña, y el mismo cuadro salía con bordes distintos (hasta 58 niveles) según los cuadros anteriores.
- **Texto que no se sale**: medir con la fuente real, partir, achicar hasta el mínimo y fallar con nombre
  y apellido; nunca un desborde silencioso.
- **Entrada continua con huecos** en vez de redibujar todo: el cuadro anterior se usa tal cual (idéntico
  aunque venga de Manim) y solo lo que sigue en pantalla lo redibuja el sistema.
- **Cabina iluminada al abrirse** (ámbar al 85 % arriba, 35 % al 40 % del alto y 8 % abajo, con la tira de
  luz en hueso al 90 %): la versión plana se veía marrón, y la de 34 % → 2 %, una caja color café; ahora el
  «?» sale de un lugar con luz.
- **Globo del cronómetro a la derecha del hueco**: a la izquierda (como en el mapa de D08) no entra con la
  marca de agua arriba; sube 16 + 30 px para dejar más de 70 px de aire sobre «Pedido». En los dos, pegado
  a la cabina y encima de la pared, con la cola corta: una cuña de 120 px que cruzaba la pared parecía un
  puntero o un megáfono.
- **Cola de la firma** relativa a la N: en la hoja se acorta; en D20.3 sale de fuera de cuadro.

## 13. Hallazgos de sistema de la revisión visual (23-oct-2026)

Tres jueces (dirección de arte, la última fila y claridad) miraron los seis pilotos. Lo de nivel sistema
quedó así (tokens versión 2); los pilotos se volvieron a renderizar con esto (auditor APROBADO, fronteras
IDÉNTICAS, `probar_sistema.mjs` «Todo bien», `probar_auditor.py --herramientas` 38 de 38).

| Hallazgo | Qué se hizo |
|---|---|
| El ámbar a baja opacidad sale marrón (junta, cabina, bloques) | Junta con el núcleo siempre pleno (el nivel solo cambia el brillo); cabina abierta 85 / 35 / 8 % con la tira en hueso (`OPACIDAD.luz_cabina`); bloques y tramos con relleno opaco `pantalla` (D07 y D08 a la vez); regla de la luz (sección 7) |
| El «?» entra al doble de tamaño | `useRebote` 0,4 → 1 (pico de 1,13 en el cuarto cuadro: el mismo resorte), opacidad min(1, 4·p), origen en la punta de la cola. Medido cuadro por cuadro: en D08.2 (2,70-2,95 s) el globo va de x 300 a 624 e y 234-386; en D14.1, x 624-904 e y 134-275: siempre dentro de la zona segura |
| El acero no se lee como dos hojas, y se pierde en la sala | `PanelAcero` sin la segunda costura, banda a la mitad y al 45 %, de acero2 a aceroclaro (#4A586F, 2,75:1), canto en hueso al 50 % de 4 px; hojas bajas planas; marco al 50 %; junta de 6 px |
| Demasiado ámbar por cuadro | Regla «como mucho dos cosas en ámbar»; Pastilla y BurbujaRespuesta con borde en hueso al 40 % por defecto (D06.1 pasa `color={COLOR.ambar}`: ahí es la respuesta del paso) |
| El teléfono, lo más brillante del cuadro | Contorno de 4 px en hueso al 40 % |
| Palomitas chicas, finas y sin columna | 56 px con el grosor del asta del rótulo (10,8 px), en una columna (`columnaPalomitas`; AscensorConCuenta de D14 recibe `xPalomita`); regla «la marca toma el asta del texto» |
| Cola del globo larga y globo pegado a «Pedido» | Globo a 30 px de la cabina, encima de la pared, cola de 50 px o menos; en el cronómetro sube 30 px más (71 px de aire sobre «Pedido») |
| Dos grises de matiz distinto | Lo pendiente en `gris`; ya no existe `opacidad.pendiente` |
| Demasiados tamaños y grosores | Siete tamaños (104 en vez de 96; 84, 68 y 52 fusionados en 88, 72 y 49), héroe con su motivo; tres trazos 3 / 5 / 7 con las excepciones escritas |
| El hueco del ascensor se pierde | Losas al 50 % y paredes al 45 %, de 5 px; `escalaTrazos` y `opacidadHueco` para el ascensor chico |
| El rojo, el texto más débil | #FF7A7A (7,85:1), con los contrastes en tokens.json y en `latex/charla.sty` |
| La hoja `--proyector` es optimista | `hoja_contactos.py --sala` (7:1, σ = 1 px, color al 60 %), probada en `probar_auditor.py --herramientas`; lo que va en la guía para presentar, en la sección 9 |
| El tachado no se separa por luz | Tachado de 7 px con filete de tinta de 3 px (Remotion y Manim); texto tachado en hueso al 55 % |
| Lo de Foco, ilegible desde el fondo | `foco_hueso` y `foco_ambar` 0,6 |
| Nada que leer abajo | `reticula.franja_inferior` (y 900) y la regla |
| Números en ámbar que parecen pisos | Regla «1-2-3 en ámbar: solo los pisos» |
| Mapa y cronómetro con rótulos en lugares distintos | Regla «la misma: `centroTramo`» |

También: el auditor de cuadros toma como reloj grande solo el bloque de sus dígitos (`reloj_union_px`):
con la columna de palomitas, la de «Prueba» (a 96 px de un «30») le corría el centro y daba un falso error.

**Decisiones entre jueces:**

- Junta: arte pedía el núcleo pleno con la opacidad solo en el brillo; última fila, `junta_reposo` 0,4 → 0,7.
  Con el núcleo pleno la junta en reposo ya da 11,3:1 contra la tinta y 4,1:1 contra el acero claro, así
  que `junta_reposo` sigue en 0,4 como nivel del brillo: reposo (0,4) y «listo para subir» (0,7) se siguen
  distinguiendo.
- Paredes y losas: arte las ponía en el trazo fino (3); última fila, en 6 px al 45-50 %. Van en el trazo
  normal (5) con las opacidades de última fila (4,3 y 5,0:1): se leen desde el fondo y respetan los tres
  trazos.
- Tachado: última fila pedía 8 px; va en el trazo fuerte (7, como las flechas) con el filete de 3 px, que es
  lo que lo separa por luz.
- Contorno del teléfono: los 4 px que pidió arte (excepción escrita a los tres trazos), al 40 %.
- Texto tachado al 55 % (lo que pidió última fila) y no al 60 % del Foco nuevo: separa más el rojo de las
  letras (1,33:1 contra 1,14:1).
- El «?» del globo pasa de 96 a 104 px: 96 ya no está en la escala y es el motivo de la charla.
- Números de las listas: arte pedía aro en hueso al 40 % y número en hueso; claridad, número en hueso en un
  círculo de acero2. Las dos cumplen la regla; para D14.2 se sugiere juntarlas: círculo de acero2 con aro en
  hueso al 40 % y el número en hueso.

**Lo que queda en cada diapositiva** (la regla ya está en el sistema; el cambio es del archivo de la
diapositiva, y estos hallazgos lo piden):

- **D06** (hecho): el teléfono de D06.1 bajado hasta salir por abajo (cy 700, con su excepción en
  `armar/auditoria_reglas.json`) y, con el hallazgo de la última fila, la burbuja de voz de 0,93 a 1,3
  mientras se encoge («0:30» a 78 px, barras de 7,8 px; a 1,3 desde el comienzo no entra: con 20 barras y
  «4:12» mediría 620 px en una pantalla de 484). En D06.2 la respuesta pasa a `<Foco paso={2}>` cuando entra
  la idea (con el 60 % del sistema: la revisión pedía hueso al 55 y ámbar al 45, y la regla es no apagar
  más). Los paneles no se abren a los 1,0 s: claridad mostró que la pantalla ya se le adelanta al orador, y
  siguen abriéndose a los 1,3 s, lo más tarde que deja el respiro; lo que se acortó es la barra cerrada (el
  segundo renglón entra 0,3 s después del primero: se ve cerrada 0,5 s y no 0,7). En D06.3, la cruz y la
  palomita de 44 px con `grosorAsta(60)` delante de «reescribir» y «funcionó» (las mismas de D20.2, que
  redibuja estos globos) y «¿Hay para tipo C?» en un `Globo` chico como el de D02.2, con «tipo C» en ámbar,
  borde de apoyo en el trazo normal y sin ícono, en vez de la pastilla con la mano (§6). **Pendiente del
  dueño del guion (deck.json):** pasar «Esta es la idea más importante de hoy, y se la voy a repetir al
  final con las mismas palabras» al final de las notas de D06.1, antes del clic, y empezar las de D06.2 con
  «[CLIC: decir la idea mientras se abren los paneles]», como D20.1; y poner al día el `visual` de D06.1 y
  D06.3 (teléfono en y 700, burbuja a 1,3, el globo del tipo C sin la mano).
- **D07 y D08, juntos** (hecho): los «10 s» de D07.3 en gris (y D08.1, que los redibuja, empezando en gris); el
  recuadro de D07.2 en el trazo normal (5). Con los hallazgos de la revisión sobre D07, además: bloques de 560 px
  (D08.1 los redibuja en el mismo píxel), rótulos de la cuenta a 60 px con corchetes de 5 px y la segunda línea
  de D07.1 sin doble exposición ni cruces (11.11).
- **D08** (hecho): los rótulos con `g.centroTramo`, como el cronómetro (y 815, 615 y 415; los «10 s» siguen
  en el centro de la banda, que es lo que miden); «ganas de preguntar» debajo del globo, calculado con
  `cajaGloboCabina` y a 50 px de la pared. Con los hallazgos de la revisión sobre D08, además: los bloques entran
  al hueco de a uno y sin cruzarse (cada uno va primero a la altura de su tramo y después entra de costado),
  el hueco se arma en dos tiempos (paredes y losas de 1,5 a 2,0 s; visor, cable y cabina de 2,1 a 2,8 s) y
  después entran los rótulos, en hueso pleno (regla «lo pendiente, solo en un viaje» de la sección 7); los
  «10 s» a 60 px en gris de punta a punta.
- **D14** (hecho; D19.3 y D19.5 lo toman de `D14MiPitch.tsx`): el ascensor chico de D14.2 va sin losas
  (`AscensorConCuenta opacidadLosas`: caían en y 425, 563 y 701, a la altura de las frases en y 430, 560 y
  690) y conserva paredes, techo, suelo, visor y la cabina abierta arriba, con `escalaTrazos` siguiendo la
  escala (5 px medidos); se probó dejar solo la cabina (`opacidadHueco`) y, sola arriba a la izquierda, se
  leía como una caja con luz suelta. Los números de las frases, en hueso en un círculo de acero2 con aro en
  hueso al 40 % (`NumeroCirculo`). Con el hallazgo propio de D14 (las tres luces bajo el «0» se leían «0…»),
  las luces van en una cápsula de vidrio de 156×44 con aro en hueso al 40 % de 3 px, como la cabina
  (`LucesEnCapsula`; con el acero2 de 2 px que se propuso desaparecía en `--sala`). **Pendiente del
  sistema:** `AscensorCrono` y `<Reloj luces>` de comun/ todavía dibujan las luces sin cápsula; D19.2, D19.4,
  A8 y A9 la llevan si usan `AscensorConCuenta` de D14 (o cuando la cápsula pase a `CuentaPrevia`).
- **D01** (hecho): nada que leer por debajo de y 900. Toda la columna sube 71 px con las distancias del
  guion (la «C» de «Cómo» queda en y 225, el borde de arriba del marco) y la tinta del pie termina en y 897;
  el lugar va a 60 px en gris (a 49 era lo más débil del cuadro en `--sala`). Mientras la organización no
  confirme el nombre del espacio, el pie dice solo «Univalle»: el nombre va en `ESPACIO_EMPRENDIMIENTO`
  (`D01Portada.tsx`) o en deck.json en lugar del marcador; si no entra en un renglón, va en dos y la
  columna sube uno más.
- **D20.2**: nada que haya que leer por debajo de y 900 (los rótulos). Con la regla de Foco de la sección 7
  («lo que vuelve como recuerdo», de la revisión sobre D06.2): los globos del recuerdo, adentro de un `<Foco>`
  si quedan en el mismo paso que la tarea.
- **D05** (cuando exista): el teléfono, como en D06; la burbuja de voz de 20 barras y «4:12» no entra a
  escala 1 en la pantalla (sección 6, Teléfono).
