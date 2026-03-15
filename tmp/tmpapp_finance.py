from __future__ import annotations

import os
import subprocess
import sys


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, "core_finance", "main.py")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        "--browser.serverAddress=localhost",
        "--browser.gatherUsageStats=false",
    ]

    subprocess.Popen(cmd)


if __name__ == "__main__":
    main()
