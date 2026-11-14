# Fuente única del guion y del deck de la charla. Genera contenido/deck.json y contenido/guion.md.
# Para cambiar un texto, una nota o un enlace (REPO, LINKEDIN, FORMULARIO), se cambia acá y se vuelve a
# correr. Después se renderizan de nuevo las diapositivas que usan lo que cambió.
# Correr con el Python del entorno de la charla (requirements.txt): PYTHONUTF8=1 python contenido/generar_deck.py
#
# LINKEDIN y FORMULARIO los pone armar/poner_datos.py, que además vuelve a armar todo. Vacíos, la charla
# igual se puede presentar: D04 anuncia el sorteo sin QR, D05 y D14 no dan por hecho que la sala se anotó
# con el formulario y en D15 va tinkazo.app en el renglón del LinkedIn.
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PPM = 140  # palabras por minuto al hablar

REPO = "github.com/nema1502/superpoderes-n8n"
LINKEDIN = "https://www.linkedin.com/in/nicolas-mejia-agreda"  # la dirección del perfil de LinkedIn (https://www.linkedin.com/in/...)
FORMULARIO = ""  # la dirección del formulario del flujo 4 publicado en n8n Cloud


def sin_esquema(direccion):
    """La dirección como se lee en pantalla: sin https://, sin www. y sin la barra del final."""
    return re.sub(r"^https?://(www\.)?", "", direccion).rstrip("/")


CON_FORMULARIO = bool(FORMULARIO)
CON_LINKEDIN = bool(LINKEDIN)

ENLACES = {
    "_doc": "Direcciones que usan las diapositivas. Los QR se generan desde acá (D04: formulario_sorteo. D13 y D15: repositorio). Mientras formulario_sorteo diga FORMULARIO_PENDIENTE, D04 anuncia el sorteo sin QR. El formulario y el LinkedIn los pone armar/poner_datos.py.",
    "formulario_sorteo": FORMULARIO or "FORMULARIO_PENDIENTE",
    "repositorio": "https://" + REPO,
    "linkedin": LINKEDIN,
    "n8n_prueba": "https://app.n8n.cloud/register",
    "serpapi_registro": "https://serpapi.com/users/sign_up",
    "serpapi_llave": "https://serpapi.com/manage-api-key",
    "ai_studio": "https://aistudio.google.com/apikey",
    "tinkazo": "https://tinkazo.app",
}

ESTILO_NODO = (
    "Nodo de flujo (el mismo en Remotion y en Manim, en toda la charla): cuadrado redondeado (radio 32 px) "
    "relleno noche, borde azul de 5 px, ícono en hueso al 45 % del lado, rótulo debajo a 60 px en hueso "
    "(49 px si no entra). Conexiones: línea azul de 5 px. Las conexiones de herramientas y memoria de un "
    "agente van a trazos (16 px de trazo y 12 de hueco), como en el editor de n8n. El dato que viaja es "
    "ámbar (un círculo de 28 px o una pastilla con el texto). Íconos de manim/comun/iconos."
)

LLAMA = (
    "La llama de Tinkazo: el archivo diseno/logos/tinkazo/llama-oscuro.svg tal cual (magenta #ff5cb3), o "
    "dibujada con los nueve rectángulos de contenido/tinkazo.md 4.1 en el mismo magenta si tiene que caminar "
    "(las patas se alternan de a pares). Sin cara, sin ojos, sin sombrero. Girada unos 3 grados. Si lleva "
    "sombra, dura y sin desenfoque."
)

FUNDIDO = lambda desde: {"tipo": "fundido", "duracion_s": 0.4, "desde": desde}

D = []  # diapositivas


def diapo(id_, nombre, titulo, motor, entrada, objetivo, pasos, seccion="principal"):
    D.append(dict(id=id_, nombre=nombre, titulo=titulo, seccion=seccion, motor=motor, piso=None,
                  entrada=entrada, objetivo=objetivo, pasos=pasos))


def paso(texto, visual, notas, dura, fuente=None, recortable=None, espera=0.0):
    return dict(texto_pantalla=texto, visual=visual, notas=notas, fuente=fuente, recortable=recortable,
                espera_s=espera, duracion_animacion_s=dura, audio=None)


# ------------------------------------------------------------------ D01
diapo("D01", "Portada", "Portada", "remotion", {"tipo": "corte", "duracion_s": 0, "desde": None},
      "Mientras entra la gente, la sala ya sabe de qué trata, dónde está y quién habla.",
      [paso(
          ["Dale superpoderes", "a tus automatizaciones", "n8n + SerpApi + IA", "Space Talks",
           "Hackathon NASA Space Apps 2026, Santa Cruz", "Nicolás Emir Mejía Agreda"],
          "Entra desde tinta (es el primer video). Animación (4,0 s): fondo tinta. Desde el borde derecho entran "
          "líneas de circuito en azul (trazo de 3 px, tramos rectos y a 45 grados, cada una termina en un punto "
          "de 10 px), se dibujan en 0,8 s con useTramo y quedan al 35 %: es el guiño al afiche. Las líneas "
          "desembocan en tres nodos chicos (96 px, con el estilo de nodo de la charla) en columna a la derecha "
          "(x 1640, y 300, 470 y 640), con una lupa, un cerebro y unos engranajes. Un punto ámbar recorre las "
          "tres conexiones una vez (1,0 s). A la izquierda, el título entra palabra por palabra (useEntrarPalabras, "
          "desfase 0,12 s), después sube n8n + SerpApi + IA (0,4 s), después el pie con un fundido y el isotipo se "
          "dibuja de un trazo (0,8 s). Cuadro final: desde x 160, alineado a la izquierda: Dale superpoderes en "
          "titulo a 120 px en y 300 y a tus automatizaciones en titulo a 104 px en y 425 (los dos renglones son "
          "el único título del cuadro). n8n + SerpApi + IA en hueso a 72 px en y 560, con los dos signos más en "
          "azul. Space Talks en gris a 60 px en y 720 y Hackathon NASA Space Apps 2026, Santa Cruz en gris a 49 px "
          "en y 790. Firma en y 960: isotipo lima de 48 px y Nicolás Emir Mejía Agreda en hueso a 60 px. Los "
          "logos de NASA Space Apps Santa Cruz y de la UCB van solo si están los archivos del afiche, "
          "como aparecen en el afiche, abajo a la derecha (x 1450 a 1850, y 930 a 1010). Sin marca de agua.",
          "[Quieta mientras entra la gente. No se dice nada. Probar el clicker y el micrófono. En otra ventana, "
          "abiertos y con la sesión iniciada: la cuenta de n8n Cloud con los flujos 1, 3 y 4 publicados y el 2 "
          "abierto en el editor (se usa con Open chat), el reto de ejemplo copiado en la pestaña del flujo 3, la "
          "ejecución de ensayo de cada uno y tinkazo.app en modo Prueba con la Cuenta de prueba. El celular con "
          "datos, por si se cae la red. Cuando la sala esté lista: CLIC y empezar.]",
          4.0)])

# ------------------------------------------------------------------ D02
diapo("D02", "CuarentaYOchoHoras", "Les quedan 32 horas", "remotion", FUNDIDO("D01"),
      "El gancho: el tiempo del hackathon es corto y una parte se va en tareas repetidas. Sin dar un número "
      "inventado, la sala siente el problema y queda planteada la promesa: que eso lo haga un flujo.",
      [paso(
          ["32:00:00", "Les quedan 32 horas."],
          "Entra con un fundido de 0,4 s desde D01. Animación (2,4 s): el visor de 7 segmentos (Visor7) enciende "
          "32:00:00 segmento por segmento, de izquierda a derecha (encendido 0 a 1, 1,2 s), con el 8 fantasma "
          "apagado al 8 %. Después sube Les quedan 32 horas. (useEntrar, 0,4 s). Cuadro final: el visor ámbar "
          "de 200 px de alto centrado en (960, 430). Les quedan 32 horas. en hueso a 88 px en y 720, centrado, "
          "con 32 horas en ámbar. Marca de agua. Nada parpadea al final.",
          "Buenas tardes. Arranco con una cuenta. El envío de proyectos cierra mañana domingo, a las once y "
          "cincuenta y nueve de la noche. [Señalar el reloj.] Les quedan unas treinta y dos horas para pasar de una idea a algo que funcione. "
          "Parece mucho. Hasta que uno empieza. [Si la charla empieza mucho más tarde de las 16:00, decir las "
          "horas que queden de verdad.]",
          3.1,
          fuente="El envío de proyectos del hackathon abre el sábado 14 de noviembre a las 9:00 y cierra el domingo 15 a las 23:59, hora de Bolivia (sitio de NASA Space Apps Santa Cruz, https://spaceappssantacruz.web.app/, investigación). De las 16:00 del sábado a ese cierre hay 32 horas, redondeando."),
       paso(
          ["¿Cuántas se van en buscar, copiar y pegar?", "buscar", "copiar", "pegar", "resumir", "avisar",
           "otra vez"],
          "Animación (3,4 s): el visor se achica y sube (escala a 0,45, a y 150, 0,5 s). Debajo aparece una grilla "
          "de 32 cuadrados, uno por hora (8 columnas por 4 filas, cuadrados de 110 px con 16 px de aire, relleno "
          "noche y borde azul al 40 %, de x 464 a 1456 y de y 400 a 888), de a uno con desfase de 0,02 s. Sube la "
          "pregunta (0,4 s). Después caen seis pastillas (Pastilla, borde hueso al 40 %, 60 px) sobre la grilla, "
          "de a una con desfase de 0,15 s y un golpe chico: buscar, copiar, pegar, resumir, avisar y otra vez. "
          "Los cuadrados que tapa cada pastilla pasan a gris al 30 % (0,3 s): son horas que se van. Las posiciones "
          "salen de una semilla fija. Cuadro final: visor chico arriba, la pregunta en hueso a 72 px en y 300, "
          "centrada, y la grilla con las seis pastillas encima y cerca de la mitad de las horas apagadas. Marca "
          "de agua.",
          "¿Cuántas de esas horas se van a ir en buscar información, copiar, pegar, resumir y avisarle al resto "
          "del equipo? [ESPERAR. Que la sala piense.] No les voy a dar un número, porque no lo sé. Pero cada uno "
          "sabe que son más de las que le gustaría.",
          3.7, espera=3),
       paso(
          ["Eso lo puede hacer un flujo."],
          "Animación (3,2 s): las seis pastillas se ordenan en una fila en y 560 (resorte, 0,6 s) y se vuelven "
          "nodos con el estilo de la charla (120 px, con su palabra debajo a 49 px). Entre ellos se dibujan las "
          "conexiones azules (0,5 s) y un punto ámbar recorre la fila una vez (1,0 s). Mientras pasa, los cuadros "
          "apagados de la grilla vuelven a su color y la grilla entera baja al 25 % detrás. Sube la frase (0,4 s). "
          "Cuadro final: la fila de seis nodos conectados en y 560, la grilla tenue detrás, y Eso lo puede hacer "
          "un flujo. en hueso a 88 px en y 790, centrada, con un flujo en ámbar. Marca de agua.",
          "Buena noticia: casi todo eso es repetir pasos. Y lo que se repite, lo puede hacer una automatización. "
          "Hoy les voy a mostrar cómo darle a una automatización dos superpoderes: ver lo que pasa en internet y "
          "pensar qué hacer con eso.",
          3.5)])

