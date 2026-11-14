// Prueba la presentación HTML en Chrome sin cabeza y saca capturas.
//
// Abre un Chrome propio (--headless=new, perfil temporal nuevo, sin extensiones,
// mudo) y lo maneja por el protocolo de DevTools con el WebSocket que trae Node,
// sin dependencias. Hace lo que haría el orador con el clicker y el teclado:
// espera que el primer video termine, avanza (flecha, Av Pág, espacio, clic),
// abre la vista del orador (S) y la captura, prueba la pantalla negra (B), salta
// con número + Enter, vuelve (flecha izquierda) y dos avances rápidos. En cada
// cambio de paso anota si el video nuevo ya tenía su primer cuadro listo
// (readyState >= 2: sin parpadeo) y junta los errores de la consola.
// Al final cierra SU Chrome (Browser.close y, si no alcanza, solo su PID).
//
// Uso:  node armar/probar_html.mjs <presentacion.html> <carpeta_capturas> [--chrome <chrome.exe>]
// Deja <carpeta>/NN_*.png y <carpeta>/informe.json.

import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const html = path.resolve(args[0] ?? "");
const carpeta = path.resolve(args[1] ?? "capturas_html");
const iChrome = args.indexOf("--chrome");
const CHROME = iChrome >= 0 ? args[iChrome + 1] : "C:/Program Files/Google/Chrome/Application/chrome.exe";
if (!fs.existsSync(html)) { console.error(`no existe ${html}`); process.exit(2); }
fs.mkdirSync(carpeta, { recursive: true });
const perfil = fs.mkdtempSync(path.join(carpeta, "perfil-chrome-"));
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", `--user-data-dir=${perfil}`, "--remote-debugging-port=0", "--no-first-run",
  "--no-default-browser-check", "--disable-extensions", "--mute-audio", "--window-size=1920,1080", "about:blank",
], { stdio: "ignore" });
const informe = { html, chrome_pid: chrome.pid, pasos: [], errores_consola: [], capturas: [], controles: [] };

async function puerto() {
  const f = path.join(perfil, "DevToolsActivePort");
  for (let i = 0; i < 100; i++) {
    if (fs.existsSync(f)) {
      const [p, ruta] = fs.readFileSync(f, "utf8").split("\n");
      if (p) return { p: Number(p), ruta: ruta.trim() };
    }
    await dormir(100);
  }
  throw new Error("Chrome no abrió el puerto de DevTools");
}

let ws, id = 0;
const pendientes = new Map();
const oyentes = [];
function enviar(method, params = {}, sessionId) {
  const msg = { id: ++id, method, params };
  if (sessionId) msg.sessionId = sessionId;
  ws.send(JSON.stringify(msg));
  return new Promise((ok, mal) => pendientes.set(msg.id, { ok, mal, method }));
}
function esperarEvento(pred, ms = 10000) {
  return new Promise((ok, mal) => {
    const o = { pred, ok };
    oyentes.push(o);
    setTimeout(() => { const k = oyentes.indexOf(o); if (k >= 0) { oyentes.splice(k, 1); mal(new Error("tiempo agotado esperando un evento")); } }, ms);
  });
}

