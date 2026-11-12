"""Keep the suite on committed fixtures.

Every test replaces ``urllib.request.urlopen``. A regression that fetches
INECC, SEMADET, datos.gob.mx, or INEGI fails here instead of depending on
those sites. Live refresh is covered by tests that set ``AIRE_OFFLINE`` and
assert the call stops before a socket opens.
"""

from __future__ import annotations

import urllib.request

import pytest


@pytest.fixture(autouse=True)
def block_public_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "A test tried to open the network. Use the committed fixtures "
            "under data/samples and data/livability/samples, or the synthetic generator."
        )

    monkeypatch.setattr(urllib.request, "urlopen", _refuse)
