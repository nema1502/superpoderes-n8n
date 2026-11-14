# Tinkazo para la charla

Este archivo junta todo lo que hace falta saber de Tinkazo para la charla del sábado 14 de noviembre de 2026: qué decir, cómo hacer el sorteo del final, qué juego usar, qué se puede tomar de la marca y cómo se une con n8n.

**De dónde sale.** Lectura del código y de la documentación de Tinkazo (https://github.com/nema1502/tinkazo) en la versión que corre en https://tinkazo.app, el commit e6500a42 del 13 de noviembre de 2026. Las rutas y los renglones de abajo son de esa versión. No se ejecutó ni se modificó nada allá. Además se hicieron tres comprobaciones contra el sitio publicado (ver el final).

**Lo que no se hizo.** No se abrió un navegador para recorrer el sorteo completo. Los textos de los botones salen de `src/i18n.ts` y de `index.html`, y los pasos salen del código y de la guía oficial del sitio (`sorteo-para-meetup.html`). Conviene un ensayo completo antes de las 16:00 (ver la sección 6).

## Lo esencial

1. Tinkazo prueba que nadie tocó el resultado después de cerrar la lista. No prueba que la lista esté bien armada: eso lo decide quien organiza.
2. El sorteo del final se hace en modo Prueba con la Cuenta de prueba, que se crea sola en el navegador. Es gratis.
3. La lista entra por texto pegado o por un archivo CSV. No existe un enlace ni un parámetro que abra Tinkazo con la lista cargada.
4. Sí existe un QR para que el público se anote desde el celular, pero solo sirve para rondas de ejemplo que no se pueden comprobar. Para el sorteo de verdad, el hueco lo cubre un formulario de n8n (sección 5).
5. Juego recomendado: Carrera de llamas, con hasta 8 ganadores. Cada sorteo dura unos 2 minutos, de los cuales 45 segundos son de espera.
6. Lo que se sortea en modo Prueba se borra de la red el 16 de diciembre de 2026. El propio sitio dice que para un evento conviene el modo Oficial. Se decide antes del sorteo (sección 6).
7. Marca: la llama y el logo, la paleta de cinco colores con tinta encima, bordes gruesos y sombras duras sin desenfoque. Nada de degradados ni de texto blanco sobre color.

## 1. Qué es Tinkazo

### Para decirlo en voz alta

Tinkazo es una herramienta gratuita para hacer sorteos que cualquiera puede comprobar. El truco es el orden. Primero se cierra la lista de participantes. Recién después aparece el número que decide quién gana. Ese número lo publica una red pública de organizaciones independientes, a una hora fija, así que nadie lo conoce antes. Ni quien organiza, ni Tinkazo. Con la lista cerrada y ese número, el resultado sale de un cálculo que siempre da lo mismo. Por eso cualquiera, desde su celular, puede rehacer el sorteo y comprobar que le da el mismo ganador. El juego que se ve en pantalla, una carrera de llamas por ejemplo, solo cuenta el resultado con ganas. No decide nada. Hay un límite que conviene decir en voz alta: Tinkazo prueba que nadie cambió el resultado después de cerrar la lista, no que la lista estuviera bien armada. Por eso se muestra la lista a la sala antes de cerrarla. Participar es gratis, siempre, y quien participa no instala nada ni crea una cuenta.

### En una frase

Sorteos que cualquiera puede comprobar. La lista se cierra antes de que exista el número que decide.

La primera parte es el lema oficial (`docs/marca.md:7`). La segunda es la idea central y está en `docs/marca.md:382`: "La lista se cierra antes de que exista el número que va a decidir. El orden es todo."

### Para una diapositiva, en tres líneas

Son las tres razones que el propio sitio da para creerle (`sorteo-para-meetup.html`, sección "Por qué se puede comprobar"):

1. La lista queda cerrada antes de que exista el número.
2. Un número público decide el sorteo. Ni quien organiza ni Tinkazo lo pueden elegir.
3. El enlace permite rehacer el sorteo desde cualquier celular.

### El nombre, para contarlo en diez segundos

En Bolivia un tinkazo es una corazonada, el presentimiento de que hoy te toca. Hay una palabra gemela, tincazo, que es el golpecito que se da haciendo resbalar el dedo sobre el pulgar. El producto es las dos cosas (`docs/marca.md:21`).

### Lo que Tinkazo no promete

Decirlo así de claro ayuda a la credibilidad, y es la regla de la marca ("admitir los límites", `docs/marca.md:175`):

- No garantiza quién entra a la lista. La guía del sitio lo dice: "Quien arma la lista decide quién entra: el sello no lo impide" (`sorteo-para-meetup.html:288`).
- Los nombres no se publican. En la red queda una huella de la lista, no los nombres. Pero el enlace del comprobante sí lleva la lista entera: quien lo abre ve todos los nombres.
- Entrar a un sorteo es gratis, siempre. Los términos no permiten usarlo en sorteos con entrada paga.
- Quien organiza responde por su sorteo y por lo que pida la ley de su país.

## 2. El sorteo del final

### 2.1 Qué hay y qué no hay, de verdad

| Pregunta | Respuesta | Dónde se ve |
| --- | --- | --- |
| Cargar la lista pegando nombres | Sí. Botón Pegar lista, o pegar en el cuadro | `index.html:310` y `:332`, `src/ui/participants.ts:326` |
| Traer la lista de Luma | Sí. Chip Desde Luma, con un "?" que explica cómo bajar el CSV | `index.html:312-313`, `src/ui/luma-ayuda.ts` |
| Subir un CSV propio | Sí. Chip Subir CSV, dentro del pliegue Premio, cuántos ganan y subir CSV. También se puede arrastrar el archivo | `index.html:372-375`, `src/ui/participants.ts:402-408` |
| Mostrar la lista en la sala, con QR para buscarse | Sí. Botón Mostrar la lista en grande | `index.html:414`, `src/ui/sala.ts`, `src/lista.ts` |
| Que el público se anote solo desde el celular con un QR | Solo en rondas de ejemplo (modo stand). Esos nombres nunca van a un sorteo sellado | `src/ui/stand-sala.ts:15-16`, `src/sala/cliente.ts:8`, `workers/sala/README.md:3` |
| Registro de equipos por QR | Sí, para equipos. La lista sellada lleva la cuenta de cada equipo, no los nombres | `src/equipos/textos.ts:10-22` y `:134`, `src/equipos/bandera.ts:7` |
| Abrir tinkazo.app con la lista ya cargada desde un enlace | No | sección 2.6 |
| Una API o un webhook para mandar la lista desde otra herramienta | No | sección 2.6 |

### 2.2 Antes de la charla

1. **Abrir con parámetros útiles.** `https://tinkazo.app/?red=prueba&theme=dark` abre en modo Prueba y con el tema oscuro (`src/stellar/config.ts:111-147` y `:196`, `src/main.ts:52`). El tema oscuro combina con la presentación. `?lang=en` pasa el sitio a inglés.
2. **Ensayo completo con el proyector y el sonido.** En la portada hay un botón **Probar con un ejemplo**. Es igual al sorteo de verdad, con una lista de dieciocho animales (Llama Lupe, Cóndor Beto y compañía) y sin grabar nada. La guía del sitio lo pide: "Hacelo una vez con el proyector y el sonido" (`src/ensayo-modo.ts:31-35`, `sorteo-para-meetup.html:78`).
3. **Usar el mismo navegador y la misma compu que en el ensayo.** La Cuenta de prueba vive en el navegador: si se cambia de navegador o se borran los datos del sitio, se crea otra (`terminos.html`, texto `tmQ4B`). Usar Chrome. Dejar la pestaña con la sesión abierta.
4. **Llevar el celular con datos como respaldo.** La guía lo pide (`sorteo-para-meetup.html:91`): sin internet no se puede sortear de verdad (`:142`).
5. **Tener una lista de respaldo.** Un archivo de texto con unos veinte nombres, para pegar si el formulario de n8n falla.
6. **Decidir el premio y cuántos ganan antes de sellar.** Después de sellar no se cambia.
7. **Grabar un video del flujo completo** para el plan B (sección 2.8).

### 2.3 Paso a paso: modo Prueba con la Cuenta de prueba

Los textos entre negritas son los de la interfaz de hoy.

1. **Entrar.** En la portada, debajo de los dos botones grandes, tocar **Otras formas de entrar** (`index.html:81`). También sirve el chip **Entrar** de arriba a la derecha. Se abre la ventana "Entrá o creá tu cuenta".
2. **Elegir la Cuenta de prueba.** Dentro de la ventana, desplegar **Más formas de entrar** (si está plegado) y tocar **Cuenta de prueba** (la etiqueta chica dice "Prueba"). La ayuda dice: "El navegador te arma una cuenta del modo Prueba y le pone fondos de prueba. No instalás nada." Al terminar aparece "Cuenta de prueba lista y con fondos de prueba." y el chip de la cabecera pasa a decir **Cuenta de prueba** (`src/ui/wallet-ui.ts:1180` y `:1302`, `src/i18n-modo-oficial.ts:66-67`).
   Es el camino con menos piezas: no depende de Google ni de un código por correo. Si se prefiere Google, el botón grande de la portada dice **Entrar con Google y sortear** (o **Entrar y sortear gratis** si Google no está disponible, `src/main.ts:378`).
3. **Cargar la lista** (sección 2.4). La herramienta se llama **Tu sorteo** y arriba tiene cuatro pasos: **Lista**, **Sellar**, **Sortear**, **Compartir** (`index.html:185-190`).
4. **Premio y ganadores.** Abrir el pliegue **Premio, cuántos ganan y subir CSV**. Escribir el premio en **¿Qué sorteás? (opcional)** y elegir **Cuántos ganan** con los atajos 1, 2, 3, 5 o 10, o escribiendo otro número (`index.html:372-395`).
5. **Mostrar la lista a la sala (recomendado).** Tocar **Mostrar la lista en grande**. La lista sale numerada, con los repetidos marcados, el principio de la huella y un QR que dice "Escaneá y buscate". Cada persona se busca en su celular. Si falta alguien, se arregla ahora. Se cierra con **Cerrar** (`src/i18n.ts:1579-1594`).
6. **Sellar.** Tocar **Sellar la lista**. El botón pasa por "Preparando el sello…", "Armando el sello…" y "Guardando el sello…" (`src/i18n.ts:2191-2193`). Debajo dice "Tu gente no necesita crear cuenta." Con la cuenta adentro, la pantalla se pone en grande y completa sola, porque el clic de Sellar pide la pantalla completa (`docs/ux.md:122-124`). Sin cuenta, el mismo botón dice **Entrar para sellar** (`src/i18n.ts:2859`).
7. **La espera.** Unos 45 segundos. La pantalla dice "El número que va a decidir" y "Nadie puede elegir el número: tampoco quien organiza." Si se sale de la pantalla grande, **Mostrar la espera en grande** la recupera (`src/i18n.ts:1049`, `src/state.ts:239`).
8. **Cambiar de juego (si hace falta).** En la espera en grande hay un botón **Cambiar de juego**. En la página, el selector **Juego elegido** hace lo mismo. Se puede cambiar hasta que arranca el show: mientras corre, el selector se apaga y dice "Mientras corre el sorteo no se cambia de juego." Con el resultado puesto, **Ver de nuevo con otro juego** cuenta el mismo resultado con otro juego (`docs/ux.md:129` y `:160`, `src/i18n.ts:1265-1267`).
9. **El sorteo arranca solo** cuando nace el número, si la espera en grande está abierta. Si no arrancó, el botón es **Lanzar el sorteo** (`index.html:463`, `docs/ux.md:135`).
10. **El resultado.** Sale en grande, con el nombre, el premio y un QR que dice "Escaneá para comprobar". Dejarlo a la vista para que la sala lo escanee (`src/i18n.ts:1131`, `docs/ux.md:137`).
11. **Lo que sigue.** Con más premios, **Siguiente premio (quedan N)**, que vuelve al paso 2 con la lista sin quienes ya ganaron. Si no, **Compartir el resultado**. Más abajo: **Mostrar en grande**, **Ver de nuevo con otro juego**, **Copiar el mensaje** y **Avisarle por WhatsApp** (`index.html:547-549`, `:583`, `:597-598`).
12. **Comprobar desde un celular.** El QR abre `verificar.html` con quién ganó y un botón grande, **Quiero comprobarlo**, que lleva al detalle (`docs/ux.md:249`, `src/i18n.ts:2239`).

### 2.4 Cómo se carga la lista

| Camino | Qué hace | Detalle |
| --- | --- | --- |
| Pegar lista | Pega lo que hay en el portapapeles, con permiso del navegador. Sin permiso, lleva al cuadro para pegar a mano | `docs/ux.md:201`, `src/ui/participants.ts:584-585` |
| Escribir en el cuadro | Un nombre por línea | placeholder "Un nombre por línea…" (`index.html:332`) |
| Desde Luma | Se baja el CSV desde Luma (Manage, pestaña Guests, Download CSV) y se marca quiénes entran: los que vinieron o los aprobados | `index.html:316-324` |
| Subir CSV | Cualquier CSV o archivo de texto | `index.html:375` |
| Arrastrar el archivo | Lo mismo, soltando el archivo sobre la lista | `src/ui/participants.ts:402-408` |

Lo que hay que saber del formato:

- **La regla del sorteo.** Una línea por persona. Se recorta cada nombre, se descartan los de menos de 2 caracteres y los repetidos exactos (distingue mayúsculas), y se conserva el primero y el orden. Se corta en la primera coma (`src/protocol/canonical.ts:9-20`). Hacen falta al menos dos nombres (`src/i18n.ts:508`).
- **Un CSV con una sola columna** se trata como lista simple. Si la primera línea dice name, nombre, nombres o participantes, se toma como encabezado y no entra como persona (`src/ui/csv.ts:75-80`).
- **Un CSV con varias columnas** abre un selector para elegir cuál tiene los nombres. Entiende coma, punto y coma y tabulación (`src/ui/csv.ts:43`). Reconoce encabezados como name, full name, nombre y nombre completo (`src/ui/csv.ts:46-50`). Si trae nombre y apellido en columnas separadas, ofrece una columna "Nombre + Apellido" (`src/ui/csv.ts:139-161`).
- **Las comas dentro de un nombre** se cambian por un espacio, porque el protocolo corta en la primera coma (`src/ui/csv.ts:182-190`). Los caracteres invisibles se sacan.
- **Una lista numerada de WhatsApp** entra sin los números (`docs/ux.md:177`).
- **El archivo se lee en el navegador** y no se sube a ningún lado (`index.html:323`).
- **Tope para el show:** 200 personas. Con más, ningún juego del selector cuenta la lista (`src/ui/recomendar.ts:84-92`, `src/state.ts:83`).

### 2.5 ¿El público puede anotarse solo desde su celular con un QR?

Hay tres cosas parecidas. Ninguna es la que hace falta para anotar a la sala en un sorteo de verdad.

**a) La sala por QR del modo stand. Existe y funciona, pero solo para rondas de ejemplo.**

