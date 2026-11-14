"""Prueba del armado a escala real: el deck de verdad con videos sintéticos.

Lee contenido/deck.json (66 pasos, unos 700 s, las notas, los dings y las
fuentes reales) y arma en .tmp/armado/escala/render/pasos/ un video sintético por
paso, con la duración del deck y la receta de frontera: cada paso va de una
"tarjeta" (el id, el título y el texto en pantalla del deck) a la siguiente con
un barrido, y queda quieto 0,3 s; los pasos largos (cronómetros) llevan una
cuenta que baja de a un segundo. El primer cuadro de cada paso es la tarjeta del
anterior (idénticos). El paso 1 sigue el campo «entrada» como lo hace Remotion
(remotion/lib/deck.mjs): con «continuo» arranca en la tarjeta final de «desde»;
con «fundido» o «puertas» arranca en una tarjeta propia y dura lo del deck menos
la transición (el armado la pone delante); con «corte», desde tinta.

No toca render/ ni salida/. Uso:
    .venv/Scripts/python.exe armar/prueba_escala.py [--solo-generar] [--show]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import deck as D  # noqa: E402
import videos as V  # noqa: E402

BASE = D.RAIZ / ".tmp" / "armado" / "escala"
W, H = D.ANCHO, D.ALTO
HUESO, GRIS, AMBAR, ACERO2 = (245, 247, 255), (154, 163, 184), (255, 181, 71), (42, 52, 70)
F_ID = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 150)
F_T = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 60)
F_L = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 49)
FUENTE_FF = "C\\:/Windows/Fonts/segoeuib.ttf"


def tarjeta(p: D.Paso, fresca=False) -> Image.Image:
    im = Image.new("RGB", (W, H), D.TINTA)
    d = ImageDraw.Draw(im)
    color = AMBAR if p.diapo.seccion == "principal" else GRIS
    d.text((120, 90), p.etiqueta if not fresca else p.diapo.id, font=F_ID, fill=color)
    d.text((120, 290), p.diapo.titulo[:52], font=F_T, fill=HUESO)
    y = 420
    textos = [] if fresca else (p.datos.get("texto_pantalla") or [])
    for t in textos[:8]:
        d.text((120, y), str(t)[:64], font=F_L, fill=GRIS)
        y += 66
    d.rectangle([120, 1000, 120 + int(1680 * p.k / len(p.diapo.pasos)), 1012], fill=ACERO2 if fresca else color)
    return im


def codificar_paso(desde: Path, hasta: Path, dur: float, cuenta: bool, destino: Path) -> None:
    """De la tarjeta `desde` a la `hasta`: barrido en (dur - 0,3) s y quieto; con la cuenta si es largo."""
    n = int(round(dur * D.FPS)) + 1
    barrido = max(0.2, min(1.2, dur - 0.3))
    # el cuadro 0 es la tarjeta de partida tal cual (xfade arranca ya un poco corrido) y después el barrido
    filtro = (f"[0:v]split[a][a2];[a]trim=end_frame=1,setpts=PTS-STARTPTS[a0];"
              f"[a2][1:v]xfade=transition=wipeleft:duration={barrido:.3f}:offset=0,trim=start_frame=1,"
              f"setpts=PTS-STARTPTS[x];[a0][x]concat=n=2:v=1,format=rgb24")
    if cuenta:
        fin = (n - 1) / D.FPS - 0.3
        filtro += (f",drawtext=fontfile='{FUENTE_FF}':fontsize=200:fontcolor=0xFFB547:x=1450:y=600:"
                   f"text='%{{eif\\:max(0\\,ceil({fin:.3f}-t))\\:d}}':enable='gt(t\\,0.02)*lt(t\\,{fin:.3f})'")
    filtro += f",trim=end_frame={n},{V.FILTRO_BT709}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(D.FPS), "-t", f"{dur + 1:.3f}", "-i", str(desde),
           "-loop", "1", "-framerate", str(D.FPS), "-t", f"{dur + 1:.3f}", "-i", str(hasta), "-filter_complex", filtro,
           "-an", "-map_metadata", "-1", "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-qp", "16",
           "-pix_fmt", "yuv420p", *V.ETIQUETAS, "-force_key_frames", f"expr:eq(n,{n - 1})", "-frames:v", str(n),
           "-movflags", "+faststart", str(destino)]
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)


def generar(base: Path) -> None:
    deck = D.cargar()
    tarjetas = base / "tarjetas"
    tarjetas.mkdir(parents=True, exist_ok=True)
    ultima_de: dict[str, Path] = {}
    tinta = tarjetas / "tinta.png"
    Image.new("RGB", (W, H), D.TINTA).save(tinta)
    t0 = time.time()
    for d in deck.diapos:
        for p in d.pasos:
            fin = tarjetas / f"{p.id}.png"
            tarjeta(p).save(fin)
            e = d.entrada
            if p.k > 1:
                ini = tarjetas / f"{d.id}_{p.k - 1}.png"
            elif e.con_transicion:
                ini = tarjetas / f"{d.id}_0_fresca.png"
                tarjeta(p, fresca=True).save(ini)
            elif e.tipo == "continuo" and e.desde:
                ini = ultima_de.get(e.desde, tinta)
            else:
                ini = tinta
            dur = p.duracion - (e.segundos if (p.k == 1 and e.con_transicion) else 0.0)
            codificar_paso(ini, fin, dur, dur > 10, base / "render" / "pasos" / d.id / f"{p.id}.mp4")
        ultima_de[d.id] = tarjetas / f"{d.pasos[-1].id}.png"
        print(f"  {d.id}: {len(d.pasos)} pasos ({time.time() - t0:.0f} s)", flush=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--solo-generar", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    base = Path(a.base)
    if not (base / "render" / "pasos").exists():
        t = time.time()
        generar(base)
        print(f"videos sintéticos de los 66 pasos: {time.time() - t:.0f} s")
    if a.solo_generar:
        return 0
    cmd = [sys.executable, str(AQUI / "armar.py"), "todo", "--sin-render", "--render", str(base / "render"),
           "--salida", str(base / "salida")] + (["--show"] if a.show else [])
    return subprocess.call(cmd, cwd=D.RAIZ)


if __name__ == "__main__":
    sys.exit(main())
