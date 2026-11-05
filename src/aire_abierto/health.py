"""Plain-language health notes in Spanish and English.

Wording follows the categories and the spirit of the messages in
NOM-172-SEMARNAT-2023, table 12. It is shortened for a daily retrospective
and it is not a medical instruction or the official hourly bulletin.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

BAND_LABEL = {
    "es": {
        "buena": "Buena, riesgo bajo",
        "aceptable": "Aceptable, riesgo moderado",
        "mala": "Mala, riesgo alto",
        "muy_mala": "Muy mala, riesgo muy alto",
        "extremadamente_mala": "Extremadamente mala, riesgo extremadamente alto",
    },
    "en": {
        "buena": "Good, low risk",
        "aceptable": "Acceptable, moderate risk",
        "mala": "Poor, high risk",
        "muy_mala": "Very poor, very high risk",
        "extremadamente_mala": "Extremely poor, extremely high risk",
    },
}

ADVICE = {
    "es": {
        "buena": (
            "Para esta banda, la norma describe un riesgo mínimo o nulo. "
            "Se puede hacer actividad al aire libre."
        ),
        "aceptable": (
            "Quien es sensible al ozono o a las partículas —niñas y niños, "
            "personas mayores, personas gestantes o quien vive con asma— puede "
            "notar irritación, tos o falta de aire. El resto puede seguir con "
            "actividad moderada. Conviene revisar el reporte horario oficial "
            "si el día cambia."
        ),
        "mala": (
            "Conviene reducir el ejercicio intenso al aire libre, como correr "
            "o jugar un partido. Si aparece tos o falta de aire, hay que parar "
            "y descansar. Quien vive con una enfermedad respiratoria o del "
            "corazón necesita más descansos."
        ),
        "muy_mala": (
            "Conviene acortar el tiempo al aire libre y evitar el esfuerzo "
            "fuerte o prolongado. Si la actividad puede hacerse en un interior "
            "sin humo de tabaco, es mejor moverla ahí. Ante síntomas, hay que "
            "consultar a la médica o al médico."
        ),
        "extremadamente_mala": (
            "Conviene permanecer en interiores y dejar para otro momento lo "
            "que iba a hacerse al aire libre. Si hay síntomas respiratorios o "
            "cardiacos intensos, hay que buscar atención médica."
        ),
    },
    "en": {
        "buena": (
            "For this band, the standard describes minimal or no health risk. "
            "Outdoor activity is fine."
        ),
        "aceptable": (
            "People sensitive to ozone or particles — children, older adults, "
            "pregnant people, and anyone with asthma — may notice irritation, "
            "cough, or shortness of breath. Others can keep up moderate activity. "
            "Check the official hourly report if the day changes."
        ),
        "mala": (
            "Ease off vigorous outdoor exercise such as running or a competitive "
            "game. If you start coughing or feel short of breath, stop and rest. "
            "People with a respiratory or heart condition need more breaks."
        ),
        "muy_mala": (
            "Spend less time outdoors and skip hard or long exertion. If the "
            "activity can move indoors to a tobacco-smoke-free place, that is "
            "the better option. If symptoms show up, talk to a clinician."
        ),
        "extremadamente_mala": (
            "Stay indoors and postpone outdoor plans. If respiratory or heart "
            "symptoms are severe, seek medical care."
        ),
    },
}

POLLUTANT = {
    "es": {
        "pm25": "las partículas finas PM2.5",
        "pm10": "las partículas PM10",
        "o3": "el ozono",
        "no2": "el dióxido de nitrógeno",
        "so2": "el dióxido de azufre",
        "co": "el monóxido de carbono",
    },
    "en": {
        "pm25": "fine particles (PM2.5)",
        "pm10": "PM10 particles",
        "o3": "ozone",
        "no2": "nitrogen dioxide",
        "so2": "sulfur dioxide",
        "co": "carbon monoxide",
    },
}

DISCLAIMER = {
    "es": (
        "Esta nota es una lectura ciudadana de mediciones públicas. Usa las "
        "bandas de la NOM-172-SEMARNAT-2023 para orientar. No sustituye el "
        "Índice AIRE y SALUD horario de SEMADET, un aviso de contingencia ni "
        "la opinión de una médica o un médico. Para el aire de hoy: "
        "https://aire.jalisco.gob.mx/"
    ),
    "en": (
        "This note is a civic reading of public measurements. It uses the "
        "bands in NOM-172-SEMARNAT-2023 as guidance. It is not SEMADET's "
        "official hourly Índice AIRE y SALUD, not a contingency alert, and "
        "not medical advice. For today's air: https://aire.jalisco.gob.mx/"
    ),
}

_MONTHS_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
_MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


@dataclass(frozen=True)
class HealthNote:
    es: str
    en: str
    disclaimer_es: str
    disclaimer_en: str


def format_day(day: date, language: str) -> str:
    if language == "es":
        return f"{day.day} de {_MONTHS_ES[day.month - 1]} de {day.year}"
    return f"{_MONTHS_EN[day.month - 1]} {day.day}, {day.year}"


def format_concentration(pollutant: str, value: float) -> str:
    if pollutant in {"pm10", "pm25"}:
        return f"{int(round_display(value))} µg/m³"
    if pollutant == "co":
        return f"{value:.2f} ppm"
    ppb = int(round_display(value * 1000))
    return f"{value:.3f} ppm ({ppb} ppb)"


def round_display(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compose_note(
    *,
    day: date,
    band: str | None,
    station_name: str | None,
    pollutant: str | None,
    concentration: float | None,
) -> HealthNote:
    if band is None or station_name is None or pollutant is None or concentration is None:
        es_day = format_day(day, "es")
        en_day = format_day(day, "en")
        return HealthNote(
            es=(
                f"El {es_day} no hay suficientes horas válidas para clasificar "
                "el día en la zona metropolitana. Este proyecto pide al menos "
                "18 horas válidas de partículas o de gases horarios antes de "
                "asignar una banda."
            ),
            en=(
                f"On {en_day} there are not enough valid hours to classify the "
                "day across the metropolitan area. This project asks for at "
                "least 18 valid hours of particles or hourly gases before it "
                "assigns a band."
            ),
            disclaimer_es=DISCLAIMER["es"],
            disclaimer_en=DISCLAIMER["en"],
        )

    value = format_concentration(pollutant, concentration)
    es = (
        f"El {format_day(day, 'es')}, la estación con la peor banda del día "
        f"fue {station_name} ({BAND_LABEL['es'][band]}). Quedó marcada por "
        f"{POLLUTANT['es'][pollutant]}, con {value}. {ADVICE['es'][band]}"
    )
    en = (
        f"On {format_day(day, 'en')}, the station with the worst band of the "
        f"day was {station_name} ({BAND_LABEL['en'][band]}). It was set by "
        f"{POLLUTANT['en'][pollutant]}, at {value}. {ADVICE['en'][band]}"
    )
    return HealthNote(
        es=es,
        en=en,
        disclaimer_es=DISCLAIMER["es"],
        disclaimer_en=DISCLAIMER["en"],
    )
