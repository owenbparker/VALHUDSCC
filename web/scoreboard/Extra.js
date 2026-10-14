//-------------------------------------------------------------------------------------------
//--------------------------------MAIN VARIABLES AND CONSTANTS-------------------------------
//--Team Colors
var Team1Color = '#00ffcc';
var Team2Color = '#ff4e5d';
//--Team Scores
var scoreElement1 = document.querySelector('.Score1');
var scoreElement2 = document.querySelector('.Score2');
//--Define Logos Elements
var logoImage1 = document.querySelector('.logo1b');
var logoImage2 = document.querySelector('.logo2b');
logoImage1.src = document.querySelector('.logo1').src;
logoImage2.src = document.querySelector('.logo2').src;
//--AutoScoreboard
const AutoScoreboardEnable = true;

//-------------------------------------------------------------------------------------------
//-------------------------------------KDA ORDER---------------------------------------------

function changeKDA() {
  var TIPs = document.getElementsByClassName("TeamIzquierda")[0].children;
  var kills = [];
  for (var i = 0; i < TIPs.length; i++) {
    var k1 = TIPs[i].getElementsByClassName("K1")[0].innerHTML;
	var d1 = TIPs[i].getElementsByClassName("D1")[0].innerHTML;
	var a1 = TIPs[i].getElementsByClassName("A1")[0].innerHTML;
    var kda1 = [k1,d1,a1];
	var kill = parseInt(kda1[0]);
    kills.push(kill);
  }
  var indices = [];
  for (var i = 0; i < kills.length; i++) {
    indices.push(i);
  }
  indices.sort(function(a, b) {
    return kills[b] - kills[a];
  });
  var tops = [788, 843, 900, 955, 1012];
  for (var i = 0; i < indices.length; i++) {
    var j = indices[i];
    TIPs[j].style.top = tops[i] + "px";
  }
}
function changeKDA2() {
  var TDPs = document.getElementsByClassName("TeamDerecha")[0].children;
  var kills = [];
  for (var i = 0; i < TDPs.length; i++) {
    var k2 = TDPs[i].getElementsByClassName("K2")[0].innerHTML;
	var d2 = TDPs[i].getElementsByClassName("D2")[0].innerHTML;
	var a2 = TDPs[i].getElementsByClassName("A2")[0].innerHTML;
    var kda2 = [k2,d2,a2];
    var kill = parseInt(kda2[0]);
    kills.push(kill);
  }
  var indices = [];
  for (var i = 0; i < kills.length; i++) {
    indices.push(i);
  }
  indices.sort(function(a, b) {
    return kills[b] - kills[a];
  });
  var tops = [788, 843, 900, 955, 1012];
  for (var i = 0; i < indices.length; i++) {
    var j = indices[i];
    TDPs[j].style.top = tops[i] + "px";
  }
}
var intervalo = setInterval(function() {
   changeKDA();
   changeKDA2();
},1000);

//-------------------------------------------------------------------------------------------
//----------------------------------ROUND ANIMATION FUNCTIONS--------------------------------

var SetP1 = 0; var SetP2 = 0; var ModMatch = 0;
function MatchPlus(){ModMatch=ModMatch+1;if (ModMatch>3){ModMatch=3;}ModPL();}
function MatchMinus(){ModMatch= ModMatch-1;if (ModMatch<0){ModMatch=0;}if (SetP1>ModMatch){SetP1=ModMatch;}if (SetP2>ModMatch){SetP2=ModMatch;}ModPL();SetModoP1();SetModoP2();}
function SetP1Plus(){SetP1 = SetP1+1;if (SetP1>ModMatch){SetP1=ModMatch;}SetModoP1();}
function SetP1Minus(){SetP1 = SetP1-1;if (SetP1<0){SetP1=0;}SetModoP1();}
function SetP2Plus(){SetP2 = SetP2+1;if (SetP2>ModMatch){SetP2=ModMatch;}SetModoP2();}
function SetP2Minus(){SetP2 = SetP2-1;if (SetP2<0){SetP2=0;}SetModoP2();}

