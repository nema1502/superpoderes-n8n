"""La vista previa: todos los pasos seguidos, con 1,5 s quietos sobre el último
cuadro de cada uno, y el sonido (el ding donde corresponde).

Sirve para revisar la charla de corrido sin PowerPoint (y para mandarla). Los
videos se leen con el demuxer concat de ffmpeg declarando a cada uno su duración
más la pausa: queda un hueco de 1,5 s entre uno y otro que el filtro fps rellena
repitiendo el último cuadro; al final, tpad agrega la última pausa. El sonido se
arma aparte (numpy): la pista de cada paso, si tiene, en el segundo en que ese
paso empieza. Codifica con NVENC (la RTX de la laptop) si está, si no con x264.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import numpy as np

from deck import FPS
from videos import ETIQUETAS, MUESTREO, ErrorVideo, audio_de, ejecutar, escribir_wav, sondear

# Medido el 23-oct-2026 con los 66 pasos (24 046 cuadros, 801 s): NVENC p4 46 s de reloj y 92 s de
# CPU; x264 veryfast 54 s y 524 s de CPU (los 16 hilos); NVENC p5 con -tune hq, 82 s. NVENC deja la
# CPU libre para los renders de Remotion y Manim; pesa más (28 contra 19 MB), da igual en una vista previa.
NVENC = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "21", "-b:v", "0",
         "-maxrate", "16M", "-bufsize", "32M", "-profile:v", "high"]
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-profile:v", "high"]


def hay_nvenc() -> bool:
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x144:d=0.2", *NVENC,
                        "-f", "null", "-"], capture_output=True)
    return r.returncode == 0


def construir(videos: list[Path], destino: Path, trabajo: Path, pausa=1.5, codificador="auto") -> dict:
    trabajo.mkdir(parents=True, exist_ok=True)
    infos = [sondear(v) for v in videos]
    inicios, t = [], 0.0
    for inf in infos:
        inicios.append(t)
        t += inf.cuadros / FPS + pausa
    total = t
    # pista de sonido
    pista = np.zeros((int(round(total * MUESTREO)) + MUESTREO, 2), np.float32)
    con_audio = 0
    for v, inf, t0 in zip(videos, infos, inicios):
        if inf.audio:
            a = audio_de(v)
            i = int(round(t0 * MUESTREO))
            pista[i:i + len(a)] += a[: len(pista) - i]
            con_audio += 1
    pista = pista[: int(round(total * MUESTREO))]
    wav = trabajo / "vista_previa_audio.wav"
    escribir_wav(wav, pista)
    # Remotion escribe sus videos con base de tiempo 1/90000 y ffmpeg (Manim y el armado) con 1/15360.
    # Con las dos mezcladas, el demuxer concat se cortaba al terminar el primer video (medido el
    # 13-nov-2026 con D01 de Remotion y D02 de Manim: 150 cuadros de 411). Se copia el video de cada
    # paso a la misma base, sin recodificar, y la lista apunta a esas copias.
    comun = trabajo / "base_comun"
    comun.mkdir(parents=True, exist_ok=True)
    copias = []
    for i, v in enumerate(videos):
        c = comun / f"{i:03d}_{Path(v).name}"
        ejecutar(["ffmpeg", "-v", "error", "-y", "-i", v, "-map", "0:v:0", "-c", "copy",
                  "-video_track_timescale", "15360", c])
        copias.append(c)
    # lista para el demuxer concat
    lista = trabajo / "vista_previa_lista.txt"
    with open(lista, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for v, inf in zip(copias, infos):
            ruta = Path(v).resolve().as_posix().replace("'", r"'\''")
            f.write(f"file '{ruta}'\nduration {inf.cuadros / FPS + pausa:.6f}\n")
    usar = codificador
    if usar == "auto":
        usar = "nvenc" if hay_nvenc() else "x264"
    cod = NVENC if usar == "nvenc" else X264
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.stem + ".codificando.mp4")
    t0 = time.time()
    ejecutar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-i", wav,
              "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "-1",
              "-vf", f"fps={FPS},tpad=stop_mode=clone:stop_duration={pausa}",
              *cod, "-pix_fmt", "yuv420p", *ETIQUETAS, "-g", str(FPS * 2),
              "-c:a", "aac", "-b:a", "192k", "-ar", str(MUESTREO), "-ac", "2",
              "-t", f"{total:.6f}", "-movflags", "+faststart", tmp])
    seg = time.time() - t0
    tmp.replace(destino)
    inf = sondear(destino)
    esperados = sum(i.cuadros for i in infos) + int(round(pausa * FPS)) * len(infos)
    if abs(inf.cuadros - esperados) > 2:
        raise ErrorVideo(f"la vista previa tiene {inf.cuadros} cuadros y se esperaban {esperados}")
    return {"archivo": str(destino), "pasos": len(videos), "duracion_s": round(total, 2), "cuadros": inf.cuadros,
            "cuadros_esperados": esperados, "con_audio": con_audio, "codificador": usar,
            "codificar_s": round(seg, 1), "bytes": destino.stat().st_size, "inicios": inicios}