El recorrido (`index.html:280-308`, `:366-367`, `src/i18n.ts:1270-1311`):

1. En la herramienta, antes de sellar, hay un enlace chico: **Tengo un stand: rondas de ejemplo con quienes pasan**. Al entrar, el cuadro de la lista empieza vacío y lo que se estaba armando queda guardado (`src/ui/stand.ts:73-87`).
2. Aparece una banda fija que dice "Ronda de ejemplo: no se puede comprobar".
3. El botón **Que se sumen con un QR** abre la sala y muestra el QR con el texto "Escaneá y sumate con tu nombre". Hay **Ver el QR en grande** y **Cerrar la sala**.
4. Cada persona escribe su nombre o apodo en una página que se abre desde su celular, y el nombre aparece en la lista de la pantalla al instante.
5. Se toca **Empezar la ronda**, aparece "Arranca en 3" y el juego elige a alguien (`src/ensayo-modo.ts:86`). Al final dice: "Fue una ronda de ejemplo: no se puede comprobar y no se entrega nada." Los botones son **Otra ronda** y **Hacer un sorteo de verdad**.

Cómo está hecho (`workers/sala/README.md`): un servicio propio en `s.tinkazo.app`, que recibe los nombres cifrados con una clave que viaja solo en el QR, después del `#`. Hasta 400 nombres por sala, 40 caracteres por nombre, sin enlaces. Un filtro de palabras manda lo dudoso a una lista "Para revisar" que quien atiende mira antes de mostrar. La sala se borra sola a las 10 horas o con **Cerrar la sala**. Durante la ronda no hay cuenta, ni premio, ni sello, ni comprobante, y el número no se pide a la red (`src/ui/stand.ts:12-27`, `src/ensayo-modo.ts:78-86`).

