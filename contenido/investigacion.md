# Investigación: n8n, SerpApi y modelos de IA

Consultado el 13 de noviembre de 2026, de noche (hora de Bolivia). Cada dato lleva la dirección de donde salió. Lo que no se pudo comprobar está en la última sección y no va a las diapositivas.

Las citas en inglés van textuales, entre comillas rectas. Las traducciones son nuestras.

## Lo que cambia decisiones (leer primero)

1. **n8n 3 todavía es beta.** La versión estable es la 2.47.7. n8n 3.0 salió en beta el 27 de octubre de 2026 y la estable está anunciada para principios de diciembre. Los workflows de la charla se escriben y se prueban para 2.47.
2. **El nodo viejo de SerpApi está obsoleto.** SerpApi (Google Search) quedó obsoleto desde n8n 2.35.0. El que va es **SerpApi Official**, un nodo comunitario verificado que mantiene SerpApi. Como herramienta del agente se llama **SerpApi Official Tool**.
3. **La prueba de n8n Cloud dura 14 días, no pide tarjeta y trae 1.000 ejecuciones.** Cada mensaje a un Chat Trigger gasta una ejecución. Si el público usa un chat o un formulario de la cuenta del orador, las 1.000 se pueden ir rápido, y solo corren 5 a la vez (el resto espera en cola).
4. **En n8n Cloud se pueden usar modelos sin llave propia** con los Gateway credits. La prueba trae 100 AI credits según la página de precios.
5. **El nodo OpenAI Chat Model 1.3 trae prendido Use Responses API.** Para un servicio compatible con la API de OpenAI y dirección base propia, conviene apagarlo y usar Chat Completions.
6. **npx n8n ya no sirve desde n8n 3, pero sí en 2.x.** Para probar en la compu: `npx n8n@2.47.7`, con Node 24.
7. **n8n cambió su marca el 14 de octubre de 2026**, en la conferencia In The Loop. El logo nuevo está en `diseno/logos/n8n/`. El viejo no se usa.

## 1. n8n hoy

### Qué es, en sus palabras

- Documentación: "n8n is a fair-code licensed workflow automation tool that combines AI features with business process automation." https://docs.n8n.io/
- Portada: "n8n is the platform for agents and workflows you can follow." https://n8n.io/
- Repositorio: "Fair-code workflow automation platform with native AI capabilities. Combine visual building with custom code, self-host or cloud, 400+ integrations." https://github.com/n8n-io/n8n
- El nombre se escribe siempre en minúscula y se pronuncia "n eight n" (en español, ene ocho ene). https://n8n.io/press/

En dos líneas: n8n es una herramienta para automatizar flujos de trabajo que junta la IA con la automatización de procesos. Se arma con bloques visuales y código cuando hace falta, en la nube o en un servidor propio.

### Versión actual

| Canal | Versión | Fuente |
| --- | --- | --- |
| Estable (npm `latest` y `stable`) | 2.47.7 | https://registry.npmjs.org/-/package/n8n/dist-tags |
| Beta de la línea 2 (npm `next` y `beta`) | 2.48.4 | misma |
| n8n 3, prelanzamiento en GitHub | 3.2.2 | https://github.com/n8n-io/n8n/releases |

- n8n 3.0.0 beta: "October 27, 2026". La estable, "early December". https://blog.n8n.io/introducing-n8n-v3
- En Cloud, el dueño de la instancia elige la versión y el canal (Beta o Stable) en Instance settings del Cloud console. n8n actualiza toda instancia al menos cada dos semanas. https://docs.n8n.io/deploy/use-n8n-cloud/update-your-version
- Lo de n8n 3.0 que nos toca: ya no se instala con npm ni con `npx n8n`, el Chat Trigger manda los mensajes por WebSocket como JSON, se elimina la versión 1 del AI Agent y desaparece Import from URL del editor. https://docs.n8n.io/changelog/v30-breaking-changes

### n8n Cloud: la prueba gratis

- **Enlace para registrarse:** https://app.n8n.cloud/register (es el botón Get Started de la portada, https://n8n.io/). Desde la página de precios, los botones Start free trial llevan a https://app.n8n.cloud/register?planId=starter y https://app.n8n.cloud/register?planId=pro. https://n8n.io/pricing/
- **Duración:** "you have 14 days to try all the features of the Pro plan", "with a limit of 1000 executions" y con "the same computing power as the Starter plan". https://docs.n8n.io/deploy/use-n8n-cloud/start-your-free-trial
- **Tarjeta:** "No credit card is required for the n8n Cloud trial." Solo la prueba del plan Business pide tarjeta. https://n8n.io/pricing/
- **Qué incluye** (precios): Global Variables, Insights (con el tablero y 14 días de historia), 5 días de historial del workflow, filtros avanzados de ejecuciones, evaluaciones ilimitadas, carpetas y el Assistant. "800 Assistant credits, plus 100 AI credits". https://n8n.io/pricing/
- **Límites** (precios): "1,000 executions, 5 concurrent executions, a 180-second execution timeout, and 1 team project". No incluye Admin Roles, el rol Editor de proyecto, Named Versions, Workflow Diffs ni la API pública de n8n. https://n8n.io/pricing/
- **Lo que pasa del límite de a 5:** queda en cola y se procesa en orden de llegada. Para este límite cuentan solo las ejecuciones de producción (las que arranca un webhook o un disparador), no las manuales. https://docs.n8n.io/deploy/use-n8n-cloud/understand-concurrency
- **Al terminar:** si no se paga, la prueba vence sola, sin cargos, y n8n borra la instancia. Quedan 90 días para bajar los workflows. https://docs.n8n.io/deploy/use-n8n-cloud/start-your-free-trial
- **Planes pagos** (precio por mes, pagando el año): Starter 20 €, Pro 50 €, Business 667 € (solo autoalojado), Enterprise a consultar. https://n8n.io/pricing/

### Modelos de IA sin llave propia: Gateway credits

