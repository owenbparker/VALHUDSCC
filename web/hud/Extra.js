	//-------------------------------------------------------------------------------------------
//--------------------------------MAIN VARIABLES AND CONSTANTS-------------------------------
//--Sponsors Settings---
const SponsorMax = 2;
const SponsorChangeTime = 4000;
const SponsorEnable = true;
var   SponsorIndex = 1;
//--AutoScoreboard
const AutoScoreboardEnable = true;
//--Camera Settings---
const CameraEnable = false;
//--Spike Pictures
const slidingImage = document.getElementById('slidingImage');
const backgroundBomb = document.getElementById('background-bomb');
const portador = document.querySelector('.portador');
//--Team Colors
var Team1Color = '#00ffcc';
var Team2Color = '#ff4e5d';
var Team1ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
var Team2ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
//--Team Names---
var TeamNM1 =  document.querySelector(".Team1b");
var TeamNM2 =  document.querySelector(".Team2b");
//--Team Scores
var scoreElement1 = document.querySelector('.Score1');
var scoreElement2 = document.querySelector('.Score2');
//--Banner Element
var bannerImage1 = document.querySelector('.banner1');
var RondaN = document.querySelector('.RondaN');
var teamAtrr = document.querySelector('.teamAtrrib');
//--Define Logos Elements
var logoImage1 = document.querySelector('.logo1b');
var logoImage2 = document.querySelector('.logo2b');
logoImage1.src = document.querySelector('.logo1').src;
logoImage2.src = document.querySelector('.logo2').src;
//--Team Names---
var TeamNM1 =  document.querySelector(".Team1b");
var TeamNM2 =  document.querySelector(".Team2b");
//--Frame Camera
var CFrame1 = "url(Resources/CAM-1.png)";
var CFrame2 = "url(Resources/CAM-2.png)";
//--DisplayTeamsState
var DisplayTeamsState = false;
//--CameraIndex
var CameraIndex;


//-------------------------------------------------------------------------------------------
//----------------------------------SPONSORS FUNCTIONS-------------------------------------

  function SponsorFx(SIndex, SEnable){
	  if (SEnable){
		document.querySelector(".Sponsors").style.display='block';
		document.querySelector(".SponsorsLogo").style.backgroundImage='url("Resources/Sponsors/Sponsor' + SIndex +'.png")';
		SponsorIndex = SponsorIndex + 1;
		if (SponsorIndex>SponsorMax){SponsorIndex=1;}
	  }else{
		document.querySelector(".Sponsors").style.display='none';
	  }
  }

const SponsorTimer = setInterval(function(){SponsorFx(SponsorIndex, SponsorEnable);}, SponsorChangeTime);

