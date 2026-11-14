# El fondo de la charla: un cielo de estrellas muy tenue y las pistas de circuito de la portada (D01),
# para que todas las diapositivas parezcan el mismo lugar. Sale un PNG opaco de 1920 x 1080 sobre
# tinta, el mismo para Remotion (<Img> en 0, 0, debajo de todo) y para Manim (imagen_en en 0, 0, debajo
# de todo), así las dos se ven idénticas.
#
# Las pistas son como las de D01: tramos rectos y a 45 grados, trazo de 3 px, un punto de 10 px en la
# punta de adentro, en azul. Entran desde los bordes y se apagan antes de salir de la zona segura
# (x 67 a 1853, y 38 a 1042): fuera de ella el fondo queda en tinta lisa, así el auditor de cuadros
# no ve nada en los márgenes ni en las esquinas. Evitan la marca de agua (arriba a la izquierda).
# En el codo de seis de ellas hay una vía: un aro de 14 px con trazo de 3 px y el centro vacío.
#
# Las estrellas (170, semilla fija): 160 tenues y 10 brillantes, tres de cada cuatro en la franja de
# afuera. Ninguna cae donde alguna diapositiva tiene contenido en su cuadro final (zonas_contenido.png,
# la unión de todos los cortes del 14-nov contra el fondo anterior), ni cerca de una pista, ni en la
# marca de agua. Las del centro no pasan del 30 %, así nunca compiten con el texto.
#
# Salen tres archivos: fondo_circuito.png (estrellas y pistas), fondo_estrellas.png (las mismas
# estrellas, para la portada, que dibuja sus propias pistas) y remotion/src/comun/pistasFondo.generado.ts
# (las polilíneas, para que los destellos de FondoVivo recorran las mismas pistas).
# Sin resplandores ni degradés: hacen bandas en el video.
#
# Correr con el Python de la charla: PYTHONUTF8=1 python diseno/medios/D01/generar_fondo.py
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
ANCHO, ALTO = 1920, 1080
SS = 4  # sobremuestreo para el antialias
TINTA = (0x07, 0x0A, 0x0F)
AZUL = (0x4D, 0xA3, 0xFF)
HUESO = (0xF5, 0xF7, 0xFF)
ALFA = 0.32  # opacidad de las pistas (en D01 quedan al 35 %: acá son el fondo)
ZONA = (67, 38, 1853, 1042)  # zona segura
RAMPA = 30  # px hacia adentro de la zona segura en los que la pista pasa de apagada a su opacidad
TRAZO = 3
PUNTO = 10
VIA = 14  # diámetro exterior del aro de una vía
SEMILLA = 14

# Cada pista: su lado y la lista de puntos (el primero fuera del cuadro o en el borde, el último es la
# punta con el punto). Tramos rectos y a 45 grados. `via`: el índice del codo que lleva vía.
PISTAS = [
    # Borde derecho
    {"lado": "der", "pts": [(1990, 160), (1820, 160), (1760, 100), (1560, 100)], "via": 1},
    {"lado": "der", "pts": [(1990, 300), (1865, 300), (1825, 340), (1825, 480)]},
    {"lado": "der", "pts": [(1990, 600), (1865, 600), (1825, 640), (1825, 760)], "via": 2},
    {"lado": "der", "pts": [(1990, 870), (1880, 870), (1820, 930), (1650, 930)]},
    {"lado": "der", "pts": [(1990, 1000), (1720, 1000)]},
    # Borde izquierdo (por debajo de la marca de agua)
    {"lado": "izq", "pts": [(-70, 250), (55, 250), (95, 290), (95, 440)], "via": 2},
    {"lado": "izq", "pts": [(-70, 560), (55, 560), (95, 600), (95, 720)]},
    {"lado": "izq", "pts": [(-70, 860), (40, 860), (100, 920), (300, 920)], "via": 2},
    {"lado": "izq", "pts": [(-70, 1000), (250, 1000)]},
    # Borde de arriba (a la derecha de la marca de agua)
    {"lado": "arriba", "pts": [(980, -70), (980, 40), (1020, 80), (1220, 80)], "via": 2},
    {"lado": "arriba", "pts": [(560, -70), (560, 45), (600, 85), (720, 85)]},
    # Las cinco del 14-nov, todas en la franja de afuera (más no entran sin pisar contenido o sin
    # quedar en la rampa del borde, donde no se verían)
    {"lado": "arriba", "pts": [(1300, -70), (1300, 45), (1340, 85), (1470, 85)], "via": 2},
    {"lado": "arriba", "pts": [(790, -70), (790, 45), (825, 80), (900, 80)]},
    {"lado": "arriba", "pts": [(440, -70), (440, 40), (475, 75), (500, 75)]},
    {"lado": "der", "pts": [(1990, 240), (1800, 240)]},
    {"lado": "der", "pts": [(1990, 815), (1790, 815)]},
]

