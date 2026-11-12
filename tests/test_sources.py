"""The README and the mart manifest name the same public sources and licenses."""

from aire_abierto.livability.pipeline import _source_cards
from aire_abierto.paths import repo_root

# Phrases a reader must be able to find without opening the provenance files.
# Licenses were read from the publisher pages, not invented.
README_CITATIONS = (
    "http://scica.inecc.gob.mx/exec/datadl",
    "https://aire.jalisco.gob.mx/Dhistoricos",
    "https://aire.jalisco.gob.mx/reportes/BD_2025.xlsx",
    "NOM-172-SEMARNAT-2023",
    "https://www.datos.gob.mx/dataset/incidencia_delictiva",
    "57fbd692-3e5c-4b1b-8621-694cb3a33035",
    "https://www.datos.gob.mx/dataset/proyecciones-de-poblacion",
    "e9160552-769b-41ee-88d1-afc765552608",
    "https://creativecommons.org/licenses/by/4.0/",
    "https://www.inegi.org.mx/contenidos/inegi/doc/terminos_info.pdf",
    "Términos de Libre Uso",
    "https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2024_diciembre_presentacion_ejecutiva.pdf",
    "https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2025_catalogo_ciudades_interes.pdf",
    "https://www.geonames.org/",
    "Click That Hood",
    "SIL Open Font License",
    "data/livability/samples",
    "data/samples",
    "AIRE_OFFLINE",
    "--source synthetic",
)


def test_readme_cites_sources_and_licenses():
    readme = (repo_root() / "README.md").read_text(encoding="utf-8")
    english_at = readme.find("## English")
    spanish_at = readme.find("## Español")
    assert english_at != -1 and spanish_at != -1
    assert english_at < spanish_at
    missing = [phrase for phrase in README_CITATIONS if phrase not in readme]
    assert missing == []


def test_source_cards_match_the_publisher_license():
    cards = {card["id"]: card for card in _source_cards()}
    assert "CC BY 4.0" in cards["sesnsp"]["license"]
    assert "57fbd692-3e5c-4b1b-8621-694cb3a33035" in cards["sesnsp"]["license"]
    assert "creativecommons.org/licenses/by/4.0" in cards["sesnsp"]["license"]
    assert "CC BY 4.0" in cards["conapo"]["license"]
    assert "e9160552-769b-41ee-88d1-afc765552608" in cards["conapo"]["license"]
    assert "Términos de Libre Uso" in cards["ensu"]["license"]
    assert "Términos de Libre Uso" in cards["enigh"]["license"]
    assert "terminos_info.pdf" in cards["ensu"]["license"]
    assert "INECC" in cards["sinaica"]["license"]
    assert cards["sinaica"]["url"] == "http://scica.inecc.gob.mx/exec/datadl"
    assert "SEMADET" in cards["semadet"]["license"]
    assert cards["semadet"]["url"].startswith("https://aire.jalisco.gob.mx/")


def test_ci_workflow_uses_fixtures_and_blocks_the_network():
    workflow = (repo_root() / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert 'AIRE_OFFLINE: "1"' in workflow
    assert "--source sample" in workflow
    assert "--source synthetic" in workflow
    assert "--source live" not in workflow
    assert "livability.download" not in workflow


def test_provenance_files_name_the_same_licenses():
    root = repo_root()
    livability = (root / "data/livability/samples/PROVENANCE.md").read_text(encoding="utf-8")
    guadalajara = (root / "data/samples/PROVENANCE.md").read_text(encoding="utf-8")
    assert "CC BY 4.0" in livability
    assert "e9160552-769b-41ee-88d1-afc765552608" in livability
    assert "57fbd692-3e5c-4b1b-8621-694cb3a33035" in livability
    assert "Términos de Libre Uso" in livability
    assert "https://creativecommons.org/licenses/by/4.0/" in livability
    assert "SEMADET" in guadalajara
    assert "SPDX" in guadalajara
