//--Spike Pictures
const slidingImage = document.getElementById('slidingImage');
const backgroundBomb = document.getElementById('background-bomb');
const portador = document.querySelector('.portador');
//--Team Colors
var Team1Color = '#313236';
var Team2Color = '#313236';
//--Team Scores
var scoreElement1 = document.querySelector('.Score1');
var scoreElement2 = document.querySelector('.Score2');
//--Banner Element
var bannerImage1 = document.querySelector('.banner1');
//--Define Logos Elements
var logoImage1 = document.querySelector('.logo1b');
var logoImage2 = document.querySelector('.logo2b');
logoImage1.src = document.querySelector('.logo1').src;
logoImage2.src = document.querySelector('.logo2').src;

//--Match Points
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
  
//---Round Count + Change Team Colors

  function ChangeColorScore() {
    const score1 = parseInt(document.querySelector('.Score1').innerText)
    const score2 = parseInt(document.querySelector('.Score2').innerText)
	const HP1Elements = document.querySelectorAll('.TeamIzquierda .HP1');
    const HP2Elements = document.querySelectorAll('.TeamDerecha .HP2');

    if (!isNaN(score1) && !isNaN(score2)) {
        const resultado = score1 + score2 + 1;
		document.getElementById('resultado').innerText = 'ROUND ' + resultado;

		if (resultado < 13) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
				//SpikeTeam(1);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#00ffca';}
				Team1Color = '#313236';
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#ff4e5e';}
				Team2Color = '#313236';
            }, 7000);
        }


        if (resultado === 13) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
				//SpikeTeam(0);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#ff4e5e';}
				Team1Color = '#313236';
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#00ffca';}
				Team2Color = '#313236';
            }, 7000);
        }

        if (resultado === 25) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
				//SpikeTeam(1);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#00ffca';}
				Team1Color = '#313236';
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#ff4e5e';}
				Team2Color = '#313236';
            }, 7000);
        }

        if (resultado >= 26) {
            setTimeout(() => {
                if (resultado % 2 === 0) {
                    document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
					//SpikeTeam(0);
                } else {
                    document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
					//SpikeTeam(1);
                }

				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = resultado % 2 === 0 ? '#ff4e5e' : '#00ffca';}
				Team1Color = resultado % 2 === 0 ? '#313236' : '#313236';
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = resultado % 2 === 0 ? '#00ffca' : '#ff4e5e';}
				Team2Color = resultado % 2 === 0 ? '#313236' : '#313236';
				
            }, 7000);
        }
    } else {
        const resultadoElement = document.getElementById('resultado');
        resultadoElement.textContent = 'ROUND';
    }
}
// SCC: the sides come from the app (select.js), not the score.
// setInterval(ChangeColorScore, 1000);
// ChangeColorScore();

//--Players without HP

function applyWithoutHP1(element, T1C) {
  const iconElement = element.querySelector('.Icon');
  const rTeam1 =  element.querySelector(".rectangle-Team1");
  const widthNumeric = parseInt(element.querySelector('.HP1').clientWidth);

  if (widthNumeric === 0) {
	//iconElement.style.filter = 'grayscale(100%)';
    //rTeam1.style.filter = 'grayscale(100%)';
    rTeam1.style.background = 'linear-gradient(to left, transparent, #000000)';
    rTeam1.style.opacity = 1;
    rTeam1.style.width = 230;
    hideElements(element);
  } else {
	iconElement.style.filter = 'none';
    rTeam1.style.filter = 'none';
	rTeam1.style.filter = 'none';
    rTeam1.style.background = T1C;
    rTeam1.style.opacity = 1;
    rTeam1.style.width = 315;
    showElements(element);
  }
}

function applyWithoutHP2(element, T2C) {
  const iconElement = element.querySelector('.Icon');
  const rTeam2 =  element.querySelector(".rectangle-Team2");
  const widthNumeric = parseInt(element.querySelector('.HP2').clientWidth);

  if (widthNumeric === 0) {
    //iconElement.style.filter = 'grayscale(100%)';
    //rTeam2.style.filter = 'grayscale(100%)';
    rTeam2.style.background = 'linear-gradient(to left, transparent, #000000)';
    rTeam2.style.opacity = 1;
    rTeam2.style.width = 230;
    hideElements(element);
  } else {
    iconElement.style.filter = 'none';
    rTeam2.style.filter = 'none';
    rTeam2.style.background = T2C;
    rTeam2.style.opacity = 1;
    rTeam2.style.width = 315;
    showElements(element);
  }
}

