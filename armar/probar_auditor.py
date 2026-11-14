"""Valida el auditor de cuadros con casos rotos a propósito (validar el validador).

Fabrica en .tmp/auditor/pruebas/ una charla de juguete de 3 diapositivas y 6 pasos (T01 a
T03) dibujada con Pillow en la paleta de la charla (tinta, hueso, ámbar, rojo, gris, la
marca de agua con el lima al 72 %, el chip de piso, el reloj de 7 segmentos) y codificada
con la receta de entrega (armar/codificar_paso.py). Después arma un caso por defecto (una
frontera con salto, un paso que termina en movimiento, texto que pisa el margen, lima en el
contenido, un paso de menos...) y corre armar/auditar_cuadros.py sobre cada uno.

Cada caso dice qué errores y avisos tienen que salir (paso y regla). Pasa si salen esos y
ninguno más: así se prueba que cada regla dispara en su caso y que no dispara en el sano.

Uso:
    python armar/probar_auditor.py                 todos los casos
    python armar/probar_auditor.py sano lima_en_contenido
    python armar/probar_auditor.py --listar
    python armar/probar_auditor.py --rehacer       vuelve a codificar los videos (si no, usa el caché)
    python armar/probar_auditor.py --herramientas  además prueba extraer_cuadros.py y hoja_contactos.py

Sale con código 1 si algún caso falla.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import json
import shutil
import subprocess
import sys
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cuadros_comun as cc  # noqa: E402

RAIZ = cc.RAIZ
BASE = RAIZ / ".tmp" / "auditor" / "pruebas"
CACHE = BASE / "cache"
ARMAR = RAIZ / "armar"
PY = sys.executable

COL = {k: cc.hex_a_rgb(v) for k, v in cc.VALORES_GUION["colores"].items()}
TINTA, HUESO, AMBAR, ROJO, GRIS = COL["tinta"], COL["hueso"], COL["ambar"], COL["rojo"], COL["gris"]
ACERO2, VIDRIO, LIMA = COL["acero2"], COL["vidrio"], COL["marca"]

N_ANIM, N_QUIETO = 24, 15                 # 0,8 s de animación y 0,5 s quieto
DUR = round((N_ANIM + N_QUIETO) / cc.FPS, 2)  # 1,3 s
ORDEN = ["T01.1", "T02.1", "T02.2", "T02.3", "T03.1", "T03.2"]

_FUENTES = {}


def fuente(px, negrita=True):
    clave = (px, negrita)
    if clave not in _FUENTES:
        _FUENTES[clave] = ImageFont.truetype("C:/Windows/Fonts/" + ("segoeuib.ttf" if negrita else "segoeui.ttf"), px)
    return _FUENTES[clave]


def mezcla(c, a, base=TINTA):
    return tuple(int(round(base[i] + a * (c[i] - base[i]))) for i in range(3))


# ---------------------------------------------------------------------------
# Dibujo de la charla de juguete
# ---------------------------------------------------------------------------

def siete(d, x, y, alto, ancho, grosor, encendidos, color, apagado=None):
    """Un dígito de 7 segmentos (a arriba, b y c a la derecha, d abajo, e y f a la izquierda, g al medio)."""
    m = alto // 2
    segs = {
        "a": (x + grosor, y, x + ancho - grosor, y + grosor),
        "b": (x + ancho - grosor, y + grosor, x + ancho, y + m),
        "c": (x + ancho - grosor, y + m, x + ancho, y + alto - grosor),
        "d": (x + grosor, y + alto - grosor, x + ancho - grosor, y + alto),
        "e": (x, y + m, x + grosor, y + alto - grosor),
        "f": (x, y + grosor, x + grosor, y + m),
        "g": (x + grosor, y + m - grosor // 2, x + ancho - grosor, y + m + grosor // 2),
    }
    for k, r in segs.items():
        if k in encendidos:
            d.rectangle((r[0], r[1], r[2] - 1, r[3] - 1), fill=color)
        elif apagado:
            d.rectangle((r[0], r[1], r[2] - 1, r[3] - 1), fill=apagado)


_MARCAS = {}


def marca_rgba(alfa=0.72, dx=0) -> Image.Image:
    """La marca de agua de juguete: N de un trazo en lima y «nemaxyz» en hueso, al 72 %,
    dentro de x 67-300, y 38-86 (la zona del guion)."""
    clave = (alfa, dx)
    if clave not in _MARCAS:
        capa = Image.new("RGBA", (cc.ANCHO, cc.ALTO), (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        a = int(round(255 * alfa))
        d.line([(71 + dx, 82), (71 + dx, 43), (100 + dx, 82), (100 + dx, 43)], fill=LIMA + (a,), width=5)
        d.text((114 + dx, 34), "nemaxyz", font=fuente(34), fill=HUESO + (a,))
        _MARCAS[clave] = capa
    return _MARCAS[clave]


def componer(im, capa):
    im.paste(Image.alpha_composite(im.convert("RGBA"), capa).convert("RGB"))


def el_marco(im, d, p):
    d.rectangle((170, 230, 730, 950), outline=mezcla(HUESO, 0.25), width=4)


def el_titulo(im, d, p):
    d.text((860, 280), "Prueba del", font=fuente(96), fill=HUESO)
    d.text((860, 400), "auditor", font=fuente(110), fill=AMBAR)


def el_pie_marca(im, d, p):
    d.line([(864, 1008), (864, 974), (889, 1008), (889, 974)], fill=LIMA, width=5)
    d.text((904, 962), "nemaxyz · Prueba", font=fuente(40), fill=HUESO)


def el_marca(im, d, p):
    componer(im, marca_rgba(p.get("alfa", 0.72), p.get("dx", 0)))


def el_chip(im, d, p):
    d.rectangle((1721, 38, 1852, 121), fill=VIDRIO, outline=ACERO2, width=2)
    d.polygon([(1741, 94), (1753, 70), (1765, 94)], fill=AMBAR)
    siete(d, 1792, 52, 56, 34, 7, p.get("segmentos", "bc"), AMBAR, mezcla(AMBAR, 0.08))


def chip_rgba(segmentos="bc") -> Image.Image:
    """El chip de juguete en una capa transparente (opaco: compuesto sobre el cuadro da lo mismo
    que dibujarlo encima)."""
    capa = Image.new("RGBA", (cc.ANCHO, cc.ALTO), (0, 0, 0, 0))
    el_chip(capa, ImageDraw.Draw(capa), {"segmentos": segmentos})
    return capa


def escribir_assets(carpeta: Path, forma: str):
    """Piezas de juguete en diseno/assets/: «cuadro» = marca_agua.png de 1920x1080, sin manifiesto;
    «manifiesto» = recortes transparentes en su zona reservada más assets.json, como los deja
    remotion/generar_assets.mjs; «manifiesto_chip7» = lo mismo, con el chip dibujado con un 7."""
    if forma == "cuadro":
        marca_rgba().save(carpeta / "marca_agua.png")
        return
    piezas = {"marca_agua": ((56, 28, 324, 96), marca_rgba()),
              "chip_piso_1": ((1713, 30, 1861, 130), chip_rgba("abc" if forma == "manifiesto_chip7" else "bc"))}
    manifiesto = {"_doc": "Piezas de prueba del auditor.", "piezas": {}}
    for nombre, (r, capa) in piezas.items():
        capa.crop(r).save(carpeta / f"{nombre}.png")
        manifiesto["piezas"][nombre] = {"x": r[0], "y": r[1], "ancho": r[2] - r[0], "alto": r[3] - r[1],
                                        "archivos": {"transparente": f"{nombre}.png"}}
    (carpeta / "assets.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")


def el_frase(im, d, p):
    d.text((160, 220), "Piso 1: la frase", font=fuente(72), fill=HUESO)


def el_plantilla(im, d, p):
    f = fuente(60)
    x = 160
    for trozo, col in (("Ayudamos a ", HUESO), ("X", AMBAR), (" a ", HUESO), ("Y", AMBAR), (" haciendo ", HUESO),
                       ("Z", AMBAR), (".", HUESO)):
        d.text((x, 380), trozo, font=f, fill=col)
        x += d.textlength(trozo, font=f)


def el_rotulos(im, d, p):
    d.text((160, 500), "para quién · qué logran · cómo", font=fuente(49), fill=GRIS)


def el_tachado(im, d, p):
    f = fuente(60)
    d.text((160, 600), "reescribir", font=f, fill=ROJO)
    w = d.textlength("reescribir", font=f)
    d.line([(154, 648), (166 + w, 648)], fill=ROJO, width=6)


def el_pastilla(im, d, p):
    d.rounded_rectangle((900, 760, 1330, 860), radius=50, fill=TINTA, outline=AMBAR, width=5)
    d.line([(940, 812), (960, 832), (995, 790)], fill=AMBAR, width=7)
    d.text((1020, 768), "funcionó", font=fuente(60), fill=HUESO)


def el_pregunta(im, d, p):
    d.text((p.get("x", 160), 450), "¿Les alcanzó?", font=fuente(96), fill=HUESO)


def el_reloj(im, d, p):
    cx, cy = p.get("cx", 1500), p.get("cy", 520)
    siete(d, cx - 60, cy - 110, 220, 120, 22, "abcdef", AMBAR, mezcla(AMBAR, 0.08))


def el_tiempo(im, d, p):
    f = fuente(72)
    w = d.textlength("Tiempo.", font=f)
    d.text((1500 - w / 2, p.get("y", 730)), "Tiempo.", font=f, fill=HUESO)


def el_fuera_margen(im, d, p):
    d.text((1640, 860), "se sale del margen", font=fuente(60), fill=HUESO)


def el_lima_palabra(im, d, p):
    d.text((300, 840), "pitch", font=fuente(72), fill=LIMA)


def el_pegado(im, d, p):
    d.text((120, 74), "pegado a la marca", font=fuente(40), fill=GRIS)


ELEMENTOS = {
    "marco": el_marco, "titulo": el_titulo, "pie_marca": el_pie_marca, "marca": el_marca, "chip": el_chip,
    "frase": el_frase, "plantilla": el_plantilla, "rotulos": el_rotulos, "tachado": el_tachado,
    "pastilla": el_pastilla, "pregunta": el_pregunta, "reloj": el_reloj, "tiempo": el_tiempo,
    "fuera_margen": el_fuera_margen, "lima_palabra": el_lima_palabra, "pegado": el_pegado,
}

ESTADOS = {
    "T01.1": [["marco", {}], ["titulo", {}], ["pie_marca", {}]],
    "T02.1": [["marca", {}], ["chip", {}], ["frase", {}], ["plantilla", {}]],
    "T02.2": [["marca", {}], ["chip", {}], ["frase", {}], ["plantilla", {}], ["rotulos", {}], ["tachado", {}]],
    "T02.3": [["marca", {}], ["chip", {}], ["frase", {}], ["plantilla", {}], ["rotulos", {}], ["tachado", {}],
              ["pastilla", {}]],
    "T03.1": [["marca", {}], ["pregunta", {}]],
    "T03.2": [["marca", {}], ["pregunta", {}], ["reloj", {}], ["tiempo", {}]],
}


def pintar(elementos) -> np.ndarray:
    im = Image.new("RGB", (cc.ANCHO, cc.ALTO), TINTA)
    d = ImageDraw.Draw(im)
    for nombre, p in elementos:
        ELEMENTOS[nombre](im, d, p)
    return np.asarray(im)


def mezclar(a, b, e):
    if e <= 0:
        return a
    if e >= 1:
        return b
    return (a.astype(np.float32) * (1 - e) + b.astype(np.float32) * e + 0.5).astype(np.uint8)


def cuadros_paso(clave, inicio, estado, mods):
    """Los cuadros de un paso: fundido de `inicio` al estado final en N_ANIM cuadros y
    N_QUIETO cuadros quietos. El primero es `inicio` tal cual (frontera exacta)."""
    n_anim = mods.get("n_anim", {}).get(clave, N_ANIM)
    n = n_anim + N_QUIETO
    fin = pintar(estado)
    mov = mods.get("movimiento", {}).get(clave)
    flash = mods.get("flash", {}).get(clave)
    cuadros = []
    for i in range(n):
        t = min(1.0, i / (n_anim - 1))
        e = t * t * (3 - 2 * t)
        objetivo = fin
        if mov:  # un elemento que se mueve hasta el último cuadro
            nombre, param, desde, hasta = mov
            est = copy.deepcopy(estado)
            for el in est:
                if el[0] == nombre:
                    el[1][param] = round(desde + (hasta - desde) * i / (n - 1))
            objetivo = pintar(est)
        if flash and flash[1] <= i < flash[2]:
            objetivo = pintar(estado + [[flash[0], {}]])
        cuadros.append(mezclar(inicio, objetivo, e))
    salto = mods.get("salto", {}).get(clave)
    if salto:
        cuadros[0] = np.roll(inicio, salto, axis=1)
    return cuadros


def codificar_con_cache(cuadros, destino: Path, fps=cc.FPS, crf=None, rehacer=False) -> str:
    h = hashlib.sha1(f"{fps}|{crf}|{N_ANIM}|{N_QUIETO}".encode())
    for c in cuadros:
        h.update(c.tobytes())
    clave = h.hexdigest()[:16]
    cache = CACHE / f"{clave}.mp4"
    if rehacer or not cache.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = CACHE / f"{clave}.parcial.mp4"
        if crf is None:
            cc.codificar_cuadros(cuadros, tmp, fps=fps)
        else:  # sin la receta: CRF común, sin cuadro clave forzado al final
            proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                                     f"{cc.ANCHO}x{cc.ALTO}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset",
                                     "medium", "-crf", str(crf), "-vf", "zscale=matrix=709:range=limited:primariesin=709"
                                     ":primaries=709:transferin=709:transfer=709", "-pix_fmt", "yuv420p",
                                     "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                                     "-color_range", "tv", "-an", "-movflags", "+faststart", str(tmp)],
                                    stdin=subprocess.PIPE)
            for c in cuadros:
                proc.stdin.write(c.tobytes())
            proc.stdin.close()
            if proc.wait():
                raise RuntimeError("ffmpeg falló")
        tmp.replace(cache)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cache, destino)
    return clave


def fabricar(carpeta: Path, estados=None, mods=None, rehacer=False):
    """Los seis pasos en carpeta/<ID>/<ID>_<k>.mp4."""
    estados = estados or ESTADOS
    mods = mods or {}
    prev = None
    for clave in ORDEN:
        if clave in mods.get("inicio_propio", {}):  # no arranca donde terminó el anterior
            inicio = pintar(mods["inicio_propio"][clave])
        elif prev is None:
            inicio = np.zeros((cc.ALTO, cc.ANCHO, 3), np.uint8) if mods.get("inicio_negro") else pintar([])
        else:
            inicio = prev
        cuadros = cuadros_paso(clave, inicio, estados[clave], mods)
        id_, k = clave.split(".")
        codificar_con_cache(cuadros, carpeta / id_ / f"{id_}_{k}.mp4", fps=mods.get("fps", {}).get(clave, cc.FPS),
                            crf=mods.get("crf", {}).get(clave), rehacer=rehacer)
        prev = cuadros[-1]
        del cuadros


def estados_con(quitar=(), agregar=(), cambiar=()):
    """Copia de ESTADOS con cambios: quitar [(paso, elemento)], agregar [(paso, elemento, params)],
    cambiar [(paso, elemento, params)]."""
    e = copy.deepcopy(ESTADOS)
    for paso, nombre in quitar:
        e[paso] = [x for x in e[paso] if x[0] != nombre]
    for paso, nombre, p in agregar:
        e[paso].append([nombre, dict(p)])
    for paso, nombre, p in cambiar:
        for x in e[paso]:
            if x[0] == nombre:
                x[1].update(p)
    return e


# ---------------------------------------------------------------------------
# Deck, reglas, tokens y audio de juguete
# ---------------------------------------------------------------------------

def paso_deck(visual, audio=None, dur=DUR):
    return {"texto_pantalla": [], "visual": visual, "notas": "Nota de prueba para el auditor de cuadros.",
            "fuente": None, "recortable": None, "segundos_habla": 0.0, "duracion_animacion_s": dur, "audio": audio}


def deck_prueba(duraciones=None, entradas=None):
    duraciones = duraciones or {}
    d = lambda c: duraciones.get(c, DUR)  # noqa: E731
    deck = {
        "titulo": "Prueba del auditor",
        "diapositivas": [
            {"id": "T01", "nombre": "Portada", "titulo": "Portada de prueba", "seccion": "principal",
             "motor": "remotion", "piso": None,
             "pasos": [paso_deck("Entra desde tinta (es el primer video). Animación de prueba.", dur=d("T01.1"))]},
            {"id": "T02", "nombre": "Piso", "titulo": "Piso 1 de prueba", "seccion": "principal", "motor": "manim",
             "piso": 1,
             "pasos": [paso_deck("Entra desde el último cuadro de T01. Animación.", dur=d("T02.1")),
                       paso_deck("Animación.", dur=d("T02.2")), paso_deck("Animación.", dur=d("T02.3"))]},
            {"id": "T03", "nombre": "Reloj", "titulo": "Reloj de prueba", "seccion": "respaldo", "motor": "remotion",
             "piso": None,
             "pasos": [paso_deck("Entra desde el último cuadro de T02. Animación.", dur=d("T03.1")),
                       paso_deck("Animación.", audio="ding:1.0", dur=d("T03.2"))]},
        ],
    }
    for diapo in deck["diapositivas"]:
        if entradas and diapo["id"] in entradas:
            diapo["entrada"] = entradas[diapo["id"]]
    return deck


REGLAS_PRUEBA = {
    "pasos_sin_marca_de_agua": ["T01"],
    "pasos_con_reloj_grande": ["T03.2"],
    "pasos_de_marca": ["T01.1"],
    "excepciones": [],
}

# La forma de diseno/tokens.json (23-oct-2026), con la lista de pasos sin marca de la charla de juguete.
TOKENS_PRUEBA = {
    "color": {"tinta": {"hex": "#070A0F"}, "hueso": {"hex": "#F5F7FF"}, "ambar": {"hex": "#FFB547"},
              "marca": {"hex": "#B8FF3C"}},
    "opacidad": {"marca_agua": 0.72},
    "reticula": {
        "margen_x": 67, "margen_y": 38,
        "zona_segura": {"x0": 67, "y0": 38, "x1": 1853, "y1": 1042},
        "marca_agua": {"x": 67, "y": 38, "alto_isotipo": 48, "x1": 300, "y1": 86,
                       "zona": {"x": 56, "y": 28, "ancho": 268, "alto": 68}},
        "chip_piso": {"x": 1721, "y": 38, "ancho": 132, "alto": 84,
                      "zona": {"x": 1713, "y": 30, "ancho": 148, "alto": 100}},
        "reloj": {"cx": 1500, "cy": 520, "alto": 220, "luces_y": 670},
    },
    "persistentes": {"marca_agua_sin": ["T01"]},
    "pasos": {"respiro_s": 0.3},
    "transiciones": {"fundido": {"duracion_s": 0.4}, "puertas": {"duracion_s": 1.05}},
}

# Otra forma posible (si tokens.json cambia): la búsqueda flexible tiene que encontrar lo mismo.
TOKENS_OTRA_FORMA = {
    "colores": {"tinta": "#070A0F", "hueso": "#F5F7FF", "ambar": "#FFB547", "marca": "#B8FF3C"},
    "margenes": {"x": 67, "y": 38},
    "zonas": {
        "marca_agua": {"x": 67, "y": 38, "ancho": 233, "alto": 48},
        "chip": [1721, 38, 1853, 122],
        "reloj": {"centro": [1500, 520], "alto": 220},
    },
}


def escribir_wav(ruta: Path, dur: float, ding: float | None, sr=48000):
    """Silencio de `dur` segundos, con el ding (mi6 → do6, 0,4 s cada tono) a los `ding` segundos."""
    x = np.zeros(int(round(dur * sr)), np.float32)
    if ding is not None:
        for f0, t0 in ((1318.5, 0.0), (1046.5, 0.4)):
            i0 = int((ding + t0) * sr)
            m = int(0.4 * sr)
            tt = np.arange(m) / sr
            tono = (0.5 * np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 5)).astype(np.float32)
            seg = x[i0:i0 + m]
            seg += tono[:len(seg)]
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def hacer_finales(origen: Path, destino: Path, ding: float):
    """Videos «finales» de juguete: recodificados con CRF 18 (sin la receta de frontera) y con
    una pista de audio (silencio, y el ding en T03.2)."""
    for clave in ORDEN:
        id_, k = clave.split(".")
        ent = origen / id_ / f"{id_}_{k}.mp4"
        sal = destino / id_ / f"{id_}_{k}.mp4"
        sal.parent.mkdir(parents=True, exist_ok=True)
        wav = destino / f"{id_}_{k}.wav"
        escribir_wav(wav, DUR, ding if clave == "T03.2" else None)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(sal)], check=True)
        wav.unlink()


def retocar(video: Path, *args):
    """Rehace el MP4 sin tocar los cuadros (copia del video) con otras opciones."""
    tmp = video.with_name(video.stem + ".retoque.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), *args, str(tmp)], check=True)
    tmp.replace(video)


# ---------------------------------------------------------------------------
# Los casos
# ---------------------------------------------------------------------------

@dataclass
class Caso:
    nombre: str
    que: str
    errores: set = field(default_factory=set)
    avisos: set = field(default_factory=set)
    videos: str = "sano"                     # qué juego de videos usa
    reglas: dict | None = None
    deck: dict | None = None
    tokens: dict | None = None
    assets: str | None = None               # None, "cuadro", "manifiesto" o "manifiesto_chip7"
    args: list = field(default_factory=list)
    salida_esperada: int | None = None       # código de salida, si no es 0/1 según los errores
    comprobar: object = None                 # función extra (informe) -> lista de problemas


def comprobar_excepcion(paso, regla, estado=None):
    def f(inf):
        p = next((x for x in inf["pasos"] if x["paso"] == paso), None)
        if not p:
            return [f"el informe no tiene {paso}"]
        probs = []
        if not any(x.startswith(regla) for x in p["excepciones"]):
            probs.append(f"el informe no lista la excepción de {regla} en {paso}")
        if estado and p["estados"].get(regla) != estado:
            probs.append(f"{paso}: el estado de {regla} es {p['estados'].get(regla)!r} y se esperaba {estado!r}")
        return probs
    return f


def comprobar_tokens(reservada_marca, reservada_chip, sin_marca_de_tokens):
    def f(inf):
        dis = inf["diseno"]
        probs = []
        if not dis["tokens"]:
            probs.append("el informe dice que no leyó tokens.json")
        if "tokens" not in str(dis["origen"].get("margenes", "")):
            probs.append(f"los márgenes no salieron de tokens.json: {dis['origen'].get('margenes')}")
        if list(dis["marca_agua"]) != [67, 38, 300, 86]:
            probs.append(f"la marca de agua leída es {dis['marca_agua']}")
        if list(dis["marca_agua_reservada"]) != reservada_marca:
            probs.append(f"la zona reservada de la marca leída es {dis['marca_agua_reservada']}")
        if list(dis["chip_reservada"]) != reservada_chip:
            probs.append(f"la zona reservada del chip leída es {dis['chip_reservada']}")
        if [dis["reloj"]["cx"], dis["reloj"]["cy"], dis["reloj"]["alto"]] != [1500, 520, 220]:
            probs.append(f"el reloj leído es {dis['reloj']}")
        origen = dis["sin_marca_de_agua_origen"]
        if ("tokens.json" in origen) != sin_marca_de_tokens or ("reglas.json" in origen) == sin_marca_de_tokens:
            probs.append(f"la lista de pasos sin marca salió de {origen}")
        return probs
    return f


def comprobar_sin_notas_de_assets(inf):
    return [f"nota sobre assets: {n['mensaje']}" for n in inf["notas"] if "assets" in n["mensaje"]]


def comprobar_quietud_medida(inf):
    p = next(x for x in inf["pasos"] if x["paso"] == "T02.1")
    q = p["info"].get("quieto_s", 0)
    return [] if q >= 0.45 else [f"T02.1 debería medir unos 0,5 s quieto y midió {q}"]


TODOS = {("T02.1", "frontera"), ("T02.2", "frontera"), ("T02.3", "frontera"), ("T03.1", "frontera"),
         ("T03.2", "frontera")}

CASOS = [
    Caso("sano", "la charla de juguete bien hecha: no dispara nada", comprobar=comprobar_quietud_medida),
    Caso("sano_con_tokens", "igual, leyendo márgenes, zonas y la lista sin marca de un tokens.json con la forma "
         "de diseno/tokens.json", tokens=TOKENS_PRUEBA,
         comprobar=comprobar_tokens([56, 28, 324, 96], [1713, 30, 1861, 130], True)),
    Caso("tokens_otra_forma", "tokens.json con otros nombres y otra forma: la búsqueda flexible lee lo mismo",
         tokens=TOKENS_OTRA_FORMA, comprobar=comprobar_tokens([47, 18, 320, 106], [1701, 18, 1873, 142], False)),
    Caso("tokens_margen_200", "tokens.json con márgenes de 200 px: lo que empieza en x 160-170 queda afuera",
         tokens={**TOKENS_PRUEBA, "reticula": {**TOKENS_PRUEBA["reticula"],
                                               "zona_segura": {"x0": 200, "y0": 38, "x1": 1720, "y1": 1042}}},
         errores={(c, "zona_segura") for c in ORDEN}),
    Caso("tokens_sin_marca_en_T02_2", "tokens.json dice que T02.2 no lleva marca de agua (y la lleva)",
         tokens={**TOKENS_PRUEBA, "persistentes": {"marca_agua_sin": ["T01", "T02.2"]}},
         errores={("T02.2", "zonas_reservadas"), ("T02.2", "lima")}),
    Caso("entrada_fundido", "T03 entra con un fundido de 0,4 s (campo «entrada»): T03.1 crudo arranca en su "
         "propio cuadro y dura 0,9 s", videos="entrada_propia",
         deck=deck_prueba(entradas={"T03": {"tipo": "fundido", "duracion_s": 0.4, "desde": "T02"}})),
    Caso("entrada_sin_declarar", "los mismos videos sin declarar la entrada: T03.1 no arranca donde terminó T02.3",
         videos="entrada_propia", errores={("T03.1", "frontera")}, avisos={("T03.1", "duracion")}),
    Caso("frontera_salto", "T02.2 arranca 8 px corrido respecto del final de T02.1",
         errores={("T02.2", "frontera")}, videos="salto"),
    Caso("frontera_sin_receta", "T02.2 codificado con CRF 18: fronteras iguales a la vista pero no idénticas",
         errores={("T02.2", "frontera"), ("T02.3", "frontera")}, videos="sin_receta"),
    Caso("termina_en_movimiento", "en T03.1 la pregunta se sigue moviendo hasta el último cuadro",
         errores={("T03.1", "quietud")}, videos="movimiento"),
    Caso("texto_en_margen", "en T03.2 un texto se sale por la derecha",
         errores={("T03.2", "zona_segura")}, videos="margen"),
    Caso("lima_en_contenido", "en T03.2 la palabra «pitch» en lima #B8FF3C",
         errores={("T03.2", "lima")}, avisos={("T03.2", "lima")}, videos="lima"),
    Caso("lima_solo_animacion", "en T02.2 aparece lima a mitad de la animación y se va",
         avisos={("T02.2", "lima")}, videos="flash"),
    Caso("paso_de_menos", "falta T02_3.mp4", errores={("T02", "pasos")}, videos="menos"),
    Caso("paso_de_mas", "sobra T03_3.mp4", errores={("T03", "pasos")}, videos="mas"),
    Caso("formato", "T01.1 etiquetado BT.601, T02.1 con audio y T02.3 a 25 fps (que además dura 0,26 s de más)",
         errores={("T01.1", "formato"), ("T02.1", "formato"), ("T02.3", "formato")},
         avisos={("T02.3", "duracion")}, videos="formato"),
    Caso("duracion_error", "deck.json pide 4 s para T02.1 y el video dura 1,3 s",
         errores={("T02.1", "duracion")}, deck=deck_prueba({"T02.1": 4.0})),
    Caso("duracion_aviso", "deck.json pide 1,5 s para T02.2 y el video dura 1,3 s",
         avisos={("T02.2", "duracion")}, deck=deck_prueba({"T02.2": 1.5})),
    Caso("primer_cuadro_negro", "la charla arranca desde negro puro y no desde la tinta",
         errores={("T01.1", "primer_cuadro")}, videos="negro"),
    Caso("falta_marca", "T02.2 sin marca de agua", errores={("T02.2", "zonas_reservadas")}, videos="sin_marca"),
    Caso("marca_atenuada", "en T02.2 la marca de agua al 45 % (la atenuó el Foco)",
         errores={("T02.2", "zonas_reservadas")}, videos="marca_tenue"),
    Caso("pegado_a_marca", "en T02.3 un texto a 3 px por debajo de la marca de agua",
         errores={("T02.3", "zonas_reservadas")}, videos="pegado"),
    Caso("falta_chip", "T02.2 sin el chip de piso", errores={("T02.2", "zonas_reservadas")}, videos="sin_chip"),
    Caso("chip_sobra", "T03.1 (sin piso) se quedó con el chip", avisos={("T03.1", "zonas_reservadas")},
         videos="chip_sobra"),
    Caso("reloj_corrido", "en T03.2 el reloj grande 40 px más abajo", errores={("T03.2", "zonas_reservadas")},
         videos="reloj_corrido"),
    Caso("reloj_tapado", "en T03.2 «Tiempo.» encima del reloj", errores={("T03.2", "zonas_reservadas")},
         videos="reloj_tapado"),
    Caso("marca_asset_sana", "con diseno/assets/marca_agua.png (1920x1080, sin manifiesto) igual a la dibujada",
         assets="cuadro", comprobar=comprobar_sin_notas_de_assets),
    Caso("marca_asset_corrida", "la marca dibujada 3 px a la derecha del PNG de diseno/assets/",
         errores={(c, "zonas_reservadas") for c in ORDEN[1:]}, videos="marca_corrida", assets="cuadro"),
    Caso("assets_manifiesto_sano", "con assets.json y los recortes de la marca y del chip en su zona reservada "
         "(la forma de remotion/generar_assets.mjs)", assets="manifiesto", comprobar=comprobar_sin_notas_de_assets),
    Caso("assets_manifiesto_corrida", "con assets.json; la marca dibujada 3 px corrida",
         errores={(c, "zonas_reservadas") for c in ORDEN[1:]}, videos="marca_corrida", assets="manifiesto"),
    Caso("assets_chip_distinto", "con assets.json; el chip de referencia tiene un 7 y el de los videos un 1",
         errores={("T02.1", "zonas_reservadas"), ("T02.2", "zonas_reservadas"), ("T02.3", "zonas_reservadas")},
         assets="manifiesto_chip7"),
    Caso("excepcion_margen", "el texto que se sale de T03.2, permitido con una excepción",
         videos="margen", reglas={**REGLAS_PRUEBA, "excepciones": [
             {"pasos": ["T03.2"], "regla": "zona_segura", "permitir": [[1800, 840, 1920, 960]],
              "motivo": "Prueba: el texto que se sale está permitido."}]},
         comprobar=comprobar_excepcion("T03.2", "zona_segura")),
    Caso("excepcion_omitir", "el movimiento final de T03.1, con la quietud exceptuada",
         videos="movimiento", reglas={**REGLAS_PRUEBA, "excepciones": [
             {"pasos": ["T03.1"], "regla": "quietud", "omitir": True, "motivo": "Prueba: se mueve a propósito."}]},
         comprobar=comprobar_excepcion("T03.1", "quietud", "exceptuada")),
    Caso("reglas_sin_motivo", "una excepción sin motivo: el auditor no arranca (código 2)",
         reglas={**REGLAS_PRUEBA, "excepciones": [{"pasos": ["T03.2"], "regla": "lima", "omitir": True}]},
         salida_esperada=2),
    Caso("final_sano", "videos finales (CRF 18 + audio, ding en su segundo) con --final",
         videos="final", args=["--final"]),
    Caso("final_ding_corrido", "el ding de T03.2 suena a los 0,4 s y deck.json lo pide a 1,0 s",
         errores={("T03.2", "audio")}, videos="final_ding", args=["--final"]),
    Caso("final_frontera_exacta", "los mismos videos finales con --tolerancia-frontera exacta",
         errores=TODOS, videos="final", args=["--final", "--tolerancia-frontera", "exacta"]),
]

JUEGOS = {
    "sano": {},
    "salto": {"mods": {"salto": {"T02.2": 8}}},
    "sin_receta": {"mods": {"crf": {"T02.2": 18}}},
    "movimiento": {"mods": {"movimiento": {"T03.1": ("pregunta", "x", 100, 160)}},
                   "estados": estados_con(cambiar=[("T03.1", "pregunta", {"x": 160})])},
    "margen": {"estados": estados_con(agregar=[("T03.2", "fuera_margen", {})])},
    "lima": {"estados": estados_con(agregar=[("T03.2", "lima_palabra", {})])},
    "flash": {"mods": {"flash": {"T02.2": ("lima_palabra", 8, 22)}}},
    "negro": {"mods": {"inicio_negro": True}},
    "sin_marca": {"estados": estados_con(quitar=[("T02.2", "marca")])},
    "marca_tenue": {"estados": estados_con(cambiar=[("T02.2", "marca", {"alfa": 0.45})])},
    "pegado": {"estados": estados_con(agregar=[("T02.3", "pegado", {})])},
    "sin_chip": {"estados": estados_con(quitar=[("T02.2", "chip")])},
    "chip_sobra": {"estados": estados_con(agregar=[("T03.1", "chip", {})])},
    "reloj_corrido": {"estados": estados_con(cambiar=[("T03.2", "reloj", {"cy": 560})])},
    "reloj_tapado": {"estados": estados_con(cambiar=[("T03.2", "tiempo", {"y": 560})])},
    "marca_corrida": {"estados": estados_con(cambiar=[(c, "marca", {"dx": 3}) for c in ORDEN[1:]])},
    "formato": {"mods": {"fps": {"T02.3": 25}}},
    "entrada_propia": {"mods": {"inicio_propio": {"T03.1": [["marca", {}]]}, "n_anim": {"T03.1": 12}}},
}


def preparar_juego(nombre: str, rehacer: bool) -> Path:
    carpeta = BASE / "videos" / nombre
    if nombre in ("menos", "mas"):
        base = preparar_juego("sano", rehacer)
        if carpeta.exists():
            shutil.rmtree(carpeta)
        shutil.copytree(base, carpeta)
        if nombre == "menos":
            (carpeta / "T02" / "T02_3.mp4").unlink()
        else:
            shutil.copyfile(carpeta / "T03" / "T03_2.mp4", carpeta / "T03" / "T03_3.mp4")
        return carpeta
    if nombre in ("final", "final_ding"):
        base = preparar_juego("sano", rehacer)
        if carpeta.exists() and not rehacer and (carpeta / "T03" / "T03_2.mp4").exists():
            return carpeta
        if carpeta.exists():
            shutil.rmtree(carpeta)
        hacer_finales(base, carpeta, 1.0 if nombre == "final" else 0.4)
        return carpeta
    j = JUEGOS[nombre]
    if carpeta.exists():
        shutil.rmtree(carpeta)
    fabricar(carpeta, j.get("estados"), j.get("mods"), rehacer)
    if nombre == "formato":
        retocar(carpeta / "T01" / "T01_1.mp4", "-c", "copy", "-bsf:v",
                "h264_metadata=colour_primaries=6:transfer_characteristics=6:matrix_coefficients=6",
                "-color_primaries", "smpte170m", "-color_trc", "smpte170m", "-colorspace", "smpte170m",
                "-movflags", "+faststart")
        retocar(carpeta / "T02" / "T02_1.mp4", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-map", "0:v",
                "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart")
    return carpeta


def correr_caso(caso: Caso, rehacer: bool) -> tuple:
    dir_caso = BASE / "casos" / caso.nombre
    if dir_caso.exists():
        shutil.rmtree(dir_caso)
    dir_caso.mkdir(parents=True)
    videos = preparar_juego(caso.videos, rehacer)
    deck = dir_caso / "deck.json"
    deck.write_text(json.dumps(caso.deck or deck_prueba(), ensure_ascii=False, indent=1), encoding="utf-8")
    reglas = dir_caso / "reglas.json"
    reglas.write_text(json.dumps(caso.reglas or REGLAS_PRUEBA, ensure_ascii=False, indent=1), encoding="utf-8")
    tokens = dir_caso / "tokens.json"
    if caso.tokens:
        tokens.write_text(json.dumps(caso.tokens, ensure_ascii=False, indent=1), encoding="utf-8")
    assets = dir_caso / "assets"
    assets.mkdir()
    if caso.assets:
        escribir_assets(assets, caso.assets)
    salida = dir_caso / "informe"
    cmd = [PY, str(ARMAR / "auditar_cuadros.py"), "--todos", "--deck", str(deck), "--guion", str(dir_caso / "sin_guion.md"),
           "--reglas", str(reglas), "--tokens", str(tokens), "--assets", str(assets), "--videos", str(videos),
           "--salida", str(salida), "--temporal", str(BASE / "tmp"), *caso.args]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    seg = time.time() - t0
    (dir_caso / "salida.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    problemas = []
    esperado = caso.salida_esperada if caso.salida_esperada is not None else (1 if caso.errores else 0)
    if r.returncode != esperado:
        problemas.append(f"código de salida {r.returncode}, se esperaba {esperado}"
                         + (f": {r.stderr.strip().splitlines()[-1]}" if r.stderr.strip() else ""))
    informe = salida / "auditoria_cuadros" if "--final" not in caso.args else salida / "auditoria_cuadros_final"
    js = informe.with_suffix(".json")
    if caso.salida_esperada == 2:
        if js.exists():
            problemas.append("escribió un informe con reglas inválidas")
        if "motivo" not in r.stderr:
            problemas.append(f"el mensaje no habla del motivo: {r.stderr.strip()[:200]}")
        return caso, problemas, seg, None
    if not js.exists():
        problemas.append(f"no escribió {js.name}")
        return caso, problemas, seg, None
    inf = json.loads(js.read_text(encoding="utf-8"))
    errores = {(h["paso"], h["regla"]): h["mensaje"] for h in inf["errores"]}
    avisos = {(h["paso"], h["regla"]): h["mensaje"] for h in inf["avisos"]}
    for e in sorted(caso.errores - set(errores)):
        problemas.append(f"NO DISPARÓ el error {e[0]} · {e[1]}")
    for a in sorted(caso.avisos - set(avisos)):
        problemas.append(f"NO DISPARÓ el aviso {a[0]} · {a[1]}")
    for e in sorted(set(errores) - caso.errores):
        problemas.append(f"disparó de más: error {e[0]} · {e[1]}: {errores[e]}")
    for a in sorted(set(avisos) - caso.avisos):
        problemas.append(f"disparó de más: aviso {a[0]} · {a[1]}: {avisos[a]}")
    if caso.comprobar:
        problemas += caso.comprobar(inf)
    return caso, problemas, seg, inf


def probar_herramientas() -> list:
    """extraer_cuadros.py y hoja_contactos.py sobre la charla de juguete sana."""
    problemas = []
    videos = preparar_juego("sano", False)
    caso = BASE / "casos" / "herramientas"
    if caso.exists():
        shutil.rmtree(caso)
    caso.mkdir(parents=True)
    deck = caso / "deck.json"
    deck.write_text(json.dumps(deck_prueba(), ensure_ascii=False, indent=1), encoding="utf-8")
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    cuadros = caso / "cuadros"
    r = subprocess.run([PY, str(ARMAR / "extraer_cuadros.py"), "--todos", "--deck", str(deck), "--videos", str(videos),
                        "--salida", str(cuadros)], capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode:
        problemas.append(f"extraer_cuadros.py salió con {r.returncode}: {r.stdout[-300:]} {r.stderr[-300:]}")
    for c in ORDEN:
        n = c.replace(".", "_")
        for cual in ("primero", "ultimo"):
            png = cuadros / f"{n}_{cual}.png"
            if not png.exists():
                problemas.append(f"extraer_cuadros.py no dejó {png.name}")
    # el primero de cada paso es el último del anterior (frontera exacta en la charla sana)
    for a, b in zip(ORDEN, ORDEN[1:]):
        ua = cc.abrir_png(cuadros / f"{a.replace('.', '_')}_ultimo.png")
        pb = cc.abrir_png(cuadros / f"{b.replace('.', '_')}_primero.png")
        if not np.array_equal(ua, pb):
            problemas.append(f"los PNG de {a} (último) y {b} (primero) no son idénticos")
    # al día: la segunda vez no saca nada
    r = subprocess.run([PY, str(ARMAR / "extraer_cuadros.py"), "--todos", "--deck", str(deck), "--videos", str(videos),
                        "--salida", str(cuadros)], capture_output=True, text=True, encoding="utf-8", env=env)
    if "0 extraídos, 6 al día" not in r.stdout:
        problemas.append(f"extraer_cuadros.py volvió a extraer lo que estaba al día: {r.stdout[-200:]}")
    hojas = caso / "hojas"
    for extra in ([], ["--medios"], ["--proyector"], ["--sala"], ["--medios", "3", "--guias"]):
        r = subprocess.run([PY, str(ARMAR / "hoja_contactos.py"), "--todos", "--deck", str(deck), "--guion",
                            str(caso / "sin_guion.md"), "--tokens", str(caso / "sin_tokens.json"), "--videos",
                            str(videos), "--cuadros", str(cuadros), "--salida", str(hojas), *extra],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        if r.returncode:
            problemas.append(f"hoja_contactos.py {' '.join(extra)} salió con {r.returncode}: {r.stderr[-300:]}")
    esperadas = ["hoja_T01.png", "hoja_T02.png", "hoja_T03.png", "hoja_charla.png", "hoja_T02_medios.png",
                 "hoja_T02_proyector.png", "hoja_charla_proyector.png", "hoja_T02_sala.png", "hoja_charla_sala.png"]
    for n in esperadas:
        if not (hojas / n).exists():
            problemas.append(f"hoja_contactos.py no dejó {n}")
    # el proyector levanta el negro: el fondo de la celda simulada es más claro que la tinta
    if (hojas / "hoja_T02_proyector.png").exists():
        im = cc.abrir_png(hojas / "hoja_T02_proyector.png")
        if im[200:260, 600:700].mean() < 35:
            problemas.append("la simulación de proyector no levantó el negro")
    # la sala difícil lo levanta todavía más (negro 0,115 en luz lineal: unos 95 de 255)
    if (hojas / "hoja_T02_sala.png").exists() and (hojas / "hoja_T02_proyector.png").exists():
        sala = cc.abrir_png(hojas / "hoja_T02_sala.png")[200:260, 600:700].mean()
        proy = cc.abrir_png(hojas / "hoja_T02_proyector.png")[200:260, 600:700].mean()
        if sala <= proy:
            problemas.append(f"la simulación de sala no levantó el negro más que la de proyector ({sala:.0f} contra {proy:.0f})")
    return problemas


def main(argv=None) -> int:
    cc.consola_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("casos", nargs="*", help="nombres de casos (por defecto, todos)")
    p.add_argument("--listar", action="store_true")
    p.add_argument("--rehacer", action="store_true", help="vuelve a codificar los videos de juguete")
    p.add_argument("--herramientas", action="store_true", help="prueba también extraer_cuadros y hoja_contactos")
    a = p.parse_args(argv)
    if a.listar:
        for c in CASOS:
            print(f"  {c.nombre:<24} {c.que}")
        return 0
    elegidos = [c for c in CASOS if not a.casos or c.nombre in a.casos]
    desconocidos = set(a.casos) - {c.nombre for c in CASOS}
    if desconocidos:
        p.error(f"casos desconocidos: {', '.join(sorted(desconocidos))}")
    BASE.mkdir(parents=True, exist_ok=True)
    fallas = 0
    t0 = time.time()
    for caso in elegidos:
        caso, problemas, seg, _ = correr_caso(caso, a.rehacer)
        dispara = ", ".join(f"{x[0]}·{x[1]}" for x in sorted(caso.errores)) or "nada"
        estado = "ok   " if not problemas else "FALLA"
        print(f"{estado} {caso.nombre:<24} {seg:5.1f} s  {caso.que}  [espera: {dispara}"
              f"{'; avisos: ' + ', '.join(f'{x[0]}·{x[1]}' for x in sorted(caso.avisos)) if caso.avisos else ''}]",
              flush=True)
        for pr in problemas:
            print(f"        - {pr}")
        fallas += bool(problemas)
    if a.herramientas:
        problemas = probar_herramientas()
        print(f"{'ok   ' if not problemas else 'FALLA'} herramientas: extraer_cuadros.py y hoja_contactos.py")
        for pr in problemas:
            print(f"        - {pr}")
        fallas += bool(problemas)
    print(f"\n{len(elegidos) - fallas if not a.herramientas else len(elegidos) + 1 - fallas} de "
          f"{len(elegidos) + (1 if a.herramientas else 0)} bien en {time.time() - t0:.0f} s. Casos en "
          f"{BASE.relative_to(RAIZ).as_posix()}/casos/ (cada uno con su informe y su salida.txt).")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
