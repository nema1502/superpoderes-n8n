# -*- coding: utf-8 -*-
"""Auditor del TEXTO de una presentacion .pptx.

El auditor de escenas mira geometria de Manim; este mira lo otro que se
rompe y nadie revisa: texto que se desborda de su cuadro, marcadores vacios
que muestran el ejemplo de la plantilla, erratas, y mezcla de tuteo con voseo
en la misma charla.

La medicion de desborde NO se estima contando caracteres: se le pregunta a
PowerPoint cuanto ocupa el texto ya compuesto (TextRange2.BoundHeight) y se
compara con el alto real del cuadro. Estimar da falsos positivos y falsos
negativos; medir, no.

Uso:
    python auditor/auditar_presentacion.py aws/AWS_Marketplace_....pptx
"""

import argparse
import re
import sys
from pathlib import Path

from pptx import Presentation

# ---------------- Reglas ----------------
# El texto puede salirse de su marcador sin molestar a nadie (esta plantilla
# no usa autoajuste). Lo que NO puede es meterse en el pie ni salirse por el
# costado: eso si lo ve la sala.
MARGEN_PIE = 40.0        # pt: banda inferior donde vive el pie del evento
MARGEN_LATERAL = 18.0    # pt
SOLAPE_TEXTO_MAX = 0.06  # dos bloques encimados mas que esto es un defecto
VINETAS_MAX = 6          # mas de esto en una diapositiva ya no se lee
CARACTERES_VINETA_MAX = 130
TITULO_MAX = 78
NOTAS_MIN = 25           # una nota mas corta que esto no ayuda a nadie

# Muestras de ejemplo de la plantilla que NUNCA deben quedar en la salida
TEXTO_PLANTILLA = ("speaker name", "lorem ipsum", "click to edit",
                   "haga clic", "titulo de", "sample text", "your title")

# Voseo vs tuteo: mezclarlos en la misma charla suena descuidado
VOSEO = re.compile(
    r"\b(quer[ée]s|sab[ée]s|ten[ée]s|pod[ée]s|busc[áa]s|suscrib[íi]s|"
    r"ten[ée]s|entr[áa]|mir[áa]|dej[áa]|prob[áa]|acord[áa]te|fij[áa]te|"
    r"sos|and[áa]|le[ée]|dec[íi]|hac[ée]s|us[áa]s)\b", re.IGNORECASE)
# Formas que solo pueden ser tuteo, en cualquier posicion de la frase.
# Incluye los PRONOMBRES (tú, ti, contigo): sin ellos se colaba un "para ti"
# en un titulo, que es justo donde mas se nota.
TUTEO = re.compile(
    r"\b(quieres|sabes|tienes|puedes|buscas|suscribes|eres|haces|usas|"
    r"pagas|vienes|pones|dices|llevas|tú|ti|contigo|tuyo|tuya)\b",
    re.IGNORECASE)

# Imperativos ambiguos: "deja" es tuteo en «deja correr el video», pero NO en
# «blockchain deja de ser un proyecto». Solo cuentan cuando ABREN la frase,
# que es donde funcionan de verdad como orden. Sin este matiz la regla daba un
# falso positivo en el deck real y me mandaba a "corregir" algo correcto.
TUTEO_IMPERATIVO = re.compile(
    r"(?:^|[.;:]\s+)(?:\d+\.\s*)?"
    r"(entra|mira|deja|prueba|revisa|conecta|anda|abre|escribe|busca)\b",
    re.IGNORECASE)

# Erratas mecanicas
DOBLE_ESPACIO = re.compile(r"\S  +\S")
ESPACIO_ANTES_PUNTO = re.compile(r"\s+[,.;:!?]")
PALABRA_REPETIDA = re.compile(r"\b(\w{3,})\s+\1\b", re.IGNORECASE)
INTERROGACION_SIN_ABRIR = re.compile(r"^(?![^?]*¿)[^?]*\?")
EXCLAMACION_SIN_ABRIR = re.compile(r"^(?![^!]*¡)[^!]*!")

NIVEL_ERROR = "ERROR"
NIVEL_AVISO = "AVISO"


class Auditoria:
    def __init__(self, nombre):
        self.nombre = nombre
        self.hallazgos = []

    def registrar(self, nivel, donde, mensaje):
        self.hallazgos.append((nivel, donde, mensaje))

    @property
    def errores(self):
        return [h for h in self.hallazgos if h[0] == NIVEL_ERROR]

    @property
    def avisos(self):
        return [h for h in self.hallazgos if h[0] == NIVEL_AVISO]

    def informe(self):
        for nivel, donde, mensaje in self.hallazgos:
            print(f"  [{nivel}] {donde}: {mensaje}")
        ok = not self.errores
        print(f"  -> {'APROBADO' if ok else 'RECHAZADO'}: "
              f"{len(self.errores)} errores, {len(self.avisos)} avisos")
        return ok


