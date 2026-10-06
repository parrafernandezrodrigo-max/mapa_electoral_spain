"""
Descarga el GeoJSON de provincias de España desde una fuente pública
y lo procesa para el frontend.

Fuente: España GeoJSON from martingonzalez.net o similar
"""
import json
import urllib.request
from pathlib import Path

OUT = Path("frontend/src/data/provinces.geojson")

# GeoJSON de provincias españolas con código INE
# Fuente: https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/spain-provinces.geojson
# Alternativa: datos del IGN simplificados

URLS = [
    # Opción 1: GeoJSON con códigos INE incluidos
    "https://raw.githubusercontent.com/alberthdev/alberthdev.github.io/master/leaflet-js/geojson/spain_provinces.geojson",
    # Opción 2: desde España-geojson repo
    "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/spain/spain-provinces.json",
]

for url in URLS:
    try:
        print(f"Descargando desde {url[:70]}...")
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"Guardado en {OUT}  ({OUT.stat().st_size:,} bytes)")

        # Inspeccionar las propiedades del primer feature
        if "features" in data:
            props = data["features"][0]["properties"]
            print(f"Propiedades del primer feature: {list(props.keys())}")
        elif "objects" in data:
            print("Formato: TopoJSON")
        break
    except Exception as e:
        print(f"  Falló: {e}")
else:
    print("\nNinguna URL funcionó. Descarga manual:")
    print("  https://github.com/martingonzalez/spain-geojson")
    print("  Coloca el fichero en frontend/src/data/provinces.geojson")