function ModPL(){
    switch (ModMatch){
    case 0:
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.visibility="hidden"
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.visibility="hidden"
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.visibility="hidden"
    break;
    case 1:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.visibility="hidden"
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.visibility="hidden"
    break;
    case 2:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.visibility="visible"
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.visibility="hidden"
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.visibility="hidden"
    break;
    case 3:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.visibility="visible"
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.visibility="visible"
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.visibility="visible"
    break;	
}}

function SetModoP1(){
switch (SetP1){
    case 0:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 1:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 2:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.backgroundColor='white';
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 3:
    document.querySelector("#rombo-container1 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container1 > div:nth-child(2)").style.backgroundColor='white';
    document.querySelector("#rombo-container1 > div:nth-child(1)").style.backgroundColor='white';
    break;	
}
}

function SetModoP2(){
switch (SetP2){
    case 0:
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 1:
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.backgroundColor='transparent';
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 2:
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.backgroundColor='white';
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.backgroundColor='transparent';
    break;
    case 3:
    document.querySelector("#rombo-container2 > div:nth-child(3)").style.backgroundColor='white';
    document.querySelector("#rombo-container2 > div:nth-child(2)").style.backgroundColor='white';
    document.querySelector("#rombo-container2 > div:nth-child(1)").style.backgroundColor='white';
    break;	
}
}

//-------------------------------------------------------------------------------------------
//--------------------------------PLAYER ANIMATION FUNCTIONS---------------------------------

  function hideElements(element) {

  const PUlti = element.querySelector('.Skill4');
  if (PUlti){
	  PUlti.style.opacity = '0.5';
  }
  const ulticontainer1 = element.querySelector('.ulti-container1');
  if (ulticontainer1) {
    ulticontainer1.style.opacity = '0';
  }
  const ulticontainer2 = element.querySelector('.ulti-container2');
  if (ulticontainer2) {
    ulticontainer2.style.opacity = '0';
  }  
  const rectanglegray = element.querySelector('.rectangle-gray');
  if (rectanglegray) {
    rectanglegray.style.display = 'none';
  }
  const rectangleblack = element.querySelector('.rectangle-black');
  if (rectangleblack) {
    rectangleblack.style.display = 'none';
  }
}

function showElements(element) {

  const PUlti = element.querySelector('.Skill4');
  if (PUlti){
	  PUlti.style.opacity = '1';
  }
  const ulticontainer1 = element.querySelector('.ulti-container1');
  if (ulticontainer1) {
  ulticontainer1.style.opacity = '1';
  }  
  const ulticontainer2 = element.querySelector('.ulti-container2');
  if (ulticontainer2) {
  ulticontainer2.style.opacity = '1';
  }  
  const rectanguloGris = element.querySelector('.rectangle-gray');
  if (rectanguloGris) {
    rectanguloGris.style.display = 'block';
  }
  const rectanguloNegro = element.querySelector('.rectangle-black');
  if (rectanguloNegro) {
    rectanguloNegro.style.display = 'block';
  }
}

//-------------------------------------------------------------------------------------------
//----------------------------------ROUND ANIMATION FUNCTIONS--------------------------------

