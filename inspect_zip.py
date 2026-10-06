import zipfile, sys
from pathlib import Path

raw = Path("data/raw")
target = sys.argv[1] if len(sys.argv) > 1 else "PROV_02_202307_1.zip"
path = raw / target

with zipfile.ZipFile(path) as arch:
    for info in sorted(arch.infolist(), key=lambda x: x.filename):
        print(f"{info.file_size:>10}  {info.filename}")
