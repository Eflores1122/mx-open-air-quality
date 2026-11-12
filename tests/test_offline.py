"""Offline builds stay on fixtures even when a live refresh is requested."""

from datetime import date

import pytest

from aire_abierto.ingest import IngestError, acquire
from aire_abierto.livability.pipeline import run_livability
from aire_abierto.offline import OfflineError
from aire_abierto.paths import repo_root


def test_guadalajara_live_stops_before_the_network(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRE_OFFLINE", "1")
    calls = {"n": 0}

    def _boom(*args, **kwargs):
        calls["n"] += 1
        raise AssertionError("urlopen")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    with pytest.raises(IngestError, match="AIRE_OFFLINE"):
        acquire("live", year=2025, root=repo_root(), work_dir=tmp_path)
    assert calls["n"] == 0


def test_guadalajara_auto_uses_the_excerpt_when_offline(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRE_OFFLINE", "1")
    acquired = acquire("auto", year=2025, root=repo_root(), work_dir=tmp_path)
    assert acquired.data_kind == "official_excerpt"
    assert acquired.source_mode == "auto"
    assert "AIRE_OFFLINE" in (acquired.fallback_reason or "")


def test_livability_live_stops_before_the_network(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRE_OFFLINE", "1")
    calls = {"n": 0}

    def _boom(*args, **kwargs):
        calls["n"] += 1
        raise AssertionError("urlopen")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    with pytest.raises(OfflineError, match="AIRE_OFFLINE"):
        run_livability(source="live", out_dir=tmp_path, as_of=date(2026, 11, 5))
    assert calls["n"] == 0


def test_cli_prints_the_offline_refusal(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AIRE_OFFLINE", "1")
    from aire_abierto.livability.pipeline import main as livability_main
    from aire_abierto.pipeline import main as guadalajara_main

    assert guadalajara_main(["--source", "live", "--year", "2025", "--out", str(tmp_path / "gdl")]) == 2
    assert "AIRE_OFFLINE" in capsys.readouterr().err
    assert livability_main(["--source", "live", "--out", str(tmp_path / "national")]) == 2
    assert "AIRE_OFFLINE" in capsys.readouterr().err


def test_livability_auto_uses_the_committed_fixtures_when_offline(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRE_OFFLINE", "1")
    result = run_livability(source="auto", out_dir=tmp_path, as_of=date(2026, 11, 5))
    assert result["ok"] is True
    assert result["manifest"]["source_mode"] == "sample"
    assert result["manifest"]["data_kind"] == "official_excerpt"
    assert "AIRE_OFFLINE" in (result["manifest"]["fallback_reason"] or "")
