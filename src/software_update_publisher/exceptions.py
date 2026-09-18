"""Typed exception hierarchy.

Every error carries What happened, Why it happened, and how to Fix it, because the operator
reading a failed scheduled run has no other context. A message that names only the symptom
costs a debugging session.
"""

from __future__ import annotations


class PublisherError(Exception):
    """Base exception carrying What, Why, and Fix details."""

    what: str
    why: str
    fix: str

    def __init__(self, *, what: str, why: str, fix: str) -> None:
        self.what = what
        self.why = why
        self.fix = fix
        super().__init__(f"What: {what} Why: {why} Fix: {fix}")


class DeclarationError(PublisherError, ValueError):
    """Raised when a product module's declaration is not internally consistent.

    This is a defect in this repository, not a condition of the outside world, so it is raised
    before any network call and it fails the run rather than skipping the product.
    """


class IdentityError(PublisherError):
    """Raised when an artifact's Add/Remove Programs identity cannot be established.

    Not every artifact has one -- an archive never will -- and that case is declared, not raised.
    This is for an artifact that was declared extractable and then was not.
    """
