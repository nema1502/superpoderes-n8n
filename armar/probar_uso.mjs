// Prueba de uso del HTML de la charla, como lo usaría el orador con un clicker.
//
// Chrome sin cabeza propio (perfil temporal), la página abierta como archivo local y SIN red
// (resolución de nombres anulada, proxy muerto y Network.emulateNetworkConditions offline).
// Fases: carga, recorrido entero con cada tecla del clicker, volver, diez avances rápidos,
// saltos, Inicio y Fin, pantalla negra, ayuda, silencio (M), pantalla completa, vista del orador
// (notas que entran, reloj que anda, maneja la presentación), recarga a mitad de la charla,
// cuatro tamaños de ventana y el procesador frenado 4 veces.
//
// Uso, detrás del turno de la máquina (abre un Chrome, unos 7 minutos con todas las fases):
//   node armar/probar_uso.mjs salida/Charla_n8n_SerpApi_IA.html <carpeta> [--fases carga,recorrido,...] [--chrome <exe>]
// Fases: recorrido, controles, orador, recarga, tamanos y cpu (por defecto todas) y diag (aparte: por qué
// falla la pantalla completa y qué pasa con la ventana del orador al recargar). La carga corre siempre.
// Deja <carpeta>/*.png, una captura por cada cosa que falla (FALLA_*.png) y <carpeta>/informe.json.
// Cierra solo SU Chrome (por PID si hace falta).
// Límites: Chrome sin ventana no da pantalla completa (se prueba solo que F y F5 no recarguen), y frenar
// el procesador por DevTools frena la página, no el decodificador de video.

import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const html = path.resolve(args[0] ?? "");
const carpeta = path.resolve(args[1] ?? "capturas_uso");
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const CHROME = opt("--chrome", "C:/Program Files/Google/Chrome/Application/chrome.exe");
const FASES = opt("--fases", "carga,recorrido,controles,orador,recarga,tamanos,cpu").split(",");
if (!fs.existsSync(html)) { console.error(`no existe ${html}`); process.exit(2); }
fs.mkdirSync(carpeta, { recursive: true });
const perfil = fs.mkdtempSync(path.join(carpeta, "perfil-chrome-"));
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", `--user-data-dir=${perfil}`, "--remote-debugging-port=0", "--no-first-run",
  "--no-default-browser-check", "--disable-extensions", "--mute-audio", "--window-size=1920,1080",
  "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", "--proxy-server=http://127.0.0.1:9",
  "--disable-background-networking", "--disable-component-update", "--disable-sync",
  "about:blank",
], { stdio: "ignore" });
const informe = { html, chrome_pid: chrome.pid, fases: {}, controles: [], errores_consola: [], pedidos_de_red: [], capturas: [] };

