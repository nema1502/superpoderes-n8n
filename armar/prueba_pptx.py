"""Prueba de punta a punta del PowerPoint de la charla (python-pptx).

Arma un .pptx 16:9 de 2 diapositivas. Cada una es un paso: un MP4 a pantalla
completa que arranca SOLO al entrar a la diapositiva, sin controles a la vista,
con el primer cuadro como póster y con notas del orador. Es el molde del
PowerPoint final: las funciones de abajo (`presentacion_16x9`, `agregar_paso`,
`reproducir_al_entrar`, `ocultar_controles`) son las que va a usar el armado.

Los dos videos se hacen con ffmpeg (3 s, 1920x1080, h264, yuv420p, +faststart):
un video maestro sin pérdida de 6 s se parte en dos pasos que comparten el
cuadro de la frontera (0-89 y 89-179), y cada paso pasa por
armar/codificar_paso.py, la misma receta que los videos de Manim y Remotion.

Uso, desde la raíz del repositorio:
    .venv/Scripts/python.exe armar/prueba_pptx.py [--salida .tmp/pptx_prueba]
Deja prueba.pptx (la receta que se usa) y prueba_manim_slides.pptx (la de
manim-slides, para comparar). Después: armar/verificar_pptx.ps1 los abre en
PowerPoint y los revisa.

Reproducción automática: se partió de la receta de manim-slides 5.7.0
(manim_slides/convert.py, `_auto_play_pptx_media`, que sale de
https://github.com/scanny/python-pptx/issues/427#issuecomment-856724440:
cambiar a delay="0" el <p:cond delay="indefinite"/> que deja python-pptx), pero
PowerPoint 16.0 no la reconoce como "Iniciar: automáticamente" (PlayOnEntry
falso, ningún efecto). La que se usa es el XML que escribe el propio PowerPoint
para esa opción (ver `reproducir_al_entrar`). Los controles se apagan con
<p14:showMediaCtrls val="0"/> en presProps.xml, que PowerPoint respeta y
conserva al guardar. Todo lo medido está en docs/infra.md.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codificar_paso import codificar  # noqa: E402

# 16:9 "panorámica" de PowerPoint: 13,333 x 7,5 pulgadas.
ANCHO = Emu(12192000)
ALTO = Emu(6858000)
FONDO = RGBColor(0x07, 0x0A, 0x0F)  # tinta de nemaxyz: si el video tarda, no hay destello blanco

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
URI_CONTROLES = "{2FDB2607-1784-4EEB-B798-7EB5836EED8A}"  # extensión p14:showMediaCtrls de p:showPr


# ------------------------------------------------------------------ PowerPoint
def presentacion_16x9():
    prs = Presentation()
    prs.slide_width, prs.slide_height = ANCHO, ALTO
    return prs


# La secuencia principal que escribe el propio PowerPoint 16.0 cuando a un video
# se le pone "Iniciar: automáticamente" (copiada de un .pptx guardado por
# PowerPoint el 22-oct-2026, ver docs/infra.md): el efecto de reproducir
# (mediacall, playFrom(0.0)) como "después de la anterior" (afterEffect), que
# arranca con la secuencia (evt="onBegin" sobre el nodo 2). Los id se renumeran
# después. Se deja AFUERA la secuencia interactiva que PowerPoint agrega para que
# un clic sobre el video lo pause: con el video a pantalla completa, un clic del
# mouse pausaría en vez de pasar de diapositiva.
_SECUENCIA_AUTOMATICA = """
<p:seq xmlns:p="{p}" concurrent="1" nextAc="seek">
  <p:cTn id="0" dur="indefinite" nodeType="mainSeq">
    <p:childTnLst>
      <p:par>
        <p:cTn id="0" fill="hold">
          <p:stCondLst>
            <p:cond delay="indefinite"/>
            <p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>
          </p:stCondLst>
          <p:childTnLst>
            <p:par>
              <p:cTn id="0" fill="hold">
                <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="0" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="afterEffect">
                      <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                      <p:childTnLst>
                        <p:cmd type="call" cmd="playFrom(0.0)">
                          <p:cBhvr>
                            <p:cTn id="0" dur="1" fill="hold"/>
                            <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>
                          </p:cBhvr>
                        </p:cmd>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:par>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:childTnLst>
  </p:cTn>
  <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
  <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
