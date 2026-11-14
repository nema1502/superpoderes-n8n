"""La verificación del armado (armar.py verificar).

1. Cada mp4 final: receta (h264 High, 1920x1080, 30 cuadros/s, yuv420p, BT.709,
   índice adelante), duración contra el deck, sonido solo donde hay ding y el ding
   en su segundo, fronteras idénticas entre pasos de una diapositiva y la entrada
   desde la diapositiva anterior.
2. Los dos .pptx: python-pptx (una diapositiva y un video por paso, notas tal
   cual, XML de arranque, controles ocultos) y PowerPoint por COM en un proceso
   hijo (armar/verificar_pptx.ps1: si el usuario tiene PowerPoint abierto, no se
   lo cierra): cantidad de diapositivas, notas, PlayOnEntry, efecto automático,
   que no se rebobine, ShowMediaControls, duración de cada video, secciones y 3
   diapositivas exportadas a PNG. Con --show, además la presentación en una
   ventana chica.
3. El PDF: una página por diapositiva (más las de fuentes), y que cada página sea
   el último cuadro de su diapositiva (se pasan a PNG con el lector de Windows).
4. El HTML: un video por paso y los datos.
5. Los saltos «número + Enter» de las notas y los números de diapositiva que cita
   el guion, contra la numeración real del .pptx.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import deck as D
import videos as V

PS = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
AQUI = Path(__file__).resolve().parent


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean())
    return float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)


# ---------------------------------------------------------------- mp4
def revisar_mp4(ctx) -> dict:
    man_ruta = ctx.rutas.render / "final" / "manifiesto.json"
    man = json.loads(man_ruta.read_text(encoding="utf-8")) if man_ruta.exists() else {}
    filas, total_b, total_s = [], 0, 0.0
    ctx.decir("  mp4 finales:")
    for d in ctx.diapos:
        anterior_ultimo = None
        for p in d.pasos:
            f = ctx.rutas.final(p)
            fila = {"paso": p.etiqueta, "archivo": str(f)}
            if not f.exists():
                ctx.error(f"{p.etiqueta}: falta {f}")
                filas.append(fila)
                continue
            inf = V.sondear(f)
            total_b += inf.tamano
            total_s += inf.cuadros / D.FPS
            fila.update(cuadros=inf.cuadros, segundos=round(inf.cuadros / D.FPS, 3), bytes=inf.tamano,
                        formato=V.problemas_de_formato(inf))
            for prob in fila["formato"]:
                ctx.error(f"{p.etiqueta}: {prob}")
            m = man.get(p.id, {})
            fila["transicion"] = m.get("transicion")
            # la duración del deck es la del paso entero: en el paso 1, con su transición (como en Remotion)
            dur = inf.cuadros / D.FPS
            dif = dur - p.duracion
            if p.duracion and abs(dif) > 2.5 / D.FPS:
                ctx.aviso(f"{p.etiqueta}: el video dura {dur:.2f} s y el deck dice {p.duracion:.2f} s ({dif:+.2f} s)")
            # sonido
            if p.dings:
                if not inf.audio:
                    ctx.error(f"{p.etiqueta}: el deck dice ding y el video no tiene sonido")
                else:
                    if inf.audio["codec"] != "aac" or inf.audio["muestreo"] != V.MUESTREO:
                        ctx.error(f"{p.etiqueta}: audio {inf.audio} (se espera AAC a {V.MUESTREO} Hz)")
                    a = V.audio_de(f)
                    t = V.inicio_sonido(a)
                    esperado = p.dings[0]
                    fila["ding_s"] = t
                    if t is None or abs(t - esperado) > 0.03:
                        ctx.error(f"{p.etiqueta}: el ding empieza en {t} s y debía en {esperado:.2f} s")
                    pico = float(np.abs(a).max()) if len(a) else 0.0
                    fila["ding_pico_dbfs"] = round(20 * np.log10(pico), 1) if pico else None
            elif inf.audio:
                ctx.aviso(f"{p.etiqueta}: tiene sonido y el deck no dice ding")
            # fronteras
            primero = V.primer_yuv(f)
            if anterior_ultimo is not None:
                c = V.comparar_yuv(anterior_ultimo, primero)
                fila["frontera"] = c["veredicto"]
                if c["veredicto"] != "IDÉNTICOS":
                    (ctx.error if c["veredicto"] == "DISTINTOS" else ctx.aviso)(
                        f"{d.id}.{p.k - 1} -> {p.etiqueta}: frontera {c['veredicto']} (máx. {c['max']})")
            else:
                e = d.entrada
                if e.desde is None:
                    a_yuv = V.tinta_yuv()
                    origen = "tinta"
                else:
                    dd = ctx.deck.diapo(e.desde)
                    fa = ctx.rutas.final(dd.pasos[-1])
                    fa = fa if fa.exists() else ctx.rutas.paso(dd.pasos[-1])
                    a_yuv = V.ultimo_yuv(fa) if fa.exists() else None
                    origen = dd.pasos[-1].etiqueta
                if a_yuv is not None:
                    c = V.comparar_yuv(a_yuv, primero)
                    fila["entrada"] = f"desde {origen}: {c['veredicto']} (máx. {c['max']})"
                    if c["veredicto"] == "DISTINTOS":
                        ctx.aviso(f"{origen} -> {p.etiqueta}: el primer cuadro no es el último de {origen} "
                                  f"(corte seco al pasar de diapositiva)")
            anterior_ultimo = V.ultimo_yuv(f)
            filas.append(fila)
            extra = f" ding {fila['ding_s']:.3f} s" if fila.get("ding_s") is not None else ""
            ctx.decir(f"    {p.etiqueta:6s} {inf.cuadros:5d} cuadros {inf.cuadros / D.FPS:7.2f} s "
                      f"{inf.tamano / 1e6:6.2f} MB  {fila.get('frontera') or fila.get('entrada', '')}{extra}"
                      + ("  " + "; ".join(fila["formato"]) if fila["formato"] else ""))
    ctx.decir(f"    total: {len(filas)} videos, {total_s / 60:.1f} min, {total_b / 1e6:.1f} MB")
    return {"videos": filas, "bytes": total_b, "segundos": total_s}


# ---------------------------------------------------------------- pptx
def _xml_pptx(ctx, ruta: Path, con_notas: bool) -> dict:
    from lxml import etree
    from pptx import Presentation
    ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
          "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main"}
    prs = Presentation(str(ruta))
    pasos = ctx.pasos
    r = {"diapositivas": len(prs.slides), "problemas": []}
    if len(prs.slides) != len(pasos):
        r["problemas"].append(f"{len(prs.slides)} diapositivas y {len(pasos)} pasos")
    for i, (s, p) in enumerate(zip(prs.slides, pasos), start=1):
        el = s._element
        videos = etree._Element.xpath(el, ".//p:pic[.//p:videoFile or .//*[local-name()='videoFile']]", namespaces=ns)
        auto = etree._Element.xpath(el, './/p:timing//p:cTn[@nodeType="mainSeq"]//p:cmd[@cmd="playFrom(0.0)"]', namespaces=ns)
        if len(videos) != 1:
            r["problemas"].append(f"diapositiva {i}: {len(videos)} videos")
        if len(auto) != 1:
            r["problemas"].append(f"diapositiva {i}: sin el arranque automático de PowerPoint")
        if con_notas:
            texto = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
            if texto.replace("\r", "\n") != p.notas_pptx:
                r["problemas"].append(f"diapositiva {i} ({p.etiqueta}): las notas no son las del deck")
        elif s.has_notes_slide:
            r["problemas"].append(f"diapositiva {i}: tiene notas y es la versión sin notas")
    pres_props = [prt for prt in prs.part.package.iter_parts() if str(prt.partname) == "/ppt/presProps.xml"]
    if not pres_props or not re.search(rb'showMediaCtrls\b[^>]*\bval="0"', pres_props[0].blob):
        r["problemas"].append("presProps.xml no apaga los controles multimedia")
    secciones = etree._Element.xpath(prs.part._element, ".//p14:section", namespaces=ns)
    r["secciones"] = len(secciones)
    return r


def _com_pptx(ctx, ruta: Path, carpeta: Path, con_notas: bool) -> dict:
    n = len(ctx.pasos)
    exportar = sorted({1, (n + 1) // 2, n})
    cmd = PS + [str(AQUI / "verificar_pptx.ps1"), "-Pptx", str(ruta), "-Salida", str(carpeta),
                "-Exportar", ",".join(map(str, exportar))]
    if ctx.args.show and con_notas:
        cmd += ["-ProbarShow", "-ProbarHasta", str(min(n, 8))]
    informe = carpeta / "informe.json"
    if informe.exists():
        informe.unlink()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not informe.exists():
        return {"resultado": "SIN INFORME", "salida": (r.stdout or "")[-800:] + (r.stderr or "")[-800:]}
    return json.loads(informe.read_text(encoding="utf-8-sig"))


def revisar_pptx(ctx) -> dict:
    out = {}
    man_ruta = ctx.rutas.render / "final" / "manifiesto.json"
    man = json.loads(man_ruta.read_text(encoding="utf-8")) if man_ruta.exists() else {}
    for con_notas, sufijo in [(True, ""), (False, "_SIN_NOTAS")]:
        ruta = ctx.salida / f"{ctx.nombre}{sufijo}.pptx"
        if not ruta.exists():
            ctx.error(f"falta {ruta.name}")
            continue
        x = _xml_pptx(ctx, ruta, con_notas)
        for prob in x["problemas"]:
            ctx.error(f"{ruta.name}: {prob}")
        carpeta = ctx.rutas.revision / "verificacion" / ("pptx" + sufijo.lower())
        com = _com_pptx(ctx, ruta, carpeta, con_notas)
        out[ruta.name] = {"bytes": ruta.stat().st_size, "xml": x, "powerpoint": com}
        if com.get("resultado") != "OK":
            ctx.aviso(f"{ruta.name}: PowerPoint no respondió ({com.get('resultado')}: {com.get('error') or com.get('salida', '')[:300]})")
            continue
        problemas = []
        if com.get("reparada"):
            problemas.append("PowerPoint la abrió como reparada")
        if com.get("diapositivas") != len(ctx.pasos):
            problemas.append(f"PowerPoint cuenta {com.get('diapositivas')} diapositivas (se esperan {len(ctx.pasos)})")
        if com.get("mostrar_controles_multimedia") != 0:
            problemas.append(f"ShowMediaControls = {com.get('mostrar_controles_multimedia')} (se espera 0)")
        if len(com.get("secciones") or []) != len(ctx.diapos):
            problemas.append(f"{len(com.get('secciones') or [])} secciones (se esperan {len(ctx.diapos)})")
        detalle = com.get("diapositivas_detalle") or []
        if isinstance(detalle, dict):
            detalle = [detalle]
        for dd, p in zip(detalle, ctx.pasos):
            medios = dd.get("medios") or []
            if isinstance(medios, dict):
                medios = [medios]
            if len(medios) != 1:
                problemas.append(f"{p.etiqueta}: {len(medios)} videos")
                continue
            mm = medios[0]
            if mm.get("reproducir_al_entrar") != -1:
                problemas.append(f"{p.etiqueta}: PlayOnEntry = {mm.get('reproducir_al_entrar')}")
            efectos = dd.get("efectos_secuencia_principal") or []
            if isinstance(efectos, str):
                efectos = [efectos]
            if efectos != ["tipo 83, disparo 3"]:
                problemas.append(f"{p.etiqueta}: efectos {efectos} (se espera reproducir después de la anterior)")
            for clave, val in [("rebobinar_al_terminar", 0), ("repetir", 0), ("ocultar_si_no_reproduce", 0),
                               ("vinculado", False), ("izq", 0), ("arriba", 0), ("ancho", 960), ("alto", 540)]:
                if mm.get(clave) != val:
                    problemas.append(f"{p.etiqueta}: {clave} = {mm.get(clave)} (se espera {val})")
            seg = (man.get(p.id) or {}).get("segundos")
            if seg and abs(mm.get("duracion_ms", 0) / 1000 - seg) > 0.08:
                problemas.append(f"{p.etiqueta}: PowerPoint dice {mm.get('duracion_ms')} ms y el video dura {seg:.3f} s")
            notas = (dd.get("notas") or "").replace("\r\n", "\n").replace("\r", "\n")
            esperado = p.notas_pptx if con_notas else ""
            if notas.strip() != esperado.strip():
                problemas.append(f"{p.etiqueta}: las notas que lee PowerPoint no son las del deck")
        for prob in problemas:
            ctx.error(f"{ruta.name}: {prob}")
        pngs = [dd.get("png") for dd in detalle if dd.get("png")]
        show = ""
        if com.get("show"):
            show = f"; presentación en ventana: {len(com['show']) - 1} diapositivas medidas"
        ctx.decir(f"  {ruta.name}: PowerPoint {com.get('version_powerpoint')}, {com.get('diapositivas')} diapositivas, "
                  f"{len(com.get('secciones') or [])} secciones, abrir {com.get('abrir_seg')} s, "
                  f"{'sin problemas' if not problemas else f'{len(problemas)} problemas'}; PNG: "
                  + ", ".join(Path(x).name for x in pngs) + show)
        out[ruta.name]["png"] = pngs
    return out


# ---------------------------------------------------------------- pdf
def revisar_pdf(ctx) -> dict:
    ruta = ctx.salida / f"{ctx.nombre}.pdf"
    if not ruta.exists():
        ctx.error(f"falta {ruta.name}")
        return {}
    res_ruta = ctx.rutas.trabajo / "pdf" / "resultado.json"
    res = json.loads(res_ruta.read_text(encoding="utf-8")) if res_ruta.exists() else {}
    carpeta = ctx.rutas.revision / "verificacion" / "pdf"
    for viejo in carpeta.glob("pagina_*.png"):
        viejo.unlink()
    r = subprocess.run(PS + [str(AQUI / "pdf_a_png.ps1"), str(ruta), str(carpeta), "1536"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Paginas:\s*(\d+)", r.stdout or "")
    if not m:
        ctx.aviso(f"no se pudo pasar el PDF a PNG: {(r.stderr or r.stdout)[-300:]}")
        return {"bytes": ruta.stat().st_size}
    paginas = int(m.group(1))
    esperadas = len(ctx.diapos) + int(res.get("paginas_fuentes", 0))
    if paginas != esperadas:
        ctx.error(f"{ruta.name}: {paginas} páginas (se esperan {len(ctx.diapos)} diapositivas + "
                  f"{res.get('paginas_fuentes', 0)} de fuentes)")
    coinciden = []
    for i, d in enumerate(ctx.diapos, start=1):
        png = carpeta / f"pagina_{i:02d}.png"
        if not png.exists():
            continue
        pag = Image.open(png).convert("RGB")
        ref = Image.open(ctx.rutas.ultimo(d.pasos[-1])).convert("RGB").resize(pag.size, Image.LANCZOS)
        ps = _psnr(np.asarray(pag), np.asarray(ref))
        coinciden.append((d.id, round(ps, 1)))
        if ps < 30:
            ctx.error(f"{ruta.name}: la página {i} no es el último cuadro de {d.id} (PSNR {ps:.1f} dB)")
    peor = min((x[1] for x in coinciden), default=None)
    ctx.decir(f"  {ruta.name}: {paginas} páginas ({len(ctx.diapos)} diapositivas + {res.get('paginas_fuentes', 0)} "
              f"de fuentes), {ruta.stat().st_size / 1e6:.1f} MB; cada página contra su cuadro: peor PSNR {peor} dB; "
              f"PNG en {carpeta}")
    return {"bytes": ruta.stat().st_size, "paginas": paginas, "esperadas": esperadas, "psnr": coinciden}


# ---------------------------------------------------------------- html
def revisar_html(ctx) -> dict:
    ruta = ctx.salida / f"{ctx.nombre}.html"
    if not ruta.exists():
        ctx.error(f"falta {ruta.name}")
        return {}
    marca = b'<script type="application/octet-stream" id="v'
    n, resto = 0, b""
    with open(ruta, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            bloque = resto + b
            n += bloque.count(marca)
            resto = bloque[-(len(marca) - 1):]
            n -= resto.count(marca)
    texto_inicio = ruta.read_bytes()[:4_000_000].decode("utf-8", "replace")
    m = re.search(r'<script id="datos" type="application/json">(.*?)</script>', texto_inicio, re.S)
    pasos = len(json.loads(m.group(1))["pasos"]) if m else None
    if n != len(ctx.pasos) or pasos != len(ctx.pasos):
        ctx.error(f"{ruta.name}: {n} videos y {pasos} pasos en los datos (se esperan {len(ctx.pasos)})")
    ctx.decir(f"  {ruta.name}: {n} videos adentro, {ruta.stat().st_size / 1e6:.1f} MB")
    return {"bytes": ruta.stat().st_size, "videos": n, "pasos": pasos}


# ---------------------------------------------------------------- saltos
def revisar_saltos(ctx) -> dict:
    deck = ctx.deck
    saltos = []
    for p in deck.pasos:
        for m in re.finditer(r"\b(\d{1,2})\s*\+\s*Enter", p.notas):
            n = int(m.group(1))
            destino = deck.paso_numero(n)
            saltos.append({"en": p.etiqueta, "numero": n, "va_a": destino.etiqueta if destino else None})
            if destino is None:
                ctx.error(f"{p.etiqueta}: la nota dice {n} + Enter y el .pptx tiene {len(deck.pasos)} diapositivas")
    if saltos:
        ctx.decir("  saltos en las notas: " + "; ".join(f"{s['en']}: {s['numero']} + Enter -> {s['va_a']}" for s in saltos))
    citas = []
    guion = D.RAIZ / "contenido" / "guion.md"
    if Path(deck.ruta).resolve() == D.DECK.resolve() and guion.exists():
        texto = guion.read_text(encoding="utf-8")
        for m in re.finditer(r"\b([DA]\d{1,2})(?:\.(\d))?\s*\((?:diapositiva\s+)?(\d{1,2})\)", texto):
            ident, k, n = m.group(1), int(m.group(2) or 1), int(m.group(3))
            try:
                real = deck.diapo(ident).pasos[k - 1].numero
            except (KeyError, IndexError):
                continue
            citas.append((f"{ident}.{k}", n, real))
            if real != n:
                ctx.error(f"guion: «{m.group(0)}» pero {ident}.{k} es la diapositiva {real} del .pptx")
        for m in re.finditer(r"\|\s*([DA]\d{1,2})\s*\|\s*(\d{1,2})(?:-(\d{1,2}))?\s*\|", texto):
            ident, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            try:
                dd = deck.diapo(ident)
            except KeyError:
                continue
            real = (dd.pasos[0].numero, dd.pasos[-1].numero)
            citas.append((ident, f"{a}-{b}", f"{real[0]}-{real[1]}"))
            if real != (a, b):
                ctx.error(f"guion, tabla de diapositivas: {ident} {a}-{b}, y en el .pptx es {real[0]}-{real[1]}")
        mal = sum(1 for c in citas if str(c[1]) != str(c[2]))
        ctx.decir(f"  números de diapositiva citados en el guion: {len(citas)}, {mal} no coinciden")
    return {"saltos": saltos, "citas_guion": citas}


def todo(ctx) -> dict:
    informe = {}
    a0, e0 = len(ctx.avisos), len(ctx.errores)   # lo de las etapas anteriores (en «todo») no es de acá
    for nombre, f in [("mp4", revisar_mp4), ("pptx", revisar_pptx), ("pdf", revisar_pdf), ("html", revisar_html),
                      ("saltos", revisar_saltos)]:
        ctx.decir(f"  [{nombre}]")
        try:
            informe[nombre] = f(ctx)
        except Exception as e:  # noqa: BLE001
            ctx.error(f"{nombre}: {type(e).__name__}: {e}")
    informe["avisos"] = ctx.avisos[a0:]
    informe["errores"] = ctx.errores[e0:]
    ctx.decir(f"  verificación: {len(informe['errores'])} errores, {len(informe['avisos'])} avisos")
    return informe
