"""Herramientas de video del armado (ffmpeg, ffprobe y PyAV).

Todo respeta la receta de frontera de docs/infra.md §7: H.264 High, yuv420p,
BT.709 de rango limitado (convertido y etiquetado), QP constante y un cuadro
clave en el último cuadro, sin metadatos heredados y con el índice adelante.

Las piezas nuevas que arma este módulo (el tramo de transición que va delante
del paso 1) se codifican desde cuadros yuv420p ya decodificados, sin volver a
convertir el color, y se PEGAN a nivel de paquetes con el video del paso: los
cuadros del paso no se recodifican nunca, así que su último cuadro sigue siendo
idéntico al bit al primero del paso siguiente. Para pegar, el SPS/PPS de las dos
partes tiene que ser el mismo: lo es entre Remotion (ffmpeg 7.1), codificar_paso.py
y este módulo (ffmpeg 9.0.2), medido el 23-oct-2026; si no lo fuera, se recodifica
todo junto y se avisa.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

from deck import ALTO, ANCHO, FPS, TINTA

FILTRO_BT709 = "zscale=matrix=709:range=limited:primariesin=709:primaries=709:transferin=709:transfer=709"
# De yuv420p BT.709 limitado a RGB: solo la matriz y el rango (no hay cambio de gama). Con
# scale y no con zscale: zscale se niega ("no path between colorspaces") si al video le
# faltan los primarios o la transferencia; con los etiquetados, los dos dan los mismos
# píxeles (medido: diferencia 0 en Remotion, codificar_paso.py y este módulo).
A_RGB = "scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24"
ETIQUETAS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
QP_FRONTERA = 16

# Receta compacta (por si el deck pesara demasiado): QP constante más alto en los
# cuadros P y B, y el MISMO QP en los cuadros I gracias a ipratio (22 - 6·log2(2,8)
# ≈ 13, como con -qp 16), más un GOP largo (un cuadro I periódico cada 30 s en vez
# de cada 8): los cuadros de frontera son I forzados y su codificación depende solo
# de la imagen, así que siguen idénticos. Medido el 23-oct-2026 en clips sintéticos
# parecidos a los reales: −27 % (animación), −28 % (cronómetro con cabina) y −43 %
# (reloj quieto) contra -qp 16, fronteras IDÉNTICAS y PSNR medio ≥ 57 dB. "CRF 18 +
# zonas QP 16" en cambio da fronteras solo IGUALES A LA VISTA (ver docs/armado.md).
RECETA_COMPACTA = ["-qp", "22", "-x264-params", "ipratio=2.8:keyint=900"]

TAM_CUADRO = ANCHO * ALTO * 3 // 2  # bytes de un cuadro yuv420p


class ErrorVideo(RuntimeError):
    pass


def ejecutar(cmd, entrada: bytes | None = None, capturar=True) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], input=entrada, capture_output=capturar)
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-12:]
        raise ErrorVideo(f"falló: {' '.join(str(c) for c in cmd[:8])} …\n" + "\n".join(err))
    return r


# ---------------------------------------------------------------- sondeo
@dataclass
class Info:
    ruta: Path
    codec: str
    perfil: str
    ancho: int
    alto: int
    pix_fmt: str
    espacio: str
    primarios: str
    transferencia: str
    rango: str
    fps: Fraction
    cuadros: int
    duracion: float          # del contenedor
    audio: dict | None       # {codec, muestreo, canales, duracion}
    tamano: int

    @property
    def duracion_video(self) -> float:
        return self.cuadros / float(self.fps) if self.fps else 0.0


def sondear(video: Path) -> Info:
    r = ejecutar(["ffprobe", "-v", "error", "-count_packets", "-show_streams", "-show_format", "-of", "json", video])
    j = json.loads(r.stdout)
    vs = [s for s in j["streams"] if s.get("codec_type") == "video"]
    if not vs:
        raise ErrorVideo(f"{video}: no tiene video")
    v = vs[0]
    au = [s for s in j["streams"] if s.get("codec_type") == "audio"]
    audio = None
    if au:
        a = au[0]
        audio = {"codec": a.get("codec_name"), "muestreo": int(a.get("sample_rate", 0)),
                 "canales": int(a.get("channels", 0)), "duracion": float(a.get("duration") or 0)}
    num, den = (int(x) for x in v.get("r_frame_rate", "0/1").split("/"))
    return Info(ruta=Path(video), codec=v.get("codec_name", ""), perfil=v.get("profile", ""),
                ancho=int(v.get("width", 0)), alto=int(v.get("height", 0)), pix_fmt=v.get("pix_fmt", ""),
                espacio=v.get("color_space", ""), primarios=v.get("color_primaries", ""),
                transferencia=v.get("color_transfer", ""), rango=v.get("color_range", ""),
                fps=Fraction(num, den) if den else Fraction(0), cuadros=int(v.get("nb_read_packets", 0)),
                duracion=float(j["format"].get("duration") or 0), audio=audio,
                tamano=int(j["format"].get("size") or Path(video).stat().st_size))


def problemas_de_formato(info: Info) -> list[str]:
    """Lo que no cumple la receta de entrega."""
    p = []
    if info.codec != "h264":
        p.append(f"códec {info.codec} (se espera h264)")
    if info.perfil not in ("High",):
        p.append(f"perfil {info.perfil} (se espera High)")
    if (info.ancho, info.alto) != (ANCHO, ALTO):
        p.append(f"{info.ancho}x{info.alto} (se espera {ANCHO}x{ALTO})")
    if info.fps != FPS:
        p.append(f"{float(info.fps):.3f} cuadros/s (se espera {FPS})")
    if info.pix_fmt != "yuv420p":
        p.append(f"pix_fmt {info.pix_fmt} (se espera yuv420p)")
    if (info.espacio, info.primarios, info.transferencia, info.rango) != ("bt709", "bt709", "bt709", "tv"):
        p.append(f"color {info.espacio}/{info.primarios}/{info.transferencia}/{info.rango} (se espera bt709 y rango tv)")
    if not moov_adelante(info.ruta):
        p.append("el índice (moov) está al final: falta +faststart")
    return p


def moov_adelante(video: Path) -> bool:
    """¿El átomo moov va antes que mdat? (PowerPoint y el navegador arrancan sin leer todo)."""
    with open(video, "rb") as f:
        tam_total = os.fstat(f.fileno()).st_size
        pos = 0
        while pos < tam_total:
            f.seek(pos)
            cab = f.read(16)
            if len(cab) < 8:
                return False
            tam = int.from_bytes(cab[:4], "big")
            tipo = cab[4:8]
            if tam == 1:
                tam = int.from_bytes(cab[8:16], "big")
            elif tam == 0:
                tam = tam_total - pos
            if tipo == b"moov":
                return True
            if tipo == b"mdat":
                return False
            if tam < 8:
                return False
            pos += tam
    return False


# ---------------------------------------------------------------- cuadros
def cuadro_png(video: Path, png: Path, cual: str = "ultimo") -> Path:
    """Primer o último cuadro DECODIFICADO, a PNG RGB con la matriz BT.709 (la que
    usan PowerPoint y el navegador con estos videos etiquetados)."""
    png.parent.mkdir(parents=True, exist_ok=True)
    if cual == "primero":
        ejecutar(["ffmpeg", "-v", "error", "-y", "-i", video, "-frames:v", "1", "-vf", A_RGB, png])
    else:
        # -sseof arranca cerca del final; -update 1 reescribe el PNG con cada cuadro: queda el último.
        ejecutar(["ffmpeg", "-v", "error", "-y", "-sseof", "-1.5", "-i", video, "-vf", A_RGB, "-update", "1", png])
        if not png.exists():
            ejecutar(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", A_RGB, "-update", "1", png])
    return png


def _yuv(cmd) -> list[bytes]:
    b = ejecutar(cmd).stdout
    if len(b) % TAM_CUADRO:
        raise ErrorVideo(f"salida yuv de tamaño raro ({len(b)} bytes)")
    return [b[i:i + TAM_CUADRO] for i in range(0, len(b), TAM_CUADRO)]


def primer_yuv(video: Path) -> bytes:
    return _yuv(["ffmpeg", "-v", "error", "-i", video, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"])[0]


def ultimo_yuv(video: Path) -> bytes:
    fr = _yuv(["ffmpeg", "-v", "error", "-sseof", "-1.5", "-i", video, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"])
    if not fr:
        fr = _yuv(["ffmpeg", "-v", "error", "-i", video, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"])
    return fr[-1]


def todos_yuv(video: Path) -> list[bytes]:
    """Todos los cuadros (solo para videos cortos: transiciones)."""
    return _yuv(["ffmpeg", "-v", "error", "-i", video, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"])


_TINTA_YUV: bytes | None = None


def tinta_yuv() -> bytes:
    """Un cuadro de tinta pura, convertido igual que los motores (zscale BT.709)."""
    global _TINTA_YUV
    if _TINTA_YUV is None:
        r, g, b = TINTA
        _TINTA_YUV = _yuv(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                           f"color=c=0x{r:02X}{g:02X}{b:02X}:s={ANCHO}x{ALTO}:r={FPS}:d=0.04,format=rgb24",
                           "-vf", FILTRO_BT709, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"])[0]
    return _TINTA_YUV


def planos(yuv: bytes):
    a = np.frombuffer(yuv, np.uint8)
    y = a[:ANCHO * ALTO].reshape(ALTO, ANCHO)
    u = a[ANCHO * ALTO:ANCHO * ALTO * 5 // 4].reshape(ALTO // 2, ANCHO // 2)
    v = a[ANCHO * ALTO * 5 // 4:].reshape(ALTO // 2, ANCHO // 2)
    return y, u, v


def comparar_yuv(a: bytes, b: bytes) -> dict:
    """Mismo criterio que armar/comparar_cuadros.py, sobre los planos yuv420p."""
    if a == b:
        return {"veredicto": "IDÉNTICOS", "max": 0, "psnr": float("inf"), "notables_pct": 0.0}
    x = np.frombuffer(a, np.uint8).astype(np.int16)
    y = np.frombuffer(b, np.uint8).astype(np.int16)
    d = np.abs(x - y)
    mse = float((d.astype(np.float64) ** 2).mean())
    psnr = 10 * np.log10(255 ** 2 / mse) if mse else float("inf")
    notables = float((d[:ANCHO * ALTO] > 24).mean() * 100)
    veredicto = "IGUALES A LA VISTA" if psnr >= 40 and notables < 0.05 else "DISTINTOS"
    return {"veredicto": veredicto, "max": int(d.max()), "psnr": psnr, "notables_pct": notables}


def yuv_a_png(yuv: bytes, png: Path) -> Path:
    png.parent.mkdir(parents=True, exist_ok=True)
    ejecutar(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{ANCHO}x{ALTO}",
              *ETIQUETAS, "-i", "-", "-frames:v", "1", "-vf", A_RGB, png], entrada=yuv)
    return png


# ---------------------------------------------------------------- codificar
def _expr_claves(claves) -> str:
    return "+".join(f"eq(n,{k})" for k in sorted(set(claves)))


def codificar_yuv(cuadros, salida: Path, claves=None, compacto=False) -> int:
    """Codifica cuadros yuv420p (BT.709 limitado, ya convertidos) con la receta.
    Por defecto, cuadro clave en el último. Devuelve la cantidad de cuadros."""
    cuadros = list(cuadros)
    n = len(cuadros)
    if n == 0:
        raise ErrorVideo("no hay cuadros para codificar")
    claves = [n - 1] if claves is None else claves
    salida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{ANCHO}x{ALTO}",
           "-r", str(FPS), *ETIQUETAS, "-i", "-", "-an", "-map_metadata", "-1",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "medium",
           *(RECETA_COMPACTA if compacto else ["-qp", str(QP_FRONTERA)]),
           "-pix_fmt", "yuv420p", *ETIQUETAS, "-force_key_frames", f"expr:{_expr_claves(claves)}",
           "-movflags", "+faststart", salida]
    p = subprocess.Popen([str(c) for c in cmd], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for c in cuadros:
            p.stdin.write(c)
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode("utf-8", "replace")
    if p.wait() != 0:
        raise ErrorVideo(f"ffmpeg no pudo codificar {salida.name}:\n{err[-1500:]}")
    return n


def codificar_rgb(cuadros_rgb, salida: Path, claves=None) -> int:
    """Cuadros RGB24 (bytes de 1920x1080x3) -> receta (con zscale a BT.709), como los motores."""
    cuadros_rgb = list(cuadros_rgb)
    n = len(cuadros_rgb)
    claves = [n - 1] if claves is None else claves
    salida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ANCHO}x{ALTO}",
           "-r", str(FPS), "-i", "-", "-an", "-map_metadata", "-1",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-qp", str(QP_FRONTERA),
           "-vf", FILTRO_BT709, "-pix_fmt", "yuv420p", *ETIQUETAS,
           "-force_key_frames", f"expr:{_expr_claves(claves)}", "-movflags", "+faststart", salida]
    p = subprocess.Popen([str(c) for c in cmd], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for c in cuadros_rgb:
        p.stdin.write(c)
    p.stdin.close()
    err = p.stderr.read().decode("utf-8", "replace")
    if p.wait() != 0:
        raise ErrorVideo(f"ffmpeg no pudo codificar {salida.name}:\n{err[-1500:]}")
    return n


def recodificar(entrada: Path, salida: Path, compacto=True) -> None:
    """Vuelve a codificar un video entregado (por ejemplo, con la receta compacta).
    El audio se copia tal cual. Como los cuadros de frontera de dos pasos vecinos
    son la misma imagen decodificada, siguen idénticos después (cuadros I a QP fijo)."""
    info = sondear(entrada)
    salida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", entrada, "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "-1",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "medium",
           *(RECETA_COMPACTA if compacto else ["-qp", str(QP_FRONTERA)]),
           "-pix_fmt", "yuv420p", *ETIQUETAS, "-force_key_frames", f"expr:eq(n,{info.cuadros - 1})",
           "-c:a", "copy", "-movflags", "+faststart", salida]
    ejecutar(cmd)


# ---------------------------------------------------------------- pegar
def extradata(video: Path) -> bytes:
    import av
    with av.open(str(video)) as c:
        return bytes(c.streams.video[0].codec_context.extradata or b"")


def pegar(partes: list[Path], salida: Path) -> int:
    """Concatena videos H.264 copiando sus paquetes (sin recodificar).

    Cada parte tiene que empezar en un cuadro clave (toda codificación de x264
    empieza en uno) y tener el mismo SPS/PPS. Devuelve la cantidad de cuadros."""
    import av
    entradas = [av.open(str(p)) for p in partes]
    try:
        vs0 = entradas[0].streams.video[0]
        ed0 = bytes(vs0.codec_context.extradata or b"")
        for p, e in zip(partes, entradas):
            if bytes(e.streams.video[0].codec_context.extradata or b"") != ed0:
                raise ErrorVideo(f"{Path(p).name}: SPS/PPS distinto de {Path(partes[0]).name}: no se puede pegar")
        salida.parent.mkdir(parents=True, exist_ok=True)
        tmp = salida.with_suffix(".pegando.mp4")
        out = av.open(str(tmp), "w", options={"movflags": "+faststart"})
        try:
            o = out.add_stream_from_template(vs0)
            desplazamiento = 0  # en segundos (Fraction)
            total = 0
            for e in entradas:
                vs = e.streams.video[0]
                tb = vs.time_base
                paso = Fraction(1, FPS)
                paquetes = [pk for pk in e.demux(vs) if pk.dts is not None and pk.size > 0]
                if not paquetes:
                    raise ErrorVideo("una parte no tiene cuadros")
                primero = min(paquetes, key=lambda pk: pk.pts)
                if not primero.is_keyframe:
                    raise ErrorVideo("una parte no empieza en un cuadro clave")
                base = primero.pts
                for pk in paquetes:
                    rel_pts = (pk.pts - base) * tb
                    rel_dts = (pk.dts - base) * tb
                    pk.pts = int(round((rel_pts + desplazamiento) / tb))
                    pk.dts = int(round((rel_dts + desplazamiento) / tb))
                    pk.stream = o
                    out.mux(pk)
                desplazamiento += len(paquetes) * paso
                total += len(paquetes)
        finally:
            out.close()
        os.replace(tmp, salida)
        return total
    finally:
        for e in entradas:
            e.close()


def copiar(entrada: Path, salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, salida)


# ---------------------------------------------------------------- audio
MUESTREO = 48000


def leer_wav(ruta: Path) -> np.ndarray:
    """WAV PCM 16 bit -> float32 (n, 2) en [-1, 1]."""
    with wave.open(str(ruta), "rb") as w:
        if w.getsampwidth() != 2:
            raise ErrorVideo(f"{ruta}: se espera PCM de 16 bit")
        if w.getframerate() != MUESTREO:
            raise ErrorVideo(f"{ruta}: se espera {MUESTREO} Hz")
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
        x = x.reshape(-1, w.getnchannels())
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2]


def escribir_wav(ruta: Path, x: np.ndarray) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    y = np.clip(np.rint(x * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(MUESTREO)
        w.writeframes(y.tobytes())


def audio_de(video: Path) -> np.ndarray | None:
    """La pista de audio de un video, decodificada a float32 estéreo de 48 kHz (o None)."""
    if sondear(video).audio is None:
        return None
    b = ejecutar(["ffmpeg", "-v", "error", "-i", video, "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-ar",
                  str(MUESTREO), "-"]).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).copy()


def pista(duracion: float, eventos: list[tuple[float, np.ndarray]], base: np.ndarray | None = None) -> np.ndarray:
    """Una pista del largo del video con cada sonido en su segundo. Si un sonido
    pasa del final, se corta con un desvanecido de 10 ms (sin chasquido)."""
    n = int(round(duracion * MUESTREO))
    x = np.zeros((n, 2), np.float32)
    if base is not None:
        m = min(n, len(base))
        x[:m] += base[:m]
    for t, s in eventos:
        i = int(round(t * MUESTREO))
        if i >= n or i < 0:
            raise ErrorVideo(f"el sonido en {t:.2f} s queda fuera del video ({duracion:.2f} s)")
        trozo = s[: n - i].copy()
        if len(trozo) < len(s):
            f = min(len(trozo), int(0.010 * MUESTREO))
            trozo[-f:] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]
        x[i:i + len(trozo)] += trozo
    return x


def poner_audio(video: Path, audio: np.ndarray, salida: Path) -> None:
    """Muxea la pista (AAC-LC 48 kHz estéreo, 192 kb/s) con el video copiado tal cual."""
    with tempfile.TemporaryDirectory(prefix="audio_") as d:
        wav = Path(d) / "pista.wav"
        escribir_wav(wav, audio)
        salida.parent.mkdir(parents=True, exist_ok=True)
        tmp = salida.with_suffix(".audio.mp4")
        ejecutar(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wav, "-map", "0:v:0", "-map", "1:a:0",
                  "-map_metadata", "-1", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(MUESTREO),
                  "-ac", "2", "-movflags", "+faststart", tmp])
        os.replace(tmp, salida)


def inicio_sonido(audio: np.ndarray, umbral_db: float = -40.0) -> float | None:
    """Primer instante (s) en que la pista supera el umbral (para verificar el ding)."""
    if audio is None or not len(audio):
        return None
    a = np.abs(audio).max(axis=1)
    i = np.flatnonzero(a > 10 ** (umbral_db / 20))
    return float(i[0] / MUESTREO) if len(i) else None
