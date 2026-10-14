// Runs inside the HUD and scoreboard templates, just before their own scripts.
//
// The templates fire their round-win banner whenever a score goes up, so the
// scores are filled in here first (synchronously), before the templates start
// watching them; otherwise every reload would play a banner.
//
// It also defines SideRound(), which the templates' colour logic calls (see
// the "SCC:" lines in Extra.js): they assumed the left team defends first.
var SCC = { state: null };
try {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/api/state", false);
  xhr.send();
  SCC.state = JSON.parse(xhr.responseText);
} catch (e) {}

if (SCC.state) {
  var m = SCC.state.game.match;
  document.querySelector(".Score1").innerText = m.score.left;
  document.querySelector(".Score2").innerText = m.score.right;
}

// The templates colour the left team teal (defending) for "rounds" 1-12 and
// red (attacking) for 13-24. Answer with a round that gives the right side.
function SideRound(round) {
  var m = SCC.state && SCC.state.game.match;
  if (!m || !SCC.state.game.connected) return round;
  return m.attackers === "left" ? 13 : 1;
}

(function () {
  var css = document.createElement("style");
  css.textContent = "h4.Information { display: none; }";
  document.head.appendChild(css);
})();
