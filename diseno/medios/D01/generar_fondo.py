# El fondo de circuito de la charla: las pistas de la portada (D01), muy tenues, para que todas las
# diapositivas parezcan el mismo lugar. Sale un PNG opaco de 1920 x 1080 sobre tinta, el mismo para
# Remotion (<Img> en 0, 0, debajo de todo) y para Manim (imagen_en en 0, 0, debajo de todo), así las
# dos se ven idénticas.
#
# Las pistas son como las de D01: tramos rectos y a 45 grados, trazo de 3 px, un punto de 10 px en la
# punta de adentro, en azul. Entran desde los bordes y se apagan antes de salir de la zona segura
# (x 67 a 1853, y 38 a 1042): fuera de ella el fondo queda en tinta lisa, así el auditor de cuadros
# no ve nada en los márgenes ni en las esquinas. Evitan la marca de agua (arriba a la izquierda).
#
# Correr con el Python de la charla: PYTHONUTF8=1 python diseno/medios/D01/generar_fondo.py
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
ANCHO, ALTO = 1920, 1080
SS = 4  # sobremuestreo para el antialias
TINTA = (0x07, 0x0A, 0x0F)
AZUL = (0x4D, 0xA3, 0xFF)
ALFA = 0.22  # opacidad de las pistas (en D01 quedan al 35 %: acá son el fondo)
ZONA = (67, 38, 1853, 1042)  # zona segura
RAMPA = 30  # px hacia adentro de la zona segura en los que la pista pasa de apagada a su opacidad
TRAZO = 3
PUNTO = 10

# Cada pista: la lista de puntos (el primero fuera del cuadro o en el borde, el último es la punta con
# el punto). Tramos rectos y a 45 grados.
PISTAS = [
    # Borde derecho
    [(1990, 160), (1820, 160), (1760, 100), (1560, 100)],
    [(1990, 300), (1865, 300), (1825, 340), (1825, 480)],
    [(1990, 600), (1865, 600), (1825, 640), (1825, 760)],
    [(1990, 870), (1880, 870), (1820, 930), (1650, 930)],
    [(1990, 1000), (1720, 1000)],
    # Borde izquierdo (por debajo de la marca de agua)
    [(-70, 250), (55, 250), (95, 290), (95, 440)],
    [(-70, 560), (55, 560), (95, 600), (95, 720)],
    [(-70, 860), (40, 860), (100, 920), (300, 920)],
    [(-70, 1000), (250, 1000)],
    # Borde de arriba (a la derecha de la marca de agua)
    [(980, -70), (980, 40), (1020, 80), (1220, 80)],
    [(560, -70), (560, 45), (600, 85), (720, 85)],
]


def mascara() -> np.ndarray:
    """Las pistas en blanco sobre negro, a tamaño final, con antialias."""
    img = Image.new("L", (ANCHO * SS, ALTO * SS), 0)
    d = ImageDraw.Draw(img)
    for pts in PISTAS:
        p = [(x * SS, y * SS) for x, y in pts]
        d.line(p, fill=255, width=TRAZO * SS, joint="curve")
        x, y = p[-1]
        r = PUNTO / 2 * SS
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    img = img.resize((ANCHO, ALTO), Image.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def rampa() -> np.ndarray:
    """De 0 en el borde de la zona segura a 1 a RAMPA px hacia adentro (0 fuera)."""
    xs = np.arange(ANCHO) + 0.5
    ys = np.arange(ALTO) + 0.5
    x0, y0, x1, y1 = ZONA
    dx = np.minimum(xs - x0, x1 - xs)
    dy = np.minimum(ys - y0, y1 - ys)
    d = np.minimum(dx[None, :], dy[:, None])
    return np.clip(d / RAMPA, 0.0, 1.0)


def main():
    a = mascara() * rampa() * ALFA
    tinta = np.array(TINTA, dtype=np.float64)
    azul = np.array(AZUL, dtype=np.float64)
    rgb = tinta[None, None, :] + a[:, :, None] * (azul - tinta)[None, None, :]
    out = Image.fromarray(np.round(rgb).astype(np.uint8), "RGB")
    destino = AQUI / "fondo_circuito.png"
    out.save(destino, optimize=True)
    print(destino, destino.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
