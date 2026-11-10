# Provenance of the livability excerpts

These files are small cuts or aggregations of public statistics so the
project rebuilds without the network. The code that refreshes them is
`python -m aire_abierto.livability.download` (module
`aire_abierto.livability.download`). CI does not run it.

Retrieved on 5 November 2026. Nothing behind a login was opened.

## Air — INECC SCICA / SINAICA

- Publisher: Instituto Nacional de Ecología y Cambio Climático (INECC)
- Page: http://scica.inecc.gob.mx/exec/datadl
- File used: hourly validated PM2.5, one network and one year, via the public form `POST /exec/addl`
- Excerpt: `sinaica_pm25_annual.csv` — annual median of station means, not the hourly file
- Rule: a station-day needs 18 hours; a station-year needs 75% of the days; the network figure is the median of those station means. The year is the newest one in which at least one station qualifies.
- Coverage in this cut: 39 networks. Years run from 2018 to 2023; 27 of them are 2022. Seven networks on the public list had no year that met the day rule (Gómez Palacio, Lerdo, Silao, Cuautla, Oaxaca, Tlaxcala estatal, Mérida).
- License: the download page does not state an SPDX license. The measurements stay attributed to INECC.

## Population — CONAPO

- Publisher: Consejo Nacional de Población (CONAPO), via datos.gob.mx
- Page: https://www.datos.gob.mx/dataset/proyecciones-de-poblacion
- File: `pobproy_inddemo.csv` (mid-year municipal population)
- Direct file: https://www.datos.gob.mx/dataset/f2b9b220-3ef7-4e3a-bde6-87e1dac78c6a/resource/e9160552-769b-41ee-88d1-afc765552608/download/pobproy_inddemo.csv
- Excerpt: `conapo_mun_2025.csv` — 2,475 municipalities, year 2025, column `POB_MIT_MUN`
- Sum of that column: 133,367,428 people

## Safety counts — SESNSP

- Publisher: Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública
- Page: https://www.datos.gob.mx/dataset/incidencia_delictiva
- License on that page: Creative Commons Attribution 4.0
- Resource id: `57fbd692-3e5c-4b1b-8621-694cb3a33035` (incidencia delictiva municipal, nueva metodología)
- The direct CSV `https://repodatos.atdt.gob.mx/api_update/sesnsp/incidencia_delictiva/IDM_NM_dic25.csv` returned HTTP 403 from the machine that built this excerpt. The rows were read from the public datastore API on datos.gob.mx, filtered to 2025 and to four crime types.
- Excerpt: `sesnsp_municipio_2025.csv` — one row per municipality, sums of homicidio doloso, feminicidio, secuestro, and extorsión. 2,486 municipalities. `sesnsp_raw_excerpt.csv` is the first 12 raw API rows, kept so the column names stay visible.
- Intentional homicide by month in 2025, national sum of the municipal file: January 2,008 through December 1,414. No month is empty, so 2025 is treated as a full year.
- The score uses homicidio doloso + feminicidio only. After joining to CONAPO, that is 20,649 deaths. The raw sum before dropping municipalities that are not in the population file is 20,677.

## Perception — INEGI ENSU

- Publisher: INEGI, Encuesta Nacional de Seguridad Pública Urbana
- Program: https://www.inegi.org.mx/programas/ensu/
- Perception: executive presentation for December 2024, https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2024_diciembre_presentacion_ejecutiva.pdf
- Excerpt: `ensu_percepcion_2024q4.csv` — 91 cities plus the national row. The figure is the December 2024 column (percent of people 18 and older who say living in their city is unsafe). The presentation says the city margins of error average about 11% and can be much wider.
- The December 2025 presentation was fetched. Its city chart does not keep the city names in the text layer, and the tabulados zip was not at the URLs this build probed, so 2025 perception is not in the mart.
- Municipalities: 2025 catalog PDF, https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2025_catalogo_ciudades_interes.pdf
- Excerpt: `ensu_municipios.csv`. Torreón (Coahuila, 5035) and Fresnillo (Zacatecas, 32010) are separate cities in the December 2024 perception table. The 2025 catalog extract did not list them as their own areas (Torreón sits inside La Laguna there). Those two municipality links were added from that 2024 composition so the 2024 percentages still have a denominator. They are the single head municipality, not a longer list.
- Corrected on 10 November 2026 against the same PDF. Two parser mistakes had survived in the first excerpt. Ramos Arizpe was stored as municipality 50270 because the PDF text prints CVEGEO `50270001` without the leading zero (it is `050270001`). Saltillo then failed the 90% coverage rule and published no rate. La Zacatecana, a locality of Guadalupe, Zacatecas, was rebuilt with Yucatán's state code because that cell is blank after Mérida, so the city of Zacatecas also carried Guadalupe, Yucatán (31017) and Yucatán's imputed rent. The excerpt now has Ramos Arizpe as 05027, and Zacatecas as Guadalupe (32017) and Zacatecas (32056) only. The mart was rebuilt from that file. The other excerpts were not re-downloaded.

## Rent — INEGI ENIGH 2024

- Publisher: INEGI, Encuesta Nacional de Ingresos y Gastos de los Hogares 2024
- Table: «Ingreso corriente total promedio trimestral por hogar, por entidad federativa según principales fuentes de ingreso, 2024»
- Column used: «Estimación del alquiler de la vivienda»
- Page: https://www.inegi.org.mx/app/tabulados/interactivos/?pxq=Hogares_Hogares_11_861f5732-c3db-4614-be03-741f649d605c
- Excerpt: `enigh_alquiler_imputado_2024.csv` — 32 states and the national row, quarterly pesos per household
- The interactive page needs a browser, so this file is a transcription of that published table made on 5 November 2026, not a second-hand estimate. The Estado de México value, 9,203 pesos, is the same figure the ENIGH 2024 results presentation prints for that state's imputed rent in 2024.
- It is an imputed rent for the average household, including owners. Dividing by 3 is this project's monthly reading. It is not a listing and it is not a city's rent.
- A machine-readable housing-price index from Sociedad Hipotecaria Federal was not retrieved. It is not in the mart. This project does not turn a price index into pesos.

## Map pins and state outlines

These files are not measurements. They only place the mart on a map.

- City pins: `data/livability/reference/place_points.csv`, joined from the GeoNames cities5000 dump (CC BY 4.0, https://www.geonames.org/), retrieved 10 November 2026. The match keeps a locality inside the same state. Each row stores the GeoNames id. La Laguna has no pin: the ENSU city crosses Coahuila and Durango, and this project does not invent a center. Tampico's pin is the locality Tampico in Tamaulipas; the ENSU city also includes municipalities in Veracruz. Los Cabos is pinned at San José del Cabo, the head locality named in the ENSU catalog.
- State outlines: `site/data/mexico_states.geojson`, simplified from Click That Hood `mexico.geojson` (MIT, Code for America, retrieved 10 November 2026). The license note is `site/data/STATES-LICENSE.txt`. The 2013 label Distrito Federal is shown as Ciudad de México. The geometry was simplified, not redrawn.
- Rebuild, when the dumps are on disk: `python3 scripts/build_map_reference.py --geonames cities5000.zip --states mexico.geojson --mart data/livability/metrics/place_mart.csv --points data/livability/reference/place_points.csv --geojson site/data/mexico_states.geojson`

## Guadalajara hourly file

The SEMADET series is unchanged. See `data/samples/PROVENANCE.md`. The livability mart only reads `data/metrics/daily_station.csv` when that build exists, and it does not put that PM2.5 into the national score.
