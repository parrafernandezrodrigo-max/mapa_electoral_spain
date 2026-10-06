"""
Metadatos de convocatorias y provincias.

Los ficheros XLSX del Ministerio tienen esta estructura fija:
  Fila 0-1 : vacías (formato)
  Fila 2   : título ("Congreso | Julio 2023 | Resultados por circunscripción")
  Fila 3   : denominaciones completas de los partidos (columnas 15, 17, 19…)
  Fila 4   : siglas de los partidos (mismas columnas)
  Fila 5   : cabeceras: 15 columnas fijas + pares (Votos, Diputados) por partido
  Fila 6+  : datos, una fila por circunscripción + fila de totales nacionales

Columnas fijas (índices 0-14):
  0  Nombre de Comunidad
  1  Código de Provincia
  2  Nombre de Provincia
  3  Población
  4  Número de mesas
  5  Censo electoral sin CERA
  6  Censo CERA
  7  Total censo electoral
  8  Total votantes CER
  9  Total votantes CERA
  10 Total votantes
  11 Votos válidos
  12 Votos a candidaturas
  13 Votos en blanco
  14 Votos nulos

Desde columna 15: pares (Votos_partido, Diputados_partido) para cada partido,
en el mismo orden que aparecen en las filas 3 y 4.
"""

# ─────────────────────────────────────────────
# Convocatorias disponibles (Congreso)
# Clave: YYYYMM  →  nombre del ZIP = PROV_02_{YYYYMM}_1.zip
# ─────────────────────────────────────────────
CONVOCATORIAS = {
    "197706": "Jun 1977",
    "197903": "Mar 1979",
    "198210": "Oct 1982",
    "198606": "Jun 1986",
    "198910": "Oct 1989",
    "199306": "Jun 1993",
    "199603": "Mar 1996",
    "200003": "Mar 2000",
    "200403": "Mar 2004",
    "200803": "Mar 2008",
    "201111": "Nov 2011",
    "201512": "Dic 2015",
    "201606": "Jun 2016",
    "201904": "Abr 2019",
    "201911": "Nov 2019",
    "202307": "Jul 2023",
}

# ─────────────────────────────────────────────
# Códigos de provincia INE → nombre
# ─────────────────────────────────────────────
PROVINCIAS = {
    "01": "Álava",        "02": "Albacete",     "03": "Alicante",
    "04": "Almería",      "05": "Ávila",        "06": "Badajoz",
    "07": "Baleares",     "08": "Barcelona",    "09": "Burgos",
    "10": "Cáceres",      "11": "Cádiz",        "12": "Castellón",
    "13": "Ciudad Real",  "14": "Córdoba",      "15": "La Coruña",
    "16": "Cuenca",       "17": "Girona",       "18": "Granada",
    "19": "Guadalajara",  "20": "Guipúzcoa",    "21": "Huelva",
    "22": "Huesca",       "23": "Jaén",         "24": "León",
    "25": "Lleida",       "26": "La Rioja",     "27": "Lugo",
    "28": "Madrid",       "29": "Málaga",       "30": "Murcia",
    "31": "Navarra",      "32": "Ourense",      "33": "Asturias",
    "34": "Palencia",     "35": "Las Palmas",   "36": "Pontevedra",
    "37": "Salamanca",    "38": "S.C. Tenerife","39": "Cantabria",
    "40": "Segovia",      "41": "Sevilla",      "42": "Soria",
    "43": "Tarragona",    "44": "Teruel",       "45": "Toledo",
    "46": "Valencia",     "47": "Valladolid",   "48": "Vizcaya",
    "49": "Zamora",       "50": "Zaragoza",     "51": "Ceuta",
    "52": "Melilla",
}

# Índices de las columnas fijas en el XLSX
META_COLS = {
    "nombre_ccaa":        0,
    "codigo_provincia":   1,
    "nombre_provincia":   2,
    "poblacion":          3,
    "num_mesas":          4,
    "censo_sin_cera":     5,
    "censo_cera":         6,
    "censo_total":        7,
    "votantes_cer":       8,
    "votantes_cera":      9,
    "votantes_total":    10,
    "votos_validos":     11,
    "votos_candidaturas":12,
    "votos_blanco":      13,
    "votos_nulos":       14,
}

FIRST_PARTY_COL = 15   # primera columna de votos de partido