def texto_de(shape):
    if not shape.has_text_frame:
        return ""
    return shape.text_frame.text


def revisar_erratas(aud, donde, texto):
    """Erratas mecanicas: las que un ojo cansado a las 2 AM no ve."""
    for linea in texto.split("\n"):
        limpio = linea.strip()
        if not limpio:
            continue
        if DOBLE_ESPACIO.search(limpio):
            aud.registrar(NIVEL_AVISO, donde,
                          f"espacio doble en «{limpio[:60]}»")
        if ESPACIO_ANTES_PUNTO.search(limpio):
            aud.registrar(NIVEL_AVISO, donde,
                          f"espacio antes de un signo en «{limpio[:60]}»")
        m = PALABRA_REPETIDA.search(limpio)
        if m:
            aud.registrar(NIVEL_ERROR, donde,
                          f"palabra repetida «{m.group(1)}» en «{limpio[:60]}»")
        if "?" in limpio and INTERROGACION_SIN_ABRIR.match(limpio):
            aud.registrar(NIVEL_AVISO, donde,
                          f"pregunta sin ¿ de apertura: «{limpio[:60]}»")
        if "!" in limpio and EXCLAMACION_SIN_ABRIR.match(limpio):
            aud.registrar(NIVEL_AVISO, donde,
                          f"exclamación sin ¡ de apertura: «{limpio[:60]}»")
        # una sola vez por linea: la coincidencia exacta ya la cubre la
        # busqueda por subcadena de abajo
        for muestra in TEXTO_PLANTILLA:
            if muestra in limpio.lower():
                aud.registrar(NIVEL_ERROR, donde,
                              f"quedó texto de ejemplo de la plantilla: "
                              f"«{limpio[:60]}»")
                break


def auditar_contenido(ruta):
    """Todo lo que se puede revisar sin abrir PowerPoint."""
    aud = Auditoria(Path(ruta).name)
    pres = Presentation(ruta)
    voseo_en, tuteo_en = [], []

    for i, slide in enumerate(pres.slides, 1):
        donde = f"diapositiva {i}"
        hay_texto = False
        for shape in slide.shapes:
            texto = texto_de(shape)
            if not texto.strip():
                continue
            hay_texto = True
            revisar_erratas(aud, donde, texto)
            if VOSEO.search(texto):
                voseo_en.append(i)
            if TUTEO.search(texto) or TUTEO_IMPERATIVO.search(texto):
                tuteo_en.append(i)

            lineas = [l for l in texto.split("\n") if l.strip()]
            es_titulo = (shape.is_placeholder
                         and shape.placeholder_format.idx == 0)
            if es_titulo and len(texto) > TITULO_MAX:
                aud.registrar(NIVEL_AVISO, donde,
                              f"título de {len(texto)} caracteres "
                              f"(máximo cómodo {TITULO_MAX})")
            if not es_titulo and len(lineas) > VINETAS_MAX:
                aud.registrar(NIVEL_ERROR, donde,
                              f"{len(lineas)} viñetas en un cuadro "
                              f"(máximo {VINETAS_MAX}): nadie las lee")
            for linea in lineas:
                if len(linea) > CARACTERES_VINETA_MAX:
                    aud.registrar(NIVEL_AVISO, donde,
                                  f"viñeta de {len(linea)} caracteres: "
                                  f"«{linea[:55]}…»")

        # marcadores vacios: en la presentacion muestran el texto de ejemplo
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 18:      # PICTURE
                continue
            if shape.has_text_frame and not shape.text_frame.text.strip():
                aud.registrar(NIVEL_ERROR, donde,
                              f"marcador idx={shape.placeholder_format.idx} "
                              f"vacío: mostrará el ejemplo de la plantilla")

        if hay_texto:
            notas = ""
            if slide.has_notes_slide:
                notas = slide.notes_slide.notes_text_frame.text.strip()
            if notas and len(notas) < NOTAS_MIN:
                aud.registrar(NIVEL_AVISO, donde,
                              f"nota del orador de {len(notas)} caracteres: "
                              f"demasiado corta para servir")

    if voseo_en and tuteo_en:
        aud.registrar(
            NIVEL_ERROR, "toda la charla",
            f"se mezcla voseo (diapositivas {sorted(set(voseo_en))}) con "
            f"tuteo (diapositivas {sorted(set(tuteo_en))}): elegí uno")
    return aud


