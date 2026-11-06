"""Invented rows with the same columns as the public excerpts.

They exist so the mart can be built with no network and no committed
files. Names and figures are round on purpose. They do not describe a
place in Mexico.
"""

from __future__ import annotations

from aire_abierto.livability.mart import Bundle


def synthetic_bundle() -> Bundle:
    return Bundle(
        data_kind="synthetic",
        networks=[
            {
                "network_code": "SYN",
                "network_name": "Red inventada",
                "place_name": "Ciudad Ejemplo",
                "state_name": "Estado Ejemplo",
                "attach_ensu_city": "Ciudad Ejemplo",
                "safety_mode": "inherit",
                "safety_ensu_cities": "",
                "safety_mun_names": "",
                "note_es": "Dato inventado.",
                "note_en": "Invented figure.",
            }
        ],
        air=[
            {
                "network_code": "SYN",
                "network_name": "Red inventada",
                "year": "2022",
                "pm25_median_ugm3": "20",
                "pm25_mean_ugm3": "21",
                "pm25_worst_ugm3": "30",
                "worst_station": "SYN-1",
                "stations_valid": "2",
                "stations_in_file": "2",
                "min_daily_hours": "18",
                "min_valid_days": "274",
                "days_in_file": "300",
                "valid": "True",
            }
        ],
        crime=[
            {
                "mun_code": "90001",
                "state_code": "90",
                "state_name": "Estado Ejemplo",
                "mun_name": "Municipio Ejemplo",
                "year": "2025",
                "homicidio_doloso": "10",
                "feminicidio": "2",
                "secuestro": "1",
                "extorsion": "4",
            },
            {
                "mun_code": "90002",
                "state_code": "90",
                "state_name": "Estado Ejemplo",
                "mun_name": "Municipio Tranquilo",
                "year": "2025",
                "homicidio_doloso": "1",
                "feminicidio": "0",
                "secuestro": "0",
                "extorsion": "0",
            },
        ],
        population=[
            {
                "mun_code": "90001",
                "state_code": "90",
                "state_name": "Estado Ejemplo",
                "mun_name": "Municipio Ejemplo",
                "year": "2025",
                "population": "100000",
            },
            {
                "mun_code": "90002",
                "state_code": "90",
                "state_name": "Estado Ejemplo",
                "mun_name": "Municipio Tranquilo",
                "year": "2025",
                "population": "50000",
            },
        ],
        perception=[
            {
                "ensu_city": "Ciudad Ejemplo",
                "september_pct": "40",
                "december_pct": "50",
                "change_pct": "25",
                "period": "2024-12",
                "comparison": "2024-09",
            }
        ],
        catalog=[
            {
                "ensu_city": "Ciudad Ejemplo",
                "ensu_city_code": "99",
                "state_code": "90",
                "state_name": "Estado Ejemplo",
                "mun_code": "90001",
                "mun_name": "Municipio Ejemplo",
                "cvegeo_example": "900010001",
            }
        ],
        rent=[
            {
                "state_name": "Estado Ejemplo",
                "year": "2024",
                "imputed_rent_quarterly_mxn": "9000",
                "table_title": "synthetic",
                "column_name": "synthetic",
            }
        ],
        semadet=None,
    )
