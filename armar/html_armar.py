"""La presentación en HTML: un solo archivo que funciona sin internet.

Los videos van adentro, en base64, cada uno en un <script type="application/
octet-stream"> que el navegador no ejecuta; el reproductor los convierte en Blob
recién cuando hacen falta (el paso actual, el siguiente y unos pocos más) y
suelta la memoria de los que quedan lejos. Las miniaturas del último cuadro de
cada paso (para la vista del orador) y las notas van en un JSON.

El reproductor está en armar/plantillas/presentacion.html (teclas, vista del
orador, pantalla negra, precarga sin parpadeo); acá solo se completa.
"""

from __future__ import annotations

import base64
import html
import io
import json
from pathlib import Path

from PIL import Image

PLANTILLA = Path(__file__).resolve().parent / "plantillas" / "presentacion.html"


def miniatura(png: Path, ancho=640, calidad=80) -> str:
    im = Image.open(png).convert("RGB")
    im = im.resize((ancho, round(ancho * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=calidad, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def construir(pasos, videos: list[Path], ultimos: list[Path], destino: Path, meta: dict,
              plan: dict[str, float] | None = None) -> dict:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    datos = {"titulo": meta.get("titulo", ""), "pasos": []}
    for i, (p, png) in enumerate(zip(pasos, ultimos), start=1):
        datos["pasos"].append({
            "n": i, "id": p.id, "etiqueta": p.etiqueta, "diapo": p.diapo.id, "titulo": p.diapo.titulo,
            "seccion": p.diapo.seccion, "notas": p.notas_pptx, "duracion": p.duracion, "audio": bool(p.dings),
            "mini": miniatura(png), "plan": (plan or {}).get(p.id),
        })
    json_datos = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    titulo = html.escape(meta.get("titulo", ""))
    cabeza, cola = plantilla.split("<!--__VIDEOS__-->")
    cabeza = (cabeza.replace("__TITULO__", titulo).replace("__AUTOR__", html.escape(meta.get("autor", "")))
              .replace("__DATOS__", json_datos))
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.stem + ".escribiendo.html")
    total_video = 0
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza)
        for i, v in enumerate(videos, start=1):
            b = Path(v).read_bytes()
            total_video += len(b)
            f.write(f'<script type="application/octet-stream" id="v{i}">')
            f.write(base64.b64encode(b).decode("ascii"))
            f.write("</script>\n")
        f.write(cola)
    tmp.replace(destino)
    return {"archivo": str(destino), "pasos": len(pasos), "bytes": destino.stat().st_size, "bytes_video": total_video}