- "Use Gateway credits to run AI models and third-party services in your n8n workflows without provider accounts or API keys." https://docs.n8n.io/deploy/use-n8n-cloud/gateway-credits
- Disponibles en n8n Cloud Starter y Pro, desde n8n 2.36.0. No en Cloud Enterprise ni en n8n autoalojado. "Free trials include Gateway credits, but you can't top up until you upgrade to a paid plan." (misma dirección)
- **Cómo se usan:** en el campo de credencial del nodo se elige **Use Gateway credits**, que muestra el saldo. Los nodos que lo aceptan aparecen arriba, en Included in n8n, con la etiqueta Gateway credits o Free credits. https://docs.n8n.io/build/understand-workflows/use-gateway-credits.md
- **Qué nodos lo dicen en su documentación:** OpenAI Chat Model y Google Gemini Chat Model ("Select Use Gateway credits in the node's credential field"). https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai y https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatgooglegemini
- **Proveedores del anuncio** (2 de septiembre de 2026): modelos de OpenAI, Anthropic, Google Gemini, Alibaba Cloud Qwen, MiniMax y Moonshot Kimi. Servicios: Brave Search, Firecrawl, Browserbase, LlamaParse y PDF.co. https://community.n8n.io/t/try-new-models-and-services-skip-the-account-setup/310859
- **Cuántos créditos:** la página de precios dice 100 AI credits para la prueba. La documentación solo dice "a small amount of free credit at sign-up". Cuánto rinde un crédito depende del modelo y está en https://app.n8n.cloud/service-pricing (pide cuenta, no la pude leer).
- Si el saldo llega a cero, los nodos que usan Gateway credits fallan. Los Gateway credits no pagan el Assistant, que tiene sus propios créditos. https://docs.n8n.io/build/understand-workflows/use-gateway-credits.md
- El viejo regalo de créditos de OpenAI para cuentas nuevas figura como "legacy" y solo en instancias sin Gateway credits. https://docs.n8n.io/deploy/use-n8n-cloud/gateway-credits

### ¿Se puede publicar un formulario o un chat público desde la prueba?

Según la documentación, sí. La prueba trae "all the features of the Pro plan" y ni la página de la prueba ni la de precios ponen límites a formularios, webhooks o chats públicos. El Form Trigger y el Chat Trigger público funcionan al **publicar** el workflow (ver punto 2). Lo que sí limita: 1.000 ejecuciones, 5 a la vez y 180 segundos por ejecución. No lo probé con una cuenta de prueba de verdad (ver al final).

## 2. Los nodos que vamos a usar

**Publicar en lugar de activar.** Desde n8n 2.0 no hay interruptor de activo: se **publica** con el botón Publish (atajo Shift + P). Al publicar, "Webhook and form triggers will use their production URLs", "Schedules will run at the times you've defined" y los eventos de apps conectadas disparan el workflow. Los cambios se guardan solos y quedan en borrador hasta publicar otra vez. https://docs.n8n.io/build/understand-workflows/save-and-publish-workflows

### Nombres y versiones para escribir el JSON

Versiones tomadas de la descripción de los nodos que trae n8n 2.47.7 (paquetes `n8n-nodes-base` 2.47.5 y `@n8n/n8n-nodes-langchain` 2.47.5, archivo `dist/types/nodes.json`):
https://registry.npmjs.org/n8n/2.47.7, https://cdn.jsdelivr.net/npm/n8n-nodes-base@2.47.5/dist/types/nodes.json y https://cdn.jsdelivr.net/npm/@n8n/n8n-nodes-langchain@2.47.5/dist/types/nodes.json