**Por qué no sirve para el sorteo del final.** El código lo dice dos veces: "estos nombres nunca van a un sorteo sellado ni a un comprobante" (`src/ui/stand-sala.ts:15-16`) y "lo que llega acá nunca va a un sorteo sellado" (`src/sala/cliente.ts:8`). Salir del modo recarga la página y repone la lista de antes (`src/ui/stand.ts:89-111`). Técnicamente los nombres quedan en un cuadro de texto y se podrían copiar a mano, pero va contra cómo está pensado: llegan de cualquiera, sin ninguna revisión, y el modo se llama ronda de ejemplo por eso. No se recomienda.

**Uso posible en la charla:** como calentamiento. El público escanea, los nombres aparecen y corre una carrera de ejemplo sin valor. Después, el sorteo de verdad se hace con otra lista (la de n8n). Cuesta tiempo de charla y no suma a la prueba, así que es opcional.

**b) El registro de equipos por QR. Existe y está prendido en producción, pero es para equipos.**

El organizador toca **Tengo equipos: registro con cupón** y después **Abrir el registro de equipos**. Aparece un QR ("Escaneá y anotá a tu equipo"). Cada equipo se anota desde el celular de su encargado, en `equipos.html`, con su cuenta (Google o una cuenta de Stellar). Hay una pantalla para el proyector, **Mostrar la pantalla del stand**, con los equipos que van llegando. Quien organiza reparte cupones desde una cuenta del evento que tiene que tener saldo para pagar la comisión de la red (`src/equipos/textos.ts:10-43`).

La diferencia clave: **la lista sellada lleva la cuenta pública de cada equipo, no sus nombres.** En el show y en el resultado se ve el nombre del equipo (`src/equipos/textos.ts:134`).

Está prendido en producción: el código publicado trae la bandera con el valor 1 por defecto. Se comprobó en el archivo `bandera-BA0mqGiM.js` del sitio, donde la función que acepta el texto 1 o el texto true tiene como valor por defecto el texto 1. Es la función de `src/equipos/bandera.ts:7`.

Sirve si el sorteo del final es entre equipos del hackathon y si ya se está usando para el evento. Para anotar a personas sueltas en medio de una charla de 30 minutos es demasiado montaje. No se probó en esta revisión.

**c) La lista en grande con QR. Existe, pero no anota a nadie.**

**Mostrar la lista en grande** pone un QR que abre `lista.html` con la lista entera en el enlace. Cada persona se busca y ve si está o si está repetida. Es de solo lectura (`src/lista.ts:13-19`).

### 2.6 ¿Se puede abrir tinkazo.app con la lista ya cargada desde un enlace?

**No.** Se revisaron todos los lugares donde el código lee la dirección. Los parámetros que existen son de presentación o de prueba, y ninguno lee nombres:

| Parámetro | Para qué sirve |
| --- | --- |
| `?lang=en` | Idioma (`src/idioma.ts:73`) |
| `?theme=dark` o `light` | Tema (`src/main.ts:52`) |
| `?red=prueba` o `oficial` | Modo (`src/stellar/config.ts:111-147`) |
| `?pace=rapido`, `normal` o `epico` | Duración del show (`src/state.ts:284`) |
| `?grande=0` o `1` | Pantalla grande (`src/ui/vista-grande.ts:45`) |
| `?demo=race` (o el nombre de otro juego) | Corre un sorteo de ejemplo con una lista incorporada. Nunca graba (`src/main.ts:476-488`) |
| `?instant=1`, `?lead=N`, `?motor=`, `?pose=` | Pruebas y capturas |

La guía de marca lo confirma para los QR del sitio: ninguna ancla ni parámetro de la dirección abre el ingreso o crea el sorteo, y lo único con consulta es `?demo=race` (`docs/marca.md:319` y `:327`).

