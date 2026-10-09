import { applyBps } from "./patch.mjs";

const $ = id => document.getElementById(id);
const elements = {
  rom: $("rom"), patch: $("patch"), status: $("status"),
  play: $("play"), download: $("download-game"), clear: $("clear"), library: $("library"),
  reload: $("reload"), remember: $("remember"), install: $("install"),
  playerbox: $("playerbox"), iframe: $("emulator"), playing: $("playing"),
  fullscreen: $("fullscreen"), exit: $("exit")
};
const MAX_ROM = 64 * 1024 * 1024;
const MAX_PATCH = 64 * 1024 * 1024;
const dbName = "gba-pocket-local-v1";
let dbPromise = null, inProgress = false, deferredInstall = null;
let pendingGame = null;
let generatedGame = null;
let playing = false;

function notify(message, error = false) {
  elements.status.textContent = message;
  elements.status.className = error ? "status error" : "status";
}
function prettyBytes(size) {
  return size >= 1024 * 1024 ? (size / 1048576).toFixed(1) + " MB" : (size / 1024).toFixed(1) + " KB";
}
function displayName(file) {
  return file.name.replace(/\.gba$/i, "").trim().slice(0, 75) || "Jogo de GBA";
}
function safeFileName(title) {
  return title.replace(/[^a-z0-9 _.-]/gi, "_").slice(0, 64);
}
function hasExt(file, ext) {
  return file && file.name.toLowerCase().endsWith(ext);
}
function getDb() {
  if (!("indexedDB" in window)) return Promise.reject(Error("Este navegador não suporta biblioteca local."));
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("games")) db.createObjectStore("games", { keyPath: "id" });
      if (!db.objectStoreNames.contains("metadata")) db.createObjectStore("metadata", { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || Error("Falha ao abrir IndexedDB."));
    request.onblocked = () => reject(Error("Feche outras abas com este app e tente novamente."));
  }).catch(err => {
    dbPromise = null;
    throw err;
  });
  return dbPromise;
}
async function putGame(game, bytes) {
  const db = await getDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["games", "metadata"], "readwrite");
    const record = { id: game.id, title: game.title, size: bytes.length, savedAt: Date.now() };
    tx.objectStore("games").put({ ...record, contents: new Blob([bytes], { type: "application/octet-stream" }) });
    tx.objectStore("metadata").put(record);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error || Error("Não foi possível guardar o jogo."));
    tx.onabort = () => reject(tx.error || Error("Armazenamento local indisponível."));
  });
}
async function listGames() {
  const db = await getDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("metadata", "readonly");
    const request = tx.objectStore("metadata").getAll();
    request.onsuccess = () => resolve(request.result.sort((a, b) => b.savedAt - a.savedAt));
    request.onerror = () => reject(request.error);
  });
}
async function loadGame(id) {
  const db = await getDb();
  const data = await new Promise((resolve, reject) => {
    const request = db.transaction("games", "readonly").objectStore("games").get(id);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  if (!data) throw Error("Este jogo não está mais na biblioteca.");
  return { title: data.title, id: data.id, bytes: new Uint8Array(await data.contents.arrayBuffer()) };
}
async function deleteGame(id) {
  const db = await getDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["games", "metadata"], "readwrite");
    tx.objectStore("games").delete(id);
    tx.objectStore("metadata").delete(id);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}
async function sha(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(x => x.toString(16).padStart(2, "0")).join("");
}
function setBusy(busy) {
  inProgress = busy;
  elements.play.disabled = busy;
  elements.clear.disabled = busy;
  elements.reload.disabled = busy;
  elements.download.disabled = busy || !generatedGame;
}
function loadFrame(title, id, bytes) {
  if (playing && !confirm("Fechar o jogo atual? Salve o progresso no emulador antes de trocar de jogo.")) {
    notify("Troca cancelada. Continue seu jogo atual.");
    return;
  }
  pendingGame = { title, id, bytes };
  playing = true;
  elements.playing.textContent = title;
  elements.playerbox.classList.add("show");
  elements.iframe.src = "./player.html?session=" + Date.now();
  elements.playerbox.scrollIntoView({ behavior: "smooth", block: "start" });
  notify("Preparando " + title + ". Aguarde a inicialização do núcleo GBA.");
}
async function refreshLibrary() {
  elements.library.replaceChildren();
  try {
    const games = await listGames();
    if (!games.length) {
      const el = document.createElement("div");
      el.className = "empty";
      el.textContent = "Nenhum jogo guardado ainda. Adicione um arquivo .gba.";
      elements.library.append(el);
      return;
    }
    for (const game of games) {
      const item = document.createElement("div");
      item.className = "game-row";
      const thumb = document.createElement("span");
      thumb.className = "game-thumb";
      thumb.textContent = "GBA";
      const meta = document.createElement("div");
      meta.className = "game-meta";
      const title = document.createElement("strong");
      title.textContent = game.title;
      title.title = game.title;
      const subtitle = document.createElement("small");
      subtitle.textContent = prettyBytes(game.size) + " · Salvo neste navegador";
      meta.append(title, subtitle);
      const actions = document.createElement("div");
      actions.className = "row-actions";
      const play = document.createElement("button");
      play.className = "btn small";
      play.textContent = "▶";
      play.title = "Jogar " + game.title;
      play.setAttribute("aria-label", "Jogar " + game.title);
      play.addEventListener("click", async () => {
        play.disabled = true;
        try {
          const result = await loadGame(game.id);
          loadFrame(result.title, result.id, result.bytes);
        } catch (e) {
          notify(e.message || "Falha ao abrir jogo.", true);
        } finally { play.disabled = false; }
      });
      const remove = document.createElement("button");
      remove.className = "btn ghost small";
      remove.textContent = "×";
      remove.title = "Remover do dispositivo";
      remove.setAttribute("aria-label", "Excluir " + game.title + " da biblioteca");
      remove.addEventListener("click", async () => {
        if (!confirm("Remover " + game.title + " da biblioteca local? O save interno do emulador é armazenado separadamente.")) return;
        try {
          await deleteGame(game.id);
          await refreshLibrary();
          notify("Jogo removido da biblioteca.");
        } catch (e) {
          notify(e.message || "Falha ao remover.", true);
        }
      });
      actions.append(play, remove);
      item.append(thumb, meta, actions);
      elements.library.append(item);
    }
  } catch (e) {
    const err = document.createElement("div");
    err.className = "empty";
    err.textContent = "Biblioteca indisponível: " + (e.message || e);
    elements.library.append(err);
  }
}
async function startFromFiles() {
  if (inProgress) return;
  const rom = elements.rom.files[0];
  const patch = elements.patch.files[0];
  if (!rom || !hasExt(rom, ".gba")) {
    notify("Selecione uma ROM válida com extensão .gba.", true);
    return;
  }
  if (rom.size === 0 || rom.size > MAX_ROM) {
    notify("A ROM precisa ter de 1 byte a 64 MB.", true);
    return;
  }
  if (patch && (!hasExt(patch, ".bps") || patch.size > MAX_PATCH)) {
    notify("Selecione um patch .bps de até 64 MB.", true);
    return;
  }
  setBusy(true);
  try {
    notify("Lendo seu jogo localmente…");
    const source = new Uint8Array(await rom.arrayBuffer());
    let game = source;
    if (patch) {
      notify("Aplicando patch BPS e verificando checksums…");
      const diff = new Uint8Array(await patch.arrayBuffer());
      game = applyBps(source, diff);
    }
    const hash = await sha(game);
    const title = displayName(rom) + (patch ? " · Modificado" : "");
    const gameInfo = { title, id: hash };
    let message = null;
    if (elements.remember.checked) {
      try {
        await putGame(gameInfo, game);
        await refreshLibrary();
      } catch (err) {
        message = "O jogo abriu, mas não foi possível guardá-lo na biblioteca: " + (err.message || err);
      }
    }
    generatedGame = { filename: safeFileName(displayName(rom) + (patch ? "-unova" : "")) + ".gba", blob: new Blob([game], { type: "application/octet-stream" }) };
    elements.download.disabled = false;
    loadFrame(gameInfo.title, gameInfo.id, game);
    if (message) notify(message, true);
  } catch (err) {
    notify(err.message || "Não foi possível abrir o jogo.", true);
  } finally {
    setBusy(false);
  }
}
elements.play.addEventListener("click", startFromFiles);
elements.download.addEventListener("click", () => {
  if (!generatedGame) return;
  const url = URL.createObjectURL(generatedGame.blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = generatedGame.filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 15000);
  notify("Download iniciado: " + generatedGame.filename + ". Guarde esse .gba no aparelho.");
});
elements.reload.addEventListener("click", refreshLibrary);
elements.clear.addEventListener("click", () => {
  elements.rom.value = "";
  elements.patch.value = "";
  generatedGame = null;
  elements.download.disabled = true;
  $("romlabel").textContent = "Selecionar ROM GBA";
  $("patchlabel").textContent = "Selecionar patch BPS";
  notify("Seleção limpa. Escolha um arquivo .gba.");
});
for (const [input, label] of [[elements.rom, $("romlabel")], [elements.patch, $("patchlabel")]]) {
  input.addEventListener("change", () => {
    label.textContent = input.files.length ? input.files[0].name : input === elements.rom ? "Selecionar ROM GBA" : "Selecionar patch BPS";
  });
}
elements.exit.addEventListener("click", () => {
  if (playing && !confirm("Fechar o emulador? Salve seu jogo no menu antes de sair.")) return;
  playing = false;
  pendingGame = null;
  elements.iframe.removeAttribute("src");
  elements.playerbox.classList.remove("show");
  notify("Emulador fechado. Seus jogos guardados continuam na biblioteca.");
});
elements.fullscreen.addEventListener("click", async () => {
  try {
    if (!document.fullscreenElement) await elements.iframe.requestFullscreen();
    else await document.exitFullscreen();
  } catch (e) {
    notify("Tela cheia não disponível neste navegador: " + (e.message || e), true);
  }
});

window.addEventListener("message", ev => {
  if (ev.origin !== location.origin || ev.source !== elements.iframe.contentWindow) return;
  const msg = ev.data;
  if (!msg || msg.source !== "gba-pocket-player") return;
  if (msg.type === "ready" && pendingGame && pendingGame.bytes) {
    const bytes = pendingGame.bytes;
    elements.iframe.contentWindow.postMessage({
      source: "gba-pocket-host",
      type: "load",
      name: safeFileName(pendingGame.title) + "-" + pendingGame.id.slice(0, 12),
      buffer: bytes.buffer
    }, location.origin, [bytes.buffer]);
    pendingGame.bytes = null;
  } else if (msg.type === "started") {
    notify("Jogo iniciado! Use os controles na tela ou o menu do emulador.");
  } else if (msg.type === "save") {
    notify("Progresso detectado pelo emulador. Faça backup do SAV pelo menu para maior segurança.");
  } else if (msg.type === "error") {
    notify("Emulador: " + (msg.message || "erro desconhecido"), true);
  }
});

window.addEventListener("beforeinstallprompt", event => {
  event.preventDefault();
  deferredInstall = event;
  elements.install.hidden = false;
});
elements.install.addEventListener("click", async () => {
  if (!deferredInstall) return;
  const prompt = deferredInstall;
  deferredInstall = null;
  elements.install.hidden = true;
  prompt.prompt();
  try { await prompt.userChoice; } catch (_) { /* install can be declined */ }
});
window.addEventListener("appinstalled", () => {
  elements.install.hidden = true;
  notify("GBA Pocket instalado neste dispositivo!");
});
if ("serviceWorker" in navigator && location.protocol === "https:") {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
}
refreshLibrary();
