"""Mapa de BEATS de una escena: en qué segundo aparece cada cosa nueva.

Por qué existe. La regla del proyecto dice "una frase de voz por beat visual",
pero hasta ahora los tiempos se sacaban de las 5 fronteras gruesas que devuelve
`auditar_sync`. Una sección contiene MUCHOS beats — cada pastilla que entra,
cada texto que se escribe, cada tachado — y mapear la narración a secciones
produce exactamente el defecto que Nicolás oyó en el video 1: la voz explicando
algo que ya salió de pantalla (práctica 7.23).

Esto ejecuta la escena en seco y anota, para cada animación, qué elementos
NUEVOS aparecieron y en qué segundo empezaron a aparecer. Con eso, cada frase
puede arrancar 0,3 s después de su beat: el ojo ve y después el oído oye.

Uso:
    python auditor/mapa_beats.py chainlink/video_02_problema_oraculo.py ProblemaOraculo
    python auditor/mapa_beats.py <archivo> <Escena> --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from manim import Scene, config  # noqa: E402

from auditar_sync import cargar_escena, es_visible, unidades_visuales  # noqa: E402


def etiqueta_de(mobjeto):
    """El texto que lleva dentro, para poder nombrar el beat."""
    partes = []
    pila = [mobjeto]
    while pila:
        m = pila.pop()
        t = getattr(m, "text", None)
        if isinstance(t, str) and t.strip():
            partes.append(t.strip())
        pila.extend(getattr(m, "submobjects", []) or [])
    return " ".join(partes[:4])


def mapa(clase):
    """Ejecuta en seco y devuelve [(segundo, etiqueta, n_elementos), …]."""
    beats = []
    original_play, original_wait = Scene.play, Scene.wait

    def visibles(self):
        vis = {}
        for raiz in self.mobjects:
            if getattr(raiz, "auditor_ignorar", False):
                continue
            for u in unidades_visuales(raiz):
                if es_visible(u):
                    vis[id(u)] = u
        return vis

    def ahora(self):
        return float(getattr(self.renderer, "time", 0.0) or 0.0)

    def play_i(self, *a, **k):
        antes_t, antes = ahora(self), visibles(self)
        original_play(self, *a, **k)
        nuevos = [m for i, m in visibles(self).items() if i not in antes]
        if nuevos:
            texto = " · ".join(filter(None, (etiqueta_de(m) for m in nuevos)))
            beats.append((round(antes_t, 1), texto[:70], len(nuevos)))

    def wait_i(self, *a, **k):
        original_wait(self, *a, **k)

    Scene.play, Scene.wait = play_i, wait_i
    config.dry_run = True
    config.progress_bar = "none"
    config.verbosity = "ERROR"
    try:
        escena = clase()
        escena.render()
        duracion = round(float(getattr(escena.renderer, "time", 0.0) or 0.0), 1)
    finally:
        Scene.play, Scene.wait = original_play, original_wait
    return beats, duracion


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo")
    ap.add_argument("escena")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    _, clases = cargar_escena(Path(args.archivo), args.escena)
    if not clases:
        raise SystemExit(f"no encontré la escena {args.escena}")
    beats, duracion = mapa(clases[0])

    if args.json:
        print(json.dumps({"duracion": duracion,
                          "beats": [{"t": t, "que": q} for t, q, _ in beats]},
                         ensure_ascii=False, indent=2))
        return

    print(f"\n== Beats de {Path(args.archivo).name} :: {args.escena} "
          f"({duracion} s, {len(beats)} beats) ==\n")
    print(f"{'seg':>6}  {'voz desde':>9}  qué aparece")
    for t, que, n in beats:
        print(f"{t:>6.1f}  {t + 0.3:>9.1f}  {que or f'({n} elementos sin texto)'}")
    print(f"\nCopiar a la línea de tiempo: "
          f"{' '.join(str(t) for t, _, _ in beats)}")


if __name__ == "__main__":
    main()
