import sys
sys.path.insert(0, '.')
import pandas as pd
from dhondt import dhondt

results = pd.read_parquet('data/processed/results_all.parquet')
r23 = results[results.conv_id == "202307"].copy()

SEAT_OVERRIDE = {"Madrid": 38, "Cádiz": 8}
REGIONAL = {"ERC", "JxCAT - JUNTS", "EH Bildu", "EAJ-PNV", "B.N.G.", "CCa", "U.P.N."}
ALL_PARTIES = ["PP","PSOE","VOX","SUMAR","PODEMOS","ERC","JxCAT - JUNTS",
               "EH Bildu","EAJ-PNV","B.N.G.","CCa","U.P.N."]

def run_vox(vox_pct, sumar_ratio=7.6/12.3, pod_share=2.3/7.6,
            swing_pp=31.9/33.1, swing_psoe=28.1/31.7, salf_pct=1.8/100):
    swing_vox = vox_pct / 12.4   # vs 23J VOX real
    nat = {p: 0 for p in ALL_PARTIES}
    prov_rows = []

    for (cod, prov), grp in r23.groupby(["codigo_provincia","nombre_provincia"]):
        seats   = SEAT_OVERRIDE.get(prov, int(grp["seats_total"].iloc[0]))
        vc_23   = int(grp["votos_candidaturas"].iloc[0])
        votes23 = dict(zip(grp["siglas"], grp["votos"]))

        st26 = votes23.get("SUMAR",0) * sumar_ratio
        votes26 = {
            "PP":      int(votes23.get("PP",0)   * swing_pp),
            "PSOE":    int(votes23.get("PSOE",0) * swing_psoe),
            "VOX":     int(votes23.get("VOX",0)  * swing_vox),
            "SUMAR":   int(st26 * (1-pod_share)),
            "PODEMOS": int(st26 * pod_share),
            "SALF":    int(vc_23 * salf_pct),
        }
        for p,v in votes23.items():
            if p in REGIONAL:
                votes26[p] = v
        votes26 = {p:v for p,v in votes26.items() if v>0}
        total_v = sum(votes26.values())
        valid   = {p:v for p,v in votes26.items() if v/total_v >= 0.03}
        esc, _, _ = dhondt(valid, seats)

        for p in ALL_PARTIES:
            nat[p] += esc.get(p,0)

        prov_rows.append({
            "prov": prov,
            "seats": seats,
            "vox_pct_prov": round(votes26.get("VOX",0)/total_v*100,1),
            "e_PP":  esc.get("PP",0),
            "e_PSOE":esc.get("PSOE",0),
            "e_VOX": esc.get("VOX",0),
            "e_SUM": esc.get("SUMAR",0)+esc.get("PODEMOS",0),
        })

    der  = nat["PP"] + nat["VOX"] + nat["U.P.N."]
    izq  = nat["PSOE"]+nat["SUMAR"]+nat["PODEMOS"]+nat["EH Bildu"]+nat["B.N.G."]
    return nat, der, izq, prov_rows

# ── Barrido Vox ──────────────────────────────────────────────
print("UMBRAL VOX (Sumar colapsado, PSOE 28.1%)")
print(f"{'Vox%':>7}  {'PP':>5}  {'PSOE':>5}  {'Vox':>5}  {'Sumar':>6}  {'DCHA':>6}  {'IZDA':>6}  {'Mayoría'}")
print("-"*68)
for vox_pct in [18.9, 17.0, 16.0, 15.5, 15.1, 14.5, 14.0, 13.5, 13.0, 12.4]:
    nat, der, izq, _ = run_vox(vox_pct)
    marker = ""
    if 175 <= der <= 182:
        marker = " ◄ objetivo"
    elif der < 176:
        marker = " ✗ sin mayoría"
    print(f"  {vox_pct:>5.1f}%  {nat['PP']:>5}  {nat['PSOE']:>5}  {nat['VOX']:>5}  "
          f"{nat['SUMAR']+nat['PODEMOS']:>6}  {der:>6}  {izq:>6}{marker}")

print()
print("UMBRAL VOX (Sumar mantiene 12%, PSOE 28.1%)")
print(f"{'Vox%':>7}  {'PP':>5}  {'PSOE':>5}  {'Vox':>5}  {'Sumar':>6}  {'DCHA':>6}  {'IZDA':>6}  {'Mayoría'}")
print("-"*68)
for vox_pct in [18.9, 17.0, 16.0, 15.1, 14.5, 14.0, 13.5, 13.0, 12.4]:
    nat, der, izq, _ = run_vox(vox_pct, sumar_ratio=0.975, pod_share=0.0)
    marker = ""
    if 175 <= der <= 182:
        marker = " ◄ objetivo"
    elif der < 176:
        marker = " ✗ sin mayoría"
    print(f"  {vox_pct:>5.1f}%  {nat['PP']:>5}  {nat['PSOE']:>5}  {nat['VOX']:>5}  "
          f"{nat['SUMAR']:>6}  {der:>6}  {izq:>6}{marker}")

# ── Detalle provincial en el escenario umbral (Vox ~15%) ─────
print()
print("DETALLE PROVINCIAL — Vox al 15% (Sumar colapsado)")
print("Provincias donde VOX pierde escaños vs escenario base (18.9%)")
print("-"*70)
_, _, _, rows_base = run_vox(18.9)
_, _, _, rows_15   = run_vox(15.1)

base_d = {r["prov"]: r for r in rows_base}
rows_15_d = {r["prov"]: r for r in rows_15}

changed = []
for prov, r15 in rows_15_d.items():
    rb = base_d[prov]
    dif_vox  = r15["e_VOX"]  - rb["e_VOX"]
    dif_pp   = r15["e_PP"]   - rb["e_PP"]
    dif_psoe = r15["e_PSOE"] - rb["e_PSOE"]
    dif_sum  = r15["e_SUM"]  - rb["e_SUM"]
    if dif_vox != 0:
        changed.append({
            "Provincia":  prov,
            "Esc_total":  rb["seats"],
            "Vox%_base":  rb["vox_pct_prov"],
            "Vox%_15":    r15["vox_pct_prov"],
            "Vox_base→15": f"{rb['e_VOX']}→{r15['e_VOX']} ({dif_vox:+d})",
            "PP_base→15":  f"{rb['e_PP']}→{r15['e_PP']} ({dif_pp:+d})",
            "PSOE_base→15":f"{rb['e_PSOE']}→{r15['e_PSOE']} ({dif_psoe:+d})",
            "Sum_base→15": f"{rb['e_SUM']}→{r15['e_SUM']} ({dif_sum:+d})",
        })

changed_df = pd.DataFrame(changed).sort_values("Esc_total", ascending=False)
print(changed_df.to_string(index=False))
