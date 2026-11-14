"""D08 Segundo superpoder: pensar (guion: contenido/guion.md, D08).

Un modelo solo sabe lo que leyó: se le pregunta qué café está abierto ahora, piensa (late dos
veces) y responde que no lo puede saber. Después la cámara se aleja un poco y aparece el agente:
el mismo nodo con un aro de cuatro estaciones (piensa, elige, mira, responde), tres herramientas y
la memoria unidas a trazos. Un punto ámbar da la vuelta: piensa, elige (la línea a Mapas se enciende
en ámbar y las otras herramientas bajan), sale hasta Mapas (que se enciende con su brillo), vuelve,
mira y responde. Al final, el agente queda atrás y al frente: Él elige cuál usar.

    <python del entorno> manim/render_diapo.py D08

Usa las piezas del grupo (nodo, ícono, líneas a trazos, punto que viaja) de d05_que_es_un_flujo.py.

Decisiones:
- Los globos siguen la convención de un chat: la pregunta a la derecha, con la cola hacia afuera (la
  persona que pregunta), y la respuesta a la izquierda, pegada al nodo y con la cola hacia él (es
  el modelo el que contesta). Con las dos colas hacia el nodo no se sabía quién hablaba.
- El aro es una elipse (640 por 460 px) y los cuatro verbos van SOBRE el aro, como estaciones de
  una línea: con un círculo de 230 px, responde salía de la zona segura, piensa se pegaba a la
  frase de arriba y mira caía debajo de y 900. El punto pasa por detrás de cada estación (la
  estación late cuando lo tiene), así nunca tapa una palabra.
- El nodo baja de 300 a 220 px y sube a (620, 620) al empezar D08.2: la cámara se aleja para
  que entre el agente entero.
- La memoria va en la columna de las herramientas, debajo de YouTube (en y 850 debajo del nodo
  chocaba con mira), unida al aro con su propia línea a trazos. Las herramientas en x 1500, con
  nodos de 120 px, para que la tarjeta de D08.3 no las corte.
- D08.3: la tarjeta mide 900 por 260 px (tapa el nodo y la estación elige enteros, sin cortar las
  herramientas) y va en tinta, sin borde, para que mande la frase. El aro, las estaciones y las
  herramientas quedan detrás al 25 % (Mapas con su línea ámbar y su brillo, que siguen diciendo cuál
  eligió). Las estaciones guardan su fondo opaco: transparente, se veía el aro por detrás.
- D08.2 y D08.3: la frase cambia en orden (TransformarEnOrden): lo que no sigue se va antes de que
  viaje la palabra que queda, y lo nuevo llega después. Con TransformarPorPartes se leía modelosolo
  y, en D08.3, herramientas se montaba sobre las.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from charla import (  # noqa: E402
    AMBAR, AZUL, GRIS, GROSOR, HUESO, OPACIDAD, RADIO, TINTA, TITULO, Desvanecer, DiapoCharla, Entrar,
    Latido, Mover, Texto, Trazo, punto, rect_borde, textos, trazo,
)
from d05_que_es_un_flujo import (  # noqa: E402
    fondo_circuito,
    NODO_RADIO, Z_NODO, Z_ROTULO, Brotar, Recorrer, a_trazos, camino, dato, icono, instante, nodo,
)
from charla import CURVA, Aparecer, Tramo, _Cambio, _Fundido, linea, u  # noqa: E402
from manim import AnimationGroup, Dot, Transform, VGroup, VMobject, rate_functions  # noqa: E402

# ---- Paso 1 ----
CEREBRO = {"cx": 160, "cy": 170, "lado": 90}
X_TITULO, Y_TITULO = 230, 170
X_FRASE, Y_FRASE = 160, 290
# El nodo y los globos van 40 px más abajo que en el deck y el nodo es más grande (300 en vez de 260):
# así el cuadro se usa entero y no queda vacío el tercio de abajo.
NODO1 = {"cx": 560, "cy": 640, "lado": 300}
GLOBO = {"alto": 116, "aire": 48, "cola": 40, "base": 36}
PREGUNTA = {"cx": 1300, "cy": 520}
RESPUESTA = {"x0": 780, "cy": 760}     # pegada al nodo: su cola termina a 30 px de él
PARTES_FRASE1 = ["Un ", "modelo", " solo sabe lo que leyó."]

# ---- Paso 2 ----
NODO2 = {"cx": 620, "cy": 620, "lado": 220}
ELIPSE = {"cx": 620, "cy": 620, "a": 320, "b": 230}
ESTACION = {"alto": 80, "aire": 30}
ANGULOS = (0, 90, 180, 270)            # piensa arriba, elige a la derecha, mira abajo, responde a la izquierda
HERRAMIENTA = {"cx": 1500, "lado": 120, "ys": (430, 570, 710)}
MEMORIA = {"cx": 1500, "cy": 850, "lado": 100}
X_ROTULO_HERR = 1585
ICONOS_HERR = ("map-location-dot", "globe", "film")
ANGULO_MEMORIA = 125                   # de dónde sale del aro la línea a la memoria
PUERTO_RADIO = 8                       # px: el punto azul de donde salen las líneas a trazos, como en n8n
PARTES_FRASE2 = ["Agente", " = ", "modelo", " + ", "herramientas", " + ", "memoria"]

# La herramienta elegida: una línea ámbar sobre la de trazos y el brillo de la receta de la charla
# (tres bordes a 4, 12 y 24 px del nodo, debajo de él). Las otras herramientas bajan a 0,4.
ELEGIDA = {"grosor": 6, "otras": 0.4}
BRILLO_NODO = ((4, 6, 0.45), (12, 8, 0.2), (24, 10, 0.08))   # distancia al borde, grosor y opacidad
Z_ELEGIDA, Z_BRILLO = 0.5, 0.6                              # sobre los trazos y debajo del dato y del nodo
# La frase cambia en tres tiempos: se va lo que no sigue, después viaja modelo, al final llega lo nuevo.
FRASE_EN_ORDEN = {"sale": 0.35, "viaja": (0.35, 0.75), "dura": 0.7}

# ---- Paso 3 ----
PARTES_FRASE3 = ["Vos le das las ", "herramientas", "."]
TARJETA = {"cx": 960, "cy": 600, "ancho": 900, "alto": 260}
ATRAS = 0.25   # D08.3: el aro y las herramientas quedan detrás de la frase


class _TransformarEnOrden(AnimationGroup):
    """TransformarPorPartes en tres tiempos, para que nunca se lean dos frases encimadas: las partes
    que no siguen se van (de 0 a `sale` del tramo), las que siguen viajan después (`viaja`) y las
    nuevas llegan al final (desde 1 - `sale`). Al final queda en escena `destino`, entero."""

    def __init__(self, origen: Texto, destino: Texto, sale: float, viaja: tuple[float, float], **kw):
        curva = CURVA["suave"]
        v0, v1 = viaja
        self.origen, self.destino = origen, destino
        solape = 2 * sale - 1   # _Cambio: la que se va ocupa de 0 a sale y la que llega de 1 - sale a 1
        claves_d = list(destino.claves)
        usadas_d: set[int] = set()
        anims, self.copias = [], []
        dist_o = 0.3 * getattr(origen, "tam", 60)
        dist_d = 0.3 * getattr(destino, "tam", 60)
        en_su_tiempo = lambda a: curva(min(1.0, max(0.0, (a - v0) / (v1 - v0))))  # noqa: E731
        for i, k in enumerate(origen.claves):
            j = next((j for j, kd in enumerate(claves_d) if kd == k and j not in usadas_d), None)
            if j is not None:
                usadas_d.add(j)
                anims.append(Transform(origen.submobjects[i], destino.submobjects[j].copy(), rate_func=en_su_tiempo))
            else:
                anims.append(_Cambio(origen.submobjects[i], True, dist_o, solape=solape))
        for j, parte_d in enumerate(destino.submobjects):
            if j not in usadas_d:
                copia = parte_d.copy()
                self.copias.append(copia)
                anims.append(_Cambio(copia, False, dist_d, solape=solape))
        super().__init__(*anims, rate_func=rate_functions.linear, **kw)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        scene.remove(self.origen, *self.origen.submobjects, *self.copias)
        scene.add(self.destino)


def TransformarEnOrden(origen: Texto, destino: Texto, retraso: float, dura: float, sale: float,
                       viaja: tuple[float, float]) -> Tramo:
    return Tramo(_TransformarEnOrden(origen, destino, sale, viaja), retraso, dura)


def Bajar(m, factor: float, retraso: float = 0.0, dura: float = 0.4) -> Tramo:
    """Baja la opacidad de `m` por `factor` (relativo a la que tiene), sin sacarlo de la escena."""
    return Tramo(_Fundido(m, 1.0, factor, CURVA["suave"]), retraso, dura)


def brillo_nodo(n, color: str = AMBAR) -> VGroup:
    """El brillo de un nodo encendido: tres bordes concéntricos detrás de él, cada vez más tenues."""
    capas = []
    for dist, grosor, alfa in BRILLO_NODO:
        lado = n.lado + 2 * dist
        r = rect_borde(n.cx, n.cy, lado, lado, NODO_RADIO + dist, grosor, color=color)
        r.set_stroke(opacity=alfa)
        r.auditor_ignorar = True
        capas.append(r)
    g = VGroup(*capas)
    for m in g.get_family():
        m.auditor_ignorar = True
    g.set_z_index(Z_BRILLO)
    return g


def en_elipse(theta_grados: float) -> tuple[float, float]:
    """El punto del aro en el ángulo dado (0 arriba, en el sentido de las agujas del reloj)."""
    t = math.radians(theta_grados)
    return ELIPSE["cx"] + ELIPSE["a"] * math.sin(t), ELIPSE["cy"] - ELIPSE["b"] * math.cos(t)


def arco(theta0: float, theta1: float, n_por_grado: int = 2) -> VMobject:
    """Un tramo del aro, de theta0 a theta1 (grados, en el sentido de las agujas del reloj)."""
    n = max(2, int(abs(theta1 - theta0) * n_por_grado))
    pts = [en_elipse(theta0 + (theta1 - theta0) * i / n) for i in range(n + 1)]
    return camino(pts)


def contorno_globo(x0, y0, x1, y1, r, cola: str, largo: float, base: float) -> VMobject:
    """El contorno de un globo de diálogo en un solo trazo (sin uniones encimadas): un rectángulo de
    puntas redondas con la cola en el borde izquierdo ("izq") o derecho ("der"), a media altura."""
    k = 0.5523 * r
    cy = (y0 + y1) / 2
    p = lambda x, y: punto(x, y)  # noqa: E731
    c = VMobject()
    c.start_new_path(p(x0 + r, y0))
    c.add_line_to(p(x1 - r, y0))
    c.add_cubic_bezier_curve_to(p(x1 - r + k, y0), p(x1, y0 + r - k), p(x1, y0 + r))
    if cola == "der":
        c.add_line_to(p(x1, cy - base / 2))
        c.add_line_to(p(x1 + largo, cy + base / 2 + 6))
        c.add_line_to(p(x1, cy + base / 2))
    c.add_line_to(p(x1, y1 - r))
    c.add_cubic_bezier_curve_to(p(x1, y1 - r + k), p(x1 - r + k, y1), p(x1 - r, y1))
    c.add_line_to(p(x0 + r, y1))
    c.add_cubic_bezier_curve_to(p(x0 + r - k, y1), p(x0, y1 - r + k), p(x0, y1 - r))
    if cola == "izq":
        c.add_line_to(p(x0, cy + base / 2))
        c.add_line_to(p(x0 - largo, cy + base / 2 + 6))
        c.add_line_to(p(x0, cy - base / 2))
    c.add_line_to(p(x0, y0 + r))
    c.add_cubic_bezier_curve_to(p(x0, y0 + r - k), p(x0 + r - k, y0), p(x0 + r, y0))
    return c


def globo(cadena: str, cx: float, cy: float, color_texto: str, cola: str) -> VGroup:
    """Un globo de diálogo: relleno tinta, borde en hueso al 40 % y el texto a 60 px centrado."""
    t = Texto(cadena, cx, cy, tam="lectura", color=color_texto, alinear="centro")
    w, h = t.avance + 2 * GLOBO["aire"], GLOBO["alto"]
    forma = contorno_globo(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, RADIO["globo"], cola, GLOBO["cola"], GLOBO["base"])
    forma.set_fill(TINTA, opacity=1)
    forma.set_stroke(HUESO, width=trazo(GROSOR["borde_globo"]), opacity=OPACIDAD["borde_apoyo"])
    g = VGroup(forma, t)
    g.forma, g.texto = forma, t
    return g


def estacion(cadena: str, cx: float, cy: float) -> VGroup:
    """Una estación del aro: el verbo a 60 px en una pastilla de fondo tinta opaco y borde azul. El
    fondo va aparte del borde para que el Foco de D08.3 no lo vuelva transparente."""
    t = Texto(cadena, cx, cy, tam="lectura", alinear="centro")
    w, h = t.avance + 2 * ESTACION["aire"], ESTACION["alto"]
    fondo = rect_borde(cx, cy, w, h, h / 2, 0.01, color=TINTA, relleno=TINTA, opacidad_relleno=1)
    fondo.set_stroke(width=0)
    borde = rect_borde(cx, cy, w, h, h / 2, GROSOR["borde"], color=AZUL)
    g = VGroup(fondo, borde, t)
    g.fondo, g.borde, g.texto, g.ancho = fondo, borde, t, w
    g.set_z_index(Z_ROTULO)
    return g


class D08Pensar(DiapoCharla):
    ID = "D08"

    def construct(self):
        t1, t2, t3 = textos("D08", 1), textos("D08", 2), textos("D08", 3)
        self.add(fondo_circuito())

        # ---------------- Paso 1: un modelo solo ----------------
        self.paso(1)
        cerebro = icono("brain", CEREBRO["cx"], CEREBRO["cy"], CEREBRO["lado"])
        pensar = Texto(t1[0], X_TITULO, Y_TITULO, tam="grande", color=TITULO)
        frase1 = Texto(t1[1], X_FRASE, Y_FRASE, tam="lectura", partes=PARTES_FRASE1)
        modelo = nodo(NODO1["cx"], NODO1["cy"], NODO1["lado"], nombre_icono="brain")
        pregunta = globo(t1[2], PREGUNTA["cx"], PREGUNTA["cy"], HUESO, "der")
        w_resp = Texto(t1[3], 960, RESPUESTA["cy"], tam="lectura", alinear="centro").avance + 2 * GLOBO["aire"]
        respuesta = globo(t1[3], RESPUESTA["x0"] + w_resp / 2, RESPUESTA["cy"], GRIS, "izq")

        self.tocar(
            Entrar(cerebro, 0.0),
            Entrar(pensar, 0.08),
            Entrar(frase1, 0.22),
            Brotar(modelo, 0.35, 0.5, desde=0.8),
        )
        # La pregunta llega desde la derecha. El modelo piensa (late dos veces) y contesta.
        self.tocar(Entrar(pregunta, 0.0, 0.5, desde="der"))
        self.esperar(0.1)
        self.tocar(Latido(modelo, 0.0, 0.35, escala=1.05))
        self.tocar(Latido(modelo, 0.05, 0.35, escala=1.05))
        self.tocar(Brotar(respuesta, 0.05, 0.4, desde=0.85))

        # ---------------- Paso 2: el agente ----------------
        self.paso(2)
        frase2 = Texto(t2[0], X_FRASE, Y_FRASE, tam="lectura", partes=PARTES_FRASE2, resaltar="Agente")
        modelo2 = nodo(NODO2["cx"], NODO2["cy"], NODO2["lado"], nombre_icono="brain")
        aro = arco(0, 360)
        estaciones = [estacion(t2[1 + i], *en_elipse(a)) for i, a in enumerate(ANGULOS)]
        herramientas, rotulos_herr = [], []
        for i, (y, ic) in enumerate(zip(HERRAMIENTA["ys"], ICONOS_HERR)):
            herramientas.append(nodo(HERRAMIENTA["cx"], y, HERRAMIENTA["lado"], nombre_icono=ic))
            rotulos_herr.append(Texto(t2[5 + i], X_ROTULO_HERR, y, tam="rotulo"))
        memoria = nodo(MEMORIA["cx"], MEMORIA["cy"], MEMORIA["lado"], nombre_icono="memory")
        rot_memoria = Texto(t2[8], X_ROTULO_HERR, MEMORIA["cy"], tam="rotulo")
        # Las líneas a trazos: de la estación elige a cada herramienta, y del aro a la memoria.
        elige = estaciones[1]
        x_elige = ELIPSE["cx"] + ELIPSE["a"] + elige.ancho / 2
        izq_herr = HERRAMIENTA["cx"] - HERRAMIENTA["lado"] / 2
        abanico = [a_trazos(x_elige, ELIPSE["cy"], izq_herr, y) for y in HERRAMIENTA["ys"]]
        mx, my = en_elipse(ANGULO_MEMORIA)
        a_memoria = a_trazos(mx, my, MEMORIA["cx"] - MEMORIA["lado"] / 2, MEMORIA["cy"])
        # Un puerto (un punto azul) donde nacen las líneas: sin él, las tres se juntaban en una mancha.
        puertos = [Dot(punto(x_elige, ELIPSE["cy"]), radius=u(PUERTO_RADIO), color=AZUL), Dot(punto(mx, my), radius=u(PUERTO_RADIO), color=AZUL)]
        for pu in puertos:
            pu.set_fill(AZUL, opacity=1).set_stroke(width=0)
            pu.set_z_index(Z_ROTULO + 0.5)
        grupos_herr = [VGroup(h, r) for h, r in zip(herramientas, rotulos_herr)]
        grupo_mem = VGroup(memoria, rot_memoria)

        # La pregunta y la respuesta se van, la frase cambia y la cámara se aleja un poco. La frase, en
        # orden: el resto de la primera se va antes de que modelo viaje (si no, se leía modelosolo).
        self.tocar(
            Desvanecer(VGroup(pregunta, respuesta), 0.0, 0.3),
            TransformarEnOrden(frase1, frase2, 0.0, FRASE_EN_ORDEN["dura"], FRASE_EN_ORDEN["sale"], FRASE_EN_ORDEN["viaja"]),
            Mover(modelo, modelo2, 0.0, 0.6),
        )
        # El aro se dibuja desde arriba, en el sentido de las agujas del reloj, y cada estación aparece
        # cuando el trazo llega a ella. Después entran las herramientas, la memoria y sus líneas.
        d_aro = 0.7
        self.tocar(
            Trazo(aro, 0.0, d_aro),
            *[Brotar(e, max(0.0, instante("suave", a / 360) * d_aro - 0.05), 0.3, desde=0.8)
              for e, a in zip(estaciones, ANGULOS)],
            *[Entrar(g, 0.55 + 0.12 * i, 0.5, desde="der") for i, g in enumerate(grupos_herr)],
            Entrar(grupo_mem, 0.91, 0.5, desde="der"),
            *[Trazo(ab, 0.75 + 0.08 * i, 0.35) for i, ab in enumerate(abanico)],
            Trazo(a_memoria, 1.0, 0.35),
            Aparecer(puertos[0], 0.7, 0.2),
            Aparecer(puertos[1], 0.95, 0.2),
        )

        # La vuelta del agente: el punto (detrás de las estaciones) piensa, elige, va a Mapas, vuelve,
        # mira y responde.
        pd = dato(*en_elipse(0))
        self.add(pd)
        piensa, _, mira, responde = estaciones
        mapas = herramientas[0]
        y_mapas = HERRAMIENTA["ys"][0]
        # Cuando elige late, la línea a Mapas se enciende en ámbar y las otras herramientas bajan:
        # desde el fondo de la sala se ve cuál eligió.
        elegida = linea(x_elige, ELIPSE["cy"], izq_herr, y_mapas, grosor=ELEGIDA["grosor"], color=AMBAR)
        elegida.set_z_index(Z_ELEGIDA)
        otras = VGroup(*grupos_herr[1:], grupo_mem, *abanico[1:], a_memoria, puertos[1])
        brillo_mapas = brillo_nodo(mapas)
        self.tocar(Latido(piensa, 0.0, 0.3))
        self.tocar(
            Recorrer(pd, arco(0, 90), 0.0, 0.5),
            Latido(elige, 0.35, 0.3),
            Trazo(elegida, 0.35, 0.4),
            Bajar(otras, ELEGIDA["otras"], 0.35, 0.4),
        )
        # La línea ámbar (6 px) tapa entera a la de trazos (5 px): la de trazos sale, así en D08.3, con
        # todo al 25 %, no asoma rayada debajo de la ámbar.
        self.remove(abanico[0])
        ida = camino([(ELIPSE["cx"] + ELIPSE["a"], ELIPSE["cy"]), (x_elige, ELIPSE["cy"]), (izq_herr, y_mapas),
                      (HERRAMIENTA["cx"], y_mapas)])
        vuelta = camino([(HERRAMIENTA["cx"], y_mapas), (izq_herr, y_mapas), (x_elige, ELIPSE["cy"]),
                         (ELIPSE["cx"] + ELIPSE["a"], ELIPSE["cy"])])
        self.tocar(Recorrer(pd, ida, 0.0, 0.35), Latido(mapas, 0.2, 0.3))
        # El nodo entero se transforma (no solo su caja): si se anima la caja sola, Manim la vuelve a
        # poner encima del ícono y el ícono desaparece.
        mapas_ambar = mapas.copy()
        mapas_ambar.caja.set_stroke(AMBAR)
        self.tocar(Recorrer(pd, vuelta, 0.0, 0.35), Mover(mapas, mapas_ambar, 0.0, 0.25), Aparecer(brillo_mapas, 0.0, 0.3))
        self.tocar(Recorrer(pd, arco(90, 180), 0.0, 0.45), Latido(mira, 0.3, 0.3))
        self.tocar(Recorrer(pd, arco(180, 270), 0.0, 0.45), Latido(responde, 0.3, 0.3))
        self.remove(pd)

        # ---------------- Paso 3: él elige ----------------
        self.paso(3)
        frase3 = Texto(t3[0], 960, Y_FRASE, tam="frase", alinear="centro", partes=PARTES_FRASE3)
        # La tarjeta lleva el borde tenue de apoyo: explica por qué el aro y las líneas se cortan en su
        # contorno. Tapa el nodo y la estación elige enteros.
        tarjeta = rect_borde(TARJETA["cx"], TARJETA["cy"], TARJETA["ancho"], TARJETA["alto"], RADIO["tarjeta"],
                             GROSOR["borde"], color=HUESO, relleno=TINTA, opacidad_relleno=1)
        tarjeta.set_stroke(opacity=OPACIDAD["borde_apoyo"])
        tarjeta.set_z_index(Z_ROTULO + 1)
        final = Texto(t3[1], TARJETA["cx"], TARJETA["cy"], tam="idea", alinear="centro", resaltar="Él elige")
        final.set_z_index(Z_ROTULO + 2)
        # Lo que la tarjeta tapa entero (el nodo, la estación elige y su puerto) se va mientras la tarjeta
        # crece encima. Así nada asoma por los bordes y el auditor no lo ve encimado.
        tapados = VGroup(modelo, elige, puertos[0])
        # Todo lo demás queda detrás al 25 %: el aro, las estaciones, Mapas con su línea ámbar y su brillo
        # (que siguen marcando cuál eligió) y las otras herramientas, que ya estaban al 40 %.
        atras = VGroup(aro, *[VGroup(e.borde, e.texto) for e in estaciones if e is not elige], grupos_herr[0],
                       elegida, brillo_mapas)
        self.tocar(
            Bajar(atras, ATRAS, 0.0, 0.3),
            Bajar(otras, ATRAS / ELEGIDA["otras"], 0.0, 0.3),
            TransformarEnOrden(frase2, frase3, 0.05, FRASE_EN_ORDEN["dura"], FRASE_EN_ORDEN["sale"], FRASE_EN_ORDEN["viaja"]),
        )
        self.tocar(
            Desvanecer(tapados, 0.0, 0.2),
            Brotar(tarjeta, 0.0, 0.35, desde=0.92),
            Entrar(final, 0.12, 0.5),
        )
