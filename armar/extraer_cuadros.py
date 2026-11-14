"""Saca el primer y el último cuadro de cada paso como PNG.

Uso:
    python armar/extraer_cuadros.py D05 D07
    python armar/extraer_cuadros.py --todos
    python armar/extraer_cuadros.py --todos --final      de render/final/ a render/cuadros/final/
    --forzar     los vuelve a sacar aunque estén al día
    --parcial    un video que falta no hace fallar

Deja render/cuadros/<ID>_<k>_primero.png y <ID>_<k>_ultimo.png. Son los cuadros
decodificados del MP4, con la misma conversión que usan el auditor y las hojas de
contactos (BT.709 de rango limitado a RGB): lo que muestra PowerPoint. Los usan el PDF y
el HTML (último cuadro), el póster de cada video en el .pptx (primer cuadro), el guion del
orador y las transiciones.

Ojo: para que un motor arranque donde terminó el otro (D06 → D07, por ejemplo) y la
frontera salga idéntica al bit, hace falta el cuadro SIN PÉRDIDA (el still de Remotion o el
último cuadro sin pérdida de Manim), no este PNG decodificado (docs/auditoria.md).

No vuelve a sacar un PNG más nuevo que su video. Sale con código 1 si falta algún video
pedido (salvo --parcial) o si alguno no se pudo leer.
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cuadros_comun as cc  # noqa: E402


def al_dia(png: Path, video: Path) -> bool:
    return png.exists() and png.stat().st_mtime >= video.stat().st_mtime


def guardar(arr, destino: Path):
    """Escribe a un temporal y lo renombra: nadie lee un PNG a medio escribir."""
    tmp = destino.with_name(destino.stem + ".parcial.png")
    cc.guardar_png(arr, tmp)
    os.replace(tmp, destino)


def extraer(paso: cc.Paso, carpeta_videos: Path, salida: Path, forzar: bool) -> tuple:
    video = paso.video(carpeta_videos)
    if not video.exists():
        return paso, "falta", None
    primero = salida / f"{paso.nombre_archivo}_primero.png"
    ultimo = salida / f"{paso.nombre_archivo}_ultimo.png"
    if not forzar and al_dia(primero, video) and al_dia(ultimo, video):
        return paso, "al día", None
    try:
        guardar(cc.primer_cuadro(video), primero)
        guardar(cc.ultimo_cuadro(video), ultimo)
    except cc.ErrorVideo as e:
        return paso, "error", str(e)
    return paso, "extraído", None


def main(argv=None) -> int:
    cc.consola_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="diapositivas (D05 D07 A1...)")
    p.add_argument("--todos", action="store_true")
    p.add_argument("--final", action="store_true", help="de render/final/ a render/cuadros/final/")
    p.add_argument("--forzar", action="store_true")
    p.add_argument("--parcial", action="store_true")
    p.add_argument("--hilos", type=int, default=2)
    g = p.add_argument_group("rutas (para las pruebas)")
    g.add_argument("--deck")
    g.add_argument("--videos")
    g.add_argument("--salida")
    a = p.parse_args(argv)
    if not a.ids and not a.todos:
        p.error("faltan las diapositivas (D05 D07...) o --todos")
    r = cc.Rutas()
    if a.deck:
        r.deck = Path(a.deck)
    deck = cc.cargar_deck(r)
    try:
        diapos = cc.elegir_diapos(deck, a.ids, a.todos)
    except ValueError as e:
        p.error(str(e))
    videos = Path(a.videos) if a.videos else (r.final if a.final else r.pasos)
    salida = Path(a.salida) if a.salida else (r.cuadros / "final" if a.final else r.cuadros)
    salida.mkdir(parents=True, exist_ok=True)
    pasos = [paso for d in diapos for paso in d.pasos]
    cuenta = {"extraído": 0, "al día": 0, "falta": 0, "error": 0}
    faltan, fallas = [], []
    with ThreadPoolExecutor(max_workers=max(1, a.hilos)) as ex:
        for paso, estado, err in ex.map(lambda q: extraer(q, videos, salida, a.forzar), pasos):
            cuenta[estado] += 1
            if estado == "falta":
                faltan.append(paso.clave)
            elif estado == "error":
                fallas.append(f"{paso.clave}: {err}")
            print(f"  {paso.clave:<6} {estado}", flush=True)
    print(f"\n{cuenta['extraído']} extraídos, {cuenta['al día']} al día, {cuenta['falta']} sin video, "
          f"{cuenta['error']} con error. PNG en {r.relativa(salida)}/")
    if faltan:
        print(f"Sin video: {', '.join(faltan)}")
    for f in fallas:
        print(f"ERROR {f}")
    return 1 if fallas or (faltan and not a.parcial) else 0


if __name__ == "__main__":
    sys.exit(main())
