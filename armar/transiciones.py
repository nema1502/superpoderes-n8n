"""Transiciones de respaldo (cuando no existe remotion/transicion.mjs).

Cada transición va del último cuadro de una diapositiva (A) al primero de la
siguiente (B): el cuadro 0 es A y el cuadro N es B, como los pasos, que se solapan
en un cuadro. Se dibujan directo en yuv420p (BT.709 de rango limitado) para no
tocar A ni B fuera de lo que se mueve, y se codifican con la receta.

- fundido: mezcla lineal de A a B (0,4 s por defecto).
- puertas: las puertas de capítulo del guion (sistema visual): dos paneles de
  acero (#1A2230 a #2A3446) de 960x1080 entran desde los costados y se juntan en
  0,45 s (inOut cúbica) con una línea de luz ámbar de 4 px en la junta; quedan
  cerradas 0,1 s; se abren en 0,5 s (out cúbica) y descubren B. La versión de
  Remotion deja además la marca de agua por encima; esta no puede (A y B ya la
  traen pintada debajo).
"""

from __future__ import annotations

import numpy as np

from deck import ALTO, ANCHO, FPS
from videos import planos

ACERO = np.array([0x1A, 0x22, 0x30], np.float32)
ACERO2 = np.array([0x2A, 0x34, 0x46], np.float32)
AMBAR = np.array([0xFF, 0xB5, 0x47], np.float32)
HUESO = np.array([0xF5, 0xF7, 0xFF], np.float32)

KR, KB = 0.2126, 0.0722
KG = 1 - KR - KB


def rgb_a_yuv(rgb: np.ndarray):
    """RGB float (0..255, alto x ancho x 3) -> Y, U, V de rango limitado BT.709 (U y V a mitad)."""
    r, g, b = (rgb[..., i] / 255.0 for i in range(3))
    ey = KR * r + KG * g + KB * b
    pb = (b - ey) / (2 * (1 - KB))
    pr = (r - ey) / (2 * (1 - KR))
    y = 16 + 219 * ey
    u = 128 + 224 * pb
    v = 128 + 224 * pr
    # 4:2:0: promedio de cada bloque de 2x2
    h, w = u.shape
    u = u.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))
    v = v.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))
    return y, u, v


def _juntar(y, u, v) -> bytes:
    f = lambda p: np.clip(np.rint(p), 0, 255).astype(np.uint8).tobytes()  # noqa: E731
    return f(y) + f(u) + f(v)


def fundido(a: bytes, b: bytes, n: int) -> list[bytes]:
    """n+1 cuadros: A, mezclas, B."""
    x = np.frombuffer(a, np.uint8).astype(np.float32)
    z = np.frombuffer(b, np.uint8).astype(np.float32)
    out = [a]
    for i in range(1, n):
        out.append(np.clip(np.rint(x + (z - x) * (i / n)), 0, 255).astype(np.uint8).tobytes())
    out.append(b)
    return out


