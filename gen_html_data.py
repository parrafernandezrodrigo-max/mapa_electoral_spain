"""
Genera el bloque de datos JS para vox_tabla.html con la columna de fragilidad.
Para cada provincia calcula si el escaño que el swing model da a VOX
lo gana con su propio primer divisor (VOX/1 = último coeficiente ganador)
→ frágil: cualquier -1pp lo pierde.
"""
import sys; sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES
import pandas as pd
from pathlib import Path

df_meta23, df_votos23 = parse_conv('202307')
df = pd.read_csv(Path(__file__).parent / 'data' / 'vox_threshold_2026.csv')
CONF_ORDER = ["MUY PROBABLE","PROBABLE","POSIBLE","POCO PROBABLE"]
df["conf_order"] = df["confidence"].map({c:i for i,c in enumerate(CONF_ORDER)})
df = df.sort_values(["conf_order","gap_pp"]).reset_index(drop=True)

rows = []
for _, r in df.iterrows():
    prov_rows = df_meta23[df_meta23['nombre_provincia'] == r['provincia']]
    if prov_rows.empty:
        rows.append(None); continue
    prov_row = prov_rows.iloc[0]
    cod   = prov_row['codigo_provincia']
    seats = int(prov_row['escanos_asignados'])
    pv23  = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
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

    # Fragilidad: el escaño de VOX es frágil si el último coeficiente ganador
    # ES el primer divisor de VOX (VOX/1), o si la diferencia entre
    # VOX/vox_seats y el siguiente competidor es < 1pp del total
    fragile = "none"
    if vox_seats > 0:
        vox_last_q = vox_votes / vox_seats          # último coeficiente ganado por VOX
        # ¿Es VOX el partido del último escaño?
        if last_p == 'VOX':
            fragile = "filo"   # VOX gana el último escaño con su propio coeficiente
        else:
            # ¿Cuánto margen tiene VOX sobre el siguiente competidor no asignado?
            # Simulamos quitándole un escaño a VOX
            if vox_seats > 0:
                v26_minus = {**v26, 'VOX': vox_votes * 0.95}  # VOX -5%
                esc_minus, _, _ = dhondt(v26_minus, seats)
                if esc_minus.get('VOX', 0) < vox_seats:
                    fragile = "sensible"  # pierde escaño con -5% de sus votos

    rows.append({
        'provincia':  r['provincia'],
        'escanos':    seats,
        'vox19':      r['vox_pct_19'],
        'vox23':      r['vox_pct_23'],
        'vox26':      round(r['vox_pct_26'], 1),
        'umbral':     r['umbral_pct'],
        'gap':        r['gap_pp'],
        'esc23':      r['vox_seats_23'],
        'esc26':      r['vox_seats_26'],
        'conf':       r['confidence'],
        'fragile':    fragile,
        'last_p':     last_p,
        'last_q_pct': round(last_q / total * 100, 2) if total else 0,
    })

# Imprimir JS array
print("const data = [")
print("  // [provincia, esc, vox19, vox23, vox26, umbral, gap, esc23, esc26, conf, fragile, last_q_pct]")
prev_conf = None
for r in rows:
    if r is None: continue
    if r['conf'] != prev_conf:
        print(f"  // ── {r['conf']} ──")
        prev_conf = r['conf']
    row = [r['provincia'], r['escanos'], r['vox19'], r['vox23'], r['vox26'],
           r['umbral'], r['gap'], r['esc23'], r['esc26'], r['conf'], r['fragile'], r['last_q_pct']]
    print(f"  {row},")
print("];")