| Nombre en pantalla | `type` en el JSON | `typeVersion` más nuevo | Credencial (tipo) |
| --- | --- | --- | --- |
| Manual Trigger | `n8n-nodes-base.manualTrigger` | 1 | ninguna |
| Schedule Trigger | `n8n-nodes-base.scheduleTrigger` | 1.4 | ninguna |
| Webhook | `n8n-nodes-base.webhook` | 2.2 | opcional: `httpBasicAuth`, `httpHeaderAuth`, `jwtAuth` |
| Respond to Webhook | `n8n-nodes-base.respondToWebhook` | 1.5 | opcional: `jwtAuth` |
| n8n Form Trigger | `n8n-nodes-base.formTrigger` | 2.6 | opcional: `httpBasicAuth` |
| n8n Form (páginas siguientes y final) | `n8n-nodes-base.form` | 2.5 | ninguna |
| Chat Trigger | `@n8n/n8n-nodes-langchain.chatTrigger` | 1.5 | opcional: `httpBasicAuth` |
| AI Agent | `@n8n/n8n-nodes-langchain.agent` | 3.1 | ninguna |
| OpenAI Chat Model | `@n8n/n8n-nodes-langchain.lmChatOpenAi` | 1.3 | `openAiApi` |
| Google Gemini Chat Model | `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 1.2 | `googlePalmApi` |
| OpenRouter Chat Model | `@n8n/n8n-nodes-langchain.lmChatOpenRouter` | 1 | `openRouterApi` |
| Groq Chat Model | `@n8n/n8n-nodes-langchain.lmChatGroq` | 1 | `groqApi` |
| Simple Memory | `@n8n/n8n-nodes-langchain.memoryBufferWindow` | 1.4 | ninguna |
| Structured Output Parser | `@n8n/n8n-nodes-langchain.outputParserStructured` | 1.3 | ninguna |
| Calculator | `@n8n/n8n-nodes-langchain.toolCalculator` | 1 | ninguna |
| Wikipedia | `@n8n/n8n-nodes-langchain.toolWikipedia` | 1 | ninguna |
| Think Tool | `@n8n/n8n-nodes-langchain.toolThink` | 1.1 | ninguna |
| Code Tool | `@n8n/n8n-nodes-langchain.toolCode` | 1.3 | ninguna |
| Call n8n Workflow Tool | `@n8n/n8n-nodes-langchain.toolWorkflow` | 2.2 | ninguna |
| HTTP Request Tool | `n8n-nodes-base.httpRequestTool` | 4.5 | las del HTTP Request |
| Data table Tool | `n8n-nodes-base.dataTableTool` | 1.1 | ninguna |
| SerpApi Official Tool | `n8n-nodes-serpapi.serpApiTool` | 1 | `serpApi` |
| SerpApi Official | `n8n-nodes-serpapi.serpApi` | 1 | `serpApi` |
| HTTP Request | `n8n-nodes-base.httpRequest` | 4.5 | según el caso |
| Code | `n8n-nodes-base.code` | 2 | ninguna |
| Edit Fields (Set) | `n8n-nodes-base.set` | 3.5 | ninguna |
| Data table | `n8n-nodes-base.dataTable` | 1.1 | ninguna |
| If | `n8n-nodes-base.if` | 2.4 | ninguna |
| Switch | `n8n-nodes-base.switch` | 3.5 | ninguna |
| Sticky Note | `n8n-nodes-base.stickyNote` | 1 | ninguna |

Notas sobre la tabla:

- Las variantes de herramienta de un nodo común (las que terminan en Tool) no están en `nodes.json`: n8n las arma al arrancar, sumando `Tool` al nombre del tipo y " Tool" al nombre visible, con las mismas versiones del nodo de base. Código de n8n 2.47.7: https://github.com/n8n-io/n8n/blob/n8n%402.47.7/packages/cli/src/tool-generation/ai-tools.ts
- Los tipos de SerpApi salen del paquete del nodo comunitario: nombre de paquete `n8n-nodes-serpapi`, nodo `serpApi`, versión 1, `usableAsTool: true`, credencial `serpApi`. https://github.com/serpapi/n8n-nodes-serpapi/blob/master/nodes/SerpApi/SerpApi.node.ts
- El nodo obsoleto `@n8n/n8n-nodes-langchain.toolSerpApi` (versión 1) sigue en 2.47.7 pero oculto. No usarlo.

### Lo que pide cada uno

**Manual Trigger.** Nada. Se corre con Execute Workflow y no corre solo. Uno por workflow. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualworkflowtrigger

**Schedule Trigger.** Trigger Rules con un intervalo: segundos, minutos, horas, días, semanas, meses o Cron. Hay que publicar el workflow. Usa la zona horaria del workflow o, si no tiene, la de la instancia (Cloud intenta detectar la del dueño al registrarse y si no usa GMT). Desde n8n 2.45.0 los intervalos de segundos y minutos se cuentan desde la publicación, no desde el reloj. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger

**Webhook.** HTTP Method, Path, autenticación (opcional) y Respond: Immediately, When Last Node Finishes, Using Respond to Webhook Node o Streaming. Tiene dos direcciones: la de prueba, que escucha con Listen for Test Event y muestra los datos en el editor, y la de producción, que se registra al publicar. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook

**n8n Form Trigger (formulario público).** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.formtrigger
- Form Title (título y h1), Form Description (subtítulo), Form Elements y Respond When (Form Is Submitted o Workflow Finishes).
- Tipos de campo: Checkboxes, Custom HTML, Date, Dropdown, Email, File, Hidden Field, Number, Password, Radio Buttons, Text y Textarea. En el JSON: `checkbox`, `html`, `date`, `dropdown`, `email`, `file`, `hiddenField`, `number`, `password`, `radio`, `text`, `textarea`.
- Para que sea público: Authentication en None (las otras son Basic Auth y n8n User Auth).
- Opciones: Form Path, Button Label, Append n8n Attribution (para sacar el pie "Form automated with n8n"), Ignore Bots, Custom Form Styling (CSS propio).
- **Ojo al escribir el JSON:** desde la versión 2.2 la ruta va en `parameters.options.path`. "On node version 2.2 and later, n8n ignores a top-level `parameters.path` when it loads the workflow." Si no, la dirección termina en el `webhookId`.
- Se pueden precargar campos con parámetros en la dirección, solo en producción.

**Página final del formulario.** Es un nodo **n8n Form** con Page Type **Form Ending** (en el JSON, `"operation": "completion"`). El workflow tiene que empezar con un n8n Form Trigger. On n8n Form Submission ofrece: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.form
- Show Completion Screen (`respondWith: "text"`): Completion Title y Completion Message.
- Redirect to URL (`"redirect"`).
- Show Text (`"showText"`): HTML libre, y acá sí se permiten `script`, `style` e `input`.
- Return Binary File (`"returnBinary"`).
- Solo se muestra una página final por ejecución.

**Chat Trigger (chat público).** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.chattrigger
- Make Chat Publicly Available (`public`): apagado mientras se arma, prendido para publicar.
- Mode: Hosted Chat (la página de chat de n8n, en el JSON `hostedChat`) o Embedded Chat (tu propia interfaz o el widget `@n8n/chat`, en el JSON `webhook`).
- Authentication: None, Basic Auth o n8n User Auth. Initial Message(s) para Hosted Chat.
- Opciones: título, subtítulo, texto del campo, CSS, Allowed Origin (CORS), Load Previous Session (necesita memoria), Response Mode (When Last Node Finishes, Using Response Nodes o Streaming) y Require Button Click to Start Chat.
- Tiene que ir conectado a un agente o a una cadena.
- "Every message to the Chat Trigger executes your workflow." Diez mensajes son diez ejecuciones.

**AI Agent.** https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent y https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/tools-agent
- Un modelo de chat conectado y, según la documentación, "You must connect at least one tool".
- Source for Prompt (User Message): tomarlo del nodo anterior (en el JSON `promptType: "auto"`, usa `chatInput`, lo que manda el Chat Trigger) o Define below (`"define"`, con el texto o una expresión en Prompt (User Message)).
- Opciones: System Message (por defecto "You are a helpful assistant"), Max Iterations (10), Return Intermediate Steps, Enable Streaming (prendido), Automatically Passthrough Binary Images. Require Specific Output Format pide un output parser.
- Desde n8n 1.82.0 todo AI Agent funciona como Tools Agent. La versión 1 del nodo se elimina en n8n 3.0.
- Para que el modelo llene parámetros de una herramienta se usa `$fromAI()`. https://docs.n8n.io/build/integrate-ai/ai-examples/use-ai-for-parameters.md

**OpenAI Chat Model.** https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai
- Credencial OpenAI (`openAiApi`): API Key, Organization ID (opcional) y **Base URL**, que por defecto es `https://api.openai.com/v1` (campo `url` en la descripción de la credencial). https://docs.n8n.io/integrations/builtin/credentials/openai
- Model: de la lista o por ID. En la versión 1.3 el valor por defecto es `gpt-5-mini`.
- Use Responses API: la documentación dice que por defecto usa Chat Completions, pero en la versión 1.3 el interruptor `responsesApiEnabled` viene en `true` según la descripción del nodo de n8n 2.47.7. Las herramientas propias de OpenAI (Web Search, File Search, Code Interpreter) solo andan con Responses y con el AI Agent.
- En Cloud acepta Use Gateway credits.

