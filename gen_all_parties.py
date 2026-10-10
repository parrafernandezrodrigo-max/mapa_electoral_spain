"""
gen_all_parties.py
Genera data/all_parties_data.js con análisis D'Hondt-umbral para:
  PP, PSOE, VOX, SUMAR, IZQ (SUMAR+PODEMOS como bloque único)
Metodología idéntica a vox_threshold_analysis.py.
"""
import sys, json
sys.path.insert(0, '.')
from parser import parse_conv
from dhondt import dhondt
from vox_threshold_analysis import scale, podemos_f, salf_f, NATIONAL_PARTIES, POLL_2026
import pandas as pd
from pathlib import Path

df_meta23, df_votos23 = parse_conv('202307')
df_meta19, df_votos19 = parse_conv('201911')

# ── Escala para el bloque izquierda (SUMAR+PODEMOS combinados = 7.6% en 2026) ──
nat23     = df_votos23.groupby('siglas')['votos'].sum()
total23   = nat23.sum()
nat_pct23 = nat23 / total23 * 100
sumar23   = nat_pct23.get('SUMAR', 0)
scale_izq = (POLL_2026['SUMAR'] + POLL_2026['PODEMOS']) / sumar23  # 7.6 / sumar%

# ── Siglas 2019 del bloque izquierda ──────────────────────────────────────────
LEFT_2019 = ['PODEMOS-IU', 'ECP-GUANYEM EL CANVI', 'PODEMOS-EU', 'MÁS PAÍS-EQUO', 'MÁS PAÍS']

# Corrección de escaños 2026 vs 2023 (redistribución censal)
SEATS_2026_OVERRIDE = {
    'Madrid': 38,
    'Cádiz':  8,
}

CONF_ORDER = ['SEGURO', 'MUY PROBABLE', 'PROBABLE', 'POSIBLE', 'POCO PROBABLE']

def conf_tier(gap):
    if gap <= 0:   return 'SEGURO'
    if gap <= 1.5: return 'MUY PROBABLE'
    if gap <= 3.0: return 'PROBABLE'
    if gap <= 5.0: return 'POSIBLE'
    return 'POCO PROBABLE'

def threshold_for(v_dict, party, seats_dict, n_seats):
    cur       = v_dict.get(party, 0)
    cur_seats = seats_dict.get(party, 0)
    total     = sum(v_dict.values())
    lo, hi    = cur, max(cur * 4 + 1, total * 0.6)
    for _ in range(60):
        mid = (lo + hi) / 2
        res, _, _ = dhondt({**v_dict, party: mid}, n_seats)
        if res.get(party, 0) > cur_seats:
            hi = mid
        else:
            lo = mid
    return hi

def build_v26(pv23, izq=False):
    def v(p): return pv23.get(p, 0)
    d = {
        'PP':      v('PP')    * scale['PP'],
        'PSOE':    v('PSOE')  * scale['PSOE'],
        'VOX':     v('VOX')   * scale['VOX'],
        'SUMAR':   v('SUMAR') * scale['SUMAR'],
        'PODEMOS': v('SUMAR') * podemos_f,
        'SALF':    v('PP')    * salf_f,
    }
    for p, votes in pv23.items():
        if p not in NATIONAL_PARTIES:
            d[p] = votes * scale['OTROS']
    d = {p: vv for p, vv in d.items() if vv > 0}
    if izq:
        combined = d.pop('SUMAR', 0) + d.pop('PODEMOS', 0)
        if combined > 0:
            d['IZQ'] = combined
    return d

def get_pct19(pv19, party_key):
    total19 = sum(pv19.values()) or 1
    if party_key in ('SUMAR', 'IZQ'):
        votes = sum(pv19.get(s, 0) for s in LEFT_2019)
    else:
        votes = pv19.get(party_key, 0)
    return round(votes / total19 * 100, 1)

def gain_attribution(diff, party_key, p_internal):
    """Proportional attribution: show any loser whose proportional contribution rounds to >=1 seat."""
    party_gain = diff.get(p_internal, 0)
    if party_gain <= 0:
        return []
    losers = sorted(
        [(p, -d) for p, d in diff.items() if d < 0 and p != p_internal],
        key=lambda x: -x[1]
    )
    total_lost = sum(loss for _, loss in losers)
    if total_lost == 0:
        return []
    result = [
        loser for loser, lost in losers
        if int(lost / total_lost * party_gain + 0.5) >= 1
    ]
    # Fallback: if no party rounds to >=1 (very fragmented losses), show biggest loser
    if not result and losers:
        result = [losers[0][0]]
    return result