def _in_out_cubica(p):
    p = min(max(p, 0.0), 1.0)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def _out_cubica(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def _panel_izquierdo() -> np.ndarray:
    """Textura RGB (alto x 960) del panel izquierdo; el borde derecho es la junta."""
    w = ANCHO // 2
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    yv = np.linspace(0, 1, ALTO, dtype=np.float32)[:, None, None]
    base = ACERO + (ACERO2 - ACERO) * (0.35 + 0.65 * x)          # más claro hacia la junta
    base = base + (yv - 0.5) * -6.0                               # luz que baja apenas desde arriba
    tex = np.broadcast_to(base, (ALTO, w, 3)).copy()
    # brillos verticales al 15 % (acero cepillado), deterministas
    for cx, ancho, alfa in [(180, 3, 0.10), (420, 2, 0.08), (610, 4, 0.12), (860, 2, 0.15)]:
        sl = slice(cx - ancho // 2, cx + (ancho + 1) // 2)
        tex[:, sl, :] = tex[:, sl, :] * (1 - alfa) + HUESO * alfa
    # bisel oscuro en el borde exterior y uno claro junto a la junta
    tex[:, :6, :] *= 0.75
    tex[:, w - 10:w - 2, :] = tex[:, w - 10:w - 2, :] * 0.8 + HUESO * 0.06
    return tex


_TEX = None


def _texturas():
    """(panel izq. sin luz, panel izq. con la luz ámbar en la junta), en RGB."""
    global _TEX
    if _TEX is None:
        izq = _panel_izquierdo()
        w = izq.shape[1]
        luz = izq.copy()
        d = (w - 1 - np.arange(w, dtype=np.float32))[None, :, None]   # distancia a la junta, en px
        brillo = np.exp(-d / 14.0) * 0.45                               # resplandor sobre el acero
        luz = luz * (1 - brillo) + AMBAR * brillo
        luz[:, w - 2:, :] = AMBAR                                       # 2 px por panel: 4 px de luz al cerrar
        _TEX = (izq, luz)
    return _TEX


def puertas(a: bytes, b: bytes, n: int, cerrar=0.45, quietas=0.10, abrir=0.50) -> list[bytes]:
    """n+1 cuadros: A, las puertas se cierran sobre A, quedan, se abren sobre B, B."""
    izq, luz = _texturas()
    total = cerrar + quietas + abrir
    escala = (n / FPS) / total          # los tiempos del guion, estirados al largo en cuadros
    t_c, t_q = cerrar * escala, (cerrar + quietas) * escala
    t_a = total * escala
    ya, ua, va = (p.astype(np.float32) for p in planos(a))
    yb, ub, vb = (p.astype(np.float32) for p in planos(b))
    w = ANCHO // 2
    out = [a]
    for i in range(1, n):
        t = i / FPS
        if t <= t_c:
            cierre = _in_out_cubica(t / t_c)
        elif t <= t_q:
            cierre = 1.0
        else:
            cierre = 1 - _out_cubica((t - t_q) / (t_a - t_q))
        # intensidad de la línea de luz: aparece al juntarse y se va al abrirse
        if t <= t_c:
            intensidad = max(0.0, (cierre - 0.7) / 0.3)
        elif t <= t_q:
            intensidad = 1.0
        else:
            intensidad = max(0.0, 1 - (t - t_q) / ((t_a - t_q) * 0.35))
        # Hasta que las puertas se juntan se ve A detrás; cerradas, el fondo pasa a B.
        fondo = (ya, ua, va) if t <= t_c + 1e-9 else (yb, ub, vb)
        borde = cierre * w                      # x del borde interno del panel izquierdo (px, con decimales)
        if borde > w - 1:                       # a menos de un píxel de juntarse: juntas (sin rendija que deje ver el fondo)
            borde = float(w)
        desp = int(np.ceil(borde))              # columnas que toca cada panel
        if desp <= 0:
            out.append(_juntar(*fondo))
            continue
        tex = izq * (1 - intensidad) + luz * intensidad
        rgb = np.zeros((ALTO, ANCHO, 3), np.float32)
        rgb[:, :desp, :] = tex[:, w - desp:, :]                 # la junta queda pegada al borde
        rgb[:, ANCHO - desp:, :] = tex[:, w - desp:, :][:, ::-1, :]  # el derecho es el espejo
        # cobertura por columna, con antialias en el borde (el borde se mueve en fracciones de píxel)
        x = np.arange(ANCHO, dtype=np.float32)
        alfa = np.maximum(np.clip(borde - x, 0, 1), np.clip(borde - (ANCHO - 1 - x), 0, 1))
        yp, up, vp = rgb_a_yuv(rgb)
        al = alfa[None, :]
        al2 = alfa.reshape(-1, 2).mean(axis=1)[None, :]
        y = fondo[0] * (1 - al) + yp * al
        u = fondo[1] * (1 - al2) + up * al2
        v = fondo[2] * (1 - al2) + vp * al2
        out.append(_juntar(y, u, v))
    out.append(b)
    return out


def generar(tipo: str, a: bytes, b: bytes, n: int) -> list[bytes]:
    if tipo == "fundido":
        return fundido(a, b, n)
    if tipo == "puertas":
        return puertas(a, b, n)
    raise ValueError(f"transición desconocida: {tipo}")
