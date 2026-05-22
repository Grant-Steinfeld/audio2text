#!/usr/bin/env python3
"""CLI shim — delegates to the audio2text package. Use `audio2text analyze` instead."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audio2text.cli import main

main()
