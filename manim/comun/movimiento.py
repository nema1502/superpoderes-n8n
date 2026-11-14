"""El movimiento del pitch de Tinkazo: cómo entran, golpean y festejan las cosas.

`estilo_tinkazo.py` dice cómo se ve la marca; esto dice cómo se mueve. Salió
del pedido de "más animado, más épico, más inesperado" (30 de septiembre de
2026), con tres reglas:

- **Todo es determinista.** El confeti sale de una semilla fija: el mismo
  render da el mismo video, como los juegos del sitio.
- **Lo que decora no se audita, lo que se lee sí.** La cortina, el confeti,
  las ondas y el brillo van marcados con `auditor_ignorar` y como objetos de
  primer nivel de la escena, que es lo que el auditor saltea. El texto que
  entra letra por letra sigue siendo un `Text` entero: si se lo partía en
  letras sueltas, el auditor dejaba de ver su tamaño y su contraste.
- **El último cuadro manda.** En una sala el público mira la diapositiva
  quieta mientras el orador habla: toda animación termina en un estado limpio,
  sin restos de confeti ni ondas.
"""

import numpy as np
from manim import (
    DOWN, LEFT, RIGHT, UP, TAU,
    Animation, Circle, Polygon, Rectangle, Square, VGroup, Wiggle, config, rate_functions,
)

# --- Lo único que cambió al copiarlo a la charla (22-oct-2026) ------------------
# Copiado del movimiento.py del pitch de Tinkazo (30-sep-2026).
# Allá estos cinco valores se importaban de `estilo_tinkazo.py`, la paleta del
# pitch de Tinkazo, un módulo que además trae la llama, el QR y la marca de
# Tinkazo. Para no arrastrar todo eso se copian acá con los MISMOS valores, así
# que el movimiento se comporta exactamente igual que en el pitch.
# Para la charla se cambian en un solo lugar, acá, por la paleta de la charla
# (fondo tinta #070A0F de estilo.NEMA_TINTA y el acento elegido; nunca el lima
# de la marca), o se pasan por argumento: Confeti(colores=...), Onda(color=...).
ACENTOS = ["#FF5CB3", "#FF8B3D", "#FFD24D", "#17C3B2", "#9B7BFF"]  # magenta, naranja, amarillo, turquesa, morado
AMARILLO = "#FFD24D"
FONDO = "#171126"
PAPEL = "#F6EFE2"
TINTA = "#191919"

ANCHO = config.frame_width
ALTO = config.frame_height


def _decorar(m, z=0):
    for x in m.get_family():
        x.auditor_ignorar = True
    m.auditor_ignorar = True
    if z:
        m.set_z_index(z)
    return m


# ---------------------------------------------------------------- cortina
# Cinco franjas del aguayo, en diagonal, que barren la pantalla de derecha a
# izquierda. Es el corte entre diapositivas: tapa lo viejo, deja lo nuevo.
_FRANJA = 3.5
_INCLINACION = 1.3


def cortina():
    g = VGroup()
    x0 = -_FRANJA * 2.5
    for i, color in enumerate([ACENTOS[k % len(ACENTOS)] for k in range(5)]):
        x = x0 + i * _FRANJA
        g.add(Polygon(
            [x, -ALTO / 2 - 0.3, 0], [x + _FRANJA + 0.02, -ALTO / 2 - 0.3, 0],
            [x + _FRANJA + 0.02 + _INCLINACION, ALTO / 2 + 0.3, 0], [x + _INCLINACION, ALTO / 2 + 0.3, 0],
            stroke_color=TINTA, stroke_width=6, fill_color=color, fill_opacity=1,
        ))
    return _decorar(g, z=60)


_ENTRA = _FRANJA * 5 + _INCLINACION + ANCHO / 2 - _FRANJA * 2.5 + 0.4   # desde tapar hasta afuera a la derecha
_SALE = _FRANJA * 2.5 + _INCLINACION + ANCHO / 2 + 0.4                  # desde tapar hasta afuera a la izquierda


def abrir(escena, tiempo=0.4):
    """La diapositiva arranca tapada por la cortina, y la cortina se va."""
    c = cortina()
    escena.add(c)
    escena.play(c.animate.shift(LEFT * _SALE), run_time=tiempo, rate_func=rate_functions.ease_in_cubic)
    escena.remove(c)


