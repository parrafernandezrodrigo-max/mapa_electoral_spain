"""
Estimación de escaños por provincia para las elecciones de noviembre 2026.
Fuente de intención de voto: encuesta 40dB El País/SER de octubre 2026.

Metodología: swing uniforme proporcional sobre los resultados reales de 2023.
  - Cada partido escala sus votos provinciales por (estimado_2026 / real_2023)
  - Podemos (nuevo separado de Sumar): se asigna proporcionalmente a los votos de Sumar 2023
  - SALF (nuevo): se asigna proporcionalmente a los votos de PP 2023
  - Partidos regionales (ERC, JxCAT, Bildu, PNV, BNG, CC...): escalan por el ratio "Otros"
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_conv
from dhondt import dhondt

# ──────────────────────────────────────────────────────────────────────────────
# 1. Estimaciones nacionales del PDF (encuesta 40dB octubre 2026, pág. 5)
#    Son porcentajes sobre votos válidos. La categoría "Otro+Blanco" (11.7%)
#    engloba regionales + blanco + nulo.
# ──────────────────────────────────────────────────────────────────────────────
POLL_2026 = {
    "PP":      31.9,
    "PSOE":    28.1,
    "VOX":     18.9,
    "SUMAR":    5.3,   # Sumar / Frente Amplio (sin Podemos)
    "PODEMOS":  2.3,   # separado de Sumar
    "SALF":     1.8,   # Se Acabó La Fiesta
    "OTROS":   11.7,   # regionales + blanco + nulo
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. Cargar resultados 2023 por provincia
# ──────────────────────────────────────────────────────────────────────────────
df_meta, df_votos = parse_conv("202307")

# Normalizar siglas al subconjunto de partidos nacionales + regionales
NATIONAL_PARTIES = {"PP", "PSOE", "VOX", "SUMAR"}
REGIONAL_PARTIES = {"ERC", "JxCAT - JUNTS", "EH Bildu", "EAJ-PNV", "B.N.G.", "CCa",
                    "CUP-PR", "U.P.N.", "NC-bc", "FO", "PACMA", "C's"}

# Totales nacionales 2023
nat_2023 = df_votos.groupby("siglas")["votos"].sum()
total_votos_23 = nat_2023.sum()
nat_pct_23 = nat_2023 / total_votos_23 * 100

# Share "Otros" 2023 = todo lo que no es PP/PSOE/VOX/SUMAR
others_23 = 100 - sum(nat_pct_23.get(p, 0) for p in NATIONAL_PARTIES)
print(f"Partidos nacionales 2023: PP={nat_pct_23.get('PP',0):.2f}%  "
      f"PSOE={nat_pct_23.get('PSOE',0):.2f}%  "
      f"VOX={nat_pct_23.get('VOX',0):.2f}%  "
      f"SUMAR={nat_pct_23.get('SUMAR',0):.2f}%")
print(f"Otros 2023: {others_23:.2f}%  (incluye regionales+blanco+nulo)")

# Factores de escala para partidos ya existentes en 2023
# Sumar 2023 se divide en: Sumar 2026 (5.3%) + Podemos 2026 (2.3%) = 7.6%
sumar_23 = nat_pct_23.get("SUMAR", 0)
scale = {
    "PP":    POLL_2026["PP"]   / nat_pct_23.get("PP",   1),
    "PSOE":  POLL_2026["PSOE"] / nat_pct_23.get("PSOE", 1),
    "VOX":   POLL_2026["VOX"]  / nat_pct_23.get("VOX",  1),
    "SUMAR": POLL_2026["SUMAR"] / sumar_23,       # fracción que queda como Sumar
    # Podemos y SALF no existían en 2023 → se calculan aparte
    "OTROS": POLL_2026["OTROS"] / others_23,
}
# Fracción de los votos de Sumar 2023 que se convierte en Podemos 2026
podemos_from_sumar = POLL_2026["PODEMOS"] / sumar_23
# SALF se toma de PP (lo más habitual en swings para nuevos partidos de derecha populista)
salf_from_pp_pct   = POLL_2026["SALF"]    / nat_pct_23.get("PP", 1)

print(f"\nFactores de escala: PP={scale['PP']:.3f}  PSOE={scale['PSOE']:.3f}  "
      f"VOX={scale['VOX']:.3f}  SUMAR={scale['SUMAR']:.3f}")
print(f"Podemos (de votos Sumar): factor={podemos_from_sumar:.3f}")
print(f"SALF (de votos PP): factor={salf_from_pp_pct:.3f}")

# ──────────────────────────────────────────────────────────────────────────────
# 3. Aplicar swing por provincia
# ──────────────────────────────────────────────────────────────────────────────
provinces = df_meta.groupby(["codigo_provincia", "nombre_provincia"]).agg(
    escanos=("escanos_asignados", "first"),
    votos_candidaturas=("votos_candidaturas", "first"),
).reset_index()

results = []

for _, prov in provinces.iterrows():
    cod  = prov["codigo_provincia"]
    name = prov["nombre_provincia"]
    seats = int(prov["escanos"])
    total_v = int(prov["votos_candidaturas"])

    # Votos 2023 por partido en esta provincia
    prov_votos = (
        df_votos[df_votos["codigo_provincia"] == cod]
        .set_index("siglas")["votos"]
        .to_dict()
    )

    def v23(p):
        return prov_votos.get(p, 0)

    # Votos estimados 2026
    votes_2026 = {}
    votes_2026["PP"]      = v23("PP")   * scale["PP"]
    votes_2026["PSOE"]    = v23("PSOE") * scale["PSOE"]
    votes_2026["VOX"]     = v23("VOX")  * scale["VOX"]
    votes_2026["SUMAR"]   = v23("SUMAR") * scale["SUMAR"]
    votes_2026["PODEMOS"] = v23("SUMAR") * podemos_from_sumar
    votes_2026["SALF"]    = v23("PP")   * salf_from_pp_pct

    # Regionales: escalan con factor "Otros"
    for party, votes in prov_votos.items():
        if party not in NATIONAL_PARTIES:
            votes_2026[party] = votes * scale["OTROS"]

    # Eliminar partidos con 0 votos
    votes_2026 = {p: v for p, v in votes_2026.items() if v > 0}

    # D'Hondt
    escanos_2026, _, _ = dhondt(votes_2026, seats)

    # D'Hondt 2023 (verificación)
    votes_2023 = {p: v for p, v in prov_votos.items() if v > 0}
    escanos_2023, _, _ = dhondt(votes_2023, seats)

    results.append({
        "codigo": cod,
        "provincia": name,
        "escanos": seats,
        "PP_26":      escanos_2026.get("PP",   0),
        "PSOE_26":    escanos_2026.get("PSOE", 0),
        "VOX_26":     escanos_2026.get("VOX",  0),
        "SUMAR_26":   escanos_2026.get("SUMAR",0),
        "PODEMOS_26": escanos_2026.get("PODEMOS",0),
        "SALF_26":    escanos_2026.get("SALF", 0),
        "OTROS_26":   sum(v for p, v in escanos_2026.items()
                         if p not in {"PP","PSOE","VOX","SUMAR","PODEMOS","SALF"}),
        "PP_23":      escanos_2023.get("PP",   0),
        "PSOE_23":    escanos_2023.get("PSOE", 0),
        "VOX_23":     escanos_2023.get("VOX",  0),
        "SUMAR_23":   escanos_2023.get("SUMAR",0),
        "OTROS_23":   sum(v for p, v in escanos_2023.items()
                         if p not in {"PP","PSOE","VOX","SUMAR"}),
    })

df = pd.DataFrame(results).sort_values("provincia")

# ──────────────────────────────────────────────────────────────────────────────
# 4. Resumen nacional
# ──────────────────────────────────────────────────────────────────────────────
def nat(col):
    return df[col].sum()

print("\n" + "="*60)
print("ESTIMACIÓN ESCAÑOS NACIONALES — NOVIEMBRE 2026 (swing uniforme)")
print("="*60)
print(f"PP:      {nat('PP_26'):3.0f}   (2023: {nat('PP_23'):.0f})")
print(f"PSOE:    {nat('PSOE_26'):3.0f}   (2023: {nat('PSOE_23'):.0f})")
print(f"VOX:     {nat('VOX_26'):3.0f}   (2023: {nat('VOX_23'):.0f})")
print(f"SUMAR:   {nat('SUMAR_26'):3.0f}   (2023: {nat('SUMAR_23'):.0f})")
print(f"PODEMOS: {nat('PODEMOS_26'):3.0f}   (2023: 0 — nueva candidatura)")
print(f"SALF:    {nat('SALF_26'):3.0f}   (2023: 0 — nueva candidatura)")
print(f"OTROS:   {nat('OTROS_26'):3.0f}   (2023: {nat('OTROS_23'):.0f})")
total_26 = sum(nat(c) for c in ["PP_26","PSOE_26","VOX_26","SUMAR_26","PODEMOS_26","SALF_26","OTROS_26"])
print(f"TOTAL:   {total_26:.0f} (deben ser 350)")

print("\n" + "─"*60)
print("COMPARACIÓN CON EL PDF (pág. 8, rango estimado):")
print("  PP:   132  (123–140)")
print("  PSOE: 112  (105–117)")
print("  VOX:   66  (63–74)")
print("  SUMAR:  5  (5–7)")
print("  PODEMOS: 2  (2)")
print("  OTROS:  33  (32–34)")
print("─"*60)

# ──────────────────────────────────────────────────────────────────────────────
# 5. Tabla por provincia
# ──────────────────────────────────────────────────────────────────────────────
display_cols = ["provincia","escanos","PP_26","PSOE_26","VOX_26","SUMAR_26","PODEMOS_26","SALF_26","OTROS_26"]
print("\nESCAÑOS POR PROVINCIA (estimación 2026):")
print(df[display_cols].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# 6. Cambios respecto a 2023
# ──────────────────────────────────────────────────────────────────────────────
df["PP_delta"]   = df["PP_26"]   - df["PP_23"]
df["PSOE_delta"] = df["PSOE_26"] - df["PSOE_23"]
df["VOX_delta"]  = df["VOX_26"]  - df["VOX_23"]
df["SUMAR_delta"]= df["SUMAR_26"]- df["SUMAR_23"]

print("\nMÁXIMOS CAMBIOS RESPECTO A 2023:")
print("\nProvincias donde PP gana escaños:")
print(df[df["PP_delta"]>0][["provincia","escanos","PP_23","PP_26","PP_delta"]].to_string(index=False))
print("\nProvincias donde PSOE pierde escaños:")
print(df[df["PSOE_delta"]<0][["provincia","escanos","PSOE_23","PSOE_26","PSOE_delta"]].to_string(index=False))
print("\nProvincias donde VOX gana escaños:")
print(df[df["VOX_delta"]>0][["provincia","escanos","VOX_23","VOX_26","VOX_delta"]].to_string(index=False))

# Guardar CSV
out = Path(__file__).parent / "data" / "estimacion_2026.csv"
df.to_csv(out, index=False)
print(f"\nCSV guardado en: {out}")