def analyze(party_key):
    p = 'IZQ' if party_key == 'IZQ' else party_key
    rows = []

    for _, meta in df_meta23.iterrows():
        cod   = meta['codigo_provincia']
        name  = meta['nombre_provincia']
        seats = SEATS_2026_OVERRIDE.get(name, int(meta['escanos_asignados']))

        pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
        pv19 = df_votos19[df_votos19['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
        total23_prov = sum(pv23.values()) or 1

        v26 = build_v26(pv23, izq=(party_key == 'IZQ'))
        total26 = sum(v26.values()) or 1

        # D'Hondt 2023 real y 2026 swing
        esc23, _, _        = dhondt({k: vv for k, vv in pv23.items() if vv > 0}, seats)
        esc26, last_q, last_p = dhondt(v26, seats)

        # Seats: IZQ 2023 = lo que sacó SUMAR en 2023
        s23 = esc23.get('SUMAR', 0) if party_key == 'IZQ' else esc23.get(p, 0)
        s26 = esc26.get(p, 0)

        # Porcentajes
        raw23 = pv23.get('SUMAR', 0) if party_key == 'IZQ' else pv23.get(p, 0)
        pct23 = raw23 / total23_prov * 100
        pct26 = v26.get(p, 0) / total26 * 100
        pct19 = get_pct19(pv19, party_key)

        # Umbral siguiente escaño
        umb_v   = threshold_for(v26, p, esc26, seats)
        umb_pct = umb_v / total26 * 100
        gap     = round(umb_pct - pct26, 1)

        # Fragilidad del escaño que ya da el swing
        fragile = 'none'
        p_votes = v26.get(p, 0)
        if s26 > 0:
            if last_p == p:
                fragile = 'filo'
            else:
                em, _, _ = dhondt({**v26, p: p_votes * 0.95}, seats)
                if em.get(p, 0) < s26:
                    fragile = 'sensible'

        # Diferencia de escaños 2023→2026 para todos los partidos
        all_ps = (set(esc23.keys()) - ({'SUMAR'} if party_key == 'IZQ' else set())) | set(esc26.keys())
        diff = {}
        for pp in all_ps:
            d23 = esc23.get('SUMAR', 0) if (party_key == 'IZQ' and pp == 'IZQ') else esc23.get(pp, 0)
            diff[pp] = esc26.get(pp, 0) - d23

        gain_from = gain_attribution(diff, party_key, p)

        rows.append({
            'prov':      name,
            'esc':       seats,
            'p19':       round(pct19, 1),
            'p23':       round(pct23, 1),
            'p26':       round(pct26, 1),
            's23':       int(s23),
            's26':       int(s26),
            'gain_from': gain_from,
            'fragile':   fragile,
            'umbral':    round(umb_pct, 1),
            'gap':       gap,
            'conf':      conf_tier(gap),
        })

    tier_order = {c: i for i, c in enumerate(CONF_ORDER)}
    rows.sort(key=lambda x: (tier_order.get(x['conf'], 99), x['gap']))
    return rows

# ── Resumen nacional ───────────────────────────────────────────────────────────
def nat_summary(party_key):
    p = 'IZQ' if party_key == 'IZQ' else party_key
    total_s23 = total_s26 = 0
    for _, meta in df_meta23.iterrows():
        cod   = meta['codigo_provincia']
        name  = meta['nombre_provincia']
        seats = SEATS_2026_OVERRIDE.get(name, int(meta['escanos_asignados']))
        pv23  = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
        v26   = build_v26(pv23, izq=(party_key == 'IZQ'))
        esc23, _, _ = dhondt({k: vv for k, vv in pv23.items() if vv > 0}, seats)
        esc26, _, _ = dhondt(v26, seats)
        total_s23 += esc23.get('SUMAR', 0) if party_key == 'IZQ' else esc23.get(p, 0)
        total_s26 += esc26.get(p, 0)
    return {'seats23': total_s23, 'seats26': total_s26}

print("Analizando partidos (puede tardar ~30s)...")
all_data = {}
summaries = {}
for party in ['VOX', 'PP', 'PSOE', 'SUMAR', 'IZQ']:
    print(f"  {party}...", end=' ', flush=True)
    all_data[party]  = analyze(party)
    summaries[party] = nat_summary(party)
    print(f"✓  ({summaries[party]['seats23']}→{summaries[party]['seats26']} esc.)")

out = Path('.') / 'data' / 'all_parties_data.js'
with open(out, 'w', encoding='utf-8') as f:
    f.write('const allPartiesData = ')
    json.dump(all_data, f, ensure_ascii=False, indent=2)
    f.write(';\n\n')
    f.write('const partySummaries = ')
    json.dump(summaries, f, ensure_ascii=False, indent=2)
    f.write(';\n')
print(f"\nGuardado: {out}")
