// Drives the PRO Selector agent select template (this folder) from the app's
// /api/state, through the template's own Set* functions: team names and
// logos, which side defends, the map, and each player's agent. An agent
// being hovered shows as a silhouette; it fills in when locked.
//
// The page slides up when agent select starts and back down when it ends.
// ?fit=1 scales it to the window; ?always=1 keeps it up (for setting up).
(function () {
  var params = new URLSearchParams(location.search);
  var sent = {};
  function call(key, fn, args) {
    var sig = JSON.stringify(args);
    if (sent[key] === sig || typeof fn !== "function") return;
    sent[key] = sig;
    try { fn.apply(null, args); } catch (e) { console.warn(key, e); }
  }
  function url(p) { return "/" + String(p || "").split("/").map(encodeURIComponent).join("/"); }

  // (Unique class names: in the template's quirks mode classes match
  // without regard to case, so ".hover" would also hit a ".Hover".)
  var css = document.createElement("style");
  css.textContent =
    // A flat, light silhouette (the cards are dark), with a soft glow.
    ".scc-silhouette > .Icon { filter: brightness(0) invert(1) opacity(.32) drop-shadow(0 0 12px rgba(255,255,255,.35)); }" +
    ".TIP1 > .Icon, .TIP2 > .Icon, .TIP3 > .Icon, .TIP4 > .Icon, .TIP5 > .Icon," +
    ".TDP1 > .Icon, .TDP2 > .Icon, .TDP3 > .Icon, .TDP4 > .Icon, .TDP5 > .Icon { transition: filter .45s ease; }" +
    ".scc-silhouette .Agent, .scc-silhouette .Agent2 { opacity: .75; }" +
    "html { transition: transform .7s cubic-bezier(.2,.8,.2,1), opacity .4s ease; }" +
    "html.scc-off { transform: translateY(460px); opacity: 0; transition: transform .6s cubic-bezier(.6,0,.8,.4), opacity .5s ease .2s; }";
  document.head.appendChild(css);

  function setLogos(side, src) {
    var n = side === "left" ? "1" : "2";
    if (sent["logo" + n] === src) return;
    sent["logo" + n] = src;
    document.querySelectorAll(".logo" + n + ", .logo" + n + "b").forEach(function (img) { img.src = url(src); });
  }

  // Sponsors (under the map): the logos saved in the control panel, in turn
  // (the template's own until some are saved).
  var sponsor = { key: "", i: 0, timer: null };
  function setSponsors(list, seconds) {
    var box = document.querySelector(".LogoSponsor");
    if (!box || !list || !list.length) return;
    var key = JSON.stringify([list, seconds]);
    if (key === sponsor.key) return;
    sponsor.key = key;
    clearInterval(sponsor.timer);
    var next = function () { box.style.backgroundImage = 'url("' + url(list[sponsor.i++ % list.length]) + '")'; };
    next();
    if (list.length > 1) sponsor.timer = setInterval(next, Math.max(1, Number(seconds) || 4) * 1000);
  }

  // Player names shrink until the whole name fits on its card (the
  // template's name box is widened to the card, keeping its edge).
  var BASE = 18, MIN = 9, WIDTH = 140;
  function fitName(t, slot, text) {
    var el = document.querySelector(t === 0 ? ".TIP" + slot + " > div.Name" : ".TDP" + slot + " > div.Name2");
    if (!el || (el.dataset.text === text && el.dataset.fitted)) return;
    el.dataset.text = text;
    el.style.whiteSpace = "nowrap";
    el.style.overflow = "hidden";
    el.style.width = WIDTH + "px";
    if (t === 1) el.style.left = (67 + 96 - WIDTH) + "px";   // right-aligned: same right edge
    shrink(el, BASE, MIN);
  }
  function shrink(el, base, min) {
    var size = base;
    el.style.fontSize = size + "px";
    while (el.scrollWidth > el.clientWidth + 0.5 && size > min) el.style.fontSize = (size -= 1) + "px";
    el.dataset.fitted = document.fonts.status === "loaded" ? "1" : "";
  }
  // Team names: one line, shrunk to fit (the template wraps them onto the cards).
  function fitTeams(left, right) {
    [[".Team1b", left], [".Team2b", right]].forEach(function (t) {
      var el = document.querySelector(t[0]);
      if (!el || (el.dataset.text === t[1] && el.dataset.fitted)) return;
      el.dataset.text = t[1];
      el.style.whiteSpace = "nowrap";
      el.style.overflow = "hidden";
      // A smaller name stays centred on the full-size one's line.
      el.style.transform = "";
      el.style.fontSize = "55px";
      var r = el.getBoundingClientRect(), mid = r.top + r.height / 2;
      shrink(el, 55, 26);
      r = el.getBoundingClientRect();
      el.style.transform = "translateY(" + (mid - (r.top + r.height / 2)) + "px)";
    });
  }
  if (document.fonts) document.fonts.ready.then(function () {
    document.querySelectorAll("[data-text]").forEach(function (el) { el.dataset.fitted = ""; });
  });

  function apply(s) {
    var a = s.agent_select || {}, cfg = s.config;
    document.documentElement.classList.toggle("scc-off", !a.active && params.get("always") !== "1");

    call("names", SetNameTeams, [cfg.left.name, cfg.left.tricode, cfg.right.name, cfg.right.tricode]);
    fitTeams(cfg.left.name, cfg.right.name);
    setLogos("left", cfg.left.logo);
    setLogos("right", cfg.right.logo);
    setSponsors(cfg.sponsors, cfg.sponsor_seconds);

    // DEF vs ATK (HUD-1) or ATK vs DEF (HUD-ATK, the labels swapped): who
    // attacks first this map.
    var leftAttacks = (cfg.attack_first || "left") === "left";
    var bg = 'url("Resources/' + (leftAttacks ? "HUD-ATK" : "HUD-1") + '.png")';
    if (document.body.style.backgroundImage !== bg) document.body.style.backgroundImage = bg;

    // The map: the HUD's map art, and its name.
    var map = a.map || "";
    if (sent.map !== map) {
      sent.map = map;
      var tile = document.querySelector(".LogoMap"), label = document.querySelector(".LogoMap > div");
      if (tile) tile.style.backgroundImage = map ? 'url("/hud/Resources/Maps/' + map + '.png")' : "none";
      if (label) label.innerText = map;
    }

    ["left", "right"].forEach(function (side, t) {
      ((a.players || {})[side] || []).forEach(function (p, i) {
        var slot = i + 1, k = side + slot;
        call(k + "name", SetNamePlayer, [t, slot, p.name || ""]);
        fitName(t, slot, p.name || "");
        call(k + "agent", SetPlayerAgent, [t, slot, p.agent || ""]);
        var card = document.querySelector((t === 0 ? ".TIP" : ".TDP") + slot);
        if (card) card.classList.toggle("scc-silhouette", !!p.agent && !p.locked);
      });
    });
  }

  function poll() {
    fetch("/api/state", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(apply)
      .catch(function () {})
      .then(function () { setTimeout(poll, 250); });
  }

  if (params.get("fit") === "1") {
    document.documentElement.style.background = "rgba(0,0,0,0.004)";
    Object.assign(document.body.style, { width: "1920px", height: "1080px", margin: "0", position: "relative" });
    var fit = function () {
      var k = Math.min(innerHeight / 1080, innerWidth / 1920);
      document.body.style.transformOrigin = "0 0";
      document.body.style.transform = "translateX(" + (innerWidth - 1920 * k) / 2 + "px) scale(" + k + ")";
    };
    addEventListener("resize", fit);
    fit();
  }
  poll();
})();
