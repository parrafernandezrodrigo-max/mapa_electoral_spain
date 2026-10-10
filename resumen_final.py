"""Resumen final consolidado con cupos 2026 corregidos."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES
import pandas as pd

df_meta23, df_votos23 = parse_conv("202307")
df = pd.read_csv(Path(__file__).parent / "data" / "vox_threshold_2026.csv")

# Cupos 2026 corregidos por el usuario
SEAT_OVERRIDE = {"Cádiz": 8, "Madrid": 38}

# Recalcular escaños nacionales con cupos corregidos
national = {}
for _, prov in df_meta23.groupby(["codigo_provincia","nombre_provincia"]).agg(
        escanos=("escanos_asignados","first"),
        votos_candidaturas=("votos_candidaturas","first")).reset_index().iterrows():
    cod  = prov["codigo_provincia"]
    name = prov["nombre_provincia"]
    seats = SEAT_OVERRIDE.get(name, int(prov["escanos"]))
    pv23 = df_votos23[df_votos23["codigo_provincia"]==cod].set_index("siglas")["votos"].to_dict()
    def v23(p): return pv23.get(p, 0)
    v26 = {
        "PP":      v23("PP")    * scale["PP"],
        "PSOE":    v23("PSOE")  * scale["PSOE"],
        "VOX":     v23("VOX")   * scale["VOX"],
        "SUMAR":   v23("SUMAR") * scale["SUMAR"],
        "PODEMOS": v23("SUMAR") * podemos_f,
        "SALF":    v23("PP")    * salf_f,
    }
    for p, votes in pv23.items():
        if p not in NATIONAL_PARTIES:
            v26[p] = votes * scale["OTROS"]
    v26 = {p: vv for p, vv in v26.items() if vv > 0}
    esc, _, _ = dhondt(v26, seats)
    for p, n in esc.items():
        national[p] = national.get(p, 0) + n

# Agrupar
PP   = national.get("PP", 0)
PSOE = national.get("PSOE", 0)
VOX  = national.get("VOX", 0)
SUM  = national.get("SUMAR", 0) + national.get("PODEMOS", 0)
SALF = national.get("SALF", 0)
OTROS = sum(v for p, v in national.items() if p not in {"PP","PSOE","VOX","SUMAR","PODEMOS","SALF"})
TOTAL = PP + PSOE + VOX + SUM + SALF + OTROS
MAJ   = 176

print("=" * 62)
print("ESTIMACIÓN FINAL — NOVIEMBRE 2026 (cupos 2026 corregidos)")
print("  Madrid: 38 esc  |  Cádiz: 8 esc")
print("=" * 62)
print()
print(f"  PP     {PP:>3}   (2023: 137  Δ{PP-137:+})")
print(f"  PSOE   {PSOE:>3}   (2023: 121  Δ{PSOE-121:+})")
print(f"  VOX    {VOX:>3}   (2023:  33  Δ{VOX-33:+})")
print(f"  Sumar+Pod {SUM:>2}   (2023:  31  Δ{SUM-31:+})")
print(f"  SALF   {SALF:>3}   (nuevo)")
print(f"  Otros  {OTROS:>3}   (2023:  28  Δ{OTROS-28:+})")
print(f"  TOTAL  {TOTAL:>3}")

# Blocs
DCHA = PP + VOX + SALF
IZQ  = PSOE + SUM
print()
print(f"  Bloque derecha  (PP+VOX+SALF):   {DCHA}  vs M.A. {DCHA-MAJ:+}")
print(f"  Bloque izquierda (PSOE+Sum+Pod): {IZQ}")
print(f"  Otros/nac/reg:                    {OTROS+0}")

# --- Desglose VOX por tier de confianza ---
print()
print("─" * 62)
print("DESGLOSE VOX POR NIVEL DE CONFIANZA (¿de dónde vienen los 65?)")
print("─" * 62)
for conf in ["MUY PROBABLE","PROBABLE","POSIBLE","POCO PROBABLE"]:
    sub = df[df["confidence"] == conf]
    s23 = int(sub["vox_seats_23"].sum())
    s26 = int(sub["vox_seats_26"].sum())
    # correccion Madrid (+1) está en MUY PROBABLE
    if conf == "MUY PROBABLE":
        s26 += 1   # Madrid gana el escaño extra con 38 cupos
    gain = s26 - s23
    pct  = s26 / VOX * 100
    print(f"  {conf:<14}  {len(sub):>2} prov  "
          f"2023={s23:>2}  swing26={s26:>2} ({pct:.0f}%)  ganancia={gain:+}")

print()
print("─" * 62)
print("ESCENARIOS PARA EL BLOQUE DE DERECHA")
print("─" * 62)
rows = [
    ("Conservador: VOX solo en prov. MUY PROBABLE + PROBABLE",
     9 + 1 + 6),   # muy prob (9+1 Madrid) + probable (6)
    ("Intermedio: base swing",
     VOX),
    ("Optimista: + crossings MUY PROBABLE+PROBABLE (+12 extra)",
     VOX + 12),
    ("Máximo: + crossings todos los tiers (+19)",
     VOX + 12 + 7),
]
print()
print(f"  {'Escenario':<50}  VOX   Dcha  vs176")
for label, vox_esc in rows:
    dcha = PP + vox_esc + SALF
    print(f"  {label:<50}   {vox_esc:>2}   {dcha:>3}  {dcha-MAJ:+}")
