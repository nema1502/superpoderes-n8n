"""Auditor de sincronía: ¿la voz habla de lo que se está viendo?

Este es el auditor que faltaba. Los otros dos revisan la imagen y el sonido por
separado; este revisa que ENCAJEN. Detecta el problema más caro de todos: que
los tiempos de la línea de tiempo se hayan escrito a ojo en vez de medirse, y
la voz vaya describiendo una sección que ya pasó.

Cómo detecta las secciones sin tocar las escenas: ejecuta la escena sin
renderizar y, tras cada animación, compara qué elementos siguen en pantalla
respecto al estado anterior. Cuando casi todo el contenido cambia de golpe, eso
es un cambio de acto — que es exactamente donde la escena hace FadeOut de un
grupo y monta el siguiente.

Reporta:
  ERROR  - una frontera de la línea de tiempo no coincide con la real
  ERROR  - una frase de voz empieza en una sección distinta de la que describe
  ERROR  - una frase se desborda a la sección siguiente
  AVISO  - una sección se queda sin voz (silencio visual largo)
  AVISO  - ritmo demasiado rápido: mucho contenido nuevo por segundo

Uso:
    python auditor/auditar_sync.py n8n/video_01_que_es_automatizar.py QueEsAutomatizar
    python auditor/auditar_sync.py --todos
"""

import argparse
import importlib.util
import inspect
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "auditor"))

from manim import Scene, config  # noqa: E402

from auditar import es_visible, unidades_visuales  # noqa: E402

# ---------------- Reglas ----------------
SIMILITUD_CORTE = 0.30    # por debajo de esto, el contenido cambió: nuevo acto
TOLERANCIA_S = 0.6        # cuánto puede desviarse una frontera declarada
# MEDIDO, no estimado: se sintetizaron 7 frases reales con
# es-BO-MarceloNeural a +6 % y se midieron los tramos hablados en la pista de
# voz aislada. Resultado: 17.1 caracteres/segundo (rango 15.2-20.0).
# La constante anterior decia 9.5 — un factor de 1.8x — y por eso los guiones
# salian 44 % mas cortos de lo necesario: el video quedaba lleno de silencios
# y se sentia desincronizado aunque cada frase cayera en su lugar.
# Se usa 16.0 (algo por debajo del promedio) para dejar aire de respiracion.
CHARS_POR_SEGUNDO = 16.0
HUECO_MINIMO = 0.8        # aire mínimo entre el fin de una frase y la siguiente
# Una narración en español va a 2.5-3 palabras por segundo. En video educativo
# el espectador además tiene que LEER la pantalla, así que por encima de 3.0 se
# siente atropellado aunque la locución sea correcta.
RITMO_MAX = 3.0
# Cobertura minima de voz por seccion. Debajo de esto el video se siente
# desincronizado aunque cada frase caiga en su lugar (ver regla 3).
COBERTURA_MIN = 0.55

NIVEL_ERROR = "ERROR"
NIVEL_AVISO = "AVISO"


