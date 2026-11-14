"""Lo común de los controles de video de la charla.

Lo usan armar/auditar_cuadros.py, armar/hoja_contactos.py, armar/extraer_cuadros.py
y armar/probar_auditor.py:

- las rutas del proyecto (todas se pueden cambiar por argumento, para las pruebas);
- deck.json: diapositivas, pasos, cómo entra cada diapositiva (el campo «entrada» o, si
  falta, el texto «Entra desde…» de su primer paso) y los títulos de los pasos (del guion);
- diseno/tokens.json: colores, márgenes y zonas fijas, con los valores del guion
  como respaldo mientras ese archivo no exista o no traiga algún dato;
- diseno/assets/: las piezas que Remotion renderiza para Manim (marca de agua, chips);
- la lectura de cuadros con ffmpeg, siempre con la misma conversión (BT.709 de rango
  limitado a RGB de 8 bits: lo que hace ffmpeg por defecto con un video etiquetado
  BT.709, medido el 23-oct-2026, y lo que muestra PowerPoint), para que el PNG
  extraído, la hoja de contactos y el auditor vean los mismos números;
- las máscaras de color (fondo, familia del lima, familia del ámbar) y las medidas de
  diferencia entre dos cuadros.

No se ejecuta solo: se importa.
"""

from __future__ import annotations

import fnmatch
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import unicodedata
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ANCHO, ALTO, FPS = 1920, 1080, 30

# Conversión única de YUV a RGB: BT.709, rango limitado (la de la receta de entrega).
DECODIFICAR = "scale=in_color_matrix=bt709:in_range=tv,format=rgb24"


