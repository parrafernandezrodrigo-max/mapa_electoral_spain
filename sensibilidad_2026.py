"""
Análisis de sensibilidad de la estimación de escaños 2026.
Pregunta: ¿cuántos escaños pueden cambiar si el swing real de VOX (el partido
con mayor incertidumbre) varía ±5 pp respecto al estimado?
También: clasifica provincias por su tamaño y nivel de certeza D'Hondt.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_conv
from dhondt import dhondt

# ── Parámetros base ──────────────────────────────────────────────────────────
POLL_2026 = {"PP": 31.9, "PSOE": 28.1, "VOX": 18.9, "SUMAR": 5.3,
             "PODEMOS": 2.3, "SALF": 1.8, "OTROS": 11.7}

NATIONAL_PARTIES = {"PP", "PSOE", "VOX", "SUMAR"}

df_meta, df_votos = parse_conv("202307")
nat_2023   = df_votos.groupby("siglas")["votos"].sum()
total_23   = nat_2023.sum()
nat_pct_23 = nat_2023 / total_23 * 100
others_23  = 100 - sum(nat_pct_23.get(p, 0) for p in NATIONAL_PARTIES)
sumar_23   = nat_pct_23.get("SUMAR", 0)

scale_base = {
    "PP":    POLL_2026["PP"]    / nat_pct_23.get("PP",   1),
    "PSOE":  POLL_2026["PSOE"]  / nat_pct_23.get("PSOE", 1),
    "VOX":   POLL_2026["VOX"]   / nat_pct_23.get("VOX",  1),
    "SUMAR": POLL_2026["SUMAR"] / sumar_23,
    "OTROS": POLL_2026["OTROS"] / others_23,
}
podemos_factor = POLL_2026["PODEMOS"] / sumar_23
salf_factor    = POLL_2026["SALF"]    / nat_pct_23.get("PP", 1)

provinces = df_meta.groupby(["codigo_provincia", "nombre_provincia"]).agg(
    escanos=("escanos_asignados", "first"),
    votos_candidaturas=("votos_candidaturas", "first"),
).reset_index()


def estimate_seats(vox_delta_pp=0.0):
    """
    Corre D'Hondt para todas las provincias con VOX escalado por un delta adicional.
    vox_delta_pp: puntos porcentuales que se suman/restan al % estimado de VOX.
    El ajuste se hace proporcionalmente tomando/dando votos a PP y PSOE (50/50).
    """
    totals = {"PP": 0, "PSOE": 0, "VOX": 0, "SUMAR": 0,
              "PODEMOS": 0, "SALF": 0, "OTROS": 0}
    rows = []

    for _, prov in provinces.iterrows():
        cod   = prov["codigo_provincia"]
        name  = prov["nombre_provincia"]
        seats = int(prov["escanos"])

        pv = (df_votos[df_votos["codigo_provincia"] == cod]
              .set_index("siglas")["votos"].to_dict())

        def v23(p): return pv.get(p, 0)

        total_prov = sum(pv.values())

        v26 = {
            "PP":      v23("PP")    * scale_base["PP"],
            "PSOE":    v23("PSOE")  * scale_base["PSOE"],
            "VOX":     v23("VOX")   * scale_base["VOX"],
            "SUMAR":   v23("SUMAR") * scale_base["SUMAR"],
            "PODEMOS": v23("SUMAR") * podemos_factor,
            "SALF":    v23("PP")    * salf_factor,
        }
        for party, votes in pv.items():
            if party not in NATIONAL_PARTIES:
                v26[party] = votes * scale_base["OTROS"]

        # Aplicar delta VOX: tomar votos de PP y PSOE a partes iguales
        if vox_delta_pp != 0 and total_prov > 0:
            delta_votos = total_prov * (vox_delta_pp / 100)
            v26["VOX"]  += delta_votos
            v26["PP"]   -= delta_votos * 0.5
            v26["PSOE"] -= delta_votos * 0.5
            # evitar negativos
            v26["VOX"]  = max(v26["VOX"],  0)
            v26["PP"]   = max(v26["PP"],   0)
            v26["PSOE"] = max(v26["PSOE"], 0)

        v26_clean = {p: v for p, v in v26.items() if v > 0}
        esc, _, _ = dhondt(v26_clean, seats)

        rows.append({
            "provincia": name,
            "escanos": seats,
            "PP":      esc.get("PP",0), "PSOE":    esc.get("PSOE",0),
            "VOX":     esc.get("VOX",0),"SUMAR":   esc.get("SUMAR",0),
            "PODEMOS": esc.get("PODEMOS",0), "SALF": esc.get("SALF",0),
            "OTROS":   sum(v for p,v in esc.items()
                           if p not in {"PP","PSOE","VOX","SUMAR","PODEMOS","SALF"}),
        })
        for p in ["PP","PSOE","VOX","SUMAR","PODEMOS","SALF","OTROS"]:
            totals[p] += esc.get(p,0) if p != "OTROS" else rows[-1]["OTROS"]

    return pd.DataFrame(rows), totals


# ── Escenario base + variaciones VOX ────────────────────────────────────────
deltas = [-10, -7, -5, -3, 0, +3, +5, +7, +10]
scenarios = {}
for d in deltas:
    _, t = estimate_seats(d)
    scenarios[d] = t

print("SENSIBILIDAD DE ESCAÑOS AL SWING DE VOX (± puntos porcentuales)")
print("Base: VOX 18.9% nacional. Ajuste tomado a PP/PSOE a partes iguales.")
print()
hdr = f"{'Δ VOX':>8}  {'PP':>5} {'PSOE':>5} {'VOX':>5} {'SUMAR':>6} {'POD':>5} {'OTROS':>6}  {'PP+VOX':>7} {'PSE+SUM+POD':>12}"
print(hdr)
print("-" * len(hdr))
for d in deltas:
    t = scenarios[d]
    pp_v   = t['PP']
    pse    = t['PSOE']
    vox    = t['VOX']
    sum_   = t['SUMAR']
    pod    = t['PODEMOS']
    otros  = t['OTROS']
    marca  = " ← BASE" if d == 0 else ""
    print(f"  {d:>+5} pp  {pp_v:>5} {pse:>5} {vox:>5} {sum_:>6} {pod:>5} {otros:>6}  "
          f"{pp_v+vox:>7} {pse+sum_+pod:>12}{marca}")

# ── Cuántos escaños son "en juego" (cambian entre escenario −5 y +5) ─────────
df_base, _ = estimate_seats(0)
df_m5,   _ = estimate_seats(-5)
df_p5,   _ = estimate_seats(+5)

df_cmp = df_base.copy()
for col in ["PP","PSOE","VOX","SUMAR","PODEMOS","SALF","OTROS"]:
    df_cmp[f"{col}_m5"] = df_m5[col]
    df_cmp[f"{col}_p5"] = df_p5[col]

# Provincias donde algún partido cambia de escaño entre −5 y +5
changes = []
for _, r in df_cmp.iterrows():
    changed_parties = []
    for p in ["PP","PSOE","VOX","SUMAR","PODEMOS","SALF","OTROS"]:
        lo = r[f"{p}_m5"]
        hi = r[f"{p}_p5"]
        if lo != hi:
            changed_parties.append(f"{p}: {lo}→{hi}")
    if changed_parties:
        changes.append({
            "provincia": r["provincia"],
            "escanos":   r["escanos"],
            "base":      f"PP={r['PP']} PSE={r['PSOE']} VOX={r['VOX']} SUM={r['SUMAR']}",
            "cambios":   ", ".join(changed_parties),
        })

print(f"\n\nPROVINCIAS CON ESCAÑOS EN JUEGO si VOX varía ±5 pp (n={len(changes)} de 52):")
print(f"{'PROVINCIA':<26} {'ESC':>4}  {'BASE':>28}  {'CAMBIO (−5pp → +5pp)':>40}")
print("-" * 105)
for c in sorted(changes, key=lambda x: -x["escanos"]):
    print(f"{c['provincia']:<26} {c['escanos']:>4}  {c['base']:>28}  {c['cambios']}")

contested_seats = sum(r["escanos"] for r in changes)
print(f"\nTotal escaños en provincias con resultado sensible: {contested_seats} de 350")
print(f"Número de provincias sensibles: {len(changes)} de 52")

# ── Clasificación por tamaño y certeza ───────────────────────────────────────
print("\n\nCLASIFICACIÓN DE PROVINCIAS POR CERTEZA DE LA ESTIMACIÓN:")
print(f"{'PROVINCIA':<26} {'ESC':>4}  {'Certeza':>10}  {'Razón'}")
print("-" * 75)
for _, r in df_base.sort_values("escanos", ascending=False).iterrows():
    name = r["provincia"]
    seats = r["escanos"]
    changed = any(c["provincia"] == name for c in changes)
    if seats >= 16:
        cert = "ALTA"
        reason = "circunscripción grande, swing diluido"
    elif seats >= 8:
        cert = "MEDIA" if changed else "MEDIA-ALTA"
        reason = "sensible a swings de ~5pp" if changed else "relativamente estable"
    elif seats >= 5:
        cert = "BAJA" if changed else "MEDIA"
        reason = "cada escaño cuelga de ~5pp" if changed else "reparto estable en este rango"
    else:
        cert = "MUY BAJA"
        reason = f"≤4 escaños: umbral real ~20-25pp, muy sensible"
    print(f"{name:<26} {seats:>4}  {cert:>10}  {reason}")
