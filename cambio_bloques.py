import sys
sys.path.insert(0, '.')
import pandas as pd
from dhondt import dhondt

results = pd.read_parquet('data/processed/results_all.parquet')
r23 = results[results.conv_id == "202307"].copy()

SEAT_OVERRIDE = {"Madrid": 38, "Cádiz": 8}
REGIONAL = {"ERC", "JxCAT - JUNTS", "EH Bildu", "EAJ-PNV", "B.N.G.", "CCa", "U.P.N."}
ALL_P = ["PP","PSOE","VOX","SUMAR","PODEMOS","ERC","JxCAT - JUNTS",
         "EH Bildu","EAJ-PNV","B.N.G.","CCa","U.P.N."]
IZDA_P = {"PSOE","SUMAR","PODEMOS","EH Bildu","B.N.G."}
DCHA_P = {"PP","VOX","U.P.N."}

def run_scenario(sumar_ratio, pod_share,
                 swing_pp=31.9/33.1, swing_psoe=28.1/31.7,
                 swing_vox=18.9/12.4, salf_pct=1.8/100):
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
        for p, v in votes23.items():
            if p in REGIONAL:
                votes26[p] = v
        votes26 = {p:v for p,v in votes26.items() if v>0}
        total_v = sum(votes26.values())
        valid   = {p:v for p,v in votes26.items() if v/total_v >= 0.03}
        esc, _, _ = dhondt(valid, seats)
        prov_rows.append({"prov": prov, "cod": cod, "seats": seats,
                          **{f"e_{p}": esc.get(p,0) for p in ALL_P}})
    return pd.DataFrame(prov_rows)

# ── 2023 real ────────────────────────────────────────────────────────────
bloc23 = []
for (cod, prov), grp in r23.groupby(["codigo_provincia","nombre_provincia"]):
    seats = SEAT_OVERRIDE.get(prov, int(grp["seats_total"].iloc[0]))
    esc23 = dict(zip(grp["siglas"], grp["escanos_dhondt"]))
    bloc23.append({
        "prov": prov, "cod": cod, "seats": seats,
        "izda23": sum(esc23.get(p,0) for p in IZDA_P),
        "dcha23": sum(esc23.get(p,0) for p in DCHA_P),
        **{f"r23_{p}": esc23.get(p,0) for p in ALL_P}
    })
df23 = pd.DataFrame(bloc23)

# ── 2026 escenarios ──────────────────────────────────────────────────────
dfA = run_scenario(sumar_ratio=7.6/12.3, pod_share=2.3/7.6)   # A: Sumar colapsado
dfB = run_scenario(sumar_ratio=0.975,    pod_share=0.0)        # B: Sumar mantiene

def add_blocs(df_proj, suffix):
    df_proj[f"izda_{suffix}"] = df_proj[[f"e_{p}" for p in IZDA_P]].sum(axis=1)
    df_proj[f"dcha_{suffix}"] = df_proj[[f"e_{p}" for p in DCHA_P]].sum(axis=1)
    return df_proj

dfA = add_blocs(dfA, "A")
dfB = add_blocs(dfB, "B")

# Renombrar columnas de escaños para no colisionar al hacer merge
for p in ALL_P:
    dfA.rename(columns={f"e_{p}": f"A_{p}"}, inplace=True)
    dfB.rename(columns={f"e_{p}": f"B_{p}"}, inplace=True)

df = df23.merge(dfA[["prov"] + [c for c in dfA.columns if c not in ["prov","cod","seats"]]],
                on="prov")
df = df.merge(dfB[["prov"] + [c for c in dfB.columns if c not in ["prov","cod","seats"]]],
              on="prov")

df["dA_izda"] = df["izda_A"] - df["izda23"]
df["dA_dcha"] = df["dcha_A"] - df["dcha23"]
df["dB_izda"] = df["izda_B"] - df["izda23"]
df["dB_dcha"] = df["dcha_B"] - df["dcha23"]

# ── Mostrar provincias con cambio en al menos uno de los dos escenarios ──
changed = df[(df["dA_izda"] != 0) | (df["dB_izda"] != 0)].sort_values("seats", ascending=False)

def escano_str(r23, rA, rB):
    if rA == rB:
        return f"{r23}→{rA}"
    else:
        return f"{r23}→{rA}(A)/{rB}(B)"

for scen, label in [("A","SUMAR COLAPSADO (5.3%)"), ("B","SUMAR MANTIENE (12%)")]:
    print(f"\n{'='*85}")
    print(f" ESCENARIO {scen}: {label}")
    print(f"{'='*85}")
    print(f"  {'Provincia':<22} {'Esc':>4}  {'Izda23':>6}→{'Izda26':>6} {'Δ':>4}  |  "
          f"{'Dcha23':>6}→{'Dcha26':>6} {'Δ':>4}  |  PP   VOX   PSOE  Sum")
    print(f"  {'-'*83}")
    scen_changed = df[df[f"d{scen}_izda"] != 0].sort_values("seats", ascending=False)
    for _, r in scen_changed.iterrows():
        di = int(r[f"d{scen}_izda"]); dd = int(r[f"d{scen}_dcha"])
        pp_c  = f"{int(r['r23_PP'])}→{int(r[f'{scen}_PP'])} ({int(r[f'{scen}_PP']-r['r23_PP']):+d})"
        vox_c = f"{int(r['r23_VOX'])}→{int(r[f'{scen}_VOX'])} ({int(r[f'{scen}_VOX']-r['r23_VOX']):+d})"
        pso_c = f"{int(r['r23_PSOE'])}→{int(r[f'{scen}_PSOE'])} ({int(r[f'{scen}_PSOE']-r['r23_PSOE']):+d})"
        sum_23 = int(r["r23_SUMAR"]) + int(r["r23_PODEMOS"])
        sum_26 = int(r[f"{scen}_SUMAR"]) + int(r[f"{scen}_PODEMOS"])
        sum_c = f"{sum_23}→{sum_26} ({sum_26-sum_23:+d})"
        print(f"  {r['prov']:<22} {int(r['seats']):>4}  "
              f"{int(r['izda23']):>6}→{int(r[f'izda_{scen}']):>5} {di:>+4}  |  "
              f"{int(r['dcha23']):>6}→{int(r[f'dcha_{scen}']):>5} {dd:>+4}  |  "
              f"{pp_c:<10}  {vox_c:<12}  {pso_c:<13}  {sum_c}")
    di_tot = scen_changed[f"d{scen}_izda"].sum()
    dd_tot = scen_changed[f"d{scen}_dcha"].sum()
    nat_izda = df["izda23"].sum(); nat_izda26 = df[f"izda_{scen}"].sum()
    nat_dcha = df["dcha23"].sum(); nat_dcha26 = df[f"dcha_{scen}"].sum()
    print(f"  {'-'*83}")
    print(f"  NACIONAL: Izda {int(nat_izda)}→{int(nat_izda26)} ({int(nat_izda26-nat_izda):+d})  |  "
          f"Dcha {int(nat_dcha)}→{int(nat_dcha26)} ({int(nat_dcha26-nat_dcha):+d})  |  Mayoría absoluta: 176")
