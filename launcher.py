import os
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"  # keeps the segfault fix

import subprocess, threading, time, webview

def start_streamlit():
    subprocess.run([
        "streamlit", "run", "dashboard/dashboard.py",
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ])

threading.Thread(target=start_streamlit, daemon=True).start()
time.sleep(3)
webview.create_window("AI Trading System", "http://localhost:8501", width=1400, height=900)
webview.start()