//-------------------------------------------------------------------------------------------
//----------------------------------MATCH MODE FUNCTIONS-------------------------------------

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
      document.querySelector("#rombo-container1 > div:nth-child(1)").style.display="none"
      document.querySelector("#rombo-container1 > div:nth-child(2)").style.display="none"
      document.querySelector("#rombo-container1 > div:nth-child(3)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(1)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(2)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(3)").style.display="none"
      break;
      case 1:
      document.querySelector("#rombo-container1 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container1 > div:nth-child(2)").style.display="none"
      document.querySelector("#rombo-container1 > div:nth-child(1)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(2)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(1)").style.display="none"
      break;
      case 2:
      document.querySelector("#rombo-container1 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container1 > div:nth-child(2)").style.display="block"
      document.querySelector("#rombo-container1 > div:nth-child(1)").style.display="none"
      document.querySelector("#rombo-container2 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(2)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(1)").style.display="none"
      break;
      case 3:
      document.querySelector("#rombo-container1 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container1 > div:nth-child(2)").style.display="block"
      document.querySelector("#rombo-container1 > div:nth-child(1)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(3)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(2)").style.display="block"
      document.querySelector("#rombo-container2 > div:nth-child(1)").style.display="block"
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
//----------------------------------ROUND ANIMATION FUNCTIONS--------------------------------

  function ChangeColorScore() {
    const score1 = parseInt(document.querySelector('.Score1').innerText);
    const score2 = parseInt(document.querySelector('.Score2').innerText);
	const HP1Elements = document.querySelectorAll('.TeamIzquierda .HP1');
    const HP2Elements = document.querySelectorAll('.TeamDerecha .HP2');
	const alertColor1 = 'linear-gradient(90deg, rgba(0, 0, 0, 0.4), rgba(50, 130, 120, 0.5) 30%, rgba(50, 130, 120, 0.5), rgba(50, 130, 120, 0.5) 60%, rgba(50, 130, 120, 0.5), rgba(0, 0, 0, 0.4) 100%)';
	const alertColor2 = 'linear-gradient(90deg, rgba(0, 0, 0, 0.4), rgba(150, 50, 50, 0.5) 20%, rgba(150, 50, 50, 0.5), rgba(150, 50, 50, 0.5) 70%, rgba(150, 50, 50, 0.5), rgba(0, 0, 0, 0.4) 100%)';

    if (!isNaN(score1) && !isNaN(score2)) {
        const resultado = SideRound(score1 + score2 + 1);  // SCC: which half's colours (see driver-pre.js)
		document.getElementById('resultado').innerText = 'ROUND ' + (score1 + score2 + 1);

		if (resultado < 13) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
				document.querySelector(".AlertPoint").style.backgroundImage='url("Resources/AlertPoint1.png")';
				CFrame1 = "url(Resources/CAM-1.png)";
				CFrame2 = "url(Resources/CAM-2.png)";
				//SpikeTeam(1);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#00ffca';}
				Team1Color = '#00ffcc';
				Team1ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".DefTimeout > img").style.background=alertColor1;
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#ff4e5e';}
				Team2Color = '#ff4e5d';
				Team2ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".AttTimeout > img").style.background=alertColor2;
            }, 7000);
        }


        if (resultado >= 13 && resultado < 25) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
				document.querySelector(".AlertPoint").style.backgroundImage='url("Resources/AlertPoint2.png")';
				CFrame1 = "url(Resources/CAM-2.png)";
				CFrame2 = "url(Resources/CAM-1.png)";
				//SpikeTeam(0);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#ff4e5e';}
				Team1Color = '#ff4e5d';
				Team1ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".DefTimeout > img").style.background=alertColor2;
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#00ffca';}
				Team2Color = '#00ffcc';
				Team2ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".AttTimeout > img").style.background=alertColor1;
            }, 7000);
        }

        if (resultado == 25) {
            setTimeout(() => {
                document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
				document.querySelector(".AlertPoint").style.backgroundImage='url("Resources/AlertPoint1.png")';
				CFrame1 = "url(Resources/CAM-1.png)";
				CFrame2 = "url(Resources/CAM-2.png)";
				//SpikeTeam(1);
				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = '#00ffca';}
				Team1Color = '#00ffcc';
				Team1ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".DefTimeout > img").style.background=alertColor1;
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = '#ff4e5e';}
				Team2Color = '#ff4e5d';
				Team2ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
				document.querySelector(".AttTimeout > img").style.background=alertColor2;
            }, 7000);
        }

        if (resultado >= 26) {
            setTimeout(() => {
                if (resultado % 2 === 0) {
                    document.body.style.backgroundImage = 'url("Resources/HUD-2.png")';
					document.querySelector(".AlertPoint").style.backgroundImage='url("Resources/AlertPoint2.png")';
					document.querySelector(".DefTimeout > img").style.background=alertColor2;
					document.querySelector(".AttTimeout > img").style.background=alertColor1;
					Team1ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
					Team2ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
					CFrame1 = "url(Resources/CAM-2.png)";
				    CFrame2 = "url(Resources/CAM-1.png)";
					//SpikeTeam(0);
                } else {
                    document.body.style.backgroundImage = 'url("Resources/HUD-1.png")';
					document.querySelector(".AlertPoint").style.backgroundImage='url("Resources/AlertPoint1.png")';
					document.querySelector(".DefTimeout > img").style.background=alertColor1;
					document.querySelector(".AttTimeout > img").style.background=alertColor2;
					Team1ColorBox = 'linear-gradient(to right, rgb(0, 95, 75) 5%, rgb(0, 0, 0) 50%)';
					Team2ColorBox = 'linear-gradient(to right, rgba(95, 0, 0, 1) 5%, rgb(0, 0, 0) 50%)';
					CFrame1 = "url(Resources/CAM-1.png)";
				    CFrame2 = "url(Resources/CAM-2.png)";
					//SpikeTeam(1);
                }

				//Team 1
				for (var i = 0; i <= 4; i++) {HP1Elements[i].style.backgroundColor = resultado % 2 === 0 ? '#ff4e5e' : '#00ffca';}
				Team1Color = resultado % 2 === 0 ? '#ff4e5d' : '#00ffcc';
				//Team 2
				for (var i = 0; i <= 4; i++) {HP2Elements[i].style.backgroundColor = resultado % 2 === 0 ? '#00ffca' : '#ff4e5e';}
				Team2Color = resultado % 2 === 0 ? '#00ffcc' : '#ff4e5d';
				
            }, 7000);
        }
    } else {
        const resultadoElement = document.getElementById('resultado');
        resultadoElement.textContent = 'ROUND';
    }
}
setInterval(ChangeColorScore, 1000);
ChangeColorScore();

