"""
Agrupación de candidaturas en bloques ideológicos.

El mapa de partidos → bloques se construye por orden de prioridad:
  1. Coincidencia exacta de siglas (normalizada)
  2. Coincidencia por prefijo/regex sobre la denominación
  3. "otros" si no coincide nada

Bloques definidos:
  izq_federal     → izquierda de ámbito estatal (PSOE, IU, Podemos, Sumar…)
  dcha_federal    → derecha de ámbito estatal (PP, Vox, Cs…)
  nac_izq         → nacionalismo/independentismo de izquierda (ERC, EH Bildu…)
  nac_centro      → nacionalismo centro o centro-derecha (PNV, CiU/JxCat, CC…)
  regionalismo    → partidos regionalistas sin adscripción clara (PRC, PAR…)
  otros           → residual
"""

import re
import pandas as pd

# ──────────────────────────────────────────────────────────────
# Definición de bloques
# ──────────────────────────────────────────────────────────────
BLOQUES = {
    "izq_federal": {
        "label": "Izquierda federal",
        "color": "#E63946",
        "siglas_exactas": {
            # PSOE y federaciones territoriales
            "PSOE", "PSC", "PSdeG-PSOE", "PSN-PSOE", "FSA-PSOE", "PSC-PSOE",
            # IU, comunistas y confluencias
            "IU", "PCE", "IC-V", "ICV", "EU", "IU-LV",
            "PCPE", "P.C.P.E.", "PTE-UC",  # comunistas históricos
            "ECP", "ECP-GUANYEM EL CANVI", "EN COMÚ", "EN COMÚ PODEM",
            "EQUO", "LOS VERDES", "VERDES", "LV-LV", "LVE",
            # Podemos / Unidas Podemos
            "PODEMOS", "UP", "UNIDAS PODEMOS", "UP-IU",
            # Sumar / Más País
            "SUMAR", "MÁS PAÍS", "MAS PAIS", "MP",
            # Confluencias y partidos de izquierda territorial de ámbito estatal
            "COMPROMÍS", "MÉS COMPROMÍS", "COMPROMÍS 2019",
            "CHA", "CHUNTA",
            "UPyD",   # centro-izquierda federal (reformista)
            # Partidos históricos transición democrática
            "PSP",    # Partido Socialista Popular (Tierno Galván, 1977-1978)
            "PSOE-H", # PSOE Histórico (escisión)
            "PTE",    # Partido del Trabajo de España (comunista, 1977-1979)
            "ORT",    # Organización Revolucionaria de los Trabajadores
            "PTE-ORT", "PT-ORT",
        },
        "regex_denominacion": [
            r"partido socialista",
            r"izquierda unida",
            r"podemos",
            r"unidas podemos",
            r"sumar",
            r"más país",
            r"en comú",
            r"guanyem",
            r"equo",
            r"verdes",
            r"union progreso",
            r"upyd",
        ],
    },
    "dcha_federal": {
        "label": "Derecha federal",
        "color": "#457B9D",
        "siglas_exactas": {
            "PP", "AP", "AP-PDP-PL", "AP-PDP",
            "UCD",
            "CDS",
            "C'S", "CS", "CIUDADANOS", "C´S", "Cs",
            "VOX",
            "UPN", "U.P.N.",   # Unión del Pueblo Navarro, aliada del PP
            "NA+",             # Navarra Suma (PP+Cs+UPN)
            # Partidos históricos transición democrática
            "CD",   # Coalición Democrática (AP+PDP, 1979)
            "CP",   # Coalición Popular (AP+PDP+PL, 1982-1986)
            "PRD",  # Partido Reformista Democrático (1986, Miquel Roca)
            "UN",   # Unión Nacional (ultraderecha, 1979)
        },
        "regex_denominacion": [
            r"partido popular",
            r"alianza popular",
            r"vox",
            r"ciudadanos",
            r"union de centro",
            r"navarra suma",
        ],
    },
    "nac_izq": {
        "label": "Nacionalismo izquierda",
        "color": "#A8DADC",
        "siglas_exactas": {
            "ERC", "ERC-SOBIRANISTES",
            "HB", "EH", "EH BILDU", "EH Bildu", "BILDU", "EA", "ARALAR",
            "EE",              # Euskadiko Ezkerra (histórico)
            "EA-EUE",          # Eusko Alkartasuna-Euskal Ezkerra
            "AMAIUR",          # coalición abertzale 2011
            "BNG",
            "NÓS",             # Candidatura Galega (BNG-CG)
            "AGE", "EN MAREA", "ANOVA",
            "CUP", "CUP-PR",
            "GBAI",            # Geroa Bai (Navarra)
            "NA-BAI", "Na-Bai", # Nafarroa Bai
            "NC-bc", "NC",     # Nueva Canarias
            "PSA-PA",  # Partido Socialista de Andalucía / Partido Andalucista (andalucismo de izquierda)
            "PSM-ENE", "PSM-EN,EU,EV,ER",  # Mallorca
            "FRONT REPUBLICÀ",
            "BLOC-VERDS", "BLOC-EV",  # Bloc Nacionalista Valencia
            "UPV",             # Unitat del Poble Valencia
            "ARALAR-ZUTIK",    # Aralar (abertzale izq.)
        },
        "regex_denominacion": [
            r"esquerra republicana",
            r"euskal herria bildu",
            r"herri batasuna",
            r"bloque nacionalista galego",
            r"candidatura d.unitat popular",
            r"en marea",
            r"nueva canarias",
            r"amaiur",
            r"geroa bai",
            r"nafarroa bai",
            r"euskadiko ezkerra",
            r"eusko alkartasuna",
            r"front republicà",
            r"candidatura galega",
            r"aralar",
            r"bloc nacionalista",
        ],
    },
    "nac_centro": {
        "label": "Nacionalismo centro",
        "color": "#F4A261",
        "siglas_exactas": {
            "CiU", "CIU", "CDC", "PDC", "JUNTS", "JXCAT", "JxCAT",
            "PDECAT-E-CIU", "PDeCAT-E-CiU", "unio.cat",
            "PNV", "EAJ-PNV",
            "CC", "CCa", "CC-PNC", "CCa-PNC",  # Coalición Canaria y variantes
            "AIC",             # Agrupaciones Independientes de Canarias (histórico)
            "PA",              # Partido Andalucista
            "CA",              # Coalición Andalucista
            "PAR",             # Partido Aragonés
            "UV",              # Unió Valenciana (histórico)
            # Cataluña transición
            "PDPC",            # Pacte Democràtic per Catalunya (Convergència, 1977-1979)
            "FDC-EDC",         # Federació de Democràcia Cristiana (UDC, parte de CiU histórico)
            "UDC-IDCC",        # Unió Democràtica de Catalunya (parte de CiU)
        },
        "regex_denominacion": [
            r"convergènc",
            r"convergencia i unio",
            r"junts per",
            r"partido nacionalista vasco",
            r"coalicion canaria",
            r"coalició canària",
            r"partido aragonés",
            r"unio valenciana",
            r"partit demòcrata",
            r"agrupaciones independientes de canarias",
            r"unio democràtica",
        ],
    },
    "regionalismo": {
        "label": "Regionalismo",
        "color": "#E9C46A",
        "siglas_exactas": {
            "PRC",     # Partido Regionalista de Cantabria
            "FORO", "FAC",
            "EXISTE",  # Teruel/Aragón/España Vaciada
            "SY",      # Soria ¡Ya!
            "TE",
            "RUIZ-MATEOS",   # Agrupación Ruiz-Mateos (1989)
            "UPL", "U.P.L.", # Unión del Pueblo Leonés
            "PAS",           # Partiu Asturianista
            "CG",            # Coalición Galega (histórico)
        },
        "regex_denominacion": [
            r"partido regionalista",
            r"foro asturias",
            r"teruel existe",
            r"soria.*ya",
            r"españa vaciada",
            r"aragón existe",
            r"ruiz.mateos",
            r"union del pueblo leon",
            r"partiu asturianista",
            r"coalicion galega",
        ],
    },
}


