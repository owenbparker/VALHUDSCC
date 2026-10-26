"""Start the HUD without a window:  python -m valhud   (add --demo for a simulated match).

For the desktop app, run ValorantHUD.exe (or python -m valhud.gui).
"""

import argparse
import os
import time

from .app import HudApp, start
from .config import Config
from .demo import DemoGame


def build_app(args):
    config = Config()
    if not os.path.exists(config.path):
        config.save()
    if args.port:
        config.update({"http_port": args.port})
    if args.host:
        config.update({"http_host": args.host, "allow_network": args.host == "0.0.0.0"})
    if args.demo:
        return HudApp(config, DemoGame(speed=args.demo_speed, team_size=config.get().get("team_size", 5)), mode="demo")
    return HudApp(config)


def add_arguments(parser):
    parser.add_argument("--demo", action="store_true", help="simulate a match instead of using the live feed")
    parser.add_argument("--demo-speed", type=float, default=4.0, help="demo game seconds per real second")
    parser.add_argument("--port", type=int, help="web server port (saved to config.json)")
    parser.add_argument("--host", help="interface to listen on; 0.0.0.0 lets other PCs on your network connect")


def main():
    parser = argparse.ArgumentParser(description="Live VALORANT broadcast HUD")
    add_arguments(parser)
    app = build_app(parser.parse_args())
    start(app)
    print("  Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


if __name__ == "__main__":
    main()
