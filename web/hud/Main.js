//-------------------------------------------------------------------------------------------
//-------------------------------------INITIAL RULES-----------------------------------------
const PVersion = "1.4";

function Scoreboard(){
	document.querySelector("body > div.Scoreboard").style.display="block"
	document.querySelector("body").style.backgroundImage="url('Resources/HUD-1.png')"
	document.querySelector("body").style.backgroundRepeat='no-repeat'
}

function LoadFont(name,url){
	if (document.querySelector("body > style") != null) {
		document.body.removeChild(document.querySelector("body > style"))
	}
    var newStyle = document.createElement('style');
    newStyle.appendChild(document.createTextNode('@font-face{font-family: '+name+'; src: url('+url+');}'));
    document.body.appendChild(newStyle)
}

//-------------------------------------------------------------------------------------------
//---------------------------------TRACKING DATA FUNCTIONS-----------------------------------

function SetNamePlayer(iTeam,iPlayer,iName){
	switch (iTeam){
		case 0:
			document.querySelector('.TIP' + iPlayer +  ' > div.Name').innerText=iName;
		break;
		case 1:
			document.querySelector('.TDP' + iPlayer +  ' > div.Name2').innerText=iName;
		break;
	}
}

function SetPlayerAgent(iTeam,iPlayer,iAgent){
	switch (iTeam){
		case 0:
			if (iAgent !== '' && iAgent !== 'Nothing') {
				document.querySelector('.TIP' + iPlayer + ' > div.Icon').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/' + iAgent + '.png)';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill1').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/C.png)';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill2').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/Q.png)';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill3').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/E.png)';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/X.png)';
			} else {
				document.querySelector('.TIP' + iPlayer + ' > div.Icon').style.backgroundImage = 'url()';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill1').style.backgroundImage = 'url()';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill2').style.backgroundImage = 'url()';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill3').style.backgroundImage = 'url()';
				document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.backgroundImage = 'url()';
			}
		break;
		case 1:
			if (iAgent !== '' && iAgent !== 'Nothing') {
				document.querySelector('.TDP' + iPlayer + ' > div.Icon').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/' + iAgent + '.png)';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill1').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/C.png)';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill2').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/Q.png)';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill3').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/E.png)';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill4').style.backgroundImage = 'url(Resources/Agentes/' + iAgent + '/X.png)';
			} else {
				document.querySelector('.TDP' + iPlayer + ' > div.Icon').style.backgroundImage = 'url()';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill1').style.backgroundImage = 'url()';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill2').style.backgroundImage = 'url()';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill3').style.backgroundImage = 'url()';
				document.querySelector('.TDP' + iPlayer + ' > div.Skill4').style.backgroundImage = 'url()';
			}
		break;
	}
}

function SetPlayerWeapon(iTeam, iPlayer, iWeapon, iAjust) {
	if (iWeapon == ''){return;}
    switch (iTeam) {
        case 0:
            document.querySelector('.TIP' + iPlayer + ' > div.Weapon1').style.backgroundImage = 'url("Resources/Armas/' + iWeapon + '.png")';
            document.querySelector('.TIP' + iPlayer + ' > div.Weapon1').style.backgroundSize = iAjust;
        break;
        case 1:
            document.querySelector('.TDP' + iPlayer + ' > div.Weapon2').style.backgroundImage = 'url("Resources/Armas/' + iWeapon + '.png")';
            document.querySelector('.TDP' + iPlayer + ' > div.Weapon2').style.backgroundSize = iAjust;
        break;
    }
}

function SetPlayerShield(iTeam, iPlayer, iShield) {
    switch (iTeam) {
        case 0:
            switch (iShield) {
                case "X":
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield').style.backgroundImage = '';
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield > div').innerText = '';
                    break;
                case "25":
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/Escudo50.png)';
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield > div').innerText = '25';
                    break;
                case "50":
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/Escudo100.png)';
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield > div').innerText = '50';
                    break;
                case "R":
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/EscudoReg.png)';
                    document.querySelector('.TIP' + iPlayer + ' > div.Shield > div').innerText = '25';
                    break;
            }
            break;
        case 1:
            switch (iShield) {
                case "X":
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield').style.backgroundImage = '';
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield > div').innerText = '';
                    break;
                case "25":
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/Escudo50.png)';
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield > div').innerText = '25';
                    break;
                case "50":
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/Escudo100.png)';
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield > div').innerText = '50';
                    break;
                case "R":
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield').style.backgroundImage = 'url(Resources/Escudos/EscudoReg.png)';
                    document.querySelector('.TDP' + iPlayer + ' > div.Shield > div').innerText = '25';
                    break;
            }
            break;
    }
}

function SetPlayerHP(iTeam,iPlayer,iHP){
	switch (iTeam){
		case 0:
			document.querySelector('.TIP' + iPlayer +  ' > div.HP1').style.width=iHP + '%';
		break;
		case 1:
			document.querySelector('.TDP' + iPlayer +  ' > div.HP2').style.width=iHP + '%';
		break;
	}
}

