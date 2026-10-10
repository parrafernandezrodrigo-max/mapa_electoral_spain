"""
Porcentajes de voto estimados por provincia (2026 vs 2023).
Usa el mismo swing uniforme proporcional que estima_2026.py.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_conv

# ─── Estimaciones nacionales PDF 40dB octubre 2026 ───────────────────────────
POLL_2026 = {
    "PP":      31.9,
    "PSOE":    28.1,
    "VOX":     18.9,
    "SUMAR":    5.3,
    "PODEMOS":  2.3,
    "SALF":     1.8,
    "OTROS":   11.7,
}

NATIONAL_PARTIES = {"PP", "PSOE", "VOX", "SUMAR"}

df_meta, df_votos = parse_conv("202307")

nat_2023 = df_votos.groupby("siglas")["votos"].sum()
total_23  = nat_2023.sum()
nat_pct_23 = nat_2023 / total_23 * 100
others_23  = 100 - sum(nat_pct_23.get(p, 0) for p in NATIONAL_PARTIES)
sumar_23   = nat_pct_23.get("SUMAR", 0)

scale = {
    "PP":    POLL_2026["PP"]    / nat_pct_23.get("PP",   1),
    "PSOE":  POLL_2026["PSOE"]  / nat_pct_23.get("PSOE", 1),
    "VOX":   POLL_2026["VOX"]   / nat_pct_23.get("VOX",  1),
    "SUMAR": POLL_2026["SUMAR"] / sumar_23,
    "OTROS": POLL_2026["OTROS"] / others_23,
}
podemos_from_sumar = POLL_2026["PODEMOS"] / sumar_23
salf_from_pp       = POLL_2026["SALF"]    / nat_pct_23.get("PP", 1)

provinces = df_meta.groupby(["codigo_provincia", "nombre_provincia"]).agg(
    escanos=("escanos_asignados", "first"),
    votos_candidaturas=("votos_candidaturas", "first"),
).reset_index()

rows = []

for _, prov in provinces.iterrows():
    cod   = prov["codigo_provincia"]
    name  = prov["nombre_provincia"]
    seats = int(prov["escanos"])

    pv = (
        df_votos[df_votos["codigo_provincia"] == cod]
        .set_index("siglas")["votos"]
        .to_dict()
    )

    def v23(p):
        return pv.get(p, 0)

    # ── Votos estimados 2026 ──────────────────────────────────────────────────
    v26 = {}
    v26["PP"]      = v23("PP")    * scale["PP"]
    v26["PSOE"]    = v23("PSOE")  * scale["PSOE"]
    v26["VOX"]     = v23("VOX")   * scale["VOX"]
    v26["SUMAR"]   = v23("SUMAR") * scale["SUMAR"]
    v26["PODEMOS"] = v23("SUMAR") * podemos_from_sumar
    v26["SALF"]    = v23("PP")    * salf_from_pp
    for party, votes in pv.items():
        if party not in NATIONAL_PARTIES:
            v26[party] = votes * scale["OTROS"]

    total_26 = sum(v26.values())
    total_23_prov = sum(pv.values())

    def pct26(p):
        return v26.get(p, 0) / total_26 * 100 if total_26 else 0

    def pct23(p):
        return pv.get(p, 0) / total_23_prov * 100 if total_23_prov else 0

    otros_26 = sum(v for p, v in v26.items()
                   if p not in {"PP","PSOE","VOX","SUMAR","PODEMOS","SALF"})
    otros_23 = sum(v for p, v in pv.items()
                   if p not in NATIONAL_PARTIES)

    rows.append({
        "provincia":  name,
        "escanos":    seats,
        # 2026 estimado
        "PP_26":      round(pct26("PP"),    1),
        "PSOE_26":    round(pct26("PSOE"),  1),
        "VOX_26":     round(pct26("VOX"),   1),
        "SUMAR_26":   round(pct26("SUMAR"), 1),
        "PODEMOS_26": round(pct26("PODEMOS"),1),
        "SALF_26":    round(pct26("SALF"),  1),
        "OTROS_26":   round(otros_26 / total_26 * 100, 1) if total_26 else 0,
        # 2023 real
        "PP_23":      round(pct23("PP"),    1),
        "PSOE_23":    round(pct23("PSOE"),  1),
        "VOX_23":     round(pct23("VOX"),   1),
        "SUMAR_23":   round(pct23("SUMAR"), 1),
        "OTROS_23":   round(otros_23 / total_23_prov * 100, 1) if total_23_prov else 0,
        # Diferencias
        "PP_d":       round(pct26("PP")    - pct23("PP"),    1),
        "PSOE_d":     round(pct26("PSOE")  - pct23("PSOE"),  1),
        "VOX_d":      round(pct26("VOX")   - pct23("VOX"),   1),
        "SUMAR_d":    round(pct26("SUMAR") - pct23("SUMAR"), 1),
    })

df = pd.DataFrame(rows).sort_values("provincia").reset_index(drop=True)

# ─── Guardar CSV completo ─────────────────────────────────────────────────────
out = Path(__file__).parent / "data" / "pct_provincias_2026.csv"
df.to_csv(out, index=False)
print(f"CSV guardado: {out}\n")

# ─── Imprimir tabla por provincia ────────────────────────────────────────────
print("=" * 120)
print(f"{'PROVINCIA':<28} {'ESC':>3}  "
      f"{'PP 26':>6} {'PSOE 26':>7} {'VOX 26':>6} {'SUM 26':>6} {'POD 26':>6} {'SALF 26':>7} {'OTR 26':>6}  "
      f"{'PP 23':>6} {'PSOE 23':>7} {'VOX 23':>6} {'SUM 23':>6} {'OTR 23':>6}  "
      f"{'ΔPP':>5} {'ΔPSOE':>5} {'ΔVOX':>5} {'ΔSUM':>5}")
print("-" * 120)

for _, r in df.iterrows():
    print(
        f"{r['provincia']:<28} {r['escanos']:>3}  "
        f"{r['PP_26']:>6.1f} {r['PSOE_26']:>7.1f} {r['VOX_26']:>6.1f} "
        f"{r['SUMAR_26']:>6.1f} {r['PODEMOS_26']:>6.1f} {r['SALF_26']:>7.1f} {r['OTROS_26']:>6.1f}  "
        f"{r['PP_23']:>6.1f} {r['PSOE_23']:>7.1f} {r['VOX_23']:>6.1f} "
        f"{r['SUMAR_23']:>6.1f} {r['OTROS_23']:>6.1f}  "
        f"{r['PP_d']:>+5.1f} {r['PSOE_d']:>+5.1f} {r['VOX_d']:>+5.1f} {r['SUMAR_d']:>+5.1f}"
    )

print("-" * 120)
# Fila nacional (promedio ponderado por votos → usamos los totales del PDF)
print(f"\n{'NACIONAL (PDF 40dB)':<28} {'350':>3}  "
      f"{'31.9':>6} {'28.1':>7} {'18.9':>6} {'5.3':>6} {'2.3':>6} {'1.8':>7} {'11.7':>6}  "
      f"{'33.1':>6} {'31.7':>7} {'12.4':>6} {'12.3':>6} {'10.5':>6}  "
      f"{'-1.2':>+5} {'-3.6':>+5} {'+6.5':>+5} {'-7.0':>+5}")