def consola_utf8():
    """La consola de Windows en español es cp1252: sin esto, las tildes salen rotas."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@dataclass
class Rutas:
    raiz: Path = RAIZ
    deck: Path = RAIZ / "contenido" / "deck.json"
    guion: Path = RAIZ / "contenido" / "guion.md"
    tokens: Path = RAIZ / "diseno" / "tokens.json"
    assets: Path = RAIZ / "diseno" / "assets"
    pasos: Path = RAIZ / "render" / "pasos"
    final: Path = RAIZ / "render" / "final"
    cuadros: Path = RAIZ / "render" / "cuadros"
    revision: Path = RAIZ / "render" / "revision"
    reglas: Path = RAIZ / "armar" / "auditoria_reglas.json"
    temporal: Path = RAIZ / ".tmp" / "auditor"

    def relativa(self, p) -> str:
        """Ruta para mostrar: relativa a la raíz si se puede, con barras /."""
        p = Path(p)
        try:
            return p.resolve().relative_to(self.raiz.resolve()).as_posix()
        except ValueError:
            return p.as_posix()


def carpeta_temporal(rutas: Rutas, nombre: str) -> Path:
    """Carpeta temporal dentro de .tmp/auditor/ (la única carpeta de temporales del proyecto)."""
    rutas.temporal.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{nombre}_", dir=rutas.temporal))


# ---------------------------------------------------------------------------
# deck.json
# ---------------------------------------------------------------------------

RE_ENTRA = re.compile(
    r"Entra desde (?:(tinta)|el (?:PNG del )?último cuadro de ([DA]\d+)(?: o de ([DA]\d+))?)")
RE_TITULO_PASO = re.compile(r"^#### ([DA]\d+)\.(\d+) · (.+?)\s*$", re.M)

# Duración por defecto de las transiciones con video propio (guion y diseno/tokens.json
# «transiciones»; las mismas que usan remotion/lib/deck.mjs y armar/deck.py).
SEGUNDOS_TRANSICION = {"fundido": 0.4, "puertas": 1.05}
TIPOS_ENTRADA = ("continuo", "fundido", "puertas", "corte")


@dataclass
class Entrada:
    """Cómo se pasa del último cuadro de la anterior al primero de esta diapositiva.

    - continuo: el paso 1 arranca en el último cuadro de `desde` (lo que hace Remotion por
      defecto, y lo que dice el guion con «Entra desde el último cuadro de…»);
    - fundido o puertas: armar.py final pega delante del paso 1 una transición de `segundos`;
      la duracion_animacion_s del paso 1 en deck.json la incluye, así que el video crudo dura
      eso menos `segundos` y no arranca en el cuadro de `desde`;
    - corte: corte seco a propósito.
    """
    tipo: str
    segundos: float
    desde: list          # ids de diapositiva o ["tinta"]
    origen: str          # "deck" (campo «entrada»), "guion" (texto «Entra desde…») o "anterior"

    @property
    def con_transicion(self) -> bool:
        return self.tipo in SEGUNDOS_TRANSICION


@dataclass
class Paso:
    diapo: str
    k: int
    duracion: float
    audio: str | None
    texto: list
    visual: str
    titulo: str = ""
    transicion_s: float = 0.0   # en el paso 1 de una entrada con fundido o puertas

    @property
    def clave(self) -> str:
        return f"{self.diapo}.{self.k}"

    @property
    def nombre_archivo(self) -> str:
        return f"{self.diapo}_{self.k}"

    @property
    def duracion_propia(self) -> float:
        """Lo que dura el video crudo (render/pasos): sin la transición, que va en render/final."""
        return self.duracion - self.transicion_s

    def video(self, carpeta: Path) -> Path:
        return Path(carpeta) / self.diapo / f"{self.diapo}_{self.k}.mp4"

    def ding(self) -> float | None:
        """Segundo del ding según deck.json («ding:34.3»), o None."""
        if self.audio and str(self.audio).startswith("ding:"):
            return float(str(self.audio).split(":", 1)[1].replace(",", "."))
        return None


@dataclass
class Diapo:
    id: str
    nombre: str
    titulo: str
    seccion: str
    motor: str
    piso: int | None
    pasos: list
    entrada: Entrada

    @property
    def entra(self) -> list:
        """["tinta"] o los id de las diapositivas desde cuyo último cuadro entra."""
        return self.entrada.desde


def leer_entrada(valor, desde_def: list, segundos_def=None) -> Entrada:
    """El campo «entrada» de deck.json, en las formas que leen Remotion y el armado:
    {"tipo": "fundido", "duracion_s": 0.4, "desde": "D19"} o "fundido 0,4 desde D19"."""
    segundos_def = segundos_def or SEGUNDOS_TRANSICION

    def norm_desde(v):
        if v is None or str(v).strip().lower() in ("", "tinta", "none", "null"):
            return ["tinta"]
        return [str(x).strip().upper() for x in (v if isinstance(v, list) else [v])]

    if isinstance(valor, dict):
        tipo = str(valor.get("tipo") or valor.get("clase") or valor.get("modo") or "fundido").strip().lower()
        seg = next((valor[k] for k in ("duracion_s", "segundos", "duracion", "s") if valor.get(k) is not None), None)
        desde = norm_desde(valor["desde"]) if "desde" in valor else desde_def
    else:
        texto = str(valor)
        tipo = next((t for t in TIPOS_ENTRADA if t in texto.lower()), "fundido")
        m = re.search(r"desde\s+([DA]\d+|tinta)", texto, re.I)
        desde = norm_desde(m.group(1)) if m else desde_def
        sin_desde = re.sub(r"desde\s+\S+", "", texto, flags=re.I)
        n = re.search(r"(\d+(?:[.,]\d+)?)", sin_desde)
        seg = n.group(1) if n else None
    if tipo not in TIPOS_ENTRADA:
        tipo = "fundido"
    if tipo in SEGUNDOS_TRANSICION:
        seg = float(str(seg).replace(",", ".")) if seg is not None else segundos_def.get(tipo, 0.4)
    else:
        seg = 0.0
    return Entrada(tipo, seg, desde, "deck")


@dataclass
class Deck:
    diapos: list
    ruta: Path

    def diapo(self, id_: str) -> Diapo | None:
        for d in self.diapos:
            if d.id == id_:
                return d
        return None

    def pasos(self, ids=None) -> list:
        return [p for d in self.diapos if ids is None or d.id in ids for p in d.pasos]

    def paso(self, clave: str) -> Paso | None:
        id_, _, k = clave.partition(".")
        d = self.diapo(id_)
        if d and k.isdigit() and 1 <= int(k) <= len(d.pasos):
            return d.pasos[int(k) - 1]
        return None

    def predecesores(self, paso: Paso) -> list:
        """De qué cuadro arranca el paso: la clave del paso anterior (o varias, si la
        diapositiva se puede abrir desde más de un lugar), o "tinta"."""
        if paso.k > 1:
            return [f"{paso.diapo}.{paso.k - 1}"]
        d = self.diapo(paso.diapo)
        salida = []
        for e in d.entra:
            if e == "tinta":
                salida.append("tinta")
            else:
                otra = self.diapo(e)
                if otra and otra.pasos:
                    salida.append(otra.pasos[-1].clave)
        return salida or ["tinta"]


def cargar_deck(rutas: Rutas, segundos_transicion=None) -> Deck:
    """Lee deck.json. La entrada de cada diapositiva sale del campo «entrada» (en la
    diapositiva o en su primer paso) si existe; si no, es «continuo» desde la diapositiva que
    nombra el guion («Entra desde el último cuadro de D20…», «desde tinta») o, si no nombra
    ninguna, desde la anterior en la lista."""
    datos = json.loads(Path(rutas.deck).read_text(encoding="utf-8"))
    titulos = {}
    if rutas.guion and Path(rutas.guion).exists():
        for m in RE_TITULO_PASO.finditer(Path(rutas.guion).read_text(encoding="utf-8")):
            titulos[f"{m.group(1)}.{m.group(2)}"] = m.group(3)
    diapos = []
    anterior = None
    for d in datos["diapositivas"]:
        pasos = []
        for k, p in enumerate(d["pasos"], 1):
            pasos.append(Paso(diapo=d["id"], k=k, duracion=float(p.get("duracion_animacion_s") or 0),
                              audio=p.get("audio"), texto=list(p.get("texto_pantalla") or []),
                              visual=p.get("visual") or "", titulo=titulos.get(f"{d['id']}.{k}", "")))
        visual0 = pasos[0].visual if pasos else ""
        m = RE_ENTRA.search(visual0)
        if m and m.group(1):
            desde, origen = ["tinta"], "guion"
        elif m:
            desde, origen = [g for g in (m.group(2), m.group(3)) if g], "guion"
        else:
            desde, origen = ([anterior] if anterior else ["tinta"]), "anterior"
        valor = d.get("entrada")
        if valor is None and d.get("pasos"):
            valor = d["pasos"][0].get("entrada")
        if valor is not None:
            entrada = leer_entrada(valor, desde, segundos_transicion)
        else:
            entrada = Entrada("continuo", 0.0, desde, origen)
        if pasos and entrada.con_transicion:
            pasos[0].transicion_s = entrada.segundos
        diapos.append(Diapo(id=d["id"], nombre=d.get("nombre", ""), titulo=d.get("titulo", ""),
                            seccion=d.get("seccion", ""), motor=d.get("motor", ""), piso=d.get("piso"),
                            pasos=pasos, entrada=entrada))
        anterior = d["id"]
    return Deck(diapos=diapos, ruta=Path(rutas.deck))


def coincide(clave: str, patrones) -> bool:
    """¿La clave de un paso ("D02.3") entra en alguno de los patrones?
    Un patrón sin punto es una diapositiva entera ("D02" = "D02.*"); vale * y ?."""
    if isinstance(patrones, str):
        patrones = [patrones]
    for p in patrones or []:
        p = str(p).strip()
        if not p:
            continue
        if "." not in p:
            p += ".*"
        if fnmatch.fnmatchcase(clave, p):
            return True
    return False


def elegir_diapos(deck: Deck, ids, todos: bool) -> list:
    """Las diapositivas pedidas, en el orden del deck. Lanza ValueError si un id no existe."""
    if todos or not ids:
        return list(deck.diapos)
    pedidos = [i.strip().upper() for i in ids]
    faltan = [i for i in pedidos if deck.diapo(i) is None]
    if faltan:
        validos = " ".join(d.id for d in deck.diapos)
        raise ValueError(f"no están en deck.json: {', '.join(faltan)} (las que hay: {validos})")
    return [d for d in deck.diapos if d.id in pedidos]


# ---------------------------------------------------------------------------
# Tokens de diseño
# ---------------------------------------------------------------------------

# Valores del guion (contenido/guion.md, «Sistema visual» y «Zonas fijas»): se usan
# para todo lo que diseno/tokens.json no traiga (o mientras no exista).
VALORES_GUION = {
    "colores": {
        "tinta": "#070A0F", "hueso": "#F5F7FF", "ambar": "#FFB547", "rojo": "#FF5C5C",
        "gris": "#9AA3B8", "acero": "#1A2230", "acero2": "#2A3446", "vidrio": "#05070A",
        "marca": "#B8FF3C",
    },
    "margen_x": 67,
    "margen_y": 38,
    "marca_agua": (67, 38, 300, 86),
    "chip": (1721, 38, 1853, 122),
    "reloj": {"cx": 1500, "cy": 520, "alto": 220},
}

NOMBRES_COLOR = {
    "tinta": ["tinta", "fondo", "background", "bg"],
    "hueso": ["hueso", "blanco", "texto"],
    "ambar": ["ambar", "acento", "accent"],
    "rojo": ["rojo", "alerta"],
    "gris": ["gris"],
    "acero": ["acero", "acero1"],
    "acero2": ["acero2"],
    "vidrio": ["vidrio"],
    "marca": ["marca", "lima", "brand", "nemaxyz"],
}
NOMBRES_ZONA = {
    "marca_agua": ["marcaagua", "marcadeagua", "watermark", "marcaaguazona"],
    "chip": ["chip", "chippiso", "chipdepiso", "chipdelpiso", "indicadorpiso"],
    "reloj": ["reloj", "relojgrande", "relojfijo", "visorreloj", "lugarreloj"],
}
NOMBRES_MARGEN = ["margenes", "margen", "zonasegura", "areasegura", "margins", "margin", "safe", "safezone"]


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _aplanar(obj, camino=()):
    salida = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            c = camino + (str(k),)
            salida.append((c, v))
            salida += _aplanar(v, c)
    elif isinstance(obj, list) and not all(isinstance(x, (int, float)) for x in obj):
        for i, v in enumerate(obj):
            salida += _aplanar(v, camino + (str(i),))
    return salida


def _buscar(planos, nombres, contexto=()):
    """Entradas cuya última clave (normalizada) está en `nombres`; primero las que tienen
    un antepasado que contiene alguna palabra de `contexto`, después las menos profundas."""
    candidatos = []
    for camino, v in planos:
        if _norm(camino[-1]) in nombres:
            ctx = any(any(w in _norm(c) for w in contexto) for c in camino[:-1]) if contexto else True
            candidatos.append((0 if ctx else 1, len(camino), camino, v))
    candidatos.sort(key=lambda x: (x[0], x[1]))
    return [(c, v) for _, _, c, v in candidatos]


def hex_a_rgb(h) -> tuple:
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"color no válido: {h!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _color(v):
    try:
        if isinstance(v, str):
            return hex_a_rgb(v)
        if isinstance(v, (list, tuple)) and len(v) in (3, 4) and all(isinstance(x, (int, float)) for x in v):
            return tuple(int(x) for x in v[:3])
        if isinstance(v, dict):
            for k in ("hex", "valor", "value", "color", "rgb"):
                for kk, vv in v.items():
                    if _norm(kk) == k:
                        return _color(vv)
    except ValueError:
        return None
    return None


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _clave(d: dict, *nombres):
    for k, v in d.items():
        if _norm(k) in nombres and _num(v) is not None:
            return _num(v)
    return None


def _rect(v):
    """Un rectángulo (x0, y0, x1, y1) en px desde casi cualquier forma razonable."""
    if isinstance(v, (list, tuple)) and len(v) == 4 and all(_num(x) is not None for x in v):
        a, b, c, d = (float(x) for x in v)
        return (a, b, c, d) if (c > a and d > b) else (a, b, a + c, b + d)
    if isinstance(v, str):
        m = re.search(r"x\s*(\d+)\s*[-–]\s*(\d+).*?y\s*(\d+)\s*[-–]\s*(\d+)", v)
        if m:
            x0, x1, y0, y1 = (float(g) for g in m.groups())
            return (x0, y0, x1, y1)
        return None
    if not isinstance(v, dict):
        return None
    x0 = _clave(v, "x0", "izquierda", "left", "xmin")
    y0 = _clave(v, "y0", "arriba", "top", "ymin", "superior")
    x1 = _clave(v, "x1", "derecha", "right", "xmax")
    y1 = _clave(v, "y1", "abajo", "bottom", "ymax", "inferior")
    x = _clave(v, "x")
    y = _clave(v, "y")
    if None not in (x0, y0, x1, y1):
        return (x0, y0, x1, y1)
    if None not in (x, y, x1, y1):
        return (x, y, x1, y1)
    w = _clave(v, "ancho", "w", "width")
    h = _clave(v, "alto", "h", "height")
    if None not in (x, y, w, h):
        return (x, y, x + w, y + h)
    cx = _clave(v, "cx", "centrox")
    cy = _clave(v, "cy", "centroy")
    for k, vv in v.items():
        if _norm(k) in ("centro", "center") and isinstance(vv, (list, tuple)) and len(vv) == 2:
            cx, cy = float(vv[0]), float(vv[1])
    if None not in (cx, cy, w, h):
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    for k, vv in v.items():
        if _norm(k) in ("rect", "caja", "bbox", "px", "zona"):
            r = _rect(vv)
            if r:
                return r
    return None


def _zona_dibujo(v):
    """(lo que ocupa el dibujo, la zona reservada o None) de una entrada de zona fija.
    La forma de diseno/tokens.json es {"x", "y", "x1", "y1" o "ancho"/"alto", "zona": {...}}:
    el dibujo, y alrededor la zona donde no se dibuja nada más."""
    if not isinstance(v, dict):
        r = _rect(v)
        return (r, None) if r else (None, None)
    reservada = None
    resto = {}
    for k, vv in v.items():
        if _norm(k) in ("zona", "reservada", "zonareservada"):
            reservada = _rect(vv)
        else:
            resto[k] = vv
    dibujo = _rect(resto) or (reservada if reservada else None)
    return dibujo, reservada


def _reloj(v):
    if isinstance(v, dict):
        cx = _clave(v, "cx", "centrox")
        cy = _clave(v, "cy", "centroy")
        for k, vv in v.items():
            if _norm(k) in ("centro", "center") and isinstance(vv, (list, tuple)) and len(vv) == 2:
                cx, cy = float(vv[0]), float(vv[1])
        alto = _clave(v, "alto", "h", "height", "altodigito", "altura")
        if None not in (cx, cy, alto):
            salida = {"cx": cx, "cy": cy, "alto": alto}
            luces = _clave(v, "lucesy")
            if luces is not None:
                salida["luces_y"] = luces
            return salida
    r = _rect(v)
    if r:
        return {"cx": (r[0] + r[2]) / 2, "cy": (r[1] + r[3]) / 2, "alto": r[3] - r[1]}
    return None


def _margenes(v):
    """(margen_x, margen_y) o un rectángulo seguro (x0, y0, x1, y1)."""
    n = _num(v)
    if n is not None:
        return ("xy", n, n)
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(_num(x) is not None for x in v):
        return ("xy", float(v[0]), float(v[1]))
    if isinstance(v, dict):
        x = _clave(v, "x", "horizontal", "lados", "laterales", "izquierda", "derecha", "costados", "left", "right")
        y = _clave(v, "y", "vertical", "arriba", "abajo", "superior", "inferior", "top", "bottom")
        if x is not None and y is not None:
            return ("xy", x, y)
    r = _rect(v)
    if r:
        return ("rect",) + tuple(r)
    return None


def _camino(datos, *claves):
    """datos[c1][c2]… o None (las claves se comparan normalizadas)."""
    actual = datos
    for c in claves:
        if not isinstance(actual, dict):
            return None
        hallado = None
        for k, v in actual.items():
            if _norm(k) == _norm(c):
                hallado = v
                break
        if hallado is None:
            return None
        actual = hallado
    return actual


@dataclass
class Tokens:
    colores: dict
    zona_segura: tuple
    marca_agua: tuple            # lo que ocupa la marca de agua dibujada
    marca_agua_zona: tuple       # su zona reservada (nada más se dibuja ahí); = marca_agua si no hay
    chip: tuple
    chip_zona: tuple
    reloj: dict                  # cx, cy, alto (y luces_y si se sabe)
    marca_agua_sin: list | None = None   # pasos sin marca de agua (persistentes.marca_agua_sin)
    respiro_s: float | None = None       # lo quieto al final de cada paso (pasos.respiro_s)
    transiciones: dict = field(default_factory=dict)  # tipo -> segundos
    origen: dict = field(default_factory=dict)
    notas: list = field(default_factory=list)
    archivo: Path | None = None

    def rgb(self, nombre) -> tuple:
        return self.colores[nombre]


def cargar_tokens(rutas: Rutas) -> Tokens:
    """diseno/tokens.json, con los valores del guion para lo que falte. Primero se buscan las
    claves de su forma actual (reticula.zona_segura, reticula.marca_agua, reticula.chip_piso,
    reticula.reloj, persistentes.marca_agua_sin, pasos.respiro_s, transiciones); si cambian de
    nombre o de lugar, una búsqueda flexible por nombre las encuentra igual (y el informe dice
    de dónde salió cada valor)."""
    g = VALORES_GUION
    colores = {k: hex_a_rgb(v) for k, v in g["colores"].items()}
    mx, my = g["margen_x"], g["margen_y"]
    t = Tokens(colores=colores, zona_segura=(mx, my, ANCHO - mx, ALTO - my), marca_agua=g["marca_agua"],
               marca_agua_zona=g["marca_agua"], chip=g["chip"], chip_zona=g["chip"], reloj=dict(g["reloj"]),
               transiciones=dict(SEGUNDOS_TRANSICION))
    claves = list(colores) + ["margenes", "marca_agua", "chip", "reloj"]
    ruta = Path(rutas.tokens)
    if not ruta.exists():
        t.notas.append(f"{rutas.relativa(ruta)} no existe: márgenes, zonas y colores salen del guion.")
        t.origen = {k: "guion" for k in claves}
        return t
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        t.notas.append(f"No se pudo leer {rutas.relativa(ruta)} ({e}): se usan los valores del guion.")
        t.origen = {k: "guion" for k in claves}
        return t
    t.archivo = ruta
    planos = _aplanar(datos)
    nombre = rutas.relativa(ruta)
    de = lambda camino: f"{nombre} → {'.'.join(camino)}"  # noqa: E731

    for k, nombres in NOMBRES_COLOR.items():
        hallado = next(((c, _color(v)) for c, v in _buscar(planos, nombres, contexto=("color", "paleta", "palette"))
                        if _color(v)), None)
        if hallado:
            t.colores[k] = hallado[1]
            t.origen[k] = de(hallado[0])
        else:
            t.origen[k] = "guion"

    # Márgenes
    seg = None
    v = _camino(datos, "reticula", "zona_segura")
    if v is not None and _margenes(v):
        seg = (("reticula", "zona_segura"), _margenes(v))
    if not seg:
        mxx, myy = _camino(datos, "reticula", "margen_x"), _camino(datos, "reticula", "margen_y")
        if _num(mxx) is not None and _num(myy) is not None:
            seg = (("reticula", "margen_x/margen_y"), ("xy", float(mxx), float(myy)))
    if not seg:
        seg = next(((c, _margenes(v)) for c, v in _buscar(planos, NOMBRES_MARGEN) if _margenes(v)), None)
    if seg:
        t.zona_segura = (seg[1][1], seg[1][2], ANCHO - seg[1][1], ALTO - seg[1][2]) if seg[1][0] == "xy" \
            else tuple(seg[1][1:])
        t.origen["margenes"] = de(seg[0])
    else:
        t.origen["margenes"] = "guion"
        t.notas.append(f"{nombre} no trae márgenes legibles: se usan los del guion (67 y 38 px).")

    # Marca de agua y chip: el dibujo y su zona reservada
    for k, exacto in (("marca_agua", ("reticula", "marca_agua")), ("chip", ("reticula", "chip_piso"))):
        hallado = None
        v = _camino(datos, *exacto)
        if v is not None and _zona_dibujo(v)[0]:
            hallado = (exacto, _zona_dibujo(v))
        if not hallado:
            for c, vv in _buscar(planos, NOMBRES_ZONA[k], contexto=("zona", "layout", "posicion", "lugar", "reticula")):
                dib = _zona_dibujo(vv)
                if dib[0]:
                    hallado = (c, dib)
                    break
        if hallado:
            dibujo, reservada = hallado[1]
            setattr(t, k, tuple(dibujo))
            setattr(t, f"{k}_zona", tuple(reservada) if reservada else tuple(dibujo))
            t.origen[k] = de(hallado[0])
        else:
            t.origen[k] = "guion"
            t.notas.append(f"{nombre} no trae la zona «{k}» legible: se usa la del guion.")

    # Reloj grande
    hallado = None
    v = _camino(datos, "reticula", "reloj")
    if v is not None and _reloj(v):
        hallado = (("reticula", "reloj"), _reloj(v))
    if not hallado:
        hallado = next(((c, _reloj(vv)) for c, vv in _buscar(planos, NOMBRES_ZONA["reloj"],
                                                             contexto=("zona", "layout", "posicion", "lugar", "reticula"))
                        if _reloj(vv)), None)
    if hallado:
        t.reloj = hallado[1]
        t.origen["reloj"] = de(hallado[0])
    else:
        t.origen["reloj"] = "guion"
        t.notas.append(f"{nombre} no trae el lugar del reloj grande legible: se usa el del guion.")

    # Listas y tiempos que también son de diseño
    v = _camino(datos, "persistentes", "marca_agua_sin")
    if v is None:
        v = next((vv for c, vv in _buscar(planos, ["marcaaguasin", "sinmarcadeagua", "sinmarcaagua"])), None)
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        t.marca_agua_sin = list(v)
        t.origen["marca_agua_sin"] = de(("persistentes", "marca_agua_sin"))
    v = _camino(datos, "pasos", "respiro_s")
    if _num(v) is not None:
        t.respiro_s = float(v)
        t.origen["respiro_s"] = de(("pasos", "respiro_s"))
    trans = _camino(datos, "transiciones")
    if isinstance(trans, dict):
        for tipo, vv in trans.items():
            s = _camino(vv, "duracion_s") if isinstance(vv, dict) else None
            if _num(s) is not None and _norm(tipo) in SEGUNDOS_TRANSICION:
                t.transiciones[_norm(tipo)] = float(s)

    redondo = lambda r: tuple(int(round(x)) for x in r)  # noqa: E731
    t.zona_segura = redondo(t.zona_segura)
    for k in ("marca_agua", "marca_agua_zona", "chip", "chip_zona"):
        setattr(t, k, redondo(getattr(t, k)))
    t.reloj = {k: float(x) for k, x in t.reloj.items()}
    return t


def cargar_assets(rutas: Rutas) -> dict:
    """Las piezas de diseno/assets/ que Remotion renderiza para Manim (marca de agua, chips).

    Con el manifiesto diseno/assets/assets.json: {"piezas": {"marca_agua": {"x", "y", "ancho",
    "alto", "archivos": {"transparente", "cuadro", "tinta"}}}}, donde x, y es la esquina del recorte
    en el cuadro de 1920x1080. Devuelve {nombre normalizado: {"nombre", "x", "y", "ancho", "alto",
    "cuadro": Path|None, "transparente": Path|None}}. Sin manifiesto, junta los PNG por nombre (la
    posición queda sin saber, salvo que el PNG mida 1920x1080)."""
    carpeta = Path(rutas.assets)
    piezas = {}
    if not carpeta.is_dir():
        return piezas
    manifiesto = carpeta / "assets.json"
    if manifiesto.exists():
        try:
            datos = json.loads(manifiesto.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            datos = {}
        for nombre, p in (datos.get("piezas") or {}).items():
            if not isinstance(p, dict):
                continue
            arch = p.get("archivos") or {}
            existe = lambda k: (carpeta / arch[k]) if arch.get(k) and (carpeta / arch[k]).exists() else None  # noqa: E731
            piezas[_norm(nombre)] = {"nombre": nombre, "x": _num(p.get("x")), "y": _num(p.get("y")),
                                     "ancho": _num(p.get("ancho")), "alto": _num(p.get("alto")),
                                     "cuadro": existe("cuadro"), "transparente": existe("transparente")}
        if piezas:
            return piezas
    for png in sorted(carpeta.glob("*.png")):
        clave = _norm(png.stem)
        if clave.endswith("1080") or clave.endswith("tinta"):
            continue
        try:
            tam = Image.open(png).size
        except OSError:
            continue
        completo = tam == (ANCHO, ALTO)
        piezas[clave] = {"nombre": png.stem, "x": 0.0 if completo else None, "y": 0.0 if completo else None,
                         "ancho": float(tam[0]), "alto": float(tam[1]),
                         "cuadro": png if completo else None, "transparente": None if completo else png}
    return piezas


def pieza_en_cuadro(pieza: dict, lugares=()) -> Image.Image | None:
    """La pieza como RGBA de 1920x1080, en su píxel. `lugares`: rectángulos donde probar a
    ponerla si no se sabe su posición (se usa el primero de su mismo tamaño)."""
    if pieza.get("cuadro"):
        im = Image.open(pieza["cuadro"]).convert("RGBA")
        if im.size == (ANCHO, ALTO):
            return im
    if pieza.get("transparente"):
        im = Image.open(pieza["transparente"]).convert("RGBA")
        x, y = pieza.get("x"), pieza.get("y")
        if x is None or y is None:
            for r in lugares:
                if (int(round(r[2] - r[0])), int(round(r[3] - r[1]))) == im.size:
                    x, y = r[0], r[1]
                    break
        if x is not None and y is not None:
            lienzo = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
            lienzo.alpha_composite(im, (int(round(x)), int(round(y))))
            return lienzo
    return None


# ---------------------------------------------------------------------------
# Reglas del auditor (armar/auditoria_reglas.json)
# ---------------------------------------------------------------------------

def cargar_reglas(rutas: Rutas) -> dict:
    ruta = Path(rutas.reglas)
    if not ruta.exists():
        return {"excepciones": []}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos.setdefault("excepciones", [])
    return datos


# ---------------------------------------------------------------------------
# Videos: ffprobe y cuadros
# ---------------------------------------------------------------------------

class ErrorVideo(Exception):
    pass


def ffprobe(video) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise ErrorVideo((r.stderr or "").strip() or "ffprobe no pudo leer el archivo")
    return json.loads(r.stdout)


def stream_video(probe: dict) -> dict | None:
    for s in probe.get("streams", []):
        if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic"):
            return s
    return None


def streams_audio(probe: dict) -> list:
    return [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]


def fraccion(s) -> float | None:
    try:
        n, d = str(s).split("/")
        return int(n) / int(d) if int(d) else None
    except (ValueError, TypeError):
        return None


def contar_cuadros(video, probe: dict | None = None) -> int:
    """Cuadros del video: nb_frames del encabezado MP4; si no está, contando paquetes."""
    probe = probe or ffprobe(video)
    v = stream_video(probe)
    if v and str(v.get("nb_frames", "")).isdigit() and int(v["nb_frames"]) > 0:
        return int(v["nb_frames"])
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        raise ErrorVideo("no pude contar los cuadros")


def moov_antes_que_mdat(video) -> bool | None:
    """¿El índice (moov) va antes de los datos (mdat)? Es lo que deja +faststart."""
    orden = []
    try:
        with open(video, "rb") as f:
            f.seek(0, 2)
            fin = f.tell()
            pos = 0
            while pos + 8 <= fin and len(orden) < 64:
                f.seek(pos)
                tam, tipo = struct.unpack(">I4s", f.read(8))
                if tam == 1:
                    tam = struct.unpack(">Q", f.read(8))[0]
                elif tam == 0:
                    tam = fin - pos
                if tam < 8:
                    break
                orden.append(tipo)
                pos += tam
    except (OSError, struct.error):
        return None
    if b"moov" in orden and b"mdat" in orden:
        return orden.index(b"moov") < orden.index(b"mdat")
    return None


def leer_cuadros(video, *, antes=(), filtro=None, max_cuadros=None, tamano=None):
    """Genera los cuadros decodificados del video como arreglos (alto, ancho, 3) uint8.

    `antes`: opciones de entrada de ffmpeg (por ejemplo ["-sseof", "-2"] o ["-ss", "1.5"]).
    `filtro`: un filtro previo a la conversión (por ejemplo un select).
    """
    if tamano is None:
        v = stream_video(ffprobe(video))
        if not v:
            raise ErrorVideo("no tiene video")
        tamano = (int(v["width"]), int(v["height"]))
    w, h = tamano
    vf = ([filtro] if filtro else []) + [DECODIFICAR]
    cmd = ["ffmpeg", "-v", "error", "-nostdin", *antes, "-i", str(video), "-an", "-sn", "-dn",
           "-vf", ",".join(vf), "-fps_mode", "passthrough"]
    if max_cuadros:
        cmd += ["-frames:v", str(max_cuadros)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=w * h * 3)
    n = w * h * 3
    terminado = False
    try:
        while True:
            buf = proc.stdout.read(n)
            if len(buf) < n:
                terminado = True
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        if not terminado:
            proc.kill()
        proc.stdout.close()
        err = proc.stderr.read().decode("utf-8", "replace").strip()
        proc.stderr.close()
        proc.wait()
        if terminado and proc.returncode:
            raise ErrorVideo(err or f"ffmpeg terminó con código {proc.returncode}")


def primer_cuadro(video, tamano=None) -> np.ndarray:
    for c in leer_cuadros(video, max_cuadros=1, tamano=tamano):
        return c
    raise ErrorVideo("no salió ningún cuadro")


def ultimos_cuadros(video, n: int, tamano=None, fps: float = FPS) -> list:
    """Los últimos n cuadros (el último al final). Decodifica solo el final del video."""
    atras = n / fps + 1.0
    cola = deque(leer_cuadros(video, antes=["-sseof", f"-{atras:.3f}"], tamano=tamano), maxlen=n)
    if not cola:
        raise ErrorVideo("no salió ningún cuadro del final")
    return list(cola)


def ultimo_cuadro(video, tamano=None) -> np.ndarray:
    return ultimos_cuadros(video, 1, tamano=tamano)[-1]


def cuadro_en(video, t: float, tamano=None) -> np.ndarray:
    for c in leer_cuadros(video, antes=["-ss", f"{max(0.0, t):.3f}"], max_cuadros=1, tamano=tamano):
        return c
    raise ErrorVideo(f"no salió ningún cuadro en {t:.2f} s")


def muestrear(video, cada: int, tamano=None):
    """Genera (índice, cuadro) para los cuadros 0, cada, 2·cada…"""
    filtro = f"select=not(mod(n\\,{int(cada)}))"
    for i, c in enumerate(leer_cuadros(video, filtro=filtro, tamano=tamano)):
        yield i * int(cada), c


def leer_audio(video, sr: int = 16000) -> np.ndarray:
    """La pista de audio en mono, como flotantes entre -1 y 1."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(video), "-vn", "-ac", "1", "-ar", str(sr),
                        "-f", "s16le", "-"], capture_output=True)
    if r.returncode:
        raise ErrorVideo(r.stderr.decode("utf-8", "replace").strip() or "no pude leer el audio")
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def guardar_png(arr: np.ndarray, ruta, nivel: int = 6):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(arr)).save(ruta, compress_level=nivel)


