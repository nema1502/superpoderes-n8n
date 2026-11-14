"""Sintetiza el ding del ascensor (armar/assets/ding.wav) y mide su sonoridad.

Guion (sistema visual, «Sonido»): un ding de ascensor de dos tonos, mi6 -> do6,
de unos 0,8 s, sintetizado para no depender de licencias. Suena solo cuando
llega el ascensor de 30 segundos (D14.1, D19.2, D19.4, A8.2, A8.3 y A9.1).

Cómo se arma cada tono: un golpe de campana limpia, con el fundamental y tres
parciales que caen más rápido cuanto más agudos (lo que hace que suene a metal y
no a pitido), más un fundamental apenas desafinado que le da un batido suave.
Ataque de 4 ms en coseno (sin chasquido) y un final que llega a cero de verdad.
El segundo tono entra a los 0,28 s mientras el primero sigue sonando (tercera
mayor descendente, el "ding-dong" de siempre). Dura 1,2 s: lo que se oye es el
primer 0,8 s y el resto es la cola que se apaga. Entra en todos los pasos con
ding: entre el ding y el final del video hay 1,3 s o más.

Nivel: se ajusta la ganancia para que la sonoridad momentánea máxima (EBU R128,
ventana de 400 ms) sea -14 LUFS, el nivel de un contenido normal en plataformas:
se oye claro sobre la sala sin sobresaltar, y el técnico ajusta el volumen como
con cualquier video. El pico real queda muy por debajo de 0 dBTP (margen para el
AAC y para PowerPoint, que reproduce al 80 %). Se mide con el filtro ebur128 de
ffmpeg, no con una cuenta propia.

Uso:
    python armar/ding.py                 regenera armar/assets/ding.wav y lo mide
    python armar/ding.py --medir <wav>   solo mide
    python armar/ding.py --sala <wav>    además, una prueba de 12 s con murmullo de sala (ruido rosa modulado)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / "assets" / "ding.wav"

MUESTREO = 48000
MI6 = 1318.51
DO6 = 1046.50
GOLPES = [(0.00, MI6), (0.28, DO6)]
# (relación con el fundamental, amplitud, constante de caída en s)
PARCIALES = [
    (1.0000, 1.00, 0.30),
    (1.0018, 0.12, 0.30),   # batido suave (2,4 Hz en mi6)
    (2.0000, 0.26, 0.15),
    (3.0000, 0.07, 0.08),
    (4.1600, 0.035, 0.045),  # el brillo inarmónico del golpe, que se va enseguida
]
DURACION = 1.2
ATAQUE = 0.004
COLA = 0.30
OBJETIVO_MOMENTANEA = -14.0   # LUFS
TECHO_PICO = -3.0             # dBTP


def sintetizar() -> np.ndarray:
    n = int(DURACION * MUESTREO)
    t = np.arange(n) / MUESTREO
    x = np.zeros(n)
    for inicio, f in GOLPES:
        tt = t - inicio
        activo = tt >= 0
        tono = np.zeros(n)
        for rel, amp, tau in PARCIALES:
            tono += amp * np.exp(-np.maximum(tt, 0) / tau) * np.sin(2 * np.pi * f * rel * np.maximum(tt, 0))
        ataque = np.clip(tt / ATAQUE, 0, 1)
        ataque = 0.5 - 0.5 * np.cos(np.pi * ataque)          # coseno: sin escalón
        x += np.where(activo, tono * ataque, 0.0)
    # cola: el último tramo baja a cero en coseno (sin corte)
    cola = int(COLA * MUESTREO)
    x[-cola:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, cola))
    x[-1] = 0.0
    return x / np.max(np.abs(x))


def escribir(ruta: Path, mono: np.ndarray) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    estereo = np.repeat(mono[:, None], 2, axis=1)
    datos = np.clip(np.rint(estereo * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(MUESTREO)
        w.writeframes(datos.tobytes())


def medir(ruta: Path) -> dict:
    """Sonoridad integrada, momentánea máxima y pico real (ffmpeg ebur128)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-af",
                        "ebur128=peak=true:framelog=info", "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    log = r.stderr
    momentaneas = [float(m) for m in re.findall(r"\bM:\s*(-?[0-9.]+)", log)]
    resumen = log[log.rfind("Summary:"):]
    integrada = float(re.search(r"I:\s*(-?[0-9.]+|-inf) LUFS", resumen).group(1))
    pico = float(re.search(r"Peak:\s*(-?[0-9.]+|-inf) dBFS", resumen).group(1))
    a = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-af", "astats=measure_overall=Peak_level+DC_offset:measure_perchannel=none",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    pico_muestra = re.search(r"Peak level dB:\s*(-?[0-9.]+)", a)
    dc = re.search(r"DC offset:\s*(-?[0-9.e+-]+)", a)
    return {"integrada_lufs": integrada, "momentanea_max_lufs": max(momentaneas) if momentaneas else None,
            "pico_real_dbtp": pico, "pico_muestra_dbfs": float(pico_muestra.group(1)) if pico_muestra else None,
            "dc": float(dc.group(1)) if dc else None}


