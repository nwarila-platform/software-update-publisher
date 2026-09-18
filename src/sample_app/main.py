"""CLI and worked sample function for the generic package."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from pydantic import ValidationError

from ._contracts import Result, ResultCode, TextRequest
from .config import load


def build_message(text: str, repeat: int = 1) -> Result[str]:
    """Validate input and render a configured sample greeting."""
    try:
        request = TextRequest(text=text, repeat=repeat)
    except ValidationError as exc:
        return Result[str](code=ResultCode.INVALID, error=str(exc))

    settings = load()
    message = " ".join(f"{settings.greeting}, {request.text.strip()}!" for _ in range(request.repeat))
    return Result[str](code=ResultCode.OK, value=message)


def _parser(default_text: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the sample package self-demo.")
    parser.add_argument("text", nargs="?", default=default_text, help="Text to include in the demo output.")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to render the message.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the sample CLI."""
    settings = load()
    args = _parser(settings.default_name).parse_args(argv)
    result = build_message(args.text, args.repeat)

    if result.code is ResultCode.OK and result.value is not None:
        sys.stdout.write(f"{result.value}\n")
        return 0

    sys.stderr.write(f"{result.error or 'Unknown sample_app error'}\n")
    return 2
