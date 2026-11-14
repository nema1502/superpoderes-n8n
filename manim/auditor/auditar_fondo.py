"""Auditor del sonido de fondo: ruido, huecos mudos, saturación y saltos.

Nació el 30 de septiembre de 2026, cuando Nicolás escuchó el video corto del
pitch y en los primeros 37 segundos había un colchón de ruido debajo de la
música. Ningún auditor lo vio: `auditar_audio.py` es para los videos con voz
del canal y nunca se corrió sobre el pitch. La causa era el grabador de la
música, que dejaba colar el ruido de la tribuna de la carrera.

Qué mide, segundo a segundo, sobre cualquier video o audio:

  ERROR  colchón de ruido: el piso de 3 a 12 kHz que queda ENTRE golpe y golpe
         (el percentil 10 en el tiempo, relativo a la energía de ese segundo).
         Un platillo o una palma aparecen y se van y no lo mueven; un ruido
         continuo sí. Medido: lo sucio da -32 dB de mediana, la música limpia
         -56 y el sonido de los juegos -49. Corte en -40, sostenido 3 s o más.
  ERROR  hueco mudo de más de 2 s en el medio (el principio y el final pueden
         arrancar y terminar en silencio).
  ERROR  saturación: muestras al tope.
  ERROR  el sonido dura distinto que la imagen (más de medio segundo).
  AVISO  salto de volumen de más de 14 dB de un segundo al siguiente.
  AVISO  volumen integrado fuera de -26 a -12 LUFS.

Uso:
    python auditor/auditar_fondo.py <video o audio> [...]
    python auditor/auditar_fondo.py --validar      # las pruebas del propio auditor

Sale con código 1 si hay algún ERROR.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 32000
N, HOP = 1024, 512
BANDA = (3000.0, 12000.0)
PISO_MAX_DB = -40.0          # piso agudo relativo; por encima hay ruido entre golpe y golpe
PISO_FUERTE_DB = -35.0       # por encima de esto el ruido es fuerte
RUIDO_FUERTE_S = 3           # ruido fuerte: error desde 3 s seguidos
RUIDO_LEVE_S = 6             # ruido leve (-40 a -35): error desde 6 s; menos, aviso
# Calibrado el 30 de septiembre de 2026 con lo medido:
#  - el colchón de la tribuna metido en la música: -31 dB durante 37 s;
#  - la tribuna vieja de la carrera en el clímax: -22 dB durante 6 s;
#  - el platillo de la música en el clímax (crash y semicorcheas): -37 a -39
#    dB durante 3 s. Es percusión, no un colchón: queda como aviso.
#  - música limpia -56 de mediana; el sonido de los juegos, -49.
MUDO_DB = -50.0              # RMS de un segundo por debajo de esto es silencio
MUDO_MAX_S = 2.0
BORDE_S = 3.0                # al principio y al final se tolera silencio
SALTO_DB = 14.0
LUFS_MIN, LUFS_MAX = -26.0, -12.0


def _ff(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def duraciones(ruta):
    r = _ff(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", str(ruta)])
    v = a = None
    for linea in r.stdout.splitlines():
        partes = linea.split(",")
        if len(partes) >= 2 and partes[1] not in ("", "N/A"):
            if partes[0] == "video":
                v = float(partes[1])
            elif partes[0] == "audio":
                a = float(partes[1])
    if a is None:
        r = _ff(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)])
        a = float(r.stdout.strip() or 0)
    return v, a


def leer(ruta):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-vn", "-ac", "1", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(crudo, dtype=np.float32)


def pico_db(ruta):
    """El pico de verdad, canal por canal. La primera versión lo medía sobre
    la mezcla en mono que se usa para el resto, y ffmpeg, al juntar los dos
    canales, suma: daba muestras "al tope" en un video con el pico en -1,9 dB."""
    r = _ff(["ffmpeg", "-hide_banner", "-i", str(ruta), "-vn", "-af",
             "astats=measure_overall=Peak_level:measure_perchannel=none", "-f", "null", "-"])
    m = re.findall(r"Peak level dB:\s+(-?[\d.]+|-inf)", r.stderr)
    return float(m[-1]) if m and m[-1] != "-inf" else None


def lufs(ruta):
    r = _ff(["ffmpeg", "-hide_banner", "-i", str(ruta), "-vn", "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def por_segundo(x):
    """Para cada segundo: el piso agudo relativo y el volumen."""
    freqs = np.fft.rfftfreq(N, 1 / SR)
    banda = (freqs >= BANDA[0]) & (freqs <= BANDA[1])
    win = np.hanning(N)
    pisos, vols = [], []
    for s in range(int(len(x) / SR)):
        seg = x[s * SR:(s + 1) * SR]
        vol = 10 * np.log10(np.mean(seg.astype(np.float64) ** 2) + 1e-20)
        frames = np.array([seg[i:i + N] * win for i in range(0, len(seg) - N, HOP)])
        P = np.abs(np.fft.rfft(frames, axis=1)) ** 2
        total = np.mean(np.sum(P, axis=1)) + 1e-20
        p10 = np.percentile(np.sum(P[:, banda], axis=1), 10) + 1e-20
        pisos.append(10 * np.log10(p10 / total))
        vols.append(vol)
    return np.array(pisos), np.array(vols)


def tramos(mascara):
    """Rangos [a, b) de segundos seguidos donde la máscara es verdadera."""
    out, a = [], None
    for i, m in enumerate(list(mascara) + [False]):
        if m and a is None:
            a = i
        elif not m and a is not None:
            out.append((a, i))
            a = None
    return out


def auditar(ruta):
    errores, avisos, datos = [], [], {}
    v, a = duraciones(ruta)
    if v is not None and a is not None and abs(v - a) > 0.5:
        errores.append(f"el sonido dura {a:.1f} s y la imagen {v:.1f} s")
    x = leer(ruta)
    if len(x) == 0:
        return [f"{ruta}: no tiene sonido"], [], {}
    dur = len(x) / SR
    pico = pico_db(ruta)
    if pico is not None and pico >= -0.1:
        errores.append(f"saturación: el pico llega a {pico:.1f} dBFS")
    pisos, vols = por_segundo(x)
    sonando = vols > MUDO_DB
    # El colchón de ruido: segundos que suenan y tienen el piso agudo alto.
    ruido = sonando & (pisos > PISO_MAX_DB)
    for a_, b_ in tramos(ruido):
        largo, nivel = b_ - a_, float(np.median(pisos[a_:b_]))
        texto = f"de {a_} a {b_} s ({largo} s): piso agudo {nivel:.0f} dB"
        if (nivel > PISO_FUERTE_DB and largo >= RUIDO_FUERTE_S) or largo >= RUIDO_LEVE_S:
            errores.append(f"colchón de ruido {texto}, el corte es {PISO_MAX_DB:.0f}")
        elif largo >= 2:
            avisos.append(f"ruido leve y corto {texto} (platillos o un efecto, revisar de oído)")
    # Huecos mudos en el medio.
    for a_, b_ in tramos(~sonando):
        if b_ - a_ > MUDO_MAX_S and a_ >= BORDE_S and b_ <= dur - BORDE_S:
            errores.append(f"hueco mudo de {a_} a {b_} s ({b_ - a_} s)")
    # Saltos de volumen entre segundos que suenan los dos.
    for i in range(1, len(vols)):
        if sonando[i] and sonando[i - 1] and abs(vols[i] - vols[i - 1]) > SALTO_DB:
            avisos.append(f"salto de volumen de {vols[i - 1] - vols[i]:+.0f} dB en el segundo {i}")
    l = lufs(ruta)
    if l is not None and not (LUFS_MIN <= l <= LUFS_MAX):
        avisos.append(f"volumen integrado {l:.1f} LUFS, fuera de {LUFS_MIN:.0f} a {LUFS_MAX:.0f}")
    datos = {"duracion": dur, "lufs": l, "pico": pico,
             "piso_mediana": float(np.median(pisos[sonando])) if sonando.any() else None,
             "segundos_con_ruido": int(ruido.sum())}
    return errores, avisos, datos


def informe(ruta):
    errores, avisos, d = auditar(ruta)
    print(f"\n{ruta}")
    if d:
        print(f"  {d['duracion']:.1f} s · {d['lufs']} LUFS · piso agudo mediano {d['piso_mediana']:.0f} dB · "
              f"{d['segundos_con_ruido']} s con ruido")
    for e in errores:
        print(f"  [ERROR] {e}")
    for w in avisos[:8]:
        print(f"  [AVISO] {w}")
    if len(avisos) > 8:
        print(f"  [AVISO] y {len(avisos) - 8} más")
    print(f"  -> {'RECHAZADO' if errores else 'APROBADO'}: {len(errores)} errores, {len(avisos)} avisos")
    return not errores


def validar():
    """Validar el validador: cada regla tiene que disparar en su caso roto y
    callarse en la música limpia. Los casos se fabrican con ffmpeg."""
    musica = Path(__file__).resolve().parents[2] / "musica"  # con tramo2.wav, no viene en el repositorio
    limpio = musica / "tramo2.wav"
    tmp = Path(tempfile.mkdtemp(prefix="fondo-"))
    casos = []

    # 1. La música limpia aprueba.
    recorte = tmp / "limpio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.5", "-t", "30", "-i", str(limpio), str(recorte)], check=True)
    casos.append(("música limpia", recorte, None))
    # 2. La misma música con un colchón de ruido rosa debajo: el caso real.
    sucio = tmp / "sucio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(recorte), "-f", "lavfi", "-i",
                    "anoisesrc=color=pink:amplitude=0.02:duration=30:sample_rate=48000",
                    "-filter_complex", "[1:a]volume=1[n];[0:a][n]amix=inputs=2:normalize=0", str(sucio)], check=True)
    casos.append(("con colchón de ruido", sucio, "colchón de ruido"))
    # 3. Un hueco mudo de 5 s en el medio.
    hueco = tmp / "hueco.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(recorte), "-af",
                    "volume=enable='between(t,12,17)':volume=0", str(hueco)], check=True)
    casos.append(("con hueco mudo", hueco, "hueco mudo"))
    # 4. Saturado.
    saturado = tmp / "saturado.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(recorte), "-af", "volume=30dB,alimiter=limit=1:level=false",
                    "-c:a", "pcm_f32le", str(saturado)], check=True)
    casos.append(("saturado", saturado, "saturación"))
    # 5. Ruido leve pero largo: también es colchón.
    leve = tmp / "leve.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(recorte), "-f", "lavfi", "-i",
                    "anoisesrc=color=pink:amplitude=0.006:duration=30:sample_rate=48000",
                    "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0", str(leve)], check=True)
    casos.append(("con colchón leve", leve, "colchón de ruido"))
    # 6. El tramo que se grabó con la tribuna metida: el defecto que motivó esto.
    real = musica / "tramo1.wav"
    if real.exists():
        casos.append(("tramo de la carrera con la tribuna", real, "colchón de ruido"))

    bien = True
    for nombre, ruta, espera in casos:
        errores, _, _ = auditar(ruta)
        dispara = [e for e in errores if espera and e.startswith(espera)]
        ok = (not errores) if espera is None else bool(dispara)
        bien &= ok
        print(f"  {'ok ' if ok else 'MAL'}  {nombre}: {errores[0] if errores else 'sin errores'}")
    print("VALIDADO" if bien else "EL AUDITOR FALLA SUS PROPIAS PRUEBAS")
    return bien


def main():
    ap = argparse.ArgumentParser(description="Auditor del sonido de fondo")
    ap.add_argument("rutas", nargs="*")
    ap.add_argument("--validar", action="store_true")
    a = ap.parse_args()
    if a.validar:
        sys.exit(0 if validar() else 1)
    if not a.rutas:
        ap.error("falta el archivo")
    ok = all([informe(r) for r in a.rutas])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