async function puerto() {
  const f = path.join(perfil, "DevToolsActivePort");
  for (let i = 0; i < 150; i++) {
    if (fs.existsSync(f)) { const [p] = fs.readFileSync(f, "utf8").split("\n"); if (p) return Number(p); }
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
async function evaluar(s, expr) {
  const r = await enviar("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }, s);
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
  return r.result.value;
}
async function hasta(s, expr, ms = 15000, cada = 80) {
  const t = Date.now();
  while (Date.now() - t < ms) {
    try { if (await evaluar(s, expr)) return Date.now() - t; } catch { /* cargando */ }
    await dormir(cada);
  }
  throw new Error(`no se cumplió en ${ms} ms: ${expr.slice(0, 160)}`);
}
async function captura(s, nombre) {
  const r = await enviar("Page.captureScreenshot", { format: "png" }, s);
  const f = path.join(carpeta, nombre);
  fs.writeFileSync(f, Buffer.from(r.data, "base64"));
  informe.capturas.push(nombre);
  return f;
}
const TECLAS = {
  ArrowRight: { code: "ArrowRight", vk: 39 }, ArrowLeft: { code: "ArrowLeft", vk: 37 }, PageDown: { code: "PageDown", vk: 34 },
  PageUp: { code: "PageUp", vk: 33 }, Enter: { code: "Enter", vk: 13, text: "\r" }, " ": { code: "Space", vk: 32, text: " " },
  Home: { code: "Home", vk: 36 }, End: { code: "End", vk: 35 }, Escape: { code: "Escape", vk: 27 }, F5: { code: "F5", vk: 116 },
  Backspace: { code: "Backspace", vk: 8 }, ".": { code: "Period", vk: 190, text: "." }, "?": { code: "Slash", vk: 191, text: "?" },
};
async function tecla(s, key) {
  const t = TECLAS[key] ?? { code: /^[0-9]$/.test(key) ? `Digit${key}` : `Key${key.toUpperCase()}`, vk: key.toUpperCase().charCodeAt(0), text: key };
  await enviar("Input.dispatchKeyEvent", { type: "keyDown", key, code: t.code, windowsVirtualKeyCode: t.vk, nativeVirtualKeyCode: t.vk, text: t.text }, s);
  await enviar("Input.dispatchKeyEvent", { type: "keyUp", key, code: t.code, windowsVirtualKeyCode: t.vk, nativeVirtualKeyCode: t.vk }, s);
}
async function clic(s, x = 960, y = 540) {
  for (const type of ["mousePressed", "mouseReleased"]) await enviar("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1 }, s);
}
const estado = (s) => evaluar(s, "window.__pitch && window.__pitch.estado()");
function controlar(fase, nombre, ok, detalle = "") {
  informe.controles.push({ fase, nombre, ok, detalle });
  console.log(`${ok ? "OK   " : "FALLA"} [${fase}] ${nombre}${detalle ? " | " + detalle : ""}`);
}
// el paso n (1..N) visible y su video terminado
const exprTerminado = (n) => `(() => { const e = window.__pitch.estado(); const v = e.videos.find(x => x.visible); return e.actual === ${n - 1} && v && v.paso === ${n} && v.terminado; })()`;
const exprVisible = (n) => `(() => { const e = window.__pitch.estado(); const v = e.videos.find(x => x.visible); return e.actual === ${n - 1} && v && v.paso === ${n} && v.readyState >= 2; })()`;
async function terminado(s, n, ms = 20000) { return hasta(s, exprTerminado(n), ms); }

// instrumentos dentro de la página: cuándo arranca y termina cada video visible, y sus cuadros
const INSTRUMENTOS = `(() => {
  if (window.__uso) return true;
  window.__uso = { fin: [], esperas: [] };
  const vs = [...document.querySelectorAll('video.paso')];
  vs.forEach((v, k) => {
    let t0 = null, c0 = 0, q0 = null;
    v.addEventListener('playing', () => { if (t0 === null) { t0 = performance.now(); c0 = v.currentTime; const q = v.getVideoPlaybackQuality(); q0 = { tot: q.totalVideoFrames, dro: q.droppedVideoFrames }; } });
    v.addEventListener('waiting', () => { const e = window.__pitch.estado().videos[k]; if (e.visible) window.__uso.esperas.push({ paso: e.paso, t: v.currentTime }); });
    v.addEventListener('emptied', () => { t0 = null; });
    v.addEventListener('ended', () => {
      const e = window.__pitch.estado().videos[k];
      const q = v.getVideoPlaybackQuality();
      if (t0 !== null) window.__uso.fin.push({ paso: e.paso, visible: e.visible, pared_s: (performance.now() - t0) / 1000, video_s: v.duration - c0,
        cuadros: q.totalVideoFrames - (q0 ? q0.tot : 0), perdidos: q.droppedVideoFrames - (q0 ? q0.dro : 0) });
      t0 = null;
    });
    v.addEventListener('pause', () => { if (!v.ended) t0 = null; });
  });
  return true;
})()`;

let N = 0;
async function abrirPagina(s, nombre) {
  try { await evaluar(s, "window.__vieja = 1"); } catch { /* sin página */ }
  const t0 = Date.now();
  await enviar("Page.navigate", { url: pathToFileURL(html).href }, s);
  const tScript = await hasta(s, "!!window.__pitch && !window.__vieja", 90000, 50);
  const tVisible = await hasta(s, exprVisible(1), 30000, 30);
  const tAnda = await hasta(s, "(() => { const v = window.__pitch.estado().videos.find(x => x.visible); return v && v.t > 0.05; })()", 30000, 30);
  await evaluar(s, INSTRUMENTOS);
  const r = { reproductor_listo_ms: tScript, primer_cuadro_ms: tScript + tVisible, video_andando_ms: Date.now() - t0 };
  informe.fases[nombre] = { ...(informe.fases[nombre] || {}), ...r };
  return r;
}

async function main() {
  const p = await puerto();
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
    if (d.method === "Network.requestWillBeSent") {
      const u = d.params.request.url;
      if (!/^(file|data|blob|about|chrome|devtools):/.test(u)) informe.pedidos_de_red.push(u.slice(0, 200));
    }
    for (const o of [...oyentes]) if (o.pred(d)) { oyentes.splice(oyentes.indexOf(o), 1); o.ok(d); }
  };
  await enviar("Target.setDiscoverTargets", { discover: true });
  const { targetInfos } = await enviar("Target.getTargets");
  const pagina = targetInfos.find((t) => t.type === "page");
  const { sessionId: s } = await enviar("Target.attachToTarget", { targetId: pagina.targetId, flatten: true });
  await enviar("Page.enable", {}, s);
  await enviar("Runtime.enable", {}, s);
  await enviar("Network.enable", {}, s);
  await enviar("Network.emulateNetworkConditions", { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 }, s);
  await enviar("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false }, s);

  // ---------------------------------------------------------------- carga
  const c = await abrirPagina(s, "carga");
  N = (await estado(s)).total;
  controlar("carga", "sin red, el reproductor arranca y el paso 1 se ve", true,
    `reproductor ${c.reproductor_listo_ms} ms, primer cuadro ${c.primer_cuadro_ms} ms, video andando ${c.video_andando_ms} ms, ${N} pasos`);
  await terminado(s, 1, 30000);
  await captura(s, "carga_paso1_final.png");

  // ---------------------------------------------------------------- recorrido entero con cada tecla
  if (FASES.includes("recorrido")) {
    const ciclo = ["ArrowRight", " ", "PageDown", "Enter", "clic"];
    const fallas = [];
    for (let n = 2; n <= N; n++) {
      const k = ciclo[(n - 2) % ciclo.length];
      await dormir(250);   // se habla: el paso queda quieto
      if (k === "clic") await clic(s); else await tecla(s, k);
      try { await terminado(s, n, 25000); }
      catch (e) { fallas.push(`paso ${n} (${k}): ${e.message.slice(0, 80)}`); await captura(s, `FALLA_recorrido_paso${n}.png`); }
      const e = await estado(s);
      if (e.actual !== n - 1) { fallas.push(`con ${k} quedó en ${e.actual + 1} y no en ${n}`); await captura(s, `FALLA_recorrido_${n}.png`); }
    }
    await captura(s, "recorrido_ultimo_paso.png");
    const e = await estado(s);
    const malos = e.registro.filter((r) => r.readyState < 2);
    const fin = await evaluar(s, "window.__uso.fin.filter(f => f.visible)");
    const esperas = (await evaluar(s, "window.__uso.esperas")).filter((x) => !(x.paso === 1 && x.t < 0.5));   // el arranque del paso 1 al abrir no cuenta
    const perdidos = fin.reduce((a, f) => a + f.perdidos, 0), cuadros = fin.reduce((a, f) => a + f.cuadros, 0);
    const lentos = fin.filter((f) => f.pared_s > f.video_s + 0.35);
    informe.fases.recorrido = { fin, esperas, fallas };
    controlar("recorrido", `los ${N} pasos con flecha, espacio, Av Pág, Enter y clic, uno por tecla`, fallas.length === 0, fallas.slice(0, 4).join(" ; "));
    controlar("recorrido", "ningún cambio mostró un video sin su primer cuadro", malos.length === 0, `${malos.length} de ${e.registro.length} (últimos 20)`);
    controlar("recorrido", "los videos corren a tiempo (sin trabarse)", lentos.length === 0 && esperas.length === 0,
      `${fin.length} medidos, ${cuadros} cuadros, ${perdidos} perdidos, ${lentos.length} lentos, ${esperas.length} esperas`);
  }

  // ---------------------------------------------------------------- controles
  if (FASES.includes("controles")) {
    // Inicio y Fin
    await tecla(s, "Home"); await terminado(s, 1, 20000);
    controlar("controles", "Inicio vuelve al paso 1", (await estado(s)).actual === 0);
    await tecla(s, "End"); await terminado(s, N, 20000);
    controlar("controles", `Fin va al paso ${N}`, (await estado(s)).actual === N - 1);
    // salto con número y Enter
    for (const destino of [20, 9, 32]) {
      for (const ch of String(destino)) await tecla(s, ch);
      await tecla(s, "Enter");
      await terminado(s, destino, 20000);
      controlar("controles", `${destino} y Enter salta al paso ${destino}`, (await estado(s)).actual === destino - 1);
    }
    await captura(s, "controles_salto_32.png");
    // volver con flecha izquierda, Re Pág y Retroceso
    for (const [k, n] of [["ArrowLeft", 31], ["PageUp", 30], ["Backspace", 29]]) {
      await tecla(s, k); await dormir(150);
      const e1 = await estado(s); const v1 = e1.videos.find((v) => v.visible);
      await terminado(s, n, 20000);
      controlar("controles", `${k} vuelve un paso y el video arranca de cero`, e1.actual === n - 1 && v1 && v1.t < 1.0, `quedó en ${e1.actual + 1}, t=${v1 ? v1.t.toFixed(2) : "?"} s`);
    }
    // volver un paso y avanzar de nuevo
    await tecla(s, "ArrowLeft"); await terminado(s, 28, 20000);
    await tecla(s, "ArrowRight"); await dormir(150);
    const e2 = await estado(s); const v2 = e2.videos.find((v) => v.visible);
    await terminado(s, 29, 20000);
    controlar("controles", "volver y avanzar de nuevo: el paso arranca de cero y termina quieto", e2.actual === 28 && v2.t < 1.0, `t=${v2.t.toFixed(2)} s`);
    await captura(s, "controles_volver_y_avanzar_29.png");
    // diez avances rápidos desde el 5
    for (const ch of "5") await tecla(s, ch);
    await tecla(s, "Enter"); await terminado(s, 5, 20000);
    const tRap = Date.now();
    for (let k = 0; k < 10; k++) { await tecla(s, "ArrowRight"); await dormir(60); }
    await dormir(40);
    await captura(s, "controles_diez_rapidos_justo_despues.png");
    let ok10 = true, det10 = "";
    try { await terminado(s, 15, 25000); } catch (e) { ok10 = false; det10 = e.message.slice(0, 90); }
    const e3 = await estado(s);
    await captura(s, "controles_diez_rapidos_final.png");
    controlar("controles", "diez avances rápidos desde el 5 llegan al 15 y queda quieto", ok10 && e3.actual === 14,
      `quedó en ${e3.actual + 1}, ${Date.now() - tRap} ms ${det10}`);
    const visibles = e3.videos.filter((v) => v.visible).length;
    controlar("controles", "después de los rápidos hay un solo video arriba", visibles === 1, `${visibles} visibles`);
    // y diez para atrás
    for (let k = 0; k < 10; k++) { await tecla(s, "ArrowLeft"); await dormir(60); }
    let okAtras = true; try { await terminado(s, 5, 25000); } catch { okAtras = false; }
    controlar("controles", "diez retrocesos rápidos vuelven al 5", okAtras && (await estado(s)).actual === 4);
    // pantalla negra con B y con punto
    await tecla(s, "b"); await dormir(150);
    const neg = (await estado(s)).negro;
    await captura(s, "controles_negro.png");
    await tecla(s, "PageDown"); await dormir(150);
    const tras = await estado(s);
    controlar("controles", "B pone negro y la tecla siguiente solo lo saca", neg && !tras.negro && tras.actual === 4);
    await tecla(s, "."); await dormir(100);
    const neg2 = (await estado(s)).negro;
    await clic(s); await dormir(150);
    const tras2 = await estado(s);
    controlar("controles", "punto pone negro y un clic lo saca sin avanzar", neg2 && !tras2.negro && tras2.actual === 4);
    // ayuda
    await tecla(s, "h"); await dormir(150);
    const ay = (await estado(s)).ayuda;
    await captura(s, "controles_ayuda.png");
    await tecla(s, "Escape"); await dormir(100);
    controlar("controles", "H abre la ayuda y Escape la cierra", ay && !(await estado(s)).ayuda);
    // silencio con M
    const m0 = await evaluar(s, "JSON.stringify(window.__pitch.estado().silencio ?? null)");
    await tecla(s, "m"); await dormir(150);
    const m1 = await evaluar(s, "JSON.stringify(window.__pitch.estado().silencio ?? null)");
    const mudos = await evaluar(s, "[...document.querySelectorAll('video.paso')].every(v => v.muted)");
    await tecla(s, "m"); await dormir(150);
    const m2 = await evaluar(s, "JSON.stringify(window.__pitch.estado().silencio ?? null)");
    controlar("controles", "M silencia y vuelve a dar sonido", m0 === "false" && m1 === "true" && m2 === "false" && mudos, `antes ${m0}, con M ${m1}, otra vez ${m2}, todos mudos con M: ${mudos}`);
    // ¿algún video trae sonido?
    const conAudio = await evaluar(s, "window.__pitch.estado().videos.map(v => v.paso)");
    informe.fases.controles = { videos_en_elementos: conAudio };
    // pantalla completa con F y con F5
    await tecla(s, "f"); await dormir(500);
    const fs1 = await evaluar(s, "!!document.fullscreenElement");
    await captura(s, "controles_pantalla_completa.png");
    await tecla(s, "f"); await dormir(500);
    const fs2 = await evaluar(s, "!!document.fullscreenElement");
    await tecla(s, "F5"); await dormir(500);
    const fs3 = await evaluar(s, "!!document.fullscreenElement");
    const sigue = (await estado(s)).actual;
    await tecla(s, "F5"); await dormir(400);
    const fs4 = await evaluar(s, "!!document.fullscreenElement");
    // Chrome sin ventana no da pantalla completa a nadie (not granted): ahí solo se comprueba que F5 no recargue
    const sinVentana = !fs1 && !fs3 && (await enviar("Runtime.evaluate", { expression: "document.documentElement.requestFullscreen().then(() => 'ok', e => e.message)", awaitPromise: true, userGesture: true, returnByValue: true }, s)).result.value === "not granted";
    if (sinVentana) controlar("controles", "F y F5 no recargan ni cambian de paso (la pantalla completa no se puede probar sin ventana)", sigue === 4, `paso ${sigue + 1}`);
    else controlar("controles", "F entra y sale de pantalla completa, F5 solo entra y no recarga", fs1 && !fs2 && fs3 && fs4 && sigue === 4,
      `F ${fs1}, F otra vez ${fs2}, F5 ${fs3}, F5 otra vez ${fs4}, paso ${sigue + 1}`);
    await enviar("Runtime.evaluate", { expression: "document.fullscreenElement && document.exitFullscreen()", awaitPromise: true }, s);
    await dormir(300);
    // el número de paso en la dirección
    const hash = await evaluar(s, "location.hash");
    controlar("controles", "el paso queda anotado en la dirección", hash === "#5", hash);
  }

  // ---------------------------------------------------------------- vista del orador
  let so = null, oradorTarget = null;
  async function abrirOrador(ancho = 1280, alto = 800) {
    const nuevo = esperarEvento((d) => d.method === "Target.targetCreated" && d.params.targetInfo.type === "page", 8000);
    await tecla(s, "s");
    const ev = await nuevo;
    oradorTarget = ev.params.targetInfo.targetId;
    so = (await enviar("Target.attachToTarget", { targetId: oradorTarget, flatten: true })).sessionId;
    await enviar("Runtime.enable", {}, so);
    await enviar("Page.enable", {}, so);
    await enviar("Emulation.setDeviceMetricsOverride", { width: ancho, height: alto, deviceScaleFactor: 1, mobile: false }, so);
    await hasta(so, "!!document.getElementById('numero') && document.getElementById('numero').textContent.includes('/')", 8000);
  }
  if (FASES.includes("diag")) {
    const d = informe.fases.diag = {};
    const r = await enviar("Runtime.evaluate", { expression: "document.documentElement.requestFullscreen().then(() => 'ok', e => e.name + ': ' + e.message)", awaitPromise: true, userGesture: true, returnByValue: true }, s);
    d.fullscreen_con_gesto = r.result.value;
    await dormir(400);
    d.fullscreen_despues = await evaluar(s, "!!document.fullscreenElement");
    await evaluar(s, "document.fullscreenElement ? document.exitFullscreen().then(() => true) : true");
    await dormir(300);
    await evaluar(s, "window.__fsErr = null; document.addEventListener('fullscreenerror', () => { window.__fsErr = 'fullscreenerror'; }); true");
    await tecla(s, "f"); await dormir(600);
    d.tecla_f = await evaluar(s, "JSON.stringify({ fs: !!document.fullscreenElement, err: window.__fsErr, activo: navigator.userActivation ? navigator.userActivation.hasBeenActive : null })");
    await evaluar(s, "document.fullscreenElement ? document.exitFullscreen().then(() => true) : true");
    await tecla(s, "5"); await tecla(s, "Enter"); await terminado(s, 5, 20000);
    await abrirOrador();
    d.origen = await evaluar(s, "location.origin + ' | ' + window.origin");
    await evaluar(s, "window.__vieja = 1");
    await enviar("Page.reload", {}, s);
    await hasta(s, "!!window.__pitch && !window.__vieja", 60000, 50);
    await dormir(800);
    const acceso = await enviar("Runtime.evaluate", { expression: "(() => { const w = window.open('', 'orador_charla'); if (!w) return 'bloqueada'; try { return 'mismo origen: ' + w.document.title; } catch (e) { return 'error: ' + e.name + ' ' + e.message; } })()", userGesture: true, returnByValue: true }, s);
    d.acceso_tras_recarga = acceso.result.value;
    const antesS = informe.errores_consola.length;
    await tecla(s, "s"); await dormir(900);
    d.orador_tras_S = await evaluar(so, "document.getElementById('numero') ? document.getElementById('numero').textContent : 'sin documento'");
    d.errores_tras_S = informe.errores_consola.slice(antesS);
    const a0 = (await estado(s)).actual;
    await tecla(so, "PageDown"); await dormir(1200);
    d.clicker_orador_tras_S = `${a0 + 1} y después ${(await estado(s)).actual + 1}`;
    console.log("DIAG", JSON.stringify(d, null, 1));
  }

  if (FASES.includes("orador")) {
    await tecla(s, "6"); await tecla(s, "Enter"); await terminado(s, 6, 20000);
    await abrirOrador();
    await dormir(600);
    await captura(so, "orador_paso6.png");
    const r1 = await evaluar(so, "document.getElementById('reloj').textContent");
    await dormir(1300);
    const r2 = await evaluar(so, "document.getElementById('reloj').textContent");
    controlar("orador", "el reloj de la vista del orador anda", r1 !== r2 && /\d\d:\d\d/.test(r2), `${r1} y después ${r2}`);
    // el cronómetro arranca con el primer avance
    await tecla(so, "PageDown"); await terminado(s, 7, 20000);
    await dormir(2200);
    const tr = await evaluar(so, "document.getElementById('trans').textContent");
    const num = await evaluar(so, "document.getElementById('numero').textContent");
    controlar("orador", "Av Pág desde la ventana del orador avanza la presentación y el cronómetro corre", num.startsWith("7 /") && tr !== "0:00", `${num}, transcurrido ${tr}`);
    // las notas de cada paso: ¿entran sin scroll y a qué tamaño?
    const medidas = [];
    for (const [ancho, alto] of [[1280, 800], [1366, 728], [1280, 680]]) {
      await enviar("Emulation.setDeviceMetricsOverride", { width: ancho, height: alto, deviceScaleFactor: 1, mobile: false }, so);
      for (let n = 1; n <= N; n++) {
        await evaluar(s, `window.__pitch.ir(${n})`);
        await hasta(so, `document.getElementById('numero').textContent.startsWith('${n} /')`, 4000, 30).catch(() => {});
        await dormir(40);
        const m = await evaluar(so, `(() => { const e = document.getElementById('notas'); const cs = getComputedStyle(e); return { n: document.getElementById('numero').textContent, alto: e.clientHeight, contenido: e.scrollHeight, letra: parseFloat(cs.fontSize) }; })()`);
        medidas.push({ ventana: `${ancho}x${alto}`, paso: n, ...m });
        if (m.contenido > m.alto + 2 && (n === 26 || n === 29) && ancho === 1366) await captura(so, `orador_notas_no_entran_paso${n}_${ancho}x${alto}.png`);
      }
    }
    informe.fases.orador = { notas: medidas };
    for (const v of ["1280x800", "1366x728", "1280x680"]) {
      const cortadas = medidas.filter((m) => m.ventana === v && m.contenido > m.alto + 2);
      const chicas = medidas.filter((m) => m.ventana === v && m.letra < 18);
      controlar("orador", `con la ventana del orador en ${v}, todas las notas entran sin scroll`, cortadas.length === 0,
        cortadas.map((m) => `${m.paso} (${m.contenido}/${m.alto})`).join(", "));
      controlar("orador", `con la ventana del orador en ${v}, la letra de las notas no baja de 18 px`, chicas.length === 0,
        `mínima ${Math.min(...medidas.filter((m) => m.ventana === v).map((m) => m.letra))} px`);
    }
    await enviar("Emulation.setDeviceMetricsOverride", { width: 1366, height: 728, deviceScaleFactor: 1, mobile: false }, so);
    await evaluar(s, "window.__pitch.ir(26)"); await dormir(300);
    await captura(so, "orador_paso26_1366x728.png");
    await evaluar(s, "window.__pitch.ir(29)"); await dormir(300);
    await captura(so, "orador_paso29_1366x728.png");
    await evaluar(s, "window.__pitch.ir(19)"); await dormir(300);
    await captura(so, "orador_paso19_1366x728.png");
    const notas19 = await evaluar(so, "document.getElementById('notas').textContent");
    controlar("orador", "las notas que nombran una de respaldo dicen el número para saltar", /A1 \(32 y Enter\)/.test(notas19), (notas19.match(/[^.]*A1[^.]*/) || [""])[0].slice(0, 120));
    // M desde la ventana del orador
    const mAntes = await evaluar(s, "JSON.stringify(window.__pitch.estado().silencio ?? null)");
    await tecla(so, "m"); await dormir(150);
    const mDesp = await evaluar(s, "JSON.stringify(window.__pitch.estado().silencio ?? null)");
    await tecla(so, "m"); await dormir(100);
    controlar("orador", "M desde la ventana del orador también silencia", mAntes !== mDesp && mDesp === "true", `${mAntes} y ${mDesp}`);
  }

  // ---------------------------------------------------------------- recarga a mitad de la charla
  if (FASES.includes("recarga")) {
    await tecla(s, "1"); await tecla(s, "4"); await tecla(s, "Enter"); await terminado(s, 14, 20000);
    const trAntes = so ? await evaluar(so, "document.getElementById('trans').textContent") : null;
    await evaluar(s, "window.__vieja = 1");
    const t0 = Date.now();
    await enviar("Page.reload", { ignoreCache: false }, s);
    await hasta(s, "!!window.__pitch && !window.__vieja", 90000, 50);
    await hasta(s, "window.__pitch.estado().actual >= 0", 30000, 50);
    const e = await estado(s);
    const ms = Date.now() - t0;
    await evaluar(s, INSTRUMENTOS);
    await terminado(s, e.actual + 1, 25000).catch(() => {});
    await captura(s, "recarga_vuelve.png");
    controlar("recarga", "al recargar en el paso 14 vuelve al 14", e.actual === 13, `quedó en ${e.actual + 1}, ${ms} ms`);
    if (so) {
      // sin apretar S de nuevo: ¿la ventana del orador vuelve a conectarse sola y sigue manejando la presentación?
      await dormir(2600);
      const sola = (await estado(s)).orador;
      const segs = (t) => { const m = /^(\d+):(\d\d)/.exec(t || ""); return m ? Number(m[1]) * 60 + Number(m[2]) : -1; };
      const tr1 = await evaluar(so, "document.getElementById('trans').textContent");
      await dormir(1300);
      const tr2 = await evaluar(so, "document.getElementById('trans').textContent");
      controlar("recarga", "después de recargar, la vista del orador se vuelve a conectar sola", sola === true, `orador conectado: ${sola}`);
      controlar("recarga", "después de recargar, el cronómetro sigue desde donde iba y corre", segs(tr1) >= segs(trAntes) && segs(tr2) > segs(tr1),
        `antes ${trAntes}, después ${tr1} y ${tr2}`);
      const antes = (await estado(s)).actual;
      await tecla(so, "PageDown");
      await dormir(1500);
      const despues = (await estado(s)).actual;
      const numO = await evaluar(so, "document.getElementById('numero') ? document.getElementById('numero').textContent : '(sin documento)'");
      const trDesp = await evaluar(so, "document.getElementById('trans') ? document.getElementById('trans').textContent : ''");
      await captura(so, "recarga_orador.png");
      controlar("recarga", "después de recargar, el clicker en la ventana del orador sigue avanzando", despues === antes + 1, `antes ${antes + 1}, después ${despues + 1}`);
      controlar("recarga", "después de recargar, la vista del orador muestra el paso actual", numO.startsWith(`${despues + 1} /`), numO);
      informe.fases.recarga = { trans_final: trDesp };
      // y S después de recargar no rompe nada
      const errAntes = informe.errores_consola.length;
      await tecla(s, "s"); await dormir(800);
      controlar("recarga", "S después de recargar no da error y deja la vista conectada", informe.errores_consola.length === errAntes && (await estado(s)).orador === true,
        informe.errores_consola.slice(errAntes).join(" | ").slice(0, 200));
    }
  }

  // ---------------------------------------------------------------- tamaños de ventana
  if (FASES.includes("tamanos")) {
    if (so) { try { await evaluar(so, "window.close()"); } catch { /* ya cerrada */ } so = null; }
    for (const [w, h, esc] of [[1920, 1080, 1], [1366, 768, 1], [1280, 720, 1], [1024, 768, 1], [1366, 768, 1.25]]) {
      await enviar("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: esc, mobile: false }, s);
      for (const n of [1, 15, 29]) {
        await evaluar(s, `window.__pitch.ir(${n})`);
        await terminado(s, n, 20000);
        await dormir(100);
        const nombre = `tamano_${w}x${h}${esc !== 1 ? "_x" + esc : ""}_paso${n}.png`;
        await captura(s, nombre);
        const caja = await evaluar(s, `(() => { const v = [...document.querySelectorAll('video.paso')].find(x => x.classList.contains('visible')); const r = v.getBoundingClientRect();
          const ar = v.videoWidth / v.videoHeight, W = r.width, H = r.height; let cw = W, ch = W / ar; if (ch > H) { ch = H; cw = H * ar; }
          return { vw: innerWidth, vh: innerHeight, el: [r.left, r.top, r.width, r.height], contenido: [ (W - cw) / 2, (H - ch) / 2, cw, ch ], video: [v.videoWidth, v.videoHeight] }; })()`);
        (informe.fases.tamanos ??= []).push({ tamano: `${w}x${h}@${esc}`, paso: n, ...caja });
      }
      const k = informe.fases.tamanos.at(-1);
      const centrado = Math.abs(k.contenido[0] * 2 + k.contenido[2] - k.vw) < 1 && Math.abs(k.contenido[1] * 2 + k.contenido[3] - k.vh) < 1;
      const entero = k.contenido[2] <= k.vw + 0.5 && k.contenido[3] <= k.vh + 0.5;
      controlar("tamanos", `en ${w}x${h} (escala ${esc}) el video se ve entero y centrado`, centrado && entero,
        `video ${k.contenido.map((x) => Math.round(x)).join(", ")} en ${k.vw}x${k.vh}`);
    }
    await enviar("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false }, s);
  }

  // ---------------------------------------------------------------- procesador frenado 4 veces
  if (FASES.includes("cpu")) {
    await enviar("Emulation.setCPUThrottlingRate", { rate: 4 }, s);
    const c4 = await abrirPagina(s, "cpu");   // carga en frío con el procesador frenado
    controlar("cpu", "con el procesador frenado 4 veces, la carga", true,
      `reproductor ${c4.reproductor_listo_ms} ms, primer cuadro ${c4.primer_cuadro_ms} ms, video andando ${c4.video_andando_ms} ms`);
    // la página abre en el paso de la dirección (#...): ir al 1
    await evaluar(s, "window.__pitch.ir(1)");
    await terminado(s, 1, 30000);
    await evaluar(s, "window.__uso.fin = []; window.__uso.esperas = []; true");
    const fallas = [];
    for (let n = 2; n <= 16; n++) {
      await dormir(300);
      await tecla(s, n % 2 ? "PageDown" : "ArrowRight");
      try { await terminado(s, n, 30000); } catch (e) { fallas.push(`paso ${n}`); await captura(s, `FALLA_cpu_paso${n}.png`); }
    }
    // y los del sorteo y el cierre
    await evaluar(s, "window.__pitch.ir(26)"); await terminado(s, 26, 30000).catch(() => fallas.push("paso 26"));
    for (let n = 27; n <= 31; n++) { await dormir(300); await tecla(s, "ArrowRight"); try { await terminado(s, n, 30000); } catch { fallas.push(`paso ${n}`); } }
    const e = await estado(s);
    const malos = e.registro.filter((r) => r.readyState < 2);
    const fin = await evaluar(s, "window.__uso.fin.filter(f => f.visible)");
    const esperas = (await evaluar(s, "window.__uso.esperas")).filter((x) => !(x.paso === 1 && x.t < 0.5));   // el arranque del paso 1 al abrir no cuenta
    const perdidos = fin.reduce((a, f) => a + f.perdidos, 0), cuadros = fin.reduce((a, f) => a + f.cuadros, 0);
    const lentos = fin.filter((f) => f.pared_s > f.video_s + 0.35);
    informe.fases.cpu = { ...informe.fases.cpu, fin, esperas, fallas };
    await captura(s, "cpu_paso31.png");
    controlar("cpu", "con el procesador frenado, cada paso llega y termina quieto", fallas.length === 0, fallas.join(", "));
    controlar("cpu", "con el procesador frenado, ningún cambio sin primer cuadro", malos.length === 0, `${malos.length} de ${e.registro.length}`);
    controlar("cpu", "con el procesador frenado, los videos no se traban", lentos.length === 0 && esperas.length === 0 && perdidos <= cuadros * 0.02,
      `${fin.length} medidos, ${cuadros} cuadros, ${perdidos} perdidos, ${lentos.length} lentos (${lentos.map((f) => f.paso + ":" + f.pared_s.toFixed(2) + "/" + f.video_s.toFixed(2)).join(" ")}), ${esperas.length} esperas`);
    await enviar("Emulation.setCPUThrottlingRate", { rate: 1 }, s);
  }

  controlar("red", "ningún pedido a internet", informe.pedidos_de_red.length === 0, informe.pedidos_de_red.slice(0, 3).join(" "));
  const errores = informe.errores_consola.filter((t) => !/bloqueó el sonido/.test(String(t)));
  controlar("consola", "sin errores en la consola", errores.length === 0, errores.slice(0, 3).join(" | "));
}

let rc = 0;
try { await main(); }
catch (e) { console.error("FALLA:", e.message); informe.error = e.message; rc = 1; }
finally {
  try { await Promise.race([enviar("Browser.close"), dormir(3000)]); } catch { /* ya cerrado */ }
  const t = Date.now();
  while (chrome.exitCode === null && Date.now() - t < 5000) await dormir(100);
  if (chrome.exitCode === null) { try { execFileSync("taskkill", ["/PID", String(chrome.pid), "/T", "/F"], { stdio: "ignore" }); informe.cerrado_por_pid = true; } catch { /* nada */ } }
  informe.chrome_cerrado = chrome.exitCode !== null || informe.cerrado_por_pid === true;
  try { ws?.close(); } catch { /* nada */ }
  for (let i = 0; i < 20; i++) { try { fs.rmSync(perfil, { recursive: true, force: true }); break; } catch { await dormir(250); } }
  if (informe.controles.some((c) => !c.ok)) rc = 1;
  fs.writeFileSync(path.join(carpeta, "informe.json"), JSON.stringify(informe, null, 1));
  console.log(`informe en ${carpeta}; Chrome cerrado: ${informe.chrome_cerrado}; ${informe.controles.filter((c) => !c.ok).length} fallas de ${informe.controles.length}`);
  process.exit(rc);
}
