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
    pinned: frozenset[str],
    now: dt.datetime,
) -> RetentionDecision:
    """Return which of *versions* may be pruned under *retention*.

    ``pinned`` names versions the consuming fleet still depends on. They are never prunable
    whatever their age or rank: the repository mirror is additive, so a console that already holds
    one keeps working, but a host rebuilt after the prune would find nothing to install. That
    failure appears long after the prune and nowhere near it.
    """
    ordered = sorted(versions, key=lambda candidate: candidate.published_at, reverse=True)
    cutoff = now - dt.timedelta(days=retention.keep_days)

    kept: list[PublishedVersion] = []
    prunable: list[PublishedVersion] = []
    reasons: dict[str, str] = {}

    for rank, candidate in enumerate(ordered, start=1):
        if candidate.version in pinned:
            reasons[candidate.version] = "the fleet pins this version"
        elif rank <= retention.keep_versions:
            reasons[candidate.version] = f"among the newest {retention.keep_versions}"
        elif candidate.published_at >= cutoff:
            reasons[candidate.version] = f"published within {retention.keep_days} days"
        else:
            prunable.append(candidate)
            continue
        kept.append(candidate)

    return RetentionDecision(prunable=tuple(prunable), kept=tuple(kept), reasons=reasons)
