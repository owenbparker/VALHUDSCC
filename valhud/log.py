"""The app's log: what used to scroll past in the command window, kept in
memory so the desktop app can show it."""

import collections
import itertools
import threading
import time

_lines = collections.deque(maxlen=500)
_ids = itertools.count(1)
_lock = threading.Lock()
_folder = None   # where the day's log file goes (set_folder), for problem reports


def set_folder(folder):
    global _folder
    _folder = folder


def path_for_today():
    import os
    return os.path.join(_folder, time.strftime("log-%Y%m%d.txt")) if _folder else None


def log(message, level="info"):
    entry = {"id": next(_ids), "time": time.strftime("%H:%M:%S"), "level": level, "message": message}
    with _lock:
        _lines.append(entry)
        path = path_for_today()
        if path:
            try:
                import os
                os.makedirs(_folder, exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(f"[{entry['time']}] {level.upper():5} {message}\n")
            except OSError:
                pass
    # Also print, for when it's run from a terminal (does nothing in the .exe).
    print(f"[{entry['time']}] {message}")


def since(after_id=0):
    with _lock:
        return [e for e in _lines if e["id"] > after_id]