</p:seq>
"""


def reproducir_al_entrar(movie, receta="powerpoint"):
    """El video arranca solo al entrar a la diapositiva.

    receta="powerpoint" (la que se usa): agrega la secuencia principal que
    escribe PowerPoint para "Iniciar: automáticamente"; en el modelo de objetos
    queda PlayOnEntry = verdadero y un efecto de reproducir "después de la
    anterior". El nodo del video (<p:video><p:cMediaNode>) queda como lo deja
    python-pptx, con delay="indefinite", igual que en los archivos de PowerPoint.

    receta="manim-slides": la de manim-slides 5.7.0 (`_auto_play_pptx_media`):
    solo cambia el delay del <p:cMediaNode> de "indefinite" a "0". PowerPoint la
    abre sin quejarse, pero su modelo de objetos dice PlayOnEntry = falso y
    ningún efecto; se deja para comparar (ver docs/infra.md).
    """
    # Con lxml directo y el espacio de nombres explícito: los nodos de <p:timing>
    # no son clases propias de python-pptx y su xpath no conoce el prefijo p:.
    ns = {"p": NS_P}
    sld = movie._element.getparent().getparent().getparent()  # p:pic -> p:spTree -> p:cSld -> p:sld
    tgt = etree._Element.xpath(sld, f'.//p:timing//p:video//p:spTgt[@spid="{movie.shape_id}"]', namespaces=ns)
    if len(tgt) != 1:
        raise RuntimeError(f"no encontré el nodo de tiempo del video {movie.shape_id}")
    if receta == "manim-slides":
        cond = etree._Element.xpath(tgt[0].getparent().getparent(), "./p:cTn/p:stCondLst/p:cond", namespaces=ns)
        if len(cond) != 1:
            raise RuntimeError("el nodo de tiempo del video no tiene una sola condición de arranque")
        cond[0].set("delay", "0")
        return
    if receta != "powerpoint":
        raise ValueError(receta)
    video = tgt[0].getparent().getparent().getparent()  # p:spTgt -> p:tgtEl -> p:cMediaNode -> p:video
    hijos = video.getparent()  # p:childTnLst del nodo raíz (tmRoot)
    if etree._Element.xpath(hijos, './p:seq/p:cTn[@nodeType="mainSeq"]', namespaces=ns):
        raise RuntimeError("la diapositiva ya tiene secuencia principal: una diapositiva = un video")
    seq = etree.fromstring(_SECUENCIA_AUTOMATICA.format(p=NS_P, spid=movie.shape_id))
    video.addprevious(seq)  # mismo orden que PowerPoint: secuencia principal, después el video
    for n, ctn in enumerate(etree._Element.xpath(sld, ".//p:timing//p:cTn", namespaces=ns), start=1):
        ctn.set("id", str(n))  # id únicos en orden de documento, como los numera PowerPoint


def agregar_paso(prs, video, poster, notas, nombre=None, receta="powerpoint"):
    """Una diapositiva = un paso: fondo tinta, el video a pantalla completa con
    su primer cuadro de póster, arranque automático y las notas del orador."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # en blanco
    relleno = slide.background.fill
    relleno.solid()
    relleno.fore_color.rgb = FONDO
    movie = slide.shapes.add_movie(str(video), 0, 0, prs.slide_width, prs.slide_height,
                                   poster_frame_image=str(poster), mime_type="video/mp4")
    if nombre:
        movie.name = nombre
    reproducir_al_entrar(movie, receta)
    slide.notes_slide.notes_text_frame.text = notas
    return slide, movie


def ocultar_controles(prs):
    """Apaga "Mostrar controles multimedia" de la presentación: así no aparece la
    barra de reproducción cuando el mouse pasa sobre el video en la sala."""
    parte = prs.part.part_related_by(RT.PRES_PROPS)
    raiz = etree.fromstring(parte.blob)
    show = raiz.find(f"{{{NS_P}}}showPr")
    if show is None:
        show = etree.Element(f"{{{NS_P}}}showPr")
        # orden del esquema: htmlPubPr, webPr, prnPr, showPr, clrMru, extLst
        siguiente = next((h for h in raiz if etree.QName(h).localname in ("clrMru", "extLst")), None)
        if siguiente is None:
            raiz.append(show)
        else:
            siguiente.addprevious(show)
    ext_lst = show.find(f"{{{NS_P}}}extLst")
    if ext_lst is None:
        ext_lst = etree.SubElement(show, f"{{{NS_P}}}extLst")
    for e in ext_lst.findall(f"{{{NS_P}}}ext"):
        if e.get("uri") == URI_CONTROLES:
            ext_lst.remove(e)
    ext = etree.SubElement(ext_lst, f"{{{NS_P}}}ext", uri=URI_CONTROLES)
    etree.SubElement(ext, f"{{{NS_P14}}}showMediaCtrls", nsmap={"p14": NS_P14}, val="0")
    parte._blob = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)


# ------------------------------------------------------------------ videos
FUENTE = r"C\:/Windows/Fonts/segoeuib.ttf"