function SetPlayerKDA(iTeam,iPlayer,iK,iD,iA){
	switch (iTeam){
		case 0:
			document.querySelector('.TIP' + iPlayer +  ' > div.K1').innerText=iK;
			document.querySelector('.TIP' + iPlayer +  ' > div.D1').innerText=iD;
			document.querySelector('.TIP' + iPlayer +  ' > div.A1').innerText=iA;
		break;
		case 1:
			document.querySelector('.TDP' + iPlayer +  ' > div.K2').innerText=iK;
			document.querySelector('.TDP' + iPlayer +  ' > div.D2').innerText=iD;
			document.querySelector('.TDP' + iPlayer +  ' > div.A2').innerText=iA;
		break;
	}
}

function SetPlayerCreds(iTeam,iPlayer,iCreds){
	switch (iTeam){
		case 0:
			document.querySelector('.TIP' + iPlayer +  ' > div.Points > div').innerText=iCreds;
		break;
		case 1:
			document.querySelector('.TDP' + iPlayer +  ' > div.Points > div').innerText=iCreds;
		break;
	}
}

function SetUltiActive(iTeam,iPlayer,iActive){
	switch (iTeam){
		case 0:
			switch(iActive){
				case 0:
					document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.animation='';
					document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.outline='';
					document.querySelector('.TIP' + iPlayer + ' > div.ulti-container1').style.display='block';
				break;
				case 1:
					document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.animation='pulse 0.6s ease-in-out infinite alternate';
					document.querySelector('.TIP' + iPlayer + ' > div.Skill4').style.outline='2px solid white';
					document.querySelector('.TIP' + iPlayer + ' > div.ulti-container1').style.display='none';
				break;
			}
		break;
		case 1:
			switch(iActive){
				case 0:
					document.querySelector('.TDP' + iPlayer + ' > div.Skill4.SR').style.animation='';
					document.querySelector('.TDP' + iPlayer + ' > div.Skill4.SR').style.outline='';
					document.querySelector('.TDP' + iPlayer + ' > div.ulti-container2').style.display='block';
				break;
				case 1:
					document.querySelector('.TDP' + iPlayer + ' > div.Skill4.SR').style.animation='pulse 0.6s ease-in-out infinite alternate';
					document.querySelector('.TDP' + iPlayer + ' > div.Skill4.SR').style.outline='2px solid white';
					document.querySelector('.TDP' + iPlayer + ' > div.ulti-container2').style.display='none';
				break;
			}
		break;
	}
}