function hideElements(element) {
  const elementsToHide = element.querySelectorAll('.Shield, .SP1, .Weapon1, .Weapon2, .Skill1, .Skill2, .Skill3');
  elementsToHide.forEach((el) => {
    el.classList.add('fade-out');
  });
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
  const elementsToShow = element.querySelectorAll('.Shield, .SP1, .Weapon1, .Weapon2, .Skill1, .Skill2, .Skill3');
  elementsToShow.forEach((el) => {
    el.classList.remove('fade-out');
    el.style.display = 'block';
  });
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

function TrackingHP() {
  const tipElements = document.querySelectorAll('.TIP1, .TIP2, .TIP3, .TIP4, .TIP5');
  tipElements.forEach((tipElement) => {
    applyWithoutHP1(tipElement,Team1Color);
  });

  const tdpElements = document.querySelectorAll('.TDP1, .TDP2, .TDP3, .TDP4, .TDP5');
  tdpElements.forEach((tdpElement) => {
    applyWithoutHP2(tdpElement,Team2Color);
  });
}

setInterval(TrackingHP, 50);

//-----Ulti Points

function UltiPoints(PlayerID, TeamID, SP, LP){
	switch (TeamID){
		case 0:
			SetUC = document.querySelectorAll(".ulti-container1")[PlayerID];
			for (var i = 1; i <= 9; i++){
				if (i <= LP){
					SetUC.querySelectorAll(".UP1")[i-1].style.display = 'inline-flex';}	
				else{
					SetUC.querySelectorAll(".UP1")[i-1].style.display = 'none';}	
				
				if (i <= SP){
					SetUC.querySelectorAll(".UP1")[i-1].style.backgroundColor = 'white';}
				else{
					SetUC.querySelectorAll(".UP1")[i-1].style.backgroundColor = 'black';}
			}
		break;
		case 1:
			SetUC = document.querySelectorAll(".ulti-container2")[PlayerID];
			for (var i = 1; i <= 9; i++){
				if (i <= LP){
					SetUC.querySelectorAll(".UP2")[i-1].style.display = 'inline-flex';}	
				else{
					SetUC.querySelectorAll(".UP2")[i-1].style.display = 'none';}	
				
				if (i <= SP){
					SetUC.querySelectorAll(".UP2")[i-1].style.backgroundColor = 'white';}
				else{
					SetUC.querySelectorAll(".UP2")[i-1].style.backgroundColor = 'black';}
			}
		break;		
	}
}

//-----Display Banner

function DisplayBanner(elementoScore1, elementoScore2, elementoBanner1, elementoLogo1, elementoLogo2) {
  var lastValue1 = parseInt(elementoScore1.innerText);
  var lastValue2 = parseInt(elementoScore2.innerText);

  var observer1 = new MutationObserver(function () {
    var newValue1 = parseInt(elementoScore1.innerText);

    if (newValue1 > lastValue1) {
      elementoBanner1.style.opacity = '1';
      elementoLogo1.style.opacity = '1';

      setTimeout(function () {
        elementoBanner1.style.opacity = '0';
        elementoLogo1.style.opacity = '0';
      }, 5000);
    }

    lastValue1 = newValue1;
  });

  var observer2 = new MutationObserver(function () {
  var newValue2 = parseInt(elementoScore2.innerText);

    if (newValue2 > lastValue2) {
      elementoLogo2.style.opacity = '1';
      elementoBanner1.style.opacity = '1';

      setTimeout(function () {
        elementoLogo2.style.opacity = '0';
        elementoBanner1.style.opacity = '0';
      }, 5000);
    }

    lastValue2 = newValue2;
  });

  observer1.observe(elementoScore1, { childList: true, subtree: true });
  observer2.observe(elementoScore2, { childList: true, subtree: true });
}

//-----Display Teams

function DisplayTeams() {
	return;
  var teamIzquierda = document.getElementById('teamIzquierda');
  var teamDerecha = document.getElementById('teamDerecha');

  if (teamIzquierda.style.left === '-385px') {
      teamIzquierda.style.left = '0px';
      teamDerecha.style.left = '-3px';
      teamIzquierda.style.opacity = '1';
      teamDerecha.style.opacity = '1';
      portador.style.opacity = '1';

  } else {
      teamIzquierda.style.left = '-385px';
      teamDerecha.style.left = '330px';
      setTimeout(() => teamIzquierda.style.opacity = '0', 600);
      setTimeout(() => teamDerecha.style.opacity = '0', 600);
      portador.style.opacity = '0';
  }
}

//-------------------------------------------------------------------------------
//-------------------------------AGENT ANIMATION---------------------------------

var imageIPath = Array(9).fill('');
const iconElements = document.querySelectorAll('.Icon');
function pjanimation(pjtarget){
	pjtarget.style.display='none';
    pjtarget.style.animation='none';
    setTimeout(function(){pjtarget.style.display='block';pjtarget.style.animation='changeIcon 1s forwards';},100);
}

function readpjpath(){
    for (let i = 0; i < iconElements.length; i++){
        if (imageIPath[i] != iconElements[i].style.backgroundImage){
            pjanimation(iconElements[i]);
			try{
			xName = iconElements[i].style.backgroundImage;
			iconElements[i].children[0].innerText=xName.substr(xName.indexOf("/Agentes/")+("/Agentes/").length,xName.lastIndexOf("/")-xName.indexOf("/Agentes/")-("/Agentes/").length);
			}catch{}
        }
    }
    for (let i = 0; i < iconElements.length; i++){
    imageIPath[i] = iconElements[i].style.backgroundImage;
    }
}

//-------------------------------------------------------------------------------
//---------------------------------MAP ANIMATION---------------------------------

function refreshmap(){
	if (document.querySelector('.Map1').childElementCount != 3 && document.querySelector('.Map2').childElementCount != 3 && document.querySelector('.Map3').childElementCount != 3) {
			readmap(".Map1");
			return;
	}
	
	if (document.querySelector('.Map1').childElementCount == 3 && document.querySelector('.Map2').childElementCount != 3 && document.querySelector('.Map3').childElementCount != 3) {
			readmap(".Map2");
			return;
	}
	
	if (document.querySelector('.Map1').childElementCount == 3 && document.querySelector('.Map2').childElementCount == 3 && document.querySelector('.Map3').childElementCount != 3) {
			readmap(".Map3");
			return;
	}
}

function readmap(elementMap){
	//Ascent
	if (document.querySelector(elementMap).innerText.indexOf("ASCENT") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Ascent.png')";
		document.querySelector(".LogoMap > div").innerText="Ascent";
	}
	//Bind
	if (document.querySelector(elementMap).innerText.indexOf("BIND") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Bind.png')";
		document.querySelector(".LogoMap > div").innerText="Bind";
	}
	//Breeze
	if (document.querySelector(elementMap).innerText.indexOf("BREEZE") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Breeze.png')";
		document.querySelector(".LogoMap > div").innerText="Breeze";
	}
	//Fracture
	if (document.querySelector(elementMap).innerText.indexOf("FRACTURE") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Fracture.png')";
		document.querySelector(".LogoMap > div").innerText="Fracture";
	}
	//Haven
	if (document.querySelector(elementMap).innerText.indexOf("HAVEN") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Haven.png')";
		document.querySelector(".LogoMap > div").innerText="Haven";
	}
	//Icebox
	if (document.querySelector(elementMap).innerText.indexOf("ICEBOX") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Icebox.png')";
		document.querySelector(".LogoMap > div").innerText="Icebox";
	}
	//Lotus
	if (document.querySelector(elementMap).innerText.indexOf("LOTUS") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Lotus.png')";
		document.querySelector(".LogoMap > div").innerText="Lotus";
	}
	//Pearl
	if (document.querySelector(elementMap).innerText.indexOf("PEARL") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Pearl.png')";
		document.querySelector(".LogoMap > div").innerText="Pearl";
	}
	//Split
	if (document.querySelector(elementMap).innerText.indexOf("SPLIT") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Split.png')";
		document.querySelector(".LogoMap > div").innerText="Split";
	}
	//Sunset
	if (document.querySelector(elementMap).innerText.indexOf("SUNSET") != -1) {
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Sunset.png')";
		document.querySelector(".LogoMap > div").innerText="Sunset";
	}
	//Abyss
	if (document.querySelector(elementMap).innerText.indexOf("ABYSS") != -1){
		document.querySelector(".LogoMap").style.backgroundImage="url('Resources/Maps/Abyss.png')";
		document.querySelector(".LogoMap > div").innerText="Abyss";
	}
}
const readchangepath = setInterval(function(){readpjpath();refreshmap();}, 10);
const backgroundImage = document.querySelector('body');

//-------------------------------------------------------------------------------
//-------------------------------------------------------------------------------

//-----Initial Settings
Scoreboard();
SlideSpike(false);
ModPL();
DisplayBanner(scoreElement1, scoreElement2, bannerImage1, logoImage1, logoImage2);