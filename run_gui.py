#!/usr/bin/env python3
"""
Start the FracPy GUI without needing to tweak PYTHONPATH.

Usage:
  python run_gui.py
"""
import os
import sys


def main() -> int:
    # Ensure the project root (this file's directory) is on sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from fracpy.gui.app import main as gui_main
    except ModuleNotFoundError as e:
        print("Could not import 'fracpy'. Make sure you're running this script from the project root.")
        print(f"Details: {e}")
        return 1

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())