def video_maestro(destino):
    """6 s sin pérdida: dos barras que se llenan (la de acento de 0 a 3 s, la gris
    de 3 a 6 s) y el rótulo del paso. Todo en RGB para que no haya conversiones."""
    filtro = (
        "color=c=0x070A0F:s=1920x1080:r=30:d=6[bg];"
        "color=c=0xFF7A59:s=1200x28:r=30:d=6[b1];"
        "color=c=0x9AA3B8:s=1200x28:r=30:d=6[b2];"
        "[bg][b1]overlay=x='360-1200+1200*min(t\\,3)/3':y=680[v1];"
        "[v1][b2]overlay=x='360-1200+1200*min(max(t-3\\,0)\\,3)/3':y=740[v2];"
        "[v2]drawbox=x=0:y=660:w=360:h=120:color=0x070A0F:t=fill,"
        f"drawtext=fontfile='{FUENTE}':text='Paso 1 de 2':fontsize=130:fontcolor=0xF5F7FF:"
        "x=(w-tw)/2:y=400:enable='lt(t\\,3)',"
        f"drawtext=fontfile='{FUENTE}':text='Paso 2 de 2':fontsize=130:fontcolor=0xF5F7FF:"
        "x=(w-tw)/2:y=400:enable='gte(t\\,3)',"
        f"drawtext=fontfile='{FUENTE}':text='prueba de PowerPoint · la charla':fontsize=40:"
        "fontcolor=0x9AA3B8:x=(w-tw)/2:y=880,format=rgb24"
    )
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-filter_complex", filtro, "-frames:v", "180",
                    "-c:v", "libx264rgb", "-qp", "0", "-preset", "veryfast", str(destino)], check=True)


def recortar(maestro, desde, hasta, destino):
    """Cuadros desde..hasta (inclusive) del maestro, sin pérdida."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(maestro),
                    "-vf", f"trim=start_frame={desde}:end_frame={hasta + 1},setpts=PTS-STARTPTS",
                    "-c:v", "libx264rgb", "-qp", "0", "-preset", "veryfast", str(destino)], check=True)


def primer_cuadro(video, png):
    """El póster: el primer cuadro DECODIFICADO del video que va a la diapositiva
    (no la imagen fuente), para que póster y video coincidan al bit."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-frames:v", "1", str(png)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--salida", default=".tmp/pptx_prueba")
    a = p.parse_args()
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)

    maestro = out / "maestro_sin_perdida.mp4"
    video_maestro(maestro)
    pasos = []
    for i, (desde, hasta) in enumerate([(0, 89), (89, 179)], start=1):
        crudo = out / f"paso{i}_sin_perdida.mp4"
        recortar(maestro, desde, hasta, crudo)
        video = out / f"paso{i}.mp4"
        codificar(crudo, video)
        poster = out / f"paso{i}_poster.png"
        primer_cuadro(video, poster)
        pasos.append((video, poster))

    notas = [
        "Paso 1. Esto es lo que dice el orador mientras la barra se llena.\n"
        "Segunda línea de la nota, con acentos: ñandú, acción, ¿qué?",
        "Paso 2. El video arrancó solo al entrar; la barra de arriba quedó llena "
        "porque las animaciones de una diapositiva son acumulativas.",
    ]
    ns = {"p": NS_P}
    for receta, nombre_archivo in [("powerpoint", "prueba.pptx"), ("manim-slides", "prueba_manim_slides.pptx")]:
        prs = presentacion_16x9()
        for i, ((video, poster), nota) in enumerate(zip(pasos, notas), start=1):
            agregar_paso(prs, video, poster, nota, nombre=f"Paso {i}", receta=receta)
        ocultar_controles(prs)
        destino = out / nombre_archivo
        prs.save(destino)

        # Control: python-pptx lo vuelve a abrir y el XML quedó como se quería.
        print(f"=== {destino} (receta {receta}, {destino.stat().st_size / 1024:.0f} KB)")
        prs2 = Presentation(destino)
        for n, slide in enumerate(prs2.slides, start=1):
            el = slide._element
            delay = etree._Element.xpath(el, ".//p:timing//p:video//p:cMediaNode/p:cTn/p:stCondLst/p:cond/@delay", namespaces=ns)
            efectos = etree._Element.xpath(el, './/p:timing//p:cTn[@presetClass="mediacall"]/@nodeType', namespaces=ns)
            ids = etree._Element.xpath(el, ".//p:timing//p:cTn/@id", namespaces=ns)
            print(f"  diapositiva {n}: cMediaNode delay={delay}, efectos={efectos}, id={ids}, "
                  f"notas={slide.notes_slide.notes_text_frame.text[:30]!r}...")
        if receta == "powerpoint":
            timing = prs2.slides[0]._element.find(f"{{{NS_P}}}timing")
            print("\n<p:timing> de la diapositiva 1:\n" + etree.tostring(timing, pretty_print=True).decode())
            props = prs2.part.part_related_by(RT.PRES_PROPS).blob.decode("utf-8")
            print("presProps.xml:\n" + props + "\n")


if __name__ == "__main__":
    main()