def _build_lookup(bloques: dict) -> tuple[dict, list]:
    """Pre-compila el lookup de siglas exactas y la lista de regex."""
    siglas_map = {}
    for bloque_id, bloque in bloques.items():
        for s in bloque.get("siglas_exactas", set()):
            siglas_map[s.upper()] = bloque_id

    regex_list = []
    for bloque_id, bloque in bloques.items():
        for pattern in bloque.get("regex_denominacion", []):
            regex_list.append((re.compile(pattern, re.IGNORECASE), bloque_id))

    return siglas_map, regex_list


_SIGLAS_MAP, _REGEX_LIST = _build_lookup(BLOQUES)


def classify(siglas: str, denominacion: str = "") -> str:
    """Clasifica un partido en un bloque. Devuelve el id del bloque."""
    key = (siglas or "").strip().upper()
    if key in _SIGLAS_MAP:
        return _SIGLAS_MAP[key]

    text = (denominacion or "").strip()
    for pattern, bloque_id in _REGEX_LIST:
        if pattern.search(text):
            return bloque_id

    return "otros"


def add_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade columna 'bloque' a un DataFrame que tenga columnas 'siglas' y 'denominacion'.
    """
    df = df.copy()
    if "denominacion" not in df.columns:
        df["denominacion"] = ""
    df["bloque"] = df.apply(
        lambda r: classify(r["siglas"], r.get("denominacion", "")),
        axis=1
    )
    return df


def block_summary(df_result: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega escaños por bloque para cada (conv_id, provincia).
    df_result debe tener columna 'bloque' (añadida con add_blocks).
    """
    return (
        df_result.groupby(["conv_id", "codigo_provincia", "nombre_provincia", "bloque"])
        .agg(
            escanos=("escanos_dhondt", "sum"),
            votos  =("votos",          "sum"),
        )
        .reset_index()
    )


def winning_block(df_block_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Determina el bloque ganador (más escaños) por provincia y convocatoria.
    En caso de empate, gana el bloque con más votos.
    """
    return (
        df_block_summary
        .sort_values(["escanos", "votos"], ascending=False)
        .groupby(["conv_id", "codigo_provincia", "nombre_provincia"])
        .first()
        .reset_index()
        .rename(columns={"bloque": "bloque_ganador"})
    )


if __name__ == "__main__":
    # Test con siglas conocidas
    test_cases = [
        ("PSOE",      "Partido Socialista Obrero Español"),
        ("PP",        "Partido Popular"),
        ("ERC",       "Esquerra Republicana de Catalunya"),
        ("EAJ-PNV",   "Partido Nacionalista Vasco"),
        ("VOX",       "Vox"),
        ("SUMAR",     "Sumar"),
        ("JXCAT",     "Junts per Catalunya"),
        ("DESCONOCIDO", "Partido Inventado de Prueba"),
    ]
    print(f"{'Siglas':<15} {'Bloque':<20} {'Label'}")
    print("-" * 55)
    for siglas, denom in test_cases:
        bloque_id = classify(siglas, denom)
        label = BLOQUES.get(bloque_id, {}).get("label", "Otros")
        print(f"{siglas:<15} {bloque_id:<20} {label}")
