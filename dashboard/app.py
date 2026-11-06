"""Civic dashboard for the Guadalajara public air-quality file."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from aire_abierto.bands import BANDS
from aire_abierto.health import compose_note

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "data" / "metrics"

COLORS = {
    "buena": "#00E400",
    "aceptable": "#FFFF00",
    "mala": "#FF7E00",
    "muy_mala": "#FF0000",
    "extremadamente_mala": "#8F3F97",
}
TINT = {
    "buena": "#E7F8E7",
    "aceptable": "#FFF8CC",
    "mala": "#FFE8D2",
    "muy_mala": "#FFDCDC",
    "extremadamente_mala": "#F4E6F6",
}
LABEL = {
    "es": {
        "buena": "Buena",
        "aceptable": "Aceptable",
        "mala": "Mala",
        "muy_mala": "Muy mala",
        "extremadamente_mala": "Extremadamente mala",
    },
    "en": {
        "buena": "Good",
        "aceptable": "Acceptable",
        "mala": "Poor",
        "muy_mala": "Very poor",
        "extremadamente_mala": "Extremely poor",
    },
}
POLLUTANT = {
    "es": {
        "pm25": "PM2.5",
        "pm10": "PM10",
        "o3": "Ozono",
        "no2": "NO2",
        "so2": "SO2",
        "co": "CO",
    },
    "en": {
        "pm25": "PM2.5",
        "pm10": "PM10",
        "o3": "Ozone",
        "no2": "NO2",
        "so2": "SO2",
        "co": "CO",
    },
}

COPY = {
    "es": {
        "title": "Aire abierto",
        "subtitle": "Zona metropolitana de Guadalajara. Lectura ciudadana de datos públicos, no un producto de empresa.",
        "language": "Idioma de la interfaz",
        "missing": "Todavía no hay métricas. En la raíz del repositorio corre: `python -m aire_abierto.pipeline --source sample`",
        "days_poor": "Días en Mala o peor",
        "worst_station": "Estación con más días así",
        "usual_pollutant": "Contaminante que más marca el día",
        "newest": "Hora más reciente del archivo",
        "trend": "Tendencia diaria",
        "trend_help": "La línea es la mediana de PM2.5 entre estaciones con al menos 18 horas válidas. El color es la peor banda de ese día, no el índice horario oficial.",
        "rank": "Estaciones con más días en Mala o peor",
        "day": "Día",
        "stations_that_day": "Estaciones ese día",
        "how": "Cómo se lee",
        "quality": "Calidad de los datos",
        "sources": "Fuentes",
        "not_today": "Esto no dice cómo está el aire ahora.",
        "pm_axis": "Mediana de PM2.5 (µg/m³)",
        "days_axis": "Días en Mala, Muy mala o Extremadamente mala",
        "band": "Peor banda del día",
        "excerpt": "Este tablero está usando un extracto público de 14 días, no el año completo.",
        "synthetic": "Estos números son inventados. No describen el aire de Guadalajara ni de ninguna otra ciudad.",
        "official": "Archivo horario público de SEMADET. Es un cierre anual, no el reporte de esta hora.",
    },
    "en": {
        "title": "Open air",
        "subtitle": "Guadalajara metropolitan area. A civic reading of public data, not a company product.",
        "language": "Interface language",
        "missing": "Metrics are not built yet. From the repo root run: `python -m aire_abierto.pipeline --source sample`",
        "days_poor": "Days at Poor or worse",
        "worst_station": "Station with the most such days",
        "usual_pollutant": "Pollutant that most often sets the day",
        "newest": "Newest hour in the file",
        "trend": "Daily trend",
        "trend_help": "The line is the median PM2.5 across stations with at least 18 valid hours. Color is the worst band that day, not the official hourly index.",
        "rank": "Stations with the most Poor-or-worse days",
        "day": "Day",
        "stations_that_day": "Stations that day",
        "how": "How to read this",
        "quality": "Data quality",
        "sources": "Sources",
        "not_today": "This does not say what the air is like right now.",
        "pm_axis": "Median PM2.5 (µg/m³)",
        "days_axis": "Days at Poor, Very poor, or Extremely poor",
        "band": "Worst band of the day",
        "excerpt": "This dashboard is using a 14-day public excerpt, not the full year.",
        "synthetic": "These numbers are invented. They do not describe the air in Guadalajara or anywhere else.",
        "official": "Public SEMADET hourly workbook. It is an annual close, not this hour's report.",
    },
}


def main() -> None:
    st.set_page_config(
        page_title="Vivir en México",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    view = st.sidebar.radio(
        "Lectura",
        ("vivir", "gdl"),
        format_func=lambda code: "Vivir en México" if code == "vivir" else "Aire en Guadalajara",
    )
    language = st.sidebar.radio("Idioma / Language", ("es", "en"), format_func=lambda code: "Español" if code == "es" else "English")
    if view == "vivir":
        dashboard_dir = Path(__file__).resolve().parent
        if str(dashboard_dir) not in sys.path:
            sys.path.insert(0, str(dashboard_dir))
        from vivir import render

        render(language)
        return
    text = COPY[language]
    st.sidebar.caption(text["language"])

    loaded = _load()
    if loaded is None:
        st.title(text["title"])
        st.info(text["missing"])
        return

    metro, stations, rank, manifest, quality = loaded
    st.title(text["title"])
    st.markdown(text["subtitle"])
    _banner(manifest, text)
    _kpis(metro, rank, quality, text, language)
    _health(metro, text)
    _trend(metro, text, language)
    _ranking(rank, text, language)
    _day_table(metro, stations, text, language)
    _how(language)
    _quality(quality, language, text)
    _sources(manifest, language, text)


def _load():
    required = ["daily_metro.csv", "daily_station.csv", "station_rank.csv", "manifest.json"]
    if any(not (METRICS / name).is_file() for name in required):
        return None
    metro = pd.read_csv(METRICS / "daily_metro.csv", parse_dates=["day"])
    stations = pd.read_csv(METRICS / "daily_station.csv", parse_dates=["day"])
    rank = pd.read_csv(METRICS / "station_rank.csv")
    manifest = json.loads((METRICS / "manifest.json").read_text(encoding="utf-8"))
    quality_path = METRICS / "quality_report.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.is_file() else {}
    return metro, stations, rank, manifest, quality


def _banner(manifest: dict, text: dict) -> None:
    kind = manifest.get("data_kind")
    if kind == "synthetic":
        st.error(text["synthetic"])
    elif kind == "official_excerpt":
        st.warning(text["excerpt"])
    else:
        st.info(text["official"] + " " + text["not_today"])
    note = manifest.get("note_es") if text is COPY["es"] else manifest.get("note_en")
    if note:
        st.caption(note)


def _kpis(metro: pd.DataFrame, rank: pd.DataFrame, quality: dict, text: dict, language: str) -> None:
    poor_days = int(metro["worst_band"].isin(BANDS[2:]).sum()) if not metro.empty else 0
    if rank.empty:
        station = "—"
        pollutant = "—"
    else:
        top = rank.iloc[0]
        station = f"{top['station_name']} ({int(top['days_mala_or_worse'])})"
        pollutant = _pollutant_name(top.get("most_frequent_dominant"), language)
    newest = "—"
    for check in quality.get("checks", []):
        if check.get("id") == "freshness":
            newest = check.get("metrics", {}).get("max_date") or "—"
    columns = st.columns(4)
    columns[0].metric(text["days_poor"], poor_days)
    columns[1].metric(text["worst_station"], station)
    columns[2].metric(text["usual_pollutant"], pollutant)
    columns[3].metric(text["newest"], newest)


def _health(metro: pd.DataFrame, text: dict) -> None:
    if metro.empty:
        return
    latest = metro.sort_values("day").iloc[-1]
    day = latest["day"].date() if isinstance(latest["day"], datetime) else latest["day"]
    band = latest["worst_band"] if isinstance(latest["worst_band"], str) and latest["worst_band"] else None
    concentration = latest["dominant_value"]
    number = None if pd.isna(concentration) or concentration == "" else float(concentration)
    note = compose_note(
        day=day if isinstance(day, date) else date.fromisoformat(str(day)[:10]),
        band=band,
        station_name=latest["worst_station_name"] or None,
        pollutant=latest["dominant_pollutant"] if isinstance(latest["dominant_pollutant"], str) and latest["dominant_pollutant"] else None,
        concentration=number,
    )
    tint = TINT.get(band or "", "#F4F1EA")
    stripe = COLORS.get(band or "", "#1C2430")
    st.markdown(
        f"""
        <div style="border:1px solid #E4DED2;border-left:8px solid {stripe};background:{tint};
                    border-radius:12px;padding:16px 18px;margin:8px 0 18px 0;">
          <p style="margin:0 0 8px 0;">{note.es}</p>
          <p style="margin:0;">{note.en}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(note.disclaimer_es)
    st.caption(note.disclaimer_en)
    del text