function SetUltiPoints(iTeam, PlayerID, SP, LP){
	switch (iTeam){
		case 0:
			SetUC = document.querySelectorAll(".ulti-container1")[PlayerID-1];
			switch (parseInt(LP)){
				case 6:
				    //Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP1")[0].style.cssText='top: 2px;left: 22px;width: 17px; height: 5px; transform: rotate(31deg)';
					SetUC.querySelectorAll(".UP1")[1].style.cssText='top: 19px;left: 30.5px;width: 17px; height: 5px; transform: rotate(90deg)';
					SetUC.querySelectorAll(".UP1")[2].style.cssText='top: 34.9px;left: 20.6px;width: 17px; height: 5px; transform: rotate(150deg)';
					SetUC.querySelectorAll(".UP1")[3].style.cssText='top: 34px;left: 2.4px;width: 17px; height: 5px; transform: rotate(210deg)';
					SetUC.querySelectorAll(".UP1")[4].style.cssText='top: 17.5px;left: -6px;width: 17px; height: 5px; transform: rotate(270deg)';
					SetUC.querySelectorAll(".UP1")[5].style.cssText='top: 1.8px;left: 3px;width: 17px; height: 5px; transform: rotate(330deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP1")).forEach(UP1 => {
						UP1.style.clipPath = 'polygon(0% 33%, 13% 18%, 31% 6%, 52% 4%, 64% 8%, 84% 23%, 92% 32%, 83% 92%, 72% 79%, 65% 74%, 53% 68%, 37% 69%, 19% 79%, 8% 91%)';
					});
				break;
				case 7:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP1")[0].style.cssText='top: 1.8px;left: 22px;width: 15.3px;height: 5px;transform: rotate(27deg)';
					SetUC.querySelectorAll(".UP1")[1].style.cssText='top: 15px;left: 31.5px;width: 15.6px;height: 5px;transform: rotate(78deg)';
					SetUC.querySelectorAll(".UP1")[2].style.cssText='top: 30px;left: 27px;width: 15.6px;height: 5px;transform: rotate(130deg)';
					SetUC.querySelectorAll(".UP1")[3].style.cssText='top: 36.9px;left: 12.4px;width: 15.6px;height: 5px;transform: rotate(179deg)';
					SetUC.querySelectorAll(".UP1")[4].style.cssText='top: 29.5px;left: -2px;width: 15.6px;height: 5px;transform: rotate(232deg)';
					SetUC.querySelectorAll(".UP1")[5].style.cssText='top: 13.8px;left: -5.0px;width: 15.6px;height: 5px;transform: rotate(283deg)';
					SetUC.querySelectorAll(".UP1")[6].style.cssText='top: 1px;left: 5.8px;width: 15.6px;height: 5px;transform: rotate(333deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP1")).forEach(UP1 => {
						UP1.style.clipPath = 'polygon(1% 29%, 7% 24%, 30% 10%, 47% 9%, 64% 10%, 76% 14%, 89% 24%, 81% 83%, 72% 74%, 65% 71%, 52% 68%, 32% 73%, 21% 78%, 10% 87%)';
					});
				break;
				case 8:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP1")[0].style.cssText='top: 1.6px;left: 22px;width: 13px;height: 4px;transform: rotate(23deg)';
					SetUC.querySelectorAll(".UP1")[1].style.cssText='top: 11.8px;left: 32px;width: 13px;height: 4px;transform: rotate(68deg)';
					SetUC.querySelectorAll(".UP1")[2].style.cssText='top: 25.8px;left: 31.9px;width: 13px;height: 4px;transform: rotate(114deg)';
					SetUC.querySelectorAll(".UP1")[3].style.cssText='top: 35.8px;left: 21.5px;width: 13px;height: 4px;transform: rotate(157deg)';
					SetUC.querySelectorAll(".UP1")[4].style.cssText='top: 35.5px;left: 6.8px;width: 13px;height: 4px;transform: rotate(204deg)';
					SetUC.querySelectorAll(".UP1")[5].style.cssText='top: 25.5px;left: -2.8px;width: 13px;height: 4px;transform: rotate(247deg)';
					SetUC.querySelectorAll(".UP1")[6].style.cssText='top: 10.5px;left: -2.6px;width: 13px;height: 4px;transform: rotate(293deg)';
					SetUC.querySelectorAll(".UP1")[7].style.cssText='top: 1px;left: 8px;width: 13px;height: 4px;transform: rotate(341deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP1")).forEach(UP1 => {
						UP1.style.clipPath = 'polygon(4% 21%, 19% 8%, 31% 6%, 52% 4%, 64% 6%, 88% 16%, 86% 55%, 84% 86%, 73% 80%, 65% 78%, 53% 76%, 37% 77%, 19% 84%, 12% 88%)';
					});
				break;
				case 9:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP1")[0].style.cssText='top: 0.6px;left: 22px;width: 11px;height: 4px;transform: rotate(21deg)';
					SetUC.querySelectorAll(".UP1")[1].style.cssText='top: 9px;left: 32px;width: 11px;height: 4px;transform: rotate(62deg)';
					SetUC.querySelectorAll(".UP1")[2].style.cssText='top: 21.6px;left: 34.2px;width: 11px;height: 4px;transform: rotate(101deg)';
					SetUC.querySelectorAll(".UP1")[3].style.cssText='top: 33.2px;left: 27.5px;width: 11px;height: 4px;transform: rotate(141deg);';
					SetUC.querySelectorAll(".UP1")[4].style.cssText='top: 37.5px;left: 15.2px;width: 11px;height: 4px;transform: rotate(181deg)';
					SetUC.querySelectorAll(".UP1")[5].style.cssText='top: 32.9;left: 3px;width: 11px;height: 4px;transform: rotate(224deg)';
					SetUC.querySelectorAll(".UP1")[6].style.cssText='top: 21px;left: -3.5px;width: 11px;height: 4px;transform: rotate(264deg)';
					SetUC.querySelectorAll(".UP1")[7].style.cssText='top: 8.8px;left: -1.0px;width: 11px;height: 4px;transform: rotate(299deg)';
					SetUC.querySelectorAll(".UP1")[8].style.cssText='top: 0.8px;left: 9px;width: 11px;height: 4px;transform: rotate(341deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP1")).forEach(UP1 => {
						UP1.style.clipPath = 'polygon(6% 22%, 19% 15%, 35% 9%, 49% 9%, 61% 9%, 76% 11%, 94% 17%, 85% 93%, 75% 90%, 59% 86%, 52% 85%, 45% 86%, 37% 87%, 14% 98%)';
					});
				break;
				default:
					SetUC.style.backgroundImage = 'url()';
				break;
			}
			for (var i = 1; i <= 9; i++){
				if (i <= LP){
					SetUC.querySelectorAll(".UP1")[i-1].style.display = 'block';}	
				else{
					SetUC.querySelectorAll(".UP1")[i-1].style.display = 'none';}	
				
				if (i <= SP){
					SetUC.querySelectorAll(".UP1")[i-1].style.backgroundColor = 'white';}
				else{
					SetUC.querySelectorAll(".UP1")[i-1].style.backgroundColor = 'rgb(127 127 127)';}
			}
		break;
		case 1:
			SetUC = document.querySelectorAll(".ulti-container2")[PlayerID-1];
			switch (parseInt(LP)){
				case 6:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP2")[0].style.cssText='top: 2.9px;left: 22.1px; height: 5px; transform: rotate(31deg)';
					SetUC.querySelectorAll(".UP2")[1].style.cssText='top: 19px;left: 30.5px; height: 5px; transform: rotate(90deg)';
					SetUC.querySelectorAll(".UP2")[2].style.cssText='top: 34.9px;left: 20.6px; height: 5px; transform: rotate(150deg)';
					SetUC.querySelectorAll(".UP2")[3].style.cssText='top: 34px;left: 2.4px; height: 5px; transform: rotate(210deg)';
					SetUC.querySelectorAll(".UP2")[4].style.cssText='top: 17.5px;left: -6px; height: 5px; transform: rotate(270deg)';
					SetUC.querySelectorAll(".UP2")[5].style.cssText='top: 1.8px;left: 3px; height: 5px; transform: rotate(330deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP2")).forEach(UP2 => {
						UP2.style.clipPath = 'polygon(0% 33%, 13% 18%, 31% 6%, 52% 4%, 64% 8%, 84% 23%, 92% 32%, 83% 92%, 72% 79%, 65% 74%, 53% 68%, 37% 69%, 19% 79%, 8% 91%)';
					});
				break;
				case 7:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP2")[0].style.cssText='top: 1.8px;left: 22px;width: 15.3px;height: 5px;transform: rotate(27deg)';
					SetUC.querySelectorAll(".UP2")[1].style.cssText='top: 15px;left: 31.5px;width: 15.6px;height: 5px;transform: rotate(78deg)';
					SetUC.querySelectorAll(".UP2")[2].style.cssText='top: 30px;left: 27px;width: 15.6px;height: 5px;transform: rotate(130deg)';
					SetUC.querySelectorAll(".UP2")[3].style.cssText='top: 36.9px;left: 12.4px;width: 15.6px;height: 5px;transform: rotate(179deg)';
					SetUC.querySelectorAll(".UP2")[4].style.cssText='top: 29.5px;left: -2px;width: 15.6px;height: 5px;transform: rotate(232deg)';
					SetUC.querySelectorAll(".UP2")[5].style.cssText='top: 13.8px;left: -5.0px;width: 15.6px;height: 5px;transform: rotate(283deg)';
					SetUC.querySelectorAll(".UP2")[6].style.cssText='top: 1px;left: 5.8px;width: 15.6px;height: 5px;transform: rotate(333deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP2")).forEach(UP2 => {
						UP2.style.clipPath = 'polygon(1% 29%, 7% 24%, 30% 10%, 47% 9%, 64% 10%, 76% 14%, 89% 24%, 81% 83%, 72% 74%, 65% 71%, 52% 68%, 32% 73%, 21% 78%, 10% 87%)';
					});
				break;
				case 8:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP2")[0].style.cssText='top: 1.6px;left: 22px;width: 13px;height: 4px;transform: rotate(23deg)';
					SetUC.querySelectorAll(".UP2")[1].style.cssText='top: 11.8px;left: 32px;width: 13px;height: 4px;transform: rotate(68deg)';
					SetUC.querySelectorAll(".UP2")[2].style.cssText='top: 25.8px;left: 31.9px;width: 13px;height: 4px;transform: rotate(114deg)';
					SetUC.querySelectorAll(".UP2")[3].style.cssText='top: 35.8px;left: 21.5px;width: 13px;height: 4px;transform: rotate(157deg)';
					SetUC.querySelectorAll(".UP2")[4].style.cssText='top: 35.5px;left: 6.8px;width: 13px;height: 4px;transform: rotate(204deg)';
					SetUC.querySelectorAll(".UP2")[5].style.cssText='top: 25.5px;left: -2.8px;width: 13px;height: 4px;transform: rotate(247deg)';
					SetUC.querySelectorAll(".UP2")[6].style.cssText='top: 10.5px;left: -2.6px;width: 13px;height: 4px;transform: rotate(293deg)';
					SetUC.querySelectorAll(".UP2")[7].style.cssText='top: 1px;left: 8px;width: 13px;height: 4px;transform: rotate(341deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP2")).forEach(UP2 => {
						UP2.style.clipPath = 'polygon(4% 21%, 19% 8%, 31% 6%, 52% 4%, 64% 6%, 88% 16%, 86% 55%, 84% 86%, 73% 80%, 65% 78%, 53% 76%, 37% 77%, 19% 84%, 12% 88%)';
					});
				break;
				case 9:
					//Set Ulti Format
					SetUC.style.backgroundImage = 'none';
					//Set Position Elements
					SetUC.querySelectorAll(".UP2")[0].style.cssText='top: 0.6px;left: 22px;width: 11px;height: 4px;transform: rotate(21deg)';
					SetUC.querySelectorAll(".UP2")[1].style.cssText='top: 9px;left: 32px;width: 11px;height: 4px;transform: rotate(62deg)';
					SetUC.querySelectorAll(".UP2")[2].style.cssText='top: 21.6px;left: 34.2px;width: 11px;height: 4px;transform: rotate(101deg)';
					SetUC.querySelectorAll(".UP2")[3].style.cssText='top: 33.2px;left: 27.5px;width: 11px;height: 4px;transform: rotate(141deg);';
					SetUC.querySelectorAll(".UP2")[4].style.cssText='top: 37.5px;left: 15.2px;width: 11px;height: 4px;transform: rotate(181deg)';
					SetUC.querySelectorAll(".UP2")[5].style.cssText='top: 32.9;left: 3px;width: 11px;height: 4px;transform: rotate(224deg)';
					SetUC.querySelectorAll(".UP2")[6].style.cssText='top: 21px;left: -3.5px;width: 11px;height: 4px;transform: rotate(264deg)';
					SetUC.querySelectorAll(".UP2")[7].style.cssText='top: 8.8px;left: -1.0px;width: 11px;height: 4px;transform: rotate(299deg)';
					SetUC.querySelectorAll(".UP2")[8].style.cssText='top: 0.8px;left: 9px;width: 11px;height: 4px;transform: rotate(341deg)';
					//Set figureclip
					Array.from(SetUC.querySelectorAll(".UP2")).forEach(UP2 => {
						UP2.style.clipPath = 'polygon(6% 22%, 19% 15%, 35% 9%, 49% 9%, 61% 9%, 76% 11%, 94% 17%, 85% 93%, 75% 90%, 59% 86%, 52% 85%, 45% 86%, 37% 87%, 14% 98%)';
					});
				break;
				default:
					SetUC.style.backgroundImage = 'url()';
				break;
			}
			for (var i = 1; i <= 9; i++){
				if (i <= LP){
					SetUC.querySelectorAll(".UP2")[i-1].style.display = 'block';}	
				else{
					SetUC.querySelectorAll(".UP2")[i-1].style.display = 'none';}	
				
				if (i <= SP){
					SetUC.querySelectorAll(".UP2")[i-1].style.backgroundColor = 'white';}
				else{
					SetUC.querySelectorAll(".UP2")[i-1].style.backgroundColor = 'rgb(127 127 127)';}
			}
		break;		
	}
}

