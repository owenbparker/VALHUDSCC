// Player webcams on the HUD: when the observer is spectating a player whose
// cam is connected (the SCC Player Cam app, VALORANT mode, with their Riot
// ID), their cam pops up in the template's camera box, bottom left of
// centre, framed in black with a bar in their side's colour, their name
// and K / D / A. Switching between players with cams is a straight cut; the
// box slides in and out when there's a cam to show or not.
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
    " box-shadow: inset 0 0 0 2px #000; }" +
    "#scc-cam video { position: absolute; left: 2px; top: 2px; width: calc(100% - 4px); height: calc(100% - 34px);" +
    " object-fit: cover; opacity: 0; background: #3c3c46; }" +   // (a straight cut between players)
    "#scc-cam video.on { opacity: 1; }" +
    // The demo's stand-in cam: the agent on a dark backdrop.
    "#scc-cam .scc-dummy { position: absolute; left: 2px; top: 2px; width: calc(100% - 4px); height: calc(100% - 34px);" +
    " display: none; background: radial-gradient(circle at 50% 35%, #4a4a58, #23232b 70%) center / cover no-repeat; }" +
    "#scc-cam .scc-dummy.on { display: block; }" +
    "#scc-cam .scc-dummy i { position: absolute; right: 8px; top: 6px; font: 12px Arabic, sans-serif; color: #fff9;" +
    " letter-spacing: .1em; font-style: normal; }" +
    // The name band: the side's colour as a strip down its full height at
    // the left, the name and K / D / A centred in it, the same space in
    // from either end.
    "#scc-cam .scc-band { position: absolute; left: 2px; right: 2px; bottom: 2px; height: 30px; background: #1f1e23;" +
    " display: flex; align-items: center; color: whitesmoke; font-family: Arabic, sans-serif; font-size: 18px; line-height: 1; }" +
    "#scc-cam .scc-bar { align-self: stretch; flex: 0 0 6px; margin-right: 12px; background: var(--team); }" +
    "#scc-cam .scc-name { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }" +
    // (the HUD's own font sits low in its line: raised to the middle)
    "#scc-cam .scc-name, #scc-cam .scc-kda { transform: translateY(-.11em); }" +
    "#scc-cam .scc-kda { padding: 0 12px 0 10px; white-space: nowrap; letter-spacing: .02em; }" +
    // Kills this round: a tag in the side's colour that flies up out of the
    // top of the frame at the first kill (and pops at each one after).
    "#scc-cam .scc-kills { position: absolute; left: 2px; bottom: 100%; height: 28px; padding: 0 10px 0 8px;" +
    " display: flex; align-items: center; gap: 6px; background: var(--team); color: #fff;" +
    " font-family: Arabic, sans-serif; font-size: 20px; line-height: 1; opacity: 0; transform: translateY(28px);" +
    " clip-path: inset(0 0 0 0); transition: opacity .2s ease, transform .4s cubic-bezier(.2,.8,.2,1); z-index: -1; }" +
    "#scc-cam .scc-kills.on { opacity: 1; transform: none; }" +
    "#scc-cam .scc-kills.pop { animation: scc-pop .35s ease; }" +
    "#scc-cam .scc-kills span { transform: translateY(-.08em); }" +
    "@keyframes scc-pop { 0% { transform: translateY(-6px) scale(1.12); } 100% { transform: none; } }";
  document.head.appendChild(style);

  var box = document.createElement("div");
  box.id = "scc-cam";
  box.innerHTML = '<div class="scc-kills"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#fff"' +
    ' stroke-width="2"><circle cx="8" cy="8" r="5"/><path d="M8 0v4M8 12v4M0 8h4M12 8h4"/></svg><span></span></div>' +
    '<div class="scc-frame"><div class="scc-videos"></div><div class="scc-dummy"><i>DEMO CAM</i></div>' +
    '<div class="scc-band"><div class="scc-bar"></div><div class="scc-name"></div><div class="scc-kda"></div></div></div>';
  (document.body || document.documentElement).appendChild(box);
  var videos = box.querySelector(".scc-videos");

  // 2v2 skirmish (config team_size 2): every player's cam sits under their
  // tab, 16:9, all the time (the pop-up cam above is left out). The
  // spectated player's tab and cam are framed together in the template's
  // highlight gold, round the outside, so nothing covers the cam. With no
  // cam connected the box shows the team's logo (the demo: the agent).
  var DUO = { tops: [500, 790], tab: 94, w: 316, h: 178, left: { left: 14, x: 14 }, right: { left: 1594, x: 1591 } };
  var GOLD = "#d6ca97";
  style.textContent +=
    ".scc-duo { position: absolute; width: " + DUO.w + "px; height: " + (DUO.tab + DUO.h) + "px; pointer-events: none; display: none; }" +
    "html.scc-2v2 .scc-duo { display: block; }" +
    ".scc-duo .scc-duo-cam { position: absolute; left: 0; right: 0; bottom: 0; height: " + DUO.h + "px; overflow: hidden;" +
    " background: radial-gradient(circle at 50% 40%, #2c2c34, #101014 75%); box-shadow: inset 0 0 0 1px #c3c3c3; }" +
    ".scc-duo video { position: absolute; left: 1px; top: 0; width: calc(100% - 2px); height: calc(100% - 1px); object-fit: cover; opacity: 0; }" +
    ".scc-duo video.on { opacity: 1; }" +
    ".scc-duo .scc-duo-logo { position: absolute; inset: 0; background: center 46% / auto 46% no-repeat; opacity: .9; }" +
    ".scc-duo .scc-duo-logo.agent { background-position: center bottom; background-size: auto 92%; opacity: 1; }" +
    ".scc-duo .scc-duo-logo i { position: absolute; right: 8px; top: 6px; font: 12px Arabic, sans-serif; color: #fff9;" +
    " letter-spacing: .1em; font-style: normal; display: none; }" +
    ".scc-duo .scc-duo-logo.agent i { display: block; }" +
    // The highlight: a gold line round the tab (its cut top corner too) and the cam.
    ".scc-duo svg { position: absolute; left: 0; top: 0; overflow: visible; opacity: 0; z-index: 6;" +
    " filter: drop-shadow(0 0 5px " + GOLD + "aa); transition: opacity .2s ease; }" +
    ".scc-duo.right svg { transform: scaleX(-1); }" +
    ".scc-duo.on svg { opacity: 1; }";

  var duoBoxes = [];
  function duoBoxesMade() {
    if (duoBoxes.length) return true;
    var homes = { left: document.getElementById("teamIzquierda"), right: document.getElementById("teamDerecha") };
    if (!homes.left || !homes.right) return false;
    var W = DUO.w, H = DUO.tab + DUO.h, o = 2.5;
    // (the tab's top corner is cut from 16 px along to 21 px down)
    var ring = [[15, -o], [W + o, -o], [W + o, H + o], [-o, H + o], [-o, 21]].map(function (p) { return p.join(","); }).join(" ");
    ["left", "right"].forEach(function (side) {
      [1, 2].forEach(function (slot) {
        var el = document.createElement("div");
        el.className = "scc-duo " + side;
        el.style.left = DUO[side].left + "px";
        el.style.top = DUO.tops[slot - 1] + "px";
        el.innerHTML = '<div class="scc-duo-cam"><div class="scc-duo-logo"><i>DEMO CAM</i></div></div>' +
          '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '"><polygon points="' + ring +
          '" fill="none" stroke="' + GOLD + '" stroke-width="3" stroke-linejoin="miter"/></svg>';
        homes[side].appendChild(el);
        duoBoxes.push({ side: side, slot: slot, el: el, cam: el.querySelector(".scc-duo-cam"), logo: el.querySelector(".scc-duo-logo") });
      });
    });
    return true;
  }

  // Moving a video pauses it.
  function moveVideo(v, to, before) {
    to.insertBefore(v, before || null);
    v.play().catch(function () {});
  }

  function url(path) { return "/" + String(path || "").split("/").map(encodeURIComponent).join("/"); }

  function renderDuo(s, pubs) {
    if (!duoBoxesMade()) return;
    var cfg = s.config, o = s.game.match.observed, demo = (s.app || {}).mode === "demo";
    duoBoxes.forEach(function (b) {
      var player = s.game.players.filter(function (p) { return p.team === b.side && p.slot === b.slot; })[0] || {};
      var cam = pubs.filter(function (p) { return p.player && p.player.team === b.side && p.player.slot === b.slot; })[0];
      var peer = cam && peers[cam.id];
      if (peer && peer.video.parentNode !== b.cam) moveVideo(peer.video, b.cam, b.logo);
      // (a cam no longer this player's goes back with the others)
      Array.prototype.forEach.call(b.cam.querySelectorAll("video"), function (v) {
        if (!peer || v !== peer.video) moveVideo(v, videos);
      });
      var live = !!(peer && peer.video.readyState >= 2);
      if (peer) peer.video.classList.toggle("on", live);
      var art = demo && player.agent
        ? "url('/hud/Resources/Agentes/" + encodeURIComponent(player.agent) + "/" + encodeURIComponent(player.agent) + ".png')"
        : cfg[b.side] && cfg[b.side].logo ? 'url("' + url(cfg[b.side].logo) + '")' : "none";
      if (b.logo.dataset.art !== art) { b.logo.dataset.art = art; b.logo.style.backgroundImage = art; }
      b.logo.classList.toggle("agent", demo && !!player.agent);
      b.logo.style.display = live ? "none" : "";
      b.el.classList.toggle("on", !!o && o.team === b.side && o.slot === b.slot);
    });
  }

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

  // The name and K / D / A fonts: installed fonts chosen in the control
  // panel, served by the app (so they show on any PC), and their sizes.
  var fontKey = "";
  function setFonts(cams) {
    var key = JSON.stringify([cams.name_font, cams.kda_font, cams.name_size, cams.kda_size]);
    if (key === fontKey) return;
    fontKey = key;
    var css = "";
    [["name", cams.name_font], ["kda", cams.kda_font]].forEach(function (f) {
      if (f[1]) css += '@font-face { font-family: "SCC cam ' + f[0] + '"; src: url("/fonts/local/' + encodeURIComponent(f[1]) + '"); }';
    });
    var el = document.getElementById("scc-cam-fonts");
    if (!el) { el = document.createElement("style"); el.id = "scc-cam-fonts"; document.head.appendChild(el); }
    el.textContent = css;
    var name = box.querySelector(".scc-name"), kda = box.querySelector(".scc-kda");
    name.style.fontFamily = cams.name_font ? '"SCC cam name", Arabic, sans-serif' : "";
    kda.style.fontFamily = cams.kda_font ? '"SCC cam kda", Arabic, sans-serif' : "";
    name.style.transform = cams.name_font ? "none" : "";
    kda.style.transform = cams.kda_font ? "none" : "";
    name.style.fontSize = (Number(cams.name_size) || 18) + "px";
    kda.style.fontSize = (Number(cams.kda_size) || 18) + "px";
  }

  // Called by driver.js with each state; hide: the buy-phase scoreboard is up.
  window.renderCams = function (s, hide) {
    var cfg = s.config, m = s.game.match, pubs = (s.cams || {}).publishers || [];
    var on = (cfg.cams || {}).enabled !== false;
    setFonts(cfg.cams || {});
    var wanted = {};
    pubs.forEach(function (p) {
      if (!on) return;
      wanted[p.id] = true;
      var peer = peers[p.id];
      if (peer && peer.pc.connectionState !== "connected" && Date.now() - peer.started > 10000) drop(p.id);
      if (registered && !peers[p.id]) connect(p.id);
    });
    Object.keys(peers).forEach(function (id) { if (!wanted[id]) drop(id); });

    if (Number(cfg.team_size) === 2) {
      box.classList.remove("on");
      return renderDuo(s, on ? pubs : []);
    }
    // (back from 2v2: the cams return to the pop-up box)
    duoBoxes.forEach(function (b) {
      Array.prototype.forEach.call(b.cam.querySelectorAll("video"), function (v) { moveVideo(v, videos); });
    });

    // The spectated player, and their cam if they have one.
    var o = m.observed, player = null, cam = null;
    if (o) {
      player = s.game.players.filter(function (p) { return p.team === o.team && p.slot === o.slot; })[0] || null;
      cam = pubs.filter(function (p) { return p.player && p.player.team === o.team && p.player.slot === o.slot; })[0] || null;
    }
    var peer = cam && peers[cam.id];
    var ready = !!(peer && peer.video.readyState >= 2);
    Object.keys(peers).forEach(function (id) { peers[id].video.classList.toggle("on", !!cam && id === cam.id); });
    // The demo match: everyone has a stand-in cam (so the cam and its
    // kill tag can be seen without real ones).
    var dummy = box.querySelector(".scc-dummy"), fake = (s.app || {}).mode === "demo" && !!player && !ready;
    dummy.classList.toggle("on", fake);
    if (fake && player.agent) {
      var art = "url('/hud/Resources/Agentes/" + encodeURIComponent(player.agent) + "/" + encodeURIComponent(player.agent) + ".png')";
      if (dummy.dataset.agent !== player.agent) {
        dummy.dataset.agent = player.agent;
        dummy.style.backgroundImage = art + ", radial-gradient(circle at 50% 35%, #4a4a58, #23232b 70%)";
        dummy.style.backgroundSize = "auto 92%, cover";
        dummy.style.backgroundPosition = "center bottom, center";
      }
    }
    var show = on && !hide && (ready || fake) && !!player;
    box.classList.toggle("on", show);
    if (!player) return;
    // The bar by the name is in their side's colour (the sides swap at half time).
    var colour = player.team === m.attackers ? cfg.attack_color : cfg.defense_color;
    box.style.setProperty("--team", colour || "#00ffcc");
    box.querySelector(".scc-name").textContent = player.name || "";
    box.querySelector(".scc-kda").textContent = [player.kills, player.deaths, player.assists].map(function (n) { return n || 0; }).join(" / ");
    var kills = player.round_kills || 0, tag = box.querySelector(".scc-kills"), who = player.team + player.slot;
    if (kills > 0) tag.querySelector("span").textContent = kills;
    if (kills > 0 && tag.dataset.who === who && Number(tag.dataset.kills) > 0 && kills > Number(tag.dataset.kills)) {
      tag.classList.remove("pop"); void tag.offsetWidth; tag.classList.add("pop");
    }
    tag.classList.toggle("on", kills > 0);
    tag.dataset.who = who;
    tag.dataset.kills = kills;
  };
})();