# Las estrellas.
N_TENUES, N_BRILLANTES = 160, 10
FRACCION_FRANJA = 0.75
FRANJA = {"x0": 300, "x1": 1620, "y0": 180, "y1": 880}  # afuera: x < x0 o x > x1, o y < y0 o y > y1
ALFA_CENTRO = 0.30
MARCA = (30, 0, 380, 140)  # la marca de agua, con margen
LEJOS_PISTA = 12
LEJOS_CONTENIDO = 12


def en_franja(x, y):
    return x < FRANJA["x0"] or x > FRANJA["x1"] or y < FRANJA["y0"] or y > FRANJA["y1"]


def mascara_pistas() -> np.ndarray:
    """Las pistas en blanco sobre negro, a tamaño final, con antialias."""
    img = Image.new("L", (ANCHO * SS, ALTO * SS), 0)
    d = ImageDraw.Draw(img)
    for q in PISTAS:
        p = [(x * SS, y * SS) for x, y in q["pts"]]
        d.line(p, fill=255, width=TRAZO * SS, joint="curve")
        x, y = p[-1]
        r = PUNTO / 2 * SS
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        if "via" in q:
            x, y = p[q["via"]]
            ro = VIA / 2 * SS
            ri = (VIA / 2 - TRAZO) * SS
            d.ellipse([x - ro, y - ro, x + ro, y + ro], fill=255)
            d.ellipse([x - ri, y - ri, x + ri, y + ri], fill=0)
    img = img.resize((ANCHO, ALTO), Image.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def rampa() -> np.ndarray:
    """De 0 en el borde de la zona segura a 1 a RAMPA px hacia adentro (0 fuera)."""
    xs = np.arange(ANCHO) + 0.5
    ys = np.arange(ALTO) + 0.5
    x0, y0, x1, y1 = ZONA
    dx = np.minimum(xs - x0, x1 - xs)
    dy = np.minimum(ys - y0, y1 - ys)
    d = np.minimum(dx[None, :], dy[:, None])
    return np.clip(d / RAMPA, 0.0, 1.0)


def distancia_a_pistas(x, y) -> float:
    mejor = 1e9
    for q in PISTAS:
        pts = q["pts"]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            vx, vy = x1 - x0, y1 - y0
            l2 = vx * vx + vy * vy
            t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / l2))
            mejor = min(mejor, np.hypot(x - (x0 + t * vx), y - (y0 + t * vy)))
        mejor = min(mejor, np.hypot(x - pts[-1][0], y - pts[-1][1]) - PUNTO / 2)
    return mejor


def estrellas(contenido: np.ndarray):
    """170 estrellas: (x, y, alfa, sigma, brillante). Rechazo con semilla fija."""
    rng = np.random.default_rng(SEMILLA)
    x0, y0, x1, y1 = ZONA
    margen = 6

    def libre(x, y):
        if not (x0 + margen <= x <= x1 - margen and y0 + margen <= y <= y1 - margen):
            return False
        if MARCA[0] <= x <= MARCA[2] and MARCA[1] <= y <= MARCA[3]:
            return False
        if distancia_a_pistas(x, y) < LEJOS_PISTA:
            return False
        xi, yi = int(x), int(y)
        r = LEJOS_CONTENIDO
        if contenido[max(0, yi - r):yi + r + 1, max(0, xi - r):xi + r + 1].any():
            return False
        return True

    out = []
    total_franja = round((N_TENUES + N_BRILLANTES) * FRACCION_FRANJA)  # 128 de 170
    pedidos = [("brillante", N_BRILLANTES), ("franja", total_franja - N_BRILLANTES), ("centro", N_TENUES + N_BRILLANTES - total_franja)]
    faltan = {}
    for tipo, n in pedidos:
        puestos = 0
        intentos = 0
        while puestos < n and intentos < 200000:
            intentos += 1
            x = rng.uniform(x0, x1)
            y = rng.uniform(y0, y1)
            if tipo in ("brillante", "franja") and not en_franja(x, y):
                continue
            if tipo == "centro" and en_franja(x, y):
                continue
            if not libre(x, y):
                continue
            if any(np.hypot(x - e[0], y - e[1]) < (40 if tipo == "brillante" or e[4] else 14) for e in out):
                continue
            if tipo == "brillante":
                out.append((x, y, 0.80, 1.0, True))
            elif tipo == "franja":
                out.append((x, y, rng.uniform(0.25, 0.60), rng.uniform(0.8, 1.4), False))
            else:
                out.append((x, y, rng.uniform(0.20, ALFA_CENTRO), rng.uniform(0.8, 1.2), False))
            puestos += 1
        faltan[tipo] = n - puestos
    return out, faltan