# ------------------------------------------------------------------ D03
diapo("D03", "QuienHabla", "Quién les habla", "remotion", FUNDIDO("D02"),
      "Quién es el orador y por qué habla de n8n: embajador de su comunidad en Bolivia, estuvo en In the Loop y "
      "construyó Tinkazo, que se usa al final. Primera aparición de la llama.",
      [paso(
          ["Nicolás Emir Mejía Agreda", "nemaxyz", "Embajador de la comunidad de n8n en Bolivia",
           "n8n In the Loop, Berlín 2026", "Fundador de Tinkazo", "19 eventos de tecnología organizados"],
          "Entra con un fundido de 0,4 s desde D02. Animación (3,0 s): el nombre entra (useEntrar, 0,5 s), el "
          "isotipo se dibuja de un trazo (0,8 s) junto a nemaxyz, y las cuatro líneas suben de a una (desfase "
          "0,2 s), cada una con un cuadradito azul de 16 px a la izquierda. Al llegar la línea de Tinkazo, la llama "
          "aparece al final del renglón con un golpe chico. Cuadro final: desde x 160, Nicolás Emir Mejía Agreda "
          "en titulo a 88 px en y 230. Isotipo lima de 48 px y nemaxyz en hueso a 49 px en y 320. Las cuatro "
          "líneas en hueso a 60 px desde x 220 (el cuadradito en x 170), en y 470, 570, 670 y 770. Al final de la "
          "primera línea, el símbolo de n8n (n8n-symbol-accent.svg, 56 px de alto, a 30 px del texto). Al final "
          "de la tercera, la llama (" + LLAMA + ") de 80 px de alto. En ámbar, como mucho dos palabras: n8n de la "
          "primera línea y Tinkazo. Sin marca de agua (el isotipo ya está).",
          "Soy Nicolás Emir Mejía Agreda, en redes nemaxyz. Soy embajador de la comunidad de n8n en Bolivia, y en "
          "octubre estuve en In the Loop, la conferencia de n8n en Berlín. Organicé diecinueve eventos de "
          "tecnología y fundé Tinkazo, una herramienta para hacer sorteos que cualquiera puede comprobar. "
          "Guárdense ese nombre, que al final lo vamos a usar. No vengo a venderles nada. Vengo a mostrarles "
          "flujos que pueden copiar hoy mismo, gratis.",
          3.4,
          fuente="La bio de la charla de octubre de 2026: 19 eventos de tecnología organizados (el número de su perfil de Luma en octubre) y Fundador de Tinkazo. Embajador de la comunidad de n8n en Bolivia y n8n In the Loop, la conferencia de n8n en Berlín, en octubre de 2026.",
          recortable="si quien presenta ya leyó la bio, decir solo la primera y las dos últimas frases (menos 15 s)")])

# ------------------------------------------------------------------ D04
diapo("D04", "AnotateAlSorteo", "Anotate al sorteo", "remotion", FUNDIDO("D03"),
      "El público se anota desde el celular en el formulario de n8n mientras empieza la charla. Así llega "
      "enganchado al final, y lo que acaba de llenar sirve para explicar qué es un flujo.",
      [paso(
          (["Al final hay sorteo.", "Escaneá y anotate", "Palabra de la charla:", "llama",
            "Participar es gratis.", sin_esquema(FORMULARIO)] if CON_FORMULARIO else
           ["Al final hay sorteo.", "Palabra de la charla:", "llama", "Participar es gratis."]),
          "Entra con un fundido de 0,4 s desde D03. Animación (3,2 s): el título entra (useEntrar, 0,5 s). A la "
          "derecha sube una tarjeta hueso de 600 por 600 px (escala de 0,9 a 1, 0,5 s) y adentro aparece el QR "
          "(fundido, 0,3 s). Las líneas de la izquierda suben de a una (desfase 0,15 s). La llama entra caminando "
          "desde el borde izquierdo de la tarjeta, por abajo (1,2 s, cuatro pasos) y se queda parada junto a su "
          "esquina inferior izquierda, sin tapar el QR. Cuadro final: desde x 140, Al final hay sorteo. en titulo "
          "a 104 px en y 200. Escaneá y anotate en hueso a 72 px en y 330. Palabra de la charla: en hueso a 60 px "
          "en y 470 y llama en ámbar a 104 px en y 580. Participar es gratis. en gris a 60 px en y 720. A la "
          "derecha, la tarjeta hueso de x 1200 a 1800 y de y 120 a 720, con el QR en tinta adentro y su margen "
          "blanco de 4 módulos (las reglas de QR de Tinkazo: oscuro sobre claro, nunca invertido, sin logo "
          "encima). Debajo, centrada en x 1500, la dirección escrita sin https:// en hueso a 49 px en y 790 (en "
          "dos renglones si no entra). La llama "
          "(" + LLAMA + ") de 300 px de alto, parada junto a la esquina de abajo a la izquierda de la tarjeta. "
          "El QR codifica enlaces.formulario_sorteo del deck. Sin formulario (mientras enlaces.formulario_sorteo "
          "diga FORMULARIO_PENDIENTE), la diapositiva anuncia el sorteo sin QR: no hay tarjeta ni dirección ni "
          "Escaneá y anotate. Desde x 140, Al final hay sorteo. en titulo a 104 px en y 240, Palabra de la "
          "charla: en hueso a 60 px en y 440, llama en ámbar a 104 px en y 550 y Participar es gratis. en gris a "
          "60 px en y 700. La llama de 560 px de alto entra caminando desde el borde derecho (1,2 s, cuatro "
          "pasos), se para con las patas en y 820 y centrada en x 1440, y se da vuelta como en la marca. Marca "
          "de agua.",
          ("Y ya que hablamos de sorteos: al final de la charla vamos a sortear [DECIR EL PREMIO] entre los que "
           "estén acá. Para entrar, escaneen este código y pongan su nombre y apellido, o un apodo que nadie más use, y la palabra de la charla, "
           "que es llama. [Señalar la palabra.] Su nombre va a salir en la pantalla, así que pongan algo que no les "
           "moleste mostrar. Participar es gratis y no tienen que crear ninguna cuenta. [Dejar el QR unos 40 "
           "segundos. Si alguien no puede escanear, leer la dirección.] Mientras se anotan, les cuento un secreto: "
           "eso que están llenando ya es una automatización." if CON_FORMULARIO else
           "Y ya que hablamos de sorteos: al final de la charla vamos a sortear [DECIR EL PREMIO] entre los que "
           "estén acá. Participar es gratis y no tienen que crear ninguna cuenta. Guarden la palabra de la charla, "
           "que es llama. [Señalar la palabra. Si el flujo 4 está publicado, mostrar en la otra pestaña, a pantalla "
           "completa, el PNG del QR de su formulario que se bajó de Chrome en la mañana, y pedir nombre y apellido, o un apodo que nadie más "
           "use, y la palabra. Dejarlo unos 40 segundos. Si no está publicado, al final se anotan levantando la "
           "mano.] Y les cuento un secreto: anotarse a un sorteo así ya es una automatización."),
          4.0, espera=40,
          fuente="La palabra de la charla y el formulario: workflows/ESPEC.md, workflow 4. Participar es gratis: regla de Tinkazo (contenido/tinkazo.md).")])

# ------------------------------------------------------------------ D05
diapo("D05", "QueEsUnFlujo", "Qué es n8n", "manim", FUNDIDO("D04"),
      "n8n mostrado como un flujo que se arma: el mismo que la sala acaba de usar. Disparador, pasos y un dato "
      "que viaja. Al final, dos datos que dicen que no es un juguete.",
      [paso(
          [("Lo que acaban de hacer es un flujo" if CON_FORMULARIO else "Anotarse al sorteo es un flujo"),
           "Formulario", "Revisar palabra", "Limpiar", "Guardar", "Ana"],
          "Entra con un fundido de 0,4 s desde D04. " + ESTILO_NODO + " Animación (4,6 s): el título entra "
          "(Entrar, 0,4 s). Los cuatro nodos entran de a uno de izquierda a derecha (Entrar, desfase 0,2 s) con "
          "sus íconos: mobile-screen-button, list-check, wand-magic-sparkles y table. Las conexiones se dibujan "
          "(Trazo, 0,4 s). Después una pastilla ámbar con el texto Ana sale del celular del primer nodo y viaja "
          "por las conexiones (Desplazar, 2,0 s en total): cada nodo late cuando pasa (Latido). Al llegar al "
          "último, la pastilla baja y queda como una fila de una tablita debajo de Guardar. Cuadro final: el "
          "título en titulo a 72 px en y 200, centrado. Cuatro nodos de 200 px en y 520, con centros en x 270, "
          "730, 1190 y 1650, y sus rótulos a 49 px en y 680. Debajo de Guardar, una tablita de 280 por 70 px "
          "(borde hueso al 40 %) con Ana en ámbar a 49 px en y 790. El título es Lo que acaban de hacer es un "
          "flujo si el deck tiene la dirección del formulario, y Anotarse al sorteo es un flujo si no la tiene. "
          "Marca de agua.",
          ("Lo que acaban de hacer es un flujo de n8n." if CON_FORMULARIO else
           "Anotarse al sorteo es un flujo de n8n. [Si se anotaron con el QR, decir: lo que acaban de hacer es un "
           "flujo.]") +
          " Un formulario recibe su nombre. Un paso revisa que la "
          "palabra sea la correcta. Otro limpia el nombre: le saca espacios de más y comas. Y el último lo guarda "
          "en una tabla. [Señalar la pastilla que viaja.] Su nombre pasa de un paso al siguiente, como una pelota "
          "que se pasan entre amigos.",
          5.3),
       paso(
          ["disparador", "pasos", "Cada paso hace una sola cosa."],
          "Animación (2,8 s): el título baja al 60 % (Foco, 0,3 s). Debajo del primer nodo se dibuja un corchete "
          "(0,4 s) con disparador en ámbar a 60 px en y 760. Debajo de los otros tres, un corchete largo con pasos "
          "en hueso a 60 px en y 760. La tablita se desvanece antes (0,3 s) para dejar lugar. Sube la frase "
          "(Entrar, 0,4 s). Cuadro final: los nodos igual, los dos corchetes con sus rótulos en y 760, y Cada paso "
          "hace una sola cosa. en hueso a 72 px en y 870, centrada. Marca de agua.",
          "Eso es n8n: bloques que se conectan. El primero es el disparador, lo que hace arrancar todo: un "
          "formulario, un mensaje, una hora del día. Los demás son pasos, y cada uno hace una sola cosa. Se arma "
          "arrastrando bloques, y si algo no existe, se escribe en un bloque de código.",
          3.1),
       paso(
          ["n8n", "más de 210 mil estrellas en GitHub", "más de 500 integraciones propias",
           "en la nube o en tu compu", "n8n.io y GitHub, 13 de noviembre de 2026"],
          "Animación (3,0 s): el flujo entero se achica a 0,55 y sube hasta y 230 (Desplazar, 0,6 s), los "
          "corchetes y la frase se desvanecen. En el centro aparece el logo de n8n (diseno/logos/n8n/"
          "n8n-logo-white-accent.svg, 110 px de alto, en y 450), tal cual, sin recolorear. Debajo suben las tres "
          "líneas (desfase 0,2 s). Cuadro final: el flujo chico arriba, el logo, más de 210 mil estrellas en "
          "GitHub en hueso a 72 px en y 620 con 210 mil en ámbar, más de 500 integraciones propias en hueso a "
          "72 px en y 720 con 500 en ámbar, en la nube o en tu compu en gris a 60 px en y 820, y la fuente en gris "
          "a 49 px en y 990. El logo dice n8n. Marca de agua.",
          "Y no es un juguete. n8n tiene más de doscientas diez mil estrellas en GitHub y más de quinientas "
          "integraciones propias. Y lo pueden usar en la nube o instalarlo en su propia compu.",
          3.3,
          fuente="210.423 estrellas en la API de GitHub el 13-nov-2026 (https://api.github.com/repos/n8n-io/n8n) y 500+ native integrations en la portada de n8n (https://n8n.io/). Investigación, punto 7.",
          recortable="saltar este paso (menos 15 s)")])

