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

# ── Partidos nacionales (excluidos de OTROS) ───────────────────────────────────
NATIONAL_23    = {'PP', 'PSOE', 'VOX', 'SUMAR'}
NATIONAL_26    = {'PP', 'PSOE', 'VOX', 'SUMAR'}   # PODEMOS y SALF van en OTROS
NAT_2019_SIGLAS = {'PP', 'PSOE', 'VOX', 'Cs'} | set(LEFT_2019)

# ── Porcentajes nacionales 2019 (para tracking ratio) ─────────────────────────
nat19     = df_votos19.groupby('siglas')['votos'].sum()
total19_n = nat19.sum()

def get_nat_pct19(party_key):
    if party_key in ('SUMAR', 'IZQ'):
        votes = sum(nat19.get(s, 0) for s in LEFT_2019)
    else:
        votes = nat19.get(party_key, 0)
    return votes / total19_n * 100

def get_nat_pct23(party_key):
    if party_key in ('SUMAR', 'IZQ'):
        return nat_pct23.get('SUMAR', 0)
    return nat_pct23.get(party_key, 0)

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
        total19_prov = sum(pv19.values()) or 1

        # Fallback para partidos nacionales ausentes en 2023 pero presentes en 2019:
        # inyectar votos 2019 escalados al pool 2023 y al factor 2019→2026,
        # de forma que v26 = pct19_prov × (nat_pct26 / nat_pct19) × total26
        pv23_model = dict(pv23)
        for _pk in ['PP', 'PSOE', 'VOX', 'SUMAR']:
            if pv23.get(_pk, 0) == 0:
                _v19 = sum(pv19.get(s, 0) for s in LEFT_2019) if _pk == 'SUMAR' else pv19.get(_pk, 0)
                _np19 = get_nat_pct19(_pk)
                _np23 = get_nat_pct23(_pk)
                if _v19 > 0 and _np19 > 0 and _np23 > 0:
                    pv23_model[_pk] = _v19 * (total23_prov / total19_prov) * (_np23 / _np19)

        v26 = build_v26(pv23_model, izq=(party_key == 'IZQ'))
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

        # Tracking histórico: ratio swing provincial 19→23 vs swing nacional 19→23
        nat_p19 = get_nat_pct19(party_key)
        nat_p23 = get_nat_pct23(party_key)
        if pct19 > 0.1 and pct23 > 0.1 and nat_p19 > 0 and nat_p23 > 0:
            prov_swing = pct23 / pct19
            nat_swing  = nat_p23 / nat_p19
            tracking   = round(prov_swing / nat_swing, 2)
        else:
            tracking   = None

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
            'tracking':  tracking,
        })

    tier_order = {c: i for i, c in enumerate(CONF_ORDER)}
    rows.sort(key=lambda x: (tier_order.get(x['conf'], 99), x['gap']))
    return rows

