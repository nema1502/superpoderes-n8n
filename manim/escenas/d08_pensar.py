"""D08 Segundo superpoder: pensar (guion: contenido/guion.md, D08).

Un modelo solo sabe lo que leyó: se le pregunta qué café está abierto ahora, piensa (late dos
veces) y responde que no lo puede saber. Después la cámara se aleja un poco y aparece el agente:
el mismo nodo con un aro de cuatro estaciones (piensa, elige, mira, responde), tres herramientas y
la memoria unidas a trazos. Un punto ámbar da la vuelta: piensa, elige, sale hasta Mapas (que se
enciende), vuelve, mira y responde. Al final, el agente queda atrás y al frente: Él elige cuál usar.

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
  herramientas) y va en tinta con borde en hueso al 40 %. Las estaciones guardan su fondo opaco en
  el Foco: al 60 % se veía el aro por detrás.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from charla import (  # noqa: E402
    AMBAR, AZUL, GRIS, GROSOR, HUESO, OPACIDAD, RADIO, TINTA, TITULO, Desvanecer, DiapoCharla, Entrar, Foco,
    Latido, Mover, Texto, TransformarPorPartes, Trazo, punto, rect_borde, textos, trazo,
)
from d05_que_es_un_flujo import (  # noqa: E402
    fondo_circuito,
    Z_NODO, Z_ROTULO, Brotar, Recorrer, a_trazos, camino, dato, icono, instante, nodo,
)
from charla import Aparecer, u  # noqa: E402
from manim import Dot, VGroup, VMobject  # noqa: E402

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

# ---- Paso 3 ----
PARTES_FRASE3 = ["Vos le das las ", "herramientas", "."]
TARJETA = {"cx": 960, "cy": 600, "ancho": 900, "alto": 260}


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

        # La pregunta y la respuesta se van, la frase cambia y la cámara se aleja un poco.
        self.tocar(
            Desvanecer(VGroup(pregunta, respuesta), 0.0, 0.3),
            TransformarPorPartes(frase1, frase2, 0.05, 0.55),
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
        self.tocar(Latido(piensa, 0.0, 0.3))
        self.tocar(Recorrer(pd, arco(0, 90), 0.0, 0.5), Latido(elige, 0.35, 0.3))
        y_mapas = HERRAMIENTA["ys"][0]
        ida = camino([(ELIPSE["cx"] + ELIPSE["a"], ELIPSE["cy"]), (x_elige, ELIPSE["cy"]), (izq_herr, y_mapas),
                      (HERRAMIENTA["cx"], y_mapas)])
        vuelta = camino([(HERRAMIENTA["cx"], y_mapas), (izq_herr, y_mapas), (x_elige, ELIPSE["cy"]),
                         (ELIPSE["cx"] + ELIPSE["a"], ELIPSE["cy"])])
        self.tocar(Recorrer(pd, ida, 0.0, 0.35), Latido(mapas, 0.2, 0.3))
        # El nodo entero se transforma (no solo su caja): si se anima la caja sola, Manim la vuelve a
        # poner encima del ícono y el ícono desaparece.
        mapas_ambar = mapas.copy()
        mapas_ambar.caja.set_stroke(AMBAR)
        self.tocar(Recorrer(pd, vuelta, 0.0, 0.35), Mover(mapas, mapas_ambar, 0.0, 0.25))
        self.tocar(Recorrer(pd, arco(90, 180), 0.0, 0.45), Latido(mira, 0.3, 0.3))
        self.tocar(Recorrer(pd, arco(180, 270), 0.0, 0.45), Latido(responde, 0.3, 0.3))
        self.remove(pd)

        # ---------------- Paso 3: él elige ----------------
        self.paso(3)
        frase3 = Texto(t3[0], 960, Y_FRASE, tam="frase", alinear="centro", partes=PARTES_FRASE3)
        tarjeta = rect_borde(TARJETA["cx"], TARJETA["cy"], TARJETA["ancho"], TARJETA["alto"], RADIO["tarjeta"],
                             GROSOR["borde"], color=HUESO, relleno=TINTA, opacidad_relleno=1)
        tarjeta.set_stroke(opacity=OPACIDAD["borde_apoyo"])
        tarjeta.set_z_index(Z_ROTULO + 1)
        final = Texto(t3[1], TARJETA["cx"], TARJETA["cy"], tam="idea", alinear="centro", resaltar="Él elige")
        final.set_z_index(Z_ROTULO + 2)
        # Mapas vuelve a azul y baja al 60 % como el resto (un solo tramo para el nodo entero).
        mapas_azul = mapas.copy()
        mapas_azul.caja.set_stroke(AZUL, opacity=OPACIDAD["foco_hueso"]).set_fill(opacity=OPACIDAD["foco_hueso"])
        mapas_azul.icono.set_fill(opacity=OPACIDAD["foco_hueso"])
        # Lo que la tarjeta tapa entero (el nodo, la estación elige y su puerto) no baja al 60 %: se va
        # mientras la tarjeta crece encima. Así nada asoma por los bordes y el auditor no lo ve encimado.
        tapados = VGroup(modelo, elige, puertos[0])
        atras = VGroup(aro, *[VGroup(e.borde, e.texto) for e in estaciones if e is not elige], rotulos_herr[0],
                       *grupos_herr[1:], grupo_mem, *abanico, a_memoria, puertos[1])
        self.tocar(
            Foco(atras, 0.0),
            Mover(mapas, mapas_azul, 0.0, 0.3),
            TransformarPorPartes(frase2, frase3, 0.05, 0.55),
        )
        self.tocar(
            Desvanecer(tapados, 0.0, 0.2),
            Brotar(tarjeta, 0.0, 0.35, desde=0.92),
            Entrar(final, 0.12, 0.5),
        )
