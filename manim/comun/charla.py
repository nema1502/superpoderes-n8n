"""Base de las diapositivas de Manim de la charla.

El mismo sistema visual que Remotion (docs/convenciones.md), del lado de Manim. Todo sale
de diseno/tokens.json y de contenido/deck.json, y todo se escribe en px del cuadro de
1920x1080 con el origen arriba a la izquierda, como el «Cuadro final» del guion:

- configuración: 1920x1080, 30 fps, 1 u = 135 px exactos (cuadro de 14,222… × 8 u), fondo
  tinta, secciones guardadas y pedazos sin pérdida (sin_perdida.py);
- `Texto`: XeLaTeX con Segoe UI Bold (la misma fuente, el mismo kerning y el mismo
  espaciado que Chrome), tamaño en px y ubicado con la regla de `<Texto>` de Remotion
  (x según `alinear`, y = centro óptico del renglón). Calibrado contra Remotion: ver
  `docs/convenciones.md` §11 y `manim/calibrar.py`;
- el movimiento con los mismos números que Remotion: el resorte de `spring()` portado tal
  cual, las curvas de Easing y los tramos en cuadros enteros (`Tramo`, `DiapoCharla.tocar`);
- `DiapoCharla`: un paso = una sección que dura lo que dice deck.json y termina quieta; la
  marca de agua y el chip de piso como PNG de diseno/assets/ en su píxel; la entrada
  continua desde el último cuadro de la diapositiva anterior.

Uso mínimo (ver manim/escenas/d07_cuanto_cabe.py):

    from charla import *

    class D07CuantoCabe(DiapoCharla):
        ID = "D07"
        def construct(self):
            t = textos("D07", 1)
            self.paso(1)
            titulo = Texto(t[0], 960, 300, tam=105, alinear="centro")
            self.tocar(self.salir_anterior(0, 0.4), Entrar(titulo, 0.2))
            self.paso(2)
            ...

Se renderiza con `<python del entorno> manim/render_diapo.py <ID>` (ver docs/ESTADO.md).
"""

from __future__ import annotations

import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Animation,
    AnimationGroup,
    CapStyleType,
    Create,
    Group,
    ImageMobject,
    Line,
    Mobject,
    RoundedRectangle,
    Scene,
    Tex,
    TexTemplate,
    Transform,
    VGroup,
    VMobject,
    config,
    rate_functions,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sin_perdida  # noqa: E402

# ---------------------------------------------------------------------------
# Rutas y datos
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
TOKENS = json.loads((RAIZ / "diseno" / "tokens.json").read_text(encoding="utf-8"))
DECK = json.loads((RAIZ / "contenido" / "deck.json").read_text(encoding="utf-8"))
ASSETS = RAIZ / "diseno" / "assets"
PIEZAS = json.loads((ASSETS / "assets.json").read_text(encoding="utf-8"))["piezas"]
CUADROS = RAIZ / "render" / "cuadros"
MEDIA = RAIZ / "render" / "manim"

ANCHO = TOKENS["lienzo"]["ancho"]
ALTO = TOKENS["lienzo"]["alto"]
FPS = TOKENS["lienzo"]["fps"]
PX = float(TOKENS["tipografia"]["manim"]["px_por_unidad"])  # 135 px por unidad de Manim

# ---------------------------------------------------------------------------
# Configuración (al importar: la escena queda en el formato de la charla)
# ---------------------------------------------------------------------------


def configurar():
    """1920x1080 a 30 fps, 1 u = 135 px en los dos ejes, fondo tinta, secciones y pedazos sin
    pérdida. Los medios van a render/manim/ (el auditor y el render comparten la caché de TeX).
    Sin caché de animaciones: la de Manim no mira los píxeles de las imágenes (trampa 31)."""
    config.pixel_width = ANCHO
    config.pixel_height = ALTO
    config.frame_rate = FPS
    config.frame_width = ANCHO / PX  # 14,222… (estilo.configurar_horizontal usa 14,222: 1 u = 135,002 px)
    config.frame_height = ALTO / PX  # 8
    config.background_color = TOKENS["color"]["tinta"]["hex"]
    config.save_sections = True
    config.disable_caching = True
    config.media_dir = str(MEDIA)
    (MEDIA / "Tex").mkdir(parents=True, exist_ok=True)
    sin_perdida.activar()


configurar()

# ---------------------------------------------------------------------------
# Coordenadas: px del cuadro (origen arriba a la izquierda) <-> unidades de Manim
# ---------------------------------------------------------------------------


def punto(x: float, y: float) -> np.ndarray:
    """El punto de Manim del píxel (x, y) del cuadro."""
    return np.array([(x - ANCHO / 2) / PX, (ALTO / 2 - y) / PX, 0.0])


def u(px: float) -> float:
    """px a unidades de Manim."""
    return px / PX


def a_px(p) -> tuple[float, float]:
    """Un punto de Manim a px del cuadro."""
    return float(p[0]) * PX + ANCHO / 2, ALTO / 2 - float(p[1]) * PX


