"""Pytest config: put the server-python root on sys.path."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("TTS_PROVIDER", "mock")
os.environ.setdefault("LOG_LEVEL", "WARNING")
