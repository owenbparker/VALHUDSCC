// Player webcams on the HUD: when the observer is spectating a player whose
// cam is connected (the SCC Player Cam app, VALORANT mode, with their Riot
// ID), their cam pops up in the template's camera box, bottom left of
// centre, framed in their side's colour with their name and K / D / A.
//
// The cams connect straight to this page over the local network (WebRTC,
// peer to peer); the app only passes the connection messages along (see
// valhud/cams.py). Every connected cam is kept open, so switching players
// is instant.
(function () {
  var ME = Math.random().toString(16).slice(2, 18);
  var BOX = { x: 480, y: 775, w: 300, h: 171 };   // the template's camera box (.CameraPosition)

  var style = document.createElement("style");
  style.textContent =
    "#scc-cam { position: absolute; left: " + BOX.x + "px; top: " + BOX.y + "px; width: " + BOX.w + "px; height: " + BOX.h + "px;" +
    " z-index: 40; pointer-events: none; opacity: 0; transform: translateY(24px);" +
    " transition: opacity .35s ease, transform .45s cubic-bezier(.2,.8,.2,1); }" +
    "#scc-cam.on { opacity: 1; transform: none; }" +
    "#scc-cam div { position: static; margin: 0; padding: 0; float: none; }" +
    "#scc-cam .scc-frame { position: absolute; inset: 0; background: #1f1e23; overflow: hidden;" +
    " box-shadow: inset 0 0 0 2px var(--team), 0 0 18px -6px var(--team); transition: box-shadow .4s; }" +
    "#scc-cam video { position: absolute; left: 2px; top: 2px; width: calc(100% - 4px); height: calc(100% - 30px);" +
    " object-fit: cover; opacity: 0; transition: opacity .3s ease; background: #3c3c46; }" +
    "#scc-cam video.on { opacity: 1; }" +
    "#scc-cam .scc-band { position: absolute; left: 2px; right: 2px; bottom: 2px; height: 26px; background: #1f1e23;" +
    " display: flex; align-items: center; color: whitesmoke; font-family: Arabic, sans-serif; font-size: 18px; }" +
    "#scc-cam .scc-bar { width: 4px; height: 18px; margin: 0 8px 0 6px; background: var(--team); transition: background .4s; }" +
    "#scc-cam .scc-name { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }" +
    "#scc-cam .scc-kda { padding: 0 10px 0 8px; white-space: nowrap; letter-spacing: .02em; }";
  document.head.appendChild(style);

  var box = document.createElement("div");
  box.id = "scc-cam";
  box.innerHTML = '<div class="scc-frame"><div class="scc-videos"></div>' +
    '<div class="scc-band"><div class="scc-bar"></div><div class="scc-name"></div><div class="scc-kda"></div></div></div>';
  (document.body || document.documentElement).appendChild(box);
  var videos = box.querySelector(".scc-videos");

  var peers = {};     // cam (publisher) id -> { pc, video, started }
  var registered = false;

  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function post(path, body) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || r.status); return d; }); });
  }

  function drop(id) {
    var p = peers[id];
    if (!p) return;
    delete peers[id];
    try { p.pc.close(); } catch (e) { /* already closed */ }
    p.video.remove();
  }

  function gathered(pc) {
    if (pc.iceGatheringState === "complete") return Promise.resolve();
    return new Promise(function (resolve) {
      pc.addEventListener("icegatheringstatechange", function () { if (pc.iceGatheringState === "complete") resolve(); });
      setTimeout(resolve, 2500);   // the local network's addresses come quickly
    });
  }

  function connect(id) {
    var video = document.createElement("video");
    video.autoplay = video.muted = video.playsInline = true;
    videos.appendChild(video);
    var pc = new RTCPeerConnection({ iceServers: [] });
    peers[id] = { pc: pc, video: video, started: Date.now() };
    pc.addTransceiver("video", { direction: "recvonly" });
    pc.ontrack = function (e) {
      video.srcObject = e.streams[0] || new MediaStream([e.track]);
      video.play().catch(function () {});
    };
    pc.onconnectionstatechange = function () {
      if (pc.connectionState === "failed" || pc.connectionState === "closed") drop(id);
    };
    pc.createOffer()
      .then(function (offer) { return pc.setLocalDescription(offer); })
      .then(function () { return gathered(pc); })
      .then(function () { return post("/api/cam/send", { to: id, from: ME, data: { type: "offer", sdp: pc.localDescription.sdp } }); })
      .catch(function () { drop(id); });
  }

  (async function inbox() {
    for (;;) {
      try {
        var r = await post("/api/cam/poll", { id: ME, wait: registered ? 20 : 0 });
        registered = true;
        (r.messages || []).forEach(function (m) {
          var p = peers[m.from];
          if (!p) return;
          if (m.type === "answer" && p.pc.signalingState === "have-local-offer") {
            p.pc.setRemoteDescription({ type: "answer", sdp: m.sdp }).catch(function () { drop(m.from); });
          } else if (m.type === "bye") drop(m.from);
        });
      } catch (e) { await sleep(2000); }
    }
  })();
  addEventListener("pagehide", function () {
    Object.keys(peers).forEach(function (id) {
      if (navigator.sendBeacon) navigator.sendBeacon("/api/cam/send",
        new Blob([JSON.stringify({ to: id, from: ME, data: { type: "bye" } })], { type: "text/plain" }));
    });
  });

  // Called by driver.js with each state; hide: the buy-phase scoreboard is up.
  window.renderCams = function (s, hide) {
    var cfg = s.config, m = s.game.match, pubs = (s.cams || {}).publishers || [];
    var on = (cfg.cams || {}).enabled !== false;
    var wanted = {};
    pubs.forEach(function (p) {
      if (!on) return;
      wanted[p.id] = true;
      var peer = peers[p.id];
      if (peer && peer.pc.connectionState !== "connected" && Date.now() - peer.started > 10000) drop(p.id);
      if (registered && !peers[p.id]) connect(p.id);
    });
    Object.keys(peers).forEach(function (id) { if (!wanted[id]) drop(id); });

    // The spectated player, and their cam if they have one.
    var o = m.observed, player = null, cam = null;
    if (o) {
      player = s.game.players.filter(function (p) { return p.team === o.team && p.slot === o.slot; })[0] || null;
      cam = pubs.filter(function (p) { return p.player && p.player.team === o.team && p.player.slot === o.slot; })[0] || null;
    }
    var peer = cam && peers[cam.id];
    var ready = !!(peer && peer.video.readyState >= 2);
    Object.keys(peers).forEach(function (id) { peers[id].video.classList.toggle("on", !!cam && id === cam.id); });
    var show = on && !hide && ready && !!player;
    box.classList.toggle("on", show);
    if (!player) return;
    // Framed in their side's colour (the sides swap at half time).
    var colour = player.team === m.attackers ? cfg.attack_color : cfg.defense_color;
    box.style.setProperty("--team", colour || "#00ffcc");
    box.querySelector(".scc-name").textContent = player.name || "";
    box.querySelector(".scc-kda").textContent = [player.kills, player.deaths, player.assists].map(function (n) { return n || 0; }).join(" / ");
  };
})();
