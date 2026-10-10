"""
tier_restructure.py
Recalcula el análisis con correcciones de cupos 2026:
  - Cádiz: 9 → 8 escaños
  - Madrid: 37 → 38 escaños
  - Ceuta: 1 escaño (pluralidad pura — necesita ser el más votado, no superar umbral)

Y muestra la re-estructura parlamentaria por escenario.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from vox_threshold_analysis import *   # reutiliza la lógica, solo cambiamos cupos

# ── Correcciones de cupos para 2026 ──────────────────────────────────────────
SEAT_OVERRIDE_2026 = {
    "Cádiz": 8,    # baja 1 respecto a 2023
    "Madrid": 38,  # sube 1 respecto a 2023
}

print("=" * 72)
print("CORRECCIONES DE CUPOS 2026")
print("  Cádiz: 9 → 8 escaños  |  Madrid: 37 → 38 escaños")
print("  Ceuta: 1 escaño → pluralidad (VOX necesita ser el MÁS VOTADO)")
print("=" * 72)

# Recargamos el CSV base y mostramos qué cambia
df = pd.read_csv(Path(__file__).parent / "data" / "vox_threshold_2026.csv")

print("\n--- ANTES (cupos 2023) ---")
for p in ["Cádiz", "Madrid", "Ceuta"]:
    r = df[df["provincia"] == p].iloc[0]
    print(f"  {p:<8} {r['escanos']}esc  VOX_26={r['vox_pct_26']:.1f}%  "
          f"umbral={r['umbral_pct']:.1f}%  gap={r['gap_pp']:+.1f}pp  → {r['confidence']}")

# ── Re-calcular esas tres provincias ────────────────────────────────────────
from parser import parse_conv
from dhondt import dhondt

df_meta23, df_votos23 = parse_conv("202307")
df_meta19, df_votos19 = parse_conv("201911")

nat23    = df_votos23.groupby("siglas")["votos"].sum()
total23  = nat23.sum()
nat_pct  = nat23 / total23 * 100
others23 = 100 - sum(nat_pct.get(p, 0) for p in NATIONAL_PARTIES)
sumar23  = nat_pct.get("SUMAR", 0)

print("\n--- DESPUÉS (cupos 2026 actualizados) ---")
for prov_name, new_seats in {**SEAT_OVERRIDE_2026, "Ceuta": 1}.items():
    prov_row = df_meta23[df_meta23["nombre_provincia"] == prov_name].iloc[0]
    cod = prov_row["codigo_provincia"]
    censo = int(prov_row["censo_total"])
    total_v23 = int(prov_row["votos_candidaturas"])
    abstention23 = max(censo - total_v23, 0)

    pv23 = (df_votos23[df_votos23["codigo_provincia"] == cod]
            .set_index("siglas")["votos"].to_dict())

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
    v26 = {p: vv for p, vv in v26.items() if vv > 0}

    total_v26 = sum(v26.values())
    vox_est_26 = v26.get("VOX", 0)
    vox_pct_26 = vox_est_26 / total_v26 * 100

    esc26, _, _ = dhondt(v26, new_seats)
    vox_seats_26 = esc26.get("VOX", 0)

    if prov_name == "Ceuta":
        # 1 escaño: el partido más votado se lo lleva, umbral = votos del líder
        sorted_v = sorted(v26.items(), key=lambda x: x[1], reverse=True)
        leader_party, leader_votes = sorted_v[0]
        if leader_party == "VOX":
            leader_party, leader_votes = sorted_v[1]
        threshold_pct = leader_votes / total_v26 * 100
        gap_pct = threshold_pct - vox_pct_26
        note = f"necesita superar a {leader_party} ({threshold_pct:.1f}%)"
    else:
        threshold_votes = next_seat_threshold(v26, esc26, new_seats)
        threshold_pct = threshold_votes / total_v26 * 100
        gap_pct = threshold_pct - vox_pct_26
        note = ""

    if gap_pct <= 0:
        conf = "SEGURO"
    elif gap_pct <= 1.5:
        conf = "MUY PROBABLE"
    elif gap_pct <= 3.0:
        conf = "PROBABLE"
    elif gap_pct <= 5.0:
        conf = "POSIBLE"
    else:
        conf = "POCO PROBABLE"

    print(f"  {prov_name:<8} {new_seats}esc  VOX_26={vox_pct_26:.1f}%  "
          f"umbral={threshold_pct:.1f}%  gap={gap_pct:+.1f}pp  → {conf}  {note}")

# ── Re-estructura parlamentaria ───────────────────────────────────────────────
print("\n" + "=" * 72)
print("RE-ESTRUCTURA PARLAMENTARIA (todos los partidos, swing base)")
print("=" * 72)

# La corrección de cupos (+1 Madrid, -1 Cádiz) no cambia el total nacional (350)
# pero redistribuye entre partidos en esas provincias
# Vamos a re-correr el swing en esas dos provincias con los nuevos cupos
# y comparar con la estimación base

PARTIES_2023 = {"PP": 137, "PSOE": 121, "VOX": 33, "SUMAR": 31, "OTROS": 28}
SWING_BASE   = {"PP": 131, "PSOE": 112, "VOX": 64, "SUMAR": 5,
                "PODEMOS": 2, "SALF": 1, "OTROS": 35}

# Corrección Madrid (+1 esc): con 38 en lugar de 37
# Corrección Cádiz (-1 esc): con 8 en lugar de 9
# Calculamos quién pierde/gana con cada cambio
changes = {}
for prov_name, (old_seats, new_seats) in {"Madrid": (37, 38), "Cádiz": (9, 8)}.items():
    prov_row = df_meta23[df_meta23["nombre_provincia"] == prov_name].iloc[0]
    cod = prov_row["codigo_provincia"]
    pv23 = (df_votos23[df_votos23["codigo_provincia"] == cod]
            .set_index("siglas")["votos"].to_dict())
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
    v26 = {p: vv for p, vv in v26.items() if vv > 0}

    esc_old, _, _ = dhondt(v26, old_seats)
    esc_new, _, _ = dhondt(v26, new_seats)

    diff = {p: esc_new.get(p, 0) - esc_old.get(p, 0) for p in set(esc_old) | set(esc_new)}
    diff = {p: v for p, v in diff.items() if v != 0}
    changes[prov_name] = (diff, esc_old, esc_new)
    print(f"\nCambio de cupo en {prov_name} ({old_seats}→{new_seats}):")
    for p, d in diff.items():
        print(f"    {p}: {esc_old.get(p,0)} → {esc_new.get(p,0)}  ({d:+})")

# ── Escenarios VOX totales ────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("ESCENARIOS DE ESCAÑOS — RE-ESTRUCTURA BLOCS")
print("=" * 72)

# Aplicar cambios de cupo al swing base
swing_corr = dict(SWING_BASE)
for prov_name, (diff, _, _) in changes.items():
    for p, d in diff.items():
        # mapear siglas al formato del swing
        key = p if p in swing_corr else "OTROS"
        swing_corr[key] = swing_corr.get(key, 0) + d

PP_c   = swing_corr["PP"]
PSOE_c = swing_corr["PSOE"]
VOX_c  = swing_corr["VOX"]
SALF_c = swing_corr.get("SALF", 1)
SUM_c  = swing_corr["SUMAR"] + swing_corr.get("PODEMOS", 0)
OTR_c  = swing_corr["OTROS"]

print(f"\n  Swing base con cupos corregidos:")
print(f"  PP={PP_c}  PSOE={PSOE_c}  VOX={VOX_c}  Sumar+Pod={SUM_c}  SALF={SALF_c}  Otros={OTR_c}")
print(f"  Total: {sum(swing_corr.values())}")

MAJ = 176
print(f"\n  Blocs (Mayoría absoluta = {MAJ}):")

scenarios = [
    ("BASE swing",               VOX_c),
    ("VOX + muy probable cross", VOX_c + 7),    # +1 por cada una de las 7 provincias MUY PROBABLE
    ("VOX + all probable cross", VOX_c + 12),   # +1 por las 12 provincias MUY+PROBABLE
    ("VOX + todos probable + mitad posible", VOX_c + 12 + 3),
    ("VOX conservador (base - POCO_PROBABLE)",   VOX_c - 20),  # si los poco_probable no se materializan
]

for label, vox_esc in scenarios:
    dcha = PP_c + vox_esc + SALF_c
    izq  = PSOE_c + SUM_c
    print(f"\n  [{label}]  VOX={vox_esc}")
    print(f"    Derecha (PP+VOX+SALF): {dcha}  vs M.A. {dcha-MAJ:+}")
    print(f"    Izquierda (PSOE+Sum):  {izq}")
    print(f"    Pendiente de bloque:   {350 - dcha - izq} (otros)")
