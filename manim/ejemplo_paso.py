"""Ejemplo mínimo de una diapositiva de la charla hecha en Manim (22-oct-2026).

Junta lo que se probó en docs/infra.md: formato 16:9 de estilo.py, un paso por
sección (cada sección termina quieta), videos parciales sin pérdida
(sin_perdida.py) y fórmulas con el texto en Segoe UI (tex_segoe.py).

Desde la raíz del repositorio:
    # 1. auditor (debe dar APROBADO); se corre desde manim/
    cd manim && ../.venv/Scripts/python.exe auditor/auditar.py ejemplo_paso.py EjemploPaso && cd ..
    # 2. render, un video sin pérdida por sección
    .venv/Scripts/python.exe -m manim render --save_sections --media_dir render/manim manim/ejemplo_paso.py EjemploPaso
    # 3. entrega: cada sección a la receta del PowerPoint
    .venv/Scripts/python.exe armar/codificar_paso.py render/manim/videos/ejemplo_paso/1080p30/sections/EjemploPaso_0000_formula.mp4 render/pasos/ejemplo_1.mp4
    .venv/Scripts/python.exe armar/codificar_paso.py render/manim/videos/ejemplo_paso/1080p30/sections/EjemploPaso_0001_plantilla.mp4 render/pasos/ejemplo_2.mp4
    # 4. la frontera entre los dos pasos tiene que dar IDÉNTICOS
    .venv/Scripts/python.exe armar/comparar_cuadros.py render/pasos/ejemplo_1.mp4 render/pasos/ejemplo_2.mp4
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "comun"))

from manim import UP, FadeIn, MathTex, Scene, Write  # noqa: E402

from estilo import BLANCO, GRIS, NEMA_TINTA, configurar_horizontal, texto  # noqa: E402
from sin_perdida import activar  # noqa: E402
from tex_segoe import PLANTILLA_SEGOE_NEGRITA  # noqa: E402

configurar_horizontal(NEMA_TINTA)
activar()

# Acento PROVISIONAL de las pruebas (el mismo de remotion/src/tokens.ts),
# hasta que el diseño elija el definitivo. Nunca el lima de la marca.
ACENTO = "#FF7A59"


class EjemploPaso(Scene):
    def construct(self):
        # ---- paso 1: la fórmula
        self.next_section("formula")
        rotulo = texto("Ejemplo de paso en Manim", tamano=30, color=GRIS)
        rotulo.to_edge(UP, buff=0.7)
        formula = MathTex(r"\text{palabras}", "=", r"\text{ritmo}", r"\times", r"\text{tiempo}",
                          font_size=100, tex_template=PLANTILLA_SEGOE_NEGRITA)
        formula[0].set_color(ACENTO)
        formula[1].set_color(GRIS)
        formula[2].set_color(BLANCO)
        formula[3].set_color(GRIS)
        formula[4].set_color(BLANCO)
        self.play(FadeIn(rotulo), run_time=0.5)
        self.play(Write(formula), run_time=1.5)
        self.wait(1)  # cada paso termina quieto: es el cuadro que mira la sala

        # ---- paso 2: arranca exactamente donde terminó el 1
        self.next_section("plantilla")
        plantilla = MathTex(r"\text{Ayudo a }", "X", r"\text{ a lograr }", "Y", r"\text{ con }", "Z",
                            font_size=84, tex_template=PLANTILLA_SEGOE_NEGRITA)
        for i in (1, 3, 5):
            plantilla[i].set_color(ACENTO)
        for i in (0, 2, 4):
            plantilla[i].set_color(BLANCO)
        self.play(formula.animate.shift(UP * 0.9), run_time=0.8)
        plantilla.next_to(formula, direction=-UP, buff=0.9)
        self.play(FadeIn(plantilla, shift=UP * 0.3), run_time=0.8)
        self.wait(1)
