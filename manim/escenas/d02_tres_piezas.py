"""D02 Las tres piezas: la diapositiva de prueba del armado en Manim (13-nov-2026).

Manim para mostrar cómo fluye algo: tres nodos (n8n, SerpApi, IA) que se conectan, y un dato que
los recorre. Sirve de plantilla: textos tal cual de deck.json (textos), todo en px del cuadro,
tiempos con tocar() dentro de cada paso y los tonos del afiche (NOCHE para el relleno de los nodos,
AZUL para bordes y conexiones). El dato que viaja va en ámbar: es lo que hay que seguir con la vista
(como mucho dos cosas en ámbar por cuadro).

    <python del entorno> manim/render_diapo.py D02

Entra con un fundido desde D01 (deck.json, entrada): el paso 1 propio dura 3,0 - 0,4 = 2,6 s y
arranca en tinta. Cuadro final de los dos pasos: tres nodos de 460 x 200 (borde azul de 5 px hacia
adentro, radio 28, relleno noche) centrados en x 340, 960 y 1580, y 540, con su nombre en hueso a
88 px, y dos conexiones azules de 5 px entre ellos. La marca de agua la pone la base.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comun"))

from charla import (  # noqa: E402
    AMBAR, AZUL, GROSOR, NOCHE, RADIO, Desplazar, Desvanecer, DiapoCharla, Entrar, Latido, Texto, Trazo, linea,
    punto, rect_borde, textos, u,
)
from manim import Dot, VGroup  # noqa: E402

CX = [340, 960, 1580]
CY = 540
ANCHO, ALTO = 460, 200
TAM = "idea"  # 88 px
DATO_RADIO = 14  # px


def nodo(nombre: str, cx: float) -> VGroup:
    caja = rect_borde(cx, CY, ANCHO, ALTO, RADIO["tarjeta"], GROSOR["borde"], color=AZUL, relleno=NOCHE, opacidad_relleno=1)
    texto = Texto(nombre, cx, CY, tam=TAM, alinear="centro")
    return VGroup(caja, texto)


def conexion(i: int):
    """La conexión entre el nodo i y el i+1, de borde a borde."""
    x0 = CX[i] + ANCHO / 2
    x1 = CX[i + 1] - ANCHO / 2
    return linea(x0, CY, x1, CY, grosor=GROSOR["trazo_normal"], color=AZUL, conector=True), x0, x1


def dato(x: float) -> Dot:
    d = Dot(punto(x, CY), radius=u(DATO_RADIO), color=AMBAR)
    d.set_fill(AMBAR, opacity=1)
    return d


class D02TresPiezas(DiapoCharla):
    ID = "D02"

    def construct(self):
        # ---- Paso 1: los tres nodos entran de a uno y se conectan (todo antes de los 2,3 s) ----
        t = textos("D02", 1)  # ["n8n", "SerpApi", "IA"]
        self.paso(1)
        nodos = [nodo(nombre, cx) for nombre, cx in zip(t, CX)]
        conexiones = [conexion(i) for i in range(2)]
        self.tocar(
            *[Entrar(n, 0.1 + 0.25 * i) for i, n in enumerate(nodos)],         # termina a los 1,1 s
            *[Trazo(c[0], 1.0 + 0.3 * i, 0.4) for i, c in enumerate(conexiones)],  # termina a los 1,7 s
        )

        # ---- Paso 2: un dato recorre el flujo y cada nodo late al recibirlo ----
        self.paso(2)
        (_, a0, a1), (_, b0, b1) = conexiones
        d1, d2 = dato(a0), dato(b0)
        self.tocar(
            Desplazar(d1, a1 - a0, 0, 0.0, 0.5, curva="suave", aparece=0.3),
            Latido(nodos[1], 0.45, 0.4),
        )
        self.tocar(
            Desvanecer(d1, 0.0, 0.2),
            Desplazar(d2, b1 - b0, 0, 0.1, 0.5, curva="suave", aparece=0.3),
            Latido(nodos[2], 0.55, 0.4),
        )
        self.tocar(Desvanecer(d2, 0.0, 0.2))                                  # todo termina a los 2,0 s
