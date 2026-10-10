import sys; sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES

df_meta23, df_votos23 = parse_conv('202307')

for prov_name in ['Ceuta', 'Melilla']:
    prov_row = df_meta23[df_meta23['nombre_provincia'] == prov_name].iloc[0]
    cod = prov_row['codigo_provincia']
    pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
    def v23(p): return pv23.get(p, 0)
    v26 = {
        'PP':      v23('PP')    * scale['PP'],
        'PSOE':    v23('PSOE')  * scale['PSOE'],
        'VOX':     v23('VOX')   * scale['VOX'],
        'SUMAR':   v23('SUMAR') * scale['SUMAR'],
        'PODEMOS': v23('SUMAR') * podemos_f,
        'SALF':    v23('PP')    * salf_f,
    }
    for p, votes in pv23.items():
        if p not in NATIONAL_PARTIES:
            v26[p] = votes * scale['OTROS']
    v26 = {p: vv for p, vv in v26.items() if vv > 0}
    total = sum(v26.values())
    sorted_v = sorted(v26.items(), key=lambda x: x[1], reverse=True)
    print(f'=== {prov_name} (1 escano) ===')
    for p, vv in sorted_v[:6]:
        marker = ' <-- VOX' if p == 'VOX' else ''
        print(f'  {p:<12} {vv/total*100:>5.1f}%  ({int(vv)} votos est.){marker}')
    vox_pct = v26.get('VOX', 0) / total * 100
    leader, leader_v = sorted_v[0] if sorted_v[0][0] != 'VOX' else sorted_v[1]
    gap = leader_v / total * 100 - vox_pct
    print(f'  Lider: {leader} ({leader_v/total*100:.1f}%) | VOX: {vox_pct:.1f}% | Gap: {gap:+.1f}pp')
    esc, _, _ = dhondt(v26, 1)
    ganador = list(esc.keys())[0]
    print(f'  Ganador estimado: {ganador}')
    print()
