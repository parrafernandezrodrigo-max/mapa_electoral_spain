"""
Parser para los XLSX de Infoelectoral (Ministerio del Interior).

Función principal:
  parse_conv(conv_id)  →  (df_meta, df_votos)

df_meta  → una fila por provincia con censo, votos totales, escaños asignados
df_votos → una fila por (provincia, partido) con votos y diputados obtenidos
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from formats import CONVOCATORIAS

RAW_DIR = Path(__file__).parent / "data" / "raw"

ROW_DENOMINACION = 3
ROW_SIGLAS       = 4
ROW_HEADERS      = 5
ROW_DATA_START   = 6

# Nombres de columnas de metadatos (fijos en todas las convocatorias)
META_FIXED = [
    "nombre_ccaa", "codigo_provincia", "nombre_provincia", "poblacion",
    "num_mesas", "censo_sin_cera", "censo_cera", "censo_total",
    "votantes_cer", "votantes_cera", "votantes_total",
    "votos_validos", "votos_candidaturas", "votos_blanco", "votos_nulos",
]
# Algunas convocatorias añaden una columna extra entre metadata y partidos;
# la detectamos dinámicamente con _detect_layout().


def _zip_path(conv_id: str) -> Path:
    return RAW_DIR / f"PROV_02_{conv_id}_1.zip"


def _load_raw(conv_id: str) -> pd.DataFrame:
    """Lee el XLSX del ZIP sin procesar (header=None)."""
    path = _zip_path(conv_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró {path.name}\n"
            f"Descarga el ZIP de https://infoelectoral.interior.gob.es "
            f"y colócalo en data/raw/"
        )
    with zipfile.ZipFile(path) as arch:
        xlsx_name = next(f for f in arch.namelist() if f.endswith(".xlsx"))
        data = arch.read(xlsx_name)

    return pd.read_excel(io.BytesIO(data), sheet_name=0, header=None, dtype=object)


def _detect_layout(raw: pd.DataFrame) -> tuple[dict[str, int], int]:
    """
    Detecta dinámicamente las posiciones de las columnas de metadatos y
    la primera columna de partido, leyendo la fila de cabeceras (ROW_HEADERS).

    Devuelve:
        meta_cols  : {nombre_campo: índice_columna}
        first_party: índice de la primera columna de votos de partido
    """
    headers = [str(raw.iloc[ROW_HEADERS, c] or "").strip() for c in range(raw.shape[1])]

    # La primera columna de partido es la primera vez que aparece "Votos"
    # sin ningún calificativo adicional (no "Votos válidos", etc.)
    first_party = None
    for i, h in enumerate(headers):
        if h == "Votos":
            first_party = i
            break

    if first_party is None:
        raise ValueError(f"No se encontró columna 'Votos' de partido en fila {ROW_HEADERS}")

    # Las columnas de metadata son las previas a first_party
    # Las asignamos en orden con los nombres conocidos
    meta_cols = {name: i for i, name in enumerate(META_FIXED) if i < first_party}

    # Si first_party > len(META_FIXED), hay columnas extra de metadatos
    # Las asignamos igualmente posicionalmente (el orden es constante)
    if first_party != len(META_FIXED):
        # Reasignar: los últimos META_FIXED fields se comprimen/expanden
        # La posición relativa es la misma, solo hay un offset
        offset = first_party - len(META_FIXED)
        meta_cols = {name: i + (offset if i >= len(META_FIXED) - 1 else 0)
                     for i, name in enumerate(META_FIXED)}
        # Más seguro: mapear por coincidencia de nombre de cabecera
        meta_cols = {}
        name_map = {
            "nombre de comunidad":     "nombre_ccaa",
            "código de provincia":     "codigo_provincia",
            "nombre de provincia":     "nombre_provincia",
            "población":               "poblacion",
            "número de mesas":         "num_mesas",
            "censo electoral sin cera":"censo_sin_cera",
            "censo cera":              "censo_cera",
            "total censo electoral":   "censo_total",
            "total votantes cer":      "votantes_cer",
            "total votantes cera":     "votantes_cera",
            "total votantes":          "votantes_total",
            "votos válidos":           "votos_validos",
            "votos a candidaturas":    "votos_candidaturas",
            "votos en blanco":         "votos_blanco",
            "votos nulos":             "votos_nulos",
        }
        for col_idx, h in enumerate(headers[:first_party]):
            key = h.lower().strip()
            if key in name_map:
                meta_cols[name_map[key]] = col_idx

    return meta_cols, first_party


def _extract_parties(raw: pd.DataFrame, first_party_col: int) -> list[dict]:
    """
    Extrae la lista de partidos a partir de las filas de cabecera.
    Devuelve lista de {col_votos, col_diputados, siglas, denominacion}.
    """
    parties = []
    col = first_party_col
    while col < raw.shape[1]:
        denominacion = raw.iloc[ROW_DENOMINACION, col]
        siglas       = raw.iloc[ROW_SIGLAS,       col]

        # Convertir a string limpio; NaN/None → vacío
        denominacion = "" if pd.isna(denominacion) else str(denominacion).strip()
        siglas       = "" if pd.isna(siglas)       else str(siglas).strip()

        if denominacion:
            parties.append({
                "col_votos":     col,
                "col_diputados": col + 1,
                "siglas":        siglas or denominacion[:20],
                "denominacion":  denominacion,
            })
        col += 2
    return parties


def _is_data_row(row: pd.Series, cod_prov_col: int) -> bool:
    """True si la fila es una circunscripción (provincia), no totales ni cabecera."""
    val = row.iloc[cod_prov_col]
    if pd.isna(val):
        return False
    try:
        n = int(val)
        return 1 <= n <= 52
    except (ValueError, TypeError):
        return False


def _to_int(val) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def parse_conv(conv_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parsea todos los datos de una convocatoria.

    Returns:
        df_meta  : una fila por provincia (metadatos + escaños asignados desde D'Hondt)
        df_votos : una fila por (provincia, partido)
    """
    raw = _load_raw(conv_id)
    meta_cols, first_party_col = _detect_layout(raw)
    parties = _extract_parties(raw, first_party_col)

    label = CONVOCATORIAS[conv_id]
    anno  = int(conv_id[:4])
    mes   = int(conv_id[4:])

    cod_prov_col = meta_cols["codigo_provincia"]

    meta_rows  = []
    votos_rows = []

    for idx in range(ROW_DATA_START, len(raw)):
        row = raw.iloc[idx]
        if not _is_data_row(row, cod_prov_col):
            continue

        cod_prov    = str(int(row.iloc[cod_prov_col])).zfill(2)
        nombre_prov = str(row.iloc[meta_cols.get("nombre_provincia", 2)] or "").strip()

        def _get(field):
            col = meta_cols.get(field)
            return _to_int(row.iloc[col]) if col is not None else 0

        escanos_total = sum(_to_int(row.iloc[p["col_diputados"]]) for p in parties)

        meta_rows.append({
            "conv_id":            conv_id,
            "label":              label,
            "anno":               anno,
            "mes":                mes,
            "codigo_provincia":   cod_prov,
            "nombre_provincia":   nombre_prov,
            "poblacion":          _get("poblacion"),
            "censo_total":        _get("censo_total"),
            "votantes_total":     _get("votantes_total"),
            "votos_validos":      _get("votos_validos"),
            "votos_candidaturas": _get("votos_candidaturas"),
            "votos_blanco":       _get("votos_blanco"),
            "votos_nulos":        _get("votos_nulos"),
            "escanos_asignados":  escanos_total,
        })

        for p in parties:
            votos     = _to_int(row.iloc[p["col_votos"]])
            diputados = _to_int(row.iloc[p["col_diputados"]])
            if votos > 0:
                votos_rows.append({
                    "conv_id":          conv_id,
                    "anno":             anno,
                    "mes":              mes,
                    "codigo_provincia": cod_prov,
                    "nombre_provincia": nombre_prov,
                    "siglas":           p["siglas"],
                    "denominacion":     p["denominacion"],
                    "votos":            votos,
                    "diputados_xlsx":   diputados,
                })

    df_meta  = pd.DataFrame(meta_rows)
    df_votos = pd.DataFrame(votos_rows)
    return df_meta, df_votos