function SetSkillsPoints(iTeam, iSkill, PlayerID, SP, LP){
	switch (iTeam){
		case 0:
			switch(iSkill){
				case 0:
					SetUC = document.querySelectorAll(".Skill1")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'inline-flex';}
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
				case 1:
					SetUC = document.querySelectorAll(".Skill2")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'inline-flex';}	
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
				case 2:
					SetUC = document.querySelectorAll(".Skill3")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'inline-flex';}	
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS1")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
			}
		break;
		case 1:
			switch(iSkill){
				case 0:
					SetUC = document.querySelectorAll(".Skill1.SR")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'inline-flex';}	
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
				case 1:
					SetUC = document.querySelectorAll(".Skill2.SR")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'inline-flex';}	
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
				case 2:
					SetUC = document.querySelectorAll(".Skill3.SR")[PlayerID-1]
						for (var i = 1; i <= 3; i++){
							if (i <= LP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'inline-flex';}	
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.display = 'none';}	
				
							if (i <= SP){
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'white';}
							else{
								SetUC.querySelectorAll(".UPS2")[i-1].style.backgroundColor = 'transparent';}
						}
				break;
			}
		break;		
	}
}

 function SetExtraData(iTeam, PlayerID, D1, D2){}

 function SetRound(lRound,rRound){
	 document.querySelector('.Score1').innerText = lRound;
	 document.querySelector('.Score2').innerText = rRound;
 } 
 
