"""Armado de la charla: de los videos de cada paso a los entregables.

Uso, desde la raíz del proyecto, con el Python del entorno de la charla (Manim, python-pptx):
    <python del entorno> armar/armar.py <subcomando> [opciones]

Los entregables se llaman como dice "archivo" en contenido/deck.json (o NOMBRE, abajo).

Subcomandos (en el orden en que los corre `todo`):
    render         renderiza los pasos: node remotion/render.mjs <ID...> o manim/render_diapo.py <ID>
                   según el motor de cada diapositiva (si el comando todavía no existe, avisa y sigue)
    transiciones   la entrada de cada diapositiva (fundido o puertas) -> render/transiciones/<ID>.mp4,
                   con node remotion/transicion.mjs si existe y, si no, con el respaldo (numpy + ffmpeg)
    final          render/final/<ID>/<ID>_<k>.mp4: el paso 1 con su transición delante (pegada sin
                   recodificar el paso) y el ding mezclado donde dice el deck; pósters y últimos cuadros
    pptx           salida/<archivo>.pptx (con notas) y _SIN_NOTAS.pptx
    pdf            salida/<archivo>.pdf (último cuadro de cada diapositiva + fuentes)
    html           salida/<archivo>.html (un solo archivo, sin internet)
    vista-previa   salida/<archivo>_vista_previa.mp4 (todo seguido, 1,5 s de pausa)
    verificar      PowerPoint por COM, cada mp4 (formato, duración, ding, fronteras), el PDF y el HTML
    todo           todo lo anterior, con un renglón de log por etapa
    ding           regenera armar/assets/ding.wav y lo mide

Opciones:
    --solo D14,D19         solo esas diapositivas (los entregables salen con sufijo _solo-D14-D19)
    --seccion principal|respaldo|todas   (por defecto todas; otra cosa agrega _principal o _respaldo)
    --salida DIR           carpeta de los entregables (salida/)
    --deck JSON            el deck (contenido/deck.json)
    --render DIR           raíz de los intermedios (render/). Con otra raíz, Remotion escribe ahí
                           (render.mjs --salida) y no se llama a Manim ni a transicion.mjs.
    --compacto auto|si|no  pptx/html: recodificar con la receta compacta (auto: si el total pasa de 250 MB)
    --codificador auto|nvenc|x264   vista previa
    --simular              render y transiciones: muestra los comandos sin correrlos
    --show                 verificar: además corre la presentación en una ventana chica y mide el video

Todo queda anotado en render/revision/armado.log. Ver docs/armado.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import deck as D  # noqa: E402
import videos as V  # noqa: E402

RAIZ = D.RAIZ
# El mismo Python que corre el armado (el del entorno con Manim): así no hace falta un .venv en la raíz.
PY = Path(sys.executable)
NOMBRE = "Charla_n8n_SerpApi_IA"
UMBRAL_COMPACTO = 250e6
DING = AQUI / "assets" / "ding.wav"
PAUSA_VISTA_PREVIA = 1.5
CMD_REMOTION = ["node", "remotion/render.mjs"]
CMD_TRANSICION = ["node", "remotion/transicion.mjs"]
CMD_MANIM = [str(PY), "manim/render_diapo.py"]
ETAPAS = ["render", "transiciones", "final", "pptx", "pdf", "html", "vista-previa", "verificar"]


# ---------------------------------------------------------------- contexto
@dataclass
class Plan:
    diapo: D.Diapo
    hacer: bool
    motivo: str
    a: bytes | None = None
    b: bytes | None = None
    veredicto: str = ""
    desde_ok: bool = True


@dataclass
class Ctx:
    args: argparse.Namespace
    deck: D.Deck
    rutas: D.Rutas
    diapos: list
    salida: Path
    nombre: str
    log: Path
    planes: dict = field(default_factory=dict)
    avisos: list = field(default_factory=list)
    errores: list = field(default_factory=list)

    @property
    def pasos(self):
        return [p for d in self.diapos for p in d.pasos]

    @property
    def render_propio(self) -> bool:
        return self.rutas.render.resolve() == (RAIZ / "render").resolve()

    def decir(self, msg: str = "") -> None:
        print(msg, flush=True)
        if self.args.simular:  # una simulación no deja rastro en render/
            return
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def aviso(self, msg: str) -> None:
        self.avisos.append(msg)
        self.decir(f"  AVISO: {msg}")

    def error(self, msg: str) -> None:
        self.errores.append(msg)
        self.decir(f"  ERROR: {msg}")


def meta(ctx: Ctx) -> dict:
    d = ctx.deck.datos
    # Las propiedades del documento de un .pptx admiten 255 caracteres como mucho (python-pptx falla si
    # se pasan). Con un evento de nombre largo, la segunda oración se deja afuera y, si igual no entra,
    # se corta en el último punto que entre.
    comentario = f"Charla para {d.get('evento', 'el evento')}."
    explica = " Cada diapositiva es un paso: un video que arranca solo y termina quieto en su último cuadro."
    if len(comentario + explica) <= 255:
        comentario += explica
    elif len(comentario) > 255:
        corte = comentario.rfind(". ", 0, 254)
        comentario = comentario[: corte + 1] if corte > 0 else comentario[:255]
    return {
        "titulo": d.get("titulo", "")[:255],
        "subtitulo": d.get("subtitulo", "")[:255],
        "autor": d.get("orador", "")[:255],
        "palabras": d.get("palabras_clave", "n8n, SerpApi, IA, automatización")[:255],
        "comentario": comentario,
    }


def mb(n: float) -> str:
    return f"{n / 1e6:.1f} MB"


def correr(ctx: Ctx, cmd: list[str], env_extra: dict | None = None) -> int:
    """Corre un comando desde la raíz del proyecto, con su salida a la consola y al log."""
    texto = " ".join(cmd)
    if ctx.args.simular:
        ctx.decir(f"  (simulado) {texto}")
        return 0
    ctx.decir(f"  $ {texto}")
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", **(env_extra or {})}
    try:
        p = subprocess.Popen(cmd, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    except FileNotFoundError as e:
        ctx.aviso(f"no se pudo correr {cmd[0]}: {e}")
        return 127
    for linea in iter(p.stdout.readline, b""):
        ctx.decir("    " + linea.decode("utf-8", "replace").rstrip())
    return p.wait()


# ---------------------------------------------------------------- render
def etapa_render(ctx: Ctx) -> None:
    remotion = [d for d in ctx.diapos if d.motor == "remotion"]
    manim = [d for d in ctx.diapos if d.motor == "manim"]
    if not ctx.render_propio and manim:
        ctx.aviso(f"con --render {ctx.rutas.render} no se llama a Manim (render_diapo.py escribe en render/): "
                  + ", ".join(d.id for d in manim))
        manim = []
    otros = [d for d in ctx.diapos if d.motor not in ("remotion", "manim")]
    for d in otros:
        ctx.aviso(f"{d.id}: motor desconocido {d.motor!r}: no se renderiza")
    t0 = time.time()
    if remotion:
        ids = [d.id for d in remotion]
        script = RAIZ / "remotion" / "render.mjs"
        registro = RAIZ / "remotion" / "src" / "diapos" / "index.ts"
        if not script.exists():
            ctx.aviso("no existe remotion/render.mjs: no se renderiza " + ", ".join(ids))
        elif not registro.exists() and not ctx.args.forzar:
            ctx.aviso("todavía no existe remotion/src/diapos/index.ts (el registro de diapositivas de Remotion): "
                      "no se renderiza " + ", ".join(ids) + " (--forzar para intentarlo igual)")
        else:
            salida = [] if ctx.render_propio else ["--salida", str(ctx.rutas.render.resolve())]
            rc = correr(ctx, CMD_REMOTION + salida + ids)
            if rc:
                ctx.aviso(f"remotion/render.mjs terminó con código {rc}")
    if manim:
        script = RAIZ / "manim" / "render_diapo.py"
        if not script.exists():
            ctx.aviso("no existe manim/render_diapo.py: no se renderiza " + ", ".join(d.id for d in manim))
        else:
            for d in manim:
                escenas = sorted((RAIZ / "manim" / "escenas").glob(f"{d.id.lower()}_*.py"))
                if not escenas and not ctx.args.forzar:
                    ctx.aviso(f"{d.id}: no hay manim/escenas/{d.id.lower()}_*.py: no se renderiza")
                    continue
                rc = correr(ctx, CMD_MANIM + [d.id])
                if rc:
                    ctx.aviso(f"manim/render_diapo.py {d.id} terminó con código {rc}")
    if ctx.args.simular:
        return
    nuevos, viejos, faltan = [], [], []
    for p in ctx.pasos:
        f = ctx.rutas.paso(p)
        if not f.exists():
            faltan.append(p.etiqueta)
        elif f.stat().st_mtime >= t0 - 1:
            nuevos.append(p.etiqueta)
        else:
            viejos.append(p.etiqueta)
    ctx.decir(f"  pasos: {len(nuevos)} nuevos, {len(viejos)} de antes, {len(faltan)} faltan"
              + (f" ({', '.join(faltan[:12])}{'…' if len(faltan) > 12 else ''})" if faltan else ""))


# ---------------------------------------------------------------- transiciones
def planificar(ctx: Ctx, d: D.Diapo) -> Plan:
    if d.id in ctx.planes:
        return ctx.planes[d.id]
    e = d.entrada
    paso1 = ctx.rutas.paso(d.pasos[0])
    if not paso1.exists():
        plan = Plan(d, False, "falta el video del paso 1", desde_ok=False)
        ctx.planes[d.id] = plan
        return plan
    b = V.primer_yuv(paso1)
    desde_ok = True
    if e.desde is None:
        a = V.tinta_yuv()
    else:
        dd = ctx.deck.diapo(e.desde)
        ult = ctx.rutas.paso(dd.pasos[-1])
        if ult.exists():
            a = V.ultimo_yuv(ult)
        else:
            a, desde_ok = V.tinta_yuv(), False
            ctx.aviso(f"{d.id}: falta {dd.pasos[-1].etiqueta} (render/pasos): la entrada sale desde tinta")
    comp = V.comparar_yuv(a, b)
    ver = comp["veredicto"]
    desde = e.desde or "tinta"
    if e.tipo == "corte":
        plan = Plan(d, False, f"corte (deck): sin transición; frontera con {desde}: {ver}", a, b, ver, desde_ok)
    elif e.tipo == "continuo":
        plan = Plan(d, False, f"continuo (deck): sin transición; frontera con {desde}: {ver}", a, b, ver, desde_ok)
        if ver == "DISTINTOS":
            ctx.aviso(f"{d.id}: entrada «continuo» pero su primer cuadro no es el último de {desde} "
                      f"(máx. {comp['max']}): ¿render viejo de {desde}? Queda un corte seco")
    elif e.explicita:
        plan = Plan(d, True, f"{e.tipo} {e.segundos:.2f} s desde {desde} (deck)", a, b, ver, desde_ok)
        if ver != "DISTINTOS":
            ctx.aviso(f"{d.id}: el deck pide {e.tipo}, pero el paso 1 ya arranca en el último cuadro de {desde} "
                      f"({ver}): la transición no cambia nada y suma {e.segundos:.2f} s")
    elif ver != "DISTINTOS":
        donde = "en tinta" if e.desde is None else f"en el último cuadro de {desde}"
        plan = Plan(d, False, f"continua: el paso 1 ya arranca {donde} ({ver})", a, b, ver, desde_ok)
    else:
        plan = Plan(d, True, f"{e.tipo} {e.segundos:.2f} s desde {desde} (sin campo «entrada»: {e.origen})",
                    a, b, ver, desde_ok)
    ctx.planes[d.id] = plan
    return plan


def generar_respaldo(ctx: Ctx, d: D.Diapo, plan: Plan) -> Path:
    import transiciones as T
    e = d.entrada
    cuadros = T.generar(e.tipo, plan.a, plan.b, e.cuadros)
    destino = ctx.rutas.transicion(d)
    V.codificar_yuv(cuadros, destino)
    return destino


def etapa_transiciones(ctx: Ctx) -> None:
    planes = [planificar(ctx, d) for d in ctx.diapos]
    hacer = [p for p in planes if p.hacer]
    for p in planes:
        ctx.decir(f"  {p.diapo.id:4s} {'->' if p.hacer else '  '} {p.motivo}")
    carpeta = ctx.rutas.transiciones
    carpeta.mkdir(parents=True, exist_ok=True)
    lista = []
    for p in hacer:
        e = p.diapo.entrada
        desde_png = V.yuv_a_png(p.a, carpeta / f"{p.diapo.id}_desde.png")
        hacia_png = V.yuv_a_png(p.b, carpeta / f"{p.diapo.id}_hacia.png")
        lista.append({"id": p.diapo.id, "tipo": e.tipo, "segundos": e.segundos, "cuadros": e.cuadros + 1,
                      "desde": e.desde, "desde_png": str(desde_png), "hacia_png": str(hacia_png),
                      "salida": str(ctx.rutas.transicion(p.diapo)),
                      "nota": "cuadro 0 = desde_png, último cuadro = hacia_png (se solapan como los pasos)"})
    plan_json = carpeta / "plan.json"
    plan_json.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    if not hacer:
        ctx.decir("  ninguna diapositiva necesita transición")
        return
    t0 = time.time()
    hechas = set()
    script = RAIZ / "remotion" / "transicion.mjs"
    if script.exists() and ctx.render_propio:
        # transicion.mjs hace una transición por llamada (--de, --a, --tipo, --salida): se le pasan los
        # cortes sin pérdida de render/cuadros/ (el último de «desde» y el primero de esta) y, si faltan,
        # los cuadros decodificados del plan. Corregido el 13-nov-2026: antes se le pasaban los ids y
        # salía siempre el respaldo.
        cuadros = ctx.rutas.render / "cuadros"
        for p, item in zip(hacer, lista):
            e = p.diapo.entrada
            de = Path(item["desde_png"])
            if e.desde:
                prev = next((x for x in ctx.deck.diapos if x.id == e.desde), None)
                sin_perdida = cuadros / f"{e.desde}_{len(prev.pasos)}.png" if prev else None
                if sin_perdida and sin_perdida.exists():
                    de = sin_perdida
            a = cuadros / f"{p.diapo.id}_0.png"
            if not a.exists():
                a = Path(item["hacia_png"])
            rc = correr(ctx, CMD_TRANSICION + ["--de", str(de), "--a", str(a), "--tipo", e.tipo,
                                               "--salida", item["salida"], "--duracion", f"{e.segundos:.3f}"])
            if rc:
                ctx.aviso(f"remotion/transicion.mjs {p.diapo.id} terminó con código {rc}: sale con el respaldo")
        if not ctx.args.simular:
            for p in hacer:
                f = ctx.rutas.transicion(p.diapo)
                if f.exists() and f.stat().st_mtime >= t0 - 1:
                    hechas.add(p.diapo.id)
    elif not script.exists():
        ctx.decir("  no existe remotion/transicion.mjs: van con el respaldo (numpy + ffmpeg)")
    if ctx.args.simular:
        return
    for p in hacer:
        if p.diapo.id in hechas:
            origen = "remotion"
        else:
            generar_respaldo(ctx, p.diapo, p)
            origen = "respaldo"
        f = ctx.rutas.transicion(p.diapo)
        fr = V.todos_yuv(f)
        c0 = V.comparar_yuv(fr[0], p.a)["veredicto"]
        c1 = V.comparar_yuv(fr[-1], p.b)["veredicto"]
        ctx.decir(f"  {p.diapo.id}: {f.name} ({origen}), {len(fr)} cuadros, {mb(f.stat().st_size)}; "
                  f"primer cuadro vs. último de {p.diapo.entrada.desde or 'tinta'}: {c0}; último vs. paso 1: {c1}")


# ---------------------------------------------------------------- final
def ding_listo(ctx: Ctx):
    if not DING.exists():
        import ding
        ctx.decir("  no estaba armar/assets/ding.wav: se genera")
        ding.generar(DING, verbose=False)
    return V.leer_wav(DING)


def recodificar_juntos(seg: Path, paso: Path, destino: Path) -> None:
    """Respaldo si el SPS/PPS no coincide: decodifica y codifica todo junto con la receta."""
    n = V.sondear(seg).cuadros + V.sondear(paso).cuadros
    V.ejecutar(["ffmpeg", "-v", "error", "-y", "-i", seg, "-i", paso, "-filter_complex",
                "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-an", "-map_metadata", "-1",
                "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-qp", str(V.QP_FRONTERA),
                "-pix_fmt", "yuv420p", *V.ETIQUETAS, "-force_key_frames", f"expr:eq(n,{n - 1})",
                "-movflags", "+faststart", destino])


def etapa_final(ctx: Ctx) -> None:
    trabajo = ctx.rutas.trabajo / "final"
    trabajo.mkdir(parents=True, exist_ok=True)
    manifiesto_ruta = ctx.rutas.render / "final" / "manifiesto.json"
    manifiesto = {}
    if manifiesto_ruta.exists():
        manifiesto = json.loads(manifiesto_ruta.read_text(encoding="utf-8"))
    ding = None
    for d in ctx.diapos:
        plan = planificar(ctx, d)
        for p in d.pasos:
            src, dst = ctx.rutas.paso(p), ctx.rutas.final(p)
            if not src.exists():
                ctx.error(f"{p.etiqueta}: falta {src.relative_to(ctx.rutas.render)}")
                continue
            prefijo, modo, transicion = 0, "copia", None
            base = src
            if p.k == 1 and plan.hacer:
                t = ctx.rutas.transicion(d)
                if not t.exists():
                    ctx.aviso(f"{d.id}: falta {t.name} (correr «transiciones»): se arma con el respaldo")
                    generar_respaldo(ctx, d, plan)
                fr = V.todos_yuv(t)
                if fr and V.comparar_yuv(fr[0], plan.a)["veredicto"] != "DISTINTOS":
                    fr = fr[1:]       # va el último cuadro de la anterior tal cual, no su copia
                if fr and V.comparar_yuv(fr[-1], plan.b)["veredicto"] != "DISTINTOS":
                    fr = fr[:-1]      # el primer cuadro del paso ya es ese
                seg = [plan.a] + fr
                seg_mp4 = trabajo / f"{p.id}_entrada.mp4"
                V.codificar_yuv(seg, seg_mp4, claves=[0])
                base = trabajo / f"{p.id}_video.mp4"
                try:
                    V.pegar([seg_mp4, src], base)
                    modo = "transición pegada"
                except V.ErrorVideo as e:
                    ctx.aviso(f"{p.etiqueta}: {e}: se recodifica todo junto (la frontera con "
                              f"{d.id}.2 queda igual a la vista, no idéntica)")
                    recodificar_juntos(seg_mp4, src, base)
                    modo = "transición recodificada"
                prefijo = len(seg)
                transicion = {"tipo": d.entrada.tipo, "cuadros": prefijo, "segundos": round(prefijo / D.FPS, 3)}
            # sonido propio del paso (hoy ninguno: la receta los saca mudos); el pegado copia solo
            # el video, así que si hay, se vuelve a poner corrido lo que dura la transición
            propio = V.audio_de(src) if V.sondear(src).audio else None
            if propio is not None and prefijo:
                propio = np.vstack([np.zeros((int(round(prefijo / D.FPS * V.MUESTREO)), 2), np.float32), propio])
            if p.dings or (propio is not None and base != src):
                # "ding:t" cuenta desde que empieza el paso entero (con su transición, si la tiene):
                # la duracion_animacion_s del paso 1 incluye la entrada, como en remotion/lib/deck.mjs.
                ding = ding if ding is not None or not p.dings else ding_listo(ctx)
                inf = V.sondear(base)
                eventos = [(t, ding) for t in p.dings]
                audio = V.pista(inf.cuadros / D.FPS, eventos, base=propio)
                V.poner_audio(base, audio, dst)
                if p.dings:
                    modo += " + ding"
            elif base == src:
                V.copiar(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(base, dst)
            V.cuadro_png(dst, ctx.rutas.primero(p), "primero")
            V.cuadro_png(dst, ctx.rutas.ultimo(p), "ultimo")
            inf = V.sondear(dst)
            manifiesto[p.id] = {
                "etiqueta": p.etiqueta, "numero": p.numero, "archivo": str(dst), "cuadros": inf.cuadros,
                "segundos": round(inf.cuadros / D.FPS, 3), "bytes": inf.tamano, "modo": modo,
                "transicion": transicion, "dings_s": [round(t, 3) for t in p.dings],
                "paso_segundos": round(V.sondear(src).cuadros / D.FPS, 3), "deck_segundos": p.duracion,
            }
            ctx.decir(f"  {p.etiqueta:6s} {modo:28s} {inf.cuadros:5d} cuadros {inf.cuadros / D.FPS:7.2f} s "
                      f"{mb(inf.tamano):>9s}" + (f"  ding a {', '.join(f'{x:.2f}' for x in manifiesto[p.id]['dings_s'])} s"
                                                 if p.dings else ""))
    manifiesto_ruta.parent.mkdir(parents=True, exist_ok=True)
    manifiesto_ruta.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- pptx / html: qué videos van
def videos_de_entrega(ctx: Ctx) -> tuple[list[Path], list[Path], bool]:
    """Los videos (y sus pósters) que van al .pptx y al HTML: los finales o, si el
    total pasa de 250 MB (o --compacto si), los recodificados con la receta compacta."""
    faltan = [p.etiqueta for p in ctx.pasos if not ctx.rutas.final(p).exists()]
    if faltan:
        raise SystemExit(f"faltan videos finales ({', '.join(faltan[:10])}…): correr «final» antes")
    finales = [ctx.rutas.final(p) for p in ctx.pasos]
    total = sum(f.stat().st_size for f in finales)
    modo = ctx.args.compacto
    compacto = modo == "si" or (modo == "auto" and total > UMBRAL_COMPACTO)
    ctx.decir(f"  videos finales: {len(finales)}, {mb(total)}"
              + (f" -> receta compacta (umbral {mb(UMBRAL_COMPACTO)})" if compacto else ""))
    if not compacto:
        return finales, [ctx.rutas.primero(p) for p in ctx.pasos], False
    videos, posters = [], []
    for p, f in zip(ctx.pasos, finales):
        c = ctx.rutas.compacto(p)
        if not c.exists() or c.stat().st_mtime < f.stat().st_mtime:
            V.recodificar(f, c, compacto=True)
        poster = ctx.rutas.render / "cuadros" / "primero_compacto" / f"{p.id}.png"
        if not poster.exists() or poster.stat().st_mtime < c.stat().st_mtime:
            V.cuadro_png(c, poster, "primero")
        videos.append(c)
        posters.append(poster)
    total_c = sum(v.stat().st_size for v in videos)
    ctx.decir(f"  receta compacta: {mb(total_c)} ({100 * total_c / total:.0f} % del original)")
    return videos, posters, True


def etapa_pptx(ctx: Ctx) -> None:
    import pptx_armar
    videos, posters, _ = videos_de_entrega(ctx)
    m = meta(ctx)
    mini = ctx.rutas.ultimo(ctx.pasos[0])
    for con_notas, sufijo in [(True, ""), (False, "_SIN_NOTAS")]:
        destino = ctx.salida / f"{ctx.nombre}{sufijo}.pptx"
        t = time.time()
        try:
            r = pptx_armar.construir(ctx.pasos, videos, posters, destino, con_notas, m, mini)
        except PermissionError:
            raise SystemExit(f"no se pudo escribir {destino}: ¿está abierto en PowerPoint? Cerralo y repetí.")
        ctx.decir(f"  {destino.name}: {r['diapositivas']} diapositivas, {r['secciones']} secciones, "
                  f"{mb(r['bytes'])}, {time.time() - t:.1f} s")


def etapa_pdf(ctx: Ctx) -> None:
    import pdf_armar
    paginas = []
    for d in ctx.diapos:
        u = ctx.rutas.ultimo(d.pasos[-1])
        if not u.exists():
            raise SystemExit(f"falta {u} (correr «final» antes)")
        paginas.append((d.id, u))
    destino = ctx.salida / f"{ctx.nombre}.pdf"
    t = time.time()
    r = pdf_armar.construir(paginas, ctx.deck.datos.get("fuentes", []), destino, ctx.rutas.trabajo / "pdf",
                            meta(ctx), icono_credito="Íconos: Font Awesome (CC BY 4.0)")
    ctx.decir(f"  {destino.name}: {r['paginas']} páginas ({r['paginas_diapositivas']} diapositivas + "
              f"{r['paginas_fuentes']} de fuentes), {mb(r['bytes'])}, {r['motor']}, {time.time() - t:.1f} s")
    if r["caracteres_faltantes"]:
        ctx.aviso("caracteres que la fuente no tiene: " + ", ".join(r["caracteres_faltantes"]))
    (ctx.rutas.trabajo / "pdf" / "resultado.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


def plan_de_tiempos(ctx: Ctx) -> dict:
    """Segundo del plan en que empieza cada paso del camino principal (video + habla de los anteriores)."""
    t, plan = 0.0, {}
    for p in ctx.deck.pasos:
        if p.diapo.seccion != "principal":
            continue
        plan[p.id] = round(t, 1)
        t += p.duracion + float(p.datos.get("segundos_habla") or 0)
    return plan


def etapa_html(ctx: Ctx) -> None:
    import html_armar
    videos, _, _ = videos_de_entrega(ctx)
    ultimos = [ctx.rutas.ultimo(p) for p in ctx.pasos]
    destino = ctx.salida / f"{ctx.nombre}.html"
    t = time.time()
    r = html_armar.construir(ctx.pasos, videos, ultimos, destino, meta(ctx), plan_de_tiempos(ctx))
    ctx.decir(f"  {destino.name}: {r['pasos']} pasos, {mb(r['bytes'])} (videos {mb(r['bytes_video'])}), "
              f"{time.time() - t:.1f} s")


def etapa_vista_previa(ctx: Ctx) -> None:
    import vista_previa
    finales = [ctx.rutas.final(p) for p in ctx.pasos]
    faltan = [f for f in finales if not f.exists()]
    if faltan:
        raise SystemExit(f"faltan videos finales ({faltan[0].name}…): correr «final» antes")
    destino = ctx.salida / f"{ctx.nombre}_vista_previa.mp4"
    r = vista_previa.construir(finales, destino, ctx.rutas.trabajo / "vista_previa", PAUSA_VISTA_PREVIA,
                               ctx.args.codificador)
    ctx.decir(f"  {destino.name}: {r['pasos']} pasos, {r['duracion_s']:.1f} s ({r['cuadros']} cuadros, se "
              f"esperaban {r['cuadros_esperados']}), {r['con_audio']} con sonido, {r['codificador']} en "
              f"{r['codificar_s']} s, {mb(r['bytes'])}")


# ---------------------------------------------------------------- verificar
def etapa_verificar(ctx: Ctx) -> None:
    import verificar
    informe = verificar.todo(ctx)
    destino = ctx.rutas.revision / "verificacion" / f"{ctx.nombre}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(informe, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ctx.decir(f"  informe: {destino}")


def etapa_ding(ctx: Ctx) -> None:
    import ding
    ding.generar(DING)


FUNCIONES = {"render": etapa_render, "transiciones": etapa_transiciones, "final": etapa_final, "pptx": etapa_pptx,
             "pdf": etapa_pdf, "html": etapa_html, "vista-previa": etapa_vista_previa, "verificar": etapa_verificar,
             "ding": etapa_ding}


# ---------------------------------------------------------------- main
def leer_argumentos(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="armar.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("subcomando", choices=ETAPAS + ["todo", "ding"])
    p.add_argument("--solo", nargs="+", help="IDs de diapositivas (D14 D19 o D14,D19)")
    p.add_argument("--seccion", choices=["principal", "respaldo", "todas"], default="todas")
    p.add_argument("--salida", default=str(RAIZ / "salida"))
    p.add_argument("--deck", default=str(D.DECK))
    p.add_argument("--render", default=str(RAIZ / "render"))
    p.add_argument("--compacto", choices=["auto", "si", "no"], default="auto")
    p.add_argument("--codificador", choices=["auto", "nvenc", "x264"], default="auto")
    p.add_argument("--simular", action="store_true")
    p.add_argument("--forzar", action="store_true", help="render: correr el motor aunque falte su registro o escena")
    p.add_argument("--show", action="store_true", help="verificar: correr la presentación en una ventana chica")
    p.add_argument("--sin-render", action="store_true", help="todo: saltear el render")
    return p.parse_args(argv)


def armar_ctx(a: argparse.Namespace) -> Ctx:
    deck = D.cargar(a.deck)
    diapos = deck.seleccionar(a.solo, a.seccion)
    if not diapos:
        raise SystemExit("la selección no tiene diapositivas")
    ids = D.normalizar_ids(a.solo)
    nombre = str(deck.datos.get("archivo") or NOMBRE)
    if ids:
        nombre += "_solo-" + "-".join(ids)
    elif a.seccion != "todas":
        nombre += "_" + a.seccion
    rutas = D.Rutas(a.render)
    return Ctx(a, deck, rutas, diapos, Path(a.salida), nombre, rutas.revision / "armado.log")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a = leer_argumentos(argv)
    ctx = armar_ctx(a)
    etapas = [a.subcomando] if a.subcomando != "todo" else [e for e in ETAPAS if not (a.sin_render and e == "render")]
    ctx.decir(f"== {datetime.now():%Y-%m-%d %H:%M:%S} armar.py {' '.join(sys.argv[1:] if argv is None else argv)}")
    ctx.decir(f"   deck {Path(a.deck).name}: {len(ctx.diapos)} diapositivas, {len(ctx.pasos)} pasos; "
              f"render {ctx.rutas.render}; salida {ctx.salida}")
    rc_total = 0
    for etapa in etapas:
        ctx.decir(f"-- {etapa}")
        t = time.time()
        rc = 0
        try:
            FUNCIONES[etapa](ctx)
        except SystemExit as e:
            if e.code not in (None, 0):
                ctx.error(str(e.code))
            rc = 1
        except Exception as e:  # noqa: BLE001  (se anota y se corta)
            import traceback
            ctx.error(f"{type(e).__name__}: {e}")
            ctx.decir(traceback.format_exc())
            rc = 1
        if etapa == "verificar" and ctx.errores:
            rc = 1
        ctx.decir(f"{etapa} rc={rc} {time.time() - t:.1f}s")
        rc_total = rc_total or rc
        if rc and a.subcomando == "todo" and etapa not in ("render", "verificar"):
            ctx.decir("   (se corta: las etapas que siguen necesitan esta)")
            break
    if ctx.avisos:
        ctx.decir(f"   {len(ctx.avisos)} avisos")
    if ctx.errores:
        ctx.decir(f"   {len(ctx.errores)} errores")
    return rc_total


if __name__ == "__main__":
    sys.exit(main())
