"""
gen_json_data.py
Genera los JSON para Observable Framework en frontend/src/data/
"""
import sys, json, re
sys.path.insert(0, '.')
from pathlib import Path

src = Path('.') / 'data' / 'all_parties_data.js'
txt = src.read_text(encoding='utf-8')

m1 = re.search(r'const allPartiesData = (.*?);\s*const partySummaries', txt, re.DOTALL)
m2 = re.search(r'const partySummaries = (.*?);?\s*$', txt, re.DOTALL)

all_data  = json.loads(m1.group(1))
summaries = json.loads(m2.group(1))

out_dir = Path('.') / 'frontend' / 'src' / 'data'
out_dir.mkdir(parents=True, exist_ok=True)

(out_dir / 'all_parties_data.json').write_text(
    json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')
(out_dir / 'party_summaries.json').write_text(
    json.dumps(summaries, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"Guardado: {out_dir}/all_parties_data.json")
print(f"Guardado: {out_dir}/party_summaries.json")
for p, s in summaries.items():
    print(f"  {p}: {s['seats23']}→{s['seats26']} esc.")
