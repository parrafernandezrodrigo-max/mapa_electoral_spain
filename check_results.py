import pandas as pd, json
from pathlib import Path

proc = Path("data/processed")

df = pd.read_parquet(proc / "results_all.parquet")
print("Conv IDs en results_all.parquet:")
print(df.groupby("conv_id")["codigo_provincia"].nunique().to_string())

with open(proc / "summary_province.json", encoding="utf-8") as f:
    js = json.load(f)
print(f"\nConv IDs en summary_province.json: {sorted(js.keys())}")

print("\nPartidos sin bloque (top 30 votos históricos totales):")
otros = df[df["bloque"] == "otros"]
top = otros.groupby(["siglas", "denominacion"])["votos"].sum().sort_values(ascending=False).head(30)
for (sig, den), v in top.items():
    print(f"  {sig:<25} {v:>12,}  {den[:60]}")
