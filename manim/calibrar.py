"""Calibración de Manim contra Remotion: el mismo texto, en el mismo lugar, ¿se ve igual?

Dibuja las mismas muestras (textos de la charla a 49-105 px, en hueso, ámbar y gris, alineados a
la izquierda, al centro y a la derecha, y un bloque de D07.3) con Remotion (<Texto> de verdad,
remotion/calibrar_manim.mjs) y con Manim (charla.Texto y charla.rect_borde), y compara los dos
cuadros muestra por muestra: posición (centro de la tinta), ancho, alto, cantidad de tinta, color
de lo lleno y diferencia por píxel. Deja los recortes lado a lado para mirarlos a tamaño real.

    .venv/Scripts/python.exe manim/calibrar.py            todo (Remotion + Manim + comparación)
    .venv/Scripts/python.exe manim/calibrar.py --solo-comparar   sin volver a renderizar

Salidas: .tmp/calibracion/ (los dos cuadros y el JSON de muestras), render/revision/calibracion/
(un PNG por muestra: Remotion arriba, Manim en el medio, la diferencia ×4 abajo) y el informe en
la consola. El resultado del 23-oct-2026 está en docs/convenciones.md §11.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "comun"))

import charla  # noqa: E402
from charla import COLOR, RAIZ, Texto, rect_borde  # noqa: E402
from manim import Scene  # noqa: E402

# Para probar otros ajustes sin tocar charla.py (los lee el proceso de Manim):
#   CALIBRAR_BASE=continua (y + 0,344·tam, sin el modelo de Chrome)  CALIBRAR_REFUERZO=0.3 (px de trazo en los glifos)
if os.environ.get("CALIBRAR_BASE") == "continua":
    charla.BASE_COMO_CHROME = False
if os.environ.get("CALIBRAR_REFUERZO"):
    charla.REFUERZO_PX = float(os.environ["CALIBRAR_REFUERZO"])

MUESTRAS = [
    # La pedida: «Ayudamos a X a Y» a 60 y 96 px, en hueso y en ámbar.
    {"texto": "Ayudamos a X a Y", "tam": 60, "color": "hueso", "x": 120, "y": 100, "alinear": "izq"},
    {"texto": "Ayudamos a X a Y", "tam": 60, "color": "ambar", "x": 1000, "y": 100, "alinear": "izq"},
    {"texto": "Ayudamos a X a Y", "tam": 96, "color": "hueso", "x": 120, "y": 230, "alinear": "izq"},
    {"texto": "Ayudamos a X a Y", "tam": 96, "color": "ambar", "x": 1000, "y": 230, "alinear": "izq"},
    # Las de D07 en sus tamaños, y las tres alineaciones.
    {"texto": "palabras = segundos × ritmo", "tam": 105, "color": "hueso", "x": 960, "y": 390, "alinear": "centro"},
    {"texto": "Tomate TATA AVATAR", "tam": 72, "color": "hueso", "x": 120, "y": 500, "alinear": "izq"},
    {"texto": "ritmo: palabras por segundo", "tam": 52, "color": "gris", "x": 1800, "y": 500, "alinear": "der"},
    {"texto": "Cálculo propio con datos de habla en español (Schwab, 2015)", "tam": 49, "color": "gris", "x": 960, "y": 600, "alinear": "centro"},
    {"texto": "60 a 75 palabras ≈ 3 frases", "tam": 72, "color": "hueso", "x": 960, "y": 700, "alinear": "centro"},
    {"texto": "20 a 25 palabras", "tam": 60, "color": "hueso", "x": 380, "y": 880, "alinear": "centro"},
    {"texto": "10 s", "tam": 60, "color": "ambar", "x": 960, "y": 880, "alinear": "centro"},
]
BLOQUES = [
    {"cx": 380, "cy": 880, "ancho": 540, "alto": 200, "radio": 24, "grosor": 5, "relleno": 0.12},
    {"cx": 1540, "cy": 880, "ancho": 540, "alto": 200, "radio": 24, "grosor": 5, "relleno": 0.12},
]

TMP = RAIZ / ".tmp" / "calibracion"
REVISION = RAIZ / "render" / "revision" / "calibracion"


class CalibracionManim(Scene):
    def construct(self):
        for b in BLOQUES:
            self.add(rect_borde(b["cx"], b["cy"], b["ancho"], b["alto"], b["radio"], b["grosor"], COLOR["ambar"],
                                opacidad_relleno=b["relleno"]))
        for m in MUESTRAS:
            self.add(Texto(m["texto"], m["x"], m["y"], tam=m["tam"], color=COLOR[m["color"]], alinear=m["alinear"]))


# ---------------------------------------------------------------------------
# Comparación
# ---------------------------------------------------------------------------


def _hex(h):
    h = h.lstrip("#")
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


def cobertura(img, color, fondo):
    """Cuánto de `color` hay en cada píxel (0 = fondo, 1 = lleno), proyectando sobre la recta
    fondo → color."""
    import numpy as np

    c = np.array(color, dtype=np.float64)
    f = np.array(fondo, dtype=np.float64)
    d = c - f
    a = ((img.astype(np.float64) - f) @ d) / (d @ d)
    return np.clip(a, 0, 1)


def medidas(a, x0, y0):
    import numpy as np

    m = a.sum()
    ys, xs = np.mgrid[0 : a.shape[0], 0 : a.shape[1]]
    cx = (a * xs).sum() / m + x0
    cy = (a * ys).sum() / m + y0
    col = np.cumsum(a.sum(axis=0)) / m
    fil = np.cumsum(a.sum(axis=1)) / m
    izq = np.searchsorted(col, 0.002) + x0
    der = np.searchsorted(col, 0.998) + x0
    arr = np.searchsorted(fil, 0.002) + y0
    aba = np.searchsorted(fil, 0.998) + y0
    return {"masa": float(m), "cx": float(cx), "cy": float(cy), "izq": int(izq), "der": int(der), "arr": int(arr), "aba": int(aba)}


def corrimiento(pr, pm, rango=3.0, paso=0.02):
    """Cuánto hay que correr el perfil `pm` para que calce con `pr` (px, con decimales): el mínimo
    de la suma de diferencias al cuadrado, corriendo con interpolación lineal."""
    import numpy as np

    idx = np.arange(len(pr), dtype=np.float64)
    mejor, mejor_d = 0.0, None
    for d in np.arange(-rango, rango + paso / 2, paso):
        movido = np.interp(idx + d, idx, pm, left=0, right=0)
        e = float(((movido - pr) ** 2).sum())
        if mejor_d is None or e < mejor_d:
            mejor, mejor_d = float(d), e
    return mejor  # positivo: Manim está más abajo / más a la derecha que Remotion


def comparar(remotion_png: Path, manim_png: Path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    R = np.asarray(Image.open(remotion_png).convert("RGB")).astype(np.int16)
    M = np.asarray(Image.open(manim_png).convert("RGB")).astype(np.int16)
    tinta = _hex(COLOR["tinta"])
    REVISION.mkdir(parents=True, exist_ok=True)
    fuente = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 18)
    filas = []
    segoe = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 1000)
    for i, m in enumerate(MUESTRAS):
        tam, x, y = m["tam"], m["x"], m["y"]
        y0, y1 = int(y - 0.95 * tam), int(y + 0.75 * tam)
        avance = segoe.getlength(m["texto"]) / 1000 * tam  # aproximado (sin kerning): solo para recortar
        if m["alinear"] == "izq":
            x0, x1 = x - 16, int(x + avance + 16)
        elif m["alinear"] == "der":
            x0, x1 = int(x - avance - 16), x + 16
        else:
            x0, x1 = int(x - avance / 2 - 16), int(x + avance / 2 + 16)
        x0, x1 = max(0, x0), min(1920, x1)
        fondo = tinta
        if any(abs(b["cx"] - x) < b["ancho"] / 2 and abs(b["cy"] - y) < b["alto"] / 2 for b in BLOQUES):
            fondo = R[y0 + 2, x0 + 2].tolist()  # el relleno del bloque (no se toca con el texto)
        col = _hex(COLOR[m["color"]])
        r, mm = R[y0:y1, x0:x1], M[y0:y1, x0:x1]
        ar, am = cobertura(r, col, fondo), cobertura(mm, col, fondo)
        mr, mn = medidas(ar, x0, y0), medidas(am, x0, y0)
        llenos = (ar > 0.98) & (am > 0.98)
        color_r = r[ar > 0.98].mean(axis=0) if (ar > 0.98).any() else [0, 0, 0]
        color_m = mm[am > 0.98].mean(axis=0) if (am > 0.98).any() else [0, 0, 0]
        dif = np.abs(r - mm).max(axis=2)
        iou = float(((ar > 0.5) & (am > 0.5)).sum() / max(1, ((ar > 0.5) | (am > 0.5)).sum()))
        fila = {
            "muestra": i, "texto": m["texto"], "tam": tam, "color": m["color"], "alinear": m["alinear"],
            "dx_centro": mn["cx"] - mr["cx"], "dy_centro": mn["cy"] - mr["cy"],
            # corrimiento que mejor calza los perfiles de filas y de columnas (no depende del peso)
            "dy": corrimiento(ar.sum(axis=1), am.sum(axis=1)), "dx": corrimiento(ar.sum(axis=0), am.sum(axis=0)),
            "ancho_r": mr["der"] - mr["izq"], "ancho_m": mn["der"] - mn["izq"],
            "alto_r": mr["aba"] - mr["arr"], "alto_m": mn["aba"] - mn["arr"],
            "izq_r": mr["izq"], "izq_m": mn["izq"], "der_r": mr["der"], "der_m": mn["der"],
            "arr_r": mr["arr"], "arr_m": mn["arr"], "aba_r": mr["aba"], "aba_m": mn["aba"],
            "masa": mn["masa"] / mr["masa"] - 1, "iou": iou,
            "color_r": [round(float(v), 1) for v in color_r], "color_m": [round(float(v), 1) for v in color_m],
            "llenos": int(llenos.sum()), "dif_max": int(dif.max()), "dif_media": float(dif.mean()),
        }
        filas.append(fila)
        # Recorte lado a lado (arriba Remotion, en el medio Manim, abajo la diferencia ×4).
        h = y1 - y0
        lienzo = Image.new("RGB", (x1 - x0 + 160, 3 * h + 20), (233, 233, 236))
        d = ImageDraw.Draw(lienzo)
        lienzo.paste(Image.fromarray(r.astype(np.uint8)), (150, 0))
        lienzo.paste(Image.fromarray(mm.astype(np.uint8)), (150, h + 10))
        lienzo.paste(Image.fromarray(np.clip(dif * 4, 0, 255).astype(np.uint8)), (150, 2 * h + 20))
        for k, rot in enumerate(("Remotion", "Manim", "dif. x4")):
            d.text((8, k * (h + 10) + h // 2 - 10), rot, fill=(17, 17, 20), font=fuente)
        lienzo.save(REVISION / f"muestra_{i:02d}.png")
    # Los bloques: el recorte entero.
    bloques = []
    for j, b in enumerate(BLOQUES):
        x0, y0 = b["cx"] - b["ancho"] // 2 - 6, b["cy"] - b["alto"] // 2 - 6
        x1, y1 = b["cx"] + b["ancho"] // 2 + 6, b["cy"] + b["alto"] // 2 + 6
        r, mm = R[y0:y1, x0:x1], M[y0:y1, x0:x1]
        dif = np.abs(r - mm).max(axis=2)
        # El relleno: la mediana de una franja interior sin texto.
        rel_r = np.median(R[y0 + 20 : y0 + 26, x0 + 40 : x1 - 40].reshape(-1, 3), axis=0)
        rel_m = np.median(M[y0 + 20 : y0 + 26, x0 + 40 : x1 - 40].reshape(-1, 3), axis=0)
        bloques.append({"bloque": j, "dif_max": int(dif.max()), "dif_media": float(dif.mean()),
                        "px_dif_mas_de_8": int((dif > 8).sum()), "relleno_r": rel_r.tolist(), "relleno_m": rel_m.tolist()})
        h, w = y1 - y0, x1 - x0
        lienzo = Image.new("RGB", (3 * w + 40, h), (233, 233, 236))
        lienzo.paste(Image.fromarray(r.astype(np.uint8)), (0, 0))
        lienzo.paste(Image.fromarray(mm.astype(np.uint8)), (w + 20, 0))
        lienzo.paste(Image.fromarray(np.clip(dif * 4, 0, 255).astype(np.uint8)), (2 * w + 40, 0))
        lienzo.save(REVISION / f"bloque_{j}.png")
    return filas, bloques


def informe(filas, bloques):
    print("\nmuestra                                   px  color  alin | dx    dy    | ancho R/M   | alto R/M  | tinta  | IoU   | lleno R -> M              | dif máx/media")
    for f in filas:
        print(f"{f['muestra']:2d} {f['texto'][:36]:<36} {f['tam']:4d} {f['color']:<6} {f['alinear']:<6}| "
              f"{f['dx']:+5.2f} {f['dy']:+5.2f} | {f['ancho_r']:5d}/{f['ancho_m']:<5d} | {f['alto_r']:4d}/{f['alto_m']:<4d} | "
              f"{f['masa'] * 100:+5.1f}% | {f['iou']:.3f} | {f['color_r']} -> {f['color_m']} | {f['dif_max']}/{f['dif_media']:.2f}")
    for b in bloques:
        print(f"bloque {b['bloque']}: dif máx {b['dif_max']}, media {b['dif_media']:.3f}, {b['px_dif_mas_de_8']} px con más de 8; "
              f"relleno R {b['relleno_r']} M {b['relleno_m']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    TMP.mkdir(parents=True, exist_ok=True)
    muestras_json = TMP / "muestras.json"
    remotion_png = TMP / "remotion.png"
    manim_png = None
    entorno = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    if "--solo-comparar" not in sys.argv:
        muestras_json.write_text(json.dumps({"muestras": MUESTRAS, "bloques": BLOQUES}, ensure_ascii=False, indent=1), encoding="utf-8")
        if "--sin-remotion" not in sys.argv or not remotion_png.exists():
            subprocess.run(["node", str(RAIZ / "remotion" / "calibrar_manim.mjs"), str(muestras_json), str(remotion_png)], check=True, cwd=RAIZ)
        subprocess.run([sys.executable, "-m", "manim", "render", "-s", "-v", "WARNING", "--progress_bar", "none",
                        str(AQUI / "calibrar.py"), "CalibracionManim"], check=True, cwd=RAIZ, env=entorno)
    candidatos = sorted((RAIZ / "render" / "manim" / "images" / "calibrar").glob("CalibracionManim*.png"), key=lambda p: p.stat().st_mtime)
    manim_png = candidatos[-1]
    filas, bloques = comparar(remotion_png, manim_png)
    (TMP / "resultado.json").write_text(json.dumps({"muestras": filas, "bloques": bloques}, ensure_ascii=False, indent=1), encoding="utf-8")
    informe(filas, bloques)
    print(f"\nRecortes: {REVISION.relative_to(RAIZ).as_posix()}/  ·  cuadros: {remotion_png.relative_to(RAIZ).as_posix()}, {manim_png.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
