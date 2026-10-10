import pandas as pd
from pathlib import Path

df = pd.read_csv(Path(__file__).parent / "data" / "vox_threshold_2026.csv")
CONF_ORDER = ["MUY PROBABLE", "PROBABLE", "POSIBLE", "POCO PROBABLE"]
df["conf_order"] = df["confidence"].map({c: i for i, c in enumerate(CONF_ORDER)})
df = df.sort_values(["conf_order", "gap_pp"]).reset_index(drop=True)

CONF_LABEL = {
    "MUY PROBABLE":  "MUY PROB ●●●●○",
    "PROBABLE":      "PROBABLE ●●●○○",
    "POSIBLE":       "POSIBLE  ●●○○○",
    "POCO PROBABLE": "POCO     ●○○○○",
}

hdr = (f"{'PROVINCIA':<26} {'ESC':>3}  "
       f"{'19N%':>5}  {'23J%':>5}  {'26est%':>6}  "
       f"{'UMBRAL':>6}  {'FALTA':>7}  "
       f"{'esc23':>5}→{'esc26':<5}  "
       f"CONFIANZA")
print(hdr)
print("─" * len(hdr))

prev_conf = None
for _, r in df.iterrows():
    if r["confidence"] != prev_conf:
        if prev_conf is not None:
            print()
        prev_conf = r["confidence"]

    s23, s26 = int(r["vox_seats_23"]), int(r["vox_seats_26"])
    esc_str = f"{s23}→{s26}" if s23 != s26 else f" ={s26}"
    gap_str = f"{r['gap_pp']:+.1f}pp"

    print(
        f"{r['provincia']:<26} {r['escanos']:>3}  "
        f"{r['vox_pct_19']:>5.1f}  {r['vox_pct_23']:>5.1f}  {r['vox_pct_26']:>6.1f}  "
        f"{r['umbral_pct']:>6.1f}  {gap_str:>7}  "
        f"{esc_str:>10}  "
        f"{CONF_LABEL[r['confidence']]}"
    )

print()
print("COLUMNAS:")
print("  19N% / 23J% = VOX en nov.2019 y jul.2023 (reales)")
print("  26est%      = estimación 2026 (swing uniforme sobre 23J)")
print("  UMBRAL      = % mínimo D'Hondt para ganar el SIGUIENTE escaño")
print("  FALTA       = gap que VOX debe cerrar para cruzar el umbral")
print("  esc23→esc26 = escaños reales 2023 → estimados 2026 (swing base)")
