"""Prueba de punta a punta del armado con un deck SINTÉTICO (no toca render/ ni salida/).

Arma en .tmp/armado/prueba/ un deck.json falso y los videos de sus pasos, con
las mismas convenciones que los motores: render/pasos/<ID>/<ID>_<k>.mp4,
1920x1080, 30 cuadros/s, la receta de frontera (QP 16, cuadro clave al final,
BT.709) y el primer cuadro de cada paso idéntico al último del anterior.

    D01  2 pasos  sin campo «entrada»; arranca en tinta, así que el fundido por defecto no hace falta
    D02  3 pasos  sin campo «entrada» y no arranca donde terminó D01: fundido de 0,4 s por defecto; ding en el paso 2
    D03  1 paso   {"tipo": "puertas", "duracion_s": 1.05}; ding a los 2,05 s del paso (1 s después de abrirse)
    D04  1 paso   {"tipo": "continuo"}: arranca en el último cuadro de D03
    A1   2 pasos  respaldo; "fundido 0,4 desde D03" (en texto)

Como en remotion/lib/deck.mjs, la duracion_animacion_s del paso 1 incluye la
transición (el video propio dura eso menos la entrada) y el ding cuenta desde
que empieza el paso entero.

Después corre armar.py con --deck/--render/--salida apuntando ahí:
    .venv/Scripts/python.exe armar/prueba_armado.py            genera y corre «todo --sin-render»
    .venv/Scripts/python.exe armar/prueba_armado.py --solo-generar
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import deck as D  # noqa: E402
import videos as V  # noqa: E402

RAIZ = D.RAIZ
BASE = RAIZ / ".tmp" / "armado" / "prueba"
W, H = D.ANCHO, D.ALTO
TINTA = D.TINTA
HUESO = (245, 247, 255)
GRIS = (154, 163, 184)
AMBAR = (255, 181, 71)
ACERO = (26, 34, 48)
ACERO2 = (42, 52, 70)
ROJO = (255, 92, 92)
F_TIT = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 120)
F_72 = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 72)
F_60 = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 60)
F_49 = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 49)
F_200 = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 220)

# (id, sección, [(segundos del video propio, ding en s desde que empieza el paso entero, o None)],
#  color, entrada (o None), segundos de la entrada que van delante del paso 1, visual)
DIAPOS = [
    ("D01", "principal", [(2.0, None), (1.5, None)], AMBAR, None, 0.0, "Entra desde tinta (es el primer video)."),
    ("D02", "principal", [(1.6, None), (3.0, 1.5), (1.2, None)], (120, 200, 255), None, 0.4,
     "Entra desde el último cuadro de D01 (fundido de 0,4 s). Animación sintética."),
    ("D03", "principal", [(2.4, 2.05)], ROJO, {"tipo": "puertas", "duracion_s": 1.05}, 1.05,
     "Entra desde el último cuadro de D02, con las PUERTAS de capítulo."),
    ("D04", "principal", [(1.5, None)], (184, 140, 255), {"tipo": "continuo"}, 0.0, "Entra desde el último cuadro de D03."),
    ("A1", "respaldo", [(1.0, None), (1.2, None)], GRIS, "fundido 0,4 desde D03", 0.4,
     "Entra desde el último cuadro de D03 (fundido de 0,4 s)."),
]


def ease(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def dibujar(ident, color, k, n_pasos, t, dur, ding):
    """Un cuadro del paso k (1..n) en el segundo t de su animación de dur segundos."""
    im = Image.new("RGB", (W, H), TINTA)
    d = ImageDraw.Draw(im)
    # marca de agua sintética (no es la de nemaxyz: es un rótulo de prueba)
    d.text((67, 38), "prueba del armado", font=F_49, fill=(90, 96, 110))
    # lo de los pasos anteriores, ya quieto
    for j in range(1, k):
        d.rounded_rectangle([140, 300 + (j - 1) * 150, 140 + 900, 300 + (j - 1) * 150 + 110], radius=18, fill=ACERO2)
        d.text((180, 312 + (j - 1) * 150), f"{ident} · paso {j} de {n_pasos}", font=F_60, fill=HUESO)
    # lo nuevo de este paso: una barra que entra y se llena, quieta los últimos 0,3 s
    p = ease(t / max(dur - 0.3, 0.01))
    y = 300 + (k - 1) * 150
    x1 = 140 + int(900 * p)
    d.rounded_rectangle([140, y, max(141, x1), y + 110], radius=18, fill=color)
    if p > 0.35:
        d.text((180, y + 12), f"{ident} · paso {k} de {n_pasos}", font=F_60, fill=TINTA if p > 0.99 else HUESO)
    # el número de diapositiva, grande, a la derecha
    d.text((1250, 260), ident, font=F_200, fill=color)
    if ding is not None:
        restante = max(0.0, ding - t)
        d.text((1250, 560), f"{restante:0.1f}".replace(".", ","), font=F_TIT, fill=AMBAR)
        if t >= ding:
            d.text((1250, 720), "ding", font=F_72, fill=AMBAR)
    d.text((140, 980), f"{ident}.{k}", font=F_49, fill=GRIS)
    return im


def generar(base: Path) -> Path:
    if base.exists():
        shutil.rmtree(base)
    render = base / "render"
    diapos_json = []
    ultimo_de = {}
    for ident, seccion, pasos, color, entrada, transicion, visual in DIAPOS:
        n = len(pasos)
        pasos_json = []
        anterior_ultimo = None
        for k, (dur, ding) in enumerate(pasos, start=1):
            delante = transicion if k == 1 else 0.0   # lo que la transición ocupa del paso entero
            cuadros = int(round(dur * D.FPS)) + 1  # se solapan en un cuadro con el anterior
            ims = []
            for i in range(cuadros):
                t = i / D.FPS
                if k == 1 and ident == "D04" and i == 0:
                    ims.append(ultimo_de["D03"])     # continuo: arranca en el último cuadro de D03
                    continue
                if k > 1 and i == 0:
                    ims.append(anterior_ultimo)
                    continue
                ims.append(dibujar(ident, color, k, n, t, dur, None if ding is None else ding - delante))
            if ident == "D01" and k == 1:
                ims[0] = Image.new("RGB", (W, H), TINTA)  # la portada arranca en tinta
            destino = render / "pasos" / ident / f"{ident}_{k}.mp4"
            V.codificar_rgb((im.tobytes() for im in ims), destino)
            anterior_ultimo = ims[-1]
            notas = {
                ("D01", 1): "[Quieta mientras entra la gente.] Hola. Esta es la primera nota, con acentos: ñandú, acción, ¿qué?",
                ("D01", 2): "Segunda: el video arrancó solo y quedó quieto. [CLIC]",
                ("D02", 1): "Entra con un fundido por defecto. [PAUSA.]",
                ("D02", 2): "[Silencio durante el viaje.] Ding a los 1,5 s del paso. [Al «ding»: mano arriba.]",
                ("D02", 3): "Si sobra tiempo, 8 + Enter va al respaldo A1.",
                ("D03", 1): "Puertas de capítulo, y el ding 1 s después de que se abren (2,05 s desde el clic).",
                ("D04", 1): "Arranca donde terminó D03: no hace falta transición. Para volver al principio, 1 + Enter.",
                ("A1", 1): "Respaldo: entra con un fundido desde D03.",
                ("A1", 2): "Último paso del respaldo. Para volver, 7 + Enter.",
            }[(ident, k)]
            pasos_json.append({
                "texto_pantalla": [f"{ident} · paso {k} de {n}"], "visual": visual if k == 1 else "Animación sintética.",
                "notas": notas, "fuente": "Prueba sintética del armado." if (ident, k) == ("D02", 1) else None,
                "recortable": "todo (−5 s)" if (ident, k) == ("D02", 3) else None,
                "segundos_habla": 5.0, "duracion_animacion_s": round(dur + delante, 3),
                "audio": f"ding:{ding}" if ding is not None else None,
            })
        ultimo_de[ident] = anterior_ultimo
        dj = {"id": ident, "nombre": f"Prueba{ident}", "titulo": f"Diapositiva de prueba {ident}", "seccion": seccion,
              "motor": "sintetico", "piso": None, "objetivo": "Probar el armado.", "pasos": pasos_json}
        if entrada is not None:
            dj["entrada"] = entrada
        diapos_json.append(dj)
    deck = {
        "titulo": "Cómo hacer tu elevator pitch", "subtitulo": "Prueba sintética del armado", "evento": "prueba",
        "orador": "Nicolás Mejía (nemaxyz)", "diapositivas": diapos_json,
        "fuentes": [
            {"dato": "[D02.1] Un dato con «comillas», un 50 % y un #numeral.", "fuente": "Fuente de prueba",
             "url": "https://example.com/ruta?a=1&b=2#parte", "fecha": "consultado el 23-oct-2026"},
            {"dato": "[D03] νῆμα (nêma) quiere decir «hilo».", "fuente": "Wiktionary, νῆμα",
             "url": "https://en.wiktionary.org/wiki/%CE%BD%E1%BF%86%CE%BC%CE%B1", "fecha": "consultado el 22-oct-2026"},
            {"dato": "[todos] Íconos Font Awesome Free (solid), licencia CC BY 4.0.", "fuente": "Font Awesome",
             "url": "https://fontawesome.com/license/free", "fecha": "consultado el 22-oct-2026"},
        ],
    }
    ruta = base / "deck.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(deck, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--solo-generar", action="store_true")
    ap.add_argument("--show", action="store_true", help="verificar con la presentación en ventana")
    a = ap.parse_args()
    base = Path(a.base)
    t = time.time()
    deck = generar(base)
    print(f"deck sintético: {deck} ({time.time() - t:.1f} s)")
    if a.solo_generar:
        return 0
    cmd = [sys.executable, str(AQUI / "armar.py"), "todo", "--deck", str(deck), "--render", str(base / "render"),
           "--salida", str(base / "salida")] + (["--show"] if a.show else [])
    return subprocess.call(cmd, cwd=RAIZ)


if __name__ == "__main__":
    sys.exit(main())
