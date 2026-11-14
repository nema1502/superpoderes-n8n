"""D05 Qué es n8n: el flujo que la sala acaba de usar (guion: contenido/guion.md, D05).

La sala se anotó al sorteo desde el celular en D04. Esta diapositiva muestra que eso fue un flujo:
el celular de cerca, con el nombre que acaba de salir, y la cámara se aleja hasta que aparece el
flujo entero (Formulario, Revisar palabra, Limpiar, Guardar). El nombre viaja por las conexiones,
entra en cada nodo (que late mientras lo procesa) y queda guardado debajo de Guardar. Después,
disparador y pasos, y al final dos datos de n8n con su logo.

    <python del entorno> manim/render_diapo.py D05

Este archivo también tiene las piezas del grupo de diapositivas que explican cómo fluye algo (D05,
D07 y D08): el nodo de flujo, los íconos, los logos, las líneas a trazos, el punto que viaja y la
cámara. D07 y D08 las importan de acá, así el nodo es el mismo en las tres.

Decisiones:
- Nodo: radio 32 px como pide el deck para toda la charla (no es un radio de los tokens), relleno
  noche, borde azul de 5 px hacia adentro e ícono en hueso dentro de un cuadrado del 45 % del lado.
- La cámara (D05.1): el celular arranca al doble y centrado, y el cuadro se abre hasta mostrar el
  flujo entero. No es la cámara de Manim (la marca de agua tiene que quedar quieta en su píxel): es
  el grupo del flujo visto con un zoom que va de 2 a 1. Los otros tres nodos aparecen mientras la
  cámara se aleja, como si siempre hubieran estado ahí.
- El título entra en dos tiempos: Lo que acaban de hacer con el celular, y es un flujo cuando el
  flujo aparece.
- El nombre pasa por DETRÁS de los nodos: entra en cada uno y sale del otro lado (el nodo late
  cuando lo tiene), como un dato que procesa cada paso. Por encima tapaba los íconos.
- El nombre queda guardado tal como viajó, la pastilla ámbar, y late una vez al llegar. La fila de
  borde fino en que se convertía antes se leía como otra cosa.
- D05.2: los corchetes van en gris y en el trazo normal (como en la charla de octubre) y abarcan el
  nodo y su rótulo. Todo el flujo va 20 px más arriba que en el deck (nodos en y 500): así
  disparador y pasos (y 748) quedan con aire arriba y abajo. El título
  pasa a gris en vez de bajar al 60 %: el amarillo al 60 % sale oliva, y el auditor de cuadros ve
  sus bordes como lima.
- D05.3: el logo en y 440 y las líneas en 630, 730 y 830, para dejarle al logo de n8n el aire que
  piden sus reglas (el alto del símbolo, 110 px, arriba y abajo).
- D05.3: el flujo se achica con sus bordes (como una cámara que se aleja) y sus rótulos se van: a
  0,55 quedaban en 27 px, que no se leen.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))

import numpy as np  # noqa: E402
from charla import (  # noqa: E402
    AMBAR, AZUL, CURVA, GRIS, GROSOR, HUESO, NOCHE, OPACIDAD, RAIZ, TINTA, TITULO, Aparecer, Desplazar,
    Desvanecer, DiapoCharla, Entrar, Foco, Latido, Mover, Texto, Tramo, Trazo, corchete, imagen_en, linea, punto,
    rect_borde, s, textos, trazo, u,
)
from charla import _aplicar_opacidad, _Entrar, _opacidades  # noqa: E402
from manim import Animation, Dot, SVGMobject, VGroup, VMobject, rate_functions  # noqa: E402

# ---------------------------------------------------------------------------
# Piezas del grupo (D05, D07 y D08)
# ---------------------------------------------------------------------------

RUTA_ICONOS = Path(__file__).resolve().parents[1] / "comun" / "iconos"
RUTA_LOGOS = RAIZ / "diseno" / "logos"

NODO_RADIO = 32          # px, deck: el nodo de flujo de toda la charla
NODO_BORDE = GROSOR["borde"]  # 5 px, hacia adentro
ICONO_LADO = 0.45        # el ícono cabe en un cuadrado del 45 % del lado del nodo
CONEXION = GROSOR["trazo_normal"]  # 5 px
TRAZOS = (16, 12)        # px: las conexiones de herramientas y memoria van a trazos, como en n8n
DATO_RADIO = 14          # px: el punto ámbar de 28 px
Z_LINEA, Z_DATO, Z_NODO, Z_ROTULO = 0, 1, 2, 3


RUTA_FONDO = RAIZ / "diseno" / "medios" / "D01" / "fondo_circuito.png"


def fondo_circuito():
    """El fondo de circuito de la charla: las pistas de la portada, muy tenues, que entran desde los
    bordes (diseno/medios/D01/generar_fondo.py). Es el mismo PNG que pone FondoCircuito en Remotion,
    pegado en su píxel y debajo de todo. El auditor de escenas no lo mira: es el fondo."""
    img = imagen_en(RUTA_FONDO, 0, 0)
    img.auditor_ignorar = True
    img.set_z_index(-1000)
    return img


def icono(nombre: str, cx: float, cy: float, lado: float, color: str = HUESO) -> SVGMobject:
    """Un ícono de manim/comun/iconos dentro de un cuadrado de `lado` px, centrado en (cx, cy)."""
    ic = SVGMobject(str(RUTA_ICONOS / f"{nombre}.svg"))
    ic.scale(u(lado) / max(ic.width, ic.height))
    ic.set_fill(color, opacity=1).set_stroke(width=0)
    ic.move_to(punto(cx, cy))
    return ic


def logo(ruta: str, cx: float, cy: float, alto: float) -> SVGMobject:
    """Un logo de diseno/logos tal cual (sus colores, sin deformar), de `alto` px, centrado en (cx, cy)."""
    lg = SVGMobject(str(RUTA_LOGOS / ruta))
    lg.scale(u(alto) / lg.height)
    for m in lg.family_members_with_points():
        m.set_stroke(width=0)  # los SVG de las marcas no traen trazo
    lg.move_to(punto(cx, cy))
    return lg


def nodo(cx: float, cy: float, lado: float, nombre_icono: str | None = None, ruta_logo: str | None = None,
         borde: str = AZUL) -> VGroup:
    """El nodo de flujo: cuadrado redondeado relleno noche, borde azul de 5 px y el ícono (o el logo) en
    hueso al 45 % del lado. Queda con .caja, .icono, .cx, .cy y .lado."""
    caja = rect_borde(cx, cy, lado, lado, NODO_RADIO, NODO_BORDE, color=borde, relleno=NOCHE, opacidad_relleno=1)
    if ruta_logo:
        dentro = logo(ruta_logo, cx, cy, ICONO_LADO * lado)
    else:
        dentro = icono(nombre_icono, cx, cy, ICONO_LADO * lado)
    g = VGroup(caja, dentro)
    g.caja, g.icono, g.cx, g.cy, g.lado = caja, dentro, cx, cy, lado
    g.set_z_index(Z_NODO)
    return g


def conexion(x0: float, y0: float, x1: float, y1: float, color: str = AZUL):
    """Una conexión recta de 5 px entre dos nodos (el auditor mira que toque sus dos extremos)."""
    ln = linea(x0, y0, x1, y1, grosor=CONEXION, color=color, conector=True)
    ln.set_z_index(Z_LINEA)
    return ln


def camino(puntos_px, radio: float = 0.0, color: str = AZUL, grosor: float = CONEXION) -> VMobject:
    """Una pista en px por varios puntos, con las esquinas redondeadas con `radio` px (como las pistas
    de un circuito). Sirve de conexión dibujada y de camino para el punto que viaja. El auditor no la
    juzga como conector (sus extremos se cuidan a mano)."""
    p = [np.array(punto(x, y)) for x, y in puntos_px]
    c = VMobject(stroke_color=color, stroke_width=trazo(grosor), fill_opacity=0)
    if radio <= 0 or len(p) < 3:
        c.set_points_as_corners(p)
    else:
        r = u(radio)
        c.start_new_path(p[0])
        for i in range(1, len(p) - 1):
            a, b, d = p[i - 1], p[i], p[i + 1]
            d1 = (b - a) / np.linalg.norm(b - a)
            d2 = (d - b) / np.linalg.norm(d - b)
            entra_, sale_ = b - d1 * r, b + d2 * r
            c.add_line_to(entra_)
            c.add_cubic_bezier_curve_to(entra_ + d1 * r * 0.55, sale_ - d2 * r * 0.55, sale_)
        c.add_line_to(p[-1])
    c.auditor_ignorar = True
    c.set_z_index(Z_LINEA)
    return c


def a_trazos(x0: float, y0: float, x1: float, y1: float, color: str = AZUL, grosor: float = CONEXION) -> VGroup:
    """Una conexión a trazos (16 px de trazo y 12 de hueco, como las de herramientas y memoria en n8n),
    de (x0, y0) a (x1, y1). Termina siempre en un trazo entero sobre el punto final."""
    largo, hueco = TRAZOS
    total = float(np.hypot(x1 - x0, y1 - y0))
    n = max(1, int((total + hueco) // (largo + hueco)))
    paso = (total - largo) / (n - 1) if n > 1 else 0.0  # reparte el sobrante en los huecos
    dx, dy = (x1 - x0) / total, (y1 - y0) / total
    piezas = []
    for i in range(n):
        a = i * paso
        b = min(total, a + largo)
        ln = linea(x0 + dx * a, y0 + dy * a, x0 + dx * b, y0 + dy * b, grosor=grosor, color=color)
        piezas.append(ln)
    g = VGroup(*piezas)
    for m in g.get_family():
        m.auditor_ignorar = True
    g.set_z_index(Z_LINEA)
    return g


def dato(x: float, y: float) -> Dot:
    """El punto ámbar de 28 px que viaja por un flujo."""
    d = Dot(punto(x, y), radius=u(DATO_RADIO), color=AMBAR)
    d.set_fill(AMBAR, opacity=1).set_stroke(width=0)
    d.set_z_index(Z_DATO)
    return d


def pastilla(cadena: str, cx: float, cy: float, tam="lectura", color_texto: str = HUESO, alto: float = 88,
             aire: float = 36, borde: str = HUESO, opacidad_borde: float = OPACIDAD["borde_apoyo"],
             relleno: str | None = None, ancho: float | None = None) -> VGroup:
    """Una pastilla: el texto centrado en un rectángulo de puntas redondas (borde hueso al 40 % por
    defecto). Queda con .caja y .texto."""
    t = Texto(cadena, cx, cy, tam=tam, color=color_texto, alinear="centro")
    w = ancho if ancho is not None else t.avance + 2 * aire
    caja = rect_borde(cx, cy, w, alto, alto / 2, NODO_BORDE, color=borde,
                      relleno=relleno, opacidad_relleno=1 if relleno else 0)
    caja.set_stroke(opacity=opacidad_borde)
    g = VGroup(caja, t)
    g.caja, g.texto, g.ancho = caja, t, w
    return g


# ---- movimiento ----


def instante(curva: str, q: float) -> float:
    """La fracción del tramo en que la curva llega a q (para sincronizar un latido con el punto)."""
    f = CURVA[curva]
    a, b = 0.0, 1.0
    for _ in range(50):
        m = (a + b) / 2
        if f(m) < q:
            a = m
        else:
            b = m
    return (a + b) / 2


def escalar(m, k: float, centro) -> None:
    """Escala un grupo con sus trazos, miembro por miembro. (scale_stroke=True de Manim le pone a
    toda la familia el trazo del grupo por k: los textos salían gordos.)"""
    for x in m.family_members_with_points():
        x.set_stroke(width=x.get_stroke_width() * k, family=False)
    m.scale(k, about_point=centro)


def aplicar_camara(m, z: float, foco, centro) -> None:
    """El grupo visto con zoom z: el punto `foco` (px del estado final) queda en `centro` (px del cuadro)."""
    escalar(m, z, punto(*foco))
    m.shift(punto(*centro) - punto(*foco))


class _Camara(Animation):
    """Una cámara sobre un grupo: en cada cuadro el grupo es su estado `final` visto con un zoom que va
    de z0 a z1 (interpolado en escala logarítmica, como un zoom de verdad) y con el foco que va de f0 a
    f1, puesto en `centro`. Lo de `aparecen` se enciende en la primera mitad del tramo."""

    def __init__(self, grupo, final, z0, f0, z1, f1, centro, curva, aparecen=(), **kw):
        self.final, self.curva = final, curva
        self.z0, self.z1 = z0, z1
        self.f0, self.f1 = np.array(f0, dtype=float), np.array(f1, dtype=float)
        self.centro = centro
        # (miembro del grupo, opacidades finales del mismo miembro en `final`)
        self.aparecen = [(m, _opacidades(final.submobjects[grupo.submobjects.index(m)])) for m in aparecen]
        super().__init__(grupo, rate_func=rate_functions.linear, **kw)

    def interpolate_mobject(self, alpha: float):
        p = self.curva(alpha)
        z = self.z0 * (self.z1 / self.z0) ** p
        f = self.f0 + (self.f1 - self.f0) * p
        self.mobject.become(self.final)
        aplicar_camara(self.mobject, z, f, self.centro)
        k = CURVA["fundido"](min(1.0, alpha / 0.6))
        for m, base in self.aparecen:
            _aplicar_opacidad(m, base, k)


def Camara(grupo, final, z0, f0, z1, f1, centro, retraso, dura, curva="suave", aparecen=()) -> Tramo:
    return Tramo(_Camara(grupo, final, z0, f0, z1, f1, centro, CURVA[curva], aparecen), retraso, dura)


class _Brotar(Animation):
    """Aparece creciendo un poco desde su centro (de `desde` a 1, salida cúbica) y encendiéndose: para
    un logo o una tarjeta, que no tienen que subir como un texto."""

    def __init__(self, m, desde: float, **kw):
        self.desde = desde
        super().__init__(m, introducer=True, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.base = _opacidades(self.mobject)
        self.centro = self.mobject.get_center()
        super().begin()

    def interpolate_mobject(self, alpha: float):
        p = CURVA["sale"](alpha)
        self.mobject.become(self.objetivo)
        if p < 1:
            self.mobject.scale(self.desde + (1 - self.desde) * p, about_point=self.centro)
        _aplicar_opacidad(self.mobject, self.base, min(1.0, 1.5 * CURVA["fundido"](alpha)))


def Brotar(m, retraso: float = 0.0, dura: float = 0.5, desde: float = 0.9) -> Tramo:
    return Tramo(_Brotar(m, desde), retraso, dura)


class _Recorrido(Animation):
    """El punto viaja por un camino (proporción del largo, con una curva). Con `aparece` se enciende al
    salir y con `apaga` se apaga al llegar (fracciones del tramo)."""

    def __init__(self, m, cam: VMobject, curva, aparece=None, apaga=None, **kw):
        self.cam, self.curva, self.aparece, self.apaga = cam, curva, aparece, apaga
        super().__init__(m, introducer=bool(aparece), rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.base = _opacidades(self.mobject)
        super().begin()

    def interpolate_mobject(self, alpha: float):
        self.mobject.move_to(self.cam.point_from_proportion(min(1.0, max(0.0, self.curva(alpha)))))
        k = 1.0
        if self.aparece:
            k *= CURVA["fundido"](min(1.0, alpha / self.aparece))
        if self.apaga:
            k *= CURVA["fundido"](min(1.0, (1 - alpha) / self.apaga))
        _aplicar_opacidad(self.mobject, self.base, k)


def Recorrer(m, cam: VMobject, retraso: float, dura: float, curva: str = "suave", aparece=None, apaga=None) -> Tramo:
    return Tramo(_Recorrido(m, cam, CURVA[curva], aparece, apaga), retraso, dura)


def entrar_partes(t: Texto, indices, retraso: float, desfase: float, dura: float = 0.5) -> list[Tramo]:
    """Entrar de algunas partes de un Texto, sin poner el Texto entero al final (para que una frase
    entre en dos tiempos). Cuando entraron todas, la escena cambia las partes por el Texto."""
    return [Tramo(_Entrar(t.submobjects[i], s(dura)), retraso + k * desfase, dura) for k, i in enumerate(indices)]


# ---------------------------------------------------------------------------
# D05
# ---------------------------------------------------------------------------

CX = [270, 730, 1190, 1650]
CY = 500                   # 20 px más arriba que el deck: deja aire a disparador, pasos y la frase de D05.2
LADO = 200
ICONOS = ["mobile-screen-button", "list-check", "wand-magic-sparkles", "table"]
TAM_ROTULO = 49            # deck D05.1: los rótulos a 49 px (Revisar palabra a 60 se tocaba con sus vecinos)
Y_ROTULO = 660
Y_TITULO = 200
# El título entra en dos tiempos: lo de antes de "es un flujo" con el celular de cerca, y "es un flujo"
# cuando la cámara se aleja. Con el formulario en el deck dice Lo que acaban de hacer es un flujo, y sin
# él, Anotarse al sorteo es un flujo (contenido/generar_deck.py): las partes salen de las palabras.
FINAL_TITULO = 3  # " es", " un", " flujo"


def partes_titulo(texto: str) -> list[str]:
    palabras = texto.split(" ")
    if len(palabras) <= FINAL_TITULO or palabras[-FINAL_TITULO:] != ["es", "un", "flujo"]:
        raise ValueError(f"D05.1: el título tiene que terminar en es un flujo: {texto!r}")
    return [palabras[0]] + [" " + x for x in palabras[1:]]


FILA = {"cx": 1650, "cy": 770}   # donde queda guardado el nombre, debajo de Guardar
PILDORA = {"alto": 64, "aire": 26, "separacion": 30}                    # el nombre que viaja
FOCO_CERCA = (330, 500)    # D05.1: donde mira la cámara al principio (el celular y el nombre)
ZOOM_CERCA = 2.0
CORCHETE = {"y": 702, "alto": 12, "grosor": GROSOR["trazo_normal"]}
Y_PARTES, Y_FRASE = 748, 870
# D05.3
ESCALA_CHICO, Y_CHICO = 0.55, 230
Y_LOGO, ALTO_LOGO = 440, 110   # 110 px de aire arriba y abajo: el alto del símbolo, como pide n8n
Y_LINEAS = (630, 730, 830)
Y_FUENTE = 990


def bordes_x(i: int) -> tuple[float, float]:
    return CX[i] - LADO / 2, CX[i] + LADO / 2


class D05QueEsUnFlujo(DiapoCharla):
    ID = "D05"

    def construct(self):
        t1, t2, t3 = textos("D05", 1), textos("D05", 2), textos("D05", 3)
        self.add(fondo_circuito())

        # ---------------- Paso 1: lo que acaban de hacer es un flujo ----------------
        self.paso(1)
        partes = partes_titulo(t1[0])
        n_antes = len(partes) - FINAL_TITULO
        titulo = Texto(t1[0], 960, Y_TITULO, tam="frase", color=TITULO, alinear="centro", partes=partes)
        nodos = [nodo(cx, CY, LADO, nombre_icono=ic) for cx, ic in zip(CX, ICONOS)]
        rotulos = [Texto(t1[1 + i], CX[i], Y_ROTULO, tam=TAM_ROTULO, alinear="centro") for i in range(4)]
        for r in rotulos:
            r.set_z_index(Z_ROTULO)
        lineas = [conexion(bordes_x(i)[1], CY, bordes_x(i + 1)[0], CY) for i in range(3)]

        # El nombre: una pastilla ámbar con el texto en tinta, sobre la primera conexión.
        ana = Texto(t1[5], 960, CY, tam="rotulo", color=TINTA, alinear="centro")
        w_ana = ana.avance + 2 * PILDORA["aire"]
        x_ana = bordes_x(0)[1] + PILDORA["separacion"] + w_ana / 2
        ana.shift(punto(x_ana, 0) - punto(960, 0))
        caja_ana = rect_borde(x_ana, CY, w_ana, PILDORA["alto"], PILDORA["alto"] / 2, 2, color=AMBAR, relleno=AMBAR,
                              opacidad_relleno=1)
        pildora = VGroup(caja_ana, ana)
        pildora.set_z_index(Z_DATO)

        # La cámara: el grupo del flujo en su estado final y visto al doble, mirando el celular.
        flujo = VGroup(*nodos, pildora)
        final = flujo.copy()
        aplicar_camara(flujo, ZOOM_CERCA, FOCO_CERCA, (960, 540))
        for n in nodos[1:]:
            _aplicar_opacidad(n, _opacidades(n), 0.0)
        self.add(*nodos[1:])  # apagados: se encienden con la cámara

        # El celular de cerca. El nombre sale de él (por detrás) y lo de arriba dice qué hicieron.
        ana_ini = pildora.get_center().copy()
        pildora.move_to(nodos[0].get_center())
        dx_px = (ana_ini[0] - pildora.get_center()[0]) * 135
        self.tocar(
            Entrar(nodos[0], 0.0, 0.5),
            entrar_partes(titulo, range(n_antes), 0.15, 0.09),
            Desplazar(pildora, dx_px, 0, 0.4, 0.5, curva="sale", aparece=0.4),
        )
        # La cámara se aleja: aparece el flujo entero, termina la frase y entran los rótulos.
        self.tocar(
            Camara(flujo, final, ZOOM_CERCA, FOCO_CERCA, 1.0, (960, 540), (960, 540), 0.0, 0.8,
                   aparecen=nodos[1:]),
            entrar_partes(titulo, range(n_antes, len(partes)), 0.4, 0.1),
            *[Aparecer(r, 0.6 + 0.08 * i, 0.3) for i, r in enumerate(rotulos)],
        )
        self.remove(*titulo.submobjects, flujo)
        self.add(titulo, *nodos, pildora)

        # Las conexiones se dibujan por delante del nombre, que arranca despacio. El nombre entra en
        # cada nodo por detrás y sale del otro lado, y el nodo late al tenerlo. (Las conexiones no se
        # dibujan antes: el nombre espera sobre la primera, y en reposo el auditor la vería cruzarlo.)
        viaje = 1.3
        x0 = pildora.get_center()[0] * 135 + 960
        tramos = [Desplazar(pildora, CX[3] - x0, 0, 0.0, viaje, curva="suave")]
        tramos += [Trazo(ln, 0.1 * i, 0.25) for i, ln in enumerate(lineas)]
        for i in (1, 2, 3):
            t_i = instante("suave", (CX[i] - x0) / (CX[3] - x0)) * viaje
            tramos.append(Latido(nodos[i], max(0.0, t_i - 0.2), 0.4, escala=1.06))
        self.tocar(*tramos)
        # Baja debajo de Guardar y queda ahí tal como viajó: la misma pastilla ámbar, que late una vez
        # al quedar guardada (antes se convertía en una fila de borde fino que se leía como otra cosa).
        self.tocar(Desplazar(pildora, 0, FILA["cy"] - CY, 0.0, 0.35, curva="suave"))
        self.tocar(Latido(pildora, 0.0, 0.35, escala=1.08))

        # ---------------- Paso 2: disparador y pasos ----------------
        self.paso(2)
        # Los corchetes abarcan el nodo y su rótulo (van justo debajo de los rótulos).
        x_d0 = min(bordes_x(0)[0], rotulos[0].izquierda)
        x_d1 = max(bordes_x(0)[1], rotulos[0].derecha)
        x_p0 = min(bordes_x(1)[0], rotulos[1].izquierda)
        x_p1 = max(bordes_x(3)[1], rotulos[3].derecha)
        cor1 = corchete(x_d0, x_d1, CORCHETE["y"], CORCHETE["alto"], CORCHETE["grosor"], GRIS)
        cor2 = corchete(x_p0, x_p1, CORCHETE["y"], CORCHETE["alto"], CORCHETE["grosor"], GRIS)
        disparador = Texto(t2[0], (x_d0 + x_d1) / 2, Y_PARTES, tam="lectura", color=AMBAR, alinear="centro")
        pasos = Texto(t2[1], (x_p0 + x_p1) / 2, Y_PARTES, tam="lectura", alinear="centro")
        frase = Texto(t2[2], 960, Y_FRASE, tam="frase", alinear="centro")
        # El título pasa a gris en vez de bajar al 60 %: el amarillo al 60 % sale oliva (como el ámbar
        # bajo, que sale marrón) y sus bordes caen en la familia del lima del auditor de cuadros.
        titulo_gris = Texto(t1[0], 960, Y_TITULO, tam="frase", color=GRIS, alinear="centro", partes=partes)
        self.tocar(
            Mover(titulo, titulo_gris, 0.0, 0.3),
            Desvanecer(pildora, 0.0, 0.3),
            Trazo(cor1, 0.2, 0.4),
            Latido(nodos[0], 0.25, 0.4),
            Entrar(disparador, 0.35),
            Trazo(cor2, 0.55, 0.45),
            Entrar(pasos, 0.7),
            Entrar(frase, 1.1),
            *[Latido(nodos[i], 1.3 + 0.15 * (i - 1), 0.4) for i in (1, 2, 3)],
        )

        # ---------------- Paso 3: n8n no es un juguete ----------------
        self.paso(3)
        red = VGroup(*nodos, *lineas)
        chico = red.copy()
        escalar(chico, ESCALA_CHICO, punto(960, CY))
        chico.shift(punto(960, Y_CHICO) - punto(960, CY))
        marca_n8n = logo("n8n/n8n-logo-white-accent.svg", 960, Y_LOGO, ALTO_LOGO)
        l1 = Texto(t3[1], 960, Y_LINEAS[0], tam="frase", alinear="centro", resaltar="210 mil")
        l2 = Texto(t3[2], 960, Y_LINEAS[1], tam="frase", alinear="centro", resaltar="500")
        l3 = Texto(t3[3], 960, Y_LINEAS[2], tam="lectura", color=GRIS, alinear="centro")
        fuente = Texto(t3[4], 960, Y_FUENTE, tam="fuente", color=GRIS, alinear="centro")
        self.tocar(
            Mover(red, chico, 0.0, 0.6),
            Desvanecer(VGroup(*rotulos), 0.0, 0.25),
            Desvanecer(VGroup(cor1, cor2, disparador, pasos, frase), 0.0, 0.3),
            Desvanecer(titulo, 0.0, 0.3),
        )
        self.tocar(
            Brotar(marca_n8n, 0.0, 0.5),
            Entrar(l1, 0.25),
            Entrar(l2, 0.45),
            Entrar(l3, 0.65),
            Aparecer(fuente, 0.85, 0.4),
        )
