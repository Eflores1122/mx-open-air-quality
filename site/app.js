(function () {
  const COPY = {
    es: {
      lede: "El ranking sale del mart de este repositorio ({places} lugares, corte del {day}). Mueve los pesos y cambian la tabla, el mapa y la ficha.",
      disclaimer: "No es un consejo para mudarse, ni el parte de hoy, ni la renta que vas a pagar.",
      warnRent: "La renta es el alquiler imputado de la ENIGH 2024 para el estado, dividido entre 3. Dos ciudades del mismo estado comparten la cifra. La Laguna, Tampico y la zona metropolitana del Valle de México no tienen la renta de un solo estado.",
      warnAir: "{one} de {air} cifras de PM2.5 salen de una sola estación. El año más antiguo de este corte es {year}.",
      warnExcerpt: "Estos números son los extractos públicos guardados en el repositorio, no una descarga de esta hora.",
      warnSynthetic: "Estos números son inventados. No describen ningún lugar de México.",
      warnLive: "Este corte se armó descargando las fuentes públicas en esa corrida. Sigue sin ser el aire de ahora.",
      weightHelp: "El puntaje reescala los pesos de las piezas que tienen número. Cero deja fuera esa pieza. Hacen falta al menos dos.",
      needTwo: "Con menos de dos piezas con peso no hay puntaje. Sube otro peso.",
      quality: "Calidad sin renta",
      withRent: "Con renta",
      air: "Aire",
      safety: "Seguridad",
      perception: "Percepción",
      rent: "Renta",
      cities: "Ciudades",
      networks: "Redes",
      states: "Entidades",
      search: "Buscar lugar o entidad",
      map: "Mapa",
      zoomIn: "Acercar este lugar",
      zoomOut: "Ver todo el país",
      mapNote: "El punto es una localidad de GeoNames, no el polígono de la ciudad ENSU. En el Valle de México se enciman: acerca el mapa para separarlos. La Laguna no tiene punto porque cruza Coahuila y Durango.",
      mapNear: "Hay otros lugares muy cerca en la vista del país.",
      noPin: "Este lugar no tiene punto en el mapa.",
      laguna: "La Laguna cruza Coahuila y Durango. El mapa no inventa un centro.",
      tableCaption: "Ranking con los pesos de ahora",
      place: "Lugar",
      entity: "Entidad",
      pm25: "PM2.5",
      stations: "Estaciones",
      rate: "Tasa",
      feel: "Inseguridad %",
      money: "Renta",
      score: "Puntaje",
      empty: "Ningún lugar pasa el filtro.",
      missing: "sin dato",
      rankLine: "Lugar {rank} de {total} con puntaje en este filtro.",
      noRank: "Sin puntaje en este filtro: faltan piezas o pesos.",
      typeCity: "Ciudad ENSU",
      typeNetwork: "Red de monitoreo",
      typeState: "Entidad",
      pm25Label: "PM2.5 anual (µg/m³)",
      stationLabel: "Estaciones con suficientes días",
      yearLabel: "Año del aire",
      rateLabel: "Homicidio doloso + feminicidio por 100 mil",
      countLabel: "Homicidios dolosos y feminicidios",
      popLabel: "Población usada",
      feelLabel: "Se siente inseguro (ENSU, %)",
      rentLabel: "Alquiler imputado al mes (pesos)",
      sideLabel: "Secuestro y extorsión por 100 mil",
      sideNote: "Se publican y no entran al puntaje.",
      oneStation: "Esta mediana sale de una sola estación ({valid} de {file} en el archivo, {year}). No cubre sola a toda la ciudad.",
      severalStations: "{valid} estaciones con suficientes días, de {file} en el archivo.",
      oldAir: "El año de la red es {year}. No describe el aire de ahora.",
      noAir: "Este lugar no tiene PM2.5 de SINAICA en el corte.",
      rentState: "Estos {money} pesos son de {state}, no de {place}. Es alquiler imputado estatal, no un anuncio.",
      rentIsState: "La renta es el promedio del estado, no el de una ciudad.",
      noRent: "No hay una renta de un solo estado para este lugar.",
      zeroRate: "La tasa es 0. Es lo que la fiscalía registró, no una prueba de que no pase nada. La extorsión se publica aparte y no entra al puntaje.",
      gdl: "La zona metropolitana de Guadalajara está en la red, no en la ciudad ENSU: PM2.5 de {pm} µg/m³ en {year}, {stations} estación con suficientes días. El archivo SEMADET de {semYear} da una mediana de {sem} µg/m³ en {semStations} estaciones y no entra a este puntaje.",
      simat: "La SIMAT del Valle de México es una red: PM2.5 de {pm} µg/m³ en {year}, {stations} estaciones. No trae una tasa única porque cruza dos entidades.",
      scatterTitle: "Costo y calidad",
      scatterHelp: "El eje horizontal es la renta imputada mensual del estado. El vertical es la calidad con los pesos de aire, delitos y percepción, sin la renta. Un punto más arriba no es una recomendación. Las ciudades de un mismo estado comparten la renta.",
      methodTitle: "Cómo se arma el puntaje",
      methodIntro: "Cada pieza va de 0 a 100. Más alto quiere decir menos carga medida, no una vida mejor. Los extremos están en el manifiesto del mart.",
      airScale: "Aire: 100 en {good} µg/m³ de PM2.5 anual o menos, 0 en {poor} o más. No es el Índice AIRE y SALUD ni la NOM-172.",
      safetyScale: "Delitos: 100 en 0 por 100 mil, 0 en {poor} o más. La canasta es homicidio doloso más feminicidio. Por encima de {poor} el puntaje se queda en 0 y la tasa sigue visible.",
      feelScale: "Percepción: 100 menos el porcentaje de la ENSU de diciembre de 2024. El margen de error de una ciudad puede ser amplio.",
      rentScale: "Renta: 100 en {good} pesos al mes o menos, 0 en {poor} o más. Es el trimestral de la ENIGH dividido entre 3.",
      lineageTitle: "De la fuente al mart",
      lineageBody: "DuckDB suma los delitos y la población de los municipios del lugar. Si falta más del 10% de esos municipios, la tasa se deja vacía. El sitio no vuelve a bajar las fuentes: lee el JSON y el Parquet ya exportados.",
      diagram: "Diagrama",
      sqlTitle: "Consultar el Parquet",
      sqlHelp: "La consulta corre en este navegador con DuckDB WASM, sobre place_mart.parquet. La primera vez se descarga el motor desde jsDelivr. Los datos no salen de esta página. El ranking de arriba usa el JSON, que es el mismo mart.",
      sqlRun: "Correr la consulta sobre el Parquet",
      sqlIdle: "Aún no corre la consulta.",
      sqlRows: "{n} filas. El Parquet tiene {total} lugares, igual que el JSON.",
      sqlFail: "La consulta no corrió.",
      checksTitle: "Calidad del corte",
      sourcesTitle: "Fuentes",
      colophon: "Atkinson Hyperlegible, del Braille Institute, porque en una tabla hay que distinguir 0, 6 y 8. Un solo verde, #0B6E4F, el mismo de las barras del tablero local: marca el puntaje, no una escala de colores. Código MIT. Cada cifra se queda con quien la publicó.",
      used: "Pesos usados",
      pin: "Punto del mapa",
    },
    en: {
      lede: "The ranking comes from this repository's mart ({places} places, cut of {day}). Move the weights and the table, the map, and the sheet change together.",
      disclaimer: "This is not advice about moving, not today's bulletin, and not the rent you will pay.",
      warnRent: "Rent is ENIGH 2024 imputed rent for the state, divided by 3. Two cities in the same state share the figure. La Laguna, Tampico, and the Mexico City metro area do not get one state's rent.",
      warnAir: "{one} of {air} PM2.5 figures come from a single station. The oldest air year in this cut is {year}.",
      warnExcerpt: "These figures are the public excerpts stored in the repository, not a download from this hour.",
      warnSynthetic: "These figures are invented. They do not describe any place in Mexico.",
      warnLive: "This cut was built by downloading the public sources for that run. It is still not today's air.",
      weightHelp: "The score rescales the weights of the pieces that have a number. Zero leaves that piece out. At least two are required.",
      needTwo: "Fewer than two weighted pieces means no score. Raise another weight.",
      quality: "Quality without rent",
      withRent: "With rent",
      air: "Air",
      safety: "Safety",
      perception: "Perception",
      rent: "Rent",
      cities: "Cities",
      networks: "Networks",
      states: "States",
      search: "Search place or state",
      map: "Map",
      zoomIn: "Zoom to this place",
      zoomOut: "Show the whole country",
      mapNote: "The pin is a GeoNames locality, not the ENSU city polygon. In the Valley of Mexico they overlap: zoom to separate them. La Laguna has no pin because it crosses Coahuila and Durango.",
      mapNear: "Other places sit very close in the country view.",
      noPin: "This place has no pin on the map.",
      laguna: "La Laguna crosses Coahuila and Durango. The map does not invent a center.",
      tableCaption: "Ranking with the current weights",
      place: "Place",
      entity: "State",
      pm25: "PM2.5",
      stations: "Stations",
      rate: "Rate",
      feel: "Unsafe %",
      money: "Rent",
      score: "Score",
      empty: "No place matches the filter.",
      missing: "no data",
      rankLine: "Place {rank} of {total} with a score in this filter.",
      noRank: "No score in this filter: pieces or weights are missing.",
      typeCity: "ENSU city",
      typeNetwork: "Monitoring network",
      typeState: "State",
      pm25Label: "Annual PM2.5 (µg/m³)",
      stationLabel: "Stations with enough days",
      yearLabel: "Air year",
      rateLabel: "Intentional homicide + feminicide per 100,000",
      countLabel: "Intentional homicides and feminicides",
      popLabel: "Population used",
      feelLabel: "Feels unsafe (ENSU, %)",
      rentLabel: "Monthly imputed rent (pesos)",
      sideLabel: "Kidnapping and extortion per 100,000",
      sideNote: "Published, and kept out of the score.",
      oneStation: "This median comes from a single station ({valid} of {file} in the file, {year}). It does not by itself cover the whole city.",
      severalStations: "{valid} stations with enough days, out of {file} in the file.",
      oldAir: "The network year is {year}. It does not describe the air right now.",
      noAir: "This place has no SINAICA PM2.5 in the cut.",
      rentState: "These {money} pesos belong to {state}, not to {place}. State imputed rent, not a listing.",
      rentIsState: "The rent is the state average, not a city's.",
      noRent: "This place does not get one state's rent.",
      zeroRate: "The rate is 0. That is what the prosecutor recorded, not proof that nothing happened. Extortion is published separately and stays out of the score.",
      gdl: "Guadalajara's metro area is a network row, not the ENSU city: PM2.5 of {pm} µg/m³ in {year}, {stations} station with enough days. The SEMADET file for {semYear} gives a median of {sem} µg/m³ across {semStations} stations and stays out of this score.",
      simat: "The Mexico City SIMAT network: PM2.5 of {pm} µg/m³ in {year}, {stations} stations. It has no single crime rate because it crosses two states.",
      scatterTitle: "Cost and quality",
      scatterHelp: "The horizontal axis is the state's monthly imputed rent. The vertical axis is quality using the air, crime, and perception weights, without rent. A higher point is not a recommendation. Cities in the same state share the rent.",
      methodTitle: "How the score is built",
      methodIntro: "Each piece runs from 0 to 100. Higher means a lighter measured burden, not a better life. The ends are in the mart manifest.",
      airScale: "Air: 100 at {good} µg/m³ annual PM2.5 or below, 0 at {poor} or above. Not the official Índice AIRE y SALUD and not NOM-172.",
      safetyScale: "Crime: 100 at 0 per 100,000, 0 at {poor} or above. The basket is intentional homicide plus feminicide. Above {poor} the score stays at 0 and the rate remains visible.",
      feelScale: "Perception: 100 minus the December 2024 ENSU percentage. The margin of error for one city can be wide.",
      rentScale: "Rent: 100 at {good} pesos a month or below, 0 at {poor} or above. ENIGH's quarterly figure divided by 3.",
      lineageTitle: "From the source to the mart",
      lineageBody: "DuckDB sums crime and population for the place's municipalities. If more than 10% of those municipalities are missing, the rate is left empty. The site does not download the sources again: it reads the exported JSON and Parquet.",
      diagram: "Diagram",
      sqlTitle: "Query the Parquet",
      sqlHelp: "The query runs in this browser with DuckDB WASM, on place_mart.parquet. The first run downloads the engine from jsDelivr. The data does not leave this page. The ranking above uses the JSON, which is the same mart.",
      sqlRun: "Run the query on the Parquet",
      sqlIdle: "The query has not run yet.",
      sqlRows: "{n} rows. The Parquet has {total} places, the same count as the JSON.",
      sqlFail: "The query did not run.",
      checksTitle: "Cut quality",
      sourcesTitle: "Sources",
      colophon: "Atkinson Hyperlegible, from the Braille Institute, because a table of figures has to keep 0, 6, and 8 apart. One green, #0B6E4F, the same one as the local dashboard bars: it marks the score, not a color scale. Code is MIT. Each figure stays with its publisher.",
      used: "Weights used",
      pin: "Map pin",
    },
  };

  const SQL_DEFAULT = [
    "SELECT place_name, state_name, air_year, air_pm25_median_ugm3,",
    "       air_stations_valid, lethal_per_100k, perception_insecurity_pct,",
    "       enigh_imputed_rent_monthly_approx_mxn",
    "FROM place_mart",
    "WHERE place_type = 'city'",
    "  AND air_stations_valid = 1",
    "ORDER BY air_pm25_median_ugm3 DESC",
  ].join("\n");

  const MERMAID = [
    "flowchart LR",
    "  SINAICA[INECC SINAICA PM2.5] --> Mart[place_mart]",
    "  SESNSP[SESNSP 2025] --> Mart",
    "  CONAPO[CONAPO 2025] --> Mart",
    "  ENSU[ENSU diciembre 2024] --> Mart",
    "  ENIGH[ENIGH 2024] --> Mart",
    "  Mart --> Files[JSON y Parquet]",
    "  Files --> Site[Ranking mapa y ficha]",
  ].join("\n");

  const state = {
    lang: "es",
    weights: { air: 40, safety: 35, perception: 25, rent: 0 },
    types: { city: true, network: false, state: false },
    query: "",
    selectedId: null,
    zoom: false,
    places: [],
    points: {},
    geo: null,
    manifest: null,
    quality: null,
    country: null,
    db: null,
    parquetRows: null,
  };

  const $ = (id) => document.getElementById(id);
  const text = () => COPY[state.lang];

  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, (_, key) => values[key] ?? "");
  }

  function fold(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/\p{M}/gu, "")
      .toLowerCase();
  }

  function formatDay(iso) {
    const match = String(iso || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!match) return "";
    const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
    return new Intl.DateTimeFormat(state.lang === "es" ? "es-MX" : "en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "UTC",
    }).format(date);
  }

  function digits(value, places) {
    if (value === null || value === undefined || Number.isNaN(value)) return text().missing;
    return new Intl.NumberFormat(state.lang === "es" ? "es-MX" : "en-GB", {
      minimumFractionDigits: places,
      maximumFractionDigits: places,
    }).format(value);
  }

  function weights01() {
    return {
      air: state.weights.air / 100,
      safety: state.weights.safety / 100,
      perception: state.weights.perception / 100,
      rent: state.weights.rent / 100,
    };
  }

  function components(place) {
    return {
      air: place.score_air,
      safety: place.score_safety,
      perception: place.score_perception,
      rent: place.score_rent,
    };
  }

  function evaluated(place) {
    const current = window.LivabilityScore.combine(components(place), weights01(), 2);
    const qualityWeights = Object.assign({}, weights01(), { rent: 0 });
    const quality = window.LivabilityScore.combine(components(place), qualityWeights, 2);
    return { score: current.score, used: current.used, quality: quality.score };
  }

  function visible() {
    const needle = fold(state.query);
    return state.places
      .filter((place) => state.types[place.place_type])
      .filter((place) => !needle || fold(place.place_name).includes(needle) || fold(place.state_name).includes(needle))
      .map((place) => Object.assign({ eval: evaluated(place) }, place))
      .sort((a, b) => {
        const as = a.eval.score;
        const bs = b.eval.score;
        if (as === null && bs === null) return a.place_name.localeCompare(b.place_name, state.lang);
        if (as === null) return 1;
        if (bs === null) return -1;
        if (bs !== as) return bs - as;
        return a.place_name.localeCompare(b.place_name, state.lang);
      });
  }

  function selectedPlace() {
    return state.places.find((place) => place.place_id === state.selectedId) || null;
  }

  function readControls() {
    state.weights.air = Number($("w-air").value);
    state.weights.safety = Number($("w-safety").value);
    state.weights.perception = Number($("w-perception").value);
    state.weights.rent = Number($("w-rent").value);
    state.types.city = $("type-city").checked;
    state.types.network = $("type-network").checked;
    state.types.state = $("type-state").checked;
    state.query = $("search").value.trim();
  }

  function syncControls() {
    ["air", "safety", "perception", "rent"].forEach((key) => {
      $("w-" + key).value = String(state.weights[key]);
      $("out-" + key).value = String(state.weights[key]);
    });
    $("type-city").checked = state.types.city;
    $("type-network").checked = state.types.network;
    $("type-state").checked = state.types.state;
    const quality = state.weights.air === 40 && state.weights.safety === 35 && state.weights.perception === 25 && state.weights.rent === 0;
    const rent = state.weights.air === 30 && state.weights.safety === 30 && state.weights.perception === 20 && state.weights.rent === 20;
    $("preset-quality").setAttribute("aria-pressed", quality ? "true" : "false");
    $("preset-rent").setAttribute("aria-pressed", rent ? "true" : "false");
  }

  function writeUrl() {
    const params = new URLSearchParams();
    ["air", "safety", "perception", "rent"].forEach((key) => params.set(key, String(state.weights[key])));
    params.set("lang", state.lang);
    const hash = state.selectedId ? "#" + encodeURIComponent(state.selectedId) : "";
    history.replaceState(null, "", "?" + params.toString() + hash);
  }

  function readUrl() {
    const params = new URLSearchParams(location.search);
    ["air", "safety", "perception", "rent"].forEach((key) => {
      if (!params.has(key)) return;
      const value = Number(params.get(key));
      if (Number.isFinite(value) && value >= 0 && value <= 100) state.weights[key] = value;
    });
    if (params.get("lang") === "en" || params.get("lang") === "es") state.lang = params.get("lang");
    const hash = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (hash) state.selectedId = hash;
  }

  function boundsOf(features) {
    const bounds = { minLon: 180, maxLon: -180, minLat: 90, maxLat: -90 };
    const walk = (coords) => {
      if (typeof coords[0] === "number") {
        bounds.minLon = Math.min(bounds.minLon, coords[0]);
        bounds.maxLon = Math.max(bounds.maxLon, coords[0]);
        bounds.minLat = Math.min(bounds.minLat, coords[1]);
        bounds.maxLat = Math.max(bounds.maxLat, coords[1]);
        return;
      }
      coords.forEach(walk);
    };
    features.forEach((feature) => walk(feature.geometry.coordinates));
    const dx = (bounds.maxLon - bounds.minLon) * 0.02;
    const dy = (bounds.maxLat - bounds.minLat) * 0.02;
    return {
      minLon: bounds.minLon - dx,
      maxLon: bounds.maxLon + dx,
      minLat: bounds.minLat - dy,
      maxLat: bounds.maxLat + dy,
    };
  }

  function project(bounds, lon, lat) {
    const width = 640;
    const height = 420;
    return [
      ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * width,
      ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * height,
    ];
  }

  function geometryPath(geometry, bounds) {
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    return polygons
      .map((polygon) =>
        polygon
          .map((ring) =>
            ring
              .map((point, index) => {
                const xy = project(bounds, point[0], point[1]);
                return (index === 0 ? "M" : "L") + xy[0].toFixed(1) + " " + xy[1].toFixed(1);
              })
              .join("") + "Z",
          )
          .join(""),
      )
      .join("");
  }

  function currentBounds() {
    if (!state.zoom) return state.country;
    const place = selectedPlace();
    const pin = place && state.points[place.place_id];
    if (!pin) return state.country;
    return { minLon: pin.lon - 0.55, maxLon: pin.lon + 0.55, minLat: pin.lat - 0.42, maxLat: pin.lat + 0.42 };
  }

  function renderStatic() {
    const copy = text();
    document.documentElement.lang = state.lang;
    $("lbl-air").textContent = copy.air;
    $("lbl-safety").textContent = copy.safety;
    $("lbl-perception").textContent = copy.perception;
    $("lbl-rent").textContent = copy.rent;
    $("lbl-city").textContent = copy.cities;
    $("lbl-network").textContent = copy.networks;
    $("lbl-state").textContent = copy.states;
    $("preset-quality").textContent = copy.quality;
    $("preset-rent").textContent = copy.withRent;
    $("search").placeholder = copy.search;
    $("search").setAttribute("aria-label", copy.search);
    $("map-title").textContent = copy.map;
    $("weight-help").textContent = copy.weightHelp;
    $("disclaimer").textContent = copy.disclaimer;
    $("scatter-title").textContent = copy.scatterTitle;
    $("scatter-help").textContent = copy.scatterHelp;
    $("method-title").textContent = copy.methodTitle;
    $("lineage-title").textContent = copy.lineageTitle;
    $("diagram-summary").textContent = copy.diagram;
    $("sql-title").textContent = copy.sqlTitle;
    $("sql-help").textContent = copy.sqlHelp;
    $("sql-run").textContent = copy.sqlRun;
    $("checks-title").textContent = copy.checksTitle;
    $("sources-title").textContent = copy.sourcesTitle;
    $("colophon").textContent = copy.colophon;
    $("preset-group").setAttribute("aria-label", copy.quality);
    const airRows = state.places.filter((place) => place.air_pm25_median_ugm3 !== null);
    const one = airRows.filter((place) => place.air_stations_valid === 1).length;
    const oldest = airRows.reduce((min, place) => Math.min(min, place.air_year), 9999);
    const kind = state.manifest.data_kind;
    const banner = kind === "synthetic" ? copy.warnSynthetic : kind === "official_live" ? copy.warnLive : copy.warnExcerpt;
    $("lede").textContent = fill(copy.lede, { places: String(state.places.length), day: formatDay(state.manifest.built_at) });
    $("warnings").replaceChildren();
    [banner, copy.warnRent, fill(copy.warnAir, { one: String(one), air: String(airRows.length), year: String(oldest) })].forEach((sentence) => {
      const item = document.createElement("li");
      item.textContent = sentence;
      $("warnings").append(item);
    });
    $("zoom").textContent = state.zoom ? copy.zoomOut : copy.zoomIn;
    $("zoom").setAttribute("aria-pressed", state.zoom ? "true" : "false");
    $("lang-es").setAttribute("aria-pressed", state.lang === "es" ? "true" : "false");
    $("lang-en").setAttribute("aria-pressed", state.lang === "en" ? "true" : "false");
  }

  function renderTable(rows) {
    const copy = text();
    const table = document.createElement("table");
    const caption = document.createElement("caption");
    caption.textContent = copy.tableCaption;
    table.append(caption);
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    [ "#", copy.place, copy.score, copy.pm25, copy.rate, copy.feel, copy.money ].forEach((label) => {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = label;
      headRow.append(cell);
    });
    head.append(headRow);
    const body = document.createElement("tbody");
    if (!rows.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 7;
      cell.textContent = copy.empty;
      row.append(cell);
      body.append(row);
    }
    let rank = 0;
    rows.forEach((place) => {
      const scored = place.eval.score !== null;
      if (scored) rank += 1;
      const row = document.createElement("tr");
      row.dataset.id = place.place_id;
      if (place.place_id === state.selectedId) row.setAttribute("aria-selected", "true");
      const cells = [
        scored ? String(rank) : "",
        null,
        digits(place.eval.score, 1),
        digits(place.air_pm25_median_ugm3, 1),
        digits(place.lethal_per_100k, 1),
        digits(place.perception_insecurity_pct, 1),
        digits(place.enigh_imputed_rent_monthly_approx_mxn, 0),
      ];
      cells.forEach((value, index) => {
        const cell = document.createElement(index === 0 ? "th" : "td");
        if (index === 0) cell.scope = "row";
        if (index === 1) {
          cell.className = "place";
          const button = document.createElement("button");
          button.type = "button";
          button.className = "place-btn";
          button.textContent = place.place_name;
          button.addEventListener("click", () => select(place.place_id));
          cell.append(button);
          if (place.state_name) {
            const stateLine = document.createElement("span");
            stateLine.className = "state-line";
            stateLine.textContent = place.state_name;
            cell.append(stateLine);
          }
        } else {
          cell.textContent = value;
          if (index === 2) cell.className = "score";
        }
        row.append(cell);
      });
      body.append(row);
    });
    table.append(head, body);
    $("table-host").replaceChildren(table);
  }

  function renderMap(rows) {
    const copy = text();
    const bounds = currentBounds();
    const svg = $("map");
    svg.replaceChildren();
    const selected = selectedPlace();
    state.geo.features.forEach((feature) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", geometryPath(feature.geometry, bounds));
      const code = feature.properties.state_code;
      const active = selected && selected.state_code === code;
      path.setAttribute("fill", active ? "#d9ebe3" : "#e7eeeb");
      path.setAttribute("stroke", active ? "#0b6e4f" : "#8aa399");
      path.setAttribute("stroke-width", active ? "1.4" : "0.8");
      svg.append(path);
    });
    const shown = rows.filter((place) => state.points[place.place_id]);
    shown.forEach((place) => {
      const pin = state.points[place.place_id];
      const xy = project(bounds, pin.lon, pin.lat);
      const chosen = place.place_id === state.selectedId;
      const button = document.createElementNS("http://www.w3.org/2000/svg", "g");
      button.setAttribute("role", "button");
      button.setAttribute("tabindex", "0");
      button.setAttribute("aria-label", place.place_name + ", " + digits(place.eval.score, 1));
      button.setAttribute("transform", "translate(" + xy[0].toFixed(1) + " " + xy[1].toFixed(1) + ")");
      const hit = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      hit.setAttribute("r", "11");
      hit.setAttribute("fill", "transparent");
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      const score = place.eval.score;
      dot.setAttribute("r", chosen ? "6.5" : "4.5");
      if (score === null) {
        dot.setAttribute("fill", "#f4f7f6");
        dot.setAttribute("stroke", "#14211c");
      } else {
        dot.setAttribute("fill", "#0b6e4f");
        dot.setAttribute("fill-opacity", (0.35 + 0.65 * Math.max(0, Math.min(100, score)) / 100).toFixed(2));
        dot.setAttribute("stroke", chosen ? "#14211c" : "#0b6e4f");
      }
      dot.setAttribute("stroke-width", chosen ? "1.6" : "0.6");
      button.append(hit, dot);
      button.addEventListener("click", () => select(place.place_id));
      button.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select(place.place_id);
        }
      });
      svg.append(button);
    });
    let note = copy.mapNote;
    if (selected && state.points[selected.place_id] && !state.zoom) {
      const pin = state.points[selected.place_id];
      const close = shown.some((place) => {
        if (place.place_id === selected.place_id) return false;
        const other = state.points[place.place_id];
        return Math.abs(other.lon - pin.lon) < 0.18 && Math.abs(other.lat - pin.lat) < 0.18;
      });
      if (close) note = copy.mapNear + " " + note;
    }
    $("map-note").textContent = note;
  }

  function fact(list, label, value) {
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = value;
    list.append(term, detail);
  }

  function renderFicha(rows) {
    const copy = text();
    const host = $("ficha");
    const place = selectedPlace();
    host.replaceChildren();
    if (!place) {
      host.textContent = copy.empty;
      return;
    }
    const view = evaluated(place);
    const title = document.createElement("h2");
    title.textContent = place.place_name;
    const where = document.createElement("p");
    where.className = "where";
    const typeName = place.place_type === "city" ? copy.typeCity : place.place_type === "network" ? copy.typeNetwork : copy.typeState;
    where.textContent = typeName + (place.state_name ? " · " + place.state_name : "");
    const rank = document.createElement("p");
    rank.className = "rank-line";
    const ranked = rows.filter((item) => item.eval.score !== null);
    const index = ranked.findIndex((item) => item.place_id === place.place_id);
    rank.textContent = index >= 0 ? fill(copy.rankLine, { rank: String(index + 1), total: String(ranked.length) }) : copy.noRank;
    if (view.score === null && weights01().air + weights01().safety + weights01().perception + weights01().rent > 0) {
      const active = Object.values(weights01()).filter((value) => value > 0).length;
      if (active < 2) rank.textContent = copy.needTwo;
    }
    host.append(title, where, rank);
    const list = document.createElement("dl");
    fact(list, copy.score, digits(view.score, 1));
    const used = Object.entries(view.used)
      .map(([key, value]) => copy[key] + " " + digits(value, 2))
      .join(", ");
    if (used) fact(list, copy.used, used);
    fact(list, copy.pm25Label, digits(place.air_pm25_median_ugm3, 1));
    fact(list, copy.stationLabel, place.air_stations_valid === null ? copy.missing : String(place.air_stations_valid));
    fact(list, copy.yearLabel, place.air_year === null ? copy.missing : String(place.air_year));
    fact(list, copy.rateLabel, digits(place.lethal_per_100k, 1));
    const deaths = place.homicidio_doloso === null ? copy.missing : digits(place.homicidio_doloso, 0) + " + " + digits(place.feminicidio, 0);
    fact(list, copy.countLabel, deaths);
    fact(list, copy.popLabel, place.safety_population === null ? copy.missing : digits(place.safety_population, 0));
    fact(list, copy.feelLabel, digits(place.perception_insecurity_pct, 1));
    fact(list, copy.rentLabel, digits(place.enigh_imputed_rent_monthly_approx_mxn, 0));
    const side = place.secuestro_per_100k === null ? copy.missing : digits(place.secuestro_per_100k, 2) + " / " + digits(place.extorsion_per_100k, 2) + ". " + copy.sideNote;
    fact(list, copy.sideLabel, side);
    host.append(list);
    const warnings = [];
    if (place.air_stations_valid === 1) {
      warnings.push(fill(copy.oneStation, {
        valid: String(place.air_stations_valid),
        file: String(place.air_stations_in_file),
        year: String(place.air_year),
      }));
    } else if (place.air_stations_valid > 1) {
      warnings.push(fill(copy.severalStations, {
        valid: String(place.air_stations_valid),
        file: String(place.air_stations_in_file),
      }));
    } else {
      warnings.push(copy.noAir);
    }
    if (place.air_year !== null) warnings.push(fill(copy.oldAir, { year: String(place.air_year) }));
    if (place.lethal_per_100k === 0) warnings.push(copy.zeroRate);
    if (place.enigh_imputed_rent_monthly_approx_mxn !== null && place.place_type !== "state") {
      warnings.push(fill(copy.rentState, {
        money: digits(place.enigh_imputed_rent_monthly_approx_mxn, 0),
        state: place.state_name,
        place: place.place_name,
      }));
    } else if (place.place_type === "state" && place.enigh_imputed_rent_monthly_approx_mxn !== null) {
      warnings.push(copy.rentIsState);
    } else {
      warnings.push(copy.noRent);
    }
    warnings.forEach((sentence) => {
      const paragraph = document.createElement("p");
      paragraph.className = "ficha-warn";
      paragraph.textContent = sentence;
      host.append(paragraph);
    });
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = state.lang === "es" ? place.note_es : place.note_en;
    host.append(note);
    const pin = state.points[place.place_id];
    const pinLine = document.createElement("p");
    pinLine.className = "note";
    if (place.place_name === "La Laguna") pinLine.textContent = copy.laguna;
    else if (!pin) pinLine.textContent = copy.noPin;
    else pinLine.textContent = copy.pin + ": " + (state.lang === "es" ? pin.note_es : pin.note_en);
    host.append(pinLine);
  }

  function renderScatter(rows) {
    const svg = $("scatter");
    svg.replaceChildren();
    const points = rows.filter((place) => place.enigh_imputed_rent_monthly_approx_mxn !== null && place.eval.quality !== null);
    if (!points.length) return;
    const rents = points.map((place) => place.enigh_imputed_rent_monthly_approx_mxn);
    const scores = points.map((place) => place.eval.quality);
    const minX = Math.min(...rents);
    const maxX = Math.max(...rents);
    const minY = Math.min(...scores, 0);
    const maxY = Math.max(...scores, 100);
    const left = 48;
    const right = 16;
    const top = 12;
    const bottom = 32;
    const width = 640;
    const height = 360;
    const xOf = (value) => left + ((value - minX) / (maxX - minX || 1)) * (width - left - right);
    const yOf = (value) => top + (1 - (value - minY) / (maxY - minY || 1)) * (height - top - bottom);
    const axis = document.createElementNS("http://www.w3.org/2000/svg", "path");
    axis.setAttribute("d", "M" + left + " " + top + "V" + (height - bottom) + "H" + (width - right));
    axis.setAttribute("fill", "none");
    axis.setAttribute("stroke", "#14211c");
    svg.append(axis);
    [[minX, height - bottom + 16, 0], [maxX, height - bottom + 16, 0], [minY, 8, left - 8], [maxY, 8, left - 8]].forEach((item, index) => {
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      const value = index < 2 ? item[0] : item[0];
      label.textContent = digits(value, index < 2 ? 0 : 0);
      label.setAttribute("fill", "#3d5248");
      label.setAttribute("font-size", "12");
      if (index < 2) {
        label.setAttribute("x", String(xOf(item[0])));
        label.setAttribute("y", String(item[1]));
        label.setAttribute("text-anchor", index === 0 ? "start" : "end");
      } else {
        label.setAttribute("x", "4");
        label.setAttribute("y", String(yOf(item[0]) + 4));
      }
      svg.append(label);
    });
    points.forEach((place) => {
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", xOf(place.enigh_imputed_rent_monthly_approx_mxn).toFixed(1));
      dot.setAttribute("cy", yOf(place.eval.quality).toFixed(1));
      dot.setAttribute("r", place.place_id === state.selectedId ? "6" : "3.5");
      dot.setAttribute("fill", place.place_id === state.selectedId ? "#0b6e4f" : "#14211c");
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = place.place_name + ": " + digits(place.eval.quality, 1);
      dot.append(title);
      svg.append(dot);
    });
  }

  function renderMethod() {
    const copy = text();
    const scoring = state.manifest.scoring;
    const host = $("method-body");
    host.replaceChildren();
    [copy.methodIntro,
      fill(copy.airScale, { good: String(scoring.air_good_ugm3), poor: String(scoring.air_poor_ugm3) }),
      fill(copy.safetyScale, { poor: String(scoring.safety_poor_per_100k) }),
      copy.feelScale,
      fill(copy.rentScale, { good: digits(scoring.rent_good_monthly_mxn, 0), poor: digits(scoring.rent_poor_monthly_mxn, 0) }),
    ].forEach((sentence) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = sentence;
      host.append(paragraph);
    });
    const gdl = state.places.find((place) => place.place_id === "network:GDL");
    const simat = state.places.find((place) => place.place_id === "network:CMX");
    if (gdl && gdl.air_pm25_median_ugm3 !== null) {
      const paragraph = document.createElement("p");
      paragraph.textContent = fill(copy.gdl, {
        pm: digits(gdl.air_pm25_median_ugm3, 1),
        year: String(gdl.air_year),
        stations: String(gdl.air_stations_valid),
        semYear: String(gdl.semadet_year),
        sem: digits(gdl.semadet_pm25_median_ugm3, 1),
        semStations: String(gdl.semadet_stations_valid),
      });
      host.append(paragraph);
    }
    if (simat && simat.air_pm25_median_ugm3 !== null) {
      const paragraph = document.createElement("p");
      paragraph.textContent = fill(copy.simat, {
        pm: digits(simat.air_pm25_median_ugm3, 1),
        year: String(simat.air_year),
        stations: String(simat.air_stations_valid),
      });
      host.append(paragraph);
    }
  }

  function renderLineage() {
    const copy = text();
    const host = $("lineage-body");
    host.replaceChildren();
    const intro = document.createElement("p");
    intro.textContent = copy.lineageBody;
    host.append(intro);
    const flow = document.createElement("ol");
    flow.className = "flow";
    const steps = state.lang === "es"
      ? ["SINAICA, PM2.5 por red", "SESNSP, delitos 2025", "CONAPO, población", "ENSU, percepción", "ENIGH, renta estatal", "Mart", "JSON y Parquet", "Esta página"]
      : ["SINAICA, PM2.5 by network", "SESNSP, 2025 crime", "CONAPO, population", "ENSU, perception", "ENIGH, state rent", "Mart", "JSON and Parquet", "This page"];
    steps.forEach((step, index) => {
      if (index) {
        const arrow = document.createElement("li");
        arrow.className = "arrow";
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = ">";
        flow.append(arrow);
      }
      const item = document.createElement("li");
      item.textContent = step;
      flow.append(item);
    });
    host.append(flow);
  }

  function renderChecks() {
    const host = $("checks");
    host.replaceChildren();
    (state.quality.checks || []).forEach((check) => {
      const paragraph = document.createElement("p");
      paragraph.className = "check";
      const detail = state.lang === "es" ? check.detail_es : check.detail_en;
      paragraph.textContent = check.status + " · " + check.id + " · " + detail;
      host.append(paragraph);
    });
  }

  function renderSources() {
    const host = $("sources");
    host.replaceChildren();
    (state.manifest.sources || []).forEach((source) => {
      const block = document.createElement("article");
      block.className = "source-card";
      const heading = document.createElement("h3");
      heading.textContent = source.publisher;
      const paragraph = document.createElement("p");
      const link = document.createElement("a");
      link.href = source.url;
      link.textContent = source.id;
      paragraph.append(link, document.createTextNode(". " + source.vintage + ". " + source.license));
      block.append(heading, paragraph);
      host.append(block);
    });
  }

  function render() {
    readControls();
    syncControls();
    renderStatic();
    const rows = visible();
    if (!state.selectedId || !state.places.some((place) => place.place_id === state.selectedId)) {
      state.selectedId = (rows[0] && rows[0].place_id) || (state.places[0] && state.places[0].place_id) || null;
    }
    renderTable(rows);
    renderMap(rows);
    renderFicha(rows);
    renderScatter(rows);
    renderMethod();
    renderLineage();
    renderChecks();
    renderSources();
    writeUrl();
  }

  function select(placeId) {
    state.selectedId = placeId;
    render();
  }

  async function runSql() {
    const copy = text();
    const status = $("sql-status");
    status.textContent = "…";
    try {
      if (!state.db) {
        const duckdb = await import("https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/+esm");
        const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
        const workerUrl = URL.createObjectURL(
          new Blob(["importScripts(" + JSON.stringify(bundle.mainWorker) + ");"], { type: "text/javascript" }),
        );
        const worker = new Worker(workerUrl);
        const database = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
        await database.instantiate(bundle.mainModule, bundle.pthreadWorker);
        URL.revokeObjectURL(workerUrl);
        const connection = await database.connect();
        const response = await fetch("data/place_mart.parquet");
        if (!response.ok) throw new Error("parquet " + response.status);
        await database.registerFileBuffer("place_mart.parquet", new Uint8Array(await response.arrayBuffer()));
        await connection.query("CREATE VIEW place_mart AS SELECT * FROM read_parquet('place_mart.parquet')");
        const count = await connection.query("SELECT count(*)::INTEGER AS n FROM place_mart");
        state.parquetRows = Number(count.toArray()[0].n);
        state.db = connection;
      }
      const result = await state.db.query($("sql").value);
      const records = result.toArray();
      status.textContent = fill(copy.sqlRows, { n: String(records.length), total: String(state.parquetRows) });
      const table = document.createElement("table");
      const fields = result.schema.fields.map((field) => field.name);
      const head = document.createElement("tr");
      fields.forEach((name) => {
        const cell = document.createElement("th");
        cell.textContent = name;
        head.append(cell);
      });
      const headWrap = document.createElement("thead");
      headWrap.append(head);
      const body = document.createElement("tbody");
      records.forEach((record) => {
        const row = document.createElement("tr");
        const values = record.toJSON();
        fields.forEach((name) => {
          const cell = document.createElement("td");
          const value = values[name];
          cell.textContent = value === null || value === undefined ? "" : String(value);
          row.append(cell);
        });
        body.append(row);
      });
      table.append(headWrap, body);
      $("sql-result").replaceChildren(table);
    } catch (error) {
      status.textContent = copy.sqlFail + " " + (error && error.message ? error.message : String(error));
    }
  }

  async function renderDiagram() {
    const node = $("mermaid");
    if (node.dataset.ready === "1") return;
    node.dataset.ready = "1";
    try {
      const mermaid = await import("https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs");
      mermaid.default.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "base",
        themeVariables: {
          fontFamily: "Atkinson Hyperlegible, sans-serif",
          primaryColor: "#e7eeeb",
          primaryTextColor: "#14211c",
          primaryBorderColor: "#0b6e4f",
          lineColor: "#3d5248",
          secondaryColor: "#f4f7f6",
          tertiaryColor: "#ffffff",
        },
      });
      const { svg } = await mermaid.default.render("lineage-diagram", MERMAID);
      const holder = document.createElement("div");
      holder.innerHTML = svg;
      node.replaceWith(holder);
    } catch (error) {
      node.textContent = MERMAID + "\n\n" + (error && error.message ? error.message : "");
    }
  }

  function bind() {
    $("controls").addEventListener("submit", (event) => event.preventDefault());
    ["w-air", "w-safety", "w-perception", "w-rent"].forEach((id) => {
      $(id).addEventListener("input", render);
    });
    ["type-city", "type-network", "type-state"].forEach((id) => $(id).addEventListener("change", render));
    $("search").addEventListener("input", render);
    $("preset-quality").addEventListener("click", () => {
      state.weights = { air: 40, safety: 35, perception: 25, rent: 0 };
      syncControls();
      render();
    });
    $("preset-rent").addEventListener("click", () => {
      state.weights = { air: 30, safety: 30, perception: 20, rent: 20 };
      syncControls();
      render();
    });
    $("zoom").addEventListener("click", () => {
      const place = selectedPlace();
      if (!state.zoom && (!place || !state.points[place.place_id])) return;
      state.zoom = !state.zoom;
      render();
    });
    $("lang-es").addEventListener("click", () => {
      state.lang = "es";
      render();
    });
    $("lang-en").addEventListener("click", () => {
      state.lang = "en";
      render();
    });
    $("sql-run").addEventListener("click", runSql);
    $("diagram-details").addEventListener("toggle", () => {
      if ($("diagram-details").open) renderDiagram();
    });
  }

  async function init() {
    readUrl();
    $("sql").value = SQL_DEFAULT;
    $("mermaid").textContent = MERMAID;
    $("sql-status").textContent = COPY[state.lang].sqlIdle;
    const [places, points, geo, manifest, quality] = await Promise.all([
      fetch("data/place_mart.json").then((response) => response.json()),
      fetch("data/place_points.json").then((response) => response.json()),
      fetch("data/mexico_states.geojson").then((response) => response.json()),
      fetch("data/manifest.json").then((response) => response.json()),
      fetch("data/quality_report.json").then((response) => response.json()),
    ]);
    state.places = places;
    points.forEach((point) => {
      state.points[point.place_id] = point;
    });
    state.geo = geo;
    state.manifest = manifest;
    state.quality = quality;
    state.country = boundsOf(geo.features);
    bind();
    syncControls();
    render();
  }

  init().catch((error) => {
    $("lede").textContent = error && error.message ? error.message : String(error);
  });
})();
