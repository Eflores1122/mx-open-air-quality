from datetime import date

from aire_abierto.health import compose_note


def test_note_is_spanish_and_english_and_names_the_station():
    note = compose_note(
        day=date(2025, 5, 3),
        band="mala",
        station_name="Miravalle",
        pollutant="pm25",
        concentration=48,
    )
    assert "Miravalle" in note.es
    assert "Miravalle" in note.en
    assert "3 de mayo de 2025" in note.es
    assert "May 3, 2025" in note.en
    assert "48 µg/m³" in note.es
    assert "marcada por las partículas finas" in note.es
    assert "aire libre" in note.es
    assert "outdoor" in note.en
    assert "https://aire.jalisco.gob.mx/" in note.disclaimer_es
    assert "not medical advice" in note.disclaimer_en


def test_missing_hours_do_not_invent_a_band():
    note = compose_note(
        day=date(2025, 5, 3),
        band=None,
        station_name=None,
        pollutant=None,
        concentration=None,
    )
    assert "suficientes horas" in note.es
    assert "not enough valid hours" in note.en
