"""El PowerPoint de la charla: una diapositiva por paso, con su video.

Usa el molde probado de armar/prueba_pptx.py (docs/infra.md §8): 16:9, fondo
tinta, el video a pantalla completa con su primer cuadro DECODIFICADO de póster,
"Iniciar: automáticamente" con el XML que escribe el propio PowerPoint y sin
controles multimedia. Agrega lo que la prueba no tenía:

- notas: `notas` del deck y, al final, «Fuente: …» y «Recortable: …» (las
  acotaciones entre corchetes quedan tal cual), con el idioma en español para que
  PowerPoint no las subraye; la versión SIN_NOTAS no tiene página de notas;
- una sección por diapositiva del guion («D14 · Mi pitch, con cronómetro…»), así
  en la vista normal se ve dónde empieza cada una y dónde está el respaldo;
- metadatos propios (título, autor, fechas, presentación 16:9, cantidad de
  diapositivas y videos) en vez de los de la plantilla de python-pptx, y una
  miniatura con la portada.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation  # noqa: F401  (lo usa verificar para releer)

from prueba_pptx import FONDO, NS_P, NS_P14, ocultar_controles, presentacion_16x9, reproducir_al_entrar

IDIOMA = "es-BO"
URI_SECCIONES = "{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _notas(slide, texto: str) -> None:
    tf = slide.notes_slide.notes_text_frame
    tf.text = texto
    for par in tf.paragraphs:
        for run in par.runs:
            run._r.get_or_add_rPr().set("lang", IDIOMA)


def _secciones(prs, grupos: list[tuple[str, list]]) -> None:
    """<p14:sectionLst> en presentation.xml: una sección por diapositiva del guion."""
    ns = {"p": NS_P}
    raiz = prs.part._element
    ids = [s.get("id") for s in etree._Element.xpath(raiz, "./p:sldIdLst/p:sldId", namespaces=ns)]
    lst = etree.Element(f"{{{NS_P14}}}sectionLst", nsmap={"p14": NS_P14})
    i = 0
    for nombre, slides in grupos:
        sec = etree.SubElement(lst, f"{{{NS_P14}}}section", name=nombre, id="{" + str(uuid.uuid4()).upper() + "}")
        sl = etree.SubElement(sec, f"{{{NS_P14}}}sldIdLst")
        for _ in slides:
            etree.SubElement(sl, f"{{{NS_P14}}}sldId", id=ids[i])
            i += 1
    if i != len(ids):
        raise RuntimeError(f"las secciones cubren {i} diapositivas y hay {len(ids)}")
    ext_lst = raiz.find(f"{{{NS_P}}}extLst")
    if ext_lst is None:
        ext_lst = etree.SubElement(raiz, f"{{{NS_P}}}extLst")  # va al final de p:presentation
    for e in ext_lst.findall(f"{{{NS_P}}}ext"):
        if e.get("uri") == URI_SECCIONES:
            ext_lst.remove(e)
    ext = etree.Element(f"{{{NS_P}}}ext", uri=URI_SECCIONES)
    ext.append(lst)
    ext_lst.insert(0, ext)


def _app_xml(diapos: int, notas: int, videos: int) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<TotalTime>0</TotalTime><Words>0</Words><Application>Microsoft Office PowerPoint</Application>"
        "<PresentationFormat>Panorámica</PresentationFormat><Paragraphs>0</Paragraphs>"
        f"<Slides>{diapos}</Slides><Notes>{notas}</Notes><HiddenSlides>0</HiddenSlides><MMClips>{videos}</MMClips>"
        "<ScaleCrop>false</ScaleCrop><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>"
        "<HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion></Properties>"
    ).encode("utf-8")


def _parte(prs, nombre: str):
    for parte in prs.part.package.iter_parts():
        if str(parte.partname) == nombre:
            return parte
    return None


def _metadatos(prs, meta: dict, diapos: int, notas: int, miniatura: Path | None) -> None:
    cp = prs.core_properties
    ahora = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    cp.title = meta.get("titulo", "")
    cp.subject = meta.get("subtitulo", "")
    cp.author = meta.get("autor", "")
    cp.last_modified_by = meta.get("autor", "")
    cp.keywords = meta.get("palabras", "")
    cp.comments = meta.get("comentario", "")
    cp.category = "Charla"
    cp.language = IDIOMA
    cp.revision = 1
    cp.created = ahora
    cp.modified = ahora
    app = _parte(prs, "/docProps/app.xml")
    if app is not None:
        app._blob = _app_xml(diapos, notas, diapos)
    mini = _parte(prs, "/docProps/thumbnail.jpeg")
    if mini is not None and miniatura and Path(miniatura).exists():
        im = Image.open(miniatura).convert("RGB")
        im.thumbnail((256, 144), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, "JPEG", quality=88)
        mini._blob = b.getvalue()
    # el tamaño quedó en 16:9: que no diga "screen4x3" (lo deja la plantilla)
    sz = prs.part._element.find(f"{{{NS_P}}}sldSz")
    if sz is not None and "type" in sz.attrib:
        del sz.attrib["type"]
    # idioma por defecto del texto (las notas): español
    for d in prs.part._element.iter(f"{{{NS_A}}}defRPr"):
        if d.get("lang"):
            d.set("lang", IDIOMA)
    for d in prs.part._element.iter(f"{{{NS_A}}}defPPr"):
        r = d.find(f"{{{NS_A}}}defRPr")
        if r is not None:
            r.set("lang", IDIOMA)


def construir(pasos, videos: list[Path], posters: list[Path], destino: Path, con_notas: bool,
              meta: dict, miniatura: Path | None = None) -> dict:
    """pasos: objetos deck.Paso en el orden del .pptx; videos y posters, uno por paso."""
    prs = presentacion_16x9()
    grupos: list[tuple[str, list]] = []
    for p, video, poster in zip(pasos, videos, posters):
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # en blanco
        relleno = slide.background.fill
        relleno.solid()
        relleno.fore_color.rgb = FONDO
        slide._element.cSld.set("name", p.etiqueta)
        movie = slide.shapes.add_movie(str(video), 0, 0, prs.slide_width, prs.slide_height,
                                       poster_frame_image=str(poster), mime_type="video/mp4")
        movie.name = p.etiqueta
        reproducir_al_entrar(movie)
        if con_notas:
            _notas(slide, p.notas_pptx)
        nombre = f"{p.diapo.id}: {p.diapo.titulo}"
        if p.diapo.seccion == "respaldo" and "respaldo" not in nombre.lower():
            nombre += " (respaldo)"
        if not grupos or grupos[-1][0] != nombre:
            grupos.append((nombre, []))
        grupos[-1][1].append(slide)
    ocultar_controles(prs)
    _secciones(prs, grupos)
    _metadatos(prs, meta, len(pasos), len(pasos) if con_notas else 0, miniatura)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.stem + ".guardando.pptx")
    prs.save(tmp)
    tmp.replace(destino)
    return {"archivo": str(destino), "diapositivas": len(pasos), "secciones": len(grupos),
            "notas": con_notas, "bytes": destino.stat().st_size}
