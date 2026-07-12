"""
AI Trading System v0.1
Application Entry Point
"""

from pathlib import Path
import json


def load_config():
    config_file = Path("config/settings.json")

    if not config_file.exists():
        print("Configuration file not found.")
        return {}

    with open(config_file, "r") as f:
        return json.load(f)


def main():
    print("=" * 50)
    print("AI Trading System v0.1")
    print("=" * 50)

    config = load_config()

    print("\nConfiguration loaded:")
    print(config)

    print("\nApplication initialized.")
    print("Ready for dashboard integration.")


if __name__ == "__main__":
    main()