Lo que sí viaja en un enlace son páginas de solo lectura, con los datos después del `#`: `lista.html#…` (la lista, para buscarse), `verificar.html#…` (un comprobante) y `evento.html#…` (varios sorteos). Lo que va después del `#` no llega a ningún servidor (`docs/evento.md:5`, `src/lista.ts:17-18`). Ninguna de esas páginas carga la lista en la herramienta.

El borrador de la lista se guarda en la pestaña, y el botón **Recuperar la lista anterior** es local al navegador. Un enlace no puede llenar ninguno de los dos.

### 2.7 Qué cambia en Oficial

| | Prueba | Oficial |
| --- | --- | --- |
| Dónde queda el sello | Red de pruebas de Stellar. Se borra entera el 16 de diciembre de 2026 (`src/i18n.ts:474`) | Red principal de Stellar, que no se reinicia (`src/i18n-modo-oficial.ts:63`) |
| Cuenta | La Cuenta de prueba (se crea sola en el navegador, con fondos de prueba), o Google, o el correo | Google, correo o la billetera Varial. **La Cuenta de prueba no funciona en Oficial** (`src/i18n-modo-oficial.ts:68`) |
| Antes del primer sorteo | Nada | Un paso a pantalla completa, **Dejá tu cuenta lista**: **Activar mi cuenta** (un toque, no se paga nada) y proteger la cuenta con el desbloqueo del equipo o con un código al correo. Termina con "Ya podés sortear en modo Oficial." (`src/i18n.ts:2905-2959`) |
| Costo de la comisión | Lo cubre Tinkazo, y puede haber un tope por cuenta y por mes (texto `tmPatrocinio`) | Con el cupón de un evento la cubre Tinkazo. Quien entra con su propia billetera la paga de su cuenta, unos centavos (`src/i18n-modo-oficial.ts:47` y `:52`) |
| Primera vez en el navegador | Nada | Una confirmación: "Vas a sellar en modo Oficial", con los botones **Sellar** y **Pasar a Prueba** (`src/i18n.ts:485-488`) |
| Cómo se pasa | Es el modo con el que abre el sitio (`.env.example:4`, y el sitio publicado no fuerza otro) | Tocar la marca del modo, que abre "¿En qué modo sorteás?", y **Pasar a Oficial**. O abrir con `?red=oficial` (`src/ui/modo-ui.ts`, `src/stellar/config.ts:218`) |
| Mensaje del sitio al sellar | "Modo Prueba: se borra el 16 de diciembre. Para tu evento, pasá a Oficial." | "Modo Oficial: este sorteo queda registrado en Stellar." (`src/i18n.ts:479-480`) |

El contrato del modo Oficial está desplegado desde el 11 de noviembre de 2026 (`src/stellar/deployments.json:27-35`). Qué implica en la práctica:

- El comprobante de un sorteo de Prueba se puede rehacer siempre, pero después del 16 de diciembre nadie podrá confirmar la hora del sello (`src/i18n-modo-oficial.ts:63`). Si el README del repositorio de la charla enlaza un comprobante como ejemplo, hay que saber que en Prueba deja de confirmarse ese día.
- Para sortear en Oficial hace falta un cupón de evento o una cuenta con saldo propio. El cupón se canjea con un enlace (`src/ui/cupon-enlace.ts`). Esa parte la resuelve quien organiza.

### 2.8 Si algo falla (plan B)

La guía oficial del sitio tiene una tabla de fallas (`sorteo-para-meetup.html:125-143`). Lo que importa para la charla:

- **No se puede sortear de verdad sin internet.** Está dicho así en la guía (`:142`). El respaldo es el celular con datos.
- **Google no deja entrar:** abrir en Chrome y no dentro de otra app, o usar la Cuenta de prueba.
- **La red no deja sellar:** la herramienta lo dice y ofrece **Probar ahora**. Si no alcanza hay dos salidas honestas: sortear más tarde con la misma lista, o **Seguir sin sello**. Con esa segunda salida el sorteo se hace pero nadie puede comprobarlo, y la pantalla dice "Sin sello: no se puede comprobar." Hay que decirlo en voz alta antes de sortear (`docs/ux.md:329` y `index.html:540`).
- **Se cortó la espera o el sorteo:** **Reintentar el sorteo**. Quien gana no cambia.
- **Se salió de la pantalla grande:** **Mostrar la espera en grande**. Si ya salió el número, **Lanzar el sorteo**.
- **No se oye:** volumen de la compu y del proyector.
- **Antes de sellar:** el botón **¿La red está bien?** da un verde, un amarillo o un rojo con la razón (`index.html:433`).

Plan B grabado, para el momento en que no haya red:

1. **Un video del flujo real.** Grabar la pantalla de un sorteo completo en modo Prueba, con la Cuenta de prueba y la lista de n8n de ensayo. Mostrarlo diciendo que es una grabación del ensayo.
2. **La demo del sitio.** `https://tinkazo.app/?demo=race&lead=3` corre sola un sorteo con una lista incorporada, sin cuenta y sin grabar nada. Necesita internet para el número, así que sirve para grabar el video y no como respaldo sin red.
3. **La ronda de ejemplo del modo stand** no pide el número a la red (`src/ui/stand.ts:16-17`). Con la página y el juego ya cargados, corre sin conexión. Siempre dice "Ronda de ejemplo: no se puede comprobar", así que sirve para mostrar el juego, nunca como sorteo de verdad. No se verificó qué partes se bajan en el momento.

Nunca usar el ejemplo ni el ensayo como si fueran el sorteo de verdad: no se graban y nadie los puede comprobar (`sorteo-para-meetup.html:143`).

### 2.9 Qué decir mientras corre la espera de 45 segundos

Frases que ya usa el sitio, para no inventar otras:

- "La lista ya no cambia, y el número que decide todavía no existe." (`sorteo-para-meetup.html:110`)
- "Nadie puede elegir el número: tampoco quien organiza." (`src/i18n.ts:1312`)
- "Escaneá el QR y buscate." Mientras, la pantalla puede mostrar la lista sellada con **Mostrar la lista en grande**, que durante la espera dice "La lista está sellada y ya no cambia. Buscate mientras sale el número." (`src/i18n.ts:1594`)

## 3. Juego, ganadores y tiempo

### Qué juego

**Carrera de llamas.** Razones, todas del repositorio:

- Es el primero del selector y el que viene elegido (`index.html:477`, `src/ui/recomendar.ts:25-27`).
- Funciona de 2 a 200 personas, con el mejor tramo entre 4 y 30 (`src/ui/recomendar.ts:84`).
- Es el que más trabajo de dirección tiene: cámara, ritmo, sonido y pruebas de que nadie delata al ganador antes de tiempo. Su guía (`docs/juegos/carrera.md`) pesa 50 KB, el doble que la de cualquier otro juego, y sus medidas están en `docs/juegos.md:767`.
- Se ve en 3D por defecto en los equipos que lo aguantan, con el interruptor **En 3D** a mano para pasar a 2D si la laptop se pone lenta. El ganador es el mismo (`docs/motores.md:123-135`).
- Los nombres se leen desde el fondo de la sala: la regla de la marca es 28 px como mínimo en 1080 de alto, y 48 px para lo principal (`docs/marca.md:151-157`).
- Es una carrera de llamas por la cordillera.