def cargar_escena(ruta, nombre_clase=None):
    ruta = Path(ruta).resolve()
    spec = importlib.util.spec_from_file_location("sync_" + ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    clases = [o for _, o in inspect.getmembers(modulo, inspect.isclass)
              if issubclass(o, Scene) and o.__module__ == spec.name]
    if nombre_clase:
        clases = [c for c in clases if c.__name__ == nombre_clase]
    return modulo, clases


def medir_escena(clase):
    """Devuelve (fronteras reales, duración, estados) ejecutando en seco."""
    estados = []          # (tiempo, conjunto de ids visibles)
    original_play, original_wait = Scene.play, Scene.wait

    def foto(self):
        vis = set()
        for raiz in self.mobjects:
            if getattr(raiz, "auditor_ignorar", False):
                continue
            for u in unidades_visuales(raiz):
                if es_visible(u):
                    vis.add(id(u))
        t = float(getattr(self.renderer, "time", 0.0) or 0.0)
        estados.append((t, vis))

    def play_i(self, *a, **k):
        original_play(self, *a, **k)
        foto(self)

    def wait_i(self, *a, **k):
        original_wait(self, *a, **k)
        foto(self)

    Scene.play, Scene.wait = play_i, wait_i
    config.dry_run = True
    config.progress_bar = "none"
    config.verbosity = "ERROR"
    try:
        escena = clase()
        escena.render()
        duracion = float(getattr(escena.renderer, "time", 0.0) or 0.0)
    finally:
        Scene.play, Scene.wait = original_play, original_wait

    fronteras = []
    for i in range(1, len(estados)):
        t_ant, prev = estados[i - 1]
        t_act, act = estados[i]
        if not prev:
            continue
        similitud = len(prev & act) / len(prev)
        if similitud < SIMILITUD_CORTE and t_ant > 0.5:
            # la frontera es el momento en que se empieza a limpiar, no el final
            if not fronteras or t_ant - fronteras[-1] > 1.5:
                fronteras.append(round(t_ant, 2))
    # el FadeOut final del cierre no es un cambio de acto: es el final
    fronteras = [f for f in fronteras if duracion - f > 1.5]
    return fronteras, duracion, estados


class AuditoriaSync:
    def __init__(self, nombre):
        self.nombre = nombre
        self.hallazgos = []
        self.notas = []

    def registrar(self, nivel, mensaje):
        self.hallazgos.append({"nivel": nivel, "mensaje": mensaje})

    def errores(self):
        return [h for h in self.hallazgos if h["nivel"] == NIVEL_ERROR]

    def avisos(self):
        return [h for h in self.hallazgos if h["nivel"] == NIVEL_AVISO]

    def escribir_reporte(self, destino):
        destino.parent.mkdir(parents=True, exist_ok=True)
        veredicto = "RECHAZADO ❌" if self.errores() else "APROBADO ✅"
        lineas = [f"# Auditoría de sincronía — {self.nombre}", "",
                  f"**Veredicto:** {veredicto} · {len(self.errores())} errores, "
                  f"{len(self.avisos())} avisos", ""]
        lineas += self.notas + [""]
        if self.hallazgos:
            lineas += ["| Nivel | Hallazgo |", "|---|---|"]
            for h in sorted(self.hallazgos,
                            key=lambda x: x["nivel"] != NIVEL_ERROR):
                lineas.append(f"| {h['nivel']} | {h['mensaje']} |")
        else:
            lineas.append("Voz y visual encajan.")
        destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def linea_para(salida_esperada):
    carpeta = RAIZ / "produccion" / "lineas_tiempo"
    for ruta in sorted(carpeta.glob("*.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if Path(datos.get("video", "")).stem == salida_esperada:
            return ruta, datos
    return None, None


def auditar(ruta_py, nombre_clase):
    modulo, clases = cargar_escena(ruta_py, nombre_clase)
    if not clases:
        raise SystemExit(f"[!] No se encontró la escena en {ruta_py}")
    clase = clases[0]
    aud = AuditoriaSync(clase.__name__)

    fronteras, duracion, _ = medir_escena(clase)
    aud.notas.append(f"**Duración real:** {duracion:.1f} s")
    aud.notas.append(f"**Secciones reales (medidas):** "
                     f"`{[round(f, 1) for f in fronteras]}`")

    ruta_json, datos = linea_para(clase.__name__)
    if not datos:
        aud.registrar(NIVEL_AVISO,
                      "no hay línea de tiempo para esta escena todavía")
        return aud, fronteras, duracion

    aud.notas.append(f"**Línea de tiempo:** `{ruta_json.name}`")

    # --- 1. cada corte de imagen tiene que estar declarado
    # Al revés NO es error: se pueden declarar cambios de música en momentos
    # donde la imagen no se limpia del todo (por ejemplo, cuando un nodo se
    # queda en pantalla a propósito mientras cambia el resto).
    declaradas = [float(s) for s in datos.get("secciones", [])]
    for r in fronteras:
        cerca = min((abs(d - r) for d in declaradas), default=None)
        if cerca is None or cerca > TOLERANCIA_S:
            aud.registrar(
                NIVEL_ERROR,
                f"la imagen cambia en {r:.1f} s y la línea de tiempo no declara "
                f"esa frontera: la música va a sonar a destiempo. Cortes "
                f"detectados: {[round(f, 1) for f in fronteras]}")
    extra = [d for d in declaradas
             if min((abs(d - r) for r in fronteras), default=99) > TOLERANCIA_S]
    if extra:
        aud.notas.append(f"**Cambios de música extra** (sin corte de imagen, "
                         f"deliberados): `{[round(e, 1) for e in extra]}`")

    # --- 2. cada frase debe vivir dentro de su sección
    limites = [0.0] + fronteras + [duracion]
    frases = datos.get("frases", [])
    for i, f in enumerate(frases):
        t = float(f["t"])
        dur_frase = len(f.get("texto", "")) / CHARS_POR_SEGUNDO
        seccion = next((j for j in range(len(limites) - 1)
                        if limites[j] <= t < limites[j + 1]), None)
        if seccion is None:
            aud.registrar(NIVEL_ERROR,
                          f"la frase {i + 1} empieza en {t:.1f} s, fuera del video")
            continue
        fin_seccion = limites[seccion + 1]
        if t + dur_frase > fin_seccion + 0.5:
            desborde = t + dur_frase - fin_seccion
            aud.registrar(
                NIVEL_ERROR,
                f"la frase {i + 1} (t={t:.1f}s, «{f['texto'][:30]}…») dura ~{dur_frase:.1f} s y se desborda "
                f"{desborde:.1f} s a la sección siguiente: se va a oír hablando "
                f"de algo que ya no está en pantalla")
        # margen de arranque: la voz no debe empezar pegada al corte
        if t - limites[seccion] < 0.15 and seccion > 0:
            aud.registrar(
                NIVEL_AVISO,
                f"la frase {i} arranca junto con el corte de imagen: dale "
                f"0.2-0.4 s para que el espectador vea antes de oír")

    # --- 3. secciones mudas y secciones MEDIO mudas
    #
    # La regla original solo miraba si una sección quedaba ENTERAMENTE sin
    # voz. Eso dejó pasar un video real: cada frase caía en su sección, el
    # auditor aprobó, y el video se sentía desincronizado porque solo el
    # 44 % del tiempo tenía voz — con huecos de hasta 11 s en los que la
    # imagen seguía y nadie hablaba. Lo cazó Nicolás mirándolo, no yo.
    #
    # Ahora se mide la COBERTURA: cuántos segundos de voz hay dentro de la
    # sección, contra cuánto dura. El silencio es una herramienta, pero
    # media sección callada se siente como un error de montaje.
    for j in range(len(limites) - 1):
        a, b = limites[j], limites[j + 1]
        largo = b - a
        de_la_seccion = [f for f in frases if a <= float(f["t"]) < b]
        if not de_la_seccion and largo > 2.5:
            aud.registrar(
                NIVEL_AVISO,
                f"la sección {j + 1} ({a:.1f}-{b:.1f} s) "
                f"se queda sin voz durante {largo:.1f} s")
            continue
        if largo < 4.0:
            continue
        voz = sum(min(float(f["t"]) + len(f.get("texto", "")) / CHARS_POR_SEGUNDO, b)
                  - float(f["t"]) for f in de_la_seccion)
        cobertura = voz / largo
        if cobertura < COBERTURA_MIN:
            aud.registrar(
                NIVEL_AVISO,
                f"la sección {j + 1} ({a:.1f}-{b:.1f} s) solo tiene voz el "
                f"{cobertura * 100:.0f} % del tiempo ({voz:.1f} s de "
                f"{largo:.1f} s): se va a sentir desincronizada — "
                f"agregá narración o acortá la escena")

    # --- 4. ritmo: cuánto contenido nuevo por segundo
    for j in range(len(limites) - 1):
        largo = limites[j + 1] - limites[j]
        if largo < 1.0:
            continue
        frase = next((f for f in frases
                      if limites[j] <= float(f["t"]) < limites[j + 1]), None)
        if frase:
            palabras = len(frase["texto"].split())
            ritmo = palabras / largo
            if ritmo > RITMO_MAX:
                aud.registrar(
                    NIVEL_AVISO,
                    f"la sección {j + 1} va a {ritmo:.1f} palabras por segundo "
                    f"({palabras} palabras en {largo:.1f} s): se siente "
                    f"atropellada, alargar la sección o acortar la frase")

    return aud, fronteras, duracion


def main():
    parser = argparse.ArgumentParser(description="Auditor de sincronía voz/imagen")
    parser.add_argument("archivo", nargs="?")
    parser.add_argument("escena", nargs="?")
    parser.add_argument("--todos", action="store_true")
    args = parser.parse_args()

    objetivos = []
    if args.todos:
        objetivos = [(p, None) for p in sorted(RAIZ.glob("*/video_*.py"))]
    elif args.archivo:
        objetivos = [(Path(args.archivo), args.escena)]
    else:
        parser.error("indica un archivo o usa --todos")

    hubo_error = False
    for ruta, escena in objetivos:
        _, clases = cargar_escena(ruta, escena)
        for clase in clases:
            print(f"\n== Sincronía de {ruta.name} :: {clase.__name__} ==")
            aud, fronteras, duracion = auditar(ruta, clase.__name__)
            print(f"   duración real: {duracion:.1f} s")
            print(f"   secciones reales: {[round(f, 1) for f in fronteras]}")
            for h in sorted(aud.hallazgos,
                            key=lambda x: x["nivel"] != NIVEL_ERROR):
                print(f"  [{h['nivel']}] {h['mensaje']}")
            reporte = RAIZ / "auditoria" / f"reporte_sync_{clase.__name__}.md"
            aud.escribir_reporte(reporte)
            estado = "RECHAZADO" if aud.errores() else "APROBADO"
            print(f"  -> {estado}: {len(aud.errores())} errores, "
                  f"{len(aud.avisos())} avisos")
            hubo_error = hubo_error or bool(aud.errores())

    sys.exit(1 if hubo_error else 0)


if __name__ == "__main__":
    main()