let spikeIntervals = [];
var spikeAnimationState = false;
function SlideSpike(isSlid) {
    if (!isSlid) {
        slidingImage.style.backgroundPositionY = "80px";
        slidingImage.style.filter = "brightness(1) sepia(1) hue-rotate(316deg) saturate(1000%) brightness(200%) contrast(1)";
        backgroundBomb.style.display = "none";
		//Clean spike animations ID's
		spikeAnimationState = false;
		spikeIntervals.forEach(id => clearTimeout(id));
		spikeIntervals = [];
    } else {
        slidingImage.style.backgroundPositionY = "-6px";
        backgroundBomb.style.display = "block";
		SpikeAnimation();
    }
}

function SpikeAnimation() {
  if (!spikeAnimationState) {
    spikeAnimationState = true;
    
    const filters = [
      "brightness(0.142) sepia(1) hue-rotate(316deg) saturate(700%) brightness(200%) contrast(1)", 
      "brightness(0.142) sepia(1) hue-rotate(316deg) saturate(700%) brightness(125%) contrast(1)"
    ];
    
    slidingImage.style.filter = filters[0];

    let totalTime = 0, toggleState = 0;
    [[20000, 1000], [18000, 500], [7000, 333]].forEach(([duration, interval]) => {
      for (let t = interval; t <= duration; t += interval) 
        spikeIntervals.push(setTimeout(() => slidingImage.style.filter = filters[toggleState ^= 1], totalTime + t));
      totalTime += duration;
    });
  }
}

function SpikeTeam(SpikeT){
	switch (SpikeT){
		case 0:
		portador.style.left = '2px';
		break;
		case 1:
		portador.style.left = '1887px';
		break;
	}
}

function SpikePlayer(SpikeID){
	switch (SpikeID){
		case 0:
		portador.style.display='none';
		break;
		case 1:
		portador.style.top = '543px';
		portador.style.display='block';
		break;
		case 2:
		portador.style.top = '649px';
		portador.style.display='block';
		break;
		case 3:
		portador.style.top = '755px';
		portador.style.display='block';
		break;
		case 4:
		portador.style.top = '861px';
		portador.style.display='block';
		break;
		case 5:
		portador.style.top = '967px';
		portador.style.display='block';
		break;
	}
}
//-------------------------------------------------------------------------------------------
//----------------------------------MATCH TOOLS FUNCTIONS------------------------------------

 function SetNameTeams(Team1Long,Team1Short,Team2Long,Team2Short){
	document.querySelector('.Team1b').innerText = Team1Long;
	document.querySelector('.Team2b').innerText = Team2Long;
	document.querySelector('.Team1').innerText = Team1Short;
	document.querySelector('.Team2').innerText = Team2Short;
 } 

