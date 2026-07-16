import os
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"  # keeps the segfault fix

import sys
import subprocess
import threading
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


def start_streamlit():
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", DASHBOARD_PATH,
        "--server.headless", "true",
        "--server.port", str(PORT),
        "--browser.gatherUsageStats", "false"
    ])


def wait_for_server(host="localhost", port=PORT, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


if not os.path.exists(DASHBOARD_PATH):
    print(f"FATAL: dashboard.py not found at {DASHBOARD_PATH}", flush=True)
    print(f"BASE_DIR was resolved to: {BASE_DIR}", flush=True)
    sys.exit(1)

print(f"[launcher] Using port {PORT} for this session", flush=True)

threading.Thread(target=start_streamlit, daemon=True).start()

if wait_for_server():
    webview.create_window(
        "AI Trading System",
        f"http://localhost:{PORT}",
        width=1400,
        height=900
    )
    webview.start()
else:
    print("Streamlit server never came up - check output above for errors.", flush=True)
