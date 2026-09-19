"""Tests for the retention decision.

This is the only code that proposes destroying an artifact, on a bucket where a delete cannot be
undone, so the cases below are mostly about what it must refuse to prune.
"""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from software_update_publisher._contracts import Retention
from software_update_publisher.retention import PublishedVersion, select_prunable

_NOW = dt.datetime(2026, 9, 18, tzinfo=dt.UTC)


def _version(name: str, days_old: int) -> PublishedVersion:
    return PublishedVersion(version=name, published_at=_NOW - dt.timedelta(days=days_old), key=f"v/{name}")


class TestWhicheverIsGreater:
    def test_a_weekly_release_keeps_the_whole_window_not_just_three(self) -> None:
        # Eight weekly releases: the 30-day bound keeps five, which is more than three.
        weekly = [_version(f"1.{i}", i * 7) for i in range(8)]
        decision = select_prunable(weekly, Retention(), pinned=frozenset(), now=_NOW)
        assert [v.version for v in decision.kept] == ["1.0", "1.1", "1.2", "1.3", "1.4"]
        assert [v.version for v in decision.prunable] == ["1.5", "1.6", "1.7"]

    def test_a_yearly_release_keeps_three_not_just_the_current_one(self) -> None:
        # Nothing but the newest is inside 30 days, so the version count is the generous bound.
        yearly = [_version("3.0", 10), _version("2.0", 400), _version("1.0", 800), _version("0.9", 1200)]
        decision = select_prunable(yearly, Retention(), pinned=frozenset(), now=_NOW)
        assert [v.version for v in decision.kept] == ["3.0", "2.0", "1.0"]
        assert [v.version for v in decision.prunable] == ["0.9"]

    def test_fewer_versions_than_the_bound_prunes_nothing(self) -> None:
        decision = select_prunable([_version("1.0", 900)], Retention(), pinned=frozenset(), now=_NOW)
        assert decision.prunable == ()

    def test_nothing_published_prunes_nothing(self) -> None:
        assert select_prunable([], Retention(), pinned=frozenset(), now=_NOW).prunable == ()


class TestGuards:
    def test_a_pinned_version_is_never_prunable_however_old(self) -> None:
        # The mirror is additive, so a console that already holds it keeps working -- but a host
        # rebuilt after the prune would find nothing to install, long after and far from the prune.
        old = [_version("3.0", 10), _version("2.0", 400), _version("1.0", 800), _version("0.9", 1200)]
        decision = select_prunable(old, Retention(), pinned=frozenset({"0.9"}), now=_NOW)
        assert decision.prunable == ()
        assert decision.reasons["0.9"] == "the fleet pins this version"

    def test_every_kept_version_says_why_it_was_kept(self) -> None:
        # A prune that cannot explain what it spared is one nobody will authorise twice.
        versions = [_version(f"1.{i}", i * 7) for i in range(8)]
        decision = select_prunable(versions, Retention(), pinned=frozenset(), now=_NOW)
        assert all(v.version in decision.reasons for v in decision.kept)

    def test_ordering_is_by_publication_not_by_version_string(self) -> None:
        # Version strings here are not all comparable: some are vendor formats, some are minted.
        # A comparator wrong about one product would delete the wrong artifact silently.
        out_of_order = [_version("1.9", 1), _version("10.0", 400), _version("2.0", 2)]
        decision = select_prunable(out_of_order, Retention(keep_versions=1, keep_days=1), pinned=frozenset(), now=_NOW)
        assert [v.version for v in decision.kept] == ["1.9"]
        assert [v.version for v in decision.prunable] == ["2.0", "10.0"]

    def test_the_newest_version_is_kept_even_with_the_narrowest_retention(self) -> None:
        versions = [_version("2.0", 0), _version("1.0", 999)]
        decision = select_prunable(versions, Retention(keep_versions=1, keep_days=1), pinned=frozenset(), now=_NOW)
        assert [v.version for v in decision.kept] == ["2.0"]


class TestDeclaration:
    @pytest.mark.parametrize("bad", [{"keep_versions": 0}, {"keep_days": 0}, {"keep_versions": -1}])
    def test_a_bound_that_keeps_nothing_is_rejected(self, bad: dict[str, int]) -> None:
        with pytest.raises(ValidationError):
            Retention(**bad)

    def test_a_product_may_declare_its_own_bounds(self) -> None:
        decision = select_prunable(
            [_version(f"1.{i}", i * 7) for i in range(8)],
            Retention(keep_versions=2, keep_days=7),
            pinned=frozenset(),
            now=_NOW,
        )
        assert [v.version for v in decision.kept] == ["1.0", "1.1"]
