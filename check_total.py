import sys, json
sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from gen_all_parties import build_v26, SEATS_2026_OVERRIDE, NATIONAL_26, nat_summary
import pandas as pd

df_meta23, df_votos23 = parse_conv('202307')

for _, meta in df_meta23.iterrows():
    cod   = meta['codigo_provincia']
    name  = meta['nombre_provincia']
    seats = SEATS_2026_OVERRIDE.get(name, int(meta['escanos_asignados']))
    pv23  = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
    v26   = build_v26(pv23, izq=False)
    esc26, _, _ = dhondt(v26, seats)
    total = sum(esc26.values())
    if total != seats:
        print(f"DESCUADRE {name}: D'Hondt da {total} esc. pero debería dar {seats}")
    # Check per-party sum
    pp_  = esc26.get('PP',0)
    psoe = esc26.get('PSOE',0)
    vox  = esc26.get('VOX',0)
    sum_ = esc26.get('SUMAR',0)
    otros = sum(v for k,v in esc26.items() if k not in NATIONAL_26)
    if pp_+psoe+vox+sum_+otros != seats:
        print(f"  {name}: PP={pp_} PSOE={psoe} VOX={vox} SUMAR={sum_} OTROS={otros} suma={pp_+psoe+vox+sum_+otros} vs {seats}")
