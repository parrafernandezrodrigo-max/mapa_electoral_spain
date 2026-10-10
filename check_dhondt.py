import sys; sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES

df_meta23, df_votos23 = parse_conv('202307')

for prov_name in ['Sevilla', 'Burgos', 'Cuenca', 'Guadalajara', 'León', 'Salamanca']:
    prov_row = df_meta23[df_meta23['nombre_provincia'] == prov_name].iloc[0]
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
    vox_pct = v26.get('VOX', 0) / total * 100
    top = sorted(v26.items(), key=lambda x: -x[1])[:5]
    top_str = '  '.join(f"{p}:{vv/total*100:.1f}%({esc.get(p,0)})" for p, vv in top)
    print(f"{prov_name} ({seats} esc): {top_str}")
    print(f"  VOX: {vox_pct:.1f}% -> {esc.get('VOX',0)} esc | coef ultimo esc: {last_q/total*100:.2f}% [{last_p}]")
    print()
