"""Pone la dirección del formulario del sorteo y el LinkedIn, y vuelve a armar la presentación.

    python armar/poner_datos.py --formulario "https://<cuenta>.app.n8n.cloud/form/..." --linkedin "https://www.linkedin.com/in/..."

Se puede pasar uno solo de los dos. Hace todo, en orden, y se corta en el primer error:

1. Escribe los datos en contenido/generar_deck.py (FORMULARIO y LINKEDIN) y el LinkedIn en README.md.
2. Genera el deck y el guion, y el QR del formulario (diseno/medios/D04/qr.json).
3. Vuelve a renderizar lo que cambia: con el formulario, D04 (el QR y la dirección), D05 y D14 (dejan
   de decir Anotarse al sorteo es un flujo y La lista la arma n8n, y pasan a Lo que acaban de hacer es un
   flujo y La lista la armó n8n). Con el LinkedIn, D15.
4. Lee el QR del cuadro final de D04 y comprueba que es la dirección. Corre el auditor de cuadros.
5. Arma todo (armar/armar.py todo --sin-render) y lo lleva a presentacion/ y videos/ (armar/entregar.py).

Este guion se corre con cualquier Python 3. Los pasos que lo necesitan usan el Python del entorno de la
charla (requirements.txt), que se busca en este orden: la variable CHARLA_PY, la clave "python" de
armar/entorno.local (un JSON que no va al repositorio), .venv/ en la raíz o, si no, el mismo Python
que corre este guion. Los módulos del QR (qrcode-generator y jsqr) se buscan en la variable QR_MODULOS
o en la clave "qr_modulos" de armar/entorno.local (ver diseno/medios/D04/generar_qr.mjs).

Con --sin-armar hace los pasos 1 a 4 y no toca presentacion/ ni videos/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GENERADOR = RAIZ / "contenido" / "generar_deck.py"
README = RAIZ / "README.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def decir(texto: str) -> None:
    print(texto, flush=True)


def entorno() -> tuple[str, str]:
    """El Python de la charla y la lista de carpetas de los módulos del QR."""
    local = {}
    archivo = RAIZ / "armar" / "entorno.local"
    if archivo.exists():
        local = json.loads(archivo.read_text(encoding="utf-8"))
    venv = RAIZ / ".venv" / "Scripts" / "python.exe"
    if not venv.exists():
        venv = RAIZ / ".venv" / "bin" / "python"
    py = os.environ.get("CHARLA_PY") or local.get("python") or (str(venv) if venv.exists() else sys.executable)
    qr = os.environ.get("QR_MODULOS") or os.pathsep.join(local.get("qr_modulos", []))
    return py, qr


def validar(nombre: str, valor: str, debe_tener: str) -> str:
    valor = valor.strip()
    if not re.fullmatch(r"https://[^\s\"'\\<>]+", valor):
        raise SystemExit(f"--{nombre}: tiene que ser una dirección completa que empiece con https:// y sin espacios: {valor!r}")
    if debe_tener not in valor:
        decir(f"AVISO: --{nombre} no dice {debe_tener}. Sigo igual: revisar que sea la dirección correcta ({valor}).")
    return valor


def escribir_constante(texto: str, nombre: str, valor: str) -> str:
    patron = re.compile(r'^(' + nombre + r' = )"[^"\n]*"', re.M)
    if len(patron.findall(texto)) != 1:
        raise SystemExit(f"no encuentro la línea {nombre} = \"...\" en contenido/generar_deck.py")
    return patron.sub(lambda m: m.group(1) + json.dumps(valor), texto)


def correr(titulo: str, comando: list[str], env: dict) -> None:
    decir(f"== {titulo}")
    t = time.time()
    r = subprocess.run(comando, cwd=RAIZ, env=env)
    if r.returncode != 0:
        raise SystemExit(f"FALLÓ: {titulo} (código {r.returncode}). No se tocó presentacion/ ni videos/.")
    decir(f"   {titulo}: bien en {time.time() - t:.0f} s")


def main() -> None:
    p = argparse.ArgumentParser(description="Pone el formulario del sorteo y el LinkedIn, y vuelve a armar la presentación.")
    p.add_argument("--formulario", help="dirección del formulario del flujo 4 publicado en n8n Cloud")
    p.add_argument("--linkedin", help="dirección del perfil de LinkedIn")
    p.add_argument("--sin-armar", action="store_true", help="solo el deck y los renders, sin presentacion/ ni videos/")
    a = p.parse_args()
    if not a.formulario and not a.linkedin:
        p.error("falta --formulario, --linkedin o los dos")

    t0 = time.time()
    formulario = validar("formulario", a.formulario, "/form") if a.formulario else None
    linkedin = validar("linkedin", a.linkedin, "linkedin.com/") if a.linkedin else None
    py, qr_modulos = entorno()
    env = dict(os.environ, PYTHONUTF8="1")
    if qr_modulos:
        env["QR_MODULOS"] = qr_modulos

    # 1. Los datos, en la fuente del deck y en el README.
    decir("== datos")
    fuente = GENERADOR.read_bytes().decode("utf-8")
    if formulario:
        fuente = escribir_constante(fuente, "FORMULARIO", formulario)
        decir(f"   formulario: {formulario}")
    if linkedin:
        fuente = escribir_constante(fuente, "LINKEDIN", linkedin)
        decir(f"   LinkedIn: {linkedin}")
    GENERADOR.write_bytes(fuente.encode("utf-8"))
    if linkedin and README.exists():
        readme = README.read_bytes().decode("utf-8")
        if "LINKEDIN_PENDIENTE" in readme:
            README.write_bytes(readme.replace("LINKEDIN_PENDIENTE", linkedin).encode("utf-8"))
            decir("   README.md: LinkedIn puesto")

    # 2. El deck, el guion y el QR.
    correr("deck y guion", [py, str(GENERADOR)], env)
    if formulario:
        correr("QR del formulario", ["node", "diseno/medios/D04/generar_qr.mjs"], env)

    # 3. Los renders de lo que cambia.
    remotion = (["D04", "D14"] if formulario else []) + (["D15"] if linkedin else [])
    correr("render de " + " ".join(remotion), ["node", "remotion/render.mjs", *remotion], env)
    if formulario:
        correr("render de D05", [py, "manim/render_diapo.py", "D05"], env)

    # 4. Los controles.
    if formulario:
        correr("el QR del cuadro final de D04", ["node", "diseno/medios/D04/generar_qr.mjs", "--comprobar", "render/cuadros/D04_1.png"], env)
    renderizadas = sorted(remotion + (["D05"] if formulario else []))
    correr("auditor de cuadros de " + " ".join(renderizadas), [py, "armar/auditar_cuadros.py", *renderizadas], env)

    if a.sin_armar:
        decir(f"LISTO sin armar, en {time.time() - t0:.0f} s. Mirar render/cuadros/D04_1.png y D15_2.png.")
        return

    # 5. El armado entero y los entregables.
    correr("armado entero", [py, "armar/armar.py", "todo", "--sin-render"], env)
    correr("presentacion/ y videos/", [py, "armar/entregar.py"], env)

    minutos = (time.time() - t0) / 60
    decir(f"LISTO en {minutos:.1f} minutos.")
    decir("Mirar render/cuadros/D04_1.png y D15_2.png, y escanear el QR del paso 6 con un celular desde el fondo de la sala.")
    decir("Para guardarlo: git add contenido diseno/medios/D04/qr.json presentacion videos README.md y un commit.")


if __name__ == "__main__":
    main()
