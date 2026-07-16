import os
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"

import sys
import subprocess
import threading
import multiprocessing
import time
import socket
import webview


def get_base_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard", "dashboard.py")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


PORT = find_free_port()


def run_streamlit_frozen(dashboard_path, port):
    os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    sys.argv = [
        "streamlit", "run", dashboard_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
    ]

    from streamlit.web.cli import main

    try:
        main()
    except SystemExit:
        pass


def start_streamlit_dev():
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", DASHBOARD_PATH,
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--browser.gatherUsageStats", "false"
    ])


def wait_for_server(port, host="localhost", timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if not os.path.exists(DASHBOARD_PATH):
        print(f"FATAL: dashboard.py not found at {DASHBOARD_PATH}", flush=True)
        print(f"BASE_DIR was resolved to: {BASE_DIR}", flush=True)
        sys.exit(1)

    print(f"[launcher] Using port {PORT} for this session", flush=True)

    if getattr(sys, "frozen", False):
        proc = multiprocessing.Process(
            target=run_streamlit_frozen,
            args=(DASHBOARD_PATH, PORT),
            daemon=True
        )
        proc.start()
        server_timeout = 90
    else:
        threading.Thread(target=start_streamlit_dev, daemon=True).start()
        server_timeout = 30

    if wait_for_server(PORT, timeout=server_timeout):
        webview.create_window(
            "AI Trading System",
            f"http://localhost:{PORT}",
            width=1400,
            height=900
        )
        webview.start()
    else:
        print("Streamlit server never came up - check output above for errors.", flush=True)