def _trend(metro: pd.DataFrame, text: dict, language: str) -> None:
    st.subheader(text["trend"])
    st.caption(text["trend_help"])
    frame = metro.dropna(subset=["median_pm25"]).copy()
    if frame.empty:
        st.write("—")
        return
    frame["band_label"] = frame["worst_band"].map(LABEL[language]).fillna("—")
    line = (
        alt.Chart(frame)
        .mark_line(color="#0B6E4F", strokeWidth=2)
        .encode(
            x=alt.X("day:T", title=None),
            y=alt.Y("median_pm25:Q", title=text["pm_axis"]),
        )
    )
    points = (
        alt.Chart(frame)
        .mark_circle(size=64, stroke="#1C2430", strokeWidth=0.6)
        .encode(
            x="day:T",
            y="median_pm25:Q",
            color=alt.Color(
                "band_label:N",
                title=text["band"],
                scale=alt.Scale(
                    domain=[LABEL[language][band] for band in BANDS],
                    range=[COLORS[band] for band in BANDS],
                ),
            ),
            tooltip=[
                alt.Tooltip("day:T", title=text["day"]),
                alt.Tooltip("median_pm25:Q", format=".1f", title="PM2.5"),
                alt.Tooltip("band_label:N", title=text["band"]),
                alt.Tooltip("worst_station_name:N", title=""),
            ],
        )
    )
    st.altair_chart(alt.layer(line, points).properties(height=320), width="stretch")


