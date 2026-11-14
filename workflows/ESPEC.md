# Los flujos de la charla: especificación

## Lo que cambió al construirlos y probarlos (14 de noviembre de 2026)

Los cuatro se construyeron, se importaron, se publicaron y se llamaron por HTTP en un n8n 2.47.7 local con SerpApi Official 0.1.10 y `openai/gpt-5-mini` por OpenRouter (OpenAI Chat Model con Base URL propia). Los JSON de `workflows/` son el export de ese n8n, limpio. Lo que esta especificación dice abajo vale, salvo esto:

1. **El modelo va sin temperatura.** `gpt-5-mini` no acepta una temperatura distinta de la de fábrica: OpenRouter lo lista sin ese parámetro y el nodo la manda igual, así que con Use Gateway credits podía fallar. Se sacó `options.temperature`.
2. **Flujos 2 y 3: Reasoning Effort en Low** (`options.reasoningEffort: low`). Medido con el mismo modelo: el flujo 3 bajó de 71 a 76 segundos a 46, y las respuestas del 2 de 13 a 28 segundos a entre 6 y 23. Si alguien elige un modelo que no razona, se saca esa opción (el README lo dice).
3. **Flujo 3: `options.timeout` en 120000.** El último paso del modelo tardó hasta 54 segundos y el cliente corta a los 60.
4. **Mensajes de sistema.** Los tres piden escribir sin rayas largas ni punto y coma (igual a veces aparecen: es lo que escribe el modelo). En el 2 se sumó "Si recomendás un lugar, decí su puntaje y cuántas reseñas tiene": sin eso, la pregunta de seguimiento volvía a buscar en Mapas, porque la memoria guarda las respuestas y no lo que trajo la herramienta. Con eso, la cuarta pregunta sale de la memoria sin buscar (comprobado). También "No ofrezcas hacer cosas que tus herramientas no hacen". En el 3, una frase por campo y tres elementos por lista, para que tarde menos.
5. **Flujo 4.** La tabla se nombra por nombre (`dataTableId` con `mode: name`, `sorteo_charla`), así el JSON anda en cualquier instancia que la tenga. Nueva rama C, **Preparar la tabla** (Manual Trigger y Data table, `table` `create`, `createIfNotExists`), para no tener que crearla a mano. **Leer la tabla** con `alwaysOutputData` (con la tabla vacía igual responde) y ordenada por `createdAt`. **Responder** con el encabezado `Content-Type: text/plain`: sin él la lista salía como HTML y el navegador juntaba los renglones en uno. n8n le agrega `charset=utf-8` solo.
6. **Formularios** con Custom Form Styling en los colores de la charla. **Páginas** de los flujos 1 y 3: también escapan las comillas dobles y solo aceptan enlaces que empiezan con http o https. El CSS va sin punto y coma: una regla por propiedad.
7. **Prueba.** El chat del flujo 2 se probó en una copia publicada como chat incrustado (`public: true`, `mode: webhook`). El JSON del repositorio sigue con `public: false`. `n8n execute` no sirve para Data tables (el módulo no carga en la línea de comandos): la rama C se probó desde el servidor, igual que el botón Execute.
8. **Lo que no se había podido comprobar, comprobado en 2.47.7:** el Form Trigger 2.6 usa `fieldName` como clave. Un JSON con `fieldName` y `options.path` importa tal cual. AI Agent 3.1 con Structured Output Parser y las herramientas de SerpApi anda (con `gpt-5-mini` por OpenRouter, falta probarlo con Gateway credits en Cloud). Sin SerpApi Official instalado, importar por línea de comandos funciona pero publicar falla con `Unrecognized node type: n8n-nodes-serpapi.serpApi`. Los JSON limpios, importados en un n8n vacío con el nodo instalado, solo piden credenciales: publicar los flujos 1 a 3 da `Missing required credential` en los nodos de SerpApi y del Modelo, el 4 se publica directo.
9. **Búsquedas de SerpApi gastadas en las pruebas: 24** (la cuenta pasó de 6 a 30 en el mes). Las respuestas están en `workflows/muestras/`.
10. **Flujo 2: la fecha de las noticias.** En el primer ensayo, el agente buscó NASA hoy y Google News devolvió notas de febrero, marzo y principios de noviembre con hoy en el título: el agente las contó como de ese día. Google News da la fecha como mes/día/año (11/04/2026 es una nota del 4 de noviembre, lo confirma su dirección). Se sumó al mensaje de sistema "Cuando cuentes una noticia, decí su fecha con día y mes. Noticias da la fecha como mes/día/año. Si la fecha no es de hoy, no digas hoy, aunque el título lo diga.", y la descripción de Noticias y su `$fromAI` piden mirar la fecha y buscar sin palabras como hoy. La pregunta de la charla pasó a ser ¿Qué noticias hay de la NASA esta semana? Decime la fecha de cada una. En Mapas, el ejemplo del `$fromAI` ya no dice abierto: con café abierto centro, Maps devolvió dos lugares sin `open_state`, y con café centro devolvió seis, cada uno con su `open_state`. Comprobado en un segundo ensayo (`workflows/muestras/flujo2-conversacion.json`): cada noticia salió con su fecha y la pregunta vieja, en otra sesión, citó una nota del día.
11. **Flujo 4: nombre y apellido.** Lista limpia saca repetidos aunque cambien mayúsculas o tildes, así que dos personas que se anotan como Ana quedan en una. El formulario pide ahora Tu nombre y apellido, o un apodo, y la descripción dice que sea un apodo que nadie más use. Solo cambia el texto: la clave del campo sigue siendo `nombre` (comprobado con las doce anotaciones de prueba).

