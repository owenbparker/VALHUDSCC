// SCC VAL HUD Link: VALORANT's game events from Overwolf, posted to the
// SCC VAL HUD on this PC (/api/ingest). An observer client's HUD passes them
// on to the GFX PC. Every two seconds it also sends everything Overwolf
// knows (a heartbeat), so the HUD can tell Overwolf is still alive and pick
// up from a restart.
"use strict";

var VALORANT = 21640;
var HUD = "http://localhost:8778";
try { HUD = localStorage.getItem("hud") || HUD; } catch (e) {}
var FEATURES = ["gep_internal", "me", "game_info", "match_info", "kill", "death"];

var running = false, supported = [], retry = null;

function post(payload) {
  try {
    fetch(HUD + "/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: "overwolf", overwolf: payload })
    }).catch(function () {});
  } catch (e) {}
}

function setFeatures() {
  clearTimeout(retry);
  if (!running) return;
  overwolf.games.events.setRequiredFeatures(FEATURES, function (r) {
    if (r && r.success) {
      supported = r.supportedFeatures || FEATURES;
    } else {
      supported = [];
      retry = setTimeout(setFeatures, 2000);   // (Overwolf isn't ready for the game yet)
    }
  });
}

function gameChanged(info) {
  var now = !!(info && info.isRunning && (info.classId || Math.floor(info.id / 10)) === VALORANT);
  if (now === running) return;
  running = now;
  supported = [];
  if (running) setFeatures();
  beat();
}

function beat() {
  if (!running || !supported.length) {
    post({ heartbeat: { running: running, features: supported } });
    return;
  }
  overwolf.games.events.getInfo(function (r) {
    var msg = { heartbeat: { running: running, features: supported } };
    if (r && r.res) msg.info = r.res;
    post(msg);
  });
}

overwolf.games.events.onInfoUpdates2.addListener(function (e) {
  if (e && e.info) post({ info: e.info, feature: e.feature });
});
overwolf.games.events.onNewEvents.addListener(function (e) {
  if (e && e.events) post({ events: e.events });
});
overwolf.games.onGameInfoUpdated.addListener(function (e) {
  if (e) gameChanged(e.gameInfo);
});
overwolf.games.getRunningGameInfo(function (info) { gameChanged(info); });
setInterval(beat, 2000);
