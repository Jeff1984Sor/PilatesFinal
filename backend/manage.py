#!/usr/bin/env python
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studiopilates.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django not installed") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
