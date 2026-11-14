"""Codifica un paso (un video sin pérdida) en el formato que va al PowerPoint.

La receta es la misma que aplica remotion/render.mjs, para que un paso de Manim
y uno de Remotion se vean con los mismos colores y empalmen igual:

- H.264 High, yuv420p, convertido a BT.709 de rango limitado con zscale (el
  mismo filtro que usa Remotion) y etiquetado como BT.709;
- QP constante 16 (no CRF) y un cuadro clave forzado en el ÚLTIMO cuadro: así
  el último cuadro de un paso y el primero del siguiente, si salen de la misma
  imagen, quedan idénticos al bit (con CRF nunca: medido el 22-oct-2026);
- sin audio, sin metadatos heredados, y el índice (moov) al principio
  (+faststart), para que PowerPoint arranque sin leer todo el archivo.

La entrada tiene que ser sin pérdida (Manim con manim/comun/sin_perdida.py,
una secuencia PNG, ProRes 4444 no: ProRes también pierde). Si se le pasa un
video con pérdida funciona igual, pero la frontera ya no queda exacta.

Uso:
    python armar/codificar_paso.py <entrada> <salida.mp4> [--qp 16] [--sostener 0.0]
    (--sostener N repite el último cuadro N segundos más, para estirar el final quieto)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

FILTRO_BT709 = "zscale=matrix=709:range=limited:primariesin=709:primaries=709:transferin=709:transfer=709"


def contar_cuadros(video):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "json", str(video)],
        check=True, capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    num, den = (int(x) for x in s["r_frame_rate"].split("/"))
    return int(s["nb_read_packets"]), num / den


def codificar(entrada, salida, qp=16, sostener=0.0):
    cuadros, fps = contar_cuadros(entrada)
    extra = int(round(sostener * fps))
    ultimo = cuadros + extra - 1
    filtro = FILTRO_BT709 if not extra else f"tpad=stop_mode=clone:stop={extra},{FILTRO_BT709}"
    cmd = [
        "ffmpeg", "-v", "error", "-y", "-i", str(entrada),
        "-an", "-map_metadata", "-1",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-qp", str(qp),
        "-vf", filtro, "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-force_key_frames", f"expr:eq(n,{ultimo})",
        "-movflags", "+faststart",
        str(salida),
    ]
    subprocess.run(cmd, check=True)
    return cuadros + extra


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("entrada")
    p.add_argument("salida")
    p.add_argument("--qp", type=int, default=16)
    p.add_argument("--sostener", type=float, default=0.0)
    a = p.parse_args()
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    n = codificar(a.entrada, a.salida, a.qp, a.sostener)
    print(f"{a.salida}: {n} cuadros, {Path(a.salida).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    sys.exit(main())
