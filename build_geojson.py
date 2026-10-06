"""
Convierte el TopoJSON de es-atlas a GeoJSON de provincias con códigos INE.
Genera frontend/src/data/provinces.geojson
"""
import json
from pathlib import Path

TOPO_PATH = Path("frontend/node_modules/es-atlas/es/provinces.json")
OUT_PATH  = Path("frontend/src/data/provinces.geojson")

with open(TOPO_PATH, encoding="utf-8") as f:
    topo = json.load(f)

# Inspeccionar estructura del TopoJSON
print("Objetos disponibles:", list(topo.get("objects", {}).keys()))

obj_key = list(topo["objects"].keys())[0]
obj = topo["objects"][obj_key]
print(f"Tipo: {obj['type']}, features: {len(obj.get('geometries', []))}")
print("Propiedades ejemplo:", obj["geometries"][0].get("properties", {}))