# ------------------------------------------------------------------ D06
diapo("D06", "DosSuperpoderes", "Ver, pensar, hacer", "remotion", FUNDIDO("D05"),
      "La revelación: un flujo común solo hace. Se le suman dos superpoderes, ver (SerpApi) y pensar (un modelo "
      "de IA). Aparece la idea clave por primera vez.",
      [paso(
          ["Un flujo común solo hace.", "No ve lo que pasa en internet.", "No piensa."],
          "Entra con un fundido de 0,4 s desde D05. Animación (2,6 s): arriba, el flujo de cuatro nodos de D05 "
          "redibujado chico (100 px, en y 230) y en Foco. Sube Un flujo común solo hace. (useEntrar, 0,4 s). "
          "Después, de a una, las dos líneas con una cruz roja pegada a su izquierda (la cruz se dibuja, 0,3 s, "
          "con el grosor del asta del texto). Cuadro final: el flujo chico arriba, Un flujo común solo hace. en "
          "titulo a 88 px en y 460, centrado. No ve lo que pasa en internet. y No piensa. en hueso a 72 px en y 620 "
          "y 730, alineadas a la izquierda desde x 520, cada una con su cruz roja de 50 px en x 450. Marca de agua.",
          "Pero un flujo común tiene un límite. Hace exactamente lo que le dijeron, siempre igual. No sabe qué "
          "está pasando afuera, en internet. Y no piensa: si llega algo raro, no sabe qué hacer.",
          3.3),
       paso(
          ["Dos superpoderes", "VER", "PENSAR", "HACER", "IA"],
          "Animación (4,2 s): todo lo anterior se desvanece (0,3 s). Sube Dos superpoderes (0,4 s). Primero "
          "aparece el nodo de la derecha, HACER, tranquilo (fundido, 0,3 s): es el que ya existía. Después entran "
          "VER y PENSAR con un golpe (escala 1,25 a 1, 0,5 s, desfase 0,3 s) y las dos conexiones azules se "
          "dibujan como pistas de circuito (0,5 s). Al final un punto ámbar recorre VER, PENSAR y HACER (1,2 s) y "
          "cada nodo late cuando pasa. Cuadro final: Dos superpoderes en titulo a 104 px en y 170, centrado. Tres "
          "nodos de 280 px con el estilo de la charla en y 480, con centros en x 420, 960 y 1500. Íconos de "
          "140 px: magnifying-glass, brain y gears. Debajo de cada uno, su verbo en hueso a 72 px en y 700 (VER, "
          "PENSAR, HACER) y, en y 800, lo que lo da: el logo de SerpApi (diseno/logos/serpapi/"
          "logo-with-wordmark-white.svg, 64 px de alto), IA en hueso a 72 px y el logo de n8n (n8n-logo-white-"
          "accent.svg, 64 px de alto). Los logos van tal cual, sin recolorear, con su espacio libre. Marca de agua.",
          "Hoy le vamos a dar dos superpoderes. Ojos, para ver lo que pasa en internet ahora mismo: eso es "
          "SerpApi. Y cabeza, para pensar y decidir: eso es un modelo de inteligencia artificial. Y n8n, que ya "
          "sabía hacer, ahora hace con lo que vio y con lo que pensó.",
          4.2),
       paso(
          ["Que el flujo vea, piense y haga."],
          "Animación (2,8 s): los tres nodos se achican a 140 px y suben hasta y 300 con sus verbos debajo a "
          "49 px (los logos se desvanecen, 0,3 s). Sube la idea (useEntrar, 0,5 s) y la cruza un barrido de luz "
          "una vez (BarridoLuz, 0,5 s). Cuadro final: los tres nodos chicos conectados en y 300, y Que el flujo "
          "vea, piense y haga. en hueso a 88 px en y 640, centrada, con vea, piense y haga en ámbar. Marca de agua.",
          "Si se llevan una sola frase de hoy, que sea esta. [Pausa.] Que el flujo vea, piense y haga.",
          2.8, espera=2)])

# ------------------------------------------------------------------ D07
diapo("D07", "Ver", "Primer superpoder: ver", "manim", FUNDIDO("D06"),
      "SerpApi hace la búsqueda en Google por el flujo y la devuelve ordenada. Un ejemplo real de anoche y los "
      "motores que trae el nodo.",
      [paso(
          ["Ver", "Busca en Google por vos y te lo devuelve ordenado.", "café", "centro de Santa Cruz", "Google",
           "\"title\": \"Sitcom Café\"", "\"rating\": 4.7", "\"reviews\": 122"],
          "Entra con un fundido de 0,4 s desde D06. " + ESTILO_NODO + " Animación (4,2 s): Ver entra con el ícono "
          "de la lupa a su izquierda (Entrar, 0,4 s) y debajo la frase. En y 470: una caja de búsqueda de 620 por "
          "100 px (borde hueso al 40 %, radio 50) donde café se escribe letra por letra (0,6 s) y, a su derecha, "
          "una pastilla gris con centro de Santa Cruz. Una línea azul lleva el punto ámbar a un nodo con el ícono "
          "de SerpApi (diseno/logos/serpapi/logo-white.svg) y de ahí a un nodo con el ícono globe rotulado Google "
          "(1,2 s). El punto vuelve por una segunda línea, abajo, y al llegar se abren tres líneas de datos, de a "
          "una (desfase 0,15 s). Cuadro final: Ver en titulo a 104 px en (230, 170) con la lupa de 90 px en x 160. "
          "La frase en hueso a 60 px en y 290 desde x 160. La caja con café (hueso, 60 px) en x 160 a 780, y 470, "
          "la pastilla a su derecha, el nodo de SerpApi (160 px) en x 1260 y el de Google (160 px) en x 1640, en "
          "y 470. Las tres líneas de datos en gris a 49 px desde x 400, en y 690, 750 y 810, con las comillas "
          "rectas tal cual. Marca de agua.",
          "Primer superpoder: ver. Google está hecho para personas, no para programas. SerpApi hace la búsqueda "
          "en Google por ustedes y les devuelve los resultados ordenados, listos para usar en un flujo.",
          4.9,
          fuente="Qué es SerpApi: https://serpapi.com/ (investigación, punto 3)."),
       paso(
          ["Sitcom Café", "Cafetería", "4,7", "122 reseñas", "Abierto hasta las 2 a. m.",
           "Google Maps vía SerpApi, 13 de noviembre de 2026, 23:29"],
          "Animación (3,0 s): la caja, los nodos y las líneas de datos se desvanecen menos las tres líneas, que se "
          "vuelven una tarjeta (TransformarPorPartes, 0,8 s): Sitcom Café sale de la primera, 4,7 de la segunda y "
          "122 reseñas de la tercera. Después suben Cafetería y Abierto hasta las 2 a. m. (desfase 0,2 s). "
          "Cuadro final: tarjeta de 1100 por 440 px centrada en (960, 560), relleno pantalla y borde hueso al "
          "40 %. Adentro, desde x 470: Sitcom Café en hueso a 88 px en y 430, Cafetería en gris a 49 px en y 510, "
          "4,7 en ámbar a 104 px en y 630 con 122 reseñas en hueso a 60 px a su derecha, y Abierto hasta las 2 a. "
          "m. en hueso a 60 px en y 730. La fuente en gris a 49 px en y 990. Marca de agua.",
          "Esta es una búsqueda real, de ayer a la noche: café cerca del centro de Santa Cruz. Y volvió esto: el "
          "nombre del lugar, el puntaje, cuántas reseñas tiene y si estaba abierto. No hubo que abrir ningún "
          "navegador. Y ese dato, dentro de un flujo, puede ir a un mensaje, a una tabla o a la IA.",
          3.0,
          fuente="workflows/muestras/serpapi-google_maps-bo.json, segundo resultado (q=café, ll=@-17.7833,-63.1821,14z, hl=es), creado el 14-nov-2026 a las 03:29 UTC, que son las 23:29 del 13 en Bolivia. El texto de Google dice Abierto, Cierra a las 2 a.m. y se muestra como Abierto hasta las 2 a. m."),
       paso(
          ["37 motores en el nodo de n8n", "Google", "Google Maps", "Google News", "Google Jobs", "Bing",
           "YouTube", "Google Scholar", "Amazon", "250 búsquedas gratis por mes"],
          "Animación (3,2 s): la tarjeta se achica y se va (0,4 s). Aparecen ocho pastillas (borde hueso al 40 %, "
          "texto hueso a 60 px) de a una, desfase 0,1 s, en tres filas centradas: Google, Google Maps y Google "
          "News en y 300, Google Jobs, Bing y YouTube en y 420, Google Scholar y Amazon en y 540. Bing y Amazon "
          "están para que se vea que no es solo Google (los dos están entre los 37 motores del nodo). "
          "Después suben las dos frases (desfase 0,2 s). Cuadro final: las tres filas de pastillas, 37 motores en "
          "el nodo de n8n en hueso a 72 px en y 700 con 37 en ámbar, y 250 búsquedas gratis por mes en hueso a "
          "72 px en y 810 con 250 en ámbar, las dos centradas. Marca de agua.",
          "Y no es solo Google. El nodo de SerpApi en n8n trae treinta y siete motores: mapas, noticias, empleos, "
          "YouTube y artículos académicos, y también Bing y Amazon, entre otros. Y la cuenta gratis trae "
          "doscientas cincuenta búsquedas por mes. Para empezar en un hackathon, alcanza.",
          3.2,
          fuente="37 operaciones del nodo SerpApi Official: https://n8n.io/integrations/serpapi/ y el código del nodo. 250 búsquedas por mes en el plan gratis: https://serpapi.com/pricing. Investigación, punto 3.",
          recortable="decir solo la primera y la última frase (menos 8 s)")])

