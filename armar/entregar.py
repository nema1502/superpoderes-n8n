"""Lleva lo que sale del armado a presentacion/ y arma videos/.

Se corre después de armar/armar.py todo (necesita salida/ y render/final/):

- presentacion/: el HTML, el PPTX con notas y el PDF de salida/, y el PDF para proyectar, con una
  página por paso (el último cuadro de cada uno) en el mismo orden y con los mismos números que el
  HTML y el PPTX: primero las principales y después las de respaldo.
- videos/: un video por diapositiva (sus pasos propios seguidos, con 1,5 s quietos en el último cuadro
  de cada uno) y la charla completa (los videos finales, con la misma pausa), con x264.

Ningún archivo de presentacion/ ni de videos/ puede pasar de 90 MB: si pasa, sale con error.

Uso: PYTHONUTF8=1 python armar/entregar.py [--sin-videos]
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "armar"))
import vista_previa as VP  # noqa: E402

LIMITE_MB = 90
PAUSA_S = 1.5


def orden_del_deck(deck: dict) -> list[dict]:
    """Las diapositivas como van en el PPTX y en el HTML: principales y después respaldo."""
    ds = deck["diapositivas"]
    return [d for d in ds if d.get("seccion") != "respaldo"] + [d for d in ds if d.get("seccion") == "respaldo"]


def copiar_salida(deck: dict, presentacion: Path) -> None:
    salida = RAIZ / "salida"
    for ext in ("html", "pptx", "pdf"):
        origen = salida / f"{deck['archivo']}.{ext}"
        if not origen.exists():
            raise SystemExit(f"falta {origen.relative_to(RAIZ)}: correr antes armar/armar.py todo")
        shutil.copy2(origen, presentacion / origen.name)
        print(f"{origen.name}: {origen.stat().st_size / 1e6:.1f} MB")


def pdf_para_proyectar(deck: dict, destino: Path) -> None:
    paginas = []
    for d in orden_del_deck(deck):
        for k in range(1, len(d["pasos"]) + 1):
            f = RAIZ / "render" / "cuadros" / "ultimo" / f"{d['id']}_{k}.png"
            if not f.exists():
                raise SystemExit(f"falta {f.relative_to(RAIZ)}: correr antes armar/armar.py todo")
            im = Image.open(f).convert("RGB")
            if im.size != (1920, 1080):
                raise SystemExit(f"{f.name} mide {im.size}")
            paginas.append(im)
    paginas[0].save(destino, "PDF", save_all=True, append_images=paginas[1:], resolution=144.0, quality=92,
                    title=deck.get("titulo", ""), author=deck.get("orador", ""),
                    subject="Para proyectar sin videos", creator="armar")
    print(f"{destino.name}: {len(paginas)} páginas, {destino.stat().st_size / 1e6:.1f} MB")


def videos_por_diapositiva(deck: dict, videos: Path, trabajo: Path) -> None:
    for d in deck["diapositivas"]:
        i = d["id"]
        pasos = [RAIZ / "render" / "pasos" / i / f"{i}_{k}.mp4" for k in range(1, len(d["pasos"]) + 1)]
        faltan = [p.name for p in pasos if not p.exists()]
        if faltan:
            raise SystemExit(f"faltan los pasos de {i}: {faltan}")
        destino = videos / f"{i}_{d['nombre']}.mp4"
        t = trabajo / i
        if t.exists():
            shutil.rmtree(t)
        r = VP.construir(pasos, destino, t, pausa=PAUSA_S, codificador="x264")
        print(f"{destino.name}: {len(pasos)} pasos, {r['duracion_s']} s, {r['bytes'] / 1e6:.2f} MB")


def charla_completa(deck: dict, videos: Path, trabajo: Path) -> None:
    finales = []
    for d in orden_del_deck(deck):
        for k in range(1, len(d["pasos"]) + 1):
            v = RAIZ / "render" / "final" / d["id"] / f"{d['id']}_{k}.mp4"
            if not v.exists():
                raise SystemExit(f"falta {v.relative_to(RAIZ)}: correr antes armar/armar.py todo")
            finales.append(v)
    destino = videos / f"00_{deck['archivo']}_completa.mp4"
    t = trabajo / "completa"
    if t.exists():
        shutil.rmtree(t)
    r = VP.construir(finales, destino, t, pausa=PAUSA_S, codificador="x264")
    print(f"{destino.name}: {r['pasos']} pasos, {r['duracion_s']} s, {r['bytes'] / 1e6:.1f} MB")


def revisar_pesos(carpetas: list[Path]) -> None:
    grandes = []
    for c in carpetas:
        for f in sorted(c.iterdir()):
            if f.is_file() and f.stat().st_size > LIMITE_MB * 1e6:
                grandes.append(f"{c.name}/{f.name} ({f.stat().st_size / 1e6:.1f} MB)")
    if grandes:
        raise SystemExit(f"pasan de {LIMITE_MB} MB: " + ", ".join(grandes))
    print(f"ningún archivo pasa de {LIMITE_MB} MB")


def main() -> None:
    t0 = time.time()
    deck = json.loads((RAIZ / "contenido" / "deck.json").read_text(encoding="utf-8"))
    presentacion = RAIZ / "presentacion"
    videos = RAIZ / "videos"
    trabajo = RAIZ / "render" / "armado" / "entregar"
    presentacion.mkdir(exist_ok=True)
    videos.mkdir(exist_ok=True)
    print("== presentacion/")
    copiar_salida(deck, presentacion)
    pdf_para_proyectar(deck, presentacion / f"{deck['archivo']}_para_proyectar.pdf")
    if "--sin-videos" not in sys.argv:
        print("== videos/")
        videos_por_diapositiva(deck, videos, trabajo)
        charla_completa(deck, videos, trabajo)
    revisar_pesos([presentacion, videos])
    print(f"entregar: listo en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