def auditar_desbordes(ruta, aud):
    """Mide DONDE TERMINA el texto ya compuesto, y si choca con algo.

    Version 1 de esta regla comparaba el texto contra el rectangulo de su
    marcador y daba 14 errores en una presentacion que se veia perfecta: en
    esta plantilla los marcadores no llevan autoajuste, asi que el texto se
    sale del marcador con total normalidad y cae en zona vacia. Al publico
    eso no le molesta; lo que si le molesta es que el texto se meta en el pie
    de la diapositiva o se encime con otro. Eso es lo que se mide ahora.

    Devuelve False si PowerPoint no esta disponible: en ese caso el desborde
    NO se revisa, y se dice en voz alta en lugar de aprobar a ciegas.
    """
    try:
        import win32com.client
    except ImportError:
        return False
    # Cambio de la charla (22-oct-2026): si el usuario ya tiene PowerPoint
    # abierto, Dispatch se engancha a SU proceso; al final se cierra solo la
    # presentación abierta acá y nunca se llama a Quit(). El original del
    # estudio siempre llamaba a Quit() y le cerraba PowerPoint al usuario.
    # (en bytes: tasklist responde en la página de códigos de la consola, y en
    # un Windows en español "INFORMACIÓN" no se decodifica como UTF-8)
    import subprocess
    lista = subprocess.run(["tasklist", "/FI", "IMAGENAME eq POWERPNT.EXE", "/NH"],
                           capture_output=True).stdout
    ya_abierto = b"POWERPNT.EXE" in lista.upper()
    try:
        app = win32com.client.Dispatch("PowerPoint.Application")
        pres = app.Presentations.Open(str(Path(ruta).resolve()),
                                      WithWindow=False)
    except Exception:
        return False

    try:
        alto = float(pres.PageSetup.SlideHeight)
        ancho = float(pres.PageSetup.SlideWidth)
        for i in range(1, pres.Slides.Count + 1):
            slide = pres.Slides(i)
            donde = f"diapositiva {i}"
            bloques = []
            for j in range(1, slide.Shapes.Count + 1):
                shape = slide.Shapes(j)
                try:
                    if not shape.HasTextFrame or not shape.TextFrame.HasText:
                        continue
                    rango = shape.TextFrame2.TextRange
                    izq = float(shape.Left)
                    arriba = float(shape.Top)
                    der = izq + float(rango.BoundWidth)
                    fondo = arriba + float(rango.BoundHeight)
                    muestra = " ".join(rango.Text.split())[:45]
                    bloques.append((izq, arriba, der, fondo, muestra))

                    if fondo > alto - MARGEN_PIE:
                        aud.registrar(
                            NIVEL_ERROR, donde,
                            f"el texto llega hasta {fondo:.0f} pt y el pie de "
                            f"la diapositiva empieza en {alto - MARGEN_PIE:.0f}"
                            f" pt: se mete en el pie de página. «{muestra}…»")
                    if der > ancho - MARGEN_LATERAL:
                        aud.registrar(
                            NIVEL_ERROR, donde,
                            f"el texto llega a {der:.0f} pt de ancho "
                            f"(borde en {ancho:.0f}): se sale por la derecha. "
                            f"«{muestra}…»")
                except Exception:
                    continue

            # dos bloques de texto encimados: el defecto que mas se ve
            for a in range(len(bloques)):
                for b in range(a + 1, len(bloques)):
                    ax1, ay1, ax2, ay2, at = bloques[a]
                    bx1, by1, bx2, by2, bt = bloques[b]
                    solape_x = min(ax2, bx2) - max(ax1, bx1)
                    solape_y = min(ay2, by2) - max(ay1, by1)
                    if solape_x <= 2 or solape_y <= 2:
                        continue
                    menor = min((ax2 - ax1) * (ay2 - ay1),
                                (bx2 - bx1) * (by2 - by1))
                    if menor <= 0:
                        continue
                    fraccion = (solape_x * solape_y) / menor
                    if fraccion > SOLAPE_TEXTO_MAX:
                        aud.registrar(
                            NIVEL_ERROR, donde,
                            f"«{at}…» y «{bt}…» se enciman "
                            f"({fraccion * 100:.0f} %)")
    finally:
        pres.Close()
        if not ya_abierto:
            app.Quit()
    return True


def main():
    ap = argparse.ArgumentParser(description="Audita el texto de un .pptx")
    ap.add_argument("pptx")
    ap.add_argument("--sin-powerpoint", action="store_true",
                    help="no medir desbordes (util en maquinas sin Office)")
    args = ap.parse_args()

    print(f"\n== Auditando texto :: {Path(args.pptx).name} ==")
    aud = auditar_contenido(args.pptx)

    medido = False
    if not args.sin_powerpoint:
        medido = auditar_desbordes(args.pptx, aud)
    if not medido:
        print("  [!] sin PowerPoint: NO se midieron los desbordes de texto")

    ok = aud.informe()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
