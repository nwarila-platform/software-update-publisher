"""Entry point for ``python -m software_update_publisher``."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
