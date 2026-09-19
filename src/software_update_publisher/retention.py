"""Decides which published versions of a product may be pruned.

This is the only part of the system that proposes destroying something, and the bucket it
proposes destroying from has versioning disabled: a delete cannot be undone. So the rule is
written to be read, and the decision is a pure function over facts, separate from whatever
carries it out.

Two bounds apply and the more generous one wins. A version survives if it is among the newest
``keep_versions``, OR if it was published within ``keep_days``. A product shipping weekly keeps a
month of releases rather than only three; a product shipping once a year keeps three rather than
only the current one.

Ordering is by publication time, not by parsing the version string. Version strings here are not
all comparable -- some are vendor formats, some are minted by this tool -- and a comparator that
is wrong about one product would delete the wrong artifact silently.

**Retention takes no account of what any consumer holds, and cannot.** This tool knows nothing
about the systems that install the software it publishes: it emits a release document, and each
consumer polls that document and reconciles itself. Nothing here reaches into a consumer to ask
what it depends on, so nothing here can spare a version on a consumer's behalf.

That makes retention a published contract rather than an implementation detail. The window is
what a consumer can rely on being able to fetch; a consumer that reconciles within it never sees
a version disappear underneath it, and one that ignores the document for longer than the window
is outside the contract by its own choice. The window therefore belongs in the release document,
where the consumers that depend on it can see it.

The stakes are higher than bucket cost. A consumer that mirrors this repository deterministically
-- discarding whatever it holds that the repository no longer carries -- makes the window decide
what exists on its machines, not merely what exists here. Pruning is then a fleet-wide removal
performed by a nightly job, which is why the decision is a pure function with its reasons
attached rather than a side effect of the code that carries it out.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from ._contracts import Retention


@dataclass(frozen=True, slots=True)
class PublishedVersion:
    """One version of one product, as the repository holds it."""

    version: str
    published_at: dt.datetime
    key: str


@dataclass(frozen=True, slots=True)
class RetentionDecision:
    """What may be pruned, what is kept, and why each survivor survived.

    The reasons are carried so a run can report them. A prune that cannot explain what it spared
    is a prune nobody will authorise twice.
    """

    prunable: tuple[PublishedVersion, ...]
    kept: tuple[PublishedVersion, ...]
    reasons: dict[str, str]


def select_prunable(
    versions: list[PublishedVersion],
    retention: Retention,
    *,
    now: dt.datetime,
) -> RetentionDecision:
    """Return which of *versions* may be pruned under *retention*."""
    ordered = sorted(versions, key=lambda candidate: candidate.published_at, reverse=True)
    cutoff = now - dt.timedelta(days=retention.keep_days)

    kept: list[PublishedVersion] = []
    prunable: list[PublishedVersion] = []
    reasons: dict[str, str] = {}

    for rank, candidate in enumerate(ordered, start=1):
        if rank <= retention.keep_versions:
            reasons[candidate.version] = f"among the newest {retention.keep_versions}"
        elif candidate.published_at >= cutoff:
            reasons[candidate.version] = f"published within {retention.keep_days} days"
        else:
            prunable.append(candidate)
            continue
        kept.append(candidate)

    return RetentionDecision(prunable=tuple(prunable), kept=tuple(kept), reasons=reasons)