# ------------------------------------------------------------------ D08
diapo("D08", "Pensar", "Segundo superpoder: pensar", "manim", FUNDIDO("D07"),
      "Un modelo solo sabe lo que leyó y no sabe qué pasa hoy. Un agente es un modelo con herramientas y "
      "memoria: piensa, elige una herramienta, mira lo que volvió y responde.",
      [paso(
          ["Pensar", "Un modelo solo sabe lo que leyó.", "¿Qué café está abierto ahora?", "No lo puedo saber."],
          "Entra con un fundido de 0,4 s desde D07. " + ESTILO_NODO + " Animación (3,6 s): Pensar entra con el "
          "ícono brain a su izquierda y debajo la frase (desfase 0,2 s). A la izquierda entra un nodo grande con "
          "el ícono brain (260 px, en (560, 600)). Desde la derecha entra un globo (rectángulo redondeado con cola "
          "hacia el nodo, borde hueso al 40 %, relleno tinta) con la pregunta. El nodo late dos veces (pensando) y "
          "responde con un segundo globo, más chico, con No lo puedo saber. en gris. Cuadro final: Pensar en "
          "titulo a 104 px en (230, 170) con el ícono brain de 90 px en x 160. Un modelo solo sabe lo que leyó. en "
          "hueso a 60 px en y 290 desde x 160. El nodo en (560, 600). Globo de la pregunta centrado en (1300, 480) "
          "con el texto en hueso a 60 px. Globo de la respuesta centrado en (1300, 700) con el texto en gris a "
          "60 px. Marca de agua.",
          "Segundo superpoder: pensar. Un modelo de inteligencia artificial, solo, sabe mucho de lo que leyó cuando "
          "lo entrenaron. Pero no sabe qué pasó hoy, ni qué café está abierto ahora. Y por su cuenta no puede "
          "hacer nada: solo responde.",
          4.3),
       paso(
          ["Agente = modelo + herramientas + memoria", "piensa", "elige", "mira", "responde", "Mapas",
           "Noticias", "YouTube", "Memoria"],
          "Animación (5,4 s): los globos se desvanecen (0,3 s). La frase de arriba cambia a la nueva "
          "(TransformarPorPartes, 0,5 s). Alrededor del nodo se dibuja un aro azul de 230 px de radio (Trazo, "
          "0,6 s) con cuatro rótulos a 60 px: piensa arriba, elige a la derecha, mira abajo y responde a la "
          "izquierda. A la derecha entran tres herramientas en columna (nodos de 140 px en x 1540, y 420, 600 y "
          "780: map-location-dot con Mapas, globe con Noticias y film con YouTube, rótulos a 49 px a su derecha) "
          "unidas al aro con líneas a trazos. Debajo del nodo grande, la memoria (memory, 110 px, en (560, 900) "
          "con Memoria a 49 px a su derecha) unida a trazos. Después un punto ámbar recorre el aro: en piensa se "
          "detiene, en elige sale por la línea a trazos hasta Mapas (la herramienta late y su borde pasa a ámbar), "
          "vuelve, pasa por mira y llega a responde (2,6 s en total). Cuadro final: la frase de arriba en hueso a "
          "60 px en y 290, con Agente en ámbar. El nodo, el aro con sus cuatro rótulos, las tres herramientas con "
          "Mapas encendida en ámbar y la memoria. Marca de agua.",
          "Un agente es un modelo con herramientas y memoria. Le hacen una pregunta, piensa qué necesita, elige "
          "una herramienta, por ejemplo buscar en mapas, mira lo que volvió y recién ahí responde. Si le falta "
          "algo, da otra vuelta.",
          5.4),
       paso(
          ["Vos le das las herramientas.", "Él elige cuál usar."],
          "Animación (2,4 s): el aro, el nodo y las herramientas bajan al 60 % (Foco, 0,3 s) y Mapas vuelve a "
          "azul. La frase de arriba cambia a Vos le das las herramientas. (TransformarPorPartes, 0,5 s). En el "
          "centro sube Él elige cuál usar. (Entrar, 0,4 s) sobre un recuadro tinta que tapa el centro del aro. "
          "Cuadro final: Vos le das las herramientas. en hueso a 72 px en y 290, centrada. Él elige cuál usar. en "
          "hueso a 88 px centrada en (960, 600), con Él elige en ámbar, sobre un recuadro tinta de 1000 por 160 "
          "px. Detrás, el agente en Foco. Marca de agua.",
          "La parte linda es esta: ustedes le dan las herramientas y le explican para qué sirve cada una. El agente "
          "decide cuál usar. Veámoslo en vivo.",
          2.4)])

# ------------------------------------------------------------------ demos
DEMO_VISUAL = (
    "Diseño de las tres diapositivas de demo (D09, D10 y D11), igual en las tres: arriba a la izquierda, en "
    "(160, 150), una pastilla con Demo N (borde hueso al 40 %, 49 px). El nombre del flujo en titulo a 104 px en "
    "y 270, desde x 160. La frase en hueso a 60 px en y 390, desde x 160. Abajo, el flujo en una fila con el "
    "estilo de nodo de la charla (nodos de 170 px en y 620, rótulos a 60 px en y 760). "
)

diapo("D09", "DemoNombre", "Demo 1: ¿Ya existe tu nombre?", "remotion", FUNDIDO("D08"),
      "Primera demo en vivo: un flujo en línea recta que ve (busca el nombre en Google) y piensa (el modelo da "
      "un veredicto con pruebas). Enseña el orden fijo, que contrasta con el agente de la demo 2.",
      [paso(
          ["Demo 1", "¿Ya existe tu nombre?", "Decí el nombre de tu proyecto.", "Formulario", "Google", "Modelo",
           "Veredicto", "Satelitazo", "LIBRE", "PasaSat / SatAviso / OrbitaYa"],
          "Entra con un fundido de 0,4 s desde D08. " + DEMO_VISUAL + ESTILO_NODO + " Animación (3,0 s): la "
          "pastilla y el título entran (useEntrar, desfase 0,15 s), después la frase. Los cuatro nodos entran de a "
          "uno (desfase 0,15 s) con sus íconos: mobile-screen-button, magnifying-glass, brain y circle-check. Las "
          "conexiones se dibujan y el punto ámbar los recorre una vez (1,0 s). Cuadro final: el diseño de arriba "
          "con los cuatro nodos centrados en x 360, 800, 1240 y 1680. Marca de agua.",
          "Primera demo, y necesito un equipo valiente. ¿Cómo se llama su proyecto? [ELEGIR un nombre que diga la "
          "sala. Si nadie se anima, usar Starlink, que sale OCUPADO y con sus enlaces. Abajo ya se ve cómo es "
          "un veredicto: Satelitazo salió LIBRE en el ensayo.] Vamos a ver si ese nombre ya "
          "existe. El flujo va en línea recta: busca el nombre en Google con SerpApi, le pasa lo que encontró al "
          "modelo y el modelo da su veredicto, con pruebas. [IR A n8n: abrir el formulario del flujo 1 y "
          "escribir el nombre. DEMO EN VIVO, unos 2 minutos. Mostrar el veredicto y abrir uno de los enlaces que "
          "encontró. Si falla: abrir la ejecución del ensayo en Executions. Sin internet: A1 (32 y Enter).]",
          3.4, espera=120,
          fuente="El flujo: workflows/ESPEC.md, workflow 1. Satelitazo, LIBRE y los otros nombres: la salida del "
                 "ensayo, workflows/muestras/flujo1-satelitazo.json."),
       paso(
          ["Línea recta:", "primero ve, después piensa."],
          "Animación (2,2 s): la frase de arriba se desvanece y el flujo baja al 60 % (Foco, 0,3 s). En el centro "
          "sube la lección en dos renglones (useEntrar, desfase 0,15 s). Cuadro final: el título y la pastilla "
          "igual, el flujo en Foco, y la lección centrada en hueso a 88 px en y 420 y 520, con primero ve y "
          "después piensa en ámbar. Marca de agua.",
          "Fíjense que el modelo no adivinó: leyó lo que trajo Google y nos mostró de dónde lo sacó. Primero ver, "
          "después pensar. Ese orden lo pusimos nosotros. En la próxima, el que decide es el agente.",
          2.2)])