def _ranking(rank: pd.DataFrame, text: dict, language: str) -> None:
    st.subheader(text["rank"])
    if rank.empty:
        return
    chart = (
        alt.Chart(rank)
        .mark_bar(color="#0B6E4F")
        .encode(
            x=alt.X("days_mala_or_worse:Q", title=text["days_axis"]),
            y=alt.Y("station_name:N", sort="-x", title=None),
            tooltip=[
                "station_name",
                "municipalities",
                "days_mala_or_worse",
                "days_with_index",
                "mean_pm25",
                "most_frequent_dominant",
            ],
        )
        .properties(height=max(280, 28 * len(rank)))
    )
    st.altair_chart(chart, width="stretch")
    show = rank.copy()
    show["most_frequent_dominant"] = show["most_frequent_dominant"].map(
        lambda value: _pollutant_name(value, language)
    )
    for column in ("mean_pm25", "mean_pm10"):
        if column in show:
            show[column] = show[column].map(lambda value: "" if pd.isna(value) else f"{float(value):.1f}")
    st.dataframe(
        show[
            [
                "station_name",
                "municipalities",
                "days_with_index",
                "days_buena",
                "days_aceptable",
                "days_mala",
                "days_muy_mala",
                "days_extremadamente_mala",
                "mean_pm25",
                "most_frequent_dominant",
            ]
        ],
        width="stretch",
        hide_index=True,
    )