**Google Gemini Chat Model.** Credencial Google Gemini(PaLM) Api (`googlePalmApi`): Host (`https://generativelanguage.googleapis.com`) y API Key, que se crea en https://aistudio.google.com/apikey. No acepta otros hosts. Model se carga de la API (en la versión 1.2 el valor por defecto es `models/gemini-3-flash-preview`). En Cloud acepta Use Gateway credits. https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatgooglegemini y https://docs.n8n.io/integrations/builtin/credentials/googleai

**OpenRouter Chat Model.** Credencial OpenRouter (`openRouterApi`): API Key y Base URL (`https://openrouter.ai/api/v1`). La llave se crea en https://openrouter.ai/keys. Model se carga de OpenRouter (por defecto `openai/gpt-4.1-mini`). Opción Response Format: Text o JSON. https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenrouter y https://docs.n8n.io/integrations/builtin/credentials/openrouter

**Cualquier servicio compatible con la API de OpenAI.** No hay un nodo aparte: se usa OpenAI Chat Model con una credencial OpenAI a la que se le cambia el Base URL por la del servicio. Con una dirección distinta de la de OpenAI, el nodo pide la lista de modelos a `<Base URL>/models` y no la filtra, así que aparecen todos los del servicio (descripción del nodo 1.3 en n8n 2.47.7). Conviene apagar Use Responses API, porque Chat Completions es el endpoint que implementan los servicios compatibles. Esta noche probamos uno con dirección base propia y respondió a `/models`, `/chat/completions` y también a `/responses`.

**Simple Memory.** Session ID: Connected Chat Trigger Node (toma `sessionId` del Chat Trigger, en el JSON `sessionIdType: "fromInput"`) o Define below (`"customKey"`, con una clave propia). Context Window Length: cuántos intercambios recuerda (5 por defecto). No sirve en queue mode. https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorybufferwindow

**Herramientas del agente.** El Tools Agent puede usar, entre otras, Call n8n Workflow, Code, HTTP Request, Calculator, Wikipedia, Think Tool, MCP Client Tool y casi cualquier nodo de app como herramienta. https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/tools-agent
- Calculator y Wikipedia no piden credencial. https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolcalculator y https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolwikipedia
- Un nodo común usado como herramienta suma el campo Description (Tool Description, automática o manual) para que el modelo sepa cuándo usarlo. https://github.com/n8n-io/n8n/blob/n8n%402.47.7/packages/cli/src/tool-generation/ai-tools.ts

**HTTP Request.** Method, URL, Authentication (recomiendan Predefined Credential Type, que también sirve con credenciales de nodos comunitarios, o Generic Credential Type), Send Query Parameters, Send Headers y Send Body (Form URLencoded, Form-Data, JSON, n8n Binary File o Raw). Opciones: Pagination, Batching, Timeout, Response, Redirects. Como herramienta suma Optimize Response. Se puede armar pegando un comando cURL. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest

**Code.** JavaScript o Python. Modos: Run Once for All Items (por defecto) o Run Once for Each Item. En Cloud no se pueden importar módulos npm, salvo `crypto` y `moment`. Python nativo (estable desde n8n 2): en Cloud no permite importar ninguna librería, ni siquiera de la biblioteca estándar, y solo trae `_items` y `_item`. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code

**Edit Fields (Set).** Mode: Manual Mapping (arrastrar valores) o JSON Output. Include in Output y Keep Only Set Fields para decidir qué sigue. Support Dot Notation. https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set

**Guardar una lista dentro de n8n: Data tables.** Existen y no piden ningún servicio de afuera. https://docs.n8n.io/build/work-with-data/data-tables y https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.datatable
- Se crean en la pestaña Data tables del proyecto (desde cero o importando un CSV) y se bajan como CSV.
- Nodo Data table. Filas: Insert, Get, Update, Upsert, Delete, If Row Exists, If Row Does Not Exist. Tablas: Create, Delete, List, Update. También funciona como herramienta del agente.
- Límite: 200 MiB entre todas las tablas de la instancia. Un nodo Code no puede leerlas directo.
- En Cloud: la página de precios las marca incluidas en Starter, Pro y Enterprise. La sección de la prueba no las nombra, pero la prueba trae las funciones del Pro. https://n8n.io/pricing/

## 3. SerpApi

### Qué es

"Scrape Google and other search engines from our fast, easy, and complete API." Es una API que hace la búsqueda en Google (y en otros buscadores) y devuelve los resultados ordenados en JSON. https://serpapi.com/

- Se escribe **SerpApi**: "one word, with the "S" and "A" as the only capitalized letters". https://serpapi.com/media
- **Plan gratis hoy:** 250 búsquedas por mes y 50 por hora. Solo cuentan las búsquedas exitosas. https://serpapi.com/pricing
- Una búsqueda repetida (misma consulta y mismos parámetros) dentro de la hora sale de la caché y no se cobra: "Cache expires after 1h. Cached searches are free". https://github.com/serpapi/n8n-nodes-serpapi/blob/master/nodes/SerpApi/descriptions/SerpApiDescription.ts
- La cuenta de la charla es Free Plan con 250 por mes (lo confirma el endpoint de cuenta de SerpApi, que no gasta búsquedas).
- Registro: https://serpapi.com/users/sign_up. La llave está en https://serpapi.com/manage-api-key.

### SerpApi en n8n

- **El nodo de n8n quedó obsoleto.** "The SerpApi (Google Search) node is deprecated from n8n 2.35.0. Use the verified SerpApi Official community node instead." https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolserpapi
- **El que va: SerpApi Official.** Nodo comunitario verificado por n8n, hecho y mantenido por SerpApi. https://n8n.io/integrations/serpapi/
  - Paquete npm `n8n-nodes-serpapi`, versión 0.1.10 (26 de marzo de 2026), licencia MIT. https://www.npmjs.com/package/n8n-nodes-serpapi
  - **En n8n Cloud:** se busca "serpapi" en el panel de nodos y se instala desde la sección More from the community. Lo instala el dueño o un admin de la instancia, y después lo usan todos. https://docs.n8n.io/integrations/community-nodes/installation-and-management/install-verified-community-nodes
  - **Operaciones (37 motores):** Amazon Search, Baidu Search, Bing Images, Bing Search, DuckDuckGo Search, eBay Search, Facebook Profile, Google AI Mode, Google AI Overview, Google Autocomplete, Google Finance, Google Flights, Google Hotels, Google Images, Google Images Light, Google Immersive Product, Google Jobs, Google Lens, Google Light, Google Local, Google Maps, Google Maps Directions, Google Maps Reviews, Google News, Google News Light, Google Play Games, Google Play Product, Google Play Store, Google Product, Google Scholar, Google Search, Google Shopping, Google Travel Explore, Google Trends, Google Trends Trending Now, Google Videos y YouTube Search. https://n8n.io/integrations/serpapi/ y https://github.com/serpapi/n8n-nodes-serpapi
  - Opciones comunes: Disable Caching (`no_cache`), Async, Output (`json`, `html` o `md`, este último "optimized for LLMs and AI agents") y JSON Restrictor (`json_restrictor`, por ejemplo `organic_results[0:3].{title,snippet}` para traer solo los tres primeros con título y resumen). https://github.com/serpapi/n8n-nodes-serpapi/blob/master/nodes/SerpApi/descriptions/SerpApiDescription.ts
