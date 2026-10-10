import json, re
from pathlib import Path

txt = Path('data/all_parties_data.js').read_text(encoding='utf-8')
# split at the two variable declarations
m1 = re.search(r'const allPartiesData = (.*?);\s*const partySummaries', txt, re.DOTALL)
m2 = re.search(r'const partySummaries = (.*?);?\s*$', txt, re.DOTALL)
parties_data = json.loads(m1.group(1))
summaries = json.loads(m2.group(1))

for p, rows in parties_data.items():
    secs = {}
    for r in rows:
        secs[r['conf']] = secs.get(r['conf'], 0) + 1
    s = summaries[p]
    print(f"{p}: {s['seats23']}→{s['seats26']} esc | tiers: {secs}")