diapo("D10", "DemoCompanero", "Demo 2: El compañero de la madrugada", "remotion", FUNDIDO("D09"),
      "Segunda demo en vivo: un chat con un agente que tiene tres herramientas de SerpApi (mapas, noticias y "
      "YouTube) y memoria. La sorpresa es ver en el registro que eligió solo la herramienta para cada pregunta.",
      [paso(
          ["Demo 2", "El compañero de la madrugada", "Preguntale como a un amigo.", "Chat", "Agente", "Mapas",
           "Noticias", "YouTube", "Podemos ir a Santuario Caffé Art"],
          "Entra con un fundido de 0,4 s desde D09. " + DEMO_VISUAL + ESTILO_NODO + " Acá la fila tiene dos "
          "nodos, Chat (comments) en x 360 y Agente (robot) en x 860, y a la derecha las tres herramientas en "
          "columna (nodos de 120 px en x 1380, y 500, 640 y 780: map-location-dot, globe y film), con sus rótulos "
          "a 60 px a su derecha, unidas al agente con líneas a trazos. Animación (3,0 s): la pastilla, el título y "
          "la frase entran (desfase 0,15 s). Entran Chat y Agente, se dibuja su conexión, y las tres herramientas "
          "salen del agente en abanico (desfase 0,15 s). El punto ámbar va de Chat al agente y elige una "
          "herramienta distinta cada vez, tres veces (Mapas, Noticias, YouTube, 1,2 s en total), y cada una late. "
          "Cuadro final: todo quieto y en azul. Marca de agua.",
          "Segunda demo: el compañero de la madrugada. Es un chat con un agente que tiene tres herramientas: "
          "mapas, noticias y videos de YouTube. Le voy a preguntar como a un amigo, y miren qué herramienta elige. [IR A "
          "n8n: abrir el chat del flujo 2. Preguntar dónde hay un café abierto cerca del centro. Después: ¿Qué noticias "
          "hay de la NASA esta semana? Decime la fecha de cada una. Después, un video corto para aprender n8n. Al final, una pregunta de seguimiento: "
          "cuál de los cafés tiene mejor puntaje. Abrir Logs y mostrar qué herramienta usó en cada una (la de YouTube se llama Videos). Si alguna noticia es vieja, decirlo: Google a veces devuelve notas de otros días, y por eso se le pide la fecha. "
          "DEMO EN VIVO, unos 2 minutos y medio. Si falla: la ejecución del ensayo. Sin internet: A2 (33 y Enter).]",
          3.4, espera=150,
          fuente="El flujo: workflows/ESPEC.md, workflow 2. Podemos ir a Santuario Caffé Art: el comienzo, tal cual, "
                 "de la primera respuesta del agente en la ejecución de ensayo del flujo 2, que salió "
                 "de Google Maps por SerpApi. Es lo que devolvió la búsqueda, no un dato de investigacion.md."),
       paso(
          ["Nadie le dijo qué usar.", "Eligió solo."],
          "Animación (2,2 s): la frase de arriba se desvanece y el flujo baja al 60 % (Foco, 0,3 s). Sube la "
          "lección en dos renglones (desfase 0,15 s). Cuadro final: el título y la pastilla igual, el flujo en "
          "Foco, y la lección centrada en hueso a 88 px en y 420 y 520, con Eligió solo en ámbar. Marca de agua.",
          "Nadie le dijo cuándo usar mapas y cuándo usar noticias. Leyó la descripción de cada herramienta y "
          "eligió. Y se acordó de lo que hablamos antes, porque tiene memoria.",
          2.2)])

diapo("D11", "DemoScout", "Demo 3: El scout del reto", "remotion", FUNDIDO("D10"),
      "Tercera demo en vivo, la más útil para la sala: pegan su reto y un agente investiga con tres herramientas "
      "y devuelve una página con lo que existe, qué leer, qué ver y tres ideas. La salida con forma fija es lo "
      "que permite armar la página.",
      [paso(
          ["Demo 3", "El scout del reto", "Pegá tu reto. Te devuelve con qué arrancar.", "Tu reto", "Agente",
           "Google", "Artículos", "YouTube", "Página"],
          "Entra con un fundido de 0,4 s desde D10. " + DEMO_VISUAL + ESTILO_NODO + " Acá la fila tiene tres "
          "nodos: Tu reto (file-contract) en x 300, Agente (robot) en x 800 y Página (desktop) en x 1650. Debajo "
          "del agente cuelgan tres herramientas chicas (90 px, en y 820, en x 640, 800 y 960: magnifying-glass, "
          "building-columns y film) unidas a trazos, con sus rótulos a 49 px debajo, en y 880. La frase va a 60 px. "
          "Animación (3,2 s): entran la pastilla, el título y la frase. Entran los tres nodos y las tres "
          "herramientas. El punto ámbar entra al agente, visita las tres herramientas una tras otra (cada una "
          "late) y sale hacia Página, que se enciende con un golpe chico. Cuadro final: todo quieto. Marca de agua.",
          "Tercera demo, y esta es para su reto. El scout del reto: pegan el reto que eligieron y el agente "
          "investiga por ustedes. Busca qué existe, artículos para leer y videos para aprender, y propone tres "
          "ideas que se pueden armar en un fin de semana. [IR A n8n: abrir el formulario del flujo 3 y pegar el "
          "reto de un equipo de la sala o el de ejemplo, que ya está copiado en la pestaña del flujo 3. Mientras piensa, abrir la "
          "ejecución y mostrar las herramientas que va usando. DEMO EN VIVO, unos 2 minutos. Si falla: la "
          "ejecución del ensayo. Sin internet: A3 (34 y Enter).]",
          3.6, espera=120,
          fuente="El flujo: workflows/ESPEC.md, workflow 3.",
          recortable="si va tarde, saltar la demo en vivo y mostrar A3 (menos 1:40)"),
       paso(
          ["La IA piensa.", "n8n le da forma."],
          "Animación (2,2 s): la frase de arriba se desvanece y el flujo baja al 60 % (Foco, 0,3 s). Sube la "
          "lección en dos renglones (desfase 0,15 s). Cuadro final: el título y la pastilla igual, el flujo en "
          "Foco, y la lección centrada en hueso a 88 px en y 420 y 520, con le da forma en ámbar. Marca de agua.",
          "La IA piensa y n8n le da forma: la respuesta sale siempre con las mismas partes, y por eso la pudimos "
          "convertir en una página. Esto, a mano, son muchas pestañas abiertas.",
          2.2)])

# ------------------------------------------------------------------ D12
diapo("D12", "IdeasParaTuReto", "Ideas para tu reto", "remotion", FUNDIDO("D11"),
      "Cuatro formas concretas de usar n8n en un proyecto del hackathon, con los mismos bloques de las demos.",
      [paso(
          ["¿Y en tu reto?", "Backend de tu prototipo", "webhook + IA + respuesta", "Asistente de tu tema",
           "chat + agente + SerpApi", "Avisos automáticos", "cada hora + noticias + IA", "Ordenar lo que llega",
           "formulario + IA + tabla"],
          "Entra con un fundido de 0,4 s desde D11. Animación (3,0 s): el título entra (0,4 s). Cuatro tarjetas "
          "(Tarjeta, relleno pantalla, borde hueso al 40 %, radio 28) entran en dos filas (useVoltear, desfase "
          "0,15 s). Cuadro final: ¿Y en tu reto? en titulo a 104 px en y 180, desde x 160. Tarjetas de 820 por "
          "250 px con esquinas en x 120 y 980, y 290 y 580. Adentro de cada una, desde 40 px del borde: el ícono "
          "en hueso de 56 px arriba a la izquierda (gears, comments, clock y table), el nombre en hueso a 60 px y "
          "debajo la receta en gris a 49 px. Ningún texto en ámbar salvo el ícono de la primera tarjeta. Marca de "
          "agua.",
          "¿Y en su reto? Cuatro ideas. Uno: n8n puede ser el backend de su prototipo. Un webhook, que es una dirección web, recibe los "
          "datos, los piensa con IA y responde. Dos: un asistente que sabe de su tema y busca en internet. Tres: "
          "avisos automáticos, por ejemplo cada hora busca noticias de su tema y les manda solo lo importante. "
          "Cuatro: un formulario que ordena lo que llega y lo guarda en una tabla. Todo eso se arma con los mismos "
          "bloques que acaban de ver.",
          3.4,
          recortable="saltar la diapositiva entera (menos 35 s)")])

# ------------------------------------------------------------------ D13
diapo("D13", "EmpezaGratis", "Empezá gratis hoy", "remotion", FUNDIDO("D12"),
      "Cómo empezar hoy sin gastar: la prueba de n8n Cloud, la cuenta gratis de SerpApi, un modelo sin llave y "
      "el repositorio con los cuatro flujos. Es la diapositiva para sacarle foto.",
      [paso(
          ["Empezá gratis hoy", "n8n Cloud: 14 días de prueba", "sin tarjeta, en app.n8n.cloud/register",
           "SerpApi: 250 búsquedas por mes", "gratis, en serpapi.com", "IA: incluida en la prueba",
           "elegí Use Gateway credits en el nodo", "Los 4 flujos de hoy", REPO],
          "Entra con un fundido de 0,4 s desde D12. Animación (3,0 s): el título entra. Las cuatro filas suben de "
          "a una (desfase 0,15 s), cada una con un número en hueso dentro de un círculo de acero2 de 56 px. A la "
          "derecha sube la tarjeta hueso del QR (escala de 0,9 a 1, 0,5 s). Cuadro final: Empezá gratis hoy en "
          "titulo a 104 px en y 160, desde x 160. Cuatro filas desde x 260 (el círculo en x 190): el nombre en "
          "hueso a 60 px en y 320, 480, 640 y 800 y su detalle en gris a 49 px 60 px más abajo (el último detalle, "
          "la dirección del repositorio, en hueso). El título va entero en titulo. En ámbar, solo los números 14 y "
          "250 de las dos primeras filas. A la derecha, la tarjeta hueso de 480 por 480 px de x 1320 a 1800 y de "
          "y 300 a 780 con el QR del repositorio (enlaces.repositorio del deck), con margen blanco de 4 módulos y "
          "sin rótulo propio: lo nombra la cuarta fila. Marca de agua.",
          "¿Cómo empiezan hoy, sin gastar nada? Uno: la prueba gratis de n8n Cloud, catorce días, sin tarjeta. "
          "Dos: una cuenta gratis de SerpApi, con doscientas cincuenta búsquedas por mes. Tres: el modelo. En la "
          "prueba de n8n Cloud, en el nodo del modelo eligen Use Gateway credits y no necesitan ninguna llave. Si "
          "se les acaban, usen una llave gratis de Google AI Studio. Ojo: en la capa gratis, lo que mandan se "
          "usa para mejorar los productos de Google. Nada de datos personales. Y en este repositorio están los "
          "cuatro flujos de hoy, listos para importar, y el enlace para registrarse en n8n. Este código lleva al repositorio. [Dejar el QR unos 20 segundos. Si en el ensayo de la mañana Use Gateway credits no apareció en el nodo del modelo o no alcanzó, la pantalla igual lo dice: agregar que, si no les aparece, usen directamente la llave de Google AI Studio.]",
          3.4, espera=20,
          fuente="Prueba de n8n Cloud, 14 días, sin tarjeta, 1.000 ejecuciones: https://n8n.io/pricing/ y https://docs.n8n.io/deploy/use-n8n-cloud/start-your-free-trial. Gateway credits: https://docs.n8n.io/deploy/use-n8n-cloud/gateway-credits. SerpApi gratis, 250 por mes: https://serpapi.com/pricing. Google AI Studio y su capa gratis: https://aistudio.google.com/docs/pricing. Investigación, puntos 1, 3 y 6.")])

