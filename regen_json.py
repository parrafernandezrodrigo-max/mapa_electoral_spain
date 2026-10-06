import json
import pandas as pd
from pathlib import Path
from pipeline import _build_json

PROCESSED_DIR = Path(__file__).parent / "data" / "processed"

df_results = pd.read_parquet(PROCESSED_DIR / "results_all.parquet")
df_blocks  = pd.read_parquet(PROCESSED_DIR / "blocks_all.parquet")

output = _build_json(df_results, df_blocks)

json_path = PROCESSED_DIR / "summary_province.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("OK →", json_path)

# Spot check
soria = output.get("202307", {}).get("42", {})
print("Soria 2023 pct_votos_perdidos:", soria.get("pct_votos_perdidos"))
print("Soria 2023 votos_perdidos_por_bloque:", soria.get("votos_perdidos_por_bloque"))
