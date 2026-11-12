// SCC VAL Overwolf Link: reads VALORANT's game events with Overwolf's game
// events package (ow-electron, so no Overwolf install) and posts them to the
// SCC VAL HUD's /api/ingest, in the shape valhud/overwolf.py reads:
//   {"source": "overwolf", "overwolf": {"info": {category: {key: value}}}}
//   {"source": "overwolf", "overwolf": {"events": [{"name", "data"}]}}
//   {"source": "overwolf", "overwolf": {"heartbeat": {"running", "features"}, "info": <getInfo>}}
// The heartbeat goes every two seconds, so the HUD knows the link's alive
// (and falls back to its screen reader when it isn't).
"use strict";

const { app, BrowserWindow, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");

const VALORANT = 21640;
const FEATURES = ["gep_internal", "me", "game_info", "match_info", "kill", "death"];
const TEST_CHANNEL = "--owepm-package-channel=gep:dev";

let win = null;
let gep = null;
let settings = { hud: "http://localhost:8778", testChannel: false };
const status = {
  gep: "Starting Overwolf's game events...", game: "VALORANT not running", hud: "",
  sent: 0, failed: 0, features: [], version: "", testChannel: false, hudUrl: "",
};
let running = false;
let featuresSet = false;

// --- settings ------------------------------------------------------------------

function settingsFile() {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings() {
  try {
    settings = Object.assign(settings, JSON.parse(fs.readFileSync(settingsFile(), "utf8")));
  } catch (e) { /* first run */ }
  status.testChannel = !!settings.testChannel;
  status.hudUrl = settings.hud;
}

function saveSettings() {
  try {
    fs.mkdirSync(path.dirname(settingsFile()), { recursive: true });
    fs.writeFileSync(settingsFile(), JSON.stringify(settings, null, 1));
  } catch (e) { /* not fatal */ }
}

// --- sending to the HUD -----------------------------------------------------------

function show() {
  if (win && !win.isDestroyed()) win.webContents.send("status", status);
}

async function post(payload) {
  const url = settings.hud.replace(/\/+$/, "") + "/api/ingest";
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: "overwolf", overwolf: payload }),
      signal: AbortSignal.timeout(3000),
    });
    status.sent += 1;
    status.hud = r.ok ? `Sending to the HUD at ${settings.hud}` : `The HUD answered ${r.status}`;
  } catch (e) {
    status.failed += 1;
    status.hud = `Can't reach the HUD at ${settings.hud}. Is the SCC VAL HUD open on this PC?`;
  }
  show();
}

// getInfo's answer, as {category: {key: value}}.
function infoOf(res) {
  let x = res;
  if (x && typeof x === "object" && x.res && typeof x.res === "object") x = x.res;
  if (x && typeof x === "object" && x.info && typeof x.info === "object") x = x.info;
  return x && typeof x === "object" ? x : null;
}

async function beat() {
  const msg = { heartbeat: { running, features: status.features } };
  if (gep && running) {
    try {
      const info = infoOf(await gep.getInfo(VALORANT));
      if (info) msg.info = info;
    } catch (e) { /* game events not ready yet */ }
  }
  post(msg);
}

// --- Overwolf's game events ------------------------------------------------------

async function setFeatures() {
  if (!gep || featuresSet) return;
  try {
    await gep.setRequiredFeatures(VALORANT, FEATURES);
    featuresSet = true;
    try { status.features = await gep.getFeatures(VALORANT); } catch (e) { status.features = FEATURES; }
  } catch (e) {
    status.gep = `Overwolf's game events aren't ready for VALORANT yet (${e && e.message || e}). Retrying...`;
    show();
    setTimeout(setFeatures, 3000);
  }
}