# ------------------------------------------------------------------ D14
diapo("D14", "ElSorteo", "El sorteo con Tinkazo", "remotion", FUNDIDO("D13"),
      "El cierre en vivo: la lista que armó n8n se sortea con Tinkazo. La llama es la protagonista. Se explica "
      "en tres líneas por qué cualquiera puede comprobarlo y se dice el límite honesto.",
      [paso(
          ["Ahora, el sorteo.", "Sorteos que cualquiera puede comprobar."],
          "Entra con un fundido de 0,4 s desde D13. Animación (3,8 s): arriba aparece el logo de Tinkazo "
          "(diseno/logos/tinkazo/logo-horizontal-oscuro.svg, 100 px de alto, centrado en y 170, tal cual). La "
          "llama, dibujada con sus nueve rectángulos en magenta #ff5cb3 y de 300 px de alto, entra caminando desde "
          "el borde izquierdo hasta el centro (2,0 s, las patas se alternan de a pares, con un rebote de 6 px por "
          "paso), frena, y gira la cabeza hacia la sala con un solo movimiento de 3 grados. Después sube el título "
          "y la frase. Cuadro final: el logo arriba. La llama parada en el centro, en (960, 510), girada 3 grados. "
          "Ahora, el sorteo. en titulo a 104 px en y 790, centrado. Sorteos que cualquiera puede comprobar. en "
          "hueso a 60 px en y 885, centrado. " + LLAMA + " Marca de agua.",
          "Y ahora, lo prometido: el sorteo. Lo vamos a hacer con Tinkazo, que es lo que yo construí. Tinkazo hace "
          "sorteos que cualquiera puede comprobar.",
          4.5,
          fuente="Lema de Tinkazo: contenido/tinkazo.md, 4.4."),
       paso(
          ["1", "Primero se cierra la lista.", "2", "Después sale un número público.", "3",
           "Nadie lo elige. Cualquiera lo comprueba."],
          "Animación (3,0 s): la llama se achica a 0,6 y camina hasta la izquierda (x 300, y 540) mientras el "
          "título y la frase se desvanecen (0,3 s). A la derecha suben tres renglones de a uno (desfase 0,3 s), "
          "cada uno con su número en hueso dentro de un círculo de acero2 de 72 px. Cuadro final: el logo arriba, "
          "la llama a la izquierda, y los renglones en hueso a 60 px desde x 640 (el círculo en x 560), en y 380, "
          "530 y 680. Cualquiera lo comprueba en ámbar. Marca de agua.",
          "¿Por qué se puede comprobar? Primero se cierra la lista. Recién después sale el número que decide, y "
          "ese número lo publica una red pública a una hora fija: no lo elijo yo, ni nadie. Con la lista y ese "
          "número, cualquiera rehace el sorteo desde su celular y le tiene que dar el mismo ganador.",
          3.0,
          fuente="Las tres razones del sitio (sorteo-para-meetup.html, Por qué se puede comprobar) y el párrafo para decir en voz alta: contenido/tinkazo.md, 1.",
          recortable="decir solo las dos primeras frases (menos 12 s)"),
       paso(
          [("La lista la armó n8n." if CON_FORMULARIO else "La lista la arma n8n."),
           "Formulario", "Limpiar", "Guardar", "tinkazo.app"],
          "Animación (3,2 s): los renglones se desvanecen. En una fila en y 560 entran tres nodos con el estilo de "
          "la charla (150 px: mobile-screen-button, wand-magic-sparkles y table, en x 300, 650 y 1000) y la llama "
          "camina hasta ocupar el cuarto lugar, en x 1450, dentro de un cuadrado crema de Tinkazo (#fff6e9, 220 px, "
          "borde de 3 px en #191919 y sombra dura de 8 px en #191919, sin desenfoque) con la llama en su magenta de "
          "fondo claro (#e93d9c, archivo llama.svg). Se dibujan las conexiones azules y una pastilla ámbar con "
          "los nombres recorre la fila hasta entrar en el cuadrado de Tinkazo, que late. Cuadro final: La lista la "
          "armó n8n. en titulo a 88 px en y 280, centrado. La fila con sus rótulos a 60 px en y 730 y tinkazo.app "
          "en hueso a 60 px debajo del cuadrado de Tinkazo. El título dice La lista la arma n8n. si el deck no "
          "tiene la dirección del formulario. Marca de agua.",
          ("Y la lista la armó n8n mientras yo hablaba." if CON_FORMULARIO else
           "Y la lista la arma n8n: un formulario, un paso que limpia y una tabla. [Si se anotaron con el QR, "
           "decir: la armó mientras yo hablaba.]") +
          " Una cosa honesta: Tinkazo prueba que nadie tocó el "
          "resultado después de cerrar la lista, no que la lista esté bien armada. Por eso se la vamos a mostrar "
          "antes de cerrarla. Vamos. [IR A n8n: abrir la dirección de la lista del flujo 4 y copiar todo. IR A "
          "tinkazo.app: Pegar lista, Mostrar la lista en grande, revisar con la sala que no haya nombres que no "
          "deban salir y preguntar si alguien no se ve en la lista, Cerrar, Sellar la lista. Durante la espera de unos 45 segundos, decir: la lista ya no "
          "cambia, y el número que decide todavía no existe. Carrera de llamas. Resultado en grande con el QR "
          "para comprobar. Si el sorteo es en modo Prueba, decir: este es un sorteo de prueba, y la red de prueba se borra el 16 de diciembre. Hasta ahí, cualquiera lo confirma. Unos 4 minutos. Plan B: si el formulario falló, que levanten la mano los que quieren "
          "entrar y escribir sus nombres directo en Tinkazo, uno por línea. Sin "
          "internet en la compu: el celular con datos.]",
          3.2, espera=240,
          fuente="El límite honesto y el paso a paso del sorteo: contenido/tinkazo.md, 1 y 2.3. La lista: workflows/ESPEC.md, workflow 4.")])

# ------------------------------------------------------------------ D15
diapo("D15", "Cierre", "Cierre", "remotion", FUNDIDO("D14"),
      "La idea clave por última vez, con las mismas palabras, y dónde encontrar todo: el repositorio, el "
      "LinkedIn y nemaxyz. Queda quieta para las preguntas.",
      [paso(
          ["Que el flujo vea, piense y haga.", "Y ustedes, a construir lo que importa."],
          "Entra con un fundido de 0,4 s desde D14. Animación (3,0 s): vuelven los tres nodos chicos de D06.3 "
          "(VER, PENSAR, HACER, 140 px, en y 300) y el punto ámbar los recorre una vez (1,0 s). Sube la idea "
          "(useEntrar, 0,5 s) y después la segunda frase. Cuadro final: los tres nodos en y 300 con sus verbos a "
          "49 px, Que el flujo vea, piense y haga. en hueso a 88 px en y 600, centrada, con vea, piense y haga en "
          "ámbar, igual que en D06.3, y Y ustedes, a construir lo que importa. en hueso a 60 px en y 720. Sin "
          "marca de agua.",
          "Me quedo con esto. Un flujo común solo hace. Con SerpApi ve, y con un modelo piensa. Que el flujo vea, "
          "piense y haga. Y ustedes, a construir lo que importa.",
          3.7),
       paso(
          ["Que el flujo vea, piense y haga.", REPO, (sin_esquema(LINKEDIN) if CON_LINKEDIN else "tinkazo.app"),
           "Gracias", "nemaxyz", "@nemaxyz"],
          "Animación (3,6 s): los nodos y la segunda frase se desvanecen. La idea sube a y 150 y se achica a 64 px "
          "(idea_arriba). A la izquierda sube la tarjeta hueso del QR del repositorio (420 por 420 px, de x 160 a "
          "580 y de y 270 a 690). A la derecha, desde x 680, suben la dirección del repositorio en hueso a 60 px "
          "en y 360 y el LinkedIn en hueso a 60 px en y 460. Gracias entra en titulo a 104 px en y 620, desde "
          "x 680. Abajo, la firma (useFirma): el hilo ámbar dibuja la N, la N pasa a lima, aparece nemaxyz y "
          "después @nemaxyz. Cuadro final: la idea arriba, el QR a la izquierda, el repositorio, el LinkedIn y "
          "Gracias a la derecha, y la firma centrada en x 1260: N de 96 px y nemaxyz a 96 px en y 830, @nemaxyz "
          "en lima a 60 px en y 950. Si están los logos del evento, van abajo a la derecha como en el "
          "afiche. El LinkedIn va sin https:// ni www. Mientras el deck no tenga el LinkedIn, en ese renglón va "
          "tinkazo.app. Sin marca de agua.",
          "Todo lo de hoy está en este repositorio: los flujos, la presentación y los videos. " +
          ("Acá está mi LinkedIn, y en redes me encuentran como nemaxyz." if CON_LINKEDIN else
           "Tinkazo está en tinkazo.app, y en redes me encuentran como nemaxyz.") +
          " Si arman algo con n8n en el hackathon, búsquenme, "
          "quiero verlo. Gracias. [Preguntas, con esta pantalla quieta.]",
          3.6)])

# ------------------------------------------------------------------ respaldo
def respaldo_demo(id_, n, nombre_flujo, desde, nota):
    diapo(id_, "EnsayoDemo%d" % n, "Demo %d sin internet" % n, "remotion", FUNDIDO(desde),
          "Plan B de la demo %d cuando no hay internet: lo que salió en el ensayo, con el mismo flujo." % n,
          [paso(
              ["Demo %d sin internet" % n, "Así salió en el ensayo", nombre_flujo,
               "Ensayo del 14 de noviembre de 2026"],
              "Entra con un fundido de 0,4 s desde %s (se llega saltando con el número de la diapositiva). "
              "Animación (2,0 s): la pastilla y el título entran (desfase 0,15 s), la tarjeta sube (escala de "
              "0,95 a 1, 0,5 s) y su contenido entra de a un renglón. Cuadro final en dos columnas. A la izquierda, "
              "de x 160 a 700: la pastilla Demo %d sin internet (borde hueso al 40 %%, 49 px) en y 170, Así salió en "
              "el ensayo en titulo a 88 px en dos renglones desde y 300, %s en gris a 60 px en y 560 (hasta dos "
              "renglones) y la fuente en gris a 49 px al pie de la columna, en dos renglones. A la derecha, una "
              "tarjeta con borde hueso al 40 %% de x 760 a 1840 y de y 120 a 900 con lo esencial de la salida real "
              "del ensayo (workflows/muestras), escrito con el sistema de la charla, a 49 px o más. A1: el nombre, "
              "LIBRE, el porqué y los otros nombres. A2: las cuatro preguntas con la herramienta que eligió el "
              "agente (sin las respuestas). A3: el reto y las tres ideas. Fondo de circuito. Marca de agua." % (desde, n, nombre_flujo),
              nota, 2.7, fuente="Salida del ensayo del flujo %d (workflows/muestras), hecha con el mismo workflow del repositorio." % n)],
          seccion="respaldo")


