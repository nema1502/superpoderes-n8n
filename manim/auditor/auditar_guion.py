"""Verifica que un guion respondió LAS 7 PREGUNTAS antes de grabar.

No juzga si la respuesta es buena — eso es humano. Lo que garantiza es que
nadie las saltee sin darse cuenta, que es exactamente como se cuela un video
con un gancho flojo: no porque alguien decidiera ignorar la lista, sino porque
nadie la miró.

Uso:
    python auditor/auditar_guion.py chainlink/guiones/02_el_problema_del_oraculo.md
    python auditor/auditar_guion.py --todos
"""

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# El orden importa y es el de LISTA_7_PREGUNTAS.md. Se busca por una palabra
# clave de cada una, no por el texto exacto: así sobrevive a que se reescriba
# la pregunta sin cambiar el sentido.
PREGUNTAS = [
    ("se detendría",  "1 · ¿alguien se detendría? (el gancho)"),
    ("haría clic",    "2 · ¿alguien haría clic? (título y portada)"),
    ("vería",         "3 · ¿vería alguien el video? (retención)"),
    ("comentar",      "4 · ¿querrán comentar?"),
    ("satisfech",     "5 · ¿estarán satisfechos? (la promesa se cumple)"),
    ("volverían",     "6 · ¿lo volverían a ver? (valor de guardado)"),
    ("suscrib",       "7 · ¿se suscribirán? (razón concreta para volver)"),
]

VEREDICTOS = ("sí", "si", "no", "dudoso")


def seccion_7(texto):
    """Devuelve el bloque de la sección de las 7 preguntas, o None."""
    m = re.search(r"^##+\s*Las 7 preguntas.*?$(.*?)(?=^##\s|\Z)",
                  texto, re.M | re.S | re.I)
    return m.group(1) if m else None


def auditar(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    fallos = []
    bloque = seccion_7(texto)
    if bloque is None:
        return ["falta la sección '## Las 7 preguntas' — ver LISTA_7_PREGUNTAS.md"]

    bajo = bloque.lower()
    for clave, nombre in PREGUNTAS:
        # la línea que menciona la pregunta
        linea = next((l for l in bloque.splitlines() if clave in l.lower()), None)
        if linea is None:
            fallos.append(f"no está respondida la pregunta {nombre}")
            continue
        resto = linea.lower().split(clave, 1)[1]
        if not any(v in resto for v in VEREDICTOS):
            fallos.append(f"la pregunta {nombre} no tiene veredicto "
                          f"(SÍ / NO / DUDOSO)")
        elif len(linea.strip()) < 40:
            fallos.append(f"la pregunta {nombre} tiene veredicto pero no "
                          f"explica por qué (menos de 40 caracteres)")

    if "no" in bajo and re.search(r"\|\s*no\s*\|", bajo):
        fallos.append("hay al menos un NO: el video no se graba todavía, "
                      "se arregla el guion primero")
    return fallos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("guion", nargs="?")
    ap.add_argument("--todos", action="store_true")
    args = ap.parse_args()

    rutas = (sorted(RAIZ.glob("*/guiones/*.md")) if args.todos
             else [Path(args.guion)])
    # planes de serie y plantillas no son videos: no se les exige la lista
    NO_SON_VIDEOS = ("_PUBLICACION", "plan_de_serie", "plantilla")
    rutas = [r for r in rutas
             if not any(x in r.name for x in NO_SON_VIDEOS)]
    if not rutas:
        raise SystemExit("no encontré guiones")

    total = 0
    for r in rutas:
        fallos = auditar(r)
        total += len(fallos)
        try:                    # un guion de prueba puede vivir fuera del repo
            nombre = r.relative_to(RAIZ)
        except ValueError:
            nombre = r
        print()
        print(f"== {nombre} ==")
        for f in fallos:
            print(f"  [ERROR] {f}")
        print(f"  -> {'RECHAZADO' if fallos else 'APROBADO'}: {len(fallos)} errores")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
