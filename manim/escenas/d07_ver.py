"""D07 Primer superpoder: ver (guion: contenido/guion.md, D07).

SerpApi hace la búsqueda en Google por el flujo y la devuelve ordenada. Se escribe café, el punto
ámbar va por la pista de arriba hasta SerpApi y Google, vuelve por la de abajo y baja hasta un
panel donde se abren tres líneas de datos. Después la cámara se acerca al panel, que se vuelve la
tarjeta del lugar (una búsqueda real de la noche del 13 de noviembre), y al final los motores que
trae el nodo de SerpApi en n8n.

    <python del entorno> manim/render_diapo.py D07

Usa las piezas del grupo (nodo, ícono, logo, pastilla, punto que viaja) de d05_que_es_un_flujo.py.

Decisiones:
- La pastilla de centro de Santa Cruz va debajo de la caja de búsqueda: a su derecha (como pedía el
  deck) chocaba con el nodo de SerpApi, porque a 49 px mide 480 px.
- Ida y vuelta por dos pistas paralelas (y 450 y 490), como una calle de doble mano: el punto entra
  por detrás de cada nodo y sale del otro lado (el nodo late al tenerlo). La vuelta baja por una
  pista con esquinas redondeadas hasta un panel con los datos, y esa pista se dibuja junto con el
  punto (las dos con la misma curva, sobre un camino de tramos iguales para que vayan parejas).
- Debajo del nodo de SerpApi, su logo con la palabra (blanco, tal cual): las reglas de SerpApi
  piden el ícono con la palabra, y así la sala lee SerpApi igual que lee Google en el otro nodo.
- La caja de búsqueda va rellena de pantalla, como un campo de texto de verdad. café se escribe
  letra por letra con un cursor que avanza.
- D07.2: el panel crece hasta ser la tarjeta (el acercamiento). Sitcom Café, 4.7 y 122 viajan
  desde sus líneas: el punto de 4.7 se vuelve la coma de 4,7. Una estrella ámbar junto al puntaje
  (la estrella y el número son una sola cosa en ámbar) y, a la derecha de la tarjeta, un nodo con
  el ícono del mapa, que dice de dónde salió el dato.
- D07.3: arriba, el logo de SerpApi con la palabra, que dice de quién son los motores.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from charla import (  # noqa: E402
    AMBAR, CURVA, GRIS, GROSOR, HUESO, OPACIDAD, PANTALLA, RADIO, TITULO, Aparecer, Desvanecer, DiapoCharla,
    Entrar, Latido, Mover, Texto, Tramo, Trazo, caja_px, punto, rect_borde, s, textos, u,
)
from charla import _aplicar_opacidad, _opacidades  # noqa: E402
from d05_que_es_un_flujo import (  # noqa: E402
    fondo_circuito,
    Brotar, Recorrer, camino, conexion, dato, entrar_partes, icono, instante, logo, nodo, pastilla,
)
from manim import Animation, Star, Transform, VGroup, VMobject, rate_functions  # noqa: E402

# ---- Paso 1 ----
LUPA = {"cx": 160, "cy": 170, "lado": 90}
X_TITULO, Y_TITULO = 230, 170
X_FRASE, Y_FRASE = 160, 290
CAJA = {"x0": 160, "x1": 780, "cy": 470, "alto": 100, "radio": 50}
X_CAFE = 206
CURSOR = {"ancho": 5, "alto": 62, "aire": 8}
Y_UBICACION = 575
SERP = (1260, 470)
GOOG = (1640, 470)
LADO = 160
Y_ROTULO = 612
ALTO_LOGO_SERP = 56          # el logo con la palabra debajo del nodo, a la altura del rótulo Google
Y_IDA, Y_VUELTA = 450, 490   # las dos pistas: de ida (arriba) y de vuelta (abajo)
X_BAJADA = 1110              # por donde baja la pista de vuelta hacia el panel
RADIO_PISTA = 24
PANEL = {"x0": 360, "x1": 960, "cy": 760, "alto": 220}
X_DATOS = 400
Y_DATOS = (700, 760, 820)
PARTES_DATOS = (['"title": "', "Sitcom Café", '"'], ['"rating": ', "4.7"], ['"reviews": ', "122"])

# ---- Paso 2 ----
TARJETA = {"cx": 960, "cy": 560, "ancho": 1100, "alto": 440}
X_TARJETA = 470
# 10 a 18 px más arriba que el deck: con 730, Abierto quedaba a 23 px del borde de abajo y a 60 del de arriba.
Y_NOMBRE, Y_TIPO, Y_NOTA, Y_ABIERTO = 420, 498, 612, 712
ESTRELLA = {"radio": 30, "aire": 26}
MAPA = {"cx": 1360, "cy": 560, "lado": 150}
Y_FUENTE = 990

# ---- Paso 3 ----
Y_LOGO_ARRIBA, ALTO_LOGO_ARRIBA = 170, 64
FILAS = ((300, (1, 2, 3)), (420, (4, 5, 6)), (540, (7, 8)))   # y de cada fila y qué textos van
PASTILLA = {"alto": 88, "aire": 36, "hueco": 32}
Y_FRASES = (700, 810)


def camino_parejo(puntos_px, radio: float, paso_px: float = 4.0) -> VMobject:
    """Un camino como `camino`, rehecho con tramos rectos de unos `paso_px` px: así dibujarlo (que
    avanza por cantidad de tramos) y recorrerlo (que avanza por largo) van parejos."""
    base = camino(puntos_px, radio)
    largo = base.get_arc_length() * 135
    n = max(2, int(largo / paso_px))
    pts = [base.point_from_proportion(i / n) for i in range(n + 1)]
    c = VMobject(stroke_color=base.get_stroke_color(), stroke_width=base.get_stroke_width(), fill_opacity=0)
    c.set_points_as_corners(pts)
    c.auditor_ignorar = True
    c.set_z_index(base.z_index)
    return c


class _Cursor(Animation):
    """El cursor de la caja: se enciende y salta a cada posición en su instante (fracciones del
    tramo), como cuando se escribe."""

    def __init__(self, m, xs_px, cortes, **kw):
        self.xs, self.cortes = xs_px, cortes
        super().__init__(m, introducer=True, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.base = _opacidades(self.mobject)
        self.y = self.mobject.get_center()[1]
        super().begin()

    def interpolate_mobject(self, alpha: float):
        i = sum(1 for c in self.cortes if alpha >= c)
        self.mobject.move_to(np.array([punto(self.xs[i], 0)[0], self.y, 0.0]))
        _aplicar_opacidad(self.mobject, self.base, CURVA["fundido"](min(1.0, alpha / max(self.cortes[0], 1e-6))))


class _Irse(Animation):
    """Se achica un poco hacia su centro y se apaga (y sale de la escena)."""

    def __init__(self, m, hasta: float, **kw):
        self.hasta = hasta
        super().__init__(m, remover=True, rate_func=rate_functions.linear, **kw)

    def begin(self):
        self.objetivo = self.mobject.copy()
        self.base = _opacidades(self.mobject)
        self.centro = self.mobject.get_center()
        super().begin()

    def interpolate_mobject(self, alpha: float):
        p = CURVA["suave"](alpha)
        self.mobject.become(self.objetivo)
        self.mobject.scale(1 + (self.hasta - 1) * p, about_point=self.centro)
        _aplicar_opacidad(self.mobject, self.base, 1 - CURVA["fundido"](alpha))

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        self.mobject.become(self.objetivo)


def Irse(m, retraso: float = 0.0, dura: float = 0.4, hasta: float = 0.85) -> Tramo:
    return Tramo(_Irse(m, hasta), retraso, dura)


def borde_apoyo(m):
    m.set_stroke(opacity=OPACIDAD["borde_apoyo"])
    return m


class D07Ver(DiapoCharla):
    ID = "D07"

    def construct(self):
        t1, t2, t3 = textos("D07", 1), textos("D07", 2), textos("D07", 3)
        self.add(fondo_circuito())

        # ---------------- Paso 1: ver ----------------
        self.paso(1)
        lupa = icono("magnifying-glass", LUPA["cx"], LUPA["cy"], LUPA["lado"])
        ver = Texto(t1[0], X_TITULO, Y_TITULO, tam="grande", color=TITULO)
        frase = Texto(t1[1], X_FRASE, Y_FRASE, tam="lectura")

        ancho_caja = CAJA["x1"] - CAJA["x0"]
        caja = borde_apoyo(rect_borde((CAJA["x0"] + CAJA["x1"]) / 2, CAJA["cy"], ancho_caja, CAJA["alto"], CAJA["radio"],
                                      GROSOR["borde"], color=HUESO, relleno=PANTALLA, opacidad_relleno=1))
        cafe = Texto(t1[2], X_CAFE, CAJA["cy"], tam="lectura", partes=list(t1[2]))
        letras = cafe.submobjects
        xs_cursor = [X_CAFE + CURSOR["aire"] / 2] + [caja_px(l)[2] + CURSOR["aire"] for l in letras]
        cursor = rect_borde(xs_cursor[0], CAJA["cy"], CURSOR["ancho"], CURSOR["alto"], 0, 0.01, color=HUESO,
                            relleno=HUESO, opacidad_relleno=1)
        cursor.set_stroke(width=0)
        cursor.auditor_ignorar = True

        # La pastilla de la zona, alineada a la izquierda con la caja (se mide antes para ubicarla).
        w_ubic = Texto(t1[3], 960, Y_UBICACION, tam="rotulo", alinear="centro").avance + 2 * 28
        ubic = pastilla(t1[3], CAJA["x0"] + w_ubic / 2, Y_UBICACION, tam="rotulo", color_texto=GRIS, alto=64, aire=28)

        serp = nodo(*SERP, LADO, ruta_logo="serpapi/logo-white.svg")
        goog = nodo(*GOOG, LADO, nombre_icono="globe")
        rot_serp = logo("serpapi/logo-with-wordmark-white.svg", SERP[0], Y_ROTULO, ALTO_LOGO_SERP)
        rot_goog = Texto(t1[4], GOOG[0], Y_ROTULO, tam="lectura", alinear="centro")

        # La caja termina en un medio círculo: la pista de ida sale de su borde, a la altura de Y_IDA.
        cx_curva = CAJA["x1"] - CAJA["radio"]
        x_sale = cx_curva + float(np.sqrt(CAJA["radio"] ** 2 - (Y_IDA - CAJA["cy"]) ** 2))
        izq_serp, der_serp = SERP[0] - LADO / 2, SERP[0] + LADO / 2
        izq_goog = GOOG[0] - LADO / 2
        l_ida1 = conexion(x_sale, Y_IDA, izq_serp, Y_IDA)
        l_ida2 = conexion(der_serp, Y_IDA, izq_goog, Y_IDA)
        l_vuelta = conexion(izq_goog, Y_VUELTA, der_serp, Y_VUELTA)
        bajada = camino_parejo([(izq_serp, Y_VUELTA), (X_BAJADA, Y_VUELTA), (X_BAJADA, PANEL["cy"]), (PANEL["x1"], PANEL["cy"])],
                               RADIO_PISTA)

        panel = borde_apoyo(rect_borde((PANEL["x0"] + PANEL["x1"]) / 2, PANEL["cy"], PANEL["x1"] - PANEL["x0"], PANEL["alto"],
                                       RADIO["tarjeta"], GROSOR["borde"], color=HUESO, relleno=PANTALLA, opacidad_relleno=1))
        datos = [Texto(t1[5 + i], X_DATOS, Y_DATOS[i], tam="rotulo", color=GRIS, partes=PARTES_DATOS[i]) for i in range(3)]

        t_letras = [0.7 + 0.12 * i for i in range(4)]
        dura_cursor = 0.62
        self.tocar(
            Entrar(lupa, 0.0),
            Entrar(ver, 0.08),
            Entrar(frase, 0.22),
            Brotar(caja, 0.4, 0.4, desde=0.94),
            Tramo(_Cursor(cursor, xs_cursor, [(t - 0.45) / dura_cursor for t in t_letras]), 0.45, dura_cursor),
            *[Aparecer(l, t, 0.07) for l, t in zip(letras, t_letras)],
            Entrar(ubic, 0.55),
            Entrar(serp, 0.5),
            Entrar(goog, 0.65),
            Aparecer(rot_serp, 0.75, 0.3),
            Aparecer(rot_goog, 0.8, 0.3),
            Trazo(l_ida1, 0.8, 0.3),
            Trazo(l_ida2, 0.9, 0.25),
            Trazo(l_vuelta, 0.95, 0.25),
        )
        self.remove(*letras)
        self.add(cafe)

        # Ida: el punto sale de la caja, entra en SerpApi y llega a Google (cada nodo late al tenerlo).
        punto_dato = dato(x_sale, Y_IDA)
        ida = camino([(x_sale, Y_IDA), (GOOG[0], Y_IDA)])
        d_ida = 0.7
        t_serp = instante("suave", (SERP[0] - x_sale) / (GOOG[0] - x_sale)) * d_ida
        self.tocar(
            Desvanecer(cursor, 0.0, 0.2),
            Recorrer(punto_dato, ida, 0.0, d_ida, aparece=0.15),
            Latido(serp, t_serp - 0.17, 0.35),
            Latido(goog, d_ida - 0.15, 0.35),
        )
        # Vuelta por la pista de abajo, otra vez a través de SerpApi,
        vuelta = camino([(GOOG[0], Y_VUELTA), (izq_serp, Y_VUELTA)])
        d_vuelta = 0.45
        t_serp2 = instante("suave", (GOOG[0] - SERP[0]) / (GOOG[0] - izq_serp)) * d_vuelta
        self.tocar(
            Recorrer(punto_dato, vuelta, 0.0, d_vuelta),
            Latido(serp, t_serp2 - 0.17, 0.35),
        )
        # y baja hasta el panel: la pista se dibuja con el punto, y el panel se abre al llegar.
        d_bajada = 0.5
        self.tocar(
            Trazo(bajada, 0.0, d_bajada),
            Recorrer(punto_dato, bajada, 0.0, d_bajada),
            Brotar(panel, 0.35, 0.3, desde=0.92),
        )
        # Se abren las tres líneas de datos, de a una.
        self.tocar(
            Desvanecer(punto_dato, 0.0, 0.15),
            *[Entrar(d, 0.05 + 0.15 * i) for i, d in enumerate(datos)],
        )

        # ---------------- Paso 2: la tarjeta del lugar ----------------
        self.paso(2)
        tarjeta = borde_apoyo(rect_borde(TARJETA["cx"], TARJETA["cy"], TARJETA["ancho"], TARJETA["alto"], RADIO["tarjeta"],
                                         GROSOR["borde"], color=HUESO, relleno=PANTALLA, opacidad_relleno=1))
        nombre = Texto(t2[0], X_TARJETA, Y_NOMBRE, tam="idea")
        tipo = Texto(t2[1], X_TARJETA, Y_TIPO, tam="rotulo", color=GRIS)
        nota = Texto(t2[2], X_TARJETA, Y_NOTA, tam="grande", color=AMBAR)
        x_estrella = nota.derecha + ESTRELLA["aire"] + ESTRELLA["radio"]
        estrella = Star(n=5, outer_radius=u(ESTRELLA["radio"]), inner_radius=u(ESTRELLA["radio"]) * 0.45,
                        color=AMBAR, fill_opacity=1, stroke_width=0).move_to(punto(x_estrella, Y_NOTA))
        resenas = Texto(t2[3], x_estrella + ESTRELLA["radio"] + ESTRELLA["aire"], Y_NOTA, tam="lectura",
                        partes=["122", " reseñas"])
        abierto = Texto(t2[4], X_TARJETA, Y_ABIERTO, tam="lectura")
        mapa = nodo(MAPA["cx"], MAPA["cy"], MAPA["lado"], nombre_icono="map-location-dot")
        fuente = Texto(t2[5], 960, Y_FUENTE, tam="fuente", color=GRIS, alinear="centro")

        viajan = [
            (datos[0].parte("Sitcom Café"), nombre.submobjects[0]),
            (datos[1].parte("4.7"), nota.submobjects[0]),
            (datos[2].parte("122"), resenas.parte("122")),
        ]
        se_van = [datos[0].parte('"title": "'), datos[0].parte('"'), datos[1].parte('"rating":'), datos[2].parte('"reviews":')]
        copias = [destino.copy() for _, destino in viajan]
        self.tocar(
            Desvanecer(VGroup(lupa, ver, frase, caja, cafe, ubic, serp, goog, rot_serp, rot_goog, l_ida1, l_ida2, l_vuelta,
                              bajada), 0.0, 0.35),
            Mover(panel, tarjeta, 0.0, 0.8),
            *[Tramo(Transform(origen, c, rate_func=CURVA["suave"]), 0.1, 0.75) for (origen, _), c in zip(viajan, copias)],
            *[Desvanecer(p, 0.0, 0.25) for p in se_van],
        )
        self.remove(*datos, *[o for o, _ in viajan], panel)
        self.add(tarjeta, nombre, nota, resenas.parte("122"))
        self.tocar(
            entrar_partes(resenas, [1], 0.0, 0.0),
            Brotar(estrella, 0.05, 0.4, desde=0.5),
            Entrar(tipo, 0.15),
            Entrar(abierto, 0.35),
            Brotar(mapa, 0.25, 0.45, desde=0.85),
            Aparecer(fuente, 0.5, 0.35),
        )
        self.remove(*resenas.submobjects)
        self.add(resenas)

        # ---------------- Paso 3: los motores del nodo ----------------
        self.paso(3)
        tarjeta_todo = VGroup(tarjeta, nombre, tipo, nota, estrella, resenas, abierto, mapa)
        marca = logo("serpapi/logo-with-wordmark-white.svg", 960, Y_LOGO_ARRIBA, ALTO_LOGO_ARRIBA)
        pastillas = []
        for y, idx in FILAS:
            anchos = [Texto(t3[i], 960, y, tam="lectura", alinear="centro").avance + 2 * PASTILLA["aire"] for i in idx]
            total = sum(anchos) + PASTILLA["hueco"] * (len(idx) - 1)
            x = 960 - total / 2
            for i, w in zip(idx, anchos):
                pastillas.append(pastilla(t3[i], x + w / 2, y, tam="lectura", alto=PASTILLA["alto"], aire=PASTILLA["aire"]))
                x += w + PASTILLA["hueco"]
        f1 = Texto(t3[0], 960, Y_FRASES[0], tam="frase", alinear="centro", resaltar="37")
        f2 = Texto(t3[9], 960, Y_FRASES[1], tam="frase", alinear="centro", resaltar="250")
        self.tocar(
            Irse(tarjeta_todo, 0.0, 0.4),
            Desvanecer(fuente, 0.0, 0.3),
        )
        self.tocar(
            Brotar(marca, 0.0, 0.45),
            *[Entrar(p, 0.15 + 0.08 * i) for i, p in enumerate(pastillas)],
            Entrar(f1, 1.0),
            Entrar(f2, 1.2),
        )