function SetRefreshLogoTeam1(iOrder){
	switch (iOrder){
		case 0:
			document.querySelector('.logo1').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo1b').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo1c').src='resources/Logos/logo1.png' + '?' + Date.now();
		break;
		case 1:
			document.querySelector('.logo2').src='resources/Logos/logo1.png' + '?' + Date.now();
            document.querySelector('.logo2b').src='resources/Logos/logo1.png' + '?' + Date.now();
            document.querySelector('.logo2c').src='resources/Logos/logo1.png' + '?' + Date.now();
		break;
	}
}

function SetRefreshLogoTeam2(iOrder){
	switch (iOrder){
		case 0:
			document.querySelector('.logo2').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo2b').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo2c').src='resources/Logos/logo2.png' + '?' + Date.now();
		break;
		case 1:
			document.querySelector('.logo1').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo1b').src='resources/Logos/logo2.png' + '?' + Date.now();
            document.querySelector('.logo1c').src='resources/Logos/logo2.png' + '?' + Date.now();
		break;
	}
}

function SetRefreshLogos(iOrder){
	switch (iOrder){
		case 0:
			document.querySelector('.logo1').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo1b').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo1c').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo2').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo2b').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo2c').src='resources/Logos/logo2.png' + '?' + Date.now();
		break;
		case 1:
			document.querySelector('.logo1').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo1b').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo1c').src='resources/Logos/logo2.png' + '?' + Date.now();
			document.querySelector('.logo2').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo2b').src='resources/Logos/logo1.png' + '?' + Date.now();
			document.querySelector('.logo2c').src='resources/Logos/logo1.png' + '?' + Date.now();
		break;
	}
}

function SetTagTeams(iTag1, iTag2){
	document.querySelector ('.RTagTeam1').innerText = iTag1;
	document.querySelector ('.RTagTeam2').innerText = iTag2;
}

function SetMapResult(iSelect, iMapValue){
	switch(iSelect){
		case 0:
			document.querySelector('.Map1').innerHTML=iMapValue;
		break;
		case 1:
			document.querySelector('.Map2').innerHTML=iMapValue;
		break;
		case 2:
			document.querySelector('.Map3').innerHTML=iMapValue;
		break;
	}
}

//-------------------------------------------------------------------------------------------
//----------------------------------MAPBANS FUNCTIONS----------------------------------------

function SetRefreshLogoMapBans(iState){
	switch(iState){
		case 0:
			document.querySelectorAll('.MapBackground')[0].style.backgroundImage='url(' + 'resources/Logos/logo1.png'  + '?' + Date.now() + ')'
            document.querySelectorAll('.MapBackground')[2].style.backgroundImage='url(' + 'resources/Logos/logo1.png'  + '?' + Date.now() + ')'
            document.querySelectorAll('.MapBackground')[4].style.backgroundImage='url(' + 'resources/Logos/logo1.png'  + '?' + Date.now() + ')'
		break;
		case 1:
			document.querySelectorAll('.MapBackground')[1].style.backgroundImage='url(' + 'resources/Logos/logo2.png'  + '?' + Date.now() + ')'
            document.querySelectorAll('.MapBackground')[3].style.backgroundImage='url(' + 'resources/Logos/logo2.png'  + '?' + Date.now() + ')'
            document.querySelectorAll('.MapBackground')[5].style.backgroundImage='url(' + 'resources/Logos/logo2.png'  + '?' + Date.now() + ')'
		break;
	}
}

function SetMapSelect(iIndex, iValue, iOption){
	switch(iOption){
		case 0:
			document.querySelectorAll('.MapSelect')[iIndex].style.backgroundImage='url(Resources/Maps/' + iValue + '.png)';
			document.querySelectorAll('.MapSelect')[iIndex].style.animation='1s ease 0s 1 normal forwards running changeIcon';
		break;
		case 1:
			document.querySelectorAll('.MapSelect')[iIndex].style.backgroundImage='';
			document.querySelectorAll('.MapSelect')[iIndex].style.animation='';
		break;
	}
}

function SetMapLabels(iIndex, iValue1, iValue2){
	document.querySelectorAll('.TeamBan')[iIndex].innerText=iValue1;
	document.querySelectorAll('.LogoText')[iIndex].innerText=iValue2;
}

