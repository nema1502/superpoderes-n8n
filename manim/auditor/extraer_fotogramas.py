"""Extrae fotogramas de un video renderizado para la auditoría VISUAL.

El auditor automático (auditar.py) atrapa lo geométrico; los fotogramas atrapan
lo semántico: elementos duplicados, mobjects fantasma, composición fea.
Revisar cada imagen generada (a ojo, o con Read si eres un modelo).

Uso:
    python auditor/extraer_fotogramas.py media/videos/<...>/Escena.mp4
    python auditor/extraer_fotogramas.py <video.mp4> --cada 1.5
"""

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Fotogramas para auditoría visual")
    parser.add_argument("video", help="ruta del .mp4 renderizado")
    parser.add_argument("--cada", type=float, default=2.0,
                        help="segundos entre fotogramas (por defecto 2)")
    parser.add_argument("--ancho", type=int, default=360,
                        help="ancho de las miniaturas (por defecto 360)")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"[!] No existe: {video}")

    destino = RAIZ / "auditoria" / f"fotogramas_{video.stem}"
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob("*.png"):
        viejo.unlink()

    alto = int(args.ancho * 16 / 9)
    resultado = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video),
         "-vf", f"fps=1/{args.cada},scale={args.ancho}:{alto}",
         str(destino / "f_%03d.png")],
        capture_output=True, text=True)
    if resultado.returncode != 0:
        sys.exit(f"[!] ffmpeg falló:\n{resultado.stderr[-800:]}")

    imagenes = sorted(destino.glob("*.png"))
    print(f"{len(imagenes)} fotogramas (1 cada {args.cada} s) en:")
    for img in imagenes:
        print(f"  {img}")


if __name__ == "__main__":
    main()
