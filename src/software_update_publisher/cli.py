"""The command line.

Owns the argument surface and the exit-code contract, because those are what a scheduled run
is read through: 0 means the run did what it set out to do, 1 means it ran and something
failed, 2 means it could not run at all.

Acquiring and publishing are not wired yet, so ``check`` asks upstream what a product is at
and reports it. It does not claim to have published anything.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections.abc import Sequence
from typing import Any

from ._version import __version__
from .config import load
from .exceptions import PublisherError
from .loader import load_products

EXIT_OK = 0
EXIT_SOMETHING_FAILED = 1
EXIT_CANNOT_RUN = 2

_TIMEOUT_SECONDS = 30


def _fetch_json(url: str) -> Any:
    """Fetch and decode one JSON document.

    The shared client a module is handed. A module never opens a socket itself, so timeouts
    and transport policy are set in one place rather than forty.
    """
    request = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310
        return json.load(response)


def check_one(key: str) -> int:
    """Check a single product by name. Used by each module's standalone entry point."""
    return _check([key])


def _check(only: Sequence[str] | None = None) -> int:
    """Ask each product what its upstream is at, and report it."""
    loaded, failures = load_products()
    if only is not None:
        loaded = [product for product in loaded if product.declaration.key in only]
        failures = [failure for failure in failures if failure.key in only]

    if not loaded and not failures:
        sys.stderr.write("No product modules matched.\n")
        return EXIT_CANNOT_RUN

    problems = len(failures)
    for failure in failures:
        sys.stderr.write(f"{failure.key}: {failure.reason}\n")

    for product in loaded:
        name = product.declaration.key
        try:
            candidate = product.module.check(_fetch_json)
        except PublisherError as exc:
            problems += 1
            sys.stderr.write(f"{name}: {exc}\n")
        except Exception as exc:  # one vendor being unreachable must not end the run
            problems += 1
            sys.stderr.write(f"{name}: upstream check failed: {exc!r}\n")
        else:
            sys.stdout.write(f"{name}  advertised={candidate.advertised_version}  {candidate.file_name}\n")

    return EXIT_SOMETHING_FAILED if problems else EXIT_OK


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="software-update-publisher",
        description="Publish verified vendor software to the application repository.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the resolved configuration and exit, without contacting any vendor or bucket.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Ask every product what its upstream is at. Contacts vendors; publishes nothing.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the products this build tracks, without contacting anything.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line."""
    args = _parser().parse_args(argv)
    settings = load()

    if args.list:
        loaded, failures = load_products()
        for product in loaded:
            declaration = product.declaration
            pin = declaration.pdq_variable or "(not pinnable)"
            sys.stdout.write(f"{declaration.key}  {declaration.artifact_class.value}  {pin}\n")
        for failure in failures:
            sys.stderr.write(f"{failure.key}: {failure.reason}\n")
        return EXIT_SOMETHING_FAILED if failures else EXIT_OK

    if args.check:
        return _check()

    if args.show_config:
        sys.stdout.write(f"repository_bucket: {settings.repository_bucket or '(unset)'}\n")
        sys.stdout.write(f"region: {settings.region}\n")
        return EXIT_OK

    # Configuration is validated before anything reaches out, so a missing bucket is one loud
    # message naming the variable rather than a failure at the first upload.
    if not settings.repository_bucket:
        sys.stderr.write(
            "What: no application repository bucket is configured. "
            "Why: SUP_REPOSITORY_BUCKET is unset, and it has no default because it names an account. "
            "Fix: set SUP_REPOSITORY_BUCKET to the application repository bucket.\n"
        )
        return EXIT_CANNOT_RUN

    # There is no loader yet, so there is no run to perform. Reporting success for work that
    # did not happen is the failure mode this tool exists to remove from the process it
    # replaces, so it says so and exits 2.
    sys.stderr.write(
        "What: this build cannot perform a publishing run. "
        "Why: no product modules are loaded; the orchestrator is not implemented yet. "
        "Fix: use --show-config to inspect configuration, and track the orchestrator work.\n"
    )
    return EXIT_CANNOT_RUN