//-------------------------------------------------------------------------------------------
//--------------------------------PLAYER ANIMATION FUNCTIONS---------------------------------

function applyWithoutHP1(element, T1C) {
  const iconElement = element.querySelector('.Icon');
  const rTeam1 =  element.querySelector(".rectangle-Team1");
  const rbTeam1 =  element.querySelector(".rectangle-gray");
  const widthNumeric = parseInt(element.querySelector('.HP1').clientWidth);
  const blackhp = element.querySelector(".rectangle-black");

  if (widthNumeric === 0) {
	iconElement.style.filter = 'grayscale(100%)';
    rTeam1.style.filter = 'grayscale(100%)';
    rTeam1.style.background = 'linear-gradient(to left, transparent, #000000)';
    rTeam1.style.opacity = 1;
    rTeam1.style.width = 280;

	////////////////////////////
	rTeam1.style.borderStyle = 'solid';
    rTeam1.style.borderWidth = '1px 0 1px 1px';
    rTeam1.style.borderColor = 'transparent';
    rTeam1.style.borderImage = 'linear-gradient(to left, rgba(255, 255, 255, 0), #c3c3c3) 1';
	rTeam1.style.borderRight = '#ffffff00';
	////////////////////////////

	blackhp.style.background = 'linear-gradient(to left, transparent, #000000)';
	blackhp.style.width = 250;
    hideElements(element);
  } else { 
	iconElement.style.filter = 'none';
    rTeam1.style.filter = 'none';
	rTeam1.style.filter = 'none';
    //rTeam1.style.background = Team1ColorBox;
    rTeam1.style.opacity = 0.8;
    rTeam1.style.width = 314;

	////////////////////////////
	rTeam1.style.borderStyle = 'solid';
    rTeam1.style.borderWidth = '1px 1px 1px 1px'; 
    rTeam1.style.borderColor = 'transparent';
	
	
	if (CameraIndex == rTeam1.parentElement.className){
		rTeam1.style.borderImage = 'linear-gradient(to left, #d6ca97ff, #d6ca97ff) 1';
		rTeam1.style.background = 'linear-gradient(to right, #918f70ff 0%, black 65%, black 35%, #918f70ff 100%)'; //AQUI
		rbTeam1.style.backgroundColor = '#d6ca97ff';
	}else{
		rTeam1.style.borderImage = 'linear-gradient(to left, #c3c3c3, #c3c3c3) 1';
		rTeam1.style.background = Team1ColorBox;
		rbTeam1.style.backgroundColor = '#c3c3c3';
	}
	
	////////////////////////////

	blackhp.style.background = 'black';
	blackhp.style.width = 314;
    showElements(element);
  }
}

function applyWithoutHP2(element, T2C) {
  const iconElement = element.querySelector('.Icon');
  const rTeam2 =  element.querySelector(".rectangle-Team2");
  const rbTeam2 =  element.querySelector(".rectangle-gray");
  const widthNumeric = parseInt(element.querySelector('.HP2').clientWidth);
  const blackhp = element.querySelector(".rectangle-black");
  
  if (widthNumeric === 0) {
	iconElement.style.filter = 'grayscale(100%)';
    rTeam2.style.filter = 'grayscale(100%)';
    rTeam2.style.background = 'linear-gradient(to left, transparent, #000000)';
    rTeam2.style.opacity = 1;
    rTeam2.style.width = 280;

	////////////////////////////
	rTeam2.style.borderStyle = 'solid';
    rTeam2.style.borderWidth = '1px 0 1px 1px';
    rTeam2.style.borderColor = 'transparent';
    rTeam2.style.borderImage = 'linear-gradient(to left, rgba(255, 255, 255, 0), #c3c3c3) 1';
	////////////////////////////

	blackhp.style.background = 'linear-gradient(to left, transparent, #000000)';
	blackhp.style.width = 250;
    hideElements(element);
  } else {
	iconElement.style.filter = 'none';
    rTeam2.style.filter = 'none';
	rTeam2.style.filter = 'none';
    //rTeam2.style.background = Team2ColorBox;
    rTeam2.style.opacity = 0.8;
    rTeam2.style.width = 314;

	////////////////////////////
	rTeam2.style.borderStyle = 'solid';
    rTeam2.style.borderWidth = '1px 1px 1px 1px'; 
    rTeam2.style.borderColor = 'transparent';
	
	if (CameraIndex == rTeam2.parentElement.className){
		rTeam2.style.borderImage = 'linear-gradient(to left, #d6ca97ff, #d6ca97ff) 1';
		rTeam2.style.background = 'linear-gradient(to right, #918f70ff 0%, black 65%, black 35%, #918f70ff 100%)'; //AQUI
		rbTeam2.style.backgroundColor = '#d6ca97ff';
	}else{
		rTeam2.style.borderImage = 'linear-gradient(to left, #c3c3c3, #c3c3c3) 1';
		rTeam2.style.background = Team2ColorBox;
		rbTeam2.style.backgroundColor = '#c3c3c3';
	}
	
	////////////////////////////

	blackhp.style.background = 'black';  
	blackhp.style.width = 314;
    showElements(element);
  }
}

