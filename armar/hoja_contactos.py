"""Hojas de contactos para revisar los videos con los ojos: el último cuadro de cada paso.

Uso:
    python armar/hoja_contactos.py D05 D07             una hoja por diapositiva
    python armar/hoja_contactos.py --todos             todas, más la hoja general de la charla
    python armar/hoja_contactos.py --todos --proyector como se vería en un proyector desde la última fila
    python armar/hoja_contactos.py --todos --sala      lo mismo en una sala difícil (proyector de aula, luz encendida)
    python armar/hoja_contactos.py D05 --medios        además, el cuadro a mitad de cada animación
    python armar/hoja_contactos.py D05 --medios 3      tres cuadros intermedios por paso (25, 50 y 75 %)
    --guias     dibuja encima los márgenes y las zonas fijas (marca de agua, chip)
    --final     usa render/final/ en vez de render/pasos/

Deja en render/revision/: hoja_<ID>.png por diapositiva y, con --todos, hoja_charla.png
(con --proyector o --sala, los mismos nombres terminados en _proyector o _sala). Cada cuadro va
rotulado con su paso (D05.3), su título del guion y su duración.

--proyector simula la sala: achica el cuadro a 960x540 (lo que se pierde de detalle a la
distancia), baja el contraste a unos 18:1 y levanta el negro (la luz de la sala sobre la
pantalla), en luz lineal. Es optimista: un buen proyector en una sala oscura.

--sala simula una sala difícil (la que hay que aprobar): un proyector de aula con la luz
encendida (negro 0,115 y blanco 0,80 en luz lineal, unos 7:1), desenfoque gaussiano de σ = 1 px
a 960x540 y brillo de color al 60 % (los colores saturados rinden menos que el blanco: la parte
saturada de cada píxel × 0,6 en luz lineal). Ahí aparecen las líneas finas que se pierden y el
ámbar que queda más apagado que el hueso. Ninguna de las dos reemplaza probar en el proyector de
verdad (docs/convenciones.md §9).

El último cuadro sale de render/cuadros/ si extraer_cuadros.py ya lo sacó y está al día; si
no, se decodifica del video.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cuadros_comun as cc  # noqa: E402

FONDO_HOJA = (233, 233, 236)
TEXTO = (17, 17, 20)
TEXTO_SUAVE = (90, 90, 100)
BORDE = (120, 120, 128)
NEGRO_PROYECTOR = 0.04    # luz lineal: el negro que deja la luz de la sala sobre la pantalla
BLANCO_PROYECTOR = 0.80   # luz lineal: el blanco de un proyector de aula
# --sala: proyector de aula (DLP) con la luz de la sala encendida, visto desde el fondo
NEGRO_SALA = 0.115        # luz lineal: con 0,80 de blanco da unos 7:1
BLANCO_SALA = 0.80
SIGMA_SALA = 1.0          # px a 960x540: el desenfoque de la óptica y de la distancia
COLOR_SALA = 0.6          # brillo de color: lo saturado rinde 0,6 de lo que rinde el blanco


def fuente(tam, negrita=True):
    for f in (("segoeuib.ttf" if negrita else "segoeui.ttf"), "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{f}", tam)
        except OSError:
            continue
    return ImageFont.load_default()


def a_lineal(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def a_srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


def simular_proyector(img: np.ndarray, negro=NEGRO_PROYECTOR, blanco=BLANCO_PROYECTOR) -> np.ndarray:
    chico = np.asarray(Image.fromarray(np.ascontiguousarray(img)).resize((960, 540), Image.BOX), np.float32)
    lin = negro + a_lineal(chico) * (blanco - negro)
    return (a_srgb(lin) * 255 + 0.5).clip(0, 255).astype(np.uint8)


def _desenfocar(x: np.ndarray, sigma: float) -> np.ndarray:
    """Desenfoque gaussiano separable por canal (en luz lineal), con los bordes replicados."""
    if sigma <= 0:
        return x
    r = max(1, int(round(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.pad(x, ((r, r), (r, r), (0, 0)), mode="edge")
    filas = sum(k[i] * pad[:, i:i + x.shape[1]] for i in range(2 * r + 1))
    return sum(k[i] * filas[i:i + x.shape[0]] for i in range(2 * r + 1))


def simular_sala(img: np.ndarray, negro=NEGRO_SALA, blanco=BLANCO_SALA, sigma=SIGMA_SALA, color=COLOR_SALA) -> np.ndarray:
    """La sala difícil (--sala): a 960x540, brillo de color × `color` (la parte saturada de cada
    píxel, en luz lineal), desenfoque gaussiano de `sigma` px y el contraste de un proyector de aula
    con la luz encendida (negro y blanco en luz lineal). La misma cuenta que usó la revisión."""
    chico = np.asarray(Image.fromarray(np.ascontiguousarray(img)).resize((960, 540), Image.BOX), np.float64)
    x = a_lineal(chico)
    if color < 1.0:
        acromatico = x.min(axis=-1, keepdims=True)
        x = acromatico + (x - acromatico) * color
    x = _desenfocar(x, sigma)
    x = negro + x * (blanco - negro)
    return (a_srgb(x) * 255 + 0.5).clip(0, 255).astype(np.uint8)


def simular(img: np.ndarray, modo: str | None) -> np.ndarray:
    """El cuadro como se vería en la sala: `modo` = "proyector", "sala" o None (tal cual)."""
    if modo == "proyector":
        return simular_proyector(img)
    if modo == "sala":
        return simular_sala(img)
    return img


def guias(img: Image.Image, tokens: cc.Tokens, reloj: bool = False):
    """Márgenes (celeste) y zonas fijas reservadas (gris) encima del cuadro, a la escala de la
    celda; en los pasos con reloj grande, dos marcas con su alto y su centro."""
    d = ImageDraw.Draw(img)
    e = img.width / cc.ANCHO
    s = tokens.zona_segura
    d.rectangle([s[0] * e, s[1] * e, s[2] * e, s[3] * e], outline=(0, 200, 230), width=1)
    for z in (tokens.marca_agua_zona, tokens.chip_zona):
        d.rectangle([z[0] * e, z[1] * e, z[2] * e, z[3] * e], outline=(150, 150, 165), width=1)
    if reloj:
        rl = tokens.reloj
        for y in (rl["cy"] - rl["alto"] / 2, rl["cy"] + rl["alto"] / 2):
            d.line([(rl["cx"] - 150) * e, y * e, (rl["cx"] + 150) * e, y * e], fill=(150, 150, 165), width=1)
        d.line([rl["cx"] * e, (rl["cy"] - 8) * e, rl["cx"] * e, (rl["cy"] + 8) * e], fill=(150, 150, 165), width=1)


class Hojas:
    def __init__(self, a):
        self.a = a
        r = cc.Rutas()
        if a.deck:
            r.deck = Path(a.deck)
        if a.guion:
            r.guion = Path(a.guion)
        if a.tokens:
            r.tokens = Path(a.tokens)
        if a.reglas:
            r.reglas = Path(a.reglas)
        self.rutas = r
        self.tokens = cc.cargar_tokens(r)
        self.deck = cc.cargar_deck(r, self.tokens.transiciones)
        self.con_reloj = cc.cargar_reglas(r).get("pasos_con_reloj_grande") or []
        self.videos = Path(a.videos) if a.videos else (r.final if a.final else r.pasos)
        self.cuadros = Path(a.cuadros) if a.cuadros else (r.cuadros / "final" if a.final else r.cuadros)
        self.salida = Path(a.salida) if a.salida else r.revision
        self.modo = "sala" if a.sala else ("proyector" if a.proyector else None)
        self.sufijo = f"_{self.modo}" if self.modo else ""
        self.medios = int(a.medios or 0)
        self.fecha = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    # --- cuadros -------------------------------------------------------------

    def ultimo(self, paso: cc.Paso):
        video = paso.video(self.videos)
        if not video.exists():
            return None
        png = self.cuadros / f"{paso.nombre_archivo}_ultimo.png"
        if png.exists() and png.stat().st_mtime >= video.stat().st_mtime:
            return cc.abrir_png(png)
        return np.array(cc.ultimo_cuadro(video))

    def duracion(self, paso: cc.Paso) -> str:
        """La duración del video (la real, no la de deck.json: en los crudos, el paso 1 de una
        entrada con fundido o puertas no trae la transición)."""
        video = paso.video(self.videos)
        if video.exists():
            try:
                return f"{cc.fmt_num(cc.contar_cuadros(video) / cc.FPS, 2)} s"
            except cc.ErrorVideo:
                pass
        return f"{cc.fmt_num(paso.duracion)} s (deck)"

    def intermedios(self, paso: cc.Paso):
        """[(fracción, segundo, cuadro)] a 1/(n+1), 2/(n+1)... de la animación."""
        video = paso.video(self.videos)
        if not video.exists() or not self.medios:
            return []
        n = cc.contar_cuadros(video)
        dur = n / cc.FPS
        objetivo = paso.duracion if self.a.final else paso.duracion_propia  # sin la transición, en los crudos
        anim = objetivo if 0 < objetivo <= dur else dur
        salida = []
        for i in range(1, self.medios + 1):
            f = i / (self.medios + 1)
            t = min(f * anim, max(0.0, dur - 1 / cc.FPS))
            salida.append((f, t, np.array(cc.cuadro_en(video, t))))
        return salida

    def preparar(self, img, ancho, clave=""):
        """El cuadro listo para pegar: simulado de proyector si toca, al ancho de la celda."""
        if img is None:
            return None
        img = simular(img, self.modo)
        im = Image.fromarray(np.ascontiguousarray(img))
        alto = round(ancho * 9 / 16)
        if im.size != (ancho, alto):
            im = im.resize((ancho, alto), Image.LANCZOS if ancho < im.width else Image.BICUBIC)
        if self.a.guias:
            guias(im, self.tokens, cc.coincide(clave, self.con_reloj))
        return im

    # --- dibujo ----------------------------------------------------------------

    def celda(self, lienzo, dib, x, y, im, rotulo, extra, ancho, f_rot, f_extra, faltante="falta"):
        alto = round(ancho * 9 / 16)
        dib.text((x, y), rotulo, fill=TEXTO, font=f_rot)
        if extra:
            w = dib.textlength(extra, font=f_extra)
            dib.text((x + ancho - w, y + 2), extra, fill=TEXTO_SUAVE, font=f_extra)
        y_img = y + f_rot.size + 10
        if im is None:
            dib.rectangle([x, y_img, x + ancho - 1, y_img + alto - 1], fill=(70, 70, 76), outline=BORDE)
            w = dib.textlength(faltante, font=f_rot)
            dib.text((x + (ancho - w) / 2, y_img + alto / 2 - f_rot.size / 2), faltante, fill=(230, 230, 230), font=f_rot)
        else:
            lienzo.paste(im, (x, y_img))
            dib.rectangle([x - 1, y_img - 1, x + ancho, y_img + alto], outline=BORDE, width=1)

    def encabezado(self, dib, titulo, sub, ancho):
        dib.text((20, 16), titulo, fill=TEXTO, font=fuente(30))
        dib.text((20, 58), sub, fill=TEXTO_SUAVE, font=fuente(19, False))

    def subtitulo(self, que):
        partes = [que, self.rutas.relativa(self.videos) + "/", self.fecha]
        if self.modo == "proyector":
            partes.append("simulación de proyector: 960x540, contraste 18:1, negro levantado")
        elif self.modo == "sala":
            partes.append("sala difícil: 960x540, contraste 7:1, desenfoque σ 1 px, color al 60 %")
        if self.a.guias:
            partes.append("guías: márgenes en celeste, zonas fijas en gris")
        return " · ".join(partes)

    def hoja_diapo(self, d: cc.Diapo) -> Path:
        pasos = d.pasos
        with ThreadPoolExecutor(max_workers=2) as ex:
            ultimos = list(ex.map(self.ultimo, pasos))
            medios = list(ex.map(self.intermedios, pasos)) if self.medios else [[] for _ in pasos]
        f_rot, f_extra = fuente(22), fuente(19, False)
        gap, margen, cab = 20, 20, 100
        if self.medios:
            cols = self.medios + 1
            ancho = min(960, (1920 - (cols - 1) * gap) // cols)
            filas = len(pasos)
        else:
            cols = 1 if len(pasos) == 1 else 2
            ancho = 960
            filas = (len(pasos) + cols - 1) // cols
        alto_celda = f_rot.size + 10 + round(ancho * 9 / 16) + gap + 8
        W = margen * 2 + cols * ancho + (cols - 1) * gap
        H = cab + filas * alto_celda + margen
        lienzo = Image.new("RGB", (max(W, 900), H), FONDO_HOJA)
        dib = ImageDraw.Draw(lienzo)
        que = "último cuadro de cada paso" + (f" y {self.medios} intermedio{'s' if self.medios > 1 else ''}"
                                              if self.medios else "")
        self.encabezado(dib, f"{d.id} · {d.titulo}  ({d.motor}, {len(pasos)} paso{'s' if len(pasos) != 1 else ''})",
                        self.subtitulo(que), W)
        for i, (paso, ult) in enumerate(zip(pasos, ultimos)):
            rot = f"{paso.clave}" + (f" · {paso.titulo}" if paso.titulo else "")
            dur = self.duracion(paso)
            if self.medios:
                y = cab + i * alto_celda
                for j, (frac, t, img) in enumerate(medios[i]):
                    x = margen + j * (ancho + gap)
                    self.celda(lienzo, dib, x, y, self.preparar(img, ancho, paso.clave),
                               f"{paso.clave} · {round(frac * 100)} %", f"{cc.fmt_num(t, 2)} s", ancho, f_rot, f_extra)
                x = margen + self.medios * (ancho + gap)
                self.celda(lienzo, dib, x, y, self.preparar(ult, ancho, paso.clave), f"{paso.clave} · último", dur,
                           ancho, f_rot,
                           f_extra, faltante=f"falta {paso.nombre_archivo}.mp4")
                if not medios[i]:
                    for j in range(self.medios):
                        self.celda(lienzo, dib, margen + j * (ancho + gap), y, None, f"{paso.clave}", "", ancho, f_rot,
                                   f_extra, faltante="sin video")
            else:
                x = margen + (i % cols) * (ancho + gap)
                y = cab + (i // cols) * alto_celda
                self.celda(lienzo, dib, x, y, self.preparar(ult, ancho, paso.clave),
                           self.recortar(dib, rot, f_rot, ancho - 90), dur,
                           ancho, f_rot, f_extra, faltante=f"falta {paso.nombre_archivo}.mp4")
        sufijo_medios = "_medios" if self.medios else ""
        destino = self.salida / f"hoja_{d.id}{sufijo_medios}{self.sufijo}.png"
        destino.parent.mkdir(parents=True, exist_ok=True)
        lienzo.save(destino)
        return destino

    @staticmethod
    def recortar(dib, texto, f, ancho):
        if dib.textlength(texto, font=f) <= ancho:
            return texto
        while texto and dib.textlength(texto + "…", font=f) > ancho:
            texto = texto[:-1]
        return texto + "…"

    def hoja_general(self, diapos) -> Path:
        cols, ancho, gap, margen, cab = 6, 304, 14, 20, 100
        alto_img = round(ancho * 9 / 16)
        f_rot, f_sec = fuente(17), fuente(24)
        secciones = []
        for seccion, nombre in (("principal", "Camino principal"), ("respaldo", "Respaldo (solo si preguntan)")):
            pasos = [p for d in diapos if (d.seccion or "principal") == seccion for p in d.pasos]
            if pasos:
                secciones.append((nombre, pasos))
        otros = [p for d in diapos if (d.seccion or "principal") not in ("principal", "respaldo") for p in d.pasos]
        if otros:
            secciones.append(("Otras", otros))
        todos = [p for _, ps in secciones for p in ps]
        with ThreadPoolExecutor(max_workers=2) as ex:
            ultimos = dict(zip((p.clave for p in todos), ex.map(self.ultimo, todos)))
        alto_celda = f_rot.size + 8 + alto_img + gap
        H = cab
        for _, ps in secciones:
            H += 44 + ((len(ps) + cols - 1) // cols) * alto_celda
        W = margen * 2 + cols * ancho + (cols - 1) * gap
        lienzo = Image.new("RGB", (W, H + margen), FONDO_HOJA)
        dib = ImageDraw.Draw(lienzo)
        con = sum(1 for v in ultimos.values() if v is not None)
        self.encabezado(dib, f"La charla entera: {len(todos)} pasos ({con} con video)",
                        self.subtitulo("último cuadro de cada paso"), W)
        y = cab
        for nombre, ps in secciones:
            dib.text((margen, y + 6), nombre, fill=TEXTO, font=f_sec)
            y += 44
            for i, p in enumerate(ps):
                x = margen + (i % cols) * (ancho + gap)
                yy = y + (i // cols) * alto_celda
                img = ultimos[p.clave]
                if img is not None:
                    img = simular(img, self.modo)
                im = None
                if img is not None:
                    im = Image.fromarray(np.ascontiguousarray(img)).resize((ancho, alto_img), Image.LANCZOS)
                    if self.a.guias:
                        guias(im, self.tokens, cc.coincide(p.clave, self.con_reloj))
                self.celda(lienzo, dib, x, yy, im, p.clave, self.duracion(p), ancho, f_rot, fuente(15, False))
            y += ((len(ps) + cols - 1) // cols) * alto_celda
        destino = self.salida / f"hoja_charla{self.sufijo}.png"
        destino.parent.mkdir(parents=True, exist_ok=True)
        lienzo.save(destino)
        return destino


def main(argv=None) -> int:
    cc.consola_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="diapositivas (D05 D07 A1...)")
    p.add_argument("--todos", action="store_true", help="todas las diapositivas y la hoja general")
    p.add_argument("--proyector", action="store_true", help="simula un proyector visto desde la última fila")
    p.add_argument("--sala", action="store_true",
                   help="simula una sala difícil: proyector de aula con luz (7:1), desenfoque y color al 60 %%")
    p.add_argument("--medios", nargs="?", type=int, const=1, default=0,
                   help="además, N cuadros a mitad de cada animación (1 si no se dice)")
    p.add_argument("--guias", action="store_true", help="dibuja los márgenes y las zonas fijas")
    p.add_argument("--final", action="store_true", help="usa render/final/")
    g = p.add_argument_group("rutas (para las pruebas)")
    g.add_argument("--deck")
    g.add_argument("--guion")
    g.add_argument("--tokens")
    g.add_argument("--reglas", help="en vez de armar/auditoria_reglas.json (qué pasos llevan el reloj grande)")
    g.add_argument("--videos")
    g.add_argument("--cuadros", help="carpeta de PNG ya extraídos (en vez de render/cuadros)")
    g.add_argument("--salida")
    a = p.parse_args(argv)
    if not a.ids and not a.todos:
        p.error("faltan las diapositivas (D05 D07...) o --todos")
    if a.medios < 0 or a.medios > 5:
        p.error("--medios va de 1 a 5")
    if a.sala and a.proyector:
        p.error("--sala y --proyector son dos simulaciones distintas: una por vez")
    h = Hojas(a)
    try:
        diapos = cc.elegir_diapos(h.deck, a.ids, a.todos)
    except ValueError as e:
        p.error(str(e))
    faltan = 0
    for d in diapos:
        destino = h.hoja_diapo(d)
        sin = [q.clave for q in d.pasos if not q.video(h.videos).exists()]
        faltan += len(sin)
        print(f"  {h.rutas.relativa(destino)}" + (f"  (sin video: {', '.join(sin)})" if sin else ""), flush=True)
    if a.todos:
        print(f"  {h.rutas.relativa(h.hoja_general(diapos))}")
    if faltan:
        print(f"{faltan} paso{'s' if faltan != 1 else ''} sin video: van como «falta» en las hojas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