respaldo_demo("A1", 1, "¿Ya existe tu nombre?", "D09",
              "[Solo si la demo 1 falla y no hay internet.] Se nos cayó internet, así que les muestro lo que salió "
              "en el ensayo con este mismo flujo. Probamos Satelitazo y Google no encontró nada con ese nombre: "
              "está libre. Y el modelo propuso otros tres nombres, por si acaso.")
respaldo_demo("A2", 2, "El compañero de la madrugada", "D10",
              "[Solo si la demo 2 falla y no hay internet.] Estas son las preguntas que le hicimos al agente en el "
              "ensayo. Miren al costado de cada pregunta qué herramienta eligió: mapas para el café, noticias para "
              "la NASA y Videos, que busca en YouTube, para el tutorial. Y en la última usó la memoria: se acordó de "
              "los cafés. [La pregunta de la NASA es la del ensayo. En vivo se le pide también la fecha de cada "
              "noticia, porque Google a veces devuelve notas de otros días.]")
respaldo_demo("A3", 3, "El scout del reto", "D11",
              "[Solo si la demo 3 falla, no hay internet o va tarde.] Arriba está el reto de ejemplo que le pasamos al "
              "scout en el ensayo. Y abajo, las tres ideas que propuso para armar en un fin de semana. La página "
              "completa trae también lo que ya existe, qué leer y qué ver.")

diapo("A4", "DespuesDeLaPrueba", "Después de los 14 días", "remotion", FUNDIDO("D15"),
      "Para las preguntas: qué pasa cuando termina la prueba de n8n Cloud y cómo seguir en la compu propia.",
      [paso(
          ["Después de los 14 días", "En tu compu: npx n8n@2.47.7", "con Node 24", "En la nube: desde 20 € por mes",
           "plan Starter, pagando el año", "Si no pagás, vence sola y sin cargos",
           "y tenés 90 días para bajar tus flujos"],
          "Entra con un fundido de 0,4 s desde D15. Animación (2,4 s): el título entra y las tres filas suben de a "
          "una (desfase 0,15 s), cada una con su ícono en hueso de 56 px a la izquierda (desktop, globe y "
          "hourglass-half). Cuadro final: Después de los 14 días en titulo a 104 px en y 170 desde x 160. Tres "
          "filas desde x 260: la línea principal en hueso a 72 px en y 340, 530 y 720 y su detalle en gris a "
          "49 px 70 px más abajo. npx n8n@2.47.7 en ámbar (la versión probada: desde n8n 3 npx ya no sirve). "
          "Marca de agua.",
          "[Para las preguntas.] Si les preguntan qué pasa después de los catorce días: n8n se puede instalar en "
          "su compu con un solo comando, npx n8n, con Node 24. En la nube, el plan más chico arranca en veinte "
          "euros por mes, pagando el año. Y si no pagan, la prueba vence sola, sin cargos, y tienen noventa días "
          "para bajarse sus flujos. Ojo: desde n8n 3, que llega a principios de diciembre, ya no se instala con npx. En el repositorio está el comando con la versión que anda hoy.",
          2.8,
          fuente="npx n8n y Node 24: https://docs.n8n.io/deploy/host-n8n/install-options/install-with-npm y https://registry.npmjs.org/n8n/2.47.7. Precio del plan Starter y vencimiento de la prueba: https://n8n.io/pricing/ y https://docs.n8n.io/deploy/use-n8n-cloud/start-your-free-trial. Investigación, puntos 1 y 5. Desde n8n 3 (estable a principios de diciembre) npx ya no sirve.")],
      seccion="respaldo")

# ------------------------------------------------------------------ deck
FUENTES = [
    {"dato": "n8n tiene más de 210 mil estrellas en GitHub (210.423)", "fuente": "API de GitHub",
     "url": "https://api.github.com/repos/n8n-io/n8n", "fecha": "2026-11-13"},
    {"dato": "Más de 500 integraciones propias de n8n", "fuente": "Portada de n8n (500+ native integrations)",
     "url": "https://n8n.io/", "fecha": "2026-11-13"},
    {"dato": "Prueba de n8n Cloud: 14 días, sin tarjeta, 1.000 ejecuciones", "fuente": "Precios y documentación de n8n",
     "url": "https://n8n.io/pricing/", "fecha": "2026-11-13"},
    {"dato": "Gateway credits: modelos sin llave propia en n8n Cloud", "fuente": "Documentación de n8n",
     "url": "https://docs.n8n.io/deploy/use-n8n-cloud/gateway-credits", "fecha": "2026-11-13"},
    {"dato": "Plan Starter desde 20 € por mes pagando el año. Si no se paga, la prueba vence sin cargos y quedan 90 días para bajar los flujos",
     "fuente": "Precios y documentación de n8n", "url": "https://docs.n8n.io/deploy/use-n8n-cloud/start-your-free-trial", "fecha": "2026-11-13"},
    {"dato": "npx n8n con Node 24 (n8n 2.47.7)", "fuente": "Documentación de instalación y registro de npm",
     "url": "https://registry.npmjs.org/n8n/2.47.7", "fecha": "2026-11-13"},
    {"dato": "SerpApi: 250 búsquedas gratis por mes", "fuente": "Precios de SerpApi",
     "url": "https://serpapi.com/pricing", "fecha": "2026-11-13"},
    {"dato": "El nodo SerpApi Official trae 37 motores", "fuente": "Página de la integración y código del nodo",
     "url": "https://n8n.io/integrations/serpapi/", "fecha": "2026-11-13"},
    {"dato": "Sitcom Café, 4,7, 122 reseñas, abierto hasta las 2 a. m.", "fuente": "Google Maps vía SerpApi (workflows/muestras/serpapi-google_maps-bo.json)",
     "url": "https://serpapi.com/google-maps-api", "fecha": "2026-11-13"},
    {"dato": "Capa gratis de Google AI Studio: lo enviado se usa para mejorar los productos de Google", "fuente": "Precios de Google AI Studio",
     "url": "https://aistudio.google.com/docs/pricing", "fecha": "2026-11-13"},
    {"dato": "Tinkazo: la lista se cierra antes de que exista el número que decide", "fuente": "Guía de marca y sitio de Tinkazo",
     "url": "https://tinkazo.app", "fecha": "2026-11-13"},
]

DECK = {
    "_estado": "Deck real de la charla, escrito el 14-nov-2026 a la madrugada. Lo genera contenido/generar_deck.py junto con contenido/guion.md: los cambios se hacen allá y se vuelve a correr (las notas son las mismas). La dirección del formulario del sorteo (D04, D05 y D14) y el LinkedIn (D15) los pone armar/poner_datos.py, que vuelve a armar todo. Sin ellos la charla igual se presenta.",
    "archivo": "Charla_n8n_SerpApi_IA",
    "titulo": "Dale superpoderes a tus automatizaciones: n8n + SerpApi + IA",
    "subtitulo": "Ver, pensar y hacer en un mismo flujo",
    "evento": "Space Talks, Conferencia 2 del Hackathon NASA Space Apps 2026, organizada por NASA Space Apps Santa Cruz. Campus UCB Santa Cruz, sábado 14 de noviembre de 2026, 16:00",
    "orador": "Nicolás Emir Mejía Agreda (@nemaxyz)",
    "duracion_objetivo_min": 27,
    "tesis": "Una automatización común solo repite pasos. Con SerpApi ve lo que pasa en internet hoy y con un modelo de IA decide qué hacer con eso. En un hackathon, un flujo así se arma en minutos, gratis, y deja a los equipos el tiempo para lo que importa.",
    "idea_clave": "Que el flujo vea, piense y haga.",
    "metaforas": "Una sola imagen manda: el flujo como una fila de nodos (cuadrados redondeados en azul noche con borde azul, como las pistas del circuito del afiche) por donde viaja un dato en ámbar. Los superpoderes son dos nodos que se le suman al que ya existía: VER (la lupa, SerpApi) y PENSAR (el cerebro, un modelo de IA), delante de HACER (n8n). Las tres palabras vuelven en D06, D15 y en cada demo. El reloj en 7 segmentos con las 32 horas que quedan hasta el cierre del envío abre la charla y sus horas perdidas se vuelven un flujo. La llama de Tinkazo acompaña en la bio y en el QR del sorteo, y es la protagonista del final.",
    "enlaces": ENLACES,
    "diapositivas": [],
    "fuentes": FUENTES,
}

PROHIBIDOS = [";", "\u2014", "\u2013", "\u00ab", "\u00bb", "\u2192", "\u2190", "\u00b7", "\u2026"]
PALABRAS_PROHIBIDAS = ["rifa", "rifas", "lotería", "raffle", "ticket", "boleto", "apuesta", "suerte", "bro", "aura",
                       "nitro"]


def revisar(texto, donde):
    for c in PROHIBIDOS:
        if c in texto:
            raise SystemExit("carácter prohibido %r en %s: %s" % (c, donde, texto[:120]))
    bajo = texto.lower()
    for p in PALABRAS_PROHIBIDAS:
        if re.search(r"(?<![\wáéíóúñü])" + re.escape(p) + r"(?![\wáéíóúñü])", bajo):
            raise SystemExit("palabra prohibida %r en %s" % (p, donde))


def palabras_dichas(notas):
    sin = re.sub(r"\[[^\]]*\]", " ", notas)
    return len(re.findall(r"[\wáéíóúñü]+", sin))


reloj = 0.0
filas_reloj = []
for d in D:
    pasos = []
    inicio = reloj
    for k, p in enumerate(d["pasos"], start=1):
        donde = "%s.%d" % (d["id"], k)
        for t in p["texto_pantalla"]:
            revisar(t, donde + " texto")
        revisar(p["visual"], donde + " visual")
        revisar(p["notas"], donde + " notas")
        for campo in ("fuente", "recortable"):
            if p[campo]:
                revisar(p[campo], donde + " " + campo)
        habla = round(palabras_dichas(p["notas"]) / PPM * 60 + p["espera_s"])
        # La duración del video sale de la animación que dice el visual: animación + 0,3 s quietos, más la
        # transición de entrada en el paso 1 si es fundido.
        m = re.search(r"Animación \(([0-9]+(?:,[0-9]+)?) s\)", p["visual"])
        if not m:
            raise SystemExit(donde + ": el visual no dice Animación (N s)")
        anim = float(m.group(1).replace(",", "."))
        if anim > 6.0:
            raise SystemExit(donde + ": la animación pasa de 6 s")
        extra = d["entrada"]["duracion_s"] if (k == 1 and d["entrada"]["tipo"] == "fundido") else 0.0
        p["duracion_animacion_s"] = round(anim + 0.3 + extra, 2)
        q = {k2: v for k2, v in p.items() if k2 != "espera_s"}
        q["segundos_habla"] = float(habla)
        q = {c: q[c] for c in ("texto_pantalla", "visual", "notas", "fuente", "recortable", "segundos_habla",
                               "duracion_animacion_s", "audio")}
        pasos.append(q)
        if d["seccion"] == "principal":
            reloj += habla
    d2 = {c: d[c] for c in ("id", "nombre", "titulo", "seccion", "motor", "piso", "entrada", "objetivo")}
    d2["pasos"] = pasos
    DECK["diapositivas"].append(d2)
    revisar(d["objetivo"], d["id"] + " objetivo")
    if d["seccion"] == "principal":
        filas_reloj.append((d["id"], d["titulo"], inicio, reloj - inicio))