async function evaluar(sesion, expr) {
  const r = await enviar("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }, sesion);
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
  return r.result.value;
}
async function hasta(sesion, expr, ms = 15000, cada = 100) {
  const t = Date.now();
  while (Date.now() - t < ms) {
    try { if (await evaluar(sesion, expr)) return true; } catch { /* la página puede estar cargando */ }
    await dormir(cada);
  }
  throw new Error(`no se cumplió: ${expr}`);
}
async function captura(sesion, nombre) {
  const r = await enviar("Page.captureScreenshot", { format: "png" }, sesion);
  const f = path.join(carpeta, nombre);
  fs.writeFileSync(f, Buffer.from(r.data, "base64"));
  informe.capturas.push(f);
  return f;
}
const TECLAS = {
  ArrowRight: { code: "ArrowRight", vk: 39 }, ArrowLeft: { code: "ArrowLeft", vk: 37 }, PageDown: { code: "PageDown", vk: 34 },
  PageUp: { code: "PageUp", vk: 33 }, Enter: { code: "Enter", vk: 13, text: "\r" }, " ": { code: "Space", vk: 32, text: " " },
};
async function tecla(sesion, key) {
  const t = TECLAS[key] ?? { code: /^[0-9]$/.test(key) ? `Digit${key}` : `Key${key.toUpperCase()}`, vk: key.toUpperCase().charCodeAt(0), text: key };
  await enviar("Input.dispatchKeyEvent", { type: "keyDown", key, code: t.code, windowsVirtualKeyCode: t.vk, nativeVirtualKeyCode: t.vk, text: t.text }, sesion);
  await enviar("Input.dispatchKeyEvent", { type: "keyUp", key, code: t.code, windowsVirtualKeyCode: t.vk, nativeVirtualKeyCode: t.vk }, sesion);
}
async function clic(sesion, x = 960, y = 540) {
  for (const type of ["mousePressed", "mouseReleased"]) {
    await enviar("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1 }, sesion);
  }
}
const estado = (s) => evaluar(s, "window.__pitch && window.__pitch.estado()");
function controlar(nombre, ok, detalle = "") {
  informe.controles.push({ nombre, ok, detalle });
  console.log(`${ok ? "OK   " : "FALLA"} ${nombre}${detalle ? " — " + detalle : ""}`);
}
async function terminado(s, n, ms = 20000) {
  await hasta(s, `(() => { const e = window.__pitch.estado(); const v = e.videos.find(x => x.visible); return e.actual === ${n - 1} && v && v.paso === ${n} && v.terminado; })()`, ms);
}

async function main() {
  const { p } = await puerto();
  const version = await (await fetch(`http://127.0.0.1:${p}/json/version`)).json();
  informe.version_chrome = version.Browser;
  ws = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((ok, mal) => { ws.onopen = ok; ws.onerror = mal; });
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pendientes.has(d.id)) {
      const { ok, mal, method } = pendientes.get(d.id);
      pendientes.delete(d.id);
      d.error ? mal(new Error(`${method}: ${d.error.message}`)) : ok(d.result);
      return;
    }
    if (d.method === "Runtime.exceptionThrown") informe.errores_consola.push(d.params.exceptionDetails?.exception?.description ?? d.params.exceptionDetails?.text);
    if (d.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(d.params.type)) informe.errores_consola.push(d.params.args.map((a) => a.value ?? a.description).join(" "));
    for (const o of [...oyentes]) if (o.pred(d)) { oyentes.splice(oyentes.indexOf(o), 1); o.ok(d); }
  };
  await enviar("Target.setDiscoverTargets", { discover: true });
  const { targetInfos } = await enviar("Target.getTargets");
  const pagina = targetInfos.find((t) => t.type === "page");
  const { sessionId: s } = await enviar("Target.attachToTarget", { targetId: pagina.targetId, flatten: true });
  await enviar("Page.enable", {}, s);
  await enviar("Runtime.enable", {}, s);
  await enviar("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false }, s);
  const t0 = Date.now();
  await enviar("Page.navigate", { url: pathToFileURL(html).href }, s);
  await hasta(s, "!!window.__pitch", 60000);
  informe.carga_ms = Date.now() - t0;
  const total = (await estado(s)).total;

  // 1. arranca solo y queda en el último cuadro
  await terminado(s, 1, 30000);
  await captura(s, "01_paso1_final.png");
  controlar("el paso 1 arranca solo y queda quieto al final", true, `carga ${informe.carga_ms} ms`);
  await hasta(s, "window.__pitch.estado().videos.some(v => v.paso === 2 && v.readyState >= 2)", 10000);
  controlar("el paso 2 está precargado antes del clic", true);

  // 2. avanzar con el clicker: flecha, Av Pág, espacio y clic
  const avances = ["ArrowRight", "PageDown", " ", "clic"];
  for (let k = 0; k < avances.length; k++) {
    const n = k + 2;
    if (avances[k] === "clic") await clic(s); else await tecla(s, avances[k]);
    await dormir(120);
    if (k === 0) await captura(s, "02_paso2_recien_empezado.png");
    await terminado(s, n);
    await captura(s, `03_paso${n}_final.png`);
  }
  // 3. vista del orador
  const nuevo = esperarEvento((d) => d.method === "Target.targetCreated" && d.params.targetInfo.type === "page", 8000);
  await tecla(s, "s");
  const ev = await nuevo;
  const { sessionId: so } = await enviar("Target.attachToTarget", { targetId: ev.params.targetInfo.targetId, flatten: true });
  await enviar("Runtime.enable", {}, so);
  await enviar("Emulation.setDeviceMetricsOverride", { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false }, so);
  await hasta(so, "!!document.getElementById('numero') && document.getElementById('numero').textContent.includes('/')", 8000);
  await dormir(400);
  await captura(so, "04_orador.png");
  const numero = await evaluar(so, "document.getElementById('numero').textContent");
  controlar("S abre la vista del orador con el número de paso", numero.startsWith("5 /"), numero);
  // el clicker manda las teclas a la ventana que tiene el foco: avanzar desde la del orador
  await tecla(so, "PageDown");
  await terminado(s, 6, 20000);
  await dormir(300);
  const numero2 = await evaluar(so, "document.getElementById('numero').textContent");
  const sig = await evaluar(so, "document.getElementById('sig-texto').textContent");
  await captura(so, "05_orador_sincronizado.png");
  controlar("la vista del orador sigue a la presentación (y la maneja)", numero2.startsWith("6 /"), `${numero2}; siguiente: ${sig}`);
  // 4. pantalla negra
  await tecla(s, "b");
  await dormir(200);
  await captura(s, "06_negro.png");
  const negro = (await estado(s)).negro;
  await tecla(s, "ArrowRight");   // con la pantalla negra, la primera tecla solo vuelve
  await dormir(200);
  const tras = await estado(s);
  controlar("B pone la pantalla negra y la siguiente tecla solo la saca", negro && !tras.negro && tras.actual === 5);
  // 5. salto con número + Enter (como en PowerPoint)
  const destino = Math.min(total, 8);
  for (const c of String(destino)) await tecla(s, c);
  await tecla(s, "Enter");
  await terminado(s, destino, 20000);
  await captura(s, `07_salto_a_${destino}.png`);
  controlar(`${destino} + Enter salta al paso ${destino}`, true);
  // 6. volver: el anterior arranca de cero
  await tecla(s, "ArrowLeft");
  await dormir(150);
  const e1 = await estado(s);
  const v1 = e1.videos.find((v) => v.visible);
  await terminado(s, destino - 1, 20000);
  controlar("flecha izquierda vuelve al paso anterior y su video arranca de cero", e1.actual === destino - 2 && v1.t < 1, `t=${v1.t.toFixed(2)} s`);
  // 7. dos avances rápidos: manda el último
  await tecla(s, "ArrowRight");
  await tecla(s, "ArrowRight");
  const fin = Math.min(total, destino + 1);
  await terminado(s, fin, 20000);
  await captura(s, `08_dos_avances_rapidos_paso${fin}.png`);
  controlar("dos avances rápidos llegan dos pasos más adelante", true);
  // 8. ¿algún cambio de paso mostró un video sin su primer cuadro?
  const e = await estado(s);
  informe.pasos = e.registro;
  const malos = e.registro.filter((r) => r.readyState < 2);
  controlar("todos los cambios de paso tenían el primer cuadro listo (sin parpadeo)", malos.length === 0, `${e.registro.length} cambios`);
  controlar("el sonido no quedó bloqueado", !e.sonidoBloqueado);
  controlar("sin errores en la consola", informe.errores_consola.length === 0, informe.errores_consola.slice(0, 3).join(" | "));
}

let rc = 0;
try {
  await main();
} catch (e) {
  console.error("FALLA:", e.message);
  informe.error = e.message;
  rc = 1;
} finally {
  try { await Promise.race([enviar("Browser.close"), dormir(3000)]); } catch { /* ya cerrado */ }
  const t = Date.now();
  while (chrome.exitCode === null && Date.now() - t < 5000) await dormir(100);
  if (chrome.exitCode === null) {
    try { execFileSync("taskkill", ["/PID", String(chrome.pid), "/T", "/F"], { stdio: "ignore" }); informe.cerrado_por_pid = true; } catch { /* nada */ }
  }
  informe.chrome_cerrado = chrome.exitCode !== null || informe.cerrado_por_pid === true;
  try { ws?.close(); } catch { /* nada */ }
  for (let i = 0; i < 20; i++) {
    try { fs.rmSync(perfil, { recursive: true, force: true }); break; } catch { await dormir(250); }
  }
  if (informe.controles.some((c) => !c.ok)) rc = 1;
  fs.writeFileSync(path.join(carpeta, "informe.json"), JSON.stringify(informe, null, 1));
  console.log(`capturas e informe en ${carpeta}; Chrome cerrado: ${informe.chrome_cerrado}`);
  process.exit(rc);
}
