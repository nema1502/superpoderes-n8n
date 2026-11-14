"""Auditor de los videos de la charla: revisa cada paso de cada diapositiva.

Uso:
    python armar/auditar_cuadros.py D05 D07            esas diapositivas (render/pasos/)
    python armar/auditar_cuadros.py --todos            toda la charla
    python armar/auditar_cuadros.py --todos --final    los videos con transición y audio (render/final/)

Opciones útiles:
    --parcial                    una diapositiva sin render es un aviso, no un error
    --tolerancia-frontera vista  acepta fronteras "iguales a la vista" (por defecto: exacta en los
                                 crudos, vista con --final)
    --muestreo 0.5               cada cuántos segundos se busca lima durante la animación (0: solo
                                 el último cuadro, más rápido)
    --estricto                   los avisos también hacen fallar
    --sin-evidencias             no guarda los PNG que muestran cada problema

Reglas: pasos, formato, duracion, frontera, quietud, primer_cuadro, zona_segura,
zonas_reservadas, lima y audio (solo --final). Qué mide cada una, con qué umbrales y cómo
marcar excepciones (armar/auditoria_reglas.json): docs/auditoria.md.

Informe: render/revision/auditoria_cuadros.md y .json (con --final, auditoria_cuadros_final.*),
y las evidencias en render/revision/auditoria/ (o auditoria_final/).
Código de salida: 0 aprobado, 1 con errores (o con avisos y --estricto), 2 mal llamado.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cuadros_comun as cc  # noqa: E402

REGLAS = {
    "pasos": "cantidad de videos igual a la de pasos de deck.json",
    "formato": "1920x1080, 30 fps, H.264 High, yuv420p, BT.709 de rango limitado, sin audio en los crudos",
    "duracion": "la duración del video frente a duracion_animacion_s",
    "frontera": "el primer cuadro es el último del paso anterior",
    "quietud": "el paso termina quieto (los últimos 0,3 s iguales)",
    "primer_cuadro": "el primer cuadro de la charla no es negro",
    "zona_segura": "en el último cuadro, nada fuera de los márgenes",
    "zonas_reservadas": "marca de agua, chip de piso y reloj grande en su lugar y sin nada encima ni pegado",
    "lima": "el lima solo en la marca de agua y en los pasos de marca",
    "audio": "el ding en su segundo y silencio en los demás pasos (solo --final)",
}
COLUMNAS = ["formato", "duracion", "frontera", "quietud", "zona_segura", "zonas_reservadas", "lima"]

# Umbrales por defecto. Se cambian en armar/auditoria_reglas.json ("umbrales") o, para
# algunos pasos, con una excepción. El ruido de compresión de referencia sale de las
# mediciones del 23-oct-2026 con la receta de frontera (docs/auditoria.md, "Calibración").
UMBRALES = {
    # fondo: un píxel es contenido si algún canal se aleja más que esto de la tinta decodificada
    "fondo_umbral": 10,
    "fondo_tolerancia_esquinas": 6,
    # zona segura
    "zona_segura_banda_px": 3,
    "zona_segura_min_px": 8,
    # quietud (bloques de 16x16 contra el último cuadro; ruido de compresión medido ≤ 5,1 y ≤ 10,6)
    "quietud_s": 0.3,
    "quietud_bloque_max": 14.0,
    "quietud_bloque_signo_max": 24.0,
    "quietud_medir_hasta_s": 1.0,
    # frontera ("vista": el criterio de comparar_cuadros.py)
    "frontera_psnr_vista": 40.0,
    "frontera_notables_pct": 0.05,
    # duración (s): tokens.json dice que cada paso dura lo que dice deck.json, respiro incluido
    "duracion_aviso_menos_s": 0.1,
    "duracion_aviso_mas_s": 0.2,
    "duracion_error_menos_s": 0.5,
    "duracion_error_menos_rel": 0.03,
    "duracion_error_mas_s": 3.0,
    "duracion_error_mas_rel": 0.25,
    "duracion_final_holgura_s": 0.5,
    # primer cuadro
    "negro_canal_max": 3,
    "negro_fraccion": 0.5,
    # zonas reservadas
    "halo_px": 20,
    "halo_tolerancia_px": 3,
    "halo_min_px": 8,
    "marca_min_lima_px": 20,
    "marca_min_contenido_pct": 3.0,
    "chip_min_ambar_px": 30,
    "chip_min_contenido_pct": 6.0,
    "reloj_min_ambar_px": 400,
    "reloj_tolerancia_x_px": 60,
    "reloj_tolerancia_y_px": 8,
    "reloj_tolerancia_alto_px": 12,
    "reloj_busqueda_ancho_px": 260,
    "reloj_busqueda_margen_px": 10,
    "reloj_union_px": 24,
    "reloj_ajeno_min_px": 40,
    "consistencia_bloque_max": 14.0,
    "consistencia_media_contenido": 12.0,
    # lima
    "lima_min_px": 6,
    "lima_holgura_px": 3,
    "muestreo_s": 0.5,
    # audio (--final)
    "ding_aviso_s": 0.15,
    "ding_error_s": 0.3,
    "silencio_dbfs": -50.0,
}

CLAVES_EXCEPCION = {"pasos", "regla", "motivo", "omitir", "permitir", "tolerancia", "anterior", "zona", "umbrales"}


class ErrorReglas(Exception):
    """auditoria_reglas.json mal escrito: el auditor no arranca (código 2)."""
ZONAS = ("marca_agua", "chip", "reloj")
CLAVES_MARCA = ["marcaagua", "marcadeagua", "watermark"]  # nombres (normalizados) de la pieza en diseno/assets/
ORDEN_NIVEL = {"ok": 0, "nota": 0, "aviso": 1, "error": 2}


@dataclass
class Hallazgo:
    nivel: str
    regla: str
    paso: str
    mensaje: str
    evidencia: str | None = None
    datos: dict = field(default_factory=dict)


@dataclass
class ResultadoPaso:
    paso: cc.Paso
    video: Path
    existe: bool = False
    geometria: bool = False
    info: dict = field(default_factory=dict)
    estados: dict = field(default_factory=dict)
    detalle: dict = field(default_factory=dict)
    hallazgos: list = field(default_factory=list)
    primero: Path | None = None
    ultimo: Path | None = None
    recortes: dict = field(default_factory=dict)
    excepciones: list = field(default_factory=list)

    @property
    def clave(self) -> str:
        return self.paso.clave

    def marcar(self, regla, nivel, mensaje, evidencia=None, **datos):
        self.hallazgos.append(Hallazgo(nivel, regla, self.clave, mensaje, evidencia, datos))
        if nivel in ("aviso", "error"):
            actual = self.estados.get(regla, "ok")
            if ORDEN_NIVEL.get(actual, 0) < ORDEN_NIVEL[nivel]:
                self.estados[regla] = nivel

    def errores_de(self, regla, zona=None) -> int:
        return sum(1 for h in self.hallazgos if h.nivel == "error" and h.regla == regla
                   and (zona is None or h.datos.get("zona") == zona))

    def ok(self, regla, detalle=None):
        self.estados.setdefault(regla, "ok")
        if detalle:
            self.detalle[regla] = detalle


def fmt(x, dec=1):
    return cc.fmt_num(x, dec)


def caja_txt(c) -> str:
    return f"x {int(c[0])}-{int(c[2])}, y {int(c[1])}-{int(c[3])}" if c else "—"


def _union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def mascara_calida(img) -> np.ndarray:
    """Colores cálidos de la familia del ámbar, con margen (tono 10°-60°, saturación ≥ 0,25):
    para no confundir con «algo ajeno» los bordes del reloj que la submuestra de croma lava."""
    r, g, b = (img[..., i].astype(np.int16) for i in range(3))
    return (r >= g) & (g >= b) & (6 * (g - b) >= (r - b)) & (4 * (r - b) >= r)


# ---------------------------------------------------------------------------
# Evidencias (PNG que muestran el problema)
# ---------------------------------------------------------------------------

def _fuente(tam=22, negrita=True):
    for f in (("segoeuib.ttf" if negrita else "segoeui.ttf"), "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{f}", tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _guias(dib, tokens: cc.Tokens, esc: float):
    s = tokens.zona_segura
    dib.rectangle([s[0] * esc, s[1] * esc, s[2] * esc, s[3] * esc], outline=(0, 200, 230), width=1)
    for z in (tokens.marca_agua, tokens.chip):
        dib.rectangle([z[0] * esc, z[1] * esc, z[2] * esc, z[3] * esc], outline=(120, 120, 140), width=1)


def evidencia_cuadro(img, titulo, tokens, mascara=None, cajas=(), color=(255, 40, 40)) -> Image.Image:
    """El cuadro a la mitad, con las guías de márgenes y zonas, los píxeles del problema
    pintados y, abajo, el problema ampliado."""
    h, w = img.shape[:2]
    base = np.array(img)
    if mascara is not None:
        m = mascara.copy()
        for _ in range(2):  # engrosar, para que se vea a la mitad
            m[1:, :] |= m[:-1, :].copy()
            m[:-1, :] |= m[1:, :].copy()
            m[:, 1:] |= m[:, :-1].copy()
            m[:, :-1] |= m[:, 1:].copy()
        base[m] = color
    chico = Image.fromarray(base).resize((w // 2, h // 2), Image.BILINEAR)
    d = ImageDraw.Draw(chico)
    if (w, h) == (cc.ANCHO, cc.ALTO):
        _guias(d, tokens, 0.5)
    for c in cajas:
        if c:
            d.rectangle([c[0] / 2 - 4, c[1] / 2 - 4, c[2] / 2 + 4, c[3] / 2 + 4], outline=color, width=2)
    zoom, factor = None, 1.0
    if cajas and cajas[0]:
        c = [int(v) for v in cajas[0]]
        x0, y0 = max(0, c[0] - 40), max(0, c[1] - 40)
        x1, y1 = min(w, c[2] + 40), min(h, c[3] + 40)
        factor = min(4.0, 940 / max(1, x1 - x0), 320 / max(1, y1 - y0))
        if factor > 1.05:
            zoom = Image.fromarray(np.ascontiguousarray(img[y0:y1, x0:x1])).resize(
                (max(1, int((x1 - x0) * factor)), max(1, int((y1 - y0) * factor))), Image.NEAREST)
    alto = 40 + chico.height + (zoom.height + 34 if zoom else 0)
    lienzo = Image.new("RGB", (max(chico.width, zoom.width if zoom else 0) + 20, alto), (24, 24, 28))
    dib = ImageDraw.Draw(lienzo)
    dib.text((10, 8), titulo, fill=(240, 240, 240), font=_fuente(20))
    lienzo.paste(chico, (10, 36))
    if zoom:
        dib.text((10, 42 + chico.height), f"ampliado ×{factor:.1f} (sin las marcas)", fill=(200, 200, 200),
                 font=_fuente(16, False))
        lienzo.paste(zoom, (10, 68 + chico.height))
    return lienzo


def evidencia_tres(a, b, titulo, rotulos) -> Image.Image:
    """Tres paneles: a, b y la diferencia amplificada."""
    paneles = [Image.fromarray(np.ascontiguousarray(a)), Image.fromarray(np.ascontiguousarray(b)),
               Image.fromarray(cc.mapa_diferencia(a, b))]
    paneles = [p.resize((640, 360), Image.BILINEAR) for p in paneles]
    lienzo = Image.new("RGB", (3 * 640 + 40, 360 + 80), (24, 24, 28))
    d = ImageDraw.Draw(lienzo)
    d.text((10, 8), titulo, fill=(240, 240, 240), font=_fuente(20))
    for i, (p, r) in enumerate(zip(paneles, rotulos + ["diferencia ×6"])):
        x = 10 + i * 650
        lienzo.paste(p, (x, 40))
        d.text((x, 406), r, fill=(210, 210, 210), font=_fuente(16, False))
    return lienzo


def evidencia_recortes(a, b, titulo, rotulos, zoom=4) -> Image.Image:
    paneles = [Image.fromarray(np.ascontiguousarray(a)), Image.fromarray(np.ascontiguousarray(b)),
               Image.fromarray(cc.mapa_diferencia(a, b))]
    paneles = [p.resize((p.width * zoom, p.height * zoom), Image.NEAREST) for p in paneles]
    pw, ph = paneles[0].size
    lienzo = Image.new("RGB", (max(3 * (pw + 10) + 10, 900), ph + 80), (24, 24, 28))
    d = ImageDraw.Draw(lienzo)
    d.text((10, 8), titulo, fill=(240, 240, 240), font=_fuente(18))
    for i, (p, r) in enumerate(zip(paneles, rotulos + ["diferencia ×6"])):
        x = 10 + i * (pw + 10)
        lienzo.paste(p, (x, 40))
        d.text((x, 46 + ph), r, fill=(210, 210, 210), font=_fuente(15, False))
    return lienzo


# ---------------------------------------------------------------------------
# El auditor
# ---------------------------------------------------------------------------

class Auditor:
    def __init__(self, a):
        self.a = a
        r = cc.Rutas()
        for campo in ("deck", "guion", "tokens", "assets", "reglas", "temporal"):
            v = getattr(a, campo, None)
            if v:
                setattr(r, campo, Path(v))
        self.rutas = r
        self.final = bool(a.final)
        self.carpeta = Path(a.videos) if a.videos else (r.final if self.final else r.pasos)
        self.tokens = cc.cargar_tokens(r)
        self.deck = cc.cargar_deck(r, self.tokens.transiciones)
        self.reglas = cc.cargar_reglas(r)
        self.validar_reglas()
        self.U = dict(UMBRALES)
        if self.tokens.respiro_s:
            self.U["quietud_s"] = self.tokens.respiro_s
        self.U.update(self.reglas.get("umbrales") or {})
        # Pasos sin marca de agua: de tokens.json (persistentes.marca_agua_sin) si lo trae; si no,
        # de auditoria_reglas.json.
        self.notas_config = []
        lista_reglas = self.reglas.get("pasos_sin_marca_de_agua")
        if self.tokens.marca_agua_sin is not None:
            self.sin_marca = self.tokens.marca_agua_sin
            self.origen_sin_marca = self.tokens.origen.get("marca_agua_sin", "tokens.json")
            if lista_reglas is not None and sorted(lista_reglas) != sorted(self.sin_marca):
                self.notas_config.append(f"auditoria_reglas.json dice que no llevan marca de agua "
                                         f"{', '.join(lista_reglas)}, y tokens.json {', '.join(self.sin_marca)}: "
                                         f"vale tokens.json")
        else:
            self.sin_marca = lista_reglas or []
            self.origen_sin_marca = self.rutas.relativa(self.rutas.reglas)
        self.diapos = cc.elegir_diapos(self.deck, a.ids, a.todos)
        self.todos = bool(a.todos)
        self.parcial = bool(a.parcial)
        self.tolerancia = a.tolerancia_frontera or ("vista" if self.final else "exacta")
        self.muestreo = self.U["muestreo_s"] if a.muestreo is None else float(a.muestreo)
        self.evidencias = not a.sin_evidencias
        self.salida = Path(a.salida) if a.salida else r.revision
        base = a.informe or ("auditoria_cuadros_final" if self.final else "auditoria_cuadros")
        self.informe_md = self.salida / f"{base}.md"
        self.informe_json = self.salida / f"{base}.json"
        self.dir_evid = self.salida / ("auditoria_final" if self.final else "auditoria")
        self.cache = r.temporal / ("cuadros_final" if self.final else "cuadros")
        self.hilos = max(1, int(a.hilos))
        self.fondo_esperado = cc.fondo_decodificado(self.tokens.rgb("tinta"), r)
        self.globales: list[Hallazgo] = []
        self.usadas: dict[int, set] = {}
        self.res: dict[str, ResultadoPaso] = {}
        self.referencias = {}
        self._candado = threading.Lock()
        self._ultimos_externos = {}
        # Lo que ocupa cada elemento fijo: la caja de tokens.json, agrandada hasta lo que ocupa su
        # pieza de diseno/assets/ si existe (la marca real de Remotion va de x 67 a 310 y de y 32 a
        # 91, más que la caja x 67-300, y 38-86). Y su zona reservada: la «zona» de tokens.json
        # («nada más se dibuja ahí») o, si no la trae, lo que ocupa más halo_px alrededor.
        self.assets = cc.cargar_assets(r)
        t = self.tokens
        self.zona_marca = self._zona_efectiva(CLAVES_MARCA, t.marca_agua, [t.marca_agua, t.marca_agua_zona])
        self.zona_chip = self._zona_efectiva([k for k in self.assets if k.startswith("chip")], t.chip,
                                             [t.chip, t.chip_zona])
        self.reservada_marca = _union(self.zona_marca, t.marca_agua_zona) if t.marca_agua_zona != t.marca_agua \
            else cc.expandir(self.zona_marca, self.U["halo_px"])
        self.reservada_chip = _union(self.zona_chip, t.chip_zona) if t.chip_zona != t.chip \
            else cc.expandir(self.zona_chip, self.U["halo_px"])

    # --- configuración -----------------------------------------------------

    def validar_reglas(self):
        errores = []
        for nombre in ("pasos_sin_marca_de_agua", "pasos_con_reloj_grande", "pasos_de_marca", "pasos_con_chip"):
            v = self.reglas.get(nombre)
            if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
                errores.append(f"«{nombre}» tiene que ser una lista de pasos («D02.1», «D03», «A8.*»)")
        for i, e in enumerate(self.reglas.get("excepciones", []), 1):
            if not isinstance(e, dict):
                errores.append(f"excepción {i}: tiene que ser un objeto")
                continue
            sobran = set(e) - CLAVES_EXCEPCION
            if sobran:
                errores.append(f"excepción {i}: claves desconocidas {sorted(sobran)} (valen {sorted(CLAVES_EXCEPCION)})")
            if e.get("regla") not in REGLAS:
                errores.append(f"excepción {i}: regla {e.get('regla')!r} desconocida (valen: {', '.join(REGLAS)})")
            pasos = e.get("pasos")
            if isinstance(pasos, str):
                e["pasos"] = [pasos]
            elif not (isinstance(pasos, list) and pasos and all(isinstance(x, str) for x in pasos)):
                errores.append(f"excepción {i}: «pasos» tiene que ser una lista no vacía")
            if not str(e.get("motivo", "")).strip():
                errores.append(f"excepción {i}: falta el «motivo» (toda excepción dice por qué)")
            if "permitir" in e:
                ok = isinstance(e["permitir"], list) and all(
                    isinstance(r, list) and len(r) == 4 and all(isinstance(x, (int, float)) for x in r)
                    and r[2] > r[0] and r[3] > r[1] for r in e["permitir"])
                if not ok:
                    errores.append(f"excepción {i}: «permitir» es una lista de rectángulos [x0, y0, x1, y1] en px")
                if e.get("regla") not in ("zona_segura", "lima", "zonas_reservadas"):
                    errores.append(f"excepción {i}: «permitir» solo vale para zona_segura, lima y zonas_reservadas")
            if "tolerancia" in e and e["tolerancia"] not in ("exacta", "vista"):
                errores.append(f"excepción {i}: «tolerancia» es «exacta» o «vista»")
            if "anterior" in e and not (isinstance(e["anterior"], list) and e["anterior"]
                                        and all(isinstance(x, str) for x in e["anterior"])):
                errores.append(f"excepción {i}: «anterior» es una lista de pasos («A8.3») o [\"tinta\"]")
            if "zona" in e and e["zona"] not in ZONAS:
                errores.append(f"excepción {i}: «zona» es una de {', '.join(ZONAS)}")
            if "zona" in e and e.get("regla") != "zonas_reservadas":
                errores.append(f"excepción {i}: «zona» solo vale para la regla zonas_reservadas")
            if "umbrales" in e:
                if not isinstance(e["umbrales"], dict):
                    errores.append(f"excepción {i}: «umbrales» es un objeto {{nombre: valor}}")
                else:
                    errores += [f"excepción {i}: umbral {k!r} desconocido" for k in e["umbrales"] if k not in UMBRALES]
        errores += [f"umbral {k!r} desconocido en «umbrales»" for k in (self.reglas.get("umbrales") or {})
                    if k not in UMBRALES]
        if errores:
            raise ErrorReglas(f"{self.rutas.relativa(self.rutas.reglas)} tiene problemas:\n  - " + "\n  - ".join(errores))

    def excepciones(self, clave, regla, zona=None):
        """Las excepciones de esa regla que valen para ese paso. Una excepción con «zona»
        vale solo cuando se pregunta por esa zona; una sin «zona», para toda la regla."""
        salida = []
        for i, e in enumerate(self.reglas.get("excepciones", [])):
            if e["regla"] != regla:
                continue
            if e.get("zona") and e["zona"] != zona:
                continue
            if cc.coincide(clave, e["pasos"]):
                salida.append((i, e))
        return salida

    def usar(self, res, i, e, que):
        with self._candado:
            self.usadas.setdefault(i, set()).add(res.clave)
        texto = f"{e['regla']}{(' (' + e['zona'] + ')') if e.get('zona') else ''}: {que}. Motivo: {e['motivo']}"
        if texto not in res.excepciones:
            res.excepciones.append(texto)

    def omitida(self, res, regla, zona=None) -> bool:
        for i, e in self.excepciones(res.clave, regla, zona):
            if e.get("omitir"):
                self.usar(res, i, e, "no se revisa")
                return True
        return False

    def umbral(self, res, regla, nombre, zona=None):
        for i, e in self.excepciones(res.clave, regla, zona):
            if nombre in (e.get("umbrales") or {}):
                self.usar(res, i, e, f"{nombre} = {e['umbrales'][nombre]}")
                return e["umbrales"][nombre]
        return self.U[nombre]

    def permitidos(self, res, regla, zona=None) -> list:
        rects = []
        for i, e in self.excepciones(res.clave, regla, zona):
            for r in e.get("permitir") or []:
                rects.append(tuple(r))
                self.usar(res, i, e, f"se permite {caja_txt(r)}")
        return rects

    def lleva_marca(self, clave) -> bool:
        return not cc.coincide(clave, self.sin_marca)

    def lleva_reloj(self, clave) -> bool:
        return cc.coincide(clave, self.reglas.get("pasos_con_reloj_grande") or [])

    def es_de_marca(self, clave) -> bool:
        return cc.coincide(clave, self.reglas.get("pasos_de_marca") or [])

    def lleva_chip(self, paso: cc.Paso):
        """El piso del chip que lleva el paso, o None. Sale de «piso» en deck.json, salvo que
        auditoria_reglas.json traiga «pasos_con_chip»."""
        lista = self.reglas.get("pasos_con_chip")
        d = self.deck.diapo(paso.diapo)
        if lista is not None:
            return (d.piso if d.piso is not None else "?") if cc.coincide(paso.clave, lista) else None
        return d.piso

    def _zona_efectiva(self, claves, zona, lugares):
        """La caja declarada, agrandada hasta lo que ocupan sus piezas de diseno/assets/: si el
        dibujo real se pasa unos píxeles de la caja, no se lo confunde con contenido ajeno."""
        caja_total = tuple(zona)
        for k in claves:
            pieza = self.assets.get(k)
            if not pieza:
                continue
            im = cc.pieza_en_cuadro(pieza, lugares)
            c = cc.caja(np.asarray(im)[..., 3] > 8) if im is not None else None
            if c:
                caja_total = _union(caja_total, c)
        return caja_total

    # --- utilidades --------------------------------------------------------

    def evidencia(self, imagen: Image.Image, res: ResultadoPaso, nombre: str) -> str | None:
        if not self.evidencias:
            return None
        self.dir_evid.mkdir(parents=True, exist_ok=True)
        ruta = self.dir_evid / f"{res.paso.nombre_archivo}_{nombre}.png"
        imagen.save(ruta)
        return ruta.relative_to(self.salida).as_posix()

    def fondo_de(self, img) -> np.ndarray:
        """La tinta tal como quedó en este cuadro (mediana de las cuatro esquinas), si está
        cerca de la esperada; si no (hay algo en las esquinas), la esperada."""
        e = 8
        esquinas = np.concatenate([img[:e, :e].reshape(-1, 3), img[:e, -e:].reshape(-1, 3),
                                   img[-e:, :e].reshape(-1, 3), img[-e:, -e:].reshape(-1, 3)])
        med = np.median(esquinas, axis=0)
        if np.abs(med - self.fondo_esperado).max() <= self.U["fondo_tolerancia_esquinas"]:
            return med.astype(np.int16)
        return self.fondo_esperado

    def log(self, texto):
        with self._candado:
            print(texto, flush=True)

    # --- regla: pasos (por diapositiva) ---------------------------------------

    def regla_pasos(self, d: cc.Diapo):
        carpeta = self.carpeta / d.id
        n = len(d.pasos)
        if not carpeta.is_dir():
            nivel = "aviso" if self.parcial else "error"
            self.globales.append(Hallazgo(nivel, "pasos", d.id,
                                          f"no hay videos: falta la carpeta {self.rutas.relativa(carpeta)}/ "
                                          f"(deck.json tiene {n} paso{'s' if n != 1 else ''})"))
            return
        patron = re.compile(rf"^{re.escape(d.id)}_(\d+)\.mp4$")
        hay, raros = set(), []
        for f in sorted(carpeta.iterdir()):
            if f.is_dir():
                continue
            m = patron.match(f.name)
            if m:
                hay.add(int(m.group(1)))
            elif f.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm", ".m4v"):
                raros.append(f.name)
        faltan = [k for k in range(1, n + 1) if k not in hay]
        sobran = sorted(k for k in hay if k < 1 or k > n)
        if faltan:
            self.globales.append(Hallazgo("error", "pasos", d.id,
                                          f"falta{'n' if len(faltan) > 1 else ''} "
                                          f"{', '.join(f'{d.id}_{k}.mp4' for k in faltan)}: deck.json tiene {n} "
                                          f"paso{'s' if n != 1 else ''} y hay {len(hay & set(range(1, n + 1)))}"))
        if sobran:
            self.globales.append(Hallazgo("error", "pasos", d.id,
                                          f"sobra{'n' if len(sobran) > 1 else ''} "
                                          f"{', '.join(f'{d.id}_{k}.mp4' for k in sobran)}: deck.json tiene {n} "
                                          f"paso{'s' if n != 1 else ''}"))
        if raros:
            self.globales.append(Hallazgo("aviso", "pasos", d.id,
                                          f"videos con un nombre que no es <ID>_<k>.mp4: {', '.join(raros)}"))

    # --- análisis de un paso -------------------------------------------------

    def analizar(self, paso: cc.Paso) -> ResultadoPaso:
        res = ResultadoPaso(paso=paso, video=paso.video(self.carpeta))
        try:
            self._analizar(res)
        except cc.ErrorVideo as e:
            res.marcar("formato", "error", f"no se pudo leer el video: {e}")
        except Exception as e:  # noqa: BLE001 - un paso roto no frena a los demás
            res.marcar("formato", "error", f"el auditor falló en este paso: {type(e).__name__}: {e}",
                       traza=traceback.format_exc())
        if not res.existe:
            marca = "falta"
        elif any(h.nivel == "error" for h in res.hallazgos):
            marca = "ERROR"
        elif any(h.nivel == "aviso" for h in res.hallazgos):
            marca = "aviso"
        else:
            marca = "ok"
        self.log(f"  {paso.clave:<6} {marca}")
        return res

    def _analizar(self, res: ResultadoPaso):
        paso = res.paso
        if not res.video.exists():
            for r in COLUMNAS + (["audio"] if self.final else []):
                res.estados[r] = "pendiente"
            return
        res.existe = True
        probe = cc.ffprobe(res.video)
        tam = self.regla_formato(res, probe)
        if tam is None:
            return
        res.geometria = tam == (cc.ANCHO, cc.ALTO)
        self.regla_duracion(res)
        primero = cc.primer_cuadro(res.video, tam)
        hasta = max(2, int(round(max(self.U["quietud_medir_hasta_s"], self.U["quietud_s"]) * cc.FPS)) + 1)
        finales = cc.ultimos_cuadros(res.video, hasta, tam)
        ultimo = np.array(finales[-1])
        self.cache.mkdir(parents=True, exist_ok=True)
        res.primero = self.cache / f"{paso.nombre_archivo}_primero.png"
        res.ultimo = self.cache / f"{paso.nombre_archivo}_ultimo.png"
        cc.guardar_png(primero, res.primero, nivel=1)
        cc.guardar_png(ultimo, res.ultimo, nivel=1)
        self.regla_quietud(res, finales)
        del finales
        if not res.geometria:
            for r in ("zona_segura", "zonas_reservadas", "lima"):
                res.estados[r] = "pendiente"
                res.detalle[r] = "no mide 1920x1080"
        else:
            fondo = self.fondo_de(ultimo)
            contenido = cc.mascara_contenido(ultimo, fondo, self.U["fondo_umbral"])
            lima = cc.mascara_lima(ultimo)
            self.regla_zona_segura(res, ultimo, contenido)
            self.regla_zonas(res, ultimo, contenido, lima)
            self.regla_lima(res, ultimo, lima, tam)
        if self.final:
            self.regla_audio(res, probe)

    # --- regla: formato --------------------------------------------------------

    def regla_formato(self, res: ResultadoPaso, probe):
        """Devuelve (ancho, alto) del video, o None si no tiene video."""
        v = cc.stream_video(probe)
        fmt_ = probe.get("format", {})
        if v is None:
            res.marcar("formato", "error", "no tiene pista de video")
            return None
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        fps = cc.fraccion(v.get("r_frame_rate"))
        afps = cc.fraccion(v.get("avg_frame_rate"))
        n = cc.contar_cuadros(res.video, probe)
        dur = n / (fps or cc.FPS)
        res.info.update({"ancho": w, "alto": h, "fps": v.get("r_frame_rate"), "cuadros": n, "duracion_s": round(dur, 3),
                         "codec": v.get("codec_name"), "perfil": v.get("profile"), "pix_fmt": v.get("pix_fmt"),
                         "color": [v.get("color_space"), v.get("color_primaries"), v.get("color_transfer"),
                                   v.get("color_range")],
                         "pistas_audio": len(cc.streams_audio(probe)), "bytes": int(fmt_.get("size", 0) or 0)})
        if "mp4" not in str(fmt_.get("format_name", "")):
            res.marcar("formato", "aviso", f"contenedor {fmt_.get('format_name')} (se espera MP4)")
        if v.get("codec_name") != "h264":
            res.marcar("formato", "error", f"códec {v.get('codec_name')}: tiene que ser H.264")
        elif v.get("profile") != "High":
            res.marcar("formato", "aviso", f"perfil {v.get('profile')}: la receta usa High")
        if (w, h) != (cc.ANCHO, cc.ALTO):
            res.marcar("formato", "error", f"mide {w}x{h}: tiene que ser {cc.ANCHO}x{cc.ALTO}")
        sar = v.get("sample_aspect_ratio")
        if sar not in (None, "1:1", "0:1", "N/A"):
            res.marcar("formato", "aviso", f"píxeles no cuadrados (SAR {sar})")
        if v.get("pix_fmt") != "yuv420p":
            res.marcar("formato", "error", f"formato de píxel {v.get('pix_fmt')}: tiene que ser yuv420p")
        if fps is None or abs(fps - cc.FPS) > 1e-6:
            res.marcar("formato", "error", f"{v.get('r_frame_rate')} cuadros por segundo: tiene que ser 30")
        elif afps is not None and abs(afps - cc.FPS) > 0.01:
            res.marcar("formato", "error", f"cuadros por segundo variables (promedio {fmt(afps, 3)}): tiene que ser "
                                           f"30 fijo")
        malas = [f"{k.replace('color_', '')} = {v.get(k) or 'sin etiqueta'}"
                 for k in ("color_space", "color_primaries", "color_transfer") if v.get(k) != "bt709"]
        if malas:
            res.marcar("formato", "error", f"no está etiquetado BT.709 ({'; '.join(malas)}): cada programa elegiría "
                                           f"sus propios colores")
        if v.get("color_range") != "tv":
            res.marcar("formato", "error", f"rango de color {v.get('color_range') or 'sin etiqueta'}: tiene que ser "
                                           f"tv (limitado), el de la receta")
        if v.get("field_order") not in (None, "progressive", "unknown"):
            res.marcar("formato", "aviso", f"orden de campos {v.get('field_order')}: se espera progresivo")
        auds = cc.streams_audio(probe)
        if auds and not self.final:
            res.marcar("formato", "error", f"tiene {len(auds)} pista{'s' if len(auds) > 1 else ''} de audio: los "
                                           f"pasos crudos van mudos (el ding se mezcla en render/final/)")
        if cc.moov_antes_que_mdat(res.video) is False:
            res.marcar("formato", "aviso", "el índice (moov) está al final: falta -movflags +faststart")
        dur_cab = float(v.get("duration") or fmt_.get("duration") or 0)
        if dur_cab and fps and abs(dur_cab - n / fps) > 1.5 / fps:
            res.marcar("formato", "aviso", f"el encabezado dice {fmt(dur_cab, 3)} s y los {n} cuadros dan "
                                           f"{fmt(n / fps, 3)} s")
        res.ok("formato", f"{n} cuadros")
        return (w, h)

    # --- regla: duración -------------------------------------------------------

    def regla_duracion(self, res: ResultadoPaso):
        if self.omitida(res, "duracion"):
            res.estados["duracion"] = "exceptuada"
            return
        d = res.info["duracion_s"]
        # En los crudos, el paso 1 de una entrada con fundido o puertas dura lo de deck.json
        # menos la transición, que armar.py final le pega delante.
        a = res.paso.duracion if self.final else res.paso.duracion_propia
        res.detalle["duracion"] = f"{fmt(d, 2)} / {fmt(a, 2)} s"
        if res.paso.duracion <= 0:
            res.marcar("duracion", "aviso", "deck.json no trae duracion_animacion_s para este paso")
            return
        if a <= 0:
            res.marcar("duracion", "error", f"deck.json da {fmt(res.paso.duracion, 2)} s y la transición de entrada "
                                            f"{fmt(res.paso.transicion_s, 2)} s: no queda video propio")
            return
        if res.paso.transicion_s and not self.final:
            res.detalle["duracion"] += f" (sin los {fmt(res.paso.transicion_s, 2)} s de transición)"
        u = lambda n: self.umbral(res, "duracion", n)  # noqa: E731
        holgura = u("duracion_final_holgura_s") if self.final else 0.0
        if d < a - max(u("duracion_error_menos_s"), u("duracion_error_menos_rel") * a):
            res.marcar("duracion", "error", f"dura {fmt(d, 2)} s y deck.json pide {fmt(a, 1)} s: le faltan "
                                            f"{fmt(a - d, 2)} s")
        elif d > a + holgura + max(u("duracion_error_mas_s"), u("duracion_error_mas_rel") * a):
            res.marcar("duracion", "error", f"dura {fmt(d, 2)} s y deck.json pide {fmt(a, 1)} s: le sobran "
                                            f"{fmt(d - a, 2)} s")
        elif d < a - u("duracion_aviso_menos_s"):
            res.marcar("duracion", "aviso", f"dura {fmt(d, 2)} s, {fmt(a - d, 2)} s menos que deck.json "
                                            f"({fmt(a, 1)} s): ¿se cortó la animación?")
        elif d > a + holgura + u("duracion_aviso_mas_s"):
            res.marcar("duracion", "aviso", f"dura {fmt(d, 2)} s, {fmt(d - a, 2)} s más que deck.json "
                                            f"({fmt(a, 1)} s)")
        res.ok("duracion")

    # --- regla: quietud --------------------------------------------------------

    def regla_quietud(self, res: ResultadoPaso, finales: list):
        """Cada uno de los últimos cuadros contra el último. Los umbrales están por encima del
        ruido entre el cuadro clave final y los anteriores, que es el mayor que deja la receta."""
        if self.omitida(res, "quietud"):
            res.estados["quietud"] = "exceptuada"
            return
        necesarios = max(2, int(round(self.umbral(res, "quietud", "quietud_s") * cc.FPS)))
        lim_b = self.umbral(res, "quietud", "quietud_bloque_max")
        lim_s = self.umbral(res, "quietud", "quietud_bloque_signo_max")
        ultimo = finales[-1]
        ultimo16 = ultimo.astype(np.int16)
        quietos, movido = 1, None
        for j in range(len(finales) - 2, -1, -1):
            bm, bs = cc.cambio_bloques(finales[j], ultimo16)
            if bm > lim_b or bs > lim_s:
                movido = (j, cc.diferencia(finales[j], ultimo))
                break
            quietos += 1
        seg = quietos / cc.FPS
        res.info["quieto_s"] = round(seg, 3)
        res.detalle["quietud"] = f"{'≥ ' if movido is None and len(finales) > 1 else ''}{fmt(seg, 2)} s"
        if quietos >= necesarios:
            res.ok("quietud")
            return
        if movido is None:
            res.marcar("quietud", "error", f"el video tiene {len(finales)} cuadro{'s' if len(finales) != 1 else ''}: "
                                           f"no alcanza para terminar {fmt(necesarios / cc.FPS, 2)} s quieto")
            return
        j, d = movido
        atras = len(finales) - 1 - j
        ev = None
        if self.evidencias:
            ev = self.evidencia(evidencia_tres(finales[j], ultimo,
                                               f"{res.clave} · quietud: cambia {fmt(atras / cc.FPS, 2)} s antes del final",
                                               [f"cuadro −{atras}", "último cuadro"]), res, "quietud")
        que = "el último cuadro cambia respecto del anterior" if atras == 1 else \
            f"termina en movimiento: solo los últimos {quietos} cuadros ({fmt(seg, 2)} s) están quietos"
        res.marcar("quietud", "error", f"{que} y hacen falta {necesarios} ({fmt(necesarios / cc.FPS, 2)} s); cambia en "
                                       f"{caja_txt(d['caja'])} (bloque máx. {fmt(d['bloque_max'])}, con signo "
                                       f"{fmt(d['bloque_signo_max'])})", evidencia=ev, quieto_s=seg)

    # --- regla: zona segura ------------------------------------------------------

    def zonas_del_paso(self, paso: cc.Paso) -> dict:
        """Las zonas reservadas que usa este paso, como rectángulos."""
        z = {}
        if self.lleva_marca(paso.clave):
            z["marca_agua"] = self.reservada_marca
        if self.lleva_chip(paso) is not None:
            z["chip"] = self.reservada_chip
        if self.lleva_reloj(paso.clave):
            rl = self.tokens.reloj
            ancho = self.U["reloj_busqueda_ancho_px"]
            z["reloj"] = (rl["cx"] - ancho, rl["cy"] - rl["alto"] / 2, rl["cx"] + ancho, rl["cy"] + rl["alto"] / 2)
        return z

    def regla_zona_segura(self, res: ResultadoPaso, img, contenido):
        if self.omitida(res, "zona_segura"):
            res.estados["zona_segura"] = "exceptuada"
            return
        banda = self.umbral(res, "zona_segura", "zona_segura_banda_px")
        seguro = self.tokens.zona_segura
        dentro = cc.mascara_rect(img.shape, [cc.expandir(seguro, banda)])
        permit = [cc.expandir(z, banda) for z in self.zonas_del_paso(res.paso).values()]
        permit += self.permitidos(res, "zona_segura")
        fuera = contenido & ~dentro & ~cc.mascara_rect(img.shape, permit)
        n = int(fuera.sum())
        if n < self.umbral(res, "zona_segura", "zona_segura_min_px"):
            res.ok("zona_segura")
            return
        c = cc.caja(fuera)
        lados = []
        if fuera[:, :max(0, seguro[0] - banda)].any():
            lados.append("izquierda")
        if fuera[:, min(img.shape[1], seguro[2] + banda):].any():
            lados.append("derecha")
        if fuera[:max(0, seguro[1] - banda), :].any():
            lados.append("arriba")
        if fuera[min(img.shape[0], seguro[3] + banda):, :].any():
            lados.append("abajo")
        ev = None
        if self.evidencias:
            ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · zona segura: {n} px fuera de los márgenes "
                                                      f"({', '.join(lados)})", self.tokens, fuera, [c]), res, "zona_segura")
        res.marcar("zona_segura", "error", f"{n} px de contenido fuera de los márgenes ({', '.join(lados)}): "
                                           f"{caja_txt(c)}; la zona segura es x {seguro[0]}-{seguro[2]}, "
                                           f"y {seguro[1]}-{seguro[3]}", evidencia=ev, px=n, caja=c)

    # --- regla: zonas reservadas -----------------------------------------------

    def _ajeno(self, res, contenido, dibujo, reservada, nombre, extra=()):
        """Contenido que no es el elemento, dentro de su zona reservada: las manchas de
        contenido (componentes conexas) que no tocan lo que ocupa el elemento, agrandado
        `halo_tolerancia_px`. Lo que sí lo toca es parte del dibujo o está pegado: eso lo ve la
        comparación con la referencia (regla_consistencia)."""
        tol = self.umbral(res, "zonas_reservadas", "halo_tolerancia_px", nombre)
        h, w = contenido.shape
        x0, y0, x1, y1 = (int(round(v)) for v in reservada)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
        sub = contenido[y0:y1, x0:x1].copy()
        if extra:
            sub &= ~cc.mascara_rect(contenido.shape, list(extra))[y0:y1, x0:x1]
        etiquetas, _ = ndimage.label(sub, structure=np.ones((3, 3), bool))
        propia = cc.mascara_rect(contenido.shape, [cc.expandir(dibujo, tol)])[y0:y1, x0:x1]
        ids = np.unique(etiquetas[propia & sub])
        m = np.zeros_like(contenido)
        m[y0:y1, x0:x1] = sub & ~np.isin(etiquetas, ids)
        return int(m.sum()), cc.caja(m), m

    def _ev_zona(self, res, img, z, titulo, nombre):
        if not self.evidencias:
            return None
        return self.evidencia(evidencia_cuadro(img, f"{res.clave} · {titulo}", self.tokens, None,
                                               [tuple(int(x) for x in z)]), res, nombre)

    def _recorte(self, res, nombre, img, z):
        """La zona reservada entera, para compararla con la referencia (regla_consistencia)."""
        x0, y0, x1, y1 = (int(round(v)) for v in z)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
        res.recortes[nombre] = (np.array(img[y0:y1, x0:x1]), (x0, y0, x1, y1))

    def regla_zonas(self, res: ResultadoPaso, img, contenido, lima):
        if self.omitida(res, "zonas_reservadas"):
            res.estados["zonas_reservadas"] = "exceptuada"
            return
        paso = res.paso
        partes = []
        ambar = cc.mascara_ambar(img, brillante=True)
        zonas = self.zonas_del_paso(paso)
        otras = lambda propia: [cc.expandir(z, 2) for k, z in zonas.items() if k != propia]  # noqa: E731
        u = lambda n, zona: self.umbral(res, "zonas_reservadas", n, zona)  # noqa: E731

        # Marca de agua: arriba a la izquierda, en todos los pasos menos los de la lista.
        z = self.zona_marca
        zm = cc.mascara_rect(img.shape, [z])
        n_lima = int((lima & zm).sum())
        pct = float((contenido & zm).sum() / max(1, zm.sum()) * 100)
        if self.omitida(res, "zonas_reservadas", "marca_agua"):
            pass
        elif "marca_agua" in zonas:
            if n_lima < u("marca_min_lima_px", "marca_agua") or pct < u("marca_min_contenido_pct", "marca_agua"):
                ev = self._ev_zona(res, img, z, "falta la marca de agua", "zonas_marca")
                res.marcar("zonas_reservadas", "error", f"falta la marca de agua arriba a la izquierda "
                                                        f"({caja_txt(z)}): {n_lima} px de lima y {fmt(pct)} % de "
                                                        f"contenido en su zona", evidencia=ev, zona="marca_agua")
            else:
                partes.append("marca")
                self._recorte(res, "marca_agua", img, self.reservada_marca)
            n, c, m = self._ajeno(res, contenido, z, self.reservada_marca, "marca_agua",
                                  otras("marca_agua") + self.permitidos(res, "zonas_reservadas", "marca_agua"))
            if n >= u("halo_min_px", "marca_agua"):
                ev = None
                if self.evidencias:
                    ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · algo ajeno en la zona de la marca de agua",
                                                         self.tokens, m, [c]), res, "zonas_marca_ajeno")
                res.marcar("zonas_reservadas", "error", f"hay algo que no es la marca de agua en su zona reservada "
                                                        f"({caja_txt(self.reservada_marca)}): {n} px en {caja_txt(c)}",
                           evidencia=ev, zona="marca_agua", ajeno=True)
        elif n_lima >= u("marca_min_lima_px", "marca_agua"):
            ev = self._ev_zona(res, img, z, "marca de agua en un paso que no la lleva", "zonas_marca")
            res.marcar("zonas_reservadas", "error", f"hay marca de agua ({n_lima} px de lima en su zona) y el guion "
                                                    f"dice que este paso no la lleva", evidencia=ev, zona="marca_agua")

        # Chip de piso: arriba a la derecha, en las diapositivas con «piso» en deck.json.
        z = self.zona_chip
        zm = cc.mascara_rect(img.shape, [z])
        n_amb = int((ambar & zm).sum())
        pct = float((contenido & zm).sum() / max(1, zm.sum()) * 100)
        piso = self.lleva_chip(paso)
        if self.omitida(res, "zonas_reservadas", "chip"):
            pass
        elif piso is not None:
            if n_amb < u("chip_min_ambar_px", "chip") or pct < u("chip_min_contenido_pct", "chip"):
                ev = self._ev_zona(res, img, z, f"falta el chip de piso {piso}", "zonas_chip")
                res.marcar("zonas_reservadas", "error", f"falta el chip de piso «{piso}» arriba a la derecha "
                                                        f"({caja_txt(z)}): {n_amb} px de ámbar y {fmt(pct)} % de "
                                                        f"contenido en su zona", evidencia=ev, zona="chip")
            else:
                partes.append(f"chip {piso}")
                self._recorte(res, f"chip_{piso}", img, self.reservada_chip)
            n, c, m = self._ajeno(res, contenido, z, self.reservada_chip, "chip",
                                  otras("chip") + self.permitidos(res, "zonas_reservadas", "chip"))
            if n >= u("halo_min_px", "chip"):
                ev = None
                if self.evidencias:
                    ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · algo ajeno en la zona del chip de piso",
                                                         self.tokens, m, [c]), res, "zonas_chip_ajeno")
                res.marcar("zonas_reservadas", "error", f"hay algo que no es el chip de piso en su zona reservada "
                                                        f"({caja_txt(self.reservada_chip)}): {n} px en {caja_txt(c)}",
                           evidencia=ev, zona="chip", ajeno=True)
        elif n_amb >= u("chip_min_ambar_px", "chip") and pct >= u("chip_min_contenido_pct", "chip"):
            ev = self._ev_zona(res, img, z, "¿un chip de piso en un paso sin piso?", "zonas_chip")
            res.marcar("zonas_reservadas", "aviso", f"en la zona del chip ({caja_txt(z)}) hay algo con ámbar y la "
                                                    f"diapositiva no tiene piso en deck.json: ¿quedó el chip?",
                       evidencia=ev, zona="chip")

        # Reloj grande: siempre en el mismo lugar, en los pasos de la lista.
        if "reloj" in zonas and not self.omitida(res, "zonas_reservadas", "reloj"):
            antes = res.errores_de("zonas_reservadas", "reloj")
            self._reloj(res, img, contenido, ambar)
            if res.errores_de("zonas_reservadas", "reloj") == antes:
                partes.append("reloj")
        res.ok("zonas_reservadas", ", ".join(partes) if partes else None)

    @staticmethod
    def _bloque_reloj(m, cx, cy, union):
        """Lo ámbar de la zona de búsqueda que es el reloj: el bloque que forman sus dígitos (los
        segmentos y los dígitos se unen a menos de 2 × `union` px) que pasa por su centro o, si el
        centro cae en un hueco (el «0»), el más grande. Lo ámbar suelto a más distancia (la palomita
        de un rótulo a 90 px, en D14.1) no es el reloj y no le corre el centro."""
        if union <= 0 or not m.any():
            return m
        etiquetas, k = ndimage.label(ndimage.binary_dilation(m, iterations=union))
        if k <= 1:
            return m
        e = int(etiquetas[int(round(cy)), int(round(cx))])
        if e == 0:
            cuenta = ndimage.sum(m, etiquetas, index=np.arange(1, k + 1))
            e = 1 + int(np.argmax(cuenta))
        return m & (etiquetas == e)

    def _reloj(self, res, img, contenido, ambar):
        rl = self.tokens.reloj
        cx, cy, alto = rl["cx"], rl["cy"], rl["alto"]
        u = lambda n: self.umbral(res, "zonas_reservadas", n, "reloj")  # noqa: E731
        aw, mg = u("reloj_busqueda_ancho_px"), u("reloj_busqueda_margen_px")
        abajo = cy + alto / 2 + mg
        if rl.get("luces_y"):  # las tres luces de la cuenta (28 px, con brillo) van debajo: no son el reloj
            abajo = min(abajo, rl["luces_y"] - 14 - 12)
        busq = (int(cx - aw), int(cy - alto / 2 - mg), int(cx + aw), int(abajo))
        m = self._bloque_reloj(ambar & cc.mascara_rect(img.shape, [busq]), cx, cy, int(u("reloj_union_px")))
        n = int(m.sum())
        lugar = f"centrado en ({cx:.0f}, {cy:.0f}) y con {alto:.0f} px de alto"
        if n < u("reloj_min_ambar_px"):
            ev = self._ev_zona(res, img, busq, "falta el reloj grande en su lugar", "zonas_reloj")
            res.marcar("zonas_reservadas", "error", f"no está el reloj grande en su lugar fijo ({lugar}): "
                                                    f"{n} px de ámbar encendido en {caja_txt(busq)}", evidencia=ev,
                       zona="reloj")
            return
        c = cc.caja(m)
        mcx, mcy, malto = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2, c[3] - c[1]
        res.info["reloj"] = {"centro": [round(mcx), round(mcy)], "alto": malto, "caja": list(c)}
        fallas = []
        if abs(mcy - cy) > u("reloj_tolerancia_y_px"):
            fallas.append(f"centro vertical en y {mcy:.0f} (va en {cy:.0f})")
        if abs(malto - alto) > u("reloj_tolerancia_alto_px"):
            fallas.append(f"{malto} px de alto (van {alto:.0f})")
        if abs(mcx - cx) > u("reloj_tolerancia_x_px"):
            fallas.append(f"centro horizontal en x {mcx:.0f} (va en {cx:.0f})")
        if fallas:
            ev = self._ev_zona(res, img, c, "el reloj grande no está en su lugar", "zonas_reloj")
            res.marcar("zonas_reservadas", "error", f"el reloj grande no está en su lugar fijo ({lugar}): "
                                                    f"{'; '.join(fallas)}", evidencia=ev, zona="reloj")
        # Nada ajeno encima ni pegado: lo brillante que no es cálido, dentro de su caja + 12 px.
        caja_r = cc.expandir(c, 12)
        ajeno = contenido & (img.max(axis=2) >= 115) & ~mascara_calida(img) & cc.mascara_rect(img.shape, [caja_r])
        perm = self.permitidos(res, "zonas_reservadas", "reloj")
        if perm:
            ajeno &= ~cc.mascara_rect(img.shape, perm)
        na = int(ajeno.sum())
        if na >= u("reloj_ajeno_min_px"):
            ca = cc.caja(ajeno)
            ev = None
            if self.evidencias:
                ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · algo encima del reloj grande", self.tokens,
                                                     ajeno, [ca]), res, "zonas_reloj_ajeno")
            res.marcar("zonas_reservadas", "error", f"hay algo que no es el reloj encima o pegado a él: {na} px en "
                                                    f"{caja_txt(ca)}", evidencia=ev, zona="reloj")

    # --- regla: lima -----------------------------------------------------------

    def lima_permitida(self, res: ResultadoPaso, clave: str, forma):
        """Dónde puede haber lima en el cuadro final del paso `clave`, como máscara; None si
        en todo el cuadro (paso de marca)."""
        if self.es_de_marca(clave):
            return None
        rects = []
        if self.lleva_marca(clave):
            rects.append(cc.expandir(self.reservada_marca, self.U["lima_holgura_px"]))
        for i, e in self.excepciones(clave, "lima"):
            for r in e.get("permitir") or []:
                rects.append(tuple(r))
                if clave == res.clave:
                    self.usar(res, i, e, f"se permite {caja_txt(r)}")
        return cc.mascara_rect(forma, rects)

    def regla_lima(self, res: ResultadoPaso, img, lima, tam):
        if self.omitida(res, "lima"):
            res.estados["lima"] = "exceptuada"
            return
        perm = self.lima_permitida(res, res.clave, img.shape)
        minimo = self.umbral(res, "lima", "lima_min_px")
        if perm is None:
            n = int(lima.sum())
            res.ok("lima", f"paso de marca, {n} px" if n else "paso de marca")
            return
        fuera = lima & ~perm
        n = int(fuera.sum())
        if n >= minimo:
            c = cc.caja(fuera)
            ev = None
            if self.evidencias:
                ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · lima fuera de la marca ({n} px)", self.tokens,
                                                     fuera, [c], color=(255, 0, 255)), res, "lima")
            res.marcar("lima", "error", f"{n} px de lima (#B8FF3C o vecinos) fuera de la marca de agua, en "
                                        f"{caja_txt(c)}: el lima es solo de la marca", evidencia=ev, px=n, caja=c)
        # Durante la animación, con muestreo. Al empezar puede quedar el lima del paso anterior
        # mientras se va: se permite donde lo permitía el anterior.
        if self.muestreo > 0 and res.info.get("cuadros", 0) > 1:
            permisos = [perm] + [self.lima_permitida(res, p, img.shape)
                                 for p in self.deck.predecesores(res.paso) if p != "tinta"]
            if all(p is not None for p in permisos):
                perm_anim = np.logical_or.reduce(permisos)
                cada = max(1, int(round(self.muestreo * cc.FPS)))
                peor = None
                for i, cuadro in cc.muestrear(res.video, cada, tam):
                    f = cc.mascara_lima(cuadro) & ~perm_anim
                    k = int(f.sum())
                    if k >= minimo and (peor is None or k > peor[1]):
                        peor = (i, k, cc.caja(f), np.array(cuadro), f)
                if peor:
                    i, k, c, cuadro, f = peor
                    ev = None
                    if self.evidencias:
                        ev = self.evidencia(evidencia_cuadro(cuadro, f"{res.clave} · lima durante la animación "
                                                                     f"(cuadro {i}, {fmt(i / cc.FPS, 2)} s)",
                                                             self.tokens, f, [c], color=(255, 0, 255)), res,
                                            "lima_animacion")
                    res.marcar("lima", "aviso", f"durante la animación hay lima fuera de la marca: {k} px en "
                                                f"{caja_txt(c)} en el cuadro {i} ({fmt(i / cc.FPS, 2)} s)",
                               evidencia=ev, cuadro=i, px=k)
        res.ok("lima")

    # --- regla: audio (--final) -------------------------------------------------

    def regla_audio(self, res: ResultadoPaso, probe):
        if self.omitida(res, "audio"):
            res.estados["audio"] = "exceptuada"
            return
        auds = cc.streams_audio(probe)
        t = res.paso.ding()
        if t is not None:
            if not auds:
                res.marcar("audio", "error", f"no tiene audio y deck.json pide el ding a los {fmt(t, 1)} s")
                return
            x = cc.leer_audio(res.video)
            inicio = inicio_sonido(x, 16000)
            if inicio is None:
                res.marcar("audio", "error", f"la pista de audio está muda y deck.json pide el ding a los {fmt(t, 1)} s")
                return
            res.info["ding_s"] = round(inicio, 3)
            dif = inicio - t
            if abs(dif) > self.umbral(res, "audio", "ding_error_s"):
                res.marcar("audio", "error", f"el ding empieza a los {fmt(inicio, 2)} s y deck.json lo pide a los "
                                             f"{fmt(t, 1)} s ({'+' if dif > 0 else '−'}{fmt(abs(dif), 2)} s)")
            elif abs(dif) > self.umbral(res, "audio", "ding_aviso_s"):
                res.marcar("audio", "aviso", f"el ding empieza a los {fmt(inicio, 2)} s; deck.json dice {fmt(t, 1)} s")
            res.ok("audio", f"ding a {fmt(inicio, 2)} s")
            return
        if auds:
            x = cc.leer_audio(res.video)
            pico = 20 * math.log10(max(1e-9, float(np.abs(x).max()) if len(x) else 1e-9))
            if pico > self.umbral(res, "audio", "silencio_dbfs"):
                res.marcar("audio", "aviso", f"suena algo (pico {fmt(pico)} dBFS) y deck.json no pide audio en este paso")
        res.ok("audio", "mudo" if not auds else "silencio")

    # --- regla: frontera ------------------------------------------------------

    def ultimo_de(self, clave: str):
        if clave in self.res and self.res[clave].ultimo:
            return cc.abrir_png(self.res[clave].ultimo)
        if clave not in self._ultimos_externos:
            img = None
            paso = self.deck.paso(clave)
            if paso and paso.video(self.carpeta).exists():
                try:
                    img = np.array(cc.ultimo_cuadro(paso.video(self.carpeta)))
                except cc.ErrorVideo:
                    img = None
            self._ultimos_externos[clave] = img
        return self._ultimos_externos[clave]

    def aceptable(self, d, tolerancia) -> bool:
        if d["veredicto"] == "IDÉNTICOS":
            return True
        return tolerancia == "vista" and d["psnr"] >= self.U["frontera_psnr_vista"] and \
            d["notables_pct"] < self.U["frontera_notables_pct"]

    def regla_frontera(self, res: ResultadoPaso):
        if not res.existe or res.primero is None:
            res.estados.setdefault("frontera", "pendiente")
            return
        if self.omitida(res, "frontera"):
            res.estados["frontera"] = "exceptuada"
            return
        if res.paso.k == 1:
            entrada = self.deck.diapo(res.paso.diapo).entrada
            if entrada.tipo == "corte":
                res.estados["frontera"] = "no aplica"
                res.detalle["frontera"] = "corte a propósito"
                return
            if entrada.con_transicion and not self.final:
                # El paso crudo arranca en su propio cuadro: la transición que lo une con la
                # anterior la pega armar.py final, y la frontera se comprueba con --final.
                res.estados["frontera"] = "no aplica"
                res.detalle["frontera"] = f"{entrada.tipo} de {fmt(entrada.segundos, 2)} s: se mira con --final"
                return
        preds = self.deck.predecesores(res.paso)
        tolerancia = self.tolerancia
        for i, e in self.excepciones(res.clave, "frontera"):
            if "anterior" in e:
                preds = list(e["anterior"])
                self.usar(res, i, e, f"entra desde {', '.join(preds)}")
            if "tolerancia" in e:
                tolerancia = e["tolerancia"]
                self.usar(res, i, e, f"tolerancia «{tolerancia}»")
        primero = cc.abrir_png(res.primero)
        es_inicio = res.paso is self.deck.diapos[0].pasos[0]
        if preds == ["tinta"]:
            if es_inicio:
                res.estados["frontera"] = "no aplica"
                res.detalle["frontera"] = "primer paso"
                return
            plano = np.empty_like(primero)
            plano[:] = self.fondo_esperado.astype(np.uint8)
            d = cc.diferencia(plano, primero)
            if not self.aceptable(d, "vista"):
                res.marcar("frontera", "error", f"entra desde tinta y el primer cuadro no es la tinta lisa "
                                                f"(máx. {d['max']}, PSNR {fmt(d['psnr'])} dB)")
            res.ok("frontera", "tinta")
            return
        probadas, faltan = [], []
        for p in preds:
            img = self.ultimo_de(p)
            if img is None:
                faltan.append(p)
            else:
                probadas.append((p, cc.diferencia(img, primero), img))
        if not probadas:
            res.estados["frontera"] = "pendiente"
            res.detalle["frontera"] = f"falta {', '.join(faltan)}"
            res.marcar("frontera", "nota", f"no se pudo comprobar la frontera: falta el video de {', '.join(faltan)}")
            return
        buenas = [(p, d) for p, d, _ in probadas if self.aceptable(d, tolerancia)]
        if buenas:
            p, d = buenas[0]
            res.ok("frontera", f"{p} {'=' if d['veredicto'] == 'IDÉNTICOS' else '≈'}")
            if d["veredicto"] != "IDÉNTICOS":
                res.marcar("frontera", "nota", f"frontera con {p} igual a la vista, no idéntica (máx. {d['max']}, "
                                               f"PSNR {fmt(d['psnr'])} dB): aceptada con tolerancia «vista»")
            otras = [q for q, dd, _ in probadas if q != p and not self.aceptable(dd, tolerancia)]
            if otras:
                res.marcar("frontera", "nota", f"empalma con {p}; si se entra desde {', '.join(otras)}, se verá un salto")
            if faltan:
                res.marcar("frontera", "nota", f"no se comprobó desde {', '.join(faltan)}: falta su video")
            return
        p, d, img = max(probadas, key=lambda t: t[1]["psnr"])
        ev = None
        if self.evidencias:
            ev = self.evidencia(evidencia_tres(img, primero, f"{res.clave} · frontera con {p}: {d['veredicto']}",
                                               [f"último cuadro de {p}", f"primer cuadro de {res.clave}"]), res,
                                "frontera")
        if d["veredicto"] == "IGUALES A LA VISTA":
            res.marcar("frontera", "error", f"la frontera con {p} no es idéntica al bit (iguales a la vista: máx. "
                                            f"{d['max']}, PSNR {fmt(d['psnr'])} dB): con la receta de frontera da 0; "
                                            f"¿se codificó sin la receta, o el paso arrancó de un PNG decodificado en "
                                            f"vez del cuadro sin pérdida?", evidencia=ev, psnr=d["psnr"], max=d["max"])
        else:
            res.marcar("frontera", "error", f"salto en la frontera con {p}: el primer cuadro no es el último de {p} "
                                            f"(máx. {d['max']}, PSNR {fmt(d['psnr'])} dB, {fmt(d['notables_pct'], 2)} % "
                                            f"de píxeles con más de 24) en {caja_txt(d['caja'])}", evidencia=ev,
                       psnr=d["psnr"], max=d["max"])

    # --- regla: primer cuadro de la charla ----------------------------------------

    def regla_primer_cuadro(self):
        if not self.deck.diapos or not self.deck.diapos[0].pasos:
            return
        paso = self.deck.diapos[0].pasos[0]
        res = self.res.get(paso.clave)
        if res is None:
            return
        if not res.existe or res.primero is None:
            res.estados["primer_cuadro"] = "pendiente"
            return
        if self.omitida(res, "primer_cuadro"):
            res.estados["primer_cuadro"] = "exceptuada"
            return
        img = cc.abrir_png(res.primero)
        negro = float((img.max(axis=2) <= self.umbral(res, "primer_cuadro", "negro_canal_max")).mean())
        media = tuple(int(x) for x in img.reshape(-1, 3).mean(axis=0))
        res.info["primer_cuadro"] = {"negro_pct": round(negro * 100, 2), "color_medio": list(media)}
        if negro >= self.umbral(res, "primer_cuadro", "negro_fraccion"):
            ev = None
            if self.evidencias:
                ev = self.evidencia(evidencia_cuadro(img, f"{res.clave} · el primer cuadro de la charla es negro",
                                                     self.tokens), res, "primer_cuadro")
            res.marcar("primer_cuadro", "error", f"el primer cuadro de la charla es negro ({fmt(negro * 100)} % de "
                                                 f"píxeles en negro puro, color medio {media}): tiene que ser la tinta "
                                                 f"del fondo, la misma de la diapositiva", evidencia=ev)
            return
        if self.deck.diapos[0].entra == ["tinta"]:
            plano = np.empty_like(img)
            plano[:] = self.fondo_esperado.astype(np.uint8)
            dd = cc.diferencia(plano, img)
            if not self.aceptable(dd, "vista"):
                res.marcar("primer_cuadro", "aviso", f"el guion dice que {paso.clave} entra desde tinta y el primer "
                                                     f"cuadro ya tiene contenido en {caja_txt(dd['caja'])}")
        res.ok("primer_cuadro", "tinta" if self.deck.diapos[0].entra == ["tinta"] else None)

    # --- la marca de agua y el chip, iguales en todos los pasos ---------------

    def referencia_asset(self, nombre: str):
        """El recorte de referencia de diseno/assets/, pasado por la receta (para comparar
        números con números), o None."""
        if nombre in self.referencias:
            return self.referencias[nombre]
        t = self.tokens
        if nombre == "marca_agua":
            claves, lugares = CLAVES_MARCA, [t.marca_agua, t.marca_agua_zona]
        else:
            n = nombre.split("_", 1)[1]
            claves, lugares = [f"chippiso{n}", f"chip{n}", f"chipdepiso{n}"], [t.chip, t.chip_zona]
        pieza = next((self.assets[k] for k in claves if k in self.assets), None)
        ref = None
        if pieza:
            ruta = pieza.get("cuadro") or pieza.get("transparente")
            im = cc.pieza_en_cuadro(pieza, lugares)
            if im is None:
                self.globales.append(Hallazgo("nota", "zonas_reservadas", "",
                                              f"no se sabe en qué píxel va {self.rutas.relativa(ruta)} (sin "
                                              f"diseno/assets/assets.json y de otro tamaño que su zona): no se usa "
                                              f"como referencia"))
                self.referencias[nombre] = None
                return None
            lienzo = Image.new("RGBA", (cc.ANCHO, cc.ALTO), t.rgb("tinta") + (255,))
            lienzo.alpha_composite(im)
            tmp = cc.carpeta_temporal(self.rutas, "referencia")
            try:
                plano = np.asarray(lienzo.convert("RGB"))
                cc.codificar_cuadros([plano, plano], tmp / "ref.mp4", self.rutas)
                dec = np.array(cc.ultimo_cuadro(tmp / "ref.mp4"))
            finally:
                for f in tmp.glob("*"):
                    f.unlink()
                tmp.rmdir()
            ref = (dec, ruta)
        self.referencias[nombre] = ref
        return ref

    def regla_consistencia(self):
        grupos = {}
        for res in self.res.values():
            for nombre, (rec, caja_) in res.recortes.items():
                grupos.setdefault(nombre, []).append((res, rec, caja_))
        for nombre, items in grupos.items():
            zona = "marca_agua" if nombre == "marca_agua" else "chip"
            asset = self.referencia_asset(nombre)
            mediana = None
            if asset:
                origen = self.rutas.relativa(asset[1])
            elif len(items) >= 3:
                origen = "la de los demás pasos (mediana)"
                formas = [r.shape for _, r, _ in items]
                forma = max(set(formas), key=formas.count)
                mediana = np.median(np.stack([r for _, r, _ in items if r.shape == forma]), axis=0).astype(np.uint8)
            else:
                continue
            for res, rec, (x0, y0, x1, y1) in items:
                if self.omitida(res, "zonas_reservadas", zona):
                    continue
                if any(h.datos.get("ajeno") and h.datos.get("zona") == zona for h in res.hallazgos):
                    continue  # ya se informó lo ajeno en esa zona: sería el mismo defecto dos veces
                ref = asset[0][y0:y1, x0:x1] if asset else mediana
                if ref.shape != rec.shape:
                    continue
                d = cc.diferencia(ref, rec, bloque=8)
                dif = np.abs(ref.astype(np.int16) - rec.astype(np.int16)).max(axis=2)
                cont = cc.mascara_contenido(ref, self.fondo_esperado, self.U["fondo_umbral"]) | \
                    cc.mascara_contenido(rec, self.fondo_esperado, self.U["fondo_umbral"])
                media = float(dif[cont].mean()) if cont.any() else 0.0
                lim_b = self.umbral(res, "zonas_reservadas", "consistencia_bloque_max", zona)
                lim_m = self.umbral(res, "zonas_reservadas", "consistencia_media_contenido", zona)
                if d["bloque_max"] > lim_b or media > lim_m:
                    quien = "la marca de agua" if zona == "marca_agua" else f"el chip de piso {nombre.split('_', 1)[1]}"
                    duda = "¿atenuada por el Foco, corrida o con algo encima?" if zona == "marca_agua" else \
                        "¿atenuado por el Foco, corrido, con otro dígito o con algo encima?"
                    ev = None
                    if self.evidencias:
                        ev = self.evidencia(evidencia_recortes(ref, rec, f"{res.clave} · {quien} {'distinta' if zona == 'marca_agua' else 'distinto'} de {origen}",
                                                               ["referencia", res.clave]), res, f"zonas_{nombre}_igual")
                    res.marcar("zonas_reservadas", "error", f"{quien} no es igual a {origen} (bloque máx. "
                                                            f"{fmt(d['bloque_max'])}, diferencia media {fmt(media)}): "
                                                            f"{duda}",
                               evidencia=ev, zona=zona)

    # --- todo junto -----------------------------------------------------------

    def correr(self) -> int:
        pasos = [p for d in self.diapos for p in d.pasos]
        print(f"Auditoría de {'los videos finales' if self.final else 'los pasos'} en "
              f"{self.rutas.relativa(self.carpeta)}/: {len(self.diapos)} diapositiva"
              f"{'s' if len(self.diapos) != 1 else ''}, {len(pasos)} paso{'s' if len(pasos) != 1 else ''}", flush=True)
        if self.evidencias and self.dir_evid.exists():
            for p in pasos:
                for f in self.dir_evid.glob(f"{p.nombre_archivo}_*.png"):
                    f.unlink()
        for d in self.diapos:
            self.regla_pasos(d)
        if self.todos and self.carpeta.is_dir():
            ids = {d.id for d in self.deck.diapos}
            for sub in sorted(self.carpeta.iterdir()):
                if sub.is_dir() and sub.name not in ids:
                    self.globales.append(Hallazgo("nota", "pasos", sub.name,
                                                  f"la carpeta {self.rutas.relativa(sub)}/ no es de ninguna "
                                                  f"diapositiva de deck.json"))
        with ThreadPoolExecutor(max_workers=self.hilos) as ex:
            for res in ex.map(self.analizar, pasos):
                self.res[res.clave] = res
        for p in pasos:
            self.regla_frontera(self.res[p.clave])
        self.regla_primer_cuadro()
        self.regla_consistencia()
        if self.todos:
            for i, e in enumerate(self.reglas.get("excepciones", [])):
                if i not in self.usadas:
                    self.globales.append(Hallazgo("nota", e["regla"], ",".join(e["pasos"]),
                                                  f"la excepción {i + 1} ({e['regla']} en {', '.join(e['pasos'])}) "
                                                  f"no se usó: ¿sigue haciendo falta?"))
        return self.informe(pasos)

    # --- informe ---------------------------------------------------------------

    def informe(self, pasos) -> int:
        hs = list(self.globales)
        for p in pasos:
            hs += self.res[p.clave].hallazgos
        errores = [h for h in hs if h.nivel == "error"]
        avisos = [h for h in hs if h.nivel == "aviso"]
        notas = [h for h in hs if h.nivel == "nota"]
        aprobado = not errores and not (self.a.estricto and avisos)
        ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.salida.mkdir(parents=True, exist_ok=True)
        alcance = "toda la charla" if self.todos else ", ".join(d.id for d in self.diapos)
        con_video = sum(1 for p in pasos if self.res[p.clave].existe)
        t = self.tokens
        cols = COLUMNAS + (["audio"] if self.final else [])
        plural = lambda n, s, p_="s": f"{n} {s}{'' if n == 1 else p_}"  # noqa: E731
        lineas = [
            f"# Auditoría de cuadros{' (videos finales)' if self.final else ''}",
            "",
            f"- Fecha: {ahora}",
            f"- Videos: `{self.rutas.relativa(self.carpeta)}/` ({'con transición y audio' if self.final else 'pasos crudos'})",
            f"- Alcance: {alcance} ({plural(len(self.diapos), 'diapositiva')}, {plural(len(pasos), 'paso')}, "
            f"{con_video} con video)",
            f"- Diseño: {('`' + self.rutas.relativa(t.archivo) + '`') if t.archivo else 'valores del guion'}; márgenes "
            f"x {t.zona_segura[0]}-{t.zona_segura[2]}, y {t.zona_segura[1]}-{t.zona_segura[3]}; marca de agua "
            f"{caja_txt(self.zona_marca)}; chip {caja_txt(self.zona_chip)}; reloj centrado en ({t.reloj['cx']:.0f}, "
            f"{t.reloj['cy']:.0f}) con {t.reloj['alto']:.0f} px de alto",
            f"- Frontera: {'exacta (idéntica al bit)' if self.tolerancia == 'exacta' else 'a la vista (PSNR ≥ 40 dB)'}; "
            f"lima durante la animación: "
            f"{('un cuadro cada ' + fmt(self.muestreo, 2) + ' s') if self.muestreo > 0 else 'no se mira'}",
            "",
            f"## Resultado: {'APROBADO' if aprobado else 'RECHAZADO'} — {plural(len(errores), 'error', 'es')}, "
            f"{plural(len(avisos), 'aviso')}",
            "",
        ]
        for nombre, lista, vacio in (("Errores", errores, "Ninguno."), ("Avisos", avisos, "Ninguno."),
                                     ("Notas", notas, "Ninguna.")):
            lineas += [f"## {nombre}", ""]
            if not lista:
                lineas.append(vacio)
            for h in lista:
                ev = f" · [evidencia]({h.evidencia})" if h.evidencia else ""
                lineas.append(f"- **{h.paso or '—'}** · `{h.regla}` · {h.mensaje}{ev}")
            lineas.append("")
        lineas += ["## Diseño y configuración usados", ""]
        lineas += [f"- Tokens: {('`' + self.rutas.relativa(t.archivo) + '`') if t.archivo else 'valores del guion'}."]
        lineas += [f"- Zonas reservadas: marca de agua {caja_txt(self.reservada_marca)}, chip "
                   f"{caja_txt(self.reservada_chip)} (lo que ocupa cada uno, más la «zona» de tokens.json)."]
        lineas += [f"- Sin marca de agua: {', '.join(self.sin_marca) or 'ninguno'} (de {self.origen_sin_marca})."]
        lineas += [f"- Con reloj grande: {', '.join(self.reglas.get('pasos_con_reloj_grande') or []) or 'ninguno'}; "
                   f"pasos de marca (lima libre): {', '.join(self.reglas.get('pasos_de_marca') or []) or 'ninguno'} "
                   f"(de `{self.rutas.relativa(self.rutas.reglas)}`)."]
        con_trans = [f"{d.id} ({d.entrada.tipo} {fmt(d.entrada.segundos, 2)} s)" for d in self.diapos
                     if d.entrada.con_transicion]
        lineas += [f"- Entradas con transición (campo «entrada» de deck.json): {', '.join(con_trans) or 'ninguna'}."]
        lineas += [f"- Quieto al final: {fmt(self.U['quietud_s'], 2)} s"
                   f"{' (pasos.respiro_s de tokens.json)' if t.respiro_s and 'quietud_s' not in (self.reglas.get('umbrales') or {}) else ''}."]
        lineas += [f"- {n}" for n in t.notas + self.notas_config]
        lineas.append("")
        lineas += ["## Por paso", "",
                   "| Paso | Video | " + " | ".join(c.replace("_", " ") for c in cols) + " |",
                   "|---|---|" + "---|" * len(cols)]
        etiqueta = {"ok": "ok", "error": "**ERROR**", "aviso": "aviso", "exceptuada": "exc.", "pendiente": "—",
                    "no aplica": "n/a"}
        for p in pasos:
            r = self.res[p.clave]
            celdas = []
            for c in cols:
                est = r.estados.get(c, "ok" if r.existe else "pendiente")
                det = r.detalle.get(c)
                celdas.append(f"{etiqueta.get(est, est)}{(' (' + det + ')') if det else ''}")
            video = f"{r.info.get('cuadros', '—')} cuadros" if r.existe else "falta"
            lineas.append(f"| {p.clave} | {video} | " + " | ".join(celdas) + " |")
        lineas += ["", "## Excepciones aplicadas", ""]
        aplicadas = [(p.clave, e) for p in pasos for e in self.res[p.clave].excepciones]
        lineas += [f"- {clave} · {e}" for clave, e in aplicadas] or ["Ninguna."]
        lineas += ["", "## Umbrales", "", "| Umbral | Valor |", "|---|---|"]
        lineas += [f"| `{k}` | {v} |" for k, v in self.U.items()]
        lineas += ["", "Qué mide cada regla y cómo marcar excepciones: `docs/auditoria.md`.", ""]
        self.informe_md.write_text("\n".join(lineas), encoding="utf-8")

        def h2d(h):
            datos = {k: (None if isinstance(v, float) and math.isinf(v) else v) for k, v in h.datos.items()}
            return {"nivel": h.nivel, "regla": h.regla, "paso": h.paso, "mensaje": h.mensaje, "evidencia": h.evidencia,
                    "datos": datos}

        def estados(r):
            e = {c: r.estados.get(c, "ok" if r.existe else "pendiente") for c in cols}
            if "primer_cuadro" in r.estados:
                e["primer_cuadro"] = r.estados["primer_cuadro"]
            return e

        datos = {
            "fecha": ahora,
            "modo": "final" if self.final else "pasos",
            "videos": self.rutas.relativa(self.carpeta),
            "alcance": [d.id for d in self.diapos],
            "todos": self.todos,
            "resultado": {"aprobado": aprobado, "errores": len(errores), "avisos": len(avisos), "notas": len(notas)},
            "parametros": {"tolerancia_frontera": self.tolerancia, "muestreo_s": self.muestreo, "parcial": self.parcial,
                           "estricto": bool(self.a.estricto)},
            "diseno": {"tokens": self.rutas.relativa(t.archivo) if t.archivo else None, "zona_segura": t.zona_segura,
                       "marca_agua": self.zona_marca, "marca_agua_reservada": self.reservada_marca,
                       "chip": self.zona_chip, "chip_reservada": self.reservada_chip, "reloj": t.reloj,
                       "sin_marca_de_agua": self.sin_marca, "sin_marca_de_agua_origen": self.origen_sin_marca,
                       "entradas": {d.id: {"tipo": d.entrada.tipo, "segundos": d.entrada.segundos,
                                           "desde": d.entrada.desde, "origen": d.entrada.origen} for d in self.diapos},
                       "colores": {k: "#%02X%02X%02X" % v for k, v in t.colores.items()}, "origen": t.origen,
                       "notas": t.notas, "tinta_decodificada": [int(x) for x in self.fondo_esperado]},
            "umbrales": self.U,
            "errores": [h2d(h) for h in errores],
            "avisos": [h2d(h) for h in avisos],
            "notas": [h2d(h) for h in notas],
            "pasos": [{"paso": p.clave, "video": self.rutas.relativa(self.res[p.clave].video),
                       "existe": self.res[p.clave].existe, "info": self.res[p.clave].info,
                       "estados": estados(self.res[p.clave]), "detalle": self.res[p.clave].detalle,
                       "excepciones": self.res[p.clave].excepciones} for p in pasos],
        }
        self.informe_json.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=_json_default),
                                     encoding="utf-8")
        print()
        for h in errores:
            print(f"  ERROR  {h.paso or '—':<6} {h.regla}: {h.mensaje}")
        for h in avisos:
            print(f"  aviso  {h.paso or '—':<6} {h.regla}: {h.mensaje}")
        print(f"\n{'APROBADO' if aprobado else 'RECHAZADO'}: {plural(len(errores), 'error', 'es')}, "
              f"{plural(len(avisos), 'aviso')}, {plural(len(notas), 'nota')}.")
        print(f"Informe: {self.rutas.relativa(self.informe_md)} y {self.rutas.relativa(self.informe_json)}")
        return 0 if aprobado else 1


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Path):
        return o.as_posix()
    if isinstance(o, tuple):
        return list(o)
    return str(o)


def inicio_sonido(x: np.ndarray, sr: int, relativo: float = 0.2, absoluto: float = 0.01) -> float | None:
    """Segundo en que empieza el primer sonido fuerte: la envolvente (máximo en ventanas de
    5 ms) pasa el 20 % del pico y -40 dBFS."""
    v = max(1, sr // 200)
    n = len(x) // v
    if n == 0:
        return None
    env = np.abs(x[:n * v]).reshape(n, v).max(axis=1)
    pico = float(env.max())
    if pico < absoluto:
        return None
    return int(np.argmax(env >= max(absoluto, relativo * pico))) * v / sr


def main(argv=None) -> int:
    cc.consola_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="diapositivas (D05 D07 A1...)")
    p.add_argument("--todos", action="store_true", help="toda la charla")
    p.add_argument("--final", action="store_true", help="audita render/final/ (con transición y audio)")
    p.add_argument("--parcial", action="store_true", help="una diapositiva sin render es aviso, no error")
    p.add_argument("--tolerancia-frontera", choices=["exacta", "vista"])
    p.add_argument("--muestreo", type=float, help="segundos entre cuadros mirados para el lima (0 = solo el final)")
    p.add_argument("--estricto", action="store_true", help="los avisos también hacen fallar")
    p.add_argument("--sin-evidencias", action="store_true")
    p.add_argument("--hilos", type=int, default=2, help="pasos en paralelo (2 por defecto)")
    p.add_argument("--informe", help="nombre base del informe, sin extensión")
    g = p.add_argument_group("rutas (para las pruebas)")
    g.add_argument("--deck")
    g.add_argument("--guion")
    g.add_argument("--tokens")
    g.add_argument("--assets")
    g.add_argument("--reglas")
    g.add_argument("--videos", help="carpeta con <ID>/<ID>_<k>.mp4 (en vez de render/pasos o render/final)")
    g.add_argument("--salida", help="carpeta del informe (en vez de render/revision)")
    g.add_argument("--temporal")
    a = p.parse_args(argv)
    if not a.ids and not a.todos:
        p.error("faltan las diapositivas (D05 D07...) o --todos")
    try:
        aud = Auditor(a)
    except ErrorReglas as e:
        print(e, file=sys.stderr)
        return 2
    except ValueError as e:
        p.error(str(e))
    return aud.correr()


if __name__ == "__main__":
    sys.exit(main())