def control_chasquidos(x: np.ndarray) -> dict:
    """Primera y última muestra en cero, y el salto máximo entre muestras contra el de
    un seno del parcial más agudo a la misma amplitud (si hay un escalón, se dispara)."""
    salto = float(np.max(np.abs(np.diff(x))))
    f_max = max(f for _, f in GOLPES) * max(r for r, _, _ in PARCIALES)
    cota = 2 * np.pi * f_max / MUESTREO * float(np.max(np.abs(x)))
    return {"primera": float(x[0]), "ultima": float(x[-1]), "salto_max": salto, "cota_seno": cota,
            "sin_chasquidos": abs(x[0]) < 1e-6 and abs(x[-1]) < 1e-6 and salto <= cota}


def generar(destino: Path = DESTINO, objetivo: float = OBJETIVO_MOMENTANEA, verbose=True) -> dict:
    x = sintetizar()
    tmp = destino.with_suffix(".tmp.wav")
    escribir(tmp, x * 0.25)
    m0 = medir(tmp)
    ganancia_db = objetivo - m0["momentanea_max_lufs"]
    g = 0.25 * 10 ** (ganancia_db / 20)
    # x está normalizada a pico 1: el pico de muestra en dBFS es 20·log10(g); medio dB de margen
    # para el pico real (entre muestras), que se mide abajo.
    g = min(g, 10 ** ((TECHO_PICO - 0.5) / 20))
    y = x * g
    escribir(destino, y)
    tmp.unlink(missing_ok=True)
    m = medir(destino)
    c = control_chasquidos(y)
    datos = {"archivo": str(destino), "duracion_s": DURACION, "golpes": GOLPES, "ganancia": g, **m, **c}
    if verbose:
        print(f"{destino}: {DURACION:.1f} s, {MUESTREO} Hz, estéreo 16 bit")
        print(f"  sonoridad momentánea máx. {m['momentanea_max_lufs']:.1f} LUFS (objetivo {objetivo:.1f}), "
              f"integrada {m['integrada_lufs']:.1f} LUFS, pico real {m['pico_real_dbtp']:.1f} dBTP, "
              f"pico de muestra {m['pico_muestra_dbfs']:.1f} dBFS, continua {m['dc']}")
        print(f"  chasquidos: primera muestra {c['primera']:.1e}, última {c['ultima']:.1e}, "
              f"salto máx. {c['salto_max']:.4f} (cota de un seno {c['cota_seno']:.4f}) -> "
              f"{'sin chasquidos' if c['sin_chasquidos'] else 'REVISAR'}")
    if m["pico_real_dbtp"] > TECHO_PICO:
        raise SystemExit(f"el pico real ({m['pico_real_dbtp']:.1f} dBTP) pasa el techo de {TECHO_PICO} dBTP")
    return datos


def prueba_sala(destino: Path, ding: Path = DESTINO, nivel_murmullo=-26.0) -> None:
    """12 s de murmullo (ruido rosa modulado como habla de muchos) con el ding a los 4 y a los 9 s."""
    rng = np.random.default_rng(3)
    n = 12 * MUESTREO
    blanco = rng.standard_normal(n)
    espectro = np.fft.rfft(blanco)
    f = np.fft.rfftfreq(n, 1 / MUESTREO)
    espectro[1:] /= np.sqrt(f[1:])                       # rosa
    espectro[(f < 120) | (f > 6000)] *= 0.1              # banda de voz
    rosa = np.fft.irfft(espectro, n)
    t = np.arange(n) / MUESTREO
    mod = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 2.3 * t + 0.6 * np.sin(2 * np.pi * 0.7 * t)))
    murmullo = rosa * mod
    murmullo /= np.sqrt(np.mean(murmullo ** 2))
    murmullo *= 10 ** (nivel_murmullo / 20)
    with wave.open(str(ding), "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2)[:, 0] / 32768.0
    mezcla = murmullo.copy()
    for s in (4.0, 9.0):
        i = int(s * MUESTREO)
        mezcla[i:i + len(d)] += d
    escribir(destino, np.clip(mezcla, -1, 1))
    print(f"{destino}: murmullo a {nivel_murmullo} dBFS RMS con el ding a los 4 y 9 s")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--medir", help="solo medir este WAV")
    p.add_argument("--salida", default=str(DESTINO))
    p.add_argument("--objetivo", type=float, default=OBJETIVO_MOMENTANEA, help="LUFS de sonoridad momentánea máxima")
    p.add_argument("--sala", help="además, escribir una prueba con murmullo de sala en este WAV")
    a = p.parse_args()
    if a.medir:
        print(medir(Path(a.medir)))
        return
    generar(Path(a.salida), a.objetivo)
    if a.sala:
        prueba_sala(Path(a.sala), Path(a.salida))


if __name__ == "__main__":
    main()