Para evitar en la charla: la ruleta y la tómbola. Funcionan y están en el sitio, pero son las que más se alejan de lo que pide la marca para una presentación (sección 4.5).

### Cuántos ganadores

- **Para una charla, de 1 a 3.** Cada ganador tiene su momento: el cartel de la corona entra de a uno, con su cara, y el primer premio es más grande (`docs/juegos.md:848`).
- **El tope de la carrera es 8,** uno por carril de la recta final (`src/ui/recomendar.ts:54`). Con más premios, el selector la apaga y dice por qué.
- Si hay muchos premios o una sala de más de 60 personas:
  - **Teleférico**: de 16 a 200 personas, ideal de 30 a 150. Todos los premios llegan juntos a la cumbre, en una cabina (`src/ui/recomendar.ts:89`, `docs/juegos.md:847`).
  - **Chovena**: de 8 a 80, ideal de 12 a 60. Se corta la música y el que trastabilla sale (`src/ui/recomendar.ts:88`).
  - **Sapo**: hasta 12 premios, ideal de 6 a 12 personas (`src/ui/recomendar.ts:61` y `:86`).

### Cuánto tarda

Cálculo hecho con las constantes y la documentación. No se midió con reloj.

| Tramo | Duración | Fuente |
| --- | --- | --- |
| Espera después de sellar, con cuenta | 45 s | `src/state.ts:239`, `src/ui/freeze.ts:851` |
| Cuenta regresiva de la sala | 3 s (no va en el ritmo Rápida) | `src/state.ts:416-417` |
| De Lanzar el sorteo hasta que arranca el juego, con cuenta | unos 10 s (grabar el sorteo en la red) | `docs/ux.md:198` |
| Show en ritmo Normal, juegos en general | 38 s (Rápida 20, Épica 45) | `src/state.ts:278` |
| Show de la carrera en ritmo Normal | 48 s con 18 personas, 60 s con 60, 68 s con 200. Es la meta de la dirección | `docs/juegos.md:767` |
| El ritmo se elige en el pliegue **Sonido, duración y más** o con `?pace=` | | `index.html:496-508` |

**Total de un sorteo con la carrera, en Normal: unos 2 minutos** (45 s de espera, unos 10 s de grabado, 3 s de cuenta y de 50 a 70 s de show), más el rato que se deje el resultado a la vista. **Cada premio extra con Siguiente premio vuelve a sellar y repite la espera de 45 s**, así que suma otros 2 minutos. Con un solo sorteo de 1 a 3 ganadores, el tiempo es el de uno.

## 4. Guiños para la presentación

### 4.1 Archivos que se pueden usar

Todos están en `public/marca/` del repositorio de Tinkazo. Tinkazo es de Nicolás y el código es MIT, así que se pueden copiar al repositorio de la charla. **No tocar ni usar `public/marca/coleccion/`** (los stickers ya impresos).

| Archivo | Qué es | Detalle |
| --- | --- | --- |
| `llama.svg` | La llama sola, en magenta `#e93d9c` | 512 x 512, nueve rectángulos |
| `llama.png` | La misma llama con fondo transparente | 2048 x 2048 |
| `llama-oscuro.svg` y `.png` | La llama en el magenta del tema oscuro `#ff5cb3` | Para fondos oscuros |
| `logo-horizontal.svg` y `.png` | Llama a la izquierda y el nombre a la derecha | Texto en tinta `#191919` y llama con "zo" en `#e93d9c`. Para fondos claros |
| `logo-horizontal-oscuro.svg` y `.png` | Lo mismo, para fondos oscuros | Texto en `#f6efe2` y magenta `#ff5cb3`. Es el que va sobre el azul noche |
| `logo-apilado.svg` y `-oscuro` | Llama arriba y nombre abajo | Más compacto que el horizontal, para portadas y cierres |
| `logo-web-horizontal.svg` y `logo-web-apilado.svg` (y `-oscuro`) | El logo con `tinkazo.app` debajo | El `.app` va en magenta |
| `sello-es.svg` y `sello-en.svg` | "Sorteo verificable con Tinkazo" | 960 x 280, para fondos claros. Se usa solo cuando hay un comprobante y se acompaña con su enlace (`docs/marca.md:244`) |
| `qr/qr-tinkazo-app-papel.svg` o `.png` | QR a `https://tinkazo.app` | Tinta sobre papel |
| `qr/qr-demo-carrera-blanco.png` | QR a `https://tinkazo.app/?demo=race` | Abre una demo con la carrera |
| `qr/qr-etiqueta-magenta.png` y `qr-etiqueta-amarilla.png` | QR con la llamita y "tinkazo.app" | Para poner encima de un arte |
| `public/juegos/race.webp` y `race-light.webp` | Captura de la carrera, 900 x 506 | También `portada/` (640 x 360) y `selector/` (320 x 180) |
| `public/marca/juego-race.jpg` | Foto de la escena de la carrera | Hay una por cada uno de seis juegos |

Reglas de uso de los logos (`docs/marca.md:256`): espacio libre alrededor igual a la altura de la llama, tamaño mínimo de 24 px de alto en pantalla, no estirar, no cambiar los colores, no ponerlo sobre fondos que no contrasten.

**La llama como dibujo propio.** Si se prefiere dibujarla en Manim o en Remotion en vez de usar el archivo, son nueve rectángulos sin curvas, en una grilla donde 1 unidad es 1 cuadro (`public/marca/llama.svg`). Cada fila es x, y, ancho y alto:

| Parte | x | y | ancho | alto |
| --- | --- | --- | --- | --- |
| Cuerpo | 2 | 11 | 16 | 7 |
| Cuello | 15 | 3 | 4 | 10 |
| Cabeza | 14 | 0 | 8 | 4 |
| Oreja | 20 | -2 | 2 | 3 |
| Pata 1 | 3 | 18 | 2.5 | 6 |
| Pata 2 | 8 | 18 | 2.5 | 6 |
| Pata 3 | 12.5 | 18 | 2.5 | 6 |
| Pata 4 | 16 | 18 | 2.5 | 6 |
| Cola | 0 | 9 | 3 | 4 |

### 4.2 Paleta

Cinco acentos, dos superficies y dos textos. La restricción es parte del estilo (`docs/marca.md:25-61`).

| Papel | Tema claro | Tema oscuro |
| --- | --- | --- |
| Fondo | papel `#fff6e9` | `#171126` |
| Tarjeta | `#ffffff` | `#221a33` |
| Texto | tinta `#191919` | `#f6efe2` |
| Texto secundario | `#4b4437` | `#cfc6b4` |
| Texto apagado | `#6b655b` | `#97909f` |
| Magenta | `#e93d9c` | `#ff5cb3` |
| Naranja | `#ff7a1a` | `#ff8b3d` |
| Turquesa | `#00a896` | `#17c3b2` |
| Amarillo | `#ffc629` | `#ffd24d` |
| Morado | `#6c4ce0` | `#9b7bff` |

