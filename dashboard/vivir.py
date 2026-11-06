"""National comparison: air, approximate rent, and safety."""

from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from aire_abierto.livability.scoring import COMBINED_WEIGHTS, combine

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "data" / "livability" / "metrics"

COPY = {
    "es": {
        "title": "Vivir en México",
        "subtitle": "Aire, renta aproximada y seguridad, con fuentes públicas. No es un consejo para mudarse.",
        "disclaimer": "Esto no es consejo oficial, ni médico, ni una evaluación de tu riesgo. Las cifras son históricas y, en la renta, aproximadas. No dicen cómo está el aire hoy ni si una calle es segura.",
        "missing": "Todavía no hay mart. En la raíz del repositorio corre: `python -m aire_abierto.livability.pipeline --source sample`",
        "weights": "Pesos del puntaje",
        "weights_help": "El puntaje combina lo que sí tiene número y reescala los pesos. Cero deja fuera esa pieza.",
        "air": "Aire",
        "safety": "Seguridad",
        "perception": "Percepción",
        "rent_w": "Renta",
        "state": "Entidad",
        "types": "Tipo de lugar",
        "city": "Ciudad ENSU",
        "network": "Red de monitoreo",
        "state_type": "Entidad federativa",
        "sort": "Ordenar por",
        "combined": "Puntaje con renta",
        "quality": "Calidad sin renta",
        "table": "Lugares",
        "chart": "Costo y calidad",
        "chart_help": "El eje horizontal es la renta imputada mensual del estado. El vertical es la calidad (aire, delitos y percepción) con los pesos de arriba, sin la renta. Un punto más arriba no es una recomendación.",
        "bars": "Puntaje con los pesos elegidos",
        "compare": "Comparar lugares",
        "pick": "Elige hasta tres",
        "how": "Cómo leerlo",
        "sources": "Fuentes",
        "checks": "Calidad de los datos",
        "synthetic": "Estos números son inventados. No describen ningún lugar de México.",
        "excerpt": "Este tablero usa extractos públicos guardados en el repositorio. No es una descarga en vivo de esta hora.",
        "live": "Este tablero se construyó descargando las fuentes públicas en esta corrida.",
        "empty": "Ningún lugar pasa el filtro.",
        "place": "Lugar",
        "pm25": "PM2.5 anual (µg/m³)",
        "rate": "Homicidio doloso + feminicidio por 100 mil",
        "feel": "Se siente inseguro (%)",
        "monthly": "Alquiler imputado mensual aprox. (pesos)",
        "score": "Puntaje",
        "note": "Nota",
        "type": "Tipo",
    },
    "en": {
        "title": "Living in Mexico",
        "subtitle": "Air, approximate rent, and safety, from public sources. Not advice about moving.",
        "disclaimer": "This is not official advice, not medical advice, and not a reading of your personal risk. The figures are historical and, for rent, approximate. They do not say what the air is like today or whether a street is safe.",
        "missing": "The mart is not built yet. From the repo root run: `python -m aire_abierto.livability.pipeline --source sample`",
        "weights": "Score weights",
        "weights_help": "The score uses the pieces that have a number and rescales the weights. Zero leaves that piece out.",
        "air": "Air",
        "safety": "Safety",
        "perception": "Perception",
        "rent_w": "Rent",
        "state": "State",
        "types": "Place type",
        "city": "ENSU city",
        "network": "Monitoring network",
        "state_type": "State",
        "sort": "Sort by",
        "combined": "Score with rent",
        "quality": "Quality without rent",
        "table": "Places",
        "chart": "Cost and quality",
        "chart_help": "The horizontal axis is the state's monthly imputed rent. The vertical axis is quality (air, lethal crime, and perception) using the weights above, without rent. A higher point is not a recommendation.",
        "bars": "Score with the chosen weights",
        "compare": "Compare places",
        "pick": "Choose up to three",
        "how": "How to read this",
        "sources": "Sources",
        "checks": "Data quality",
        "synthetic": "These numbers are invented. They do not describe any place in Mexico.",
        "excerpt": "This dashboard uses public excerpts stored in the repository. It is not a live download of this hour.",
        "live": "This dashboard was built by downloading the public sources for this run.",
        "empty": "No place matches the filter.",
        "place": "Place",
        "pm25": "Annual PM2.5 (µg/m³)",
        "rate": "Intentional homicide + feminicide per 100,000",
        "feel": "Feels unsafe (%)",
        "monthly": "Approx. monthly imputed rent (pesos)",
        "score": "Score",
        "note": "Note",
        "type": "Type",
    },
}