def caja_px(m: Mobject) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) en px de la caja de tinta de un mobject."""
    x0, y1 = a_px(m.get_corner(DOWN + LEFT))
    x1, y0 = a_px(m.get_corner(UP + RIGHT))
    return x0, y0, x1, y1


# ---------------------------------------------------------------------------
# Tokens: color, opacidad, tipografía, retícula, movimiento
# ---------------------------------------------------------------------------

COLOR = {k: v["hex"] for k, v in TOKENS["color"].items()}
TINTA = COLOR["tinta"]
HUESO = COLOR["hueso"]
AMBAR = COLOR["ambar"]
ROJO = COLOR["rojo"]
GRIS = COLOR["gris"]
ACERO = COLOR["acero"]
ACERO2 = COLOR["acero2"]
VIDRIO = COLOR["vidrio"]
PANTALLA = COLOR["pantalla"]
MARCA = COLOR["marca"]  # SOLO isotipo, marca de agua y firma: nunca contenido
# Los tres tonos del afiche de esta charla (tokens versión 3; uso en docs/ESTADO.md).
NOCHE = COLOR["noche"]    # azul noche: paneles, tarjetas y nodos de un flujo
TITULO = COLOR["titulo"]  # amarillo lima: solo títulos, sobre tinta
AZUL = COLOR["azul"]      # acento azul: conexiones, líneas de circuito, bordes de nodos

OPACIDAD = {k: v for k, v in TOKENS["opacidad"].items() if not k.startswith("_")}
TIPO = TOKENS["tipografia"]
ESCALA = TIPO["escala_px"]
MINIMO = TIPO["minimo_px"]
RETICULA = TOKENS["reticula"]
ZONA = RETICULA["zona_segura"]
RADIO = TOKENS["radio"]
GROSOR = TOKENS["grosor"]
MOV = TOKENS["movimiento"]
DURA = MOV["duracion_s"]
DESFASE = MOV["desfase_s"]
DISTANCIA = MOV["distancia_px"]
RESPIRO_S = TOKENS["pasos"]["respiro_s"]
ANIMACION_MAX_S = TOKENS["pasos"]["animacion_max_s"]

# Manim: px de fuente CSS = 1,873 × `tamano` de estilo.texto() (lo usa el auditor para el mínimo).
PX_POR_TAMANO = TIPO["manim"]["px_por_tamano"]


def px_de(tam) -> float:
    """px de un tamaño de la escala (`"lectura"` = 60, `"frase"` = 72…) o el número tal cual."""
    return float(ESCALA[tam]) if isinstance(tam, str) else float(tam)


def trazo(px: float) -> float:
    """stroke_width de Manim para un trazo de `px` píxeles (1 u = 135 px y Cairo multiplica por
    0,01 u: px = 1,35 × stroke_width)."""
    return px / (PX * 0.01)


def s(seg: float) -> int:
    """Segundos a cuadros (como `s()` de remotion/src/pasos.ts)."""
    return int(round(seg * FPS))


RESPIRO = s(RESPIRO_S)

# ---------------------------------------------------------------------------
# deck.json: textos, pasos, entradas y elementos fijos (la lógica de remotion/src/deck.ts)
# ---------------------------------------------------------------------------

IDS = [d["id"] for d in DECK["diapositivas"]]


def diapo(id_: str) -> dict:
    for d in DECK["diapositivas"]:
        if d["id"] == id_:
            return d
    raise KeyError(f"«{id_}» no está en deck.json (hay: {' '.join(IDS)})")


def textos(id_: str, paso: int) -> list[str]:
    """Los textos en pantalla del paso (1, 2…) tal cual están en deck.json. No se retocan: si uno
    no entra, se ajusta el diseño o se reporta."""
    d = diapo(id_)
    if not 1 <= paso <= len(d["pasos"]):
        raise IndexError(f"{id_} tiene {len(d['pasos'])} pasos: no hay paso {paso}")
    return list(d["pasos"][paso - 1]["texto_pantalla"])


def entrada(id_: str) -> dict:
    """Cómo entra la diapositiva: {"tipo", "duracion_s", "desde"} (deck.json → entrada)."""
    i = IDS.index(id_)
    d = diapo(id_)
    e = d.get("entrada") or {"tipo": "corte" if i == 0 else "continuo", "duracion_s": 0}
    desde = e["desde"] if "desde" in e else (None if i <= 0 else IDS[i - 1])
    return {"tipo": e["tipo"], "duracion_s": e.get("duracion_s", 0) or 0, "desde": desde}


def marca_en(id_: str, k: int) -> bool:
    sin = TOKENS["persistentes"]["marca_agua_sin"]
    return not (id_ in sin or f"{id_}.{k}" in sin)


def chip_en(id_: str):
    p = diapo(id_).get("piso")
    return None if p is None else str(p)


def estado_previo(id_: str) -> dict:
    """Marca de agua y chip justo antes del paso 1 (los del último paso de la anterior si la
    entrada es continua; si no, los del paso 1)."""
    e = entrada(id_)
    if e["tipo"] == "continuo" and e["desde"]:
        n = len(diapo(e["desde"])["pasos"])
        return {"marca": marca_en(e["desde"], n), "chip": chip_en(e["desde"])}
    return {"marca": marca_en(id_, 1), "chip": chip_en(id_)}


def duraciones_propias(id_: str) -> list[float]:
    """Duración (s) del video propio de cada paso: la de deck.json; en el paso 1 se descuenta la
    transición (fundido o puertas), que es otro video."""
    d = diapo(id_)
    e = entrada(id_)
    desc = e["duracion_s"] if e["tipo"] in ("fundido", "puertas") else 0
    return [round((p["duracion_animacion_s"] - (desc if k == 0 else 0)) * 1000) / 1000 for k, p in enumerate(d["pasos"])]


# ---------------------------------------------------------------------------
# Curvas y resortes: los de Remotion, con los mismos números
# ---------------------------------------------------------------------------


def _cubica(t):
    return t * t * t


def _seno(t):
    return 1 - math.cos(t * math.pi / 2)


def _in_out(f):
    return lambda t: f(t * 2) / 2 if t < 0.5 else 1 - f((1 - t) * 2) / 2


def _out(f):
    return lambda t: 1 - f(1 - t)


_EASING = {
    "inOut(cubic)": _in_out(_cubica),
    "out(cubic)": _out(_cubica),
    "in(cubic)": _cubica,
    "linear": lambda t: t,
    "inOut(sin)": _in_out(_seno),
}


def _curva_de(nombre: str):
    f = _EASING[MOV["curvas"][nombre]["remotion"]]

    def curva(t):
        return f(min(1.0, max(0.0, t)))

    curva.__name__ = f"curva_{nombre}"
    return curva


CURVA = {k: _curva_de(k) for k in MOV["curvas"] if not k.startswith("_")}

_RESORTE_FABRICA = {"damping": 10.0, "mass": 1.0, "stiffness": 100.0}
RESORTE = {k: {**_RESORTE_FABRICA, **v} for k, v in MOV["resortes"].items()}


def _avanzar(anim, ahora, c, m, k):
    """advance() de remotion/dist/cjs/spring/spring-utils.js (4.0.532), operación por operación."""
    hacia, ultimo, actual, vel = anim
    dt = min(ahora - ultimo, 64)
    v0 = -vel
    x0 = hacia - actual
    zeta = c / (2 * math.sqrt(k * m))
    w0 = math.sqrt(k / m)
    t = dt / 1000
    if zeta < 1:
        w1 = w0 * math.sqrt(1 - zeta**2)
        sin1 = math.sin(w1 * t)
        cos1 = math.cos(w1 * t)
        env = math.exp(-zeta * w0 * t)
        frag = env * (sin1 * ((v0 + zeta * w0 * x0) / w1) + x0 * cos1)
        pos = hacia - frag
        nv = zeta * w0 * frag - env * (cos1 * (v0 + zeta * w0 * x0) - w1 * x0 * sin1)
    else:
        env = math.exp(-w0 * t)
        pos = hacia - env * (x0 + (v0 + w0 * x0) * t)
        nv = env * (v0 * (t * w0 - 1) + t * x0 * w0 * w0)
    return (hacia, ahora, pos, nv)


@lru_cache(maxsize=None)
def _resorte_en(cuadro: float, c: float, m: float, k: float) -> float:
    """springCalculation(): posición del resorte (0 → 1) en un cuadro (puede ser fraccionario)."""
    anim = (1.0, 0.0, 0.0, 0.0)
    fc = max(0.0, cuadro)
    resto = fc % 1
    for f in range(int(math.floor(fc)) + 1):
        anim = _avanzar(anim, f / FPS * 1000, c, m, k)
    if resto > 0:
        anim = _avanzar(anim, fc / FPS * 1000, c, m, k)
    return anim[2]


@lru_cache(maxsize=None)
def _duracion_natural(c: float, m: float, k: float, umbral: float = 0.005) -> int:
    """measureSpring(): cuadros hasta que el resorte queda quieto dentro del umbral."""
    cuadro = 0
    dif = abs(_resorte_en(cuadro, c, m, k) - 1)
    while dif >= umbral:
        cuadro += 1
        dif = abs(_resorte_en(cuadro, c, m, k) - 1)
    terminado = cuadro
    i = 0
    while i < 20:
        cuadro += 1
        dif = abs(_resorte_en(cuadro, c, m, k) - 1)
        if dif >= umbral:
            i = 0
            terminado = cuadro + 1
        i += 1
    return terminado


def resorte(cuadro: float, n: int, nombre: str = "entrar") -> float:
    """spring({frame: cuadro, fps: 30, config: RESORTE[nombre], durationInFrames: n}) de Remotion."""
    r = RESORTE[nombre]
    c, m, k = float(r["damping"]), float(r["mass"]), float(r["stiffness"])
    if cuadro > n:
        return 1.0
    natural = _duracion_natural(c, m, k)
    return _resorte_en(cuadro / (n / natural), c, m, k)


def entra(cuadro: float, n: int, nombre: str = "entrar") -> float:
    """useEntra(): 0 antes del tramo, exactamente 1 al final, el resorte en el medio."""
    if cuadro <= 0:
        return 0.0
    if cuadro >= n:
        return 1.0
    return resorte(cuadro, n, nombre)


# ---------------------------------------------------------------------------
# Texto: XeLaTeX con Segoe UI Bold, en px y en el lugar de <Texto> de Remotion
# ---------------------------------------------------------------------------

# El cuerpo se compone a 100 pt (más cifras significativas en el SVG de dvisvgm) y se escala
# después: lo que importa es el em. Dos reglas de 1 em de alto, sin ancho (\rlap y \llap), marcan
# el comienzo del renglón, su línea base y el final del avance: con ellas el texto se ubica como
# lo ubica Chrome (por la línea base y el avance), no por la caja de tinta, que cambia con las
# letras. Después se quitan.
EM_PT = 100
_ARCHIVO_FUENTE = Path(TIPO["archivo"])
PLANTILLA_TEXTO = TexTemplate(
    tex_compiler="xelatex",
    output_format=".xdv",
    documentclass=r"\documentclass[preview]{standalone}",
    preamble="\n".join(
        [
            r"\usepackage{fontspec}",
            # El archivo de la fuente (no el nombre): el mismo segoeuib.ttf que usa Chrome.
            # Ligatures=TeXOff: «--», «''» o «?`» quedan como se escribieron (como en Chrome).
            rf"\setmainfont{{{_ARCHIVO_FUENTE.name}}}[Path={_ARCHIVO_FUENTE.parent.as_posix()}/, Ligatures=TeXOff]",
            # Sin espacio extra después de los puntos (Chrome no lo pone).
            r"\frenchspacing",
            # Cada parte se compone en una caja horizontal: sin cortes de renglón ni guiones.
            r"\newenvironment{renglon}{\leavevmode\hbox\bgroup\ignorespaces}{\unskip\egroup}",
            rf"\AtBeginDocument{{\fontsize{{{EM_PT}pt}}{{{int(EM_PT * 1.2)}pt}}\selectfont}}",
        ]
    ),
)
_REGLA_I = rf"\rlap{{\rule{{4pt}}{{{EM_PT}pt}}}}"
_REGLA_D = rf"\llap{{\rule{{4pt}}{{{EM_PT}pt}}}}"

# La línea base, como la pone Chrome en <Texto> de Remotion (medido con manim/calibrar.py el
# 23-oct-2026; ver docs/convenciones.md §11). El renglón es una caja de alto lh = round(tam ×
# interlineado) cuyo borde de arriba está en y − lh/2 − 0,07·tam (la corrección óptica); Blink
# redondea el ascenso y el descenso de la fuente a px enteros, reparte el interlineado sobrante
# por mitades (la de arriba hacia abajo: floor) y dibuja los glifos con la línea base en un píxel
# entero. Medido en 11 muestras de 49 a 105 px: el modelo coincide con Chrome a ±0,35 px (el error
# de la medición), y la fórmula continua y + 0,344·tam erraba hasta 0,9 px.
_FUENTE_METRICAS = None


def _metricas_fuente() -> tuple[float, float]:
    """Ascenso y descenso de segoeuib.ttf en em (hhea/OS2: 2210 y 514 de 2048)."""
    global _FUENTE_METRICAS
    if _FUENTE_METRICAS is None:
        from PIL import ImageFont

        f = ImageFont.truetype(str(_ARCHIVO_FUENTE), 2048)
        asc, desc = f.getmetrics()
        _FUENTE_METRICAS = (asc / 2048, desc / 2048)
    return _FUENTE_METRICAS


def _redondear_js(v: float) -> int:
    """Math.round de JavaScript (la mitad, hacia arriba)."""
    return math.floor(v + 0.5)


def interlineado_de(tam: float) -> float:
    """Interlineado por defecto según el tamaño (interlineadoDe de Remotion): títulos 1,1; ideas y
    frases 1,25; lectura 1,3."""
    il = TIPO["interlineado"]
    if tam >= ESCALA["grande"]:
        return il["titulo"]
    if tam >= ESCALA["idea_arriba"]:
        return il["idea"]
    return il["lectura"]


def linea_base(y: float, tam: float, renglon: int = 0, renglones: int = 1, interlineado: float | None = None,
               ancla_y: str = "centro") -> float:
    """px de la línea base del renglón `renglon` de un <Texto> de Remotion anclado en `y`."""
    asc_em, desc_em = _metricas_fuente()
    lh = _redondear_js(tam * (interlineado if interlineado is not None else interlineado_de(tam)))
    arriba = (y - lh / 2 if ancla_y == "primero" else y - lh * renglones / 2) - TIPO["correccion_optica_em"] * tam
    asc, desc = _redondear_js(asc_em * tam), _redondear_js(desc_em * tam)
    medio_interlineado = math.floor((lh - asc - desc) / 2)
    return float(_redondear_js(arriba + renglon * lh + medio_interlineado + asc))


# Con False, la fórmula continua (solo para comparar en la calibración).
BASE_COMO_CHROME = True
K_BASE = 0.34406  # (ascenso − descenso)/2 − 0,07 em: la línea base sin redondeos

# Trazo (px) del mismo color alrededor de cada glifo, para igualar el peso con el que Chrome
# dibuja el texto: su antialias en gris lo engorda (sin trazo, Manim tenía 1,5 a 6 % menos tinta,
# más en el texto claro). Calibrado por color: con estos valores la tinta queda a ±2 % (ver
# convenciones §11). Un número suelto vale para todos los colores; 0 = solo el relleno.
REFUERZO_PX: float | dict = {HUESO: 0.4, AMBAR: 0.3, GRIS: 0.3, "otro": 0.35}


def _refuerzo(color: str) -> float:
    if isinstance(REFUERZO_PX, dict):
        return float(REFUERZO_PX.get(color, REFUERZO_PX.get(color.upper(), REFUERZO_PX.get("otro", 0.0))))
    return float(REFUERZO_PX)


_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "%": r"\%",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escapar_tex(cadena: str) -> str:
    """El texto tal cual, para TeX (los caracteres especiales escapados)."""
    return "".join(_ESCAPES.get(c, c) for c in cadena)


def ancho_disponible(x: float, alinear: str) -> float:
    """Ancho que deja la zona segura para un texto anclado en x (anchoDisponible de Remotion)."""
    if alinear == "izq":
        return ZONA["x1"] - x
    if alinear == "der":
        return x - ZONA["x0"]
    return 2 * min(x - ZONA["x0"], ZONA["x1"] - x)


def _segmentar(cadena: str, partes, resaltar, color) -> list[tuple[str, str]]:
    """Corta el texto en partes (para TransformarPorPartes y para los colores)."""
    if partes is None:
        partes = [cadena]
    if "".join(partes) != cadena:
        raise ValueError(f"Texto: las partes {partes!r} no forman «{cadena}» letra por letra")
    segs = [(p, color) for p in partes if p]
    if resaltar:
        mapa = (
            {resaltar: AMBAR}
            if isinstance(resaltar, str)
            else ({r: AMBAR for r in resaltar} if isinstance(resaltar, (list, tuple)) else dict(resaltar))
        )
        for parte, c in mapa.items():
            if parte not in cadena:
                raise ValueError(f"Texto: «{parte}» no aparece en «{cadena}» (el resaltado tiene que coincidir letra por letra)")
            nuevos = []
            for txt, col in segs:
                while parte in txt:
                    i = txt.index(parte)
                    if txt[:i]:
                        nuevos.append((txt[:i], col))
                    nuevos.append((parte, c))
                    txt = txt[i + len(parte) :]
                if txt:
                    nuevos.append((txt, col))
            if not any(t == parte for t, _ in nuevos):
                raise ValueError(f"Texto: «{parte}» cruza el límite de dos partes en «{cadena}»")
            segs = nuevos
    if "  " in cadena:
        raise ValueError(f"Texto: «{cadena}» tiene dos espacios seguidos (TeX los junta y Chrome no)")
    # Una parte que es solo espacio no tiene tinta: se pega a la anterior (o a la siguiente).
    juntos: list[tuple[str, str]] = []
    for txt, col in segs:
        if not txt.strip() and juntos:
            juntos[-1] = (juntos[-1][0] + txt, juntos[-1][1])
        elif juntos and not juntos[-1][0].strip():
            juntos[-1] = (juntos[-1][0] + txt, col)
        else:
            juntos.append((txt, col))
    return juntos


class Texto(Tex):
    """Un renglón de texto en Segoe UI Bold, como `<Texto>` de Remotion.

    - `cadena`: el texto exacto (de `textos(id, paso)`).
    - `x`, `y`: `x` según `alinear` ("izq", "centro", "der"); `y` = centro óptico del renglón.
    - `tam`: px o nombre de la escala ("lectura" = 60, "frase" = 72…).
    - `partes`: cortes del texto (con sus espacios) para transformarlo por partes; la clave de
      cada parte es su texto sin espacios en los bordes.
    - `resaltar`: "palabra" (ámbar), ["X", "Y"] o {"funcionó": AMBAR, "reescribir": ROJO}.
    - Nunca sale de la zona segura: si no entra, se achica hasta `minimo` (60 en lectura, 49 en
      rótulos) con un AVISO, o falla con el texto culpable. El texto no se cambia.

    Queda con `izquierda`, `derecha` y `base` (px del renglón: comienzo y fin del avance, línea
    base), `tam`, `claves` y `parte(clave)`; y con `es_texto`, `texto_auditor` y
    `tamano_efectivo` para que el auditor lo juzgue como un texto.
    """

    def __init__(self, cadena: str, x: float, y: float, tam="lectura", color: str = HUESO, alinear: str = "izq",
                 partes=None, resaltar=None, ancho: float | None = None, minimo: float | None = None, **kw):
        tam_px = px_de(tam)
        minimo_px = minimo if minimo is not None else (MINIMO["lectura"] if tam_px >= MINIMO["lectura"] else MINIMO["rotulo"])
        if tam_px < MINIMO["rotulo"] and (minimo is None or minimo > tam_px):
            raise ValueError(f"Texto «{cadena}» a {tam_px:g} px: el mínimo es {MINIMO['rotulo']} px (rótulos) y {MINIMO['lectura']} px (lectura).")
        segs = _segmentar(cadena, partes, resaltar, color)
        self.claves = [t.strip() for t, _ in segs]
        super().__init__(_REGLA_I, *[escapar_tex(t) for t, _ in segs], _REGLA_D,
                         tex_template=PLANTILLA_TEXTO, tex_environment="renglon", arg_separator="", **kw)
        # Las partes se cortan contando glifos (Manim compila cada parte aparte): se comprueba.
        for (txt, _), sub in zip(segs, self.submobjects[1:-1]):
            esperado = len("".join(txt.split()))
            if len(sub.submobjects) != esperado:
                raise ValueError(f"Texto «{cadena}»: la parte «{txt}» dio {len(sub.submobjects)} glifos y tiene {esperado} letras "
                                 "(¿una ligadura o un carácter que la fuente no tiene?)")
        regla_i, regla_d = self.submobjects[0], self.submobjects[-1]
        if len(regla_i.submobjects) != 1 or len(regla_d.submobjects) != 1:
            raise ValueError(f"Texto «{cadena}»: no se encontraron las reglas de referencia")
        avance_em = (regla_d.get_right()[0] - regla_i.get_left()[0]) / regla_i.height
        # Ancho disponible y achique (como disponerTexto de Remotion: de a 2 px arriba de 80, de a 1 abajo).
        max_ancho = min(ancho if ancho is not None else math.inf, ancho_disponible(x, alinear))
        if max_ancho <= 0:
            raise ValueError(f"Texto «{cadena}»: x = {x} queda fuera de la zona segura ({ZONA['x0']}-{ZONA['x1']}).")
        t = tam_px
        while avance_em * t > max_ancho + 0.5:
            t -= 2 if t > 80 else 1
            if t < min(minimo_px, tam_px):
                raise ValueError(f"El texto «{cadena}» no entra: a {tam_px:g} px mide {avance_em * tam_px:.0f} px y el lugar es de "
                                 f"{max_ancho:.0f} px, sin bajar de {minimo_px:g} px. No cambiar el texto: ajustar el diseño o reportarlo.")
        if t != tam_px:
            print(f"AVISO: «{cadena}» se achicó de {tam_px:g} a {t:g} px para entrar en {max_ancho:.0f} px.")
        tam_px = t
        # Escala: 1 em = tam_px px.
        self.scale((tam_px / PX) / regla_i.height, about_point=ORIGIN)
        avance = avance_em * tam_px
        izquierda = x if alinear == "izq" else (x - avance / 2 if alinear == "centro" else x - avance)
        base = linea_base(y, tam_px) if BASE_COMO_CHROME else y + K_BASE * tam_px
        origen = np.array([regla_i.get_left()[0], regla_i.get_bottom()[1], 0.0])
        self.shift(punto(izquierda, base) - origen)
        self.remove(regla_i, regla_d)
        self.tex_strings = self.tex_strings[1:-1]
        for (_, col), sub in zip(segs, self.submobjects):
            sub.set_fill(col, opacity=1)
            refuerzo = _refuerzo(col)
            if refuerzo > 0:
                sub.set_stroke(col, width=trazo(refuerzo), opacity=1)
            else:
                sub.set_stroke(width=0)
        self.texto = cadena
        self.tam = tam_px
        self.izquierda, self.derecha, self.base = izquierda, izquierda + avance, base
        self.avance = avance
        self.es_texto = True
        self.texto_auditor = cadena
        self.tamano_efectivo = tam_px / PX_POR_TAMANO

    def parte(self, clave: str) -> VMobject:
        """La parte cuyo texto (sin espacios en los bordes) es `clave`."""
        idx = [i for i, k in enumerate(self.claves) if k == clave]
        if len(idx) != 1:
            raise KeyError(f"Texto «{self.texto}»: la parte «{clave}» aparece {len(idx)} veces (partes: {self.claves})")
        return self.submobjects[idx[0]]

    def centro_parte_px(self, clave: str) -> float:
        """x (px) del centro de la tinta de una parte."""
        x0, _, x1, _ = caja_px(self.parte(clave))
        return (x0 + x1) / 2


def altura_mayuscula(tam) -> float:
    """Alto de la mayúscula en px (Segoe UI Bold: 0,7 em)."""
    return TIPO["mayuscula_em"] * px_de(tam)


# ---------------------------------------------------------------------------
# Formas en px
# ---------------------------------------------------------------------------


def rect_borde(cx: float, cy: float, ancho: float, alto: float, radio: float, grosor: float, color: str = AMBAR,
               relleno: str | None = None, opacidad_relleno: float = 0.0) -> RoundedRectangle:
    """Rectángulo redondeado como un <div> de Remotion con `boxSizing: border-box`: la caja
    exterior mide ancho × alto con radio `radio`, y el borde de `grosor` px va hacia adentro."""
    r = RoundedRectangle(
        width=u(ancho - grosor), height=u(alto - grosor), corner_radius=u(max(0.0, radio - grosor / 2)),
        stroke_color=color, stroke_width=trazo(grosor),
        fill_color=relleno or color, fill_opacity=opacidad_relleno,
    )
    r.move_to(punto(cx, cy))
    r.auditor_ignorar = False
    return r


def linea(x0: float, y0: float, x1: float, y1: float, grosor: float = GROSOR["borde_fino"], color: str = GRIS,
          conector: bool = False) -> Line:
    """Una línea recta en px (sin flecha). Por defecto es un trazo de dibujo (subrayado, tachado,
    marco) y el auditor no la juzga; con `conector=True` une dos cosas y el auditor mira que no
    quede corta, suelta ni cruzando un texto."""
    ln = Line(punto(x0, y0), punto(x1, y1), stroke_color=color, stroke_width=trazo(grosor))
    ln.auditor_ignorar = not conector
    return ln


def linea_subrayado(y: float, tam) -> float:
    """y del subrayado de un Texto anclado en y (lineaSubrayado de Remotion)."""
    return y + (TIPO["mayuscula_em"] / 2 + 0.13) * px_de(tam)


def linea_tachado(y: float, tam) -> float:
    """y del tachado de un Texto anclado en y: cruza las minúsculas por el medio (lineaTachado)."""
    return y + 0.06 * px_de(tam)


def subrayado(x0: float, x1: float, y: float, color: str = AMBAR, grosor: float = GROSOR["subrayado"], trazos=None) -> VMobject:
    """Subrayado como el de Remotion: ámbar de 5 px (el trazo normal) con puntas redondas;
    `trazos=(largo, hueco)` en px lo hace a trazos (D09.3: «haciendo» a trazos grises)."""
    if trazos:
        largo, hueco = trazos
        total = x1 - x0
        n = max(1, int((total + hueco) // (largo + hueco)))
        ln = VGroup(*[Line(punto(x0 + i * (largo + hueco), y), punto(min(x1, x0 + i * (largo + hueco) + largo), y),
                           stroke_color=color, stroke_width=trazo(grosor)) for i in range(n)])
    else:
        ln = Line(punto(x0, y), punto(x1, y), stroke_color=color, stroke_width=trazo(grosor))
        ln.set_cap_style(CapStyleType.ROUND)
    for m in ln.get_family():
        m.auditor_ignorar = True
    return ln


def tachado(x0: float, x1: float, y: float, color: str = ROJO, grosor: float = GROSOR["tachado"],
            filete: float = GROSOR["tachado_filete"]) -> VMobject:
    """Tachado rojo de 7 px (el trazo fuerte) con puntas redondas y un filete de tinta de 3 px a cada
    lado que corta las letras (Tachado de Remotion): el rojo tiene la misma luz que el gris, y sin el
    filete se separaba de las letras solo por el tono. El texto tachado va en hueso al 55 %
    (OPACIDAD["tachado_texto"]). Se dibuja (Trazo) como un solo objeto: el filete debajo del rojo."""
    rojo = subrayado(x0, x1, y, color, grosor)
    if filete <= 0:
        return rojo
    fondo = subrayado(x0, x1, y, TINTA, grosor + 2 * filete)
    g = VGroup(fondo, rojo)
    for m in g.get_family():
        m.auditor_ignorar = True
    return g


def corchete(x0: float, x1: float, y: float, alto: float = 10, grosor: float = GROSOR["borde_fino"], color: str = GRIS) -> VMobject:
    """Un corchete abierto hacia arriba (⌴) de x0 a x1 en y, con patas de `alto` px: marca la palabra
    de arriba para el rótulo de abajo. Se dibuja de la pata izquierda a la derecha."""
    c = VMobject(stroke_color=color, stroke_width=trazo(grosor), fill_opacity=0)
    c.set_points_as_corners([punto(x0, y - alto), punto(x0, y), punto(x1, y), punto(x1, y - alto)])
    c.auditor_ignorar = True
    return c


# ---------------------------------------------------------------------------
# Imágenes en su píxel exacto (marca de agua, chip, cuadro anterior)
# ---------------------------------------------------------------------------


def imagen_en(ruta, x: int, y: int) -> ImageMobject:
    """Un PNG con su esquina de arriba a la izquierda en el píxel (x, y), sin remuestrear.

    La cámara de Manim trunca las esquinas a píxeles enteros y redimensiona la imagen a esa caja:
    con las esquinas corridas 0,001 px hacia abajo y a la derecha, la caja sale exactamente del
    tamaño del PNG y la imagen se pega tal cual (comprobado: cuadro idéntico al PNG)."""
    img = ImageMobject(str(ruta))
    h, w = img.pixel_array.shape[:2]
    e = 1e-3
    img.points = np.array([punto(x + e, y + e), punto(x + w + e, y + e), punto(x + e, y + h + e), punto(x + w + e, y + h + e)])
    img.set_resampling_algorithm(0)  # vecino más cercano si alguna vez hiciera falta remuestrear
    img.ancho_px, img.alto_px = w, h
    img.x_px, img.y_px = x, y
    img.ruta = str(ruta)
    return img


def pieza(nombre: str, opaca: bool = True) -> ImageMobject:
    """Una pieza de diseno/assets/ en su píxel: "marca_agua", "chip_piso_1"… Opaca = el recorte
    sobre tinta (idéntico al píxel a Remotion); transparente para animarla encima de algo."""
    p = PIEZAS[nombre]
    archivo = p["archivos"]["tinta" if opaca else "transparente"]
    img = imagen_en(ASSETS / archivo, p["x"], p["y"])
    img.auditor_ignorar = True
    img.set_z_index(1000)
    return img


# ---------------------------------------------------------------------------
# Animaciones (el vocabulario de movimiento, con los números de Remotion)
# ---------------------------------------------------------------------------


class Tramo:
    """Una animación ubicada en el tiempo de su segmento: empieza `retraso` s después del
    comienzo del segmento y dura `dura` s (en cuadros enteros, como `tramoDe` de Remotion)."""

    def __init__(self, anim: Animation, retraso: float, dura: float):
        if retraso < 0:
            raise ValueError(f"Tramo con retraso negativo ({retraso} s)")
        if dura > ANIMACION_MAX_S + 1e-9:
            raise ValueError(f"Una animación dura {dura} s; el máximo es {ANIMACION_MAX_S} s")
        self.anim = anim
        self.ini = s(retraso)
        self.n = max(1, s(dura))

    @property
    def fin(self) -> int:
        return self.ini + self.n


def _opacidades(m: Mobject):
    return [(x.get_fill_opacity(), x.get_stroke_opacity()) for x in m.family_members_with_points()]


def _aplicar_opacidad(m: Mobject, base, k: float):
    for x, (f, st) in zip(m.family_members_with_points(), base):
        x.set_fill(opacity=f * k)
        x.set_stroke(opacity=st * k)


class _Entrar(Animation):
    """Entrar de Remotion (useEntrar): resorte damping 15 / mass 0,7 en n cuadros, opacidad
    min(1, 1,5·p) y sube (1 − p)·60 px (o entra 40 px de costado)."""

    def __init__(self, m: Mobject, n: int, desde: str = "abajo", distancia: float | None = None, dueno: Mobject | None = None, **kw):
        lateral = desde in ("izq", "der")
        d = distancia if distancia is not None else (DISTANCIA["entrar_lateral"] if lateral else DISTANCIA["entrar"])
        self.desplazo = {"abajo": DOWN, "arriba": UP, "izq": LEFT, "der": RIGHT}[desde] * u(d)
        self.n = n
        self.dueno = dueno
        super().__init__(m, introducer=True, rate_func=rate_functions.linear, **kw)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        if self.dueno is not None:
            # Entró una parte: al final queda en escena el Texto entero (para el auditor y para lo
            # que venga después, que lo mueve como una unidad).
            scene.add(self.dueno)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        cuadro = alpha * self.n
        if abs(cuadro - round(cuadro)) < 1e-9:
            cuadro = round(cuadro)
        p = entra(cuadro, self.n, "entrar")
        self.mobject.become(self.objetivo)
        if p < 1:
            self.mobject.shift(self.desplazo * (1 - p))
        _aplicar_opacidad(self.mobject, self.base, min(1.0, 1.5 * p))


def Entrar(m: Mobject, retraso: float = 0.0, dura: float = DURA["entrar"], desde: str = "abajo", distancia=None) -> Tramo:
    """Entrar (casi todo el texto): ver _Entrar."""
    return Tramo(_Entrar(m, s(dura), desde, distancia), retraso, dura)


def EntrarPartes(t: Texto, retraso: float = 0.0, desfase: float = DESFASE["palabras"], dura: float = DURA["entrar"]) -> list[Tramo]:
    """Entrar parte por parte (palabra por palabra si las partes son palabras), desfase 0,12 s."""
    return [Tramo(_Entrar(p, s(dura), dueno=t), retraso + i * desfase, dura) for i, p in enumerate(t.submobjects)]


class _Fundido(Animation):
    """Opacidad de `desde` a `hasta` (relativa a la que tenía) con una curva."""

    def __init__(self, m: Mobject, desde: float, hasta: float, curva, introducer=False, remover=False, **kw):
        self.desde, self.hasta, self.curva = desde, hasta, curva
        super().__init__(m, introducer=introducer, remover=remover, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        k = self.desde + (self.hasta - self.desde) * self.curva(alpha)
        _aplicar_opacidad(self.mobject, self.base, k)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        if self.remover:
            # Si vuelve a la escena, que vuelva con su opacidad.
            _aplicar_opacidad(self.mobject, self.base, 1.0)


def Aparecer(m: Mobject, retraso: float = 0.0, dura: float = DURA["desvanecer"]) -> Tramo:
    """Aparece con un fundido (inOut seno), sin moverse."""
    return Tramo(_Fundido(m, 0.0, 1.0, CURVA["fundido"], introducer=True), retraso, dura)


def Desvanecer(m: Mobject, retraso: float = 0.0, dura: float = DURA["desvanecer"]) -> Tramo:
    """Se va con un fundido (inOut seno) y sale de la escena."""
    return Tramo(_Fundido(m, 1.0, 0.0, CURVA["fundido"], remover=True), retraso, dura)


class _FundidoImagen(Animation):
    """Fundido de un ImageMobject tocando su canal alfa (set_opacity lo pisaría entero)."""

    def __init__(self, img: ImageMobject, desde: float, hasta: float, curva, introducer=False, remover=False, **kw):
        self.desde, self.hasta, self.curva = desde, hasta, curva
        self.alfa = img.pixel_array[:, :, 3].astype(np.float64)
        super().__init__(img, introducer=introducer, remover=remover, rate_func=rate_functions.linear, **kw)

    def interpolate_mobject(self, alpha: float):
        k = self.desde + (self.hasta - self.desde) * self.curva(alpha)
        self.mobject.pixel_array[:, :, 3] = np.clip(np.round(self.alfa * k), 0, 255).astype(np.uint8)


def DesvanecerImagen(img: ImageMobject, retraso: float = 0.0, dura: float = DURA["fundido"]) -> Tramo:
    return Tramo(_FundidoImagen(img, 1.0, 0.0, CURVA["fundido"], remover=True), retraso, dura)


def AparecerImagen(img: ImageMobject, retraso: float = 0.0, dura: float = DURA["fundido"]) -> Tramo:
    return Tramo(_FundidoImagen(img, 0.0, 1.0, CURVA["fundido"], introducer=True), retraso, dura)


def Trazo(m: VMobject, retraso: float = 0.0, dura: float = DURA["trazo"], curva: str = "suave") -> Tramo:
    """Un trazo que se dibuja (evolvePath en Remotion, Create en Manim)."""
    return Tramo(Create(m, rate_func=CURVA[curva]), retraso, dura)


def Mover(m: Mobject, destino: Mobject, retraso: float = 0.0, dura: float = 0.5, curva: str = "suave") -> Tramo:
    """`m` toma la forma y el lugar de `destino` (Transform), con una curva."""
    return Tramo(Transform(m, destino, rate_func=CURVA[curva]), retraso, dura)


class _Latido(Animation):
    """Un solo latido: escala 1 → `escala` → 1 (seno), alrededor del centro."""

    def __init__(self, m: Mobject, escala: float, **kw):
        self.escala = escala
        super().__init__(m, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.centro = self.mobject.get_center()
        super().begin()

    def interpolate_mobject(self, alpha: float):
        k = 1 + (self.escala - 1) * math.sin(math.pi * alpha)
        self.mobject.become(self.objetivo)
        if alpha > 0:
            self.mobject.scale(k, about_point=self.centro)


def Latido(m: Mobject, retraso: float = 0.0, dura: float = 0.4, escala: float = 1.06) -> Tramo:
    return Tramo(_Latido(m, escala), retraso, dura)


class _CrecerDesdeIzquierda(Animation):
    """Un rectángulo redondeado (rect_borde) que crece a lo ancho desde su borde izquierdo, con
    el radio y el borde fijos: a la izquierda se ve como una pastilla que se estira."""

    def __init__(self, r: RoundedRectangle, ancho: float, alto: float, radio: float, grosor: float, curva, **kw):
        self.ancho, self.alto, self.radio, self.grosor, self.curva = ancho, alto, radio, grosor, curva
        super().__init__(r, introducer=True, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.izq = self.mobject.get_left()
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        p = self.curva(alpha)
        minimo = 2 * self.radio
        w = minimo + (self.ancho - minimo) * p
        nuevo = RoundedRectangle(width=u(w - self.grosor), height=u(self.alto - self.grosor),
                                 corner_radius=u(max(0.0, self.radio - self.grosor / 2)))
        nuevo.match_style(self.objetivo)
        nuevo.move_to(self.izq, aligned_edge=LEFT)
        self.mobject.become(nuevo)
        _aplicar_opacidad(self.mobject, self.base, min(1.0, 4 * p))


def CrecerDesdeIzquierda(r: RoundedRectangle, ancho: float, alto: float, radio: float, grosor: float,
                         retraso: float = 0.0, dura: float = DURA["entrar"], curva: str = "sale") -> Tramo:
    return Tramo(_CrecerDesdeIzquierda(r, ancho, alto, radio, grosor, CURVA[curva]), retraso, dura)


class _Foco(Animation):
    """Foco: lo ya explicado baja a hueso al 60 % y su ámbar al 60 % (OPACIDAD foco_hueso y
    foco_ambar; 0,3 s, inOut cúbica)."""

    def __init__(self, m: Mobject, **kw):
        super().__init__(m, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.base = _opacidades(self.mobject)
        self.factor = []
        for x in self.mobject.family_members_with_points():
            es_ambar = x.get_fill_color().to_hex().upper() == AMBAR.upper() or x.get_stroke_color().to_hex().upper() == AMBAR.upper()
            self.factor.append(OPACIDAD["foco_ambar"] if es_ambar else OPACIDAD["foco_hueso"])
        super().begin()

    def interpolate_mobject(self, alpha: float):
        p = CURVA["suave"](alpha)
        for x, (f, st), k in zip(self.mobject.family_members_with_points(), self.base, self.factor):
            x.set_fill(opacity=f * (1 - p * (1 - k)))
            x.set_stroke(opacity=st * (1 - p * (1 - k)))


def Foco(m: Mobject, retraso: float = 0.0, dura: float = DURA["foco"]) -> Tramo:
    return Tramo(_Foco(m), retraso, dura)


class _Cambio(Animation):
    """Una parte que se va o que llega en un TransformarPorPartes, como el dígito de un visor: la que
    se va sube y se apaga en la primera parte del tramo; la que llega sube desde abajo y se enciende
    en la segunda. Las dos casi no se superponen: nunca se leen dos palabras encimadas."""

    def __init__(self, m: Mobject, sale: bool, distancia: float, solape: float = 0.2, **kw):
        self.sale, self.solape = sale, solape
        self.desplazo = UP * u(distancia)
        super().__init__(m, introducer=not sale, remover=sale, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        mitad = (1 + self.solape) / 2  # cada uno ocupa 0,6 del tramo y se superponen 0,2
        if self.sale:
            a = min(1.0, alpha / mitad)
            k, d = 1 - CURVA["fundido"](a), CURVA["sale"](a)
        else:
            a = max(0.0, (alpha - (1 - mitad)) / mitad)
            k, d = CURVA["fundido"](a), -(1 - CURVA["sale"](a))
        self.mobject.become(self.objetivo)
        if d:
            self.mobject.shift(self.desplazo * d)
        _aplicar_opacidad(self.mobject, self.base, k)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        if self.sale:
            _aplicar_opacidad(self.mobject, self.base, 1.0)


class _TransformarPorPartes(AnimationGroup):
    """De un Texto a otro, parte por parte (lo que TransformMatchingTex hace con las cadenas, sin
    deformar letras ni encimar palabras):

    - las partes con la misma clave viajan a su lugar nuevo (y toman su tamaño y color), salvo las
      de `separar` (para que dos palabras no se crucen por el medio del renglón);
    - las demás cambian como un dígito de visor (_Cambio): la vieja sube y se apaga en su lugar, la
      nueva sube desde abajo y se enciende en el suyo.
    Al final queda en escena `destino` (el Texto nuevo, entero)."""

    def __init__(self, origen: Texto, destino: Texto, separar=(), curva=None, **kw):
        curva = curva or CURVA["suave"]
        self.origen, self.destino = origen, destino
        separar = set(separar)
        claves_d = list(destino.claves)
        usadas_d: set[int] = set()
        anims = []
        self.copias = []
        dist_o = 0.3 * getattr(origen, "tam", 60)
        dist_d = 0.3 * getattr(destino, "tam", 60)
        for i, k in enumerate(origen.claves):
            j = next((j for j, kd in enumerate(claves_d) if kd == k and j not in usadas_d), None) if k not in separar else None
            if j is not None:
                usadas_d.add(j)
                anims.append(Transform(origen.submobjects[i], destino.submobjects[j].copy(), rate_func=curva))
            else:
                anims.append(_Cambio(origen.submobjects[i], True, dist_o))
        for j, parte_d in enumerate(destino.submobjects):
            if j not in usadas_d:
                copia = parte_d.copy()
                self.copias.append(copia)
                anims.append(_Cambio(copia, False, dist_d))
        super().__init__(*anims, rate_func=rate_functions.linear, **kw)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        # Scene.remove no saca la familia: las partes van una por una (si no, quedaban fantasmas).
        scene.remove(self.origen, *self.origen.submobjects, *self.copias)
        scene.add(self.destino)


def TransformarPorPartes(origen: Texto, destino: Texto, retraso: float = 0.0, dura: float = 0.8, separar=(),
                         curva: str = "suave") -> Tramo:
    return Tramo(_TransformarPorPartes(origen, destino, separar, CURVA[curva]), retraso, dura)


class _Desplazar(Animation):
    """Mueve un objeto dx, dy px con una curva; con `aparece` (fracción del tramo) además se
    enciende desde 0 al empezar (una copia que sale de su original sin dibujarse dos veces)."""

    def __init__(self, m: Mobject, dx: float, dy: float, curva, aparece: float | None = None, **kw):
        self.delta = np.array([u(dx), -u(dy), 0.0])
        self.curva, self.aparece = curva, aparece
        super().__init__(m, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        self.mobject.become(self.objetivo)
        self.mobject.shift(self.delta * self.curva(alpha))
        if self.aparece:
            _aplicar_opacidad(self.mobject, self.base, CURVA["fundido"](min(1.0, alpha / self.aparece)))


def Desplazar(m: Mobject, dx: float, dy: float, retraso: float = 0.0, dura: float = 0.5, curva: str = "suave",
              aparece: float | None = None) -> Tramo:
    return Tramo(_Desplazar(m, dx, dy, CURVA[curva], aparece), retraso, dura)


class Segmento(AnimationGroup):
    """Varios tramos en un solo play, cada uno en sus cuadros: el cuadro i del segmento (i = 0…n−1)
    le da a cada tramo α = (i − inicio)/duración, recortado a [0, 1]. Así una animación de 0,5 s
    que empieza a los 0,2 s ocupa los mismos cuadros que en Remotion."""

    def __init__(self, tramos: list[Tramo], n: int):
        self.tramos = tramos
        self.n = n
        super().__init__(*[t.anim for t in tramos], run_time=(n - 0.5) / FPS, rate_func=rate_functions.linear)

    def interpolate(self, alpha: float) -> None:
        i = int(round(alpha * self.run_time * FPS))
        for t in self.tramos:
            if i <= t.ini:
                a = 0.0
            elif i >= t.fin:
                a = 1.0
            else:
                a = (i - t.ini) / t.n
            t.anim.interpolate(a)


# ---------------------------------------------------------------------------
# La diapositiva
# ---------------------------------------------------------------------------


class DiapoCharla(Scene):
    """Base de las diapositivas de Manim. La subclase define `ID` ("D07") y `construct()`:

        self.paso(1)                         # abre la sección del paso 1
        self.tocar(Entrar(a, 0.2), ...)      # un segmento: los tramos en sus cuadros
        self.tocar(...)                      # el siguiente segmento empieza donde terminó este
        self.paso(2)                         # cierra el 1 (quieto hasta su duración) y abre el 2

    - Cada paso dura lo que dice deck.json (respiro incluido); si una animación pisa los últimos
      0,3 s, falla y dice cuál. El último cuadro de cada paso es el primero del siguiente.
    - La marca de agua y el chip de piso los pone la base, en su píxel, encima de todo.
    - `self.anterior()`: en una entrada continua, el último cuadro de la anterior (el PNG a
      pantalla completa, o lo que devuelva `estado_anterior()` si la anterior es de Manim).
    """

    ID: str = ""

    def setup(self):
        if not self.ID:
            raise ValueError(f"{type(self).__name__}: falta ID (por ejemplo ID = \"D07\")")
        self.d = diapo(self.ID)
        nombre = f"{self.ID}{self.d['nombre']}"
        if type(self).__name__ != nombre:
            print(f"AVISO: la clase {type(self).__name__} se tendría que llamar {nombre} (deck.json → nombre)")
        if self.d["motor"] != "manim":
            print(f"AVISO: {self.ID} es de {self.d['motor']} según deck.json")
        self.cuadros_paso = [s(x) for x in duraciones_propias(self.ID)]
        self.n_pasos = len(self.cuadros_paso)
        self.entrada = entrada(self.ID)
        self._k = 0
        self._cuadro = 0
        self._fin_anim = 0
        self._pendientes: list[Tramo] = []
        self._anterior = None
        self._estado_fijo = estado_previo(self.ID)
        self._marca = None
        self._chip = None
        if self._estado_fijo["marca"]:
            self._marca = pieza("marca_agua")
            self._marca.es_marca_agua = True
            self.add(self._marca)
        if self._estado_fijo["chip"] is not None:
            self._chip = pieza(f"chip_piso_{self._estado_fijo['chip']}")
            self.add(self._chip)

    # ---- pasos ----

    def paso(self, k: int):
        """Cierra el paso anterior (quieto hasta su duración) y abre la sección del paso k."""
        if k != self._k + 1:
            raise ValueError(f"{self.ID}: después del paso {self._k} viene el {self._k + 1}, no el {k}")
        if k > self.n_pasos:
            raise ValueError(f"{self.ID}: deck.json dice {self.n_pasos} pasos; no hay paso {k}")
        if self._k:
            self._cerrar_paso()
        self.next_section(f"paso_{k}")
        self._k, self._cuadro, self._fin_anim = k, 0, 0
        self._cambios_fijos(k)

    def tocar(self, *tramos, hasta: float | None = None):
        """Un segmento: los tramos (Entrar(...), Aparecer(...), Tramo(anim, retraso, dura)…) con
        sus tiempos contados desde el comienzo del segmento. Dura hasta que termina el último
        tramo (o `hasta` s). Los cambios de la marca y el chip entran en el primer segmento."""
        if not self._k:
            raise RuntimeError(f"{self.ID}: tocar() antes de paso(1)")
        lista: list[Tramo] = []
        for t in tramos:
            if isinstance(t, (list, tuple)):
                lista.extend(t)
            else:
                lista.append(t)
        if self._pendientes:
            if self._cuadro:
                raise RuntimeError(f"{self.ID}.{self._k}: la marca de agua o el chip cambian en este paso: el primer tocar() tiene que empezar en el cuadro 0")
            lista = self._pendientes + lista
            self._pendientes = []
        for t in lista:
            if not isinstance(t, Tramo):
                raise TypeError(f"{self.ID}.{self._k}: tocar() recibe Tramo (Entrar, Aparecer, Tramo(anim, retraso, dura)…), no {type(t).__name__}")
        familias = {}
        for t in lista:
            for m in t.anim.mobject.get_family():
                if id(m) in familias and familias[id(m)] is not t:
                    raise ValueError(f"{self.ID}.{self._k}: dos tramos del mismo segmento mueven el mismo objeto ({type(m).__name__}); usar otro tocar()")
                familias[id(m)] = t
        n = max(t.fin for t in lista)
        if hasta is not None:
            n = max(n, s(hasta))
        self.play(Segmento(lista, n))
        self._fin_anim = max(self._fin_anim, self._cuadro + max(t.fin for t in lista))
        self._cuadro += n

    def esperar(self, seg: float):
        """Quieto `seg` segundos dentro del paso (en cuadros enteros)."""
        n = s(seg)
        if n > 0:
            self._quieto(n)
            self._cuadro += n

    def _quieto(self, n: int):
        """Exactamente n cuadros quietos. Una espera estática de Manim da int(duración × 30) cuadros
        (trunca); con updaters, uno por cada 1/30 s empezando en 0 (redondea para arriba)."""
        con_updaters = bool(self.always_update_mobjects or self.updaters
                            or any(m.has_time_based_updater() for m in self.get_mobject_family_members()))
        self.wait(((n - 0.5) if con_updaters else (n + 0.5)) / FPS)

    def _cerrar_paso(self):
        k, total = self._k, self.cuadros_paso[self._k - 1]
        if self._pendientes:
            self.tocar()  # solo los cambios de la marca o el chip
        limite = total - RESPIRO
        if self._fin_anim > limite:
            n = lambda v: f"{v:.2f}".replace(".", ",")  # noqa: E731
            raise ValueError(f"{self.ID}.{k}: una animación termina a los {n(self._fin_anim / FPS)} s y el paso dura {n(total / FPS)} s: "
                             f"tiene que terminar antes de los {n(limite / FPS)} s (los últimos {n(RESPIRO_S)} s van quietos: el respiro).")
        if self._cuadro > total:
            raise ValueError(f"{self.ID}.{k}: el paso usa {self._cuadro} cuadros y dura {total} ({total / FPS:.2f} s según deck.json)")
        if k == 1 and self._anterior is not None and self._anterior in self.mobjects:
            raise ValueError(f"{self.ID}.1: el cuadro anterior sigue en escena al final del paso 1: tiene que irse antes del respiro")
        resto = total - self._cuadro
        if resto > 0:
            self._quieto(resto)
            self._cuadro = total

    def tear_down(self):
        if self._k:
            if self._k != self.n_pasos:
                raise ValueError(f"{self.ID}: la escena tiene {self._k} pasos y deck.json {self.n_pasos}")
            self._cerrar_paso()
            # Un cuadro más, en su propia sección: es el último cuadro del último paso (los videos de
            # paso llevan los dos extremos, como los de Remotion).
            self.next_section("fin")
            self._quieto(1)
        super().tear_down()

    # ---- elementos fijos: marca de agua y chip de piso ----

    def _cambios_fijos(self, k: int):
        """Como `Persistentes` de remotion/src/sistema/Diapositiva.tsx: si la marca o el chip cambian
        al empezar el paso k, el cambio se anima en 0,3 s desde el cuadro 0 del paso."""
        marca = marca_en(self.ID, k)
        chip = chip_en(self.ID)
        antes = self._estado_fijo
        entra_s, sale_s = TOKENS["persistentes"]["entra_s"], TOKENS["persistentes"]["sale_s"]
        if marca != antes["marca"]:
            if marca:
                self._marca = pieza("marca_agua")
                self._marca.es_marca_agua = True
                self._pendientes.append(Tramo(_PiezaAparece(self._marca, "marca_agua", escala=False), 0, entra_s))
            else:
                # El recorte opaco se funde sobre tinta (su zona es reservada: es lo mismo que fundir la
                # marca, y el cuadro 0 del paso queda idéntico al último del anterior).
                self._pendientes.append(DesvanecerImagen(self._marca, 0, sale_s))
                self._marca = None
        if k == 1 and chip != antes["chip"]:
            if antes["chip"] is None:
                self._chip = pieza(f"chip_piso_{chip}")
                self._pendientes.append(Tramo(_PiezaAparece(self._chip, f"chip_piso_{chip}", escala=True), 0, entra_s))
            elif chip is None:
                self._pendientes.append(DesvanecerImagen(self._chip, 0, sale_s))
                self._chip = None
            else:
                raise NotImplementedError(f"{self.ID}: el chip cambia de {antes['chip']} a {chip}: el dígito rodado está en Remotion (ChipPiso), no en Manim")
        self._estado_fijo = {"marca": marca, "chip": chip}

    # ---- entrada continua ----

    def anterior(self):
        """El último cuadro de la diapositiva anterior, ya en escena (solo en el paso 1 de una entrada
        continua). Si la anterior es de Manim y esta clase define `estado_anterior()`, son sus objetos
        (reconstruidos con el mismo código); si no, el PNG de render/cuadros/<anterior>_<n>.png a
        pantalla completa, debajo de todo (la marca y el chip quedan encima, en su píxel)."""
        e = self.entrada
        if e["tipo"] != "continuo" or not e["desde"]:
            raise ValueError(f"{self.ID}: anterior() es solo para entradas «continuo» (esta entra con «{e['tipo']}»)")
        if self._k != 1 or self._cuadro:
            raise ValueError(f"{self.ID}: anterior() va al comienzo del paso 1")
        prev = diapo(e["desde"])
        if prev["motor"] == "manim" and hasattr(self, "estado_anterior"):
            objetos = self.estado_anterior()
            grupo = Group(*objetos)
            self.add(*objetos)
            self._anterior = grupo
            return grupo
        n = len(prev["pasos"])
        png = CUADROS / f"{e['desde']}_{n}.png"
        if not png.exists():
            print(f"AVISO: falta {png.relative_to(RAIZ).as_posix()}: {self.ID} arranca desde tinta y su frontera con {e['desde']}.{n} no va a empalmar.")
            img = imagen_en(_png_tinta(), 0, 0)
        else:
            img = imagen_en(png, 0, 0)
        img.auditor_ignorar = True
        img.set_z_index(-100)
        self.add(img)
        self._anterior = img
        return img

    def salir_anterior(self, retraso: float = 0.0, dura: float = DURA["fundido"]) -> Tramo:
        """El cuadro anterior se funde a tinta (0,4 s por defecto, como <Anterior sale>)."""
        a = self._anterior if self._anterior is not None else self.anterior()
        if isinstance(a, ImageMobject):
            return DesvanecerImagen(a, retraso, dura)
        return Desvanecer(a, retraso, dura)


class _PiezaAparece(Animation):
    """La marca de agua o el chip aparecen como en Remotion: fundido de 0,3 s (la marca, inOut
    seno) o fundido y escala 0,9 → 1 alrededor del centro de la caja (el chip, out cúbica).

    Mientras dura se dibuja el PNG transparente sobre lo que haya debajo; al terminar, `opaca`
    (el recorte opaco, idéntico al píxel a Remotion) toma su lugar."""

    def __init__(self, opaca: ImageMobject, nombre: str, escala: bool, **kw):
        self.opaca = opaca
        img = pieza(nombre, opaca=False)
        self.alfa = img.pixel_array[:, :, 3].astype(np.float64)
        self.puntos = img.points.copy()
        self.escala = escala
        self.curva = CURVA["sale"] if escala else CURVA["fundido"]
        ch = RETICULA["chip_piso"]
        self.centro = punto(ch["x"] + ch["ancho"] / 2, ch["y"] + ch["alto"] / 2)
        super().__init__(img, introducer=True, rate_func=rate_functions.linear, **kw)

    def interpolate_mobject(self, alpha: float):
        p = self.curva(alpha)
        if self.escala:
            esc = MOV["escala"]["tarjeta_entra"] + (1 - MOV["escala"]["tarjeta_entra"]) * p
            self.mobject.points = (self.puntos - self.centro) * esc + self.centro if p < 1 else self.puntos.copy()
        self.mobject.pixel_array[:, :, 3] = np.clip(np.round(self.alfa * p), 0, 255).astype(np.uint8)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        scene.remove(self.mobject)
        scene.add(self.opaca)


@lru_cache(maxsize=1)
def _png_tinta() -> str:
    """Un cuadro liso de tinta (para cuando falta el de la anterior)."""
    from PIL import Image

    ruta = MEDIA / "tinta_1080.png"
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        h = TINTA.lstrip("#")
        Image.new("RGB", (ANCHO, ALTO), tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))).save(ruta)
    return str(ruta)


__all__ = [
    # datos
    "RAIZ", "TOKENS", "DECK", "ANCHO", "ALTO", "FPS", "PX", "textos", "diapo", "entrada", "duraciones_propias",
    # coordenadas
    "punto", "u", "a_px", "caja_px", "s", "trazo",
    # tokens
    "COLOR", "TINTA", "HUESO", "AMBAR", "ROJO", "GRIS", "ACERO", "ACERO2", "VIDRIO", "PANTALLA", "MARCA",
    "NOCHE", "TITULO", "AZUL",
    "OPACIDAD", "ESCALA", "RETICULA", "ZONA", "RADIO", "GROSOR", "DURA", "DESFASE", "DISTANCIA", "CURVA", "RESPIRO_S",
    "px_de", "altura_mayuscula", "linea_base", "interlineado_de", "resorte", "entra",
    # piezas
    "Texto", "rect_borde", "linea", "corchete", "subrayado", "tachado", "linea_subrayado", "linea_tachado",
    "imagen_en", "pieza",
    # movimiento
    "Tramo", "Entrar", "EntrarPartes", "Aparecer", "Desvanecer", "AparecerImagen", "DesvanecerImagen", "Trazo",
    "Mover", "Desplazar", "Latido", "CrecerDesdeIzquierda", "Foco", "TransformarPorPartes", "Segmento",
    # escena
    "DiapoCharla",
]