def abrir_png(ruta) -> np.ndarray:
    return np.asarray(Image.open(ruta).convert("RGB"))


def codificar_cuadros(cuadros, salida, rutas: Rutas | None = None, fps: int = FPS):
    """Codifica cuadros RGB con la receta de entrega: primero sin pérdida (libx264rgb qp 0)
    y después armar/codificar_paso.py, igual que los pasos de Manim."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from codificar_paso import codificar  # noqa: E402
    rutas = rutas or Rutas()
    tmp = carpeta_temporal(rutas, "codificar")
    sp = tmp / "sin_perdida.mkv"
    proc = None
    try:
        for c in cuadros:
            c = np.ascontiguousarray(c, np.uint8)
            if proc is None:
                h, w = c.shape[:2]
                proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264rgb",
                                         "-qp", "0", "-preset", "ultrafast", str(sp)], stdin=subprocess.PIPE)
            proc.stdin.write(c.tobytes())
        if proc is None:
            raise ValueError("no hay cuadros para codificar")
        proc.stdin.close()
        if proc.wait():
            raise ErrorVideo("ffmpeg no pudo escribir el video sin pérdida")
        Path(salida).parent.mkdir(parents=True, exist_ok=True)
        codificar(sp, salida)
    finally:
        for f in tmp.glob("*"):
            f.unlink()
        tmp.rmdir()


_FONDOS = {}


def fondo_decodificado(rgb, rutas: Rutas | None = None) -> np.ndarray:
    """El color plano `rgb` tal como sale después de la receta de entrega (BT.709 limitado,
    QP 16): la tinta #070A0F vuelve como (5, 9, 13)."""
    rgb = tuple(int(x) for x in rgb)
    if rgb not in _FONDOS:
        rutas = rutas or Rutas()
        tmp = carpeta_temporal(rutas, "fondo")
        video = tmp / "fondo.mp4"
        try:
            plano = np.empty((64, 64, 3), np.uint8)
            plano[:] = rgb
            codificar_cuadros([plano, plano], video, rutas)
            c = ultimo_cuadro(video, tamano=(64, 64))
            _FONDOS[rgb] = np.median(c.reshape(-1, 3), axis=0).astype(np.int16)
        finally:
            for f in tmp.glob("*"):
                f.unlink()
            tmp.rmdir()
    return _FONDOS[rgb].copy()