HOW = {
    "es": """
El **puntaje de calidad** junta aire, homicidio doloso más feminicidio, y la percepción de inseguridad. La **renta** va en el eje del costo y, si le das peso, también en el puntaje combinado.

- El aire es la mediana anual de PM2.5 de una red SINAICA, no el índice de hoy. Guadalajara conserva además el archivo de SEMADET, aparte del puntaje nacional.
- La seguridad del puntaje es una tasa de 2025 por 100 mil. Secuestro y extorsión se muestran y no entran al puntaje.
- La percepción es la ENSU de diciembre de 2024. Una ciudad puede tener un margen de error grande.
- La renta es el alquiler imputado de la ENIGH 2024 en el **estado**, partido entre 3. Dos ciudades del mismo estado comparten esa cifra. Una cifra baja no significa que el salario alcance.

Los pesos de arriba se pueden mover. Si falta un dato, ese peso se reparte entre lo que sí está.
""",
    "en": """
The **quality score** joins air, intentional homicide plus feminicide, and the perception of insecurity. **Rent** sits on the cost axis and, if you give it weight, in the combined score too.

- Air is the annual median PM2.5 of a SINAICA network, not today's index. Guadalajara also keeps the SEMADET file, outside the national score.
- The safety piece of the score is a 2025 rate per 100,000. Kidnapping and extortion are shown and stay out of the score.
- Perception is ENSU for December 2024. One city can have a wide margin of error.
- Rent is ENIGH 2024 imputed rent for the **state**, divided by 3. Two cities in the same state share that figure. A low figure does not mean local earnings cover it.

The weights above can be moved. If a figure is missing, its weight is shared by the pieces that exist.
""",
}

TYPE_LABEL = {
    "es": {"city": "Ciudad", "network": "Red", "state": "Entidad"},
    "en": {"city": "City", "network": "Network", "state": "State"},
}


def render(language: str) -> None:
    text = COPY[language]
    st.title(text["title"])
    st.markdown(text["subtitle"])
    st.warning(text["disclaimer"])
    loaded = _load()
    if loaded is None:
        st.info(text["missing"])
        return
    frame, manifest, quality = loaded
    _banner(manifest, text)
    weights = _weights(text)
    scored = _rescore(frame, weights)
    filtered = _filter(scored, text, language)
    if filtered.empty:
        st.info(text["empty"])
    else:
        sort_key = st.radio(
            text["sort"],
            ("quality_now", "score_now"),
            format_func=lambda key: text["quality"] if key == "quality_now" else text["combined"],
            horizontal=True,
        )
        _table(filtered, text, language, sort_key)
        _charts(filtered, text, sort_key)
        _compare(filtered, text, language)
    with st.expander(text["how"], expanded=False):
        st.markdown(HOW[language])
    _quality(quality, text)
    _sources(manifest, text)


def _load():
    mart = METRICS / "place_mart.csv"
    manifest_path = METRICS / "manifest.json"
    quality_path = METRICS / "quality_report.json"
    if not mart.is_file() or not manifest_path.is_file():
        return None
    frame = pd.read_csv(mart)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.is_file() else {"checks": []}
    return frame, manifest, quality


def _banner(manifest: dict, text: dict) -> None:
    kind = manifest.get("data_kind")
    if kind == "synthetic":
        st.error(text["synthetic"])
    elif kind == "official_live":
        st.info(text["live"])
    else:
        st.info(text["excerpt"])


def _weights(text: dict) -> dict[str, float]:
    st.sidebar.markdown(f"**{text['weights']}**")
    st.sidebar.caption(text["weights_help"])
    return {
        "air": st.sidebar.slider(text["air"], 0, 100, int(COMBINED_WEIGHTS["air"] * 100)) / 100,
        "safety": st.sidebar.slider(text["safety"], 0, 100, int(COMBINED_WEIGHTS["safety"] * 100)) / 100,
        "perception": st.sidebar.slider(text["perception"], 0, 100, int(COMBINED_WEIGHTS["perception"] * 100)) / 100,
        "rent": st.sidebar.slider(text["rent_w"], 0, 100, int(COMBINED_WEIGHTS["rent"] * 100)) / 100,
    }


