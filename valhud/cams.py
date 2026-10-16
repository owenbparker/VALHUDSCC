"""Player webcams on the HUD.

Each player can run the SCC Player Cam app on their PC, pick VALORANT and
enter their Riot ID (or read it from the Riot Client). Their cam connects
straight to the HUD over the local network (WebRTC, peer to peer); this app
only passes the connection messages between the cam and the overlays.

A cam is matched to a player in the match by the name part of the Riot ID
("leaf" of "leaf#NA1"), and the overlay shows the cam of the player the
observer is spectating.
"""

import difflib
import json
import re
import threading
import time
import unicodedata

from .log import log

LONG_POLL = 20          # seconds a poll waits for a message
GONE_AFTER = LONG_POLL + 15

_CONFUSABLE = str.maketrans({"0": "o", "1": "l", "|": "l", "!": "l", "5": "s", "$": "s", "8": "b"})


def normalise(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower()).translate(_CONFUSABLE)


def clean_riot_id(text):
    """'  leaf #NA1 ' -> 'leaf#NA1'; raises ValueError when it isn't one."""
    text = re.sub(r"\s*#\s*", "#", str(text or "").strip())
    name, _, tag = text.partition("#")
    name = name.strip()
    if not name or len(name) > 16 or len(tag) > 5 or not tag:
        raise ValueError("Enter your Riot ID as Name#TAG")
    return f"{name}#{tag.strip()}"


def name_matches(riot_name, player_name):
    """Is the player shown as player_name the one with this Riot ID name?
    The HUD's names are read off the spectator screen, so allow a misread
    letter in longer names, and a team tag in front ("G2 valyn")."""
    a, b = normalise(riot_name), normalise(player_name)
    if not a or not b:
        return False
    if a == b or (len(a) >= 3 and b.endswith(a) and len(b) - len(a) <= 4):
        return True
    return len(a) >= 5 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.85


def match_players(riot_ids, players):
    """{riot id: {"team", "slot", "name"}} for the ids that are in the match."""
    out, taken = {}, set()
    for rid in riot_ids:
        name = rid.split("#")[0]
        for p in players:
            key = (p.get("team"), p.get("slot"))
            if key not in taken and name_matches(name, p.get("name") or ""):
                out[rid] = {"team": key[0], "slot": key[1], "name": p.get("name")}
                taken.add(key)
                break
    return out


class CamHub:
    """Passes WebRTC connection messages between player cams (publishers)
    and the overlays showing them (viewers), and keeps track of whose cam is
    whose."""

    def __init__(self):
        self._cond = threading.Condition()
        self._inbox = {}       # peer id -> [messages]
        self._seen = {}        # peer id -> last poll
        self._riot = {}        # publisher id -> Riot ID
        self._label = {}       # publisher id -> camera name

    def poll(self, peer, riot_id=None, label=None, wait=LONG_POLL):
        """A cam or overlay checking in; waits up to `wait` seconds for
        messages. A cam passes its Riot ID ("" when it leaves)."""
        if not peer or len(peer) > 64:
            raise ValueError("Bad peer id")
        deadline = time.time() + max(0.0, min(float(wait or 0), LONG_POLL))
        with self._cond:
            self._touch(peer)
            if riot_id is not None:
                rid = clean_riot_id(riot_id) if riot_id else ""
                if rid:
                    for other, r in list(self._riot.items()):
                        if other != peer and r.lower() == rid.lower():
                            self._riot.pop(other)   # one cam per player: the newest wins
                            self._inbox.setdefault(other, []).append({"from": "hub", "type": "replaced"})
                if self._riot.get(peer, "") != rid:
                    log(f"Player cam {'connected' if rid else 'left'}: {rid or self._riot.get(peer, '')}"
                        + (f" ({label})" if label and rid else ""))
                if rid:
                    self._riot[peer] = rid
                else:
                    self._riot.pop(peer, None)
                if label is not None:
                    self._label[peer] = str(label)[:60]
            while not self._inbox.get(peer) and time.time() < deadline:
                self._cond.wait(deadline - time.time())
                self._touch(peer)
            return {"riot_id": self._riot.get(peer), "messages": self._inbox.pop(peer, [])}

    def send(self, to, sender, data):
        if not isinstance(data, dict) or len(json.dumps(data)) > 64 * 1024:
            raise ValueError("Bad message")
        with self._cond:
            if to not in self._seen:
                raise ValueError("That cam or overlay isn't connected")
            box = self._inbox.setdefault(to, [])
            box.append({**data, "from": sender})
            del box[:-50]
            self._cond.notify_all()

    def _touch(self, peer):
        now = time.time()
        self._seen[peer] = now
        for p, t in list(self._seen.items()):
            if now - t > GONE_AFTER:
                for d in (self._seen, self._inbox, self._label):
                    d.pop(p, None)
                rid = self._riot.pop(p, None)
                if rid:
                    log(f"Player cam disconnected: {rid}")

    def publishers(self, players=()):
        """[{"id", "riot_id", "label", "player": {"team", "slot", "name"} or None}]."""
        with self._cond:
            now = time.time()
            live = [(p, rid) for p, rid in self._riot.items() if now - self._seen.get(p, 0) < GONE_AFTER]
            labels = dict(self._label)
        matched = match_players([rid for _, rid in live], players)
        return [{"id": p, "riot_id": rid, "label": labels.get(p, ""), "player": matched.get(rid)} for p, rid in live]
