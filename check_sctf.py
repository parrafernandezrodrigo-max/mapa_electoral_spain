import json
d = json.load(open('frontend/src/data/all_parties_data.json', encoding='utf-8'))
r = next(x for x in d['VOX'] if x['prov'] == 'Santa Cruz de Tenerife')
print('Santa Cruz VOX:')
print(f"  p19={r['p19']}%  p23={r['p23']}%  p26={r['p26']}%")
print(f"  s23={r['s23']}  s26={r['s26']}  tracking={r['tracking']}")
print(f"  conf={r['conf']}  gap={r['gap']}pp")