- **Como herramienta del AI Agent:** **SerpApi Official Tool** (tipo `n8n-nodes-serpapi.serpApiTool`). Al conectar una herramienta aparecen dos nodos de SerpApi: el viejo, SerpApi (Google Search), y el nuevo. SerpApi pide elegir el Official Tool. https://serpapi.com/blog/boost-your-n8n-workflows-with-serpapis-verified-node/
- **Credencial:** SerpApi API (tipo `serpApi`), con un solo campo, API Key. La manda como parámetro `api_key` y la prueba contra `https://serpapi.com/account`. https://github.com/serpapi/n8n-nodes-serpapi/blob/master/credentials/SerpApi.credentials.ts
- **Sin el nodo, con HTTP Request:** GET a `https://serpapi.com/search.json` con los parámetros `engine`, `q` (o el que pida el motor), `gl`, `hl` y `api_key`. En Authentication se puede elegir Predefined Credential Type y la misma credencial de SerpApi. https://serpapi.com/blog/boost-your-n8n-workflows-with-serpapis-verified-node/ y https://serpapi.com/search-api

### Los motores más vistosos

Las respuestas de ejemplo de abajo son reales, de esta noche, con Bolivia y español. Están completas en `workflows/muestras/` (sin la llave). Para Google se resume el ejemplo de su documentación.

| Motor | `engine` | Qué pide | Bolivia y español | Muestra |
| --- | --- | --- | --- | --- |
| Google | `google` | `q` | `gl` y `hl` aceptados (Bolivia está en la lista de países) | documentación |
| Google News | `google_news` | `q` opcional | `gl=bo`, `hl=es`: anduvo | `serpapi-google_news-bo.json` |
| Google Maps | `google_maps` | `type=search`, `q`, `ll` o `location` | `hl=es` anduvo. `gl` solo afecta la ficha de un lugar | `serpapi-google_maps-bo.json` |
| Google Scholar | `google_scholar` | `q` | `hl` y `lr` (no tiene `gl`) | sin muestra |
| Google Jobs | `google_jobs` | `q` | `gl=bo`, `hl=es`: anduvo. Bolivia está en la lista de Google Jobs | `serpapi-google_jobs-bo.json` |
| Google Trends | `google_trends` | `q`, `data_type` | usa `geo` (no `gl`): `geo=BO`, `hl=es` anduvo | `serpapi-google_trends-bo.json` |
| Google Flights | `google_flights` | `departure_id`, `arrival_id`, `outbound_date`, `type` | `gl=bo`, `hl=es` anduvo. `currency=BOB` NO: da error 400, usar `USD` | `serpapi-google_flights-bo.json` |
| Google Lens | `google_lens` | `url` de una imagen | usa `hl` y `country` (no `gl`) | sin muestra |
| YouTube | `youtube` | `search_query` (no `q`) | `gl=bo`, `hl=es`: anduvo | `serpapi-youtube-bo.json` |

Documentación de cada motor: https://serpapi.com/search-api, https://serpapi.com/google-news-api, https://serpapi.com/google-maps-api, https://serpapi.com/google-scholar-api, https://serpapi.com/google-jobs-api, https://serpapi.com/google-trends-api, https://serpapi.com/google-flights-api, https://serpapi.com/google-lens-api, https://serpapi.com/youtube-search-api. Países: https://serpapi.com/google-countries (fila "bo Bolivia"). Países de Google Jobs: https://serpapi.com/google-jobs-countries.

Qué devolvió cada una (resumen):

- **Google** (ejemplo de la documentación, búsqueda "Coffee"): `organic_results` con `position`, `title`, `link`, `snippet`, `source` y `sitelinks`, más `knowledge_graph`, `local_results`, `related_questions`, `related_searches` y `pagination`.
- **Google News**, `q=Santa Cruz de la Sierra`: 100 elementos en `news_results`. Los primeros son bloques (Noticias principales, Publicaciones en X) y después notas sueltas, cada una con `title`, `source.name`, `link`, `date` e `iso_date`. Ejemplo: "Alcaldía identifica más de 3.000 puestos abandonados en 26 mercados municipales de Santa Cruz", de EL DÍA.
- **Google Jobs**, `q=programador Santa Cruz Bolivia`: 9 en `jobs_results`, cada uno con `title`, `company_name`, `location`, `via` y `extensions`. Ejemplo: "Programador/a Junior", Santa Cruz de la Sierra, vía LinkedIn Bolivia, "hace 1 día", "Tiempo completo". Las páginas siguientes se piden con `next_page_token`.
- **Google Maps**, `q=café` y `ll=@-17.7833,-63.1821,14z`: 20 en `local_results`, cada uno con `title`, `rating`, `reviews`, `address`, `type` y `gps_coordinates`. Ejemplo: "Sitcom Café", 4,7 estrellas, 122 reseñas, Cafetería, Santa Cruz de la Sierra.
- **Google Trends**, `q=inteligencia artificial`, `geo=BO`, `date=today 12-m`: `interest_over_time.timeline_data` con 53 semanas, cada una con `date` y `values[].extracted_value` (0 a 100). La primera semana (del 9 al 15 de noviembre de 2025) marca 96 y la última (del 8 al 14 de noviembre de 2026) marca 74, como dato parcial.
- **Google Flights**, Viru Viru (`VVI`) a El Alto (`LPB`), solo ida el 15 de diciembre de 2026: 3 en `best_flights` y 5 en `other_flights`, cada uno con los tramos (aerolínea, número de vuelo, aeropuertos y horas), `total_duration` y `price`. Más `price_insights` con el precio más bajo, si está caro o normal y la historia de precios. Ejemplo: BoA OB 661, sale 05:35, 65 minutos, 75 USD.
- **YouTube**, `search_query=n8n tutorial español`: 14 en `video_results` (más anuncios y listas), cada uno con `title`, `channel.name`, `views`, `length` y `published_date`. Ejemplo: "Curso de N8N desde CERO (completo)", 318.039 vistas, 1:48:16.