def barrer(escena, quitar, tiempo=0.34):
    """La cortina entra, se lleva lo que había y deja la pantalla limpia."""
    c = cortina().shift(RIGHT * _ENTRA)
    escena.add(c)
    escena.play(c.animate.shift(LEFT * _ENTRA), run_time=tiempo, rate_func=rate_functions.ease_out_cubic)
    for m in quitar:
        m.clear_updaters()
    escena.remove(*quitar)
    escena.play(c.animate.shift(LEFT * _SALE), run_time=tiempo, rate_func=rate_functions.ease_in_cubic)
    escena.remove(c)


# ---------------------------------------------------------------- fondo
def brillo(color, centro, radio=6.0, capas=14, opacidad=0.016):
    """Un resplandor suave detrás de todo: círculos apenas opacos, apilados."""
    g = VGroup(*[
        Circle(radius=radio * (1 - k / capas) + 0.3, stroke_width=0, fill_color=color, fill_opacity=opacidad)
        for k in range(capas)
    ]).move_to([centro[0], centro[1], 0])
    return _decorar(g, z=-10)


def ribete(ancho=None, alto=0.13, opacidad=0.55):
    """La guarda de abajo: rombos del aguayo sobre una banda, a juego con la
    tira de colores de arriba."""
    ancho = ancho or ANCHO + 0.2
    g = VGroup(Rectangle(width=ancho, height=alto, stroke_width=0, fill_color="#EFE4CF", fill_opacity=opacidad))
    lado = alto * 0.36
    paso = lado * 2.8
    x = -ancho / 2 + paso / 2
    while x < ancho / 2:
        g.add(Polygon([x, lado, 0], [x + lado, 0, 0], [x, -lado, 0], [x - lado, 0, 0],
                      stroke_width=0, fill_color=TINTA, fill_opacity=opacidad))
        x += paso
    g.move_to([0, -ALTO / 2 + alto / 2, 0])
    return _decorar(g, z=-5)


# ---------------------------------------------------------------- entradas
def _hojas(m):
    return [x for x in m.family_members_with_points()]


class _Anim(Animation):
    """Base de las animaciones propias. Manim le pasa a `interpolate_mobject`
    el avance crudo: sin la curva de aceleración y sin tope, así que cuando
    comparte un `play` con otra más larga pasa de 1 y se desborda. Acá se
    recorta y se le aplica la curva antes de dibujar."""

    def interpolate_mobject(self, alpha):
        self.paso(self.rate_func(min(1.0, max(0.0, alpha))))

    def paso(self, a):
        raise NotImplementedError


class Cascada(_Anim):
    """Las letras caen de a una y rebotan al asentarse. Anima el texto entero
    (no letras sueltas en la escena), así sigue siendo un `Text` para el
    auditor y para el `FadeOut` que venga después."""

    def __init__(self, m, cada=0.3, alto=0.45, **kw):
        # `cada`: qué parte del tiempo total tarda en asentarse cada letra.
        self.cada, self.alto = cada, alto
        n = max(1, len(_hojas(m)))
        kw.setdefault("run_time", min(1.3, 0.45 + 0.013 * n))
        kw.setdefault("rate_func", rate_functions.linear)
        super().__init__(m, **kw)

    def paso(self, alpha):
        hojas, bases = _hojas(self.mobject), _hojas(self.starting_mobject)
        n = len(hojas)
        for i, (h, b) in enumerate(zip(hojas, bases)):
            arranque = (i / (n - 1)) * (1 - self.cada) if n > 1 else 0.0
            a = min(1.0, max(0.0, (alpha - arranque) / self.cada))
            h.become(b)
            if a < 1:
                h.shift(UP * self.alto * (1 - rate_functions.ease_out_back(a)))
                h.set_fill(opacity=b.get_fill_opacity() * min(1.0, a * 2.5))
                h.set_stroke(opacity=b.get_stroke_opacity() * min(1.0, a * 2.5))


class Golpe(_Anim):
    """Un sello que cae desde grande y se asienta con rebote."""

    def __init__(self, m, desde=1.9, giro=0.12, **kw):
        self.desde, self.giro = desde, giro
        kw.setdefault("run_time", 0.42)
        kw.setdefault("rate_func", rate_functions.linear)
        super().__init__(m, **kw)

    def paso(self, alpha):
        self.mobject.become(self.starting_mobject)
        e = rate_functions.ease_out_back(alpha)
        esc = self.desde + (1 - self.desde) * e
        self.mobject.scale(max(0.05, esc))
        self.mobject.rotate(self.giro * (1 - e))
        for h, b in zip(_hojas(self.mobject), _hojas(self.starting_mobject)):
            h.set_fill(opacity=b.get_fill_opacity() * min(1.0, alpha * 3))
            h.set_stroke(opacity=b.get_stroke_opacity() * min(1.0, alpha * 3))


