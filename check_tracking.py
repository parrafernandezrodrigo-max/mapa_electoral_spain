import json
d = json.load(open('frontend/src/data/all_parties_data.json', encoding='utf-8'))
for party in ['VOX','PP','PSOE','SUMAR','IZQ']:
    vals = sorted(r['tracking'] for r in d[party] if r['tracking'] is not None)
    n = len(vals)
    p10 = vals[n // 10]
    med = vals[n // 2]
    p90 = vals[int(n * 0.9)]
    print(f'{party}: min={vals[0]:.2f}  p10={p10:.2f}  median={med:.2f}  p90={p90:.2f}  max={vals[-1]:.2f}')
    # Show outliers (< 0.5 or > 1.7)
    out = [(r['prov'], r['tracking']) for r in d[party] if r['tracking'] is not None and (r['tracking'] < 0.5 or r['tracking'] > 1.7)]
    if out:
        print(f'  outliers: {out}')