# ---------------------------------------------------------------------------
# Máscaras de color
# ---------------------------------------------------------------------------

def _canales(img):
    a = img.astype(np.int16)
    return a[..., 0], a[..., 1], a[..., 2]


def mascara_contenido(img, fondo, umbral: int) -> np.ndarray:
    """Píxeles que no son fondo: algún canal se aleja más de `umbral` del fondo."""
    d = np.abs(img.astype(np.int16) - np.asarray(fondo, np.int16).reshape(1, 1, 3)).max(axis=2)
    return d > umbral


def mascara_lima(img, v_min: int = 46, s_min: float = 0.40) -> np.ndarray:
    """La familia del lima #B8FF3C (tono 82°): tono entre 65° y 110°, saturación ≥ s_min y
    brillo ≥ v_min. Incluye sus bordes con antialias y el lima al 72 % de la marca de agua.
    Ningún otro color de la paleta cae ahí (el ámbar está en 36°, el rojo en 0°, el hueso,
    el gris y el acero son casi neutros y azulados)."""
    r, g, b = _canales(img)
    return ((g >= r) & (r >= b) & (g >= v_min)
            & (6 * (r - b) >= (g - b))            # tono ≤ 110°
            & (12 * (r - b) <= 11 * (g - b))      # tono ≥ 65°
            & ((g - b) * 100 >= int(round(s_min * 100)) * g))   # saturación ≥ s_min