def parse_all(conv_ids: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parsea todas las convocatorias disponibles y las concatena."""
    if conv_ids is None:
        conv_ids = [c for c in CONVOCATORIAS if _zip_path(c).exists()]

    all_meta  = []
    all_votos = []
    for conv_id in conv_ids:
        print(f"  Parseando {CONVOCATORIAS[conv_id]} ({conv_id})…")
        try:
            df_m, df_v = parse_conv(conv_id)
            all_meta.append(df_m)
            all_votos.append(df_v)
            print(f"    → {len(df_m)} provincias, {len(df_v)} filas de votos")
        except Exception as e:
            print(f"    [ERROR] {e}")

    return pd.concat(all_meta, ignore_index=True), pd.concat(all_votos, ignore_index=True)


if __name__ == "__main__":
    df_meta, df_votos = parse_conv("202307")
    print("\n=== METADATOS PROVINCIA (2023) ===")
    print(df_meta[["codigo_provincia", "nombre_provincia", "escanos_asignados",
                   "votos_candidaturas", "censo_total"]].to_string(index=False))
    print(f"\n=== VOTOS (primeras 20 filas) ===")
    print(df_votos.head(20).to_string(index=False))
    print(f"\nTotal partidos únicos: {df_votos['siglas'].nunique()}")
