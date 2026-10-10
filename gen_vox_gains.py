"""
Para cada provincia donde VOX gana escaños en el swing 2026,
muestra de qué partido(s) los saca.
Compara D'Hondt 2023 real vs D'Hondt 2026 swing.
"""
import sys, json
sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES
import pandas as pd
from pathlib import Path

df_meta23, df_votos23 = parse_conv('202307')
df = pd.read_csv(Path('.') / 'data' / 'vox_threshold_2026.csv')

CONF_ORDER = ['MUY PROBABLE','PROBABLE','POSIBLE','POCO PROBABLE']
df['conf_order'] = df['confidence'].map({c:i for i,c in enumerate(CONF_ORDER)})
df = df.sort_values(['conf_order','gap_pp']).reset_index(drop=True)

results = {}

for _, r in df.iterrows():
    prov_rows = df_meta23[df_meta23['nombre_provincia'] == r['provincia']]
    if prov_rows.empty:
        continue
    prov_row = prov_rows.iloc[0]
    cod = prov_row['codigo_provincia']
    seats = int(prov_row['escanos_asignados'])

    pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
    def v23(p): return pv23.get(p, 0)

    # D'Hondt 2023 real
    esc23, _, _ = dhondt(pv23, seats)

    # D'Hondt 2026 swing
    v26 = {
        'PP':     v23('PP')    * scale['PP'],
        'PSOE':   v23('PSOE')  * scale['PSOE'],
        'VOX':    v23('VOX')   * scale['VOX'],
        'SUMAR':  v23('SUMAR') * scale['SUMAR'],
        'PODEMOS':v23('SUMAR') * podemos_f,
        'SALF':   v23('PP')    * salf_f,
    }
    for p, votes in pv23.items():
        if p not in NATIONAL_PARTIES:
            v26[p] = votes * scale['OTROS']
    v26 = {p: vv for p, vv in v26.items() if vv > 0}
    esc26, _, _ = dhondt(v26, seats)

    # Diferencia de escaños
    all_parties = set(esc23.keys()) | set(esc26.keys())
    diff = {p: esc26.get(p, 0) - esc23.get(p, 0) for p in all_parties}

    vox_gain = diff.get('VOX', 0)

    # Atribuir los escaños de VOX solo hasta cubrir su ganancia,
    # tomando los mayores perdedores en orden descendente.
    all_losers = sorted(
        [(p, -d) for p, d in diff.items() if d < 0 and p != 'VOX'],
        key=lambda x: -x[1]
    )
    attributed = []
    remaining = vox_gain
    for party, lost in all_losers:
        if remaining <= 0:
            break
        take = min(lost, remaining)
        attributed.append((party, take))
        remaining -= take

    results[r['provincia']] = {
        'vox_gain': vox_gain,
        'losers': attributed,
        'esc23': esc23,
        'esc26': esc26,
    }

# Imprimir provincias donde VOX gana escaños
print(f"{'PROVINCIA':<30} {'GAIN':>4}  PIERDE(N)")
print("-" * 60)
for prov, d in results.items():
    if d['vox_gain'] > 0:
        losers_str = ', '.join(f"{p}({n})" for p, n in d['losers'])
        print(f"{prov:<30} +{d['vox_gain']:>2}     {losers_str}")

# Generar JSON para el HTML
gain_map = {}
for prov, d in results.items():
    if d['vox_gain'] > 0:
        gain_map[prov] = ', '.join(p for p, n in d['losers'])
    else:
        gain_map[prov] = ''

out = Path('.') / 'data' / 'vox_gains.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(gain_map, f, ensure_ascii=False, indent=2)
print(f"\nGuardado: {out}")
