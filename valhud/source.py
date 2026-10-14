"""The live feed: match data POSTed to /api/ingest by whatever reads the game
(the screen reader, an Overwolf app, another tool), merged into one state."""

import threading
import time

from . import game


class LiveFeed:
    last_error = None

    def __init__(self, config):
        self.config = config
        self.state = game.empty_state()
        self.received_at = 0.0
        self.count = 0
        self.sources = {}  # name -> last time it sent something
        self._lock = threading.Lock()

    def apply(self, update):
        if not isinstance(update, dict):
            raise ValueError("Expected a JSON object")
        with self._lock:
            if update.get("reset"):
                self.state = game.empty_state()
            self.state = game.merge(self.state, update)
            now = time.time()
            self.received_at = now
            self.count += 1
            self.sources[str(update.get("source") or "unnamed")] = now

    def fetch(self):
        timeout = float(self.config.get().get("live_timeout") or 10)
        with self._lock:
            self.state["connected"] = time.time() - self.received_at < timeout
            return self.state

    def info(self):
        now = time.time()
        return {"updates": self.count, "age": round(now - self.received_at, 1) if self.received_at else None,
                "sources": {k: round(now - v, 1) for k, v in self.sources.items()}}