def mascara_ambar(img, brillante: bool = True) -> np.ndarray:
    """La familia del ámbar #FFB547 (tono 36°): tono entre 20° y 50°, saturación ≥ 0,45.
    Con brillante=True, solo lo encendido (rojo ≥ 140: deja afuera el ámbar al 8 % de los
    segmentos apagados y el atenuado por el Foco)."""
    r, g, b = _canales(img)
    v_min = 140 if brillante else 60
    return ((r >= g) & (g >= b) & (r >= v_min)
            & (3 * (g - b) >= (r - b))            # tono ≥ 20°
            & (6 * (g - b) <= 5 * (r - b))        # tono ≤ 50°
            & (20 * (r - b) >= 9 * r))            # saturación ≥ 0,45


def mascara_rect(forma, rects) -> np.ndarray:
    m = np.zeros(forma[:2], bool)
    for r in rects:
        x0, y0, x1, y1 = (int(round(v)) for v in r)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(forma[1], x1), min(forma[0], y1)
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = True
    return m


def expandir(r, d):
    return (r[0] - d, r[1] - d, r[2] + d, r[3] + d)


def caja(mascara) -> tuple | None:
    ys, xs = np.nonzero(mascara)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


# ---------------------------------------------------------------------------
# Diferencias entre cuadros
# ---------------------------------------------------------------------------

