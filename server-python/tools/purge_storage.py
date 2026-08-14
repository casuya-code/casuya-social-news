"""Purge expired script-audio directories from storage.

Usage:
  python tools/purge_storage.py              # delete audio older than 24h
  python tools/purge_storage.py --hours 48   # custom retention
  python tools/purge_storage.py --dry-run    # report only
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from maintenance.retention import main  # noqa: E402

if __name__ == "__main__":
    main()