function hideElements(element) {
  const elementsToHide = element.querySelectorAll('.Shield, .SP1, .Weapon1, .Weapon2, .Skill1, .Skill2, .Skill3');
  elementsToHide.forEach((el) => {
    el.classList.add('fade-out');
  });
  
  const PSkill = element.querySelector('.Points')
  if (PSkill){
	  PSkill.style.top = '63';
	  PSkill.style.left = '70';
  }
  const PUlti = element.querySelector('.Skill4');
  if (PUlti){
	  PUlti.style.opacity = '0.5';
  }
  const ulticontainer1 = element.querySelector('.ulti-container1');
  if (ulticontainer1) {
    ulticontainer1.style.opacity = '1';
	ulticontainer1.style.filter = 'sepia(0.2) grayscale(0.4) brightness(1)';
  }
  const ulticontainer2 = element.querySelector('.ulti-container2');
  if (ulticontainer2) {
    ulticontainer2.style.opacity = '1';
	ulticontainer2.style.filter = 'sepia(0.2) grayscale(0.4) brightness(1)';
  }  
  const rectanglegray = element.querySelector('.rectangle-gray');
  if (rectanglegray) {
    rectanglegray.style.display = 'block';
  }
  const rectangleblack = element.querySelector('.rectangle-black');
  if (rectangleblack) {
    //rectangleblack.style.display = 'none';
  }
  if (element.className == CameraIndex) {CameraViewInactive();}
}

