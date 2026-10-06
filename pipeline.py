"""
Pipeline completo: XLSX → D'Hondt → bloques → JSON para el frontend.

Uso:
    python pipeline.py                  # procesa todas las convocatorias disponibles
    python pipeline.py 202307 198910    # procesa convocatorias específicas
    python pipeline.py --check          # muestra qué convocatorias están disponibles

Salida en data/processed/:
    results_all.parquet      → tabla completa por (conv, provincia, partido)
    blocks_all.parquet       → tabla por bloques
    summary_province.json    → resumen por provincia listo para el frontend
    bloques_meta.json        → colores y labels de los bloques
"""

import json
import sys
from pathlib import Path

import pandas as pd

from formats import CONVOCATORIAS
from parser import parse_all, _zip_path
from dhondt import compute_all_provinces, province_summary
from blocks import add_blocks, block_summary, winning_block, BLOQUES

PROCESSED_DIR = Path(__file__).parent / "data" / "processed"


def check_available() -> list[str]:
    available = [c for c in CONVOCATORIAS if _zip_path(c).exists()]
    print(f"\nConvocatorias disponibles ({len(available)}/{len(CONVOCATORIAS)}):")
    for conv_id, label in CONVOCATORIAS.items():
        status = "✓" if conv_id in available else "✗ (ZIP no encontrado)"
        print(f"  {conv_id}  {label:<12}  {status}")
    return available


def run(conv_ids: list[str]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nParsing {len(conv_ids)} convocatoria(s)…")
    df_meta, df_votos = parse_all(conv_ids)

    if df_meta.empty:
        print("[ERROR] No se parsearon datos.")
        return

    print(f"\nCalculando D'Hondt y barrera real…")
    df_results = compute_all_provinces(df_meta, df_votos)

    # Verificación global D'Hondt vs XLSX oficial
    n_total = df_results["codigo_provincia"].nunique() * df_results["conv_id"].nunique()
    n_ok    = df_results.groupby(["conv_id", "codigo_provincia"])["dhondt_verificado"].first().sum()
    print(f"  Verificación D'Hondt vs XLSX: {n_ok:.0f}/{df_results.groupby(['conv_id','codigo_provincia']).ngroups} provincias correctas")

    discrepancias = df_results[df_results["escanos_dhondt"] != df_results["escanos_xlsx"]]
    if not discrepancias.empty:
        print(f"\n  [AVISO] {len(discrepancias)} discrepancias D'Hondt vs XLSX (empates o partidos con igual cociente):")
        cols = ["conv_id", "nombre_provincia", "siglas", "votos", "escanos_dhondt", "escanos_xlsx"]
        print(discrepancias[cols].head(10).to_string(index=False))

    print(f"\nAsignando bloques ideológicos…")
    df_results = add_blocks(df_results)

    # Partidos importantes sin bloque asignado
    otros = df_results[df_results["bloque"] == "otros"]
    if not otros.empty:
        top_sin_bloque = (
            otros.groupby("siglas")["votos"].sum()
            .sort_values(ascending=False).head(15)
        )
        print(f"\n  Partidos sin bloque (top por votos totales históricos):")
        for sig, v in top_sin_bloque.items():
            print(f"    {sig:<25} {v:>10,}")

    df_blocks = block_summary(df_results)

    # ── Guardar ──────────────────────────────────
    df_results.to_parquet(PROCESSED_DIR / "results_all.parquet", index=False)
    df_blocks.to_parquet( PROCESSED_DIR / "blocks_all.parquet",  index=False)
    print(f"\nGuardado results_all.parquet  ({len(df_results):,} filas)")

    # ── JSON para el frontend ─────────────────────
    output = _build_json(df_results, df_blocks)
    json_path = PROCESSED_DIR / "summary_province.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Guardado summary_province.json  ({len(output)} convocatorias)")

    bloques_meta = {k: {"label": v["label"], "color": v["color"]} for k, v in BLOQUES.items()}
    with open(PROCESSED_DIR / "bloques_meta.json", "w", encoding="utf-8") as f:
        json.dump(bloques_meta, f, ensure_ascii=False, indent=2)

    # ── Resumen de barrera real ────────────────────
    _print_barrier_summary(df_results)


def _build_json(df_results: pd.DataFrame, df_blocks: pd.DataFrame) -> dict:
    """Estructura JSON para el frontend: {conv_id: {cod_prov: {...}}}"""
    output = {}
    prov_sum = province_summary(df_results)
    winning  = winning_block(df_blocks)

    for conv_id in sorted(df_results["conv_id"].unique()):
        cr = df_results[df_results["conv_id"] == conv_id]
        cb = df_blocks[df_blocks["conv_id"] == conv_id]
        ps = prov_sum[prov_sum["conv_id"] == conv_id]

        # Escaños por bloque y provincia
        blocks_pivot = (
            cb.pivot_table(index="codigo_provincia", columns="bloque",
                           values="escanos", aggfunc="sum", fill_value=0)
            .to_dict(orient="index")
        )

        output[conv_id] = {}
        label = CONVOCATORIAS[conv_id]

        for _, row in ps.iterrows():
            cp = row["codigo_provincia"]
            w  = winning[(winning["conv_id"] == conv_id) & (winning["codigo_provincia"] == cp)]
            bloque_ganador = w["bloque_ganador"].iloc[0] if len(w) else "otros"

            # Top 5 partidos por votos en esa provincia
            top5 = (
                cr[cr["codigo_provincia"] == cp]
                .nlargest(5, "votos")[["siglas", "votos", "escanos_dhondt", "bloque"]]
                .to_dict("records")
            )

            output[conv_id][cp] = {
                "nombre":               row["nombre_provincia"],
                "label_eleccion":       label,
                "seats_total":          int(row["seats_total"]),
                "votos_candidaturas":   int(row["votos_candidaturas"]),
                "barrera_real_pct":     float(row["barrera_real_pct"]) if pd.notna(row["barrera_real_pct"]) else None,
                "partido_ultimo_escano":row["partido_ultimo_escano"],
                "bloque_ganador":       bloque_ganador,
                "escanos_por_bloque":   {k: int(v) for k, v in blocks_pivot.get(cp, {}).items()},
                "top5_partidos":        top5,
            }

    return output


def _print_barrier_summary(df_results: pd.DataFrame) -> None:
    """Imprime tabla de barrera real por provincia para la última convocatoria."""
    last_conv = sorted(df_results["conv_id"].unique())[-1]
    label     = CONVOCATORIAS[last_conv]
    subset    = (
        df_results[df_results["conv_id"] == last_conv]
        .groupby(["nombre_provincia", "seats_total"])["barrera_real_pct"]
        .first().reset_index()
        .sort_values("seats_total")
    )
    print(f"\n{'─'*55}")
    print(f"Barrera real por provincia — {label} ({last_conv})")
    print(f"{'Provincia':<25} {'Escaños':>7}  {'Barrera real':>12}")
    print(f"{'─'*55}")
    for _, r in subset.iterrows():
        print(f"{r['nombre_provincia']:<25} {int(r['seats_total']):>7}  {r['barrera_real_pct']:>11.1f}%")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--check" in args:
        check_available()
        sys.exit(0)

    targets = [a for a in args if not a.startswith("--")]
    if not targets:
        targets = check_available()

    if targets:
        run(targets)
