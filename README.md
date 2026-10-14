# SCC VALORANT HUD

A VALORANT broadcast HUD in the style of the VCT Champions 2025 broadcast, for the St. Clair Saints. It's a Windows desktop app with a GFX controller, an overlay for OBS / vMix, a buy-phase scoreboard, data for vMix GT Title Designer, and an observer client. It's built the same way as the [League HUD](https://github.com/owenbparker/LeagueHUDSCC), but it's a separate app.

## Install

Download and run **[SCC-VAL-HUD-Setup.exe](https://github.com/owenbparker/VALHUDSCC/releases/latest/download/SCC-VAL-HUD-Setup.exe)**.
- It downloads the latest version from GitHub and installs it to `C:\SCC VAL HUD`.
- It adds a **SCC VAL HUD** desktop shortcut.
- No administrator rights are needed.
- Windows may show "Windows protected your PC" the first time: choose **More info -> Run anyway**.

The app updates itself. The **Check for updates** / **Update to vX** button is on every screen.

The VALORANT HUD runs on port **8778** (the League HUD uses 8777), so both can run on the same PC.

## Clients

The app opens on a choice of client:

### GFX Controller

Runs the HUD.

- **Live feed / Demo match:** the demo plays a believable match (buy phases, fights, the spike, economy, ults and half time), so everything can be set up without a game.
- **Teams:** name, tricode, logo and series wins.
- **Series & maps:** best of 1/3/5, which team attacks first, the map pool, the map being played, and map winners.
- **Broadcast:**
  - timeouts left (the diamonds under the score)
  - the timeout card for either team
  - the technical pause card
  - **Show scoreboard**, which keeps the scoreboard overlay up (it otherwise shows itself in the buy phase)
- **Players:** type names to replace the game's.
- **Show HUD on game:** the HUD in a see-through, click-through window on top of VALORANT. Use Windowed Fullscreen or Windowed, not exclusive Fullscreen.
- **Outputs:**
  - `http://localhost:8778/overlay`: HUD (browser source, 1920x1080)
  - `http://localhost:8778/scoreboard`: buy-phase scoreboard
  - `http://localhost:8778/hud.csv`: data for vMix, also `/hud.json` and `/hud.xml`
  - **Let other PCs on the network read the HUD**

### Observer Client

Enter the GFX PC's address (e.g. `http://192.168.2.40:8778/overlay`) and click **Show HUD on game** to draw that PC's HUD over the game here.

## The HUD

The overlay is the Champions 2025 HUD template (`web/hud`, `web/scoreboard`, with its art, agent, ability and weapon images and fonts), driven by `web/driver.js`.

**Top bar:**
- team tricodes and logos
- score
- round
- series diamonds
- timeouts
- maps of the series
- attack/defence colours, which swap at half time and in overtime

**Player panels** (5 a side):
- agent
- name
- health bar
- shields (light / heavy / regen)
- credits
- weapon
- C/Q/E charges
- ult points (with a pulse when the ult is ready)
- spike carrier

Dead players grey out.

**Banners and cards:**
- round-win banner (ATK/DEF, team, logo) when a score goes up
- panels slide away for the buy phase
- spike-planted animation
- timeout and tech-pause cards

**Scoreboard:** every player's agent, loadout, credits, ult, abilities and K/D/A, sorted by kills, plus the round history (defuse / elimination / time / detonation).

## Live game data

VALORANT has no official live-data API for spectators like League's. Riot keeps health, abilities and economy away from other programs because of its anti-cheat. Broadcast tools get them by reading the spectator's own player panels off the screen. That is the next step for this app: a screen reader like the League HUD's gold reader. It needs spectator screenshots to build against.

Anything that can read the match can already feed the HUD by POSTing JSON to `http://localhost:8778/api/ingest`. Only changed fields need sending:

```json
{"source": "reader",
 "match": {"map": "Ascent", "round": 7, "phase": "combat", "timer": 63, "attackers": "left",
           "score": {"left": 4, "right": 2},
           "spike": {"state": "planted", "timer": 30, "carrier": null},
           "round_winner": "", "win_type": "",
           "rounds": [{"winner": "left", "win_type": "Elimination"}]},
 "players": [{"team": "left", "slot": 1, "name": "Ace", "agent": "Jett", "alive": true, "health": 76,
              "shield": 50, "regen_shield": false, "credits": 2300, "weapon": "Vandal",
              "kills": 5, "deaths": 3, "assists": 1, "ult_points": 6, "ult_max": 8,
              "abilities": {"C": [1, 2], "Q": [1, 1], "E": [0, 1]}, "spike": false}]}
```

Field values:
- `team`: `left` / `right`; `slot`: 1-5.
- `phase`: `buy` / `combat` / `end`.
- `spike.state`: `carried` / `planted` / `defused` / `detonated`.
- `win_type`: `Elimination` / `Detonation` / `Deactivation` / `Time`.
- Agent and weapon names match the image folders (`KAY/O` is accepted as `Kayo`).
- Send `"reset": true` to start a new match from scratch.

## Running from source

```
pip install -r requirements-windows.txt
python -m valhud.gui            # the desktop app
python -m valhud --demo         # just the server, with a demo match
python -m unittest discover -s tests
```
