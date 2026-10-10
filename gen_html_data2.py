import sys; sys.path.insert(0, '.')
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

lines = []
prev_conf = None
for _, r in df.iterrows():
    prov_rows = df_meta23[df_meta23['nombre_provincia'] == r['provincia']]
    if prov_rows.empty: continue
    prov_row = prov_rows.iloc[0]
    cod = prov_row['codigo_provincia']
    seats = int(prov_row['escanos_asignados'])
    pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
    def v23(p): return pv23.get(p, 0)
    v26 = {'PP': v23('PP')*scale['PP'], 'PSOE': v23('PSOE')*scale['PSOE'],
           'VOX': v23('VOX')*scale['VOX'], 'SUMAR': v23('SUMAR')*scale['SUMAR'],
           'PODEMOS': v23('SUMAR')*podemos_f, 'SALF': v23('PP')*salf_f}
    for p, votes in pv23.items():
        if p not in NATIONAL_PARTIES: v26[p] = votes * scale['OTROS']
    v26 = {p: vv for p, vv in v26.items() if vv > 0}
    total = sum(v26.values())
    esc, last_q, last_p = dhondt(v26, seats)
    vox_seats = esc.get('VOX', 0)
    vox_votes = v26.get('VOX', 0)
    fragile = 'none'
    if vox_seats > 0:
        if last_p == 'VOX':
            fragile = 'filo'
        else:
            v26_m = dict(v26)
            v26_m['VOX'] = vox_votes * 0.95
            esc_m, _, _ = dhondt(v26_m, seats)
            if esc_m.get('VOX', 0) < vox_seats:
                fragile = 'sensible'
    if r['confidence'] != prev_conf:
        lines.append(f'  // -- {r["confidence"]} --')
        prev_conf = r['confidence']
    lq = round(float(last_q) / total * 100, 2) if total else 0
    p = r['provincia']
    v19 = float(r['vox_pct_19'])
    v23x = float(r['vox_pct_23'])
    v26x = float(r['vox_pct_26'])
    umb  = float(r['umbral_pct'])
    gap  = float(r['gap_pp'])
    s23  = int(r['vox_seats_23'])
    s26  = int(r['vox_seats_26'])
    conf = r['confidence']
    lines.append(f'  ["{p}", {seats}, {v19}, {v23x}, {v26x}, {umb}, {gap}, {s23}, {s26}, "{conf}", "{fragile}", {lq}],')

out = Path('.') / 'data' / 'html_data_clean.js'
with open(out, 'w', encoding='utf-8') as f:
    f.write('const data = [\n  // [provincia, esc, vox19, vox23, vox26, umbral, gap, esc23, esc26, conf, fragile, last_q_pct]\n')
    for l in lines:
        f.write(l + '\n')
    f.write('];\n')
print(f'Escrito: {out}')