Cuatro workflows de n8n para la charla Dale superpoderes a tus automatizaciones (Space Talks, Hackathon NASA Space Apps 2026, Santa Cruz). Este archivo dice qué se construye, nodo por nodo, y cómo se prueba y se demuestra. Los nombres de los nodos, sus tipos y sus versiones salen de `contenido/investigacion.md` (punto 2) y de la descripción de nodos de n8n 2.47.7 (`n8n-nodes-base` 2.47.5 y `@n8n/n8n-nodes-langchain` 2.47.5, `dist/types/nodes.json`). Los parámetros del nodo de SerpApi salen de su código (https://github.com/serpapi/n8n-nodes-serpapi).

| # | Nombre | La frase que lo vende | Qué enseña | Diapositiva |
|---|---|---|---|---|
| 1 | ¿Ya existe tu nombre? | Decí el nombre de tu proyecto y en segundos sabés si ya existe. | Un flujo en línea recta: primero ve, después piensa | D09 |
| 2 | El compañero de la madrugada | Le preguntás como a un amigo y él elige dónde buscar. | Un agente con herramientas y memoria elige solo | D10 |
| 3 | El scout del reto | Pegás tu reto y en un minuto tenés con qué arrancar. | Un agente que investiga, con una salida de forma fija que n8n convierte en página | D11 |
| 4 | La lista del sorteo | Te anotás desde el celular y la lista sale lista para Tinkazo. | Disparadores, limpieza de datos y una tabla dentro de n8n | D04, D05 y D14 |

Cada uno es más interesante que el anterior: el 1 tiene el orden fijo que pusimos nosotros, en el 2 el modelo decide qué herramienta usar, y el 3 hace varias búsquedas seguidas y entrega algo que el equipo usa esa misma noche.

## Lo común a los cuatro

### Versiones y nodos

- **n8n 2.47.7**, la estable. n8n 3 sigue en beta: nada de lo de acá se prueba ahí.
- **SerpApi Official** (nodo comunitario verificado, paquete `n8n-nodes-serpapi`), tipo `n8n-nodes-serpapi.serpApi`, versión 1. Como herramienta del agente, **SerpApi Official Tool**, tipo `n8n-nodes-serpapi.serpApiTool`, versión 1. Nunca el viejo SerpApi (Google Search), que está obsoleto desde n8n 2.35.0.
- Parámetros del nodo de SerpApi: `resource` = `search`, `operation` = el motor (`google`, `google_maps`, `google_news`, `youtube`, `google_scholar`), el campo de búsqueda (`q`, o `search_query` en YouTube) y `additionalFields` con `hl`, `gl` y `json_restrictor`. Google Maps tiene además `type` (`search`) y `ll` arriba, fuera de `additionalFields`.
- En una herramienta, la descripción para el modelo va en `descriptionType` = `manual` y `toolDescription` (los suma n8n al convertir el nodo en herramienta). El valor que llena el modelo se escribe con `$fromAI('clave', 'descripción', 'string')`.
- **El modelo:** OpenAI Chat Model, tipo `@n8n/n8n-nodes-langchain.lmChatOpenAi`, versión 1.3. Se eligió este porque en n8n Cloud acepta **Use Gateway credits** (sin llave) y en la compu acepta cualquier servicio compatible cambiando la Base URL de la credencial. Si alguien prefiere la llave gratis de Google AI Studio, se cambia el subnodo por Google Gemini Chat Model (`lmChatGoogleGemini` 1.2) y no cambia nada más.
  - En la compu, para probar: credencial OpenAI con la Base URL del servicio compatible, el modelo por ID y `responsesApiEnabled` en `false` (Chat Completions, que es lo que implementan los servicios compatibles).
  - En el JSON del repositorio: `"model": { "__rl": true, "mode": "list", "value": "gpt-5-mini" }` (el valor por defecto de la 1.3) y `responsesApiEnabled` en `false`. En Cloud, quien importa elige Use Gateway credits en la credencial y un modelo de la lista que aparece. Que ese modelo ande con Gateway credits está sin probar: se prueba en una cuenta de n8n Cloud antes de la charla, junto con cuántos créditos gasta cada demo.
  - `options.temperature` 0,4 en los cuatro modelos: queremos respuestas parecidas entre el ensayo y el vivo.

### Cómo se entregan

- Los JSON van en `workflows/` con estos nombres: `1-ya-existe-tu-nombre.json`, `2-companero-de-la-madrugada.json`, `3-scout-del-reto.json` y `4-lista-del-sorteo.json`.
- **Sin el bloque `credentials` en ningún nodo** (investigación, punto 4). Revisar también que ningún HTTP Request lleve encabezados con llaves y que el JSON no tenga la palabra `api_key`. Cada persona elige su credencial después de importar.
- `"settings": { "executionOrder": "v1" }` y `"active": false`.
- Cada workflow lleva **notas adhesivas** (Sticky Note, `n8n-nodes-base.stickyNote` versión 1) en español, cortas y grandes, que expliquen el flujo en el lienzo: el público las ve en el proyector. Una arriba con el nombre y la frase que lo vende, y una al lado de cada grupo de nodos que diga qué hace (por ejemplo, Ver: busca en Google con SerpApi). Sin punto y coma ni rayas, como el resto del repositorio.
- Nombres de nodo en español, cortos, los que se ven en las diapositivas (Formulario, Buscar en Google, Pensar, Página).
- Una guía corta por workflow en `workflows/README.md`: qué hace, cómo se importa en Cloud (instalar SerpApi Official antes de importar), qué credenciales elegir y una prueba de un minuto.

### Cómo se probaron

- **n8n en la compu:** `npx n8n@2.47.7` con Node 24, con `N8N_USER_FOLDER` apuntando a una carpeta temporal (nunca a la del usuario) y un `N8N_PORT` libre. SerpApi Official se instala como nodo comunitario (en la interfaz, Settings, Community Nodes, `n8n-nodes-serpapi`, o con npm dentro de la carpeta `.n8n/nodes` de esa instancia).
- **Credenciales:** `import:credentials` con un archivo armado por un guion que lee las llaves de los archivos `.env` locales con `node --env-file`. Ese archivo se crea fuera del repositorio y se borra apenas se importa. Nunca se imprime, y ninguna llave queda en los JSON, las muestras ni las capturas.
- **Importar cada JSON** con `import:workflow` en la 2.47.7 local antes de darlo por bueno: es la prueba de que el JSON está bien escrito.
- **Llamarlos de verdad:** una copia de prueba de cada workflow, publicada, con las credenciales puestas, y llamada por HTTP como lo haría el navegador: los formularios con un POST, el chat por su webhook y la lista con un GET. Los nodos Code se prueban antes con las muestras de `workflows/muestras/`, sin gastar búsquedas.
- **Búsquedas de SerpApi:** el plan gratis trae 250 por mes, así que cada respuesta nueva se guarda en `workflows/muestras/` con el mismo formato que las que ya están, sin la llave, y se reusa. Una búsqueda igual dentro de la hora sale de la caché y no se cobra.
- **El formulario y el chat públicos se prueban en Cloud**, no en la compu: un n8n local no se ve desde internet. Se hace en la cuenta de n8n Cloud de la charla, antes de empezar.

### El plan B de cada demo

1. **Con internet, si la demo falla en vivo:** en n8n, pestaña Executions, abrir la ejecución del ensayo de esa mañana y mostrarla nodo por nodo. Para eso cada flujo se corre una vez en la cuenta de Cloud antes de la charla.
2. **Sin internet:** las diapositivas de respaldo A1, A2 y A3, que muestran una captura del ensayo. La captura de cada flujo va en `diseno/medios/A1/ensayo.png` (flujo 1), `A2` (flujo 2) y `A3` (flujo 3): PNG de 2080 por 1520 px, una página a 1040 por 760 px con escala 2. Se arma con un archivo HTML local hecho con la salida real de la prueba (la página que devuelve el flujo 1 o 3, o la conversación del flujo 2 con la herramienta que usó cada respuesta) y una captura de Chrome sin cabeza, detrás del turno. Letra grande: lo más chico a 22 px de la página, que en la diapositiva queda a 22 px de 1080.
3. Si Nicolás graba la pantalla del ensayo de la mañana (Win + Alt + R), ese video va a `videos/` y es el mejor plan B de todos.

### Cómo se ven las páginas que devuelven los flujos 1 y 3

Un nodo n8n Form con Page Type Form Ending y `respondWith` = `showText` deja mostrar HTML propio (investigación, punto 2). La página usa los colores de la charla, para que la demo y las diapositivas se vean de la misma familia: fondo `#070A0F`, texto `#F5F7FF`, acento ámbar `#FFB547`, enlaces en azul `#4DA3FF`, texto de apoyo `#9AA3B8`, letra Segoe UI, system-ui o sans-serif en negrita, títulos de 44 px o más y texto de 22 px o más, una columna de 720 px como máximo. Todo texto que venga de afuera (el formulario, Google, el modelo) pasa por una función que escapa `&`, `<` y `>` antes de entrar al HTML. Los enlaces abren en otra pestaña.

## 1. ¿Ya existe tu nombre?

**La frase que lo vende:** Decí el nombre de tu proyecto y en segundos sabés si ya existe.

**Qué enseña:** un flujo en línea recta. Un disparador, un nodo que ve (SerpApi busca en Google), uno que piensa (el modelo lee lo que volvió y da un veredicto) y uno que responde. Las expresiones llevan el dato de un nodo al siguiente. El orden lo decidimos nosotros: primero ver, después pensar. Contrasta con el flujo 2, donde decide el agente.

**Credenciales:** SerpApi API (`serpApi`) y el modelo (OpenAI, o Use Gateway credits en Cloud).

### Nodo por nodo

1. **Formulario.** n8n Form Trigger, `n8n-nodes-base.formTrigger` 2.6. Con `webhookId` propio.
   - `formTitle`: ¿Ya existe tu nombre?
   - `formDescription`: Escribí el nombre de tu proyecto. Lo buscamos en Google y te decimos si está libre.
   - `formFields.values`: dos campos. Uno de texto con `fieldLabel` Nombre del proyecto, `fieldName` `nombre`, `placeholder` Por ejemplo, Chakana, `requiredField` true. Otro de texto con `fieldLabel` ¿De qué se trata? (opcional), `fieldName` `idea`, `placeholder` Una app que avisa cuando...
   - `responseMode`: `lastNode` (la página final la da el último nodo).
   - `options`: `path` `ya-existe` (desde la 2.2 la ruta va acá, no arriba), `buttonLabel` Buscar, `appendAttribution` false.
2. **Buscar en Google.** SerpApi Official, `n8n-nodes-serpapi.serpApi` 1.
   - `operation`: `google`.
   - `q`: `={{ '"' + $json.nombre.trim() + '"' }}` (el nombre exacto, entre comillas).
   - `additionalFields`: `hl` `es` y `json_restrictor` `organic_results[0:6].{title,link,snippet,source}`.
3. **Resumir resultados.** Code, `n8n-nodes-base.code` 2, JavaScript, Run Once for All Items. Arma un texto corto para el modelo y guarda los tres primeros enlaces para la página:

```js
const r = $input.first().json
const form = $('Formulario').first().json
const lista = (r.organic_results || []).slice(0, 6)
const renglones = lista.map(function (x, i) {
  return (i + 1) + '. ' + x.title + ' (' + (x.source || x.link) + '): ' + (x.snippet || '')
})
return [{
  json: {
    nombre: form.nombre.trim(),
    idea: (form.idea || '').trim(),
    cantidad: lista.length,
    resultados: renglones.length ? renglones.join('\n') : 'Google no encontró nada con ese nombre exacto.',
    enlaces: lista.slice(0, 3).map(function (x) { return { titulo: x.title, enlace: x.link } })
  }
}]
```

4. **Pensar.** Basic LLM Chain, `@n8n/n8n-nodes-langchain.chainLlm` 1.9 (existe en la 2.47.5, versiones 1 a 1.9).
   - `promptType`: `define`.
   - `text`: `={{ 'Nombre: ' + $json.nombre + '\nDe qué se trata: ' + ($json.idea || 'no lo dijo') + '\nLo que encontró Google:\n' + $json.resultados }}`
   - `messages.messageValues`: uno de tipo `SystemMessagePromptTemplate` con este texto:

```text
Sos el juez de nombres de un hackathon. Te paso el nombre de un proyecto, de qué se trata y lo que encontró Google al buscar ese nombre exacto.
Respondé en español, con estas tres líneas y nada más:
VEREDICTO: LIBRE, OCUPADO o DUDOSO
POR QUÉ: una sola frase que diga qué encontraste y dónde, o que no apareció nada parecido.
OTROS NOMBRES: tres nombres cortos y fáciles de decir en español, separados por comas.
OCUPADO quiere decir que hay una app, una empresa o un producto con ese nombre exacto. DUDOSO, que el nombre aparece pero para otra cosa. LIBRE, que no aparece.
No inventes nada que no esté en lo que encontró Google.
```

   - Subnodo **Modelo**: OpenAI Chat Model 1.3, conectado con `ai_languageModel`.
5. **Armar la página.** Code 2, Run Once for All Items. Separa las tres líneas y arma el HTML:

```js
function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function linea(texto, clave) {
  const m = texto.match(new RegExp(clave + '\\s*:\\s*(.+)', 'i'))
  return m ? m[1].trim() : ''
}
const datos = $('Resumir resultados').first().json
const texto = $input.first().json.text || ''
const veredicto = linea(texto, 'VEREDICTO').toUpperCase().replace(/[^A-ZÁÉÍÓÚ]/g, '') || 'DUDOSO'
const porque = linea(texto, 'POR QU[ÉE]')
const otros = linea(texto, 'OTROS NOMBRES').split(',').map(function (x) { return x.trim() }).filter(Boolean)
const enlaces = datos.enlaces.map(function (e) {
  return '<li><a href="' + esc(e.enlace) + '" target="_blank" rel="noopener">' + esc(e.titulo) + '</a></li>'
}).join('')
const html = '<div class="tarjeta">' +
  '<p class="rotulo">¿Ya existe tu nombre?</p>' +
  '<h1>' + esc(datos.nombre) + '</h1>' +
  '<p class="veredicto ' + esc(veredicto.toLowerCase()) + '">' + esc(veredicto) + '</p>' +
  '<p>' + esc(porque) + '</p>' +
  (otros.length ? '<p class="rotulo">Otros nombres</p><p class="otros">' + otros.map(esc).join(' / ') + '</p>' : '') +
  (enlaces ? '<p class="rotulo">Lo que encontró Google</p><ul>' + enlaces + '</ul>' : '') +
  '</div>'
return [{ json: { html: html, veredicto: veredicto } }]
```

   Quien lo arma agrega el bloque de estilo con los colores de la charla (sección de arriba): LIBRE en ámbar, OCUPADO en `#FF7A7A`, DUDOSO en `#9AA3B8`, el veredicto a 64 px.
6. **Página.** n8n Form, `n8n-nodes-base.form` 2.5, `operation` `completion`, `respondWith` `showText`, `responseText` `={{ $json.html }}`.

Conexiones `main`: Formulario, Buscar en Google, Resumir resultados, Pensar, Armar la página, Página. Modelo a Pensar por `ai_languageModel`.

### Entrada y salida de ejemplo

- **Entrada:** Nombre del proyecto Satelitazo, ¿De qué se trata? Una app que avisa cuando pasa un satélite sobre tu ciudad.
- **Nombres de respaldo** si la sala no se anima: Starlink (para mostrar un OCUPADO evidente, con sus enlaces) y el nombre de un proyecto que Nicolás invente en el momento.
- **Salida:** una página con el nombre, el veredicto en grande, una frase que cita lo encontrado, tres nombres alternativos y hasta tres enlaces reales. El veredicto exacto depende de lo que devuelva Google ese día: no se promete en la charla.

### La demo en vivo (menos de 2 minutos)

1. Desde D09, Nicolás pregunta a la sala el nombre de un proyecto.
2. Abre el formulario (la dirección de producción, en una pestaña ya abierta), escribe el nombre y toca Buscar. Unos segundos de espera: buen momento para decir que está buscando en Google de verdad.
3. Aparece la página. Lee el veredicto en voz alta y abre uno de los enlaces: el modelo no adivinó, leyó.
4. Si sobra tiempo, abre la ejecución en el editor y muestra el dato pasando de nodo en nodo.

**Momento de sorpresa:** el veredicto con pruebas, en segundos, sobre un nombre que la sala acaba de decir.

**Plan B sin internet:** A1 con la captura del ensayo.

**Búsquedas:** una por nombre. Repetir el mismo nombre en la hora no gasta.

## 2. El compañero de la madrugada

**La frase que lo vende:** Le preguntás como a un amigo y él elige dónde buscar.

**Qué enseña:** qué es un agente. Un modelo con tres herramientas (cada una con su descripción) y memoria. Nadie le dice qué herramienta usar: lee las descripciones y elige. `$fromAI` deja que el modelo escriba la búsqueda. La memoria hace que una pregunta de seguimiento funcione sin repetir el contexto.

**Credenciales:** SerpApi API y el modelo.

### Nodo por nodo

1. **Chat.** Chat Trigger, `@n8n/n8n-nodes-langchain.chatTrigger` 1.5, con `webhookId`. `public` false: en la charla se usa el chat del editor (Open chat), que no hace falta publicar.
2. **Compañero.** AI Agent, `@n8n/n8n-nodes-langchain.agent` 3.1.
   - `promptType`: `auto` (toma `chatInput` del Chat).
   - `options.maxIterations`: 6.
   - `options.systemMessage`:

```text
Sos el compañero de un equipo en el hackathon NASA Space Apps, en Santa Cruz de la Sierra, Bolivia. Ahora es {{ $now.setZone('America/La_Paz').setLocale('es').toFormat("cccc d 'de' LLLL, HH:mm") }}.
Respondés en español de Bolivia, corto y claro, como un amigo que sabe.
Tenés tres herramientas: Mapas (lugares en Google Maps), Noticias (Google News) y Videos (YouTube). Usá la que haga falta, o varias.
Nunca inventes lugares, horarios, noticias ni videos. Si no está en lo que devolvió la herramienta, decí que no lo encontraste.
Cuando recomiendes algo, nombrá de dónde sale (el lugar, el medio o el canal) y poné el enlace si lo tenés.
Como mucho seis renglones.
```

(El JSON final suma tres renglones que salieron de las pruebas: el puntaje y las reseñas de cada lugar, la fecha de cada noticia y no ofrecer lo que las herramientas no hacen. Ver el punto 4 y el 10 de arriba.)

3. **Modelo.** OpenAI Chat Model 1.3, `ai_languageModel` al agente.
4. **Memoria.** Simple Memory, `@n8n/n8n-nodes-langchain.memoryBufferWindow` 1.4, `sessionIdType` `fromInput`, `contextWindowLength` 6, `ai_memory` al agente.
5. **Mapas.** SerpApi Official Tool, `n8n-nodes-serpapi.serpApiTool` 1, `ai_tool` al agente.
   - `operation` `google_maps`, `type` `search`, `ll` `@-17.7833,-63.1821,14z` (centro de Santa Cruz, el mismo de la muestra).
   - `q`: `={{ $fromAI('q', 'Qué buscar en Google Maps, en español y con la zona, sin la palabra abierto (cada lugar ya dice si está abierto). Por ejemplo: café centro Santa Cruz de la Sierra', 'string') }}`
   - `additionalFields`: `hl` `es`, `json_restrictor` `local_results[0:6].{title,rating,reviews,type,open_state,address}`.
   - `descriptionType` `manual`, `toolDescription`: Busca lugares reales en Google Maps cerca del centro de Santa Cruz de la Sierra, Bolivia, por ejemplo cafés, comida, farmacias o fotocopias. Devuelve el nombre, el puntaje, cuántas reseñas tiene, si está abierto y la dirección. Usala para preguntas sobre lugares.
6. **Noticias.** SerpApi Official Tool 1, `ai_tool` al agente.
   - `operation` `google_news`.
   - `q`: `={{ $fromAI('q', 'El tema de las noticias, en pocas palabras y en español, sin palabras como hoy o ahora', 'string') }}`
   - `additionalFields`: `gl` `bo`, `hl` `es`, `json_restrictor` `news_results[0:8].{title,source,date,link}`.
   - `toolDescription`: Busca noticias en Google News, en español y para Bolivia. Devuelve el título, el medio, la fecha (mes/día/año) y el enlace. No todas son de hoy: mirá la fecha de cada una. Usala para preguntas sobre noticias de hoy o de esta semana.
7. **Videos.** SerpApi Official Tool 1, `ai_tool` al agente.
   - `operation` `youtube`.
   - `search_query`: `={{ $fromAI('busqueda', 'Qué buscar en YouTube, en español', 'string') }}`
   - `additionalFields`: `gl` `bo`, `hl` `es`, `json_restrictor` `video_results[0:5].{title,link,channel,length,views}`.
   - `toolDescription`: Busca videos en YouTube en español. Devuelve el título, el canal, la duración, las vistas y el enlace. Usala cuando pidan un video o un tutorial.

Conexiones: Chat a Compañero por `main`. Modelo, Memoria y las tres herramientas al Compañero por sus tipos de IA (en el lienzo se ven a trazos).

### Entrada y salida de ejemplo

Las tres preguntas de la charla, en este orden:

1. Somos cuatro y necesitamos un café abierto cerca del centro. ¿Dónde vamos? (usa Mapas)
2. ¿Qué noticias hay de la NASA esta semana? Decime la fecha de cada una. (usa Noticias)
3. Pasame un video corto en español para aprender n8n. (usa Videos)
4. De seguimiento: De esos cafés, ¿cuál tiene mejor puntaje? (no busca de nuevo: usa la memoria)

**Salida esperada:** respuestas cortas que nombran lugares, medios y canales reales con su enlace, y cada noticia con su fecha. En el registro del agente (Logs) se ve qué herramienta usó en cada pregunta. Lo que diga depende del día: las muestras de `workflows/muestras/` (Maps con café, YouTube con n8n tutorial español) sirven para probar sin gastar.

### La demo en vivo (2 minutos y medio)

1. Desde D10, Nicolás abre el workflow 2 en el editor y el chat.
2. Escribe las preguntas 1, 2 y 3 (puede pedirle a la sala que elija el tema de la segunda).
3. Abre el panel de registros y señala la herramienta de cada respuesta: Mapas, Noticias, Videos.
4. Hace la pregunta 4 y muestra que no hubo búsqueda nueva.

**Momento de sorpresa:** el registro muestra que eligió una herramienta distinta para cada pregunta, sin que nadie se lo dijera.

**Plan B sin internet:** A2 con la captura del ensayo (la conversación y, al lado de cada respuesta, la herramienta que usó).

**Búsquedas:** una o dos por pregunta. Unas cuatro por demo.

## 3. El scout del reto

**La frase que lo vende:** Pegás tu reto y en un minuto tenés con qué arrancar.

**Qué enseña:** un agente que hace varias búsquedas seguidas con distintas herramientas y una **salida con forma fija** (Structured Output Parser), que es lo que permite que n8n la convierta en una página. La IA piensa y n8n le da forma.

**Credenciales:** SerpApi API y el modelo.

### Nodo por nodo

1. **Tu reto.** n8n Form Trigger 2.6, con `webhookId`.
   - `formTitle`: El scout del reto
   - `formDescription`: Pegá el reto que eligieron. En un minuto te devuelvo qué existe, qué leer, qué ver y tres ideas para el fin de semana.
   - Campos: `reto` (Textarea, `fieldLabel` Tu reto, obligatorio, `placeholder` Pegá acá el reto o contalo con tus palabras) y `equipo` (Dropdown, `fieldLabel` ¿Qué sabe hacer tu equipo?, opciones Web, Apps, Datos, Hardware y Diseño, obligatorio).
   - `responseMode` `lastNode`. `options`: `path` `scout-del-reto`, `buttonLabel` Investigar, `appendAttribution` false.
2. **Scout.** AI Agent 3.1.
   - `promptType` `define`, `text`: `={{ 'Reto: ' + $json.reto + '\nNuestro equipo sabe de: ' + $json.equipo }}`
   - `hasOutputParser` true.
   - `options.maxIterations` 8.
   - `options.systemMessage`:

```text
Sos el scout de un equipo del hackathon NASA Space Apps en Santa Cruz de la Sierra, Bolivia. Te pasan el reto que eligieron y lo que sabe hacer el equipo.
Investigá con tus herramientas, como mucho una búsqueda con cada una: Google para ver qué ya existe, Artículos para encontrar qué leer y Videos para encontrar un tutorial que les sirva.
Después proponé tres ideas que un equipo de cuatro personas pueda armar en un fin de semana con lo que sabe hacer. Cada idea con un primer paso concreto para esta noche.
Respondé en español. Usá solo enlaces que vinieron en los resultados de las herramientas, nunca inventes uno. Si una herramienta no trajo nada útil, dejá esa lista vacía.
```

3. **Modelo.** OpenAI Chat Model 1.3, `ai_languageModel`.
4. **Google.** SerpApi Official Tool 1, `operation` `google`, `q` con `$fromAI('q', 'Qué buscar en Google para ver proyectos, apps o datos abiertos que ya existan sobre el reto', 'string')`, `additionalFields` `hl` `es`, `json_restrictor` `organic_results[0:5].{title,link,snippet,source}`. Descripción: Busca en Google proyectos, apps, datos abiertos y páginas que ya existan sobre el tema. Se puede escribir en español o en inglés.
5. **Artículos.** SerpApi Official Tool 1, `operation` `google_scholar`, `q` con `$fromAI('q', 'Búsqueda en inglés, con palabras técnicas del tema', 'string')`, `json_restrictor` `organic_results[0:5].{title,link,snippet,publication_info}`. Descripción: Busca artículos académicos en Google Scholar. Escribí la búsqueda en inglés.
6. **Videos.** SerpApi Official Tool 1, igual que en el flujo 2 (`youtube`, `gl` `bo`, `hl` `es`). Descripción: Busca tutoriales en YouTube en español para aprender la tecnología que necesita el equipo.
7. **Forma de la respuesta.** Structured Output Parser, `@n8n/n8n-nodes-langchain.outputParserStructured` 1.3, `schemaType` `fromJson`, `ai_outputParser` al agente, con este ejemplo en `jsonSchemaExample`:

```json
{
  "reto_en_una_frase": "Avisar a tiempo cuando hay riesgo de incendio cerca de una comunidad",
  "ya_existe": [{ "nombre": "Nombre del proyecto", "que_es": "Qué hace, en una frase", "enlace": "https://..." }],
  "para_leer": [{ "titulo": "Título del artículo", "enlace": "https://..." }],
  "para_ver": [{ "titulo": "Título del video", "canal": "Canal", "enlace": "https://..." }],
  "ideas": [{ "nombre": "Nombre corto", "que_hace": "Qué hace, en una frase", "primer_paso": "Qué hacer esta noche" }]
}
```

8. **Armar la página.** Code 2. Lee `$json.output` (la respuesta ya con forma) y arma el HTML con las cinco partes: el reto en una frase arriba, Ya existe, Para leer, Para ver y las tres ideas en tarjetas numeradas. Mismas reglas que el flujo 1: todo escapado, enlaces en otra pestaña, los colores de la charla. Si una lista viene vacía, esa sección no se muestra.
9. **Página.** n8n Form 2.5, `completion`, `showText`, `responseText` `={{ $json.html }}`.

### Entrada y salida de ejemplo

- **Reto de ejemplo** (escrito para la demo, no es un reto oficial del hackathon): Queremos avisar a las comunidades rurales de Santa Cruz cuando hay riesgo de incendio cerca, usando datos de satélites de la NASA. Equipo: Datos.
- Mejor todavía, el reto real de un equipo de la sala.
- **Salida esperada:** una página con el reto en una frase, de uno a cinco proyectos que ya existen, de uno a cinco artículos, de uno a cinco videos y tres ideas con su primer paso. Todos los enlaces vienen de las búsquedas.

### La demo en vivo (menos de 2 minutos)

1. Desde D11, Nicolás abre el formulario del flujo 3 y pega el reto (el de un equipo o el de ejemplo, que tiene copiado).
2. Mientras el agente trabaja (de 20 a 60 segundos), abre la ejecución en el editor y muestra las herramientas que va usando.
3. Vuelve a la pestaña del formulario: aparece la página. Recorre las cinco partes y abre un enlace.

**Momento de sorpresa:** en menos de un minuto, una página ordenada con enlaces reales y tres ideas para esa misma noche.

**Cuidado:** el límite de Cloud es de 180 segundos por ejecución. Si en el ensayo tarda más de 60, bajar `maxIterations` a 6 o pedir en el mensaje de sistema que use solo Google y Videos.

**Plan B sin internet:** A3 con la captura del ensayo. Si va tarde, también A3.

**Búsquedas:** tres por reto.

## 4. La lista del sorteo

**La frase que lo vende:** Te anotás desde el celular y la lista sale lista para Tinkazo.

**Qué enseña:** que un flujo puede tener dos disparadores, que limpiar datos es un paso más, y que n8n guarda datos sin ningún servicio de afuera (Data tables). Es el flujo que la sala usa en D04 y que se explica en D05.

**Credenciales:** ninguna. Antes de importar, crear en el proyecto la Data table **sorteo_charla** con una columna de texto **nombre** (pestaña Data tables, desde cero).

Por qué no se usa la sala por QR de Tinkazo: esos nombres son solo para rondas de ejemplo y nunca van a un sorteo sellado (contenido/tinkazo.md, 2.5). Este flujo cubre ese hueco sin tocar Tinkazo. El único paso a mano es copiar y pegar la lista, y está bien que así sea: quien organiza decide quién entra.

### Rama A: anotarse

1. **Anotate.** n8n Form Trigger 2.6, con `webhookId`.
   - `formTitle`: Sorteo de la charla
   - `formDescription`: Poné tu nombre y apellido, o un apodo que nadie más use: va a salir en la pantalla y en el enlace para comprobar el sorteo. Participar es gratis.
   - Campos: `nombre` (Text, `fieldLabel` Tu nombre y apellido, o un apodo, obligatorio) y `palabra` (Text, `fieldLabel` La palabra de la charla, `placeholder` Está en la pantalla, obligatorio). Nada de correo, teléfono ni edad.
   - `responseMode` `lastNode`. `options`: `path` `sorteo-space-apps`, `buttonLabel` Anotarme, `appendAttribution` false.
2. **¿Dijo la palabra?** If, `n8n-nodes-base.if` 2.4. Condición: `={{ String($json.palabra || '').trim().toLowerCase() }}` igual a `llama`.
3. Rama verdadera, **Limpiar.** Code 2, **Run Once for Each Item**, con la misma limpieza de Tinkazo:

```js
function limpiar(texto) {
  return String(texto || '')
    .replace(/[\u200B-\u200F\u2060\uFEFF]/g, '')
    .replace(/,/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 40)
}
return { json: { nombre: limpiar($json.nombre) } }
```

4. **Guardar.** Data table, `n8n-nodes-base.dataTable` 1.1, `resource` `row`, `operation` `insert`, tabla sorteo_charla, columna `nombre` = `={{ $json.nombre }}`.
5. **Listo.** n8n Form 2.5, `completion`, `respondWith` `text`, `completionTitle` Listo, estás en la lista, `completionMessage` Al final de la charla sorteamos con Tinkazo. Mirá la pantalla.
6. Rama falsa, **Falta la palabra.** n8n Form 2.5, `completion`, `completionTitle` Esa no es la palabra, `completionMessage` Está en la pantalla de la charla. Volvé a abrir el formulario e intentá de nuevo.

### Rama B: la lista para Tinkazo

1. **Lista.** Webhook, `n8n-nodes-base.webhook` 2.2, con `webhookId`, `httpMethod` `GET`, `path` `lista-sorteo-space-apps`, `responseMode` `responseNode`.
2. **Leer la tabla.** Data table 1.1, `operation` `get`, tabla sorteo_charla, `returnAll` true.
3. **Lista limpia.** Code 2, Run Once for All Items, el código de `contenido/tinkazo.md` (5.3) tal cual: saca invisibles, cambia comas por espacios, exige 2 caracteres o más, descarta enlaces y correos y no deja pasar repetidos aunque cambien mayúsculas o tildes. Devuelve `cantidad` y `lista` (un nombre por línea).
4. **Responder.** Respond to Webhook, `n8n-nodes-base.respondToWebhook` 1.5, `respondWith` `text`, `responseBody` `={{ $json.lista }}`. Si el navegador muestra mal las tildes, agregar el encabezado Content-Type con text/plain y charset utf-8.

### Entrada y salida de ejemplo

- **Entrada:** desde el celular, Tu nombre y apellido, o un apodo: ` Ana , ` y la palabra Llama.
- **Salida de la rama A:** una fila nueva en sorteo_charla con `Ana` y la página Listo, estás en la lista.
- **Salida de la rama B:** al abrir la dirección de producción de Lista en el navegador, solo texto, un nombre por línea, sin repetidos. Se selecciona todo, se copia y en Tinkazo se toca Pegar lista.
- **Prueba antes de publicar:** doce entradas como las de tinkazo.md 5.3 (repetidos con mayúsculas y tildes, una coma, un nombre de una letra, un enlace, un correo, un invisible, uno vacío y uno de más de 40 letras) tienen que dar 6 nombres.

### En la charla

- **D04:** el QR abre la dirección de producción de Anotate. La palabra de la charla es llama.
- **D05:** mientras se explica qué es un flujo, se puede mostrar la pestaña Executions con las anotaciones que van entrando.
- **D14:** Nicolás abre la dirección de Lista en una pestaña, copia todo, va a tinkazo.app y sigue el paso a paso de contenido/tinkazo.md, 2.3.

**Plan B:** si la rama B falla pero la tabla tiene los nombres, se baja la tabla como CSV desde la pestaña Data tables y en Tinkazo se usa Subir CSV. Si el formulario no anda, que levanten la mano los que quieren entrar y Nicolás escribe sus nombres directo en Tinkazo, uno por línea. Nunca una lista inventada: el sorteo es entre los que están.

**Límites que se dicen en voz alta:** el formulario es abierto. La palabra y la limpieza ayudan, pero alguien con el enlace puede anotarse dos veces con nombres distintos. Por eso la lista se muestra a la sala antes de sellarla. Tinkazo prueba que nadie tocó el resultado después de cerrar la lista, no que la lista esté bien armada.

**Después de la charla:** vaciar la tabla. Los nombres ya salieron en pantalla y en el comprobante, y no hace falta guardarlos.

## Lo que esta especificación no pudo comprobar

- Que el AI Agent 3.1 ande con el Structured Output Parser y las herramientas de SerpApi con el modelo de Gateway credits. Se comprueba en el ensayo de Cloud.
- Que la salida del Form Trigger 2.6 use `fieldName` como clave (así lo sugiere la descripción del nodo desde la 2.5). Si usa la etiqueta, se ajustan las expresiones.
- Que un JSON con `fieldName` y `options.path` importe tal cual en la versión de Cloud de la cuenta de la charla. Ver la versión en el menú de ayuda, About n8n.
- Qué pasa en Cloud al importar un workflow con SerpApi Official sin el nodo instalado. Por eso se instala antes.
