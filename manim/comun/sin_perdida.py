"""Videos de Manim sin pérdida, para que las fronteras entre pasos sean exactas.

Manim 0.19.2 codifica cada animación con libx264, crf 23 y yuv420p, y después
solo pega esos pedazos: cada sección sale con pérdida y sin etiqueta de color.
Medido el 22-oct-2026 con .tmp/prueba_manim.py: el último cuadro de la sección
1 y el primero de la 2 quedan "iguales a la vista" pero no idénticos (máx. 58
de diferencia, PSNR 47 dB), y PowerPoint puede leer los colores con otra matriz
que el póster.

Con `activar()` los pedazos salen en H.264 RGB sin pérdida (libx264rgb, qp 0).
Las secciones se siguen armando igual (Manim solo pega los pedazos), y el paso
a la entrega (BT.709, QP 16, cuadro clave en el último cuadro, faststart) lo
hace `armar/codificar_paso.py`, con la misma receta que Remotion.

Uso, a nivel de módulo y después de `configurar_horizontal`:

    from sin_perdida import activar
    activar()

Los pedazos sin pérdida van a otra carpeta de caché (`partial_movie_files_sp`):
Manim reutiliza un pedazo si su hash coincide, y el hash no incluye el códec,
así que sin esto mezclaría pedazos viejos con pérdida. Pesan unas 5 veces
más que el paso entregado (medido: 957 KB y 2,1 MB contra 211 y 397 KB), pero
viven en media/ o render/, que no van al repo.
"""

from queue import Queue
from threading import Thread

import av
from manim import config
from manim.scene import scene_file_writer as sfw

_ORIGINAL = sfw.SceneFileWriter.open_partial_movie_stream


def _abrir_sin_perdida(self, file_path=None):
    """Copia de SceneFileWriter.open_partial_movie_stream (Manim 0.19.2) con otro
    códec: libx264rgb a qp 0 en vez de libx264 a crf 23 en yuv420p."""
    if file_path is None:
        file_path = self.partial_movie_files[self.renderer.num_plays]
    self.partial_movie_file_path = file_path

    contenedor = av.open(file_path, mode="w")
    stream = contenedor.add_stream(
        "libx264rgb",
        rate=sfw.to_av_frame_rate(config.frame_rate),
        options={"an": "1", "qp": "0", "preset": "veryfast"},
    )
    stream.pix_fmt = "rgb24"
    stream.width = config.pixel_width
    stream.height = config.pixel_height

    self.video_container = contenedor
    self.video_stream = stream
    self.queue = Queue()
    self.writer_thread = Thread(target=self.listen_and_write, args=())
    self.writer_thread.start()


def activar():
    if config.transparent or config.movie_file_extension != ".mp4":
        raise RuntimeError("sin_perdida: solo para .mp4 opaco (sin --transparent ni --format webm/gif)")
    config.partial_movie_dir = "{video_dir}/partial_movie_files_sp/{scene_name}"
    sfw.SceneFileWriter.open_partial_movie_stream = _abrir_sin_perdida


def desactivar():
    sfw.SceneFileWriter.open_partial_movie_stream = _ORIGINAL