**La regla que más se rompe:** sobre los cinco acentos va tinta, no blanco. La única excepción es el morado en tema claro. Blanco sobre naranja da un contraste de 2,61 y no se lee en un proyector (`docs/marca.md:63-82`).

**El par más fuerte de la marca es amarillo con tinta encima, 11,19 a 1.** Por eso el cartel del ganador es amarillo. Si hay que destacar una sola cosa en una diapositiva, va en ese par. Para la diapositiva del ganador, o la del sorteo, es el recurso ideal (`docs/marca.md:84`).

Como el azul noche del afiche no es el fondo de Tinkazo, lo más limpio es poner lo de Tinkazo dentro de una tarjeta crema `#fff6e9` con borde y sombra de tinta (ver abajo), o usar `logo-horizontal-oscuro` directo sobre el azul.

### 4.3 Tipografía y estilo

- **Estilo: neobrutalismo.** Bordes gruesos de tinta, sombras duras sin desenfoque, colores planos. Borde grueso de 3 px sólido en tinta, borde fino de 2 px, sombra grande de `6px 6px 0` en tinta, sombra chica de `3px 3px 0`. Las calcomanías giran entre -2 y +2 grados (`docs/marca.md:86-98`).
- **Títulos:** `system-ui`, peso 900, con `letter-spacing: -0.02em`. Rótulos en versalitas, con separación de 0.08em a 0.14em.
- **Texto:** `system-ui`, pesos 500 a 700.
- **Todo dato que se pueda comprobar va en monoespaciada** (`ui-monospace`, Consolas, 700): una huella, un número de ronda, una dirección. Es una señal de la marca: lo que está en monoespaciada se puede comprobar (`docs/marca.md:137-145`).
- **Para los archivos de logo** se usó Montserrat Black (licencia OFL), porque la letra del sistema cambia de un equipo a otro (`docs/marca.md:254`). Si hace falta escribir "Tinkazo" como logotipo en el video, es Montserrat Black con "Tinka" en tinta y "zo" en magenta.
- **La llama:** magenta, con sombra dura de tinta, girada unos tres grados. Sin cara, sin ojos, sin sombrero ni poncho: es una silueta y con eso alcanza (`docs/marca.md:159-163`).

### 4.4 Frases de la marca (textos del sitio, tal cual)

- Lema: "Sorteos que cualquiera puede comprobar." En inglés, "Draws anyone can check." (`docs/marca.md:7-9`)
- Portada: "Sorteos justos, en pantalla grande." y "Pegá tu lista y mirá quién gana." (`index.html:73-74`)
- "Diez juegos. Ninguno decide nada." (`index.html:105`)
- "No hace falta creerme: cada paso se puede comprobar." (`index.html:123`)
- "Participar es gratis, siempre." (`index.html:430`)
- "Tu gente no necesita crear cuenta." (`src/i18n.ts:437`)
- "La lista se cierra antes de que exista el número que va a decidir. El orden es todo." (`docs/marca.md:382`)
- "Nadie puede elegir el número: tampoco quien organiza." (`src/i18n.ts:1312`)
- El pie del sitio: "Hecho con ♥ en Bolivia". Es del sitio. En las diapositivas rige la regla de la sección 4.5 sobre la palabra Bolivia.

El orden que la marca recomienda para presentar Tinkazo (`docs/marca.md:378-388`): la palabra, el problema (en todo sorteo hay alguien que cree que el organizador le dio el premio a su amigo), el truco en una frase, la demostración en vivo, la prueba desde un celular ajeno, el costo y la honestidad. La que más convence es mostrar un límite: la herramienta no da un verde fácil cuando no puede probar algo.

### 4.5 Lo que NO hay que hacer con la marca

- **El nombre:** "Tinkazo", siempre junto y con mayúscula inicial. Nunca "TinkaZo", ni "TINKAZO" en texto corrido, ni "Tinkazo App" (`docs/marca.md:17`). El sitio es **tinkazo.app**. La dirección con `.com` pertenece a otro sitio. Instagram es `@tinkazo.app`, con k.
- **El logo:** no estirarlo, no recolorearlo, no ponerle efectos, no ponerlo sobre un fondo que no contraste.
- **La llama:** no ponerle cara, ojos, sombrero ni poncho, y no redibujarla con curvas.
- **Efectos:** nada de degradados suaves ni de sombras difuminadas. Si una diapositiva tiene una sombra con desenfoque, no es de Tinkazo (`docs/marca.md:98`).
- **Texto blanco sobre un acento** (menos el morado claro). Va tinta.
- **Letra chica.** En pantalla grande, lo secundario no baja de 28 px en 1080 de alto, y lo principal va a 48 px o más (`docs/marca.md:151-157`).
- **Tecnicismos.** Nada de nombres de la red de números, bytes, firmas, hashes ni cifras de comisión a la vista. No se explica la criptografía antes de explicar para qué sirve. En una presentación no conviene mostrar el código del contrato, el diagrama de arquitectura ni la explicación de la firma (`docs/marca.md:181` y `:388`).
- **Palabras de la marca:** "Revoluciona", "disrumpe", "la próxima generación de", "impulsado por blockchain" (`docs/marca.md:179`). No decir "0 servidores" a secas: hay un servicio propio para los enlaces cortos y otro para las salas (`docs/marca.md:233`).
- **Prometer lo que no está hecho.** Si algo está en el modo Prueba, se dice Prueba. No afirmar que Tinkazo es el único ni el primero en algo: no hay un dato que lo respalde.
- **Juegos de mesa.** Nada de dados, cartas, fichas ni tragamonedas, ni como decoración (`docs/marca.md:294`).
- **Lo boliviano entra por la función, no por la decoración.** No van wiphalas, cholitas, el Illimani, Tiwanaku ni la palabra "Bolivia" escrita en pantalla en las piezas de Tinkazo (`docs/marca.md:212`).
- **Sugerir aval.** Tinkazo no es parte de la NASA ni de Space Apps, y no se escribe "aliado oficial", "socio" ni "certificado por Stellar" (`docs/marca.md:310` y `:350`). El logo de NASA Space Apps y el de la UCB van solo como aparecen en el afiche del evento.
- **Si se muestra el logo de Stellar**, es el oficial y sin alterar, como lo usa el sitio (`public/terceros/stellar/`), con la línea "Hecho con" y sin sugerir que la fundación lo avala (`docs/marca.md:333-354`).
- **Un comprobante de Prueba como evidencia permanente.** Deja de confirmarse el 16 de diciembre de 2026.

### 4.6 Créditos para el README

Una línea que se puede copiar:

