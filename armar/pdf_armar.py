"""El PDF de la charla: el último cuadro de cada diapositiva y, al final, las fuentes.

Una página por diapositiva del guion (principales y después respaldo) con el
último cuadro del último paso, en JPEG de buena calidad, a página completa 16:9
(13,333 x 7,5 pulgadas, como el .pptx). Después, las fuentes del deck con su
dirección (con enlace) y la fecha de consulta: la hoja impresa dice «Direcciones
y fechas de consulta: en el PDF de la charla».

Se compone con XeLaTeX (Segoe UI, como todo lo demás): el JPEG entra tal cual
al PDF, sin recomprimir, y el texto de las fuentes queda como texto (se puede
buscar y copiar). Si XeLaTeX no está, sale solo con las imágenes (Pillow).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

CALIDAD_JPEG = 90


def a_jpeg(png: Path, jpg: Path, calidad=CALIDAD_JPEG) -> Path:
    jpg.parent.mkdir(parents=True, exist_ok=True)
    Image.open(png).convert("RGB").save(jpg, "JPEG", quality=calidad, optimize=True, subsampling=0)
    return jpg


_ESC = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%", "#": r"\#", "&": r"\&", "_": r"\_",
        "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def tex(s: str) -> str:
    return "".join(_ESC.get(c, c) for c in s)


def tex_url(u: str) -> str:
    return u.replace("\\", "/").replace("%", r"\%").replace("#", r"\#").replace("&", r"\&").replace("_", r"\_").replace("~", r"\textasciitilde{}")


def _etiquetas(dato: str):
    m = re.match(r"\s*\[([^\]]+)\]\s*(.*)", dato, re.S)
    return (m.group(1), m.group(2)) if m else ("", dato)


PREAMBULO = r"""\documentclass{article}
\usepackage{fontspec}
\setmainfont{Segoe UI}[BoldFont={Segoe UI Bold}, ItalicFont={Segoe UI Italic}, BoldItalicFont={Segoe UI Bold Italic}]
\usepackage[paperwidth=13.333in,paperheight=7.5in,margin=0pt]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\definecolor{tinta}{HTML}{070A0F}
\definecolor{hueso}{HTML}{F5F7FF}
\definecolor{gris}{HTML}{9AA3B8}
\definecolor{ambar}{HTML}{FFB547}
\usepackage[hidelinks]{hyperref}
\hypersetup{pdftitle={<<TITULO>>}, pdfauthor={<<AUTOR>>}, pdfsubject={<<TEMA>>}, pdfkeywords={<<CLAVES>>}, pdfcreator={armar/armar.py (XeLaTeX)}, pdflang={es-BO}, pdfdisplaydoctitle=true}
\pagestyle{empty}
\pagecolor{tinta}
\color{hueso}
\setlength{\parindent}{0pt}
\setlength{\topskip}{0pt}
\setlength{\parskip}{0pt}
\begin{document}
"""


def construir(paginas: list[tuple[str, Path]], fuentes: list[dict], destino: Path, trabajo: Path, meta: dict,
              icono_credito: str | None = None) -> dict:
    """paginas: (etiqueta, png del último cuadro) en orden. Devuelve datos del PDF."""
    trabajo.mkdir(parents=True, exist_ok=True)
    jpgs = []
    for i, (etiqueta, png) in enumerate(paginas, start=1):
        jpgs.append(a_jpeg(png, trabajo / f"p{i:02d}_{etiqueta}.jpg"))
    xelatex = shutil.which("xelatex")
    if not xelatex:
        return _solo_imagenes(jpgs, destino, meta)
    cuerpo = []
    for j in jpgs:
        # La imagen cuelga de la primera línea sin ocupar alto: así nunca "no entra" y salta de página.
        cuerpo.append(r"\noindent\raisebox{-\paperheight}[0pt][0pt]{\includegraphics[width=\paperwidth,height=\paperheight]{"
                      + j.name + "}}\n\\newpage\n")
    if fuentes:
        cuerpo.append(r"\newgeometry{left=0.8in,right=0.8in,top=0.6in,bottom=0.6in}" "\n")
        # bandera izquierda y sin cortar palabras (los patrones de corte cargados son los del inglés)
        cuerpo.append(r"\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000" "\n")
        cuerpo.append(r"\fontsize{16}{21}\selectfont" "\n")
        cuerpo.append(r"{\fontsize{34}{40}\selectfont\bfseries\color{ambar} Fuentes\par}\vspace{6pt}"
                      r"{\color{gris}" + tex(meta.get("titulo", "")) + r". Cada dato, con la diapositiva donde aparece, "
                      r"su fuente, la dirección y la fecha de consulta.\par}\vspace{16pt}" "\n")
        for f in fuentes:
            etiq, dato = _etiquetas(f.get("dato", ""))
            linea = []
            if etiq:
                linea.append(r"{\bfseries\color{ambar}[" + tex(etiq) + r"]}~")
            linea.append(tex(dato))
            cuerpo.append(r"\begin{minipage}{\linewidth}\raggedright " + "".join(linea) + r"\par\vspace{3pt}"
                          r"{\fontsize{13.5}{17.5}\selectfont\color{gris}" + tex(f.get("fuente", "")))
            if f.get("url"):
                cuerpo.append(r", \href{" + tex_url(f["url"]) + r"}{\color{ambar}" + tex(f["url"]) + "}")
            if f.get("fecha"):
                cuerpo.append(", " + tex(f["fecha"]))
            cuerpo.append(r"\par}\end{minipage}\par\vspace{10pt}" "\n")
        if icono_credito:
            cuerpo.append(r"\vspace{6pt}{\color{gris}" + tex(icono_credito) + r"\par}" "\n")
    doc = (PREAMBULO.replace("<<TITULO>>", tex(meta.get("titulo", "")))
           .replace("<<AUTOR>>", tex(meta.get("autor", "")))
           .replace("<<TEMA>>", tex(meta.get("subtitulo", "")))
           .replace("<<CLAVES>>", tex(meta.get("palabras", "")))) + "".join(cuerpo) + r"\end{document}" "\n"
    fuente_tex = trabajo / "charla.tex"
    fuente_tex.write_text(doc, encoding="utf-8")
    r = None
    for _ in range(2):  # dos pasadas: hyperref y la cuenta de páginas
        r = subprocess.run([xelatex, "-interaction=nonstopmode", "-halt-on-error", fuente_tex.name], cwd=trabajo,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            break
    log = (trabajo / "charla.log").read_text(encoding="utf-8", errors="replace") if (trabajo / "charla.log").exists() else ""
    if r.returncode != 0 or not (trabajo / "charla.pdf").exists():
        cola = "\n".join(log.splitlines()[-25:])
        raise RuntimeError(f"XeLaTeX falló ({fuente_tex}):\n{cola}")
    faltan = sorted(set(re.findall(r"Missing character: There is no (.+?) in font", log)))
    paginas_pdf = int(re.search(r"Output written on charla\.pdf \((\d+) page", log).group(1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(trabajo / "charla.pdf", destino)
    return {"archivo": str(destino), "paginas": paginas_pdf, "paginas_diapositivas": len(jpgs),
            "paginas_fuentes": paginas_pdf - len(jpgs), "caracteres_faltantes": faltan,
            "bytes": destino.stat().st_size, "motor": "xelatex",
            "sobrellenas": len(re.findall(r"Overfull \\[hv]box", log))}


def _solo_imagenes(jpgs: list[Path], destino: Path, meta: dict) -> dict:
    ims = [Image.open(j).convert("RGB") for j in jpgs]
    destino.parent.mkdir(parents=True, exist_ok=True)
    ims[0].save(destino, "PDF", save_all=True, append_images=ims[1:], resolution=144.0, quality=CALIDAD_JPEG,
                title=meta.get("titulo", ""), author=meta.get("autor", ""), subject=meta.get("subtitulo", ""))
    return {"archivo": str(destino), "paginas": len(ims), "paginas_diapositivas": len(ims), "paginas_fuentes": 0,
            "caracteres_faltantes": [], "bytes": destino.stat().st_size, "motor": "pillow"}