function showElements(element) {
  const elementsToShow = element.querySelectorAll('.Shield, .SP1, .Weapon1, .Weapon2, .Skill1, .Skill2, .Skill3, .Points');
  elementsToShow.forEach((el) => {
    el.classList.remove('fade-out');
    el.style.display = 'block';
  });
  
  const PSkill = element.querySelector('.Points')
  if (PSkill){
	  PSkill.style.top = '14px';
  	  PSkill.style.left = '258';
  }
  const PUlti = element.querySelector('.Skill4');
  if (PUlti){
	  PUlti.style.opacity = '1';
  }
  const ulticontainer1 = element.querySelector('.ulti-container1');
  if (ulticontainer1) {
  ulticontainer1.style.opacity = '1';
  ulticontainer1.style.filter = '';
  }  
  const ulticontainer2 = element.querySelector('.ulti-container2');
  if (ulticontainer2) {
  ulticontainer2.style.opacity = '1';
  ulticontainer2.style.filter = '';
  }  
  const rectanglegray = element.querySelector('.rectangle-gray');
  if (rectanglegray) {
    rectanglegray.style.display = 'block';
  }
  const rectangleblack = element.querySelector('.rectangle-black');
  if (rectangleblack) {
    rectangleblack.style.display = 'block';
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
  
  refreshKDACamera()
}

setInterval(TrackingHP, 50);

//-------------------------------------------------------------------------------------------
//-------------------------------------BANNER FUNCTIONS--------------------------------------

const BOX_FADE_MS       = 200;
const BOX_MOVE_MS       = 200;
const BOX_HOLD_MS       = 0;
const BANNER_VISIBLE_MS = 5000;

const BOX_RETURN_TOTAL = 20 + Math.max(BOX_MOVE_MS, BOX_FADE_MS) + BOX_FADE_MS;

const OFFSET_SYNC_MS = 300;

function positionRedBoxes() {
  const box1 = document.querySelector('.Box-red1');
  const box2 = document.querySelector('.Box-red2');

  [box1, box2].forEach(el => {
    if (!el) return;
    el.style.display = "block";
    el.style.opacity = "0";
    el.style.left = "890px";
  });

  setTimeout(() => {
    if (box1) { box1.style.left = "510px";  box1.style.opacity = "1"; }
    if (box2) { box2.style.left = "1300px"; box2.style.opacity = "1"; }
  }, 20);

  const totalHold = 20 + Math.max(BOX_MOVE_MS, BOX_FADE_MS) + BOX_HOLD_MS;
  setTimeout(() => {
    [box1, box2].forEach(el => el && (el.style.opacity = "0"));

    setTimeout(() => {
      [box1, box2].forEach(el => {
        if (!el) return;
        el.style.display = "none";
      });
    }, BOX_FADE_MS);
  }, totalHold);
}

function resetRedBoxes() {
  const box1 = document.querySelector('.Box-red1');
  const box2 = document.querySelector('.Box-red2');

  [box1, box2].forEach(el => {
    if (!el) return;
    el.style.display = "block";
    el.style.opacity = "0";
  });

  setTimeout(() => {
    [box1, box2].forEach(el => {
      if (!el) return;
      el.style.opacity = "1";
      el.style.left = "890px";
    });
  }, 20);

  const totalRound = 20 + Math.max(BOX_MOVE_MS, BOX_FADE_MS);
  setTimeout(() => {
    [box1, box2].forEach(el => el && (el.style.opacity = "0"));

    setTimeout(() => {
      [box1, box2].forEach(el => {
        if (!el) return;
        el.style.display = "none";
      });
    }, BOX_FADE_MS);
  }, totalRound);
}

function animationrep(elemento, elementoLogo, elementoTeam) {
  CameraViewInactive();
  elementoLogo.style.opacity = "0";
  teamAtrr.style.opacity = "0";
  elemento.src = "resources/Logos/banner1.png?"; // + Date.now();
  elementoLogo.style.top = "355px";
  elemento.style.top = "150px";
  RondaN.style.opacity = "0";
  teamAtrr.style.top = "350px";
  elemento.style.clipPath = "inset(0% 50%)";
  elemento.style.transition = "clip-path 0.2s ease";
  elementoTeam.style.top = "310px";

  positionRedBoxes();

  setTimeout(() => { elemento.style.clipPath = "inset(0%)"; }, 30);

  [elementoLogo, elemento, RondaN, teamAtrr, elementoTeam].forEach(el => el.style.display = "block");

  setTimeout(function () {
    elementoLogo.style.opacity = "1";
    teamAtrr.style.opacity = "1";
    elementoTeam.style.opacity = "1";

const startResetAt = Math.max(0, BANNER_VISIBLE_MS - BOX_RETURN_TOTAL + OFFSET_SYNC_MS);

setTimeout(() => {
  resetRedBoxes();
}, startResetAt);

    setTimeout(function () {
      elementoLogo.style.opacity = "0";
      teamAtrr.style.opacity = "0";
      elementoTeam.style.opacity = "0";

      setTimeout(function () {
        [elementoLogo, elemento, RondaN, teamAtrr, elementoTeam].forEach(el => (el.style.display = "none"));
      }, 0);

    }, BANNER_VISIBLE_MS);

  }, 100);

  if (AutoScoreboardEnable){
	setTimeout(function () { DisplayTeams(); }, 6600);
	setTimeout(function () { DisplayTeams(); }, 34500);  
  }
}

function DisplayBanner(
  elementoScore1, elementoScore2,
  elementoBanner1, elementoLogo1, elementoLogo2,
  RondaN, elementoTeam1, elementoTeam2
) {
  var lastValue1 = parseInt(elementoScore1.innerText);
  var lastValue2 = parseInt(elementoScore2.innerText);

  var observer1 = new MutationObserver(function () {
    var newValue1 = parseInt(elementoScore1.innerText);

    if (newValue1 !== lastValue1) {
      if (newValue1 > lastValue1) {
        if (document.querySelector("body").style.backgroundImage.indexOf("HUD-1") != -1) {
          teamAtrr.innerText = "DEF";
        } else {
          teamAtrr.innerText = "ATK";
        }
        elementoTeam1.innerText = document.querySelector(".Team1").innerText;
        animationrep(elementoBanner1, elementoLogo1, elementoTeam1);
      }
      lastValue1 = newValue1;
      updateRonda();
    }
  });

  var observer2 = new MutationObserver(function () {
    var newValue2 = parseInt(elementoScore2.innerText);

    if (newValue2 !== lastValue2) {
      if (newValue2 > lastValue2) {
        if (document.querySelector("body").style.backgroundImage.indexOf("HUD-1") != -1) {
          teamAtrr.innerText = "ATK";
        } else {
          teamAtrr.innerText = "DEF";
        }
        elementoTeam2.innerText = document.querySelector(".Team2").innerText;
        animationrep(elementoBanner1, elementoLogo2, elementoTeam2);
      }
      lastValue2 = newValue2;
      updateRonda();
    }
  });

  observer1.observe(elementoScore1, { childList: true, subtree: true });
  observer2.observe(elementoScore2, { childList: true, subtree: true });

  function updateRonda() {
    var totalRondas = lastValue1 + lastValue2;
    RondaN.innerText = "ROUND " + totalRondas;
  }
  
  updateRonda();
}


//-------------------------------------------------------------------------------------------
//-------------------------------------SHOW/HIDE TEAMS---------------------------------------

function DisplayTeams() {
  var teamIzquierda = document.getElementById('teamIzquierda');
  var teamDerecha = document.getElementById('teamDerecha');
  CameraViewInactive();

  if (teamIzquierda.style.left === '-385px') {
      teamIzquierda.style.left = '0px';
      teamDerecha.style.left = '-3px';
      teamIzquierda.style.opacity = '1';
      teamDerecha.style.opacity = '1';
      portador.style.opacity = '1';
	  DisplayTeamsState = false;

  } else {
      teamIzquierda.style.left = '-385px';
      teamDerecha.style.left = '330px';
      setTimeout(() => teamIzquierda.style.opacity = '0', 600);
      setTimeout(() => teamDerecha.style.opacity = '0', 600);
      portador.style.opacity = '0';
	  DisplayTeamsState = true;
  }
}

//-------------------------------------------------------------------------------------------
//------------------------------------MAP BANS ANIMATION-------------------------------------

const MapBansElements = document.querySelectorAll('.MapSelect'); var MapIPath = Array(6).fill('');

function MapAnimation(MapTarget, Index){
	MapTarget.style.display='none';
    MapTarget.style.animation='none';
	document.querySelectorAll('.MapBanIcon')[Index].style.opacity='0';
    setTimeout(function(){
		MapTarget.style.display='block';
		MapTarget.style.animation='changeIcon 1s forwards';
		//BanIcon
		if (document.querySelectorAll('.MapBanIcon')[Index].style.display=='block' && MapTarget.style.backgroundImage != ''){
			setTimeout(function () {document.querySelectorAll('.MapBanIcon')[Index].style.opacity='0.6';}, 2600);
		}
		else {
			document.querySelectorAll('.MapBanIcon')[Index].style.opacity='0';
		}
		//PickTeam
		if (document.querySelectorAll('.MapSelectSubText')[Index].style.display=='block' && MapTarget.style.backgroundImage != ''){
			setTimeout(function () {document.querySelectorAll('.MapSelectSubText')[Index].style.opacity='1';}, 2600);
		}
		else {
			document.querySelectorAll('.MapSelectSubText')[Index].style.opacity='0';
		}
	},100);
}

function ReadMapPath(){
    for (let i = 0; i < MapBansElements.length; i++){
        if (MapIPath [i] != MapBansElements[i].style.backgroundImage){
            MapAnimation(MapBansElements[i],i);
        }
		
		if (document.querySelectorAll('.MapBanIcon')[i].style.display=='block' && document.querySelectorAll('.MapBanIcon')[i].style.opacity=='0' && MapBansElements[i].style.backgroundImage != ''){
			setTimeout(function () {document.querySelectorAll('.MapBanIcon')[i].style.opacity='0.6';}, 2600);
		}
		
		if (document.querySelectorAll('.MapSelectSubText')[i].style.display=='block' && document.querySelectorAll('.MapSelectSubText')[i].style.opacity=='0' && MapBansElements[i].style.backgroundImage != ''){
			setTimeout(function () {document.querySelectorAll('.MapSelectSubText')[i].style.opacity='1';}, 2600);
		}

    }
    for (let i = 0; i < MapBansElements.length; i++){
    MapIPath [i] = MapBansElements[i].style.backgroundImage;
    }
}

const ReadChangePath = setInterval(function(){ReadMapPath();}, 100);

//-------------------------------------------------------------------------------------------
//------------------------------------CAMERA FUNCTIONS---------------------------------------

function SwitchButton(BKey){
	switch (BKey){
	case 10:
		CameraIndex="";
		document.querySelector(".CameraSet").style.display="none";
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="none";
		
		document.querySelector(".CameraPosition").style.display="none";
		document.querySelector(".CameraViews").style.display="none";
		
		document.querySelector(".CameraView").style.backgroundImage="";
		CameraViewInactive();
	break;	
	case 5:
		if (document.querySelectorAll(".HP1")[0].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TIP1";
		document.querySelector(".CameraSet").style.top="550px";
		document.querySelector(".CameraSet").style.left="329px";
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="1px solid rgb(101 101 101)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame1;
		
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player1.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TIP1 > div.Name").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP1 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP1 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP1 > div.A1").innerText.trim(); 
		
		CameraViewActive(0);
		LoadCamera(0);
		}
	break;
	case 4:
		if (document.querySelectorAll(".HP1")[1].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TIP2";
		document.querySelector(".CameraSet").style.top="656px";
		document.querySelector(".CameraSet").style.left="329px";
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame1;
				
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player2.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TIP2 > div.Name").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP2 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP2 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP2 > div.A1").innerText.trim(); 
		
		CameraViewActive(1);
		LoadCamera(1);
		}
	break;
	case 3:
		if (document.querySelectorAll(".HP1")[2].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TIP3";
		document.querySelector(".CameraSet").style.top="762px";
		document.querySelector(".CameraSet").style.left="329px";
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame1;
				
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player3.png)";

		document.querySelector(".CameraName").innerText=document.querySelector(".TIP3 > div.Name").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP3 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP3 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP3 > div.A1").innerText.trim(); 
		
		CameraViewActive(2);
		LoadCamera(2);
		}
	break;
	case 2:
		if (document.querySelectorAll(".HP1")[3].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TIP4";
		document.querySelector(".CameraSet").style.top="868px";
		document.querySelector(".CameraSet").style.left="329px";
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame1;
				
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player4.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TIP4 > div.Name").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP4 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP4 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP4 > div.A1").innerText.trim(); 
		
		CameraViewActive(3);
		LoadCamera(3);
		}
	break;
	case 1:
		if (document.querySelectorAll(".HP1")[4].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TIP5";
		document.querySelector(".CameraSet").style.top="974px"
		document.querySelector(".CameraSet").style.left="329px"
		
		document.querySelector(".CameraSet").style.borderLeft="none";
		document.querySelector(".CameraSet").style.borderRight="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame1;
				
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player5.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TIP5 > div.Name").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP5 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP5 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP5 > div.A1").innerText.trim(); 
		
		CameraViewActive(4);
		LoadCamera(4);
		}
	break;
  case 6:
		if (document.querySelectorAll(".HP2")[0].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TDP1";
		document.querySelector(".CameraSet").style.top="550px";
		document.querySelector(".CameraSet").style.left="1560px";
		
		document.querySelector(".CameraSet").style.borderRight="none";
		document.querySelector(".CameraSet").style.borderLeft="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame2;
						
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player6.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TDP1 > div.Name2").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP1 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP1 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP1 > div.A2").innerText.trim(); 
		
		CameraViewActive(5);
		LoadCamera(5);
		}
	break;
	case 7:
		if (document.querySelectorAll(".HP2")[1].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TDP2";
		document.querySelector(".CameraSet").style.top="656px";
		document.querySelector(".CameraSet").style.left="1560px";
		
		document.querySelector(".CameraSet").style.borderRight="none";
		document.querySelector(".CameraSet").style.borderLeft="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame2;
						
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player7.png)";

		document.querySelector(".CameraName").innerText=document.querySelector(".TDP2 > div.Name2").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP2 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP2 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP2 > div.A2").innerText.trim(); 
		
		CameraViewActive(6);
		LoadCamera(6);
		}
	break;
	case 8:
		if (document.querySelectorAll(".HP2")[2].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TDP3";
		document.querySelector(".CameraSet").style.top="762px";
		document.querySelector(".CameraSet").style.left="1560px";
		
		document.querySelector(".CameraSet").style.borderRight="none";
		document.querySelector(".CameraSet").style.borderLeft="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame2;
						
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player8.png)";

		document.querySelector(".CameraName").innerText=document.querySelector(".TDP3 > div.Name2").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP3 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP3 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP3 > div.A2").innerText.trim(); 
		
		CameraViewActive(7);
		LoadCamera(7);
		}
	break;
	case 9:
		if (document.querySelectorAll(".HP2")[3].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TDP4";
		document.querySelector(".CameraSet").style.top="868px";
		document.querySelector(".CameraSet").style.left="1560px";
		
		document.querySelector(".CameraSet").style.borderRight="none";
		document.querySelector(".CameraSet").style.borderLeft="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame2;
						
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player9.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TDP4 > div.Name2").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP4 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP4 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP4 > div.A2").innerText.trim(); 
		
		CameraViewActive(8);
		LoadCamera(8);
		}
	break;
	case 0:
		if (document.querySelectorAll(".HP2")[4].style.width != "0%" && DisplayTeamsState == false){
		CameraIndex="TDP5";
		document.querySelector(".CameraSet").style.top="974px";
		document.querySelector(".CameraSet").style.left="1560px";
		
		document.querySelector(".CameraSet").style.borderRight="none";
		document.querySelector(".CameraSet").style.borderLeft="1px solid rgb(139, 139, 139)";
		
		document.querySelector(".CameraPosition").style.backgroundImage=CFrame2;
						
		document.querySelector(".CameraView").style.backgroundImage="url(PlayerPic/Player10.png)";
		
		document.querySelector(".CameraName").innerText=document.querySelector(".TDP5 > div.Name2").innerText;
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP5 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP5 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP5 > div.A2").innerText.trim(); 
		
		CameraViewActive(9);
		LoadCamera(9);
		}
	break;
	}
}