class Voltear(_Anim):
    """Una tarjeta que da vuelta, como un naipe: se estira de canto a entera."""

    def __init__(self, m, **kw):
        kw.setdefault("run_time", 0.45)
        kw.setdefault("rate_func", rate_functions.ease_out_back)
        super().__init__(m, **kw)

    def paso(self, alpha):
        self.mobject.become(self.starting_mobject)
        self.mobject.stretch(max(0.02, alpha), 0)
        for h, b in zip(_hojas(self.mobject), _hojas(self.starting_mobject)):
            h.set_fill(opacity=b.get_fill_opacity() * min(1.0, alpha * 2))
            h.set_stroke(opacity=b.get_stroke_opacity() * min(1.0, alpha * 2))


def sacudon(m, fuerza=1.0):
    """El sacudón después del golpe."""
    return Wiggle(m, scale_value=1 + 0.035 * fuerza, rotation_angle=0.02 * TAU * fuerza,
                  n_wiggles=3, run_time=0.32)


class Contador(_Anim):
    """Un número que corre hasta su valor, como un marcador."""

    def __init__(self, m, hacer, desde, hasta, formato=None, **kw):
        self.hacer, self.desde, self.hasta = hacer, desde, hasta
        self.formato = formato or (lambda v: str(int(round(v))))
        self.centro = m.get_center()
        kw.setdefault("run_time", 1.0)
        kw.setdefault("rate_func", rate_functions.ease_out_cubic)
        super().__init__(m, **kw)

    def paso(self, alpha):
        v = self.desde + (self.hasta - self.desde) * alpha
        self.mobject.become(self.hacer(self.formato(v)).move_to(self.centro))


# ---------------------------------------------------------------- festejos
class Confeti(_Anim):
    """Rombos y papelitos del aguayo que saltan y caen. Semilla fija."""

    def __init__(self, centro, n=36, semilla=1, colores=None, velocidad=(3.5, 7.5),
                 abanico=(0.12, 0.88), gravedad=10.0, tam=(0.08, 0.17), duracion=1.5, **kw):
        rng = np.random.default_rng(semilla)
        colores = colores or ACENTOS + [PAPEL]
        piezas = VGroup()
        self.datos = []
        for i in range(n):
            lado = rng.uniform(*tam)
            if i % 3 == 0:
                forma = Polygon([0, lado, 0], [lado * 0.7, 0, 0], [0, -lado, 0], [-lado * 0.7, 0, 0])
            else:
                forma = Rectangle(width=lado * 1.6, height=lado * 0.7)
            forma.set_stroke(width=0).set_fill(colores[i % len(colores)], opacity=1)
            forma.move_to([centro[0], centro[1], 0])
            piezas.add(forma)
            ang = rng.uniform(*abanico) * np.pi
            v = rng.uniform(*velocidad)
            self.datos.append((v * np.cos(ang), v * np.sin(ang), rng.uniform(-9, 9)))
        self.gravedad, self.T = gravedad, duracion
        _decorar(piezas, z=40)
        kw.setdefault("rate_func", rate_functions.linear)
        super().__init__(piezas, run_time=duracion, remover=True, **kw)

    def paso(self, alpha):
        t = alpha * self.T
        # Apagado del todo antes del final: el último cuadro de una
        # diapositiva es el que queda quieto mientras el orador habla, y si el
        # confeti seguía a medio apagar, quedaba pegado en pantalla.
        apagar = min(1.0, max(0.0, (0.9 - alpha) / 0.3))
        for h, b, (vx, vy, w) in zip(self.mobject, self.starting_mobject, self.datos):
            h.become(b)
            h.rotate(w * t)
            h.shift([vx * t, vy * t - 0.5 * self.gravedad * t * t, 0])
            h.set_fill(opacity=apagar)