function SetMapBanMode(iB){
	switch (iB){
		case 0:
			document.querySelectorAll('.BanTitle')[0].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[0].style.display='block';
			document.querySelectorAll('.BanTitle')[1].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[1].style.display='block';
			document.querySelectorAll('.BanTitle')[2].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[2].style.display='block';
			document.querySelectorAll('.BanTitle')[3].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[3].style.display='block';
			document.querySelectorAll('.BanTitle')[4].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[4].style.display='block';
			document.querySelectorAll('.BanTitle')[5].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[5].style.display='block';
			document.querySelectorAll('.BanTitle')[6].innerText='Decider Map';	document.querySelectorAll('.MapBanIcon')[6].style.display='none';
		break;
		case 1:
			document.querySelectorAll('.BanTitle')[0].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[0].style.display='block';
			document.querySelectorAll('.BanTitle')[1].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[1].style.display='block';
			document.querySelectorAll('.BanTitle')[2].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[2].style.display='block';
			document.querySelectorAll('.BanTitle')[3].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[3].style.display='block';
			document.querySelectorAll('.BanTitle')[4].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[4].style.display='block';
			document.querySelectorAll('.BanTitle')[5].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[5].style.display='none';
			document.querySelectorAll('.BanTitle')[6].innerText='Decider Map';	document.querySelectorAll('.MapBanIcon')[6].style.display='none';
		break;
		case 2:
			document.querySelectorAll('.BanTitle')[0].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[0].style.display='block';
			document.querySelectorAll('.BanTitle')[1].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[1].style.display='block';
			document.querySelectorAll('.BanTitle')[2].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[2].style.display='none';
			document.querySelectorAll('.BanTitle')[3].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[3].style.display='none';
			document.querySelectorAll('.BanTitle')[4].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[4].style.display='block';
			document.querySelectorAll('.BanTitle')[5].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[5].style.display='block';
			document.querySelectorAll('.BanTitle')[6].innerText='Decider Map';	document.querySelectorAll('.MapBanIcon')[6].style.display='none';
		break;
		case 3:
			document.querySelectorAll('.BanTitle')[0].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[0].style.display='block';
			document.querySelectorAll('.BanTitle')[1].innerText='Veto Map';	document.querySelectorAll('.MapBanIcon')[1].style.display='block';
			document.querySelectorAll('.BanTitle')[2].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[2].style.display='none';
			document.querySelectorAll('.BanTitle')[3].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[3].style.display='none';
			document.querySelectorAll('.BanTitle')[4].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[4].style.display='none';
			document.querySelectorAll('.BanTitle')[5].innerText='Select Map';	document.querySelectorAll('.MapBanIcon')[5].style.display='none';
			document.querySelectorAll('.BanTitle')[6].innerText='Decider Map';	document.querySelectorAll('.MapBanIcon')[6].style.display='none';
		break;
	}
}

const PDEF = 'PICKS\n DEFENSE';const PATK = 'PICKS\n ATTACK';

function SetDefAtkBy(iState, iIndex, iValue, iConst){
	switch (iState){
		case 0:
			document.querySelectorAll('.MapSelectSubText')[iIndex].innerText= iValue + ' ' + iConst;
			document.querySelectorAll('.MapSelectSubText')[iIndex].style.display='block';
			document.querySelectorAll('.MapSelectSubText')[iIndex].style.opacity='1';
		break;
		case 1:
			document.querySelectorAll('.MapSelectSubText')[iIndex].innerText='';
			document.querySelectorAll('.MapSelectSubText')[iIndex].style.display='none';
			document.querySelectorAll('.MapSelectSubText')[iIndex].style.opacity='0';
		break;
	}
}

//-------------------------------------------------------------------------------------------
//----------------------------------PAUSE ALERTS FUNCTIONS-----------------------------------

function TechnicalPause(iState){
	document.querySelector(".TechPause").style.display = "flex";
	if (iState){
		document.querySelector(".TechPause").style.opacity = "1";
		document.querySelector(".TechPause").style.top = "200";
	}else{
		document.querySelector(".TechPause").style.opacity = "0";
		document.querySelector(".TechPause").style.top = "900";
	}
}

function DefTimeOut(iState){
	document.querySelector(".DefTimeout").style.display = "flex";
	document.querySelector(".Pause.DefTimeout > div > p").innerText = document.querySelector(".Team1b").innerText;
	if (iState){
		document.querySelector(".DefTimeout").style.opacity = "1";
		document.querySelector(".DefTimeout").style.top = "200";
	}else{
		document.querySelector(".DefTimeout").style.opacity = "0";
		document.querySelector(".DefTimeout").style.top = "900";
	}
}

function AttTimeOut(iState){
	document.querySelector(".AttTimeout").style.display = "flex";
	document.querySelector(".Pause.AttTimeout > div > p").innerText = document.querySelector(".Team2b").innerText;
	if (iState){
		document.querySelector(".AttTimeout").style.opacity = "1";
		document.querySelector(".AttTimeout").style.top = "200";
	}else{
		document.querySelector(".AttTimeout").style.opacity = "0";
		document.querySelector(".AttTimeout").style.top = "900";
	}
}

function ShowTagTeams(iState){
	if (iState){
		document.querySelector(".Team1").style.top = "-40";
		document.querySelector(".Team2").style.top = "-40";
		document.querySelector(".RTagTeam1").style.opacity = "1";
		document.querySelector(".RTagTeam2").style.opacity = "1";
	}else{
		document.querySelector(".Team1").style.top = "-33";
		document.querySelector(".Team2").style.top = "-33";
		document.querySelector(".RTagTeam1").style.opacity = "0";
		document.querySelector(".RTagTeam2").style.opacity = "0";
	}
}