> Tinkazo (https://tinkazo.app) es un proyecto de Nicolás Emir Mejía Agreda, de código abierto con licencia MIT: https://github.com/nema1502/tinkazo. Su logo y su llama son de Tinkazo.

Si en una diapositiva hay una captura de un juego con las caritas de los participantes, agregar: "Parte de los dibujos de los participantes son Twemoji, con licencia CC BY 4.0." Son 17 de los 32 dibujos (`public/emblemas/CREDITOS.txt:10-18`). La licencia completa está en `public/emblemas/LICENCIA-TWEMOJI-CC-BY-4.0.txt`.

## 5. Cómo unir n8n con el sorteo

### 5.1 La idea

Un **formulario de n8n** donde el público se anota desde el celular, con un QR en la diapositiva. Un segundo flujo **devuelve la lista limpia, lista para pegar en Tinkazo**. La charla es de n8n, así que lo que se cuenta es: "La lista del sorteo la armó una automatización mientras yo hablaba. Y la lista se cierra antes del número".

Es posible hoy sin cambiar nada de Tinkazo. El único paso manual es copiar y pegar la lista. Eso no es un defecto de la idea: en la lógica de Tinkazo, quien organiza arma la lista y decide quién entra, y esa decisión no se automatiza a ciegas.

Por qué encaja: el hueco que se encontró en la sección 2.5 es que no hay un camino para anotar a la sala en un sorteo sellado. El formulario lo cubre sin tocar Tinkazo.

**Una nota sobre los nombres de los nodos.** Los nombres de nodos y opciones de n8n que aparecen abajo (Form Trigger, Data table, Code, Respond to Webhook y los demás) son los que se conocen, pero no se verificaron en esta revisión. Quien arma los workflows tiene que confirmarlos contra la documentación oficial de n8n, que se anota en `contenido/investigacion.md`. Lo que sí está verificado es todo lo de Tinkazo.

### 5.2 Cómo se arma

**Flujo A: el formulario del público.**

1. **Form Trigger.** Un formulario con un solo campo obligatorio: "Tu nombre o apodo (sale en la pantalla)". Opcional, un segundo campo con la palabra de la charla (ver 5.4). Mensaje de cierre del formulario: "Listo, estás en la lista." Nada de correo, teléfono ni edad: cuanto menos se pide, menos hay que cuidar.
2. **IF (palabra de la charla).** Solo pasan los que escribieron la palabra que se muestra en una diapositiva. Frena a quien tenga el enlace pero no esté en la sala.
3. **Code (limpiar).** Deja el nombre como lo entiende Tinkazo (ver 5.3).
4. **Data table** (o Google Sheets si el plan lo pide). Guarda una fila por persona: nombre limpio y hora.

**Flujo B: la lista lista para pegar.**

1. **Webhook** con método GET.
2. **Data table**, leer todas las filas.
3. **Code**, quitar repetidos y armar el texto de la lista (el mismo código de 5.3, pensado para varias filas).
4. **Respond to Webhook** con la lista como **texto plano**, un nombre por línea. Al abrir su dirección en el navegador se ve solo la lista: se toca en la página, se selecciona todo, se copia, y en Tinkazo se toca **Pegar lista**. Variante: devolver un archivo CSV con una columna `nombre` para usar **Subir CSV**.

**Mientras se anota el público,** la pantalla puede mostrar la vista de ejecuciones de n8n: cada anotación es una ejecución nueva que aparece en vivo. Es una demostración de automatización con el público adentro.

### 5.3 El nodo que limpia (copiable)

Hace lo que hace Tinkazo al leer una lista: saca invisibles, cambia comas por espacio, junta espacios, exige 2 caracteres o más y no deja pasar repetidos aunque cambien mayúsculas o tildes. Corta a 40 caracteres, que es el tope de la sala de Tinkazo (`src/sala/filtro.ts:23`). Descarta lo que parezca un enlace o un correo. Para el nodo Code en modo "ejecutar una vez con todos los elementos". Está escrito sin punto y coma ni flechas para respetar las reglas de escritura del proyecto (JavaScript lo admite).

```js
function limpiar(texto) {
  return String(texto || '')
    .replace(/[\u200B-\u200F\u2060\uFEFF]/g, '')
    .replace(/,/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 40)
}

function clave(texto) {
  return texto.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase()
}

const vistos = {}
const nombres = []

for (const item of $input.all()) {
  const nombre = limpiar(item.json.nombre)
  if (nombre.length < 2) continue
  if (/https?:|www\.|@/i.test(nombre)) continue
  const k = clave(nombre)
  if (vistos[k]) continue
  vistos[k] = true
  nombres.push(nombre)
}

return [{ json: { cantidad: nombres.length, lista: nombres.join('\n') } }]
```

**Cómo se probó.** Fuera de n8n, en Node, con un `$input` simulado y doce entradas: dos repetidos (uno con mayúsculas distintas y otro con tilde), una coma, un nombre de una letra, un enlace, un correo, un carácter invisible, un nombre vacío y uno de más de 40 caracteres. Salieron 6 nombres limpios. Dentro de n8n no se probó: falta correrlo en el nodo Code con datos reales del formulario.

El campo `nombre` es el nombre del campo del formulario o de la columna de la tabla: si se llama distinto, se cambia en una sola línea. La regla de Tinkazo que respeta: `src/protocol/canonical.ts:9-20` y `src/ui/csv.ts:360-367`.

Para que la lista no pase de lo que cuenta un juego, se puede sumar un nodo IF que avise cuando `cantidad` pase de 200 (`src/ui/recomendar.ts:84-92`).

### 5.4 Antes y durante la charla

**Antes.**

- Armar los dos flujos y **ensayarlos con la dirección de producción** (la de un flujo activado, no la de prueba). Confirmar en la documentación de n8n cómo se obtiene cada dirección.
- Probar con cinco o diez nombres repetidos, con tildes, con comas, con un enlace y con un nombre larguísimo. Ver que la lista salga bien.
- **Pegar la lista de prueba en Tinkazo sin sellar** y mirar que diga "Lista de N personas" y que **Mostrar la lista en grande** la muestre bien. Antes de sellar no se graba nada.
- **Hacer el QR del formulario** y ponerlo en una diapositiva. Seguir las reglas de QR de la marca: tinta oscura sobre fondo claro, nunca invertido, con un margen blanco de cuatro módulos, grande, sin logo encima, y probarlo con un celular a la distancia real de la sala (`docs/marca.md:327`). Los QR de `public/marca/qr/` son solo para tinkazo.app: el del formulario hay que generarlo aparte.
- Poner en la misma diapositiva la dirección escrita, por si alguien no puede escanear.
- Vaciar la tabla antes de empezar.

**Durante.**

1. Mostrar el QR a mitad de la charla, durante la parte de n8n. Que se anoten mientras se habla de otra cosa.
2. Al final, ejecutar el flujo B, copiar la lista y pegarla en Tinkazo.
3. Mostrar la lista en grande a la sala. Mirar los repetidos y revisar nombres que no deban salir en pantalla antes de cerrarla. Es el momento de quitar un nombre, porque la lista se puede editar hasta sellar.
4. Sellar y seguir los pasos de la sección 2.3.

**Después de la charla.** Borrar la tabla. Los nombres salen en pantalla y en el enlace del comprobante, y no hace falta guardarlos.

### 5.5 Límites y cómo contarlos

- **El formulario es abierto.** Cualquiera con el enlace puede anotarse varias veces con nombres distintos o desde afuera de la sala. La palabra de la charla, los repetidos y el tope de 40 caracteres ayudan, pero no lo cierran del todo. Decirlo es parte de la lección: **Tinkazo prueba que el sorteo fue limpio a partir de la lista, y la lista sigue siendo cosa de quien organiza.** Es la misma honestidad que la marca pide.
- **Los nombres se ven en pantalla y en el comprobante.** Que el texto del formulario lo diga: "Tu nombre o apodo va a salir en la pantalla y en el enlace de comprobación del sorteo". Participar es gratis y no se pide nada más.
- **Un filtro de nombres con modelo de lenguaje** (revisar nombres ofensivos antes de la pantalla) calza con el tema de la charla. Tiene un costo: los nombres del público viajan a un proveedor de modelos. Si se hace, decirlo, y que lo dudoso vaya a una tabla "para revisar" en lugar de borrarse solo. La sala de Tinkazo hace algo parecido con una lista fija de palabras (`src/sala/filtro.ts`), y aun así avisa que "alguien tiene que estar mirando la pantalla".
- **Si el formulario cae,** se pega la lista de respaldo (sección 2.2).

### 5.6 Qué es posible hoy y qué no

| Posible hoy, sin cambiar Tinkazo | No es posible hoy |
| --- | --- |
| Que n8n arme, limpie y deje lista una lista de nombres | Que n8n cargue la lista en Tinkazo sin que una persona la pegue (no hay API, webhook ni parámetro, sección 2.6) |
| Pegar esa lista con **Pegar lista**, o subirla como CSV con **Subir CSV** | Que n8n anote a la gente en un sorteo ya sellado (la lista se cierra, y las salas por QR no llegan a un sorteo sellado, sección 2.5) |
| Mostrar esa lista a la sala con **Mostrar la lista en grande** y cerrarla con el sello | Que n8n lea el resultado: el comprobante viaja después del `#` del enlace y nunca llega a un servidor (`docs/evento.md:5`) |
| Sortear y compartir el comprobante con el QR | |

**Lo que haría falta cambiar en Tinkazo** para cerrar el hueco es un enlace que abra la herramienta con la lista cargada, como ya lo hace `lista.html` para solo leer. Es una idea para después de la charla. No se debe tocar nada de Tinkazo antes del evento.

### 5.7 Otras dos ideas más chicas

- **Lista desde donde ya está.** Si la lista ya existe en Luma, en una hoja de cálculo o en un formulario de otra herramienta, un flujo que la lea, la limpie con el mismo código de 5.3 y la devuelva como texto o CSV. Es el flujo B sin el formulario.
- **Aviso después del sorteo.** La guía de Tinkazo propone un mensaje de cierre (`sorteo-para-meetup.html`, sección 5, "Después"): "Gracias por venir. Acá está el resultado. Abrí el enlace para comprobarlo desde tu celular y buscá tu nombre en la lista." Un flujo donde Nicolás pega la dirección del comprobante en un formulario y n8n la manda con ese mensaje a un canal o a la lista de correo de los que se anotaron. Solo tiene sentido si el formulario del flujo A también pidió una forma de avisar, y eso suma datos personales: se evaluaría aparte.

## 6. Lo que se decide antes del sorteo

**Decisiones de quien organiza:**

1. **Prueba u Oficial para el sorteo con premio real.** La charla usa Prueba con la Cuenta de prueba, y así está descrito. Pero el propio sitio dice "Para tu evento, pasá a Oficial" y define Oficial como el modo "para los sorteos que cuentan". Oficial pide un cupón de evento y el paso "Dejá tu cuenta lista". Si el premio es de verdad, conviene decidirlo hoy y ensayar el camino elegido.
2. **A quién se sortea:** a las personas de la sala (sirve el formulario de n8n) o a los equipos del hackathon (sirve el registro de equipos de Tinkazo, que ya está prendido).
3. **Cuántos premios y cuáles.** De eso depende si alcanza la carrera de llamas (hasta 8) o si conviene otro juego.
4. **Si se usa la ronda de ejemplo con QR como calentamiento.** Es opcional y consume tiempo de charla.

**Para comprobar en el ensayo:**

- Un ensayo completo con navegador, con la Cuenta de prueba, de lista a comprobante, con el tiempo medido. Esta revisión se hizo leyendo el código y la documentación, no recorriendo el sorteo.
- Los nombres exactos de los nodos de n8n y de dónde sale la dirección de producción de un formulario y de un webhook en n8n Cloud.
- Que la lista de respaldo y el video del plan B estén guardados en la carpeta local de la charla.

## Fuentes y comprobaciones

**Archivos leídos del repositorio de Tinkazo** (commit e6500a42): `docs/marca.md`, `docs/ux.md`, `docs/evento.md`, `docs/juegos.md`, `docs/juegos/carrera.md`, `docs/motores.md`, `docs/kit-organizador.md`, `index.html`, `sorteo-para-meetup.html`, `src/i18n.ts`, `src/i18n-modo-oficial.ts`, `src/state.ts`, `src/main.ts`, `src/lista.ts`, `src/ensayo-modo.ts`, `src/stellar/config.ts`, `src/stellar/deployments.json`, `src/protocol/canonical.ts`, `src/ui/csv.ts`, `src/ui/participants.ts`, `src/ui/stand.ts`, `src/ui/stand-sala.ts`, `src/ui/recomendar.ts`, `src/ui/wallet-ui.ts`, `src/sala/cliente.ts`, `src/sala/filtro.ts`, `src/equipos/bandera.ts`, `src/equipos/textos.ts`, `workers/sala/README.md`, y la carpeta `public/marca/`. La copia de `docs/marca.md` que está en la rama principal de la carpeta de trabajo es más vieja y no trae la sección de letra grande ni algunas reglas, así que se usó la de la versión publicada.

**Comprobaciones contra el sitio publicado, el 13 de noviembre de 2026:**

1. La portada de https://tinkazo.app trae el botón **Tengo un stand: rondas de ejemplo con quienes pasan** (`id="btn-stand"`).
2. El servicio de salas `s.tinkazo.app` está vivo: contesta 404 a una sala inventada. No se creó ninguna sala.
3. En el código publicado, la función de la bandera de equipos tiene el valor 1 por defecto, y el modo con el que abre el sitio es Prueba (no hay un modo de construcción que lo cambie).

**Ejecutado:** nada en el repositorio de Tinkazo. Las consultas al sitio fueron lecturas de páginas públicas.