class Onda(_Anim):
    """Un anillo que sale de un punto y se apaga: el faro que late."""

    def __init__(self, centro, radio=0.5, hasta=3.2, color=AMARILLO, grosor=6, **kw):
        anillo = Circle(radius=radio, stroke_color=color, stroke_width=grosor, fill_opacity=0)
        anillo.move_to([centro[0], centro[1], 0])
        self.hasta = hasta
        _decorar(anillo, z=5)
        kw.setdefault("run_time", 1.1)
        kw.setdefault("rate_func", rate_functions.ease_out_cubic)
        super().__init__(anillo, remover=True, **kw)

    def paso(self, alpha):
        self.mobject.become(self.starting_mobject)
        self.mobject.scale(1 + (self.hasta - 1) * alpha)
        self.mobject.set_stroke(opacity=max(0.0, 1 - alpha / 0.9))


class Destello(_Anim):
    """Un flash de cámara sobre toda la pantalla."""

    def __init__(self, color=PAPEL, fuerza=0.85, **kw):
        r = Rectangle(width=ANCHO + 0.4, height=ALTO + 0.4, stroke_width=0, fill_color=color, fill_opacity=0)
        _decorar(r, z=55)
        self.fuerza = fuerza
        kw.setdefault("run_time", 0.5)
        kw.setdefault("rate_func", rate_functions.linear)
        super().__init__(r, remover=True, **kw)

    def paso(self, alpha):
        self.mobject.set_fill(opacity=self.fuerza * (1 - alpha) ** 2)


class Viaje(_Anim):
    """Un punto de luz que recorre un camino: el dato que viaja de una caja a
    la otra."""

    def __init__(self, puntos, color=AMARILLO, lado=0.2, **kw):
        self.puntos = [np.array(p, dtype=float) for p in puntos]
        chispa = Square(side_length=lado, stroke_color=TINTA, stroke_width=3, fill_color=color, fill_opacity=1)
        chispa.rotate(TAU / 8).move_to(self.puntos[0])
        _decorar(chispa, z=30)
        kw.setdefault("run_time", 0.9)
        kw.setdefault("rate_func", rate_functions.ease_in_out_sine)
        super().__init__(chispa, remover=True, **kw)

    def paso(self, alpha):
        tramos = len(self.puntos) - 1
        x = alpha * tramos
        i = min(tramos - 1, int(x))
        f = x - i
        p = self.puntos[i] * (1 - f) + self.puntos[i + 1] * f
        self.mobject.become(self.starting_mobject).move_to(p)
        self.mobject.rotate(alpha * TAU)


def chispas(centro, n=6, radio=1.0, color=AMARILLO, semilla=3):
    """Estrellitas de cuatro puntas que aparecen y se van alrededor de algo."""
    rng = np.random.default_rng(semilla)
    anims = []
    for i in range(n):
        ang = TAU * i / n + rng.uniform(-0.3, 0.3)
        r = radio * rng.uniform(0.85, 1.25)
        p = np.array([centro[0] + r * np.cos(ang) * 1.6, centro[1] + r * np.sin(ang), 0])
        anims.append(Chispa(p, color=color, tam=rng.uniform(0.14, 0.26)))
    return anims


class Chispa(_Anim):
    def __init__(self, p, color=AMARILLO, tam=0.2, **kw):
        s = tam
        estrella = Polygon([0, s, 0], [s * 0.22, s * 0.22, 0], [s, 0, 0], [s * 0.22, -s * 0.22, 0],
                           [0, -s, 0], [-s * 0.22, -s * 0.22, 0], [-s, 0, 0], [-s * 0.22, s * 0.22, 0],
                           stroke_width=0, fill_color=color, fill_opacity=1).move_to(p)
        _decorar(estrella, z=35)
        kw.setdefault("run_time", 0.9)
        kw.setdefault("rate_func", rate_functions.linear)
        super().__init__(estrella, remover=True, **kw)

    def paso(self, alpha):
        self.mobject.become(self.starting_mobject)
        k = np.sin(np.pi * min(1.0, alpha / 0.88))
        self.mobject.scale(max(0.001, k * 1.2))
        if alpha >= 0.88:
            self.mobject.set_fill(opacity=0)
        self.mobject.rotate(alpha * TAU / 4)


def es_decoracion(m):
    return getattr(m, "auditor_ignorar", False)


__all__ = [
    "Cascada", "Golpe", "Voltear", "Contador", "Confeti", "Onda", "Destello", "Viaje", "Chispa",
    "abrir", "barrer", "brillo", "ribete", "sacudon", "chispas", "cortina", "es_decoracion",
    "DOWN", "FONDO",
]
