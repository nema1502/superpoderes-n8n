"""Hoja de verificación visual de assets (logos e íconos).

Renderiza TODOS los assets de comun/logos/ y comun/iconos/ en una sola imagen
de contacto, tal y como los dibuja Manim. REGLA: cada asset nuevo se verifica
aquí (a ojo, o con Read si eres un modelo) ANTES de usarlo en una escena — un
SVG complejo puede deformarse al importarlo (nos pasó con el logo de Avalanche,
que quedó irreconocible y llegó hasta el video final).

Uso:
    python auditor/probar_logos.py
Salida:
    auditoria/hoja_assets.png
"""

import shutil
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from manim import (  # noqa: E402
    DOWN, WHITE, Group, ImageMobject, Rectangle, SVGMobject, Scene, Text,
    config,
)

CELDA = 2.6
COLUMNAS = 5
FONDO = "#11131C"


def cargar(ruta):
    if ruta.suffix == ".png":
        return ImageMobject(str(ruta))
    m = SVGMobject(str(ruta))
    # los SVG monocromos (íconos, marcas de simpleicons) se pintan blancos
    if all(sub.get_fill_opacity() == 0 or True for sub in m.submobjects):
        pass
    return m


class HojaAssets(Scene):
    def construct(self):
        rutas = sorted((RAIZ / "comun" / "logos").glob("*.*")) + \
            sorted((RAIZ / "comun" / "iconos").glob("*.*"))
        filas = (len(rutas) + COLUMNAS - 1) // COLUMNAS

        config.frame_width = COLUMNAS * CELDA
        config.frame_height = filas * CELDA

        for i, ruta in enumerate(rutas):
            col, fila = i % COLUMNAS, i // COLUMNAS
            x = (col + 0.5) * CELDA - config.frame_width / 2
            y = config.frame_height / 2 - (fila + 0.5) * CELDA
            try:
                m = cargar(ruta)
                if isinstance(m, SVGMobject) and ruta.parent.name == "iconos":
                    m.set_fill(WHITE, opacity=1).set_stroke(width=0)
                m.scale_to_fit_height(1.4)
                if m.width > 2.2:
                    m.scale_to_fit_width(2.2)
                m.move_to([x, y + 0.25, 0])
                self.add(m)
            except Exception as e:
                self.add(Text(f"ERROR {e}", font_size=14).move_to([x, y, 0]))
            etiqueta = Text(ruta.name, font="Segoe UI", font_size=17)
            etiqueta.move_to([x, y - 0.95, 0])
            self.add(etiqueta)
            self.add(Rectangle(width=CELDA, height=CELDA, stroke_width=1,
                               stroke_opacity=0.25).move_to([x, y, 0]))


def main():
    config.pixel_width = 1200
    config.background_color = FONDO
    config.write_to_movie = False
    config.save_last_frame = True
    config.verbosity = "ERROR"
    config.progress_bar = "none"

    rutas = sorted((RAIZ / "comun" / "logos").glob("*.*")) + \
        sorted((RAIZ / "comun" / "iconos").glob("*.*"))
    filas = (len(rutas) + COLUMNAS - 1) // COLUMNAS
    config.pixel_height = max(1, int(1200 * (filas * CELDA) / (COLUMNAS * CELDA)))

    escena = HojaAssets()
    escena.render()

    destino = RAIZ / "auditoria" / "hoja_assets.png"
    destino.parent.mkdir(exist_ok=True)
    origen = Path(escena.renderer.file_writer.image_file_path)
    shutil.copy(origen, destino)
    print(f"Hoja de assets: {destino}")
    print(f"({len(rutas)} assets — revisar que cada uno se vea como el original)")


if __name__ == "__main__":
    main()