function ChangeColorScore() {
  const score1 = parseInt(document.querySelector('.Score1').innerText)
  const score2 = parseInt(document.querySelector('.Score2').innerText)
  const Icon1 = document.querySelectorAll(".Icon.iconb1");
  const Icon2 = document.querySelectorAll(".Icon.iconb2");
  
  if (!isNaN(score1) && !isNaN(score2)) {
      const resultado = SideRound(score1 + score2 + 1);  // SCC: which half's colours (see driver-pre.js)
  document.getElementById('resultado').innerText = 'ROUND ' + (score1 + score2 + 1);

  if (resultado < 13) {
          setTimeout(() => {
              document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
			  document.querySelector(".Score1").style.color = '#00ffc6';
			  document.querySelector(".Score2").style.color = '#ff4d5e';
			  Team1Color = '#00ffcc';
			  Team2Color = '#ff4e5d';
			  for (var i=0; i<5; i++){
				document.querySelectorAll(".Skill4")[i].style.backgroundColor='#313236a6';
				document.querySelectorAll(".Skill4.SR")[i].style.backgroundColor='#313236a6';
			  }
          }, 0);
      }

      if (resultado >= 13 && resultado < 25) {
          setTimeout(() => {
              document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
			  document.querySelector(".Score2").style.color = '#00ffc6';
			  document.querySelector(".Score1").style.color = '#ff4d5e';
			  Team2Color = '#00ffcc';
			  Team1Color = '#ff4e5d';
			  for (var i=0; i<5; i++){
				document.querySelectorAll(".Skill4.SR")[i].style.backgroundColor='#313236a6';
				document.querySelectorAll(".Skill4")[i].style.backgroundColor='#313236a6';
			  }
          }, 0);
      }

      if (resultado == 25) {
          setTimeout(() => {
              document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
			  document.querySelector(".Score1").style.color = '#00ffc6';
			  document.querySelector(".Score2").style.color = '#ff4d5e';
			  Team1Color = '#00ffcc';
			  Team2Color = '#ff4e5d';
			  for (var i=0; i<5; i++){
				document.querySelectorAll(".Skill4")[i].style.backgroundColor='#313236a6';
				document.querySelectorAll(".Skill4.SR")[i].style.backgroundColor='#313236a6';
			  }
          }, 0);
      }

      if (resultado >= 26) {
          setTimeout(() => {
              if (resultado % 2 === 0) {
                  document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
				  document.querySelector(".Score2").style.color = '#00ffc6';
				  document.querySelector(".Score1").style.color = '#ff4d5e';
				  Team2Color = '#00ffcc';
				  Team1Color = '#ff4e5d';
			   for (var i=0; i<5; i++){
				document.querySelectorAll(".Skill4.SR")[i].style.backgroundColor='#313236a6';
				document.querySelectorAll(".Skill4")[i].style.backgroundColor='#313236a6';
			   }
        //SpikeTeam(0);
              } else {
                  document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
				  document.querySelector(".Score1").style.color = '#00ffc6';
				  document.querySelector(".Score2").style.color = '#ff4d5e';
				  Team1Color = '#00ffcc';
				  Team2Color = '#ff4e5d';
			  for (var i=0; i<5; i++){
				document.querySelectorAll(".Skill4")[i].style.backgroundColor='#313236a6';
				document.querySelectorAll(".Skill4.SR")[i].style.backgroundColor='#313236a6';
			  }
        //SpikeTeam(1);
              }

          }, 0);
      }
  } else {
      const resultadoElement = document.getElementById('resultado');
      resultadoElement.textContent = 'ROUND';
  }
}

//-------------------------------------------------------------------------------------------
//-------------------------------------BANNER FUNCTIONS--------------------------------------

function AutoScoreboard() {
  if (AutoScoreboardEnable){
	setTimeout(function () { DisplayTeams(); }, 6600);
	setTimeout(function () { DisplayTeams(); }, 34500);  
  }
}

function DisplayBanner(elementoScore1, elementoScore2) {
  var lastValue1 = parseInt(elementoScore1.innerText);
  var lastValue2 = parseInt(elementoScore2.innerText);

  var observer1 = new MutationObserver(function () {
    var newValue1 = parseInt(elementoScore1.innerText);

    if (newValue1 !== lastValue1) {
      if (newValue1 > lastValue1) {
        AutoScoreboard();
      }
      lastValue1 = newValue1;
    }
  });

  var observer2 = new MutationObserver(function () {
    var newValue2 = parseInt(elementoScore2.innerText);

    if (newValue2 !== lastValue2) {
      if (newValue2 > lastValue2) {
        AutoScoreboard();
      }
      lastValue2 = newValue2;
    }
  });

  observer1.observe(elementoScore1, { childList: true, subtree: true });
  observer2.observe(elementoScore2, { childList: true, subtree: true });
}

if (AutoScoreboardEnable){
	document.querySelector("html").style.opacity='0';
}

function DisplayTeams() {
	if (!AutoScoreboardEnable){return;}
	document.querySelector("html").style.transition= "opacity 0.5s ease";
	
	if (document.querySelector("html").style.opacity=='0'){
		document.querySelector("html").style.opacity='1';
	}else{
		document.querySelector("html").style.opacity='0';
	}
}

function SwitchButton() {}

//-------------------------------------------------------------------------------------------
//-------------------------------------------------------------------------------------------

setInterval(ChangeColorScore, 1000);
DisplayBanner(scoreElement1, scoreElement2);
ChangeColorScore();

Scoreboard();