def _bloques(m: np.ndarray, t: int) -> np.ndarray:
    h, w = m.shape[:2]
    h2, w2 = h // t * t, w // t * t
    if h2 == 0 or w2 == 0:
        return m.reshape(1, -1).mean(axis=1, keepdims=True)
    return m[:h2, :w2].reshape(h2 // t, t, w2 // t, t).mean(axis=(1, 3))


def diferencia(a: np.ndarray, b: np.ndarray, bloque: int = 16) -> dict:
    """Mide cuánto difieren dos cuadros. Veredicto con el mismo criterio que
    armar/comparar_cuadros.py: IDÉNTICOS (ni un píxel), IGUALES A LA VISTA (PSNR ≥ 40 dB y
    menos del 0,05 % de píxeles con más de 24 de diferencia) o DISTINTOS.
    Además: `bloque_max`, el error absoluto medio del peor bloque de 16x16 (un movimiento
    chico concentrado lo sube mucho; el ruido de compresión, poco), y `bloque_signo_max`,
    el del error con signo (un fundido que no terminó lo sube; el ruido se cancela)."""
    if a.shape != b.shape:
        return {"veredicto": "DISTINTOS", "motivo": f"tamaños {a.shape[1]}x{a.shape[0]} y {b.shape[1]}x{b.shape[0]}",
                "max": 255, "psnr": 0.0, "notables_pct": 100.0, "bloque_max": 255.0, "bloque_signo_max": 765.0,
                "caja": None}
    ai, bi = a.astype(np.int16), b.astype(np.int16)
    d = ai - bi
    dmax = np.abs(d).max(axis=2)
    m = int(dmax.max())
    if m == 0:
        return {"veredicto": "IDÉNTICOS", "max": 0, "psnr": math.inf, "notables_pct": 0.0, "bloque_max": 0.0,
                "bloque_signo_max": 0.0, "caja": None}
    mse = float((d.astype(np.float64) ** 2).mean())
    psnr = 10 * math.log10(255 ** 2 / mse) if mse else math.inf
    notables = float((dmax > 24).mean() * 100)
    bmax = float(_bloques(dmax.astype(np.float32), bloque).max())
    bsig = float(np.abs(_bloques(d.sum(axis=2).astype(np.float32), bloque)).max())
    veredicto = "IGUALES A LA VISTA" if psnr >= 40 and notables < 0.05 else "DISTINTOS"
    return {"veredicto": veredicto, "max": m, "psnr": psnr, "notables_pct": notables, "bloque_max": bmax,
            "bloque_signo_max": bsig, "caja": caja(dmax > 8)}


def cambio_bloques(a: np.ndarray, b16: np.ndarray, bloque: int = 16) -> tuple:
    """Versión liviana de diferencia() para comparar muchos cuadros contra uno solo
    (b16 = ese cuadro en int16): solo (bloque_max, bloque_signo_max)."""
    d = a.astype(np.int16)
    d -= b16
    m = np.abs(d).max(axis=2)
    s = d.sum(axis=2, dtype=np.int32)
    return (float(_bloques(m.astype(np.float32), bloque).max()),
            float(np.abs(_bloques(s.astype(np.float32), bloque)).max()))


def mapa_diferencia(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Imagen de la diferencia, amplificada para que se vea (×6, en rojo sobre gris)."""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    base = (a.astype(np.float32).mean(axis=2) * 0.35).astype(np.uint8)
    out = np.stack([base, base, base], axis=2).astype(np.int16)
    amp = np.clip(d * 6, 0, 255)
    out[..., 0] = np.maximum(out[..., 0], amp)
    out[..., 1] = np.where(amp > 0, out[..., 1] // 2, out[..., 1])
    out[..., 2] = np.where(amp > 0, out[..., 2] // 2, out[..., 2])
    return out.clip(0, 255).astype(np.uint8)


def fmt_num(x, dec: int = 1) -> str:
    """Número con coma decimal, como el resto de la documentación."""
    if x is None:
        return "—"
    if isinstance(x, float) and math.isinf(x):
        return "∞"
    return f"{x:.{dec}f}".replace(".", ",")