def _day_table(metro: pd.DataFrame, stations: pd.DataFrame, text: dict, language: str) -> None:
    st.subheader(text["stations_that_day"])
    days = list(metro.sort_values("day", ascending=False)["day"])
    if not days:
        return
    chosen = st.selectbox(text["day"], days, format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"))
    one = stations[stations["day"] == chosen].copy()
    one["band_label"] = one["band"].map(LABEL[language]).fillna("—")
    one["dominant_pollutant"] = one["dominant_pollutant"].map(lambda value: _pollutant_name(value, language))
    one = one.sort_values(["band_rank", "pm25_rounded"], ascending=[False, False], na_position="last")
    st.dataframe(
        one[
            [
                "station_name",
                "municipalities",
                "band_label",
                "dominant_pollutant",
                "pm25_rounded",
                "pm25_n",
                "pm10_rounded",
                "o3_rounded_ppm",
                "o3_n",
                "no2_rounded_ppm",
                "co_rounded_ppm",
            ]
        ],
        width="stretch",
        hide_index=True,
    )


def _how(language: str) -> None:
    title = "Cómo se lee" if language == "es" else "How to read this"
    with st.expander(title):
        if language == "es":
            st.markdown(
                """
- La banda del día en cada estación es la peor entre PM2.5, PM10, ozono, NO2, SO2 y CO, cuando hay datos suficientes.
- PM2.5 y PM10 usan el promedio de 24 horas. Hacen falta al menos 18 horas válidas. La norma habla de ese promedio como la referencia de riesgo; el índice horario oficial usa además un promedio móvil ponderado de 12 horas, que aquí no se reproduce.
- Ozono, NO2 y SO2 usan la hora más alta del día, también con al menos 18 horas válidas. El CO usa el máximo de los promedios móviles de 8 horas con al menos 6 horas válidas en la ventana.
- Las partículas se leen con la columna de la NOM-172 que rige desde enero de 2026. En 2025 la banda Aceptable llegaba más arriba (PM2.5 hasta 33 µg/m³ y PM10 hasta 60). Aplicar el corte de 2026 a un archivo de 2025 es una lectura con la regla vigente, no la clasificación que se publicaba ese año.
- El día de la ciudad lo marca la peor estación. Así lo pide la norma para el índice que se difunde: el que muestra el mayor deterioro.
- Celdas con bandera (ND, IO, IR, IF, IC) se quedan vacías. No se rellenan.
- En el archivo de SEMADET la hora 00:00 es la hora que cierra el día anterior. El día civil se arma con ese criterio.
                """
            )
        else:
            st.markdown(
                """
- A station's daily band is the worst among PM2.5, PM10, ozone, NO2, SO2, and CO, when there is enough data.
- PM2.5 and PM10 use the 24-hour mean. At least 18 valid hours are required. The standard treats that mean as the health reference. The official hourly index also uses a 12-hour weighted average, which is not reproduced here.
- Ozone, NO2, and SO2 use the highest hour of the day, again with at least 18 valid hours. CO uses the highest 8-hour mean whose window has at least 6 valid hours.
- Particles use the NOM-172 column in force since January 2026. During 2025 the Acceptable band reached higher (PM2.5 up to 33 µg/m³ and PM10 up to 60). Applying the 2026 cut to a 2025 file is a reading under the current rule, not the classification published that year.
- The city day is set by the worst station. That is what the standard asks of the index shown to the public: the one with the greatest deterioration.
- Flagged cells (ND, IO, IR, IF, IC) stay empty. They are not filled in.
- In the SEMADET file, 00:00 is the hour that closes the previous day. Civil days are built that way.
                """
            )


def _quality(quality: dict, language: str, text: dict) -> None:
    with st.expander(text["quality"]):
        if not quality:
            st.write("—")
            return
        if not quality.get("ok", True):
            st.error("Hay controles que no pasan." if language == "es" else "Some checks failed.")
        detail = "detail_es" if language == "es" else "detail_en"
        for check in quality.get("checks", []):
            status = check.get("status", "")
            line = f"**{status} · {check.get('id')}.** {check.get(detail, '')}"
            if status == "fail":
                st.error(line)
            elif status == "warn":
                st.warning(line)
            else:
                st.write(line)
        nulls = {}
        for check in quality.get("checks", []):
            if check.get("id") == "null_rates":
                nulls = check.get("metrics", {}).get("null_rates") or {}
        if nulls:
            frame = pd.DataFrame(
                {"pollutant": list(nulls), "null_rate": [nulls[key] for key in nulls]}
            )
            st.bar_chart(frame.set_index("pollutant"))


def _sources(manifest: dict, language: str, text: dict) -> None:
    with st.expander(text["sources"]):
        if language == "es":
            st.markdown(
                f"""
- **Mediciones:** Secretaría de Medio Ambiente y Desarrollo Territorial de Jalisco (SEMADET), Sistema de Monitoreo Atmosférico de Jalisco (SIMAJ). Archivo horario público [`BD_AÑO.xlsx`](https://aire.jalisco.gob.mx/reportes/BD_2025.xlsx), listado en [Datos históricos](https://aire.jalisco.gob.mx/Dhistoricos).
- **Nombres de estación:** reporte diario de SEMADET y documentos públicos de contingencia. Santa Margarita aparece como SMT en el archivo de 2025 y como SMA en documentos anteriores.
- **Bandas:** NOM-172-SEMARNAT-2023, Diario Oficial de la Federación, 25 de enero de 2024, tablas 4 a 9.
- **Este repositorio** no es SEMADET, no es SEMARNAT y no es un aviso oficial.
- Archivo usado en esta construcción: `{manifest.get("data_kind")}`, SHA-256 `{manifest.get("sha256", "")[:16]}…`.
                """
            )
        else:
            st.markdown(
                f"""
- **Measurements:** Jalisco's environment secretariat (SEMADET), Jalisco air-monitoring system (SIMAJ). Public hourly workbook [`BD_YEAR.xlsx`](https://aire.jalisco.gob.mx/reportes/BD_2025.xlsx), listed under [Historical data](https://aire.jalisco.gob.mx/Dhistoricos).
- **Station names:** SEMADET's daily report and public contingency documents. Santa Margarita is SMT in the 2025 file and SMA in older documents.
- **Bands:** NOM-172-SEMARNAT-2023, Official Gazette, 25 January 2024, tables 4 to 9.
- **This repository** is not SEMADET, not SEMARNAT, and not an official alert.
- File used for this build: `{manifest.get("data_kind")}`, SHA-256 `{str(manifest.get("sha256", ""))[:16]}…`.
                """
            )


def _pollutant_name(value: object, language: str) -> str:
    if not isinstance(value, str) or not value or (isinstance(value, float)):
        return "—"
    return POLLUTANT[language].get(value, value)


def _css() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #F6F4EF; }
          h1 { letter-spacing: -0.03em; }
          [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