def capa_estrellas(lista) -> np.ndarray:
    """Alfa de hueso de las estrellas (gaussianas; las brillantes con núcleo y halo)."""
    a = np.zeros((ALTO, ANCHO), dtype=np.float64)
    for x, y, alfa, sigma, brillante in lista:
        capas = [(alfa, sigma)] + ([(0.25, 3.0)] if brillante else [])
        for k, sg in capas:
            r = int(np.ceil(4 * sg))
            xi, yi = int(round(x)), int(round(y))
            xs = np.arange(xi - r, xi + r + 1)
            ys = np.arange(yi - r, yi + r + 1)
            g = np.exp(-(((xs[None, :] - x) ** 2) + ((ys[:, None] - y) ** 2)) / (2 * sg * sg))
            sub = a[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
            # Suma de luz (1 - (1 - a)(1 - b)), así el núcleo y el halo no pasan de 1.
            sub[:] = 1 - (1 - sub) * (1 - k * g)
    return a


def componer(a_pistas, a_estrellas) -> Image.Image:
    tinta = np.array(TINTA, dtype=np.float64)
    azul = np.array(AZUL, dtype=np.float64)
    hueso = np.array(HUESO, dtype=np.float64)
    rgb = tinta[None, None, :] + a_pistas[:, :, None] * (azul - tinta)[None, None, :]
    rgb = rgb + a_estrellas[:, :, None] * (hueso[None, None, :] - rgb)
    return Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), "RGB")


def ts_pistas() -> str:
    filas = []
    for q in PISTAS:
        pts = ", ".join(f"[{x}, {y}]" for x, y in q["pts"])
        filas.append(f'  {{ lado: "{q["lado"]}", pts: [{pts}] }},')
    return (
        "// Generado por diseno/medios/D01/generar_fondo.py. No editar a mano.\n"
        "// Las pistas del fondo: el primer punto en el borde o fuera del cuadro, el último es el punto.\n"
        'export const PISTAS_FONDO: { lado: "der" | "izq" | "arriba"; pts: [number, number][] }[] = [\n'
        + "\n".join(filas)
        + "\n];\n"
    )


def main():
    actual = AQUI / "fondo_circuito.png"
    v1 = AQUI / "fondo_circuito_v1.png"
    if actual.exists() and not v1.exists():
        shutil.copyfile(actual, v1)
        print("copia del fondo anterior:", v1)

    contenido = np.asarray(Image.open(AQUI / "zonas_contenido.png").convert("L")) > 127
    r = rampa()
    a_pistas = mascara_pistas() * r * ALFA
    lista, faltan = estrellas(contenido)
    a_estrellas = capa_estrellas(lista) * r
    # Nada de estrellas en la marca de agua ni pegado a una pista (por si un halo se estira).
    m = MARCA
    a_estrellas[m[1]:m[3], m[0]:m[2]] = 0

    componer(a_pistas, a_estrellas).save(actual, optimize=True)
    componer(np.zeros_like(a_pistas), a_estrellas).save(AQUI / "fondo_estrellas.png", optimize=True)
    ts = RAIZ / "remotion" / "src" / "comun" / "pistasFondo.generado.ts"
    ts.write_text(ts_pistas(), encoding="utf-8", newline="\n")

    n_fr = sum(1 for e in lista if en_franja(e[0], e[1]))
    n_br = sum(1 for e in lista if e[4])
    cen = [e for e in lista if not en_franja(e[0], e[1])]
    print(json.dumps({
        "pistas": len(PISTAS),
        "estrellas": len(lista),
        "en_franja": n_fr,
        "brillantes": n_br,
        "centro": len(cen),
        "alfa_max_centro": round(max((e[2] for e in cen), default=0), 3),
        "faltan": faltan,
    }, ensure_ascii=False))
    for f in (actual, AQUI / "fondo_estrellas.png", ts):
        print(f, f.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
