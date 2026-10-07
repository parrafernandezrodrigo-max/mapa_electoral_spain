import json
from pathlib import Path

data = json.loads(Path("data/processed/summary_province.json").read_text(encoding="utf-8"))

for cp, label in [("42", "Soria"), ("28", "Madrid"), ("08", "Barcelona")]:
    p = data["202307"][cp]
    vc = p["votos_candidaturas"]
    all_parties = p["partidos_con_escano"] + p["partidos_sin_escano"]
    big  = [q for q in all_parties if q["votos"]/vc >= 0.01]  # >= 1%
    tiny = [q for q in all_parties if q["votos"]/vc <  0.01]
    tiny_votes = sum(q["votos"] for q in tiny)
    print(f"\n{label} — {p['seats_total']} esc, {vc:,} votos")
    print(f"  Partidos >= 1% ({len(big)}): {[q['siglas'] for q in big]}")
    print(f"  Partidos <  1% ({len(tiny)}): {tiny_votes:,} votos ({tiny_votes/vc*100:.1f}%)")
