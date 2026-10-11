import sys
sys.path.insert(0, '.')
from vox_threshold_analysis import POLL_2026, NATIONAL_PARTIES, scale
from gen_all_parties import nat_pct23, get_nat_pct19, get_nat_pct23

print("Factores de swing 2023→2026 por partido:")
for p in ['VOX', 'PP', 'PSOE', 'SUMAR']:
    n23 = get_nat_pct23(p)
    poll = POLL_2026.get(p, 0)
    print(f"  {p}: {n23:.2f}% (2023) → {poll:.1f}% (encuesta) = ×{poll/n23:.3f}")
