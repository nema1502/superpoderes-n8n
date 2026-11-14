# Marca de Tinkazo, para los guiños de la charla

Copiados el 13 de noviembre de 2026 de la carpeta `public/marca/` del repositorio de Tinkazo (rama principal), sin cambios. La guía completa es `docs/marca.md` de ese repositorio.

| Archivo | Qué es | Sobre qué fondo |
|---|---|---|
| `llama-oscuro.svg` / `.png` | la llama sola, magenta `#ff5cb3` | oscuro (el de la charla) |
| `llama.svg` / `.png` | la llama sola, magenta `#e93d9c` | claro |
| `logo-horizontal-oscuro.svg` / `.png` | llama y TINKAZO en una línea, `Tinka` en `#f6efe2` y `zo` en magenta | oscuro |
| `logo-horizontal.svg` / `.png` | lo mismo, `Tinka` en tinta `#191919` | claro |
| `logo-apilado-oscuro.svg` / `.png` | llama arriba y TINKAZO abajo | oscuro |
| `logo-apilado.svg` / `.png` | lo mismo | claro |

En las diapositivas van las versiones `-oscuro`: el fondo de la charla es tinta. En Remotion se usan con `staticFile("logos/tinkazo/llama-oscuro.svg")` (la carpeta pública de los bundles es `diseno/`). En Manim, con `SVGMobject` o `ImageMobject` desde esta carpeta.

## Lo que pide la marca

- Se escribe **Tinkazo**, junto y con mayúscula inicial. En el logo, `Tinka` y `zo` llevan colores distintos: es la única vez que el nombre se parte.
- Se dice **sorteo**, siempre. Entrar a un sorteo es gratis, siempre.
- La idea en una línea: **Sorteos que cualquiera puede comprobar.**
- La llama es una silueta pixelada en magenta, sin cara, sin sombrero ni poncho. Si lleva sombra, es dura (sin desenfoque), en tinta, y la llama va rotada unos tres grados.
- El estilo es plano: colores llenos, bordes gruesos, sombras duras. Nada de degradés suaves ni sombras difuminadas, y nada de dados, cartas ni fichas.
- Tema oscuro de la marca: fondo `#171126`, tarjeta `#221a33`, texto `#f6efe2`, magenta `#ff5cb3`, naranja `#ff8b3d`, turquesa `#17c3b2`, amarillo `#ffd24d`, morado `#9b7bff`. Sobre un acento va texto oscuro, no blanco.

## En esta charla

La marca de Tinkazo es un guiño y el sorteo del final, no el sistema visual: las diapositivas siguen con los tokens de `diseno/tokens.json`. Donde aparece Tinkazo (la diapositiva del sorteo, el cierre), el logo va tal cual, sin recolorear ni deformar, y el magenta queda solo en el logo y en la llama.
