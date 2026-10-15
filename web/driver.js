// Drives the HUD and scoreboard templates (web/hud, web/scoreboard) from the
// app's /api/state, by calling the templates' own Set* functions. Each call is
// only made when its arguments change, so animations aren't restarted.
//
// URL options: ?fit=1 scales the 1920x1080 page to the window (the desktop
// app's HUD-on-the-game window); ?scoreboard=0 leaves out the buy-phase
// scoreboard, which the HUD otherwise carries (for when it's a separate
// browser source).
(function () {
  var SCOREBOARD = location.pathname.indexOf("/scoreboard") === 0;
  var params = new URLSearchParams(location.search);
  var sent = {};

  // Call fn(args...) unless it was last called with the same arguments.
  function call(key, fn, args) {
    var sig = JSON.stringify(args);
    if (sent[key] === sig || typeof fn !== "function") return;
    sent[key] = sig;
    try { fn.apply(null, args); } catch (e) { console.warn(key, e); }
  }

  function setLogos(side, src) {
    var n = side === "left" ? "1" : "2";
    if (sent["logo" + n] === src) return;
    sent["logo" + n] = src;
    var url = "/" + String(src || "").split("/").map(encodeURIComponent).join("/");
    document.querySelectorAll(".logo" + n + ", .logo" + n + "b, .logo" + n + "c").forEach(function (img) {
      img.src = url;
    });
  }

  function shieldCode(p) {
    if (p.regen_shield) return "R";
    return p.shield >= 50 ? "50" : p.shield > 0 ? "25" : "X";
  }

  // Buy phase: the scoreboard shows and the HUD's player panels slide away.
  // Decided from the game's phase (read off the BUY PHASE banner, or the
  // demo's), not the templates' own timers: those flip on every score
  // change, so a page opened mid-round or a misread score left them the
  // wrong way round, and each copy of the page out of step with the others.
  var templateToggle = window.DisplayTeams;
  window.DisplayTeams = function () {};
  var board = { total: null, from: 0, until: 0 };
  function wantBoard(m, cfg) {
    if ((cfg.show || {}).scoreboard) return true;
    if (m.phase === "buy") return true;
    if (m.phase === "combat" || m.phase === "end") return false;
    // Phase unknown (a feed that doesn't say): the templates' timing after a won round.
    var total = (m.score.left || 0) + (m.score.right || 0), now = Date.now();
    if (board.total !== null && total > board.total) { board.from = now + 6600; board.until = now + 34500; }
    board.total = total;
    return now >= board.from && now < board.until;
  }
  function showBoard(on) {
    if (SCOREBOARD) {
      var root = document.documentElement.style;
      root.transition = "opacity 0.5s ease";
      root.opacity = on ? "1" : "0";
    } else {
      var left = document.getElementById("teamIzquierda");
      var hidden = left && left.style.left === "-385px";
      if (left && !!on !== !!hidden && typeof templateToggle === "function") templateToggle();
    }
  }

  var WIN_CODE = { Deactivation: "1", Elimination: "2", Time: "3", Detonation: "4" };

  function applyState(s) {
    var g = s.game, m = g.match, cfg = s.config;
    SCC.state = s;  // SideRound() reads it

    // Teams, logos, score, series.
    call("names", SetNameTeams, [cfg.left.name, cfg.left.tricode, cfg.right.name, cfg.right.tricode]);
    setLogos("left", cfg.left.logo);
    setLogos("right", cfg.right.logo);
    call("round", SetRound, [m.score.left, m.score.right]);
    var need = Math.min(3, Math.ceil((cfg.best_of || 1) / 2));
    var series = JSON.stringify([need, cfg.left.wins, cfg.right.wins]);
    if (sent.series !== series && typeof ModPL === "function") {
      sent.series = series;
      ModMatch = need;
      SetP1 = Math.min(need, cfg.left.wins || 0);
      SetP2 = Math.min(need, cfg.right.wins || 0);
      ModPL(); SetModoP1(); SetModoP2();
    }
    (cfg.maps || []).slice(0, 3).forEach(function (map, i) {
      var label = String(map.name || "").toUpperCase();
      if (map.winner) label += " <span>" + cfg[map.winner].tricode + "</span>";
      else if (i === cfg.current_map) label = "<span>" + label + "</span>";
      call("map" + i, SetMapResult, [i, label]);
    });

    // Players: team 0 is the left panel, team 1 the right; slots 1-5.
    g.players.forEach(function (p) {
      var t = p.team === "left" ? 0 : 1, i = p.slot, k = "p" + t + i + ":";
      call(k + "name", SetNamePlayer, [t, i, p.name]);
      call(k + "agent", SetPlayerAgent, [t, i, p.agent || ""]);
      if (p.weapon) call(k + "weapon", SetPlayerWeapon, [t, i, p.weapon, "contain"]);
      else if (sent[k + "weapon"] !== "[]") {
        // No gun (an empty loadout on the scoreboard): clear the old one.
        sent[k + "weapon"] = "[]";
        var gun = document.querySelector(t === 0 ? ".TIP" + i + " > div.Weapon1" : ".TDP" + i + " > div.Weapon2");
        if (gun) gun.style.backgroundImage = "none";
      }
      call(k + "shield", SetPlayerShield, [t, i, shieldCode(p)]);
      call(k + "hp", SetPlayerHP, [t, i, p.alive ? Math.max(1, p.health) : 0]);
      call(k + "kda", SetPlayerKDA, [t, i, p.kills, p.deaths, p.assists]);
      call(k + "creds", SetPlayerCreds, [t, i, p.credits]);
      var max = Math.max(6, Math.min(9, p.ult_max || 7));
      call(k + "ult", SetUltiPoints, [t, i, Math.min(p.ult_points, max), max]);
      call(k + "ultready", SetUltiActive, [t, i, p.ult_points >= max ? 1 : 0]);
      ["C", "Q", "E"].forEach(function (key, n) {
        var a = (p.abilities || {})[key] || [0, 1];
        call(k + "skill" + n, SetSkillsPoints, [t, n, i, Math.min(3, a[0]), Math.min(3, Math.max(1, a[1]))]);
      });
    });

    if (SCOREBOARD) {
      // Round history: per team, a code per round (0 = lost).
      var codes = { left: [], right: [] };
      (m.rounds || []).forEach(function (r) {
        codes.left.push(r.winner === "left" ? WIN_CODE[r.win_type] || "2" : "0");
        codes.right.push(r.winner === "right" ? WIN_CODE[r.win_type] || "2" : "0");
      });
      call("rounds", RoundTeams, [codes.left.join("|"), codes.right.join("|")]);
      showBoard(wantBoard(m, cfg));
      return;
    }

    // The spike: planted animation, and who's carrying it.
    var planted = m.spike.state === "planted";
    call("planted", SlideSpike, [planted]);
    var carrier = m.spike.carrier;
    if (m.spike.state === "carried" && carrier && m.phase !== "end") {
      call("spiketeam", SpikeTeam, [carrier[0] === "left" ? 0 : 1]);
      call("spikeplayer", SpikePlayer, [carrier[1]]);
    } else {
      call("spikeplayer", SpikePlayer, [0]);
    }

    // Timeouts left (2 diamonds a side), timeout cards and technical pause.
    var to = cfg.timeouts || {};
    var dots = function (n) { return n >= 2 ? "11" : n === 1 ? "10" : "00"; };
    call("timeouts", ShowTimeOutPoints, [(cfg.show || {}).timeouts !== false, dots(to.left) + dots(to.right)]);
    call("deftimeout", DefTimeOut, [cfg.timeout_call === "left"]);
    call("atttimeout", AttTimeOut, [cfg.timeout_call === "right"]);
    call("techpause", TechnicalPause, [!!cfg.tech_pause]);
    showBoard(wantBoard(m, cfg));
  }

  function poll() {
    fetch("/api/state", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(applyState)
      .catch(function () {})
      .then(function () { setTimeout(poll, 250); });
  }

  // The buy-phase scoreboard is its own page (web/scoreboard): it shows
  // itself after each round and hides for the next one. The HUD carries it,
  // so the HUD window (and a single browser source) has it too.
  if (!SCOREBOARD && params.get("scoreboard") !== "0") {
    var board = document.createElement("iframe");
    board.src = "/scoreboard";
    board.title = "Scoreboard";
    board.setAttribute("scrolling", "no");
    Object.assign(board.style, { position: "absolute", left: "0", top: "0", width: "1920px", height: "1080px",
                                 border: "0", background: "transparent", pointerEvents: "none", zIndex: "50" });
    (document.body || document.documentElement).appendChild(board);
  }

  if (params.get("fit") === "1") {
    // Scale with the screen's height, centred, like the game's own HUD.
    // The template paints its top bar as the page background, which a
    // transform doesn't scale; keep that background on a 1920x1080 body
    // (an almost-invisible page background stops it moving to the page).
    document.documentElement.style.background = "rgba(0,0,0,0.004)";
    Object.assign(document.body.style, { width: "1920px", height: "1080px", margin: "0", position: "relative" });
    var fit = function () {
      var k = Math.min(innerHeight / 1080, innerWidth / 1920);
      var root = document.documentElement.style;
      root.transformOrigin = "0 0";
      root.transform = "translateX(" + (innerWidth - 1920 * k) / 2 + "px) scale(" + k + ")";
    };
    addEventListener("resize", fit);
    fit();
  }
  poll();
})();
