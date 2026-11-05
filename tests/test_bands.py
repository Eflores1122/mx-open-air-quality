from aire_abierto.bands import band_for, classify, round_half_up, worst_band


def test_particle_edges_use_2026_cuts_and_exact_boundary_goes_to_the_worse_band():
    assert classify(14, "pm25") == "buena"
    assert classify(15, "pm25") == "aceptable"
    assert classify(25, "pm25") == "aceptable"
    assert classify(26, "pm25") == "mala"
    assert classify(79, "pm25") == "mala"
    assert classify(80, "pm25") == "muy_mala"
    assert classify(130, "pm25") == "muy_mala"
    assert classify(131, "pm25") == "extremadamente_mala"
    assert classify(44, "pm10") == "buena"
    assert classify(45, "pm10") == "aceptable"
    assert classify(50, "pm10") == "aceptable"
    assert classify(51, "pm10") == "mala"


def test_gas_edges_and_half_up_rounding():
    assert round_half_up(14.5, 0) == 15
    assert round_half_up(0.0575, 3) == 0.058
    rounded, band = band_for(0.0575, "o3", complete=True)
    assert rounded == 0.058
    assert band == "aceptable"
    assert classify(0.090, "o3") == "aceptable"
    assert classify(0.091, "o3") == "mala"
    assert classify(0.175, "o3") == "muy_mala"
    assert classify(0.176, "o3") == "extremadamente_mala"
    assert classify(5, "co") == "aceptable"
    assert classify(4.99, "co") == "buena"
    assert classify(0.304, "so2") == "muy_mala"
    assert classify(0.305, "so2") == "extremadamente_mala"


def test_incomplete_day_has_no_band_and_pm25_wins_a_tie():
    assert band_for(80, "pm25", complete=False) == (None, None)
    band, pollutant, rank = worst_band({"pm25": "mala", "o3": "mala", "pm10": "aceptable"})
    assert (band, pollutant, rank) == ("mala", "pm25", 2)
    assert worst_band({"pm25": None, "o3": None}) == (None, None, None)