//----Load Camera FirstTime
function LoadCamera(BKey){
	if (!CameraEnable){return;}
	
	if (document.querySelectorAll(".CameraViews")[BKey].src == document.location){
		document.querySelectorAll(".CameraViews")[BKey].src=CameraURL[BKey] + "&cleanoutput&transparent&hidemenu";
	}
}

function refreshKDACamera(){
	switch (CameraIndex){
	case "TIP1":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP1 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP1 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP1 > div.A1").innerText.trim(); 
	break;
	case "TIP2":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP2 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP2 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP2 > div.A1").innerText.trim(); 
	break
	case "TIP3":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP3 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP3 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP3 > div.A1").innerText.trim(); 
	break;
	case "TIP4":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP4 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP4 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP4 > div.A1").innerText.trim(); 
	break;
	case "TIP5":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TIP5 > div.K1").innerText.trim() + "|" + document.querySelector(".TIP5 > div.D1").innerText.trim() + "|" + document.querySelector(".TIP5 > div.A1").innerText.trim(); 
	break;
    case "TDP1":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP1 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP1 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP1 > div.A2").innerText.trim(); 
	break;
	case "TDP2":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP2 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP2 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP2 > div.A2").innerText.trim(); 
	break;
	case "TDP3":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP3 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP3 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP3 > div.A2").innerText.trim(); 
	break;
	case "TDP4":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP4 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP4 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP4 > div.A2").innerText.trim(); 
	break;
	case "TDP5":
		document.querySelector(".CameraKDA").innerText=document.querySelector(".TDP5 > div.K2").innerText.trim() + "|" + document.querySelector(".TDP5 > div.D2").innerText.trim() + "|" + document.querySelector(".TDP5 > div.A2").innerText.trim(); 
	break;
	}
}