# ── OTROS: partidos regionales agregados ──────────────────────────────────────
def analyze_otros():
    rows = []
    for _, meta in df_meta23.iterrows():
        cod   = meta['codigo_provincia']
        name  = meta['nombre_provincia']
        seats = SEATS_2026_OVERRIDE.get(name, int(meta['escanos_asignados']))

        pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
        pv19 = df_votos19[df_votos19['codigo_provincia'] == cod].set_index('siglas')['votos'].to_dict()
        total23_prov = sum(pv23.values()) or 1
        total19_prov = sum(pv19.values()) or 1

        pv23_model = dict(pv23)
        for _pk in ['PP', 'PSOE', 'VOX', 'SUMAR']:
            if pv23.get(_pk, 0) == 0:
                _v19 = sum(pv19.get(s, 0) for s in LEFT_2019) if _pk == 'SUMAR' else pv19.get(_pk, 0)
                _np19 = get_nat_pct19(_pk)
                _np23 = get_nat_pct23(_pk)
                if _v19 > 0 and _np19 > 0 and _np23 > 0:
                    pv23_model[_pk] = _v19 * (total23_prov / total19_prov) * (_np23 / _np19)

        v26 = build_v26(pv23_model, izq=False)
        total26 = sum(v26.values()) or 1

        esc23, _, _ = dhondt({k: vv for k, vv in pv23.items() if vv > 0}, seats)
        esc26, _, _ = dhondt(v26, seats)

        s23 = sum(v for k, v in esc23.items() if k not in NATIONAL_23)
        s26 = sum(v for k, v in esc26.items() if k not in NATIONAL_26)

        raw23 = sum(v for k, v in pv23.items() if k not in NATIONAL_23)
        pct23 = raw23 / total23_prov * 100
        raw19 = sum(v for k, v in pv19.items() if k not in NAT_2019_SIGLAS)
        pct19 = raw19 / total19_prov * 100
        otros26 = sum(v for k, v in v26.items() if k not in NATIONAL_26)
        pct26 = otros26 / total26 * 100

        diff_all = {k: esc26.get(k, 0) - esc23.get(k, 0)
                    for k in set(list(esc23.keys()) + list(esc26.keys()))}
        otros_gain = s26 - s23
        if otros_gain > 0:
            nat_losers = sorted(
                [(k, -d) for k, d in diff_all.items() if d < 0 and k in NATIONAL_23],
                key=lambda x: -x[1]
            )
            gain_from = [nat_losers[0][0]] if nat_losers else []
        else:
            gain_from = []

        rows.append({
            'prov': name, 'esc': seats,
            'p19': round(pct19, 1), 'p23': round(pct23, 1), 'p26': round(pct26, 1),
            's23': int(s23), 's26': int(s26),
            'gain_from': gain_from, 'fragile': None,
            'umbral': 0, 'gap': None, 'conf': None,
            'tracking': None,
        })

    rows.sort(key=lambda x: -x['esc'])
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
for party in ['VOX', 'PP', 'PSOE', 'SUMAR']:
    print(f"  {party}...", end=' ', flush=True)
    all_data[party] = analyze(party)
    summaries[party] = {
        'seats23': sum(r['s23'] for r in all_data[party]),
        'seats26': sum(r['s26'] for r in all_data[party]),
    }
    print(f"✓  ({summaries[party]['seats23']}→{summaries[party]['seats26']} esc.)")

print(f"  OTROS...", end=' ', flush=True)
all_data['OTROS']  = analyze_otros()
summaries['OTROS'] = {
    'seats23': sum(r['s23'] for r in all_data['OTROS']),
    'seats26': sum(r['s26'] for r in all_data['OTROS']),
}
total23 = sum(summaries[p]['seats23'] for p in ['VOX','PP','PSOE','SUMAR','OTROS'])
total26 = sum(summaries[p]['seats26'] for p in ['VOX','PP','PSOE','SUMAR','OTROS'])
print(f"✓  ({summaries['OTROS']['seats23']}→{summaries['OTROS']['seats26']} esc.)  |  TOTAL: {total23}→{total26}")

out = Path('.') / 'data' / 'all_parties_data.js'
with open(out, 'w', encoding='utf-8') as f:
    f.write('const allPartiesData = ')
    json.dump(all_data, f, ensure_ascii=False, indent=2)
    f.write(';\n\n')
    f.write('const partySummaries = ')
    json.dump(summaries, f, ensure_ascii=False, indent=2)
    f.write(';\n')
print(f"\nGuardado: {out}")

# Escribir también los JSON que consume el Observable Framework
fe_data = Path('.') / 'frontend' / 'src' / 'data'
with open(fe_data / 'all_parties_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
with open(fe_data / 'party_summaries.json', 'w', encoding='utf-8') as f:
    json.dump(summaries, f, ensure_ascii=False, indent=2)
print(f"Guardado: {fe_data / 'all_parties_data.json'}")
