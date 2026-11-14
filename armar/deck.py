"""El deck de la charla visto por el armado: diapositivas, pasos, entradas y rutas.

contenido/deck.json es la fuente de verdad. Acá solo se lee: cada diapositiva
tiene sus pasos en orden (un paso = un video = una diapositiva del .pptx), las
principales primero y el respaldo después.

La ENTRADA de una diapositiva (cómo se pasa del último cuadro de la anterior al
primero de esta) sale del campo "entrada" si existe, en la diapositiva o en su
primer paso. La forma es la que lee remotion/lib/deck.mjs (entradaDe):

    {"tipo": "fundido" | "puertas" | "continuo" | "corte", "duracion_s": 0.4, "desde": "D19"}

- fundido, puertas: se renderiza la transición y va delante del video propio del
  paso 1. Como en Remotion, la duracion_animacion_s del paso 1 en el deck INCLUYE
  la transición (el video propio dura eso menos duracion_s) y el "ding:t" cuenta
  desde que empieza el paso entero, o sea desde el primer cuadro de la transición.
- continuo: sin transición; el paso 1 ya arranca en el último cuadro de "desde".
- corte: sin transición, corte seco a propósito.
- "desde": de qué diapositiva sale (por defecto, la anterior); null = de tinta.

También se aceptan textos ("fundido 0,4 desde D19", "puertas", "corte") y las
claves "segundos" o "s". Si el campo falta: fundido de 0,4 s desde la diapositiva
que nombra el guion en el «visual» del primer paso («Entra desde el último cuadro
de D20…») o, si no nombra ninguna, desde la anterior; y si el primer cuadro ya es
igual al último de esa (la escena arranca donde terminó la otra, que es lo que
hace Remotion con «continuo», su valor por defecto), el fundido no cambiaría nada
y no se hace (ver armar.py transiciones).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DECK = RAIZ / "contenido" / "deck.json"

FPS = 30
ANCHO, ALTO = 1920, 1080
TINTA = (0x07, 0x0A, 0x0F)

SEGUNDOS_FUNDIDO = 0.4
SEGUNDOS_PUERTAS = 1.05  # se juntan 0,45 s, cerradas 0,1 s, se abren 0,5 s (guion: sistema visual)
TIPOS_ENTRADA = ("fundido", "puertas", "continuo", "corte")
CON_TRANSICION = ("fundido", "puertas")

SECCIONES = ("principal", "respaldo")


@dataclass
class Entrada:
    tipo: str            # "fundido", "puertas", "continuo" o "corte"
    segundos: float      # largo de la transición (0 en continuo y corte)
    desde: str | None    # id de la diapositiva cuyo último cuadro es el punto de partida; None = tinta
    origen: str          # "deck" (campo "entrada"), "visual" (el «desde» lo dice el guion) o "defecto"

    @property
    def explicita(self) -> bool:
        return self.origen == "deck"

    @property
    def con_transicion(self) -> bool:
        return self.tipo in CON_TRANSICION

    @property
    def cuadros(self) -> int:
        return max(1, int(round(self.segundos * FPS))) if self.con_transicion else 0

    def describir(self) -> str:
        desde = self.desde or "tinta"
        if not self.con_transicion:
            return f"{self.tipo} (desde {desde}; {self.origen})"
        return f"{self.tipo} {self.segundos:.2f} s desde {desde} ({self.origen})"


@dataclass
class Paso:
    diapo: "Diapo"
    k: int                # 1, 2, 3...
    datos: dict
    numero: int = 0       # número de diapositiva en el .pptx completo (1..66)

    @property
    def id(self) -> str:          # D14_1: nombre de archivo
        return f"{self.diapo.id}_{self.k}"

    @property
    def etiqueta(self) -> str:    # D14.1: como lo escribe el guion
        return f"{self.diapo.id}.{self.k}"

    @property
    def es_primero(self) -> bool:
        return self.k == 1

    @property
    def es_ultimo(self) -> bool:
        return self.k == len(self.diapo.pasos)

    @property
    def duracion(self) -> float:
        return float(self.datos.get("duracion_animacion_s") or 0.0)

    @property
    def notas(self) -> str:
        return self.datos.get("notas") or ""

    @property
    def notas_pptx(self) -> str:
        """Lo que va en las notas del .pptx: `notas` y, al final, «Fuente: …» y
        «Recortable: …» cuando existen (guion, «Para quien construye»)."""
        partes = [self.notas.strip()]
        if self.datos.get("fuente"):
            partes.append(f"Fuente: {self.datos['fuente'].strip()}")
        if self.datos.get("recortable"):
            partes.append(f"Recortable: {self.datos['recortable'].strip()}")
        return "\n\n".join(p for p in partes if p)

    @property
    def dings(self) -> list[float]:
        """Segundos (desde que empieza el paso) en que suena el ding."""
        return leer_audio(self.datos.get("audio"), self.etiqueta)


@dataclass
class Diapo:
    id: str
    nombre: str
    titulo: str
    seccion: str
    motor: str
    datos: dict
    indice: int                       # posición en el deck (0..)
    pasos: list[Paso] = field(default_factory=list)
    entrada: Entrada | None = None

    @property
    def etiqueta_seccion(self) -> str:
        return f"{self.id} · {self.titulo}"


def leer_audio(valor, quien="") -> list[float]:
    """"ding:34.3" -> [34.3]. Acepta varios separados por coma o punto y coma, o una lista."""
    if not valor:
        return []
    items = valor if isinstance(valor, list) else re.split(r"[;,]\s*(?=ding)", str(valor))
    tiempos = []
    for it in items:
        m = re.fullmatch(r"\s*ding\s*:\s*([0-9]+(?:[.,][0-9]+)?)\s*s?\s*", str(it))
        if not m:
            raise ValueError(f"{quien}: audio desconocido {it!r} (se espera 'ding:<segundos>')")
        tiempos.append(float(m.group(1).replace(",", ".")))
    return tiempos


# ---------------------------------------------------------------- entradas
_RE_NUM = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*(?:s\b|seg)?")
_RE_DESDE = re.compile(r"desde\s*:?\s*(tinta|[DA]\d{1,2})\b", re.IGNORECASE)


def _tipo_de(texto: str) -> str | None:
    t = texto.lower()
    if "puerta" in t:
        return "puertas"
    if "fund" in t:
        return "fundido"
    if "corte" in t or "seco" in t:
        return "corte"
    if any(p in t for p in ("continu", "ningun", "sin transici", "nada")):
        return "continuo"
    return None


def _segundos_por_defecto(tipo: str) -> float:
    return {"fundido": SEGUNDOS_FUNDIDO, "puertas": SEGUNDOS_PUERTAS}.get(tipo, 0.0)


def _normalizar_desde(valor) -> str | None:
    if valor is None:
        return None
    v = str(valor).strip()
    if v.lower() in ("", "tinta", "negro", "ninguna", "null"):
        return None
    return v.upper()


def leer_entrada(valor, anterior: str | None) -> Entrada:
    """El campo "entrada" del deck, en cualquiera de sus formas."""
    if isinstance(valor, dict):
        tipo = _tipo_de(str(valor.get("tipo") or valor.get("clase") or valor.get("modo") or "fundido")) or "fundido"
        seg = next((valor[k] for k in ("segundos", "duracion_s", "duracion", "s") if valor.get(k) is not None), None)
        seg = float(str(seg).replace(",", ".")) if seg is not None else _segundos_por_defecto(tipo)
        desde = _normalizar_desde(valor["desde"]) if "desde" in valor else anterior
        return Entrada(tipo, seg if tipo in CON_TRANSICION else 0.0, desde, "deck")
    texto = str(valor)
    tipo = _tipo_de(texto) or "fundido"
    sin_desde = _RE_DESDE.sub("", texto)
    m = _RE_NUM.search(sin_desde)
    seg = float(m.group(1).replace(",", ".")) if m else _segundos_por_defecto(tipo)
    md = _RE_DESDE.search(texto)
    desde = _normalizar_desde(md.group(1)) if md else anterior
    return Entrada(tipo, seg if tipo in CON_TRANSICION else 0.0, desde, "deck")


def entrada_por_visual(visual: str, anterior: str | None) -> Entrada:
    """Sin campo "entrada": fundido de 0,4 s desde la diapositiva que nombra el guion
    en la frase «Entra desde…» del primer paso (A8 sale de D19 y A1-A7 de D20, no de
    la anterior en la lista) o, si no nombra ninguna, desde la anterior."""
    linea = (visual or "")[:400]
    desde, origen = anterior, "defecto"
    m = re.search(r"Entra desde (?:el PNG del |el )?último cuadro de ([DA]\d{1,2})", linea)
    if m:
        desde, origen = m.group(1), "visual"
    elif re.search(r"Entra desde tinta", linea):
        desde, origen = None, "visual"
    return Entrada("fundido", SEGUNDOS_FUNDIDO, desde, origen)


# ---------------------------------------------------------------- deck
@dataclass
class Deck:
    datos: dict
    diapos: list[Diapo]
    ruta: Path

    @property
    def pasos(self) -> list[Paso]:
        return [p for d in self.diapos for p in d.pasos]

    def diapo(self, ident: str) -> Diapo:
        for d in self.diapos:
            if d.id == ident.upper():
                return d
        raise KeyError(f"no hay diapositiva {ident} en {self.ruta}")

    def paso_numero(self, n: int) -> Paso | None:
        pasos = self.pasos
        return pasos[n - 1] if 1 <= n <= len(pasos) else None

    def seleccionar(self, solo=None, seccion="todas") -> list[Diapo]:
        ids = normalizar_ids(solo)
        if ids:
            faltan = [i for i in ids if i not in {d.id for d in self.diapos}]
            if faltan:
                raise SystemExit(f"--solo: no existen en el deck: {', '.join(faltan)}")
        out = []
        for d in self.diapos:
            if seccion != "todas" and d.seccion != seccion:
                continue
            if ids and d.id not in ids:
                continue
            out.append(d)
        return out


def normalizar_ids(solo) -> list[str]:
    if not solo:
        return []
    if isinstance(solo, str):
        solo = [solo]
    ids = []
    for s in solo:
        for x in re.split(r"[\s,;]+", s.strip()):
            if x:
                ids.append(x.upper())
    return ids


def cargar(ruta: Path | str = DECK) -> Deck:
    ruta = Path(ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    diapos: list[Diapo] = []
    for i, d in enumerate(datos["diapositivas"]):
        if d.get("seccion") not in SECCIONES:
            raise ValueError(f"{d.get('id')}: sección desconocida {d.get('seccion')!r}")
        diapo = Diapo(id=d["id"], nombre=d.get("nombre", d["id"]), titulo=d.get("titulo", d["id"]),
                      seccion=d["seccion"], motor=d.get("motor", ""), datos=d, indice=i)
        diapo.pasos = [Paso(diapo, k, p) for k, p in enumerate(d["pasos"], start=1)]
        if not diapo.pasos:
            raise ValueError(f"{diapo.id}: no tiene pasos")
        diapos.append(diapo)
    ids = [d.id for d in diapos]
    if len(set(ids)) != len(ids):
        raise ValueError("hay id de diapositiva repetidos en el deck")
    # numeración del .pptx completo: principales y después el respaldo, en el orden del deck
    n = 0
    for d in diapos:
        for p in d.pasos:
            n += 1
            p.numero = n
    # entradas
    for i, d in enumerate(diapos):
        anterior = diapos[i - 1].id if i > 0 else None
        valor = d.datos.get("entrada", d.pasos[0].datos.get("entrada"))
        if valor is not None:
            d.entrada = leer_entrada(valor, anterior)
        else:
            d.entrada = entrada_por_visual(d.pasos[0].datos.get("visual", ""), anterior)
        if d.entrada.desde is not None and d.entrada.desde not in ids:
            raise ValueError(f"{d.id}: la entrada sale de {d.entrada.desde}, que no está en el deck")
        if d.entrada.desde == d.id:
            raise ValueError(f"{d.id}: la entrada no puede salir de la misma diapositiva")
    return Deck(datos, diapos, ruta)


# ---------------------------------------------------------------- rutas
class Rutas:
    """Dónde vive cada cosa (render/ por defecto; otra raíz para las pruebas)."""

    def __init__(self, render: Path | str = RAIZ / "render"):
        self.render = Path(render)

    def paso(self, p: Paso) -> Path:
        return self.render / "pasos" / p.diapo.id / f"{p.id}.mp4"

    def transicion(self, d: Diapo) -> Path:
        return self.render / "transiciones" / f"{d.id}.mp4"

    def final(self, p: Paso) -> Path:
        return self.render / "final" / p.diapo.id / f"{p.id}.mp4"

    def compacto(self, p: Paso) -> Path:
        return self.render / "compacto" / p.diapo.id / f"{p.id}.mp4"

    def primero(self, p: Paso) -> Path:     # póster del .pptx: primer cuadro decodificado del video final
        return self.render / "cuadros" / "primero" / f"{p.id}.png"

    def ultimo(self, p: Paso) -> Path:      # último cuadro del video final (PDF, vista del orador)
        return self.render / "cuadros" / "ultimo" / f"{p.id}.png"

    @property
    def transiciones(self) -> Path:
        return self.render / "transiciones"

    @property
    def revision(self) -> Path:
        return self.render / "revision"

    @property
    def trabajo(self) -> Path:
        return self.render / "armado"
