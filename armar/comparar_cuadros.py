"""¿El primer cuadro de un paso es igual al último del paso anterior?

Es la regla que hace que la charla no "salte" al pasar de diapositiva: cada
paso arranca exactamente donde terminó el anterior. Se extraen los dos cuadros
con ffmpeg (a PNG) y se comparan con Pillow.

Uso:
    python armar/comparar_cuadros.py <anterior.mp4> <siguiente.mp4> [--guardar <carpeta>]

Veredicto:
    IDÉNTICOS          ni un píxel distinto
    IGUALES A LA VISTA diferencias de compresión (PSNR >= 40 dB, nada se mueve)
    DISTINTOS          cambió algo de verdad: sale con código 1
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops


def extraer(video, png, ultimo):
    if ultimo:
        # -update 1 reescribe el PNG con cada cuadro: queda el último.
        # -sseof -2 arranca dos segundos antes del final para no decodificar todo.
        cmd = ["ffmpeg", "-v", "error", "-y", "-sseof", "-2", "-i", str(video), "-update", "1", str(png)]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-frames:v", "1", str(png)]
    subprocess.run(cmd, check=True)
    return Image.open(png).convert("RGB")


def comparar(a, b):
    if a.size != b.size:
        return {"veredicto": "DISTINTOS", "motivo": f"tamaños {a.size} y {b.size}"}
    caja = ImageChops.difference(a, b).getbbox()
    if caja is None:
        return {"veredicto": "IDÉNTICOS", "max": 0, "media": 0.0, "psnr": float("inf"), "caja": None}
    x, y = np.asarray(a, dtype=np.int16), np.asarray(b, dtype=np.int16)
    d = np.abs(x - y)
    mse = float((d.astype(np.float64) ** 2).mean())
    psnr = 10 * np.log10(255 ** 2 / mse) if mse else float("inf")
    notables = float((d.max(axis=2) > 24).mean() * 100)
    veredicto = "IGUALES A LA VISTA" if psnr >= 40 and notables < 0.05 else "DISTINTOS"
    return {"veredicto": veredicto, "max": int(d.max()), "media": float(d.mean()), "psnr": psnr,
            "pixeles_notables_pct": notables, "caja": caja}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("anterior")
    p.add_argument("siguiente")
    p.add_argument("--guardar", help="carpeta donde dejar los dos PNG")
    a = p.parse_args()
    carpeta = Path(a.guardar) if a.guardar else Path(tempfile.mkdtemp(prefix="cuadros_"))
    carpeta.mkdir(parents=True, exist_ok=True)
    ultimo = extraer(a.anterior, carpeta / "ultimo_del_anterior.png", ultimo=True)
    primero = extraer(a.siguiente, carpeta / "primero_del_siguiente.png", ultimo=False)
    r = comparar(ultimo, primero)
    print(f"Último de  {a.anterior}")
    print(f"Primero de {a.siguiente}")
    for k, v in r.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"PNG en {carpeta}")
    sys.exit(1 if r["veredicto"] == "DISTINTOS" else 0)


if __name__ == "__main__":
    main()
