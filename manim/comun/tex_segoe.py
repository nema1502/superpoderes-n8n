"""Fórmulas de Manim con el texto en Segoe UI (XeLaTeX + fontspec).

La plantilla por defecto de Manim compila con `latex` y escribe `\\text{...}` en
Computer Modern, con serifa, que choca con el Segoe UI del resto de la charla.
Con esta plantilla, `MathTex` compila con XeLaTeX (salida .xdv, que dvisvgm
convierte igual) y el texto de las fórmulas sale en Segoe UI. Probado el
22-oct-2026 en .tmp/infra/prueba_xetex.py (TinyTeX, TeX Live 2026).

Las letras sueltas en modo matemático (X, Y, Z) siguen en la itálica
matemática clásica, que contrasta bien. Con `\\mathit{X}` salen en Segoe UI
Italic. Las dos opciones se ven en la prueba; la elección es de diseño.

Además, el texto compuesto por LaTeX kernea bien. `Text` de Manim (Pango) deja
huecos después de la T mayúscula ("INFRAEST RUCTURA", "MATHT EX"): para rótulos
en mayúsculas dentro de Manim, esta plantilla con `Tex` es la salida.

Uso:
    from tex_segoe import PLANTILLA_SEGOE, PLANTILLA_SEGOE_NEGRITA
    MathTex(r"\\text{palabras}", "=", r"\\text{ritmo}", r"\\times", r"\\text{tiempo}",
            tex_template=PLANTILLA_SEGOE)
"""

from manim import TexTemplate


def plantilla_segoe(negrita=False):
    fuente = "Segoe UI Bold" if negrita else "Segoe UI"
    return TexTemplate(
        tex_compiler="xelatex",
        output_format=".xdv",
        documentclass=r"\documentclass[preview]{standalone}",
        preamble=(
            "\\usepackage{amsmath}\n"
            "\\usepackage{fontspec}\n"
            f"\\setmainfont{{{fuente}}}[BoldFont={{Segoe UI Bold}}, ItalicFont={{Segoe UI Italic}}, "
            "BoldItalicFont={Segoe UI Bold Italic}]\n"
        ),
    )


PLANTILLA_SEGOE = plantilla_segoe()
PLANTILLA_SEGOE_NEGRITA = plantilla_segoe(negrita=True)
