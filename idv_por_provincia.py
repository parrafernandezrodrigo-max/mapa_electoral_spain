"""
Intención de voto directa (P3) ponderada por provincia, comparada con el swing model.
Incluye el N por provincia para evaluar la fiabilidad de los datos de encuesta.
"""
import pandas as pd
from pathlib import Path

df = pd.read_excel(
    r'C:\Users\rodrigo.parra\Downloads\Copia de 03_Datos_octubre_2026.xlsx',
    sheet_name='Sheet1'
)

party_map = {
    'PSOE (Partido Socialista Obrero Español)': 'PSOE',
    'PP (Partido Popular)':                     'PP',
    'Vox':                                      'VOX',
    'Sumar':                                    'SUMAR',
    'Podemos':                                  'PODEMOS',
    'Se acabó la fiesta':                       'SALF',
    'ERC (Esquerra Republicana de Catalunya)':  'ERC',
    'JxCAT - Junts per Catalunya':              'JxCAT',
    'EH Bildu':                                 'BILDU',
    'EAJ-PNV':                                  'PNV',
    'BNG':                                      'BNG',
    'Coalición Canaria':                        'CC',
}
EXCLUDE = {'No lo sé', 'No votaría', 'Votaría en blanco', 'Votaría nulo',
           'Prefiero no contestar', None}

df['partido'] = df['p3'].apply(lambda x: party_map.get(x, 'OTROS'))

# Incluimos TODOS (incluso OTROS) en el denominador para los porcentajes
# pero marcamos cuáles son válidos
df['es_partido'] = ~df['p3'].isin(EXCLUDE) & df['p3'].notna()

rows = []
for prov, grp in df.groupby('prov'):
    valid = grp[grp['es_partido']]
    total_w = valid['ponde'].sum()
    n = len(valid)
    n_total = len(grp)

    by_party = valid.groupby('partido')['ponde'].sum()
    pp    = by_party.get('PP',    0) / total_w * 100 if total_w else 0
    psoe  = by_party.get('PSOE',  0) / total_w * 100 if total_w else 0
    vox   = by_party.get('VOX',   0) / total_w * 100 if total_w else 0
    sumar = by_party.get('SUMAR', 0) / total_w * 100 if total_w else 0
    pod   = by_party.get('PODEMOS',0)/ total_w * 100 if total_w else 0
    salf  = by_party.get('SALF',  0) / total_w * 100 if total_w else 0
    otros = 100 - pp - psoe - vox - sumar - pod - salf

    rows.append({
        'provincia': prov, 'N_valido': n, 'N_total': n_total,
        'PP': round(pp,1), 'PSOE': round(psoe,1), 'VOX': round(vox,1),
        'SUMAR': round(sumar,1), 'PODEMOS': round(pod,1), 'SALF': round(salf,1),
        'OTROS': round(otros,1),
    })

df_prov = pd.DataFrame(rows).sort_values('provincia').reset_index(drop=True)

# ── Cargar swing model para comparar ─────────────────────────────────────────
swing_csv = Path(__file__).parent / 'data' / 'pct_provincias_2026.csv'
swing = pd.read_csv(swing_csv)[['provincia','PP_26','PSOE_26','VOX_26','SUMAR_26']]
swing = swing.rename(columns={'PP_26':'PP_sw','PSOE_26':'PSOE_sw',
                               'VOX_26':'VOX_sw','SUMAR_26':'SUMAR_sw'})

# Normalizar nombre provincia para merge (aproximación)
df_prov['prov_key'] = df_prov['provincia'].str.strip()
swing['prov_key']   = swing['provincia'].str.strip()
merged = df_prov.merge(swing, on='prov_key', how='left')
# After merge, 'provincia' from df_prov becomes 'provincia_x' if swing also has 'provincia'
if 'provincia_x' in merged.columns:
    merged = merged.rename(columns={'provincia_x': 'provincia'})
    merged = merged.drop(columns=['provincia_y'], errors='ignore')

# ── Imprimir ──────────────────────────────────────────────────────────────────
print("IDV DIRECTA (P3 ponderada) vs SWING MODEL — por provincia")
print("N_v = respondentes con voto válido en esa provincia (base para % IDV)")
print("Swing = estimación del modelo de swing uniforme sobre 2023")
print()
hdr = (f"{'PROVINCIA':<26} {'N_v':>4}  "
       f"{'PP idv':>6} {'PP sw':>6} {'ΔPP':>5}  "
       f"{'PSE idv':>7} {'PSE sw':>7} {'ΔPSE':>5}  "
       f"{'VOX idv':>7} {'VOX sw':>7} {'ΔVOX':>5}  "
       f"{'SUM idv':>7} {'SUM sw':>7} {'ΔSUM':>5}")
print(hdr)
print("-" * len(hdr))

for _, r in merged.iterrows():
    pp_d   = r['PP']    - r['PP_sw']   if pd.notna(r['PP_sw'])   else float('nan')
    pse_d  = r['PSOE']  - r['PSOE_sw'] if pd.notna(r['PSOE_sw']) else float('nan')
    vox_d  = r['VOX']   - r['VOX_sw']  if pd.notna(r['VOX_sw'])  else float('nan')
    sum_d  = r['SUMAR'] - r['SUMAR_sw']if pd.notna(r['SUMAR_sw'])else float('nan')

    def fmt(v):
        return f"{v:>+5.1f}" if pd.notna(v) else "  n/a"

    print(
        f"{r['provincia']:<26} {r['N_valido']:>4}  "
        f"{r['PP']:>6.1f} {r['PP_sw']:>6.1f} {fmt(pp_d)}  "
        f"{r['PSOE']:>7.1f} {r['PSOE_sw']:>7.1f} {fmt(pse_d)}  "
        f"{r['VOX']:>7.1f} {r['VOX_sw']:>7.1f} {fmt(vox_d)}  "
        f"{r['SUMAR']:>7.1f} {r['SUMAR_sw']:>7.1f} {fmt(sum_d)}"
    )

print()
print("AVISO: con N_v < 30 los porcentajes IDV tienen error muestral muy alto (>±18pp)")
print("       con N_v < 15 son básicamente anecdóticos.")

# Guardar CSV
out = Path(__file__).parent / 'data' / 'idv_vs_swing_por_provincia.csv'
merged.drop(columns=['prov_key','provincia_y'], errors='ignore').to_csv(out, index=False)
print(f"\nCSV guardado: {out}")
