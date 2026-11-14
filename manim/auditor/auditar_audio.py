"""Auditor de audio: revisa que el video suene como debe antes de publicar.

El auditor visual (auditar.py) cuida la imagen; este cuida el sonido. Analiza
el MP4 ya producido y su línea de tiempo, y reporta:

  ERROR  - sin pista de audio, o audio más corto que el video
  ERROR  - saturación (clipping): el pico real pasa de 0 dBTP
  ERROR  - hueco de silencio largo (el video se queda mudo)
  ERROR  - una frase de voz no suena donde dice la línea de tiempo
  AVISO  - volumen integrado lejos de -14 LUFS (norma de TikTok/YouTube)
  AVISO  - pico real por encima de -1 dBTP (riesgo al recomprimir la app)
  AVISO  - música tapando la voz (poco contraste entre hablado y fondo)
  AVISO  - rango dinámico plano (todo al mismo volumen: aburre)

Uso:
    python auditor/auditar_audio.py chainlink/02_problema_del_oraculo_PUBLICAR.mp4
    python auditor/auditar_audio.py --todos
Reporte: auditoria/reporte_audio_<nombre>.md
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent

# ---------------- Reglas ----------------
LUFS_OBJETIVO = -14.0
# Ventana asimétrica y no un ±1.5 simétrico, por dos razones medidas:
#  - con un techo duro de -1 dBTP, este material (música con golpes) se queda
#    en torno a -15.6 LUFS; forzar -14 exige comprimir tanto que la dinámica
#    cae de 18 a 15.6 dB y el video suena aplastado. No compensa.
#  - TikTok y YouTube normalizan al reproducir: BAJAN lo que viene muy alto,
#    pero lo que viene algo bajo se escucha igual. Pasarse es peor que quedarse.
LUFS_MIN = -16.2
LUFS_MAX = -12.5
PICO_MAX_DBTP = -1.0
SILENCIO_MAX = 2.5       # segundos mudos seguidos aceptables
UMBRAL_SILENCIO = 0.008  # amplitud RMS considerada silencio
# Qué mide de verdad esta cifra: cuánto más fuerte suena un tramo HABLADO que un
# tramo de música sola (las pausas entre frases, ya descontadas las transiciones
# con crash). NO mide inteligibilidad: en una mezcla ya hecha no se puede separar
# la voz de la música agachada debajo de ella — de eso se encarga el sidechain.
# El defecto real y audible es que las pausas peguen MÁS que la narración.
CONTRASTE_MIN_DB = -3.0
RANGO_MIN_DB = 4.0       # variación mínima de volumen a lo largo del video
RETUMBE_MAX_PCT = 6.0    # energía máxima bajo 70 Hz (el celular no la reproduce)
ZUMBIDO_HZ_MIN = 70.0    # por debajo de esto, un tono sostenido es zumbido
# Planitud espectral en las transiciones: por encima de esto, el barrido suena
# a aire (respiración/estornudo) en vez de a transición musical.
# Se mide SOLO de 1500 a 7900 Hz, que es donde vive el siseo. En el espectro
# completo la medida no sirve: percusión de ruido blanco daba 0.120 y la tonal
# 0.094 — indistinguibles — porque los graves musicales, que pesan mucho más,
# aplastan la diferencia. Acotado a esa banda la separación pasa a 1.7x
# (0.83 contra 0.49) y el umbral tiene margen real.
AIRE_BANDA = (1500.0, 7900.0)
AIRE_MAX = 0.65
# Si el grave dominante vive bajo 70 Hz casi la mitad del video, ya se percibe
# como vibración continua. El caso real que motivó la regla daba 55 %.
ZUMBIDO_PERSISTENCIA = 0.45

NIVEL_ERROR = "ERROR"
NIVEL_AVISO = "AVISO"


def ejecutar(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duracion_de(ruta):
    r = ejecutar(["ffprobe", "-v", "error", "-show_entries",
                  "format=duration", "-of", "csv=p=0", str(ruta)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def tiene_audio(ruta):
    r = ejecutar(["ffprobe", "-v", "error", "-select_streams", "a",
                  "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                  str(ruta)])
    return "audio" in r.stdout


def medir_loudness(ruta):
    """Devuelve (LUFS integrado, pico real dBTP) usando el filtro loudnorm."""
    r = ejecutar(["ffmpeg", "-i", str(ruta), "-af",
                  "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                  "-f", "null", "-"])
    bloque = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not bloque:
        return None, None
    datos = json.loads(bloque[-1])
    return float(datos["input_i"]), float(datos["input_tp"])


def extraer_mono(ruta, destino, sr=16000):
    ejecutar(["ffmpeg", "-y", "-i", str(ruta), "-ac", "1", "-ar", str(sr),
              "-vn", str(destino)])
    with wave.open(str(destino), "rb") as w:
        datos = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return datos.astype(np.float32) / 32768.0, sr


def envolvente(senal, sr, ventana=0.05):
    """RMS por ventana: la 'forma' del volumen a lo largo del tiempo."""
    n = max(1, int(sr * ventana))
    recorte = senal[: len(senal) // n * n].reshape(-1, n)
    return np.sqrt((recorte ** 2).mean(axis=1)), ventana


def a_db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


def planitud_espectral(trozo, sr=None, banda=None):
    """Qué tan 'ruido' es un sonido (0 = tono puro, 1 = ruido blanco).

    Se calcula como media geométrica / media aritmética del espectro. Un
    barrido de ruido largo tiene planitud alta y el oído lo interpreta como
    respiración o soplido; un barrido tonal la tiene baja y suena musical.

    Con `banda` se acota a un rango de frecuencias. Es necesario: sobre el
    espectro entero, el bombo y el bajo aportan tanta energía que ahogan la
    diferencia entre percusión de ruido y percusión tonal. El siseo se decide
    entre 1.5 y 8 kHz.
    """
    esp = np.abs(np.fft.rfft(trozo * np.hanning(len(trozo)))) + 1e-10
    if banda and sr:
        frec = np.fft.rfftfreq(len(trozo), 1.0 / sr)
        esp = esp[(frec >= banda[0]) & (frec <= banda[1])]
        if len(esp) < 8:
            return None
    geo = np.exp(np.mean(np.log(esp)))
    return float(geo / np.mean(esp))


def aire_en_transiciones(senal, sr, fronteras):
    """Planitud de la SUBIDA que precede a cada transición.

    Se mide el segundo anterior al golpe, no el golpe. El crash de un platillo
    es ruido por naturaleza y dura un instante: eso no se percibe como
    respiración. Lo que sí se percibe es un barrido sostenido de aire creciendo
    durante un segundo — ese es el que hay que vigilar.

    OJO: esta regla habla de la MÚSICA. Si en esa ventana el narrador está
    hablando, lo que se mide es su voz — y el habla tiene planitud altísima
    (las eses y las efes son ruido puro). Medido en el video 1: con voz encima
    una frontera daba 0.457 y sin voz 0.054, nueve veces más, por un defecto
    que no existía. Por eso quien llama a esta función debe pasarle la pista
    SIN VOZ cuando exista (ver `_pista_de_musica`).
    """
    valores = []
    for f in fronteras:
        ini = int(max(0, (float(f) - 1.1)) * sr)
        fin = min(len(senal), int((float(f) - 0.08) * sr))
        if fin - ini > sr // 4:
            v = planitud_espectral(senal[ini:fin], sr, AIRE_BANDA)
            if v is not None:
                valores.append(v)
    return float(np.mean(valores)) if valores else None


def _pista_de_musica(ruta, destino, sr=16000):
    """Devuelve (señal, sr, es_solo_musica) para las reglas de música.

    `producir.py` deja siempre un hermano `_SIN_VOZ.mp4` con la misma música y
    los mismos tiempos. Esa es la pista correcta para juzgar la música: la
    mezcla final lleva la voz encima y contamina la medición.
    """
    hermano = Path(str(ruta).replace("_PUBLICAR.mp4", "_PUBLICAR_SIN_VOZ.mp4"))
    if hermano != Path(ruta) and hermano.exists():
        s, r = extraer_mono(hermano, Path(destino).with_name("_sin_voz.wav"), sr)
        return s, r, True
    return None, None, False


def analisis_espectral(senal, sr):
    """Busca retumbe y zumbidos: los dos defectos que arruinan el oído.

    - retumbe: energía por debajo de 70 Hz. Un altavoz de celular no reproduce
      esas notas; las convierte en vibración.
    - zumbido sostenido: un mismo tono grave que domina la mayor parte del
      video. Es lo que vuelve incómodo escucharlo pasados unos segundos.
    """
    ventana = int(sr * 1.0)
    marcos = [senal[i:i + ventana] for i in range(0, len(senal) - ventana, ventana)]
    if not marcos:
        return 0.0, None, 0.0

    frecuencias = np.fft.rfftfreq(ventana, 1 / sr)
    grave = (frecuencias >= 20) & (frecuencias < 150)
    retumbe_pct, picos = [], []
    for m in marcos:
        esp = np.abs(np.fft.rfft(m * np.hanning(len(m))))
        total = esp.sum() + 1e-12
        retumbe_pct.append(100 * esp[frecuencias < 70].sum() / total)
        if esp[grave].max() > 0:
            picos.append(float(frecuencias[grave][int(np.argmax(esp[grave]))]))

    if not picos:
        return float(np.mean(retumbe_pct)), None, 0.0
    # No importa que sea SIEMPRE el mismo tono (cambia con cada sección): lo que
    # zumba es que el grave dominante viva por debajo del límite audible del
    # altavoz. Se mide qué fracción del video está en esa zona.
    picos = np.array(picos)
    mediana = float(np.median(picos))
    fraccion_baja = float((picos < ZUMBIDO_HZ_MIN).mean())
    return float(np.mean(retumbe_pct)), mediana, fraccion_baja


class AuditoriaAudio:
    def __init__(self, nombre):
        self.nombre = nombre
        self.hallazgos = []
        self.medidas = {}

    def registrar(self, nivel, mensaje):
        self.hallazgos.append({"nivel": nivel, "mensaje": mensaje})

    def errores(self):
        return [h for h in self.hallazgos if h["nivel"] == NIVEL_ERROR]

    def avisos(self):
        return [h for h in self.hallazgos if h["nivel"] == NIVEL_AVISO]

    def escribir_reporte(self, destino):
        destino.parent.mkdir(parents=True, exist_ok=True)
        veredicto = "RECHAZADO ❌" if self.errores() else "APROBADO ✅"
        lineas = [f"# Auditoría de audio — {self.nombre}", "",
                  f"**Veredicto:** {veredicto} · {len(self.errores())} errores, "
                  f"{len(self.avisos())} avisos", ""]
        if self.medidas:
            lineas += ["| Medida | Valor | Objetivo |", "|---|---|---|"]
            for k, (v, obj) in self.medidas.items():
                lineas.append(f"| {k} | {v} | {obj} |")
            lineas.append("")
        if self.hallazgos:
            lineas += ["| Nivel | Hallazgo |", "|---|---|"]
            for h in sorted(self.hallazgos,
                            key=lambda x: x["nivel"] != NIVEL_ERROR):
                lineas.append(f"| {h['nivel']} | {h['mensaje']} |")
        else:
            lineas.append("Sin hallazgos: el audio cumple todas las reglas.")
        destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def auditar(ruta_video, linea_tiempo=None):
    aud = AuditoriaAudio(Path(ruta_video).name)

    if not tiene_audio(ruta_video):
        aud.registrar(NIVEL_ERROR, "el archivo NO tiene pista de audio")
        return aud

    dur_video = duracion_de(ruta_video)

    # --- nivel integrado y pico real
    lufs, pico = medir_loudness(ruta_video)
    if lufs is not None:
        aud.medidas["Volumen integrado"] = (
            f"{lufs:.1f} LUFS", f"{LUFS_MIN} a {LUFS_MAX} (ref. {LUFS_OBJETIVO})")
        aud.medidas["Pico real"] = (f"{pico:.1f} dBTP", f"≤ {PICO_MAX_DBTP}")
        if lufs < LUFS_MIN:
            aud.registrar(
                NIVEL_AVISO,
                f"volumen integrado {lufs:.1f} LUFS: suena bajo frente a otros "
                f"videos del feed (mínimo {LUFS_MIN})")
        elif lufs > LUFS_MAX:
            aud.registrar(
                NIVEL_AVISO,
                f"volumen integrado {lufs:.1f} LUFS: suena alto y la plataforma "
                f"lo va a bajar (máximo {LUFS_MAX})")
        if pico > 0.0:
            aud.registrar(NIVEL_ERROR,
                          f"saturación: el pico real llega a {pico:.1f} dBTP")
        elif pico > PICO_MAX_DBTP:
            aud.registrar(
                NIVEL_AVISO,
                f"pico real {pico:.1f} dBTP (máx {PICO_MAX_DBTP}): la app puede "
                f"distorsionar al recomprimir")

    # --- análisis de la forma de onda
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        senal, sr = extraer_mono(ruta_video, wav)
        dur_audio = len(senal) / sr
        aud.medidas["Duración audio"] = (f"{dur_audio:.1f} s",
                                         f"{dur_video:.1f} s (video)")
        if dur_video - dur_audio > 0.35:
            aud.registrar(
                NIVEL_ERROR,
                f"el audio dura {dur_audio:.1f} s y el video {dur_video:.1f} s: "
                f"el final se queda mudo")

        # --- retumbe y zumbido sostenido
        retumbe, tono, persistencia = analisis_espectral(senal, sr)
        aud.medidas["Energía bajo 70 Hz"] = (f"{retumbe:.1f} %",
                                             f"≤ {RETUMBE_MAX_PCT} %")
        if retumbe > RETUMBE_MAX_PCT:
            aud.registrar(
                NIVEL_AVISO,
                f"{retumbe:.1f} % de la energía está bajo 70 Hz: en el altavoz "
                f"de un celular eso no suena a grave, suena a vibración")
        if tono is not None:
            aud.medidas["Grave dominante"] = (
                f"{tono:.0f} Hz · bajo 70 Hz el {persistencia * 100:.0f} % del video",
                f"> {ZUMBIDO_HZ_MIN:.0f} Hz")
            if persistencia > ZUMBIDO_PERSISTENCIA:
                aud.registrar(
                    NIVEL_ERROR,
                    f"zumbido: el grave dominante está por debajo de "
                    f"{ZUMBIDO_HZ_MIN:.0f} Hz durante el "
                    f"{persistencia * 100:.0f} % del video (mediana {tono:.0f} Hz). "
                    f"Subir el bajo a 80-110 Hz y evitar ondas cuadradas")

        # --- sonido de aire en las transiciones (respiración / soplido)
        if linea_tiempo:
            _d = json.loads(Path(linea_tiempo).read_text(encoding="utf-8"))
            # Se mide sobre la música SOLA: con la voz encima, las eses del
            # narrador se cuentan como aire y la regla dispara sin defecto.
            _mus, _msr, _solo = _pista_de_musica(ruta_video, tmp, sr)
            aire = aire_en_transiciones(_mus if _solo else senal,
                                        _msr if _solo else sr,
                                        _d.get("secciones", []))
            if aire is not None:
                _fuente = "" if _solo else " · medido CON voz: puede exagerar"
                aud.medidas["Ruido en transiciones"] = (f"{aire:.3f}{_fuente}",
                                                        f"≤ {AIRE_MAX}")
                if aire > AIRE_MAX:
                    aud.registrar(
                        NIVEL_AVISO,
                        f"las transiciones suenan a aire (planitud {aire:.3f}): "
                        f"se perciben como respiración o soplido. Usar subidas "
                        f"tonales en vez de barridos de ruido")

        env, paso = envolvente(senal, sr)
        if len(env) == 0:
            aud.registrar(NIVEL_ERROR, "la pista de audio está vacía")
            return aud

        # huecos de silencio
        mudo = env < UMBRAL_SILENCIO
        mayor, actual, inicio_mayor, inicio = 0, 0, 0, 0
        for i, m in enumerate(mudo):
            if m:
                if actual == 0:
                    inicio = i
                actual += 1
                if actual > mayor:
                    mayor, inicio_mayor = actual, inicio
            else:
                actual = 0
        silencio_s = mayor * paso
        aud.medidas["Silencio más largo"] = (f"{silencio_s:.1f} s",
                                             f"≤ {SILENCIO_MAX} s")
        if silencio_s > SILENCIO_MAX:
            aud.registrar(
                NIVEL_ERROR,
                f"hueco mudo de {silencio_s:.1f} s desde el segundo "
                f"{inicio_mayor * paso:.1f}")

        # rango dinámico: si todo suena igual, el video se siente plano
        env_db = a_db(env)
        activo = env_db[env_db > a_db(UMBRAL_SILENCIO)]
        if len(activo) > 10:
            rango = float(np.percentile(activo, 95) - np.percentile(activo, 20))
            aud.medidas["Rango dinámico"] = (f"{rango:.1f} dB",
                                             f"≥ {RANGO_MIN_DB} dB")
            if rango < RANGO_MIN_DB:
                aud.registrar(
                    NIVEL_AVISO,
                    f"rango dinámico de solo {rango:.1f} dB: todo suena al mismo "
                    f"volumen y el video se percibe plano")

        # --- contraste voz/música usando la línea de tiempo
        if linea_tiempo:
            datos = json.loads(Path(linea_tiempo).read_text(encoding="utf-8"))
            frases = datos.get("frases", [])
            # La ventana de cada frase se estima por el LARGO DEL TEXTO (~14
            # caracteres por segundo) y se corta en la frase siguiente. Antes
            # se usaba un fijo de 2.5 s y, como las frases duran 5-8 s, media
            # voz se contaba como "solo música" y el contraste salía falso.
            ventanas = []
            for i, f in enumerate(frases):
                ini_s = float(f["t"])
                estimado = len(f.get("texto", "")) / 14.0
                tope = (float(frases[i + 1]["t"]) if i + 1 < len(frases)
                        else dur_audio)
                ventanas.append((ini_s, min(ini_s + estimado, tope)))

            niveles_voz, faltantes = [], []
            for i, (ini_s, fin_s) in enumerate(ventanas):
                ini, fin = int(ini_s / paso), min(len(env), int(fin_s / paso))
                if ini >= len(env) or fin <= ini:
                    faltantes.append(i)
                    continue
                trozo = env[ini:fin]
                if float(trozo.max()) < UMBRAL_SILENCIO * 2.5:
                    faltantes.append(i)
                else:
                    niveles_voz.append(float(np.percentile(trozo, 80)))
            for i in faltantes:
                aud.registrar(
                    NIVEL_ERROR,
                    f"la frase {i} (segundo {frases[i]['t']}) no suena: la voz "
                    f"falta o está corrida")

            # zonas sin voz = música sola (con margen de 0.3 s por respiración)
            marca_voz = np.zeros(len(env), dtype=bool)
            for ini_s, fin_s in ventanas:
                ini = max(0, int((ini_s - 0.3) / paso))
                fin = min(len(env), int((fin_s + 0.3) / paso))
                marca_voz[ini:fin] = True

            # Las transiciones llevan riser y crash, fuertes A PROPÓSITO. Si se
            # cuentan como "música de fondo" el contraste sale falso y bajo.
            for frontera in datos.get("secciones", []):
                ini = max(0, int((float(frontera) - 0.8) / paso))
                fin = min(len(env), int((float(frontera) + 1.0) / paso))
                marca_voz[ini:fin] = True
            solo_musica = env[~marca_voz & (env > UMBRAL_SILENCIO)]
            if not niveles_voz:
                aud.medidas["Contraste voz/música"] = ("sin datos de voz", "—")
            elif len(solo_musica) <= 5:
                # nunca dejar pasar esto en silencio: que no se pueda medir es
                # información, no un aprobado
                aud.medidas["Voz vs música en pausas"] = (
                    "no medible", f"≥ {CONTRASTE_MIN_DB} dB")
                aud.registrar(
                    NIVEL_AVISO,
                    "no se pudo medir: la narración cubre casi todo el video y "
                    "no quedan pausas musicales. Deja 1-2 s de respiro entre "
                    "secciones")
            else:
                contraste = float(a_db(np.mean(niveles_voz))
                                  - a_db(np.percentile(solo_musica, 80)))
                aud.medidas["Voz vs música en pausas"] = (
                    f"{contraste:.1f} dB", f"≥ {CONTRASTE_MIN_DB} dB")
                if contraste < CONTRASTE_MIN_DB:
                    aud.registrar(
                        NIVEL_AVISO,
                        f"las pausas musicales pegan {abs(contraste):.1f} dB MÁS "
                        f"que la narración: bajar la música o subir el sidechain")
    return aud


def linea_para(video):
    """Busca la línea de tiempo que produjo ese video."""
    carpeta = RAIZ / "produccion" / "lineas_tiempo"
    if not carpeta.exists():
        return None
    objetivo = Path(video).name
    for ruta in carpeta.glob("*.json"):
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            continue
        if Path(datos.get("salida", "")).name == objetivo:
            return ruta
    return None


def main():
    parser = argparse.ArgumentParser(description="Auditor de audio de nemaxyz")
    parser.add_argument("video", nargs="?")
    parser.add_argument("--todos", action="store_true",
                        help="auditar todos los *_PUBLICAR.mp4")
    args = parser.parse_args()

    if args.todos:
        videos = sorted(RAIZ.glob("*/*_PUBLICAR.mp4"))
    elif args.video:
        videos = [Path(args.video)]
    else:
        parser.error("indica un video o usa --todos")

    hubo_error = False
    for video in videos:
        if not video.exists():
            print(f"[!] No existe: {video}")
            hubo_error = True
            continue
        print(f"\n== Audio de {video.name} ==")
        aud = auditar(video, linea_para(video))
        for k, (v, obj) in aud.medidas.items():
            print(f"   {k}: {v}   (objetivo {obj})")
        for h in sorted(aud.hallazgos, key=lambda x: x["nivel"] != NIVEL_ERROR):
            print(f"  [{h['nivel']}] {h['mensaje']}")
        reporte = RAIZ / "auditoria" / f"reporte_audio_{video.stem}.md"
        aud.escribir_reporte(reporte)
        estado = "RECHAZADO" if aud.errores() else "APROBADO"
        print(f"  -> {estado}: {len(aud.errores())} errores, "
              f"{len(aud.avisos())} avisos")
        hubo_error = hubo_error or bool(aud.errores())

    sys.exit(1 if hubo_error else 0)


if __name__ == "__main__":
    main()