for clave in ("tesis", "idea_clave", "metaforas", "subtitulo", "evento"):
    revisar(DECK[clave], clave)

(RAIZ / "contenido" / "deck.json").write_text(json.dumps(DECK, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mmss(s):
    s = int(round(s))
    return "%d:%02d" % (s // 60, s % 60)


print("diapositivas:", len(D), "principales:", sum(1 for d in D if d["seccion"] == "principal"),
      "pasos:", sum(len(d["pasos"]) for d in D))
for fila in filas_reloj:
    print(fila[0], mmss(fila[2]), mmss(fila[3]), fila[1])
print("total:", mmss(reloj))

# ------------------------------------------------------------------ guion.md
G = []
G.append("# Guion: Dale superpoderes a tus automatizaciones: n8n + SerpApi + IA\n")
G.append("Space Talks, Conferencia 2 del Hackathon NASA Space Apps 2026, Santa Cruz (Campus UCB). Sábado 14 de "
         "noviembre de 2026, 16:00. Habla Nicolás Emir Mejía Agreda (@nemaxyz).\n")
G.append("Este archivo y `contenido/deck.json` salen de la misma fuente, `contenido/generar_deck.py`, así que las notas del orador son "
         "idénticas en los dos. Los datos salen de `contenido/investigacion.md` y lo de Tinkazo de "
         "`contenido/tinkazo.md`. Los flujos de las demos están en `workflows/ESPEC.md`.\n")
G.append("**Cómo leer cada paso.** Pantalla es el texto exacto que se lee. Visual dice qué se ve y cómo se "
         "mueve (el detalle para quien construye está en el deck). Lo que dice Nicolás va palabra por palabra, en "
         "su voz, y lo que va entre corchetes es una acotación. El tiempo cuenta las palabras dichas a 140 por "
         "minuto, más las esperas y las demos en vivo.\n")

G.append("## En una mirada\n")
G.append("| Qué | Decisión |\n|---|---|")
G.append("| Tesis | " + DECK["tesis"] + " |")
G.append("| Idea clave | **" + DECK["idea_clave"] + "** Se dice con las mismas palabras en D06 y en D15. VER es SerpApi, PENSAR es el modelo, HACER es n8n. |")
G.append("| Gancho | Les quedan 32 horas hasta el cierre del envío. ¿Cuántas se van en buscar, copiar y pegar? Sin dar un número inventado (D02). |")
G.append("| Cierre | La idea clave, el repositorio, el LinkedIn y nemaxyz, después del sorteo en vivo con Tinkazo. |")
N_PRINC = sum(len(d["pasos"]) for d in D if d["seccion"] == "principal")
N_RESP = sum(len(d["pasos"]) for d in D if d["seccion"] == "respaldo")
G.append("| Diapositivas | 15 principales (%d pasos) y 4 de respaldo (%d pasos: A1 a A3, el plan B de cada demo, y A4 para las preguntas). En total, %d diapositivas en el .pptx |" % (N_PRINC, N_RESP, N_PRINC + N_RESP))
G.append("| Motores | Manim para explicar cómo fluye algo: D05 (qué es un flujo), D07 (ver) y D08 (pensar). Remotion para lo demás |")
G.append("| Demos en vivo | Tres flujos de n8n y el del sorteo (workflows/ESPEC.md). Cada una con su plan B |")
G.append("| La llama | Aparece en D03 (bio) y D04 (el QR del sorteo) y es la protagonista en D14 |")
G.append("| Tiempo | " + mmss(reloj) + " con las demos y el sorteo, contando a 140 palabras por minuto. Con los cambios de ventana, las risas y lo que la sala responde, contar unos 5 minutos más: entre 25 y 28. Recortes en orden más abajo |")
G.append("")

G.append("## Tesis, idea clave y metáfora\n")
G.append("**Tesis.** " + DECK["tesis"] + "\n")
G.append("**Idea clave.** " + DECK["idea_clave"] + " Tiene tres verbos que la sala ya vio dibujados como tres "
         "nodos, en el orden en que trabaja un flujo con superpoderes: primero ve, después piensa, después hace. "
         "Va con su remate, Y ustedes, a construir lo que importa, que le habla a gente con poco tiempo.\n")
G.append("**Metáfora.** " + DECK["metaforas"] + "\n")
G.append("**El orden de la charla.** Gancho (el tiempo del hackathon), quién habla, el QR del sorteo al principio "
         "para que la sala se anote mientras escucha, qué es un flujo (con el flujo que acaban de usar), la "
         "revelación de los dos superpoderes, cada superpoder explicado, tres demos de menos a más (línea recta, "
         "un agente que elige, un agente que investiga su reto), ideas para su reto, cómo empezar gratis, el "
         "sorteo y el cierre.\n")

G.append("## Los cuatro flujos de la charla\n")
G.append("| Flujo | La frase que lo vende | Qué enseña | Dónde |\n|---|---|---|---|")
G.append("| 1. ¿Ya existe tu nombre? | Decí el nombre de tu proyecto y en segundos sabés si ya existe. | Un flujo en línea recta: ver y después pensar | D09 |")
G.append("| 2. El compañero de la madrugada | Le preguntás como a un amigo y él elige dónde buscar. | Un agente con herramientas y memoria elige solo | D10 |")
G.append("| 3. El scout del reto | Pegás tu reto y en un minuto tenés con qué arrancar. | Un agente que investiga y una salida con forma fija que n8n convierte en página | D11 |")
G.append("| 4. La lista del sorteo | Te anotás desde el celular y la lista sale lista para Tinkazo. | Disparadores, limpieza de datos y una tabla | D04, D05 y D14 |")
G.append("")

G.append("## Mapa de tiempos\n")
G.append("| Diapositiva | Empieza | Dura | Qué |\n|---|---|---|---|")
for fila in filas_reloj:
    G.append("| %s | %s | %s | %s |" % (fila[0], mmss(fila[2]), mmss(fila[3]), fila[1]))
G.append("| Total | | %s | |" % mmss(reloj))
G.append("")
G.append("**Si hay que acortar, en este orden:** saltar D12 (menos 35 s). En D05.3, saltar el paso (menos 15 s). "
         "En D14.2, solo las dos primeras frases (menos 12 s). En D07.3, solo la primera y la última frase (menos "
         "8 s). En D03, la versión corta (menos 15 s). Si sigue faltando, la demo 3 no se hace en vivo y se "
         "muestra A3 (menos 1:40). El sorteo no se recorta: es la promesa del principio.\n")
G.append("**Si sobra tiempo:** en la demo 2, que la sala dicte una pregunta más. En la demo 1, probar dos nombres.\n")

G.append("## Diapositiva por diapositiva\n")
reloj2 = 0.0
for d in DECK["diapositivas"]:
    if d["seccion"] != "principal":
        continue
    G.append("### %s. %s (%s)\n" % (d["id"], d["titulo"], d["motor"].capitalize()))
    G.append("Empieza en el minuto %s. %s\n" % (mmss(reloj2), d["objetivo"]))
    for k, p in enumerate(d["pasos"], start=1):
        reloj2 += p["segundos_habla"]
        G.append("**%s.%d**\n" % (d["id"], k))
        G.append("- Pantalla: " + (" / ".join(p["texto_pantalla"]) if p["texto_pantalla"] else "(sin texto)"))
        G.append("- Visual: " + p["visual"])
        G.append("- Lo que dice Nicolás: " + p["notas"])
        G.append("- Tiempo: %d s. Reloj al terminar el paso: %s." % (p["segundos_habla"], mmss(reloj2)))
        if p["fuente"]:
            G.append("- Fuente: " + p["fuente"])
        if p["recortable"]:
            G.append("- Recortable: " + p["recortable"])
        G.append("")

G.append("## Respaldo\n")
G.append("No están en el camino principal. Se llega con el número de la diapositiva y Enter en el HTML, o desde "
         "la sección de respaldo del .pptx.\n")
for d in DECK["diapositivas"]:
    if d["seccion"] != "respaldo":
        continue
    p = d["pasos"][0]
    G.append("### %s. %s\n" % (d["id"], d["titulo"]))
    G.append(d["objetivo"] + "\n")
    G.append("- Pantalla: " + " / ".join(p["texto_pantalla"]))
    G.append("- Visual: " + p["visual"])
    G.append("- Lo que dice Nicolás: " + p["notas"])
    if p["fuente"]:
        G.append("- Fuente: " + p["fuente"])
    G.append("")

G.append("## Plan B, en una tabla\n")
G.append("| Qué falla | Qué se hace |\n|---|---|")
G.append("| Una demo da error con internet | Abrir en n8n la pestaña Executions y mostrar la ejecución del ensayo de esa mañana, nodo por nodo |")
G.append("| No hay internet en la compu | Demos: A1, A2 y A3. Sorteo: el celular con datos como módem. Sin red no se puede sortear de verdad, y se dice así |")
G.append("| El formulario del sorteo no anda | Si la tabla tiene nombres, bajarla como CSV y usar Subir CSV en Tinkazo. Si no, que levanten la mano los que quieren entrar y escribir sus nombres directo en Tinkazo, uno por línea |")
G.append("| Tinkazo no deja sellar | La herramienta lo dice y ofrece Probar ahora. Si no alcanza, sortear más tarde con la misma lista o Seguir sin sello, diciendo en voz alta que así no se puede comprobar (contenido/tinkazo.md, 2.8) |")
G.append("| Se acaban los Gateway credits | Cambiar la credencial del modelo por una de respaldo cargada antes en la cuenta: una llave propia de OpenRouter o de Google AI Studio (workflows/README.md) |")
G.append("")

G.append("## Fuentes\n")
for f in FUENTES:
    G.append("- %s. %s, %s (consultado el %s)." % (f["dato"], f["fuente"], f["url"], f["fecha"]))
G.append("")

texto_guion = "\n".join(G)
revisar(texto_guion.replace("`", ""), "guion.md")
(RAIZ / "contenido" / "guion.md").write_text(texto_guion, encoding="utf-8")
print("guion.md:", len(texto_guion), "caracteres")