Búsquedas gastadas por esta investigación: 6 de las 40 de la noche.

## 4. Exportar e importar workflows

https://docs.n8n.io/build/manage-workflows/export-and-import

- n8n guarda los workflows como JSON.
- **Exportar:** menú del editor, **Download**. O copiar los nodos (Ctrl + C) y pegarlos donde haga falta.
- **Importar:** menú del editor, **Import from File**, o pegar el JSON en el lienzo (Ctrl + V). Existe Import from URL, pero desaparece en n8n 3.0.
- **Credenciales:** el JSON exportado lleva el nombre y el ID de cada credencial que usa un nodo, nunca la llave. "While IDs aren't sensitive, the names could be". Un HTTP Request armado desde cURL puede traer encabezados de autenticación. Antes de publicar un JSON hay que limpiar eso. Para el repositorio: sacar el bloque `credentials` de cada nodo y que cada persona elija su credencial después de importar.
- Por línea de comandos (ver punto 5) y por la API pública de n8n (que la prueba de Cloud no incluye).

### La forma del JSON

Campos mínimos para importar por línea de comandos: `nodes` y `connections`. Si falta `id`, n8n genera uno. Código de n8n 2.47.7: https://github.com/n8n-io/n8n/blob/n8n%402.47.7/packages/cli/src/commands/import/workflow.ts

Cada nodo lleva `id` (un UUID), `name` (único en el workflow, las conexiones lo usan), `type`, `typeVersion`, `position` (`[x, y]`) y `parameters`. Los disparadores con dirección pública (Webhook, Form Trigger, Chat Trigger y los n8n Form) llevan además `webhookId` (un UUID). Si usa credencial, `credentials` con `{ "<tipo>": { "id": "...", "name": "..." } }`.

