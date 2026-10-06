from parser import parse_conv
from formats import CONVOCATORIAS
import traceback

for conv_id in ["198910", "199306", "201111", "201512", "201606", "201904", "201911", "202307"]:
    print(f"\n{conv_id} ({CONVOCATORIAS[conv_id]})", end=" → ")
    try:
        dm, dv = parse_conv(conv_id)
        print(f"{len(dm)} provincias, {len(dv)} filas votos, {dv['siglas'].nunique()} partidos únicos")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
