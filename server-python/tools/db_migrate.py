"""Database migration helper — thin wrapper over alembic.

Usage (from server-python/):
    python tools/db_migrate.py upgrade head
    python tools/db_migrate.py downgrade -1
    python tools/db_migrate.py current
    python tools/db_migrate.py check        # detect schema/model drift

The database URL comes from DATABASE_URL / .env; override with
ALEMBIC_DATABASE_URL (e.g. sqlite+aiosqlite:///./dev.db for offline SQLite).
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent


def _config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    cfg = _config()

    if cmd == "upgrade":
        command.upgrade(cfg, rest[0] if rest else "head")
    elif cmd == "downgrade":
        if not rest:
            print("usage: python tools/db_migrate.py downgrade <revision>")
            return 1
        command.downgrade(cfg, rest[0])
    elif cmd == "current":
        command.current(cfg)
    elif cmd == "check":
        command.check(cfg)
    elif cmd == "revision":
        message = " ".join(rest)
        command.revision(cfg, message=message, autogenerate=True)
    else:
        print(f"unknown command: {cmd}\n{__doc__}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