function startGep(version) {
  gep = app.overwolf.packages.gep;
  status.version = version || "";
  status.gep = `Overwolf game events ${version || ""} ready`;
  gep.removeAllListeners();

  gep.on("game-detected", (e, gameId, name) => {
    if (gameId !== VALORANT) return;
    e.enable();
    running = true;
    status.game = "VALORANT detected: reading its game events";
    setFeatures();
    beat();
  });
  gep.on("elevated-privileges-required", (e, gameId) => {
    if (gameId !== VALORANT) return;
    status.game = "VALORANT is running as administrator: close this and run it as administrator too";
    show();
  });
  gep.on("game-exit", (e, gameId) => {
    if (gameId !== VALORANT) return;
    running = false;
    featuresSet = false;
    status.game = "VALORANT not running";
    beat();
  });
  gep.on("new-info-update", (e, gameId, ...items) => {
    if (gameId !== VALORANT) return;
    const info = {};
    for (const d of items) {
      if (!d || typeof d !== "object" || !d.key) continue;
      const cat = d.category || d.feature || "match_info";
      (info[cat] = info[cat] || {})[d.key] = d.value;
    }
    if (Object.keys(info).length) post({ info });
  });
  gep.on("new-game-event", (e, gameId, ...items) => {
    if (gameId !== VALORANT) return;
    const events = items.filter(d => d && typeof d === "object" && (d.key || d.name))
      .map(d => ({ name: d.key || d.name, data: d.value !== undefined ? d.value : d.data }));
    if (events.length) post({ events });
  });
  gep.on("error", (e, gameId, error) => {
    status.gep = `Overwolf game events error: ${error}`;
    show();
  });
  featuresSet = false;
  setFeatures();
  show();
}

// --- the window --------------------------------------------------------------------

function createWindow() {
  win = new BrowserWindow({
    width: 460, height: 400, resizable: false, autoHideMenuBar: true, title: "SCC VAL Overwolf Link",
    icon: path.join(__dirname, "icon.png"), backgroundColor: "#111318",
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, "index.html"));
  win.webContents.on("did-finish-load", show);
}

ipcMain.on("set-hud", (e, url) => {
  url = String(url || "").trim();
  if (!/^https?:\/\//i.test(url)) url = "http://" + url;
  settings.hud = url.replace(/\/+$/, "") || "http://localhost:8778";
  status.hudUrl = settings.hud;
  saveSettings();
  beat();
});

ipcMain.on("set-test-channel", (e, on) => {
  settings.testChannel = !!on;
  saveSettings();
  // The package channel is read at start: start again with (or without) it.
  const args = process.argv.slice(1).filter(a => a !== TEST_CHANNEL);
  if (settings.testChannel) args.push(TEST_CHANNEL);
  app.relaunch({ args });
  app.exit(0);
});

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => { if (win) { win.show(); win.focus(); } });
  app.whenReady().then(() => {
    loadSettings();
    // Overwolf's test channel (for games whose events aren't released to
    // ow-electron yet): restart with it when it's on.
    if (settings.testChannel && !process.argv.includes(TEST_CHANNEL)) {
      app.relaunch({ args: process.argv.slice(1).concat([TEST_CHANNEL]) });
      app.exit(0);
      return;
    }
    createWindow();
    const packages = app.overwolf && app.overwolf.packages;
    if (!packages) {
      status.gep = "This build has no Overwolf packages (it must be built with ow-electron)";
      show();
      return;
    }
    packages.on("ready", (e, name, version) => { if (name === "gep") startGep(version); });
    packages.on("failed-to-initialize", (e, name) => {
      if (name === "gep") { status.gep = "Overwolf's game events failed to start. Restart this app"; show(); }
    });
    packages.on("crashed", (e, canRecover) => {
      status.gep = "Overwolf's game events crashed" + (canRecover ? ": restarting them" : "");
      show();
      if (canRecover) packages.relaunch();
    });
    if (packages.gep) startGep("");   // (already loaded)
    setInterval(beat, 2000);
  });
  app.on("window-all-closed", () => app.quit());
}
