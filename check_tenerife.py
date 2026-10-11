import sys
sys.path.insert(0, '.')
from parser import parse_conv

df_meta23, df_votos23 = parse_conv('202307')
df_meta19, df_votos19 = parse_conv('201911')

# Buscar Santa Cruz de Tenerife
meta = df_meta23[df_meta23['nombre_provincia'].str.contains('Tenerife', na=False)]
if meta.empty:
    meta = df_meta23[df_meta23['nombre_provincia'].str.contains('Santa', na=False)]
print("Provincias con 'Santa' o 'Tenerife':", meta['nombre_provincia'].tolist())

cod = meta.iloc[0]['codigo_provincia']
total = df_votos23[df_votos23['codigo_provincia'] == cod]['votos'].sum()

print(f"\n--- 2023 (cod={cod}) ---")
pv23 = df_votos23[df_votos23['codigo_provincia'] == cod].copy()
pv23['pct'] = pv23['votos'] / total * 100
print(pv23[['siglas','votos','pct']].sort_values('votos', ascending=False).to_string(index=False))

print(f"\n--- 2019 (cod={cod}) ---")
total19 = df_votos19[df_votos19['codigo_provincia'] == cod]['votos'].sum()
pv19 = df_votos19[df_votos19['codigo_provincia'] == cod].copy()
pv19['pct'] = pv19['votos'] / total19 * 100
print(pv19[['siglas','votos','pct']].sort_values('votos', ascending=False).to_string(index=False))
