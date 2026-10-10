"""
vox_threshold_analysis.py

Para cada provincia calcula:
  1. VOX % en 2019N y 2023 (trayectoria real)
  2. Umbral D'Hondt real para el escaño marginal de VOX (¿cuánto necesita?)
  3. Estimación 2026 (swing model)
  4. Combustible disponible: votos PP×15.6% + abstención×12.7%
     (según matriz de transferencia encuesta 40dB oct-26, pág.10)
  5. Gap = umbral - estimación_2026
  6. ¿Puede el combustible cerrar el gap?
  7. Nivel de confianza de que VOX gana ese escaño marginal
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_conv
from dhondt import dhondt

# ── Matriz de transferencia 40dB (pág. 10 del PDF) ────────────────────────────
# % de ex-votantes de cada grupo que irían a VOX
PP_TO_VOX       = 0.156   # 15.6% de ex-PP van a VOX
ABST_TO_VOX     = 0.127   # 12.7% de no-votantes 2023 irían a VOX

# ── Swing model (igual que estima_2026.py) ────────────────────────────────────
POLL_2026 = {"PP": 31.9, "PSOE": 28.1, "VOX": 18.9, "SUMAR": 5.3,
             "PODEMOS": 2.3, "SALF": 1.8, "OTROS": 11.7}
NATIONAL_PARTIES = {"PP", "PSOE", "VOX", "SUMAR"}

df_meta23, df_votos23 = parse_conv("202307")
df_meta19, df_votos19 = parse_conv("201911")

nat23    = df_votos23.groupby("siglas")["votos"].sum()
total23  = nat23.sum()
nat_pct  = nat23 / total23 * 100
others23 = 100 - sum(nat_pct.get(p, 0) for p in NATIONAL_PARTIES)
sumar23  = nat_pct.get("SUMAR", 0)

scale = {
    "PP":    POLL_2026["PP"]    / nat_pct.get("PP",   1),
    "PSOE":  POLL_2026["PSOE"]  / nat_pct.get("PSOE", 1),
    "VOX":   POLL_2026["VOX"]   / nat_pct.get("VOX",  1),
    "SUMAR": POLL_2026["SUMAR"] / sumar23,
    "OTROS": POLL_2026["OTROS"] / others23,
}
podemos_f = POLL_2026["PODEMOS"] / sumar23
salf_f    = POLL_2026["SALF"]    / nat_pct.get("PP", 1)


def next_seat_threshold(votes_dict: dict, current_seats: dict, seats_total: int) -> float:
    """
    Devuelve los votos mínimos que necesita VOX para ganar UN escaño más.
    Usa búsqueda binaria sobre los votos de VOX.
    """
    current_vox = votes_dict.get("VOX", 0)
    current_vox_seats = current_seats.get("VOX", 0)

    total_votes = sum(votes_dict.values())
    lo = current_vox
    hi = max(current_vox * 4 + 1, total_votes * 0.6)  # upper bound: enough to win majority
    for _ in range(50):
        mid = (lo + hi) / 2
        test_votes = {**votes_dict, "VOX": mid}
        result, _, _ = dhondt(test_votes, seats_total)
        if result.get("VOX", 0) > current_vox_seats:
            hi = mid
        else:
            lo = mid
    return hi


provinces = df_meta23.groupby(["codigo_provincia", "nombre_provincia"]).agg(
    escanos=("escanos_asignados", "first"),
    votos_candidaturas=("votos_candidaturas", "first"),
    censo=("censo_total", "first"),
).reset_index()

rows = []

for _, prov in provinces.iterrows():
    cod   = prov["codigo_provincia"]
    name  = prov["nombre_provincia"]
    seats = int(prov["escanos"])
    censo = int(prov["censo"])
    total_v23 = int(prov["votos_candidaturas"])

    # ── Votos reales 2023 ──────────────────────────────────────────────────
    pv23 = (df_votos23[df_votos23["codigo_provincia"] == cod]
            .set_index("siglas")["votos"].to_dict())

    # Abstención 2023 (censo - votantes totales)
    # votos_candidaturas != votantes_total (excluye blanco/nulo)
    # Usamos censo - votos_candidaturas como proxy de abstención+blanco+nulo
    abstention23 = max(censo - total_v23, 0)

    # ── VOX en 2019N ──────────────────────────────────────────────────────
    pv19 = (df_votos19[df_votos19["codigo_provincia"] == cod]
            .set_index("siglas")["votos"].to_dict())
    total_v19 = sum(pv19.values())
    vox_pct_19 = pv19.get("VOX", 0) / total_v19 * 100 if total_v19 else 0

    # ── VOX en 2023 ───────────────────────────────────────────────────────
    vox_pct_23 = pv23.get("VOX", 0) / total_v23 * 100 if total_v23 else 0

    # ── D'Hondt real 2023 (verificación) ─────────────────────────────────
    esc23, _, _ = dhondt({p: v for p, v in pv23.items() if v > 0}, seats)
    vox_seats_23 = esc23.get("VOX", 0)

    # ── Estimación 2026 (swing) ───────────────────────────────────────────
    def v23(p): return pv23.get(p, 0)

    v26 = {
        "PP":      v23("PP")    * scale["PP"],
        "PSOE":    v23("PSOE")  * scale["PSOE"],
        "VOX":     v23("VOX")   * scale["VOX"],
        "SUMAR":   v23("SUMAR") * scale["SUMAR"],
        "PODEMOS": v23("SUMAR") * podemos_f,
        "SALF":    v23("PP")    * salf_f,
    }
    for party, votes in pv23.items():
        if party not in NATIONAL_PARTIES:
            v26[party] = votes * scale["OTROS"]
    v26 = {p: v for p, v in v26.items() if v > 0}

    total_v26    = sum(v26.values())
    vox_est_26   = v26.get("VOX", 0)
    vox_pct_26   = vox_est_26 / total_v26 * 100 if total_v26 else 0

    esc26, _, _ = dhondt(v26, seats)
    vox_seats_26 = esc26.get("VOX", 0)

    # ── Umbral para escaño marginal de VOX ────────────────────────────────
    threshold_votes = next_seat_threshold(v26, esc26, seats)
    threshold_pct   = threshold_votes / total_v26 * 100

    gap_votes = threshold_votes - vox_est_26
    gap_pct   = threshold_pct - vox_pct_26

    # ── Combustible disponible ────────────────────────────────────────────
    # PP→VOX: ex-votantes PP 2023 que la encuesta dice pueden ir a VOX
    fuel_from_pp   = v23("PP") * PP_TO_VOX
    # Abstención→VOX: no-votantes que podrían activarse para VOX
    fuel_from_abst = abstention23 * ABST_TO_VOX
    fuel_total     = fuel_from_pp + fuel_from_abst
    fuel_pct       = fuel_total / total_v26 * 100 if total_v26 else 0

    # ── ¿Puede el combustible cerrar el gap? ─────────────────────────────
    # "Cobertura": cuánto del gap cubre el combustible (>1 = puede cubrir)
    coverage = fuel_total / gap_votes if gap_votes > 0 else 999

    # ── Nivel de confianza ────────────────────────────────────────────────
    if gap_pct <= 0:
        confidence = "SEGURO"        # ya está por encima del umbral
        conf_num   = 5
    elif gap_pct <= 1.5 and coverage >= 1.5:
        confidence = "MUY PROBABLE"
        conf_num   = 4
    elif gap_pct <= 3.0 and coverage >= 1.0:
        confidence = "PROBABLE"
        conf_num   = 3
    elif gap_pct <= 5.0 and coverage >= 0.7:
        confidence = "POSIBLE"
        conf_num   = 2
    else:
        confidence = "POCO PROBABLE"
        conf_num   = 1

    rows.append({
        "provincia":    name,
        "escanos":      seats,
        "vox_pct_19":   round(vox_pct_19, 1),
        "vox_pct_23":   round(vox_pct_23, 1),
        "vox_pct_26":   round(vox_pct_26, 1),
        "vox_seats_23": vox_seats_23,
        "vox_seats_26": vox_seats_26,
        "umbral_pct":   round(threshold_pct, 1),
        "gap_pp":       round(gap_pct, 1),
        "fuel_pp_pct":  round(fuel_from_pp  / total_v26 * 100, 1) if total_v26 else 0,
        "fuel_abs_pct": round(fuel_from_abst/ total_v26 * 100, 1) if total_v26 else 0,
        "fuel_total_pct": round(fuel_pct, 1),
        "coverage":     round(coverage, 2),
        "confidence":   confidence,
        "conf_num":     conf_num,
        "delta_19_23":  round(vox_pct_23 - vox_pct_19, 1),
        "delta_23_26":  round(vox_pct_26 - vox_pct_23, 1),
    })

df = pd.DataFrame(rows).sort_values(["conf_num","gap_pp"], ascending=[False, True]).reset_index(drop=True)

# ── Imprimir tabla completa ───────────────────────────────────────────────────
print("VOX — ANÁLISIS DE UMBRAL D'HONDT POR PROVINCIA")
print("Fuente transferencias: encuesta 40dB oct-26 (PP→VOX 15.6%, Abstención→VOX 12.7%)")
print()
hdr = (f"{'PROVINCIA':<26} {'ESC':>3}  "
       f"{'19N%':>5} {'23%':>5} {'26est%':>6} "
       f"{'esc23':>5} {'esc26':>5}  "
       f"{'umbral':>6} {'gap':>5}  "
       f"{'combustible':>11}  {'cobert':>6}  "
       f"{'CONFIANZA':>13}")
print(hdr)
print("-" * len(hdr))

CONF_SYMBOL = {
    "SEGURO":       "●●●●●",
    "MUY PROBABLE": "●●●●○",
    "PROBABLE":     "●●●○○",
    "POSIBLE":      "●●○○○",
    "POCO PROBABLE":"●○○○○",
}

for _, r in df.iterrows():
    gap_str  = f"{r['gap_pp']:+.1f}pp" if r['gap_pp'] != 999 else "  ya lo tiene"
    fuel_str = f"PP:{r['fuel_pp_pct']:.1f}+Abs:{r['fuel_abs_pct']:.1f}={r['fuel_total_pct']:.1f}pp"
    cov_str  = f"×{r['coverage']:.1f}" if r['coverage'] < 99 else "> ×10"
    print(
        f"{r['provincia']:<26} {r['escanos']:>3}  "
        f"{r['vox_pct_19']:>5.1f} {r['vox_pct_23']:>5.1f} {r['vox_pct_26']:>6.1f} "
        f"{r['vox_seats_23']:>5} {r['vox_seats_26']:>5}  "
        f"{r['umbral_pct']:>6.1f} {gap_str:>8}  "
        f"{fuel_str:>24}  {cov_str:>6}  "
        f"{r['confidence']:<13}  {CONF_SYMBOL[r['confidence']]}"
    )

print()
print("NOTAS:")
print("  umbral = % mínimo que necesita VOX para ganar el siguiente escaño (D'Hondt)")
print("  gap    = umbral - estimación_2026 (negativo = ya supera el umbral)")
print("  combustible = PP_2023×15.6% + Abstención_2023×12.7% sobre votos válidos 2026")
print("  cobertura   = combustible / gap  (>1 = combustible suficiente para cubrir el gap)")

# ── Guardar CSV ───────────────────────────────────────────────────────────────
out = Path(__file__).parent / "data" / "vox_threshold_2026.csv"
df.to_csv(out, index=False)
print(f"\nCSV: {out}")

# ── Resumen por nivel de confianza ────────────────────────────────────────────
print("\nRESUMEN:")
for conf in ["SEGURO", "MUY PROBABLE", "PROBABLE", "POSIBLE", "POCO PROBABLE"]:
    sub = df[df["confidence"] == conf]
    total_esc = sub["vox_seats_26"].sum()
    provs = ", ".join(sub["provincia"].tolist())
    print(f"  {CONF_SYMBOL[conf]}  {conf:<13}  "
          f"{len(sub):>2} provincias  {total_esc:>2} esc.  →  {provs}")
