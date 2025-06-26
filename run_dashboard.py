
import os
import argparse
import logging
from threading import Thread

try:
    from distutils.util import strtobool
except ImportError:  # pragma: no cover - Python 3.12+
    def strtobool(val: str) -> int:  # type: ignore
        val = val.lower()
        if val in ("y", "yes", "t", "true", "on", "1"):
            return 1
        if val in ("n", "no", "f", "false", "off", "0"):
            return 0
        raise ValueError(f"invalid truth value {val!r}")

from dashboard import app
from dashboard.opc_client import run_async, disconnect_from_server
from EnpresorOPCDataViewBeforeRestructure import (
    start_auto_reconnection,
    delayed_startup_connect,
    load_saved_image,
)
from dashboard.state import app_state

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Run the OPC dashboard")

        def env_bool(name: str, default: bool) -> bool:
            val = os.getenv(name)
            if val is None:
                return default
            try:
                return bool(strtobool(val))
            except ValueError:
                return default

        open_browser_default = env_bool("OPEN_BROWSER", True)
        debug_default = env_bool("DEBUG", True)

        parser.add_argument(
            "--open-browser",
            dest="open_browser",
            action="store_true",
            default=open_browser_default,
            help="Automatically open the web browser (default: %(default)s)",
        )
        parser.add_argument(
            "--no-open-browser",
            dest="open_browser",
            action="store_false",
            help="Do not open the web browser automatically",
        )
        parser.add_argument(
            "--debug",
            dest="debug",
            action="store_true",
            default=debug_default,
            help="Run the app in debug mode (default: %(default)s)",
        )
        parser.add_argument(
            "--no-debug",
            dest="debug",
            action="store_false",
            help="Disable debug mode",
        )

        args = parser.parse_args()

        logger.info("Starting dashboard application...")

        logger.info("About to start auto-reconnection thread...")
        start_auto_reconnection()
        logger.info("Auto-reconnection thread start command completed")

        startup_thread = Thread(target=delayed_startup_connect)
        startup_thread.daemon = True
        startup_thread.start()
        logger.info("Scheduled startup auto-connection...")

        saved_image = load_saved_image()
        if saved_image:
            logger.info("Loaded saved custom image")

        import socket

        def get_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("10.255.255.255", 1))
                IP = s.getsockname()[0]
            except Exception:
                IP = "127.0.0.1"
            finally:
                s.close()
            return IP

        local_ip = get_ip()

        print("\nDashboard Access URLs:")
        print("  Local access:    http://127.0.0.1:8050/")
        print(f"  Network access:  http://{local_ip}:8050/")
        print("\nPress Ctrl+C to exit the application\n")

        if args.open_browser:
            import webbrowser
            import threading
            import time

            def open_browser():
                time.sleep(1.5)
                webbrowser.open_new("http://127.0.0.1:8050/")

            threading.Thread(target=open_browser).start()

        app.run(debug=False, use_reloader=False, host="0.0.0.0", port=8050)

    except KeyboardInterrupt:
        print("\nShutting down...")
        if app_state.connected:
            run_async(disconnect_from_server())
        print("Disconnected from server")
        print("Goodbye!")

