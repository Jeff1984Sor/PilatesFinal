import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ROOT_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
for path in (PROJECT_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.append(path)
