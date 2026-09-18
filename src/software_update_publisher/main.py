"""Command-line entry point.

The orchestrator and the product modules are not here yet. What this file already owns is the
argument surface and the exit-code contract, because those are what a scheduled run is read
through: 0 means the run did what it set out to do, 2 means it could not run at all.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ._version import __version__
from .config import load

EXIT_OK = 0
EXIT_CANNOT_RUN = 2


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line."""
    args = _parser().parse_args(argv)
    settings = load()

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
