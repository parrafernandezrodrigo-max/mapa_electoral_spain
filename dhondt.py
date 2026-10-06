"""
Algoritmo D'Hondt y cálculo de la barrera electoral real.

La barrera legal en España es del 3% provincial, pero la barrera
REAL (porcentaje mínimo para obtener UN escaño) depende del número de
escaños de la provincia y de cómo se distribuyen los votos.

Barrera real = cociente D'Hondt que ganó el último escaño / votos válidos * 100
"""

import pandas as pd


def dhondt(votes: dict[str, int], seats: int) -> tuple[dict[str, int], float, str]:
    """
    Reparte 'seats' escaños según D'Hondt.

    Returns:
        (escanos_dict, ultimo_cociente, partido_ultimo_escano)
    """
    if seats <= 0 or not votes:
        return {p: 0 for p in votes}, 0.0, ""

    # Generar todos los cocientes posibles
    quotients = [
        (v / d, party, d)
        for party, v in votes.items()
        for d in range(1, seats + 1)
    ]
    quotients.sort(key=lambda x: x[0], reverse=True)

    result = {p: 0 for p in votes}
    ultimo_cociente = 0.0
    ultimo_partido  = ""

    for i in range(seats):
        q, party, _ = quotients[i]
        result[party] += 1
        ultimo_cociente = q
        ultimo_partido  = party

    return result, ultimo_cociente, ultimo_partido


def real_barrier(votes: dict[str, int], seats: int, votos_candidaturas: int) -> dict | None:
    """
    Calcula la barrera electoral real para una circunscripción.

    Usamos 'votos a candidaturas' (no votos válidos totales) como denominador
    porque es el total que D'Hondt tiene en cuenta (excluye blancos y nulos).
    """
    votes = {p: v for p, v in votes.items() if v > 0}
    if not votes or seats <= 0 or votos_candidaturas <= 0:
        return None

    escanos, ultimo_q, ultimo_p = dhondt(votes, seats)

    return {
        "escanos":               escanos,
        "ultimo_cociente":       ultimo_q,
        "partido_ultimo_escano": ultimo_p,
        "barrera_real_pct":      round(ultimo_q / votos_candidaturas * 100, 3),
    }


def compute_all_provinces(df_meta: pd.DataFrame, df_votos: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica D'Hondt a todas las provincias de una convocatoria.

    Args:
        df_meta:  de parser.parse_conv() → df_meta
        df_votos: de parser.parse_conv() → df_votos

    Returns:
        DataFrame con una fila por (conv_id, provincia, partido):
          escanos_dhondt, barrera_real_pct, es_ultimo_escano, verificado
    """
    # Añadir metadatos de provincia al DataFrame de votos
    df = df_votos.merge(
        df_meta[["conv_id", "codigo_provincia", "escanos_asignados", "votos_candidaturas"]],
        on=["conv_id", "codigo_provincia"],
        how="left"
    )

    results = []

    for (conv_id, cod_prov), grp in df.groupby(["conv_id", "codigo_provincia"]):
        seats       = int(grp["escanos_asignados"].iloc[0])
        total_votos = int(grp["votos_candidaturas"].iloc[0])
        votes_dict  = dict(zip(grp["siglas"], grp["votos"]))

        rb = real_barrier(votes_dict, seats, total_votos)
        if rb is None:
            continue

        # Verificar que nuestro D'Hondt coincide con los datos oficiales del XLSX
        escanos_oficiales  = dict(zip(grp["siglas"], grp["diputados_xlsx"]))
        total_dhondt       = sum(rb["escanos"].values())
        total_oficial      = sum(escanos_oficiales.values())
        verificado         = (total_dhondt == total_oficial == seats)

        for _, row in grp.iterrows():
            partido = row["siglas"]
            results.append({
                "conv_id":            conv_id,
                "anno":               row["anno"],
                "codigo_provincia":   cod_prov,
                "nombre_provincia":   row["nombre_provincia"],
                "siglas":             partido,
                "denominacion":       row["denominacion"],
                "votos":              row["votos"],
                "escanos_dhondt":     rb["escanos"].get(partido, 0),
                "escanos_xlsx":       escanos_oficiales.get(partido, 0),
                "seats_total":        seats,
                "votos_candidaturas": total_votos,
                "barrera_real_pct":   rb["barrera_real_pct"],
                "ultimo_cociente":    rb["ultimo_cociente"],
                "partido_ultimo_escano": rb["partido_ultimo_escano"],
                "es_ultimo_escano":   partido == rb["partido_ultimo_escano"],
                "dhondt_verificado":  verificado,
            })

    return pd.DataFrame(results)


def province_summary(df_result: pd.DataFrame) -> pd.DataFrame:
    """Una fila por (conv_id, provincia) con el resumen de la circunscripción."""
    return (
        df_result
        .groupby(["conv_id", "anno", "codigo_provincia", "nombre_provincia"])
        .agg(
            seats_total          =("seats_total",           "first"),
            votos_candidaturas   =("votos_candidaturas",    "first"),
            barrera_real_pct     =("barrera_real_pct",      "first"),
            partido_ultimo_escano=("partido_ultimo_escano", "first"),
            ultimo_cociente      =("ultimo_cociente",       "first"),
            dhondt_verificado    =("dhondt_verificado",     "first"),
        )
        .reset_index()
    )


if __name__ == "__main__":
    # Test del algoritmo
    votos = {"PSOE": 250_000, "PP": 200_000, "VOX": 80_000, "SUMAR": 60_000, "ERC": 40_000}
    escanos, ultimo_q, ultimo_p = dhondt(votos, 8)
    print("D'Hondt (8 escaños):")
    for p, e in sorted(escanos.items(), key=lambda x: -x[1]):
        print(f"  {p:<8} {e}")
    total = sum(votos.values())
    print(f"\nÚltimo escaño: {ultimo_p} (cociente {ultimo_q:,.0f})")
    print(f"Barrera real: {ultimo_q/total*100:.2f}%")
