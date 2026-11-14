"""Renderiza diapositivas de Manim paso por paso, como remotion/render.mjs las de Remotion.

    .venv/Scripts/python.exe manim/render_diapo.py D07 [D09 ...]

Para cada diapositiva:

1. busca la escena: manim/escenas/<id>_*.py (en minúsculas) con la clase <ID><Nombre> de deck.json;
2. si entra «continuo» desde una de Remotion, se asegura de que render/cuadros/<anterior>_<n>.png
   exista y esté al día (si no, lo saca con node remotion/render.mjs --still <anterior> pasos);
3. corre el auditor en seco (manim/auditor/auditar.py): tiene que dar APROBADO, o no renderiza;
4. renderiza con secciones y pedazos sin pérdida (lo configura manim/comun/charla.py);
5. arma cada paso k con los cuadros de la sección k más el primero de la k+1 (el último cuadro de un
   paso es el primero del siguiente, como en Remotion) y lo codifica con la receta de frontera
   (armar/codificar_paso.py) en render/pasos/<ID>/<ID>_<k>.mp4;
6. deja los cortes sin pérdida en render/cuadros/<ID>_<k>.png (k = 0: el primer cuadro; 1…n: el
   último de cada paso): los usa la diapositiva siguiente;
7. comprueba los cuadros de cada paso contra deck.json, la frontera con la anterior (PNG contra PNG)
   y la de cada paso con el siguiente (videos decodificados): tienen que ser IDÉNTICAS.

Opciones: --sin-auditor (solo para probar; no para entregar) · --sin-refrescar (no saca el PNG de la
anterior aunque falte o esté viejo) · --refrescar-anterior (lo saca siempre).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MANIM = RAIZ / "manim"
ESCENAS = MANIM / "escenas"
PASOS = RAIZ / "render" / "pasos"
CUADROS = RAIZ / "render" / "cuadros"
MEDIA = RAIZ / "render" / "manim"
REMOTION_SRC = RAIZ / "remotion" / "src"
PY = sys.executable

sys.path.insert(0, str(RAIZ / "armar"))
import codificar_paso  # noqa: E402
import comparar_cuadros  # noqa: E402

ENTORNO = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
FPS = 30


def deck():
    return json.loads((RAIZ / "contenido" / "deck.json").read_text(encoding="utf-8"))


def tokens():
    return json.loads((RAIZ / "diseno" / "tokens.json").read_text(encoding="utf-8"))


def diapo(d, id_):
    for x in d["diapositivas"]:
        if x["id"] == id_:
            return x
    raise SystemExit(f"«{id_}» no está en deck.json")


def entrada(d, id_):
    ids = [x["id"] for x in d["diapositivas"]]
    i = ids.index(id_)
    x = diapo(d, id_)
    e = x.get("entrada") or {"tipo": "corte" if i == 0 else "continuo", "duracion_s": 0}
    desde = e["desde"] if "desde" in e else (None if i <= 0 else ids[i - 1])
    return {"tipo": e["tipo"], "duracion_s": e.get("duracion_s", 0) or 0, "desde": desde}


def cuadros_por_paso(d, id_):
    x = diapo(d, id_)
    e = entrada(d, id_)
    desc = e["duracion_s"] if e["tipo"] in ("fundido", "puertas") else 0
    return [int(round(round((p["duracion_animacion_s"] - (desc if k == 0 else 0)) * 1000) / 1000 * FPS)) for k, p in enumerate(x["pasos"])]


def rel(p: Path) -> str:
    try:
        return Path(p).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return Path(p).as_posix()


def escena_de(d, id_):
    x = diapo(d, id_)
    if x["motor"] != "manim":
        raise SystemExit(f"{id_} es de {x['motor']}: se renderiza con node remotion/render.mjs {id_}")
    clase = f"{id_}{x['nombre']}"
    candidatos = sorted(ESCENAS.glob(f"{id_.lower()}_*.py"))
    for c in candidatos:
        if re.search(rf"^class\s+{clase}\b", c.read_text(encoding="utf-8"), re.M):
            return c, clase
    raise SystemExit(f"{id_}: no encuentro manim/escenas/{id_.lower()}_*.py con la clase {clase} (hay: {[c.name for c in candidatos]})")


# ---------------------------------------------------------------------------
# El cuadro de la anterior (entrada continua)
# ---------------------------------------------------------------------------


def fuentes_mas_nuevas(id_prev: str) -> float:
    """Lo mismo que fuentesMasNuevas() de remotion/render.mjs: la fecha más nueva de lo que cambia
    una diapositiva de Remotion."""
    archivos = [RAIZ / "diseno" / "tokens.json", RAIZ / "contenido" / "deck.json"]
    archivos += [p for p in (REMOTION_SRC / "diapos").glob(f"{id_prev}*.tsx") if re.match(rf"^{id_prev}[A-Z]", p.name)]
    for carpeta in ("comun", "sistema"):
        archivos += list((REMOTION_SRC / carpeta).iterdir())
    archivos += [REMOTION_SRC / "pasos.ts", REMOTION_SRC / "deck.ts", REMOTION_SRC / "tokens.ts"]
    return max(p.stat().st_mtime for p in archivos if p.exists())


def preparar_anterior(d, id_, args) -> tuple[Path | None, str | None]:
    e = entrada(d, id_)
    if e["tipo"] != "continuo" or not e["desde"]:
        return None, None
    prev = diapo(d, e["desde"])
    n = len(prev["pasos"])
    png = CUADROS / f"{e['desde']}_{n}.png"
    nombre = f"{e['desde']}.{n}"
    if prev["motor"] == "remotion" and not args.sin_refrescar:
        viejo = png.exists() and png.stat().st_mtime < fuentes_mas_nuevas(e["desde"])
        if not png.exists() or viejo or args.refrescar_anterior:
            print(f"  {id_} entra desde {nombre}: saco su último cuadro{' (el que había estaba viejo)' if viejo else ''}")
            r = subprocess.run(["node", str(RAIZ / "remotion" / "render.mjs"), "--still", e["desde"], "pasos"], cwd=RAIZ)
            if r.returncode != 0:
                print(f"  AVISO: no se pudo sacar {rel(png)}; sigo con el que hay" if png.exists() else f"  AVISO: no se pudo sacar {rel(png)}")
    if not png.exists():
        print(f"  AVISO: falta {rel(png)} ({e['desde']} es de {prev['motor']}): {id_} arranca desde tinta y su frontera no va a empalmar.")
        return None, nombre
    return png, nombre


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def auditar(modulo: Path, clase: str) -> bool:
    t0 = time.time()
    r = subprocess.run([PY, str(MANIM / "auditor" / "auditar.py"), str(modulo), clase], cwd=MANIM, env=ENTORNO,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lineas = [x for x in r.stdout.splitlines() if x.strip().startswith(("[", "->", "=="))]
    for x in lineas:
        print(f"  {x.strip()}")
    if r.returncode != 0:
        if not lineas:
            print(r.stdout[-3000:], r.stderr[-3000:])
        return False
    print(f"  auditor: {time.time() - t0:.1f} s")
    return True


def renderizar(modulo: Path, clase: str) -> Path:
    t0 = time.time()
    r = subprocess.run([PY, "-m", "manim", "render", "-v", "WARNING", "--progress_bar", "none", str(modulo), clase],
                       cwd=RAIZ, env=ENTORNO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-4000:], r.stderr[-6000:])
        raise SystemExit(f"{clase}: falló el render de Manim")
    for x in (r.stdout + r.stderr).splitlines():
        if "AVISO" in x:
            print(f"  {x.strip()}")
    secciones = MEDIA / "videos" / modulo.stem / "1080p30" / "sections"
    print(f"  render de Manim: {time.time() - t0:.1f} s")
    return secciones


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def contar(video: Path) -> int:
    return codificar_paso.contar_cuadros(video)[0]


def armar_pasos(id_, clase, secciones: Path, esperados: list[int], tmp: Path) -> list[Path]:
    info = json.loads((secciones / f"{clase}.json").read_text(encoding="utf-8"))
    nombres = [s["name"] for s in info]
    n = len(esperados)
    esperado_nombres = [f"paso_{k}" for k in range(1, n + 1)] + ["fin"]
    if nombres != esperado_nombres:
        raise SystemExit(f"{id_}: las secciones son {nombres} y se esperaban {esperado_nombres}")
    videos = [secciones / s["video"] for s in info]
    for k in range(n):
        c = contar(videos[k])
        if c != esperados[k]:
            raise SystemExit(f"{id_}.{k + 1}: la sección tiene {c} cuadros y el paso dura {esperados[k]} ({esperados[k] / FPS:.2f} s según deck.json)")
    if contar(videos[n]) != 1:
        raise SystemExit(f"{id_}: la sección «fin» tiene {contar(videos[n])} cuadros (se espera 1)")
    destino = PASOS / id_
    destino.mkdir(parents=True, exist_ok=True)
    salidas = []
    for k in range(1, n + 1):
        crudo = tmp / f"{id_}_{k}_sp.mkv"
        ffmpeg("-i", str(videos[k - 1]), "-i", str(videos[k]),
               "-filter_complex", "[1:v]trim=end_frame=1,setpts=PTS-STARTPTS[b];[0:v][b]concat=n=2:v=1:a=0[v]",
               "-map", "[v]", "-c:v", "libx264rgb", "-qp", "0", "-preset", "veryfast", "-pix_fmt", "rgb24", str(crudo))
        final = destino / f"{id_}_{k}.mp4"
        provisorio = destino / f"{id_}_{k}.{os.getpid()}.tmp.mp4"
        cuadros = codificar_paso.codificar(crudo, provisorio)
        os.replace(provisorio, final)
        if cuadros != esperados[k - 1] + 1:
            raise SystemExit(f"{id_}_{k}.mp4: {cuadros} cuadros y se esperaban {esperados[k - 1] + 1}")
        print(f"  {id_}_{k}.mp4: {cuadros} cuadros")
        salidas.append(final)
    for f in destino.glob(f"{id_}_*.mp4"):
        m = re.fullmatch(rf"{id_}_(\d+)\.mp4", f.name)
        if m and int(m.group(1)) > n:
            f.unlink()
    # Cortes sin pérdida: k = 0 el primer cuadro; k = 1…n el último de cada paso (= primero de la sección k+1).
    CUADROS.mkdir(parents=True, exist_ok=True)
    for k in range(0, n + 1):
        fuente = videos[0] if k == 0 else videos[k]
        png = CUADROS / f"{id_}_{k}.png"
        provisorio = CUADROS / f"{id_}_{k}.{os.getpid()}.tmp.png"
        ffmpeg("-i", str(fuente), "-frames:v", "1", "-pix_fmt", "rgb24", str(provisorio))
        os.replace(provisorio, png)
    return salidas


def comparar_png(a: Path, b: Path) -> str:
    from PIL import Image

    r = comparar_cuadros.comparar(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"))
    if r["veredicto"] == "IDÉNTICOS":
        return "IDÉNTICA"
    import numpy as np

    x = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
    y = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
    distintos = int((np.abs(x - y).max(axis=2) > 0).sum())
    return f"DISTINTA ({distintos} px, máx. {r.get('max')}, caja {r.get('caja')})"


def fronteras(id_, salidas: list[Path], tmp: Path) -> list[str]:
    malas = []
    for k in range(1, len(salidas)):
        a = comparar_cuadros.extraer(salidas[k - 1], tmp / f"f{k}_ultimo.png", ultimo=True)
        b = comparar_cuadros.extraer(salidas[k], tmp / f"f{k}_primero.png", ultimo=False)
        r = comparar_cuadros.comparar(a, b)
        print(f"  frontera {id_}.{k} → {id_}.{k + 1}: {r['veredicto']}")
        if r["veredicto"] != "IDÉNTICOS":
            malas.append(f"{id_}.{k} → {id_}.{k + 1}")
    return malas


def render_diapo(id_: str, args) -> bool:
    t0 = time.time()
    d = deck()
    modulo, clase = escena_de(d, id_)
    print(f"{id_}: {rel(modulo)} :: {clase}")
    esperados = cuadros_por_paso(d, id_)
    anterior, nombre_anterior = preparar_anterior(d, id_, args)
    if not args.sin_auditor and not auditar(modulo, clase):
        print(f"  {id_}: el auditor RECHAZÓ la escena (reporte en manim/auditoria/reporte_{clase}.md): no se renderiza")
        return False
    secciones = renderizar(modulo, clase)
    tmp = Path(tempfile.mkdtemp(prefix=f"render_{id_}_", dir=RAIZ / ".tmp" if (RAIZ / ".tmp").exists() else None))
    try:
        salidas = armar_pasos(id_, clase, secciones, esperados, tmp)
        resumen = ""
        if anterior is not None:
            veredicto = comparar_png(anterior, CUADROS / f"{id_}_0.png")
            resumen = f" · frontera con {nombre_anterior}: {veredicto}"
            print(f"  frontera con {nombre_anterior}: {veredicto}")
        elif nombre_anterior:
            resumen = f" · frontera con {nombre_anterior}: SIN CUADRO"
        malas = fronteras(id_, salidas, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = sum(esperados) + 1
    print(f"  {id_}: {len(esperados)} pasos, {total} cuadros en {time.time() - t0:.1f} s -> {rel(PASOS / id_)}/{resumen}")
    return not malas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="+")
    p.add_argument("--sin-auditor", action="store_true")
    p.add_argument("--sin-refrescar", action="store_true")
    p.add_argument("--refrescar-anterior", action="store_true")
    args = p.parse_args()
    (RAIZ / ".tmp").mkdir(exist_ok=True)
    errores = [i.upper() for i in args.ids if not render_diapo(i.upper(), args)]
    print(f"Listo{' · con errores: ' + ' '.join(errores) if errores else ''}.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
