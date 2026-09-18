"""Check this one product: python -m software_update_publisher.products.google_chrome

Guarded, unlike a bare ``raise SystemExit(...)``: without this, merely importing the module --
which any package walker, documentation build or coverage discovery pass will do -- performs a
live network fetch and exits the interpreter. This file is the shape every future product copies.
"""

from __future__ import annotations

from ...cli import check_one

if __name__ == "__main__":
    raise SystemExit(check_one("google_chrome"))