Las conexiones van por nombre de nodo. Las comunes son `main`. Los subnodos de IA se conectan **desde** el subnodo **hacia** el agente con los tipos `ai_languageModel`, `ai_memory`, `ai_tool` y `ai_outputParser`. Así lo muestra la plantilla oficial de agente con chat que enlaza la documentación (https://n8n.io/workflows/1954-ai-agent-chat/, JSON en https://api.n8n.io/api/templates/workflows/1954):

```json
{
  "name": "Agente con chat",
  "nodes": [
    {
      "id": "0b6f2c1e-1111-4a5b-9c3d-000000000001",
      "name": "Chat",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "typeVersion": 1.5,
      "position": [0, 0],
      "webhookId": "0b6f2c1e-1111-4a5b-9c3d-0000000000aa",
      "parameters": { "public": true, "options": {} }
    },
    {
      "id": "0b6f2c1e-1111-4a5b-9c3d-000000000002",
      "name": "Agente",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 3.1,
      "position": [260, 0],
      "parameters": { "options": { "systemMessage": "Respondé en español, corto." } }
    },
    {
      "id": "0b6f2c1e-1111-4a5b-9c3d-000000000003",
      "name": "Modelo",
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1.2,
      "position": [180, 220],
      "parameters": { "options": {} }
    },
    {
      "id": "0b6f2c1e-1111-4a5b-9c3d-000000000004",
      "name": "Memoria",
      "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
      "typeVersion": 1.4,
      "position": [320, 220],
      "parameters": {}
    },
    {
      "id": "0b6f2c1e-1111-4a5b-9c3d-000000000005",
      "name": "Calculadora",
      "type": "@n8n/n8n-nodes-langchain.toolCalculator",
      "typeVersion": 1,
      "position": [460, 220],
      "parameters": {}
    }
  ],
  "connections": {
    "Chat": { "main": [[{ "node": "Agente", "type": "main", "index": 0 }]] },
    "Modelo": { "ai_languageModel": [[{ "node": "Agente", "type": "ai_languageModel", "index": 0 }]] },
    "Memoria": { "ai_memory": [[{ "node": "Agente", "type": "ai_memory", "index": 0 }]] },
    "Calculadora": { "ai_tool": [[{ "node": "Agente", "type": "ai_tool", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

Este ejemplo muestra la forma, no está probado tal cual. Todo workflow del repositorio se importa en un n8n 2.47.7 local antes de darlo por bueno (punto 5).

Para elegir el modelo de Gemini en el JSON, `modelName` lleva el prefijo `models/` (por ejemplo `models/gemini-3-flash-preview`, el valor por defecto desde la versión 1.1). En OpenAI Chat Model, desde la 1.2, el modelo es un selector: la plantilla oficial lo escribe `"model": { "__rl": true, "mode": "list", "value": "gpt-4o-mini" }` (el otro modo es `"id"`). Para un servicio compatible conviene `"responsesApiEnabled": false`.

La plantilla oficial publica las credenciales con un ID de relleno, por ejemplo `"credentials": { "openAiApi": { "id": "credential-id", "name": "openAiApi Credential" } }`. https://api.n8n.io/api/templates/workflows/1954

## 5. n8n en la compu, para probar

**Instalar y abrir.** https://docs.n8n.io/deploy/host-n8n/install-options/install-with-npm
- `npx n8n` abre n8n en http://localhost:5678 sin instalarlo. Con versión fija: `npx n8n@2.47.7`.
- La instalación con npm está obsoleta desde n8n 3.0 y en n8n 3 ya no funciona. Para 2.47.7 sí.
- **Versión de Node:** la documentación dice "between 20.19 and 24.x, inclusive". El paquete `n8n@2.47.7` pide `node >= 24.0.0` (campo `engines` en https://registry.npmjs.org/n8n/2.47.7). Usar Node 24. La compu de la charla tiene Node 24.21.0.
- El Assistant de n8n no está en la instalación con npm.
- Para no mezclar datos, `N8N_USER_FOLDER` define dónde crea n8n su carpeta `.n8n` (base de datos y llave de cifrado). Puerto: `N8N_PORT`, 5678 por defecto. https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/use-environment-variables/deployment.md

**Comandos.** https://docs.n8n.io/deploy/host-n8n/configure-n8n/use-the-command-line

| Para qué | Comando |
| --- | --- |
| Importar un workflow | `n8n import:workflow --input=archivo.json` |
| Importar una carpeta de workflows | `n8n import:workflow --separate --input=carpeta/` |
| Importar credenciales | `n8n import:credentials --input=archivo.json` |
| Ver los workflows con su ID | `n8n list:workflow` |
| Correr un workflow guardado | `n8n execute --id=<ID>` |
| Publicar (el viejo "activar") | `n8n publish:workflow --id=<ID>` |
| Despublicar | `n8n unpublish:workflow --id=<ID>` o `--all` |
| Exportar un workflow | `n8n export:workflow --id=<ID> --output=archivo.json --pretty` |
| Exportar todos, uno por archivo | `n8n export:workflow --backup --output=carpeta/` |
| Exportar credenciales | `n8n export:credentials --all --output=archivo.json` |
| Arrancar el servidor | `n8n start` (o solo `n8n`) |

Con npx, cada comando va detrás de `npx n8n@2.47.7`, por ejemplo `npx n8n@2.47.7 import:workflow --input=archivo.json`.

Detalles que importan:

- `import:workflow` deja **despublicado** todo lo que importa. Respetar el campo `active` del JSON (`--activeState=fromJson`) solo anda en queue mode o multi-main. Para publicar: `publish:workflow`, que hace las mismas comprobaciones que el botón. Con el servicio de publicación prendido (lo normal) un n8n que está corriendo toma el cambio en unos 15 segundos, sin reiniciar.
- `update:workflow --active=true` está obsoleto desde n8n 2.0.
- `list:workflow` existe en el código de n8n 2.47.7 (https://github.com/n8n-io/n8n/tree/n8n%402.47.7/packages/cli/src/commands/list) aunque la página de la línea de comandos no lo nombra.
- `import:credentials` acepta la credencial con los datos en texto plano (un objeto en `data`) y los cifra al importar (https://github.com/n8n-io/n8n/blob/n8n%402.47.7/packages/cli/src/commands/import/credentials.ts). Ese archivo lleva la llave a la vista: va fuera del repositorio y se borra después.
- `export:credentials --decrypted` deja todas las llaves a la vista. No usarlo en el repositorio.
- n8n recomienda para mover workflows entre instancias la nueva n8n CLI con paquetes `.n8np` (en Preview) y planea dejar obsoletos los comandos de exportar e importar del servidor, sin fecha.
- Un formulario o un chat de un n8n local no se ve desde internet sin un túnel. Para la charla, lo público va en Cloud.
- En el n8n local, SerpApi Official se instala desde Settings, Community Nodes, Install, escribiendo el nombre de paquete `n8n-nodes-serpapi` y aceptando el aviso de riesgos. Lo hace el dueño o un admin. https://docs.n8n.io/integrations/community-nodes/installation-and-management/gui-installation.md

## 6. Modelos que el público puede usar gratis hoy

| Opción | Cómo se saca | Límites | Nodo de n8n |
| --- | --- | --- | --- |
| Gateway credits de la prueba de n8n Cloud | Nada que sacar: al crear la cuenta de prueba ya vienen. En el nodo, Use Gateway credits | 100 AI credits según la página de precios. Cuánto rinden depende del modelo. Sin recarga durante la prueba | OpenAI Chat Model o Google Gemini Chat Model |
| Capa gratis de Google Gemini | Llave en https://aistudio.google.com/apikey (Create API Key) | Por proyecto, no por llave, y se reinician a medianoche hora del Pacífico. Los números de cada modelo se ven en AI Studio. En la capa gratis, lo que se manda se usa para mejorar los productos de Google | Google Gemini Chat Model |
| Modelos gratis de OpenRouter (ID terminado en `:free`) | Llave en https://openrouter.ai/keys | 20 pedidos por minuto. 50 por día si la cuenta compró menos de 10 créditos, 1.000 por día con 10 o más. Con saldo negativo fallan también los gratis | OpenRouter Chat Model |
| Groq | Llave en su consola, https://console.groq.com | No pude confirmar los del plan gratis (ver al final) | Groq Chat Model |

Fuentes: https://n8n.io/pricing/, https://docs.n8n.io/deploy/use-n8n-cloud/gateway-credits, https://aistudio.google.com/docs/pricing, https://aistudio.google.com/docs/rate-limits, https://aistudio.google.com/docs/available-regions (Bolivia figura), https://openrouter.ai/docs/api-reference/limits, https://openrouter.ai/api/v1/models, https://console.groq.com/docs/rate-limits.

Detalle de cada uno:

- **Gemini, modelos con capa gratis** según la página de precios, entre otros: `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` y `gemini-3-flash-preview`. Sin capa gratis: Gemini 4 Carbon, Gemini 4 Argon y Gemini 3.1 Pro Preview. Gemini 2.5 Pro y 2.5 Flash todavía tienen capa gratis, pero están obsoletos y desde el 1 de diciembre de 2026 sus pedidos pasan a otros modelos. https://aistudio.google.com/docs/pricing
- **OpenRouter, modelos gratis hoy:** 14 con `:free`, de 471. Los 14 dicen aceptar herramientas, por ejemplo `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-3.5-lightning:free` y `baidu/ernie-5.5-flash-preview:free`. La lista cambia seguido. https://openrouter.ai/api/v1/models
- **Groq:** la tabla de su página dice que son "the base limits for the Developer plan". Modelos de texto que figuran: `openai/gpt-oss-120b`, `openai/gpt-oss-20b` y `qwen/qwen3.8-27b`. https://console.groq.com/docs/rate-limits

**Recomendación para el público: los Gateway credits de la prueba de n8n Cloud.** Es lo único que no pide crear otra cuenta ni copiar una llave: el que se registra en la prueba (que igual necesita para seguir la charla) elige Use Gateway credits en el nodo del modelo y ya anda. Copiar llaves es donde más se traba la gente en una sala. Plan B, la llave gratis de Google AI Studio: Bolivia está entre las regiones habilitadas y es una sola llave que se pega en la credencial del nodo de Gemini. Decirle al público que en la capa gratis de Gemini lo que se manda se usa para mejorar los productos de Google, así que nada de datos personales. OpenRouter gratis queda corto para un agente con herramientas: 50 pedidos por día y cada respuesta del agente puede usar varios.

## 7. Datos ciertos para la charla

1. **n8n tiene más de 210 mil estrellas en GitHub.** 210.423 al consultar la API de GitHub esta noche (https://api.github.com/repos/n8n-io/n8n). La portada dice "Top 50 Github project with 210.3k stars" (https://n8n.io/). En el lanzamiento de n8n 2.0 eran "about 160,000" (https://blog.n8n.io/introducing-n8n-v3).
2. **Más de 500 integraciones nativas**, según la portada: "500+ native integrations" (https://n8n.io/). Ojo: la página de integraciones dice "2,000+ integrations" contando también las de la comunidad (https://n8n.io/integrations/) y el repositorio dice "400+". Para la diapositiva, la de la portada.
3. **n8n estrenó marca nueva el 14 de octubre de 2026 en In The Loop**, su conferencia. El símbolo nuevo muestra la actividad que generan las conexiones, no solo los nodos, por el giro hacia la IA con agentes. Se quedaron con el rosa. https://blog.n8n.io/n8n-brand-refresh-2026/
4. **Empresas que lo usan, según n8n:** Vodafone ("£2.2M saved on threat intelligence"), Icatu Seguros ("200 hours saved every month"), Seguros Bolívar, Trendyol ("700 active workflows in under a year"), Stepstone y Huel. https://n8n.io/case-studies/
5. **La comunidad de n8n:** el foro pasó "from 115,192 to over 183,000" miembros entre n8n 2.0 y 3.0 (https://blog.n8n.io/introducing-n8n-v3). La portada habla de "250k+ developers in our community" (https://n8n.io/).
6. **SerpApi, empresas que lo usan según SerpApi:** Nvidia, Shopify, Perplexity, Adobe, Samsung, KPMG, Salesforce, Morgan Stanley y Naciones Unidas, entre otras. https://serpapi.com/
7. **SerpApi cubre mucho más que Google.** El menú de su documentación tiene 160 páginas de API (conteo propio de esta noche, incluye utilidades como la de cuenta), con Bing, YouTube, Amazon, Walmart, Yahoo, Yandex, Baidu, DuckDuckGo y Tripadvisor, entre otros. El nodo de n8n trae 37 de esos motores. https://serpapi.com/search-api y https://n8n.io/integrations/serpapi/

## 8. Logos

Bajados de sus fuentes oficiales a `diseno/logos/n8n/` y `diseno/logos/serpapi/`. De dónde salió cada uno y qué dicen sus reglas: `diseno/logos/FUENTES.md`.

## 9. El evento y lo que salió de las pruebas

- **Fechas del hackathon en Santa Cruz:** "14 y 15 de noviembre de 2026". El envío de proyectos "abre el sábado 14 de noviembre a las 9:00 AM y cierra el domingo 15 de noviembre a las 11:59 PM (hora local)". Sitio de NASA Space Apps Santa Cruz, https://spaceappssantacruz.web.app/ (consultado el 14 de noviembre de 2026, de madrugada). A las 16:00 del sábado faltan unas 32 horas para ese cierre. Ninguna fuente dice que el hackathon dure 48 horas: 48 horas son los dos días del fin de semana.
- **Google News da la fecha como mes/día/año.** En `workflows/muestras/serpapi-google_news-companero-2.json` del primer ensayo, una nota de LaSexta con fecha `11/04/2026` tiene `20261104` en su dirección: es del 4 de noviembre. Con la búsqueda NASA hoy, Google News devolvió notas viejas con hoy en el título (de febrero, marzo y principios de noviembre) y el agente las contó como de ese día. Por eso el flujo 2 pide la fecha de cada noticia (`workflows/ESPEC.md`, punto 10).
- **Comprobado después en n8n 2.47.7** (`workflows/ESPEC.md`, punto 8): un JSON con `fieldName` y `options.path` importa tal cual. Sin SerpApi Official instalado, importar funciona pero publicar falla con `Unrecognized node type: n8n-nodes-serpapi.serpApi`. Los JSON sin bloque `credentials`, importados en un n8n vacío, solo piden elegir las credenciales.

## LO QUE NO PUDE COMPROBAR

- **Publicar un formulario o un chat público desde una cuenta de prueba de verdad.** La documentación no lo limita, pero no creé una cuenta de prueba. Hay que probarlo en la cuenta de la charla antes de las 16:00.
- **Cuánto rinden los 100 AI credits** de la prueba. La tabla de precios por servicio (https://app.n8n.cloud/service-pricing) pide cuenta. Tampoco está escrito si los "100 AI credits" de la página de precios son exactamente los Gateway credits (la documentación solo dice "a small amount of free credit").
- **Qué versión corre hoy una cuenta nueva de Cloud.** Si fuera más vieja que 2.47, alguna `typeVersion` de la tabla podría no existir ahí. Se ve en la cuenta (menú de ayuda, About n8n) y se cambia en el Cloud console.
- **Si Use Gateway credits aparece en Google Gemini Chat Model y en OpenAI Chat Model cuando están conectados a un AI Agent.** La documentación lo dice de cada nodo, sin hablar del agente.
- **Use Responses API por defecto en OpenAI Chat Model 1.3.** La documentación dice que el nodo usa Chat Completions por defecto, la descripción del nodo en el código dice `true`. Lo que se vea en el editor manda.
- **Qué pasa en Cloud al importar un workflow con SerpApi Official sin tener el nodo instalado.** En un n8n local, publicar falla (punto 9). En Cloud no se probó. Instalar el nodo antes de importar.
- **Qué pasa con las credenciales al importar en otra instancia** cuando el JSON trae un ID de credencial que ahí no existe. No está en la documentación que leí. Por eso los JSON se publican sin el bloque `credentials`.
- **Las tres demos en n8n Cloud con Use Gateway credits.** Todas las pruebas se hicieron en un n8n local con `openai/gpt-5-mini` por OpenRouter. Falta correrlas en Cloud y anotar el saldo de créditos antes y después.
- **Límites del plan gratis de Groq.** Su tabla dice que son del plan Developer.
- **Límites por modelo de la capa gratis de Gemini.** Google los muestra solo en AI Studio, con la cuenta.
- **Si la capa gratis de Gemini pide tarjeta.** La página no lo dice. Sí dice que para Bolivia la API está habilitada.
- **El número exacto de motores de SerpApi.** SerpApi no publica un total. El 160 es un conteo nuestro de los enlaces de su documentación.
- **Google Scholar y Google Lens con Bolivia.** No gastamos búsquedas en ellos. Según su documentación, Scholar no tiene `gl` y Lens usa `country`.
