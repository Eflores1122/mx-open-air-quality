"""Refuse publisher downloads when CI, or a caller, asks for fixtures only.

``AIRE_OFFLINE=1`` is set on the GitHub Actions test job. ``--source sample``
reads the committed excerpts. ``--source synthetic`` writes invented rows.
Neither path calls this guard. ``--source live`` and the refresh module do.
"""

from __future__ import annotations

import os

OFFLINE_ENV = "AIRE_OFFLINE"


class OfflineError(RuntimeError):
    """A download was requested while network access is turned off."""


def network_disabled() -> bool:
    return os.environ.get(OFFLINE_ENV, "").strip().lower() in {"1", "true", "yes"}


def require_network(action: str) -> None:
    if network_disabled():
        raise OfflineError(
            f"{action} needs the public network, and {OFFLINE_ENV} is set. "
            "Use the committed fixtures (--source sample) or the synthetic "
            "generator (--source synthetic)."
        )
