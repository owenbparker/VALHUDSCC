"""Match recorder: keeps what the reader saw, so a match can be read again
later (python -m valhud.replay) and every reader fix proven on real matches
before it reaches a show.

A recording is a folder under recordings/ next to the app:

    recordings/20261115-193012-Lotus/
        frames/000012-0012.35.jpg the game, about once a second (frame number,
                                  then seconds since the recording started)
        events.jsonl              every reading sent to the HUD (screen reader,
                                  Riot Client, observer), one JSON line each:
                                  {"t": seconds, "kind": ..., "data": ...}
        riot-*.json               what the Riot Client gave (pregame, core-game)
        match-details.json        the finished match from Riot's servers, when
                                  it could be fetched: the answer key
        info.json                 version, screen size, when it started/ended

A recording starts by itself at agent select or the first frame of a match
(while the screen is being read) and ends after a few minutes with neither.
Old recordings are deleted once they're older than KEEP_DAYS or the folder
is over KEEP_GB.
"""

import json
import os
import queue
import shutil
import threading
import time

from .log import log, log_once


class MatchRecorder:
    FRAME_EVERY = 1.0      # seconds between saved frames
    IDLE_END = 180.0       # no agent select / match for this long: the recording's over
    KEEP_DAYS = 14
    KEEP_GB = 15.0
    QUALITY = 85           # JPEG quality (about 200 KB a 1080p frame)

    def __init__(self, folder, enabled=lambda: True, version=""):
        self.folder = folder
        self.enabled = enabled
        self.version = version
        self.current = None        # this recording's folder
        self.started = 0.0
        self.seen_at = 0.0         # last agent select / match frame
        self.map = ""
        self.frames = 0
        self._frame_at = 0.0
        self._events = None
        self._lock = threading.RLock()
        self._jobs = queue.Queue(maxsize=8)
        self._writer = None

    # --- what the app tells it -------------------------------------------------

    def seen(self, what, map_name=""):
        """Agent select or a match is on screen ("select" / "match"): starts a
        recording if none is running (a new one after a match, at the next
        agent select)."""
        if not self._on():
            return
        with self._lock:
            now = time.time()
            if self.current and what == "select" and getattr(self, "_had_match", False) \
                    and now - getattr(self, "_select_at", 0) > 60:
                self.stop("next agent select")
            if not self.current:
                self.start(map_name)
            if what == "select":
                self._select_at = now
            else:
                self._had_match = True
            if map_name and not self.map:
                self.map = map_name
                self._write_info()
            self.seen_at = now

    def frame(self, image):
        """A captured frame (PIL image): saved about once a second while a
        recording runs."""
        with self._lock:
            if not self.current:
                return
            now = time.time()
            if now - self.seen_at > self.IDLE_END:
                self.stop("nothing to record for a while")
                return
            if now - self._frame_at < self.FRAME_EVERY:
                return
            self._frame_at = now
            self._seq = getattr(self, "_seq", 0) + 1
            path = os.path.join(self.current, "frames", f"{self._seq:06d}-{now - self.started:09.2f}.jpg")
        try:
            self._jobs.put_nowait((path, image.copy()))
        except queue.Full:
            log_once("recorder-full", "Match recorder: the disk is too slow, a frame was skipped")
        self._ensure_writer()

    def event(self, kind, data):
        """A reading sent to the HUD (or anything worth keeping with the frames)."""
        with self._lock:
            if not self.current or not self._events:
                return
            try:
                self._events.write(json.dumps({"t": round(time.time() - self.started, 3), "kind": kind, "data": data},
                                              default=str) + "\n")
                self._events.flush()
            except (OSError, TypeError, ValueError) as e:
                log_once("recorder-event", f"Match recorder couldn't write an event: {e!r}")

    def attach(self, name, data, match_id=None):
        """A JSON file kept with the recording (Riot's pregame, core-game and
        match details). Match details arrive after the match: they go into the
        recording that has that match id, even if it has ended."""
        folder = self.current
        if match_id:
            folder = self._folder_for_match(match_id) or folder
        elif self.current:
            self.match_ids_seen(data)
        if not folder:
            return
        try:
            with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, default=str)
        except OSError as e:
            log_once("recorder-attach", f"Match recorder couldn't save {name}: {e!r}")

    def match_ids_seen(self, data):
        """Remembers the Riot match id of this recording (from pregame/core-game)."""
        mid = data.get("MatchID") or data.get("ID") if isinstance(data, dict) else None
        if mid and self.current:
            ids = self.__dict__.setdefault("_ids", {})
            if ids.get(self.current) != mid:
                ids[self.current] = mid
                self._write_info()

    # --- recordings ------------------------------------------------------------

    def start(self, map_name=""):
        with self._lock:
            if self.current:
                return
            stamp = time.strftime("%Y%m%d-%H%M%S")
            name = stamp + (f"-{map_name}" if map_name else "")
            self.current = os.path.join(self.folder, name)
            os.makedirs(os.path.join(self.current, "frames"), exist_ok=True)
            self.started = self.seen_at = time.time()
            self.map, self.frames, self._frame_at, self._had_match, self._seq = map_name, 0, 0.0, False, 0
            self._events = open(os.path.join(self.current, "events.jsonl"), "a", encoding="utf-8")
            self._write_info()
            log(f"Recording the match for replay: {name}")
        threading.Thread(target=self.prune, daemon=True).start()

    def stop(self, why=""):
        with self._lock:
            if not self.current:
                return
            self._write_info(ended=time.time())
            try:
                self._events.close()
            except OSError:
                pass
            log(f"Match recording ended ({why}): {self.frames} frames in {os.path.basename(self.current)}")
            self.current, self._events = None, None

    def info(self):
        return {"enabled": self._on(), "recording": os.path.basename(self.current) if self.current else None,
                "frames": self.frames, "folder": self.folder}

    def prune(self):
        """Deletes recordings older than KEEP_DAYS, then the oldest while the
        folder is over KEEP_GB (never the one running)."""
        try:
            names = sorted(n for n in os.listdir(self.folder) if os.path.isdir(os.path.join(self.folder, n)))
        except OSError:
            return
        live = os.path.basename(self.current) if self.current else None
        sizes = {}
        for n in names:
            total = 0
            for root, _, files in os.walk(os.path.join(self.folder, n)):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            sizes[n] = total
        cutoff = time.time() - self.KEEP_DAYS * 86400
        total = sum(sizes.values())
        for n in names:
            if n == live:
                continue
            old = os.path.getmtime(os.path.join(self.folder, n)) < cutoff
            if old or total > self.KEEP_GB * 1e9:
                shutil.rmtree(os.path.join(self.folder, n), ignore_errors=True)
                total -= sizes[n]
                log(f"Deleted an old match recording: {n}")

    # --- inside ---------------------------------------------------------------

    def _on(self):
        try:
            return bool(self.enabled())
        except Exception:
            return False

    def _folder_for_match(self, match_id):
        for folder, mid in self.__dict__.get("_ids", {}).items():
            if mid == match_id:
                return folder
        return None

    def _write_info(self, ended=None):
        if not self.current:
            return
        info = {"version": self.version, "started": self.started, "map": self.map,
                "match_id": self.__dict__.get("_ids", {}).get(self.current), "frames": self.frames}
        if ended:
            info["ended"] = ended
        try:
            with open(os.path.join(self.current, "info.json"), "w", encoding="utf-8") as f:
                json.dump(info, f, indent=1)
        except OSError:
            pass

    def _ensure_writer(self):
        if self._writer and self._writer.is_alive():
            return
        self._writer = threading.Thread(target=self._write_frames, daemon=True)
        self._writer.start()

    def _write_frames(self):
        while True:
            try:
                path, image = self._jobs.get(timeout=30)
            except queue.Empty:
                return
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                image.convert("RGB").save(path, "JPEG", quality=self.QUALITY)
                self.frames += 1
            except (OSError, ValueError) as e:
                log_once("recorder-frame", f"Match recorder couldn't save a frame: {e!r}")
