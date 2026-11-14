"""Confirma con números qué fuente quedó en un cuadro renderizado.

Mirar el cuadro no alcanza: si Segoe UI faltara, Chrome (Remotion) o Pango
(Manim) caerían en silencio a otra sans, parecida a primera vista. Acá se
recorta una línea de texto del PNG y se la compara con el mismo texto dibujado
por Pillow con cada fuente candidata, al mismo tamaño en px, de dos maneras:

- **forma**: se superponen las dos manchas de tinta (escaladas a la misma
  caja) y se mide cuánto coinciden (IoU, de 0 a 1). Es lo que decide: la "g",
  la "t" o la "a" de Segoe UI no se parecen a las de Arial. Se compara PALABRA
  POR PALABRA (promedio pesado por ancho): Pango, el motor de texto de Manim,
  espacia algunas letras distinto que Chrome y Pillow (deja un hueco entre la T
  y la R de "INFRAESTRUCTURA"), y en la línea entera ese corrimiento se acumula
  y el IoU deja de medir la forma. Si no se pueden separar las palabras, se
  compara la línea entera y se avisa.
- **ancho**: cuánto mide la línea. Solo informa: Arial Bold y Segoe UI Bold
  miden casi lo mismo en algunas frases (medido: 0,9 % en el título de prueba).

Gana la de forma más parecida; si no es Segoe UI Bold, sale con código 1.

Además cuenta los píxeles con franja de color en la línea (saturación > 60):
en un texto neutro (hueso sobre tinta) tiene que dar casi 0. Si da miles, Chrome
dibujó con ClearType (antialias subpíxel): falta el `Lienzo` de Remotion.

Uso (texto claro sobre fondo oscuro):
    python armar/verificar_fuente.py <cuadro.png> "<texto>" <tamaño_px> <y_arriba> <y_abajo>
Ejemplo (el still de la prueba de Remotion):
    .venv/Scripts/python.exe armar/verificar_fuente.py remotion/out/prueba.png "Cómo hacer tu elevator pitch" 120 400 560
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FUENTES = Path("C:/Windows/Fonts")
CANDIDATAS = {
    "Segoe UI Bold": "segoeuib.ttf",
    "Segoe UI Semibold": "seguisb.ttf",
    "Arial Bold": "arialbd.ttf",
    "Calibri Bold": "calibrib.ttf",
    "Verdana Bold": "verdanab.ttf",
    "Tahoma Bold": "tahomabd.ttf",
}
UMBRAL = 110  # luminancia que separa letra de fondo


def recorte_tinta(gris):
    """La caja mínima que contiene toda la tinta."""
    filas = np.where((gris > UMBRAL).any(axis=1))[0]
    cols = np.where((gris > UMBRAL).any(axis=0))[0]
    if not len(filas) or not len(cols):
        raise SystemExit("No hay texto claro en esa franja: revisar y_arriba / y_abajo.")
    return gris[filas[0]:filas[-1] + 1, cols[0]:cols[-1] + 1]


def dibujar(archivo, texto, tam):
    fuente = ImageFont.truetype(str(FUENTES / archivo), tam)
    lienzo = Image.new("L", (int(tam * len(texto)) + 200, int(tam * 2)), 0)
    ImageDraw.Draw(lienzo).text((100, tam // 3), texto, font=fuente, fill=255)
    return recorte_tinta(np.asarray(lienzo))


def iou(a, b):
    """Coincidencia de dos manchas de tinta, con `b` llevada a la caja de `a`."""
    b = np.asarray(Image.fromarray(b).resize((a.shape[1], a.shape[0]), Image.BILINEAR))
    ma, mb = a > UMBRAL, b > UMBRAL
    return float((ma & mb).sum() / max(1, (ma | mb).sum()))


def palabras(linea, n):
    """Corta la línea en sus n palabras por los n-1 huecos sin tinta más anchos.
    Un umbral fijo no sirve: Pango deja huecos de 12-16 px DENTRO de algunas
    palabras en mayúsculas, cerca de los 20-22 px de un espacio (medido)."""
    cols = np.where((linea > UMBRAL).any(axis=0))[0]
    huecos = np.diff(cols)
    if n < 2 or len(huecos) < n - 1:
        return [linea]
    cortes = np.sort(np.argsort(huecos)[::-1][:n - 1])
    if huecos[cortes].min() <= 2:
        return [linea]
    inicios = np.r_[cols[0], cols[cortes + 1]]
    fines = np.r_[cols[cortes], cols[-1]]
    return [recorte_tinta(linea[:, a:b + 1]) for a, b in zip(inicios, fines)]


def comparar_forma(linea, cand, tam, n):
    """IoU palabra por palabra (pesado por ancho); si no se pueden separar las
    n palabras en los dos, el de la línea entera."""
    pa, pb = palabras(linea, n), palabras(cand, n)
    if len(pa) == len(pb) == n:
        anchos = [p.shape[1] for p in pa]
        return sum(iou(x, y) * w for x, y, w in zip(pa, pb, anchos)) / sum(anchos), True
    return iou(linea, cand), False


def main():
    if len(sys.argv) != 6:
        print(__doc__)
        sys.exit(2)
    png, texto, tam, y0, y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    franja = np.asarray(Image.open(png).convert("RGB"), dtype=np.int16)[y0:y1]
    saturados = int(((franja.max(axis=2) - franja.min(axis=2)) > 60).sum())
    linea = recorte_tinta(np.asarray(Image.open(png).convert("L"))[y0:y1])
    print(f"Línea medida en el cuadro: {linea.shape[1]} x {linea.shape[0]} px")
    print(f"Píxeles con franja de color (ClearType si el texto es neutro): {saturados}")
    resultados = []
    por_palabra = True
    n = len(texto.split())
    for nombre, archivo in CANDIDATAS.items():
        if not (FUENTES / archivo).exists():
            continue
        cand = dibujar(archivo, texto, tam)
        dif = (cand.shape[1] - linea.shape[1]) / linea.shape[1] * 100
        f, ok = comparar_forma(linea, cand, tam, n)
        por_palabra = por_palabra and ok
        resultados.append((f, nombre, cand.shape[1], dif))
    print(f"Forma comparada {'palabra por palabra' if por_palabra else 'en la línea entera (no se pudieron separar las palabras en todas)'}")
    print(f"  {'fuente':<18} {'forma (IoU)':>11}  {'ancho':>8}")
    for forma, nombre, ancho, dif in sorted(resultados, reverse=True):
        print(f"  {nombre:<18} {forma:>11.3f}  {ancho:>5} px ({dif:+.1f} %)")
    forma, ganadora, _, dif = max(resultados)
    print(f"La más parecida: {ganadora}")
    sys.exit(0 if ganadora == "Segoe UI Bold" and abs(dif) < 2.0 else 1)


if __name__ == "__main__":
    main()