function CameraViewActive(Index){
	for (i=0; i<=document.querySelectorAll(".CameraViews").length-1;i+=1){
		document.querySelectorAll(".CameraViews")[i].style.display="none";
		document.querySelector(".CameraSet").style.display="none";
		document.querySelector(".CameraPosition").style.display="none";
	}
	
	if (!CameraEnable){return;}
	
	if (document.querySelector(".banner1").style.display!="block"){
		document.querySelectorAll(".CameraViews")[Index].style.display="block";	
		document.querySelector(".CameraSet").style.display="none";
		document.querySelector(".CameraPosition").style.display="block";
		document.querySelector(".CameraView").style.display="block";
	}
}

function CameraViewInactive(){
	for (i=0; i<=document.querySelectorAll(".CameraViews").length-1;i+=1){
	  	document.querySelector(".CameraSet").style.display="none";
		document.querySelector(".CameraPosition").style.display="none";
		document.querySelectorAll(".CameraViews")[i].style.display="none";
	}
	document.querySelector(".CameraView").style.display="none";
}


//-------------------------------------------------------------------------------------------
//----------------------------------INITIAL SETTINGS-----------------------------------------

Scoreboard();
SlideSpike(false);
ModPL();
DisplayBanner(scoreElement1, scoreElement2, bannerImage1, logoImage1, logoImage2, RondaN, TeamNM1, TeamNM2);