function ShowTimeOutPoints(iState, iPoints){
	if (iState){
		document.querySelector('.AlertPoint').style.opacity='1';
		const ArrPoints = [iPoints.substr(0,1),iPoints.substr(1,1),iPoints.substr(2,1),iPoints.substr(3,1)];
		
		for(var i = 0; i < ArrPoints.length; i++){
			if(parseInt(ArrPoints[i])){
				document.querySelectorAll(".rombo-timeout")[i].style.backgroundColor="white";
			}else{
				document.querySelectorAll(".rombo-timeout")[i].style.backgroundColor="transparent";
			}	
		}
		
	}else{
		document.querySelector('.AlertPoint').style.opacity='0';
	}
}

//-------------------------------------------------------------------------------------------
//----------------------------------ROUND TEAMS FUNCTIONS------------------------------------

function RoundTeams(RTL, RLR){
	return;
	const ARound = parseInt(document.querySelector(".Score1").innerText) + parseInt(document.querySelector(".Score2").innerText) + 1;
	LIndex = RTL.split("|"); RIndex = RLR.split("|"); 
	
	if (ARound <=13){
		for (let i = 0; i < 13; i++) {
			if (String(i+1).length == 1){document.querySelectorAll(".Round-Num")[i].innerText = String("0"+(i+1));} 
			else{document.querySelectorAll(".Round-Num")[i].innerText = String(i+1);}}
		RoundPointer(ARound);
	
		for (let i=0; i < 12; i++){
		if (LIndex[i] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="52px";
			document.querySelectorAll(".Round-State")[i].style.top ="19px"
			switch (LIndex[i]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
			}
			continue;
		}
		if (RIndex[i] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="12px";
			document.querySelectorAll(".Round-State")[i].style.top ="59px"
			switch (RIndex[i]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if (ARound < 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 13) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
			}
			continue;
		}
			document.querySelectorAll(".Round-Num")[i].style.top="32px";
			document.querySelectorAll(".Round-State")[i].style.backgroundImage= "";
			document.querySelectorAll(".Round-Val")[i].style.backgroundColor = "";
		}
	}
		
	if (ARound > 13 && ARound <= 26){
		for (let i = 0; i < 13; i++) {
			if (String(ARound - 12 + i).length == 1){document.querySelectorAll(".Round-Num")[i].innerText = String("0"+(ARound - 12 + i));} 
			else{document.querySelectorAll(".Round-Num")[i].innerText = String(ARound - 12 + i);}
			} 
		RoundPointer(13);
		
		for (let i=0; i < 12; i++){
		if (LIndex[ARound - 13 + i] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="52px";
			document.querySelectorAll(".Round-State")[i].style.top ="19px"
			switch (LIndex[ARound - 13 + i]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
			}
			continue;
		}
		if (RIndex[ARound - 13 + i] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="12px";
			document.querySelectorAll(".Round-State")[i].style.top ="59px"
			switch (RIndex[ARound - 13 + i]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if ((ARound > 13 && ARound < 25) || ARound == 26) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				if (ARound == 25) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
			}
			continue;
		}
			document.querySelectorAll(".Round-Num")[i].style.top="32px";
			document.querySelectorAll(".Round-State")[i].style.backgroundImage= "";
			document.querySelectorAll(".Round-Val")[i].style.backgroundColor = "";
		}
		
	}
	
	if (ARound > 26){
		for (let i = 0; i < 13; i++) {
			if (String(ARound - 12 + i).length == 1){document.querySelectorAll(".Round-Num")[i].innerText = String("0"+(ARound - 12 + i));} 
			else{document.querySelectorAll(".Round-Num")[i].innerText = String(ARound - 12 + i);}
			} 
		RoundPointer(13);
		if (ARound % 2 === 0) {IPz=0;} else {IPz=1;}
				
		for (let i=0; i < 12; i++){
		if (LIndex[13 + i - IPz] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="52px";
			document.querySelectorAll(".Round-State")[i].style.top ="19px"
			switch (LIndex[13 + i - IPz]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
                if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';}
				break;
			}
			continue;
		}
		if (RIndex[13 + i - IPz] != 0){
			document.querySelectorAll(".Round-Num")[i].style.top="12px";
			document.querySelectorAll(".Round-State")[i].style.top ="59px"
			switch (RIndex[13 + i - IPz]){
				case "1":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Deactivation.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "2":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Elimination.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "3":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Time.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
				case "4":
				document.querySelectorAll(".Round-State")[i].style.backgroundImage= "url('resources/logos/Detonation.png')";
				if (ARound % 2 === 0) {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#177562e6';} 
				else {document.querySelectorAll(".Round-Val")[i].style.backgroundColor ='#6b2a39e6';}
				break;
			}
			continue;
		}
			document.querySelectorAll(".Round-Num")[i].style.top="32px";
			document.querySelectorAll(".Round-State")[i].style.backgroundImage= "";
			document.querySelectorAll(".Round-Val")[i].style.backgroundColor = "";
		}
		
	}
	
	
}

function RoundPointer(i){
	for (let s = 0; s < 13; s++){
		document.querySelectorAll(".Round-Val")[s].style.backgroundImage = "";
	}
	document.querySelectorAll(".Round-Val")[i-1].style.backgroundImage = "url(resources/Logos/Round.png)";
}

//-------------------------------------------------------------------------------------------
//-------------------------------------------------------------------------------------------