def _rescore(frame: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    scored = frame.copy()
    combined: list[float | None] = []
    quality: list[float | None] = []
    quality_weights = {key: value for key, value in weights.items() if key != "rent"}
    for row in scored.itertuples(index=False):
        components = {
            "air": _none(getattr(row, "score_air")),
            "safety": _none(getattr(row, "score_safety")),
            "perception": _none(getattr(row, "score_perception")),
            "rent": _none(getattr(row, "score_rent")),
        }
        combined_score, _used = combine(components, weights, minimum=2)
        quality_score, _used_quality = combine(components, quality_weights, minimum=2)
        combined.append(combined_score)
        quality.append(quality_score)
    scored["score_now"] = combined
    scored["quality_now"] = quality
    return scored


def _filter(frame: pd.DataFrame, text: dict, language: str) -> pd.DataFrame:
    states = sorted(state for state in frame["state_name"].dropna().astype(str).unique() if state and state != "nan")
    chosen_states = st.sidebar.multiselect(text["state"], states)
    type_options = ["city", "network", "state"]
    chosen_types = st.sidebar.multiselect(
        text["types"],
        type_options,
        default=type_options,
        format_func=lambda code: TYPE_LABEL[language][code],
    )
    filtered = frame[frame["place_type"].isin(chosen_types)] if chosen_types else frame.iloc[0:0]
    if chosen_states:
        filtered = filtered[filtered["state_name"].isin(chosen_states)]
    return filtered


def _table(frame: pd.DataFrame, text: dict, language: str, sort_key: str) -> None:
    ordered = frame.sort_values(sort_key, ascending=False, na_position="last")
    show = ordered.assign(
        place_type_label=ordered["place_type"].map(TYPE_LABEL[language]),
        score_display=ordered[sort_key],
    )
    columns = {
        "place_name": text["place"],
        "place_type_label": text["type"],
        "state_name": text["state"],
        "air_pm25_median_ugm3": text["pm25"],
        "lethal_per_100k": text["rate"],
        "perception_insecurity_pct": text["feel"],
        "enigh_imputed_rent_monthly_approx_mxn": text["monthly"],
        "score_display": text["score"],
    }
    st.subheader(text["table"])
    st.dataframe(
        show[list(columns)].rename(columns=columns),
        use_container_width=True,
        hide_index=True,
        height=460,
    )


def _charts(frame: pd.DataFrame, text: dict, sort_key: str) -> None:
    left, right = st.columns(2)
    bars = frame.dropna(subset=[sort_key]).sort_values(sort_key, ascending=False).head(20)
    with left:
        st.subheader(text["bars"])
        if bars.empty:
            st.caption(text["empty"])
        else:
            chart = (
                alt.Chart(bars)
                .mark_bar(color="#0B6E4F")
                .encode(
                    x=alt.X(f"{sort_key}:Q", title=text["score"]),
                    y=alt.Y("place_name:N", sort="-x", title=None),
                    tooltip=["place_name", "state_name", sort_key],
                )
                .properties(height=420)
            )
            st.altair_chart(chart, use_container_width=True)
    scatter = frame.dropna(subset=["enigh_imputed_rent_monthly_approx_mxn", "quality_now"])
    with right:
        st.subheader(text["chart"])
        st.caption(text["chart_help"])
        if scatter.empty:
            st.caption(text["empty"])
        else:
            chart = (
                alt.Chart(scatter)
                .mark_circle(size=80, opacity=0.85)
                .encode(
                    x=alt.X("enigh_imputed_rent_monthly_approx_mxn:Q", title=text["monthly"]),
                    y=alt.Y("quality_now:Q", title=text["quality"]),
                    color=alt.Color("place_type:N", title=text["type"]),
                    tooltip=["place_name", "state_name", "quality_now", "enigh_imputed_rent_monthly_approx_mxn"],
                )
                .properties(height=420)
            )
            st.altair_chart(chart, use_container_width=True)


def _compare(frame: pd.DataFrame, text: dict, language: str) -> None:
    st.subheader(text["compare"])
    labeled = frame.assign(label=frame["place_name"].astype(str) + " · " + frame["place_type"].astype(str))
    picked = st.multiselect(text["pick"], labeled["label"].tolist(), max_selections=3)
    if len(picked) < 2:
        return
    subset = labeled[labeled["label"].isin(picked)]
    columns = st.columns(len(picked))
    note_column = "note_es" if language == "es" else "note_en"
    fields = [
        ("place_type", text["type"]),
        ("state_name", text["state"]),
        ("air_year", "Año aire" if language == "es" else "Air year"),
        ("air_pm25_median_ugm3", text["pm25"]),
        ("lethal_per_100k", text["rate"]),
        ("secuestro_per_100k", "Secuestro por 100 mil" if language == "es" else "Kidnapping per 100,000"),
        ("extorsion_per_100k", "Extorsión por 100 mil" if language == "es" else "Extortion per 100,000"),
        ("perception_insecurity_pct", text["feel"]),
        ("enigh_imputed_rent_monthly_approx_mxn", text["monthly"]),
        ("score_now", text["score"]),
    ]
    for column, name in zip(columns, picked, strict=False):
        row = subset[subset["label"] == name].iloc[0]
        with column:
            st.markdown(f"### {row['place_name']}")
            for key, label in fields:
                value = row.get(key, "")
                if pd.isna(value) or value == "":
                    value = "—"
                st.markdown(f"**{label}:** {value}")
            st.caption(str(row.get(note_column, "")))


def _quality(quality: dict, text: dict) -> None:
    st.subheader(text["checks"])
    for check in quality.get("checks", []):
        status = check["status"]
        line = f"{check['detail_es']} / {check['detail_en']}"
        if status == "fail":
            st.error(f"{check['id']}: {line}")
        elif status == "warn":
            st.warning(f"{check['id']}: {line}")
        else:
            st.caption(f"{check['id']}: {line}")


def _sources(manifest: dict, text: dict) -> None:
    st.subheader(text["sources"])
    for source in manifest.get("sources", []):
        st.markdown(
            f"**{source['publisher']}** · [{source['id']}]({source['url']})  \n"
            f"{source['vintage']}. {source['license']}"
        )


def _none(value: object) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
    except TypeError:
        if value is None:
            return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None
